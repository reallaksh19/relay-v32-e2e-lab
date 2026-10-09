"""Readiness → blind Stage 1 activation: no accidental PR/head disclosure."""
from __future__ import annotations
import json
import unittest

from runner_protocol import activate, verify_activation, seal_activated_plan, verify_gate
from runner_readiness import assess, render_task_evidence
from runner_stage1 import Stage1Error
import test_runner_stage1 as base

PACKET = base.PACKET
PLAN = base.PLAN

class ReadinessActivationTests(unittest.TestCase):
    _git = base.Stage1Tests._git
    capture = base.Stage1Tests.capture

    def setUp(self):
        base.Stage1Tests.setUp(self)
        self.capture()
        self.gate = self.root / "recorder" / "signal-gate.json"

    def observation(self, **changed):
        return {
            "run_id": "RUN-1",
            "responsibility": "reallaksh19/relay-v32-e2e-lab#4",
            "candidate_sha": "f" * 40,
            "source_kind": "AGENT_SELF_ESTIMATE",
            "used_context_tokens": None,
            "usable_context_tokens": None,
            "episode_consumed_percent": 72,
            "next_unit_demand_tokens": None,
            "safety_reserve_tokens": None,
            "cognitive_warning": "NONE",
            "interruption_risk": "NONE",
            "agent_requests_runner": False,
            "confidence": "LOW",
            **changed,
        }

    def evidence(self, **changed):
        return render_task_evidence(assess(self.observation(**changed)))

    def test_proper_time_for_runner_activates_and_seals_blindly(self):
        text = self.evidence()
        result = activate(self.snapshot, PACKET, readiness_evidence=text)
        self.assertEqual("TASK_EVIDENCE_PARSED_UNAUTHENTICATED", result["time_for_runner"])
        self.assertEqual(result, verify_activation(self.snapshot))
        self.assertNotIn("f" * 40, json.dumps(result))  # no incumbent current head in Runner packet
        self.assertNotIn("episode_consumed_percent", json.dumps(result))
        seal_activated_plan(self.snapshot, self.receipt, self.gate, PLAN)
        self.assertEqual("NOT_GRANTED", verify_gate(self.snapshot, self.receipt, self.gate)["stage2_authority"])

    def test_not_yet_time_for_runner_fails_closed(self):
        with self.assertRaisesRegex(Stage1Error, "RUNNER_SIGNAL_NOT_REQUESTED"):
            activate(self.snapshot, PACKET, readiness_evidence=self.evidence(episode_consumed_percent=45))
        self.assertFalse((self.snapshot / "activation.json").exists())

    def test_different_run_id_rejected(self):
        with self.assertRaisesRegex(Stage1Error, "RUNNER_SIGNAL_IDENTITY_MISMATCH"):
            activate(self.snapshot, PACKET, readiness_evidence=self.evidence(run_id="OTHER-AGENT"))

    def test_wrong_responsibility_ref_rejected(self):
        with self.assertRaisesRegex(Stage1Error, "RUNNER_SIGNAL_IDENTITY_MISMATCH"):
            activate(self.snapshot, PACKET, readiness_evidence=self.evidence(
                responsibility="reallaksh19/relay-v32-e2e-lab#5"))

    def test_forged_authority_rejected(self):
        bogus = self.evidence().replace('"execution_authority":"NOT_GRANTED"', '"execution_authority":"GRANTED"')
        with self.assertRaises(ValueError):
            activate(self.snapshot, PACKET, readiness_evidence=bogus)
        self.assertFalse((self.snapshot / "activation.json").exists())

    def test_original_unverified_testing_path_marked_unverified(self):
        prior = activate(self.snapshot, PACKET)
        self.assertEqual("AGENT_SIGNAL_UNVERIFIED", prior["time_for_runner"])
        self.assertIsNone(prior["readiness_evidence_digest"])
        self.assertEqual(prior, verify_activation(self.snapshot))


if __name__ == "__main__":
    unittest.main()
