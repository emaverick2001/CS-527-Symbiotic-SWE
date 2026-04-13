from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = '0.1.0'


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return str(value)
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    return value


class SerializableModel:
    def model_dump(self) -> dict[str, Any]:
        return _to_jsonable(self)

    def model_dump_json(self, indent: int | None = None) -> str:
        return json.dumps(self.model_dump(), indent=indent, sort_keys=False)


@dataclass
class TestSignal(SerializableModel):
    name: str
    error: str | None = None


class OracleType(StrEnum):
    TESTS = 'tests'
    LOGICAL_CONSTRAINTS = 'logical_constraints'
    GROUND_TRUTH_PATCH = 'ground_truth_patch'


@dataclass
class OracleSpec(SerializableModel):
    type: OracleType
    spec: dict[str, Any] | list[Any] | str | None = None


@dataclass
class TaskMetadata(SerializableModel):
    dataset: str
    repo_name: str
    difficulty: str | None = None
    bug_type: str | None = None
    subset: str | None = None
    source_split: str | None = None
    raw_instance_id: str | None = None
    dataset_source: str | None = None
    source_path: str | None = None
    logic_heavy: bool = False
    tags: list[str] = field(default_factory=list)
    preprocessing_timestamp: str | None = None
    bug_report_path: str | None = None
    failing_tests_path: str | None = None
    execution_trace_path: str | None = None
    oracle_path: str | None = None
    repo_index_path: str | None = None
    raw_fields_path: str | None = None
    status: str | None = None


@dataclass
class TaskObject(SerializableModel):
    task_id: str
    repo: str
    repo_commit: str
    bug_description: str
    metadata: TaskMetadata
    schema_version: str = SCHEMA_VERSION
    repo_path: str | None = None
    failing_tests: list[TestSignal] = field(default_factory=list)
    execution_trace: list[str] = field(default_factory=list)
    oracle: OracleSpec | None = None


TaskContract = TaskObject


@dataclass
class RepoIndex(SerializableModel):
    files: dict[str, str]
    ast_map: dict[str, Any]
    symbol_table: dict[str, dict[str, Any] | list[dict[str, Any]]]
    import_graph: dict[str, list[str]]
    call_graph: dict[str, list[str]]
