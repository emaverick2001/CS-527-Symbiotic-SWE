import json
from pathlib import Path

from symbiotic_swe.models import ExecutionMode, RunRequest
from symbiotic_swe.orchestration import execute_run
from symbiotic_swe.orchestration.pipeline import stage_keys
from symbiotic_swe.workspace import build_run_layout


def test_workspace_layout_separates_outputs_and_repo_checkouts(tmp_path: Path) -> None:
    run_layout = build_run_layout(
        ExecutionMode.TASK,
        run_id='task-demo',
        root=tmp_path,
    )
    task_layout = run_layout.task_layout('demo task')

    assert run_layout.root == tmp_path / 'artifacts' / 'runs' / 'task-demo'
    assert task_layout.repo_dir == (
        tmp_path / 'artifacts' / 'workspaces' / 'task-demo' / 'demo-task' / 'repo'
    )
    assert task_layout.iteration_dir(0).name == 'iter_000'
    assert task_layout.stage_dir(0, 'retrieval') == (
        tmp_path
        / 'artifacts'
        / 'runs'
        / 'task-demo'
        / 'tasks'
        / 'demo-task'
        / 'iterations'
        / 'iter_000'
        / 'retrieval'
    )
    assert (
        run_layout.run_log_path
        == tmp_path / 'artifacts' / 'logs' / 'task-demo' / 'run.log'
    )
    assert run_layout.retrieval_embeddings_cache_dir == (
        tmp_path / 'artifacts' / 'cache' / 'task-demo' / 'retrieval_embeddings'
    )


def test_pipeline_stage_order_matches_proposal() -> None:
    assert stage_keys() == (
        'retrieval',
        'patch_generation',
        'slicing',
        'symbolic_reasoning',
        'evaluation',
    )


def test_execute_run_writes_metadata_logs_and_cache_layout(tmp_path: Path) -> None:
    config_path = tmp_path / 'configs' / 'task.toml'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('mode = "task"\n', encoding='utf-8')

    request = RunRequest(
        mode=ExecutionMode.TASK,
        task_ids=('demo-task',),
        config_path=config_path,
        max_iterations=1,
        run_id='task-demo',
    )

    run_layout = execute_run(request, root=tmp_path)
    metadata = json.loads(run_layout.metadata_path.read_text(encoding='utf-8'))
    task_layout = run_layout.task_layout('demo-task')

    assert run_layout.run_log_path.exists()
    assert run_layout.error_log_path.exists()
    assert run_layout.prompt_outputs_cache_dir.exists()
    assert task_layout.solver_logs_dir.exists()
    assert task_layout.patch_logs_dir.exists()
    assert metadata['run_id'] == 'task-demo'
    assert metadata['config_snapshot_path'].endswith('config_snapshot.toml')
    assert metadata['versions']['prompt_version'] == 'v0'
    assert metadata['cache_paths']['solver_outputs'].endswith('solver_outputs')
