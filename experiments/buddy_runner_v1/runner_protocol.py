"""Two-event Stage 1 gate: real start-source capture, later WHAT/WHY activation.

Production host MUST custody/fence all snapshot/receipt paths independently of
both agents, isolate Runner from current GitHub and source, and attest order.
Filesystem O_EXCL is not a signed immutable timestamp.
"""
import argparse
import json
from pathlib import Path
from runner_stage1 import (
    Stage1Error, _exclusive_json, capture_start, digest,
    packet_check, seal_plan, validate_snapshot, verify_seal,
)

ACTIVATION = "v32-buddy-runner-activation-v1"
GATE = "v32-buddy-sealed-stage1-gate-v1"


def activate(snapshot_dir, packet):
    """Only called at TIME_FOR_RUNNER; absolutely no live repo reads."""
    source = validate_snapshot(snapshot_dir)
    packet_check(packet)
    activation = {
        "schema": ACTIVATION, "run_id": source["run_id"],
        "start_manifest_digest": digest(source),
        "time_for_runner": "AGENT_SIGNAL_UNVERIFIED",
        "issue_state": "FROZEN_START_ONLY",
        "incumbent_what_why_at_activation": packet,
        "runner_authority": "READ_ONLY",
    }
    _exclusive_json(Path(snapshot_dir) / "activation.json", activation)
    return activation


def verify_activation(snapshot_dir):
    source = validate_snapshot(snapshot_dir)
    try:
        activation = json.loads((Path(snapshot_dir) / "activation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage1Error("ACTIVATION_REQUIRED_BEFORE_PLAN") from exc
    if (activation.get("schema") != ACTIVATION or activation.get("run_id") != source["run_id"]
            or activation.get("start_manifest_digest") != digest(source)
            or activation.get("time_for_runner") != "AGENT_SIGNAL_UNVERIFIED"
            or activation.get("issue_state") != "FROZEN_START_ONLY"
            or activation.get("runner_authority") != "READ_ONLY"):
        raise Stage1Error("ACTIVATION_SOURCE_MISMATCH")
    packet_check(activation.get("incumbent_what_why_at_activation"))
    return activation


def seal_activated_plan(snapshot_dir, receipt_file, gate_file, plan):
    activation = verify_activation(snapshot_dir)
    receipt = seal_plan(snapshot_dir, receipt_file, plan)
    gate = {
        "schema": GATE, "run_id": activation["run_id"],
        "start_manifest_digest": activation["start_manifest_digest"],
        "activation_digest": digest(activation),
        "independent_plan_receipt_digest": digest(receipt),
        "disclosure_order": "REQUIRES_EXTERNAL_RECORDER_ATTESTATION",
        "stage2_authority": "NOT_GRANTED",
    }
    _exclusive_json(gate_file, gate)
    return gate


def verify_gate(snapshot_dir, receipt_file, gate_file):
    activation = verify_activation(snapshot_dir)
    receipt = verify_seal(snapshot_dir, receipt_file)
    try:
        gate = json.loads(Path(gate_file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage1Error("SEALED_GATE_MISSING") from exc
    if (gate.get("schema") != GATE or gate.get("run_id") != activation["run_id"]
            or gate.get("start_manifest_digest") != activation["start_manifest_digest"]
            or gate.get("activation_digest") != digest(activation)
            or gate.get("independent_plan_receipt_digest") != digest(receipt)
            or gate.get("disclosure_order") != "REQUIRES_EXTERNAL_RECORDER_ATTESTATION"
            or gate.get("stage2_authority") != "NOT_GRANTED"):
        raise Stage1Error("SEALED_GATE_BASIS_MISMATCH")
    return gate


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    start = sub.add_parser("start")
    for name in ("repo", "snapshot", "run", "start-sha", "initial-packet"):
        start.add_argument("--" + name, required=True)
    activation = sub.add_parser("activate")
    for name in ("snapshot", "packet"):
        activation.add_argument("--" + name, required=True)
    seal = sub.add_parser("seal")
    for name in ("snapshot", "receipt", "gate", "plan"):
        seal.add_argument("--" + name, required=True)
    verify = sub.add_parser("verify-gate")
    for name in ("snapshot", "receipt", "gate"):
        verify.add_argument("--" + name, required=True)
    args = ap.parse_args()
    try:
        if args.cmd == "start":
            result = capture_start(args.repo, args.snapshot, run_id=args.run,
                                   expected_sha=getattr(args, "start_sha"),
                                   packet=json.loads(Path(args.initial_packet).read_text()))
        elif args.cmd == "activate":
            result = activate(args.snapshot, json.loads(Path(args.packet).read_text()))
        elif args.cmd == "seal":
            result = seal_activated_plan(args.snapshot, args.receipt, args.gate,
                                         json.loads(Path(args.plan).read_text()))
        else:
            result = verify_gate(args.snapshot, args.receipt, args.gate)
        print(json.dumps({"state": "PASS", "schema": result["schema"], "run_id": result["run_id"]}))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        ap.exit(2, "RUNNER_STAGE1_FAIL_CLOSED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
