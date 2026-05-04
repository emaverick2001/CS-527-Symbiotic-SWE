from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from symbiotic_swe.contracts import PreparedTaskArtifact
from symbiotic_swe.dataset.repo_indexer import RepositoryIndexer, RepositoryIndexerConfig
from symbiotic_swe.dataset.task_loader import TaskLoader, TaskLoaderConfig
from symbiotic_swe.dataset.task_normalizer import TaskNormalizer
from src.dataset.task_loader import (
    PREFERRED_REPOS,
    CandidateTask,
    RawTaskError,
    TaskObject,
)
from src.dataset.dataset_writer import write_jsonl


@dataclass
class DatasetPreparationResult:
    raw_tasks: Tuple[TaskObject, ...]
    malformed_tasks: Tuple[RawTaskError, ...]
    repo_failures: Tuple[PreparedTaskArtifact, ...]
    smoke_tasks: Tuple[PreparedTaskArtifact, ...]
    dev_tasks: Tuple[PreparedTaskArtifact, ...]
    final_eval_tasks: Tuple[PreparedTaskArtifact, ...]
    output_dir: Path


def _write_report(output_dir: Path, result: DatasetPreparationResult) -> None:
    status_counts: Dict[str, int] = {}
    all_artifacts = (
        list(result.smoke_tasks)
        + list(result.dev_tasks)
        + list(result.final_eval_tasks)
        + list(result.repo_failures)
    )
    for art in all_artifacts:
        s = art.task.metadata.status
        status_counts[s] = status_counts.get(s, 0) + 1

    report = {
        'tasks_loaded': len(result.raw_tasks),
        'malformed_task_count': len(result.malformed_tasks),
        'repo_failures': len(result.repo_failures),
        'smoke_count': len(result.smoke_tasks),
        'dev_count': len(result.dev_tasks),
        'final_eval_count': len(result.final_eval_tasks),
        'status_counts': status_counts,
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
    }
    (output_dir / 'task_preparation_report.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8'
    )

    summary = {
        'schema_version': '0.1.0',
        'tasks_loaded': len(result.raw_tasks),
        'malformed': len(result.malformed_tasks),
        'prepared': len(result.smoke_tasks) + len(result.dev_tasks) + len(result.final_eval_tasks),
        'repo_failures': len(result.repo_failures),
    }
    (output_dir / 'reproducibility_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )


def _write_manifest(output_dir: Path, artifacts: List[PreparedTaskArtifact]) -> None:
    rows = [
        {
            'task_id': a.task.task_id,
            'repo': a.task.repo,
            'subset': a.task.metadata.subset,
            'status': a.status,
            'artifact_dir': a.artifact_dir,
        }
        for a in artifacts
    ]
    manifest_path = output_dir / 'manifests' / 'dataset_manifest.jsonl'
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(manifest_path, rows)


def _write_failure_logs(
    output_dir: Path,
    malformed: List[RawTaskError],
    failures: List[PreparedTaskArtifact],
) -> None:
    logs_dir = output_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    mat_failures = [
        {'task_id': a.task.task_id, 'error': a.error or 'unknown'}
        for a in failures
    ]
    write_jsonl(logs_dir / 'materialization_failures.jsonl', mat_failures)

    parse_fails = []
    for a in failures:
        if a.repo_index:
            for f in a.repo_index.files:
                if f.parse_failed:
                    parse_fails.append({'task_id': a.task.task_id, 'file': f.path})
    write_jsonl(logs_dir / 'repo_parse_failures.jsonl', parse_fails)


def prepare_swe_bench_tasks(
    input_path: Path,
    output_dir: Path,
    dataset_name: str = 'SWE-bench Verified',
    split: str = 'test',
    preferred_repos: Tuple[str, ...] = PREFERRED_REPOS,
    repo_filter_mode: str = 'preferred',
    smoke_count: int = 5,
    dev_count: int = 20,
    final_eval_count: int = 40,
    max_changed_lines: int = 30,
    max_changed_files: int = 3,
    min_logic_score: int = 6,
    repo_source_overrides: Optional[Dict[str, Any]] = None,
    workspace_root: Optional[Path] = None,
    cache_root: Optional[Path] = None,
) -> DatasetPreparationResult:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    loader = TaskLoader(TaskLoaderConfig(
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
    ))
    normalizer = TaskNormalizer()
    indexer = RepositoryIndexer(RepositoryIndexerConfig(
        workspace_root=workspace_root or output_dir / 'workspaces',
        cache_root=cache_root or output_dir / '.cache',
        repo_source_overrides={
            k: Path(v) for k, v in (repo_source_overrides or {}).items()
        },
    ))

    raw_tasks, malformed_tasks = loader.load_raw_tasks(input_path)
    candidates = loader.score_tasks(raw_tasks)
    smoke_cands, dev_cands, final_cands, _skipped = loader.select_subsets(candidates)

    def _prepare(cands: List[CandidateTask], subset: str) -> Tuple[List[PreparedTaskArtifact], List[PreparedTaskArtifact]]:
        ok: List[PreparedTaskArtifact] = []
        failures: List[PreparedTaskArtifact] = []
        for cand in cands:
            norm = normalizer.normalize_task(cand, subset)
            art = indexer.prepare_task(norm, cand.raw, subset, output_dir, timestamp)
            # Count as repo_failure when materialization itself failed (no usable repo)
            if art.task.repo_path is None or art.error is not None:
                failures.append(art)
            else:
                ok.append(art)
        return ok, failures

    smoke_ok, smoke_fail = _prepare(smoke_cands[:smoke_count], 'smoke')
    dev_ok, dev_fail = _prepare(dev_cands[:dev_count], 'dev')
    final_ok, final_fail = _prepare(final_cands[:final_eval_count], 'final_eval')

    all_failures = smoke_fail + dev_fail + final_fail
    all_ok = smoke_ok + dev_ok + final_ok

    # Write logs/manifest/reports
    _write_manifest(output_dir, all_ok + all_failures)
    _write_failure_logs(output_dir, list(malformed_tasks), all_failures)

    result = DatasetPreparationResult(
        raw_tasks=tuple(raw_tasks),
        malformed_tasks=tuple(malformed_tasks),
        repo_failures=tuple(all_failures),
        smoke_tasks=tuple(smoke_ok),
        dev_tasks=tuple(dev_ok),
        final_eval_tasks=tuple(final_ok),
        output_dir=output_dir,
    )
    _write_report(output_dir, result)
    return result
