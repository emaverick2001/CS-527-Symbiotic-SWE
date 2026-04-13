from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from src.cache import cache_manifest
from src.constants import (
    FAILURE_LOG_TYPES,
    REQUESTED_CONFIG_SNAPSHOT_FILENAME,
    RESOLVED_CONFIG_SNAPSHOT_FILENAME,
)
from src.models import ExecutionMode, RunRequest
from src.orchestration.pipeline import PIPELINE_STAGES
from src.schemas import dump_resolved_config, load_resolved_config
from src.versions import PROMPT_VERSION, SCHEMA_VERSION, version_manifest
from src.workspace import RunLayout, TaskLayout, build_run_layout


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )


def _write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding='utf-8')


def _seed_run_files(run_layout: RunLayout, config_path: Path) -> dict[str, object]:
    _write_text(run_layout.run_log_path, '')
    _write_text(run_layout.error_log_path, '')
    requested_snapshot_path = run_layout.root / REQUESTED_CONFIG_SNAPSHOT_FILENAME
    resolved_snapshot_path = run_layout.root / RESOLVED_CONFIG_SNAPSHOT_FILENAME
    resolved_config = load_resolved_config(config_path)
    resolved_config_payload = dump_resolved_config(resolved_config)

    _write_text(requested_snapshot_path, config_path.read_text(encoding='utf-8'))
    _write_json(resolved_snapshot_path, resolved_config_payload)
    return {
        'requested_snapshot_path': str(requested_snapshot_path),
        'resolved_snapshot_path': str(resolved_snapshot_path),
        'resolved_config': resolved_config_payload,
        'cache_manifest': cache_manifest(
            resolved_config,
            run_layout.run_id,
            run_layout.cache_root,
        ),
    }


def _scaffold_task(layout: TaskLayout, max_iterations: int) -> dict[str, object]:
    layout.create()
    _write_text(layout.logs_dir / 'task.log', '')
    _write_text(layout.solver_logs_dir / 'solver.log', '')
    _write_text(layout.patch_logs_dir / 'patch.log', '')
    _write_text(layout.error_logs_dir / 'errors.log', '')
    _write_text(layout.patch_apply_failure_log_path, '')
    _write_text(layout.ast_parse_failure_log_path, '')
    _write_text(layout.solver_timeout_log_path, '')
    _write_text(layout.unsupported_symbolic_construct_log_path, '')

    for iteration in range(max_iterations):
        iteration_dir = layout.iteration_dir(iteration)
        iteration_dir.mkdir(parents=True, exist_ok=True)
        for stage in PIPELINE_STAGES:
            stage_dir = layout.stage_dir(iteration, stage.key)
            stage_dir.mkdir(parents=True, exist_ok=True)
            _write_json(
                stage_dir / 'placeholder.json',
                {
                    'schema_version': SCHEMA_VERSION,
                    'prompt_version': PROMPT_VERSION,
                    'iteration': iteration,
                    'stage': stage.key,
                    'description': stage.description,
                    'status': 'placeholder',
                },
            )

    task_manifest = {
        'schema_version': SCHEMA_VERSION,
        'task_id': layout.task_id,
        'workspace_repo': str(layout.repo_dir),
        'artifact_root': str(layout.artifact_dir),
        'logs': {
            'task_log': str(layout.logs_dir / 'task.log'),
            'solver_log': str(layout.solver_logs_dir / 'solver.log'),
            'patch_log': str(layout.patch_logs_dir / 'patch.log'),
            'error_log': str(layout.error_logs_dir / 'errors.log'),
            'failure_logs': {
                'patch_apply_failure': str(layout.patch_apply_failure_log_path),
                'ast_parse_failure': str(layout.ast_parse_failure_log_path),
                'solver_timeout': str(layout.solver_timeout_log_path),
                'unsupported_symbolic_construct': str(
                    layout.unsupported_symbolic_construct_log_path
                ),
            },
        },
        'iterations': [
            {
                'iteration_id': f'iter_{iteration:03d}',
                'stages': [stage.key for stage in PIPELINE_STAGES],
            }
            for iteration in range(max_iterations)
        ],
    }
    _write_json(layout.summary_dir / 'task_layout.json', task_manifest)
    return task_manifest


def execute_run(request: RunRequest, root: Path | None = None) -> RunLayout:
    run_layout = build_run_layout(request.mode, request.run_id, root=root)
    run_layout.create()
    seeded_files = _seed_run_files(run_layout, request.config_path)

    task_manifests = [
        _scaffold_task(run_layout.task_layout(task_id), request.max_iterations)
        for task_id in request.task_ids
    ]
    timestamp = datetime.now(tz=UTC).isoformat()

    run_metadata = {
        'schema_version': SCHEMA_VERSION,
        'run_id': run_layout.run_id,
        'mode': request.mode.value,
        'timestamp': timestamp,
        'config_path': str(request.config_path),
        'config_snapshot_path': seeded_files['requested_snapshot_path'],
        'resolved_config_path': seeded_files['resolved_snapshot_path'],
        'resolved_config': seeded_files['resolved_config'],
        'task_ids': [manifest['task_id'] for manifest in task_manifests],
        'pipeline_stages': [stage.key for stage in PIPELINE_STAGES],
        'workspace_root': str(run_layout.workspace_root),
        'artifact_root': str(run_layout.root),
        'log_paths': {
            'run_log': str(run_layout.run_log_path),
            'error_log': str(run_layout.error_log_path),
        },
        'failure_log_types': list(FAILURE_LOG_TYPES),
        'cache_paths': {
            'parsed_repo_indexes': str(run_layout.parsed_repo_indexes_cache_dir),
            'retrieval_embeddings': str(run_layout.retrieval_embeddings_cache_dir),
            'retrieved_context': str(run_layout.retrieved_context_cache_dir),
            'solver_outputs': str(run_layout.solver_outputs_cache_dir),
            'prompt_outputs': str(run_layout.prompt_outputs_cache_dir),
        },
        'cache_policy': seeded_files['cache_manifest'],
        'versions': version_manifest(run_layout.root.parents[2]),
    }
    if request.mode == ExecutionMode.ABLATION and request.ablation_name is not None:
        run_metadata['ablation_name'] = request.ablation_name

    _write_json(run_layout.metadata_path, run_metadata)

    if request.mode != ExecutionMode.TASK:
        _write_json(
            run_layout.summary_path,
            {
                'schema_version': SCHEMA_VERSION,
                'run_id': run_layout.run_id,
                'mode': request.mode.value,
                'task_count': len(task_manifests),
                'task_ids': [manifest['task_id'] for manifest in task_manifests],
            },
        )

    return run_layout
