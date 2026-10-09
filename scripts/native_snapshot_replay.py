"""Read-only offline replay of a real GitHub lab snapshot through pinned Common DELP.

Snapshot is private provider material and MUST NOT be committed by this script.
It is an operator-collected record, not an authenticated evidence or Owner decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable

REPO = "reallaksh19/relay-v32-e2e-lab"
SCHEMA = "lab-v32-native-provider-snapshot-v1"
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_COMMENTS_PER_LEAF = 1000
# Approved lab graph version; changing plan/claim/trust input requires an explicit
# separately reviewed release pin, never a self-consistent caller snapshot.
RELEASED_GRAPH_BLOB = "fde7e1fbd0c71efb64a678206f0bc9f32e36f6c8"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def require_released_graph(graph: dict, raw_graph: bytes) -> None:
    """Guard released graph custody before any provider read or offline replay.

    Snapshot-internal checksum agreement is insufficient: an attacker could
    rehash an altered graph and an altered snapshot together.
    """
    if git_blob(raw_graph) != RELEASED_GRAPH_BLOB:
        raise ValueError("RELEASED_GRAPH_SOURCE_BLOB_NOT_PINNED")
    try:
        from_bytes = json.loads(raw_graph)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("RELEASED_GRAPH_SOURCE_NOT_JSON") from exc
    if from_bytes != graph:
        raise ValueError("GRAPH_MAPPING_DIFFERS_FROM_PINNED_BYTES")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                  separators=(",", ":")).encode("utf-8")).hexdigest()


def _number(ref: str, repo: str = REPO) -> int:
    if not isinstance(ref, str) or not ref.startswith(repo + "#"):
        raise ValueError("PROVIDER_BINDING_REPOSITORY_MISMATCH")
    suffix = ref[len(repo) + 1:]
    if not suffix.isdigit() or int(suffix) < 1:
        raise ValueError("PROVIDER_BINDING_INVALID_NUMBER")
    return int(suffix)


def _layout(graph: dict) -> tuple[list[int], dict[int, dict], list[int]]:
    if graph.get("programme", {}).get("repository") != REPO:
        raise ValueError("GRAPH_REPOSITORY_MISMATCH")
    if graph["programme"].get("base_ref", "main") != "main":
        raise ValueError("GRAPH_BASE_UNAUTHORIZED")
    numbers, leaves, prs = [], {}, []
    for node in graph.get("nodes", []):
        no = _number(node["ref"])
        if no in numbers:
            raise ValueError("DUPLICATE_GRAPH_ISSUE")
        numbers.append(no)
        if node.get("kind") == "LEAF":
            prs.append(_number(node["primary_pr"]))
            if node.get("candidate_ref") not in ("lab/r01", "lab/r02", "lab/r03"):
                raise ValueError("UNRELEASED_LEAF_CANDIDATE_REF")
            leaves[no] = node
    if len(numbers) != 6 or len(leaves) != 3 or len(set(prs)) != 3:
        raise ValueError("GRAPH_SHAPE_NOT_RELEASED_LAB")
    return sorted(numbers), leaves, sorted(prs)


def validate_snapshot(graph: dict, graph_bytes: bytes, snap: dict) -> None:
    require_released_graph(graph, graph_bytes)
    issues, leaves, prs = _layout(graph)
    if snap.get("schema") != SCHEMA or snap.get("repository") != REPO:
        raise ValueError("SNAPSHOT_SCHEMA_OR_REPO_MISMATCH")
    if snap.get("graph_git_blob") != git_blob(graph_bytes):
        raise ValueError("SNAPSHOT_GRAPH_BLOB_MISMATCH")
    if not SHA.fullmatch(str(snap.get("main_sha", ""))):
        raise ValueError("SNAPSHOT_MAIN_SHA_INVALID")
    if snap.get("main_sha") != snap.get("final_main_sha"):
        raise ValueError("SNAPSHOT_MAIN_MOVED_DURING_CAPTURE")
    issue_dict, pull_dict, comments_dict = snap.get("issues"), snap.get("pulls"), snap.get("comments")
    if not isinstance(issue_dict, dict) or set(issue_dict) != set(map(str, issues)):
        raise ValueError("SNAPSHOT_ISSUE_SET_INCOMPLETE")
    if not isinstance(pull_dict, dict) or set(pull_dict) != set(map(str, prs)):
        raise ValueError("SNAPSHOT_PR_SET_INCOMPLETE")
    if not isinstance(comments_dict, dict) or set(comments_dict) != set(map(str, leaves)):
        raise ValueError("SNAPSHOT_COMMENT_SET_INCOMPLETE")
    for key, issue in issue_dict.items():
        if not isinstance(issue, dict) or not isinstance(issue.get("title"), str):
            raise ValueError(f"SNAPSHOT_ISSUE_TITLE_INVALID:{key}")
    for leaf_num, leaf in leaves.items():
        pr_num = _number(leaf["primary_pr"])
        p = pull_dict[str(pr_num)]
        if p.get("number") != pr_num or p.get("merged") is not True:
            raise ValueError("SNAPSHOT_PR_NUMBER_OR_MERGE_INVALID")
        head, base = p.get("head") or {}, p.get("base") or {}
        if (head.get("repo") or {}).get("full_name") != REPO or (base.get("repo") or {}).get("full_name") != REPO:
            raise ValueError("SNAPSHOT_PR_REPO_MISMATCH")
        if head.get("ref") != leaf["candidate_ref"] or base.get("ref") != "main":
            raise ValueError("SNAPSHOT_PR_BRANCH_MISMATCH")
        if not SHA.fullmatch(str(head.get("sha", ""))) or not SHA.fullmatch(str(base.get("sha", ""))):
            raise ValueError("SNAPSHOT_PR_COMMIT_INVALID")
        comments = comments_dict[str(leaf_num)]
        if not isinstance(comments, list) or len(comments) > MAX_COMMENTS_PER_LEAF:
            raise ValueError("SNAPSHOT_COMMENTS_UNBOUNDED")
        seen = set()
        for c in comments:
            if not isinstance(c, dict) or not isinstance(c.get("body"), str):
                raise ValueError("SNAPSHOT_COMMENT_INVALID")
            if not isinstance(c.get("id"), int) or c["id"] <= 0 or c["id"] in seen:
                raise ValueError("SNAPSHOT_COMMENT_ID_REPEATED_OR_INVALID")
            seen.add(c["id"])
            if not isinstance((c.get("user") or {}).get("login"), str) or not isinstance(c.get("author_association"), str):
                raise ValueError("SNAPSHOT_COMMENT_AUTHOR_NOT_GROUNDED")
    if snap.get("source_kind") != "GITHUB_GET_ONLY_UNATTESTED":
        raise ValueError("SNAPSHOT_FALSE_AUTHORITY")


class SnapshotTransport:
    """Exact subset of native GhTransport reads; deliberately no write methods."""
    def __init__(self, snapshot: dict):
        self.s = snapshot

    def get_commit_sha(self, ref: str) -> str:
        if ref != "main":
            raise ValueError("UNRELEASED_BASE_REF")
        return self.s["main_sha"]

    def get_issue(self, number: int) -> dict:
        return dict(self.s["issues"][str(number)])

    def get_pull(self, number: int) -> dict:
        return json.loads(json.dumps(self.s["pulls"][str(number)]))

    def list_comments(self, number: int) -> list:
        return json.loads(json.dumps(self.s["comments"][str(number)]))


def replay(graph: dict, graph_bytes: bytes, snapshot: dict, pinned_engine: Any) -> dict:
    validate_snapshot(graph, graph_bytes, snapshot)
    transport = SnapshotTransport(snapshot)
    # Native engine, not an emulated progress formula or hand-authored facts.
    native = pinned_engine.plan_github(transport, graph)
    if not isinstance(native.get("input_digest"), str) or not native["input_digest"].startswith("sha256:"):
        raise ValueError("NATIVE_INPUT_DIGEST_INVALID")
    if set(native.get("expected_titles", {})) != {n["ref"] for n in graph["nodes"]}:
        raise ValueError("NATIVE_TITLE_COVERAGE_INCOMPLETE")
    return {"schema": "lab-v32-native-offline-readback-v1", "main_sha": snapshot["main_sha"],
            "graph_git_blob": snapshot["graph_git_blob"], "source_snapshot_sha256": sha256_json(snapshot),
            "native_input_digest": native["input_digest"],
            "native_expected_titles": native["expected_titles"], "native_title_drift": native["drift"],
            "rejected_native_facts": native["rejected_facts"],
            "source_view_drift_count": native["would_write_titles"],
            "fact_admission": "NOT_PERFORMED", "issue_or_pr_writes": False,
            "provider_authentication": "EXTERNAL_CAPTURE_NOT_INDEPENDENTLY_ATTESTED",
            "owner_approval": "WAIVED_NOT_PASSED", "progress_credit": "NONE"}


def _get(endpoint: str) -> Any:
    p = subprocess.run(["gh", "api", "-X", "GET", endpoint], capture_output=True, text=True)
    if p.returncode:
        raise ValueError("PROVIDER_GET_FAILED")  # no raw stderr (may contain secrets)
    return json.loads(p.stdout)


def _pull(p: dict) -> dict:
    return {"number": p.get("number"), "merged": p.get("merged"),
            "head": {"ref": p.get("head", {}).get("ref"), "sha": p.get("head", {}).get("sha"),
                     "repo": {"full_name": p.get("head", {}).get("repo", {}).get("full_name")}},
            "base": {"ref": p.get("base", {}).get("ref"), "sha": p.get("base", {}).get("sha"),
                     "repo": {"full_name": p.get("base", {}).get("repo", {}).get("full_name")}}}


def capture(graph: dict, raw_graph: bytes, fetch: Callable[[str], Any] = _get) -> dict:
    require_released_graph(graph, raw_graph)  # Zero GitHub GETs on an unapproved graph.
    issues, leaves, prs = _layout(graph)
    main = fetch(f"repos/{REPO}/commits/main")["sha"]
    titles = {str(n): {"title": fetch(f"repos/{REPO}/issues/{n}")["title"]} for n in issues}
    pulls = {str(n): _pull(fetch(f"repos/{REPO}/pulls/{n}")) for n in prs}
    comments: dict[str, list] = {}
    for n in leaves:
        found = []
        page = 1
        while True:
            batch = fetch(f"repos/{REPO}/issues/{n}/comments?per_page=100&page={page}")
            if not isinstance(batch, list):
                raise ValueError("PROVIDER_COMMENT_PAGE_NOT_LIST")
            for c in batch:
                found.append({"id": c["id"], "body": c["body"],
                              "user": {"login": (c.get("user") or {}).get("login")},
                              "author_association": c.get("author_association")})
            if len(found) > MAX_COMMENTS_PER_LEAF:
                raise ValueError("PROVIDER_COMMENT_CUSTODY_UNBOUNDED")
            if len(batch) < 100:
                break
            page += 1
        comments[str(n)] = found
    # Detect concurrent provider mutation across all protected observation classes.
    for n in issues:
        if fetch(f"repos/{REPO}/issues/{n}").get("title") != titles[str(n)]["title"]:
            raise ValueError("ISSUE_TITLE_CHANGED_DURING_CAPTURE")
    for n in prs:
        if _pull(fetch(f"repos/{REPO}/pulls/{n}")) != pulls[str(n)]:
            raise ValueError("PR_CHANGED_DURING_CAPTURE")
    for n in leaves:
        again = []
        page = 1
        while True:
            batch = fetch(f"repos/{REPO}/issues/{n}/comments?per_page=100&page={page}")
            if not isinstance(batch, list):
                raise ValueError("PROVIDER_COMMENT_PAGE_NOT_LIST")
            again.extend({"id": c["id"], "body": c["body"],
                          "user": {"login": (c.get("user") or {}).get("login")},
                          "author_association": c.get("author_association")} for c in batch)
            if len(again) > MAX_COMMENTS_PER_LEAF:
                raise ValueError("PROVIDER_COMMENT_CUSTODY_UNBOUNDED")
            if len(batch) < 100:
                break
            page += 1
        if sha256_json(again) != sha256_json(comments[str(n)]):
            raise ValueError("COMMENTS_CHANGED_DURING_CAPTURE")
    final_main = fetch(f"repos/{REPO}/commits/main")["sha"]
    out = {"schema": SCHEMA, "repository": REPO, "graph_git_blob": git_blob(raw_graph),
           "main_sha": main, "final_main_sha": final_main, "source_kind": "GITHUB_GET_ONLY_UNATTESTED",
           "issues": titles, "pulls": pulls, "comments": comments}
    validate_snapshot(graph, raw_graph, out)
    return out


def _private_save(path: Path, data: dict) -> None:
    if path.is_symlink() or path.exists():
        raise ValueError("REPLAY_OUTPUT_PATH_ALREADY_EXISTS_OR_SYMLINK")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("capture", "replay"))
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--engine", type=Path)
    p.add_argument("--output", type=Path)
    opts = p.parse_args()
    try:
        raw = opts.graph.read_bytes()
        graph = json.loads(raw)
        if opts.mode == "capture":
            _private_save(opts.snapshot, capture(graph, raw))
            print("GET_ONLY_SNAPSHOT_SAVED_LOCALLY; PRIVATE; NOT_ATTESTED; NO_FACTS")
        else:
            if not opts.engine or not opts.output:
                raise ValueError("REPLAY_REQUIRES_ENGINE_AND_OUTPUT")
            # Import the existing immutable engine guard, not a second authority.
            from native_material_status_probe import load_trusted_engine
            engine = load_trusted_engine(opts.engine)
            snapshot = json.loads(opts.snapshot.read_text(encoding="utf-8"))
            _private_save(opts.output, replay(graph, raw, snapshot, engine))
            print("ACTUAL_NATIVE_ENGINE_OFFLINE_REPLAY; LOCAL_SNAPSHOT_UNATTESTED; NO_WRITES")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("NATIVE_OFFLINE_REPLAY_BLOCKED:" + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
