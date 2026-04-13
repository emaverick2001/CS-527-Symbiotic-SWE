from __future__ import annotations

"""
Task loading, normalization, scoring, and subset selection for benchmark rows.

This module is responsible for turning raw SWE-bench-style JSONL rows into a
normalized internal task representation, scoring tasks for logic-heavy
characteristics, and selecting subsets for smoke/dev/final evaluation runs.

Main flow:
1. Load raw rows from a JSONL file.
2. Normalize dataset-specific field names into a common shape.
3. Validate required fields and collect row-level errors.
4. Score tasks using patch/text heuristics.
5. Select balanced subsets for smoke, dev, and final evaluation.

Typical usage:
    loader = TaskLoader(TaskLoaderConfig())
    tasks, errors = loader.load_raw_tasks(Path("data/benchmarks/.../test.jsonl"))
    candidates = loader.score_tasks(tasks)
    smoke, dev, final_eval, skipped = loader.select_subsets(candidates)

Key outputs:
- `TaskObject`: normalized benchmark task record
- `RawTaskError`: validation or parsing failure for a row
- `CandidateTask`: scored task with selection metadata

CLI Usage:
    poetry run python -m src.dataset.task_loader \\
        --input-jsonl data/benchmarks/swe_bench/verified/jsonl/test.jsonl \\
        --output-dir data/benchmarks/swe_bench/verified/filtered \\
        --smoke-count 5 \\
        --core-count 40 \\
        --repo-filter-mode preferred
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.contracts import TaskContract

PREFERRED_REPOS = (
    'sympy/sympy',
    'pandas-dev/pandas',
    'numpy/numpy',
    'scikit-learn/scikit-learn',
    'matplotlib/matplotlib',
)

REPO_FILTER_MODES = ('preferred', 'strict', 'none')
SUPPORTED_DATASET_SOURCES = ('swe_bench_verified', 'synthetic_humaneval_bugfix')

LOGIC_PATCH_PATTERNS = {
    'branching': [r'^[+-]\s*if\b', r'^[+-]\s*elif\b', r'^[+-]\s*else\b'],
    'boolean_logic': [r'^[+-].*\band\b', r'^[+-].*\bor\b', r'^[+-].*\bnot\b'],
    'comparisons': [
        r'==',
        r'!=',
        r'<=',
        r'>=',
        r'(?<![<>=!])<(?![=])',
        r'(?<![<>=!])>(?![=])',
    ],
    'return_logic': [r'^[+-]\s*return\b'],
    'arithmetic_logic': [r'^[+-].*[+\-*/%]', r'^[+-].*\b(sum|min|max|abs|len)\('],
}

LOGIC_TEXT_PATTERNS = {
    'edge_cases': [
        r'\bedge case\b',
        r'\bempty\b',
        r'\bzero\b',
        r'\bnone\b',
        r'\bboundary\b',
        r'\boff[- ]by[- ]one\b',
        r'\bcorner case\b',
    ],
    'assertions': [r'\bassert(?:ion)?\b', r'\braise(?:s|d)?\b', r'\bexception\b'],
    'conditional_reasoning': [
        r'\bcondition(?:al)?\b',
        r'\bpredicate\b',
        r'\bcomparison\b',
        r'\bboolean\b',
        r'\blogic(?:al)?\b',
    ],
    'wrong_behavior': [
        r'\bwrong return\b',
        r'\bwrong result\b',
        r'\bincorrect\b',
        r'\bunexpected\b',
        r'\bshould return\b',
        r'\bshould not\b',
    ],
}

NEGATIVE_TEXT_PATTERNS = {
    'dependency_change': [r'\bdependency\b', r'\bversion mismatch\b'],
    'import_fix': [r'\bimport error\b', r'\bmissing import\b'],
    'config_change': [r'\bconfig(?:uration)?\b'],
}

NEGATIVE_PATCH_PATTERNS = {
    'dependency_change': [
        r'pyproject\.toml',
        r'requirements',
        r'setup\.py',
        r'poetry\.lock',
        r'Pipfile',
    ],
    'import_fix': [r'^[+-]\s*import\b', r'^[+-]\s*from\b'],
    'config_change': [r'tox\.ini', r'\.coveragerc', r'pytest\.ini', r'conf(?:ig)?'],
}

REQUIRED_RAW_FIELDS = (
    'instance_id',
    'repo',
    'base_commit',
    'problem_statement',
    'FAIL_TO_PASS',
)


@dataclass(frozen=True)
class TaskObject:
    dataset: str
    dataset_source: str
    split: str
    source_path: str
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    failing_tests: tuple[str, ...]
    passing_tests: tuple[str, ...]
    patch: str | None
    test_patch: str | None
    hints_text: str
    difficulty: str | None
    execution_trace: tuple[str, ...]
    constraint_spec: dict[str, Any] | list[Any] | str | None
    raw_fields: dict[str, Any]


@dataclass(frozen=True)
class RawTaskError:
    source_path: str
    row_number: int
    reason: str
    raw_fields: dict[str, Any]


@dataclass(frozen=True)
class CandidateTask:
    raw: TaskObject
    score: int
    changed_lines: int
    changed_files: tuple[str, ...]
    labels: tuple[str, ...]
    logic_heavy: bool
    include_for_smoke: bool
    exclusion_reasons: tuple[str, ...]


@dataclass(frozen=True)
class NormalizedArtifactPaths:
    candidate_path: Path
    normalized_path: Path
    raw_fields_path: Path
    malformed_path: Path | None = None


@dataclass(frozen=True)
class TaskLoaderConfig:
    dataset_name: str = 'SWE-bench Verified'
    split: str = 'test'
    dataset_source: str | None = None
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS
    repo_filter_mode: str = 'preferred'
    smoke_count: int = 5
    dev_count: int = 10
    final_eval_count: int = 40
    max_changed_lines: int = 30
    max_changed_files: int = 3
    min_logic_score: int = 6


def infer_dataset_source(dataset_name: str) -> str:
    normalized = dataset_name.strip().lower().replace('-', '_').replace(' ', '_')
    if 'swe' in normalized and 'bench' in normalized:
        return 'swe_bench_verified'
    if 'humaneval' in normalized:
        return 'synthetic_humaneval_bugfix'
    return normalized


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding='utf-8') as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def parse_test_list(raw_value: Any) -> list[str]:
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value]
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(raw_value)
            except (ValueError, SyntaxError):
                return [raw_value]
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return [str(parsed)]
    return [str(raw_value)]


def normalize_trace(raw_value: Any) -> tuple[str, ...]:
    if isinstance(raw_value, list):
        return tuple(str(item) for item in raw_value)
    if isinstance(raw_value, str) and raw_value.strip():
        return (raw_value,)
    return ()


def _first_present(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ''):
            return row[key]
    return None


def normalize_benchmark_row(
    row: dict[str, Any],
    dataset_source: str,
) -> dict[str, Any]:
    if dataset_source == 'swe_bench_verified':
        return dict(row)

    if dataset_source == 'synthetic_humaneval_bugfix':
        normalized = dict(row)
        normalized.setdefault(
            'instance_id',
            _first_present(row, 'instance_id', 'task_id', 'problem_id'),
        )
        normalized.setdefault('repo', _first_present(row, 'repo', 'repo_identifier'))
        normalized.setdefault(
            'base_commit',
            _first_present(row, 'base_commit', 'repo_commit', 'commit'),
        )
        normalized.setdefault(
            'problem_statement',
            _first_present(row, 'problem_statement', 'bug_report', 'prompt'),
        )
        normalized.setdefault(
            'FAIL_TO_PASS',
            _first_present(row, 'FAIL_TO_PASS', 'failing_tests'),
        )
        normalized.setdefault(
            'PASS_TO_PASS',
            _first_present(row, 'PASS_TO_PASS', 'passing_tests'),
        )
        normalized.setdefault('patch', _first_present(row, 'patch', 'gold_patch'))
        normalized.setdefault('test_patch', _first_present(row, 'test_patch'))
        normalized.setdefault('hints_text', _first_present(row, 'hints_text', 'hints'))
        normalized.setdefault('difficulty', _first_present(row, 'difficulty'))
        normalized.setdefault(
            'constraint_spec',
            _first_present(row, 'constraint_spec', 'oracle', 'logical_constraints'),
        )
        normalized.setdefault(
            'execution_trace',
            _first_present(row, 'execution_trace', 'trace'),
        )
        return normalized

    raise ValueError(f'Unsupported dataset_source: {dataset_source}')


def missing_required_fields(row: dict[str, Any]) -> tuple[str, ...]:
    missing: list[str] = []
    for field in REQUIRED_RAW_FIELDS:
        value = row.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)
    if not parse_test_list(row.get('FAIL_TO_PASS')):
        missing.append('FAIL_TO_PASS')
    return tuple(dict.fromkeys(missing))


def find_hits(text: str, patterns: list[str], multiline: bool = False) -> list[str]:
    flags = re.IGNORECASE | (re.MULTILINE if multiline else 0)
    return [pattern for pattern in patterns if re.search(pattern, text, flags)]


def collect_hits(
    text: str,
    pattern_groups: dict[str, list[str]],
    multiline: bool = False,
) -> dict[str, list[str]]:
    return {
        label: find_hits(text, patterns, multiline=multiline)
        for label, patterns in pattern_groups.items()
    }


def count_changed_lines(patch: str) -> int:
    changed = 0
    for line in patch.splitlines():
        if line.startswith(('+++', '---', '@@')):
            continue
        if line.startswith('+') or line.startswith('-'):
            changed += 1
    return changed


def changed_files(patch: str) -> tuple[str, ...]:
    files: list[str] = []
    for line in patch.splitlines():
        if line.startswith('diff --git '):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[2].removeprefix('a/'))
        elif line.startswith('--- a/'):
            files.append(line.removeprefix('--- a/'))
    return tuple(dict.fromkeys(files))


def label_task(
    patch_hits: dict[str, list[str]],
    text_hits: dict[str, list[str]],
) -> tuple[str, ...]:
    labels: list[str] = []
    if patch_hits['arithmetic_logic']:
        labels.append('arithmetic_predicate_bug')
    if patch_hits['comparisons']:
        labels.append('relational_operator_bug')
    if text_hits['assertions']:
        labels.append('assertion_violation_bug')
    if patch_hits['branching'] and (
        patch_hits['boolean_logic'] or len(patch_hits['comparisons']) >= 2
    ):
        labels.append('multi_conditional_reasoning_bug')
    if patch_hits['return_logic'] or text_hits['wrong_behavior']:
        labels.append('wrong_return_logic_bug')
    if text_hits['edge_cases']:
        labels.append('edge_case_bug')
    return tuple(dict.fromkeys(labels))


def _score_repo(
    repo: str,
    preferred_repos: tuple[str, ...],
    repo_filter_mode: str,
) -> tuple[int, list[str]]:
    if repo in preferred_repos:
        return 4, []
    if repo_filter_mode == 'strict':
        return 0, ['repo_not_preferred']
    return 0, []


def _score_patch_size(
    changed_line_count: int,
    changed_file_list: tuple[str, ...],
    max_changed_lines: int,
    max_changed_files: int,
) -> tuple[int, list[str]]:
    score = 0
    exclusions: list[str] = []
    if changed_line_count <= 12:
        score += 4
    elif changed_line_count <= 20:
        score += 2
    elif changed_line_count <= max_changed_lines:
        score += 1
    else:
        exclusions.append('patch_too_large')
        score -= 8

    if len(changed_file_list) == 1:
        score += 2
    elif len(changed_file_list) <= max_changed_files:
        score += 1
    else:
        exclusions.append('too_many_files_changed')
        score -= 6
    return score, exclusions


def _score_patch_signals(patch_hits: dict[str, list[str]]) -> int:
    score = 0
    for label, hits in patch_hits.items():
        if hits:
            score += 2
            if label in {'comparisons', 'branching', 'boolean_logic'}:
                score += 1
    return score


def _score_text_signals(text_hits: dict[str, list[str]]) -> int:
    return sum(1 for hits in text_hits.values() if hits)


def _score_labels(labels: tuple[str, ...]) -> int:
    score = 0
    if len(labels) >= 2:
        score += 2
    if 'multi_conditional_reasoning_bug' in labels:
        score += 2
    return score


def _negative_text_penalty(negative_text_hits: dict[str, list[str]]) -> int:
    return -sum(1 for hits in negative_text_hits.values() if hits)


def _negative_patch_exclusions(
    negative_patch_hits: dict[str, list[str]],
) -> tuple[int, list[str]]:
    score = 0
    exclusions: list[str] = []
    for category, hits in negative_patch_hits.items():
        if not hits:
            continue
        score -= 3
        exclusions.append(category)
    return score, exclusions


def score_candidate(
    task: TaskObject,
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
) -> CandidateTask:
    patch = task.patch or ''
    combined_text = f'{task.problem_statement}\n{task.hints_text}'
    patch_hits = collect_hits(patch, LOGIC_PATCH_PATTERNS, multiline=True)
    text_hits = collect_hits(combined_text, LOGIC_TEXT_PATTERNS)
    negative_text_hits = collect_hits(combined_text, NEGATIVE_TEXT_PATTERNS)
    negative_patch_hits = collect_hits(patch, NEGATIVE_PATCH_PATTERNS, multiline=True)
    changed_line_count = count_changed_lines(patch)
    changed_file_list = changed_files(patch)
    labels = label_task(patch_hits, text_hits)

    score = 0
    exclusion_reasons: list[str] = []

    repo_score, repo_exclusions = _score_repo(
        task.repo,
        preferred_repos,
        repo_filter_mode,
    )
    score += repo_score
    exclusion_reasons.extend(repo_exclusions)

    if not patch:
        exclusion_reasons.append('missing_patch')

    patch_size_score, patch_size_exclusions = _score_patch_size(
        changed_line_count,
        changed_file_list,
        max_changed_lines,
        max_changed_files,
    )
    score += patch_size_score
    exclusion_reasons.extend(patch_size_exclusions)

    if len(task.failing_tests) <= 2:
        score += 1

    score += _score_patch_signals(patch_hits)
    score += _score_text_signals(text_hits)
    score += _score_labels(labels)
    score += _negative_text_penalty(negative_text_hits)

    negative_patch_score, negative_patch_exclusions = _negative_patch_exclusions(
        negative_patch_hits
    )
    score += negative_patch_score
    exclusion_reasons.extend(negative_patch_exclusions)

    logic_heavy = score >= min_logic_score and not exclusion_reasons
    include_for_smoke = (
        logic_heavy
        and changed_line_count <= 12
        and len(changed_file_list) == 1
        and len(task.failing_tests) <= 2
    )
    return CandidateTask(
        raw=task,
        score=score,
        changed_lines=changed_line_count,
        changed_files=changed_file_list,
        labels=labels,
        logic_heavy=logic_heavy,
        include_for_smoke=include_for_smoke,
        exclusion_reasons=tuple(dict.fromkeys(exclusion_reasons)),
    )


def balanced_take(
    candidates: list[CandidateTask],
    limit: int,
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
) -> list[CandidateTask]:
    if limit <= 0:
        return []

    selected: list[CandidateTask] = []
    seen: set[str] = set()
    grouped = {
        repo: [candidate for candidate in candidates if candidate.raw.repo == repo]
        for repo in preferred_repos
    }
    grouped = {repo: rows for repo, rows in grouped.items() if rows}
    max_len = max((len(rows) for rows in grouped.values()), default=0)

    for index in range(max_len):
        for repo in preferred_repos:
            rows = grouped.get(repo, [])
            if index >= len(rows):
                continue
            candidate = rows[index]
            if candidate.raw.instance_id in seen:
                continue
            selected.append(candidate)
            seen.add(candidate.raw.instance_id)
            if len(selected) >= limit:
                return selected

    for candidate in candidates:
        if candidate.raw.instance_id in seen:
            continue
        selected.append(candidate)
        seen.add(candidate.raw.instance_id)
        if len(selected) >= limit:
            break
    return selected


def sort_candidates(candidates: list[CandidateTask]) -> list[CandidateTask]:
    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate.score,
            candidate.changed_lines,
            candidate.raw.repo,
            candidate.raw.instance_id,
        ),
    )


def build_task_subsets(
    candidates: list[CandidateTask],
    smoke_count: int = 5,
    dev_count: int = 10,
    final_eval_count: int = 40,
    preferred_repos: tuple[str, ...] = PREFERRED_REPOS,
) -> tuple[
    list[CandidateTask], list[CandidateTask], list[CandidateTask], list[CandidateTask]
]:
    usable = sort_candidates(
        [candidate for candidate in candidates if not candidate.exclusion_reasons]
    )
    skipped = sort_candidates(
        [candidate for candidate in candidates if candidate.exclusion_reasons]
    )

    smoke_candidates = [
        candidate for candidate in usable if candidate.include_for_smoke
    ]
    smoke_tasks = balanced_take(smoke_candidates, smoke_count, preferred_repos)
    used_ids = {candidate.raw.instance_id for candidate in smoke_tasks}

    remaining_logic = [
        candidate
        for candidate in usable
        if candidate.logic_heavy and candidate.raw.instance_id not in used_ids
    ]
    dev_tasks = balanced_take(remaining_logic, dev_count, preferred_repos)
    used_ids.update(candidate.raw.instance_id for candidate in dev_tasks)

    remaining_for_final = [
        candidate
        for candidate in usable
        if candidate.logic_heavy and candidate.raw.instance_id not in used_ids
    ]
    final_eval_tasks = balanced_take(
        remaining_for_final,
        final_eval_count,
        preferred_repos,
    )
    return smoke_tasks, dev_tasks, final_eval_tasks, skipped


def raw_subset_rows(candidates: list[CandidateTask]) -> list[dict[str, Any]]:
    return [dict(candidate.raw.raw_fields) for candidate in candidates]


def write_raw_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row) + '\n')


class TaskLoader:
    """Load benchmark rows, validate required fields, and select logic-heavy tasks."""

    def __init__(self, config: TaskLoaderConfig | None = None) -> None:
        self.config = config or TaskLoaderConfig()
        self.dataset_source = self.config.dataset_source or infer_dataset_source(
            self.config.dataset_name
        )
        if self.dataset_source not in SUPPORTED_DATASET_SOURCES:
            raise ValueError(f'Unsupported dataset_source: {self.dataset_source}')

    def validate_row(
        self,
        row: dict[str, Any],
        row_number: int,
        input_path: Path,
    ) -> tuple[TaskObject | None, RawTaskError | None]:
        normalized_row = normalize_benchmark_row(row, self.dataset_source)
        missing_fields = missing_required_fields(normalized_row)
        if missing_fields:
            return None, RawTaskError(
                source_path=str(input_path),
                row_number=row_number,
                reason=f'missing_required_fields:{",".join(missing_fields)}',
                raw_fields=row,
            )

        return (
            TaskObject(
                dataset=self.config.dataset_name,
                dataset_source=self.dataset_source,
                split=self.config.split,
                source_path=str(input_path),
                instance_id=str(normalized_row['instance_id']),
                repo=str(normalized_row['repo']),
                base_commit=str(normalized_row['base_commit']),
                problem_statement=str(normalized_row['problem_statement']),
                failing_tests=tuple(
                    parse_test_list(normalized_row.get('FAIL_TO_PASS'))
                ),
                passing_tests=tuple(
                    parse_test_list(normalized_row.get('PASS_TO_PASS'))
                ),
                patch=str(normalized_row['patch'])
                if normalized_row.get('patch')
                else None,
                test_patch=str(normalized_row['test_patch'])
                if normalized_row.get('test_patch')
                else None,
                hints_text=str(normalized_row.get('hints_text') or ''),
                difficulty=str(normalized_row.get('difficulty'))
                if normalized_row.get('difficulty')
                else None,
                execution_trace=normalize_trace(
                    normalized_row.get('execution_trace') or normalized_row.get('trace')
                ),
                constraint_spec=normalized_row.get('constraint_spec')
                or normalized_row.get('oracle'),
                raw_fields=row,
            ),
            None,
        )

    def load_raw_tasks(
        self,
        input_path: Path,
    ) -> tuple[list[TaskObject], list[RawTaskError]]:
        raw_rows = parse_jsonl(input_path)
        tasks: list[TaskObject] = []
        errors: list[RawTaskError] = []

        for index, row in enumerate(raw_rows, start=1):
            task, error = self.validate_row(row, index, input_path)
            if error is not None:
                errors.append(error)
                continue
            if task is not None:
                tasks.append(task)

        return tasks, errors

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

    def normalize_task(self, candidate: CandidateTask, subset: str) -> TaskContract:
        return TaskNormalizer().normalize_task(candidate, subset)

    def write_normalized_artifacts(
        self,
        task: TaskContract,
        candidate: CandidateTask,
        output_dir: Path,
        malformed_rows: list[RawTaskError] | None = None,
    ) -> NormalizedArtifactPaths:
        return TaskNormalizer().write_normalized_artifacts(
            task=task,
            candidate=candidate,
            output_dir=output_dir,
            malformed_rows=malformed_rows,
        )

    def write_normalized_preview(
        self,
        task: TaskContract,
        candidate: CandidateTask,
        malformed_rows: list[RawTaskError],
        output_dir: Path,
    ) -> tuple[Path, Path, Path]:
        return TaskNormalizer().write_normalized_preview(
            task=task,
            candidate=candidate,
            malformed_rows=malformed_rows,
            output_dir=output_dir,
        )

    def select_subsets(
        self,
        candidates: list[CandidateTask],
    ) -> tuple[
        list[CandidateTask],
        list[CandidateTask],
        list[CandidateTask],
        list[CandidateTask],
    ]:
        return build_task_subsets(
            candidates,
            smoke_count=self.config.smoke_count,
            dev_count=self.config.dev_count,
            final_eval_count=self.config.final_eval_count,
            preferred_repos=self.config.preferred_repos,
        )


def _build_cli_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description='Rank raw SWE-bench Verified tasks and export raw subset JSONL files.',
    )
    parser.add_argument(
        '--input-jsonl',
        type=Path,
        default=project_root
        / 'data'
        / 'benchmarks'
        / 'swe_bench'
        / 'verified'
        / 'jsonl'
        / 'test.jsonl',
        help='Path to the raw SWE-bench Verified JSONL file.',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=project_root
        / 'data'
        / 'benchmarks'
        / 'swe_bench'
        / 'verified'
        / 'filtered',
        help='Directory where raw filtered subset files should be written.',
    )
    parser.add_argument(
        '--repo-filter-mode',
        choices=REPO_FILTER_MODES,
        default='preferred',
        help='Repo filtering mode used while scoring raw tasks.',
    )
    parser.add_argument(
        '--core-count',
        type=int,
        default=40,
        help='Number of top logic-heavy tasks to write to core_tasks.jsonl.',
    )
    parser.add_argument(
        '--smoke-count',
        type=int,
        default=5,
        help='Number of smoke tasks to write to smoke_tasks.jsonl.',
    )
    parser.add_argument(
        '--max-changed-lines',
        type=int,
        default=30,
        help='Maximum changed lines allowed when scoring/filtering.',
    )
    parser.add_argument(
        '--max-changed-files',
        type=int,
        default=3,
        help='Maximum changed files allowed when scoring/filtering.',
    )
    parser.add_argument(
        '--min-logic-score',
        type=int,
        default=6,
        help='Minimum internal score for logic-heavy inclusion.',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite filtered output files even if they already exist.',
    )
    return parser


def export_ranked_raw_subsets(
    loader: TaskLoader,
    input_path: Path,
    output_dir: Path,
    core_count: int,
    smoke_count: int,
    force: bool = False,
) -> tuple[Path, Path, int, int, int, int]:
    raw_tasks, malformed_rows = loader.load_raw_tasks(input_path)
    candidates = loader.score_tasks(raw_tasks)
    smoke_candidates, _dev_candidates, core_candidates, skipped = loader.select_subsets(
        candidates
    )

    core_path = output_dir / 'core_tasks.jsonl'
    smoke_path = output_dir / 'smoke_tasks.jsonl'
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_smoke = smoke_candidates[:smoke_count]
    selected_core = core_candidates[:core_count]

    if force or not smoke_path.exists():
        write_raw_jsonl(smoke_path, raw_subset_rows(selected_smoke))
    if force or not core_path.exists():
        write_raw_jsonl(core_path, raw_subset_rows(selected_core))

    return (
        smoke_path,
        core_path,
        len(raw_tasks),
        len(malformed_rows),
        len(selected_smoke),
        len(selected_core),
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    input_path = args.input_jsonl.resolve()
    output_dir = args.output_dir.resolve()
    loader = TaskLoader(
        TaskLoaderConfig(
            repo_filter_mode=args.repo_filter_mode,
            smoke_count=args.smoke_count,
            final_eval_count=args.core_count,
            dev_count=0,
            max_changed_lines=args.max_changed_lines,
            max_changed_files=args.max_changed_files,
            min_logic_score=args.min_logic_score,
        )
    )
    (
        smoke_path,
        core_path,
        loaded_count,
        malformed_count,
        smoke_written,
        core_written,
    ) = export_ranked_raw_subsets(
        loader=loader,
        input_path=input_path,
        output_dir=output_dir,
        core_count=args.core_count,
        smoke_count=args.smoke_count,
        force=args.force,
    )

    print(f'Loaded raw tasks: {loaded_count}')
    print(f'Malformed rows skipped: {malformed_count}')
    print(f'Smoke tasks selected: {smoke_written}')
    print(f'Core tasks selected: {core_written}')
    print(f'Smoke tasks file: {smoke_path}')
    print(f'Core tasks file: {core_path}')
    if not args.force:
        print('Existing files were preserved unless missing. Use --force to overwrite.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
