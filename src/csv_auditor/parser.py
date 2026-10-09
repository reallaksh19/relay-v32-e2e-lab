"""R01 — validated CSV input with lossless keyed field values."""
from __future__ import annotations

import csv
from pathlib import Path


def read_rows(path: str | Path) -> dict[str, dict[str, str]]:
    """Map each exact ID to its unchanged non-ID column values.

    Fail closed on a missing/ambiguous header, empty or duplicate IDs,
    malformed CSV quoting, or rows that do not match the declared columns.
    ID spelling and data fields are deliberately not normalized.
    """
    rows: dict[str, dict[str, str]] = {}
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            header = next(reader, None)
            if not header or "id" not in header:
                raise ValueError("CSV header must contain an 'id' column")
            if any(not name.strip() for name in header) or len(header) != len(set(header)):
                raise ValueError("CSV header has empty or duplicate column names")

            id_index = header.index("id")
            for values in reader:
                if len(values) != len(header):
                    raise ValueError(
                        f"CSV row ending at line {reader.line_num} has "
                        f"{len(values)} fields; expected {len(header)}"
                    )
                identity = values[id_index]
                if not identity.strip():
                    raise ValueError(f"CSV row ending at line {reader.line_num} has empty id")
                if identity in rows:
                    raise ValueError(
                        f"CSV row ending at line {reader.line_num} has duplicate id {identity!r}"
                    )
                rows[identity] = {
                    name: value
                    for name, value in zip(header, values)
                    if name != "id"
                }
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV input: {exc}") from exc

    return rows
