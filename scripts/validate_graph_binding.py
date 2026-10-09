"""Fail-closed, data-only verifier for a released V3.2 leaf PR association.

The caller runs this trusted code from the target branch; the candidate contributes
only a JSON execution graph. Native V3.2 validation is an additional mandatory gate.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PR_REF = re.compile(r"^(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(?P<number>[1-9][0-9]*)$")


def strict_json(path: str) -> Any:
    """Reject duplicate JSON fields: otherwise a malicious binding may be ambiguous."""
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"DUPLICATE_JSON_KEY: {key}")
            value[key] = item
        return value
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def verify_binding(before: dict, after: dict, *, changed_paths: list[str],
                   pr: dict | None = None) -> dict[str, Any]:
    if changed_paths != ["governance/released-graph.json"]:
        raise ValueError("NOT_GRAPH_ONLY_CHANGE: exact changed-path allowlist required")
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("GRAPH_MUST_BE_OBJECT")
    if before.get("programme", {}).get("repository") != after.get("programme", {}).get("repository"):
        raise ValueError("REPOSITORY_CHANGED")
    repository = str(before["programme"]["repository"])
    original_nodes = before.get("nodes")
    candidate_nodes = after.get("nodes")
    if not isinstance(original_nodes, list) or not isinstance(candidate_nodes, list):
        raise ValueError("INVALID_NODE_LIST")
    if len(original_nodes) != len(candidate_nodes):
        raise ValueError("NODE_COUNT_CHANGED")
    without_binding = json.loads(json.dumps(after))
    changed: list[tuple[dict, dict]] = []
    for prev, current, scrubbed in zip(original_nodes, candidate_nodes, without_binding["nodes"]):
        if not isinstance(prev, dict) or not isinstance(current, dict):
            raise ValueError("INVALID_NODE")
        if current == prev:
            continue
        if prev.get("kind") != "LEAF" or prev.get("primary_pr") is not None:
            raise ValueError("NON_NEW_LEAF_BINDING")
        if not isinstance(current.get("primary_pr"), str):
            raise ValueError("INVALID_PRIMARY_PR")
        changed.append((prev, current))
        scrubbed.pop("primary_pr", None)
    if len(changed) != 1 or without_binding != before:
        raise ValueError("SEMANTIC_GRAPH_DRIFT: only one null-to-real primary_pr is permitted")
    prev, node = changed[0]
    association = PR_REF.fullmatch(node["primary_pr"])
    if not association or association.group("repository") != repository:
        raise ValueError("INVALID_PR_REPOSITORY")
    if not isinstance(prev.get("candidate_ref"), str) or not prev["candidate_ref"]:
        raise ValueError("MISSING_ORIGINAL_CANDIDATE_BRANCH")
    target_num = int(association.group("number"))
    if pr is not None:
        if pr.get("number") != target_num:
            raise ValueError("WRONG_PROVIDER_PR_NUMBER")
        head, base = pr.get("head") or {}, pr.get("base") or {}
        if (head.get("repo") or {}).get("full_name") != repository:
            raise ValueError("WRONG_PROVIDER_HEAD_REPOSITORY")
        if (base.get("repo") or {}).get("full_name") != repository:
            raise ValueError("WRONG_PROVIDER_BASE_REPOSITORY")
        if head.get("ref") != prev["candidate_ref"]:
            raise ValueError("PR_HEAD_BRANCH_DOES_NOT_MATCH_RELEASED_CANDIDATE_REF")
        if base.get("ref") != before["programme"].get("base_ref", "main"):
            raise ValueError("PR_BASE_BRANCH_MISMATCH")
        if not re.fullmatch(r"[0-9a-f]{40}", str(head.get("sha") or "")):
            raise ValueError("PR_HEAD_SHA_NOT_VERIFIED")
    return {"status": "GRAPH_ONLY_MATERIAL_BINDING", "responsibility_id": node["responsibility_id"],
            "leaf": node["ref"], "primary_pr": node["primary_pr"],
            "candidate_ref": node["candidate_ref"], "source_repository": repository,
            "provider_head_sha": (pr or {}).get("head", {}).get("sha"),
            "semantic_claims_unchanged": True, "progress_credit": "NONE"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--changed-paths", required=True)
    p.add_argument("--provider-pr")
    args = p.parse_args()
    try:
        paths = Path(args.changed_paths).read_text(encoding="utf-8").splitlines()
        result = verify_binding(strict_json(args.base), strict_json(args.candidate), changed_paths=paths,
                                pr=strict_json(args.provider_pr) if args.provider_pr else None)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"GOVERNANCE_BINDING_REJECTED: {exc}") from exc
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
