"""Launch limits. Plain code only: the verdict never depends on a model or on the note."""

from dataclasses import dataclass
from typing import Literal

WIND_MAX_KNOTS = 25
TEMP_MIN_C = 4
FUEL_MIN_PCT = 98
FUEL_MAX_PCT = 100

Verdict = Literal["go", "no_go"]


@dataclass(frozen=True)
class Violation:
    reading: str
    value: float
    message: str


@dataclass(frozen=True)
class LimitResult:
    verdict: Verdict
    violations: list[Violation]


def check_limits(wind_knots: float, temp_c: float, fuel_pct: float) -> LimitResult:
    violations = []
    if wind_knots > WIND_MAX_KNOTS:
        violations.append(
            Violation(
                "wind_knots",
                wind_knots,
                f"Wind {wind_knots:g} kt exceeds the limit of {WIND_MAX_KNOTS} kt or less",
            )
        )
    if temp_c < TEMP_MIN_C:
        violations.append(
            Violation(
                "temp_c",
                temp_c,
                f"Temperature {temp_c:g} °C is below the limit of {TEMP_MIN_C} °C or more",
            )
        )
    if not FUEL_MIN_PCT <= fuel_pct <= FUEL_MAX_PCT:
        violations.append(
            Violation(
                "fuel_pct",
                fuel_pct,
                f"Fuel {fuel_pct:g}% is outside the limit of {FUEL_MIN_PCT} to {FUEL_MAX_PCT}%",
            )
        )
    return LimitResult("no_go" if violations else "go", violations)
