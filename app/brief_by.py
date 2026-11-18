"""How soon the Flight Director must be briefed. Plain code."""

from typing import Literal

Severity = Literal["low", "medium", "high"]

MINUTES: dict[str, int] = {"high": 5, "medium": 15, "low": 30}


def effective_severity(severity: Severity, has_violations: bool) -> Severity:
    # A broken launch limit is a code fact; it outranks the model's opinion of severity.
    return "high" if has_violations else severity


def brief_by_minutes(severity: Severity, has_violations: bool) -> int:
    return MINUTES[effective_severity(severity, has_violations)]
