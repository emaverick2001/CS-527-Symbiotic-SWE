from __future__ import annotations

import uuid
from typing import Any, Dict

from symbiotic_swe.contracts import (
    CounterexampleContract,
    CritiqueContract,
    SolverResultContract,
)


def _format_inputs(inputs: Dict[str, Any]) -> str:
    parts = []
    for k, v in inputs.items():
        if isinstance(v, list) and len(v) == 0:
            parts.append(f'{k} = [] (empty list)')
        else:
            parts.append(f'{k} = {repr(v)}')
    return ', '.join(parts) if parts else 'unknown inputs'


def build_critique(
    counterexample: CounterexampleContract,
    solver_result: SolverResultContract,
    iteration: int,
) -> CritiqueContract:
    critique_id = str(uuid.uuid4())[:8]
    inputs_str = _format_inputs(counterexample.inputs)
    func = counterexample.affected_function.split('::')[-1] if '::' in counterexample.affected_function else counterexample.affected_function

    short_text = (
        f'Your patch (iteration {iteration}) still fails the symbolic verifier.\n'
        f'Function `{func}` produces incorrect behavior when called with {inputs_str}.\n'
        f'Violation: {counterexample.violated_condition}\n\n'
        f'You must handle the case where {inputs_str} explicitly to satisfy the logical constraint.'
    )

    structured: Dict[str, Any] = {
        'function': func,
        'inputs': counterexample.inputs,
        'error': counterexample.observed_failure,
        'violated_condition': counterexample.violated_condition,
        'iteration': iteration,
    }

    return CritiqueContract(
        critique_id=critique_id,
        task_id=counterexample.task_id,
        iteration=iteration,
        short_text=short_text,
        structured=structured,
        source_counterexample_id=counterexample.counterexample_id,
    )
