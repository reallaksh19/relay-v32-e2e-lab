import pathlib, sys, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import bootstrap_issues as bootstrap

class OwnerApprovalGateTests(unittest.TestCase):
    def setUp(self):
        self.repo='reallaksh19/relay-v32-e2e-lab'
        self.digest='sha256:'+'c'*64
        self.sha='a'*40
        self.exact=f'APPROVE_LAB_PROPOSAL_V2 digest={self.digest} source_sha={self.sha}'
    def decision(self, author, body):
        row={'id':101,'html_url':'https://github.com/reallaksh19/relay-v32-e2e-lab/issues/1#issuecomment-101',
             'user':{'login':author},'body':body}
        with patch.object(bootstrap,'api',return_value=[row]):
            return bootstrap.owner_decision(self.repo,1,self.digest,self.sha)
    def test_author_is_provider_observed_repo_owner_not_issue_text(self):
        with self.assertRaisesRegex(RuntimeError,'OWNER_APPROVAL_REQUIRED'):
            self.decision('driveby',self.exact)
    def test_no_approval_on_wrong_digest(self):
        with self.assertRaisesRegex(RuntimeError,'OWNER_APPROVAL_REQUIRED'):
            self.decision('reallaksh19',self.exact.replace('c'*64,'b'*64))
    def test_no_approval_on_wrong_pinned_commit(self):
        with self.assertRaisesRegex(RuntimeError,'OWNER_APPROVAL_REQUIRED'):
            self.decision('reallaksh19',self.exact.replace('a'*40,'b'*40))
    def test_exact_owner_comment_qualifies_only_the_human_decision_boundary(self):
        r=self.decision('reallaksh19',self.exact)
        self.assertEqual(101,r['comment_id'])
        self.assertEqual(self.digest,r['proposal_digest'])
        self.assertEqual(self.sha,r['proposal_sha'])
    def test_duplicate_matching_owner_approvals_are_ambiguous(self):
        row={'id':101,'html_url':'https://github.com/x/y/issues/1#issuecomment-101','user':{'login':'reallaksh19'},'body':self.exact}
        with patch.object(bootstrap,'api',return_value=[row,{**row,'id':102}]):
            with self.assertRaisesRegex(RuntimeError,'OWNER_APPROVAL_REQUIRED'):
                bootstrap.owner_decision(self.repo,1,self.digest,self.sha)
