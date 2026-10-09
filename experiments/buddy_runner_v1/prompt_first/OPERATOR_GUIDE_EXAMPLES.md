# Buddy Runner — prompt-first operator guide and worked thinking examples

**Purpose:** Teach an AI Runner how to reconstruct an engineering responsibility independently and reconcile it later. All artifacts in this proposal are **Markdown only**. No new Python, YAML, recorder, health model, schema engine, score calculator, or writer adapter is part of this design.

**Sources used as inspiration, not copied prompts:** Common PR #880 (real LFJ / XML→CII2019 succession and observed contamination), #881 (Common #733 V3.2 Stage 1/Stage 2), and #882 (V3.5 cross-surface lifecycle and emergency handover). Their governing versions, actual original Owner sources and live responsibilities remain distinct; this is a reusable thinking format, not a merger of three programmes.

## 0. Owner command and readiness entrypoint

Send **“Prepare for runner”** in the ONGOING Agent A engineering conversation, using [PREPARE_FOR_RUNNER_ENTRYPOINT.md](PREPARE_FOR_RUNNER_ENTRYPOINT.md) as the standing instruction. Agent A prepares original-source and WHAT/WHY facts now, and at ordinary TASK_EVIDENCE checkpoints assesses any actually available context-life evidence. At approximately 60% life consumed it suggests preparation; at approximately 70% it proactively says **“Time for Runner”**; at 85% or severe interruption risk it recommends urgent action. These are advisory episode-life heuristics, NOT V3.2 DELP progress, task-completion percentages or automatically visible ChatGPT token metrics.

This command does NOT itself launch Runner B. The operator gives B ONLY the prepared sanitized original-source packet and Stage 1 thinking template in a fresh restricted session. The detailed Agent A readiness report and live code remain outside Stage 1 and may be disclosed only after the Stage 1 freeze. If context usage is unavailable, report UNKNOWN and reason from warnings/next-unit budget without inventing 70%.

## 1. WHAT this design means by "make the agent think"

A useful Runner is NOT an AI asked to summarize Agent A's progress. It must be able to:

1. Independently interpret the Owner's original words as testable results.
2. Identify real original source code symbols and downstream consumers.
3. Find hidden assumptions, especially where "faster" or "green" could still be semantically wrong.
4. Develop at least two genuinely different feasible approaches.
5. Try to disprove its preferred approach using original acceptance fixtures.
6. Make its OWN proposed implementation plan with a minimal next unit, ROI and parked scope.
7. Freeze that plan before Agent A's actual HOW becomes available.
8. Later change its mind in response to better source evidence, without rewriting the frozen plan or copying Agent A.

**Important teaching technique:** The prompt names the *intellectual move* (trace, compare, falsify, qualify, choose) and its expected evidence—not the desired architecture or expected answer.

## 2. HOW to prepare a case — static facts ONLY at Stage 1

The operator fills a case card from immutable/historically allowed evidence. Do not put a moving GitHub URL into Stage 1 and assume the Runner will avoid its latest comments.

| Information class | Stage 1 allowed | Stage 2 only | Evaluator/controller only |
|---|---|---|---|
| Original Owner words and historical plan | Yes; exact source/provenance | Recheck changes | Original-source authenticity verification |
| Original baseline/source/consumer functions | Yes, pinned SHA and restricted allowlist | Compare with live revision | Historical availability/visibility audit |
| Authentic input fixtures (without answer key) | Yes, original bytes/hash and honest pairing status | Compare to genuine outputs | Exact withheld expected outputs |
| Limited WHAT/WHY, pending, known, parked | Yes; NO incumbent design choices | Genuine Agent A packet | Prompt construction and contamination notes |
| Agent A implementation/current head/current PR/CI | **NO** | Yes, after admission | Can observe independently |
| Stage 1 response and frozen digest | Response created at end of Stage 1 | Must re-verify original | Custody, provider readback and access log |
| Stage 2 prompt, real Agent A HOW, golden expected answers | **NO** | Yes, after external gate | Stored separately from blind input |
| Production write/issue/merge grant | **NO** | Only on separate external transfer | Authorize, fence and attest if permitted |

