"""Cost in code, never from a model. Decimal so many tiny costs sum exactly."""

from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any, NamedTuple

PER_MILLION = Decimal(1_000_000)


class Price(NamedTuple):
    input_per_m: Decimal
    output_per_m: Decimal


def step_cost(
    model: str, input_tokens: int, output_tokens: int, prices: Mapping[str, Price]
) -> Decimal:
    if model not in prices:
        raise KeyError(f"no price for model {model!r}")
    p = prices[model]
    return (p.input_per_m * input_tokens + p.output_per_m * output_tokens) / PER_MILLION


def report_cost(steps: Iterable[Mapping[str, Any]], prices: Mapping[str, Price]) -> Decimal:
    return sum(
        (
            step_cost(s["model"], s["input_tokens"], s["output_tokens"], prices)
            for s in steps
            if s["model"]
        ),
        Decimal(0),
    )
