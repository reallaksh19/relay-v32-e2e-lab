"""Deterministic baseline-only fixture: NOT a live LLM Runner."""
import json, pathlib, socket
root=pathlib.Path('/blind')
manifest=json.loads((root/'manifest.json').read_text())
path=root/'source/src/csv_auditor/parser.py'
assert path.exists()
for forbidden in ('/etc/passwd','/mnt/data','/home/oai','/root/.ssh'):
    assert not pathlib.Path(forbidden).exists(), forbidden
try:
    socket.create_connection(('1.1.1.1',443),timeout=1)
    raise RuntimeError('NETWORK_BYPASS')
except OSError:
    pass
out={"source_baseline_sha": manifest['origin']['initial_commit'], "blind_source_paths":sorted(manifest['source_files']),"network":"DENIED","host_credentials":"UNMOUNTED","runner_type":"DETERMINISTIC_TEST_FIXTURE_NOT_LLM","writer_authority":"NOT_GRANTED"}
plan = {
    "understanding": ["R01 requires reliable CSV record ID handling; reconstructed from original seed only"],
    "approach": ["Inspect original parser and R01 input oracle; implement strict ID validation"],
    "rejected_alternatives": ["Silently coerce missing/duplicate IDs"],
    "assumptions": ["Frozen original acceptance oracle sets scope"],
    "questions": ["Are additional CSV dialects Owner-approved?"],
    "next_action": "Run the frozen missing/duplicate ID oracle against candidate code",
}
pathlib.Path('/output/runner_plan.json').write_text(json.dumps(plan,sort_keys=True))
pathlib.Path('/output/fixture_result.json').write_text(json.dumps(out,sort_keys=True))
print(json.dumps(out,sort_keys=True))
