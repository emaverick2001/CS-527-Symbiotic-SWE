from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from symbiotic_swe.dataset.task_loader import TaskLoader, TaskLoaderConfig
from symbiotic_swe.dataset.task_normalizer import TaskNormalizer


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


def cmd_normalize_one(args: argparse.Namespace) -> int:
    input_path = Path(args.input_jsonl).resolve()
    output_dir = Path(args.output_dir).resolve()
    task_id = args.task_id

    loader = TaskLoader(TaskLoaderConfig(repo_filter_mode='none'))
    normalizer = TaskNormalizer()

    raw_tasks, malformed = loader.load_raw_tasks(input_path)
    match = next((t for t in raw_tasks if t.instance_id == task_id), None)
    if match is None:
        print(f'Task {task_id} not found in {input_path}')
        return 1

    candidate = loader.score_task(match)
    normalized = normalizer.normalize_task(candidate, 'preview')

    candidate_path = output_dir / f'{task_id}.candidate.json'
    normalized_path = output_dir / f'{task_id}.normalized.json'

    _write_json(candidate_path, {
        'instance_id': candidate.raw.instance_id,
        'score': candidate.score,
        'changed_lines': candidate.changed_lines,
        'changed_files': list(candidate.changed_files),
        'labels': list(candidate.labels),
        'logic_heavy': candidate.logic_heavy,
        'include_for_smoke': candidate.include_for_smoke,
        'exclusion_reasons': list(candidate.exclusion_reasons),
    })
    _write_json(normalized_path, json.loads(normalized.model_dump_json()))

    print(f'Written: {candidate_path}')
    print(f'Written: {normalized_path}')
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='symbiotic-swe dataset commands')
    sub = parser.add_subparsers(dest='command')

    norm_one = sub.add_parser('normalize-one', help='Normalize a single task by ID')
    norm_one.add_argument('--input-jsonl', required=True)
    norm_one.add_argument('--task-id', required=True)
    norm_one.add_argument('--output-dir', required=True)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == 'normalize-one':
        return cmd_normalize_one(args)
    parser.print_help()
    return 1
