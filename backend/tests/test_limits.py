import pytest

from app.limits import check_limits

OK = {"wind_knots": 10, "temp_c": 15, "fuel_pct": 99}


@pytest.mark.parametrize(
    "field, value, verdict",
    [
        ("wind_knots", 25, "go"),  # exactly on: "25 knots or less"
        ("wind_knots", 25.1, "no_go"),
        ("temp_c", 4, "go"),  # exactly on: "4 C or more"
        ("temp_c", 3.9, "no_go"),
        ("fuel_pct", 98, "go"),  # exactly on low edge
        ("fuel_pct", 97.9, "no_go"),
        ("fuel_pct", 100, "go"),  # exactly on high edge
        ("fuel_pct", 100.1, "no_go"),
    ],
)
def test_each_limit_on_and_just_past(field, value, verdict):
    result = check_limits(**{**OK, field: value})
    assert result.verdict == verdict
    assert len(result.violations) == (verdict == "no_go")
    if result.violations:
        assert result.violations[0].field == field


def test_all_good_is_go_with_no_violations():
    result = check_limits(**OK)
    assert result.verdict == "go"
    assert result.violations == []


def test_all_bad_lists_every_violation():
    result = check_limits(wind_knots=30, temp_c=0, fuel_pct=50)
    assert result.verdict == "no_go"
    assert [v.field for v in result.violations] == ["wind_knots", "temp_c", "fuel_pct"]


def test_violation_message_names_value_and_limit():
    (v,) = check_limits(**{**OK, "wind_knots": 27}).violations
    assert "27" in v.message and "25" in v.message
