# P3/P4 — native materialization vs issue title reconciliation

**State: SOURCE IMPLEMENTED; NATIVE LIVE EXECUTION NOT YET QUALIFIED.**

## Basis and observed conflict

Common V3.2 source pin: `13989969f6b7e432c4f7c1ddfe975449dba53593`; `delp_projection_v32.py` Git blob `804cacca930e47c4528bb0d245efaf941996e4cf`.

The lab's released graph binds real merged source PRs R01→#8, R02→#13, R03→#15. Its previous issue titles at readback showed:

- Root #1: `D0/E0 · WAITING`
- R01 #4: `P0/E0 · NOT_STARTED`
- R02 #5, R03 #6: `P0/E0 · WAITING_DEPENDENCY`

The zero *numbers* can remain legitimate without accepted facts; however, the native engine's `compute_leaf` source recognizes `pr_state=MERGED` when records are absent and derives `lifecycle=UNMATERIALIZED` / `state=UNMATERIALIZED` (native lines 2982–3009). Root/phase roll-up also prioritizes `UNMATERIALIZED` (lines 3341–3347). Therefore `NOT_STARTED` and `WAITING_DEPENDENCY` are not a reliable current material presentation until the exact live native read is executed.

## HOW this implementation addresses the actual source

`scripts/native_material_status_probe.py` imports the **real** immutable Common V3.2 engine, rejecting a mismatched engine Git blob before Python import. It reuses `validate_graph`, `ledger_from_github`, `observe_github`, `project` and `title_drift`; it contains **no shadow P/E/D arithmetic** and writes neither issues nor facts.

One read: fetch real issue titles, actual comments with native author restrictions, real provider PR heads and the main commit. Compute native projection and expected titles. Repeat the entire read once and reject if main SHA, native input digest, comments, PR material or issue titles changed. Reject if merged PR is reported as `NOT_STARTED`. The workflow requires the observed main SHA to equal the exact event SHA, so even source-consistent historical observations are not misreported as current.

Output: a machine-readable read-only report for all six nodes, containing actual and expected titles, native state/lifecycle, node progress, PR/material identity, changed-title count, accepted/rejected-facts metadata, native input digest and explicit zero-writes flags.

`tests/test_native_material_status_probe.py`: 16 orchestrator positive/negative tests with a deliberately injected test double, **not** a substitute for executing the real pinned Common projector. Covers graph/repository/base/engine SHA rejection, moving main, changing comments, moving titles, moving native input digest, missing provider observation, merged-as-not-started regression, and exact event SHA positive/negative controls.

`.github/workflows/v32-native-material-state-readonly.yml` uses main-only trigger, trusted checkout at exact `GITHUB_SHA`, read-only issue/PR access, immutable Common pin, 16 local gate controls, actual native `GhTransport` provider observation, and a report artifact. It has no `issues: write`, no source writer, no structured checkpoint emission and no PR metadata patch.

## What is still NOT delivered

1. **Live execution:** Actions in this lab have repeatedly failed before allocating runners or executing steps. This workflow must actually execute native Common code, succeed and publish a verifiable artifact at an observed source SHA. Until then its expected output is a source-grounded hypothesis, not a completed native GitHub test.
2. **Facts admission:** Local receipt PR #19 proves nine committed tests were executed *locally*, but its operator attestation is `NOT_PROVIDED`. No source-independent witness or admissible V3.2 `CHECKPOINT_FACTS_V1` has been established. Progress must not be fabricated to change the displayed zero values.
3. **Issue publisher:** After a stable native GET-only observation, the authorized native publisher must preserve human-owned issue text, avoid epoch races, and independently verify readback and idempotence. This diagnostic does **not** publish titles and does not resolve the Owner T05 `WAIVED_NOT_PASSED` gate.
4. **PR view / C6:** Real draft/merged PR title and managed description consistency, acceptance-qualified source/CI facts and actual cold successor native C6 remain separate responsibilities.

## Exact next safe step

Execute the trusted GET-only job against a stable lab main and archive the native JSON. Compare its expected title states with actual issue/phase/root titles and ledger, without writing. If source and allowed authority subsequently permit, update derived issue titles through the single native writer and verify second-pass idempotence. Continue to independent acceptance and PR/C6 qualification; do not claim a complete V3.2 lifecycle from this report alone.

The Buddy Runner remains in standby; it is not promoted by this work.
