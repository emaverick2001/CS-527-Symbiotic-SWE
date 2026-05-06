"""Generate the RQ3 cost-vs-success scatter plot from a run metrics.json.

The plot is intentionally generated as SVG using only the Python standard
library so it can run in the project environment without adding plotting
dependencies.
"""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_METRICS = Path('artifacts/runs/final_eval_gpt_5_3_codex_sympy_real_tests/metrics.json')
DEFAULT_OUTPUT = Path('docs/figures/cost_success_tradeoff.svg')
DEFAULT_CAPTION = Path('docs/figures/cost_success_tradeoff_caption.md')
CONDITION_ORDER = ['neural_only', 'neural_slicing', 'neural_solver', 'neural_cegf']


@dataclass(frozen=True)
class Point:
    condition: str
    avg_tokens: float
    success_pct: float
    avg_runtime_s: float
    tokens_per_success: float | None


def _load_points(metrics_path: Path) -> list[Point]:
    data = json.loads(metrics_path.read_text(encoding='utf-8'))
    points: list[Point] = []
    for condition in CONDITION_ORDER:
        if condition not in data:
            continue
        metrics = data[condition]
        tokens_per_success = metrics.get('tokens_per_success')
        if metrics.get('test_resolved_tasks', 0) == 0:
            tokens_per_success = None
        points.append(
            Point(
                condition=condition,
                avg_tokens=float(metrics['avg_tokens']),
                success_pct=float(metrics['real_test_success_rate']) * 100.0,
                avg_runtime_s=float(metrics['avg_duration_ms']) / 1000.0,
                tokens_per_success=(
                    None if tokens_per_success is None else float(tokens_per_success)
                ),
            )
        )
    if not points:
        raise ValueError(f'no known conditions found in {metrics_path}')
    return points


def _nice_bounds(values: list[float], pad_fraction: float = 0.12) -> tuple[float, float]:
    low = min(values)
    high = max(values)
    if low == high:
        return low * 0.9, high * 1.1
    pad = (high - low) * pad_fraction
    return low - pad, high + pad


def _fmt_tokens(value: float) -> str:
    return f'{value:,.0f}'


def _fmt_tokens_one(value: float) -> str:
    return f'{value:,.1f}'


def _svg_text(text: str) -> str:
    return html.escape(text, quote=True)


