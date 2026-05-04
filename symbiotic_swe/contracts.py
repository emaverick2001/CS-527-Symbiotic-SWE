from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OracleSpec(BaseModel):
    type: str  # 'tests' | 'constraints' | 'ground_truth'
    spec: Any


class TaskMetadata(BaseModel):
    dataset: str
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    logic_heavy: bool = False
    bug_type: Optional[str] = None
    repo_name: str
    status: str = 'valid'  # 'valid' | 'partial' | 'invalid'
    subset: Optional[str] = None
    preprocessing_timestamp: Optional[str] = None
    bug_report_path: Optional[str] = None
    failing_tests_path: Optional[str] = None
    oracle_path: Optional[str] = None
    repo_index_path: Optional[str] = None
    raw_fields_path: Optional[str] = None


class CanonicalTask(BaseModel):
    schema_version: str = '0.1.0'
    task_id: str
    repo: str
    repo_commit: str
    repo_path: Optional[str] = None
    bug_description: str
    failing_tests: List[str]
    execution_trace: List[str] = Field(default_factory=list)
    oracle: Optional[OracleSpec] = None
    metadata: TaskMetadata


class RepoSymbol(BaseModel):
    name: str
    kind: str  # 'function' | 'class' | 'method'
    file: str
    line_start: int
    line_end: int
    source: str = ''


class RepoFileEntry(BaseModel):
    path: str
    role: str  # 'source' | 'test' | 'other'
    symbols: List[RepoSymbol] = Field(default_factory=list)
    parse_failed: bool = False
    imports: List[str] = Field(default_factory=list)


class RepoIndex(BaseModel):
    repo: str
    index_path: str
    source_file_count: int = 0
    test_file_count: int = 0
    parse_failure_count: int = 0
    total_symbols: int = 0
    files: List[RepoFileEntry] = Field(default_factory=list)
    cached: bool = False


class MaterializationResult(BaseModel):
    is_valid: bool
    local_repo_path: Optional[str] = None
    resolved_commit: Optional[str] = None
    error: Optional[str] = None


class PreparedTaskArtifact(BaseModel):
    task: CanonicalTask
    repo_index: Optional[RepoIndex] = None
    status: str = 'valid'  # 'valid' | 'partial' | 'invalid'
    artifact_dir: Optional[str] = None
    error: Optional[str] = None


class PatchApplicationResult(BaseModel):
    applied: bool
    error: Optional[str] = None
    rejected_hunks: int = 0


class RetrievedContext(BaseModel):
    task_id: str
    query: str
    files: List[RepoFileEntry] = Field(default_factory=list)
    symbols: List[RepoSymbol] = Field(default_factory=list)
    total_chars: int = 0


class PatchContract(BaseModel):
    schema_version: str = '0.1.0'
    patch_id: str
    task_id: str
    iteration: int
    raw_text: str
    diff: str
    target_files: List[str] = Field(default_factory=list)
    reasoning: str = ''
    parse_ok: bool = False
    syntax_ok: bool = False
    apply_ok: bool = False
    errors: List[str] = Field(default_factory=list)
    model: str = ''
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ProgramSlice(BaseModel):
    schema_version: str = '0.1.0'
    slice_id: str
    task_id: str
    iteration: int
    target_functions: List[str] = Field(default_factory=list)
    modified_nodes: List[str] = Field(default_factory=list)
    affected_variables: List[str] = Field(default_factory=list)
    path_conditions: List[str] = Field(default_factory=list)
    related_tests: List[str] = Field(default_factory=list)
    source_snippets: Dict[str, str] = Field(default_factory=dict)


class SolverResultContract(BaseModel):
    schema_version: str = '0.1.0'
    solver_result_id: str
    task_id: str
    iteration: int
    status: str  # 'sat' | 'unsat' | 'unknown' | 'timeout' | 'error' | 'not_applicable'
    model: Optional[Dict[str, Any]] = None
    violated_property: Optional[str] = None
    solver_time_ms: int = 0
    error: Optional[str] = None


class CounterexampleContract(BaseModel):
    schema_version: str = '0.1.0'
    counterexample_id: str
    task_id: str
    iteration: int
    inputs: Dict[str, Any] = Field(default_factory=dict)
    violated_condition: str = ''
    observed_failure: str = ''
    affected_function: str = ''
    replay_ok: bool = False


class CritiqueContract(BaseModel):
    schema_version: str = '0.1.0'
    critique_id: str
    task_id: str
    iteration: int
    short_text: str
    structured: Dict[str, Any] = Field(default_factory=dict)
    source_counterexample_id: Optional[str] = None


class TestSuiteResult(BaseModel):
    name: str
    tests: List[str] = Field(default_factory=list)
    command: List[str] = Field(default_factory=list)
    returncode: Optional[int] = None
    passed: Optional[bool] = None
    duration_ms: int = 0
    stdout: str = ''
    stderr: str = ''
    error: Optional[str] = None


class TestEvaluationResult(BaseModel):
    schema_version: str = '0.1.0'
    task_id: str
    iteration: int
    resolved: bool = False
    evaluated: bool = False
    fail_to_pass: TestSuiteResult
    pass_to_pass: TestSuiteResult
    duration_ms: int = 0
    error: Optional[str] = None


class IterationRecord(BaseModel):
    iteration: int
    patch: Optional[PatchContract] = None
    program_slice: Optional[ProgramSlice] = None
    solver_result: Optional[SolverResultContract] = None
    counterexample: Optional[CounterexampleContract] = None
    critique: Optional[CritiqueContract] = None
    test_evaluation: Optional[TestEvaluationResult] = None
    duration_ms: int = 0


class RunMetrics(BaseModel):
    task_id: str
    run_id: str
    condition: str  # 'neural_only' | 'neural_cegf' | 'neural_slicing' | 'neural_solver'
    success: bool = False
    termination_reason: str = ''
    total_iterations: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_duration_ms: int = 0
    solver_duration_ms: int = 0
    solver_outcomes: Dict[str, int] = Field(default_factory=dict)
    patch_apply_failures: int = 0
    repeated_counterexamples: int = 0
    test_evaluated: bool = False
    test_resolved: bool = False
    final_test_evaluation: Optional[TestEvaluationResult] = None
    iterations: List[IterationRecord] = Field(default_factory=list)
