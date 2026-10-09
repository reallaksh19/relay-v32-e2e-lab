"""Pure probe orchestration tests, not a substitute for pinned Common tests."""
import importlib.util
from pathlib import Path
import copy
import unittest
spec=importlib.util.spec_from_file_location('readprobe',Path(__file__).resolve().parents[1]/'scripts'/'native_material_status_probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
LAB=probe.LAB

class Provider:
    def __init__(self):
        self.sha='a'*40
        self.titles={1:'ROOT - stale',4:'R01 - NOT_STARTED'}
        self.calls=0
        self.issue_reads=0
        self.pr='MERGED'
        self.comments=[]
    def get_commit_sha(self,ref):
        self.calls+=1
        return self.sha
    def get_issue(self,n):
        self.issue_reads+=1
        return {'title':self.titles[n]}

class Native:
    def validate_graph(self,g):
        return {'nodes':{f'{LAB}#1':{'kind':'ROOT','number':1},f'{LAB}#4':{'kind':'LEAF','number':4}}}
    def ledger_from_github(self,t,g):
        return list(t.comments)
    def observe_github(self,t,g):
        return {f'{LAB}#4':{'pr_state':t.pr,'candidate_sha':'b'*40}}
    def project(self,g,ledger,observations):
        leaf=f'{LAB}#4';root=f'{LAB}#1'
        state='UNMATERIALIZED' if not ledger and observations[leaf]['pr_state']=='MERGED' else 'ACTIVE'
        return {'input_digest': 'sha256:'+'c'*64 if not ledger else 'sha256:'+'d'*64,
                'rejected_facts':[],
                'nodes':{root:{'state':state,'lifecycle':state,'title_prefix':'ROOT EXPECTED','progress':{'D':0,'E':0}},
                         leaf:{'state':state,'lifecycle':state,'title_prefix':'R01 EXPECTED','progress':{'P':0,'E':0},'materialization':{'status':state}}}}
    def title_drift(self,title,prefix):
        return {'status':'OK' if title==prefix else 'STALE_OR_HAND_EDITED','expected':prefix}

def graph():return {'programme':{'repository':LAB,'base_ref':'main'}}

class ProbeContract(unittest.TestCase):
    def test_merged_without_facts_unmaterialized_and_no_writes(self):
        p=Provider();r=probe.reconcile(Native(),graph(),p)
        self.assertEqual('UNMATERIALIZED',r['nodes'][0]['native_state'])
        self.assertEqual(2,r['title_drift_count']);self.assertFalse(r['facts_created']);self.assertFalse(r['issue_titles_written'])
        self.assertEqual(0,r['ledger_records_observed'])
    def test_no_unauthorized_repository(self):
        a=graph();a['programme']['repository']='different/repo'
        with self.assertRaisesRegex(ValueError,'WRONG_LAB'):probe.reconcile(Native(),a,Provider())
    def test_no_unreleased_base(self):
        a=graph();a['programme']['base_ref']='dev'
        with self.assertRaisesRegex(ValueError,'BASE_REF_UNAUTHORIZED'):probe.reconcile(Native(),a,Provider())
    def test_main_sha_required(self):
        p=Provider();p.sha='not-sha'
        with self.assertRaisesRegex(ValueError,'MAIN_SHA_INVALID'):probe.reconcile(Native(),graph(),p)
    def test_moving_main_rejected(self):
        p=Provider()
        def moving(ref):p.calls+=1;return 'a'*40 if p.calls==1 else 'b'*40
        p.get_commit_sha=moving
        with self.assertRaisesRegex(ValueError,'MAIN_MOVED'):probe.reconcile(Native(),graph(),p)
    def test_issue_title_movement_rejected_between_reads(self):
        p=Provider();orig=p.get_issue
        def edit(n):
            v=orig(n)
            if p.issue_reads>2:return {'title':v['title']+' changed'}
            return v
        p.get_issue=edit
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):probe.reconcile(Native(),graph(),p)
    def test_late_fact_ledger_rejected(self):
        p=Provider();n=Native();count=[0]
        def moving_ledger(t,g):count[0]+=1;return [] if count[0]==1 else [{'facts':'new'}]
        n.ledger_from_github=moving_ledger
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):probe.reconcile(n,graph(),p)
    def test_native_input_digest_race_detected(self):
        p=Provider();n=Native();old=n.project;count=[0]
        def mutate(*a):
            count[0]+=1;r=old(*a);r['input_digest']='sha256:'+('d' if count[0]>1 else 'c')*64;return r
        n.project=mutate
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHANGED'):probe.reconcile(n,graph(),p)
    def test_wrong_native_node_rejected(self):
        p=Provider();n=Native();n.project=lambda *args:{'input_digest':'sha256:'+'c'*64,'rejected_facts':[], 'nodes':{'oops':{'title_prefix':'hi'}}}
        with self.assertRaisesRegex(ValueError,'NATIVE_PROJECTION_REF_MISMATCH'):probe.reconcile(n,graph(),p)
    def test_absent_leaf_provider_rejected(self):
        p=Provider();n=Native();n.observe_github=lambda *args:{}
        with self.assertRaises((KeyError,ValueError)):probe.reconcile(n,graph(),p)
    def test_merged_pr_does_not_become_not_started(self):
        p=Provider();n=Native();old=n.project
        def wrong(*a):
            r=old(*a);leaf=f'{LAB}#4';r['nodes'][leaf]['lifecycle']='NOT_STARTED';return r
        n.project=wrong
        with self.assertRaisesRegex(ValueError,'NATIVE_MERGED_PR_MISTAKEN'):probe.reconcile(n,graph(),p)
    def test_no_writes_even_with_source_comments(self):
        p=Provider();p.comments=[{'source':'issue#4','facts':{'unit':'U01'}}]
        r=probe.reconcile(Native(),graph(),p)
        self.assertFalse(r['facts_created']);self.assertEqual(1,r['ledger_records_observed'])
    def test_native_engine_untrusted_bytes_fail_before_import(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            f=Path(td)/'engine.py';f.write_text('raise RuntimeError("DANGER")')
            with self.assertRaisesRegex(ValueError,'ENGINE_BLOB_NOT_PINNED'):probe.load_trusted_engine(f)
    def test_event_main_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"DOES_NOT_MATCH_EVENT_SHA"):
            probe.reconcile(Native(),graph(),Provider(),expected_main_sha="b"*40)
    def test_event_main_exact_match(self):
        r=probe.reconcile(Native(),graph(),Provider(),expected_main_sha="a"*40)
        self.assertEqual("a"*40,r["source_main_sha"])
    def test_missing_engine_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'ENGINE_FILE_MISSING'):probe.load_trusted_engine(Path('/no/such/engine.py'))

if __name__=='__main__':unittest.main()
