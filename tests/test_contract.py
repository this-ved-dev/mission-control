import json
from pathlib import Path

from app.export_openapi import current_spec

SPEC = Path(__file__).parent.parent / "openapi.json"


def test_committed_openapi_matches_the_code():
    committed = json.loads(SPEC.read_text())
    assert committed == current_spec(), "run: uv run python -m app.export_openapi"


def test_spec_documents_the_report_endpoints():
    paths = current_spec()["paths"]
    assert {"/api/reports", "/api/reports/{report_id}"} <= paths.keys()
    assert "422" in paths["/api/reports"]["post"]["responses"]
