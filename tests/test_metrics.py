from __future__ import annotations

from symbiotic_swe.contracts import (
    IterationRecord,
    RunMetrics,
    SolverResultContract,
    TestEvaluationResult as EvaluationResult,
    TestSuiteResult as SuiteResult,
)
from symbiotic_swe.evaluation.metrics import aggregate_metrics


def _test_evaluation(*, resolved: bool, f2p: bool = True, p2p: bool = True) -> EvaluationResult:
    return EvaluationResult(
        task_id='task',
        iteration=0,
        resolved=resolved,
        evaluated=True,
        fail_to_pass=SuiteResult(name='FAIL_TO_PASS', tests=['tests/test_bug.py::test_bug'], passed=f2p),
        pass_to_pass=SuiteResult(name='PASS_TO_PASS', tests=['tests/test_old.py::test_old'], passed=p2p),
    )


def test_aggregate_metrics_reports_real_test_and_logical_correctness_rates() -> None:
    resolved_with_unsat = RunMetrics(
        task_id='task1',
        run_id='r1',
        condition='neural_cegf',
        success=True,
        termination_reason='tests_resolved',
        total_iterations=1,
        total_prompt_tokens=100,
        total_completion_tokens=20,
        total_duration_ms=1000,
        solver_duration_ms=100,
        solver_outcomes={'unsat': 1},
        test_evaluated=True,
        test_resolved=True,
        final_test_evaluation=_test_evaluation(resolved=True),
        iterations=[
            IterationRecord(
                iteration=0,
                solver_result=SolverResultContract(
                    solver_result_id='s1',
                    task_id='task1',
                    iteration=0,
                    status='unsat',
                ),
            )
        ],
    )
    resolved_without_solver = RunMetrics(
        task_id='task2',
        run_id='r2',
        condition='neural_cegf',
        success=True,
        termination_reason='tests_resolved',
        total_iterations=1,
        total_prompt_tokens=80,
        total_completion_tokens=20,
        total_duration_ms=1000,
        test_evaluated=True,
        test_resolved=True,
        final_test_evaluation=_test_evaluation(resolved=True),
        iterations=[IterationRecord(iteration=0)],
    )
    unresolved_with_sat = RunMetrics(
        task_id='task3',
        run_id='r3',
        condition='neural_cegf',
        success=False,
        termination_reason='tests_failed_after_solver',
        total_iterations=1,
        total_prompt_tokens=50,
        total_completion_tokens=10,
        total_duration_ms=1000,
        solver_duration_ms=50,
        solver_outcomes={'sat': 1},
        test_evaluated=True,
        test_resolved=False,
        final_test_evaluation=_test_evaluation(resolved=False, f2p=True, p2p=False),
        iterations=[
            IterationRecord(
                iteration=0,
                solver_result=SolverResultContract(
                    solver_result_id='s2',
                    task_id='task3',
                    iteration=0,
                    status='sat',
                ),
            )
        ],
    )

    summary = aggregate_metrics({'neural_cegf': [resolved_with_unsat, resolved_without_solver, unresolved_with_sat]})
    metrics = summary['neural_cegf']

    assert metrics['real_test_success_rate'] == 0.6667
    assert metrics['bug_resolution_rate'] == 0.6667
    assert metrics['test_resolution_rate'] == 0.6667
    assert metrics['logical_correctness_rate'] == 0.3333
    assert metrics['solver_coverage_rate'] == 0.6667
    assert metrics['counterexample_detection_rate'] == 0.5
    assert metrics['tokens_per_success'] == 110.0
    assert metrics['solver_overhead_fraction'] == 0.05
    assert metrics['regression_rate'] == 0.3333
