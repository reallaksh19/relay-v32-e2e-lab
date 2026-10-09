"""GET-only Common V3.2 projection reconciliation for the real GitHub lab.

This consumes the real immutable DELP engine; does not implement alternative
progress arithmetic, publish facts, or use issue titles as source truth.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

LAB = "reallaksh19/relay-v32-e2e-lab"
ENGINE_BLOB = "804cacca930e47c4528bb0d245efaf941996e4cf"
REQUIRED_ENGINE = "13989969f6b7e432c4f7c1ddfe975449dba53593"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_trusted_engine(path: Path) -> Any:
    if not path.is_file() or path.is_symlink():
        raise ValueError("PINNED_ENGINE_FILE_MISSING_OR_SYMLINK")
    if git_blob(path.read_bytes()) != ENGINE_BLOB:
        raise ValueError("COMMON_V32_ENGINE_BLOB_NOT_PINNED")
    spec = importlib.util.spec_from_file_location("lab_exact_common_v32", path)
    if spec is None or spec.loader is None:
        raise ValueError("ENGINE_NOT_IMPORTABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _projection_once(engine: Any, graph: dict, transport: Any) -> dict:
    indexed = engine.validate_graph(graph)
    if graph["programme"].get("repository") != LAB:
        raise ValueError("WRONG_LAB_REPOSITORY")
    base_ref = graph["programme"].get("base_ref", "main")
    if base_ref != "main":
        raise ValueError("BASE_REF_UNAUTHORIZED")
    base_before = transport.get_commit_sha(base_ref)
    if not isinstance(base_before, str) or not SHA.fullmatch(base_before):
        raise ValueError("PROVIDER_MAIN_SHA_INVALID")
    titles = {ref: str(transport.get_issue(node["number"]).get("title") or "")
              for ref, node in indexed["nodes"].items()}
    # The native engine handles trusted-author association, comments, candidate
    # heads, fact schema and progress. No test-generated ledger is fed here.
    ledger = engine.ledger_from_github(transport, graph)
    observation = engine.observe_github(transport, graph)
    projection = engine.project(graph, ledger, observation)
    base_after = transport.get_commit_sha(base_ref)
    if base_before != base_after:
        raise ValueError("PROVIDER_MAIN_MOVED_DURING_READ")
    rows = []
    for ref, result in projection["nodes"].items():
        if ref not in indexed["nodes"] or ref not in titles:
            raise ValueError("NATIVE_PROJECTION_REF_MISMATCH")
        native = indexed["nodes"][ref]
        drift = engine.title_drift(titles[ref], result["title_prefix"])
        if drift.get("status") not in {"OK", "STALE_OR_HAND_EDITED", "MISSING_PROJECTION", "LEGACY_FORMAT"}:
            raise ValueError("NATIVE_TITLE_DRIFT_UNRECOGNIZED")
        row = {"ref": ref, "kind": native["kind"], "actual_title": titles[ref],
               "native_state": result["state"], "native_lifecycle": result["lifecycle"],
               "native_progress": {k: result["progress"].get(k) for k in
                                  (("P", "E") if native["kind"] == "LEAF" else ("D", "E"))},
               "title_drift": drift["status"], "expected_title": drift["expected"]}
        if native["kind"] == "LEAF":
            if ref not in observation:
                raise ValueError("MISSING_NATIVE_PROVIDER_LEAF_OBSERVATION")
            row["candidate_head"] = observation[ref].get("candidate_sha")
            row["observed_pr_state"] = observation[ref].get("pr_state")
            row["materialization"] = (result.get("materialization") or {}).get("status")
            if row["observed_pr_state"] == "MERGED" and row["native_lifecycle"] == "NOT_STARTED":
                raise ValueError("NATIVE_MERGED_PR_MISTAKEN_FOR_NOT_STARTED")
        rows.append(row)
    return {"source_main_sha": base_before, "native_input_digest": projection["input_digest"],
            "rejected_fact_count": len(projection.get("rejected_facts") or []),
            "ledger_records_observed": len(ledger),
            "nodes": sorted(rows, key=lambda x: x["ref"])}


def reconcile(engine: Any, graph: dict, transport: Any) -> dict:
    first = _projection_once(engine, graph, transport)
    second = _projection_once(engine, graph, transport)
    if first != second:
        raise ValueError("PROVIDER_SNAPSHOT_CHANGED_BETWEEN_READS")
    return {"schema": "lab-v32-native-material-projection-readonly-v1",
            "source_repository": LAB, "pinned_common_engine_commit": REQUIRED_ENGINE,
            "pinned_common_engine_blob": ENGINE_BLOB,
            "outcome": "GET_ONLY_NATIVE_PROJECTION_READBACK",
            "source_main_sha": first["source_main_sha"],
            "native_input_digest": first["native_input_digest"],
            "rejected_fact_count": first["rejected_fact_count"],
            "ledger_records_observed": first["ledger_records_observed"],
            "nodes": first["nodes"],
            "title_drift_count": sum(n["title_drift"] != "OK" for n in first["nodes"]),
            "facts_created": False, "issue_titles_written": False,
            "pr_titles_written": False, "semantic_progress_awarded_by_this_tool": False,
            "scope": "NATIVE_ISSUE_READ_MODEL_ONLY_PR_WRITER_AND_C6_NOT_TESTED",
            "authority": "READ_ONLY_UNTRUSTED_UNTIL_REAL_GITHUB_RUN_ATTESTED"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--graph", required=True)
    p.add_argument("--engine", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
        engine = load_trusted_engine(Path(args.engine))
        report = reconcile(engine, graph, engine.GhTransport(LAB))
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError, AttributeError) as exc:
        print(f"NATIVE_PROJECTION_PROBE_BLOCKED:{exc}", file=sys.stderr)
        return 2
    print("READ_ONLY_NATIVE_DELP_OBSERVED; "+str(report["title_drift_count"])+" DRIFTED TITLES; NO FACTS CREATED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
