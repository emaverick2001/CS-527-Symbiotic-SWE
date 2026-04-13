from __future__ import annotations

from pathlib import Path

from src.models import RunRequest
from src.orchestration.runner import execute_run
from src.workspace import RunLayout


def execute_pipeline_run(request: RunRequest, root: Path | None = None) -> RunLayout:
    """Route every execution mode through one controller entrypoint."""
    return execute_run(request, root=root)
