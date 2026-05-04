#!/usr/bin/env bash
set -euo pipefail

PREPARED_DIR="${PREPARED_DIR:-data/prepared/prepared/smoke}"
MAX_ITERATIONS="${MAX_ITERATIONS:-1}"
CONDITIONS="${CONDITIONS:-neural_only,neural_cegf}"
OUTPUT_ROOT="${OUTPUT_ROOT:-artifacts/runs/model_ablation}"

# Format: provider:model. Override to compare a different set.
MODELS="${MODELS:-openai:gpt-5.4-mini openai:gpt-5.5 openai:gpt-5.3-codex}"

for entry in ${MODELS}; do
  provider="${entry%%:*}"
  model="${entry#*:}"
  run_slug="${provider}_${model//[^a-zA-Z0-9._-]/-}"
  output_dir="${OUTPUT_ROOT}/${run_slug}"

  echo "==> ${provider}:${model}"
  uv run symbiotic-swe smoke \
    --preflight-only \
    --prepared-dir "${PREPARED_DIR}" \
    --output-dir "${output_dir}" \
    --conditions "${CONDITIONS}" \
    --max-iterations "${MAX_ITERATIONS}" \
    --provider "${provider}" \
    --model "${model}"

  uv run symbiotic-swe smoke \
    --prepared-dir "${PREPARED_DIR}" \
    --output-dir "${output_dir}" \
    --conditions "${CONDITIONS}" \
    --max-iterations "${MAX_ITERATIONS}" \
    --provider "${provider}" \
    --model "${model}"
done
