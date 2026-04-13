from __future__ import annotations

import ast
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.contracts import TaskContract
from src.dataset.task_loader import RawTaskDefinition


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


@dataclass(frozen=True)
class MaterializationResult:
    task_id: str
    repo: str
    source_repo_path: str | None
    local_repo_path: str | None
    requested_commit: str | None
    resolved_commit: str | None
    checkout_succeeded: bool
    source_file_count: int
    test_file_count: int
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return (
            self.error is None
            and self.local_repo_path is not None
            and self.checkout_succeeded
            and self.source_file_count > 0
            and self.test_file_count > 0
        )


@dataclass(frozen=True)
class PatchApplyResult:
    repo_path: str
    applied: bool
    patch_path: str
    error: str | None = None


@dataclass(frozen=True)
class RepositoryIndexResult:
    repo_path: str
    cache_dir: str
    index_path: str
    cached: bool
    file_count: int
    source_file_count: int
    test_file_count: int
    parse_failure_count: int
    parse_failures: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class PreparedTaskArtifact:
    subset: str
    task: TaskContract
    raw_definition: RawTaskDefinition
    status: str
    materialization: MaterializationResult
    repo_index: RepositoryIndexResult | None
    artifact_dir: str | None


@dataclass(frozen=True)
class RepositoryIndexerConfig:
    workspace_root: Path
    cache_root: Path
    repo_source_root: Path | None = None
    repo_source_overrides: dict[str, Path] | None = None


def _repo_slug(repo: str) -> str:
    return repo.replace('/', '__')


def _task_slug(task_id: str) -> str:
    return task_id.replace('/', '__')


def _candidate_source_paths(
    repo: str,
    raw_fields: dict[str, Any],
    repo_source_root: Path | None,
    repo_source_overrides: dict[str, Path] | None,
) -> list[Path]:
    candidates: list[Path] = []
    raw_repo_source = raw_fields.get('repo_source')
    if isinstance(raw_repo_source, str) and raw_repo_source.strip():
        candidates.append(Path(raw_repo_source).expanduser())
    if repo_source_overrides is not None and repo in repo_source_overrides:
        candidates.append(repo_source_overrides[repo])
    if repo_source_root is not None:
        candidates.extend(
            [
                repo_source_root / repo,
                repo_source_root / _repo_slug(repo),
                repo_source_root / repo.split('/')[-1],
            ]
        )
    return candidates


def resolve_repository_source(
    repo: str,
    raw_fields: dict[str, Any],
    repo_source_root: Path | None = None,
    repo_source_overrides: dict[str, Path] | None = None,
) -> Path | None:
    for candidate in _candidate_source_paths(
        repo,
        raw_fields,
        repo_source_root,
        repo_source_overrides,
    ):
        expanded = candidate.expanduser().resolve()
        if expanded.exists():
            return expanded
    return None


def _is_git_repo(path: Path) -> bool:
    return (path / '.git').exists()


def _run_git(repo_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['git', *args],
        cwd=repo_path,
        check=False,
        capture_output=True,
        text=True,
    )


def _python_files(repo_path: Path) -> list[Path]:
    return sorted(
        path
        for path in repo_path.rglob('*.py')
        if '.git' not in path.parts and '__pycache__' not in path.parts
    )


def _is_test_file(path: Path, repo_path: Path) -> bool:
    relative = path.relative_to(repo_path)
    return 'tests' in relative.parts or relative.name.startswith('test_')


def persist_validation_signals(
    raw_task: RawTaskDefinition,
    task_dir: Path,
) -> dict[str, str]:
    bug_report_path = task_dir / 'bug_report.txt'
    failing_tests_path = task_dir / 'failing_tests.json'
    execution_trace_path = task_dir / 'execution_trace.json'
    oracle_path = task_dir / 'oracle.json'

    bug_report_path.write_text(raw_task.problem_statement + '\n', encoding='utf-8')
    _write_json(
        failing_tests_path,
        {
            'fail_to_pass': list(raw_task.failing_tests),
            'pass_to_pass': list(raw_task.passing_tests),
        },
    )
    _write_json(
        execution_trace_path, {'execution_trace': list(raw_task.execution_trace)}
    )
    _write_json(
        oracle_path,
        {
            'gold_patch': raw_task.patch,
            'test_patch': raw_task.test_patch,
            'constraint_spec': raw_task.constraint_spec,
        },
    )
    return {
        'bug_report_path': str(bug_report_path),
        'failing_tests_path': str(failing_tests_path),
        'execution_trace_path': str(execution_trace_path),
        'oracle_path': str(oracle_path),
    }


