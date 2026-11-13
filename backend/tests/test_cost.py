from decimal import Decimal

import pytest

from app.cost import Price, report_cost, step_cost

PRICES = {"small": Price(Decimal("1.00"), Decimal("5.00")), "free": Price(Decimal(0), Decimal(0))}


def test_one_million_input_tokens_at_one_dollar():
    assert step_cost("small", 1_000_000, 0, PRICES) == Decimal("1.00")


def test_output_tokens_use_output_rate():
    assert step_cost("small", 0, 200_000, PRICES) == Decimal("1.00")


def test_zero_tokens_cost_nothing():
    assert step_cost("small", 0, 0, PRICES) == 0


def test_local_model_is_free():
    assert step_cost("free", 5000, 5000, PRICES) == 0


def test_unknown_model_is_an_error_not_free():
    with pytest.raises(KeyError, match="mystery"):
        step_cost("mystery", 1, 1, PRICES)


def test_report_total_is_exact_sum_and_skips_code_steps():
    steps = [
        {"model": None, "input_tokens": 0, "output_tokens": 0},  # code step
        {"model": "small", "input_tokens": 300, "output_tokens": 40},
        {"model": "small", "input_tokens": 700, "output_tokens": 60},
    ]
    # (300+700) * 1/1M + (40+60) * 5/1M = 0.001 + 0.0005
    assert report_cost(steps, PRICES) == Decimal("0.0015")
