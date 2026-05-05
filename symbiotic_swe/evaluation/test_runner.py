from __future__ import annotations

import ast
import os
import shutil
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List

from symbiotic_swe.contracts import CanonicalTask, TestEvaluationResult, TestSuiteResult
from symbiotic_swe.dataset.repo_indexer import apply_patch_to_repository


_OUTPUT_LIMIT = 12_000


def _tail(text: str, limit: int = _OUTPUT_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _oracle_list(task: CanonicalTask, key: str) -> List[str]:
    if task.oracle is None or not isinstance(task.oracle.spec, dict):
        return []
    raw = task.oracle.spec.get(key, [])
    if isinstance(raw, str):
        return [raw] if raw else []
    if isinstance(raw, Iterable):
        return [str(item) for item in raw if str(item)]
    return []


def pass_to_pass_tests(task: CanonicalTask) -> List[str]:
    return _oracle_list(task, 'passing_tests')


def _oracle_text(task: CanonicalTask, key: str) -> str:
    if task.oracle is None or not isinstance(task.oracle.spec, dict):
        return ''
    raw = task.oracle.spec.get(key, '')
    return raw if isinstance(raw, str) else ''


def _test_patch_paths(task: CanonicalTask) -> List[str]:
    patch_text = _oracle_text(task, 'test_patch')
    paths: List[str] = []
    seen: set[str] = set()
    for match in re.finditer(r'^diff --git a/(\S+) b/(\S+)$', patch_text, flags=re.MULTILINE):
        path = match.group(2)
        if path.endswith('.py') and path not in seen:
            paths.append(path)
            seen.add(path)
    for match in re.finditer(r'^\+\+\+ b/(\S+)$', patch_text, flags=re.MULTILINE):
        path = match.group(1)
        if path.endswith('.py') and path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def _apply_oracle_test_patch(repo_path: Path, task: CanonicalTask) -> str | None:
    test_patch = _oracle_text(task, 'test_patch')
    if not test_patch.strip():
        return None

    result = apply_patch_to_repository(repo_path, test_patch)
    if result.applied:
        return None
    return result.error or 'oracle test_patch did not apply'


def _looks_like_pytest_node(target: str) -> bool:
    return '::' in target or target.endswith('.py') or '/' in target or '\\' in target


def _is_test_file(path: Path) -> bool:
    parts = path.parts
    return path.name.startswith('test_') or path.name.endswith('_test.py') or 'tests' in parts


def _iter_candidate_test_files(repo_path: Path, task: CanonicalTask) -> List[Path]:
    candidates: List[Path] = []
    seen: set[Path] = set()

    for rel_path in _test_patch_paths(task):
        path = repo_path / rel_path
        if path.exists() and path.suffix == '.py' and path not in seen:
            candidates.append(path)
            seen.add(path)

    for path in sorted(repo_path.rglob('*.py')):
        if _is_test_file(path) and path not in seen:
            candidates.append(path)
            seen.add(path)
    return candidates


def _find_test_node_in_file(repo_path: Path, path: Path, test_name: str) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return None

    rel_path = path.relative_to(repo_path).as_posix()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == test_name:
            return f'{rel_path}::{test_name}'
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == test_name:
                    return f'{rel_path}::{node.name}::{test_name}'
    return None


def _normalize_test_target(repo_path: Path, task: CanonicalTask, target: str) -> str:
    target = target.strip()
    if not target or _looks_like_pytest_node(target):
        return target

    for path in _iter_candidate_test_files(repo_path, task):
        node_id = _find_test_node_in_file(repo_path, path, target)
        if node_id:
            return node_id
    return target


def _normalize_test_targets(repo_path: Path, task: CanonicalTask, targets: List[str]) -> List[str]:
    return [_normalize_test_target(repo_path, task, target) for target in targets]


def _pytest_env(repo_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    pythonpath_entries = [str(repo_path)]
    shim_dir = _legacy_sympy_shim_dir(repo_path)
    if shim_dir is not None:
        pythonpath_entries.insert(0, str(shim_dir))
    if (repo_path / 'lib').is_dir():
        pythonpath_entries.insert(0, str(repo_path / 'lib'))
    existing_pythonpath = env.get('PYTHONPATH')
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env['PYTHONPATH'] = os.pathsep.join(pythonpath_entries)
    env.setdefault('MPLBACKEND', 'Agg')
    if 'MPLCONFIGDIR' not in env:
        mpl_config = repo_path / '.mplconfig'
        mpl_config.mkdir(exist_ok=True)
        env['MPLCONFIGDIR'] = str(mpl_config)
    return env


def _legacy_sympy_shim_dir(repo_path: Path) -> Path | None:
    basic_py = repo_path / 'sympy' / 'core' / 'basic.py'
    if not basic_py.exists():
        return None
    source = basic_py.read_text(encoding='utf-8', errors='replace')
    if 'from collections import Mapping' not in source and 'collections.Mapping' not in source:
        return None

    shim_dir = repo_path / '.symbiotic_swe_pytest_shims'
    shim_dir.mkdir(exist_ok=True)
    (shim_dir / 'sitecustomize.py').write_text(
        '\n'.join(
            [
                'import collections',
                'import collections.abc',
                '',
                'for _name in (',
                '    "Mapping",',
                '    "MutableMapping",',
                '    "Sequence",',
                '    "MutableSequence",',
                '    "Set",',
                '    "MutableSet",',
                '    "Iterable",',
                '    "Iterator",',
                '    "Callable",',
                '):',
                '    if not hasattr(collections, _name) and hasattr(collections.abc, _name):',
                '        setattr(collections, _name, getattr(collections.abc, _name))',
                '',
            ]
        ),
        encoding='utf-8',
    )
    return shim_dir


def _repo_slug(task: CanonicalTask) -> str:
    return task.repo.lower().replace('_', '-')


def _is_scikit_learn_task(task: CanonicalTask, repo_path: Path) -> bool:
    return _repo_slug(task) == 'scikit-learn/scikit-learn' or (repo_path / 'sklearn').is_dir()


def _is_matplotlib_task(task: CanonicalTask, repo_path: Path) -> bool:
    return _repo_slug(task) == 'matplotlib/matplotlib' or (repo_path / 'lib' / 'matplotlib').is_dir()


def _sklearn_check_build_extension_exists(repo_path: Path) -> bool:
    check_build_dir = repo_path / 'sklearn' / '__check_build'
    return any(check_build_dir.glob('_check_build*.so')) or any(check_build_dir.glob('_check_build*.pyd'))


def _run_repo_prep_command(
    repo_path: Path,
    command: list[str],
    timeout_sec: int,
    extra_env: dict[str, str] | None = None,
) -> tuple[bool, str]:
    env = _pytest_env(repo_path)
    if extra_env:
        env.update(extra_env)
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        output = '\n'.join(part for part in (exc.stdout or '', exc.stderr or '') if part)
        return False, f'command timed out after {timeout_sec}s: {" ".join(command)}\n{_tail(output)}'

    if result.returncode == 0:
        return True, ''
    output = '\n'.join(part for part in (result.stdout, result.stderr) if part)
    return False, f'command failed ({result.returncode}): {" ".join(command)}\n{_tail(output)}'


def _prepare_scikit_learn_repo(repo_path: Path) -> str | None:
    if _sklearn_check_build_extension_exists(repo_path):
        return None

    setup_py = repo_path / 'setup.py'
    if not setup_py.exists():
        return 'scikit-learn source checkout has no setup.py; cannot build extension modules'

    build_tool = shutil.which('make')
    commands = []
    if build_tool:
        commands.append(['make', 'in'])
    commands.append([sys.executable, 'setup.py', 'build_ext', '--inplace'])

    errors: list[str] = []
    build_env = {'SKLEARN_NO_OPENMP': '1'}
    for command in commands:
        ok, detail = _run_repo_prep_command(
            repo_path,
            command,
            timeout_sec=600,
            extra_env=build_env,
        )
        if ok and _sklearn_check_build_extension_exists(repo_path):
            return None
        if detail:
            errors.append(detail)

    return 'scikit-learn build failed before pytest:\n' + '\n\n'.join(errors)


def _prepare_repo_for_pytest(repo_path: Path, task: CanonicalTask) -> str | None:
    if _is_scikit_learn_task(task, repo_path):
        return _prepare_scikit_learn_repo(repo_path)
    return None


def _environment_limited_error(repo_path: Path, task: CanonicalTask, result: TestSuiteResult) -> str | None:
    output = f'{result.stderr}\n{result.stdout}'
    if _is_scikit_learn_task(task, repo_path) and 'sklearn.__check_build._check_build' in output:
        return 'environment_limited: scikit-learn extension modules are not built'
    if _is_matplotlib_task(task, repo_path) and 'Matplotlib is not built with the correct FreeType version' in output:
        return 'environment_limited: Matplotlib FreeType version mismatch in local test environment'
    return None


def _run_pytest_suite(repo_path: Path, name: str, tests: List[str], timeout_sec: int) -> TestSuiteResult:
    if not tests:
        return TestSuiteResult(name=name, tests=[], passed=True)

    command = [sys.executable, '-m', 'pytest', '-q', *tests]
    started = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=_pytest_env(repo_path),
        )
    except subprocess.TimeoutExpired as exc:
        return TestSuiteResult(
            name=name,
            tests=tests,
            command=command,
            returncode=None,
            passed=False,
            duration_ms=int((time.time() - started) * 1000),
            stdout=_tail(exc.stdout or ''),
            stderr=_tail(exc.stderr or ''),
            error=f'pytest timeout after {timeout_sec}s',
        )

    return TestSuiteResult(
        name=name,
        tests=tests,
        command=command,
        returncode=result.returncode,
        passed=result.returncode == 0,
        duration_ms=int((time.time() - started) * 1000),
        stdout=_tail(result.stdout),
        stderr=_tail(result.stderr),
    )


def evaluate_task_tests(
    repo_path: Path,
    task: CanonicalTask,
    iteration: int,
    timeout_sec: int = 120,
) -> TestEvaluationResult:
    started = time.time()
    fail_to_pass = list(task.failing_tests)
    pass_to_pass = pass_to_pass_tests(task)

    test_patch_error = _apply_oracle_test_patch(repo_path, task)
    if test_patch_error is not None:
        fail_result = TestSuiteResult(
            name='FAIL_TO_PASS',
            tests=fail_to_pass,
            command=['git', 'apply', '<oracle test_patch>'],
            returncode=1,
            passed=False,
            duration_ms=int((time.time() - started) * 1000),
            error=f'test_patch apply failed: {test_patch_error}',
        )
        pass_result = TestSuiteResult(name='PASS_TO_PASS', tests=pass_to_pass, passed=False)
        return TestEvaluationResult(
            task_id=task.task_id,
            iteration=iteration,
            resolved=False,
            evaluated=False,
            fail_to_pass=fail_result,
            pass_to_pass=pass_result,
            duration_ms=int((time.time() - started) * 1000),
            error=fail_result.error,
        )

    prep_error = _prepare_repo_for_pytest(repo_path, task)
    if prep_error is not None:
        fail_result = TestSuiteResult(
            name='FAIL_TO_PASS',
            tests=fail_to_pass,
            command=['<repo test environment prep>'],
            returncode=1,
            passed=False,
            duration_ms=int((time.time() - started) * 1000),
            error=f'environment_limited: {prep_error}',
        )
        pass_result = TestSuiteResult(name='PASS_TO_PASS', tests=pass_to_pass, passed=False)
        return TestEvaluationResult(
            task_id=task.task_id,
            iteration=iteration,
            resolved=False,
            evaluated=False,
            fail_to_pass=fail_result,
            pass_to_pass=pass_result,
            duration_ms=int((time.time() - started) * 1000),
            error=fail_result.error,
        )

    fail_to_pass = _normalize_test_targets(repo_path, task, fail_to_pass)
    pass_to_pass = _normalize_test_targets(repo_path, task, pass_to_pass)

    f2p_result = _run_pytest_suite(repo_path, 'FAIL_TO_PASS', fail_to_pass, timeout_sec)
    p2p_result = _run_pytest_suite(repo_path, 'PASS_TO_PASS', pass_to_pass, timeout_sec)

    f2p_env_error = _environment_limited_error(repo_path, task, f2p_result)
    p2p_env_error = _environment_limited_error(repo_path, task, p2p_result)
    if f2p_env_error:
        f2p_result = f2p_result.model_copy(update={'error': f2p_env_error})
    if p2p_env_error:
        p2p_result = p2p_result.model_copy(update={'error': p2p_env_error})

    evaluated = bool(fail_to_pass)
    resolved = bool(evaluated and f2p_result.passed and p2p_result.passed)
    error: str | None = None
    if not fail_to_pass:
        error = 'no FAIL_TO_PASS tests available'
    elif f2p_env_error or p2p_env_error:
        error = f2p_env_error or p2p_env_error

    return TestEvaluationResult(
        task_id=task.task_id,
        iteration=iteration,
        resolved=resolved,
        evaluated=evaluated,
        fail_to_pass=f2p_result,
        pass_to_pass=p2p_result,
        duration_ms=int((time.time() - started) * 1000),
        error=error,
    )