def materialize_repository_snapshot(
    task_id: str,
    repo: str,
    requested_commit: str | None,
    raw_fields: dict[str, Any],
    workspace_root: Path,
    repo_source_root: Path | None = None,
    repo_source_overrides: dict[str, Path] | None = None,
) -> MaterializationResult:
    source_repo_path = resolve_repository_source(
        repo,
        raw_fields,
        repo_source_root=repo_source_root,
        repo_source_overrides=repo_source_overrides,
    )
    if source_repo_path is None:
        return MaterializationResult(
            task_id=task_id,
            repo=repo,
            source_repo_path=None,
            local_repo_path=None,
            requested_commit=requested_commit,
            resolved_commit=None,
            checkout_succeeded=False,
            source_file_count=0,
            test_file_count=0,
            error='repository_source_not_found',
        )

    task_workspace = workspace_root / _task_slug(task_id)
    local_repo_path = task_workspace / 'repo'
    if local_repo_path.exists():
        shutil.rmtree(local_repo_path)
    task_workspace.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_repo_path, local_repo_path)

    checkout_succeeded = True
    resolved_commit: str | None = None
    if _is_git_repo(local_repo_path):
        if requested_commit:
            checkout = _run_git(
                local_repo_path, 'checkout', '--detach', requested_commit
            )
            checkout_succeeded = checkout.returncode == 0
            if not checkout_succeeded:
                return MaterializationResult(
                    task_id=task_id,
                    repo=repo,
                    source_repo_path=str(source_repo_path),
                    local_repo_path=str(local_repo_path),
                    requested_commit=requested_commit,
                    resolved_commit=None,
                    checkout_succeeded=False,
                    source_file_count=0,
                    test_file_count=0,
                    error=f'checkout_failed:{checkout.stderr.strip() or checkout.stdout.strip()}',
                )
        head = _run_git(local_repo_path, 'rev-parse', 'HEAD')
        if head.returncode == 0:
            resolved_commit = head.stdout.strip()
    elif requested_commit:
        checkout_succeeded = False
        return MaterializationResult(
            task_id=task_id,
            repo=repo,
            source_repo_path=str(source_repo_path),
            local_repo_path=str(local_repo_path),
            requested_commit=requested_commit,
            resolved_commit=None,
            checkout_succeeded=False,
            source_file_count=0,
            test_file_count=0,
            error='checkout_failed:not_a_git_repository',
        )

    python_files = _python_files(local_repo_path)
    source_file_count = sum(
        1 for path in python_files if not _is_test_file(path, local_repo_path)
    )
    test_file_count = sum(
        1 for path in python_files if _is_test_file(path, local_repo_path)
    )
    if source_file_count == 0:
        return MaterializationResult(
            task_id=task_id,
            repo=repo,
            source_repo_path=str(source_repo_path),
            local_repo_path=str(local_repo_path),
            requested_commit=requested_commit,
            resolved_commit=resolved_commit,
            checkout_succeeded=checkout_succeeded,
            source_file_count=source_file_count,
            test_file_count=test_file_count,
            error='repository_missing_source_files',
        )
    if test_file_count == 0:
        return MaterializationResult(
            task_id=task_id,
            repo=repo,
            source_repo_path=str(source_repo_path),
            local_repo_path=str(local_repo_path),
            requested_commit=requested_commit,
            resolved_commit=resolved_commit,
            checkout_succeeded=checkout_succeeded,
            source_file_count=source_file_count,
            test_file_count=test_file_count,
            error='repository_missing_test_files',
        )

    return MaterializationResult(
        task_id=task_id,
        repo=repo,
        source_repo_path=str(source_repo_path),
        local_repo_path=str(local_repo_path),
        requested_commit=requested_commit,
        resolved_commit=resolved_commit,
        checkout_succeeded=checkout_succeeded,
        source_file_count=source_file_count,
        test_file_count=test_file_count,
    )


