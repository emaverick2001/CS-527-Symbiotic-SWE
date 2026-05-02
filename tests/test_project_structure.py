from pathlib import Path

from scripts.validate_project_structure import RUN_ID_PATTERN, validate


def test_project_structure_contract_is_present() -> None:
    root = Path(__file__).resolve().parents[1]

    assert validate(root) == []


def test_run_id_pattern_requires_symbolic_solver_fields() -> None:
    assert RUN_ID_PATTERN.fullmatch('20260502_132500_gpt4o_symbolic-feedback_crosshair-z3_s42')
    assert RUN_ID_PATTERN.fullmatch('20260502_132500_gpt4o_ablation-no-symbolic_none_s0')
    assert not RUN_ID_PATTERN.fullmatch('2026-05-02_gpt4o_symbolic-feedback_crosshair-z3_42')
