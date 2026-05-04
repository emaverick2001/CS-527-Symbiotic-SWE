#!/usr/bin/env bash
set -euo pipefail

PREPARED_DIR="${PREPARED_DIR:-data/prepared/prepared/smoke}"
PROVIDER="${PROVIDER:-openai}"
MODEL="${MODEL:-gpt-5.4-mini}"
MAX_ITERATIONS="${MAX_ITERATIONS:-1}"
CONDITIONS="${CONDITIONS:-neural_cegf}"
PREFLIGHT_ONLY="${PREFLIGHT_ONLY:-0}"

if [[ -z "${TASK_ID:-}" ]]; then
  first_task_json="$(find "${PREPARED_DIR}" -mindepth 2 -maxdepth 2 -name task.json | sort | head -n 1)"
  if [[ -z "${first_task_json}" ]]; then
    echo "No prepared task.json found under ${PREPARED_DIR}" >&2
    exit 1
  fi
  TASK_ID="$(basename "$(dirname "${first_task_json}")")"
fi

RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)_${PROVIDER}_${MODEL//_/-}_one-task-smoke_z3_s0}"
OUTPUT_DIR="${OUTPUT_DIR:-artifacts/runs/${RUN_ID}}"

echo "One-task smoke"
echo "  task_id:        ${TASK_ID}"
echo "  prepared_dir:   ${PREPARED_DIR}"
echo "  output_dir:     ${OUTPUT_DIR}"
echo "  provider/model: ${PROVIDER}:${MODEL}"
echo "  conditions:     ${CONDITIONS}"
echo "  max_iterations: ${MAX_ITERATIONS}"

uv run symbiotic-swe smoke \
  --preflight-only \
  --task-id "${TASK_ID}" \
  --prepared-dir "${PREPARED_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --conditions "${CONDITIONS}" \
  --max-iterations "${MAX_ITERATIONS}" \
  --provider "${PROVIDER}" \
  --model "${MODEL}"

if [[ "${PREFLIGHT_ONLY}" == "1" || "${PREFLIGHT_ONLY}" == "true" ]]; then
  echo
  echo "Preflight complete. Set PREFLIGHT_ONLY=0 or omit it to run the model call."
  exit 0
fi

uv run symbiotic-swe smoke \
  --task-id "${TASK_ID}" \
  --prepared-dir "${PREPARED_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --conditions "${CONDITIONS}" \
  --max-iterations "${MAX_ITERATIONS}" \
  --provider "${PROVIDER}" \
  --model "${MODEL}"

echo
echo "Generated artifact bundle:"
find "${OUTPUT_DIR}" -maxdepth 3 -type f | sort
echo
echo "Start inspection here:"
echo "  ${OUTPUT_DIR}/errors.log"
echo "  ${OUTPUT_DIR}/evaluation_results.jsonl"
echo "  ${OUTPUT_DIR}/patch_manifest.json"
echo "  ${OUTPUT_DIR}/metrics.json"
