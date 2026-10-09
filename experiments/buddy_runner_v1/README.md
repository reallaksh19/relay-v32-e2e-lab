# Engineering Relay V3.2 — Buddy Runner blind Stage 1 (experimental)

**Status:** isolated research/code experiment, not a production V3.2 feature.
Governing qualification: Common #879; existing lab R01 responsibility: lab #4.
The lab synthetic CSV programme does not become a new Owner requirement.

## Prompt-first operating entrypoint — “Prepare for runner” (Markdown-only proposal)

The reusable instructions are in [prompt_first/PREPARE_FOR_RUNNER_ENTRYPOINT.md](prompt_first/PREPARE_FOR_RUNNER_ENTRYPOINT.md),
[Stage 1](prompt_first/STAGE1_THINKING_TEMPLATE.md),
[Stage 2](prompt_first/STAGE2_RECONCILIATION_TEMPLATE.md), and
[operator examples](prompt_first/OPERATOR_GUIDE_EXAMPLES.md).

The Owner may say **“Prepare for runner”** to an *active* Agent A.
Under the prompt-first contract that means: assess actually available
episode/context-life evidence; begin the sanitized original-source and
WHAT/WHY intake immediately; and continue the authorized engineering
task. At each ordinary TASK_EVIDENCE checkpoint, Agent A should
proactively suggest **“Time for Runner”** near approximately 70% of
**estimated agent life consumed** (60% prepare; 85% urgent), or earlier
for credible reliability/next-unit runway warnings. Provider-reported
tokens, calibrated episode estimates, self-estimates and UNKNOWN are
distinct; never invent token readings or substitute task P/E/D or
seven-component delivery health for context-life consumption.

No Markdown prompt automatically reads hidden model context-window
telemetry, triggers in the background, creates a new AI Runner session
or enforces tool access. The live agent/operator must actually load the
entrypoint and separately enforce a fresh Stage 1 restricted context.
The legacy BR-05 Python advisory remains an *optional historical
experiment*; the prompt-first revamp does not change or require it.
A suggestion is not observed Stage 1 execution, a sealed plan,
Stage 2 disclosure or a transfer of exclusive source-write authority.

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

**Stage 2:** read-only reconciliation and local custody-event gate implemented for the research harness. **Exclusive-writer promotion:** NOT IMPLEMENTED.

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

## BR-08 — Actual namespace fixture and provider readback preflight

See [BR08_QUALIFICATION.md](BR08_QUALIFICATION.md) for reproducible
steps, exact qualification boundaries, and the failed witness-admission
preflight.

The BR-08 subprocess uses real Linux user, mount, network, PID and IPC
namespaces (unshare), private tmpfs root/chroot, read-only source mount and
a separate empty output mount. The sandboxed executable is a DETERMINISTIC
TEST FIXTURE, not an LLM. One integrated rehearsal verifies that the
original frozen source can drive an isolated plan, sealed before read-only
Stage2 reconciliation after simulated Agent1 progress. It does not run
a real independent AI or observe a real Agent1 interruption.

provider_readback.py handles GitHub provider-shaped comments but always
reports STRUCTURALLY_VALIDATED_ONLY, never an authenticated online readback.
The connected GitHub comment reader returned null created_at/updated_at
for inspected Common #879 evidence; chronological witness admission
therefore FAILS CLOSED. Independent signing provider remains unconfigured.

Local Python suite: 82/82 PASS at BR08 implementation baseline.
Hosted GitHub Actions, witness independence and Owner-approved writer
promotion remain NOT QUALIFIED.

## BR-07 — Detached external witness + fail-closed Runner launch

Two security boundaries have now been added to the experimental helpers.

**1. Detached witness — witness_anchor.py**

The Stage 2 CLI requires a versioned Ed25519-signed PLAN_SEALED witness
receipt. The verifier checks the witness's exact public key against an
independently pinned SHA-256 fingerprint, validates the detached signature,
matches the signing event to the MAC-verified recorder journal's third
event (PLAN_SEALED), and binds original source manifest + plan receipt
+ sealed Stage 1 gate digests. Modified/replayed run IDs, changed plans,
wrong keys, noncanonical/duplicate JSON keys, missing/wrong signatures,
and invalid stage ordering fail closed.

