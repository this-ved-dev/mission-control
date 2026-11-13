from pathlib import Path

from fastapi import FastAPI


def create_app(db_path: Path | str = "data/mission.db") -> FastAPI:
    app = FastAPI(title="Mission Control", version="0.1.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
