from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from symbiotic_swe.contracts import RunMetrics


def _safe_mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _final_solver_status(run: RunMetrics) -> str | None:
    for record in reversed(run.iterations):
        if record.solver_result is not None:
            return record.solver_result.status
    return None


def _has_environment_limited_error(run: RunMetrics) -> bool:
    evaluation = run.final_test_evaluation
    if evaluation is None:
        return False
    values = [
        evaluation.error,
        evaluation.fail_to_pass.error,
        evaluation.pass_to_pass.error,
    ]
    return any(isinstance(value, str) and value.startswith('environment_limited:') for value in values)


def _fail_to_pass_passed(run: RunMetrics) -> bool:
    evaluation = run.final_test_evaluation
    return bool(evaluation and evaluation.fail_to_pass.passed)


def _pass_to_pass_failed(run: RunMetrics) -> bool:
    evaluation = run.final_test_evaluation
    return bool(evaluation and evaluation.pass_to_pass.tests and evaluation.pass_to_pass.passed is False)


def _critique_changed_next_patch(run: RunMetrics) -> tuple[int, int]:
    useful = 0
    total = 0
    records = run.iterations
    for index, record in enumerate(records[:-1]):
        if record.critique is None or record.patch is None:
            continue
        total += 1
        next_patch = records[index + 1].patch
        if next_patch is not None and next_patch.diff != record.patch.diff:
            useful += 1
    return useful, total


def aggregate_metrics(results_by_condition: Dict[str, List[RunMetrics]]) -> Dict:
    summary: Dict = {}

    for condition, runs in results_by_condition.items():
        if not runs:
            continue

        n = len(runs)
        successes = [r for r in runs if r.success]
        test_evaluated = [r for r in runs if r.test_evaluated]
        test_resolved = [r for r in runs if r.test_resolved]
        real_test_success_rate = _safe_rate(len(test_resolved), n)

        iterations = [r.total_iterations for r in runs]
        tokens = [r.total_prompt_tokens + r.total_completion_tokens for r in runs]
        durations = [r.total_duration_ms for r in runs]
        solver_durations = [r.solver_duration_ms for r in runs]
        apply_failures = [r.patch_apply_failures for r in runs]
        repeated_ces = [r.repeated_counterexamples for r in runs]

        successful_tokens = [
            r.total_prompt_tokens + r.total_completion_tokens
            for r in runs if r.test_resolved
        ]
        tps = sum(successful_tokens) / len(test_resolved) if test_resolved else 0.0

        solver_outcomes: Dict[str, int] = {}
        for r in runs:
            for status, count in r.solver_outcomes.items():
                solver_outcomes[status] = solver_outcomes.get(status, 0) + count
        solver_evaluated_patches = sum(solver_outcomes.values())
        solver_evaluated_tasks = sum(1 for r in runs if r.solver_outcomes)
        logical_correct = [
            r for r in runs
            if r.test_resolved and _final_solver_status(r) == 'unsat'
        ]
        f2p_passed = [r for r in runs if _fail_to_pass_passed(r)]
        regressions = [
            r for r in f2p_passed
            if _pass_to_pass_failed(r) or _final_solver_status(r) == 'sat'
        ]
        critique_useful = 0
        critique_total = 0
        for r in runs:
            useful, total = _critique_changed_next_patch(r)
            critique_useful += useful
            critique_total += total

        total_solver_time = sum(solver_durations)
        total_time = sum(durations)
        solver_overhead = total_solver_time / total_time if total_time > 0 else 0.0

        termination_reasons: Dict[str, int] = {}
        for r in runs:
            reason = r.termination_reason
            termination_reasons[reason] = termination_reasons.get(reason, 0) + 1

        summary[condition] = {
            'n_tasks': n,
            'patch_acceptance_success_rate': round(_safe_rate(len(successes), n), 4),
            'bug_resolution_rate': round(real_test_success_rate, 4),
            'real_test_success_rate': round(real_test_success_rate, 4),
            'test_evaluated_tasks': len(test_evaluated),
            'test_resolved_tasks': len(test_resolved),
            'test_resolution_rate': round(_safe_rate(len(test_resolved), len(test_evaluated)), 4),
            'logical_correct_tasks': len(logical_correct),
            'logical_correctness_rate': round(_safe_rate(len(logical_correct), n), 4),
            'solver_covered_tasks': solver_evaluated_tasks,
            'solver_coverage_rate': round(_safe_rate(solver_evaluated_tasks, n), 4),
            'solver_evaluated_patches': solver_evaluated_patches,
            'counterexample_detection_rate': round(
                _safe_rate(solver_outcomes.get('sat', 0), solver_evaluated_patches), 4
            ),
            'avg_iterations': round(_safe_mean(iterations), 2),
            'avg_tokens': round(_safe_mean(tokens), 1),
            'tokens_per_success': round(tps, 6),
            'avg_duration_ms': round(_safe_mean(durations), 1),
            'solver_overhead_fraction': round(solver_overhead, 4),
            'avg_patch_apply_failures': round(_safe_mean(apply_failures), 2),
            'repeated_counterexample_rate': round(_safe_mean(repeated_ces), 2),
            'regression_rate': round(_safe_rate(len(regressions), len(f2p_passed)), 4),
            'critique_utility_rate': round(_safe_rate(critique_useful, critique_total), 4),
            'critique_events': critique_total,
            'environment_limited_tasks': sum(1 for r in runs if _has_environment_limited_error(r)),
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
        print(f'  [{condition}] real_test_success={stats["real_test_success_rate"]:.1%}  '
              f'avg_iters={stats["avg_iterations"]}  '
              f'avg_tokens={stats["avg_tokens"]:.0f}')

    return summary_path
