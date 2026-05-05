from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from symbiotic_swe.contracts import (
    CanonicalTask,
    MaterializationResult,
    PreparedTaskArtifact,
    RepoFileEntry,
    RepoIndex,
    RepoSymbol,
    PatchApplicationResult,
)


@dataclass(frozen=True)
class RepositoryIndexerConfig:
    workspace_root: Path = Path('workspaces')
    cache_root: Path = Path('.cache/repo_index')
    repo_source_overrides: Dict[str, Path] = field(default_factory=dict)


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ['git', *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f'git {args[0]} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def _extract_symbols(source: str, filepath: str) -> tuple[List[RepoSymbol], List[str]]:
    """Raises SyntaxError if the source cannot be parsed."""
    symbols: List[RepoSymbol] = []
    imports: List[str] = []
    tree = ast.parse(source)  # intentionally let SyntaxError propagate

    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, 'end_lineno', node.lineno)
            snippet = '\n'.join(lines[node.lineno - 1:end_line])
            symbols.append(RepoSymbol(
                name=node.name,
                kind='function',
                file=filepath,
                line_start=node.lineno,
                line_end=end_line,
                source=textwrap.dedent(snippet),
            ))
        elif isinstance(node, ast.ClassDef):
            end_line = getattr(node, 'end_lineno', node.lineno)
            symbols.append(RepoSymbol(
                name=node.name,
                kind='class',
                file=filepath,
                line_start=node.lineno,
                line_end=end_line,
            ))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            imports.append(mod)

    return symbols, imports


def build_repository_index(
    repo_path: Path,
    repo: str,
    cache_root: Path,
) -> RepoIndex:
    cache_key = hashlib.sha256(str(repo_path.resolve()).encode()).hexdigest()[:16]
    cache_file = cache_root / f'{cache_key}.json'

    if cache_file.exists():
        data = json.loads(cache_file.read_text(encoding='utf-8'))
        idx = RepoIndex(**data)
        idx = idx.model_copy(update={'cached': True})
        return idx

    files: List[RepoFileEntry] = []
    source_count = test_count = fail_count = 0

    for py_file in sorted(repo_path.rglob('*.py')):
        rel = str(py_file.relative_to(repo_path))
        parts = rel.replace('\\', '/').split('/')
        is_test = any(p in {'tests', 'test'} or p.startswith('test_') for p in parts)
        role = 'test' if is_test else 'source'

        try:
            source = py_file.read_text(encoding='utf-8', errors='replace')
            symbols, imports = _extract_symbols(source, rel)
            failed = False
        except (SyntaxError, Exception):
            symbols, imports = [], []
            failed = True

        files.append(RepoFileEntry(
            path=rel,
            role=role,
            symbols=symbols,
            parse_failed=failed,
            imports=imports,
        ))

        if failed:
            fail_count += 1
        elif role == 'test':
            test_count += 1
        else:
            source_count += 1

    cache_root.mkdir(parents=True, exist_ok=True)
    idx = RepoIndex(
        repo=repo,
        index_path=str(cache_file),
        source_file_count=source_count,
        test_file_count=test_count,
        parse_failure_count=fail_count,
        total_symbols=sum(len(f.symbols) for f in files),
        files=files,
        cached=False,
    )
    cache_file.write_text(idx.model_dump_json(indent=2), encoding='utf-8')
    return idx


