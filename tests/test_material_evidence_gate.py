import importlib.util
import json
from pathlib import Path
import copy
import unittest

spec = importlib.util.spec_from_file_location('gate',Path(__file__).resolve().parents[1] / 'scripts' / 'material_evidence_gate.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REPO='reallaksh19/relay-v32-e2e-lab'


def inputs():
    nodes=[]; obs=[]
    for i,(prnum,branch) in enumerate([(8,'lab/r01'),(13,'lab/r02'),(15,'lab/r03')],1):
        name=f'R0{i}'; sha=(str(i)*40)
        nodes.append({'kind':'LEAF','responsibility_id':name,'ref':f'{REPO}#{i+3}','primary_pr':f'{REPO}#{prnum}','candidate_ref':branch})
        obs.append({'responsibility_id':name,'pr':{'number':prnum,'merged':True,'head':{'ref':branch,'sha':sha,'repo':{'full_name':REPO}},'base':{'ref':'main','repo':{'full_name':REPO}}},'runs':[{'id':i,'event':'pull_request','head_sha':sha,'status':'completed','conclusion':'failure','jobs':[{'name':'responsibility-acceptance','runner_name':'','status':'completed','conclusion':'failure','steps':[]}]}]})
    return {'programme':{'repository':REPO,'base_ref':'main'},'nodes':nodes}, {'schema':'lab-v32-provider-observation-v1','repository':REPO,'leaves':obs}

class Preflight(unittest.TestCase):
    def test_pre_runner_failure_retains_material_without_facts(self):
        graph, snap=inputs();out=mod.evaluate(graph,snap)
        self.assertEqual('NOT_QUALIFIED_FOR_FACTS_ADMISSION',out['overall'])
        self.assertTrue(all('HOSTED_NO_RUNNER_EXECUTED' in x['blockers'] for x in out['leaves']))
        self.assertTrue(all(x['material_state']=='SOURCE_MATERIAL_OBSERVED' and not x['facts_admitted'] for x in out['leaves']))
    def test_no_actions_does_not_become_green(self):
        a,b=inputs(); b['leaves'][0]['runs']=[]
        self.assertIn('NO_EXACT_HEAD_PRODUCT_ACTIONS',mod.evaluate(a,b)['leaves'][0]['blockers'])
    def test_wrong_head_not_confused_with_main_merge_sha(self):
        a,b=inputs();b['leaves'][0]['pr']['head']['sha']='bad'
        self.assertEqual('MATERIAL_IDENTITY_UNVERIFIED',mod.evaluate(a,b)['leaves'][0]['material_state'])
    def test_wrong_pr_number_fails_binding(self):
        a,b=inputs();b['leaves'][1]['pr']['number']=14
        self.assertIn('BOUND_PR_MISMATCH',mod.evaluate(a,b)['leaves'][1]['blockers'])
    def test_wrong_branch_fails(self):
        a,b=inputs();b['leaves'][0]['pr']['head']['ref']='lab/r02'
        self.assertIn('PR_BRANCH_BINDING_MISMATCH',mod.evaluate(a,b)['leaves'][0]['blockers'])
    def test_wrong_base_fails(self):
        a,b=inputs();b['leaves'][0]['pr']['base']['ref']='dev'
        self.assertIn('PR_BASE_BRANCH_MISMATCH',mod.evaluate(a,b)['leaves'][0]['blockers'])
    def test_unmerged_fails(self):
        a,b=inputs();b['leaves'][0]['pr']['merged']=False
        self.assertIn('PR_NOT_MERGED',mod.evaluate(a,b)['leaves'][0]['blockers'])
    def test_wrong_repo_fails(self):
        a,b=inputs();b['leaves'][0]['pr']['head']['repo']['full_name']='attacker/repo'
        self.assertIn('PR_HEAD_REPOSITORY_MISMATCH',mod.evaluate(a,b)['leaves'][0]['blockers'])
    def test_missing_leaf_rejected(self):
        a,b=inputs();b['leaves'].pop()
        with self.assertRaisesRegex(ValueError,'MISSING_LEAF'):mod.evaluate(a,b)
    def test_duplicate_leaf_rejected(self):
        a,b=inputs();b['leaves'][1]['responsibility_id']='R01'
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):mod.evaluate(a,b)
    def test_fake_green_without_runner_does_not_qualify(self):
        a,b=inputs();r=b['leaves'][0]['runs'][0];r['conclusion']='success';r['jobs'][0]['conclusion']='success'
        self.assertEqual([],mod.evaluate(a,b)['leaves'][0]['executed_acceptance_run_ids'])
    def test_real_success_step_still_not_facts(self):
        a,b=inputs();r=b['leaves'][0]['runs'][0];r['conclusion']='success';j=r['jobs'][0];j['runner_name']='GitHub Actions 42';j['conclusion']='success';j['steps']=[{'name':'Run current responsibility plus predecessors','status':'completed','conclusion':'success'}]
        x=mod.evaluate(a,b)['leaves'][0]
        self.assertEqual([1],x['executed_acceptance_run_ids'])
        self.assertFalse(x['facts_admitted']);self.assertIn('NO_INDEPENDENT_TEST_ARTIFACT_ATTESTATION',x['blockers'])
    def test_other_workflow_green_is_not_acceptance(self):
        a,b=inputs();r=b['leaves'][0]['runs'][0];r['conclusion']='success';j=r['jobs'][0];j['name']='seed-contract';j['runner_name']='runner';j['conclusion']='success';j['steps']=[{'name':'Run current responsibility plus predecessors','status':'completed','conclusion':'success'}]
        self.assertEqual([],mod.evaluate(a,b)['leaves'][0]['executed_acceptance_run_ids'])
    def test_wrong_candidate_sha_run_cannot_count(self):
        a,b=inputs();r=b['leaves'][0]['runs'][0];r['head_sha']='a'*40;r['conclusion']='success';r['jobs'][0]['runner_name']='runner'
        self.assertIn('NO_EXACT_HEAD_PRODUCT_ACTIONS',mod.evaluate(a,b)['leaves'][0]['blockers'])
    def test_no_progress_credit_under_any_case(self):
        a,b=inputs()
        self.assertTrue(all(x['progress_credit']=='NONE' for x in mod.evaluate(a,b)['leaves']))

if __name__=='__main__':unittest.main()
