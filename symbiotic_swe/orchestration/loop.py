"""
Counter-Example Guided Feedback (CEGF) loop.

Conditions:
  neural_only      - LLM generates patch, no symbolic verification
  neural_slicing   - LLM + impact slicing, no solver
  neural_solver    - LLM + slicing + solver verification (no feedback to LLM)
  neural_cegf      - Full system: LLM + slicing + solver + critique feedback
"""

from __future__ import annotations

import ast
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from symbiotic_swe.contracts import (
    CanonicalTask,
    CritiqueContract,
    IterationRecord,
    RepoIndex,
    RunMetrics,
    TestEvaluationResult,
)
from symbiotic_swe.context_selection.selector import select_context
from symbiotic_swe.dataset.repo_indexer import apply_patch_to_repository
from symbiotic_swe.evaluation.test_runner import evaluate_task_tests
from symbiotic_swe.feedback.critique import build_critique
from symbiotic_swe.patch_generation.generator import generate_patch, repair_patch_application
from symbiotic_swe.slicing.slicer import slice_impact
from symbiotic_swe.symbolic_reasoning.solver import extract_counterexample, run_solver


def _make_working_copy(repo_path: Path, work_root: Path, task_id: str, run_id: str) -> Path:
    dest = work_root / task_id / run_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(repo_path, dest)
    return dest


def _reset_working_copy(work_copy: Path, repo_path: Path) -> None:
    shutil.rmtree(work_copy)
    shutil.copytree(repo_path, work_copy)


def _record_test_evaluation(
    *,
    task: CanonicalTask,
    record: IterationRecord,
    metrics: RunMetrics,
    work_copy: Optional[Path],
) -> Optional[TestEvaluationResult]:
    if work_copy is None or not work_copy.exists():
        return None

    evaluation = evaluate_task_tests(work_copy, task, record.iteration)
    record.test_evaluation = evaluation
    metrics.test_evaluated = evaluation.evaluated
    metrics.test_resolved = evaluation.resolved
    metrics.final_test_evaluation = evaluation
    return evaluation


