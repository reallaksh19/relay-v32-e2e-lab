"""R01 executable boundary; implementing this is a genuine task, not seeded as complete."""
from pathlib import Path


def read_rows(path: str | Path) -> dict[str, dict[str, str]]:
    """Return id -> column/value mapping, validating header and unique nonempty IDs."""
    raise NotImplementedError("R01 is not implemented; see real leaf issue")
