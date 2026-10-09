"""Experimental V3.2 Buddy Stage 2: source-grounded, READ-ONLY plan reconciliation.

Host must seal Runner's Stage 1 plan in independent custody before disclosing
Stage 2. Local hashes, incumbent assertions and tool-supplied provider facts
cannot authenticate historical order, CI or execution authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

from runner_protocol import verify_gate
from runner_stage1 import Stage1Error, _exclusive_json, digest
from recorder_custody import validate_disclosure, secret_from_env

_SHA = re.compile(r"^[a-f0-9]{40}$")
_ALLOWED_R01_WRITE = frozenset({"src/csv_auditor/parser.py"})
_R01_TEST = "acceptance/test_r01_input.py"


def _git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       check=False, timeout=30)
    if p.returncode:
        raise Stage1Error("STAGE2_GIT_QUERY_FAILED:" + args[0])
    return p.stdout.strip()


def _check_incumbent_plan(value: dict) -> None:
    if not isinstance(value, dict) or set(value) != {"approach", "pending", "next_action", "source_claims"}:
        raise Stage1Error("INCUMBENT_HANDOVER_SCHEMA_INVALID")
    if not isinstance(value["next_action"], str) or not value["next_action"].strip():
        raise Stage1Error("INCUMBENT_NEXT_ACTION_REQUIRED")
    for key in ("approach", "pending", "source_claims"):
        if not isinstance(value[key], list) or not all(isinstance(x, str) and x.strip() for x in value[key]):
            raise Stage1Error("INCUMBENT_HANDOVER_FIELD_INVALID:" + key)
    if not value["approach"]:
        raise Stage1Error("INCUMBENT_APPROACH_REQUIRED")


def _check_decisions(value: dict) -> None:
    expected = {"agreements", "agent1_stronger", "runner_stronger", "unresolved",
                "high_roi_in_scope", "medium_roi_parked", "next_action", "owner_scope_change"}
    if not isinstance(value, dict) or set(value) != expected:
        raise Stage1Error("RECONCILIATION_DECISIONS_SCHEMA_INVALID")
    if not isinstance(value["next_action"], str) or not value["next_action"].strip():
        raise Stage1Error("RECONCILIATION_NEXT_ACTION_REQUIRED")
    for key in expected - {"next_action", "owner_scope_change"}:
        entries = value[key]
        if not isinstance(entries, list) or len(entries) > 20:
            raise Stage1Error("RECONCILIATION_ENTRIES_INVALID:" + key)
        for row in entries:
            if not isinstance(row, dict) or set(row) != {"finding", "why", "evidence_refs"}:
                raise Stage1Error("RECONCILIATION_ENTRY_SCHEMA_INVALID:" + key)
            if any(not isinstance(row[k], str) or not row[k].strip() for k in ("finding", "why")):
                raise Stage1Error("RECONCILIATION_REASON_REQUIRED:" + key)
            refs = row["evidence_refs"]
            if not isinstance(refs, list) or not refs or any(not isinstance(r, str) or not r.strip() for r in refs):
                raise Stage1Error("RECONCILIATION_EVIDENCE_REQUIRED:" + key)
    if value["owner_scope_change"] not in ("NONE", "OWNER_DECISION_REQUIRED"):
        raise Stage1Error("SCOPE_DECISION_INVALID")


def observe_current_source(repo: str | Path, initial_commit: str, expected_head: str) -> dict:
    repo = Path(repo)
    if not _SHA.fullmatch(initial_commit) or not _SHA.fullmatch(expected_head):
        raise Stage1Error("STAGE2_SOURCE_SHA_INVALID")
    if _git(repo, "rev-parse", "HEAD") != expected_head:
        raise Stage1Error("STAGE2_CANDIDATE_MOVED")
    if _git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise Stage1Error("STAGE2_UNRESOLVED_INFLIGHT_WRITES")
    _git(repo, "cat-file", "-e", initial_commit + "^{commit}")
    if _git(repo, "merge-base", initial_commit, expected_head) != initial_commit:
        raise Stage1Error("STAGE2_START_NOT_ANCESTOR")
    changed = sorted(set(filter(None, _git(repo, "diff", "--name-only", initial_commit,
                                           expected_head, "--").splitlines())))
    unexpected = [p for p in changed if p not in _ALLOWED_R01_WRITE]
    if _git(repo, "rev-parse", "HEAD") != expected_head:
        raise Stage1Error("STAGE2_CANDIDATE_MOVED_DURING_READ")
    if _git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise Stage1Error("STAGE2_INFLIGHT_WRITES_DURING_READ")
    return {"initial_commit": initial_commit, "observed_head": expected_head,
            "changed_paths": changed, "unexpected_paths": unexpected,
            "source_currentness": "EXACT_LOCAL_GIT_READ_ONLY",
            "provider_currentness": "NOT_OBSERVED",
            "provider_pr_ci_qualification": "UNKNOWN",
            "working_tree": "CLEAN", "golden_oracle": _R01_TEST}


def reconcile(snapshot_dir: str | Path, plan_receipt_path: str | Path,
              stage1_gate_path: str | Path, repo: str | Path,
              expected_head: str, incumbent_plan: dict, decisions: dict,
              report_path: str | Path, *, custody_observation: dict | None = None) -> dict:
    gate = verify_gate(snapshot_dir, plan_receipt_path, stage1_gate_path)
    plan_receipt = json.loads(Path(plan_receipt_path).read_text(encoding="utf-8"))
    _check_incumbent_plan(incumbent_plan)
    _check_decisions(decisions)
    if Path(report_path).resolve().is_relative_to(Path(repo).resolve()):
        raise Stage1Error("STAGE2_REPORT_INSIDE_SOURCE_REPO")
    original = json.loads((Path(snapshot_dir) / "manifest.json").read_text(encoding="utf-8"))
    initial = original["origin"]["initial_commit"]
    observed = observe_current_source(repo, initial, expected_head)
    uncertainty = []
    if observed["unexpected_paths"]:
        uncertainty.append("SCOPE_DRIFT_REQUIRES_OWNER_PLAN_RECONCILIATION")
    if decisions["unresolved"]:
        uncertainty.append("UNRESOLVED_PLAN_DISAGREEMENT")
    if decisions["owner_scope_change"] == "OWNER_DECISION_REQUIRED":
        uncertainty.append("OWNER_AUTHORIZATION_REQUIRED")
    uncertainty.extend(["PROVIDER_PR_CI_UNKNOWN", "EXTERNAL_RECEIPT_CUSTODY_UNVERIFIED",
                        "AGENT_PLAN_EVIDENCE_REFS_NOT_INDEPENDENTLY_QUALIFIED"])
    output = {
        "schema": "v32-buddy-stage2-reconciliation-v1",
        "run_id": gate["run_id"],
        "stage1_gate_digest": digest(gate),
        "independent_plan_digest": plan_receipt["plan_digest"],
        "independent_plan": plan_receipt["independent_plan"],
        "incumbent_plan_digest": digest(incumbent_plan),
        "incumbent_plan": incumbent_plan,
        "source_observation": observed,
        "decisions": decisions,
        "unresolved": uncertainty,
        "execution_authority": "NOT_GRANTED",
        "writer_transfer": "NOT_ATTEMPTED",
        "github_issue_update": "NOT_ATTEMPTED",
        "custody_observation": custody_observation or
            {"state": "UNATTESTED_LOCAL_LIBRARY_CALL", "execution_authority": "NOT_GRANTED"},
        "state": "READ_ONLY_RECONCILIATION_REQUIRES_EXTERNAL_ADMISSION",
    }
    _exclusive_json(report_path, output)
    return output


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ("snapshot", "receipt", "gate", "repo", "head", "incumbent-plan",
                "decisions", "report"):
        ap.add_argument("--" + key, required=True)
    ap.add_argument("--custody-journal", required=True)
    ap.add_argument("--disclosure", required=True)
    ap.add_argument("--external-anchor", required=True)
    ns = ap.parse_args()
    try:
        incumbent = json.loads(Path(ns.incumbent_plan).read_text(encoding="utf-8"))
        decisions = json.loads(Path(ns.decisions).read_text(encoding="utf-8"))
        disclosure = json.loads(Path(ns.disclosure).read_text(encoding="utf-8"))
        if (disclosure.get("candidate_sha") != ns.head or
                disclosure.get("incumbent_plan_digest") != digest(incumbent)):
            raise Stage1Error("STAGE2_CUSTODY_DISCLOSURE_BASIS_MISMATCH")
        custody = validate_disclosure(ns.custody_journal, secret_from_env(),
                                      ns.snapshot, ns.receipt, ns.gate,
                                      disclosure, external_anchor=ns.external_anchor)
        result = reconcile(ns.snapshot, ns.receipt, ns.gate, ns.repo, ns.head,
                           incumbent, decisions, ns.report,
                           custody_observation={
                               "state": "LOCAL_RECORDER_EVENT_CHAIN_VERIFIED",
                               "journal_event_count": custody["events"],
                               "externally_supplied_anchor_checked": custody["external_anchor_checked"],
                               "temporal_independence": "NOT_AUTHENTICATED_BY_THIS_CLIENT",
                               "execution_authority": "NOT_GRANTED",
                           })
    except (Stage1Error, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        ap.exit(2, "STAGE2_FAIL_CLOSED: " + str(exc) + "\n")
    print(json.dumps({"result": "READ_ONLY", "schema": result["schema"],
                      "candidate": result["source_observation"]["observed_head"],
                      "execution_authority": result["execution_authority"]}))


if __name__ == "__main__":
    main()
