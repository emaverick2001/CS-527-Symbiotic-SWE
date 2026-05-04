from __future__ import annotations

import subprocess
from pathlib import Path

from symbiotic_swe.contracts import (
    CanonicalTask,
    CounterexampleContract,
    OracleSpec,
    PatchContract,
    RepoFileEntry,
    RepoIndex,
    RetrievedContext,
    SolverResultContract,
    TaskMetadata,
)
from symbiotic_swe.context_selection.selector import load_context_source, select_context
from symbiotic_swe.dataset.repo_indexer import apply_patch_to_repository
from symbiotic_swe.evaluation.test_runner import evaluate_task_tests
from symbiotic_swe.feedback.critique import build_critique
from symbiotic_swe.orchestration.runner import run_benchmark
from symbiotic_swe.patch_generation.generator import _extract_diff
from symbiotic_swe.patch_generation.prompt_builder import build_patch_prompt
from symbiotic_swe.slicing.slicer import slice_impact
from symbiotic_swe.symbolic_reasoning.solver import extract_counterexample, run_solver


PATCH_DIFF = """diff --git a/pkg/logic.py b/pkg/logic.py
--- a/pkg/logic.py
+++ b/pkg/logic.py
@@ -1,2 +1,4 @@
 def first(values):
+    if len(values) == 0:
+        return None
     return values[0]
"""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / 'repo'
    (repo / 'pkg').mkdir(parents=True)
    (repo / 'tests').mkdir()
    (repo / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (repo / 'pkg' / 'logic.py').write_text('def first(values):\n    return values[0]\n', encoding='utf-8')
    (repo / 'tests' / 'test_logic.py').write_text(
        '\n'.join(
            [
                'from pkg.logic import first',
                '',
                'def test_empty():',
                '    assert first([]) is None',
                '',
                'def test_nonempty():',
                '    assert first([7]) == 7',
                '',
            ]
        ),
        encoding='utf-8',
    )
    _git(repo, 'init')
    _git(repo, 'config', 'user.email', 'fixture@example.com')
    _git(repo, 'config', 'user.name', 'Fixture User')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-m', 'fixture')
    return repo


def _task(repo: Path) -> CanonicalTask:
    return CanonicalTask(
        task_id='fixture__first-1',
        repo='fixture/repo',
        repo_commit=_git(repo, 'rev-parse', 'HEAD'),
        repo_path=str(repo),
        bug_description='first([]) raises IndexError instead of returning None.',
        failing_tests=['tests/test_logic.py::test_empty'],
        oracle=OracleSpec(
            type='tests',
            spec={'passing_tests': ['tests/test_logic.py::test_nonempty']},
        ),
        metadata=TaskMetadata(
            dataset='synthetic',
            logic_heavy=True,
            repo_name='repo',
            subset='smoke',
        ),
    )


def test_prompt_builder_includes_symbolic_critique(tmp_path: Path) -> None:
    task = _task(_fixture_repo(tmp_path))
    critique = build_critique(
        CounterexampleContract(
            counterexample_id='ce1',
            task_id=task.task_id,
            iteration=0,
            inputs={'values': []},
            violated_condition='IndexError when values is empty',
            observed_failure='IndexError',
            affected_function='pkg/logic.py::first',
        ),
        SolverResultContract(
            solver_result_id='s1',
            task_id=task.task_id,
            iteration=0,
            status='sat',
            violated_property='IndexError when values is empty',
        ),
        iteration=0,
    )

    messages = build_patch_prompt(task, 'def first(values): ...', iteration=1, critique=critique)

    assert 'Symbolic Verifier Feedback' in messages[0]['content']
    assert 'values = []' in messages[0]['content']
    assert 'git-style unified diff' in messages[0]['content']
    assert 'checked-out repository' in messages[0]['content']


def test_patch_parser_extracts_last_diff_block() -> None:
    raw = f'ignore me\n```diff\n{PATCH_DIFF}```\n'

    parsed = _extract_diff(raw)

    assert parsed.startswith('diff --git a/pkg/logic.py b/pkg/logic.py')
    assert '+    if len(values) == 0:' in parsed


def test_patch_parser_adds_missing_git_headers() -> None:
    raw = """```diff
--- a/pkg/logic.py
+++ b/pkg/logic.py
@@ -1,2 +1,4 @@
 def first(values):
+    if len(values) == 0:
+        return None
     return values[0]
```"""

    parsed = _extract_diff(raw)

    assert parsed.startswith('diff --git a/pkg/logic.py b/pkg/logic.py')
    assert '--- a/pkg/logic.py\n+++ b/pkg/logic.py' in parsed


def test_context_source_includes_exact_traceback_window(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    task = _task(repo).model_copy(update={
        'bug_description': 'Traceback points at pkg/logic.py:2 when values is empty.'
    })

    context = load_context_source(
        task,
        RetrievedContext(task_id=task.task_id, query='', files=[], symbols=[]),
        repo,
    )

    assert '# File: pkg/logic.py' in context
    assert 'Exact checked-out source lines' in context
    assert 'return values[0]' in context


def test_sympy_numeric_boolean_report_prioritizes_numbers_context(tmp_path: Path) -> None:
    repo = tmp_path / 'repo'
    (repo / 'sympy' / 'core').mkdir(parents=True)
    (repo / 'sympy' / 'logic').mkdir(parents=True)
    numbers_source = '\n'.join(
        [
            'class Integer:',
            '    pass',
            '',
            'class Float(Number):',
            '    def __eq__(self, other):',
            '        from sympy.logic.boolalg import Boolean',
            '        if not self:',
            '            return not other',
            '        if isinstance(other, Boolean):',
            '            return False',
            '        return False',
            '',
        ]
    )
    boolalg_source = '\n'.join(
        [
            'class BooleanAtom:',
            '    def _do_eq_sympify(self, other):',
            '        return self == other',
            '',
        ]
    )
    (repo / 'sympy' / 'core' / 'numbers.py').write_text(numbers_source, encoding='utf-8')
    (repo / 'sympy' / 'logic' / 'boolalg.py').write_text(boolalg_source, encoding='utf-8')
    task = CanonicalTask(
        task_id='sympy__sympy-20801',
        repo='sympy/sympy',
        repo_commit='abc123',
        repo_path=str(repo),
        bug_description='S(0.0) == S.false returns True but numeric equality should return False.',
        failing_tests=['test_zero_not_false'],
        metadata=TaskMetadata(dataset='synthetic', logic_heavy=True, repo_name='sympy'),
    )
    repo_index = RepoIndex(
        repo='sympy/sympy',
        index_path='memory',
        files=[
            RepoFileEntry(path='sympy/logic/boolalg.py', role='source'),
            RepoFileEntry(path='sympy/core/numbers.py', role='source'),
        ],
    )

    context = select_context(task, repo_index)
    source = load_context_source(task, context, repo)

    assert context.files[0].path == 'sympy/core/numbers.py'
    assert '# High-priority source context: SymPy Float.__eq__ numeric-vs-Boolean equality logic.' in source
    assert 'if isinstance(other, Boolean):' in source
    assert 'sympy/logic/boolalg.py' in source


def test_patch_application_tolerates_offset_hunk(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    offset_diff = """diff --git a/pkg/logic.py b/pkg/logic.py
--- a/pkg/logic.py
+++ b/pkg/logic.py
@@ -20,2 +20,4 @@
 def first(values):
+    if len(values) == 0:
+        return None
     return values[0]
"""

    result = apply_patch_to_repository(repo, offset_diff)

    assert result.applied is True
    assert 'return None' in (repo / 'pkg' / 'logic.py').read_text(encoding='utf-8')


def test_slicing_and_solver_find_then_clear_index_risk(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    task = _task(repo)
    risky_slice = slice_impact(
        PatchContract(
            patch_id='p1',
            task_id=task.task_id,
            iteration=0,
            raw_text='',
            diff=PATCH_DIFF,
            target_files=['pkg/logic.py'],
            parse_ok=True,
        ),
        repo,
        task.task_id,
    )

    risky = run_solver(risky_slice, task)
    assert risky.status == 'sat'
    counterexample = extract_counterexample(risky, risky_slice, task)
    assert counterexample is not None
    assert counterexample.inputs == {'values': []}

    (repo / 'pkg' / 'logic.py').write_text(
        'def first(values):\n    if len(values) == 0:\n        return None\n    return values[0]\n',
        encoding='utf-8',
    )
    safe_slice = slice_impact(
        PatchContract(
            patch_id='p2',
            task_id=task.task_id,
            iteration=0,
            raw_text='',
            diff=PATCH_DIFF,
            target_files=['pkg/logic.py'],
            parse_ok=True,
        ),
        repo,
        task.task_id,
    )
    assert run_solver(safe_slice, task).status == 'unsat'


def test_evaluate_task_tests_records_true_resolution(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    task = _task(repo)

    unresolved = evaluate_task_tests(repo, task, iteration=0)
    assert unresolved.resolved is False
    assert unresolved.fail_to_pass.passed is False
    assert unresolved.pass_to_pass.passed is True

    (repo / 'pkg' / 'logic.py').write_text(
        'def first(values):\n    if len(values) == 0:\n        return None\n    return values[0]\n',
        encoding='utf-8',
    )
    resolved = evaluate_task_tests(repo, task, iteration=1)
    assert resolved.resolved is True


def test_evaluate_task_tests_applies_oracle_test_patch(tmp_path: Path) -> None:
    repo = tmp_path / 'repo'
    (repo / 'pkg').mkdir(parents=True)
    (repo / 'tests').mkdir()
    (repo / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (repo / 'pkg' / 'logic.py').write_text('def first(values):\n    return values[0]\n', encoding='utf-8')
    (repo / 'tests' / 'test_logic.py').write_text(
        'from pkg.logic import first\n\n'
        'def test_nonempty():\n'
        '    assert first([7]) == 7\n',
        encoding='utf-8',
    )
    _git(repo, 'init')
    _git(repo, 'config', 'user.email', 'fixture@example.com')
    _git(repo, 'config', 'user.name', 'Fixture User')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-m', 'fixture')

    test_patch = """diff --git a/tests/test_logic.py b/tests/test_logic.py
--- a/tests/test_logic.py
+++ b/tests/test_logic.py
@@ -2,5 +2,8 @@
 
+def test_empty():
+    assert first([]) is None
+
 def test_nonempty():
     assert first([7]) == 7
"""
    task = CanonicalTask(
        task_id='fixture__first-1',
        repo='fixture/repo',
        repo_commit=_git(repo, 'rev-parse', 'HEAD'),
        repo_path=str(repo),
        bug_description='first([]) raises IndexError instead of returning None.',
        failing_tests=['tests/test_logic.py::test_empty'],
        oracle=OracleSpec(type='tests', spec={'test_patch': test_patch}),
        metadata=TaskMetadata(dataset='synthetic', logic_heavy=True, repo_name='repo'),
    )

    result = evaluate_task_tests(repo, task, iteration=0)

    assert result.evaluated is True
    assert result.fail_to_pass.returncode == 1
    assert 'not found' not in result.fail_to_pass.stderr
    assert 'def test_empty' in (repo / 'tests' / 'test_logic.py').read_text(encoding='utf-8')


def test_synthetic_cegf_pipeline_writes_run_artifacts(tmp_path: Path, monkeypatch) -> None:
    repo = _fixture_repo(tmp_path)
    task = _task(repo)
    output_dir = tmp_path / 'artifacts' / 'runs' / '20260503_120000_test_neural-cegf_z3_s0'

    def fake_generate_patch(*args, **kwargs) -> PatchContract:
        return PatchContract(
            patch_id='patch1',
            task_id=task.task_id,
            iteration=kwargs['iteration'],
            raw_text=f'```diff\n{PATCH_DIFF}```',
            diff=PATCH_DIFF,
            target_files=['pkg/logic.py'],
            parse_ok=True,
            model='test',
        )

    monkeypatch.setattr('symbiotic_swe.orchestration.loop.generate_patch', fake_generate_patch)

    results = run_benchmark(
        [task],
        conditions=['neural_cegf'],
        max_iterations=1,
        model='test',
        output_dir=output_dir,
        cache_root=tmp_path / 'cache',
        experiment_name='neural-cegf',
    )

    metrics = results['neural_cegf'][0]
    assert metrics.success is True
    assert metrics.test_resolved is True
    assert metrics.termination_reason == 'tests_resolved'

    for required in (
        'config.yaml',
        'run_manifest.json',
        'task_manifest.json',
        'metrics.json',
        'stage_timings.csv',
        'solver_results.jsonl',
        'patch_manifest.json',
        'evaluation_results.jsonl',
        'errors.log',
        'summary.md',
    ):
        assert (output_dir / required).exists()
