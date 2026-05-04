#!/usr/bin/env bash
set -euo pipefail

PREPARED_DIR="${PREPARED_DIR:-data/prepared/prepared/smoke}"
PROVIDER="${PROVIDER:-openai}"
MODEL="${MODEL:-gpt-5.4-mini}"
MAX_ITERATIONS="${MAX_ITERATIONS:-1}"
CONDITIONS="${CONDITIONS:-neural_only,neural_slicing,neural_solver,neural_cegf}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)_${PROVIDER}_${MODEL//_/-}_smoke_z3_s0}"
OUTPUT_DIR="${OUTPUT_DIR:-artifacts/runs/${RUN_ID}}"

uv run symbiotic-swe smoke \
  --preflight-only \
  --prepared-dir "${PREPARED_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --conditions "${CONDITIONS}" \
  --max-iterations "${MAX_ITERATIONS}" \
  --provider "${PROVIDER}" \
  --model "${MODEL}"

uv run symbiotic-swe smoke \
  --prepared-dir "${PREPARED_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --conditions "${CONDITIONS}" \
  --max-iterations "${MAX_ITERATIONS}" \
  --provider "${PROVIDER}" \
  --model "${MODEL}"
