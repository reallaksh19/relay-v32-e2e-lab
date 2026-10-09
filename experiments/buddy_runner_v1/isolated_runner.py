"""BR-07 fail-closed containerized Stage1 Runner launcher (experimental).

Runs only a digest-pinned pre-reviewed external Runner image, not an LLM
instance. No credentials, network, live repository, agent logs, PR or host
home directory are mounted. Host Docker policy/image provenance still require
independent qualification. There is NEVER an unsandboxed fallback.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

from runner_stage1 import Stage1Error, R01_PATHS, validate_snapshot
from runner_protocol import verify_activation

IMAGE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/-]*@sha256:[a-f0-9]{64}$")


def _require(ok, message):
    if not ok:
        raise Stage1Error(message)


def _tree_inventory(directory):
    return {p.relative_to(directory).as_posix(): p for p in directory.rglob("*")
            if p.is_file() or p.is_symlink()}


def validate_stage1_input(snapshot):
    base = Path(snapshot)
    _require(base.is_dir() and not base.is_symlink(), "RUNNER_SNAPSHOT_INVALID")
    validate_snapshot(base)
    verify_activation(base)
    observed = _tree_inventory(base)
    allowed = {"manifest.json", "activation.json"} | {"source/" + p for p in R01_PATHS}
    _require(set(observed) == allowed, "RUNNER_EXTRA_SNAPSHOT_CONTENT")
    for item in observed.values():
        _require(not item.is_symlink(), "RUNNER_SNAPSHOT_SYMLINK")
    return base.resolve()


def build_command(snapshot, output, *, image, approved_image):
    """Construct a fixed Docker argv, with no shell, mounts or env from Runner."""
    _require(type(image) is str and bool(IMAGE.fullmatch(image)), "RUNNER_IMAGE_NOT_DIGEST_PINNED")
    _require(type(approved_image) is str and image == approved_image,
             "RUNNER_IMAGE_NOT_OWNER_APPROVED")
    source = validate_stage1_input(snapshot)
    output = Path(output)
    _require(output.is_dir() and not output.is_symlink(), "RUNNER_OUTPUT_NOT_DIRECTORY")
    dest = output.resolve()
    _require(not dest.is_relative_to(source) and not source.is_relative_to(dest),
             "RUNNER_OUTPUT_OVERLAPS_SOURCE")
    _require(not any(dest.iterdir()), "RUNNER_OUTPUT_NOT_EMPTY")
    _require(all("," not in str(p) and "\n" not in str(p) and "\r" not in str(p)
                 for p in (source, dest)), "RUNNER_MOUNT_PATH_UNSAFE")
    _require(os.name == "posix", "RUNNER_PLATFORM_UNSUPPORTED")
    return [
        "docker", "run", "--rm", "--pull", "never", "--network", "none",
        "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "64", "--memory", "512m", "--cpus", "1",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "--mount", f"type=bind,src={source},dst=/blind,readonly",
        "--mount", f"type=bind,src={dest},dst=/output",
        "--tmpfs", "/tmp:rw,nosuid,noexec,size=32m",
        image,
    ]


def launch(snapshot, output, *, image, approved_image, timeout=600):
    _require(type(timeout) is int and 1 <= timeout <= 3600, "RUNNER_TIMEOUT_INVALID")
    args = build_command(snapshot, output, image=image, approved_image=approved_image)
    binary = shutil.which("docker")
    _require(binary is not None, "ISOLATED_RUNTIME_UNAVAILABLE_NO_FALLBACK")
    args[0] = binary
    # The Docker host remains privileged; only a trusted recorder may launch.
    # Restrict host process environment: no inherited tokens or GitHub config.
    try:
        result = subprocess.run(args, env={"PATH": "/usr/bin:/bin", "LANG": "C",
                                           "HOME": "/nonexistent"},
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=timeout, check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise Stage1Error("ISOLATED_RUNNER_FAILED_OR_TIMED_OUT") from exc
    _require(result.returncode == 0, "ISOLATED_RUNNER_EXIT_NONZERO")
    return {"status": "PROCESS_EXITED_SUCCESSFULLY",
            "sandbox": "DIGEST_PINNED_DOCKER_NO_NETWORK_NO_HOST_HOME",
            "independent_reconstruction_accuracy": "NOT_EVALUATED",
            "host_isolation_attestation": "REQUIRES_EXTERNAL_PROVIDER_EVIDENCE",
            "execution_authority": "NOT_GRANTED"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--approved-image", required=True,
                    help="Must be independently Owner-pinned; CLI equality is not approval")
    args = ap.parse_args()
    try:
        print(launch(args.snapshot, args.output, image=args.image,
                     approved_image=args.approved_image))
    except (Stage1Error, OSError) as exc:
        ap.exit(2, f"ISOLATION_FAIL_CLOSED: {exc}\n")


if __name__ == "__main__":
    main()
