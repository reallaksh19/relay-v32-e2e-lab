import pathlib,sys,json,unittest,hashlib
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'stress'))
import verdict

class VerdictGuardTests(unittest.TestCase):
    def setUp(self):
        self.matrix=json.loads((ROOT/'stress/scenarios.json').read_text())
        self.template=json.loads((ROOT/'stress/scenario-results.template.json').read_text())
    def test_initial_live_matrix_is_not_qualified(self):
        result=verdict.evaluate(self.matrix,self.template,live=False,repo='reallaksh19/relay-v32-e2e-lab')
        self.assertNotEqual('E2E_PASS_WITH_PROVIDER_READBACK',result['status'])
        self.assertGreaterEqual(len(result['errors']),15)
    def test_forged_all_green_json_without_provider_readback_cannot_pass(self):
        fake=json.loads(json.dumps(self.template))
        for row in fake['scenarios']:
            row.update(status='PASS',source_sha='a'*40,run_refs=['https://github.com/reallaksh19/relay-v32-e2e-lab/actions/runs/123'],executor_login='agent')
            row['independent_reviewer']={'login':'reviewer','comment_url':'https://github.com/reallaksh19/relay-v32-e2e-lab/issues/1#issuecomment-123'}
        result=verdict.evaluate(self.matrix,fake,live=False,repo='reallaksh19/relay-v32-e2e-lab')
        self.assertIn('LIVE_PROVIDER_READBACK_REQUIRED',result['errors'])
    def test_duplicated_scenario_ids_rejected(self):
        bad=json.loads(json.dumps(self.template));bad['scenarios'][-1]['id']='S01'
        result=verdict.evaluate(self.matrix,bad,live=False,repo='reallaksh19/relay-v32-e2e-lab')
        self.assertIn('MISSING_OR_DUPLICATE_SCENARIO_IDS',result['errors'])

class LiveReadbackRegressionTests(unittest.TestCase):
    """Single-scenario oracle: a completed failing CI run must never qualify."""
    repo='reallaksh19/relay-v32-e2e-lab'
    sha='b'*40
    def specimen(self):
        matrix={'scenarios':[{'id':'S01','expect':'expected functionality'}]}
        row={
            'id':'S01','status':'PASS','source_sha':self.sha,
            'run_refs':[f'https://github.com/{self.repo}/actions/runs/123'],
            'executor_login':'agent','expected':'expected functionality',
            'observed':'independent product observation',
            'independent_reviewer':{'login':'reviewer','comment_url':f'https://github.com/{self.repo}/issues/5#issuecomment-9'},
        }
        digest=hashlib.sha256(json.dumps({k:row[k] for k in ('id','expected','observed','source_sha','run_refs')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        comment={'user':{'login':'reviewer'},'issue_url':f'https://api.github.com/repos/{self.repo}/issues/5',
                 'body':f'LAB_VERDICT S01 PASS result_digest={digest}'}
        run={'repository':{'full_name':self.repo},'head_sha':self.sha,'status':'completed','conclusion':'success'}
        return matrix,{'scenarios':[row]},comment,run

    def exercise(self,run_change=None,comment_change=None):
        matrix,observed,comment,run=self.specimen()
        if run_change: run.update(run_change)
        if comment_change: comment.update(comment_change)
        def get(ref):
            return comment if '/issues/comments/' in ref else run
        with patch.object(verdict,'gh',side_effect=get):
            return verdict.evaluate(matrix,observed,live=True,repo=self.repo)

    def test_genuine_completed_success_with_matching_issue_comment_can_qualify_one_case(self):
        self.assertEqual('E2E_PASS_WITH_PROVIDER_READBACK',self.exercise()['status'])

    def test_completed_failure_is_not_treated_as_success(self):
        self.assertIn('S01:RUN_REPO_HEAD_OR_SUCCESS_MISMATCH',self.exercise(run_change={'conclusion':'failure'})['errors'])

    def test_completed_cancelled_is_not_treated_as_success(self):
        self.assertIn('S01:RUN_REPO_HEAD_OR_SUCCESS_MISMATCH',self.exercise(run_change={'conclusion':'cancelled'})['errors'])

    def test_foreign_repository_run_is_rejected(self):
        self.assertIn('S01:RUN_REPO_HEAD_OR_SUCCESS_MISMATCH',self.exercise(run_change={'repository':{'full_name':'other/lab'}})['errors'])

    def test_wrong_issue_comment_origin_is_rejected(self):
        self.assertIn('S01:REVIEWER_PROVIDER_MISMATCH',self.exercise(comment_change={'issue_url':f'https://api.github.com/repos/{self.repo}/issues/7'})['errors'])
