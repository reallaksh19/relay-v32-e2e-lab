# V3.2 real-GitHub end-to-end laboratory — STARTER, not a PASS

This is a **disposable private-repository experiment** for `reallaksh19/Common` V3.2. It is not V3.5. The actual Owner asked whether the protocol can be stress-tested in a small dummy GitHub repository and authorized proceeding. The CSV requirements are an **assistant-designed test fixture**, not a fabricated verbatim Owner product instruction. Original chat permalink is UNKNOWN.

## Status at package generation

- Starter files generated and local bootstrap/smoke checks can pass; acceptance tests for R01/R02/R03 are deliberately **RED** until agents implement the feature.
- The new private repository, issues, PRs, GitHub Actions, native handover and live scoreboard **are NOT created by generating this ZIP**.
- The V3.2 engine comes from a pinned `Common` checkout; scripts do not provide a fake engine or silently fall back to V3.5.
- **All live publishing is OFF by default**. The `delp-readonly.yml` workflow uses `contents:read`; the live publisher must be added/reviewed and intentionally enabled later.

## Setup (authenticated GitHub CLI on your machine)

1. Install `git`, `gh`, and Python 3.11+; run `gh auth login`.
2. Unzip and `cd relay-v32-e2e-lab-starter`. Because **Common is a private repository**, grant the lab a narrowly scoped **read-only** fine-grained GitHub token for Common contents, saved as the lab secret `COMMON_READ_TOKEN` before dispatching `delp-readonly.yml`. Never put this token in source or logs. Local commands can use your existing `gh` authorization.
3. Execute `python scripts/create_private_lab.py --repository reallaksh19/relay-v32-e2e-lab` to initialize a git repository, create a **private** GitHub repository and push the untouched seed. The script refuses to proceed if `origin` exists or the repo already exists.
4. Clone `reallaksh19/Common` to a separate directory and check out the immutable SHA in `governance/engine-lock.json`. Then execute `python scripts/bootstrap_issues.py --prepare --repository reallaksh19/relay-v32-e2e-lab --engine ../Common/skills/engineering-pr-delivery-v3.2/scripts/delp_projection_v32.py`. This creates only the **root issue** and pre-materialization Proposal-V2, computes the canonical digest and commits the exact proposed basis. **Do not create child issues yet.**
5. **Human approval gate:** Post the exact `APPROVE_LAB_PROPOSAL_V2 digest=... source_sha=...` comment printed by the prepare step **on the new GitHub parent issue**, from the repository Owner account. The script checks its provider author and content; it never posts an approval for you. Then run the same command with `--release` instead of `--prepare`. Only now does it materialize genuine phase/leaf issues, bind returned provider IDs into the released graph and push `main`. This is a deliberate two-step Owner-controlled bootstrap, not one self-authorized transaction.
6. Confirm Common is at the pinned SHA in `governance/engine-lock.json`, and run:

```bash
python scripts/check_graph.py --engine ../Common/skills/engineering-pr-delivery-v3.2/scripts/delp_projection_v32.py
python scripts/check_graph.py --engine ../Common/skills/engineering-pr-delivery-v3.2/scripts/delp_projection_v32.py --live-readonly
```

7. Assign an implementation agent to R01 only. Let it open a real PR, and after independent agreement replace the branch `candidate_ref` with `primary_pr` through a **new graph revision**. Do not update the graph as if it were a task checkpoint; changes to released scope require a recorded plan update. Repeat for R02 and R03 respecting dependencies.
8. Use `python -m unittest discover -s acceptance -p 'test_r*.py' -v` for actual functional acceptance (deliberately RED on the starter). The smoke suite `python -m unittest discover -s tests -v` must always pass.
9. Run `python stress/run_v32.py --engine ...` only on the released graph. For adversarial P/E/D tests it uses real V3.2 `delp_projection_v32.py` as a library and rejects authored P values, evidence gaps and candidate moves. It does **not** claim authenticated provider currentness.

## Contract

- One real programme parent, two real phase issues, three real leaf issues, separate real PRs, V3.2 graph with explicit claims and dependencies.
- Accepted facts must originate in `TASK_EVIDENCE` with `CHECKPOINT_FACTS_V1`; PR head and CI must be observed live, not copied from an issue title.
- One releasable unit must have positive functional tests and negative controls. Three leaf PRs must deliver the user-visible example.
- Every transition must include source SHA, GitHub issue/PR IDs, actual Actions run ID, and **an independent expected/actual assertion**.
- Cold successor starts without predecessor chat history and answers the six questions in `stress/cold_successor_challenge.md` using GitHub evidence only.
- No source provenance, independent review, owner permission, issue-title writer, or cold custody is self-proved by a generated SHA or a passing test.

