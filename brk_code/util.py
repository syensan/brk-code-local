"""Utility functions for BRK-Code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def canonical_serialize(obj: Any) -> bytes:
    """Serialize object to canonical JSON bytes (sorted keys, compact)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_json_str(obj: Any) -> str:
    """Serialize object to canonical JSON string (sorted keys, compact)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def format_size(n: int) -> str:
    """Format byte count as human-readable string."""
    if n < 1024:
        return f"{n} bytes"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    else:
        return f"{n / (1024 * 1024):.1f} MB"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_test_file(path: Path) -> bool:
    """Check if a path looks like a test file."""
    name = path.name
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
