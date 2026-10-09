"""BR-07 witness key separation, source scope, replay and false-clock tests."""
from __future__ import annotations
import base64
import json
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import test_recorder_custody as base
from runner_stage1 import Stage1Error, canonical, digest
from recorder_custody import append
from witness_anchor import load_signed_witness, verify_witness, SCHEMA


class WitnessTests(unittest.TestCase):
    _git = base.CustodyTests._git
    capture = base.CustodyTests.capture
    _request = base.CustodyTests._request
    _seal = base.CustodyTests._seal

    def setUp(self):
        base.CustodyTests.setUp(self)
        self.private = Ed25519PrivateKey.generate()
        self.pub = self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        import hashlib
        self.pinned = "sha256:" + hashlib.sha256(self.pub).hexdigest()
        sealed = self._seal()
        self.last = append(self.journal, base.KEY, "STAGE2_DISCLOSED", self.snapshot,
                           receipt=self.receipt, gate=self.gate, disclosure=self.disclosure,
                           expected_last_mac=sealed["mac"])
        events = [json.loads(x) for x in self.journal.read_text().splitlines()]
        source = json.loads((self.snapshot / "manifest.json").read_text())
        plan = json.loads(self.receipt.read_text())
        gate = json.loads(self.gate.read_text())
        self.body = {
            "schema": SCHEMA, "witness_id": "owner-recorder-v1",
            "run_id": source["run_id"],
            "event": "PLAN_SEALED", "sealed_event_mac": events[2]["mac"],
            "manifest_digest": digest(source), "plan_receipt_digest": digest(plan),
            "gate_digest": digest(gate),
            "witness_event_id": "independent-witness-001",
            "attested_at_utc": "2026-10-09T12:50:00Z",
        }

    def sign(self, **override):
        signed = {**self.body, **override}
        signature = self.private.sign(canonical(signed))
        return canonical({**signed, "signature_b64": base64.b64encode(signature).decode()})

    def check(self, signed=None):
        return verify_witness(signed if signed is not None else self.sign(), self.pub,
                              expected_public_key_sha256=self.pinned,
                              journal=self.journal, recorder_key=base.KEY,
                              snapshot=self.snapshot, plan_receipt=self.receipt,
                              gate=self.gate, expected_witness_id="owner-recorder-v1",
                              expected_last_mac=self.last["mac"])

    def test_positive_signed_stage1_before_disclosure(self):
        report = self.check()
        self.assertEqual("ED25519_VERIFIED_AGAINST_PINNED_KEY", report["witness_signature"])
        self.assertTrue(report["recorded_before_stage2_in_mac_chain"])
        self.assertEqual("NOT_VERIFIED_BY_THIS_MODULE", report["provider_readback"])
        self.assertEqual("WITNESS_ASSERTION_NOT_PROVEN", report["timestamp_accuracy"])
        self.assertEqual("NOT_GRANTED", report["execution_authority"])

    def test_injected_fake_public_key_must_fail_pin(self):
        other = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        with self.assertRaisesRegex(Stage1Error, "WITNESS_KEY_NOT_PINNED"):
            verify_witness(self.sign(), other, expected_public_key_sha256=self.pinned,
                journal=self.journal, recorder_key=base.KEY, snapshot=self.snapshot,
                plan_receipt=self.receipt, gate=self.gate,
                expected_witness_id="owner-recorder-v1", expected_last_mac=self.last["mac"])

    def test_signature_modification_detected(self):
        original = json.loads(self.sign())
        original["attested_at_utc"] = "2026-10-08T12:50:00Z"
        with self.assertRaisesRegex(Stage1Error, "WITNESS_SIGNATURE_VERIFICATION_FAILED"):
            self.check(canonical(original))

    def test_other_stage_receipt_rejected_even_if_signed(self):
        with self.assertRaisesRegex(Stage1Error, "WITNESS_EVENT_INVALID"):
            self.check(self.sign(event="STAGE2_DISCLOSED"))

    def test_cross_run_replay_rejected(self):
        with self.assertRaisesRegex(Stage1Error, "WITNESS_SEALED_BASIS_MISMATCH"):
            self.check(self.sign(run_id="OTHER-RUN"))

    def test_other_mac_fails(self):
        with self.assertRaisesRegex(Stage1Error, "WITNESS_SEAL_MAC_MISMATCH"):
            self.check(self.sign(sealed_event_mac="0" * 64))

    def test_changed_gate_basis_fails(self):
        with self.assertRaisesRegex(Stage1Error, "WITNESS_SEALED_BASIS_MISMATCH"):
            self.check(self.sign(gate_digest="sha256:" + "0" * 64))

    def test_duplicate_json_key_detected(self):
        raw = self.sign().decode().replace('"schema":', '"schema":"another","schema":')
        with self.assertRaisesRegex(Stage1Error, "WITNESS_DUPLICATE_JSON_KEY"):
            load_signed_witness(raw.encode())

    def test_truncated_signature_rejected(self):
        obj = json.loads(self.sign())
        obj["signature_b64"] = "AAAA"
        with self.assertRaisesRegex(Stage1Error, "WITNESS_SIGNATURE_ENCODING_INVALID"):
            self.check(canonical(obj))

    def test_invalid_calendar_date_rejected(self):
        with self.assertRaisesRegex(Stage1Error, "WITNESS_TIME_INVALID"):
            self.check(self.sign(attested_at_utc="2026-02-31T12:50:00Z"))

    def test_bad_mac_journal_detected_even_with_valid_witness(self):
        self.journal.write_text(self.journal.read_text().replace("STAGE2_DISCLOSED","RUNNER_REQUESTED"))
        with self.assertRaises(Stage1Error):
            self.check()

    def test_wrong_external_anchor_fails(self):
        with self.assertRaisesRegex(Stage1Error, "EXTERNAL_ANCHOR_MISMATCH"):
            verify_witness(self.sign(), self.pub, expected_public_key_sha256=self.pinned,
                journal=self.journal, recorder_key=base.KEY, snapshot=self.snapshot,
                plan_receipt=self.receipt, gate=self.gate,
                expected_witness_id="owner-recorder-v1", expected_last_mac="1"*64)

    def test_unsigned_extra_field_fails(self):
        with self.assertRaisesRegex(Stage1Error, "WITNESS_SCHEMA_INVALID"):
            self.check(self.sign(implicit_merge_authority="yes"))


if __name__ == "__main__":
    unittest.main()
