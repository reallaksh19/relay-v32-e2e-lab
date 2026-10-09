# TASK_EVIDENCE — LAB-T04 — Pre-materialization Proposal-V2 / ROOT ONLY PASS

**Experiment:** Common V3.2 CSV Auditor private GitHub lab; governed by `reallaksh19/Common#876`.

- **Task ID:** LAB-T04
- **Status:** PASS
- **Operator/agent identity:** Antigravity local agent (authenticated via `gh` CLI as `reallaksh19`)
- **Repository:** `reallaksh19/relay-v32-e2e-lab`
- **Protocol:** `reallaksh19/Common@13989969f6b7e432c4f7c1ddfe975449dba53593:skills/engineering-pr-delivery-v3.2`
- **Executed material SHA:** `975433cf557f7f6de0f015c83f5e92cd119a0e51`
- **Commands executed:**
  1. `python scripts/bootstrap_issues.py --prepare --repository reallaksh19/relay-v32-e2e-lab --engine ..\Common\skills\engineering-pr-delivery-v3.2\scripts\delp_projection_v32.py`
  2. `python ..\Common\skills\engineering-pr-delivery-v3.2\scripts\delp_projection_v32.py decompose-check --graph governance/pre-materialization-graph.json --json`
  3. `gh api repos/reallaksh19/relay-v32-e2e-lab/contents/governance/pre-materialization-graph.json?ref=975433cf557f7f6de0f015c83f5e92cd119a0e51`
  4. `gh issue list --repo reallaksh19/relay-v32-e2e-lab --state all`
  5. `gh issue view 1 --repo reallaksh19/relay-v32-e2e-lab`
  6. `python scripts/bootstrap_issues.py --release --repository reallaksh19/relay-v32-e2e-lab --engine ..\Common\skills\engineering-pr-delivery-v3.2\scripts\delp_projection_v32.py` (negative test)
- **Exit code(s):**
  1. `0` (`PREPARED_NOT_OWNER_APPROVED`, pinned SHA `975433cf557f7f6de0f015c83f5e92cd119a0e51`)
  2. `0` (`RELEASEABLE`, 3 product leaves)
  3. `0` (remote file blob read back successfully)
  4. `0` (exactly 1 issue found: #1 ROOT)
  5. `0` (0 comments, root description verified)
  6. `1` (`RuntimeError: OWNER_APPROVAL_REQUIRED` negative gate confirmed)
- **Expected independent oracle:**
  - Exactly one ROOT issue (#1) created on GitHub.
  - Zero child (PHASE or LEAF) issues created before Owner approval.
  - Native engine `decompose-check --json` yields `RELEASEABLE`, 3 semantic responsibilities (R01, R02, R03), and stable digest `sha256:b153846fbb2f189ac255e3677072d35a3f591e8402199bb14eddf8b653c58ad8`.
  - Committed proposal pushed to `main` at exact 40-hex SHA `975433cf557f7f6de0f015c83f5e92cd119a0e51`.
  - Required comment text displayed for separate human Owner action (never posted by agent).
- **Observed actual output:**
  - Bootstrap prepare output:
    ```json
    {
      "status": "PREPARED_NOT_OWNER_APPROVED",
      "root_issue": "https://github.com/reallaksh19/relay-v32-e2e-lab/issues/1",
      "proposal_digest": "sha256:b153846fbb2f189ac255e3677072d35a3f591e8402199bb14eddf8b653c58ad8",
      "pinned_sha": "975433cf557f7f6de0f015c83f5e92cd119a0e51",
      "required_comment": "APPROVE_LAB_PROPOSAL_V2 digest=sha256:b153846fbb2f189ac255e3677072d35a3f591e8402199bb14eddf8b653c58ad8 source_sha=975433cf557f7f6de0f015c83f5e92cd119a0e51",
      "children_created": false
    }
    ```
  - Native `decompose-check` summary:
    ```json
    {
      "release_state": "RELEASEABLE",
      "proposal_digest": "sha256:b153846fbb2f189ac255e3677072d35a3f591e8402199bb14eddf8b653c58ad8",
      "summary": { "evaluated": 3, "releasable": 3, "not_releasable": 0, "by_class": { "PRODUCT": 3 } }
    }
    ```
  - Independent issue query on `reallaksh19/relay-v32-e2e-lab`:
    ```text
    1  OPEN  [LAB-V32-CSV] ROOT — Owner intent and semantic acceptance
    ```
- **Result comparison:** MATCH — Pre-materialization Proposal-V2 validated native `RELEASEABLE`, exactly one ROOT issue exists, zero child issues created.
- **Durable source refs:**
  - Governing issue: https://github.com/reallaksh19/Common/issues/876
  - Lab ROOT issue: https://github.com/reallaksh19/relay-v32-e2e-lab/issues/1
  - Pinned proposal commit: https://github.com/reallaksh19/relay-v32-e2e-lab/commit/975433cf557f7f6de0f015c83f5e92cd119a0e51
  - Pre-materialization proposal file: https://github.com/reallaksh19/relay-v32-e2e-lab/blob/975433cf557f7f6de0f015c83f5e92cd119a0e51/governance/pre-materialization-graph.json
- **Negative controls:**
  - Zero child issues: `gh issue list` verified exactly 1 ROOT issue and 0 PHASE/LEAF issues.
  - Release rejection: `bootstrap_issues.py --release` failed closed with exit code 1 (`OWNER_APPROVAL_REQUIRED`), refusing to create child issues without genuine Owner comment.
- **Blockers and unknowns:**
  - Owner approval comment is required on ROOT issue #1 before LAB-T06 release.
  - Agent must not self-approve or post the required comment.
- **Printed required comment (awaiting human Owner posting on ROOT #1):**
  `APPROVE_LAB_PROPOSAL_V2 digest=sha256:b153846fbb2f189ac255e3677072d35a3f591e8402199bb14eddf8b653c58ad8 source_sha=975433cf557f7f6de0f015c83f5e92cd119a0e51`
- **Next authorized task:** LAB-T05 (Owner approval STOP gate).
- **Evidence publication URL:** https://github.com/reallaksh19/Common/issues/876#issuecomment-6077692483

**Owner/custody restrictions:** This message is a local agent's test report, **not** independent review, source authenticity proof or a published `CHECKPOINT_FACTS_V1` progress record. Emit the latter only on a real released leaf when source facts, PR head and evidence are proven.
