from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ExecutionMode(StrEnum):
    TASK = 'task'
    BENCHMARK = 'benchmark'
    ABLATION = 'ablation'


@dataclass(frozen=True)
class StageSpec:
    key: str
    description: str


@dataclass(frozen=True)
class RunRequest:
    mode: ExecutionMode
    task_ids: tuple[str, ...]
    config_path: Path
    max_iterations: int = 1
    run_id: str | None = None
    ablation_name: str | None = None
