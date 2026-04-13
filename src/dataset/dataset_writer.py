from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.dataset.repo_indexer import PreparedTaskArtifact

if TYPE_CHECKING:
    from src.dataset.preparation import DatasetPreparationResult


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def _write_jsonl(path: Path, payloads: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for payload in payloads:
            handle.write(json.dumps(payload, sort_keys=True) + '\n')


def prepared_split_payload(
    artifacts: tuple[PreparedTaskArtifact, ...],
) -> list[dict[str, object]]:
    return [json.loads(artifact.task.model_dump_json()) for artifact in artifacts]


def write_prepared_tasks(result: DatasetPreparationResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_or_partial = [
        artifact
        for artifact in (
            *result.smoke_tasks,
            *result.dev_tasks,
            *result.final_eval_tasks,
        )
        if artifact.status in {'valid', 'partial'}
    ]

    _write_jsonl(
        output_dir / 'manifests' / 'dataset_manifest.jsonl',
        prepared_split_payload(tuple(valid_or_partial)),
    )
    _write_jsonl(
        output_dir / 'manifests' / 'smoke_tasks.jsonl',
        prepared_split_payload(result.smoke_tasks),
    )
    _write_jsonl(
        output_dir / 'manifests' / 'dev_tasks.jsonl',
        prepared_split_payload(result.dev_tasks),
    )
    _write_jsonl(
        output_dir / 'manifests' / 'final_eval_tasks.jsonl',
        prepared_split_payload(result.final_eval_tasks),
    )
    _write_jsonl(
        output_dir / 'logs' / 'malformed_tasks.jsonl',
        [asdict(error) for error in result.malformed_tasks],
    )
    _write_jsonl(
        output_dir / 'logs' / 'skipped_tasks.jsonl',
        [
            {
                'task_id': candidate.raw.instance_id,
                'repo': candidate.raw.repo,
                'score': candidate.score,
                'exclusion_reasons': list(candidate.exclusion_reasons),
                'labels': list(candidate.labels),
            }
            for candidate in result.skipped_tasks
        ],
    )
    _write_jsonl(
        output_dir / 'logs' / 'materialization_failures.jsonl',
        [
            {
                'task_id': artifact.task.task_id,
                'repo': artifact.task.repo,
                'status': artifact.status,
                'error': artifact.materialization.error,
                'source_repo_path': artifact.materialization.source_repo_path,
            }
            for artifact in result.repo_failures
        ],
    )
    _write_jsonl(
        output_dir / 'logs' / 'repo_parse_failures.jsonl',
        [
            {
                'task_id': artifact.task.task_id,
                'repo_index_path': artifact.repo_index.index_path,
                'parse_failures': list(artifact.repo_index.parse_failures),
            }
            for artifact in valid_or_partial
            if artifact.repo_index is not None
            and artifact.repo_index.parse_failure_count
        ],
    )

    valid_count = sum(1 for artifact in valid_or_partial if artifact.status == 'valid')
    partial_count = sum(
        1 for artifact in valid_or_partial if artifact.status == 'partial'
    )
    _write_json(
        output_dir / 'task_preparation_report.json',
        {
            'dataset': 'SWE-bench Verified',
            'tasks_loaded': len(result.raw_tasks),
            'tasks_filtered': len(result.skipped_tasks),
            'malformed_task_count': len(result.malformed_tasks),
            'repo_failures': len(result.repo_failures),
            'parse_failure_tasks': sum(
                1
                for artifact in valid_or_partial
                if artifact.repo_index is not None
                and artifact.repo_index.parse_failure_count
            ),
            'status_counts': {
                'valid': valid_count,
                'partial': partial_count,
                'invalid': len(result.repo_failures),
            },
            'subset_counts': {
                'smoke': len(result.smoke_tasks),
                'dev': len(result.dev_tasks),
                'final_eval': len(result.final_eval_tasks),
            },
        },
    )
    _write_json(
        output_dir / 'reproducibility_summary.json',
        {
            'generated_at': datetime.now(tz=UTC).isoformat(),
            'dataset_manifest_path': str(
                output_dir / 'manifests' / 'dataset_manifest.jsonl'
            ),
            'split_manifests': {
                'smoke': str(output_dir / 'manifests' / 'smoke_tasks.jsonl'),
                'dev': str(output_dir / 'manifests' / 'dev_tasks.jsonl'),
                'final_eval': str(output_dir / 'manifests' / 'final_eval_tasks.jsonl'),
            },
            'logs_dir': str(output_dir / 'logs'),
        },
    )
