# BR-09 — Buddy Runner controlled-trial qualification schema

Status: experimental lab code. Governing Common issue #879 and reference
Common #718. This does not amend or release the production V3.2 protocol.

## Why this exists

Stage 1 → Stage 2 source and event mechanics cannot establish actual
continuity quality, lower total cost, or independent witness custody.
Tests that run a deterministic fixture are not evidence that an AI Runner
reconstructed HOW. A complete-looking TASK_EVIDENCE body is not proof of
provider-authenticated publication. BR-09 prevents those substitutions.

## Matched conditions and frozen case basis

Each case holds exactly four ordered treatments:

- CONTROL: no Runner and no interrupted original agent.
- EARLY_50: Runner called at roughly 50% of useful context.
- TARGET_70: Runner called at roughly 70%.
- LATE_85: Runner called at roughly 85%.

Keep the exact original source start commit, frozen Owner-intent digest,
golden-fixture digest and case-parameters digest identical across trials.
Distinct trial/run IDs avoid duplicate and replayed records.

These labels are experimental treatments, not proof of genuine model
context occupancy. Capture the real provider observation or mark the
runway percentage as an agent self-estimate in underlying TASK_EVIDENCE.
A simulated interruption must be marked SIMULATED. A fixed script/fixture
must be marked DETERMINISTIC_FIXTURE, never REAL_AGENT.

## Evidence and measurement discipline

Each treatment must contain exactly these phase slots, in order:

ORIGINAL_START, RUNNER_BLIND_READ, RUNNER_PLAN_SEALED,
WITNESS_PROVIDER_READBACK, AGENT1_INTERRUPTED,
STAGE2_SOURCE_RECONCILED, GOLDEN_ORACLE, COST_CAPTURE.

Each phase holds an artifact SHA-256, provider reference, observer
principal and result PASS / FAIL / UNKNOWN. These values are caller
claims until independently checked by the relevant trusted provider;
ordinary text references do not authenticate them.

Measure and record actual agent-1, Runner and reviewer token usage,
their three respective costs in integer micro-USD, and recovery duration
in seconds. If not obtainable, the field is null and costs must remain
UNKNOWN, never coerced to zero or guessed. Comparisons use total combined
cost, not Runner-only cost; never claim productivity gain just because
the original agent stopped consuming tokens.

The experimental CLI:

    python experiments/buddy_runner_v1/trial_evaluator.py \
      --input experiments/buddy_runner_v1/fixtures/br09_four_conditions_unqualified.json \
      --output /recorder-only/br09-report.json

The output is exclusively written to a NEW path; it does not mutate the
trial source and cannot replace an older report. The fixture is
SYNTHETIC/UNQUALIFIED, its zero-filled digests are placeholders, and
all measured metrics are explicitly null.

## Qualification and custody boundary

Even if a trial record reports REAL_AGENT, OBSERVED interruption,
INDEPENDENTLY_ATTESTED readback and all PASS phases, the evaluator
returns qualification EXTERNAL_VERIFIER_REQUIRED and
production_write_authority NOT_GRANTED.

This is deliberate. It has no trusted connection to the signature key
custodian, model provider, source Git server, or Owner authorization
service. Future admission needs an independently pinned witness key,
provider-authenticated timestamp/immutable record, actual blind model
run and exact-head golden tests reviewed outside both coding agents.

The evaluator never changes CHECKPOINT_FACTS_V1, progress weights,
issue live scoreboards, lease state or production source.

## Acceptance cases

test_trial_evaluator.py proves strict four-condition ordering, no
duplicate run IDs, fixed original source and golden oracle digests,
matched scenario inputs, no fabricated cost, failure for invalid or
unsequenced proof slots, and no promotion from even self-claimed complete
real-agent evidence.

Local verification: 14/14 focused and 96/96 combined Buddy v1 tests
passed on the available development harness. This does NOT establish
hosted exact-head CI, independent signed facts or model continuity.