def _check_patch_syntax(repo_path: Path, target_files: list[str]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    checked = False
    for rel_path in target_files:
        if not rel_path.endswith('.py'):
            continue
        checked = True
        path = repo_path / rel_path
        try:
            ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        except Exception as exc:
            errors.append(f'{rel_path}: syntax check failed: {exc}')
    return (not errors if checked else True), errors


def _build_test_failure_critique(
    task: CanonicalTask,
    evaluation: TestEvaluationResult,
    iteration: int,
) -> CritiqueContract:
    f2p = evaluation.fail_to_pass
    stderr = (f2p.stderr or '').strip()
    stdout = (f2p.stdout or '').strip()
    output = stderr or stdout or f2p.error or 'pytest failed without captured output'
    output = output[-4000:]
    return CritiqueContract(
        critique_id=str(uuid.uuid4())[:8],
        task_id=task.task_id,
        iteration=iteration,
        short_text=(
            f'Your patch from iteration {iteration} applied, but the real FAIL_TO_PASS tests still failed.\n'
            f'Tests: {", ".join(f2p.tests) if f2p.tests else "unknown"}\n'
            f'Pytest return code: {f2p.returncode}\n\n'
            f'Pytest failure output:\n{output}\n\n'
            'Use this concrete pytest failure as the primary repair signal. '
            'Keep the next patch minimal and make sure it applies to the exact checked-out source.'
        ),
        structured={
            'source': 'pytest',
            'tests': f2p.tests,
            'returncode': f2p.returncode,
            'iteration': iteration,
        },
    )


def run_cegf_loop(
    task: CanonicalTask,
    repo_index: RepoIndex,
    condition: str = 'neural_cegf',
    max_iterations: int = 3,
    api_key: Optional[str] = None,
    model: str = 'gpt-5.4-mini',
    provider: str = 'openai',
    work_root: Optional[Path] = None,
) -> RunMetrics:
    assert condition in {'neural_only', 'neural_slicing', 'neural_solver', 'neural_cegf'}

    run_id = str(uuid.uuid4())[:8]
    repo_path = Path(task.repo_path) if task.repo_path else None
    work_root = work_root or Path('/tmp/symbiotic_swe_runs')

    metrics = RunMetrics(
        task_id=task.task_id,
        run_id=run_id,
        condition=condition,
        model_provider=provider,
        model=model,
    )

    context = select_context(task, repo_index)

    # Make a disposable working copy of the repo for applying patches
    work_copy: Optional[Path] = None
    if repo_path and repo_path.exists():
        work_copy = _make_working_copy(repo_path, work_root, task.task_id, run_id)

    critique: Optional[CritiqueContract] = None
    seen_counterexamples: set = set()
    t_start = time.time()

    for iteration in range(max_iterations):
        t_iter = time.time()
        record = IterationRecord(iteration=iteration)

        # ── 1. Generate patch ───────────────────────────────────────────────
        patch = generate_patch(
            task=task,
            context=context,
            iteration=iteration,
            critique=critique if condition == 'neural_cegf' else None,
            repo_path=repo_path,
            api_key=api_key,
            model=model,
            provider=provider,
        )
        record.patch = patch
        metrics.total_prompt_tokens += patch.prompt_tokens
        metrics.total_completion_tokens += patch.completion_tokens

        if not patch.parse_ok:
            metrics.patch_apply_failures += 1
            record.duration_ms = int((time.time() - t_iter) * 1000)
            metrics.iterations.append(record)
            continue

        # ── 2. Apply patch ──────────────────────────────────────────────────
        apply_result = None
        if work_copy and work_copy.exists():
            apply_result = apply_patch_to_repository(work_copy, patch.diff)
            if not apply_result.applied and apply_result.error and api_key:
                _reset_working_copy(work_copy, repo_path)
                repaired_patch = repair_patch_application(
                    task=task,
                    failed_patch=patch,
                    apply_error=apply_result.error,
                    repo_path=work_copy,
                    api_key=api_key,
                    model=model,
                    provider=provider,
                )
                metrics.total_prompt_tokens += repaired_patch.prompt_tokens
                metrics.total_completion_tokens += repaired_patch.completion_tokens
                if repaired_patch.parse_ok:
                    repaired_apply_result = apply_patch_to_repository(work_copy, repaired_patch.diff)
                    repaired_patch = repaired_patch.model_copy(update={
                        'apply_ok': repaired_apply_result.applied,
                        'errors': repaired_patch.errors + (
                            [repaired_apply_result.error] if repaired_apply_result.error else []
                        ),
                    })
                    if repaired_apply_result.applied:
                        patch = repaired_patch
                        apply_result = repaired_apply_result
                    else:
                        patch = repaired_patch
                        apply_result = repaired_apply_result
                else:
                    patch = repaired_patch

            patch = patch.model_copy(update={
                'apply_ok': apply_result.applied,
                'errors': patch.errors + ([apply_result.error] if apply_result.error else []),
            })
            record.patch = patch

            if not apply_result.applied:
                metrics.patch_apply_failures += 1
                _reset_working_copy(work_copy, repo_path)
                record.duration_ms = int((time.time() - t_iter) * 1000)
                metrics.iterations.append(record)
                continue

            syntax_ok, syntax_errors = _check_patch_syntax(work_copy, patch.target_files)
            patch = patch.model_copy(update={
                'syntax_ok': syntax_ok,
                'errors': patch.errors + syntax_errors,
            })
            record.patch = patch

        # ── 3. Neural-only: stop after first successful patch apply ─────────
        if condition == 'neural_only':
            test_eval = _record_test_evaluation(
                task=task,
                record=record,
                metrics=metrics,
                work_copy=work_copy,
            )
            if test_eval is not None:
                metrics.success = test_eval.resolved
                metrics.termination_reason = 'tests_resolved' if test_eval.resolved else 'tests_failed'
            else:
                metrics.success = True
                metrics.termination_reason = 'neural_only_patch_applied_no_test_evaluation'
            record.duration_ms = int((time.time() - t_iter) * 1000)
            metrics.iterations.append(record)
            break

        # ── 4. Slice impact ─────────────────────────────────────────────────
        slice_repo = work_copy if (work_copy and work_copy.exists()) else repo_path
        program_slice = None
        if slice_repo:
            program_slice = slice_impact(patch, slice_repo, task.task_id)
            record.program_slice = program_slice

        if condition == 'neural_slicing':
            test_eval = _record_test_evaluation(
                task=task,
                record=record,
                metrics=metrics,
                work_copy=work_copy,
            )
            if test_eval is not None:
                metrics.success = test_eval.resolved
                metrics.termination_reason = 'tests_resolved' if test_eval.resolved else 'tests_failed_after_slicing'
            else:
                metrics.success = True
                metrics.termination_reason = 'slicing_only_patch_applied_no_test_evaluation'
            record.duration_ms = int((time.time() - t_iter) * 1000)
            metrics.iterations.append(record)
            break

        # ── 5. Symbolic verification ────────────────────────────────────────
        t_solver = time.time()
        solver_result = None
        if program_slice is not None:
            solver_result = run_solver(program_slice, task)
            metrics.solver_duration_ms += int((time.time() - t_solver) * 1000)
            record.solver_result = solver_result
            status = solver_result.status
            metrics.solver_outcomes[status] = metrics.solver_outcomes.get(status, 0) + 1

        if solver_result is None or solver_result.status in {'unsat', 'not_applicable', 'unknown', 'timeout', 'error'}:
            test_eval = _record_test_evaluation(
                task=task,
                record=record,
                metrics=metrics,
                work_copy=work_copy,
            )
            if test_eval is not None:
                metrics.success = test_eval.resolved
                metrics.termination_reason = 'tests_resolved' if test_eval.resolved else 'tests_failed_after_solver'
                if (
                    condition == 'neural_cegf'
                    and not test_eval.resolved
                    and iteration < max_iterations - 1
                ):
                    critique = _build_test_failure_critique(task, test_eval, iteration)
                    record.critique = critique
                    if work_copy and repo_path:
                        _reset_working_copy(work_copy, repo_path)
                    record.duration_ms = int((time.time() - t_iter) * 1000)
                    metrics.iterations.append(record)
                    continue
            else:
                metrics.success = True
                metrics.termination_reason = solver_result.status if solver_result else 'no_slice'
            record.duration_ms = int((time.time() - t_iter) * 1000)
            metrics.iterations.append(record)
            break

        # ── 6. Counterexample found ─────────────────────────────────────────
        counterexample = extract_counterexample(solver_result, program_slice, task)
        record.counterexample = counterexample

        if condition == 'neural_solver':
            # Solver only — no CEGF feedback, record and stop
            metrics.success = False
            metrics.termination_reason = 'solver_sat_no_feedback'
            record.duration_ms = int((time.time() - t_iter) * 1000)
            metrics.iterations.append(record)
            break

        # ── 7. Build critique and loop (neural_cegf) ────────────────────────
        ce_key = str(counterexample.inputs) if counterexample else ''
        if ce_key in seen_counterexamples:
            metrics.repeated_counterexamples += 1
        else:
            seen_counterexamples.add(ce_key)

        if counterexample:
            critique = build_critique(counterexample, solver_result, iteration)
            record.critique = critique

        # Reset working copy for next iteration
        if work_copy and repo_path:
            _reset_working_copy(work_copy, repo_path)

        record.duration_ms = int((time.time() - t_iter) * 1000)
        metrics.iterations.append(record)

    else:
        # Exhausted budget
        metrics.termination_reason = 'budget_exhausted'

    metrics.total_iterations = len(metrics.iterations)
    metrics.total_duration_ms = int((time.time() - t_start) * 1000)

    # Cleanup working copy
    if work_copy and work_copy.exists():
        shutil.rmtree(work_copy, ignore_errors=True)

    return metrics
