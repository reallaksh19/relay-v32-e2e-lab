# Agent A: “Prepare for runner” — operating prompt

**Who uses this:** The *current primary Agent A* in the existing engineering conversation. The Owner's message **“Prepare for runner”** asks Agent A to prepare immediately; it does NOT mean 70% context consumption has been measured, a Runner has launched, or execution rights are transferred.

This is a Markdown-only instruction, not another monitor, schema calculator, Python program, or background timer.

## 1. Do this when the Owner says “Prepare for runner”

1. **Identify the existing responsibility.** Read actual Owner requirements, approved parent/leaf, task boundaries and original task-start source SHA. Separate VERIFIED original START, historical research cutoff, and UNKNOWN. Do not invent a START commit retrospectively.
2. **Assess usable agent life.** If the provider actually exposes used/usable context tokens, record the source and calculate consumed percentage. Otherwise use a clearly labeled, qualitative or approximate working-episode assessment; if there is no defensible estimate, say UNKNOWN.
3. **Prepare a Stage 1-only WHAT/WHY packet NOW.** Use only original Owner wording/provenance, immutable original source/consumer allowlist, authentic input fixture identities, accepted original roadmap/claim, WHAT problem, WHY it matters, pending, known and parked. Avoid current Agent A HOW, PR/head/CI statistics, design choices, recent source changes, Stage 2 material and evaluator expected answers.
4. **Review the next work unit and signs of risk.** Can Agent A complete the next bounded unit within a reliable working window? Is there evidence of context compression, loss of source facts, contradictory decisions, repeated research or an interruption risk? State the observation, not a fictional model-health number.
5. **Suggest the proper state.** PREPARE now in response to the Owner even when life-consumed is unknown/low. Recommend **“Time for Runner”** at roughly 70% consumed, or earlier if a credible risk or Owner request to actually launch requires it. Explain why.
6. **Keep engineering continuity intact.** Agent A continues its authorized work. Runner B, once separately launched in a fresh restricted context, prepares an independent plan. Stage 2 and exclusive writer transfer happen only after their separate actual gates.

## 2. How to pick up readiness evidence (without inventing stats)

Review these facts at each real TASK_EVIDENCE checkpoint, significant milestone, before a large next unit, and after a reliability/compaction warning. Do not claim continuous monitoring between messages.

| Evidence type | How to use it |
|---|---|
| Provider-observed context tokens used and usable capacity | PROVIDER_REPORTED; include actual numerator, denominator, source, observation time; compute fraction only from real values |
| Explicit working-episode budget / actual recorded milestones | CALIBRATED_EPISODE; give approximate consumed-life band and calibration, not token telemetry |
| Agent's own cognitive warning, uncertainty or estimated episode consumption | AGENT_SELF_ESTIMATE; label LOW confidence unless well supported |
| No exposed usable context or episode basis | UNAVAILABLE; say consumed life UNKNOWN, never manufacture 70% |
| Remaining reliable runway versus next semantic unit | If unit cannot fit with a safety reserve, recommend early Runner preparation and state the risk |
| Severe coherence warning or imminent interruption | Urgent Runner recommendation even when the percentage is UNKNOWN |

**Never substitute:** engineering progress P/E/D, issue scoreboard, task-completion percentage, a DELP seven-part agent delivery-health score, number of tool calls or elapsed clock time for usable context-life consumed. They can explain *risk* but are not token measurements.

## 3. When Agent A should proactively suggest “Time for Runner”

| Available life-consumed estimate | Advisory / what to do |
|---|---|
| Below ~60% | CONTINUE; record any specific risk |
| ~60–69% | PREPARE; ready the sanitized original-source and WHAT/WHY intake |
| ~70–84% | REQUEST_RUNNER; **propose “Time for Runner” to the Owner and in ordinary TASK_EVIDENCE** |
| ~85%+ | URGENT_RUNNER; request immediate separate Runner preparation and plan for emergency read-only reconciliation |
| UNKNOWN | Do not claim a threshold crossed; propose based on explicit Owner direction, credible cognitive warning, near-term interruption or insufficient next-unit runway |