The witness MUST be a truly independent signer, with private key and
publication custody inaccessible to Agent 1, Runner and the application
recorder. **No production signing endpoint, key, provider callback,
timestamp authority or external witness receipt has been configured.**
Tests generate temporary Ed25519 keys, *not* real external attestation.
A signature validates only signer/key/basis; it does not prove an
immutable provider posting, authentic UTC timestamp, receipt creation
before disclosure, or organizational independence. All of those still
require independent provider-side evidence.

Additional REQUIRED Stage2 CLI inputs (in addition to BR-06 parameters):

    --witness-receipt /trusted-readback/runner-seal.witness.json
    --witness-public-key /trusted-config/witness-ed25519-public.raw
    --witness-key-fingerprint sha256:PINNED_SHA256_OF_32_PUBLIC_KEY_BYTES
    --witness-id OWNER_AUTHORIZED_INDEPENDENT_WITNESS

The receipt must be independently retrieved from the witness's provider;
copying it from Agent 1's checkout or a self-authored packet is not
proven custody. The local verifier always reports provider_readback:
NOT_VERIFIED_BY_THIS_MODULE and execution_authority: NOT_GRANTED.

Python dependency: cryptography==46.0.4, pinned for CI.

**2. Runner launch — isolated_runner.py**

The prototype constructs a fixed, no-shell Docker invocation whose image
must be digest-pinned and equal to an independently controlled approved
image string. Only the four allowlisted original source files, original
manifest and later sanitized activation are mounted at /blind READ ONLY.
The empty Runner output directory is separately mounted at /output.
Docker network is NONE, image is read-only, Linux caps are dropped,
no-new-privileges applied, memory/process limits fixed, and host
environment restricted. No host Git checkout, home directory, GitHub
credential, recorder key, PR statistics, Stage2 source or future issue
comments may be mounted. Extra files and symlinks in the blind source
bundle cause immediate rejection.

    python /trusted-tools/experiments/buddy_runner_v1/isolated_runner.py \
      --snapshot /isolated/run-001 \
      --output /runner-output/empty-run-001 \
      --image OWNER_REVIEWED_RUNNER_IMAGE@sha256:EXACT_64_HEX_DIGEST \
      --approved-image OWNER_REVIEWED_RUNNER_IMAGE@sha256:EXACT_64_HEX_DIGEST

The CLI's equality check is a local protection, not proof of Owner image
authorization: the approved digest must come from independently secured
configuration. No container image/Runner intelligence has been supplied
or executed in this experimental PR. Docker is absent on the testing
host; Linux unshare -n is denied; launch therefore fails closed
with ISOLATED_RUNTIME_UNAVAILABLE_NO_FALLBACK.

An actual isolated Runner host must independently prove its Docker daemon
configuration, image provenance, mount confinement, credential isolation,
network denial and runtime logs; a simulated subprocess/unit test is not a
qualification of a live LLM Runner. This module NEVER promotes Runner,
creates a new R01 responsibility, or publishes accepted TaskEvidence.

**Verification:** 64/64 focused local tests PASS with temporary Git repos
and synthetic witness keys; 13 witness and 11 isolation cases extend the
previous 40. No real external witness service, runtime isolation execution,
live Agent1→Runner continuity, or Chromium/browser exercise is claimed.
Hosted CI remains blocked by jobs failing without visible steps.

## BR-06 — Recorder-keyed event ordering (experiment only)

The trusted recorder must hold an independent random 32-byte-or-longer secret
in its own environment (BUDDY_RECORDER_KEY_HEX), inaccessible to Agent 1,
Runner, chat, source control and GitHub Actions logs. Do not use the fixed
test-only key from test_recorder_custody.py. Linux fcntl file locking is used;
this module does not provide a Windows-hosted recorder implementation.

BR-06 implements a fail-closed four-event sequence in
recorder_custody.py:

