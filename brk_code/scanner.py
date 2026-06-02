"""Source directory scanner for BRK-Code."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .constants import DEFAULT_EXCLUDE_DIRS, TARGET_EXTENSIONS, DEFAULT_EXCLUDE_PATTERNS
from .errors import SourceScanError
from .util import sha256_file, is_test_file


@dataclass
class ScannedFile:
    """Information about a scanned source file."""
    path: str
    language: str
    size_bytes: int
    sha256: str
    line_count: int
    imports: list[str] = field(default_factory=list)
    is_test: bool = False


@dataclass
class ScannedDirectory:
    """Information about a scanned directory."""
    path: str
    file_count: int = 0


def scan_source_directory(
    source_dir: Path,
    exclude_dirs: frozenset[str] | None = None,
) -> tuple[list[ScannedFile], list[ScannedDirectory]]:
    """Recursively scan a source directory for Python files.

    Returns (files, directories).
    """
    if not source_dir.is_dir():
        raise SourceScanError(f"Source directory does not exist: {source_dir}")

    exclude = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    files: list[ScannedFile] = []
    dir_map: dict[str, ScannedDirectory] = {}

    for path in sorted(source_dir.rglob("*")):
        # Check exclude directories
        parts = path.relative_to(source_dir).parts
        if any(part in exclude for part in parts):
            continue

        # Check exclude patterns
        if any(path.match(pat) for pat in DEFAULT_EXCLUDE_PATTERNS):
            continue

        if path.is_dir():
            rel = str(path.relative_to(source_dir))
            if rel not in dir_map:
                dir_map[rel] = ScannedDirectory(path=rel)
        elif path.is_file() and path.suffix in TARGET_EXTENSIONS:
            rel = str(path.relative_to(source_dir))
            rel_posix = rel.replace("\\", "/")

            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                raise SourceScanError(f"Cannot read file {path}: {e}") from e

            lines = text.splitlines()
            file_hash = sha256_file(path)

            # Quick import extraction (will be refined by AST analyzer)
            imports: list[str] = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    parts_import = stripped.split()
                    if len(parts_import) >= 2:
                        mod = parts_import[1].split(".")[0]
                        if mod not in imports:
                            imports.append(mod)

            sf = ScannedFile(
                path=rel_posix,
                language="python",
                size_bytes=path.stat().st_size,
                sha256=file_hash,
                line_count=len(lines),
                imports=imports,
                is_test=is_test_file(path),
            )
            files.append(sf)

            # Update directory counts
            parent = str(path.parent.relative_to(source_dir)).replace("\\", "/")
            if parent == ".":
                parent = "."
            if parent not in dir_map:
                dir_map[parent] = ScannedDirectory(path=parent)
            dir_map[parent].file_count += 1

    # Ensure root directory exists
    if "." not in dir_map:
        dir_map["."] = ScannedDirectory(path=".")

    # Count root files
    root_count = sum(1 for f in files if "/" not in f.path)
    dir_map["."].file_count = root_count

    directories = sorted(dir_map.values(), key=lambda d: d.path)
    return files, directories


def build_repo_graph(
    source_dir: Path,
    root_name: str,
    files: list[ScannedFile],
    directories: list[ScannedDirectory],
) -> dict:
    """Build the repo_graph section of the container."""
    return {
        "root": root_name,
        "files": [
            {
                "path": f.path,
                "language": f.language,
                "size_bytes": f.size_bytes,
                "sha256": f.sha256,
                "line_count": f.line_count,
                "imports": f.imports,
                "is_test": f.is_test,
            }
            for f in files
        ],
        "directories": [
            {
                "path": d.path,
                "file_count": d.file_count,
            }
            for d in directories
        ],
    }
