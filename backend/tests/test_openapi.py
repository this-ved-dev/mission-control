import json
from pathlib import Path

from app.main import create_app

SPEC = Path(__file__).parents[2] / "openapi.json"


def test_committed_openapi_spec_matches_the_app(tmp_path):
    live = create_app(db_path=tmp_path / "t.db", run_pipeline=False).openapi()
    assert json.loads(SPEC.read_text()) == live, "run `make openapi` and commit the result"
