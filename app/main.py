"""App factory. Run with: uvicorn app.main:create_app --factory"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import api
from app.config import Settings
from app.schemas import field_errors
from app.store import Store


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="Mission Control",
        version="2.0.0",
        description="Go/No-Go launch console: anomaly reports in, human-approved briefings out.",
    )
    app.state.settings = settings
    app.state.store = Store(settings.db_path)
    app.include_router(api.router)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"message": "Invalid report", "errors": field_errors(exc.errors())}, status_code=422
        )

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
