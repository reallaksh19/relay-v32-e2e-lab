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

## CLI (run from original clean START checkout with a trusted recorder)

    python experiments/buddy_runner_v1/runner_protocol.py start \
      --repo . --snapshot /isolated/run-001 --run run-001 \
      --start-sha ACTUAL_START_SHA --initial-packet /recorder/original-what-why.json

After Agent 1 continues coding and signals TIME_FOR_RUNNER:

    python experiments/buddy_runner_v1/runner_protocol.py activate \
      --snapshot /isolated/run-001 --packet /recorder/late-what-why.json

Once Runner authors its INDEPENDENT plan, recorder-owned sealing:

    python experiments/buddy_runner_v1/runner_protocol.py seal \
      --snapshot /isolated/run-001 \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json \
      --plan /recorder-only/runner-own-plan.json

Verify before Stage 2 reveal:

    python experiments/buddy_runner_v1/runner_protocol.py verify-gate \
      --snapshot /isolated/run-001 \
      --receipt /recorder-only/run-001.plan.json \
      --gate /recorder-only/run-001.gate.json

The underlying runner_stage1.py helpers are intentionally lower-level
building blocks. A valid two-event experimental workflow MUST use the
runner_protocol.py activation and bound gate, not a bare plan receipt.

    python -m unittest discover -s experiments/buddy_runner_v1 -p 'test_*.py' -v

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
