"""Cost per step and per report, computed in code from token counts."""

from collections.abc import Iterable, Mapping
from decimal import Decimal

# USD per 1M tokens. Claude on Azure AI Foundry bills at the standard Anthropic API rates.
PRICES: dict[str, tuple[Decimal, Decimal]] = {
    "claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "fake": (Decimal("2"), Decimal("10")),  # offline demo model, priced like Sonnet 5.5
}
MILLION = Decimal(1_000_000)


def step_cost(model: str | None, input_tokens: int, output_tokens: int) -> Decimal:
    if model is None:  # code step
        return Decimal(0)
    if model not in PRICES:
        raise KeyError(f"no price for model {model!r}")
    price_in, price_out = PRICES[model]
    return (price_in * input_tokens + price_out * output_tokens) / MILLION


def report_cost(steps: Iterable[Mapping]) -> Decimal:
    return sum(
        (step_cost(s["model"], s["input_tokens"], s["output_tokens"]) for s in steps),
        Decimal(0),
    )
