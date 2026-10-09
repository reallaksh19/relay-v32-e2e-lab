"""Checks real snapshot transport and custody boundaries; native engine run is separate."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'native_snapshot_replay.py'
spec = importlib.util.spec_from_file_location('native_snapshot_replay', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
REPO=mod.REPO


def inputs():
    # Test the real approved release bytes, not a plausible six-node mock.
    # The new source-custody gate requires exact historical graph identity.
    raw=(SOURCE.parents[0] / 'governance' / 'released-graph.json').read_bytes()
    graph=json.loads(raw)
    assert mod.git_blob(raw)==mod.RELEASED_GRAPH_BLOB
    pulls={}
    for n,branch in [(8,'lab/r01'),(13,'lab/r02'),(15,'lab/r03')]:
        pulls[str(n)]={'number':n,'merged':True,
          'head':{'ref':branch,'sha':str(n%10)*40,'repo':{'full_name':REPO}},
          'base':{'ref':'main','sha':'b'*40,'repo':{'full_name':REPO}}}
    snap={'schema':mod.SCHEMA,'repository':REPO,'graph_git_blob':mod.git_blob(raw),
          'main_sha':'a'*40,'final_main_sha':'a'*40,'source_kind':'GITHUB_GET_ONLY_UNATTESTED',
          'issues':{str(n):{'title':f'issue-{n}'} for n in range(1,7)},
          'pulls':pulls,
          'comments':{str(n):[{'id':n*100,'body':f'# {n} task evidence',
                             'user':{'login':'reviewer'},'author_association':'COLLABORATOR'}] for n in (4,5,6)}}
    return graph,raw,snap


class FakeEngine:
    def plan_github(self,t,g):
        # This only tests the transport's read surface. It is NOT the Common engine.
        assert t.get_commit_sha('main')=='a'*40
        for i in range(1,7):
            assert t.get_issue(i)['title']==f'issue-{i}'
        for k in (4,5,6):
            assert t.list_comments(k)[0]['author_association']=='COLLABORATOR'
        for k in (8,13,15):
            assert t.get_pull(k)['merged'] is True
        return {'input_digest':'sha256:'+'c'*64,
                'expected_titles':{n['ref']:f'expected-{n["ref"]}' for n in g['nodes']},
                'drift':{n['ref']:{'status':'STALE_OR_HAND_EDITED'} for n in g['nodes']},
                'rejected_facts':[], 'would_write_titles':6}


class ReplayTests(unittest.TestCase):
    def setUp(self):self.graph,self.raw,self.snapshot=inputs()
    def check(self):return mod.validate_snapshot(self.graph,self.raw,self.snapshot)
    def test_valid_read_only_transport(self):
        self.check(); t=mod.SnapshotTransport(self.snapshot)
        self.assertFalse(hasattr(t,'patch_title'))
        self.assertEqual('a'*40,t.get_commit_sha('main'))
        self.assertEqual(8,t.get_pull(8)['number'])
        r=mod.replay(self.graph,self.raw,self.snapshot,FakeEngine())
        self.assertFalse(r['issue_or_pr_writes'])
        self.assertEqual('NONE',r['progress_credit'])
        self.assertEqual(6,r['source_view_drift_count'])
    def test_capture_two_pass_complete(self):
        d={f'repos/{REPO}/commits/main':{'sha':'a'*40}}
        for i in range(1,7):d[f'repos/{REPO}/issues/{i}']={'title':f'issue-{i}'}
        for key,v in self.snapshot['pulls'].items():d[f'repos/{REPO}/pulls/{key}']=v
        for key,v in self.snapshot['comments'].items():
            d[f'repos/{REPO}/issues/{key}/comments?per_page=100&page=1']=v
        result=mod.capture(self.graph,self.raw,d.__getitem__)
        self.assertEqual(self.snapshot,result)
    def test_changed_main_rejected(self):
        self.snapshot['final_main_sha']='c'*40
        with self.assertRaisesRegex(ValueError,'MAIN_MOVED'):self.check()
    def test_graph_blob_drift_rejected(self):
        self.raw+=b'\n'
        with self.assertRaisesRegex(ValueError,'RELEASED_GRAPH_SOURCE_BLOB_NOT_PINNED'):self.check()
    def test_wrong_repository(self):
        self.snapshot['repository']='fake/repo'
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_SCHEMA_OR_REPO'):self.check()
    def test_missing_issues(self):
        self.snapshot['issues'].pop('2')
        with self.assertRaisesRegex(ValueError,'ISSUE_SET_INCOMPLETE'):self.check()
    def test_missing_pr(self):
        self.snapshot['pulls'].pop('8')
        with self.assertRaisesRegex(ValueError,'PR_SET_INCOMPLETE'):self.check()
    def test_missing_leaf_comments(self):
        self.snapshot['comments'].pop('4')
        with self.assertRaisesRegex(ValueError,'COMMENT_SET_INCOMPLETE'):self.check()
    def test_changed_pr_head_branch(self):
        self.snapshot['pulls']['8']['head']['ref']='lab/r02'
        with self.assertRaisesRegex(ValueError,'PR_BRANCH_MISMATCH'):self.check()
    def test_unmerged_pr_rejected(self):
        self.snapshot['pulls']['13']['merged']=False
        with self.assertRaisesRegex(ValueError,'PR_NUMBER_OR_MERGE_INVALID'):self.check()
    def test_duplicate_comment_ids(self):
        self.snapshot['comments']['4'].append(copy.deepcopy(self.snapshot['comments']['4'][0]))
        with self.assertRaisesRegex(ValueError,'COMMENT_ID_REPEATED'):self.check()
    def test_missing_author_association(self):
        self.snapshot['comments']['4'][0].pop('author_association')
        with self.assertRaisesRegex(ValueError,'COMMENT_AUTHOR_NOT_GROUNDED'):self.check()
    def test_forged_attestation_flag_refused(self):
        self.snapshot['source_kind']='SIGNED_INDEPENDENT_OWNER_FACTS'
        with self.assertRaisesRegex(ValueError,'FALSE_AUTHORITY'):self.check()
    def test_extra_provider_material_refused(self):
        self.snapshot['pulls']['21']=self.snapshot['pulls']['8']
        with self.assertRaisesRegex(ValueError,'PR_SET_INCOMPLETE'):self.check()
    def test_source_graph_changed_weights(self):
        self.graph['nodes'][3]['weight']=35
        with self.assertRaisesRegex(ValueError,'RELEASED_GRAPH_SOURCE_BLOB_NOT_PINNED'):
            mod.validate_snapshot(self.graph,json.dumps(self.graph,sort_keys=True).encode(),self.snapshot)
    def test_disallowed_branch_binding(self):
        self.graph['nodes'][3]['candidate_ref']='feature/random'
        with self.assertRaisesRegex(ValueError,'GRAPH_MAPPING_DIFFERS_FROM_PINNED_BYTES'):self.check()
    def test_capture_issue_title_race(self):
        d={f'repos/{REPO}/commits/main':{'sha':'a'*40}}
        for i in range(1,7):d[f'repos/{REPO}/issues/{i}']={'title':f'issue-{i}'}
        for key,v in self.snapshot['pulls'].items():d[f'repos/{REPO}/pulls/{key}']=v
        for key,v in self.snapshot['comments'].items():d[f'repos/{REPO}/issues/{key}/comments?per_page=100&page=1']=v
        counter=[0]
        def mutate(endpoint):
            if endpoint.endswith('/issues/4'):
                counter[0]+=1
                if counter[0]>1:return {'title':'edited'}
            return d[endpoint]
        with self.assertRaisesRegex(ValueError,'ISSUE_TITLE_CHANGED'):mod.capture(self.graph,self.raw,mutate)
    def test_capture_comment_body_race(self):
        d={f'repos/{REPO}/commits/main':{'sha':'a'*40}}
        for i in range(1,7):d[f'repos/{REPO}/issues/{i}']={'title':f'issue-{i}'}
        for key,v in self.snapshot['pulls'].items():d[f'repos/{REPO}/pulls/{key}']=v
        for key,v in self.snapshot['comments'].items():d[f'repos/{REPO}/issues/{key}/comments?per_page=100&page=1']=v
        counter=[0]
        def mutate(endpoint):
            if endpoint.endswith('/issues/4/comments?per_page=100&page=1'):
                counter[0]+=1
                if counter[0]>1:
                    body=copy.deepcopy(d[endpoint]);body[0]['body']='edited';return body
            return d[endpoint]
        with self.assertRaisesRegex(ValueError,'COMMENTS_CHANGED_DURING'):mod.capture(self.graph,self.raw,mutate)
    def test_provider_page_not_list(self):
        d={f'repos/{REPO}/commits/main':{'sha':'a'*40}}
        for i in range(1,7):d[f'repos/{REPO}/issues/{i}']={'title':f'issue-{i}'}
        for key,v in self.snapshot['pulls'].items():d[f'repos/{REPO}/pulls/{key}']=v
        for key,v in self.snapshot['comments'].items():d[f'repos/{REPO}/issues/{key}/comments?per_page=100&page=1']=v
        d[f'repos/{REPO}/issues/4/comments?per_page=100&page=1']={'unexpected':True}
        with self.assertRaisesRegex(ValueError,'PAGE_NOT_LIST'):mod.capture(self.graph,self.raw,d.__getitem__)
    def test_private_output_file_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'snapshot.json';mod._private_save(p,self.snapshot)
            self.assertEqual(0o600, p.stat().st_mode & 0o777)
            with self.assertRaisesRegex(ValueError,'OUTPUT_PATH_ALREADY_EXISTS'):mod._private_save(p,self.snapshot)
    def test_unexpected_main_ref_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNRELEASED_BASE_REF'):
            mod.SnapshotTransport(self.snapshot).get_commit_sha('develop')
    def test_pristine_graph_exact_release_source(self):
        self.assertEqual(mod.RELEASED_GRAPH_BLOB,mod.git_blob(self.raw))
        mod.require_released_graph(self.graph,self.raw)

    def test_coherent_graph_and_snapshot_rehash_is_not_authority(self):
        # The old guard accepted a rewritten graph if the snapshot's blob was
        # recomputed consistently. The new guard rejects this even on replay.
        self.graph['nodes'][3]['weight']=99
        self.raw=json.dumps(self.graph,sort_keys=True).encode()
        self.snapshot['graph_git_blob']=mod.git_blob(self.raw)
        with self.assertRaisesRegex(ValueError,'RELEASED_GRAPH_SOURCE_BLOB_NOT_PINNED'):
            mod.replay(self.graph,self.raw,self.snapshot,FakeEngine())

    def test_changed_mapping_against_unchanged_approved_bytes_refused(self):
        self.graph['nodes'][3]['weight']=99
        with self.assertRaisesRegex(ValueError,'GRAPH_MAPPING_DIFFERS_FROM_PINNED_BYTES'):
            self.check()

    def test_capture_refuses_changed_graph_before_any_get(self):
        self.graph['nodes'][3]['weight']=99
        changed=json.dumps(self.graph,sort_keys=True).encode()
        provider_calls=[]
        def forbidden_get(url):
            provider_calls.append(url)
            raise AssertionError("Unexpected provider GET before graph approval")
        with self.assertRaisesRegex(ValueError,'RELEASED_GRAPH_SOURCE_BLOB_NOT_PINNED'):
            mod.capture(self.graph,changed,forbidden_get)
        self.assertEqual([],provider_calls)

    def test_snapshot_aliasing_does_not_mutate(self):
        t=mod.SnapshotTransport(self.snapshot)
        p=t.get_pull(8);p['head']['ref']='evil'
        c=t.list_comments(4);c[0]['body']='evil'
        self.assertEqual('lab/r01',t.get_pull(8)['head']['ref'])
        self.assertEqual('# 4 task evidence',t.list_comments(4)[0]['body'])

if __name__=='__main__':unittest.main()
