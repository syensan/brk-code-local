"""SQLite export for BRK-Code."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .container import BRKCodeContainer


def export_sqlite(container: BRKCodeContainer, output_path: Path) -> None:
    """Export container data to a SQLite database for querying."""
    data = container.data
    header = data.get("header", {})
    repo_graph = data.get("repo_graph", {})
    ast_graph = data.get("ast_semantic_graph", {})
    symbol_table = data.get("symbol_table", {})
    dep_graph = data.get("dependency_graph", {})
    security = data.get("security_report", {})
    learning = data.get("learning_tasks", [])
    contract = data.get("contract", {})

    conn = sqlite3.connect(str(output_path))
    cur = conn.cursor()

    # metadata table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    meta_entries = [
        ("format_version", header.get("format_version", "")),
        ("profile", header.get("profile", "")),
        ("source_root_name", header.get("source_root_name", "")),
        ("file_count", str(header.get("file_count", 0))),
        ("python_file_count", str(header.get("python_file_count", 0))),
        ("lossless", str(header.get("flags", {}).get("lossless", False))),
        ("semantic_equivalent", str(header.get("flags", {}).get("semantic_equivalent", True))),
        ("ai_learning_optimized", str(header.get("flags", {}).get("ai_learning_optimized", True))),
        ("secrets_redacted", str(security.get("secrets_redacted", 0))),
        ("security_findings_count", str(len(security.get("findings", [])))),
        ("learning_task_count", str(len(learning))),
    ]
    cur.executemany("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", meta_entries)

    # files table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            language TEXT,
            size_bytes INTEGER,
            sha256 TEXT,
            line_count INTEGER,
            is_test INTEGER
        )
    """)
    for f in repo_graph.get("files", []):
        cur.execute(
            "INSERT OR REPLACE INTO files VALUES (?, ?, ?, ?, ?, ?)",
            (f["path"], f["language"], f["size_bytes"], f["sha256"],
             f["line_count"], int(f.get("is_test", False))),
        )

    # symbols table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS symbols (
            name TEXT,
            qualified_name TEXT PRIMARY KEY,
            kind TEXT,
            file TEXT,
            line INTEGER,
            signature TEXT
        )
    """)
    for s in symbol_table.get("symbols", []):
        cur.execute(
            "INSERT OR REPLACE INTO symbols VALUES (?, ?, ?, ?, ?, ?)",
            (s["name"], s["qualified_name"], s["kind"], s["file"],
             s["line"], s["signature"]),
        )

    # functions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS functions (
            name TEXT,
            qualified_name TEXT PRIMARY KEY,
            file TEXT,
            line INTEGER,
            end_line INTEGER,
            args TEXT,
            returns TEXT,
            docstring TEXT,
            is_async INTEGER,
            complexity_estimate INTEGER
        )
    """)
    for f in ast_graph.get("functions", []):
        cur.execute(
            "INSERT OR REPLACE INTO functions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f["name"], f["qualified_name"], f["file"], f["line"],
             f["end_line"], json_str(f["args"]), f.get("returns"),
             f.get("docstring"), int(f.get("is_async", False)),
             f.get("complexity_estimate", 0)),
        )

    # classes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            name TEXT PRIMARY KEY,
            file TEXT,
            line INTEGER,
            docstring TEXT,
            methods TEXT,
            bases TEXT
        )
    """)
    for c in ast_graph.get("classes", []):
        cur.execute(
            "INSERT OR REPLACE INTO classes VALUES (?, ?, ?, ?, ?, ?)",
            (c["name"], c["file"], c["line"], c.get("docstring"),
             json_str(c.get("methods", [])), json_str(c.get("bases", []))),
        )

    # imports table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_file TEXT,
            module TEXT,
            kind TEXT
        )
    """)
    for imp in dep_graph.get("imports", []):
        cur.execute(
            "INSERT INTO imports (from_file, module, kind) VALUES (?, ?, ?)",
            (imp["from_file"], imp["module"], imp["kind"]),
        )

    # security_findings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS security_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file TEXT,
            line INTEGER,
            severity TEXT,
            type TEXT,
            message TEXT
        )
    """)
    for finding in security.get("findings", []):
        cur.execute(
            "INSERT INTO security_findings (file, line, severity, type, message) VALUES (?, ?, ?, ?, ?)",
            (finding["file"], finding["line"], finding["severity"],
             finding["type"], finding["message"]),
        )

    # learning_tasks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT,
            prompt TEXT,
            input_json TEXT,
            expected_output_hint TEXT
        )
    """)
    for task in learning:
        import json
        cur.execute(
            "INSERT INTO learning_tasks (task_type, prompt, input_json, expected_output_hint) VALUES (?, ?, ?, ?)",
            (task["task_type"], task["prompt"],
             json.dumps(task.get("input", {}), ensure_ascii=False),
             task.get("expected_output_hint", "")),
        )

    conn.commit()
    conn.close()


def json_str(obj: Any) -> str:
    """Convert a list to a JSON string for SQLite storage."""
    import json
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, ensure_ascii=False)
