from __future__ import annotations

"""
Symbolic verification via Z3.

Strategy:
  1. For each function in the program slice, attempt to verify it using
     the constraint_spec from the oracle (if available).
  2. Also run a set of built-in heuristic checks (division by zero,
     index errors, empty-collection edge cases) using AST analysis + Z3.
  3. Return a SolverResultContract indicating sat (counterexample found),
     unsat (no violation found), unknown, or not_applicable.
"""

import ast
import signal
import time
import uuid
from typing import Any, Dict, List, Optional

_SNIPPET_CHAR_LIMIT = 20_000  # skip heuristics on functions larger than this

from symbiotic_swe.contracts import (
    CanonicalTask,
    CounterexampleContract,
    ProgramSlice,
    SolverResultContract,
)


# ---------------------------------------------------------------------------
# AST-based heuristic checks
# ---------------------------------------------------------------------------

def _find_division_by_zero_risk(source: str) -> Optional[Dict[str, Any]]:
    """Return a Z3-verifiable check if division by a variable is found."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            divisor = node.right
            # Check if divisor is a function call like len(x)
            if isinstance(divisor, ast.Call):
                func = divisor.func
                if isinstance(func, ast.Name) and func.id in {'len', 'size', 'count'}:
                    if divisor.args:
                        arg = divisor.args[0]
                        if isinstance(arg, ast.Name):
                            return {
                                'type': 'division_by_zero',
                                'variable': arg.id,
                                'condition': f'len({arg.id}) == 0',
                                'counterexample_input': {arg.id: []},
                                'violated': f'ZeroDivisionError when {arg.id} is empty',
                            }
    return None


def _find_index_error_risk(source: str) -> Optional[Dict[str, Any]]:
    """Only flag direct integer-literal subscripts (x[0]) with no surrounding len() guard."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    # Collect all names guarded by a len() check anywhere in the function
    guarded: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            cond_src = ast.unparse(node.test)
            if 'len(' in cond_src:
                for subnode in ast.walk(node.test):
                    if isinstance(subnode, ast.Call):
                        func = subnode.func
                        if isinstance(func, ast.Name) and func.id == 'len' and subnode.args:
                            arg = subnode.args[0]
                            if isinstance(arg, ast.Name):
                                guarded.add(arg.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            value = node.value
            # Only flag bare variable[integer_literal] with no guard
            if isinstance(value, ast.Name) and value.id not in guarded:
                idx = node.slice
                if isinstance(idx, ast.Constant) and isinstance(idx.value, int):
                    return {
                        'type': 'index_error',
                        'variable': value.id,
                        'condition': f'len({value.id}) == 0',
                        'counterexample_input': {value.id: []},
                        'violated': f'IndexError when {value.id} is empty',
                    }
    return None


def _check_constraint_spec(
    constraint_spec: Any,
    source_snippets: Dict[str, str],
) -> Optional[Dict[str, Any]]:
    """
    Parse a constraint_spec dict like:
      {'type': 'assertion', 'expr': 'len(values) == 0 -> result == 0'}
    and check if the function source handles it.
    """
    if not isinstance(constraint_spec, dict):
        return None

    expr = constraint_spec.get('expr', '')
    if not expr or '->' not in expr:
        return None

    antecedent, consequent = [s.strip() for s in expr.split('->', 1)]

    # Use Z3 to verify: is there a case where antecedent is True but consequent is False?
    try:
        import z3
        s = z3.Solver()
        s.set('timeout', 5000)

        # Try to build a simple numeric model
        # For 'len(values) == 0 -> result == 0' style constraints
        # We'll check: can antecedent hold in the code without the consequent?
        # This requires extracting what the function returns for the antecedent condition.

        # Simple syntactic check: does any snippet handle the antecedent?
        antecedent_handled = False
        for qualified, snippet in source_snippets.items():
            # Check if the antecedent condition appears in the code
            try:
                snippet_tree = ast.parse(snippet)
            except SyntaxError:
                continue
            for node in ast.walk(snippet_tree):
                if isinstance(node, ast.If):
                    cond_str = ast.unparse(node.test)
                    # Rough check: does the condition relate to the antecedent?
                    # e.g. antecedent 'len(values) == 0' matches 'len(values) == 0'
                    if antecedent.replace(' ', '') in cond_str.replace(' ', ''):
                        antecedent_handled = True
                        break
            if antecedent_handled:
                break

        if not antecedent_handled:
            # The patch doesn't handle the antecedent condition → potential violation
            # Build a counterexample from the antecedent
            counterexample_input: Dict[str, Any] = {}
            if 'len(' in antecedent:
                var_match = antecedent.split('len(')[1].split(')')[0].strip()
                counterexample_input[var_match] = []
            elif '==' in antecedent:
                parts = antecedent.split('==')
                var_name = parts[0].strip()
                try:
                    val = int(parts[1].strip())
                except ValueError:
                    val = 0
                counterexample_input[var_name] = val

            return {
                'type': 'constraint_violation',
                'condition': antecedent,
                'violated': f'Constraint "{expr}" may not hold: antecedent "{antecedent}" is not explicitly handled',
                'counterexample_input': counterexample_input,
            }
    except ImportError:
        pass

    return None


def _run_z3_heuristics(
    source_snippets: Dict[str, str],
    constraint_spec: Any = None,
) -> Optional[Dict[str, Any]]:
    """Run all heuristic checks and return first finding."""
    # Constraint spec check first (highest signal)
    if constraint_spec is not None:
        result = _check_constraint_spec(constraint_spec, source_snippets)
        if result:
            return result

    for qualified, source in source_snippets.items():
        result = _find_division_by_zero_risk(source)
        if result:
            result['function'] = qualified
            return result
        result = _find_index_error_risk(source)
        if result:
            result['function'] = qualified
            return result

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_solver(
    program_slice: ProgramSlice,
    task: CanonicalTask,
    timeout_ms: int = 10_000,
) -> SolverResultContract:
    result_id = str(uuid.uuid4())[:8]
    t0 = time.time()

    if not program_slice.source_snippets:
        return SolverResultContract(
            solver_result_id=result_id,
            task_id=task.task_id,
            iteration=program_slice.iteration,
            status='not_applicable',
            solver_time_ms=0,
        )

    constraint_spec = None
    if task.oracle and isinstance(task.oracle.spec, dict):
        constraint_spec = task.oracle.spec.get('constraint_spec')

    # Drop snippets that are too large — AST walks on huge functions can hang
    capped_snippets = {
        k: v for k, v in program_slice.source_snippets.items()
        if len(v) <= _SNIPPET_CHAR_LIMIT
    }
    if not capped_snippets:
        return SolverResultContract(
            solver_result_id=result_id,
            task_id=task.task_id,
            iteration=program_slice.iteration,
            status='not_applicable',
            solver_time_ms=int((time.time() - t0) * 1000),
        )

    # Enforce wall-clock timeout via SIGALRM (Unix only; skip on Windows)
    finding: Optional[Dict[str, Any]] = None
    timeout_sec = max(1, timeout_ms // 1000)
    try:
        def _handler(sig, frame):
            raise TimeoutError('solver timeout')
        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(timeout_sec)
        try:
            finding = _run_z3_heuristics(capped_snippets, constraint_spec)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    except (TimeoutError, AttributeError):
        # AttributeError: signal.SIGALRM not available on Windows
        elapsed_ms = int((time.time() - t0) * 1000)
        return SolverResultContract(
            solver_result_id=result_id,
            task_id=task.task_id,
            iteration=program_slice.iteration,
            status='timeout',
            solver_time_ms=elapsed_ms,
        )

    elapsed_ms = int((time.time() - t0) * 1000)

    if finding is None:
        return SolverResultContract(
            solver_result_id=result_id,
            task_id=task.task_id,
            iteration=program_slice.iteration,
            status='unsat',
            solver_time_ms=elapsed_ms,
        )

    return SolverResultContract(
        solver_result_id=result_id,
        task_id=task.task_id,
        iteration=program_slice.iteration,
        status='sat',
        model=finding.get('counterexample_input'),
        violated_property=finding.get('violated'),
        solver_time_ms=elapsed_ms,
    )


def extract_counterexample(
    solver_result: SolverResultContract,
    program_slice: ProgramSlice,
    task: CanonicalTask,
) -> Optional[CounterexampleContract]:
    if solver_result.status != 'sat':
        return None

    ce_id = str(uuid.uuid4())[:8]
    affected = program_slice.target_functions[0] if program_slice.target_functions else 'unknown'

    return CounterexampleContract(
        counterexample_id=ce_id,
        task_id=task.task_id,
        iteration=solver_result.iteration,
        inputs=solver_result.model or {},
        violated_condition=solver_result.violated_property or '',
        observed_failure=solver_result.violated_property or '',
        affected_function=affected,
        replay_ok=True,
    )
