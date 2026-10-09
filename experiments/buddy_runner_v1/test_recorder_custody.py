"""BR-06 ordered recorder tests: replay, forged, rollback, cross-run controls."""
from __future__ import annotations
import json
import unittest

import test_runner_stage1 as seed
from runner_stage1 import Stage1Error, capture_start
from runner_protocol import activate, seal_activated_plan
from runner_readiness import assess, render_task_evidence
from recorder_custody import append, verify_events, verify_journal, validate_disclosure

KEY = bytes.fromhex("b3" * 32)  # TEST ONLY: never a real recorder credential.
PACKET, PLAN = seed.PACKET, seed.PLAN


class CustodyTests(unittest.TestCase):
    _git = seed.Stage1Tests._git
    capture = seed.Stage1Tests.capture

    def setUp(self):
        seed.Stage1Tests.setUp(self)
        self.capture()
        self.journal = self.root / "recorder" / "events.jsonl"
        self.receipt = self.root / "recorder" / "runner.json"
        self.gate = self.root / "recorder" / "gate.json"
        self.disclosure = {
            "run_id": "RUN-1", "candidate_sha": self.start,
            "incumbent_plan_digest": "sha256:" + "2" * 64,
            "source_context_digest": "sha256:" + "3" * 64,
        }
        self.begin = append(self.journal, KEY, "START_PINNED", self.snapshot)

    def _request(self):
        observed = {
            "run_id": "RUN-1", "responsibility": "reallaksh19/relay-v32-e2e-lab#4",
            "candidate_sha": self.start,
            "source_kind": "AGENT_SELF_ESTIMATE", "used_context_tokens": None,
            "usable_context_tokens": None, "episode_consumed_percent": 71,
            "next_unit_demand_tokens": None, "safety_reserve_tokens": None,
            "cognitive_warning": "NONE", "interruption_risk": "NONE",
            "agent_requests_runner": False, "confidence": "LOW",
        }
        activate(self.snapshot, PACKET, readiness_evidence=render_task_evidence(assess(observed)))
        return append(self.journal, KEY, "RUNNER_REQUESTED", self.snapshot,
                      expected_last_mac=self.begin["mac"])

    def _seal(self):
        request = self._request()
        seal_activated_plan(self.snapshot, self.receipt, self.gate, PLAN)
        return append(self.journal, KEY, "PLAN_SEALED", self.snapshot,
                      receipt=self.receipt, gate=self.gate, expected_last_mac=request["mac"])

    def test_nominal_order_and_stage2_gate(self):
        sealed = self._seal()
        with self.assertRaisesRegex(Stage1Error, "RECORDER_DISCLOSURE_NOT_OPEN"):
            validate_disclosure(self.journal, KEY, self.snapshot, self.receipt,
                                self.gate, self.disclosure)
        end = append(self.journal, KEY, "STAGE2_DISCLOSED", self.snapshot,
                     receipt=self.receipt, gate=self.gate, disclosure=self.disclosure,
                     expected_last_mac=sealed["mac"])
        state = validate_disclosure(self.journal, KEY, self.snapshot,
                                    self.receipt, self.gate, self.disclosure,
                                    external_anchor=end["mac"])
        self.assertEqual(4, state["events"])
        self.assertTrue(state["external_anchor_checked"])
        self.assertEqual("NOT_GRANTED", state["execution_authority"])
        self.assertEqual("NOT_PROVEN_BY_LOCAL_JOURNAL", state["trusted_temporal_custody"])

    def test_reject_seal_before_request(self):
        with self.assertRaises(Stage1Error):
            append(self.journal, KEY, "PLAN_SEALED", self.snapshot,
                   receipt=self.receipt, gate=self.gate)

    def test_duplicate_and_out_of_order_events_rejected(self):
        self._request()
        with self.assertRaisesRegex(Stage1Error, "RECORDER_TRANSITION_REJECTED"):
            append(self.journal, KEY, "RUNNER_REQUESTED", self.snapshot)

    def test_unverified_legacy_signal_cannot_count(self):
        activate(self.snapshot, PACKET)
        with self.assertRaisesRegex(Stage1Error, "RECORDER_RUNNER_SIGNAL_NOT_BOUND"):
            append(self.journal, KEY, "RUNNER_REQUESTED", self.snapshot)

    def test_journal_tampering_detected(self):
        self._request()
        self.journal.write_text(self.journal.read_text().replace("RUNNER_REQUESTED", "PLAN_SEALED"))
        with self.assertRaises(Stage1Error):
            verify_journal(self.journal, KEY)

    def test_mac_forgery_detected(self):
        rows = [json.loads(x) for x in self.journal.read_text().splitlines()]
        rows[0]["basis"]["initial_commit"] = "c" * 40
        with self.assertRaisesRegex(Stage1Error, "RECORDER_MAC_INVALID"):
            verify_events(rows, KEY)

    def test_external_anchor_refuses_rollback(self):
        sealed = self._seal()
        truncated = self.journal.read_text().splitlines()[:2]
        self.journal.write_text("\n".join(truncated) + "\n")
        with self.assertRaisesRegex(Stage1Error, "EXTERNAL_ANCHOR_MISMATCH"):
            verify_journal(self.journal, KEY, anchor=sealed["mac"])

    def test_wrong_recorder_key_detected(self):
        with self.assertRaisesRegex(Stage1Error, "RECORDER_MAC_INVALID"):
            verify_journal(self.journal, bytes.fromhex("a1" * 32))

    def test_cross_run_rejected(self):
        self._request()
        other = self.root / "other-snapshot"
        capture_start(self.repo, other, run_id="RUN-2", expected_sha=self.start, packet=PACKET)
        observed = {
            "run_id": "RUN-2", "responsibility": "reallaksh19/relay-v32-e2e-lab#4",
            "candidate_sha": self.start, "source_kind": "AGENT_SELF_ESTIMATE",
            "used_context_tokens": None, "usable_context_tokens": None,
            "episode_consumed_percent": 71, "next_unit_demand_tokens": None,
            "safety_reserve_tokens": None, "cognitive_warning": "NONE",
            "interruption_risk": "NONE", "agent_requests_runner": False,
            "confidence": "LOW",
        }
        activate(other, PACKET, readiness_evidence=render_task_evidence(assess(observed)))
        other_receipt = self.root / "recorder" / "other-plan.json"
        other_gate = self.root / "recorder" / "other-gate.json"
        seal_activated_plan(other, other_receipt, other_gate, PLAN)
        with self.assertRaisesRegex(Stage1Error, "RECORDER_RUN_MISMATCH"):
            append(self.journal, KEY, "PLAN_SEALED", other,
                   receipt=other_receipt, gate=other_gate)

    def test_stage2_payload_mismatch_detected(self):
        sealed = self._seal()
        append(self.journal, KEY, "STAGE2_DISCLOSED", self.snapshot,
               receipt=self.receipt, gate=self.gate, disclosure=self.disclosure,
               expected_last_mac=sealed["mac"])
        changed = {**self.disclosure, "candidate_sha": "0" * 40}
        with self.assertRaisesRegex(Stage1Error, "RECORDER_DISCLOSURE_NOT_BOUND"):
            validate_disclosure(self.journal, KEY, self.snapshot, self.receipt,
                                self.gate, changed)

    def test_source_rewrite_invalidates_later_sequence(self):
        self._request()
        path = self.snapshot / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["origin"]["initial_commit"] = "0" * 40
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(Stage1Error, "ACTIVATION_SOURCE_MISMATCH"):
            append(self.journal, KEY, "PLAN_SEALED", self.snapshot,
                   receipt=self.receipt, gate=self.gate)

    def test_truncated_journal_fail_closed(self):
        self.journal.write_bytes(self.journal.read_bytes()[:-1])
        with self.assertRaisesRegex(Stage1Error, "RECORDER_JOURNAL_TRUNCATED"):
            verify_journal(self.journal, KEY)


if __name__ == "__main__":
    unittest.main()
