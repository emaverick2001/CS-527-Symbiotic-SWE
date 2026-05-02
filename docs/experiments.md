# Experiment Conventions

Use `docs/project_structure.md` as the source of truth for directories, run ids, and required run artifacts.

## Primary Comparisons

- `baseline`: retrieval, patch generation, and evaluation without symbolic feedback.
- `symbolic-feedback`: retrieval, patch generation, slicing, solver checks, feedback transformation, and evaluation.
- `ablation-no-symbolic`: same iteration budget as symbolic feedback, but with solver checks disabled.

## Run Ids

Use:

```text
{YYYYMMDD_HHMMSS}_{agent}_{experiment}_{solver}_{seed}
```

Examples:

```text
20260502_132500_gpt4o_baseline_crosshair-z3_s0
20260502_140000_gpt4o_symbolic-feedback_crosshair-z3_s42
20260502_153000_gpt4o_ablation-no-symbolic_none_s42
```

## Minimum Metrics

- resolved task count
- fail-to-pass success rate
- pass-to-pass preservation rate
- mean iterations per resolved task
- patch apply failure rate
- solver invocation count
- solver timeout rate
- unsupported symbolic construct rate
- counterexamples found per task
- feedback accepted per task
