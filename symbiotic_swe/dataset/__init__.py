from __future__ import annotations

import ast
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from src.dataset.task_loader import (
    PREFERRED_REPOS,
    CandidateTask,
    RawTaskError,
    TaskLoader as BaseTaskLoader,
    TaskLoaderConfig as BaseTaskLoaderConfig,
    TaskObject,
    balanced_take,
    changed_files,
    count_changed_lines,
    label_task,
    parse_test_list,
    score_candidate,
)


@dataclass(frozen=True)
class TaskLoaderConfig:
    dataset_name: str = 'SWE-bench Verified'
    split: str = 'test'
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS
    repo_filter_mode: str = 'preferred'
    smoke_count: int = 5
    dev_count: int = 10
    final_eval_count: int = 30
    max_changed_lines: int = 30
    max_changed_files: int = 3
    min_logic_score: int = 6


class TaskLoader:
    def __init__(self, config: TaskLoaderConfig | None = None) -> None:
        self.config = config or TaskLoaderConfig()
        self._base = BaseTaskLoader(
            BaseTaskLoaderConfig(
                dataset_name=self.config.dataset_name,
                split=self.config.split,
                preferred_repos=self.config.preferred_repos,
                repo_filter_mode=self.config.repo_filter_mode,
                smoke_count=self.config.smoke_count,
                core_count=self.config.dev_count + self.config.final_eval_count,
                max_changed_lines=self.config.max_changed_lines,
                max_changed_files=self.config.max_changed_files,
                min_logic_score=self.config.min_logic_score,
            )
        )

    def validate_row(
        self,
        row: dict[str, Any],
        row_number: int,
        input_path: Path,
    ) -> tuple[TaskObject | None, RawTaskError | None]:
        return self._base.validate_row(row, row_number, input_path)

    def load_raw_tasks(self, input_path: Path) -> tuple[list[TaskObject], list[RawTaskError]]:
        return self._base.load_raw_tasks(input_path)

    def score_task(self, task: TaskObject) -> CandidateTask:
        return score_candidate(
            task=task,
            preferred_repos=self.config.preferred_repos,
            repo_filter_mode=self.config.repo_filter_mode,
            max_changed_lines=self.config.max_changed_lines,
            max_changed_files=self.config.max_changed_files,
            min_logic_score=self.config.min_logic_score,
        )

    def score_tasks(self, tasks: list[TaskObject]) -> list[CandidateTask]:
        return [self.score_task(task) for task in tasks]

    def select_subsets(
        self,
        candidates: list[CandidateTask],
    ) -> tuple[list[CandidateTask], list[CandidateTask], list[CandidateTask], list[CandidateTask]]:
        usable = sorted(
            [candidate for candidate in candidates if candidate.logic_heavy and not candidate.exclusion_reasons],
            key=lambda candidate: (-candidate.score, candidate.changed_lines, candidate.raw.repo, candidate.raw.instance_id),
        )
        skipped = sorted(
            [candidate for candidate in candidates if candidate.exclusion_reasons],
            key=lambda candidate: (-candidate.score, candidate.changed_lines, candidate.raw.repo, candidate.raw.instance_id),
        )

        smoke_pool = [candidate for candidate in usable if candidate.include_for_smoke]
        smoke_tasks = balanced_take(smoke_pool, self.config.smoke_count, self.config.preferred_repos)
        used_ids = {candidate.raw.instance_id for candidate in smoke_tasks}

        remaining = [candidate for candidate in usable if candidate.raw.instance_id not in used_ids]
        dev_tasks = balanced_take(remaining, self.config.dev_count, self.config.preferred_repos)
        used_ids.update(candidate.raw.instance_id for candidate in dev_tasks)

        final_pool = [candidate for candidate in remaining if candidate.raw.instance_id not in used_ids]
        final_eval_tasks = balanced_take(final_pool, self.config.final_eval_count, self.config.preferred_repos)
        return smoke_tasks, dev_tasks, final_eval_tasks, skipped


