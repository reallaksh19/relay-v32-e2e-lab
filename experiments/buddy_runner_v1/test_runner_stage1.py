from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from runner_stage1 import (R01_PATHS, Stage1Error, capture_start, digest,
                           seal_plan, validate_snapshot, verify_seal)


PACKET = {
    "what": ["Input ID validity not yet guaranteed"],
    "why": ["A comparison requires unique nonempty record keys"],
    "pending": ["Reconcile missing/duplicate ID behavior"],
    "known_issues": ["Duplicate IDs must fail closed"],
    "parked": ["Extra CSV dialect support out of scope"],
}
PLAN = {
    "understanding": ["R01 owns exact keyed record validity"],
    "approach": ["Use strict CSV field parsing and reject invalid keys"],
    "rejected_alternatives": ["Silently replace duplicates"],
    "assumptions": ["Existing golden fixture is authoritative for scope"],
    "questions": ["Are additional CSV dialects in scope?"],
    "next_action": "Verify missing header and empty ID before proceeding to duplicate IDs",
}


class Stage1Tests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        for path in R01_PATHS:
            p = self.repo / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("ORIGINAL START SOURCE " + path + "\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "agent start")
        self.start = self._git("rev-parse", "HEAD").strip()
        self.snapshot = self.root / "isolated"
        self.receipt = self.root / "recorder" / "sealed.json"

    def _git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def capture(self):
        return capture_start(self.repo, self.snapshot, run_id="RUN-1", expected_sha=self.start, packet=PACKET)

    def test_sealed_happy_path_and_repeat_is_rejected(self):
        m = self.capture()
        self.assertEqual("v32-buddy-stage1-v1", m["schema"])
        result = seal_plan(self.snapshot, self.receipt, PLAN)
        self.assertEqual(digest(PLAN), result["plan_digest"])
        self.assertEqual(result, verify_seal(self.snapshot, self.receipt))
        with self.assertRaisesRegex(Stage1Error, "RECEIPT_ALREADY_EXISTS"):
            seal_plan(self.snapshot, self.receipt, PLAN)

    def test_later_implementation_is_not_in_stage1(self):
        self.capture()
        path = self.repo / "src/csv_auditor/parser.py"
        path.write_text("AGENT_1_PRIVATE_IMPLEMENTATION", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "agent 1 changes")
        copied = (self.snapshot / "source" / "src/csv_auditor/parser.py").read_text()
        self.assertNotIn("PRIVATE_IMPLEMENTATION", copied)
        self.assertEqual(set(validate_snapshot(self.snapshot)["source_files"]), set(R01_PATHS))
        self.assertFalse((self.snapshot / ".git").exists())

    def test_wrong_start_sha_rejected(self):
        with self.assertRaisesRegex(Stage1Error, "START_HEAD_MISMATCH"):
            capture_start(self.repo, self.snapshot, run_id="RUN-1", expected_sha="0"*40, packet=PACKET)

    def test_dirty_start_rejected(self):
        (self.repo / "src/csv_auditor/parser.py").write_text("unsaved solution")
        with self.assertRaisesRegex(Stage1Error, "START_WORKTREE_NOT_CLEAN"):
            self.capture()

    def test_predecessor_how_or_pr_statistics_key_rejected(self):
        for secret in ("current_source_commit", "pr_stats", "implementation_how", "final_plan"):
            bad = {**PACKET, secret: "leak"}
            with self.assertRaisesRegex(Stage1Error, "STAGE1_PACKET_SCHEMA_INVALID"):
                capture_start(self.repo, self.snapshot, run_id="RUN-1", expected_sha=self.start, packet=bad)

    def test_source_tamper_or_extra_file_detected(self):
        self.capture()
        f = self.snapshot / "source" / "src/csv_auditor/parser.py"
        f.write_text("malicious replacement")
        with self.assertRaisesRegex(Stage1Error, "SNAPSHOT_SOURCE_TAMPER"):
            validate_snapshot(self.snapshot)

    def test_mismatched_receipt_rejected(self):
        self.capture()
        seal_plan(self.snapshot, self.receipt, PLAN)
        payload = json.loads(self.receipt.read_text())
        payload["independent_plan"]["next_action"] = "use predecessor solution"
        self.receipt.write_text(json.dumps(payload))
        with self.assertRaisesRegex(Stage1Error, "SEAL_BASIS_MISMATCH"):
            verify_seal(self.snapshot, self.receipt)

    def test_snapshot_manifest_tamper_rejected_by_seal(self):
        self.capture()
        payload = json.loads((self.snapshot / "manifest.json").read_text())
        payload["source_files"]["src/csv_auditor/parser.py"] = "sha256:" + "f"*64
        (self.snapshot / "manifest.json").write_text(json.dumps(payload))
        with self.assertRaisesRegex(Stage1Error, "SNAPSHOT_SOURCE_TAMPER"):
            seal_plan(self.snapshot, self.receipt, PLAN)

    def test_path_traversal_and_unapproved_allowlist_rejected(self):
        from runner_stage1 import checked_path
        for p in ("../secret", "/tmp/file", "foo/../bar", "foo\\bar"):
            with self.assertRaises(Stage1Error):
                checked_path(p)
        with self.assertRaisesRegex(Stage1Error, "UNRELEASED_SOURCE_ALLOWLIST"):
            capture_start(self.repo, self.snapshot, run_id="RUN-1", expected_sha=self.start,
                          packet=PACKET, paths=("src/csv_auditor/parser.py",))

    def test_unapproved_origin_stage1_has_no_live_repo_access(self):
        self.capture()
        files = list(self.snapshot.rglob("*"))
        self.assertFalse(any(p.name in (".git", ".env", "gh-auth.json") for p in files))
        self.assertEqual({p.relative_to(self.snapshot/"source").as_posix() for p in (self.snapshot/"source").rglob("*") if p.is_file()}, set(R01_PATHS))


if __name__ == "__main__":
    unittest.main()
