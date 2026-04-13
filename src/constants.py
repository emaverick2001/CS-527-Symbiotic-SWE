from __future__ import annotations

CONFIGS_DIRNAME = 'configs'
EXPERIMENTS_DIRNAME = 'experiments'

PIPELINE_STAGE_KEYS = (
    'retrieval',
    'patch_generation',
    'slicing',
    'symbolic_reasoning',
    'evaluation',
)

FAILURE_LOG_TYPES = (
    'patch_apply_failure',
    'ast_parse_failure',
    'solver_timeout',
    'unsupported_symbolic_construct',
)

DEFAULT_MODEL_PROVIDER = 'openai'
DEFAULT_MODEL_NAME = 'gpt-4o'
DEFAULT_REASONING_EFFORT = 'medium'
DEFAULT_SOLVER_BACKEND = 'crosshair+z3'
DEFAULT_BENCHMARK_NAME = 'SWE-bench Verified'
