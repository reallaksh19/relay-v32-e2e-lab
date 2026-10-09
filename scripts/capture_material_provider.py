"""Collect bounded real GitHub PR/Actions observations for read-only V3.2 audit.

This is a transport, not a trust/acceptance authority. Any API or head change
aborts capture. Never prints credentials, POSTs, or emits CHECKPOINT_FACTS.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

REPO = "reallaksh19/relay-v32-e2e-lab"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def github_get(endpoint: str) -> dict:
    response = subprocess.run(["gh", "api", "-X", "GET", endpoint],
                              text=True, capture_output=True, check=False)
    if response.returncode:
        # Raw stderr could contain arbitrary data, including credentials. Never emit it.
        raise RuntimeError(f"GITHUB_PROVIDER_READ_FAILED: endpoint_family={endpoint.split('/')[2] if len(endpoint.split('/')) > 2 else 'unknown'}")
    return json.loads(response.stdout)


def capture(graph: dict, get: Callable[[str], dict], *, max_runs: int = 30) -> dict:
    if graph.get("programme", {}).get("repository") != REPO:
        raise ValueError("GRAPH_REPOSITORY_MISMATCH")
    if not isinstance(max_runs, int) or not 1 <= max_runs <= 100:
        raise ValueError("MAX_RUNS_OUT_OF_BOUNDS")
    leaves = []
    anchors = []
    for leaf in graph.get("nodes", []):
        if leaf.get("kind") != "LEAF":
            continue
        ref = leaf.get("primary_pr")
        if not isinstance(ref, str) or not ref.startswith(REPO + "#"):
            raise ValueError("LEAF_HAS_NO_EXACT_BOUND_PROVIDER_PR")
        suffix = ref[len(REPO)+1:]
        if not suffix.isdigit() or int(suffix) < 1:
            raise ValueError("INVALID_PR_NUMBER")
        number = int(suffix)
        pr = get(f"repos/{REPO}/pulls/{number}")
        head = (pr.get("head") or {}).get("sha")
        if pr.get("number") != number or not isinstance(head, str) or not SHA.fullmatch(head):
            raise ValueError("PR_NUMBER_OR_SHA_CHANGED")
        runs_payload = get(f"repos/{REPO}/actions/runs?head_sha={head}&per_page=100")
        count = runs_payload.get("total_count")
        if not isinstance(count, int) or count > 100:
            raise ValueError("RUNS_PAGINATION_OR_COUNT_UNVERIFIED")
        runs = []
        for run in runs_payload.get("workflow_runs", []):
            if run.get("head_sha") != head or run.get("event") not in ("push", "pull_request"):
                continue
            if len(runs) >= max_runs:
                raise ValueError("RUNS_TRUNCATED_STOP_INSTEAD_OF_GREEN")
            run_id = run.get("id")
            if not isinstance(run_id, int) or run_id < 1:
                raise ValueError("RUN_ID_INVALID")
            jobs_data = get(f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100")
            job_count = jobs_data.get("total_count")
            if not isinstance(job_count, int) or job_count > 100:
                raise ValueError("JOBS_PAGINATION_UNVERIFIED")
            jobs = []
            for job in jobs_data.get("jobs", []):
                jobs.append({"id": job.get("id"), "name": job.get("name"),
                             "status": job.get("status"), "conclusion": job.get("conclusion"),
                             "runner_name": job.get("runner_name"),
                             "steps": [{"name": step.get("name"), "status": step.get("status"),
                                        "conclusion": step.get("conclusion")}
                                       for step in job.get("steps", [])]})
            runs.append({"id": run_id, "event": run.get("event"),
                         "head_sha": head, "status": run.get("status"),
                         "conclusion": run.get("conclusion"), "jobs": jobs})
        # Whitelist only provider identity/state fields; never archive descriptions,
        # users, comments, or other incidental private PR metadata.
        public_pr = {"number": number, "merged": pr.get("merged"),
                     "head": {"sha": head, "ref": (pr.get("head") or {}).get("ref"),
                              "repo": {"full_name": ((pr.get("head") or {}).get("repo") or {}).get("full_name")}},
                     "base": {"sha": (pr.get("base") or {}).get("sha"),
                              "ref": (pr.get("base") or {}).get("ref"),
                              "repo": {"full_name": ((pr.get("base") or {}).get("repo") or {}).get("full_name")}}}
        leaves.append({"responsibility_id": leaf["responsibility_id"], "pr": public_pr, "runs": runs})
        anchors.append((number, head, pr.get("merged"), pr.get("base", {}).get("sha")))
    if not leaves:
        raise ValueError("NO_LEAVES")
    # Fail closed if provider material moved DURING the multi-source observation.
    for number, head, merged, base_sha in anchors:
        current = get(f"repos/{REPO}/pulls/{number}")
        if (current.get("head", {}).get("sha") != head or
            current.get("base", {}).get("sha") != base_sha or
            current.get("merged") != merged):
            raise ValueError("PROVIDER_CANDIDATE_CHANGED_DURING_OBSERVATION")
    return {"schema": "lab-v32-provider-observation-v1", "repository": REPO,
            "leaves": leaves, "capture_authority": "READ_ONLY_PROVIDER_OBSERVATION_NOT_FACTS_ADMISSION",
            "provider_authenticity": "REQUIRES_OPERATOR_TOKEN_AND_RUN_LOG_ATTESTATION"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
        result = capture(graph, github_get)
        Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("READ_ONLY_PROVIDER_SNAPSHOT_CAPTURED; NO FACTS ADMITTED")
    except (KeyError, TypeError, ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"PROVIDER_CAPTURE_BLOCKED: {exc}")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
