from __future__ import annotations

import subprocess
from pathlib import Path

from symbiotic_swe.contracts import CanonicalTask, TaskMetadata
from symbiotic_swe.dataset.materialization import (
    MaterializeReposConfig,
    materialize_prepared_repos,
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _source_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / 'source'
    repo.mkdir()
    (repo / 'pkg.py').write_text('VALUE = 1\n', encoding='utf-8')
    _git(repo, 'init')
    _git(repo, 'config', 'user.email', 'fixture@example.com')
    _git(repo, 'config', 'user.name', 'Fixture User')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-m', 'fixture')
    return repo, _git(repo, 'rev-parse', 'HEAD')


def _write_task(prepared_dir: Path, commit: str) -> None:
    task_dir = prepared_dir / 'fixture__repo-1'
    task_dir.mkdir(parents=True)
    task = CanonicalTask(
        task_id='fixture__repo-1',
        repo='fixture/repo',
        repo_commit=commit,
        bug_description='demo bug',
        failing_tests=['tests/test_demo.py::test_demo'],
        metadata=TaskMetadata(dataset='synthetic', repo_name='repo'),
    )
    (task_dir / 'task.json').write_text(task.model_dump_json(indent=2), encoding='utf-8')


def test_materialize_prepared_repos_uses_existing_mirror_cache(tmp_path: Path) -> None:
    source, commit = _source_repo(tmp_path)
    prepared_dir = tmp_path / 'prepared' / 'smoke'
    _write_task(prepared_dir, commit)

    cache_dir = tmp_path / 'repo_cache'
    cache_dir.mkdir()
    subprocess.run(
        ['git', 'clone', '--mirror', str(source), str(cache_dir / 'fixture__repo.git')],
        check=True,
        capture_output=True,
        text=True,
    )

    result = materialize_prepared_repos(
        MaterializeReposConfig(
            prepared_dir=prepared_dir,
            repo_cache_dir=cache_dir,
            workspace_root=tmp_path / 'workspaces',
        )
    )

    workspace = tmp_path / 'workspaces' / 'fixture__repo-1' / 'repo'
    assert result.ok is True
    assert result.results[0].status == 'created'
    assert (workspace / '.git').exists()
    assert _git(workspace, 'rev-parse', 'HEAD') == commit
    assert (workspace / 'pkg.py').read_text(encoding='utf-8') == 'VALUE = 1\n'


def test_materialize_prepared_repos_reports_ready_workspace(tmp_path: Path) -> None:
    source, commit = _source_repo(tmp_path)
    prepared_dir = tmp_path / 'prepared' / 'smoke'
    _write_task(prepared_dir, commit)

    workspace = tmp_path / 'workspaces' / 'fixture__repo-1' / 'repo'
    workspace.parent.mkdir(parents=True)
    subprocess.run(['git', 'clone', str(source), str(workspace)], check=True, capture_output=True, text=True)

    result = materialize_prepared_repos(
        MaterializeReposConfig(
            prepared_dir=prepared_dir,
            repo_cache_dir=tmp_path / 'repo_cache',
            workspace_root=tmp_path / 'workspaces',
        )
    )

    assert result.ok is True
    assert result.results[0].status == 'ready'
