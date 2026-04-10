# Repository Structure Decisions

This repository now mirrors the conceptual pipeline described in the proposal.

## Top-Level Layout

- `src/`
  - Python package source for the Symbiotic SWE system
- `configs/`
  - runtime defaults and mode-specific configs
- `data/`
  - task JSON files and benchmark rows
- `artifacts/`
  - generated outputs, caches, and temporary task workspaces
- `tests/`
  - smoke tests for structure and entrypoints
- `docs/`
  - design notes and proposal material

## Pipeline Package Layout

- `src/symbiotic_swe/orchestration/`
  - entrypoint-facing orchestration and stage ordering
- `src/symbiotic_swe/retrieval/`
- `src/symbiotic_swe/patch_generation/`
- `src/symbiotic_swe/slicing/`
- `src/symbiotic_swe/symbolic_reasoning/`
- `src/symbiotic_swe/evaluation/`

Each stage package currently contains a placeholder `STAGE_SPEC` so the code structure matches the research pipeline before stage logic is implemented.

## Execution Entrypoints

- `symbiotic-swe-task`
  - scaffold or run a single repair task
- `symbiotic-swe-benchmark`
  - scaffold or run a benchmark sweep
- `symbiotic-swe-ablation`
  - scaffold or run an ablation sweep

All three wrappers call the same CLI module and differ only in execution mode.

## Workspace And Artifact Conventions

Temporary task repositories live at:

```text
artifacts/workspaces/<run_id>/<task_id>/repo/
```

Persistent run outputs live at:

```text
artifacts/runs/<run_id>/
```

Per-task outputs live at:

```text
artifacts/runs/<run_id>/tasks/<task_id>/
```

Per-iteration outputs live at:

```text
artifacts/runs/<run_id>/tasks/<task_id>/iterations/iter_000/<stage>/
```

This keeps mutable checkouts separate from persistent artifacts and makes iteration-by-iteration analysis deterministic.
