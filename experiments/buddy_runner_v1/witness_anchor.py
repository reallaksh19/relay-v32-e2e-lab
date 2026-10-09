"""BR-07 detached Ed25519 witness verifier for Stage1-before-Stage2.

Independent witness MUST hold its private key outside Agent1/Runner/recorder
implementation. A valid signature alone does not authenticate time,
independence, immutable publication or actual provider readback.
"""
from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from recorder_custody import read_verified_journal
from runner_stage1 import Stage1Error, canonical, digest, validate_snapshot
from runner_protocol import verify_gate

SCHEMA = "v32-buddy-external-witness-v1"
FIELDS = frozenset({"schema", "witness_id", "run_id", "event", "sealed_event_mac",
                   "manifest_digest", "plan_receipt_digest", "gate_digest",
                   "witness_event_id", "attested_at_utc", "signature_b64"})
HEX64 = re.compile(r"^[a-f0-9]{64}$")
DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


def _check(ok, error):
    if not ok:
        raise Stage1Error(error)


def load_signed_witness(raw: bytes):
    _check(isinstance(raw, bytes) and len(raw) <= 8192, "WITNESS_RECEIPT_OVERSIZE")
    def unique(pairs):
        values = {}
        for key, val in pairs:
            _check(key not in values, "WITNESS_DUPLICATE_JSON_KEY")
            values[key] = val
        return values
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Stage1Error("WITNESS_RECEIPT_INVALID_JSON") from exc
    _check(type(obj) is dict and set(obj) == FIELDS, "WITNESS_SCHEMA_INVALID")
    _check(obj["schema"] == SCHEMA and obj["event"] == "PLAN_SEALED",
           "WITNESS_EVENT_INVALID")
    for key in ("witness_id", "run_id", "witness_event_id"):
        _check(type(obj[key]) is str and bool(ID.fullmatch(obj[key])), "WITNESS_ID_INVALID:" + key)
    _check(type(obj["sealed_event_mac"]) is str and bool(HEX64.fullmatch(obj["sealed_event_mac"])),
           "WITNESS_MAC_INVALID")
    for key in ("manifest_digest", "plan_receipt_digest", "gate_digest"):
        _check(type(obj[key]) is str and bool(DIGEST.fullmatch(obj[key])),
               "WITNESS_DIGEST_INVALID:" + key)
    stamp = obj["attested_at_utc"]
    _check(type(stamp) is str and bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", stamp)),
           "WITNESS_TIME_FORMAT_INVALID")
    try:
        datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise Stage1Error("WITNESS_TIME_INVALID") from exc
    _check(type(obj["signature_b64"]) is str, "WITNESS_SIGNATURE_INVALID")
    try:
        signature = base64.b64decode(obj["signature_b64"], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise Stage1Error("WITNESS_SIGNATURE_ENCODING_INVALID") from exc
    _check(len(signature) == 64 and base64.b64encode(signature).decode() == obj["signature_b64"],
           "WITNESS_SIGNATURE_ENCODING_INVALID")
    return obj, signature


def verify_witness(receipt_bytes: bytes, trusted_public_key: bytes, *,
                   expected_public_key_sha256: str, journal: Path, recorder_key: bytes,
                   snapshot: Path, plan_receipt: Path, gate: Path,
                   expected_witness_id: str, expected_last_mac: str):
    """Verify a detached witness using separately pinned public key.

    Caller must obtain receipt from an independent provider; this function
    does not assert that a source URL or a timestamp is externally verified.
    """
    obj, signature = load_signed_witness(receipt_bytes)
    _check(type(trusted_public_key) is bytes and len(trusted_public_key) == 32,
           "WITNESS_PUBLIC_KEY_INVALID")
    fingerprint = "sha256:" + hashlib.sha256(trusted_public_key).hexdigest()
    _check(expected_public_key_sha256 == fingerprint, "WITNESS_KEY_NOT_PINNED")
    _check(obj["witness_id"] == expected_witness_id, "WITNESS_ID_MISMATCH")
    signed = {key: val for key, val in obj.items() if key != "signature_b64"}
    try:
        Ed25519PublicKey.from_public_bytes(trusted_public_key).verify(signature, canonical(signed))
    except (InvalidSignature, ValueError) as exc:
        raise Stage1Error("WITNESS_SIGNATURE_VERIFICATION_FAILED") from exc
    source = validate_snapshot(snapshot)
    sealed_gate = verify_gate(snapshot, plan_receipt, gate)
    plan = json.loads(Path(plan_receipt).read_text(encoding="utf-8"))
    state, rows = read_verified_journal(journal, recorder_key, anchor=expected_last_mac)
    _check(state["events"] == 4 and state["last_event"] == "STAGE2_DISCLOSED",
           "WITNESS_STAGE2_NOT_DISCLOSED")
    _check(len(rows) == 4 and rows[2]["event"] == "PLAN_SEALED",
           "WITNESS_PRE_DISCLOSURE_EVENT_MISSING")
    _check(obj["sealed_event_mac"] == rows[2]["mac"], "WITNESS_SEAL_MAC_MISMATCH")
    _check(obj["run_id"] == source["run_id"] and
           obj["manifest_digest"] == digest(source) and
           obj["plan_receipt_digest"] == digest(plan) and
           obj["gate_digest"] == digest(sealed_gate), "WITNESS_SEALED_BASIS_MISMATCH")
    return {"schema": SCHEMA, "witness": obj["witness_id"],
            "witness_event_id": obj["witness_event_id"],
            "witness_receipt_digest": "sha256:" + hashlib.sha256(receipt_bytes).hexdigest(),
            "witness_signature": "ED25519_VERIFIED_AGAINST_PINNED_KEY",
            "witness_event": "PLAN_SEALED",
            "recorded_before_stage2_in_mac_chain": True,
            "provider_readback": "NOT_VERIFIED_BY_THIS_MODULE",
            "claimed_utc_timestamp": obj["attested_at_utc"],
            "timestamp_accuracy": "WITNESS_ASSERTION_NOT_PROVEN",
            "witness_independence": "REQUIRES_EXTERNAL_CUSTODY_EVIDENCE",
            "execution_authority": "NOT_GRANTED"}
