from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from symbiotic_swe.models import ExecutionMode


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _slugify(value: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9._-]+', '-', value.strip()).strip('-')
    return slug or 'unnamed-task'


def _default_run_id(mode: ExecutionMode) -> str:
    timestamp = datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')
    return f'{mode.value}-{timestamp}'


@dataclass(frozen=True)
class RepositoryLayout:
    root: Path
    configs_dir: Path
    data_dir: Path
    artifacts_dir: Path
    runs_dir: Path
    logs_dir: Path
    cache_dir: Path
    retrieval_cache_dir: Path
    solver_cache_dir: Path
    prompt_cache_dir: Path
    workspaces_dir: Path

    @classmethod
    def from_root(cls, root: Path | None = None) -> RepositoryLayout:
        base = (root or project_root()).resolve()
        artifacts_dir = base / 'artifacts'
        cache_dir = artifacts_dir / 'cache'
        return cls(
            root=base,
            configs_dir=base / 'configs',
            data_dir=base / 'data',
            artifacts_dir=artifacts_dir,
            runs_dir=artifacts_dir / 'runs',
            logs_dir=artifacts_dir / 'logs',
            cache_dir=cache_dir,
            retrieval_cache_dir=cache_dir / 'retrieval',
            solver_cache_dir=cache_dir / 'solver',
            prompt_cache_dir=cache_dir / 'prompts',
            workspaces_dir=artifacts_dir / 'workspaces',
        )


@dataclass(frozen=True)
class TaskLayout:
    task_id: str
    artifact_dir: Path
    workspace_dir: Path
    repo_dir: Path
    iterations_dir: Path
    summary_dir: Path
    logs_dir: Path
    solver_logs_dir: Path
    patch_logs_dir: Path
    error_logs_dir: Path

    def create(self) -> None:
        for path in (
            self.artifact_dir,
            self.workspace_dir,
            self.repo_dir,
            self.iterations_dir,
            self.summary_dir,
            self.logs_dir,
            self.solver_logs_dir,
            self.patch_logs_dir,
            self.error_logs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def iteration_dir(self, iteration: int) -> Path:
        return self.iterations_dir / f'iter_{iteration:03d}'

    def stage_dir(self, iteration: int, stage_key: str) -> Path:
        return self.iteration_dir(iteration) / stage_key


@dataclass(frozen=True)
class RunLayout:
    mode: ExecutionMode
    run_id: str
    root: Path
    tasks_dir: Path
    workspace_root: Path
    logs_dir: Path
    run_log_path: Path
    error_log_path: Path
    cache_root: Path
    retrieval_embeddings_cache_dir: Path
    retrieved_context_cache_dir: Path
    solver_outputs_cache_dir: Path
    prompt_outputs_cache_dir: Path
    metadata_path: Path
    summary_path: Path

    def create(self) -> None:
        for path in (
            self.root,
            self.tasks_dir,
            self.workspace_root,
            self.logs_dir,
            self.cache_root,
            self.retrieval_embeddings_cache_dir,
            self.retrieved_context_cache_dir,
            self.solver_outputs_cache_dir,
            self.prompt_outputs_cache_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def task_layout(self, task_id: str) -> TaskLayout:
        normalized_task_id = _slugify(task_id)
        artifact_dir = self.tasks_dir / normalized_task_id
        workspace_dir = self.workspace_root / normalized_task_id
        return TaskLayout(
            task_id=normalized_task_id,
            artifact_dir=artifact_dir,
            workspace_dir=workspace_dir,
            repo_dir=workspace_dir / 'repo',
            iterations_dir=artifact_dir / 'iterations',
            summary_dir=artifact_dir / 'summary',
            logs_dir=artifact_dir / 'logs',
            solver_logs_dir=artifact_dir / 'logs' / 'solver',
            patch_logs_dir=artifact_dir / 'logs' / 'patches',
            error_logs_dir=artifact_dir / 'logs' / 'errors',
        )


def build_run_layout(
    mode: ExecutionMode,
    run_id: str | None = None,
    root: Path | None = None,
) -> RunLayout:
    repo_layout = RepositoryLayout.from_root(root)
    resolved_run_id = run_id or _default_run_id(mode)
    run_root = repo_layout.runs_dir / resolved_run_id
    workspace_root = repo_layout.workspaces_dir / resolved_run_id
    cache_root = repo_layout.cache_dir / resolved_run_id
    logs_dir = repo_layout.logs_dir / resolved_run_id
    return RunLayout(
        mode=mode,
        run_id=resolved_run_id,
        root=run_root,
        tasks_dir=run_root / 'tasks',
        workspace_root=workspace_root,
        logs_dir=logs_dir,
        run_log_path=logs_dir / 'run.log',
        error_log_path=logs_dir / 'error.log',
        cache_root=cache_root,
        retrieval_embeddings_cache_dir=cache_root / 'retrieval_embeddings',
        retrieved_context_cache_dir=cache_root / 'retrieved_context',
        solver_outputs_cache_dir=cache_root / 'solver_outputs',
        prompt_outputs_cache_dir=cache_root / 'prompt_outputs',
        metadata_path=run_root / 'run_metadata.json',
        summary_path=run_root / 'benchmark_summary.json',
    )
