# CS-527 Symbiotic SWE

Symbiotic-SWE is a neuro-symbolic software repair pipeline for logic-heavy SWE-bench-style tasks. It combines neural patch generation with optional impact slicing, symbolic checking, counterexample-guided feedback, and real pytest evaluation.

The current project is past scaffold mode: the CLI can run smoke experiments, ablations, materialize prepared repositories, apply generated patches, run `FAIL_TO_PASS` and `PASS_TO_PASS` tests, and write structured artifacts for analysis.

## Pipeline

The implemented repair loop is:

1. Load a prepared `CanonicalTask`.
2. Select repository context from the checked-out task repo.
3. Generate a git-style patch with a configurable model provider.
4. Apply the patch to a disposable working copy.
5. If patch application fails, ask the model for one patch-repair rewrite using exact checked-out target file content.
6. Optionally run impact slicing.
7. Optionally run symbolic verification.
8. Optionally convert counterexamples or pytest failures into critique feedback.
9. Run real task tests.
10. Write metrics, patch manifests, solver results, test verdicts, and summary artifacts.

Supported experiment conditions:

- `neural_only`: model patch generation plus real test evaluation.
- `neural_slicing`: patch generation plus impact slicing.
- `neural_solver`: patch generation, slicing, and solver checking without feedback.
- `neural_cegf`: full counterexample-guided feedback loop.

## Setup

Use Python 3.11 and `uv`.

```bash
git clone https://github.com/emaverick2001/CS-527-Symbiotic-SWE.git
cd CS-527-Symbiotic-SWE

uv sync --extra dev --extra swebench
source .venv/bin/activate
```

Set one model API key:

```bash
export OPENAI_API_KEY=...
# or
export ANTHROPIC_API_KEY=...
```

Sanity checks:

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
```

## Preparing Repositories

Prepared task JSON files live under:

```text
data/prepared/prepared/<split>/<task_id>/task.json
```

The CLI expects each task to point to a local git checkout. Use materialization to create or repair reusable workspaces:

```bash
uv run --extra swebench symbiotic-swe materialize-repos \
  --prepared-dir data/prepared/prepared/dev \
  --repo-cache-dir data/repo_cache \
  --workspace-root data/prepared/workspaces \
  --force
```

For a task subset, repeat `--task-id`:

```bash
uv run --extra swebench symbiotic-swe materialize-repos \
  --prepared-dir data/prepared/prepared/dev \
  --repo-cache-dir data/repo_cache \
  --workspace-root data/prepared/workspaces \
  --force \
  --task-id sympy__sympy-13031 \
  --task-id sympy__sympy-15875
```

## Running Experiments

One-task smoke check:

```bash
TASK_ID=sympy__sympy-20801 \
CONDITIONS=neural_cegf \
MODEL=gpt-5.3-codex \
MAX_ITERATIONS=1 \
scripts/run_one_task_smoke.sh
```

Smoke split:

```bash
PROVIDER=openai \
MODEL=gpt-5.3-codex \
CONDITIONS=neural_only,neural_cegf \
MAX_ITERATIONS=1 \
scripts/run_smoke.sh
```

Main held-out SymPy final evaluation used for the latest paper tables:

```bash
uv run --extra swebench symbiotic-swe ablation \
  --prepared-dir data/prepared/prepared/final_eval \
  --output-dir artifacts/runs/final_eval_gpt_5_3_codex_sympy_real_tests \
  --provider openai \
  --model gpt-5.3-codex \
  --max-iterations 3 \
  --task-id sympy__sympy-11618 \
  --task-id sympy__sympy-12481 \
  --task-id sympy__sympy-13372 \
  --task-id sympy__sympy-13480 \
  --task-id sympy__sympy-13647 \
  --task-id sympy__sympy-14711 \
  --task-id sympy__sympy-15809 \
  --task-id sympy__sympy-17630 \
  --task-id sympy__sympy-19495 \
  --task-id sympy__sympy-19954 \
  --task-id sympy__sympy-20154 \
  --task-id sympy__sympy-20428 \
  --task-id sympy__sympy-21847 \
  --task-id sympy__sympy-22714
