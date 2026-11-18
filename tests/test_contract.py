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


def test_export_check_passes_when_in_sync(capsys):
    from app.export_openapi import main

    assert main(["--check"]) == 0


def test_export_check_fails_on_drift(tmp_path, monkeypatch):
    from app import export_openapi

    stale = tmp_path / "openapi.json"
    stale.write_text("{}")
    monkeypatch.setattr(export_openapi, "SPEC", stale)
    assert export_openapi.main(["--check"]) == 1
    assert export_openapi.main([]) == 0  # rewrite it
    assert export_openapi.main(["--check"]) == 0
