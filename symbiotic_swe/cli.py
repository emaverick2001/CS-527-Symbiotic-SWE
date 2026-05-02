from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='symbiotic-swe')
    subparsers = parser.add_subparsers(dest='command', required=True)

    task = subparsers.add_parser('task')
    task.add_argument('--task-id', required=True)
    task.add_argument('--config', type=Path, default=Path('configs/baseline.yaml'))
    task.add_argument('--max-iterations', type=int, default=1)

    smoke = subparsers.add_parser('smoke')
    smoke.add_argument('--task-id', dest='task_ids', action='append')
    smoke.add_argument('--config', type=Path, default=Path('configs/smoke.yaml'))

    benchmark = subparsers.add_parser('benchmark')
    benchmark.add_argument('--task-id', dest='task_ids', action='append', required=True)
    benchmark.add_argument('--config', type=Path, default=Path('configs/evaluation.yaml'))

    ablation = subparsers.add_parser('ablation')
    ablation.add_argument('--ablation-name', required=True)
    ablation.add_argument('--task-id', dest='task_ids', action='append', required=True)
    ablation.add_argument('--config', type=Path, default=Path('configs/evaluation.yaml'))
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
