from __future__ import annotations

import argparse
import re
from pathlib import Path


RUN_ID_PATTERN = re.compile(
    r'^\d{8}_\d{6}_[a-z0-9][a-z0-9-]*_[a-z0-9][a-z0-9-]*_[a-z0-9][a-z0-9-]*_s\d+$'
)

REQUIRED_DIRECTORIES = (
    'assets/diagrams',
    'assets/figures',
    'artifacts/runs',
    'artifacts/workspaces',
    'artifacts/cache/huggingface',
    'artifacts/cache/repositories',
    'artifacts/cache/retrieval',
    'artifacts/cache/solver',
    'artifacts/checkpoints/patch_generator',
    'artifacts/checkpoints/context_selector',
    'artifacts/checkpoints/symbolic_models',
    'artifacts/patches/baseline',
    'artifacts/patches/symbolic_feedback',
    'artifacts/patches/ablations',
    'artifacts/solver_outputs/crosshair',
    'artifacts/solver_outputs/z3',
    'artifacts/solver_outputs/cvc5',
    'artifacts/metrics/baseline',
    'artifacts/metrics/symbolic_feedback',
    'artifacts/metrics/ablations',
    'artifacts/logs/pipeline',
    'artifacts/logs/evaluation',
    'artifacts/logs/solver',
    'artifacts/logs/errors',
    'configs/datasets',
    'configs/experiments',
    'configs/solvers',
    'data/benchmarks',
    'data/raw/swe_bench',
    'data/raw/repositories',
    'data/processed/swe_bench/manifests',
    'data/processed/swe_bench/splits',
    'data/processed/slices',
    'data/processed/constraints',
    'docs',
    'notebooks',
    'scripts',
    'src',
    'tests',
)

REQUIRED_FILES = (
    'configs/global.yaml',
    'configs/baseline.yaml',
    'configs/evaluation.yaml',
    'configs/smoke.yaml',
    'configs/datasets/swe_bench_verified.yaml',
    'configs/experiments/baseline.yaml',
    'configs/experiments/symbolic_feedback.yaml',
    'configs/experiments/ablation_no_symbolic.yaml',
    'configs/solvers/crosshair_z3.yaml',
    'configs/solvers/z3.yaml',
    'configs/solvers/cvc5.yaml',
    'docs/project_structure.md',
)

REQUIRED_RUN_FILES = (
    'config.yaml',
    'run_manifest.json',
    'task_manifest.json',
    'metrics.json',
    'stage_timings.csv',
    'solver_queries.jsonl',
    'solver_results.jsonl',
    'patch_manifest.json',
    'evaluation_results.jsonl',
    'errors.log',
    'summary.md',
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def missing_paths(root: Path, relative_paths: tuple[str, ...]) -> list[str]:
    return [relative_path for relative_path in relative_paths if not (root / relative_path).exists()]


def invalid_run_directories(root: Path) -> list[str]:
    runs_dir = root / 'artifacts' / 'runs'
    if not runs_dir.exists():
        return ['artifacts/runs']

    invalid: list[str] = []
    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir() and not path.name.startswith('.')):
        if not RUN_ID_PATTERN.fullmatch(run_dir.name):
            invalid.append(f'{run_dir.relative_to(root)}: invalid run id')
            continue

        for required_file in REQUIRED_RUN_FILES:
            if not (run_dir / required_file).exists():
                invalid.append(f'{run_dir.relative_to(root)}: missing {required_file}')
    return invalid


def validate(root: Path, check_runs: bool = False) -> list[str]:
    failures: list[str] = []
    failures.extend(f'missing directory: {path}' for path in missing_paths(root, REQUIRED_DIRECTORIES))
    failures.extend(f'missing file: {path}' for path in missing_paths(root, REQUIRED_FILES))
    if check_runs:
        failures.extend(invalid_run_directories(root))
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Validate the project scaffold conventions.')
    parser.add_argument(
        '--root',
        type=Path,
        default=project_root(),
        help='Repository root to validate. Defaults to this script parent repository.',
    )
    parser.add_argument(
        '--check-runs',
        action='store_true',
        help='Also validate completed run directories under artifacts/runs.',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    failures = validate(root, check_runs=args.check_runs)
    if failures:
        print('Project structure validation failed:')
        for failure in failures:
            print(f'  - {failure}')
        return 1

    print(f'Project structure validation passed: {root}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
