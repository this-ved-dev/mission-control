import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

GOOD = {
    "name": "Priya Shah",
    "station": "PROP",
    "wind_knots": 18.5,
    "temp_c": 6.2,
    "fuel_pct": 99.1,
    "note": "LOX vent valve 2 took ~400 ms longer to close on the last cycle. Recovered on retry.",
}


@pytest.fixture
def settings(tmp_path):
    return Settings(llm="fake", db_path=str(tmp_path / "mc.db"))


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def good():
    return dict(GOOD)
