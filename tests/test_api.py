import pytest


def test_filing_returns_the_code_verdict(client, good):
    r = client.post("/api/reports", json={**good, "wind_knots": 27})
    assert r.status_code == 201
    body = r.json()
    assert body["verdict"] == "no_go"
    assert body["violations"] == [
        {
            "reading": "wind_knots",
            "value": 27,
            "message": "Wind 27 kt exceeds the limit of 25 kt or less",
        }
    ]


def test_all_fields_are_saved(client, good):
    report_id = client.post("/api/reports", json=good).json()["id"]
    body = client.get(f"/api/reports/{report_id}").json()
    assert {k: body[k] for k in good} == good
    assert body["verdict"] == "go"


def test_reading_just_past_a_limit_is_accepted_not_rejected(client, good):
    r = client.post("/api/reports", json={**good, "fuel_pct": 100.1})
    assert r.status_code == 201
    assert r.json()["verdict"] == "no_go"


def test_limits_check_is_the_first_trace_step(client, good):
    body = client.post("/api/reports", json=good).json()
    step = body["steps"][0]
    assert step["name"] == "limits_check"
    assert step["kind"] == "code"
    assert step["input_tokens"] == step["output_tokens"] == 0


@pytest.mark.parametrize("field", ["name", "station", "wind_knots", "temp_c", "fuel_pct", "note"])
def test_missing_field_is_rejected_with_clear_message(client, good, field):
    del good[field]
    r = client.post("/api/reports", json=good)
    assert r.status_code == 422
    assert r.json()["errors"] == {field: f"{field} is required"}


@pytest.mark.parametrize(
    ("patch", "field", "message"),
    [
        ({"name": "   "}, "name", "name must not be empty"),
        ({"note": ""}, "note", "note must not be empty"),
        ({"note": "x" * 5001}, "note", "note must be 5000 characters or fewer"),
        ({"temp_c": "cold"}, "temp_c", "temp_c must be a number"),
        ({"wind_knots": -3}, "wind_knots", "wind_knots must be between 0 and 200"),
        ({"fuel_pct": 151}, "fuel_pct", "fuel_pct must be between 0 and 150"),
        (
            {"station": "MARS"},
            "station",
            "station must be one of PROP, GNC, COMMS, WX, GND, RANGE",
        ),
    ],
)
def test_bad_input_is_rejected_with_clear_message(client, good, patch, field, message):
    r = client.post("/api/reports", json={**good, **patch})
    assert r.status_code == 422
    assert r.json()["errors"][field] == message


def test_non_finite_number_is_rejected(client, good):
    r = client.post(
        "/api/reports",
        content='{"name":"a","station":"WX","wind_knots":NaN,"temp_c":5,"fuel_pct":99,"note":"n"}',
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 422
    assert r.json()["errors"]["wind_knots"] == "wind_knots must be a finite number"


def test_rejected_report_is_not_saved(client, good):
    client.post("/api/reports", json={**good, "name": ""})
    assert client.get("/api/reports").json() == []


def test_unknown_report_is_404(client):
    r = client.get("/api/reports/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "report 999 not found"}


def test_list_returns_filed_reports(client, good):
    client.post("/api/reports", json=good)
    client.post("/api/reports", json={**good, "station": "WX"})
    assert sorted(r["station"] for r in client.get("/api/reports").json()) == ["PROP", "WX"]


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}
