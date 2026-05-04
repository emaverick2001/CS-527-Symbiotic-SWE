from __future__ import annotations

import os
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


def _apply_oracle_test_patch(repo_path: Path, task: CanonicalTask) -> str | None:
    test_patch = _oracle_text(task, 'test_patch')
    if not test_patch.strip():
        return None

    result = apply_patch_to_repository(repo_path, test_patch)
    if result.applied:
        return None
    return result.error or 'oracle test_patch did not apply'


def _pytest_env(repo_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    pythonpath_entries = [str(repo_path)]
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

    f2p_result = _run_pytest_suite(repo_path, 'FAIL_TO_PASS', fail_to_pass, timeout_sec)
    p2p_result = _run_pytest_suite(repo_path, 'PASS_TO_PASS', pass_to_pass, timeout_sec)

    evaluated = bool(fail_to_pass)
    resolved = bool(evaluated and f2p_result.passed and p2p_result.passed)
    error: str | None = None
    if not fail_to_pass:
        error = 'no FAIL_TO_PASS tests available'

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
