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
    materialize_args = parser.parse_args(['materialize-repos', '--task-id', 'bug-001'])

    assert task_args.command == 'task'
    assert smoke_args.command == 'smoke'
    assert smoke_args.task_ids is None
    assert benchmark_args.command == 'benchmark'
    assert benchmark_args.task_ids == ['bug-001', 'bug-002']
    assert ablation_args.command == 'ablation'
    assert materialize_args.command == 'materialize-repos'
    assert materialize_args.task_ids == ['bug-001']
    assert smoke_args.provider == 'openai'
    assert smoke_args.model == 'gpt-5.4-mini'


def test_cli_accepts_openai_provider_for_smoke() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            'smoke',
            '--preflight-only',
            '--provider',
            'openai',
            '--model',
            'gpt-5.5',
        ]
    )

    assert args.command == 'smoke'
    assert args.preflight_only is True
    assert args.provider == 'openai'
    assert args.model == 'gpt-5.5'
