# Project Structure Conventions

This project studies whether symbolic solvers can improve an agentic software repair loop on SWE-bench style tasks. Directory names should describe that workflow directly: tasks, repository context, candidate patches, program slices, solver constraints, counterexamples, feedback, and evaluation.

## Top-Level Layout

```text
assets/
  diagrams/
  figures/
artifacts/
  runs/
  workspaces/
  cache/
  checkpoints/
  patches/
  solver_outputs/
  metrics/
  logs/
configs/
  datasets/
  experiments/
  solvers/
data/
  benchmarks/
  raw/
  processed/
docs/
notebooks/
scripts/
src/
tests/
```

## Assets

- `assets/diagrams/`: architecture diagrams, pipeline flow diagrams, and stage contract diagrams.
- `assets/figures/`: publication/report figures derived from experiment metrics.

Do not place generated run outputs here. Anything that changes per run belongs under `artifacts/`.

## Artifacts

`artifacts/` is for generated state. Most contents are ignored by Git except `.gitkeep` placeholders and intentionally checked-in examples.

### Run Naming

Every full experiment run should use:

```text
{YYYYMMDD_HHMMSS}_{agent}_{experiment}_{solver}_{seed}
```

Example:

```text
20260502_132500_gpt4o_baseline_crosshair-z3_s0
20260502_140000_gpt4o_symbolic-feedback_crosshair-z3_s42
20260502_153000_gpt4o_ablation-no-symbolic_none_s42
```

Use lowercase slugs for all fields. Replace spaces with hyphens. Keep the seed explicit even for deterministic smoke runs.

### Run Folder Contract

Each `artifacts/runs/{run_id}/` folder should contain:

```text
config.yaml
run_manifest.json
task_manifest.json
metrics.json
stage_timings.csv
solver_queries.jsonl
solver_results.jsonl
patch_manifest.json
evaluation_results.jsonl
errors.log
summary.md
tasks/
```

Required meanings:

- `config.yaml`: exact resolved config used for the run, after inheritance/defaults.
- `run_manifest.json`: run id, git commit, command, environment metadata, Python version, dependency lockfile hash, and start/end timestamps.
- `task_manifest.json`: ordered task ids, dataset source, split, filters, and skipped-task reasons.
- `metrics.json`: aggregate metrics only, such as pass rate, resolved count, solver timeout rate, and mean iterations.
- `stage_timings.csv`: one row per task/stage/iteration with wall-clock timing.
- `solver_queries.jsonl`: one query envelope per symbolic invocation.
- `solver_results.jsonl`: one solver result per symbolic invocation.
- `patch_manifest.json`: generated patch ids, source iteration, apply status, and final selection status.
- `evaluation_results.jsonl`: one task-level evaluation result per row.
- `errors.log`: human-readable run-level failures.
- `summary.md`: short narrative summary for lab notes and reports.

Task-level artifacts live under:

```text
artifacts/runs/{run_id}/tasks/{task_id}/
  task_input.json
  normalized_task.json
  logs/
  iterations/
    iter_000/
      retrieval/
      patch_generation/
      slicing/
      symbolic_reasoning/
      feedback_transformation/
      evaluation/
```

Each stage directory should contain the smallest durable files needed to reproduce or inspect that stage. Prefer JSON/JSONL/CSV/YAML over ad hoc text.

### Artifact Subdirectories

- `artifacts/workspaces/`: temporary repository checkouts, one per run/task.
- `artifacts/cache/huggingface/`: Hugging Face dataset cache.
- `artifacts/cache/repositories/`: reusable repository clones or bare mirrors.
- `artifacts/cache/retrieval/`: reusable indexes, symbol maps, and chunk metadata.
- `artifacts/cache/solver/`: reusable symbolic summaries, constraint caches, and solver model caches.
- `artifacts/checkpoints/patch_generator/`: model or adapter checkpoints for patch generation experiments.
- `artifacts/checkpoints/context_selector/`: learned ranking/checkpoint state for context selection.
- `artifacts/checkpoints/symbolic_models/`: learned symbolic abstractions, if added later.
- `artifacts/patches/`: exported candidate/final patch bundles outside run folders.
- `artifacts/solver_outputs/`: solver-native logs and models when they are too verbose for run-level JSONL files.
- `artifacts/metrics/`: aggregate tables used by notebooks and reports.
- `artifacts/logs/`: cross-run logs grouped by `pipeline/`, `evaluation/`, `solver/`, and `errors/`.

