from typing import Literal

Severity = Literal["low", "medium", "high"]

BRIEF_BY_MINUTES: dict[str, int] = {"high": 5, "medium": 15, "low": 30}


def effective_severity(severity: Severity, has_violations: bool) -> Severity:
    return "high" if has_violations else severity


def brief_by_minutes(severity: Severity, has_violations: bool) -> int:
    return BRIEF_BY_MINUTES[effective_severity(severity, has_violations)]
