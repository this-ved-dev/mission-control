from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import GOOD


def test_reports_survive_a_restart(db_path):
    with TestClient(create_app(db_path=db_path, run_pipeline=False)) as first:
        report_id = first.post("/api/reports", json=GOOD).json()["id"]

    # A brand-new app instance on the same file: nothing is held in memory.
    with TestClient(create_app(db_path=db_path, run_pipeline=False)) as second:
        reports = second.get("/api/reports").json()
        assert [r["id"] for r in reports] == [report_id]
        assert reports[0]["note"] == GOOD["note"]
