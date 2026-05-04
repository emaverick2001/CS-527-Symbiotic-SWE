from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional


DEFAULT_PROVIDER = 'openai'
DEFAULT_MODEL = 'gpt-5.4-mini'


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_tasks_from_jsonl(path: Path) -> List:
    from symbiotic_swe.contracts import CanonicalTask
    tasks = []
    with path.open(encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line:
                tasks.append(CanonicalTask(**json.loads(line)))
    return tasks


def _load_prepared_tasks(prepared_dir: Path) -> List:
    from symbiotic_swe.contracts import CanonicalTask
    tasks = []
    for task_json in sorted(prepared_dir.rglob('task.json')):
        try:
            task = CanonicalTask(**json.loads(task_json.read_text(encoding='utf-8')))
            tasks.append(_repair_prepared_task_paths(task))
        except Exception:
            pass
    return tasks


def _default_prepared_dir(subset: str | None = None) -> Path:
    base = _project_root() / 'data' / 'prepared' / 'prepared'
    return base / subset if subset else base


def _repair_prepared_task_paths(task):
    """Make checked-in prepared tasks portable across local checkout paths."""
    if task.repo_path and Path(task.repo_path).exists():
        return task

    local_repo = _project_root() / 'data' / 'prepared' / 'workspaces' / task.task_id / 'repo'
    if local_repo.exists():
        return task.model_copy(update={'repo_path': str(local_repo)})
    return task


def _select_tasks(tasks: List, task_ids: Optional[List[str]]) -> List:
    if not task_ids:
        return tasks
    wanted = set(task_ids)
    return [task for task in tasks if task.task_id in wanted]


def _api_key_from_env(provider: str) -> str | None:
    if provider == 'openai':
        return os.environ.get('OPENAI_API_KEY')
    return os.environ.get('ANTHROPIC_API_KEY')


def _preflight_smoke(
    *,
    prepared_dir: Path,
    output_dir: Path | None,
    task_ids: Optional[List[str]],
    api_key: Optional[str],
    provider: str,
) -> int:
    tasks = _select_tasks(_load_prepared_tasks(prepared_dir), task_ids)
    failures: list[str] = []

    if not prepared_dir.exists():
        failures.append(f'prepared directory does not exist: {prepared_dir}')
    if not tasks:
        failures.append(f'no prepared tasks found in {prepared_dir}')

    missing_repos = []
    for task in tasks:
        if not task.repo_path:
            missing_repos.append(f'{task.task_id}: missing repo_path')
            continue
        repo_path = Path(task.repo_path)
        if not repo_path.exists():
            missing_repos.append(f'{task.task_id}: repo_path does not exist: {repo_path}')
    failures.extend(missing_repos)

    if not api_key:
        env_name = 'OPENAI_API_KEY' if provider == 'openai' else 'ANTHROPIC_API_KEY'
        failures.append(f'{env_name} is not set and --api-key was not provided')

    print('Smoke preflight')
    print(f'  prepared_dir: {prepared_dir}')
    print(f'  output_dir:   {output_dir or "(auto artifacts/runs/<run_id>)"}')
    print(f'  tasks:        {len(tasks)}')
    print(f'  provider:     {provider}')
    print(f'  api_key:      {"set" if api_key else "missing"}')

    if failures:
        print('  status:       failed')
        for failure in failures:
            print(f'  - {failure}')
        return 1

    print('  status:       ready')
    return 0


# ── sub-commands ────────────────────────────────────────────────────────────

def cmd_run_task(args: argparse.Namespace) -> int:
    from symbiotic_swe.contracts import CanonicalTask
    from symbiotic_swe.orchestration.runner import run_task

    if args.task_json:
        task_path = Path(args.task_json).resolve()
        task = CanonicalTask(**json.loads(task_path.read_text(encoding='utf-8')))
    else:
        if not args.task_id:
            print('Either --task-json or --task-id is required.', file=sys.stderr)
            return 1
        prepared_dir = Path(args.prepared_dir).resolve() if args.prepared_dir else _default_prepared_dir()
        matches = _select_tasks(_load_prepared_tasks(prepared_dir), [args.task_id])
        if not matches:
            print(f'No prepared task found for {args.task_id} in {prepared_dir}', file=sys.stderr)
            return 1
        task = matches[0]

    metrics = run_task(
        task=task,
        condition=args.condition,
        max_iterations=args.max_iterations,
        api_key=args.api_key or _api_key_from_env(args.provider),
        model=args.model,
        provider=args.provider,
        work_root=Path(args.work_root) if args.work_root else None,
    )

    output = Path(args.output) if args.output else Path(f'{task.task_id}_{args.condition}.json')
    output.write_text(metrics.model_dump_json(indent=2), encoding='utf-8')
    status = 'SUCCESS' if metrics.success else 'FAIL'
    print(f'{status} | {task.task_id} | {args.condition} | '
          f'{metrics.total_iterations} iters | {metrics.total_duration_ms}ms')
    return 0


def cmd_run_benchmark(args: argparse.Namespace) -> int:
    from symbiotic_swe.orchestration.runner import run_benchmark

    default_subset = 'smoke' if args.command == 'smoke' else None
    prepared_dir = Path(args.prepared_dir).resolve() if args.prepared_dir else _default_prepared_dir(default_subset)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    conditions = args.conditions.split(',')
    api_key = args.api_key or _api_key_from_env(args.provider)

    if getattr(args, 'preflight_only', False):
        return _preflight_smoke(
            prepared_dir=prepared_dir,
            output_dir=output_dir,
            task_ids=args.task_ids,
            api_key=api_key,
            provider=args.provider,
        )

    tasks = _select_tasks(_load_prepared_tasks(prepared_dir), args.task_ids)
    if not tasks:
        print(f'No prepared tasks found in {prepared_dir}', file=sys.stderr)
        return 1

    print(f'Running {len(tasks)} tasks × {len(conditions)} conditions')
    run_benchmark(
        tasks=tasks,
        conditions=conditions,
        max_iterations=args.max_iterations,
        api_key=api_key,
        model=args.model,
        provider=args.provider,
        output_dir=output_dir,
        work_root=Path(args.work_root) if args.work_root else None,
        experiment_name=args.experiment_name,
    )
    return 0


def cmd_prepare_dataset(args: argparse.Namespace) -> int:
    from symbiotic_swe.dataset.preparation import prepare_swe_bench_tasks

    result = prepare_swe_bench_tasks(
        input_path=Path(args.input_jsonl).resolve(),
        output_dir=Path(args.output_dir).resolve(),
        smoke_count=args.smoke_count,
        dev_count=args.dev_count,
        final_eval_count=args.final_eval_count,
        repo_filter_mode=args.repo_filter_mode,
        workspace_root=Path(args.workspace_root) if args.workspace_root else None,
        cache_root=Path(args.cache_root) if args.cache_root else None,
    )
    print(f'Tasks loaded:    {len(result.raw_tasks)}')
    print(f'Malformed:       {len(result.malformed_tasks)}')
    print(f'Repo failures:   {len(result.repo_failures)}')
    print(f'Smoke tasks:     {len(result.smoke_tasks)}')
    print(f'Dev tasks:       {len(result.dev_tasks)}')
    print(f'Final eval:      {len(result.final_eval_tasks)}')
    print(f'Output dir:      {result.output_dir}')
    return 0


# ── parsers ─────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Symbiotic-SWE pipeline CLI')
    sub = parser.add_subparsers(dest='command')

    # task — run pipeline on a single task
    p_task = sub.add_parser('task', help='Run the pipeline on a single task')
    p_task.add_argument('--task-id', dest='task_id')
    p_task.add_argument('--task-json')
    p_task.add_argument('--prepared-dir')
    p_task.add_argument('--condition', default='neural_cegf',
                        choices=['neural_only', 'neural_slicing', 'neural_solver', 'neural_cegf'])
    p_task.add_argument('--max-iterations', type=int, default=3)
    p_task.add_argument('--api-key')
    p_task.add_argument('--provider', default=DEFAULT_PROVIDER, choices=['anthropic', 'openai'])
    p_task.add_argument('--model', default=DEFAULT_MODEL)
    p_task.add_argument('--work-root')
    p_task.add_argument('--output')

    # smoke — quick smoke test
    p_smoke = sub.add_parser('smoke', help='Run smoke tasks')
    p_smoke.add_argument('--task-id', dest='task_ids', action='append', default=None)
    p_smoke.add_argument('--prepared-dir')
    p_smoke.add_argument('--output-dir')
    p_smoke.add_argument('--max-iterations', type=int, default=3)
    p_smoke.add_argument('--api-key')
    p_smoke.add_argument('--provider', default=DEFAULT_PROVIDER, choices=['anthropic', 'openai'])
    p_smoke.add_argument('--model', default=DEFAULT_MODEL)
    p_smoke.add_argument('--conditions', default='neural_only,neural_slicing,neural_solver,neural_cegf')
    p_smoke.add_argument('--work-root')
    p_smoke.add_argument('--preflight-only', action='store_true')

    # benchmark — full benchmark run
    p_bench = sub.add_parser('benchmark', help='Run all conditions on a prepared dataset')
    p_bench.add_argument('--task-id', dest='task_ids', action='append', default=None)
    p_bench.add_argument('--prepared-dir')
    p_bench.add_argument('--output-dir')
    p_bench.add_argument('--conditions', default='neural_only,neural_cegf')
    p_bench.add_argument('--max-iterations', type=int, default=3)
    p_bench.add_argument('--api-key')
    p_bench.add_argument('--provider', default=DEFAULT_PROVIDER, choices=['anthropic', 'openai'])
    p_bench.add_argument('--model', default=DEFAULT_MODEL)
    p_bench.add_argument('--work-root')
    p_bench.add_argument('--experiment-name', default='symbiotic_swe')

    # ablation — all four conditions for ablation study
    p_abl = sub.add_parser('ablation', help='Run ablation study across all conditions')
    p_abl.add_argument('--task-id', dest='task_ids', action='append', default=None)
    p_abl.add_argument('--ablation-name')
    p_abl.add_argument('--prepared-dir')
    p_abl.add_argument('--output-dir')
    p_abl.add_argument('--max-iterations', type=int, default=3)
    p_abl.add_argument('--api-key')
    p_abl.add_argument('--provider', default=DEFAULT_PROVIDER, choices=['anthropic', 'openai'])
    p_abl.add_argument('--model', default=DEFAULT_MODEL)

    # prepare-dataset
    p_prep = sub.add_parser('prepare-dataset', help='Prepare SWE-bench tasks for the pipeline')
    p_prep.add_argument('--input-jsonl', required=True)
    p_prep.add_argument('--output-dir', required=True)
    p_prep.add_argument('--smoke-count', type=int, default=5)
    p_prep.add_argument('--dev-count', type=int, default=20)
    p_prep.add_argument('--final-eval-count', type=int, default=40)
    p_prep.add_argument('--repo-filter-mode', default='preferred',
                        choices=['preferred', 'strict', 'none'])
    p_prep.add_argument('--workspace-root')
    p_prep.add_argument('--cache-root')

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == 'task':
        return cmd_run_task(args)
    if args.command in ('smoke', 'benchmark', 'ablation'):
        if not hasattr(args, 'conditions') or args.conditions is None:
            args.conditions = 'neural_only,neural_slicing,neural_solver,neural_cegf'
        if not hasattr(args, 'work_root'):
            args.work_root = None
        if not hasattr(args, 'experiment_name') or args.experiment_name is None:
            args.experiment_name = getattr(args, 'ablation_name', None) or 'symbiotic_swe'
        return cmd_run_benchmark(args)
    if args.command == 'prepare-dataset':
        return cmd_prepare_dataset(args)
    parser.print_help()
    return 1


def main_task(argv: Optional[List[str]] = None) -> int:
    return main(['task'] + (argv or sys.argv[1:]))


def main_smoke(argv: Optional[List[str]] = None) -> int:
    return main(['smoke'] + (argv or sys.argv[1:]))


def main_benchmark(argv: Optional[List[str]] = None) -> int:
    return main(['benchmark'] + (argv or sys.argv[1:]))


def main_ablation(argv: Optional[List[str]] = None) -> int:
    return main(['ablation'] + (argv or sys.argv[1:]))


if __name__ == '__main__':
    raise SystemExit(main())