@dataclass(frozen=True)
class TaskMetadata:
    repo_name: str
    subset: str
    score: int
    changed_lines: int
    changed_files: tuple[str, ...]
    labels: tuple[str, ...]
    logic_heavy: bool
    bug_type: str | None
    status: str = 'normalized'
    preprocessing_timestamp: str | None = None
    bug_report_path: str | None = None
    failing_tests_path: str | None = None
    oracle_path: str | None = None
    repo_index_path: str | None = None
    raw_fields_path: str | None = None


@dataclass(frozen=True)
class TaskOracle:
    failing_tests: tuple[str, ...]
    passing_tests: tuple[str, ...]
    spec: dict[str, Any]


@dataclass(frozen=True)
class NormalizedTask:
    task_id: str
    repo: str
    base_commit: str
    problem_statement: str
    repo_path: str | None
    metadata: TaskMetadata
    oracle: TaskOracle | None


class TaskNormalizer:
    def normalize_task(self, candidate: CandidateTask, subset: str) -> NormalizedTask:
        raw = candidate.raw
        repo_name = raw.repo.split('/')[-1]
        bug_type = candidate.labels[0] if candidate.labels else None
        return NormalizedTask(
            task_id=raw.instance_id,
            repo=raw.repo,
            base_commit=raw.base_commit,
            problem_statement=raw.problem_statement,
            repo_path=None,
            metadata=TaskMetadata(
                repo_name=repo_name,
                subset=subset,
                score=candidate.score,
                changed_lines=candidate.changed_lines,
                changed_files=candidate.changed_files,
                labels=candidate.labels,
                logic_heavy=candidate.logic_heavy,
                bug_type=bug_type,
            ),
            oracle=TaskOracle(
                failing_tests=raw.failing_tests,
                passing_tests=raw.passing_tests,
                spec={
                    'gold_patch': raw.patch,
                    'test_patch': raw.test_patch,
                    'constraint_spec': raw.constraint_spec,
                },
            ),
        )


@dataclass(frozen=True)
class PatchApplyResult:
    applied: bool
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class MaterializedRepository:
    is_valid: bool
    local_repo_path: str | None
    resolved_commit: str | None
    error: str | None = None


@dataclass(frozen=True)
class RepositoryIndex:
    index_path: str
    source_file_count: int
    test_file_count: int
    parse_failure_count: int
    cached: bool = False


@dataclass(frozen=True)
class RepositoryIndexerConfig:
    workspace_root: Path
    cache_root: Path
    repo_source_overrides: dict[str, Path] = field(default_factory=dict)


@dataclass(frozen=True)
class PreparedTaskArtifact:
    task: NormalizedTask
    status: str
    artifact_dir: str | None
    error: str | None = None


@dataclass(frozen=True)
class DatasetPreparationResult:
    raw_tasks: tuple[TaskObject, ...]
    malformed_tasks: tuple[RawTaskError, ...]
    repo_failures: tuple[PreparedTaskArtifact, ...]
    smoke_tasks: tuple[PreparedTaskArtifact, ...]
    dev_tasks: tuple[PreparedTaskArtifact, ...]
    final_eval_tasks: tuple[PreparedTaskArtifact, ...]


def _run_git(cwd: Path | None, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)


def _slug_repo(repo: str) -> str:
    return repo.replace('/', '__')


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(_jsonable(row), sort_keys=True) + '\n')


def _task_to_dict(task: NormalizedTask) -> dict[str, Any]:
    return cast(dict[str, Any], _jsonable(asdict(task)))


def _replace_task_metadata(task: NormalizedTask, **updates: Any) -> NormalizedTask:
    metadata_values = asdict(task.metadata)
    repo_path = updates.pop('repo_path', task.repo_path)
    metadata_values.update(updates)
    return NormalizedTask(
        task_id=task.task_id,
        repo=task.repo,
        base_commit=task.base_commit,
        problem_statement=task.problem_statement,
        repo_path=repo_path,
        metadata=TaskMetadata(**metadata_values),
        oracle=task.oracle,
    )