def apply_patch_to_repository(repo_path: Path, patch_text: str) -> PatchApplyResult:
    patch_path = repo_path / '.symbiotic_patch.diff'
    patch_path.write_text(patch_text, encoding='utf-8')
    result = subprocess.run(
        ['git', 'apply', '--whitespace=nowarn', str(patch_path)],
        cwd=repo_path,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return PatchApplyResult(
            repo_path=str(repo_path),
            applied=False,
            patch_path=str(patch_path),
            error=result.stderr.strip() or result.stdout.strip(),
        )
    return PatchApplyResult(
        repo_path=str(repo_path),
        applied=True,
        patch_path=str(patch_path),
    )


def _serialize_symbol(
    node: ast.AST, filepath: str, parent: str | None = None
) -> dict[str, Any]:
    name = getattr(node, 'name', '<anonymous>')
    qualified_name = f'{parent}.{name}' if parent else name
    kind = 'class' if isinstance(node, ast.ClassDef) else 'function'
    return {
        'name': name,
        'qualified_name': qualified_name,
        'kind': kind,
        'filepath': filepath,
        'lineno': getattr(node, 'lineno', 1),
        'end_lineno': getattr(node, 'end_lineno', getattr(node, 'lineno', 1)),
    }


def _extract_imports(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            imports.append(module)
    return sorted(dict.fromkeys(imports))


def _called_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _extract_symbol_table_and_call_graph(
    tree: ast.Module, filepath: str
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    symbols: list[dict[str, Any]] = []
    call_graph: dict[str, list[str]] = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            symbol = _serialize_symbol(node, filepath)
            symbols.append(symbol)
            calls = sorted(
                dict.fromkeys(
                    called
                    for called in (
                        _called_name(call)
                        for call in ast.walk(node)
                        if isinstance(call, ast.Call)
                    )
                    if called is not None
                )
            )
            call_graph[symbol['qualified_name']] = calls
        elif isinstance(node, ast.ClassDef):
            class_symbol = _serialize_symbol(node, filepath)
            symbols.append(class_symbol)
            for child in node.body:
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    method_symbol = _serialize_symbol(
                        child,
                        filepath,
                        parent=class_symbol['qualified_name'],
                    )
                    symbols.append(method_symbol)
                    calls = sorted(
                        dict.fromkeys(
                            called
                            for called in (
                                _called_name(call)
                                for call in ast.walk(child)
                                if isinstance(call, ast.Call)
                            )
                            if called is not None
                        )
                    )
                    call_graph[method_symbol['qualified_name']] = calls
    return symbols, call_graph


def build_repository_index(
    repo_path: Path,
    repo: str,
    cache_root: Path,
) -> RepositoryIndexResult:
    resolved_commit = 'working-tree'
    if _is_git_repo(repo_path):
        head = _run_git(repo_path, 'rev-parse', 'HEAD')
        if head.returncode == 0:
            resolved_commit = head.stdout.strip()

    cache_dir = cache_root / f'{_repo_slug(repo)}__{resolved_commit}'
    index_path = cache_dir / 'repo_index.json'
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding='utf-8'))
        parse_failures = tuple(payload.get('parse_failures', []))
        return RepositoryIndexResult(
            repo_path=str(repo_path),
            cache_dir=str(cache_dir),
            index_path=str(index_path),
            cached=True,
            file_count=int(payload.get('file_count', 0)),
            source_file_count=int(payload.get('source_file_count', 0)),
            test_file_count=int(payload.get('test_file_count', 0)),
            parse_failure_count=len(parse_failures),
            parse_failures=parse_failures,
        )

    cache_dir.mkdir(parents=True, exist_ok=True)
    python_files = _python_files(repo_path)
    files: dict[str, dict[str, Any]] = {}
    ast_map: dict[str, str] = {}
    symbol_table: dict[str, list[dict[str, Any]]] = {}
    import_graph: dict[str, list[str]] = {}
    call_graph: dict[str, list[str]] = {}
    parse_failures: list[dict[str, Any]] = []
    source_file_count = 0
    test_file_count = 0

    for path in python_files:
        relative = str(path.relative_to(repo_path))
        role = 'test' if _is_test_file(path, repo_path) else 'source'
        if role == 'test':
            test_file_count += 1
        else:
            source_file_count += 1

        source_text = path.read_text(encoding='utf-8')
        try:
            tree = ast.parse(source_text, filename=relative)
        except SyntaxError as exc:
            parse_failures.append(
                {
                    'filepath': relative,
                    'error': exc.msg,
                    'lineno': exc.lineno,
                    'offset': exc.offset,
                }
            )
            files[relative] = {
                'role': role,
                'imports': [],
                'top_level_symbols': [],
                'parse_ok': False,
            }
            continue

        imports = _extract_imports(tree)
        symbols, file_call_graph = _extract_symbol_table_and_call_graph(tree, relative)
        ast_map[relative] = ast.dump(tree, include_attributes=False)
        import_graph[relative] = imports
        files[relative] = {
            'role': role,
            'imports': imports,
            'top_level_symbols': [symbol['qualified_name'] for symbol in symbols],
            'parse_ok': True,
        }
        for symbol in symbols:
            symbol_table.setdefault(symbol['qualified_name'], []).append(symbol)
        call_graph.update(file_call_graph)

    payload = {
        'repo': repo,
        'repo_path': str(repo_path),
        'resolved_commit': resolved_commit,
        'file_count': len(python_files),
        'source_file_count': source_file_count,
        'test_file_count': test_file_count,
        'files': files,
        'ast_map': ast_map,
        'symbol_table': symbol_table,
        'import_graph': import_graph,
        'call_graph': call_graph,
        'parse_failures': parse_failures,
    }
    index_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return RepositoryIndexResult(
        repo_path=str(repo_path),
        cache_dir=str(cache_dir),
        index_path=str(index_path),
        cached=False,
        file_count=len(python_files),
        source_file_count=source_file_count,
        test_file_count=test_file_count,
        parse_failure_count=len(parse_failures),
        parse_failures=tuple(parse_failures),
    )


class RepositoryIndexer:
    """Materialize task repositories, persist validation signals, and cache repo indexes."""

    def __init__(self, config: RepositoryIndexerConfig) -> None:
        self.config = config

    def materialize_task_repository(
        self,
        task: TaskContract,
        raw_task: RawTaskDefinition,
    ) -> MaterializationResult:
        return materialize_repository_snapshot(
            task_id=task.task_id,
            repo=task.repo,
            requested_commit=task.repo_commit,
            raw_fields=raw_task.raw_fields,
            workspace_root=self.config.workspace_root,
            repo_source_root=self.config.repo_source_root,
            repo_source_overrides=self.config.repo_source_overrides,
        )

    def index_repository(self, task: TaskContract) -> RepositoryIndexResult:
        if task.repo_path is None:
            raise ValueError(
                'task.repo_path must be set before indexing the repository'
            )
        return build_repository_index(
            repo_path=Path(task.repo_path),
            repo=task.repo,
            cache_root=self.config.cache_root,
        )

    def prepare_task(
        self,
        task: TaskContract,
        raw_task: RawTaskDefinition,
        subset: str,
        output_dir: Path,
        timestamp: str | None = None,
    ) -> PreparedTaskArtifact:
        preparation_timestamp = timestamp or datetime.now(tz=UTC).isoformat()
        raw_dir = output_dir / 'raw'
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_fields_path = raw_dir / f'{task.task_id}.json'
        _write_json(raw_fields_path, raw_task.raw_fields)

        materialization = self.materialize_task_repository(task, raw_task)
        task.metadata.preprocessing_timestamp = preparation_timestamp
        task.metadata.raw_fields_path = str(raw_fields_path)

        if not materialization.is_valid:
            task.metadata.status = 'invalid'
            return PreparedTaskArtifact(
                subset=subset,
                task=task,
                raw_definition=raw_task,
                status='invalid',
                materialization=materialization,
                repo_index=None,
                artifact_dir=None,
            )

        task.repo_path = materialization.local_repo_path
        task_dir = output_dir / 'prepared' / subset / task.task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        persisted_paths = persist_validation_signals(raw_task, task_dir)
        repo_index = self.index_repository(task)

        task.metadata.bug_report_path = persisted_paths['bug_report_path']
        task.metadata.failing_tests_path = persisted_paths['failing_tests_path']
        task.metadata.execution_trace_path = persisted_paths['execution_trace_path']
        task.metadata.oracle_path = persisted_paths['oracle_path']
        task.metadata.repo_index_path = repo_index.index_path
        task.metadata.status = 'partial' if repo_index.parse_failure_count else 'valid'

        _write_json(task_dir / 'task.json', json.loads(task.model_dump_json()))
        _write_json(task_dir / 'repo_materialization.json', asdict(materialization))
        _write_json(
            task_dir / 'repo_index_reference.json',
            {
                'repo_index_path': repo_index.index_path,
                'cached': repo_index.cached,
                'parse_failure_count': repo_index.parse_failure_count,
            },
        )
        return PreparedTaskArtifact(
            subset=subset,
            task=task,
            raw_definition=raw_task,
            status=task.metadata.status or 'valid',
            materialization=materialization,
            repo_index=repo_index,
            artifact_dir=str(task_dir),
        )
