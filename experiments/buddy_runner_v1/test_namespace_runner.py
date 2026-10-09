"""Real user/mount/network namespaces where OS permits; fail-closed otherwise."""
from __future__ import annotations
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
import test_runner_stage1 as base
from runner_protocol import activate
from runner_stage1 import Stage1Error
from namespace_runner import run_fixture

class NamespaceRunnerTests(unittest.TestCase):
    _git = base.Stage1Tests._git
    capture = base.Stage1Tests.capture
    def setUp(self):
        base.Stage1Tests.setUp(self)
        self.capture()
        activate(self.snapshot, base.PACKET)
        self.out = self.root / 'new-output'; self.out.mkdir()
        self.chroot = self.root / 'new-root'; self.chroot.mkdir()
        self.program = Path(__file__).with_name('ns_fixture_runner.py')
        self.entry = Path(__file__).with_name('ns_entry.sh')
    @staticmethod
    def sha(p):return 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()
    def call(self, **kw):
        return run_fixture(self.snapshot,self.out,self.chroot,
            runner_program=self.program,approved_program_digest=self.sha(self.program),
            entry_script=self.entry,approved_entry_digest=self.sha(self.entry),**kw)

    def test_real_namespaced_source_only_and_network_denial(self):
        result=self.call()
        self.assertEqual('ISOLATED_FIXTURE_EXECUTED',result['status'])
        self.assertEqual('NOT_EXECUTED',result['llm_agent'])
        self.assertEqual('NOT_GRANTED',result['execution_authority'])
        self.assertTrue((self.out/'fixture_result.json').is_file())
        self.assertFalse(any(self.chroot.iterdir()))

    def test_wrong_program_digest_rejected(self):
        with self.assertRaisesRegex(Stage1Error,'NOT_APPROVED'):
            run_fixture(self.snapshot,self.out,self.chroot,
                runner_program=self.program,approved_program_digest='sha256:'+'0'*64,
                entry_script=self.entry,approved_entry_digest=self.sha(self.entry))

    def test_no_namespace_toolchain_fails_closed(self):
        with patch('namespace_runner.shutil.which',return_value=None):
            with self.assertRaisesRegex(Stage1Error,'NO_FALLBACK'):
                self.call()

    def test_dirty_snapshot_denied(self):
        (self.snapshot/'current_agent_plan.txt').write_text('forbidden')
        with self.assertRaisesRegex(Stage1Error,'RUNNER_EXTRA_SNAPSHOT_CONTENT'):
            self.call()

    def test_output_reuse_denied(self):
        (self.out/'fixture_result.json').write_text('other')
        with self.assertRaisesRegex(Stage1Error,'NAMESPACE_OUTPUT_NOT_EMPTY'):
            self.call()

    def test_root_output_overlap_denied(self):
        with self.assertRaisesRegex(Stage1Error,'NAMESPACE_PATH_OVERLAP'):
            run_fixture(self.snapshot,self.out,self.out,
                runner_program=self.program,approved_program_digest=self.sha(self.program),
                entry_script=self.entry,approved_entry_digest=self.sha(self.entry))
