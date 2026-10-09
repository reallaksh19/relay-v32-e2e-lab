# TASK_EVIDENCE — LAB-T01 — V3.2 source pin and native-engine eligibility PASS

**Experiment:** Common V3.2 CSV Auditor private GitHub lab; governed by `reallaksh19/Common#876`.

- **Task ID:** LAB-T01
- **Status:** PASS
- **Operator/agent identity:** Antigravity local agent (authenticated via `gh` CLI as `reallaksh19`)
- **Repository:** `reallaksh19/relay-v32-e2e-lab` (NOT_CREATED; local starter at `C:\CodeB\relay-v32-e2e-lab-starter`, Common cloned at `C:\CodeB\Common`)
- **Protocol:** `reallaksh19/Common@13989969f6b7e432c4f7c1ddfe975449dba53593:skills/engineering-pr-delivery-v3.2`
- **Executed material SHA:** `13989969f6b7e432c4f7c1ddfe975449dba53593`
- **Commands executed:**
  1. `gh repo clone reallaksh19/Common ..\Common`
  2. `git -C ..\Common checkout 13989969f6b7e432c4f7c1ddfe975449dba53593`
  3. `git -C ..\Common rev-parse HEAD`
  4. `Test-Path ..\Common\skills\engineering-pr-delivery-v3.2\scripts\delp_projection_v32.py`
  5. `python ..\Common\skills\engineering-pr-delivery-v3.2\scripts\delp_projection_v32.py --help`
- **Exit code(s):**
  1. `0`
  2. `0` (switched to detached HEAD `13989969`)
  3. `0` (`13989969f6b7e432c4f7c1ddfe975449dba53593`)
  4. `0` (`True`)
  5. `0` (DELP V3.2 usage banner printed)
- **Expected independent oracle:**
  - Authenticated clone of private `reallaksh19/Common` succeeds.
  - Checkout of pinned SHA `13989969f6b7e432c4f7c1ddfe975449dba53593` succeeds.
  - `git rev-parse HEAD` returns exact 40-hex string `13989969f6b7e432c4f7c1ddfe975449dba53593`.
  - Path `skills/engineering-pr-delivery-v3.2/scripts/delp_projection_v32.py` exists (V3.2 native engine, not V3.5).
  - Script `--help` exits 0 with `DELP V3.2: facts in, projections out.` banner and 11 subcommands.
- **Observed actual output:**
  - Git rev-parse:
    ```text
    13989969f6b7e432c4f7c1ddfe975449dba53593
    ```
  - Engine help excerpt:
    ```text
    usage: delp_projection_v32.py [-h]
                                  {validate-graph,validate-facts,decompose-check,graph-diff,frontier,frontier-verify,health,project,admit,verify-titles,sync-github}
                                  ...

    DELP V3.2: facts in, projections out.
    ```
- **Result comparison:** MATCH — Pinned source commit verified bit-for-bit. Engine availability confirmed.
- **Durable source refs:**
  - Governing issue: https://github.com/reallaksh19/Common/issues/876
  - Common pinned commit: https://github.com/reallaksh19/Common/commit/13989969f6b7e432c4f7c1ddfe975449dba53593
  - Target lab repository: NOT_CREATED (`reallaksh19/relay-v32-e2e-lab`)
- **Negative controls:**
  - Hard stop gate: If HEAD SHA did not match `13989969f6b7e432c4f7c1ddfe975449dba53593`, execution would have terminated immediately with STOP.
- **Blockers and unknowns:**
  - Source availability verified; native live DELP qualification remains to be run.
  - Lab repository `reallaksh19/relay-v32-e2e-lab` not yet created on remote.
- **Next authorized task:** LAB-T02 (Create private dummy GitHub repository `reallaksh19/relay-v32-e2e-lab` via `python scripts/create_private_lab.py --repository reallaksh19/relay-v32-e2e-lab`).
- **Evidence publication URL:** https://github.com/reallaksh19/Common/issues/876#issuecomment-6077592283

**Owner/custody restrictions:** This message is a local agent's test report, **not** independent review, source authenticity proof or a published `CHECKPOINT_FACTS_V1` progress record. Emit the latter only on a real released leaf when source facts, PR head and evidence are proven.
