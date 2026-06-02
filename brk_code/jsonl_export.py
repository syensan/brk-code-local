"""JSONL export for BRK-Code learning tasks."""

from __future__ import annotations

import json
from pathlib import Path

from .container import BRKCodeContainer


def export_jsonl(container: BRKCodeContainer, output_path: Path) -> None:
    """Export learning tasks from container as JSONL file."""
    tasks = container.data.get("learning_tasks", [])

    with open(output_path, "w", encoding="utf-8") as f:
        for task in tasks:
            line = json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            f.write(line + "\n")
