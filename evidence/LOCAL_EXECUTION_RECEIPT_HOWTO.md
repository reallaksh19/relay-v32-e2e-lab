# V3.2 lab — exact-source local execution receipt (P3)

This document and the associated code distinguish **executed test output** from **admissible, independently attested checkpoint evidence**.

## Exact basis

Historical known-good lab application source: `73ffc780f4dfbd9de9010bbe71524f6f6de72765`. The seven pinned Python files are identified individually by their **actual Git blob SHA-1s** in `COMMITTED_ACCEPTANCE_BLOBS_V1.json`. This source commit is an immutable replay reference; it is NOT a substitute for checking the current default-branch graph, CI event SHA or PR head at acceptance time.

Existing graph binds R01→PR#8, R02→PR#13 and R03→PR#15. The original committed acceptance suites have respectively 4, 3 and 2 cases; locally created supplementary tests are **not** part of the nine-case committed golden set.

## Replay (requires Python 3.11+ and a source checkout)

Run from an actual checkout containing the files listed in the manifest:

```sh
python -m unittest discover -s tests -p test_exact_source_test_receipt.py -v
python scripts/exact_source_test_receipt.py \
  --root . \
  --manifest evidence/COMMITTED_ACCEPTANCE_BLOBS_V1.json \
  --output /tmp/v32-local-execution-receipt.json
```

The runner first compares each test and production Python source file to the expected Git object blob, rejecting absent/changed/symlinked files. It then launches each of the **three real committed acceptance suites**, checks subprocess exit code and exactly collected test IDs, and records nine collected tests with observed return codes and log digests. It rejects a false zero-test "OK" and unexpected test-class substitutions.

The checked-in `LOCAL_EXECUTION_RECEIPT_V1.json` is the observed run made in this conversation, after checking all seven file blobs and executing 9/9 committed tests locally. The replay checks themselves ran 14/14. A different Python version or machine can yield a different *log hash* because unittest prints runtime seconds, while the named test result and source identifiers should match.

## Evidence custody and native V3.2 next gate

This is a **SELF-OPERATED LOCAL TEST RECEIPT**. Neither the checked-in file nor its hash proves that a separate independent reviewer witnessed execution; nor does it prove the local workspace was fetched exclusively from the claimed commit. Verify the Git blob identities directly against GitHub and require external run/witness evidence before admission.

The separate `.github/workflows/v32-committed-acceptance-receipt.yml` is designed to execute the same pinned tests from a real `GITHUB_SHA`, upload a receipt and a GitHub Actions run-link artifact, and leave the token read-only. Its success must be observed from actual executed steps and artifact readback. Hosted runners currently fail before execution; the workflow source alone is not a PASS.

**Never turn `LOCAL_PASS_NOT_INDEPENDENT` into `CHECKPOINT_FACTS_V1` with `COMPLETE/VERIFIED` and arbitrary nonempty `evidence_refs`.** The pinned Common V3.2 pure projector can accept syntactically nonempty refs that have not been independently authenticated. An authorized producer must witness the exact candidate source, the golden outcome, test log artifact, provider head, protected Owner instruction/actor, and base/graph epoch; only then may a trusted native fact be proposed/published and the issue/PR scoreboards projected. T05 remains `WAIVED_NOT_PASSED` and is NOT Owner approval.

No writes to issue titles, PR managed descriptions, engineering source, Common protocol or Buddy Runner are performed by this package.
