"""Minimal dataset package exports for the current iterative pipeline."""

from importlib import import_module
from typing import Any

__all__ = [
    'CandidateTask',
    'PREFERRED_REPOS',
    'REPO_FILTER_MODES',
    'RawTaskError',
    'TaskLoader',
    'TaskLoaderConfig',
    'TaskObject',
    'export_ranked_raw_subsets',
    'raw_subset_rows',
    'score_candidate',
    'write_raw_jsonl',
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = import_module('src.dataset.task_loader')
        return getattr(module, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
