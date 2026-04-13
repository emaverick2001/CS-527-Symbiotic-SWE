# Core System Design

This document turns the proposal into concrete workflow and object contracts that the implementation can build against.

## High-Level Workflow

```text
Bug Report + Failing Tests + Repo Snapshot
  -> Task Normalization
  -> Context Retrieval
  -> Neural Patch Proposal
  -> Patch Application
  -> Impact Slicing
  -> Constraint Extraction
  -> Symbolic Verification
  -> Counterexample Generation
  -> Critique Transformation
  -> Patch Refinement
  -> Validation + Termination
```

This is the closed Symbiotic-SWE loop:

```text
task instance -> retrieved repo context -> candidate patch -> impacted program slice
-> symbolic constraints -> solver result -> counterexample -> critique -> refined patch
```

## Low-Level Workflow

### 1. Task Intake

- Load one benchmark row or task JSON.
- Normalize fields into a canonical `TaskContract`.
- Attach repo identifiers, bug description, failing tests, and metadata.

### 2. Retrieval

- Build a query from the bug description and failing tests.
- Rank relevant symbols/chunks from the repo index.
- Persist the chosen context as `RetrievedContextContract`.

### 3. Patch Proposal

- Prompt the LLM with bug context and formatting constraints.
- Parse the response into a `PatchContract`.
- Record parse, syntax, and apply status separately.

### 4. Impact Slicing

- Apply the patch in a temporary working tree.
- Find modified AST nodes and enclosing symbols.
- Reduce the affected region into a `ProgramSliceContract`.

### 5. Symbolic Reasoning

- Translate the slice into a `SymbolicProblemContract`.
- Run the solver and capture a `SolverResultContract`.
- If `sat`, replay and package a `CounterexampleContract`.

### 6. Feedback Loop

- Convert the counterexample into a compact `CritiqueContract`.
- Feed the critique back into the next patch prompt.
- Append an `IterationRecordContract` to the trajectory.

### 7. Termination

- Stop when the solver returns `unsat`, validation succeeds, or the budget is exhausted.
- Summarize the loop with `RunMetricsContract`.

## Core Object Contracts

These contracts come directly from the proposal's artifact schema and execution sections.

### `TaskContract`

Represents one repair instance.

```python
{
  "schema_version": "0.1.0",
  "task_id": "sympy__sympy-17139",
  "repo": "sympy/sympy",
  "repo_commit": "...",
  "repo_path": "...",
  "bug_description": "...",
  "failing_tests": [...],
  "execution_trace": [...],
  "oracle": {...},
  "metadata": {
    "dataset": "SWE-bench Verified",
    "difficulty": "15 min - 1 hour",
    "tags": ["logic-heavy"],
    "logic_heavy": true
  }
}
```

### `PatchContract`

Represents one candidate repair.

```python
{
  "schema_version": "0.1.0",
  "patch_id": "...",
  "task_id": "...",
  "iteration": 0,
  "raw_text": "...",
  "diff": "...",
  "target_files": ["..."],
  "reasoning": "...",
  "parse_ok": true,
  "syntax_ok": true,
  "apply_ok": true,
  "errors": [],
  "metadata": {
    "model": "...",
    "prompt_version": "v0",
    "prompt_path": "..."
  }
}
```

### `ProgramSliceContract`

Represents the reduced slice sent to symbolic analysis.

```python
{
  "schema_version": "0.1.0",
  "slice_id": "...",
  "task_id": "...",
  "iteration": 0,
  "target_functions": ["sum_list"],
  "modified_nodes": [...],
  "affected_variables": ["lst"],
  "path_conditions": ["len(lst) == 0"],
  "related_tests": ["test_sum_list_empty"]
}
```

### `SymbolicProblemContract`

Represents the solver-facing logical problem.

```python
{
  "schema_version": "0.1.0",
  "symbolic_problem_id": "...",
  "task_id": "...",
  "iteration": 0,
  "function_name": "sum_list",
  "variables": {"lst": "List[Int]"},
  "path_constraints": ["len(lst) == 0"],
  "postconditions": ["len(lst) == 0 -> result == 0"],
  "unsupported_nodes": []
}
```

### `SolverResultContract`

Represents the solver outcome.

```python
{
  "schema_version": "0.1.0",
  "solver_result_id": "...",
  "task_id": "...",
  "iteration": 0,
  "status": "sat",
  "model": {"lst": []},
  "violated_property": "empty list should return 0",
  "solver_time_ms": 47,
  "raw_log_path": "..."
}
```

### `CounterexampleContract`

Represents the concrete failure case returned by symbolic reasoning.

```python
{
  "schema_version": "0.1.0",
  "counterexample_id": "...",
  "task_id": "...",
  "iteration": 0,
  "inputs": {"lst": []},
  "violated_condition": "len(lst) == 0 -> result == 0",
  "observed_failure": "ZeroDivisionError",
  "affected_function": "sum_list",
  "replay_ok": true
}
```

### `CritiqueContract`

Represents the prompt-ready explanation produced from the counterexample.

```python
{
  "schema_version": "0.1.0",
  "critique_id": "...",
  "task_id": "...",
  "iteration": 0,
  "short_text": "Your patch still fails when lst = [].",
  "structured": {
    "function": "sum_list",
    "inputs": {"lst": []},
    "error": "ZeroDivisionError"
  },
  "source_counterexample_id": "..."
}
```

### `PipelineStateContract`

Represents the canonical runtime state for one task loop.

```python
{
  "schema_version": "0.1.0",
  "task": {...},
  "context": {...},
  "patch": {...},
  "slice": {...},
  "constraints": {...},
  "solver_result": {...},
  "counterexample": {...},
  "critique": {...},
  "history": [...],
  "metrics": {...}
}
```

## Implementation Mapping

- Contracts live in [contracts.py](/Users/maver/Desktop/Coding%20Projects/AI/CS-527-Symbiotic-SWE/src/symbiotic_swe/contracts.py).
- Each contract is a strict Pydantic model with `extra='forbid'`.
- These objects are designed to back the proposal artifacts:
  - `task.json`
  - `retrieval/topk_context.json`
  - `patches/iteration_k.diff`
  - `analysis/program_slice.json`
  - `constraints/spec.json`
  - `solver/solver_result.json`
  - `counterexamples/iteration_k.json`
  - `feedback/iteration_k.json`
  - `history/trajectory.json`
  - `metrics/run_summary.json`
