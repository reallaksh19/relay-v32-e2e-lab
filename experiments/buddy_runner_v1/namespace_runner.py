"""BR-08 experimental Linux namespace fixture runner; no unsafe fallback.

This executes a deterministic tool in a real new user/mount/network/PID namespace.
No LLM model/runtime is provided. Caller supplies a separately approved tool
and approved launcher digests; CLI equality alone is NOT an Owner authorization.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from isolated_runner import validate_stage1_input
from runner_stage1 import Stage1Error

SHA256 = re.compile(r"^sha256:[a-f0-9]{64}$")

def _require(condition, reason):
    if not condition:
        raise Stage1Error(reason)


def _digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _regular_file(path):
    p = Path(path)
    _require(p.is_file() and not p.is_symlink() and p.stat().st_size <= 1_000_000,
             "NAMESPACE_UNTRUSTED_PROGRAM")
    return p.resolve()


def run_fixture(snapshot, output, root, *, runner_program, approved_program_digest,
                entry_script, approved_entry_digest, timeout=20):
    _require(os.name == "posix" and os.path.exists("/proc/self/ns/user"),
             "NAMESPACE_LINUX_REQUIRED")
    _require(type(timeout) is int and 1 <= timeout <= 120,
             "NAMESPACE_TIMEOUT_INVALID")
    inp = validate_stage1_input(snapshot)
    dest = Path(output)
    newroot = Path(root)
    _require(dest.is_dir() and not dest.is_symlink() and not list(dest.iterdir()),
             "NAMESPACE_OUTPUT_NOT_EMPTY")
    _require(newroot.is_dir() and not newroot.is_symlink() and not list(newroot.iterdir()),
             "NAMESPACE_ROOT_NOT_EMPTY")
    dest, newroot = dest.resolve(), newroot.resolve()
    _require(len({str(inp), str(dest), str(newroot)}) == 3 and
             all(not a.is_relative_to(b) for a in (inp, dest, newroot) for b in
                 (inp, dest, newroot) if a != b), "NAMESPACE_PATH_OVERLAP")
    program = _regular_file(runner_program)
    entry = _regular_file(entry_script)
    for path, digest in ((program, approved_program_digest), (entry, approved_entry_digest)):
        _require(type(digest) is str and SHA256.fullmatch(digest) and digest == _digest(path),
                 "NAMESPACE_TOOL_DIGEST_NOT_APPROVED")
        _require(not path.is_relative_to(inp) and not path.is_relative_to(dest) and
                 not path.is_relative_to(newroot), "NAMESPACE_PROGRAM_IN_UNTRUSTED_DIR")
    _require(all("\n" not in str(p) and "\r" not in str(p) for p in (inp, dest, newroot, program, entry)),
             "NAMESPACE_BAD_PATH")
    binaries = [shutil.which(i) for i in ("unshare", "mount", "chroot", "setpriv", "sh")]
    _require(all(binaries), "NAMESPACE_TOOLCHAIN_UNAVAILABLE_NO_FALLBACK")
    argv = [binaries[0], "--user", "--map-root-user", "--mount", "--net", "--pid",
            "--fork", "--ipc", binaries[4], str(entry), str(newroot), str(inp),
            str(dest), str(program)]
    # No credential/network/tool variables inherited by the child process.
    try:
        p = subprocess.run(argv, capture_output=True, text=True, check=False,
                           timeout=timeout, stdin=subprocess.DEVNULL,
                           env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C",
                                "HOME": "/nonexistent"})
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stage1Error("NAMESPACE_EXECUTION_UNAVAILABLE_NO_FALLBACK") from exc
    _require(p.returncode == 0, "NAMESPACE_EXECUTION_REJECTED:" + p.stderr[-250:])
    _require((dest / "fixture_result.json").is_file() and
             not (dest / "fixture_result.json").is_symlink(),
             "NAMESPACE_EXPECTED_RECEIPT_MISSING")
    result = json.loads((dest / "fixture_result.json").read_text(encoding="utf-8"))
    _require(type(result) is dict and result.get("network") == "DENIED" and
             result.get("host_credentials") == "UNMOUNTED" and
             result.get("writer_authority") == "NOT_GRANTED" and
             result.get("runner_type") == "DETERMINISTIC_TEST_FIXTURE_NOT_LLM",
             "NAMESPACE_FIXTURE_CLAIM_INVALID")
    return {"schema": "v32-buddy-namespace-rehearsal-v1", "status": "ISOLATED_FIXTURE_EXECUTED",
            "runtime": "LINUX_USER_MOUNT_NET_PID_IPC_NAMESPACE_WITH_CHROOT",
            "tool_digest": _digest(program), "entry_digest": _digest(entry),
            "fixture_result_digest": _digest(dest / "fixture_result.json"),
            "network_observed": "DENIED_BY_ACTUAL_SOCKET_ATTEMPT",
            "filesystem_observed": "EXPECTED_HOST_PATHS_INACCESSIBLE",
            "llm_agent": "NOT_EXECUTED", "live_interruption": "NOT_EXECUTED",
            "provider_witness": "NOT_QUALIFIED", "execution_authority": "NOT_GRANTED"}