def load_raw_swe_bench_tasks(
    input_path: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
) -> tuple[list[TaskObject], list[RawTaskError]]:
    loader = TaskLoader(TaskLoaderConfig(dataset_name=dataset_name, split=split))
    return loader.load_raw_tasks(input_path)


def apply_patch_to_repository(repo_path: Path, patch_text: str) -> PatchApplyResult:
    result = subprocess.run(
        ['git', 'apply', '--whitespace=nowarn', '-'],
        cwd=repo_path,
        input=patch_text,
        capture_output=True,
        text=True,
    )
    return PatchApplyResult(
        applied=result.returncode == 0,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def materialize_repository_snapshot(
    task_id: str,
    repo: str,
    requested_commit: str,
    raw_fields: dict[str, Any],
    workspace_root: Path,
    repo_source_overrides: dict[str, Path],
) -> MaterializedRepository:
    del raw_fields
    source_repo = repo_source_overrides.get(repo)
    if source_repo is None:
        return MaterializedRepository(False, None, None, f'missing_repo_source_override:{repo}')

    target = workspace_root / task_id / _slug_repo(repo)
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    clone_result = _run_git(None, 'clone', str(source_repo), str(target))
    if clone_result.returncode != 0:
        return MaterializedRepository(False, None, None, clone_result.stderr.strip())

    checkout_result = _run_git(target, 'checkout', requested_commit)
    if checkout_result.returncode != 0:
        return MaterializedRepository(False, str(target), None, checkout_result.stderr.strip())

    rev_parse = _run_git(target, 'rev-parse', 'HEAD')
    if rev_parse.returncode != 0:
        return MaterializedRepository(False, str(target), None, rev_parse.stderr.strip())
    return MaterializedRepository(True, str(target), rev_parse.stdout.strip())


def build_repository_index(repo_path: Path, repo: str, cache_root: Path) -> RepositoryIndex:
    index_dir = cache_root / 'repo_indexes'
    index_path = index_dir / f'{_slug_repo(repo)}_{repo_path.resolve().name}.json'
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding='utf-8'))
        return RepositoryIndex(
            index_path=str(index_path),
            source_file_count=int(payload['source_file_count']),
            test_file_count=int(payload['test_file_count']),
            parse_failure_count=int(payload['parse_failure_count']),
            cached=True,
        )

    source_files = []
    test_files = []
    parse_failures = []
    for path in sorted(repo_path.rglob('*.py')):
        relative = path.relative_to(repo_path).as_posix()
        if relative.startswith('.git/'):
            continue
        if relative.startswith('tests/') or '/tests/' in relative or path.name.startswith('test_'):
            test_files.append(relative)
        else:
            source_files.append(relative)
        try:
            ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError as exc:
            parse_failures.append({'path': relative, 'message': str(exc)})

    payload = {
        'repo': repo,
        'repo_path': str(repo_path),
        'source_files': source_files,
        'test_files': test_files,
        'parse_failures': parse_failures,
        'source_file_count': len(source_files),
        'test_file_count': len(test_files),
        'parse_failure_count': len(parse_failures),
    }
    _write_json(index_path, payload)
    return RepositoryIndex(
        index_path=str(index_path),
        source_file_count=len(source_files),
        test_file_count=len(test_files),
        parse_failure_count=len(parse_failures),
        cached=False,
    )


