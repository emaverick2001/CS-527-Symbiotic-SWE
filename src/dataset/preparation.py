from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.contracts import TaskContract
from src.dataset.dataset_writer import write_prepared_tasks
from src.dataset.repo_indexer import (
    PreparedTaskArtifact,
    RepositoryIndexer,
    RepositoryIndexerConfig,
)
from src.dataset.task_loader import (
    PREFERRED_REPOS,
    CandidateTask,
    RawTaskDefinition,
    RawTaskError,
    TaskLoader,
    TaskLoaderConfig,
    score_candidate,
)


@dataclass(frozen=True)
class DatasetPreparationResult:
    raw_tasks: tuple[RawTaskDefinition, ...]
    malformed_tasks: tuple[RawTaskError, ...]
    skipped_tasks: tuple[CandidateTask, ...]
    repo_failures: tuple[PreparedTaskArtifact, ...]
    smoke_tasks: tuple[PreparedTaskArtifact, ...]
    dev_tasks: tuple[PreparedTaskArtifact, ...]
    final_eval_tasks: tuple[PreparedTaskArtifact, ...]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_swe_bench_input_path(root: Path | None = None) -> Path:
    base = root or project_root()
    return (
        base / 'data' / 'benchmarks' / 'swe_bench' / 'verified' / 'jsonl' / 'test.jsonl'
    )


def default_processed_output_dir(root: Path | None = None) -> Path:
    base = root or project_root()
    return base / 'data' / 'processed' / 'tasks' / 'swe_bench_verified'


def default_repo_source_root(root: Path | None = None) -> Path:
    base = root or project_root()
    return base / 'data' / 'raw' / 'repos'


def load_raw_swe_bench_tasks(
    input_path: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
) -> tuple[list[RawTaskDefinition], list[RawTaskError]]:
    loader = TaskLoader(TaskLoaderConfig(dataset_name=dataset_name, split=split))
    return loader.load_raw_tasks(input_path)


def score_task_definition(
    task: RawTaskDefinition,
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


def normalize_task(candidate: CandidateTask, subset: str) -> TaskContract:
    return TaskLoader().normalize_task(candidate, subset)


def prepare_swe_bench_tasks(
    input_path: Path,
    output_dir: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    smoke_count: int = 5,
    dev_count: int = 10,
    final_eval_count: int = 40,
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
    workspace_root: Path | None = None,
    cache_root: Path | None = None,
    repo_source_root: Path | None = None,
    repo_source_overrides: dict[str, Path] | None = None,
) -> DatasetPreparationResult:
    loader = TaskLoader(
        TaskLoaderConfig(
            dataset_name=dataset_name,
            split=split,
            preferred_repos=preferred_repos,
            repo_filter_mode=repo_filter_mode,
            smoke_count=smoke_count,
            dev_count=dev_count,
            final_eval_count=final_eval_count,
            max_changed_lines=max_changed_lines,
            max_changed_files=max_changed_files,
            min_logic_score=min_logic_score,
        )
    )
    raw_tasks, malformed_tasks = loader.load_raw_tasks(input_path=input_path)
    candidates = loader.score_tasks(raw_tasks)
    smoke_candidates, dev_candidates, final_eval_candidates, skipped = (
        loader.select_subsets(candidates)
    )

    output_dir = output_dir.resolve()
    workspace_root = (workspace_root or (output_dir / 'workspaces')).resolve()
    cache_root = (
        cache_root or (output_dir / 'cache' / 'parsed_repo_indexes')
    ).resolve()
    repo_source_root = (
        repo_source_root.resolve() if repo_source_root is not None else None
    )
    timestamp = datetime.now(tz=UTC).isoformat()
    indexer = RepositoryIndexer(
        RepositoryIndexerConfig(
            workspace_root=workspace_root,
            cache_root=cache_root,
            repo_source_root=repo_source_root,
            repo_source_overrides=repo_source_overrides,
        )
    )

    repo_failures: list[PreparedTaskArtifact] = []

    def prepare_subset(
        subset: str, candidates_for_subset: list[CandidateTask]
    ) -> tuple[PreparedTaskArtifact, ...]:
        artifacts: list[PreparedTaskArtifact] = []
        for candidate in candidates_for_subset:
            artifact = indexer.prepare_task(
                task=loader.normalize_task(candidate, subset),
                raw_task=candidate.raw,
                subset=subset,
                output_dir=output_dir,
                timestamp=timestamp,
            )
            if artifact.status == 'invalid':
                repo_failures.append(artifact)
                continue
            artifacts.append(artifact)
        return tuple(artifacts)

    result = DatasetPreparationResult(
        raw_tasks=tuple(raw_tasks),
        malformed_tasks=tuple(malformed_tasks),
        skipped_tasks=tuple(skipped),
        repo_failures=(),
        smoke_tasks=prepare_subset('smoke', smoke_candidates),
        dev_tasks=prepare_subset('dev', dev_candidates),
        final_eval_tasks=prepare_subset('final_eval', final_eval_candidates),
    )
    result = DatasetPreparationResult(
        raw_tasks=result.raw_tasks,
        malformed_tasks=result.malformed_tasks,
        skipped_tasks=result.skipped_tasks,
        repo_failures=tuple(repo_failures),
        smoke_tasks=result.smoke_tasks,
        dev_tasks=result.dev_tasks,
        final_eval_tasks=result.final_eval_tasks,
    )
    write_prepared_tasks(result, output_dir)
    return result
