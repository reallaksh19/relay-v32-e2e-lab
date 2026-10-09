"""R02 — deterministic classification of changes to R01 keyed CSV records."""
from __future__ import annotations


def diff(before: dict, after: dict) -> dict[str, list[str]]:
    """Return sorted, disjoint added/removed/modified IDs.

    Exact keys and field strings are compared without trimming or coercion.
    Dictionary/CSV row ordering has no effect. Neither input is mutated.
    """
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("R02 expects two R01 keyed-record mappings")

    previous_ids = set(before)
    current_ids = set(after)
    return {
        "added": sorted(current_ids - previous_ids),
        "removed": sorted(previous_ids - current_ids),
        "modified": sorted(
            identity for identity in previous_ids & current_ids
            if before[identity] != after[identity]
        ),
    }
