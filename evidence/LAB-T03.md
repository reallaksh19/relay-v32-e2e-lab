# TASK_EVIDENCE — LAB-T03 — Runner credentials and CI source pin PASS

**Experiment:** Common V3.2 CSV Auditor private GitHub lab; governed by `reallaksh19/Common#876`.

- **Task ID:** LAB-T03
- **Status:** PASS
- **Operator/agent identity:** Antigravity local agent (authenticated via `gh` CLI as `reallaksh19`)
- **Repository:** `reallaksh19/relay-v32-e2e-lab`
- **Protocol:** `reallaksh19/Common@13989969f6b7e432c4f7c1ddfe975449dba53593:skills/engineering-pr-delivery-v3.2`
- **Executed material SHA:** `f1a5ed5fea233bc902aa0e1fe678d488c5956b47`
- **Commands executed:**
  1. `gh auth token | gh secret set COMMON_READ_TOKEN --repo reallaksh19/relay-v32-e2e-lab`
  2. `gh secret list --repo reallaksh19/relay-v32-e2e-lab`
  3. `gh workflow run delp-readonly.yml --repo reallaksh19/relay-v32-e2e-lab`
  4. `gh run view 37907447283 --repo reallaksh19/relay-v32-e2e-lab --log`
- **Exit code(s):**
  1. `0` (secret configured)
  2. `0` (`COMMON_READ_TOKEN 2026-10-09T08:49:53Z` confirmed)
  3. `0` (dispatched workflow run `37907447283`)
  4. `0` (log retrieved and verified)
- **Expected independent oracle:**
  - `COMMON_READ_TOKEN` secret provisioned in lab repository.
  - Workflow `.github/workflows/delp-readonly.yml` enforces read-only scopes (`contents: read`, `issues: read`, `pull-requests: read`) and no default writer.
  - Checkout step pins exact Common SHA `13989969f6b7e432c4f7c1ddfe975449dba53593` (not `main`).
  - Runner verification test passes: `test "$(git -C .protocol/common rev-parse HEAD)" = '13989969f6b7e432c4f7c1ddfe975449dba53593'`.
  - Secret content is never emitted in logs or files.
- **Observed actual output:**
  - Secret list readback:
    ```text
    COMMON_READ_TOKEN  2026-10-09T08:49:53Z
    ```
  - Workflow permissions in `.github/workflows/delp-readonly.yml`:
    ```yaml
    permissions:
      contents: read
      issues: read
      pull-requests: read
    ```
  - Runner step execution from run `37907447283`:
    - `Checkout exact Common V3.2 source`: completed successfully using `secrets.COMMON_READ_TOKEN` at ref `13989969f6b7e432c4f7c1ddfe975449dba53593`.
    - `Verify pin and released plan`:
      - `test "$(git -C .protocol/common rev-parse HEAD)" = '13989969f6b7e432c4f7c1ddfe975449dba53593'` succeeded.
      - `python scripts/check_graph.py ...` failed closed with exit code 2: `check_graph.py: error: need actual pinned Common V3.2 engine and bootstrapped released graph` (expected pre-release behavior before T06).
- **Result comparison:** MATCH — Secret provisioned, read-only permissions confirmed, checkout pin verified in live GitHub Actions environment.
- **Durable source refs:**
  - Governing issue: https://github.com/reallaksh19/Common/issues/876
  - Workflow specification: https://github.com/reallaksh19/relay-v32-e2e-lab/blob/main/.github/workflows/delp-readonly.yml
  - Verification Actions run: https://github.com/reallaksh19/relay-v32-e2e-lab/actions/runs/37907447283
- **Negative controls:**
  - Exact pin verification: fails closed if checked-out Common SHA deviates from `13989969f6b7e432c4f7c1ddfe975449dba53593`.
  - Graph verification: fails closed (exit code 2) while pre-release graph is unreleased.
- **Blockers and unknowns:**
  - Proposal V2 not yet generated (scheduled for LAB-T04).
  - Human Owner approval gate pending after proposal generation (scheduled for LAB-T05).
- **Next authorized task:** LAB-T04 (Pre-materialization Proposal-V2 / ROOT ONLY).
- **Evidence publication URL:** https://github.com/reallaksh19/Common/issues/876#issuecomment-6077656718

**Owner/custody restrictions:** This message is a local agent's test report, **not** independent review, source authenticity proof or a published `CHECKPOINT_FACTS_V1` progress record. Emit the latter only on a real released leaf when source facts, PR head and evidence are proven.
