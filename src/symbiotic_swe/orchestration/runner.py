from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from symbiotic_swe.contracts import CanonicalTask, RunMetrics
from symbiotic_swe.dataset.repo_indexer import build_repository_index
from symbiotic_swe.orchestration.loop import run_cegf_loop


SUPPORTED_CONDITIONS = ('neural_only', 'neural_slicing', 'neural_solver', 'neural_cegf')


def run_task(
    task: CanonicalTask,
    condition: str = 'neural_cegf',
    max_iterations: int = 3,
    api_key: Optional[str] = None,
    model: str = 'claude-sonnet-4-6',
    work_root: Optional[Path] = None,
    cache_root: Optional[Path] = None,
) -> RunMetrics:
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

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
        work_root=work_root,
    )


def run_benchmark(
    tasks: List[CanonicalTask],
    conditions: List[str] = ('neural_only', 'neural_cegf'),
    max_iterations: int = 3,
    api_key: Optional[str] = None,
    model: str = 'claude-sonnet-4-6',
    output_dir: Optional[Path] = None,
    work_root: Optional[Path] = None,
    cache_root: Optional[Path] = None,
) -> Dict[str, List[RunMetrics]]:
    results: Dict[str, List[RunMetrics]] = {cond: [] for cond in conditions}

    output_dir = output_dir or Path('experiments/results')
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

    return results
