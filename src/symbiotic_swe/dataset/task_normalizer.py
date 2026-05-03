from __future__ import annotations

from src.dataset.task_loader import CandidateTask
from symbiotic_swe.contracts import CanonicalTask, OracleSpec, TaskMetadata


_BUG_TYPE_PRIORITY = [
    'multi_conditional_reasoning_bug',
    'arithmetic_predicate_bug',
    'relational_operator_bug',
    'assertion_violation_bug',
    'wrong_return_logic_bug',
    'edge_case_bug',
]


def _primary_bug_type(labels: tuple) -> str | None:
    for label in _BUG_TYPE_PRIORITY:
        if label in labels:
            return label
    return labels[0] if labels else None


def _build_oracle(candidate: CandidateTask) -> OracleSpec | None:
    raw = candidate.raw
    spec: dict = {}
    if raw.patch:
        spec['gold_patch'] = raw.patch
    if raw.test_patch:
        spec['test_patch'] = raw.test_patch
    if raw.constraint_spec is not None:
        spec['constraint_spec'] = raw.constraint_spec

    if not spec and not raw.failing_tests:
        return None

    oracle_type = 'tests'
    if raw.constraint_spec is not None:
        oracle_type = 'constraints'
    if raw.patch:
        oracle_type = 'ground_truth'

    return OracleSpec(type=oracle_type, spec=spec or list(raw.failing_tests))


class TaskNormalizer:
    def normalize_task(self, candidate: CandidateTask, subset: str) -> CanonicalTask:
        raw = candidate.raw
        repo_name = raw.repo.split('/')[-1]
        bug_type = _primary_bug_type(candidate.labels)
        tags = ['logic-heavy'] if candidate.logic_heavy else []
        if bug_type:
            tags.append(bug_type)

        oracle = _build_oracle(candidate)

        metadata = TaskMetadata(
            dataset=raw.dataset,
            difficulty=raw.difficulty,
            tags=tags,
            logic_heavy=candidate.logic_heavy,
            bug_type=bug_type,
            repo_name=repo_name,
            status='valid',
            subset=subset,
        )

        return CanonicalTask(
            task_id=raw.instance_id,
            repo=raw.repo,
            repo_commit=raw.base_commit,
            bug_description=raw.problem_statement,
            failing_tests=list(raw.failing_tests),
            execution_trace=list(raw.execution_trace),
            oracle=oracle,
            metadata=metadata,
        )
