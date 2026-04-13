from __future__ import annotations

from pathlib import Path

from src.models import RunRequest


def execute_run(request: RunRequest, root: Path | None = None) -> None:
    """Placeholder orchestration entrypoint for the iterative build stage."""
    raise NotImplementedError(
        'The orchestration runner has not been implemented yet. '
        'Build the dataset and downstream stages incrementally before wiring '
        'full pipeline execution.'
    )
