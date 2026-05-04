from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# allow running as a script
if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.dataset.task_loader import (
    PREFERRED_REPOS,
    CandidateTask,
    RawTaskError,
    TaskObject,
    balanced_take,
    parse_jsonl,
    score_candidate,
    sort_candidates,
)


@dataclass(frozen=True)
class TaskLoaderConfig:
    dataset_name: str = 'SWE-bench Verified'
    split: str = 'test'
    preferred_repos: Tuple[str, ...] = PREFERRED_REPOS
    repo_filter_mode: str = 'preferred'
    smoke_count: int = 5
    dev_count: int = 20
    final_eval_count: int = 40
    max_changed_lines: int = 30
    max_changed_files: int = 3
    min_logic_score: int = 6


def _build_subsets(
    candidates: List[CandidateTask],
    smoke_count: int,
    dev_count: int,
    final_eval_count: int,
    preferred_repos: Tuple[str, ...] = PREFERRED_REPOS,
) -> Tuple[List[CandidateTask], List[CandidateTask], List[CandidateTask], List[CandidateTask]]:
    usable = sort_candidates([c for c in candidates if not c.exclusion_reasons])
    skipped = sort_candidates([c for c in candidates if c.exclusion_reasons])

    smoke_pool = [c for c in usable if c.include_for_smoke]
    smoke = balanced_take(smoke_pool, smoke_count, preferred_repos)
    used = {c.raw.instance_id for c in smoke}

    remaining = [c for c in usable if c.logic_heavy and c.raw.instance_id not in used]
    dev = balanced_take(remaining, dev_count, preferred_repos)
    used |= {c.raw.instance_id for c in dev}

    final_pool = [c for c in usable if c.logic_heavy and c.raw.instance_id not in used]
    final_eval = balanced_take(final_pool, final_eval_count, preferred_repos)

    return smoke, dev, final_eval, skipped


class TaskLoader:
    def __init__(self, config: Optional[TaskLoaderConfig] = None) -> None:
        self.config = config or TaskLoaderConfig()
        self.dataset_source = 'swe_bench_verified'

    def validate_row(
        self,
        row: dict,
        row_number: int,
        input_path: Path,
    ) -> Tuple[Optional[TaskObject], Optional[RawTaskError]]:
        from src.dataset.task_loader import TaskLoader as _BaseLoader, TaskLoaderConfig as _BaseCfg
        base = _BaseLoader(_BaseCfg(
            dataset_name=self.config.dataset_name,
            split=self.config.split,
            preferred_repos=self.config.preferred_repos,
            repo_filter_mode=self.config.repo_filter_mode,
        ))
        return base.validate_row(row, row_number, input_path)

    def load_raw_tasks(self, input_path: Path) -> Tuple[List[TaskObject], List[RawTaskError]]:
        raw_rows = parse_jsonl(input_path)
        tasks: List[TaskObject] = []
        errors: List[RawTaskError] = []
        for index, row in enumerate(raw_rows, start=1):
            task, error = self.validate_row(row, index, input_path)
            if error is not None:
                errors.append(error)
            elif task is not None:
                tasks.append(task)
        return tasks, errors

    def score_task(self, task: TaskObject) -> CandidateTask:
        return score_candidate(
            task=task,
            preferred_repos=self.config.preferred_repos,
            repo_filter_mode=self.config.repo_filter_mode,
            max_changed_lines=self.config.max_changed_lines,
            max_changed_files=self.config.max_changed_files,
            min_logic_score=self.config.min_logic_score,
        )

    def score_tasks(self, tasks: List[TaskObject]) -> List[CandidateTask]:
        return [self.score_task(t) for t in tasks]

    def select_subsets(
        self, candidates: List[CandidateTask]
    ) -> Tuple[List[CandidateTask], List[CandidateTask], List[CandidateTask], List[CandidateTask]]:
        return _build_subsets(
            candidates,
            smoke_count=self.config.smoke_count,
            dev_count=self.config.dev_count,
            final_eval_count=self.config.final_eval_count,
            preferred_repos=self.config.preferred_repos,
        )


def load_raw_swe_bench_tasks(
    input_path: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
) -> Tuple[List[TaskObject], List[RawTaskError]]:
    loader = TaskLoader(TaskLoaderConfig(dataset_name=dataset_name, split=split))
    return loader.load_raw_tasks(input_path)
