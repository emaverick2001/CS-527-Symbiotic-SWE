from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.dataset.dataset_writer import write_task_subset_files
from src.dataset.task_loader import (
    PREFERRED_REPOS,
    CandidateTask,
    RawTaskError,
    TaskLoader,
    TaskLoaderConfig,
    TaskObject,
    raw_subset_rows,
    score_candidate,
)


@dataclass(frozen=True)
class DatasetPreparationResult:
    raw_tasks: tuple[TaskObject, ...]
    malformed_tasks: tuple[RawTaskError, ...]
    skipped_tasks: tuple[CandidateTask, ...]
    smoke_tasks: tuple[TaskObject, ...]
    core_tasks: tuple[TaskObject, ...]
    smoke_path: Path
    core_path: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_swe_bench_input_path(root: Path | None = None) -> Path:
    base = root or project_root()
    return base / 'data' / 'benchmarks' / 'swe_bench' / 'verified' / 'jsonl' / 'test.jsonl'


def default_processed_output_dir(root: Path | None = None) -> Path:
    base = root or project_root()
    return base / 'data' / 'benchmarks' / 'swe_bench' / 'verified' / 'filtered'


def load_raw_swe_bench_tasks(
    input_path: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
) -> tuple[list[TaskObject], list[RawTaskError]]:
    loader = TaskLoader(TaskLoaderConfig(dataset_name=dataset_name, split=split))
    return loader.load_raw_tasks(input_path)


def score_task_definition(
    task: TaskObject,
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
) -> CandidateTask:
    return score_candidate(
        task=task,
        preferred_repos=preferred_repos,
        repo_filter_mode=repo_filter_mode,
        max_changed_lines=max_changed_lines,
        max_changed_files=max_changed_files,
        min_logic_score=min_logic_score,
    )


def prepare_swe_bench_tasks(
    input_path: Path,
    output_dir: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    smoke_count: int = 5,
    core_count: int = 40,
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
) -> DatasetPreparationResult:
    loader = TaskLoader(
        TaskLoaderConfig(
            dataset_name=dataset_name,
            split=split,
            preferred_repos=preferred_repos,
            repo_filter_mode=repo_filter_mode,
            smoke_count=smoke_count,
            core_count=core_count,
            max_changed_lines=max_changed_lines,
            max_changed_files=max_changed_files,
            min_logic_score=min_logic_score,
        )
    )
    raw_tasks, malformed_tasks = loader.load_raw_tasks(input_path=input_path)
    candidates = loader.score_tasks(raw_tasks)
    smoke_candidates, core_candidates, skipped = loader.select_subsets(candidates)

    smoke_rows = raw_subset_rows(smoke_candidates[:smoke_count])
    core_rows = raw_subset_rows(core_candidates[:core_count])
    smoke_path, core_path = write_task_subset_files(
        output_dir.resolve(),
        smoke_rows=smoke_rows,
        core_rows=core_rows,
    )

    return DatasetPreparationResult(
        raw_tasks=tuple(raw_tasks),
        malformed_tasks=tuple(malformed_tasks),
        skipped_tasks=tuple(skipped),
        smoke_tasks=tuple(candidate.raw for candidate in smoke_candidates[:smoke_count]),
        core_tasks=tuple(candidate.raw for candidate in core_candidates[:core_count]),
        smoke_path=smoke_path,
        core_path=core_path,
    )
