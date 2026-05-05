from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from symbiotic_swe.contracts import CanonicalTask, RunMetrics
from symbiotic_swe.dataset.repo_indexer import build_repository_index
from symbiotic_swe.evaluation.metrics import aggregate_metrics
from symbiotic_swe.orchestration.loop import run_cegf_loop


SUPPORTED_CONDITIONS = ('neural_only', 'neural_slicing', 'neural_solver', 'neural_cegf')


def _slug(value: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug or 'none'


def _default_run_dir(model: str, experiment_name: str, conditions: List[str]) -> Path:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    solver = 'z3' if any(condition in {'neural_solver', 'neural_cegf'} for condition in conditions) else 'none'
    condition_slug = 'mixed' if len(conditions) > 1 else conditions[0].replace('_', '-')
    experiment = _slug(experiment_name or condition_slug)
    run_id = f'{timestamp}_{_slug(model)}_{experiment}_{solver}_s0'
    return Path('artifacts') / 'runs' / run_id


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _write_jsonl(path: Path, rows: List[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + '\n')


def _write_run_artifacts(
    run_dir: Path,
    *,
    tasks: List[CanonicalTask],
    conditions: List[str],
    results: Dict[str, List[RunMetrics]],
    model: str,
    provider: str,
    max_iterations: int,
    experiment_name: str,
    started_at: str,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    ended_at = datetime.now().isoformat()

    (run_dir / 'config.yaml').write_text(
        '\n'.join(
            [
                f'experiment_name: {experiment_name}',
                f'provider: {provider}',
                f'model: {model}',
                f'max_iterations: {max_iterations}',
                'conditions:',
                *[f'  - {condition}' for condition in conditions],
                '',
            ]
        ),
        encoding='utf-8',
    )
    _write_json(
        run_dir / 'run_manifest.json',
        {
            'experiment_name': experiment_name,
            'provider': provider,
            'model': model,
            'task_ids': [task.task_id for task in tasks],
            'n_tasks': len(tasks),
            'conditions': conditions,
            'max_iterations': max_iterations,
            'started_at': started_at,
            'ended_at': ended_at,
        },
    )
    _write_json(
        run_dir / 'task_manifest.json',
        {
            'tasks': [
                {
                    'task_id': task.task_id,
                    'repo': task.repo,
                    'repo_commit': task.repo_commit,
                    'subset': task.metadata.subset,
                    'failing_tests': task.failing_tests,
                }
                for task in tasks
            ]
        },
    )
    _write_json(run_dir / 'metrics.json', aggregate_metrics(results))

    timing_lines = ['condition,task_id,run_id,iteration,duration_ms,solver_time_ms,test_duration_ms']
    solver_rows: List[dict[str, Any]] = []
    patch_rows: List[dict[str, Any]] = []
    evaluation_rows: List[dict[str, Any]] = []
    error_lines: List[str] = []

    for condition, runs in results.items():
        for metrics in runs:
            final_patch_id = None
            for record in metrics.iterations:
                solver_time = record.solver_result.solver_time_ms if record.solver_result else 0
                test_time = record.test_evaluation.duration_ms if record.test_evaluation else 0
                timing_lines.append(
                    f'{condition},{metrics.task_id},{metrics.run_id},{record.iteration},'
                    f'{record.duration_ms},{solver_time},{test_time}'
                )

                if record.patch:
                    final_patch_id = record.patch.patch_id
                    patch_rows.append(
                        {
                            'condition': condition,
                            'task_id': metrics.task_id,
                            'run_id': metrics.run_id,
                            'model_provider': metrics.model_provider,
                            'model': metrics.model,
                            'iteration': record.iteration,
                            'patch_id': record.patch.patch_id,
                            'target_files': record.patch.target_files,
                            'parse_ok': record.patch.parse_ok,
                            'apply_ok': record.patch.apply_ok,
                            'errors': record.patch.errors,
                        }
                    )
                    for error in record.patch.errors:
                        error_lines.append(f'{condition} {metrics.task_id} iter {record.iteration}: {error}')

                if record.solver_result:
                    solver_rows.append(
                        {
                            'condition': condition,
                            'task_id': metrics.task_id,
                            **record.solver_result.model_dump(),
                        }
                    )

                if record.test_evaluation:
                    evaluation_rows.append(
                        {
                            'condition': condition,
                            'task_id': metrics.task_id,
                            'run_id': metrics.run_id,
                            **record.test_evaluation.model_dump(),
                        }
                    )

            patch_rows.append(
                {
                    'condition': condition,
                    'task_id': metrics.task_id,
                    'run_id': metrics.run_id,
                    'model_provider': metrics.model_provider,
                    'model': metrics.model,
                    'final_patch_id': final_patch_id,
                    'success': metrics.success,
                    'termination_reason': metrics.termination_reason,
                }
            )

    (run_dir / 'stage_timings.csv').write_text('\n'.join(timing_lines) + '\n', encoding='utf-8')
    _write_jsonl(run_dir / 'solver_queries.jsonl', [])
    _write_jsonl(run_dir / 'solver_results.jsonl', solver_rows)
    _write_json(run_dir / 'patch_manifest.json', {'patches': patch_rows})
    _write_jsonl(run_dir / 'evaluation_results.jsonl', evaluation_rows)
    (run_dir / 'errors.log').write_text('\n'.join(error_lines) + ('\n' if error_lines else ''), encoding='utf-8')
    (run_dir / 'summary.md').write_text(
        f'# {experiment_name}\n\n'
        f'- Tasks: {len(tasks)}\n'
        f'- Conditions: {", ".join(conditions)}\n'
        f'- Started: {started_at}\n'
        f'- Ended: {ended_at}\n',
        encoding='utf-8',
    )


def run_task(
    task: CanonicalTask,
    condition: str = 'neural_cegf',
    max_iterations: int = 3,
    api_key: Optional[str] = None,
    model: str = 'gpt-5.4-mini',
    provider: str = 'openai',
    work_root: Optional[Path] = None,
    cache_root: Optional[Path] = None,
) -> RunMetrics:
    if provider == 'openai':
        api_key = api_key or os.environ.get('OPENAI_API_KEY')
    elif provider == 'anthropic':
        api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    else:
        raise ValueError(f'unsupported model provider: {provider}')

    repo_path = Path(task.repo_path) if task.repo_path else None
    cache_root = cache_root or Path('/tmp/symbiotic_swe_cache')

    if repo_path and repo_path.exists():
        repo_index = build_repository_index(
            repo_path=repo_path,
            repo=task.repo,
            cache_root=cache_root,
        )
    else:
        from symbiotic_swe.contracts import RepoIndex
        repo_index = RepoIndex(repo=task.repo, index_path='', files=[])

    return run_cegf_loop(
        task=task,
        repo_index=repo_index,
        condition=condition,
        max_iterations=max_iterations,
        api_key=api_key,
        model=model,
        provider=provider,
        work_root=work_root,
    )


def run_benchmark(
    tasks: List[CanonicalTask],
    conditions: List[str] = ('neural_only', 'neural_cegf'),
    max_iterations: int = 3,
    api_key: Optional[str] = None,
    model: str = 'gpt-5.4-mini',
    provider: str = 'openai',
    output_dir: Optional[Path] = None,
    work_root: Optional[Path] = None,
    cache_root: Optional[Path] = None,
    experiment_name: str = 'symbiotic-swe',
) -> Dict[str, List[RunMetrics]]:
    results: Dict[str, List[RunMetrics]] = {cond: [] for cond in conditions}

    started_at = datetime.now().isoformat()
    output_dir = output_dir or _default_run_dir(model, experiment_name, conditions)
    output_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        for condition in conditions:
            print(f'[{condition}] Running {task.task_id}...')
            metrics = run_task(
                task=task,
                condition=condition,
                max_iterations=max_iterations,
                api_key=api_key,
                model=model,
                provider=provider,
                work_root=work_root,
                cache_root=cache_root,
            )
            results[condition].append(metrics)

            # Write per-task result
            task_dir = output_dir / condition / task.task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            (task_dir / 'metrics.json').write_text(
                metrics.model_dump_json(indent=2), encoding='utf-8'
            )
            status = 'success' if metrics.success else 'fail'
            print(f'  -> {status} in {metrics.total_iterations} iterations '
                  f'({metrics.total_duration_ms}ms)')

    _write_run_artifacts(
        output_dir,
        tasks=tasks,
        conditions=conditions,
        results=results,
        model=model,
        provider=provider,
        max_iterations=max_iterations,
        experiment_name=experiment_name,
        started_at=started_at,
    )
    return results