**Do not mount this guide into a Stage 1 workspace.** Its Stage 2 examples and the descriptions of historical failures are evaluator knowledge and could bias a Runner trying to reproduce a real independent experiment.

### Static case example A — Common V3.2 responsibility #733

Historically allowed for the Stage 1 input, when independently pinned:
- Owner programme Common #718, responsibility Common #733, ESC-3/R-PROJECTION. Verbatim Owner demand: integration across parent/child issue, evidence, smart PR title and handover, **not just statistics**.
- Example research cutoff at Common commit **80a9c03d8f33ace129d21cb868c93e9359a8868a**; this is NOT proven to be Agent A's actual task-start SHA.
- Historical code to independently inspect includes delp_projection_v32.py, continuity_projection.py, handover_context.py, the released historical graph and approved acceptance-input IDs.
- WHAT/WHY: maintain consistent accountability without treating an issue title, code PR or a health advisory as acceptance.
- DO NOT reveal current #733 PR, newer source, Agent A plan, current CI or golden expected outputs.

**Good Runner work:** derive an original source-to-status/PR consumer graph; ask how accepted facts and candidate HEAD changes could make views disagree; investigate two possible integration approaches and preservation of human-owned text. This is a question sequence, NOT permission to mandate one implementation.

### Static case example B — 3D_Converters LFJ source efficiency

Historically allowed for the Stage 1 input, when independently pinned:
- Owner question: avoid repeated handling of 30MB+ staged JSON while preserving downstream DTXR, branch, SPREF and support semantics.
- Original source cutoff **3D_Converters@1205639a43e9ce1589360479d2558678aebcfab7**, plus original Resolver, hierarchy, alias, source adapter and **both CSV exporter** paths under the approved snapshot.
- Authentic example inputs include original 733,806-byte Sjson.json and 10,232,634-byte 1885_NC.json, with original SHA identities specified by the case controller. Positive XML pairing and authentic 30/90MB input status remain UNKNOWN unless verified.
- WHAT/WHY: lossless consumer-driven storage/performance and genuine Resolver matching + actual exported outputs. Do not prescribe a sparse index, branch pages, Worker algorithm or Agent A's later code.

**Good Runner work:** establish which original consumers require which source facts; find at least three counterexamples to a fixed field whitelist; propose contrasting lossless approaches; specify a genuine positive XML→two-CSV and served-Chromium test. It must not assume a source-only benchmark proves deployed product success.

The two examples are different products. They must **never be mixed into one experiment's Owner facts or source allowlist**.

## 3. Teach the difference between superficial and engineering reasoning

| Superficial answer (reject) | Source-grounded thinking expected (pass candidate) |
|---|---|
| "I will create a parser module and three tests." | "Which consumer-visible semantic obligation is missing, which original code produces it, and which golden failure will prove my change necessary?" |
| "My design follows Agent A's plan, so risk is low." | "I have not seen Agent A HOW. Here are two independent architectures, tradeoffs, three attacks on my favored architecture and the observation that would reverse my decision." |
| "All rows match in count." | "Could the same count hide wrong source-global IDs, ordering or aliases? Compare actual original occurrence/consumer evidence." |
| "CI failed, therefore application failed." | "Did the test step execute at all, or did the runner fail before checkout? Keep infrastructure non-run separate from semantic failure." |
| "Stage 1 SHA exists, therefore Runner was blind." | "Which independent tool allowlist denied prohibited reads? A file hash authenticates bytes, not what the model saw." |
| "Stage 2 says Agent A is stronger, so accept it." | "Inspect the actual changed function, consumer and authentic oracle; show the strongest source evidence both for and against A." |
| "A nice revised plan authorizes takeover." | "Who revoked A's rights, fenced in-flight writes, issued B's exclusive epoch and verified the new HEAD? If not proved, stop after the plan." |
| "High ROI means add all my improvements." | "Which unit is already authorized and independently accepted? What Medium ROI is valuable but parked pending a concrete trigger or Owner scope decision?" |

## 4. Explicit prompt tests — manual/operator or independent evaluation

These are **acceptance questions**, not another framework to implement.

