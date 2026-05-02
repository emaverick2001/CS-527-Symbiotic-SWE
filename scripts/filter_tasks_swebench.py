from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.dataset.task_loader import (
    PREFERRED_REPOS,
    CandidateTask,
    TaskLoader,
    TaskLoaderConfig,
    balanced_take as _balanced_take,
    changed_files,
    count_changed_lines,
    label_task,
    score_candidate,
)

__all__ = [
    'PREFERRED_REPOS',
    'balanced_take',
    'changed_files',
    'count_changed_lines',
    'label_task',
    'score_example',
]


@dataclass(frozen=True)
class FilterCandidate:
    candidate: CandidateTask

    @property
    def include_for_logic(self) -> bool:
        return self.candidate.logic_heavy

    @property
    def include_for_smoke(self) -> bool:
        return self.candidate.include_for_smoke

    @property
    def score(self) -> int:
        return self.candidate.score

    @property
    def labels(self) -> tuple[str, ...]:
        return self.candidate.labels

    @property
    def repo(self) -> str:
        return self.candidate.raw.repo


def score_example(
    example: dict[str, Any],
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
) -> FilterCandidate:
    normalized_example = {
        'base_commit': 'unknown',
        'PASS_TO_PASS': '[]',
        'test_patch': '',
        **example,
    }
    if not normalized_example.get('test_patch'):
        normalized_example['test_patch'] = 'diff --git a/tests/test_placeholder.py b/tests/test_placeholder.py'
    loader = TaskLoader(
        TaskLoaderConfig(
            preferred_repos=preferred_repos,
            repo_filter_mode=repo_filter_mode,
            max_changed_lines=max_changed_lines,
            max_changed_files=max_changed_files,
        )
    )
    task, error = loader.validate_row(normalized_example, row_number=1, input_path=Path('<memory>'))
    if error is not None or task is None:
        raise ValueError(error.reason if error is not None else 'invalid task')
    return FilterCandidate(
        score_candidate(
            task=task,
            preferred_repos=preferred_repos,
            repo_filter_mode=repo_filter_mode,
            max_changed_lines=max_changed_lines,
            max_changed_files=max_changed_files,
        )
    )


def balanced_take(
    candidates: list[FilterCandidate],
    limit: int,
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
) -> list[FilterCandidate]:
    selected = _balanced_take([candidate.candidate for candidate in candidates], limit, preferred_repos)
    selected_ids = {candidate.raw.instance_id for candidate in selected}
    return [candidate for candidate in candidates if candidate.candidate.raw.instance_id in selected_ids][:limit]
