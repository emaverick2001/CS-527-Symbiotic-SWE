from __future__ import annotations

import argparse
from pathlib import Path

from symbiotic_swe.dataset import (
    TaskLoader,
    TaskLoaderConfig,
    TaskNormalizer,
    _candidate_to_json,
    _task_to_dict,
    _write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='symbiotic-swe-dataset')
    subparsers = parser.add_subparsers(dest='command', required=True)

    normalize_one = subparsers.add_parser('normalize-one')
    normalize_one.add_argument('--input-jsonl', type=Path, required=True)
    normalize_one.add_argument('--task-id', required=True)
    normalize_one.add_argument('--output-dir', type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == 'normalize-one':
        loader = TaskLoader(TaskLoaderConfig(repo_filter_mode='none'))
        raw_tasks, malformed = loader.load_raw_tasks(args.input_jsonl)
        del malformed
        for raw_task in raw_tasks:
            if raw_task.instance_id != args.task_id:
                continue
            candidate = loader.score_task(raw_task)
            normalized = TaskNormalizer().normalize_task(candidate, 'preview')
            args.output_dir.mkdir(parents=True, exist_ok=True)
            _write_json(args.output_dir / f'{args.task_id}.candidate.json', _candidate_to_json(candidate))
            _write_json(args.output_dir / f'{args.task_id}.normalized.json', _task_to_dict(normalized))
            return 0
        return 1
    return 1
