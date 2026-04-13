from scripts.filter_tasks_swebench import (
    PREFERRED_REPOS,
    balanced_take,
    changed_files,
    count_changed_lines,
    label_task,
    score_example,
)


def test_count_changed_lines_ignores_diff_headers() -> None:
    patch = """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,2 @@
-if x < 0:
+if x <= 0:
     return 1
"""
    assert count_changed_lines(patch) == 2


def test_changed_files_extracts_unique_targets() -> None:
    patch = """diff --git a/foo.py b/foo.py
diff --git a/bar.py b/bar.py
diff --git a/foo.py b/foo.py
"""
    assert changed_files(patch) == ('foo.py', 'bar.py')


def test_label_task_flags_logic_categories() -> None:
    patch_hits = {
        'branching': ['if'],
        'boolean_logic': ['and'],
        'comparisons': ['<='],
        'return_logic': ['return'],
        'arithmetic_logic': ['+'],
    }
    text_hits = {
        'edge_cases': ['empty'],
        'assertions': ['assert'],
        'conditional_reasoning': ['predicate'],
        'wrong_behavior': ['incorrect'],
    }
    assert label_task(patch_hits, text_hits) == (
        'arithmetic_predicate_bug',
        'relational_operator_bug',
        'assertion_violation_bug',
        'multi_conditional_reasoning_bug',
        'wrong_return_logic_bug',
        'edge_case_bug',
    )


def test_score_example_prefers_logic_heavy_small_patch() -> None:
    example = {
        'instance_id': 'sympy__sympy-1',
        'repo': 'sympy/sympy',
        'patch': """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,3 @@
-if value < 0:
+if value <= 0 and flag:
-    return total / count
+    return total + 1
""",
        'problem_statement': 'Incorrect edge case handling causes wrong return value and assertion failure.',
        'hints_text': '',
        'FAIL_TO_PASS': '["foo::test_bug"]',
    }

    candidate = score_example(
        example=example,
        preferred_repos=PREFERRED_REPOS,
        repo_filter_mode='preferred',
        max_changed_lines=30,
        max_changed_files=3,
    )

    assert candidate.include_for_logic is True
    assert candidate.include_for_smoke is True
    assert candidate.score >= 10
    assert 'edge_case_bug' in candidate.labels
    assert 'relational_operator_bug' in candidate.labels


def test_balanced_take_spreads_across_preferred_repos() -> None:
    candidates = [
        score_example(
            example={
                'instance_id': f'id-{index}',
                'repo': repo,
                'patch': """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,2 @@
-if x < 0:
+if x <= 0:
""",
                'problem_statement': 'Incorrect edge case condition.',
                'hints_text': '',
                'FAIL_TO_PASS': '["foo::test_bug"]',
            },
            preferred_repos=PREFERRED_REPOS,
            repo_filter_mode='preferred',
            max_changed_lines=30,
            max_changed_files=3,
        )
        for index, repo in enumerate(PREFERRED_REPOS[:3])
    ]

    selected = balanced_take(candidates, 2, PREFERRED_REPOS)

    assert len(selected) == 2
    assert selected[0].repo != selected[1].repo
