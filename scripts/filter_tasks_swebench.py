"""
Adapter script: exposes the task-loader scoring logic with a flat interface
expected by legacy tests and scripts.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from src.dataset.task_loader import (
    PREFERRED_REPOS,
    changed_files,
    collect_hits,
    count_changed_lines,
    label_task,
    LOGIC_PATCH_PATTERNS,
    LOGIC_TEXT_PATTERNS,
    NEGATIVE_PATCH_PATTERNS,
    NEGATIVE_TEXT_PATTERNS,
    _score_patch_size,
    _score_patch_signals,
    _score_text_signals,
    _score_labels,
    _score_repo,
    _negative_patch_exclusions,
    _negative_text_penalty,
)

__all__ = [
    'PREFERRED_REPOS',
    'balanced_take',
    'changed_files',
    'count_changed_lines',
    'label_task',
    'score_example',
]


@dataclass
class ScoredExample:
    instance_id: str
    repo: str
    score: int
    changed_lines: int
    changed_file_list: Tuple[str, ...]
    labels: Tuple[str, ...]
    include_for_logic: bool
    include_for_smoke: bool
    exclusion_reasons: Tuple[str, ...]


def score_example(
    example: Dict[str, Any],
    preferred_repos: Tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
) -> ScoredExample:
    repo = str(example.get('repo', ''))
    patch = str(example.get('patch', ''))
    combined_text = f"{example.get('problem_statement', '')} {example.get('hints_text', '')}"

    patch_hits = collect_hits(patch, LOGIC_PATCH_PATTERNS, multiline=True)
    text_hits = collect_hits(combined_text, LOGIC_TEXT_PATTERNS)
    negative_text_hits = collect_hits(combined_text, NEGATIVE_TEXT_PATTERNS)
    negative_patch_hits = collect_hits(patch, NEGATIVE_PATCH_PATTERNS, multiline=True)

    changed_line_count = count_changed_lines(patch)
    changed_file_list = changed_files(patch)
    labels = label_task(patch_hits, text_hits)

    score = 0
    exclusion_reasons: List[str] = []

    repo_score, repo_exclusions = _score_repo(repo, preferred_repos, repo_filter_mode)
    score += repo_score
    exclusion_reasons.extend(repo_exclusions)

    if not patch:
        exclusion_reasons.append('missing_patch')

    patch_size_score, patch_size_exclusions = _score_patch_size(
        changed_line_count, changed_file_list, max_changed_lines, max_changed_files
    )
    score += patch_size_score
    exclusion_reasons.extend(patch_size_exclusions)

    score += _score_patch_signals(patch_hits)
    score += _score_text_signals(text_hits)
    score += _score_labels(labels)
    score += _negative_text_penalty(negative_text_hits)

    neg_score, neg_exclusions = _negative_patch_exclusions(negative_patch_hits)
    score += neg_score
    exclusion_reasons.extend(neg_exclusions)

    include_for_logic = score >= min_logic_score and not exclusion_reasons
    include_for_smoke = (
        include_for_logic
        and changed_line_count <= 12
        and len(changed_file_list) == 1
    )

    return ScoredExample(
        instance_id=str(example.get('instance_id', '')),
        repo=repo,
        score=score,
        changed_lines=changed_line_count,
        changed_file_list=changed_file_list,
        labels=labels,
        include_for_logic=include_for_logic,
        include_for_smoke=include_for_smoke,
        exclusion_reasons=tuple(dict.fromkeys(exclusion_reasons)),
    )


def balanced_take(
    candidates: List[ScoredExample],
    limit: int,
    preferred_repos: Tuple[str, ...] = PREFERRED_REPOS,
) -> List[ScoredExample]:
    if limit <= 0:
        return []
    selected: List[ScoredExample] = []
    seen: set = set()
    grouped = {
        repo: [c for c in candidates if c.repo == repo]
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
            if candidate.instance_id in seen:
                continue
            selected.append(candidate)
            seen.add(candidate.instance_id)
            if len(selected) >= limit:
                return selected

    for candidate in candidates:
        if candidate.instance_id in seen:
            continue
        selected.append(candidate)
        seen.add(candidate.instance_id)
        if len(selected) >= limit:
            break
    return selected