def materialize_repository_snapshot(
    task_id: str,
    repo: str,
    requested_commit: str,
    raw_fields: dict,
    workspace_root: Path,
    repo_source_overrides: Optional[Dict[str, Path]] = None,
) -> MaterializationResult:
    overrides = repo_source_overrides or {}
    dest = workspace_root / task_id / 'repo'
    dest.mkdir(parents=True, exist_ok=True)

    if repo in overrides:
        source = Path(overrides[repo])
        try:
            _git(source, 'checkout', requested_commit, '--')
            resolved = _git(source, 'rev-parse', 'HEAD')
            # copy to workspace (or just use source directly for simplicity)
            import shutil
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest, dirs_exist_ok=False)
            return MaterializationResult(
                is_valid=True,
                local_repo_path=str(dest),
                resolved_commit=resolved,
            )
        except Exception as exc:
            return MaterializationResult(is_valid=False, error=str(exc))

    # Try GitHub clone
    clone_url = f'https://github.com/{repo}.git'
    try:
        if not (dest / '.git').exists():
            result = subprocess.run(
                ['git', 'clone', '--quiet', clone_url, str(dest)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                return MaterializationResult(
                    is_valid=False,
                    error=f'clone failed: {result.stderr.strip()}',
                )
        _git(dest, 'checkout', requested_commit)
        resolved = _git(dest, 'rev-parse', 'HEAD')
        return MaterializationResult(
            is_valid=True,
            local_repo_path=str(dest),
            resolved_commit=resolved,
        )
    except Exception as exc:
        return MaterializationResult(is_valid=False, error=str(exc))


def apply_patch_to_repository(repo_path: Path, patch_text: str) -> PatchApplicationResult:
    if not patch_text.strip():
        return PatchApplicationResult(applied=False, error='empty patch')

    def _without_index_lines(text: str) -> str:
        return '\n'.join(
            line for line in text.splitlines()
            if not line.startswith('index ')
        ) + '\n'

    patch_variants = [patch_text]
    stripped_index_patch = _without_index_lines(patch_text)
    if stripped_index_patch != patch_text:
        patch_variants.append(stripped_index_patch)

    # Try atomic git apply modes first. Avoid --reject here because it can leave
    # partial changes and .rej files before more tolerant fallbacks run.
    git_errors: list[str] = []
    git_modes = [
        ['git', 'apply', '--recount', '-'],
        ['git', 'apply', '--ignore-space-change', '--ignore-whitespace', '--recount', '-'],
        ['git', 'apply', '--3way', '--recount', '-'],
        ['git', 'apply', '--3way', '--ignore-space-change', '--ignore-whitespace', '--recount', '-'],
    ]
    for variant in patch_variants:
        for command in git_modes:
            result = subprocess.run(
                command,
                input=variant,
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return PatchApplicationResult(applied=True)
            detail = result.stderr.strip() or result.stdout.strip()
            if detail:
                git_errors.append(detail)

    first_error = git_errors[0] if git_errors else ''

    # Fallback: patch with fuzz=3 to tolerate slightly wrong line numbers or
    # small context drift. Dry-run first so failed attempts do not dirty the repo.
    patch_errors: list[str] = []
    for variant in patch_variants:
        patch_dry_run = subprocess.run(
            ['patch', '--dry-run', '-p1', '-F3', '-t', '--no-backup-if-mismatch'],
            input=variant,
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if patch_dry_run.returncode == 0:
            patch_apply = subprocess.run(
                ['patch', '-p1', '-F3', '-t', '--no-backup-if-mismatch'],
                input=variant,
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if patch_apply.returncode == 0:
                return PatchApplicationResult(applied=True)
            detail = patch_apply.stderr.strip() or patch_apply.stdout.strip()
            if detail:
                patch_errors.append(detail)
        else:
            detail = patch_dry_run.stderr.strip() or patch_dry_run.stdout.strip()
            if detail:
                patch_errors.append(detail)

    errors = [*git_errors, *patch_errors]
    combined_error = '\n\n'.join(dict.fromkeys(error for error in errors if error))
    rejected = combined_error.count('.rej') + combined_error.count('Rejected hunk')
    return PatchApplicationResult(
        applied=False,
        error=combined_error or first_error,
        rejected_hunks=rejected,
    )


class RepositoryIndexer:
    def __init__(self, config: Optional[RepositoryIndexerConfig] = None) -> None:
        self.config = config or RepositoryIndexerConfig()

    def prepare_task(
        self,
        task: CanonicalTask,
        raw_task: Any,
        subset: str,
        output_dir: Path,
        timestamp: str = '',
    ) -> PreparedTaskArtifact:
        from datetime import datetime, timezone
        if not timestamp:
            timestamp = datetime.now(tz=timezone.utc).isoformat()

        artifact_dir = output_dir / 'prepared' / subset / task.task_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Materialize repository
        mat = materialize_repository_snapshot(
            task_id=task.task_id,
            repo=task.repo,
            requested_commit=task.repo_commit,
            raw_fields=raw_task.raw_fields if hasattr(raw_task, 'raw_fields') else {},
            workspace_root=self.config.workspace_root,
            repo_source_overrides={
                k: Path(v) for k, v in self.config.repo_source_overrides.items()
            },
        )

        status = 'valid' if mat.is_valid else 'partial'
        repo_path = mat.local_repo_path

        # Build repo index
        repo_index = None
        repo_index_path = None
        if mat.is_valid and repo_path:
            try:
                repo_index = build_repository_index(
                    repo_path=Path(repo_path),
                    repo=task.repo,
                    cache_root=self.config.cache_root,
                )
                repo_index_path = repo_index.index_path
            except Exception:
                status = 'partial'

        # Write sidecar files
        bug_report_path = str(artifact_dir / 'bug_report.txt')
        failing_tests_path = str(artifact_dir / 'failing_tests.json')
        oracle_path = str(artifact_dir / 'oracle.json')
        raw_fields_path = str(artifact_dir / 'raw_fields.json')

        (artifact_dir / 'bug_report.txt').write_text(task.bug_description, encoding='utf-8')
        (artifact_dir / 'failing_tests.json').write_text(
            json.dumps(task.failing_tests, indent=2), encoding='utf-8'
        )
        if task.oracle:
            (artifact_dir / 'oracle.json').write_text(
                task.oracle.model_dump_json(indent=2), encoding='utf-8'
            )
        (artifact_dir / 'raw_fields.json').write_text(
            json.dumps(raw_task.raw_fields if hasattr(raw_task, 'raw_fields') else {}, indent=2),
            encoding='utf-8',
        )

        updated_meta = task.metadata.model_copy(update={
            'status': status,
            'subset': subset,
            'preprocessing_timestamp': timestamp,
            'bug_report_path': bug_report_path,
            'failing_tests_path': failing_tests_path,
            'oracle_path': oracle_path,
            'repo_index_path': repo_index_path,
            'raw_fields_path': raw_fields_path,
        })
        updated_task = task.model_copy(update={
            'repo_path': repo_path,
            'metadata': updated_meta,
        })

        # Write canonical task.json
        (artifact_dir / 'task.json').write_text(
            updated_task.model_dump_json(indent=2), encoding='utf-8'
        )

        return PreparedTaskArtifact(
            task=updated_task,
            repo_index=repo_index,
            status=status,
            artifact_dir=str(artifact_dir),
            error=mat.error if not mat.is_valid else None,
        )
