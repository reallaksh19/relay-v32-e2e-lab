from __future__ import annotations

import json
import unittest

from runner_stage1 import Stage1Error
from runner_protocol import activate, seal_activated_plan
from stage2_reconcile import reconcile
import test_runner_stage1 as base

PACKET, PLAN = base.PACKET, base.PLAN
INCUMBENT = {
    "approach": ["Validate ID inputs at the reader"],
    "pending": ["Exact-head oracle"],
    "next_action": "Check duplicate ID behavior",
    "source_claims": ["Input correctness addressed"],
}
DECISIONS = {
    "agreements": [{"finding": "Input validity", "why": "Required by contract",
                    "evidence_refs": ["acceptance/test_r01_input.py"]}],
    "agent1_stronger": [], "runner_stronger": [], "unresolved": [],
    "high_roi_in_scope": [], "medium_roi_parked": [],
    "next_action": "Inspect current parser and run exact-head golden tests",
    "owner_scope_change": "NONE",
}


class Stage2Tests(unittest.TestCase):
    def _git(self, *args):
        return base.Stage1Tests._git(self, *args)

    def capture(self):
        return base.Stage1Tests.capture(self)

    def setUp(self):
        base.Stage1Tests.setUp(self)
        self.capture()
        activate(self.snapshot, PACKET)
        self.gate = self.root / "recorder" / "gate.json"
        seal_activated_plan(self.snapshot, self.receipt, self.gate, PLAN)
        self.report = self.root / "recorder" / "reconciled.json"

    def state(self, decisions=DECISIONS, plan=INCUMBENT, head=None):
        return reconcile(self.snapshot, self.receipt, self.gate, self.repo,
                         head or self._git("rev-parse", "HEAD").strip(),
                         plan, decisions, self.report)

    def test_read_only_reconciliation_binds_independent_plan_and_source(self):
        path = self.repo / "src/csv_auditor/parser.py"
        path.write_text("incumbent implementation")
        self._git("add", ".")
        self._git("commit", "-qm", "incumbent change")
        out = self.state()
        self.assertEqual(["src/csv_auditor/parser.py"], out["source_observation"]["changed_paths"])
        self.assertEqual([], out["source_observation"]["unexpected_paths"])
        self.assertEqual(PLAN, out["independent_plan"])
        self.assertEqual("NOT_GRANTED", out["execution_authority"])
        self.assertIn("PROVIDER_PR_CI_UNKNOWN", out["unresolved"])
        self.assertEqual("NOT_ATTEMPTED", out["github_issue_update"])
        with self.assertRaisesRegex(Stage1Error, "RECEIPT_ALREADY_EXISTS"):
            self.state()

    def test_stale_head_fails_closed(self):
        path = self.repo / "src/csv_auditor/parser.py"
        path.write_text("new code")
        self._git("add", ".")
        self._git("commit", "-qm", "new head")
        with self.assertRaisesRegex(Stage1Error, "STAGE2_CANDIDATE_MOVED"):
            self.state(head=self.start)
        self.assertFalse(self.report.exists())

    def test_dirty_inflight_edits_refused(self):
        (self.repo / "src/csv_auditor/parser.py").write_text("uncommitted")
        with self.assertRaisesRegex(Stage1Error, "UNRESOLVED_INFLIGHT_WRITES"):
            self.state()
        self.assertFalse(self.report.exists())

    def test_unrelated_edited_path_creates_scope_drift(self):
        (self.repo / "governance/owner-intent.md").write_text("unauthorized update")
        self._git("add", ".")
        self._git("commit", "-qm", "unexpected")
        out = self.state()
        self.assertIn("governance/owner-intent.md", out["source_observation"]["unexpected_paths"])
        self.assertIn("SCOPE_DRIFT_REQUIRES_OWNER_PLAN_RECONCILIATION", out["unresolved"])

    def test_missing_seal_fails_before_current_source_access(self):
        self.gate.unlink()
        with self.assertRaisesRegex(Stage1Error, "SEALED_GATE_MISSING"):
            self.state()
        self.assertFalse(self.report.exists())

    def test_replaced_independent_plan_detected(self):
        receipt = json.loads(self.receipt.read_text())
        receipt["independent_plan"]["next_action"] = "copy incumbent"
        self.receipt.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(Stage1Error, "SEAL_BASIS_MISMATCH"):
            self.state()

    def test_unresolved_disagreement_and_roi_no_auto_scope(self):
        decisions = {**DECISIONS, "unresolved": [{"finding": "Missing acceptance proof",
                        "why": "Only candidate code observed", "evidence_refs": ["fixture:R01"]}],
                     "medium_roi_parked": [{"finding": "Extra CSV encoding support",
                        "why": "Outside released claim", "evidence_refs": ["plan:R01"]}],
                     "owner_scope_change": "OWNER_DECISION_REQUIRED"}
        out = self.state(decisions=decisions)
        self.assertIn("UNRESOLVED_PLAN_DISAGREEMENT", out["unresolved"])
        self.assertIn("OWNER_AUTHORIZATION_REQUIRED", out["unresolved"])
        self.assertEqual("NOT_GRANTED", out["execution_authority"])

    def test_missing_decision_evidence_is_rejected(self):
        decisions = {**DECISIONS, "agreements": [{"finding": "looks good", "why": "intuition", "evidence_refs": []}]}
        with self.assertRaisesRegex(Stage1Error, "RECONCILIATION_EVIDENCE_REQUIRED"):
            self.state(decisions=decisions)

    def test_new_untracked_file_is_inflight(self):
        (self.repo / "notes.txt").write_text("possible unfinished write")
        with self.assertRaisesRegex(Stage1Error, "UNRESOLVED_INFLIGHT_WRITES"):
            self.state()

    def test_report_inside_repo_rejected(self):
        with self.assertRaisesRegex(Stage1Error, "STAGE2_REPORT_INSIDE_SOURCE_REPO"):
            reconcile(self.snapshot, self.receipt, self.gate, self.repo,
                      self._git("rev-parse", "HEAD").strip(), INCUMBENT, DECISIONS,
                      self.repo / "would-change-worktree.json")

    def test_predecessor_plan_invalid(self):
        with self.assertRaisesRegex(Stage1Error, "INCUMBENT_HANDOVER_SCHEMA_INVALID"):
            self.state(plan={"current_pr": "7"})


if __name__ == "__main__":
    unittest.main()