class RepositoryIndexer:
    def __init__(self, config: RepositoryIndexerConfig) -> None:
        self.config = config

    def prepare_task(
        self,
        task: NormalizedTask,
        raw_task: TaskObject,
        subset: str,
        output_dir: Path,
        timestamp: str,
    ) -> PreparedTaskArtifact:
        artifact_dir = output_dir / 'prepared' / subset / task.task_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        materialized = materialize_repository_snapshot(
            task_id=task.task_id,
            repo=task.repo,
            requested_commit=task.base_commit,
            raw_fields=raw_task.raw_fields,
            workspace_root=self.config.workspace_root,
            repo_source_overrides=self.config.repo_source_overrides,
        )
        if not materialized.is_valid or materialized.local_repo_path is None:
            failed_task = _replace_task_metadata(task, status='failed', preprocessing_timestamp=timestamp)
            return PreparedTaskArtifact(failed_task, 'failed', str(artifact_dir), materialized.error)

        repo_index = build_repository_index(
            repo_path=Path(materialized.local_repo_path),
            repo=task.repo,
            cache_root=self.config.cache_root,
        )

        bug_report_path = artifact_dir / 'bug_report.md'
        failing_tests_path = artifact_dir / 'failing_tests.json'
        oracle_path = artifact_dir / 'oracle.json'
        raw_fields_path = artifact_dir / 'raw_fields.json'
        task_path = artifact_dir / 'task.json'

        bug_report_path.write_text(raw_task.problem_statement + '\n', encoding='utf-8')
        _write_json(failing_tests_path, {'FAIL_TO_PASS': list(raw_task.failing_tests)})
        _write_json(
            oracle_path,
            {
                'gold_patch': raw_task.patch,
                'test_patch': raw_task.test_patch,
                'constraint_spec': raw_task.constraint_spec,
            },
        )
        _write_json(raw_fields_path, raw_task.raw_fields)

        status = 'partial' if repo_index.parse_failure_count else 'valid'
        prepared_task = _replace_task_metadata(
            task,
            status=status,
            preprocessing_timestamp=timestamp,
            bug_report_path=str(bug_report_path),
            failing_tests_path=str(failing_tests_path),
            oracle_path=str(oracle_path),
            repo_index_path=repo_index.index_path,
            raw_fields_path=str(raw_fields_path),
            repo_path=materialized.local_repo_path,
        )
        _write_json(task_path, _task_to_dict(prepared_task))
        return PreparedTaskArtifact(prepared_task, status, str(artifact_dir))


def _candidate_to_json(candidate: CandidateTask) -> dict[str, Any]:
    return {
        'task_id': candidate.raw.instance_id,
        'repo': candidate.raw.repo,
        'score': candidate.score,
        'changed_lines': candidate.changed_lines,
        'changed_files': list(candidate.changed_files),
        'labels': list(candidate.labels),
        'logic_heavy': candidate.logic_heavy,
        'include_for_smoke': candidate.include_for_smoke,
        'exclusion_reasons': list(candidate.exclusion_reasons),
    }


