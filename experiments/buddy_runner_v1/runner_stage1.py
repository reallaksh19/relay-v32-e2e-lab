"""Experimental V3.2 Buddy Runner Stage 1: start-source isolation + sealed plan.

This module never reads the incumbent's current candidate or current PR. The
launcher MUST run the buddy without a live repository, GitHub credentials, or
network/tools exposing current material. Local receipts are not signatures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

SCHEMA = "v32-buddy-stage1-v1"
SHA = re.compile(r"^[a-f0-9]{40}$")
RUN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
# Release-specific, pinned input manifest; no .git, session log, mutable issue,
# PR, newer source, task-evidence comments, or agent implementation notes.
R01_PATHS = (
    "governance/owner-intent.md",
    "governance/released-graph.json",
    "src/csv_auditor/parser.py",
    "acceptance/test_r01_input.py",
)
PACKET_KEYS = frozenset({"what", "why", "pending", "known_issues", "parked"})
PLAN_KEYS = frozenset({"understanding", "approach", "rejected_alternatives", "assumptions", "questions", "next_action"})


class Stage1Error(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def sha_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def git(repo, *args):
    completed = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
    if completed.returncode:
        raise Stage1Error("GIT_SOURCE_UNAVAILABLE")
    return completed.stdout


def checked_path(value):
    if not isinstance(value, str) or not value or "\\" in value or any(c.isspace() for c in value):
        raise Stage1Error("INVALID_SOURCE_PATH")
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in (".", "..", "") for part in value.split("/")) or p.as_posix() != value:
        raise Stage1Error("INVALID_SOURCE_PATH")
    return value


def packet_check(packet):
    if not isinstance(packet, dict) or set(packet) != PACKET_KEYS:
        raise Stage1Error("STAGE1_PACKET_SCHEMA_INVALID")
    for name, entries in packet.items():
        if not isinstance(entries, list) or len(entries) > 12 or any(
            not isinstance(v, str) or not v.strip() or len(v) > 400 for v in entries
        ):
            raise Stage1Error("STAGE1_PACKET_FIELD_INVALID:" + name)
    if not packet["what"] or not packet["why"]:
        raise Stage1Error("STAGE1_WHAT_WHY_REQUIRED")
    # Human/independent review of the free text is still required: exact-key
    # gating cannot prove an adversarial incumbent did not embed a HOW hint.


def _exclusive_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise Stage1Error("RECEIPT_ALREADY_EXISTS") from exc
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def capture_start(repo, outdir, *, run_id, expected_sha, packet, paths=R01_PATHS):
    """Called at ACTUAL agent start, before Agent 1 writes source.

    Snapshot contains only bytes from the verified START commit, not mutable
    working-tree contents. The calling recorder must hold custody of outdir.
    """
    repo, outdir = Path(repo), Path(outdir)
    if not RUN.fullmatch(run_id) or not SHA.fullmatch(expected_sha):
        raise Stage1Error("INVALID_RUN_OR_SHA")
    if tuple(paths) != R01_PATHS or len(set(paths)) != len(paths):
        raise Stage1Error("UNRELEASED_SOURCE_ALLOWLIST")
    packet_check(packet)
    actual = git(repo, "rev-parse", "HEAD").decode().strip()
    if actual != expected_sha:
        raise Stage1Error("START_HEAD_MISMATCH")
    if git(repo, "status", "--porcelain").strip():
        raise Stage1Error("START_WORKTREE_NOT_CLEAN")
    if outdir.exists():
        raise Stage1Error("SNAPSHOT_ALREADY_EXISTS")
    # Refuse destination inside repository, where a future coder could change it.
    if outdir.resolve().is_relative_to(repo.resolve()):
        raise Stage1Error("SNAPSHOT_INSIDE_SOURCE_REPO")
    staged = {}
    for path in paths:
        checked_path(path)
        mode = git(repo, "ls-tree", expected_sha, "--", path).decode().strip()
        if not mode.startswith("100644 blob ") and not mode.startswith("100755 blob "):
            raise Stage1Error("NOT_REGULAR_PINNED_FILE:" + path)
        content = git(repo, "show", expected_sha + ":" + path)
        if len(content) > 2_000_000:
            raise Stage1Error("SOURCE_TOO_LARGE")
        staged[path] = content
    # The bundle is an allowlisted TREE without .git or network credentials.
    outdir.mkdir(parents=True)
    files = {}
    for path, content in staged.items():
        target = outdir / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        files[path] = sha_bytes(content)
    manifest = {
        "schema": SCHEMA,
        "run_id": run_id,
        "origin": {"repo": "reallaksh19/relay-v32-e2e-lab", "initial_commit": expected_sha,
                   "responsibility": "R01", "issue": 4},
        "source_files": files,
        "what_why": packet,
        "disclosure": {"incumbent_implementation": "DENIED", "current_pr": "DENIED",
                       "incumbent_plan": "DENIED", "live_provider": "DENIED"},
    }
    _exclusive_json(outdir / "manifest.json", manifest)
    return manifest


def validate_snapshot(outdir):
    outdir = Path(outdir)
    manifest = json.loads((outdir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA or set(manifest.get("source_files", {})) != set(R01_PATHS):
        raise Stage1Error("SNAPSHOT_SCHEMA_OR_ALLOWLIST_INVALID")
    packet_check(manifest.get("what_why"))
    for path, expected in manifest["source_files"].items():
        target = outdir / "source" / checked_path(path)
        if target.is_symlink() or not target.is_file() or sha_bytes(target.read_bytes()) != expected:
            raise Stage1Error("SNAPSHOT_SOURCE_TAMPER:" + path)
    actual_paths = {p.relative_to(outdir / "source").as_posix()
                    for p in (outdir / "source").rglob("*") if p.is_file() or p.is_symlink()}
    if actual_paths != set(R01_PATHS):
        raise Stage1Error("EXTRA_SNAPSHOT_CONTENT")
    if manifest.get("disclosure") != {"incumbent_implementation": "DENIED", "current_pr": "DENIED",
                                   "incumbent_plan": "DENIED", "live_provider": "DENIED"}:
        raise Stage1Error("DISCLOSURE_POLICY_INVALID")
    return manifest


def seal_plan(snapshot_dir, sealed_receipt_path, plan):
    """Recorder-owned receipt. Must run before Stage 2 disclosure.

    O_EXCL/fsync prevents accidental replacement, NOT hostile mutation by a
    party with write access. External trusted custody is required for a real
    nonrepudiation/temporal-disclosure claim.
    """
    source = validate_snapshot(snapshot_dir)
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
        raise Stage1Error("RUNNER_PLAN_SCHEMA_INVALID")
    for key, val in plan.items():
        if key == "next_action":
            if not isinstance(val, str) or not val.strip() or len(val) > 500:
                raise Stage1Error("RUNNER_NEXT_ACTION_INVALID")
        elif not isinstance(val, list) or not val or len(val) > 20 or any(
            not isinstance(x, str) or not x.strip() or len(x) > 600 for x in val
        ):
            raise Stage1Error("RUNNER_PLAN_FIELD_INVALID:" + key)
    receipt = {
        "schema": "v32-buddy-plan-receipt-v1", "run_id": source["run_id"],
        "stage1_manifest_digest": digest(source), "independent_plan": plan,
        "plan_digest": digest(plan),
        "pre_stage2_disclosure": "RECORDER_ATTESTATION_REQUIRED",
        "authority": "NO_EXECUTION_OR_MERGE_AUTHORITY",
    }
    _exclusive_json(sealed_receipt_path, receipt)
    return receipt


def verify_seal(snapshot_dir, receipt_path):
    source = validate_snapshot(snapshot_dir)
    receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    if (receipt.get("schema") != "v32-buddy-plan-receipt-v1"
            or receipt.get("run_id") != source["run_id"]
            or receipt.get("stage1_manifest_digest") != digest(source)
            or receipt.get("plan_digest") != digest(receipt.get("independent_plan"))
            or receipt.get("pre_stage2_disclosure") != "RECORDER_ATTESTATION_REQUIRED"):
        raise Stage1Error("SEAL_BASIS_MISMATCH")
    return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    a = sub.add_parser("capture-start")
    a.add_argument("--repo", required=True)
    a.add_argument("--snapshot", required=True)
    a.add_argument("--run", required=True)
    a.add_argument("--start-sha", required=True)
    a.add_argument("--packet", required=True, help="WHAT/WHY JSON file only")
    b = sub.add_parser("seal")
    b.add_argument("--snapshot", required=True)
    b.add_argument("--receipt", required=True)
    b.add_argument("--plan", required=True)
    c = sub.add_parser("verify")
    c.add_argument("--snapshot", required=True)
    c.add_argument("--receipt", required=True)
    args = ap.parse_args()
    try:
        if args.command == "capture-start":
            x = capture_start(args.repo, args.snapshot, run_id=args.run,
                              expected_sha=args.start_sha, packet=json.loads(Path(args.packet).read_text()))
        elif args.command == "seal":
            x = seal_plan(args.snapshot, args.receipt, json.loads(Path(args.plan).read_text()))
        else:
            x = verify_seal(args.snapshot, args.receipt)
        print(json.dumps({"result": "PASS", "schema": x["schema"], "run_id": x["run_id"]}))
    except (Stage1Error, json.JSONDecodeError, OSError) as exc:
        ap.exit(2, f"STAGE1_FAIL_CLOSED: {exc}\n")


if __name__ == "__main__":
    main()
