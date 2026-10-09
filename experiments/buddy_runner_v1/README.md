# Engineering Relay V3.2 — Buddy Runner blind Stage 1 (experimental)

**Status:** isolated research/code experiment, not a production V3.2 feature.
Governing qualification: Common #879; existing lab R01 responsibility: lab #4.
The lab synthetic CSV programme does not become a new Owner requirement.

## Two event architecture

**Event 0 — observed Agent 1 START:** a trusted harness records actual clean
HEAD (not a retrospectively chosen commit) and copies a release-specific
allowlist of four files *from that commit's Git tree*. At START only the
original parent/claim WHAT/WHY is known and supplied as initial-packet.

**Event 1 — TIME_FOR_RUNNER at approximately 70% useful life:** Agent 1
publishes WHAT/WHY of what it addressed, pending problems, known issues and
parked decisions. The harness adds those words to the earlier source-only
snapshot WITHOUT re-reading the current repository. Both initial and late
packets must pass exact-key validation.

**Event 2 — Runner plan seal:** a read-only isolated Runner derives its own
plan from the start tree and the permitted Stage 1 facts. Trusted recorder
seals plan/activation/start-manifest identities before Stage 2 disclosure.

**Stage 2 and promotion:** NOT IMPLEMENTED in this slice.

## CLI (run the trusted recorder OUTSIDE the original checkout)

The original seed commit does not contain the new experimental Runner script.
Install its exact reviewed version in a trusted recorder environment; invoke
that copy against the clean original Agent 1 source checkout. Never copy the
recorder's implementation into the original source tree just to run capture.

    python /trusted-tools/experiments/buddy_runner_v1/runner_protocol.py start \
      --repo . --snapshot /isolated/run-001 --run run-001 \
      --start-sha ACTUAL_START_SHA --initial-packet /recorder/original-what-why.json

After Agent 1 continues coding and signals TIME_FOR_RUNNER:

    python /trusted-tools/experiments/buddy_runner_v1/runner_protocol.py activate \
      --snapshot /isolated/run-001 --packet /recorder/late-what-why.json \
      --evidence /recorder/agent-task-evidence.md

Once Runner authors its INDEPENDENT plan, recorder-owned sealing:

    python /trusted-tools/experiments/buddy_runner_v1/runner_protocol.py seal \
      --snapshot /isolated/run-001 \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json \
      --plan /recorder-only/runner-own-plan.json

Verify before Stage 2 reveal:

    python /trusted-tools/experiments/buddy_runner_v1/runner_protocol.py verify-gate \
      --snapshot /isolated/run-001 \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json

The underlying runner_stage1.py helpers are intentionally lower-level
building blocks. A valid two-event experimental workflow MUST use the
runner_protocol.py activation and bound gate, not a bare plan receipt.

    python -m unittest discover -s experiments/buddy_runner_v1 -p 'test_*.py' -v


## BR-05 — Advisory TIME_FOR_RUNNER and Stage 1 trigger binding

This experimental module is an additional ORDINARY TASK_EVIDENCE / CHECKPOINT
payload, not a fifth engineering publication family. Its JSON block is
RUNNER_READINESS_V1, explicitly separate from CHECKPOINT_FACTS_V1.
It never authors DELP P/E/D, issue title, execution permission or writer
transfer.

Generate the advisory from a source-labelled observation (may be UNKNOWN):

    python /trusted-tools/experiments/buddy_runner_v1/runner_readiness.py render \
      --observation /recorder/runner-observation.json \
      --output /recorder/agent-task-evidence.md

Validate it before treating it as the Agent 1 Runner request:

    python /trusted-tools/experiments/buddy_runner_v1/runner_readiness.py verify \
      --evidence /recorder/agent-task-evidence.md

Example input fixture: fixtures/readiness_70_percent_synthetic.json. It uses
AGENT_SELF_ESTIMATE/LOW confidence and **does not invent context-token telemetry
or an actual Agent 1 execution**. A trusted external agent/session recorder
must separately anchor the identity of the comment author, provider content,
candidate and actual observation time. The local generator only makes a
syntactically valid *publishable proposal*; it DOES NOT POST to GitHub.

