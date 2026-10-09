# Engineering Relay V3.2 — Buddy Runner Stage 1 experiment

**Status:** experimental, source-isolated construction only. Not production.
Tracking: Common issue #879; existing lab responsibility #4.

## Scope: BR-00–BR-03 first slice

1. Actual Agent 1 START must bind a clean checkout to an exact SHA. The recorder
   calls capture-start at that moment; a retrospectively selected commit is not
   observed START evidence.
2. A versioned Stage 1 source allowlist exposes only four original R01 files,
   reading from the PINNED Git object (not the later incumbent working tree).
   Current PR stats, incumbent HOW and incumbent final plan are excluded.
3. Stage 1 WHAT/WHY packet is exact-key filtered. Its free text still requires
   independent contamination review.
4. Runner plan is sealed with an exclusive recorder write, binding original
   manifest digest and independent plan digest. Any Stage 2 must verify first.

## Instructions

Capture from the original clean Agent 1 start checkout:

    python experiments/buddy_runner_v1/runner_stage1.py capture-start \
      --repo . --snapshot /isolated/buddy-run-001 --run buddy-run-001 \
      --start-sha ACTUAL_40_HEX_START_SHA --packet /recorder/what-why.json

The WHAT/WHY packet has precisely five arrays: what, why, pending, known_issues,
parked. The plan has five nonempty arrays: understanding, approach,
rejected_alternatives, assumptions, questions; and one next_action string.

Seal with recorder custody BEFORE disclosing any newer information:

    python experiments/buddy_runner_v1/runner_stage1.py seal \
      --snapshot /isolated/buddy-run-001 \
      --receipt /recorder-only/buddy-run-001.receipt.json \
      --plan /recorder-only/runner-plan.json

Verify:

    python experiments/buddy_runner_v1/runner_stage1.py verify \
      --snapshot /isolated/buddy-run-001 \
      --receipt /recorder-only/buddy-run-001.receipt.json

Test:

    python -m unittest discover -s experiments/buddy_runner_v1 -p 'test_*.py' -v

## Important limitations / remaining work

This is NOT a cryptographic temporal seal or actual runtime sandbox. A hostile
actor with recorder-write access can change both a receipt and its digest.
The final recorder needs independent immutable storage and a disclosure event.
The Buddy runtime must be isolated from all GitHub access, network, credentials,
live repo, current issue comments, and post-cutoff context by the host, not merely
by prompt. Script cannot revoke tools exposed by another agent runtime.

Pending: TIME_FOR_RUNNER advisory in ordinary TASK_EVIDENCE; observed remaining
working-runway estimate; source-authenticated original Owner/issue snapshots;
trusted recorder custody; Stage 2 source and final-plan reconciliation; single
writer promotion; real Agent 1/Runner interruption test; comparative cost trials.

Tests use generated temporary Git repositories. They do NOT prove real agent
takeover, whole V3.2 lifecycle, genuine 70% health measurement, or C6 production
readiness. No Common frozen files or current R01 product were modified.
