import json
import unittest

from runner_stage1 import Stage1Error
from runner_protocol import activate, verify_gate, verify_activation, seal_activated_plan
import test_runner_stage1 as base
PACKET, PLAN = base.PACKET, base.PLAN


class ProtocolTests(unittest.TestCase):
    _git = base.Stage1Tests._git
    capture = base.Stage1Tests.capture

    def setUp(self):
        base.Stage1Tests.setUp(self)

    def test_two_stage_order_and_tamper(self):
        self.capture()  # genuine start source snapshot
        with self.assertRaisesRegex(Stage1Error, "ACTIVATION_REQUIRED"):
            verify_activation(self.snapshot)
        # Incumbent's implementation can move before late WHAT/WHY is published.
        p = self.repo / "src/csv_auditor/parser.py"
        p.write_text("AGENT_1_NEW_CODE")
        self._git("add", ".")
        self._git("commit", "-qm", "Agent1 progress")
        activate(self.snapshot, {**PACKET, "what": ["R01 initial ID validation addressed"]})
        gate_path = self.root / "recorder" / "gate.json"
        sealed = seal_activated_plan(self.snapshot, self.receipt, gate_path, PLAN)
        self.assertEqual(sealed, verify_gate(self.snapshot, self.receipt, gate_path))
        self.assertNotIn("AGENT_1_NEW_CODE", (self.snapshot / "source/src/csv_auditor/parser.py").read_text())
        data = json.loads((self.snapshot / "activation.json").read_text())
        data["incumbent_what_why_at_activation"]["what"] = ["mutated"]
        (self.snapshot / "activation.json").write_text(json.dumps(data))
        with self.assertRaisesRegex(Stage1Error, "SEALED_GATE_BASIS_MISMATCH"):
            verify_gate(self.snapshot, self.receipt, gate_path)

    def test_activation_refuses_repeat_and_unknown_fields(self):
        self.capture()
        with self.assertRaisesRegex(Stage1Error, "STAGE1_PACKET_SCHEMA_INVALID"):
            activate(self.snapshot, {**PACKET, "agent_1_how": ["secret"]})
        activate(self.snapshot, PACKET)
        with self.assertRaisesRegex(Stage1Error, "RECEIPT_ALREADY_EXISTS"):
            activate(self.snapshot, PACKET)

    def test_cannot_seal_before_activation(self):
        self.capture()
        with self.assertRaisesRegex(Stage1Error, "ACTIVATION_REQUIRED"):
            seal_activated_plan(self.snapshot, self.receipt, self.root / "gate.json", PLAN)

    def test_gate_must_be_present_and_bound(self):
        self.capture()
        activate(self.snapshot, PACKET)
        seal_activated_plan(self.snapshot, self.receipt, self.root / "gate.json", PLAN)
        (self.root / "gate.json").unlink()
        with self.assertRaisesRegex(Stage1Error, "SEALED_GATE_MISSING"):
            verify_gate(self.snapshot, self.receipt, self.root / "gate.json")


if __name__ == "__main__":
    unittest.main()
