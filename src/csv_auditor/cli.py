"""R03 — deterministic JSON CSV-diff CLI with fail-closed input errors."""
from __future__ import annotations

import json
import sys

from .compare import diff
from .parser import read_rows


def main(argv: list[str] | None = None) -> int:
    """Accept exactly two CSV paths and print one JSON result on full success."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("CSV_ERROR: expected exactly two CSV input paths", file=sys.stderr)
        return 2

    try:
        before = read_rows(args[0])
        after = read_rows(args[1])
        changes = diff(before, after)
    except (OSError, ValueError) as exc:
        print(f"CSV_ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(changes, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
