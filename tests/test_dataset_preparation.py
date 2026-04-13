from __future__ import annotations

import json
import subprocess
from pathlib import Path

from symbiotic_swe.dataset import (
    RepositoryIndexer,
    RepositoryIndexerConfig,
    TaskLoader,
    TaskLoaderConfig,
    TaskNormalizer,
    apply_patch_to_repository,
    build_repository_index,
    load_raw_swe_bench_tasks,
    materialize_repository_snapshot,
    prepare_swe_bench_tasks,
)
from symbiotic_swe.dataset.commands import main as dataset_main


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row) + '\n')


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _create_fixture_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / 'fixture_repo'
    repo.mkdir(parents=True, exist_ok=True)
    (repo / 'pkg').mkdir()
    (repo / 'tests').mkdir()
    (repo / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (repo / 'pkg' / 'logic.py').write_text(
        '\n'.join(
            [
                'def is_nonempty(values):',
                '    return len(values) > 0',
                '',
                'def sum_list(values):',
                '    return sum(values) / len(values)',
                '',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    (repo / 'tests' / 'test_logic.py').write_text(
        '\n'.join(
            [
                'from pkg.logic import is_nonempty, sum_list',
                '',
                'def test_is_nonempty_empty():',
                '    assert is_nonempty([]) is False',
                '',
                'def test_sum_list_empty():',
                '    assert sum_list([]) == 0',
                '',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    (repo / 'pkg' / 'broken.py').write_text(
        'def broken(:\n    return 1\n',
        encoding='utf-8',
    )

    _git(repo, 'init')
    _git(repo, 'config', 'user.email', 'fixture@example.com')
    _git(repo, 'config', 'user.name', 'Fixture User')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-m', 'fixture repo')
    return repo, _git(repo, 'rev-parse', 'HEAD')


def _valid_row(
    instance_id: str,
    repo: str,
    base_commit: str,
    problem_statement: str,
    patch: str,
) -> dict[str, object]:
    return {
        'instance_id': instance_id,
        'repo': repo,
        'base_commit': base_commit,
        'problem_statement': problem_statement,
        'FAIL_TO_PASS': '["tests/test_logic.py::test_bug"]',
        'PASS_TO_PASS': '["tests/test_logic.py::test_guard"]',
        'patch': patch,
        'test_patch': 'diff --git a/tests/test_logic.py b/tests/test_logic.py',
        'hints_text': '',
        'difficulty': '15 min - 1 hour',
        'constraint_spec': {
            'type': 'assertion',
            'expr': 'len(values) == 0 -> result == 0',
        },
    }


def test_load_raw_swe_bench_tasks_skips_malformed_rows(tmp_path: Path) -> None:
    input_path = tmp_path / 'raw.jsonl'
    _write_jsonl(
        input_path,
        [
            _valid_row(
                'sympy__sympy-1',
                'sympy/sympy',
                'deadbeef',
                'Incorrect edge case handling when the list is empty.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return sum(values) / len(values)',
                        '+    if len(values) == 0:',
                        '+        return 0',
                        '+    return sum(values) / len(values)',
                    ]
                ),
            ),
            {
                'instance_id': 'broken-task',
                'repo': 'sympy/sympy',
                'problem_statement': '',
                'FAIL_TO_PASS': '[]',
            },
        ],
    )

    raw_tasks, malformed = load_raw_swe_bench_tasks(input_path)

    assert len(raw_tasks) == 1
    assert raw_tasks[0].instance_id == 'sympy__sympy-1'
    assert raw_tasks[0].failing_tests == ('tests/test_logic.py::test_bug',)
    assert (
        raw_tasks[0].test_patch
        == 'diff --git a/tests/test_logic.py b/tests/test_logic.py'
    )
    assert len(malformed) == 1
    assert malformed[0].reason.startswith('missing_required_fields:')


def test_task_loader_component_loads_scores_and_selects(tmp_path: Path) -> None:
    input_path = tmp_path / 'raw.jsonl'
    _write_jsonl(
        input_path,
        [
            _valid_row(
                'sympy__sympy-1',
                'sympy/sympy',
                'deadbeef',
                'Incorrect edge case handling when the list is empty.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return sum(values) / len(values)',
                        '+    if len(values) == 0:',
                        '+        return 0',
                        '+    return sum(values) / len(values)',
                    ]
                ),
            ),
            _valid_row(
                'pandas__pandas-2',
                'pandas-dev/pandas',
                'deadbeef',
                'Function returns the wrong result for an empty frame boundary case.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return len(values) > 0',
                        '+    if len(values) == 0:',
                        '+        return False',
                        '+    return len(values) > 0',
                    ]
                ),
            ),
        ],
    )
    loader = TaskLoader(
        TaskLoaderConfig(
            repo_filter_mode='strict',
            smoke_count=1,
            dev_count=1,
            final_eval_count=0,
        )
    )

    raw_tasks, malformed = loader.load_raw_tasks(input_path)
    candidates = loader.score_tasks(raw_tasks)
    smoke_tasks, dev_tasks, final_eval_tasks, skipped = loader.select_subsets(
        candidates
    )

    assert len(raw_tasks) == 2
    assert malformed == []
    assert candidates[0].raw.instance_id == 'sympy__sympy-1'
    assert candidates[0].logic_heavy is True
    assert len(smoke_tasks) == 1
    assert len(dev_tasks) == 1
    assert final_eval_tasks == []
    assert skipped == []


def test_task_normalizer_component_creates_canonical_task() -> None:
    loader = TaskLoader(TaskLoaderConfig(repo_filter_mode='none'))
    normalizer = TaskNormalizer()
    raw_task, error = loader.validate_row(
        _valid_row(
            'sympy__sympy-1',
            'sympy/sympy',
            'deadbeef',
            'Incorrect edge case handling when the list is empty.',
            '\n'.join(
                [
                    'diff --git a/pkg/logic.py b/pkg/logic.py',
                    '--- a/pkg/logic.py',
                    '+++ b/pkg/logic.py',
                    '@@',
                    '-    return sum(values) / len(values)',
                    '+    if len(values) == 0:',
                    '+        return 0',
                    '+    return sum(values) / len(values)',
                ]
            ),
        ),
        row_number=1,
        input_path=Path('synthetic.jsonl'),
    )

    assert error is None
    assert raw_task is not None

    candidate = loader.score_task(raw_task)
    task = normalizer.normalize_task(candidate, 'smoke')

    assert task.task_id == 'sympy__sympy-1'
    assert task.repo == 'sympy/sympy'
    assert task.metadata.repo_name == 'sympy'
    assert task.metadata.logic_heavy is True
    assert task.metadata.bug_type is not None
    assert task.oracle is not None


def test_repository_indexer_component_prepares_canonical_task_artifact(
    tmp_path: Path,
) -> None:
    source_repo, commit = _create_fixture_repo(tmp_path)
    loader = TaskLoader(TaskLoaderConfig(repo_filter_mode='none'))
    normalizer = TaskNormalizer()
    indexer = RepositoryIndexer(
        RepositoryIndexerConfig(
            workspace_root=tmp_path / 'workspaces',
            cache_root=tmp_path / 'cache',
            repo_source_overrides={'sympy/sympy': source_repo},
        )
    )

    raw_task, error = loader.validate_row(
        _valid_row(
            'sympy__sympy-1',
            'sympy/sympy',
            commit,
            'Incorrect edge case handling when the list is empty.',
            '\n'.join(
                [
                    'diff --git a/pkg/logic.py b/pkg/logic.py',
                    '--- a/pkg/logic.py',
                    '+++ b/pkg/logic.py',
                    '@@',
                    '-    return sum(values) / len(values)',
                    '+    if len(values) == 0:',
                    '+        return 0',
                    '+    return sum(values) / len(values)',
                ]
            ),
        ),
        row_number=1,
        input_path=Path('synthetic.jsonl'),
    )

    assert error is None
    assert raw_task is not None

    candidate = loader.score_task(raw_task)
    normalized = normalizer.normalize_task(candidate, 'smoke')
    artifact = indexer.prepare_task(
        task=normalized,
        raw_task=raw_task,
        subset='smoke',
        output_dir=tmp_path / 'prepared_output',
        timestamp='2026-04-12T00:00:00+00:00',
    )

    assert artifact.status in {'valid', 'partial'}
    assert artifact.task.repo_path is not None
    assert artifact.task.metadata.preprocessing_timestamp == '2026-04-12T00:00:00+00:00'
    assert artifact.task.metadata.bug_report_path is not None
    assert artifact.task.metadata.failing_tests_path is not None
    assert artifact.task.metadata.oracle_path is not None
    assert artifact.task.metadata.repo_index_path is not None
    assert Path(artifact.artifact_dir or '').exists()
    assert Path(artifact.task.metadata.raw_fields_path or '').exists()


def test_dataset_command_normalize_one_writes_preview_artifacts(tmp_path: Path) -> None:
    input_path = tmp_path / 'raw.jsonl'
    output_dir = tmp_path / 'normalized_preview'
    _write_jsonl(
        input_path,
        [
            _valid_row(
                'sympy__sympy-1',
                'sympy/sympy',
                'deadbeef',
                'Incorrect edge case handling when the list is empty.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return sum(values) / len(values)',
                        '+    if len(values) == 0:',
                        '+        return 0',
                        '+    return sum(values) / len(values)',
                    ]
                ),
            )
        ],
    )

    exit_code = dataset_main(
        [
            'normalize-one',
            '--input-jsonl',
            str(input_path),
            '--task-id',
            'sympy__sympy-1',
            '--output-dir',
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / 'sympy__sympy-1.candidate.json').exists()
    assert (output_dir / 'sympy__sympy-1.normalized.json').exists()


def test_materialize_repository_snapshot_and_index_repository(tmp_path: Path) -> None:
    source_repo, commit = _create_fixture_repo(tmp_path)

    materialized = materialize_repository_snapshot(
        task_id='sympy__sympy-1',
        repo='sympy/sympy',
        requested_commit=commit,
        raw_fields={},
        workspace_root=tmp_path / 'workspaces',
        repo_source_overrides={'sympy/sympy': source_repo},
    )

    assert materialized.is_valid is True
    assert materialized.local_repo_path is not None
    assert materialized.resolved_commit == commit

    repo_index = build_repository_index(
        repo_path=Path(materialized.local_repo_path),
        repo='sympy/sympy',
        cache_root=tmp_path / 'cache',
    )

    assert Path(repo_index.index_path).exists()
    assert repo_index.source_file_count >= 1
    assert repo_index.test_file_count >= 1
    assert repo_index.parse_failure_count == 1

    cached_index = build_repository_index(
        repo_path=Path(materialized.local_repo_path),
        repo='sympy/sympy',
        cache_root=tmp_path / 'cache',
    )
    assert cached_index.cached is True


def test_apply_patch_to_repository_updates_fixture_repo(tmp_path: Path) -> None:
    source_repo, _commit = _create_fixture_repo(tmp_path)
    target_file = source_repo / 'pkg' / 'logic.py'
    original = target_file.read_text(encoding='utf-8')
    target_file.write_text(
        original.replace(
            'def sum_list(values):\n    return sum(values) / len(values)\n',
            'def sum_list(values):\n    if len(values) == 0:\n        return 0\n    return sum(values) / len(values)\n',
        ),
        encoding='utf-8',
    )
    patch_text = subprocess.run(
        ['git', 'diff'],
        cwd=source_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    _git(source_repo, 'checkout', '--', 'pkg/logic.py')

    result = apply_patch_to_repository(source_repo, patch_text)

    assert result.applied is True
    updated_source = (source_repo / 'pkg' / 'logic.py').read_text(encoding='utf-8')
    assert 'if len(values) == 0:' in updated_source


def test_prepare_swe_bench_tasks_materializes_repos_and_writes_reports(
    tmp_path: Path,
) -> None:
    source_repo, commit = _create_fixture_repo(tmp_path)
    input_path = tmp_path / 'verified.jsonl'
    output_dir = tmp_path / 'processed'
    _write_jsonl(
        input_path,
        [
            _valid_row(
                'sympy__sympy-1',
                'sympy/sympy',
                commit,
                'Incorrect edge case handling when the list is empty.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return sum(values) / len(values)',
                        '+    if len(values) == 0:',
                        '+        return 0',
                        '+    return sum(values) / len(values)',
                    ]
                ),
            ),
            _valid_row(
                'pandas__pandas-2',
                'pandas-dev/pandas',
                commit,
                'Function returns the wrong result for an empty frame boundary case.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return len(values) > 0',
                        '+    return len(values) >= 0',
                    ]
                ),
            ),
            _valid_row(
                'numpy__numpy-3',
                'numpy/numpy',
                commit,
                'Incorrect comparison logic for a boundary condition.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return len(values) > 0',
                        '+    return len(values) >= 0',
                    ]
                ),
            ),
            _valid_row(
                'matplotlib__matplotlib-4',
                'matplotlib/matplotlib',
                commit,
                'Assertion failure caused by wrong conditional logic in rendering.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return len(values) > 0',
                        '+    return len(values) >= 0',
                    ]
                ),
            ),
            _valid_row(
                'sklearn__sklearn-5',
                'scikit-learn/scikit-learn',
                commit,
                'Boundary validation bug.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return len(values) > 0',
                        '+    return len(values) >= 0',
                    ]
                ),
            ),
            _valid_row(
                'sympy__sympy-missing-source',
                'sympy/sympy',
                commit,
                'Same bug, but the repo source mapping is missing on purpose.',
                '\n'.join(
                    [
                        'diff --git a/pkg/logic.py b/pkg/logic.py',
                        '--- a/pkg/logic.py',
                        '+++ b/pkg/logic.py',
                        '@@',
                        '-    return len(values) > 0',
                        '+    return len(values) >= 0',
                    ]
                ),
            ),
            {
                'instance_id': 'broken-task',
                'repo': 'sympy/sympy',
                'base_commit': '',
                'problem_statement': 'Missing required fields should be logged.',
                'FAIL_TO_PASS': '[]',
            },
        ],
    )

    result = prepare_swe_bench_tasks(
        input_path=input_path,
        output_dir=output_dir,
        smoke_count=1,
        dev_count=1,
        final_eval_count=3,
        repo_filter_mode='strict',
        repo_source_overrides={
            'sympy/sympy': source_repo,
            'pandas-dev/pandas': source_repo,
            'numpy/numpy': source_repo,
            'matplotlib/matplotlib': source_repo,
        },
        workspace_root=tmp_path / 'workspaces',
        cache_root=tmp_path / 'cache',
    )

    assert len(result.raw_tasks) == 6
    assert len(result.malformed_tasks) == 1
    assert len(result.repo_failures) == 1
    assert len(result.smoke_tasks) == 1
    assert len(result.dev_tasks) == 1
    assert len(result.final_eval_tasks) == 2

    smoke_task = result.smoke_tasks[0].task
    assert smoke_task.repo_path is not None
    assert smoke_task.metadata.status in {'valid', 'partial'}
    assert smoke_task.metadata.repo_index_path is not None
    assert smoke_task.metadata.bug_report_path is not None
    assert smoke_task.metadata.failing_tests_path is not None
    assert smoke_task.metadata.oracle_path is not None
    assert smoke_task.oracle is not None
    assert isinstance(smoke_task.oracle.spec, dict)
    assert 'gold_patch' in smoke_task.oracle.spec
    assert 'test_patch' in smoke_task.oracle.spec
    assert 'constraint_spec' in smoke_task.oracle.spec

    prepared_task_path = (
        output_dir / 'prepared' / 'smoke' / smoke_task.task_id / 'task.json'
    )
    dataset_manifest = output_dir / 'manifests' / 'dataset_manifest.jsonl'
    materialization_failures = output_dir / 'logs' / 'materialization_failures.jsonl'
    parse_failures = output_dir / 'logs' / 'repo_parse_failures.jsonl'
    summary_report = output_dir / 'reproducibility_summary.json'
    prep_report = output_dir / 'task_preparation_report.json'

    assert prepared_task_path.exists()
    assert dataset_manifest.exists()
    assert materialization_failures.exists()
    assert parse_failures.exists()
    assert summary_report.exists()
    assert prep_report.exists()

    report = json.loads(prep_report.read_text(encoding='utf-8'))
    assert report['repo_failures'] == 1
    assert report['tasks_loaded'] == 6
    assert report['malformed_task_count'] == 1
    assert report['status_counts']['partial'] >= 1