1. START_PINNED — hash of original source manifest and actual start SHA.
2. RUNNER_REQUESTED — validated activation digest (parsed readiness evidence,
   explicitly still unauthenticated until a provider/recorder confirms origin).
3. PLAN_SEALED — stage1 independent-plan receipt and sealed gate digests.
4. STAGE2_DISCLOSED — digest of post-seal disclosure manifest, bound to one
   current candidate HEAD and incumbent-plan digest.

Each append locks the recorder journal, verifies its MAC chain + expected
prior event and writes a new HMAC-SHA256 record with fsync. The journal must
reside in recorder-controlled storage, outside agent-controlled directories.
A previously observed last MAC can be supplied as --last-mac on append/verify;
a self-copied journal MAC is NOT independently witnessed evidence.

Recoding the test sequence with trusted tools:

    python /trusted-tools/experiments/buddy_runner_v1/recorder_custody.py start \
      --snapshot /isolated/run-001 --journal /recorder-only/run-001.jsonl

    python /trusted-tools/experiments/buddy_runner_v1/recorder_custody.py request \
      --snapshot /isolated/run-001 --journal /recorder-only/run-001.jsonl \
      --last-mac PREVIOUS_EXTERNALLY_RETAINED_MAC

    python /trusted-tools/experiments/buddy_runner_v1/recorder_custody.py seal \
      --snapshot /isolated/run-001 --journal /recorder-only/run-001.jsonl \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json \
      --last-mac PREVIOUS_EXTERNALLY_RETAINED_MAC

    python /trusted-tools/experiments/buddy_runner_v1/recorder_custody.py disclose \
      --snapshot /isolated/run-001 --journal /recorder-only/run-001.jsonl \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json \
      --disclosure /recorder-only/run-001.disclosure.json \
      --last-mac PREVIOUS_EXTERNALLY_RETAINED_MAC

The disclosure JSON must contain exactly: run_id, candidate_sha (40 hex),
incumbent_plan_digest (sha256), source_context_digest (sha256). Its digests
bind caller-supplied facts; they do not prove CI/PR correctness by themselves.
An actual independent recorder MUST anchor each phase before disclosure
through an independently controlled append-only provider artifact or
timestamped storage. The local code cannot prove historical timing,
provenance, author identity, or prevent full journal rollback without an
external anchor.

**Stage 2 CLI is now fail-closed:** requires --custody-journal,
--disclosure, and --external-anchor; the recorder's secret is read from
BUDDY_RECORDER_KEY_HEX, never passed through the command line. It rejects a
missing disclosure, mismatched candidate/Agent 1 plan, modified MAC chain,
absent anchor or wrong phase order before current source reconciliation.
A caller may provide its own MAC, so external authentication still requires
independent custody, not simply matching a local digest.

The direct Python reconcile(...) API remains usable in unit tests and
returns UNATTESTED_LOCAL_LIBRARY_CALL if no custody proof is supplied.
Neither API can grant source-write permission, Owner authority, or merge
permission. Stage 2 reconciliation remains local-source only, with provider
CI/PR truth UNKNOWN.

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
      --report /recorder-only/read-only-stage2.json \
      --custody-journal /recorder-only/run-001.jsonl \
      --disclosure /recorder-only/run-001.disclosure.json \
      --external-anchor EXTERNALLY_RETAINED_LAST_MAC \
      --witness-receipt /trusted-readback/runner-seal.witness.json \
      --witness-public-key /trusted-config/witness-ed25519-public.raw \
      --witness-key-fingerprint sha256:TRUSTED_64_HEX_DIGEST \
      --witness-id INDEPENDENT_WITNESS

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

Pending: actual Agent Health provider observations and calibration; source-pinned
Owner/issue historical cutoff and authenticated provenance; a real Runner
without network/live GitHub access; independent external immutable recorder
custody; provider-current PR/CI; single-writer fenced promotion; repeated
50/70/85% and control trials with measured total recovery cost.

No Common frozen V3.2 source, native owner contract or existing R01 product
file changed. These unit tests use temporary Git repositories, and a passing
CI run would only qualify these helper functions, not the complete V3.2
end-to-end lifecycle or a real interrupted-agent takeover.
