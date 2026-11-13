"""Launch commit criteria. Plain code only: the note is deliberately not a parameter."""

from typing import Literal

from pydantic import BaseModel

WIND_MAX_KNOTS = 25
TEMP_MIN_C = 4
FUEL_MIN_PCT = 98
FUEL_MAX_PCT = 100

Verdict = Literal["go", "no_go"]


class Violation(BaseModel):
    field: str
    value: float
    message: str


class LimitResult(BaseModel):
    verdict: Verdict
    violations: list[Violation]


def check_limits(wind_knots: float, temp_c: float, fuel_pct: float) -> LimitResult:
    violations = []
    if wind_knots > WIND_MAX_KNOTS:
        msg = f"wind {wind_knots} kt exceeds max {WIND_MAX_KNOTS} kt"
        violations.append(Violation(field="wind_knots", value=wind_knots, message=msg))
    if temp_c < TEMP_MIN_C:
        msg = f"temp {temp_c} C below min {TEMP_MIN_C} C"
        violations.append(Violation(field="temp_c", value=temp_c, message=msg))
    if not FUEL_MIN_PCT <= fuel_pct <= FUEL_MAX_PCT:
        msg = f"fuel {fuel_pct}% outside {FUEL_MIN_PCT}-{FUEL_MAX_PCT}%"
        violations.append(Violation(field="fuel_pct", value=fuel_pct, message=msg))
    return LimitResult(verdict="no_go" if violations else "go", violations=violations)
