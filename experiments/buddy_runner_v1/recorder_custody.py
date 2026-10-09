"""BR-06 experimental, recorder-keyed sequence guard for Buddy Stage1 -> Stage2.

MAC authenticates a local journal against a key retained by the independent
recorder; it is NOT a trusted clock, external immutable log, or custody grant.
The agent/runner MUST NOT receive the key or write access to the journal.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re

from runner_stage1 import Stage1Error, canonical, digest, validate_snapshot
from runner_protocol import verify_activation, verify_gate

SCHEMA = "v32-buddy-recorder-event-v1"
EVENTS = ("START_PINNED", "RUNNER_REQUESTED", "PLAN_SEALED", "STAGE2_DISCLOSED")
_SHA = re.compile(r"^[a-f0-9]{40}$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


def _require(predicate, error):
    if not predicate:
        raise Stage1Error(error)


def secret_from_env():
    """The secret is never accepted in command-line arguments or journal."""
    value = os.environ.get("BUDDY_RECORDER_KEY_HEX", "")
    _require(bool(re.fullmatch(r"[a-fA-F0-9]{64,}", value)) and len(value) % 2 == 0,
             "RECORDER_KEY_UNAVAILABLE")
    secret = bytes.fromhex(value)
    _require(len(secret) >= 32, "RECORDER_KEY_TOO_SHORT")
    return secret


def _mac(secret, body):
    return hmac.new(secret, canonical(body), hashlib.sha256).hexdigest()


def _read(f):
    f.seek(0)
    content = f.read()
    if not content:
        return []
    _require(content.endswith(b"\n"), "RECORDER_JOURNAL_TRUNCATED")
    result = []
    for line in content.splitlines():
        try:
            obj = json.loads(line)
        except (ValueError, UnicodeDecodeError) as exc:
            raise Stage1Error("RECORDER_JOURNAL_INVALID_JSON") from exc
        _require(isinstance(obj, dict), "RECORDER_JOURNAL_ROW_INVALID")
        _require(line == canonical(obj), "RECORDER_NONCANONICAL_LINE")
        result.append(obj)
    _require(len(result) <= 4, "RECORDER_EXCESS_EVENT_COUNT")
    return result


def verify_events(events, secret, *, anchor=None):
    """Verify MAC chain + order. Anchor is an externally observed last MAC.

    A self-supplied anchor is NOT an independent external observation.
    """
    _require(isinstance(events, list) and len(events) <= 4, "RECORDER_EVENT_COUNT_INVALID")
    previous = "GENESIS"
    run_id = None
    first_digest = None
    for idx, event in enumerate(events):
        _require(isinstance(event, dict) and set(event) ==
                 {"schema", "seq", "event", "run_id", "basis", "previous_mac", "mac"},
                 "RECORDER_EVENT_SCHEMA_INVALID")
        _require(event["schema"] == SCHEMA and type(event["seq"]) is int and
                 event["seq"] == idx + 1 and event["event"] == EVENTS[idx],
                 "RECORDER_SEQUENCE_INVALID")
        _require(event["previous_mac"] == previous, "RECORDER_CHAIN_BROKEN")
        basis = event["basis"]
        _require(isinstance(basis, dict) and all(isinstance(x, str) for x in basis.values()),
                 "RECORDER_BASIS_INVALID")
        if idx == 0:
            _require(set(basis) == {"manifest", "initial_commit"} and
                     _DIGEST.fullmatch(basis["manifest"]) and _SHA.fullmatch(basis["initial_commit"]),
                     "RECORDER_START_BASIS_INVALID")
            first_digest = basis["manifest"]
            run_id = event["run_id"]
            _require(isinstance(run_id, str) and 0 < len(run_id) <= 80,
                     "RECORDER_RUN_INVALID")
        else:
            allowed = (
                {"manifest", "activation"},
                {"manifest", "activation", "plan", "gate"},
                {"manifest", "activation", "plan", "gate", "disclosure", "candidate_sha"},
            )[idx - 1]
            _require(set(basis) == allowed and all(
                _DIGEST.fullmatch(value) for key, value in basis.items() if key != "candidate_sha"),
                "RECORDER_STAGE_BASIS_INVALID")
            if idx == 3:
                _require(bool(_SHA.fullmatch(basis["candidate_sha"])), "RECORDER_CANDIDATE_INVALID")
            _require(event["run_id"] == run_id and basis["manifest"] == first_digest,
                     "RECORDER_CROSS_RUN_OR_MANIFEST_DRIFT")
            for key, old_value in events[idx - 1]["basis"].items():
                if key != "initial_commit":
                    _require(basis.get(key) == old_value, "RECORDER_BASIS_DRIFT:" + key)
        expected = _mac(secret, {k: v for k, v in event.items() if k != "mac"})
        _require(isinstance(event["mac"], str) and hmac.compare_digest(expected, event["mac"]),
                 "RECORDER_MAC_INVALID")
        previous = event["mac"]
    if anchor is not None:
        _require(bool(events) and isinstance(anchor, str) and
                 hmac.compare_digest(anchor, previous), "EXTERNAL_ANCHOR_MISMATCH")
    return {"events": len(events), "last_event": events[-1]["event"] if events else "NONE",
            "last_mac": previous, "run_id": run_id,
            "external_anchor_checked": anchor is not None,
            "trusted_temporal_custody": "NOT_PROVEN_BY_LOCAL_JOURNAL",
            "execution_authority": "NOT_GRANTED"}


def _basis(kind, snapshot, *, receipt=None, gate=None, disclosure=None):
    source = validate_snapshot(snapshot)
    base = {"manifest": digest(source)}
    if kind == "START_PINNED":
        return source["run_id"], {**base, "initial_commit": source["origin"]["initial_commit"]}
    activation = verify_activation(snapshot)
    _require(activation["time_for_runner"] == "TASK_EVIDENCE_PARSED_UNAUTHENTICATED",
             "RECORDER_RUNNER_SIGNAL_NOT_BOUND")
    base["activation"] = digest(activation)
    if kind == "RUNNER_REQUESTED":
        return source["run_id"], base
    verified_gate = verify_gate(snapshot, receipt, gate)
    plan_receipt = json.loads(Path(receipt).read_text(encoding="utf-8"))
    base.update({"plan": digest(plan_receipt), "gate": digest(verified_gate)})
    if kind == "PLAN_SEALED":
        return source["run_id"], base
    _require(kind == "STAGE2_DISCLOSED" and isinstance(disclosure, dict) and
             set(disclosure) == {"run_id", "candidate_sha", "incumbent_plan_digest", "source_context_digest"},
             "RECORDER_DISCLOSURE_SCHEMA_INVALID")
    _require(disclosure["run_id"] == source["run_id"] and
             isinstance(disclosure["candidate_sha"], str) and _SHA.fullmatch(disclosure["candidate_sha"]),
             "RECORDER_DISCLOSURE_IDENTITY_INVALID")
    _require(all(isinstance(disclosure[k], str) and _DIGEST.fullmatch(disclosure[k]) for k in
                 ("incumbent_plan_digest", "source_context_digest")),
             "RECORDER_DISCLOSURE_DIGEST_INVALID")
    return source["run_id"], {**base, "disclosure": digest(disclosure),
                                 "candidate_sha": disclosure["candidate_sha"]}


def append(journal, secret, kind, snapshot, *, receipt=None, gate=None,
           disclosure=None, expected_last_mac=None):
    _require(kind in EVENTS, "RECORDER_EVENT_INVALID")
    journal = Path(journal)
    _require(journal.exists() or kind == "START_PINNED", "RECORDER_GENESIS_REQUIRED")
    _require(not journal.is_symlink(), "RECORDER_JOURNAL_SYMLINK")
    run_id, basis = _basis(kind, snapshot, receipt=receipt, gate=gate, disclosure=disclosure)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        events = _read(stream)
        state = verify_events(events, secret, anchor=expected_last_mac)
        idx = len(events)
        _require(idx < len(EVENTS) and EVENTS[idx] == kind, "RECORDER_TRANSITION_REJECTED")
        if events:
            _require(events[0]["run_id"] == run_id, "RECORDER_RUN_MISMATCH")
            for key, previous in events[-1]["basis"].items():
                if key != "initial_commit":
                    _require(basis.get(key) == previous, "RECORDER_BASIS_MISMATCH:" + key)
        else:
            _require(kind == "START_PINNED", "RECORDER_GENESIS_REQUIRED")
        event = {"schema": SCHEMA, "seq": idx + 1, "event": kind,
                 "run_id": run_id, "basis": basis, "previous_mac": state["last_mac"]}
        event["mac"] = _mac(secret, event)
        stream.seek(0, 2)
        stream.write(canonical(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        return event


def verify_journal(journal, secret, *, anchor=None):
    journal = Path(journal)
    _require(journal.is_file() and not journal.is_symlink(), "RECORDER_JOURNAL_MISSING")
    with journal.open("rb") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
        return verify_events(_read(stream), secret, anchor=anchor)


def validate_disclosure(journal, secret, snapshot, receipt, gate,
                        disclosure, *, external_anchor=None):
    journal = Path(journal)
    _require(journal.is_file() and not journal.is_symlink(), "RECORDER_JOURNAL_MISSING")
    # A single protected read: never verify a previous journal and then compare
    # against independently reread bytes that could have moved in between.
    with journal.open("rb") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
        events = _read(stream)
        state = verify_events(events, secret, anchor=external_anchor)
        _require(state["last_event"] == "STAGE2_DISCLOSED", "RECORDER_DISCLOSURE_NOT_OPEN")
        run_id, expected = _basis("STAGE2_DISCLOSED", snapshot, receipt=receipt,
                                  gate=gate, disclosure=disclosure)
        _require(events[-1]["run_id"] == run_id and events[-1]["basis"] == expected,
                 "RECORDER_DISCLOSURE_NOT_BOUND")
        return state


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("start", "request", "seal", "disclose", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--journal", required=True)
        if name != "verify":
            p.add_argument("--snapshot", required=True)
        if name in ("seal", "disclose"):
            p.add_argument("--receipt", required=True)
            p.add_argument("--gate", required=True)
        if name == "disclose":
            p.add_argument("--disclosure", required=True)
        p.add_argument("--last-mac", help="previous EXTERNALLY retained MAC, not journal supplied")
    args = ap.parse_args()
    try:
        key = secret_from_env()
        if args.command == "verify":
            result = verify_journal(args.journal, key, anchor=args.last_mac)
        else:
            kind = dict(start="START_PINNED", request="RUNNER_REQUESTED",
                        seal="PLAN_SEALED", disclose="STAGE2_DISCLOSED")[args.command]
            event = append(args.journal, key, kind, args.snapshot,
                           receipt=getattr(args, "receipt", None),
                           gate=getattr(args, "gate", None),
                           disclosure=json.loads(Path(args.disclosure).read_text(encoding="utf-8"))
                           if args.command == "disclose" else None,
                           expected_last_mac=args.last_mac)
            result = {"last_event": kind, "last_mac": event["mac"],
                      "execution_authority": "NOT_GRANTED",
                      "trusted_temporal_custody": "NOT_PROVEN_BY_LOCAL_JOURNAL"}
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, TypeError) as exc:
        ap.exit(2, "RECORDER_FAIL_CLOSED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
