from symbiotic_swe.cli import build_parser


def test_cli_exposes_all_execution_modes() -> None:
    parser = build_parser()

    task_args = parser.parse_args(['task', '--task-id', 'demo-task'])
    smoke_args = parser.parse_args(['smoke'])
    benchmark_args = parser.parse_args(
        ['benchmark', '--task-id', 'bug-001', '--task-id', 'bug-002']
    )
    ablation_args = parser.parse_args(
        ['ablation', '--ablation-name', 'no-symbolic', '--task-id', 'bug-001']
    )

    assert task_args.command == 'task'
    assert smoke_args.command == 'smoke'
    assert smoke_args.task_ids is None
    assert benchmark_args.command == 'benchmark'
    assert benchmark_args.task_ids == ['bug-001', 'bug-002']
    assert ablation_args.command == 'ablation'
