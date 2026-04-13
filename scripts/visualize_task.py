from __future__ import annotations

"""
Visualize one SWE-bench task from a JSON or JSONL file.

Usage:
    poetry run python scripts/visualize_task.py data/benchmarks/swe_bench/verified/filtered/jsonl/test.jsonl
    poetry run python scripts/visualize_task.py data/benchmarks/swe_bench/verified/filtered/smoke_tasks.jsonl --index 0
    poetry run python scripts/visualize_task.py data/benchmarks/swe_bench/verified/filtered/smoke_tasks.jsonl --task-id <TASK_ID>

What it prints:
- total task count in the file
- the selected raw task JSON
- a field-by-field type summary
- a compact normalized preview of nested values

Use this script when you want to inspect the structure of one task before
writing parsing code or updating schema/dataclass definitions.
"""

import argparse
import json
from pathlib import Path
from typing import Any


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f'Task file not found: {path}')

    if path.suffix.lower() == '.jsonl':
        tasks: list[dict[str, Any]] = []
        with path.open('r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f'Invalid JSON on line {line_no}: {exc}') from exc
                if not isinstance(obj, dict):
                    raise ValueError(
                        f'Expected object on line {line_no}, got {type(obj).__name__}'
                    )
                tasks.append(obj)
        return tasks

    if path.suffix.lower() == '.json':
        obj = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(obj, list):
            if not all(isinstance(item, dict) for item in obj):
                raise ValueError('JSON list must contain only objects')
            return obj
        if isinstance(obj, dict):
            return [obj]
        raise ValueError(f'Expected JSON object or list, got {type(obj).__name__}')

    raise ValueError(f'Unsupported file type: {path.suffix}')


def _summarize(value: Any, depth: int = 0, max_depth: int = 2) -> Any:
    if depth >= max_depth:
        return f'<{type(value).__name__}>'

    if isinstance(value, dict):
        return {
            key: _summarize(item, depth + 1, max_depth) for key, item in value.items()
        }

    if isinstance(value, list):
        preview = [_summarize(item, depth + 1, max_depth) for item in value[:3]]
        if len(value) > 3:
            preview.append(f'... ({len(value) - 3} more)')
        return preview

    if isinstance(value, str):
        return value if len(value) <= 220 else value[:220] + '...'

    return value


def _print_field_summary(task: dict[str, Any]) -> None:
    print('\nFIELD SUMMARY')
    print('-' * 60)
    for key, value in task.items():
        if isinstance(value, list):
            extra = f' len={len(value)}'
        elif isinstance(value, dict):
            extra = f' keys={list(value.keys())[:10]}'
        else:
            extra = ''
        print(f'{key}: {type(value).__name__}{extra}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Visualize one SWE-bench task')
    parser.add_argument(
        'path',
        type=Path,
        help='Path to a JSON or JSONL task file',
    )
    parser.add_argument(
        '--index',
        type=int,
        default=0,
        help='0-based index of the task to display',
    )
    parser.add_argument(
        '--task-id',
        type=str,
        default=None,
        help='Optional task_id to select instead of --index',
    )
    args = parser.parse_args()

    tasks = _load_tasks(args.path)
    if not tasks:
        raise ValueError(f'No tasks found in {args.path}')

    if args.task_id is not None:
        matches = [task for task in tasks if task.get('task_id') == args.task_id]
        if not matches:
            available = [task.get('task_id') for task in tasks[:10]]
            raise ValueError(
                f'Task id not found: {args.task_id}. '
                f'First available ids: {available}'
            )
        task = matches[0]
    else:
        if args.index < 0 or args.index >= len(tasks):
            raise IndexError(f'Index {args.index} out of range for {len(tasks)} tasks')
        task = tasks[args.index]

    print(f'TASK COUNT: {len(tasks)}')
    print(f'SELECTED INDEX: {args.index}')
    print('\nRAW TASK')
    print('-' * 60)
    print(json.dumps(task, indent=2, ensure_ascii=False)[:12000])

    _print_field_summary(task)

    print('\nNORMALIZED VIEW')
    print('-' * 60)
    print(json.dumps(_summarize(task), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
