from __future__ import annotations

from pathlib import Path

from src.models import RunRequest
from src.orchestration.runner import execute_run


def execute_pipeline_run(request: RunRequest, root: Path | None = None) -> None:
    """Minimal controller wrapper around the current orchestration stub."""
    return execute_run(request, root=root)
