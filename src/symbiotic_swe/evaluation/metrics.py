from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from symbiotic_swe.contracts import RunMetrics


def _safe_mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_metrics(results_by_condition: Dict[str, List[RunMetrics]]) -> Dict:
    summary: Dict = {}

    for condition, runs in results_by_condition.items():
        if not runs:
            continue

        n = len(runs)
        successes = [r for r in runs if r.success]
        resolution_rate = len(successes) / n

        iterations = [r.total_iterations for r in runs]
        tokens = [r.total_prompt_tokens + r.total_completion_tokens for r in runs]
        durations = [r.total_duration_ms for r in runs]
        solver_durations = [r.solver_duration_ms for r in runs]
        apply_failures = [r.patch_apply_failures for r in runs]
        repeated_ces = [r.repeated_counterexamples for r in runs]

        successful_tokens = [
            r.total_prompt_tokens + r.total_completion_tokens
            for r in runs if r.success
        ]
        tps = sum(successful_tokens) / len(successes) if successes else 0.0

        solver_outcomes: Dict[str, int] = {}
        for r in runs:
            for status, count in r.solver_outcomes.items():
                solver_outcomes[status] = solver_outcomes.get(status, 0) + count

        total_solver_time = sum(solver_durations)
        total_time = sum(durations)
        solver_overhead = total_solver_time / total_time if total_time > 0 else 0.0

        termination_reasons: Dict[str, int] = {}
        for r in runs:
            reason = r.termination_reason
            termination_reasons[reason] = termination_reasons.get(reason, 0) + 1

        summary[condition] = {
            'n_tasks': n,
            'bug_resolution_rate': round(resolution_rate, 4),
            'avg_iterations': round(_safe_mean(iterations), 2),
            'avg_tokens': round(_safe_mean(tokens), 1),
            'tokens_per_success': round(tps, 6),
            'avg_duration_ms': round(_safe_mean(durations), 1),
            'solver_overhead_fraction': round(solver_overhead, 4),
            'avg_patch_apply_failures': round(_safe_mean(apply_failures), 2),
            'repeated_counterexample_rate': round(_safe_mean(repeated_ces), 2),
            'solver_outcomes': solver_outcomes,
            'termination_reasons': termination_reasons,
        }

    return summary


def write_experiment_summary(
    results_by_condition: Dict[str, List[RunMetrics]],
    output_dir: Path,
    experiment_name: str = 'experiment',
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    agg = aggregate_metrics(results_by_condition)

    summary_path = output_dir / f'{experiment_name}_summary.json'
    summary_path.write_text(json.dumps(agg, indent=2), encoding='utf-8')

    # Write per-condition JSONL
    for condition, runs in results_by_condition.items():
        cond_dir = output_dir / condition
        cond_dir.mkdir(exist_ok=True)
        rows_path = cond_dir / 'all_runs.jsonl'
        with rows_path.open('w', encoding='utf-8') as fh:
            for r in runs:
                fh.write(r.model_dump_json() + '\n')

    print(f'Experiment summary written to {summary_path}')
    for condition, stats in agg.items():
        print(f'  [{condition}] resolution={stats["bug_resolution_rate"]:.1%}  '
              f'avg_iters={stats["avg_iterations"]}  '
              f'avg_tokens={stats["avg_tokens"]:.0f}')

    return summary_path
