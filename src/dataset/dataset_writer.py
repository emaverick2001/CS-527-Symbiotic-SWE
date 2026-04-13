from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + '\n')


def write_task_subset_files(
    output_dir: Path,
    *,
    smoke_rows: list[dict[str, Any]],
    core_rows: list[dict[str, Any]],
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke_path = output_dir / 'smoke_tasks.jsonl'
    core_path = output_dir / 'core_tasks.jsonl'
    write_jsonl(smoke_path, smoke_rows)
    write_jsonl(core_path, core_rows)
    return smoke_path, core_path
