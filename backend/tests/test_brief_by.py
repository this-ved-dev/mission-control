import pytest

from app.brief_by import brief_by_minutes, effective_severity


@pytest.mark.parametrize("severity, minutes", [("high", 5), ("medium", 15), ("low", 30)])
def test_time_follows_severity(severity, minutes):
    assert brief_by_minutes(severity, has_violations=False) == minutes


@pytest.mark.parametrize("severity", ["low", "medium", "high"])
def test_any_violation_counts_as_high(severity):
    assert effective_severity(severity, has_violations=True) == "high"
    assert brief_by_minutes(severity, has_violations=True) == 5