```

## Current Result Artifact

The primary final-evaluation run is:

```text
artifacts/runs/final_eval_gpt_5_3_codex_sympy_real_tests
```

High-level held-out SymPy result:

| Condition | Real Test Success | Test Resolution | Logical Correctness | Avg. Iterations | Avg. Runtime | Avg. Tokens | Tokens / Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `neural_only` | 14.3% | 18.2% | 0.0% | 1.50 | 8.6s | 16,746.6 | 7,734.0 |
| `neural_slicing` | 21.4% | 27.3% | 0.0% | 1.71 | 11.2s | 21,835.2 | 15,435.3 |
| `neural_solver` | 21.4% | 33.3% | 21.4% | 1.79 | 10.1s | 21,002.4 | 12,984.0 |
| `neural_cegf` | 35.7% | 45.5% | 35.7% | 2.50 | 16.6s | 30,025.9 | 17,420.8 |

Interpretation:

- `neural_cegf` is the strongest condition on the held-out final SymPy subset.
- `neural_cegf` improves both real-test success and solver-backed logical correctness over `neural_only`.
- The improvement is not free: `neural_cegf` has the highest average runtime, average token use, and tokens per success.
- `neural_solver` shows that symbolic checking without feedback is weaker than the full feedback loop.

Definitions:

- Real Test Success: resolved tasks divided by all final-evaluation tasks.
- Test Resolution: resolved tasks divided by tasks that reached real test evaluation.
- Logical Correctness: tasks where real tests pass and the final solver status is `unsat`, divided by all final-evaluation tasks.
- Tokens / Success: LLM tokens spent on successful repairs divided by the number of successful repairs.

The development ablation used during tuning is:

```text
artifacts/runs/dev_ablation_gpt_5_3_codex_sympy_real_tests_v4
```

Use it as supporting development evidence, not as the primary final result.

See:

- `docs/experiment_analysis.md`
- `docs/experiments.md`
- `docs/Key_Observations.md`
- `docs/high_low_pipeline.MD`

## Paper Figures

Generate the RQ3 cost-vs-success scatterplot from the final-evaluation metrics:

```bash
uv run python scripts/plot_cost_success_tradeoff.py
```

Outputs:

- `docs/figures/cost_success_tradeoff.svg`
- `docs/figures/cost_success_tradeoff_caption.md`

The figure plots average tokens per task against real-test success rate, with bubble size encoding average wall-clock runtime.

## Artifacts

Each run directory contains:

- `run_manifest.json`: provider, model, conditions, task IDs, and run timing.
- `metrics.json`: aggregate metrics by condition.
- `evaluation_results.jsonl`: real pytest verdicts.
- `patch_manifest.json`: generated patch metadata and apply status.
- `solver_results.jsonl`: solver outcomes and counterexample-related records.
- `stage_timings.csv`: per-iteration timing.
- `errors.log`: human-readable failures.
- `<condition>/<task_id>/metrics.json`: per-task metrics.

Generated run artifacts are intentionally ignored by git unless explicitly selected for reporting.

## Repository Layout

- `symbiotic_swe/`: runtime package.
- `symbiotic_swe/context_selection/`: context retrieval and task-specific source selection.
- `symbiotic_swe/patch_generation/`: prompt construction, model calls, diff parsing, and patch repair retry.
- `symbiotic_swe/slicing/`: impact slicing.
- `symbiotic_swe/symbolic_reasoning/`: solver integration and counterexample extraction.
- `symbiotic_swe/feedback/`: critique generation.
- `symbiotic_swe/evaluation/`: pytest execution and metrics aggregation.
- `symbiotic_swe/orchestration/`: experiment loop and run artifact writing.
- `scripts/`: smoke/model/materialization helpers.
- `configs/`: experiment and evaluation configs.
- `data/prepared/`: prepared task manifests and local task workspaces.
- `data/repo_cache/`: reusable git cache for materialized repositories.
- `artifacts/runs/`: generated experiment runs.
- `docs/`: pipeline notes, experimental observations, and paper planning.
- `tests/`: unit and synthetic end-to-end tests.

## Development Notes

- Primary dependency file: `pyproject.toml`.
- Lockfile: `uv.lock`.
- Runtime package layout is top-level `symbiotic_swe/`.
- Python target: 3.11.
- SWE-bench support dependencies are installed with `--extra swebench`.

Avoid committing local caches, virtual environments, generated repo workspaces, and bulk run artifacts.
