from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from symbiotic_swe.contracts import CanonicalTask


@dataclass
class MaterializeReposConfig:
    prepared_dir: Path
    repo_cache_dir: Path
    workspace_root: Path
    task_ids: set[str] | None = None
    fetch: bool = False
    force: bool = False
    dry_run: bool = False


@dataclass
class MaterializedTaskResult:
    task_id: str
    repo: str
    commit: str
    workspace_path: Path
    status: str
    message: str = ''


@dataclass
class MaterializeReposResult:
    results: list[MaterializedTaskResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(result.status == 'failed' for result in self.results)

    @property
    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return counts


def _run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['git', *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _git(args: list[str], cwd: Path | None = None) -> str:
    result = _run_git(args, cwd)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or f'git {" ".join(args)} failed')
    return result.stdout.strip()


def _safe_repo_cache_name(repo: str) -> str:
    return repo.replace('/', '__') + '.git'


def _load_prepared_tasks(prepared_dir: Path, task_ids: set[str] | None = None) -> list[CanonicalTask]:
    tasks: list[CanonicalTask] = []
    for task_json in sorted(prepared_dir.rglob('task.json')):
        task = CanonicalTask(**json.loads(task_json.read_text(encoding='utf-8')))
        if task_ids is None or task.task_id in task_ids:
            tasks.append(task)
    return tasks


def _workspace_path(config: MaterializeReposConfig, task: CanonicalTask) -> Path:
    return config.workspace_root / task.task_id / 'repo'


def _mirror_path(config: MaterializeReposConfig, repo: str) -> Path:
    return config.repo_cache_dir / _safe_repo_cache_name(repo)


def _is_git_checkout(path: Path) -> bool:
    return (path / '.git').exists()


def _checkout_head(path: Path) -> str | None:
    if not _is_git_checkout(path):
        return None
    result = _run_git(['rev-parse', 'HEAD'], cwd=path)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _is_empty_dir(path: Path) -> bool:
    return path.is_dir() and not any(path.iterdir())


def _ensure_mirror(config: MaterializeReposConfig, repo: str) -> tuple[bool, str]:
    mirror = _mirror_path(config, repo)
    clone_url = f'https://github.com/{repo}.git'

    if mirror.exists():
        if not (mirror / 'HEAD').exists():
            return False, f'cache exists but is not a bare git mirror: {mirror}'
        if config.fetch:
            if config.dry_run:
                return True, f'would fetch mirror {mirror}'
            _git(['--git-dir', str(mirror), 'fetch', '--prune', 'origin'])
            return True, f'fetched mirror {mirror}'
        return True, f'using mirror {mirror}'

    if config.dry_run:
        return True, f'would clone mirror {clone_url} -> {mirror}'

    mirror.parent.mkdir(parents=True, exist_ok=True)
    result = _run_git(['clone', '--mirror', clone_url, str(mirror)])
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        return False, f'clone mirror failed: {detail}'
    return True, f'cloned mirror {mirror}'


def _remove_if_safe(path: Path, *, force: bool) -> bool:
    if not path.exists():
        return True
    if _is_empty_dir(path):
        path.rmdir()
        return True
    if force:
        shutil.rmtree(path)
        return True
    return False


def _ensure_workspace(config: MaterializeReposConfig, task: CanonicalTask) -> MaterializedTaskResult:
    workspace = _workspace_path(config, task)
    current_head = _checkout_head(workspace)
    if current_head == task.repo_commit:
        return MaterializedTaskResult(
            task_id=task.task_id,
            repo=task.repo,
            commit=task.repo_commit,
            workspace_path=workspace,
            status='ready',
            message='workspace already at requested commit',
        )

    if current_head and current_head != task.repo_commit and not config.force:
        return MaterializedTaskResult(
            task_id=task.task_id,
            repo=task.repo,
            commit=task.repo_commit,
            workspace_path=workspace,
            status='failed',
            message=(
                f'workspace exists at {current_head}; rerun with --force to replace it '
                f'with {task.repo_commit}'
            ),
        )

    mirror_ok, mirror_message = _ensure_mirror(config, task.repo)
    if not mirror_ok:
        return MaterializedTaskResult(
            task_id=task.task_id,
            repo=task.repo,
            commit=task.repo_commit,
            workspace_path=workspace,
            status='failed',
            message=mirror_message,
        )

    if config.dry_run:
        return MaterializedTaskResult(
            task_id=task.task_id,
            repo=task.repo,
            commit=task.repo_commit,
            workspace_path=workspace,
            status='planned',
            message=f'{mirror_message}; would materialize workspace',
        )

    if not _remove_if_safe(workspace, force=config.force):
        return MaterializedTaskResult(
            task_id=task.task_id,
            repo=task.repo,
            commit=task.repo_commit,
            workspace_path=workspace,
            status='failed',
            message=f'workspace exists and is not empty: {workspace}; rerun with --force',
        )

    workspace.parent.mkdir(parents=True, exist_ok=True)
    mirror = _mirror_path(config, task.repo)
    result = _run_git([
        '--git-dir',
        str(mirror),
        'worktree',
        'add',
        '--detach',
        str(workspace),
        task.repo_commit,
    ])
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        return MaterializedTaskResult(
            task_id=task.task_id,
            repo=task.repo,
            commit=task.repo_commit,
            workspace_path=workspace,
            status='failed',
            message=f'worktree add failed: {detail}',
        )

    return MaterializedTaskResult(
        task_id=task.task_id,
        repo=task.repo,
        commit=task.repo_commit,
        workspace_path=workspace,
        status='created',
        message=mirror_message,
    )


def materialize_prepared_repos(config: MaterializeReposConfig) -> MaterializeReposResult:
    tasks = _load_prepared_tasks(config.prepared_dir, config.task_ids)
    result = MaterializeReposResult()

    for task in tasks:
        result.results.append(_ensure_workspace(config, task))

    return result


def iter_unique_repos(tasks: Iterable[CanonicalTask]) -> list[str]:
    return sorted({task.repo for task in tasks})
