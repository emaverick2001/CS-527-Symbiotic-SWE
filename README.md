# CS-527-Symbiotic-SWE

- Integrating Symbolic Solvers into the Agentic Debugging Loop.

## Overview

This repository is the implementation scaffold for a neuro-symbolic software repair system. The pipeline is organized around six stages:

- pipeline orchestration
- retrieval
- patch generation
- slicing
- symbolic reasoning
- evaluation

The current codebase defines the repository layout, execution entrypoints, run/workspace conventions, cache locations, logging locations, and version-tracking metadata that later stages will build on.

## Setup

### Local Poetry + venv

```bash
git clone https://github.com/emaverick2001/CS-527-Symbiotic-SWE.git
cd CS-527-Symbiotic-SWE

# Make sure Python 3.11 is available
python3.11 --version
# if not
brew install python@3.11

# If Poetry is not installed, install it
brew install poetry

# Create an in-project virtual environment
poetry config virtualenvs.in-project true
poetry env use python3.11
poetry install

# Activate the environment
source .venv/bin/activate

# Install git hooks
pre-commit install

# Sanity checks
poetry run pytest
poetry run ruff check .
poetry run mypy .
```

### Reproducible Docker Path

```bash
docker build -t symbiotic-swe .
docker run --rm -it symbiotic-swe
```

## Running The Scaffold

```bash
# Single-task execution
poetry run symbiotic-swe-task --task-id demo-task --max-iterations 2

# Benchmark execution
poetry run symbiotic-swe-benchmark --task-id task-001 --task-id task-002

# Ablation execution
poetry run symbiotic-swe-ablation \
  --ablation-name no-symbolic-feedback \
  --task-id task-001
```

## Downloading SWE-bench

SWE-bench is hosted on Hugging Face. The official dataset cards list:

- `princeton-nlp/SWE-bench`
- `princeton-nlp/SWE-bench_Lite`
- `princeton-nlp/SWE-bench_Verified`

Install the Hugging Face datasets client in your project environment:

```bash
poetry run pip install datasets
```

Download the recommended verified subset into this repo:

```bash
poetry run python scripts/download_swe_bench.py --preset verified
```

Download the Lite subset:

```bash
poetry run python scripts/download_swe_bench.py --preset lite
```

Download the full benchmark:

```bash
poetry run python scripts/download_swe_bench.py --preset full
```

By default this writes:

- benchmark files to `data/benchmarks/swe_bench/<preset>/`
- Hugging Face cache files to `artifacts/cache/huggingface/datasets/`

If you only want one split, pass `--split test` or another split name.

## Repository Structure

- `src/symbiotic_swe/orchestration/`
  - CLI-facing orchestration and run scaffolding
- `src/symbiotic_swe/retrieval/`
  - retrieval stage placeholder
- `src/symbiotic_swe/patch_generation/`
  - patch generation stage placeholder
- `src/symbiotic_swe/slicing/`
  - slicing stage placeholder
- `src/symbiotic_swe/symbolic_reasoning/`
  - solver-facing reasoning stage placeholder
- `src/symbiotic_swe/evaluation/`
  - evaluation stage placeholder
- `configs/`
  - base, task, benchmark, and ablation configs
- `data/tasks/`
  - single-task inputs
- `data/benchmarks/`
  - benchmark manifests
- `artifacts/runs/`
  - persistent run artifacts
- `artifacts/logs/`
  - run-level logs
- `artifacts/cache/`
  - reusable caches
- `artifacts/workspaces/`
  - temporary per-task working repos
- `docs/`
  - proposal and developer-facing design notes
- `tests/`
  - smoke tests for the scaffold contract

## Artifact And Working Directory Layout

Temporary repository checkouts live at:

```text
artifacts/workspaces/<run_id>/<task_id>/repo/
```

Persistent task artifacts live at:

```text
artifacts/runs/<run_id>/tasks/<task_id>/
```

Per-iteration stage artifacts live at:

```text
artifacts/runs/<run_id>/tasks/<task_id>/iterations/iter_000/<stage>/
```

Run-level logs live at:

```text
artifacts/logs/<run_id>/
```

Run-level caches live at:

```text
artifacts/cache/<run_id>/
```

The cache tree is split into:

- `retrieval_embeddings/`
- `retrieved_context/`
- `solver_outputs/`
- `prompt_outputs/`

## Version Tracking

Each run metadata file records:

- Python version constraint
- dependency manifest path
- dependency lockfile path
- prompt version
- schema version

## Developer Notes

- Main dependency manifest: `pyproject.toml`
- Locked dependency versions: `poetry.lock`
- Local environment path: `.venv/`
- Container environment: `Dockerfile`
- Additional structure notes: [docs/REPO_STRUCTURE.md](/Users/maver/Desktop/Coding%20Projects/AI/CS-527-Symbiotic-SWE/docs/REPO_STRUCTURE.md)
- Environment notes: [docs/ENVIRONMENT.md](/Users/maver/Desktop/Coding%20Projects/AI/CS-527-Symbiotic-SWE/docs/ENVIRONMENT.md)
