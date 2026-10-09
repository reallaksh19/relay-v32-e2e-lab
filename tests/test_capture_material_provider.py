import importlib.util
import copy
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('capture',Path(__file__).resolve().parents[1]/'scripts'/'capture_material_provider.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REPO='reallaksh19/relay-v32-e2e-lab'

def fixture():
    g={'programme':{'repository':REPO},'nodes':[{'kind':'LEAF','responsibility_id':'R01','primary_pr':f'{REPO}#8'}]}
    pr={'number':8,'head':{'sha':'a'*40,'ref':'lab/r01','repo':{'full_name':REPO}},'base':{'ref':'main','sha':'b'*40,'repo':{'full_name':REPO}},'merged':True}
    run={'id':55,'head_sha':'a'*40,'event':'pull_request','conclusion':'failure','status':'completed'}
    jobs={'total_count':1,'jobs':[{'id':9,'name':'responsibility-acceptance','status':'completed','conclusion':'failure','runner_name':'','steps':[]}]}
    payloads={f'repos/{REPO}/pulls/8':pr,f'repos/{REPO}/actions/runs?head_sha={'a'*40}&per_page=100':{'total_count':1,'workflow_runs':[run]},f'repos/{REPO}/actions/runs/55/jobs?per_page=100':jobs}
    return g,payloads

class CaptureTests(unittest.TestCase):
    def test_read_only_capture_retains_failed_job(self):
        graph,payload=fixture();self.assertEqual('',mod.capture(graph,payload.__getitem__)['leaves'][0]['runs'][0]['jobs'][0]['runner_name'])
    def test_no_pr_bound(self):
        g,p=fixture();g['nodes'][0].pop('primary_pr')
        with self.assertRaisesRegex(ValueError,'BOUND'):mod.capture(g,p.__getitem__)
    def test_wrong_pr(self):
        g,p=fixture();p[f'repos/{REPO}/pulls/8']['number']=7
        with self.assertRaisesRegex(ValueError,'PR_NUMBER'):mod.capture(g,p.__getitem__)
    def test_no_pagination_guess(self):
        g,p=fixture();p[f'repos/{REPO}/actions/runs?head_sha={'a'*40}&per_page=100']['total_count']=101
        with self.assertRaisesRegex(ValueError,'PAGINATION'):mod.capture(g,p.__getitem__)
    def test_job_pagination_rejected(self):
        g,p=fixture();p[f'repos/{REPO}/actions/runs/55/jobs?per_page=100']['total_count']=101
        with self.assertRaisesRegex(ValueError,'JOBS_PAGINATION'):mod.capture(g,p.__getitem__)
    def test_unexpected_runs_rejected_when_truncated(self):
        g,p=fixture();run=p[f'repos/{REPO}/actions/runs?head_sha={'a'*40}&per_page=100']['workflow_runs'][0];p[f'repos/{REPO}/actions/runs?head_sha={'a'*40}&per_page=100']['workflow_runs']=[run,copy.deepcopy(run)]
        with self.assertRaisesRegex(ValueError,'TRUNCATED'):mod.capture(g,p.__getitem__,max_runs=1)
    def test_moving_head_rejected(self):
        g,p=fixture();count=[0];old=p[f'repos/{REPO}/pulls/8']
        def getter(endpoint):
            if endpoint.endswith('/pulls/8'):
                count[0]+=1
                if count[0]==2:
                    newer=copy.deepcopy(old);newer['head']['sha']='c'*40;return newer
            return p[endpoint]
        with self.assertRaisesRegex(ValueError,'CHANGED_DURING_OBSERVATION'):mod.capture(g,getter)

if __name__=='__main__':unittest.main()
