from fastapi.testclient import TestClient

from app.main import create_app


def test_health(tmp_path):
    client = TestClient(create_app(db_path=tmp_path / "t.db"))
    assert client.get("/api/health").json() == {"status": "ok"}
