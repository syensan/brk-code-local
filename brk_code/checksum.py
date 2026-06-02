"""BRK-Code semantic checksum computation."""

from __future__ import annotations

import hashlib
from typing import Any

from .util import canonical_serialize


def compute_semantic_checksum(
    contract: dict[str, Any],
    repo_graph: dict[str, Any],
    ast_semantic_graph: dict[str, Any],
    symbol_table: dict[str, Any],
    dependency_graph: dict[str, Any],
    task_outputs: dict[str, Any],
    flags: dict[str, Any],
) -> dict[str, str]:
    """Compute SHA-256 semantic checksum over key container sections.

    This is NOT a bit-exact checksum of source files.
    It verifies the integrity of the semantic code graph.
    """
    parts = [
        canonical_serialize(contract),
        canonical_serialize(repo_graph),
        canonical_serialize(ast_semantic_graph),
        canonical_serialize(symbol_table),
        canonical_serialize(dependency_graph),
        canonical_serialize(task_outputs),
        canonical_serialize(flags),
    ]
    h = hashlib.sha256()
    for part in parts:
        h.update(part)
    return {
        "algorithm": "sha256",
        "type": "semantic",
        "digest": h.hexdigest(),
        "note": "Semantic checksum over code meaning graph. Not a bit-exact checksum of source files.",
    }
