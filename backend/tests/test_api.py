import pytest

from tests.conftest import GOOD


def test_file_report_saves_all_fields(client):
    r = client.post("/api/reports", json=GOOD)
    assert r.status_code == 202
    report = client.get(f"/api/reports/{r.json()['id']}").json()
    for key, value in GOOD.items():
        assert report[key] == value
    assert report["status"] == "received"


def test_out_of_limit_reading_is_valid_input(client):
    # 30 kt breaks a launch limit but is a real reading: accept it, verdict comes later.
    assert client.post("/api/reports", json={**GOOD, "wind_knots": 30}).status_code == 202
    assert client.post("/api/reports", json={**GOOD, "fuel_pct": 100.1}).status_code == 202


@pytest.mark.parametrize(
    "patch, field, text",
    [
        ({"fuel_pct": None}, "fuel_pct", "number"),
        ({"temp_c": "abc"}, "temp_c", "number"),
        ({"note": "   "}, "note", "empty"),
        ({"name": ""}, "name", "empty"),
        ({"wind_knots": -3}, "wind_knots", "0"),
        ({"fuel_pct": 151}, "fuel_pct", "150"),
        ({"note": "x" * 5001}, "note", "5000"),
    ],
)
def test_bad_input_rejected_with_clear_message(client, patch, field, text):
    r = client.post("/api/reports", json={**GOOD, **patch})
    assert r.status_code == 422
    errors = r.json()["errors"]
    assert field in errors and text in errors[field]


def test_missing_field_is_named(client):
    body = {k: v for k, v in GOOD.items() if k != "station"}
    r = client.post("/api/reports", json=body)
    assert r.status_code == 422
    assert "required" in r.json()["errors"]["station"]


def test_unknown_report_is_404(client):
    assert client.get("/api/reports/999").status_code == 404


def test_limits_check_endpoint_uses_plain_code(client):
    r = client.post("/api/limits/check", json={"wind_knots": 25.1, "temp_c": 4, "fuel_pct": 98})
    assert r.json()["verdict"] == "no_go"
    assert [v["field"] for v in r.json()["violations"]] == ["wind_knots"]