def prepare_swe_bench_tasks(
    input_path: Path,
    output_dir: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    smoke_count: int = 5,
    dev_count: int = 10,
    final_eval_count: int = 30,
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
    repo_source_overrides: dict[str, Path] | None = None,
    workspace_root: Path | None = None,
    cache_root: Path | None = None,
) -> DatasetPreparationResult:
    timestamp = datetime.now(tz=UTC).isoformat()
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
    raw_tasks, malformed_tasks = loader.load_raw_tasks(input_path)
    candidates = loader.score_tasks(raw_tasks)
    smoke_candidates, dev_candidates, final_candidates, skipped = loader.select_subsets(candidates)
    del skipped

    normalizer = TaskNormalizer()
    indexer = RepositoryIndexer(
        RepositoryIndexerConfig(
            workspace_root=workspace_root or output_dir / 'workspaces',
            cache_root=cache_root or output_dir / 'cache',
            repo_source_overrides=repo_source_overrides or {},
        )
    )

    repo_failures: list[PreparedTaskArtifact] = []

    def prepare_many(selected: list[CandidateTask], subset: str) -> list[PreparedTaskArtifact]:
        prepared: list[PreparedTaskArtifact] = []
        for candidate in selected:
            task = normalizer.normalize_task(candidate, subset)
            artifact = indexer.prepare_task(task, candidate.raw, subset, output_dir, timestamp)
            if artifact.status == 'failed':
                repo_failures.append(artifact)
            else:
                prepared.append(artifact)
        return prepared

    smoke_tasks = prepare_many(smoke_candidates, 'smoke')
    dev_tasks = prepare_many(dev_candidates, 'dev')
    final_eval_tasks = prepare_many(final_candidates, 'final_eval')

    manifest_rows = [
        {'subset': subset, 'task_id': artifact.task.task_id, 'status': artifact.status, 'artifact_dir': artifact.artifact_dir}
        for subset, artifacts in (
            ('smoke', smoke_tasks),
            ('dev', dev_tasks),
            ('final_eval', final_eval_tasks),
        )
        for artifact in artifacts
    ]
    _write_jsonl(output_dir / 'manifests' / 'dataset_manifest.jsonl', manifest_rows)
    _write_jsonl(
        output_dir / 'logs' / 'materialization_failures.jsonl',
        [{'task_id': artifact.task.task_id, 'repo': artifact.task.repo, 'error': artifact.error} for artifact in repo_failures],
    )

    parse_failure_rows = []
    for artifact in [*smoke_tasks, *dev_tasks, *final_eval_tasks]:
        if artifact.task.metadata.status == 'partial':
            parse_failure_rows.append(
                {
                    'task_id': artifact.task.task_id,
                    'repo_index_path': artifact.task.metadata.repo_index_path,
                }
            )
    _write_jsonl(output_dir / 'logs' / 'repo_parse_failures.jsonl', parse_failure_rows)

    _write_json(
        output_dir / 'task_preparation_report.json',
        {
            'tasks_loaded': len(raw_tasks),
            'malformed_task_count': len(malformed_tasks),
            'repo_failures': len(repo_failures),
            'smoke_tasks': len(smoke_tasks),
            'dev_tasks': len(dev_tasks),
            'final_eval_tasks': len(final_eval_tasks),
            'status_counts': {
                'valid': sum(1 for artifact in [*smoke_tasks, *dev_tasks, *final_eval_tasks] if artifact.status == 'valid'),
                'partial': sum(1 for artifact in [*smoke_tasks, *dev_tasks, *final_eval_tasks] if artifact.status == 'partial'),
                'failed': len(repo_failures),
            },
        },
    )
    _write_json(
        output_dir / 'reproducibility_summary.json',
        {
            'input_path': str(input_path),
            'timestamp': timestamp,
            'dataset_name': dataset_name,
            'split': split,
            'repo_filter_mode': repo_filter_mode,
        },
    )

    return DatasetPreparationResult(
        raw_tasks=tuple(raw_tasks),
        malformed_tasks=tuple(malformed_tasks),
        repo_failures=tuple(repo_failures),
        smoke_tasks=tuple(smoke_tasks),
        dev_tasks=tuple(dev_tasks),
        final_eval_tasks=tuple(final_eval_tasks),
    )


__all__ = [
    'PREFERRED_REPOS',
    'CandidateTask',
    'DatasetPreparationResult',
    'MaterializedRepository',
    'NormalizedTask',
    'PatchApplyResult',
    'PreparedTaskArtifact',
    'RawTaskError',
    'RepositoryIndex',
    'RepositoryIndexer',
    'RepositoryIndexerConfig',
    'TaskLoader',
    'TaskLoaderConfig',
    'TaskNormalizer',
    'TaskObject',
    'apply_patch_to_repository',
    'build_repository_index',
    'changed_files',
    'count_changed_lines',
    'label_task',
    'load_raw_swe_bench_tasks',
    'materialize_repository_snapshot',
    'parse_test_list',
    'prepare_swe_bench_tasks',
]
