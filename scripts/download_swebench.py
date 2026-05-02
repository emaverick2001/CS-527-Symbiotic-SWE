from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

PRESET_DATASETS = {
    'verified': 'princeton-nlp/SWE-bench_Verified',
    'lite': 'princeton-nlp/SWE-bench_Lite',
    'full': 'princeton-nlp/SWE-bench',
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(
        description='Download SWE-bench into the project benchmark directory.',
    )
    parser.add_argument(
        '--preset',
        choices=sorted(PRESET_DATASETS),
        default='verified',
        help='Named SWE-bench dataset to download.',
    )
    parser.add_argument(
        '--dataset-id',
        help='Override the Hugging Face dataset id. Defaults to the selected preset.',
    )
    parser.add_argument(
        '--split',
        help='Optional split to download. If omitted, all available splits are downloaded.',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Directory where the exported benchmark files should be written.',
    )
    parser.add_argument(
        '--hf-cache-dir',
        type=Path,
        default=root / 'artifacts' / 'cache' / 'huggingface' / 'datasets',
        help='Project-local Hugging Face cache directory.',
    )
    parser.add_argument(
        '--format',
        choices=('hf', 'jsonl', 'both'),
        default='both',
        help='Whether to save the dataset in Hugging Face format, JSONL, or both.',
    )
    return parser.parse_args()


def default_output_dir(root: Path, preset: str) -> Path:
    return root / 'data' / 'benchmarks' / 'swe_bench' / preset


def resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir is not None:
        return cast(Path, args.output_dir).resolve()
    return default_output_dir(project_root(), args.preset)


def _write_jsonl(rows: list[dict[str, Any]], target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + '\n')


def _load_dataset(dataset_id: str, split: str | None, cache_dir: Path) -> Any:
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(
            'The `datasets` package is required. Install it with '
            '`poetry run pip install datasets` or add it to your Poetry env first.'
        ) from exc

    load_kwargs: dict[str, Any] = {
        'path': dataset_id,
        'cache_dir': str(cache_dir),
    }
    if split is not None:
        load_kwargs['split'] = split
    return load_dataset(**load_kwargs)


def main() -> int:
    args = parse_args()
    dataset_id = args.dataset_id or PRESET_DATASETS[args.preset]
    output_dir = resolve_output_dir(args)
    hf_cache_dir = args.hf_cache_dir.resolve()
    hf_cache_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = _load_dataset(dataset_id, args.split, hf_cache_dir)
    saved_splits: dict[str, int] = {}

    if args.format in {'hf', 'both'}:
        (output_dir / 'hf').mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(output_dir / 'hf'))

    if hasattr(dataset, 'items'):
        split_items = dataset.items()
    else:
        split_name = args.split or 'default'
        split_items = [(split_name, dataset)]

    if args.format in {'jsonl', 'both'}:
        for split_name, split_dataset in split_items:
            rows = list(split_dataset)
            saved_splits[split_name] = len(rows)
            _write_jsonl(rows, output_dir / 'jsonl' / f'{split_name}.jsonl')
    else:
        for split_name, split_dataset in split_items:
            saved_splits[split_name] = len(split_dataset)

    metadata = {
        'downloaded_at': datetime.now(tz=UTC).isoformat(),
        'dataset_id': dataset_id,
        'preset': args.preset,
        'split': args.split,
        'output_dir': str(output_dir),
        'hf_cache_dir': str(hf_cache_dir),
        'format': args.format,
        'splits': saved_splits,
    }
    (output_dir / 'metadata.json').write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )

    print(f'Downloaded {dataset_id} to {output_dir}')
    print(f'Hugging Face cache: {hf_cache_dir}')
    for split_name, row_count in saved_splits.items():
        print(f'  {split_name}: {row_count} rows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