The production CLI for runner_protocol activate now requires --evidence.
It parses the TASK_EVIDENCE record, requires REQUEST_RUNNER or URGENT_RUNNER,
and binds run_id/responsibility to the original pinned START manifest. It
adds only an opaque evidence digest to the Stage 1 activation; the Runner
does not see current candidate HEAD or context-token measurements. Legacy
Python-function activation without evidence is marked AGENT_SIGNAL_UNVERIFIED
and must never count as independently proven readiness.

Calibration is tentative: at 60% PREPARE, approximately 70% REQUEST,
approximately 85% URGENT. A severe warning, imminent interruption, or next
unit consuming remaining reliable runway triggers earlier. Missing telemetry
is UNKNOWN, not HEALTHY. Provider-reported values are still untrusted when
merely supplied by an agent; source_trust remains explicitly unverified.

## Stage 2 read-only reconciliation (BR-04, experimental)

Only after the independent Stage 1 plan is recorded and sealed, expose the
current Agent 1 source and its plan. The Stage 2 command validates the Stage 1
gate FIRST, observes a clean exact Git HEAD, checks that the original START
commit is an ancestor of the current HEAD, derives all changed file paths,
identifies changes outside R01's parser write surface, and produces a versioned
source-bound plan-comparison record.

The predecessor plan is a JSON object with approach[], pending[],
source_claims[], and next_action. The Runner reconciliation decisions object
must contain agreements[], agent1_stronger[], runner_stronger[], unresolved[],
high_roi_in_scope[], medium_roi_parked[], next_action, and owner_scope_change
(NONE or OWNER_DECISION_REQUIRED). Each decision entry is a finding/why/
evidence_refs record; refs are still agent-supplied, not independently qualified.

Run the reconciler FROM A TRUSTED TOOL INSTALLATION OUTSIDE the source checkout:

    python /trusted-tools/experiments/buddy_runner_v1/stage2_reconcile.py \
      --snapshot /isolated/run-001 \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json \
      --repo /checkout/Agent1-current-R01 \
      --head VERIFIED_CURRENT_40_HEX_SHA \
      --incumbent-plan /recorder-only/incumbent.json \
      --decisions /recorder-only/runner-comparison.json \
      --report /recorder-only/read-only-stage2.json

This stage rejects a stale candidate HEAD, dirty/untracked working files,
missing/tampered Stage 1 gate, an unrelated or non-descendant source, an
unsealed output target, and malformed/non-evidenced plan-disagreement records.
It does NOT validate PR/CI via GitHub, execute tests, authenticate the original
Owner message, publish to an issue, or promote the Runner to a writer.

The report ALWAYS states execution_authority: NOT_GRANTED and
writer_transfer: NOT_ATTEMPTED. Verification/Owner authority must come through
a distinct externally verified admission protocol. A suggestion about medium
ROI remains parked and cannot silently change released graph scope.

## Boundaries and unproven requirements

No current source, PR statistics, Agent 1 HOW, final plan, current CI or future
issue comments are included in the Stage 1 snapshot. The snapshot directory
must be provided to Runner INSTEAD of a live Git checkout. The host must deny
Runner network, GitHub connectors, credentials and chat with future details:
these Python helpers do not revoke external privileges.

The late WHAT/WHY packet's free text can still leak HOW if maliciously authored;
syntactic field validation cannot prove no semantic hints. Independently screen
such packets before a blinded trial.

Filesystem exclusive-create and SHA256 detect accidental/simple post-seal edits,
NOT coordinated tampering, authenticated Owner origin or chronological fact.
Trusted immutable recorder storage, temporal order attestation and source
provenance remain to be built. Its contents must not be writable by either
coding agent.

Pending: Agent Health working-runway calibration; event-gated TIME_FOR_RUNNER
advisory in existing TASK_EVIDENCE without DELP score changes; source-pinned
Owner/issue snapshot and cutoff guard; real Runner execution; independent
Stage 2 plan reconciliation; single-writer fenced promotion; 50/70/85% trial,
clean no-injury control and independent measured recovery economics.

No Common frozen V3.2 source, native owner contract or existing R01 product
file changed. These unit tests use temporary Git repositories, and a passing
CI run would only qualify these helper functions, not the complete V3.2
end-to-end lifecycle or a real interrupted-agent takeover.