Overrides: an Owner request to **prepare** acts immediately but is not proof of 70%; an explicit Agent A request, mild warning or runway mismatch may justify REQUEST_RUNNER earlier; severe warning/imminent loss may justify URGENT_RUNNER regardless of percentage. Always label the triggering reason.

**Agent A suggestion is not automatic execution.** REQUEST_RUNNER is not RUNNER_LAUNCHED, not STAGE1_PLAN_FROZEN, not STAGE2_ADMITTED, and not PROMOTED_WRITER. No suggestion can change the existing task's accepted facts, P/E/D or exclusive lease.

## 4. Minimal Markdown checkpoint (not a new machine schema)

Copy into normal TASK_EVIDENCE, using only actually observed details:

> **RUNNER READINESS — Agent A advisory / no authority transfer**
>
> - Governed responsibility and Owner source: [existing leaf + approved scope]
> - Original START: [source SHA + independently observed / historical-only / UNKNOWN]
> - Context observation: [used/usable tokens + source, or episode estimate + method, or UNAVAILABLE]
> - Agent-life consumed: [measured share / approximate band + grade / UNKNOWN]
> - Confidence: [HIGH / MEDIUM / LOW / UNKNOWN and WHY]
> - Reliability and interruption warning: [NONE / MILD / SEVERE, supporting observation]
> - Next bounded semantic unit/runway: [unit, demand, margin or UNKNOWN]
> - Recommendation: [CONTINUE / PREPARE / REQUEST_RUNNER / URGENT_RUNNER]
> - Owner-facing suggestion: [“Prepare for runner” / “Time for Runner” / “Urgent Runner recommended”]
> - Stage 1 original-source/WHAT-WHY package: [prepared / pending / blocked; no HOW]
> - Runner B: [NOT_LAUNCHED unless independently observed]
> - Stage 1 plan: [NOT_FROZEN unless actual committed/readback proof]
> - Authority: [Agent A primary; Runner B read-only; no change to DELP/lease]

If the existing approved repository expects structured TASK_EVIDENCE data, comply with its *already released* protocol. This document does not amend any accepted evidence schema.

## 5. Examples of agent behaviour (fictional, not measured)

**Owner prompt at unknown context usage:**

> “Prepare for runner” received. I am assembling a sanitized original-source and WHAT/WHY intake for the existing responsibility. Context-life consumption is **UNKNOWN**; no provider tokens are exposed. My recommendation is PREPARE at the Owner's request, not a fabricated 70% trigger. Agent A continues engineering.

**Agent proactively proposes at a defensible approximate 70% estimate:**

> **Time for Runner — REQUEST_RUNNER (AGENT_SELF_ESTIMATE, LOW confidence).** Based on [actual estimate method], roughly 70% of this working episode may be consumed. Provider token counts are UNKNOWN. The next semantic unit involves [actual next task and risk]. I recommend a fresh Stage 1 Runner receive only the original source, Owner intent and WHAT/WHY; I remain the authorized primary engineer.

**Early warning despite unknown percent:**

> **Time for Runner — URGENT_RUNNER (severe reliability/interruption warning).** I cannot verify context usage, but [specific observed risk] threatens accurate continuation. Recommend starting an independently restricted Stage 1 preparation now; no Stage 2 disclosure or writer transfer has occurred.

## 6. Relationship to the other Markdown templates

- **This entrypoint** belongs in the active Agent A conversation. It decides when to suggest Runner preparation and prepares *static original inputs*.
- **STAGE1_THINKING_TEMPLATE.md** belongs only to a fresh blind Runner B. It receives coarse trigger reason/source-confidence and sanitized original facts, NEVER Agent A current source/head/CI/solution.
- **STAGE2_RECONCILIATION_TEMPLATE.md** belongs to that same Runner after an externally verified plan freeze and explicit Stage 2 admission; only now may Agent A's actual checkpoint and live source be read.
- **OPERATOR_GUIDE_EXAMPLES.md** remains operator/evaluator-side and is not given to Runner B during Stage 1.

This prompt does not itself inspect private model telemetry, launch a new AI session, prevent unrestricted tools or carry out background checks. It tells Agent A *how to assess and proactively propose* at its actual checkpoints.
