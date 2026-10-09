import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('receipt',HERE/'scripts'/'exact_source_test_receipt.py')
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
MANIFEST=json.loads((HERE/'evidence'/'COMMITTED_ACCEPTANCE_BLOBS_V1.json').read_text())
SOURCE=HERE

class EvidenceReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name in gate.EXPECTED_FILES:
            f=self.root/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE/name,f)
        self.m=copy.deepcopy(MANIFEST)
    def test_committed_source_manifest_clean(self):
        self.assertEqual(7,len(gate.check_manifest(self.root,self.m)))
    def test_nine_actual_source_bound_tests(self):
        r=gate.execute(self.root,self.m)
        self.assertEqual(9,r['committed_goldens_run'])
        self.assertEqual([4,3,2],[x['actual_tests_run'] for x in r['tests']])
        self.assertFalse(r['checkpoint_facts_admitted']);self.assertEqual('NONE',r['progress_credit'])
    def test_actual_source_edit_fails_before_test(self):
        p=self.root/'src/csv_auditor/cli.py';p.write_text(p.read_text()+'\n# tamper\n')
        with self.assertRaisesRegex(ValueError,'BLOB_MISMATCH'):gate.execute(self.root,self.m)
    def test_test_oracle_edit_fails(self):
        p=self.root/'acceptance/test_r01_input.py';p.write_text('def fake(): return True')
        with self.assertRaisesRegex(ValueError,'BLOB_MISMATCH'):gate.execute(self.root,self.m)
    def test_wrong_committed_blob_reference_fails(self):
        self.m['blobs']['src/csv_auditor/parser.py']='0'*40
        with self.assertRaisesRegex(ValueError,'BLOB_MISMATCH'):gate.execute(self.root,self.m)
    def test_missing_source_file_fails(self):
        (self.root/'src/csv_auditor/compare.py').unlink()
        with self.assertRaisesRegex(ValueError,'UNSAFE_OR_MISSING'):gate.execute(self.root,self.m)
    def test_symlink_source_refuses_external(self):
        path=self.root/'src/csv_auditor/parser.py';path.unlink();path.symlink_to(SOURCE/'src/csv_auditor/parser.py')
        with self.assertRaisesRegex(ValueError,'UNSAFE_OR_MISSING'):gate.execute(self.root,self.m)
    def test_manifest_add_extra_file_fails(self):
        self.m['blobs']['acceptance/unreleased_test.py']='f'*40
        with self.assertRaisesRegex(ValueError,'FILE_SET'):gate.execute(self.root,self.m)
    def test_missing_test_not_silently_skipped(self):
        self.m['blobs'].pop('acceptance/test_r03_cli.py')
        with self.assertRaisesRegex(ValueError,'FILE_SET'):gate.execute(self.root,self.m)
    def test_wrong_repository_fails(self):
        self.m['repository']='stranger/repo'
        with self.assertRaisesRegex(ValueError,'WRONG_REPOSITORY'):gate.execute(self.root,self.m)
    def test_false_zero_test_green_is_rejected(self):
        def fake_run(*a,**k):
            return subprocess.CompletedProcess(a[0],0,stdout='',stderr='\nRan 0 tests in 0.001s\n\nOK\n')
        with self.assertRaisesRegex(ValueError,'COLLECTION_FAILED'):gate.execute(self.root,self.m,runner=fake_run)
    def test_wrong_test_class_green_rejected(self):
        def fake_run(*a,**k):
            return subprocess.CompletedProcess(a[0],0,stdout='',stderr='test_a (test_r01_input.Fake.test_a) ... ok\nRan 4 tests in 0.010s\n\nOK')
        with self.assertRaisesRegex(ValueError,'COLLECTION_FAILED'):gate.execute(self.root,self.m,runner=fake_run)
    def test_forged_green_on_nonzero_exit_rejected(self):
        def fake_run(*a,**k):
            return subprocess.CompletedProcess(a[0],1,stdout='',stderr='Ran 4 tests in 0.01s\nOK')
        with self.assertRaisesRegex(ValueError,'COLLECTION_FAILED'):gate.execute(self.root,self.m,runner=fake_run)
    def test_missing_base_sha_rejected(self):
        self.m['base_main_sha']='UNVERIFIED'
        with self.assertRaisesRegex(ValueError,'BASE_COMMIT'):gate.execute(self.root,self.m)

if __name__=='__main__':unittest.main()
