"""Fail-closed local V3.2 application test receipt; never publishes CHECKPOINT_FACTS.

The manifest must be checked against real GitHub blob identities by a separate
operator. This machine-produced receipt is replayable, NOT independent custody.
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

SCHEMA = "lab-v32-local-execution-receipt-v1"
TESTS = {
    "R01": ("test_r01_input.py", 4, "R01InputAcceptance"),
    "R02": ("test_r02_compare.py", 3, "R02CompareAcceptance"),
    "R03": ("test_r03_cli.py", 2, "R03CLIAcceptance"),
}
EXPECTED_FILES = frozenset({
    "src/csv_auditor/__init__.py", "src/csv_auditor/parser.py",
    "src/csv_auditor/compare.py", "src/csv_auditor/cli.py",
    "acceptance/test_r01_input.py", "acceptance/test_r02_compare.py",
    "acceptance/test_r03_cli.py",
})
BLOB = re.compile(r"[0-9a-f]{40}\Z")
RESULT = re.compile(r"^(test_[A-Za-z0-9_]+) \((test_r0[123]_[A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\.(test_[A-Za-z0-9_]+)\) \.\.\. ok$", re.MULTILINE)


def git_blob(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def check_manifest(root: Path, manifest: dict) -> dict[str, str]:
    if manifest.get("schema") != "lab-v32-committed-acceptance-manifest-v1":
        raise ValueError("MANIFEST_SCHEMA_INVALID")
    entries = manifest.get("blobs")
    if not isinstance(entries, dict) or set(entries) != EXPECTED_FILES:
        raise ValueError("INCOMPLETE_OR_EXTRA_PINNED_FILE_SET")
    resolved = root.resolve(strict=True)
    observed = {}
    for name, expected in entries.items():
        if not isinstance(expected, str) or not BLOB.fullmatch(expected):
            raise ValueError(f"INVALID_PINNED_BLOB:{name}")
        file = resolved / name
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(resolved):
            raise ValueError(f"UNSAFE_OR_MISSING_SOURCE_PATH:{name}")
        actual = git_blob(file.read_bytes())
        if actual != expected:
            raise ValueError(f"EXACT_SOURCE_BLOB_MISMATCH:{name}")
        observed[name] = actual
    if manifest.get("repository") != "reallaksh19/relay-v32-e2e-lab":
        raise ValueError("WRONG_REPOSITORY")
    if not BLOB.fullmatch(str(manifest.get("base_main_sha") or "")):
        raise ValueError("MISSING_BASE_COMMIT")
    return observed


def execute(root: Path, manifest: dict, *, runner=None) -> dict:
    observed = check_manifest(root, manifest)
    run = runner or subprocess.run
    root = root.resolve()
    entries = []
    for leaf, (filename, count, class_name) in TESTS.items():
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", "acceptance", "-p", filename, "-v"]
        env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1")
        result = run(cmd, cwd=root, env=env, capture_output=True, text=True, check=False)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        found = RESULT.findall(output)
        unique = {(name, module, cls, inner) for name, module, cls, inner in found}
        expected_module = filename.removesuffix(".py")
        strict_collection = (len(found) == count and len(unique) == count and
                             all(module == expected_module and cls == class_name
                                 and name == inner for name, module, cls, inner in found) and
                             re.search(rf"(?m)^Ran {count} tests? in [0-9.]+s$", output) is not None and
                             re.search(r"(?m)^OK$", output) is not None and
                             not re.search(r"(?im)^(FAILED|ERROR|SKIPPED|unexpected success|expected failure)", output))
        if result.returncode != 0 or not strict_collection:
            raise ValueError(f"TEST_EXECUTION_OR_COLLECTION_FAILED:{leaf}:exit={result.returncode}")
        entries.append({"responsibility_id": leaf, "test_file": filename,
                        "actual_collected_test_ids": sorted(f"{module}.{cls}.{name}" for name, module, cls, inner in unique),
                        "actual_tests_run": count, "returncode": result.returncode,
                        "outcome": "LOCAL_PASS_NOT_INDEPENDENT", "log_sha256": hashlib.sha256(output.encode()).hexdigest()})
    return {"schema": SCHEMA, "repository": manifest["repository"],
            "expected_main_sha": manifest["base_main_sha"], "verified_local_git_blobs": observed,
            "tests": entries, "committed_goldens_run": sum(e["actual_tests_run"] for e in entries),
            "operator_attestation": "NOT_PROVIDED", "github_run_attestation": "NOT_EXECUTED_BY_THIS_TOOL",
            "stage2_runner": "STANDBY", "checkpoint_facts_admitted": False,
            "owner_authorization": "WAIVED_NOT_PASSED", "progress_credit": "NONE"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        result = execute(Path(args.root), manifest)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"EXACT_SOURCE_LOCAL_RECEIPT_BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"LOCAL_RECEIPT_WRITTEN: {args.output}; GOLDEN_TESTS={result['committed_goldens_run']}; NO_CHECKPOINT_FACTS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
