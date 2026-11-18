import pytest

from app.limits import check_limits

OK = {"wind_knots": 10, "temp_c": 15, "fuel_pct": 99}


@pytest.mark.parametrize(
    ("override", "verdict"),
    [
        ({"wind_knots": 25}, "go"),  # exactly on the wind limit
        ({"wind_knots": 25.1}, "no_go"),  # just past it
        ({"temp_c": 4}, "go"),  # exactly on the temperature limit
        ({"temp_c": 3.9}, "no_go"),
        ({"fuel_pct": 98}, "go"),  # low fuel edge
        ({"fuel_pct": 97.9}, "no_go"),
        ({"fuel_pct": 100}, "go"),  # high fuel edge
        ({"fuel_pct": 100.1}, "no_go"),
        ({}, "go"),
    ],
)
def test_verdict_on_and_just_past_each_limit(override, verdict):
    result = check_limits(**{**OK, **override})
    assert result.verdict == verdict
    assert bool(result.violations) == (verdict == "no_go")


def test_every_violation_is_listed():
    result = check_limits(wind_knots=30, temp_c=0, fuel_pct=50)
    assert result.verdict == "no_go"
    assert [v.reading for v in result.violations] == ["wind_knots", "temp_c", "fuel_pct"]


def test_violation_describes_value_and_limit():
    (v,) = check_limits(wind_knots=27, temp_c=15, fuel_pct=99).violations
    assert v.value == 27
    assert v.message == "Wind 27 kt exceeds the limit of 25 kt or less"
