"""Fail-closed responsibility-scoped acceptance selection for lab PRs.

Never grade the whole unfinished programme as a condition for an R01-only PR.
All earlier responsibilities must be green for a later stage to pass. On main
all product acceptance cases run and may deliberately remain RED before R03.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

PATTERNS = {
    'R01': ['test_r01_input.py'],
    'R02': ['test_r01_input.py', 'test_r02_compare.py'],
    'R03': ['test_r01_input.py', 'test_r02_compare.py', 'test_r03_cli.py'],
}


def stage_patterns(branch: str) -> list[str]:
    if branch == 'main':
        return list(PATTERNS['R03'])
    match = re.fullmatch(r'lab/(r0[123])(?:/[A-Za-z0-9_.-]+)*', branch)
    if match is None:
        raise ValueError(f'BRANCH_UNGOVERNED: {branch!r}; expected lab/r01, lab/r02, lab/r03, or main')
    return list(PATTERNS[match.group(1).upper()])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', required=True, help='Real GitHub head_ref (or main)')
    parser.add_argument('--plan', action='store_true', help='Print exact selected tests but do not execute')
    args = parser.parse_args()
    try:
        patterns = stage_patterns(args.branch)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'branch': args.branch, 'selected_acceptance_patterns': patterns,
                      'scope': 'RESPONSIBILITY_AND_PREDECESSORS_ONLY' if args.branch != 'main' else 'FULL_PROGRAMME'},
                     sort_keys=True), flush=True)
    if args.plan:
        return 0
    for pattern in patterns:
        cmd = [sys.executable, '-m', 'unittest', 'discover', '-s', 'acceptance', '-p', pattern, '-v']
        completed = subprocess.run(cmd, check=False)
        if completed.returncode:
            print(f'RESPONSIBILITY_ACCEPTANCE_RED: {pattern}', file=sys.stderr)
            return completed.returncode
    print('SELECTED_RESPONSIBILITY_ACCEPTANCE_PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
