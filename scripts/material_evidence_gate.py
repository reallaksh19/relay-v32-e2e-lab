"""Read-only, source-bound qualification preflight for V3.2 lab material.

Produces NO CHECKPOINT_FACTS and NO semantic progress. Provider JSON without
independent execution/artifact custody is never sufficient to award evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SHA = re.compile(r"[0-9a-f]{40}\Z")
PROTOCOL = "lab-v32-material-evidence-preflight-v1"
EXPECTED_REPOSITORY = "reallaksh19/relay-v32-e2e-lab"


def evaluate(graph: dict, snapshot: dict) -> dict:
    """Audit live GitHub PR/run/job observations without publishing facts."""
    if graph.get("programme", {}).get("repository") != EXPECTED_REPOSITORY:
        raise ValueError("GRAPH_REPOSITORY_MISMATCH")
    if snapshot.get("schema") != "lab-v32-provider-observation-v1":
        raise ValueError("PROVIDER_SNAPSHOT_SCHEMA_MISMATCH")
    if snapshot.get("repository") != EXPECTED_REPOSITORY:
        raise ValueError("PROVIDER_REPOSITORY_MISMATCH")
    rows = snapshot.get("leaves")
    if not isinstance(rows, list):
        raise ValueError("PROVIDER_LEAVES_NOT_LIST")
    expected = {node["responsibility_id"]: node for node in graph.get("nodes", [])
                if node.get("kind") == "LEAF"}
    observed: dict[str, Any] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("responsibility_id"), str):
            raise ValueError("INVALID_PROVIDER_LEAF")
        name = row["responsibility_id"]
        if name not in expected or name in observed:
            raise ValueError("UNKNOWN_OR_DUPLICATE_LEAF")
        observed[name] = row
    if set(expected) != set(observed):
        raise ValueError("MISSING_LEAF_OBSERVATION")
    reports = []
    for name in sorted(expected):
        node, row = expected[name], observed[name]
        binding = node.get("primary_pr")
        pr = row.get("pr")
        issues = []
        if not isinstance(pr, dict):
            issues.append("PROVIDER_PR_NOT_READ")
            pr = {}
        if binding != f"{EXPECTED_REPOSITORY}#{pr.get('number')}":
            issues.append("BOUND_PR_MISMATCH")
        head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
        base = pr.get("base") if isinstance(pr.get("base"), dict) else {}
        sha = head.get("sha")
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            issues.append("UNVERIFIED_CANDIDATE_SHA")
        if (head.get("repo") or {}).get("full_name") != EXPECTED_REPOSITORY:
            issues.append("PR_HEAD_REPOSITORY_MISMATCH")
        if (base.get("repo") or {}).get("full_name") != EXPECTED_REPOSITORY:
            issues.append("PR_BASE_REPOSITORY_MISMATCH")
        if base.get("ref") != graph["programme"].get("base_ref", "main"):
            issues.append("PR_BASE_BRANCH_MISMATCH")
        if head.get("ref") != node.get("candidate_ref"):
            issues.append("PR_BRANCH_BINDING_MISMATCH")
        if not pr.get("merged"):
            issues.append("PR_NOT_MERGED")
        runs = row.get("runs", [])
        if not isinstance(runs, list):
            raise ValueError("RUNS_NOT_LIST")
        matching = [r for r in runs if isinstance(r, dict) and r.get("head_sha") == sha
                    and r.get("event") in ("push", "pull_request")]
        successful = []
        for run in matching:
            jobs = run.get("jobs", [])
            if not isinstance(jobs, list):
                continue
            accepted = [j for j in jobs if isinstance(j, dict)
                        and j.get("name") == "responsibility-acceptance"
                        and j.get("status") == "completed"
                        and j.get("conclusion") == "success"
                        and isinstance(j.get("runner_name"), str) and j["runner_name"].strip()
                        and any(isinstance(s, dict) and s.get("name") == "Run current responsibility plus predecessors"
                                and s.get("status") == "completed" and s.get("conclusion") == "success"
                                for s in j.get("steps", []))]
            if run.get("status") == "completed" and run.get("conclusion") == "success" and accepted:
                successful.append(run.get("id"))
        if not matching:
            issues.append("NO_EXACT_HEAD_PRODUCT_ACTIONS")
        elif not successful:
            if all(not any(j.get("runner_name") for j in r.get("jobs", [])
                           if isinstance(j, dict)) for r in matching):
                issues.append("HOSTED_NO_RUNNER_EXECUTED")
            else:
                issues.append("NO_EXECUTED_SUCCESSFUL_ACCEPTANCE_JOB")
        # Even one successful named step does not prove that individual assertions executed.
        # Exact output/artifact custody and independent test acceptance remain separate gates.
        verdict = "SOURCE_MATERIAL_OBSERVED" if not any(x.endswith("MISMATCH") or
            x in {"UNVERIFIED_CANDIDATE_SHA", "PR_NOT_MERGED", "PROVIDER_PR_NOT_READ"}
            for x in issues) else "MATERIAL_IDENTITY_UNVERIFIED"
        reports.append({"responsibility_id": name, "leaf": node["ref"],
                        "primary_pr": binding, "observed_candidate_sha": sha,
                        "material_state": verdict,
                        "executed_acceptance_run_ids": successful,
                        "blockers": issues + ["NO_INDEPENDENT_TEST_ARTIFACT_ATTESTATION",
                                               "NO_ACCEPTED_CHECKPOINT_FACTS_PROVENANCE"],
                        "facts_admitted": False, "progress_credit": "NONE"})
    return {"schema": PROTOCOL, "repository": EXPECTED_REPOSITORY,
            "overall": "NOT_QUALIFIED_FOR_FACTS_ADMISSION", "wrote_github": False,
            "source_observation": "PROVIDER_SNAPSHOT_NOT_CRYPTOGRAPHICALLY_AUTHENTICATED_BY_THIS_PURE_FUNCTION",
            "leaves": reports}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True)
    parser.add_argument("--provider-snapshot", required=True)
    parser.add_argument("--output")
    opts = parser.parse_args()
    try:
        graph = json.loads(Path(opts.graph).read_text(encoding="utf-8"))
        snapshot = json.loads(Path(opts.provider_snapshot).read_text(encoding="utf-8"))
        report = evaluate(graph, snapshot)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"MATERIAL_PREFLIGHT_ERROR: {exc}")
        return 2
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if opts.output:
        Path(opts.output).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if all(r["material_state"] == "SOURCE_MATERIAL_OBSERVED" for r in report["leaves"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
