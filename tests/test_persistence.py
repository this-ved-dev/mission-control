from fastapi.testclient import TestClient

from app.main import create_app


def test_reports_survive_a_restart(settings, good):
    with TestClient(create_app(settings)) as first:
        report_id = first.post("/api/reports", json=good).json()["id"]

    # A brand-new app instance on the same database file, as after a server restart.
    with TestClient(create_app(settings)) as second:
        body = second.get(f"/api/reports/{report_id}").json()

    assert {k: body[k] for k in good} == good
