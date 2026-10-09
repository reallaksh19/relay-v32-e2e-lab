# V3.2 lab — private provider snapshot and genuine Common-native offline replay

STATUS: IMPLEMENTED LOCALLY; FULL REAL PROVIDER + PINNED COMMON REPLAY NOT YET EXECUTED. FACTS ADMITTED: NONE.

## Why this exists

The lab's released graph binds merged application PRs #8, #13 and #15 to R01–R03. The pinned Common V3.2 engine distinguishes a merged PR with no accepted facts (UNMATERIALIZED) from no work (NOT_STARTED). GitHub Actions has repeatedly failed before runner startup, so the existing hosted GET-only native materialization workflow cannot establish the real present state.

This implementation provides an alternative local read-only capture/replay route to the SAME real Common DELP engine, not another projection algorithm or a fake facts ledger.

## Source contracts

- Lab: reallaksh19/relay-v32-e2e-lab, current governance/released-graph.json; last verified blob fde7e1fbd0c71efb64a678206f0bc9f32e36f6c8.
- Common native engine: commit 13989969f6b7e432c4f7c1ddfe975449dba53593; delp_projection_v32.py blob 804cacca930e47c4528bb0d245efaf941996e4cf.
- Engine is imported ONLY through existing native_material_status_probe.load_trusted_engine after immutable Git blob check.
- Snapshot contains six real issue titles, all comments of leaf issues #4/#5/#6 with GitHub ID, login, author association and full body, current PR head/base/ref/merged material for PRs #8/#13/#15, observed main SHA, source graph blob and a second full provider reread.
- Snapshot and report are local-only, exclusively created with mode 0600. NO PRIVILEGED/PRIVATE COMMENT TEXT SHOULD BE COMMITTED OR UPLOADED.

## Actual local commands

From a current lab main checkout, with GitHub CLI authentication and an immutable Common checkout:

    python -m unittest discover -s tests -p test_native_snapshot_replay.py -v

    python scripts/native_snapshot_replay.py capture \
      --graph governance/released-graph.json \
      --snapshot /tmp/v32-private-snapshot.json

    python scripts/native_snapshot_replay.py replay \
      --graph governance/released-graph.json \
      --snapshot /tmp/v32-private-snapshot.json \
      --engine /path/to/Common/skills/engineering-pr-delivery-v3.2/scripts/delp_projection_v32.py \
      --output /tmp/v32-offline-report.json

The capture performs only gh api -X GET. It rejects missing provider material, changed PR heads/base/merged state, changed issue title or comments, duplicate comment identity, incomplete/unbounded source and changed main SHA.

The replay refuses changed graph bytes, invalid bindings, missing comments, unmerged PRs or incompatible source. It adapts the snapshot into the exact native transport reads; invokes real Common plan_github (which calls its own ledger_from_github, observe_github, project and title_drift); and outputs expected titles, drift, rejected facts and source/input digests. It has NO write API and no manual P/E/D math.

## Verification and boundaries

- All 22 local tests of the transport, source/graph identity, moving input, fake attestation, read-only contract and private output passed.
- Source/test git object SHAs: 0fe0f171596e5f00984233b3376a5c3a436ef6d8 and d50932ba747d3fd3868d0987179908eff6b60b9c.
- The 22 tests use a deliberately fake Common engine to verify the transport contract; they DO NOT count as executing the actual immutable Common source against live GitHub data.
- A self-captured snapshot digest is not independent provider/Owner attestation. It must never be interpreted as accepted CHECKPOINT_FACTS_V1 or automatic authorization to rewrite titles.
- Original 9 committed application golden tests passed locally; independent witness and hosted execution are still missing. Original T05 Owner grant remains WAIVED_NOT_PASSED. Buddy Runner remains in standby.

## Next qualification

Perform real local GET-only capture and actual pinned Common native replay, preserve hash and observed main SHA, verify expected-vs-actual issue titles and the exact rejected facts. Have a separate trusted actor audit source/CI and Owner custody. Only then propose fact admission or authorized native issue/PR writing, with changed-input fail-closed reread and publication idempotence. Finally exercise C6 cold successor. No positive E2E acceptance can be inferred from this PR alone.
