from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from symbiotic_swe.models import ExecutionMode, RunRequest
from symbiotic_swe.orchestration import execute_run
from symbiotic_swe.workspace import project_root


def build_parser() -> argparse.ArgumentParser:
    root = project_root()
    parser = argparse.ArgumentParser(
        prog='symbiotic-swe',
        description='Scaffold and execute the Symbiotic SWE repair pipeline.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    task_parser = subparsers.add_parser('task', help='Run one repair task.')
    task_parser.add_argument('--task-id', required=True, help='Unique task identifier.')
    task_parser.add_argument(
        '--config',
        type=Path,
        default=root / 'configs' / 'task.toml',
        help='Path to the single-task config file.',
    )
    task_parser.add_argument('--run-id', help='Optional explicit run identifier.')
    task_parser.add_argument(
        '--max-iterations',
        type=int,
        default=1,
        help='Number of iteration folders to scaffold for the task.',
    )

    benchmark_parser = subparsers.add_parser('benchmark', help='Run a benchmark sweep.')
    benchmark_parser.add_argument(
        '--task-id',
        action='append',
        required=True,
        dest='task_ids',
        help='Task identifier to include in the benchmark run. Repeat to add more.',
    )
    benchmark_parser.add_argument(
        '--config',
        type=Path,
        default=root / 'configs' / 'benchmark.toml',
        help='Path to the benchmark config file.',
    )
    benchmark_parser.add_argument('--run-id', help='Optional explicit run identifier.')
    benchmark_parser.add_argument(
        '--max-iterations',
        type=int,
        default=1,
        help='Number of iteration folders to scaffold per task.',
    )

    ablation_parser = subparsers.add_parser('ablation', help='Run an ablation sweep.')
    ablation_parser.add_argument(
        '--ablation-name',
        required=True,
        help='Name of the component or setting being ablated.',
    )
    ablation_parser.add_argument(
        '--task-id',
        action='append',
        required=True,
        dest='task_ids',
        help='Task identifier to include in the ablation run. Repeat to add more.',
    )
    ablation_parser.add_argument(
        '--config',
        type=Path,
        default=root / 'configs' / 'ablation.toml',
        help='Path to the ablation config file.',
    )
    ablation_parser.add_argument('--run-id', help='Optional explicit run identifier.')
    ablation_parser.add_argument(
        '--max-iterations',
        type=int,
        default=1,
        help='Number of iteration folders to scaffold per task.',
    )

    return parser


def _request_from_args(args: argparse.Namespace) -> RunRequest:
    if args.command == 'task':
        return RunRequest(
            mode=ExecutionMode.TASK,
            task_ids=(args.task_id,),
            config_path=args.config,
            max_iterations=args.max_iterations,
            run_id=args.run_id,
        )
    if args.command == 'benchmark':
        return RunRequest(
            mode=ExecutionMode.BENCHMARK,
            task_ids=tuple(args.task_ids),
            config_path=args.config,
            max_iterations=args.max_iterations,
            run_id=args.run_id,
        )
    return RunRequest(
        mode=ExecutionMode.ABLATION,
        task_ids=tuple(args.task_ids),
        config_path=args.config,
        max_iterations=args.max_iterations,
        run_id=args.run_id,
        ablation_name=args.ablation_name,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    request = _request_from_args(args)
    layout = execute_run(request)
    print(f'Initialized {request.mode.value} run: {layout.run_id}')
    print(f'Artifacts: {layout.root}')
    print(f'Workspaces: {layout.workspace_root}')
    return 0


def _mode_wrapper(command: str, argv: Sequence[str] | None = None) -> int:
    forwarded_args = [command, *(argv if argv is not None else sys.argv[1:])]
    return main(forwarded_args)


def main_task() -> int:
    return _mode_wrapper('task')


def main_benchmark() -> int:
    return _mode_wrapper('benchmark')


def main_ablation() -> int:
    return _mode_wrapper('ablation')