## Configs

Root config files may remain as convenience entrypoints:

- `configs/global.yaml`
- `configs/baseline.yaml`
- `configs/evaluation.yaml`
- `configs/smoke.yaml`

Domain-specific config files should be grouped by role:

```text
configs/
  datasets/
    swe_bench_verified.yaml
  experiments/
    baseline.yaml
    symbolic_feedback.yaml
    ablation_no_symbolic.yaml
  solvers/
    crosshair_z3.yaml
    z3.yaml
    cvc5.yaml
```

Config files should be declarative. Do not encode project paths in scripts when the value can live in YAML.

## Source Packages

The current source layout is stage-oriented:

- `src/dataset/`: benchmark loading, normalization, validation, and manifest writing.
- `src/retrieval/` and `src/context_selection/`: logic-aware file, symbol, and chunk selection.
- `src/patch_generation/`: candidate patch generation and patch refinement.
- `src/slicing/`: extraction of code slices relevant to solver checks.
- `src/symbolic/` and `src/symbolic_reasoning/`: constraint construction, solver invocation, and counterexample handling.
- `src/feedback/`: transforms solver outputs into actionable patch critiques.
- `src/evaluation/`: task execution, result scoring, and metric aggregation.
- `src/orchestration/`: run workspace management, stage execution, and artifact layout.
- `src/pipeline/`: public pipeline entrypoints.
- `src/utils/`: shared config, path, seed, logging, and I/O helpers.

Keep stage contracts explicit. A stage should write its own artifacts and consume only declared upstream artifacts.

## Data

- `data/benchmarks/swe_bench/`: downloaded SWE-bench exports.
- `data/raw/swe_bench/`: raw benchmark snapshots or manual task fixtures.
- `data/raw/repositories/`: raw repository snapshots if they must be preserved outside workspaces.
- `data/processed/swe_bench/manifests/`: normalized task manifests.
- `data/processed/swe_bench/splits/`: smoke/final/ablation split files.
- `data/processed/slices/`: reusable code slice datasets.
- `data/processed/constraints/`: reusable symbolic constraint datasets.

Downloaded or generated data should stay ignored unless it is a tiny fixture needed by tests.

## Notebooks

Use numbered notebooks only for exploratory analysis:

```text
notebooks/
  01_data_exploration.ipynb
  02_baseline_analysis.ipynb
  03_solver_diagnostics.ipynb
  04_results_visualization.ipynb
```

Notebook outputs should be reproducible from `data/processed/` and `artifacts/metrics/`.

## Scripts

Scripts are thin command wrappers around Python modules. They should not contain core pipeline logic.

Recommended scripts:

- `scripts/download_swebench.py`: download benchmark data.
- `scripts/visualize_task.py`: inspect a task fixture or benchmark task.
- `scripts/validate_project_structure.py`: validate this scaffold.
- `scripts/run_smoke.sh`: run a small end-to-end smoke set.
- `scripts/run_baseline.sh`: run the non-symbolic baseline.
- `scripts/run_symbolic_feedback.sh`: run the solver-feedback experiment.
- `scripts/evaluate_run.sh`: evaluate an existing run folder.

## Validation Rules

The scaffold is considered valid when:

- required top-level directories exist;
- required artifact subdirectories exist;
- required config groups exist;
- root config entrypoints exist;
- run ids match `{YYYYMMDD_HHMMSS}_{agent}_{experiment}_{solver}_{seed}`;
- every completed run folder contains the required run-level files listed above.

Run:

```bash
python scripts/validate_project_structure.py
```

Use `--check-runs` once real run folders exist and should be validated.
