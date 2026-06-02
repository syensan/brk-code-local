"""Sparse source residual management for BRK-Code."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .ast_analyzer import ASTResult
from .constants import DEFAULT_MAX_SNIPPET_LINES


def build_sparse_source_residual(
    source_dir: Path,
    ast_result: ASTResult,
    include_snippets: bool = False,
    max_snippet_lines: int = DEFAULT_MAX_SNIPPET_LINES,
) -> dict[str, Any]:
    """Build the sparse_source_residual section.

    By default, no source snippets are stored.
    With include_snippets=True, minimal function signature+docstring snippets
    are stored for AI learning context.

    This is NOT a full source snapshot.
    """
    snippets: list[dict[str, Any]] = []

    if not include_snippets:
        return {
            "policy": "minimal_snippets_only",
            "snippets": snippets,
            "note": "No snippets included. Use --include-snippets to include minimal function context.",
        }

    for func in ast_result.functions:
        if func.name.startswith("test_"):
            continue
        if func.name.startswith("_") and func.name != "__init__":
            continue

        file_path = source_dir / func.file
        if not file_path.exists():
            continue

        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        # Extract snippet: function signature + docstring context
        start = max(0, func.line - 1)  # 0-indexed
        # Limit snippet length
        end_line = min(func.end_line, func.line + max_snippet_lines - 1)
        end = min(end_line, len(lines))

        snippet_lines = lines[start:end]
        snippet_text = "\n".join(snippet_lines)

        # Only include if there's meaningful content
        if len(snippet_text.strip()) > 0:
            snippets.append({
                "file": func.file,
                "line_start": func.line,
                "line_end": end_line,
                "reason": "function_signature_and_docstring_context",
                "text": snippet_text,
            })

    return {
        "policy": "minimal_snippets_only",
        "snippets": snippets,
        "note": "This is not a full source snapshot. Only minimal function context for AI learning.",
    }
