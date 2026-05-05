from dataclasses import dataclass

from symbiotic_swe import cli
from symbiotic_swe.cli import build_parser


@dataclass
class _TaskStub:
    task_id: str
    repo_path: str | None

    def model_copy(self, update: dict):
        return _TaskStub(
            task_id=update.get('task_id', self.task_id),
            repo_path=update.get('repo_path', self.repo_path),
        )


def test_cli_exposes_all_execution_modes() -> None:
    parser = build_parser()

    task_args = parser.parse_args(['task', '--task-id', 'demo-task'])
    smoke_args = parser.parse_args(['smoke'])
    benchmark_args = parser.parse_args(
        ['benchmark', '--task-id', 'bug-001', '--task-id', 'bug-002']
    )
    ablation_args = parser.parse_args(
        ['ablation', '--ablation-name', 'no-symbolic', '--task-id', 'bug-001']
    )
    materialize_args = parser.parse_args(['materialize-repos', '--task-id', 'bug-001'])

    assert task_args.command == 'task'
    assert smoke_args.command == 'smoke'
    assert smoke_args.task_ids is None
    assert benchmark_args.command == 'benchmark'
    assert benchmark_args.task_ids == ['bug-001', 'bug-002']
    assert ablation_args.command == 'ablation'
    assert materialize_args.command == 'materialize-repos'
    assert materialize_args.task_ids == ['bug-001']
    assert smoke_args.provider == 'openai'
    assert smoke_args.model == 'gpt-5.4-mini'


def test_cli_accepts_openai_provider_for_smoke() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            'smoke',
            '--preflight-only',
            '--provider',
            'openai',
            '--model',
            'gpt-5.5',
        ]
    )

    assert args.command == 'smoke'
    assert args.preflight_only is True
    assert args.provider == 'openai'
    assert args.model == 'gpt-5.5'


def test_prepared_task_path_repair_requires_git_checkout(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, '_project_root', lambda: tmp_path)
    local_repo = tmp_path / 'data' / 'prepared' / 'workspaces' / 'demo-task' / 'repo'
    local_repo.mkdir(parents=True)
    task = _TaskStub(task_id='demo-task', repo_path='/Users/teammate/project/workspace/repo')

    repaired = cli._repair_prepared_task_paths(task)

    assert repaired.repo_path == task.repo_path

    (local_repo / '.git').write_text('gitdir: ../.git/worktrees/demo-task\n', encoding='utf-8')
    repaired = cli._repair_prepared_task_paths(task)

    assert repaired.repo_path == str(local_repo)
