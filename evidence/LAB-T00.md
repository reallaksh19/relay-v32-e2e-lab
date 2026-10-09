# TASK_EVIDENCE — LAB-T00 — Clean ZIP preflight and local-agent smoke test PASS

**Experiment:** Common V3.2 CSV Auditor private GitHub lab; governed by `reallaksh19/Common#876`.

- **Task ID:** LAB-T00
- **Status:** PASS
- **Operator/agent identity:** Antigravity local agent (authenticated via `gh` CLI as `reallaksh19`)
- **Repository:** `reallaksh19/relay-v32-e2e-lab` (NOT_CREATED; clean extracted workspace at `C:\CodeB\relay-v32-e2e-lab-starter` with no `.git`)
- **Protocol:** `reallaksh19/Common@13989969f6b7e432c4f7c1ddfe975449dba53593:skills/engineering-pr-delivery-v3.2`
- **Executed material SHA:** NOT_APPLICABLE (Clean ZIP extraction; Archive SHA256: `9f1c317494168bda0ea83baf31c5a6db4d6035085c102743b22c707c3f4a5030`)
- **Commands executed:**
  1. `Get-FileHash C:\Users\reall\Downloads\relay-v32-e2e-lab-starter.zip -Algorithm SHA256`
  2. `python -c "import json, hashlib, pathlib; manifest = json.load(open('evidence/file-manifest.json'))['files']; mismatches = []; [mismatches.append(f) for f, h in manifest.items() if hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() != h]; print('Mismatches:', mismatches, 'Total verified:', len(manifest))"`
  3. `git status`
  4. `python -m unittest discover -s tests -v`
  5. `python scripts/acceptance_stage.py --branch lab/r01 --plan`
  6. `python -m unittest discover -s acceptance -p "test_r*.py" -v`
- **Exit code(s):**
  1. `0` (computed SHA256 `9F1C317494168BDA0EA83BAF31C5A6DB4D6035085C102743B22C707C3F4A5030`)
  2. `0` (`Mismatches: [] Total verified: 34`)
  3. `1` (`fatal: not a git repository (or any of the parent directories): .git`)
  4. `0` (`Ran 27 tests in 0.007s -> OK`)
  5. `0` (`{"branch": "lab/r01", "scope": "RESPONSIBILITY_AND_PREDECESSORS_ONLY", "selected_acceptance_patterns": ["test_r01_input.py"]}`)
  6. `1` (`Ran 9 tests in 0.100s -> FAILED (failures=2, errors=7)`)
- **Expected independent oracle:**
  - Archive checksum matches `9f1c317494168bda0ea83baf31c5a6db4d6035085c102743b22c707c3f4a5030` and 34 manifest files match exactly.
  - Workspace is clean and not a git repository (`.git` absent).
  - Starter smoke suite: 27 PASS.
  - Acceptance stage planner for `lab/r01` selects only `test_r01_input.py`.
  - Product acceptance suite: 9 intentional precommitted RED tests (2 assertion failures, 7 `NotImplementedError` errors).
- **Observed actual output:**
  - Test suite stdout:
    ```text
    Ran 27 tests in 0.007s
    OK
    ```
  - Stage planner stdout:
    ```text
    {"branch": "lab/r01", "scope": "RESPONSIBILITY_AND_PREDECESSORS_ONLY", "selected_acceptance_patterns": ["test_r01_input.py"]}
    ```
  - Acceptance suite excerpt:
    ```text
    ERROR: test_empty_id (test_r01_input.R01InputAcceptance.test_empty_id) -> NotImplementedError: R01 is not implemented; see real leaf issue
    ERROR: test_missing_header (test_r01_input.R01InputAcceptance.test_missing_header) -> NotImplementedError: R01 is not implemented; see real leaf issue
    ERROR: test_valid (test_r01_input.R01InputAcceptance.test_valid) -> NotImplementedError: R01 is not implemented; see real leaf issue
    ERROR: test_no_change (test_r02_compare.R02CompareAcceptance.test_no_change) -> NotImplementedError: R02 is not implemented; see real leaf issue
    ERROR: test_stable_sorting (test_r02_compare.R02CompareAcceptance.test_stable_sorting) -> NotImplementedError: R02 is not implemented; see real leaf issue
    ERROR: test_three_change_classes (test_r02_compare.R02CompareAcceptance.test_three_change_classes) -> NotImplementedError: R02 is not implemented; see real leaf issue
    FAIL: test_end_to_end (test_r03_cli.R03CLIAcceptance.test_end_to_end) -> AssertionError: 0 != 1 (NotImplementedError: R03 is not implemented)
    FAIL: test_invalid_fails_closed (test_r03_cli.R03CLIAcceptance.test_invalid_fails_closed) -> AssertionError: 'CSV_ERROR:' not found (NotImplementedError)
    Ran 9 tests in 0.100s
    FAILED (failures=2, errors=7)
    ```
  - Directory check:
    - No `.git` present.
    - No `package.json` in workspace (confirmed Python-only layout).
    - 34/34 files matching manifest hashes.
- **Result comparison:** MATCH — Independent local-agent execution matches all preflight expectations. 27 starter tests pass, R01 planner isolates R01, 9 functional acceptance tests remain precommitted RED.
- **Durable source refs:**
  - Tracking issue: https://github.com/reallaksh19/Common/issues/876
  - Prior assistant preflight: https://github.com/reallaksh19/Common/issues/876#issuecomment-6076987550
  - Prior environmental blocker record: https://github.com/reallaksh19/Common/issues/876#issuecomment-6077411072
  - Target lab repository: NOT_CREATED (`reallaksh19/relay-v32-e2e-lab`)
- **Negative controls:**
  - Expected negative: 9 product acceptance tests intentionally failed (exit 1).
  - Expected negative: `git status` failed (exit 1, repository not initialized yet).
- **Blockers and unknowns:**
  - Environment blocker (`googlecloudtools.datacloud_telemetry` PreToolUse hook crash) resolved by operator running `agy plugin disable googlecloudtools.datacloud_telemetry`.
  - Remote repository `reallaksh19/relay-v32-e2e-lab` not yet created.
  - Pinned Common repository not yet cloned locally.
- **Next authorized task:** LAB-T01 (Clone private Common at immutable V3.2 SHA `13989969f6b7e432c4f7c1ddfe975449dba53593`).
- **Evidence publication URL:** https://github.com/reallaksh19/Common/issues/876#issuecomment-6077570006

**Owner/custody restrictions:** This message is a local agent's test report, **not** independent review, source authenticity proof or a published `CHECKPOINT_FACTS_V1` progress record. Emit the latter only on a real released leaf when source facts, PR head and evidence are proven.