## Guardrails

- Never use `Common` repository production issue writers for the lab.
- Never run an auto publisher with write permissions or a `pull_request_target` workflow unless it has been independently reviewed and Owner has approved it in this **private lab**.
- Never treat completed unit tests as passing the 15 live GitHub attack scenarios.
- Use `main` graph as observed released source for native handover. Agent-selected commit SHA alone is insufficient release proof.

## Tracked known gaps

1. V3.2 WP1 SourceReceiptV2 PR #874 is not an authenticated source-to-DELP integration; it is currently stacked on governance PR #873.
2. Existing D01/D03/D06 RED failures require versioned V2 repair; do not make the legacy V1 digest change just to green those tests.
3. V3.2 PR title/description read view is not proof that a live PR writer is installed.
4. The native C6 handover requires an actual released JSON graph and real provider reads. Offline JSON imitation does not qualify.

See `stress/scenarios.json` and `governance/acceptance-claims.json`.

## Private Common checkout for local graph release

```bash
gh repo clone reallaksh19/Common ../Common
git -C ../Common checkout 13989969f6b7e432c4f7c1ddfe975449dba53593
python scripts/bootstrap_issues.py --prepare --repository reallaksh19/relay-v32-e2e-lab --engine ../Common/skills/engineering-pr-delivery-v3.2/scripts/delp_projection_v32.py
```

At this stage the script prints a full, exact `APPROVE_LAB_PROPOSAL_V2` comment. Post that comment **yourself** in the newly created parent GitHub issue; then run the identical command with `--release`. It refuses to create children without matching GitHub Owner comment readback. This verifies provider account association but cannot prove who controlled a bearer token; independent original-message custody remains UNKNOWN until separately established.

The lab's `COMMON_READ_TOKEN` is required for GitHub Actions because `reallaksh19/Common` is private: the lab's default `GITHUB_TOKEN` does not automatically have access to it. The workflow contains no fallback to a moving public branch or fake engine.

## Final release verifier (fails closed)

The 15 scenarios start at `NOT_EXECUTED` in `stress/scenario-results.template.json`. Record actual scenario executions into a new results file with exact completed GitHub Actions URLs, their `source_sha`, independent expected/observed result strings and a separate evaluator's provider issue-comment URL containing `LAB_VERDICT Sxx PASS result_digest=<canonical SHA256 of the scenario record>`. Then call:

```bash
python stress/verdict.py --repository reallaksh19/relay-v32-e2e-lab \
  --results evidence/scenario-results.json --readback
```

Unlike a self-graded JSON fixture, the verdict script reads each workflow run's SHA/status and the independent evaluator's GitHub comment. It will not issue an E2E pass when the provider is unavailable or any of 15 cases lacks matching evidence. Bearer-token account identity is still not proof of physical human authorship; stronger independent custody would require an external anchor.

## Local agent test execution — evidence after every task

See **[`LOCAL_AGENT_TASKS.md`](LOCAL_AGENT_TASKS.md)** for the mandatory sequential LAB-T00…T12 checklist, commands, Owner STOP gate, per-task GitHub issue #876 evidence publication and separate app acceptance by responsibility. Use **[`evidence/TASK_EVIDENCE_TEMPLATE.md`](evidence/TASK_EVIDENCE_TEMPLATE.md)** after **each** task, including a blocked task. The agent may begin T00 offline now; private Common access enables T01, and authenticated repo creation enables T02–T04. The human Owner must separately approve the exact proposal digest+source SHA at T05. No implementation/issue-scoreboard/cold successor success may be preclaimed.

App CI selection is intentionally stage-aware: `lab/r01` requires R01; `lab/r02` requires R01+R02; `lab/r03` and `main` require all three. An unknown branch fails closed. Thus precommitted unfinished feature cases cannot falsely block the earlier PR's *own* acceptance while remaining visible as unfinished programme work.

The release verdict verifier now checks that every referenced GitHub Actions run ended **with `conclusion: success`**, not merely `status: completed`, and that each independent evaluator comment belongs to the referenced issue. Verified failures/cancellations or foreign repository runs cannot qualify an E2E PASS.
