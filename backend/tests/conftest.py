import pytest
from fastapi.testclient import TestClient

from app.main import create_app

GOOD = {
    "name": "Priya Shah",
    "station": "PROP",
    "wind_knots": 12,
    "temp_c": 9,
    "fuel_pct": 99.2,
    "note": "LOX vent valve 2 took ~400ms longer to close. Recovered on retry.",
}


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "mission.db"


@pytest.fixture
def client(db_path):
    with TestClient(create_app(db_path=db_path, run_pipeline=False)) as c:
        yield c
