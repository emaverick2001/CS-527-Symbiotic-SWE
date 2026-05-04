#!/usr/bin/env bash
set -euo pipefail

PREPARED_DIR="${PREPARED_DIR:-data/prepared/prepared/smoke}"
REPO_CACHE_DIR="${REPO_CACHE_DIR:-data/repo_cache}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-data/prepared/workspaces}"
FETCH="${FETCH:-0}"
FORCE="${FORCE:-0}"
DRY_RUN="${DRY_RUN:-0}"

args=(
  symbiotic-swe materialize-repos
  --prepared-dir "${PREPARED_DIR}"
  --repo-cache-dir "${REPO_CACHE_DIR}"
  --workspace-root "${WORKSPACE_ROOT}"
)

if [[ -n "${TASK_ID:-}" ]]; then
  args+=(--task-id "${TASK_ID}")
fi

if [[ "${FETCH}" == "1" || "${FETCH}" == "true" ]]; then
  args+=(--fetch)
fi

if [[ "${FORCE}" == "1" || "${FORCE}" == "true" ]]; then
  args+=(--force)
fi

if [[ "${DRY_RUN}" == "1" || "${DRY_RUN}" == "true" ]]; then
  args+=(--dry-run)
fi

uv run "${args[@]}"
