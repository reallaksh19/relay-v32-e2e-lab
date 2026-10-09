"""Fail closed without real container sandbox; reject source and custody leaks."""
from __future__ import annotations
import unittest
from unittest.mock import patch
import test_runner_stage1 as seed
from runner_protocol import activate
from runner_stage1 import Stage1Error
from isolated_runner import build_command, launch

IMAGE = "registry.example.org/blind-runner@sha256:" + "a" * 64


class IsolationTests(unittest.TestCase):
    _git = seed.Stage1Tests._git
    capture = seed.Stage1Tests.capture

    def setUp(self):
        seed.Stage1Tests.setUp(self)
        self.capture()
        activate(self.snapshot, seed.PACKET)
        self.output = self.root / "runner-output"
        self.output.mkdir()

    def command(self, **kw):
        return build_command(self.snapshot, self.output, image=IMAGE, approved_image=IMAGE, **kw)

    def test_fixed_isolation_flags_and_allowlist(self):
        c = self.command()
        for key in ("--network", "none", "--read-only", "--cap-drop", "ALL",
                    "--pids-limit", "64", "--memory", "512m", "--pull", "never"):
            self.assertIn(key, c)
        self.assertEqual("docker", c[0])
        self.assertEqual(IMAGE, c[-1])
        self.assertFalse(any("GITHUB_TOKEN" in a or "HOME=" in a for a in c))
        self.assertEqual(2, sum("type=bind" in arg for arg in c))

    def test_absent_sandbox_binary_does_not_fallback(self):
        with patch("isolated_runner.shutil.which", return_value=None):
            with self.assertRaisesRegex(Stage1Error, "NO_FALLBACK"):
                launch(self.snapshot, self.output, image=IMAGE, approved_image=IMAGE)

    def test_extra_file_in_snapshot_denied(self):
        (self.snapshot / "private-note.txt").write_text("future implementation leaked")
        with self.assertRaisesRegex(Stage1Error, "RUNNER_EXTRA_SNAPSHOT_CONTENT"):
            self.command()

    def test_sealed_plan_receipt_inside_snapshot_denied(self):
        (self.snapshot / "seal.json").write_text('{"secret":"should not see"}')
        with self.assertRaisesRegex(Stage1Error, "RUNNER_EXTRA_SNAPSHOT_CONTENT"):
            self.command()

    def test_source_symlink_denied(self):
        dest = self.snapshot / "source/src/csv_auditor/parser.py"
        dest.unlink()
        dest.symlink_to(self.root / "repo/src/csv_auditor/parser.py")
        with self.assertRaises(Stage1Error):
            self.command()

    def test_unapproved_image_denied(self):
        with self.assertRaisesRegex(Stage1Error, "NOT_OWNER_APPROVED"):
            build_command(self.snapshot, self.output, image=IMAGE,
                          approved_image="registry.example.org/blind-runner@sha256:"+"b"*64)

    def test_unpinned_image_denied(self):
        with self.assertRaisesRegex(Stage1Error, "NOT_DIGEST_PINNED"):
            build_command(self.snapshot, self.output, image="latest", approved_image="latest")

    def test_output_cannot_contain_existing_files(self):
        (self.output / "old-credentials.txt").write_text("existing secret")
        with self.assertRaisesRegex(Stage1Error, "RUNNER_OUTPUT_NOT_EMPTY"):
            self.command()

    def test_output_cannot_overlap_input(self):
        with self.assertRaisesRegex(Stage1Error, "RUNNER_OUTPUT_OVERLAPS_SOURCE"):
            build_command(self.snapshot, self.snapshot, image=IMAGE, approved_image=IMAGE)

    def test_output_invalid_symlink_denied(self):
        self.output.rmdir()
        self.output.symlink_to(self.root)
        with self.assertRaisesRegex(Stage1Error, "RUNNER_OUTPUT_NOT_DIRECTORY"):
            self.command()

    def test_invalid_time_budget(self):
        with self.assertRaisesRegex(Stage1Error, "RUNNER_TIMEOUT_INVALID"):
            launch(self.snapshot, self.output, image=IMAGE, approved_image=IMAGE, timeout=0)


if __name__ == "__main__":
    unittest.main()
