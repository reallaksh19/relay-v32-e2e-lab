# TASK_EVIDENCE — LAB-T02 — Private lab repository creation and verification PASS

**Experiment:** Common V3.2 CSV Auditor private GitHub lab; governed by `reallaksh19/Common#876`.

- **Task ID:** LAB-T02
- **Status:** PASS
- **Operator/agent identity:** Antigravity local agent (authenticated via `gh` CLI as `reallaksh19`)
- **Repository:** `reallaksh19/relay-v32-e2e-lab` (private: `true`, html_url: `https://github.com/reallaksh19/relay-v32-e2e-lab`)
- **Protocol:** `reallaksh19/Common@13989969f6b7e432c4f7c1ddfe975449dba53593:skills/engineering-pr-delivery-v3.2`
- **Executed material SHA:** `f1a5ed5fea233bc902aa0e1fe678d488c5956b47`
- **Commands executed:**
  1. `gh api repos/reallaksh19/relay-v32-e2e-lab` (pre-creation check)
  2. `python scripts/create_private_lab.py --repository reallaksh19/relay-v32-e2e-lab`
  3. `gh api repos/reallaksh19/relay-v32-e2e-lab --jq '{name: .name, full_name: .full_name, private: .private, html_url: .html_url, default_branch: .default_branch}'`
  4. `gh api repos/reallaksh19/relay-v32-e2e-lab/commits/main --jq '{sha: .sha, commit_message: .commit.message}'`
  5. `gh run list --repo reallaksh19/relay-v32-e2e-lab`
- **Exit code(s):**
  1. `1` (HTTP 404 Not Found before creation; confirms no collision or accidental overwrite)
  2. `0` (`CREATED_PRIVATE_LAB reallaksh19/relay-v32-e2e-lab`, `INITIAL_HEAD f1a5ed5fea233bc902aa0e1fe678d488c5956b47`)
  3. `0` (`{"default_branch":"main","full_name":"reallaksh19/relay-v32-e2e-lab","html_url":"https://github.com/reallaksh19/relay-v32-e2e-lab","name":"relay-v32-e2e-lab","private":true}`)
  4. `0` (`{"commit_message":"lab: preserve Owner request and precommitted RED feature oracles","sha":"f1a5ed5fea233bc902aa0e1fe678d488c5956b47"}`)
  5. `0` (Initial baseline run `37907254178` completed failure on push to main)
- **Expected independent oracle:**
  - Remote repository `reallaksh19/relay-v32-e2e-lab` is created as private (`private: true`).
  - Source committed and pushed cleanly to remote `main`.
  - Independent GitHub API readback confirms private repository status and matching HEAD SHA.
  - Baseline all-product workflow on `main` executes and is intentionally RED until R03.
- **Observed actual output:**
  - Repo creation stdout:
    ```text
    CREATED_PRIVATE_LAB reallaksh19/relay-v32-e2e-lab
    INITIAL_HEAD f1a5ed5fea233bc902aa0e1fe678d488c5956b47
    ```
  - Independent API readback:
    ```json
    {"default_branch":"main","full_name":"reallaksh19/relay-v32-e2e-lab","html_url":"https://github.com/reallaksh19/relay-v32-e2e-lab","name":"relay-v32-e2e-lab","private":true}
    ```
  - Remote commit verification:
    ```json
    {"commit_message":"lab: preserve Owner request and precommitted RED feature oracles","sha":"f1a5ed5fea233bc902aa0e1fe678d488c5956b47"}
    ```
  - Workflow run observation:
    ```text
    completed failure lab: preserve Owner request and precommitted RED feature oracles CSV auditor staged acceptance (RED until implemented) main push 37907254178
    ```
- **Result comparison:** MATCH — Private repository created, pushed, and independently verified via GitHub API readback.
- **Durable source refs:**
  - Governing issue: https://github.com/reallaksh19/Common/issues/876
  - Created private lab repo: https://github.com/reallaksh19/relay-v32-e2e-lab
  - Remote initial commit: https://github.com/reallaksh19/relay-v32-e2e-lab/commit/f1a5ed5fea233bc902aa0e1fe678d488c5956b47
  - Initial baseline CI run: https://github.com/reallaksh19/relay-v32-e2e-lab/actions/runs/37907254178
- **Negative controls:**
  - 404 readback confirmed absent before repo creation (pre-check prevented accidental overwrite).
  - Baseline all-product acceptance workflow `37907254178` on `main` failed as expected (precommitted RED).
- **Blockers and unknowns:**
  - Actions secret `COMMON_READ_TOKEN` for reading private Common not yet configured in new repo (scheduled for LAB-T03).
  - ROOT issue and Proposal V2 not yet created (scheduled for LAB-T04).
- **Next authorized task:** LAB-T03 (Configure read-only Common access secret `COMMON_READ_TOKEN` for GitHub Actions on `reallaksh19/relay-v32-e2e-lab`).
- **Evidence publication URL:** https://github.com/reallaksh19/Common/issues/876#issuecomment-6077627441

**Owner/custody restrictions:** This message is a local agent's test report, **not** independent review, source authenticity proof or a published `CHECKPOINT_FACTS_V1` progress record. Emit the latter only on a real released leaf when source facts, PR head and evidence are proven.
