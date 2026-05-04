from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List

from symbiotic_swe.contracts import CanonicalTask, TestEvaluationResult, TestSuiteResult


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
