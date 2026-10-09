# BR-08 Qualification — real namespace rehearsal and GitHub witness readback

Status: PARTIAL / NOT PRODUCTION-QUALIFIED. This is a lab experiment, not the canonical V3.2 protocol, a new product responsibility or a real two-agent handover. Private lab PR #7 remains DRAFT.

## What actually executed

namespace_runner.py invokes the Linux kernel via unshare with user, mount,
network, PID and IPC namespaces. The new root is private tmpfs, with system
executable libraries mounted read-only, the frozen Stage1 input mounted
read-only and a separate empty output mount. The runner executable and
launcher script are checked against SHA-256. The new process runs Python
isolated mode (-I), no-new-privileges, dropped bounding capabilities, and
with no inherited agent environment. If the required namespaces or
executables cannot be obtained, the runner FAILS CLOSED.

ns_fixture_runner.py is a DETERMINISTIC FIXTURE and NOT a second LLM. It reads
only the original baseline, emits a fixed reconstruction-plan illustration,
checks absence of named host paths and actually attempts a direct TCP
connection to 1.1.1.1:443, which must fail. The successful namespace
rehearsal is a real kernel isolation observation, not an adversarial
sandbox certification or an independent cognitive reconstruction result.
Read-only /usr remains mounted for the Python runtime; any real untrusted
agent deployment requires a separate mount, kernel-policy and image audit.

test_episode_rehearsal.py exercises source freeze -> simulated Agent1
implementation commit -> agent-estimated urgent TIME_FOR_RUNNER signal ->
real isolated deterministic fixture subprocess -> sealed plan ->
HMAC-chained local evidence events -> read-only Stage2 reconciliation at
the newer candidate HEAD. It asserts Agent1's private implementation
does not leak into the Stage1 plan. The interruption is SIMULATED.
It neither terminates an actual AI session nor uses a second AI model.

Local test command:
    python -m unittest discover -s experiments/buddy_runner_v1 -p 'test_*.py' -q

Executed on local Python 3.13: 82/82 PASS, including a genuine confined
subprocess and eleven provider-shaped readback checks. This does not
qualify GitHub-hosted test execution or a real independent Runner.

## External witness provider preflight — FAILS CLOSED

provider_readback.py validates claimed distinct author identity, exact
issue comment URL and ID, timestamps, absence of edits, exact signed
witness receipt bytes and publication before disclosure. It refuses
same-actor publication, edited or missing timestamps, changed receipt
or disclosure, wrong origin and reordered events. The input is a
GitHub-provider-shaped snapshot, not an authenticated network fetch;
the verifier always reports STRUCTURALLY_VALIDATED_ONLY.

A real connector readback of Common issue #879 comment 6081342094
returned author reallaksh19 and its previously published evidence body,
but created_at and updated_at were BOTH NULL. This cannot support
provider-certified chronology. Moreover no independent witness actor,
independently provisioned key, signed live receipt or separate disclosure
comment is currently connected. A self-published GitHub comment does not
satisfy independent witness custody.

Ed25519 fixture tests use ephemeral synthetic keys only.

## Exact admission gates still outstanding

1. Externally pinned independent witness identity/key, independent signing
   custody and verifiable provider-published signed receipt.
2. Provider authenticated creation/edit/time evidence and an immutable
   external anchor: editable comments alone are not WORM storage.
3. Actual independent AI Runner reconstructing HOW from the original
   source without future implementation details.
4. Actual interrupted Agent1 and Stage2 AI reconciliation, tested
   source HEAD, Golden fixtures, and independent correctness judgement.
5. Hosted GitHub Actions admission: a shell-only runner-entry-probe still
   fails with no exposed job steps or logs.
6. Owner-granted exclusive writer lease and fencing before issue/source
   writes, promotion or merging.
7. Comparative 50%, 70%, 85% and no-injury controls with real cost,
   correctness and recovery-time measurements.

Verdict: LOCAL MECHANICS ADVANCED. EXTERNAL WITNESS, TRUE AGENT SUCCESSION,
HOSTED CI AND PRODUCTION AUTHORITY REMAIN NOT QUALIFIED.
