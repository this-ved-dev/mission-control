from decimal import Decimal

import pytest

from app.cost import report_cost, step_cost


def test_one_million_input_tokens_costs_the_input_price():
    assert step_cost("claude-sonnet-5-5", 1_000_000, 0) == Decimal("2")


def test_one_million_output_tokens_costs_the_output_price():
    assert step_cost("claude-sonnet-5-5", 0, 1_000_000) == Decimal("10")


def test_small_step_is_exact():
    # 412 * 2 / 1e6 + 38 * 10 / 1e6 = 0.000824 + 0.00038
    assert step_cost("claude-sonnet-5-5", 412, 38) == Decimal("0.001204")


def test_code_steps_cost_nothing():
    assert step_cost(None, 0, 0) == Decimal(0)


def test_unknown_model_is_an_error_not_free():
    with pytest.raises(KeyError, match="no price for model 'mystery'"):
        step_cost("mystery", 10, 10)


def test_report_cost_sums_steps():
    steps = [
        {"model": None, "input_tokens": 0, "output_tokens": 0},
        {"model": "claude-sonnet-5-5", "input_tokens": 412, "output_tokens": 38},
        {"model": "claude-sonnet-5-5", "input_tokens": 1000, "output_tokens": 200},
    ]
    assert report_cost(steps) == Decimal("0.001204") + Decimal("0.004")