def _render_svg(points: list[Point], title: str) -> str:
    width = 1200
    height = 760
    left = 118
    right = 330
    top = 94
    bottom = 116
    plot_w = width - left - right
    plot_h = height - top - bottom

    x_min, x_max = _nice_bounds([p.avg_tokens for p in points])
    y_min, y_max = _nice_bounds([0.0] + [p.success_pct for p in points], pad_fraction=0.18)
    y_min = max(0.0, y_min)

    runtime_min = min(p.avg_runtime_s for p in points)
    runtime_max = max(p.avg_runtime_s for p in points)

    def x_scale(value: float) -> float:
        return left + ((value - x_min) / (x_max - x_min)) * plot_w

    def y_scale(value: float) -> float:
        return top + (1.0 - ((value - y_min) / (y_max - y_min))) * plot_h

    def radius(value: float) -> float:
        if runtime_max == runtime_min:
            return 14.0
        return 10.0 + ((value - runtime_min) / (runtime_max - runtime_min)) * 16.0

    colors = {
        'neural_only': '#4C78A8',
        'neural_slicing': '#59A14F',
        'neural_solver': '#F28E2B',
        'neural_cegf': '#B07AA1',
    }

    x_ticks = 5
    y_ticks = 5
    lines: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f'<title>{_svg_text(title)}</title>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="42" text-anchor="middle" '
        'font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="700" fill="#222">'
        f'{_svg_text(title)}</text>',
        f'<text x="{width / 2}" y="72" text-anchor="middle" '
        'font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#555">'
        'Held-out SymPy final evaluation; bubble size encodes average runtime'
        '</text>',
    ]

    # Grid and axes.
    for i in range(x_ticks + 1):
        value = x_min + (x_max - x_min) * i / x_ticks
        x = x_scale(value)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top + plot_h + 30}" text-anchor="middle" '
            'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#555">'
            f'{_fmt_tokens(value)}</text>'
        )
    for i in range(y_ticks + 1):
        value = y_min + (y_max - y_min) * i / y_ticks
        y = y_scale(value)
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left - 16}" y="{y + 4:.1f}" text-anchor="end" '
            'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#555">'
            f'{value:.0f}%</text>'
        )
    lines.extend([
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#333" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#333" stroke-width="1.4"/>',
        f'<text x="{left + plot_w / 2}" y="{height - 36}" text-anchor="middle" '
        'font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="700" fill="#222">'
        'Average tokens per task</text>',
        f'<text x="34" y="{top + plot_h / 2}" text-anchor="middle" '
        'font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="700" fill="#222" '
        'transform="rotate(-90 34 '
        f'{top + plot_h / 2})">Real-test success rate</text>',
    ])

    # Points and labels.
    for point in points:
        x = x_scale(point.avg_tokens)
        y = y_scale(point.success_pct)
        r = radius(point.avg_runtime_s)
        color = colors.get(point.condition, '#777777')
        label_text = point.condition
        tps = 'N/A' if point.tokens_per_success is None else _fmt_tokens_one(point.tokens_per_success)
        lines.extend([
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" fill-opacity="0.86" '
            'stroke="#222" stroke-width="1.2"/>',
            f'<text x="{x + r + 8:.1f}" y="{y - 4:.1f}" '
            'font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="700" fill="#222">'
            f'{_svg_text(label_text)}</text>',
            f'<text x="{x + r + 8:.1f}" y="{y + 14:.1f}" '
            'font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#555">'
            f'TPS {_svg_text(tps)}, {point.avg_runtime_s:.1f}s</text>',
        ])

    # Legend / interpretation panel.
    panel_x = left + plot_w + 48
    panel_y = top + 10
    panel_w = right - 78
    lines.extend([
        f'<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="260" rx="8" '
        'fill="#f7f7f7" stroke="#d0d0d0"/>',
        f'<text x="{panel_x + 18}" y="{panel_y + 32}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="700" fill="#222">'
        'How to read this</text>',
        f'<text x="{panel_x + 18}" y="{panel_y + 62}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#444">'
        'Up is better: more tasks resolved.</text>',
        f'<text x="{panel_x + 18}" y="{panel_y + 84}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#444">'
        'Left is cheaper: fewer tokens per task.</text>',
        f'<text x="{panel_x + 18}" y="{panel_y + 106}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#444">'
        'Larger bubbles took longer.</text>',
        f'<text x="{panel_x + 18}" y="{panel_y + 140}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#444">'
        'CEGF is most effective, but also</text>',
        f'<text x="{panel_x + 18}" y="{panel_y + 160}" '
        'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#444">'
        'the highest-cost condition.</text>',
    ])

    legend_y = panel_y + 196
    for idx, point in enumerate(points):
        y = legend_y + idx * 20
        color = colors.get(point.condition, '#777777')
        lines.append(f'<circle cx="{panel_x + 18}" cy="{y - 4}" r="6" fill="{color}" stroke="#222" stroke-width="0.8"/>')
        lines.append(
            f'<text x="{panel_x + 32}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
            'font-size="12" fill="#333">'
            f'{_svg_text(point.condition)}: {point.success_pct:.1f}% success</text>'
        )

    lines.append('</svg>')
    return '\n'.join(lines) + '\n'


def _render_caption(points: list[Point], metrics_path: Path) -> str:
    by_condition = {p.condition: p for p in points}
    neural_only = by_condition.get('neural_only')
    cegf = by_condition.get('neural_cegf')
    if neural_only and cegf:
        comparison = (
            f'In this run, `neural_cegf` increases real-test success from '
            f'{neural_only.success_pct:.1f}% to {cegf.success_pct:.1f}%, while average token use rises from '
            f'{_fmt_tokens_one(neural_only.avg_tokens)} to {_fmt_tokens_one(cegf.avg_tokens)} and average runtime '
            f'rises from {neural_only.avg_runtime_s:.1f}s to {cegf.avg_runtime_s:.1f}s.'
        )
    else:
        comparison = 'The plotted conditions show the tradeoff between repair success and model/runtime cost.'

    return f"""\
**Figure: Cost-effectiveness tradeoff on the held-out SymPy final evaluation.**

Each point is one ablation condition from `{metrics_path}`. The x-axis reports average
LLM tokens per task, the y-axis reports real-test success rate, and bubble size encodes
average wall-clock runtime. {comparison} The figure supports the RQ3 conclusion that
counterexample-guided feedback is more effective but not globally more efficient: its
overhead is justified mainly when it recovers tasks that the neural baseline does not solve.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, default=DEFAULT_METRICS)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--caption', type=Path, default=DEFAULT_CAPTION)
    parser.add_argument(
        '--title',
        default='Cost vs Success Tradeoff',
        help='SVG title text',
    )
    args = parser.parse_args()

    points = _load_points(args.metrics)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.caption.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_render_svg(points, args.title), encoding='utf-8')
    args.caption.write_text(_render_caption(points, args.metrics), encoding='utf-8')
    print(f'wrote {args.output}')
    print(f'wrote {args.caption}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