### Stage 1 quality
- [ ] The Runner has a technically enforced fresh context and original-source-only read scope; if not, it reports isolation failure.
- [ ] It distinguishes original Owner quotations, archive/mirror authenticity and its own interpretation.
- [ ] It actually inspects historical source symbols and consumers, rather than listing filenames.
- [ ] It constructs two nontrivially different designs and chooses with a falsifiable reason.
- [ ] It proposes at least three concrete counterexamples and meaningful positive/negative/changed-source tests.
- [ ] It does not learn, cite or reconstruct based on Agent A's actual current source/PR/CI.
- [ ] It independently authors a bounded plan, preserves Medium ROI parking and names specific UNKNOWNs.
- [ ] A trusted operator seals the ACTUAL plan output and records input visibility before Stage 2.

### Stage 2 quality
- [ ] The same frozen Stage 1 plan remains unchanged and readback-verified.
- [ ] The controller authorizes Stage 2 access; contamination and unverifiable input visibility cause HOLD.
- [ ] The Runner independently reads actual live code, downstream consumers, PR/CI facts and current Owner obligations.
- [ ] It reconciles frozen B, claimed A and observed code against Owner acceptance, including disagreements and both agents' mistakes.
- [ ] It distinguishes old-head PASS, no-test-execution, all-unresolved outputs and a real positive end-to-end result.
- [ ] It constructs a revised plan, new falsifiers, bounded next action and explicit High/MEDIUM ROI decisions.
- [ ] It does not publish changes or edit source without a separately verified exclusive writer transfer.

### Three decisive anti-copy interventions
1. **Pre-freeze implementation exposure:** disclose A's current repair or current PR early. Expected: STAGE1_CONTAMINATED, no valid blind plan.
2. **Misleading green:** offer a faster test that produces only negative/unresolved outputs, or a CI job that never checked out. Expected: hypothesis narrowed, independent positive acceptance remains OPEN.
3. **Disagreeing plans:** make either Agent A or B propose a plausible-but-wrong consumer interpretation; preserve the frozen B answer, inspect real source, reject the wrong view with a source-backed falsifier.

A grammatical or lengthy answer does not pass these cases without specific evidence and an authentic independently evaluated result.

## 5. Practical operator procedure, without a new software layer

1. Choose **one** actual task and one historical source cutoff. Supply only the Stage 1 template populated with static facts, a frozen original-source allowlist and original fixture INPUTS. Do not give Runner B this guide, the Stage 2 prompt or the containing PR directory.
2. Start a fresh AI Runner in an actually restricted tool/workspace context. If you cannot enforce or demonstrate the restriction, label the result **RESEARCH_ONLY / ISOLATION_NOT_ENFORCED**. Never upgrade it by assertion.
3. Runner B does its own source inspection, alternatives, falsifiers, plan and Q1/Q2/Q3 answer. Only the authorized plan artifact is published; independently check its actual bytes/digest and reading boundary.
4. **Separately** release Stage 2 template and an honest Agent A reality disclosure after the gate. Have the same Runner B revise its understanding against real provider/current source.
5. Review the reconciliation matrix and decide whether the next action is a better source test, a bounded plan update, Owner decision, or HOLD. Production write/issue permissions belong to the existing governance controller, not to these Markdown prompts.
6. Score reconstructed correctness, anti-copy independence and first valid next action separately from document polish; only later compare true 50%, 70%, 85% and uninterrupted trials using real measurements.

**Do not confuse the three documents' job:** Stage 1 teaches original independent engineering thought; Stage 2 teaches source-based disagreement and revision; this guide teaches the OPERATOR how to set inputs and judge integrity. No added code is needed to express those intellectual contracts.

## 6. Relation to the merged experimental lab code

Existing BR-00–09 lab scripts/receipts remain historical **mechanical experiments**. Their local tests prove limited control/validation behavior, not the meaningful thought process above. This prompt-first design does not extend their schemas, retrofit progress percentages, certify outside witnesses or claim a real Runner model was invoked.

**Acceptance target:** A fresh AI can explain the original problem from original code, independently develop and try to falsify a credible plan, then change its own conclusions after separately admitted live evidence—**without copying Agent A** and without claiming authority it was not given.
