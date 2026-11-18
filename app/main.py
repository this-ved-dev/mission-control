"""App factory. Run with: uvicorn app.main:create_app --factory"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import api, web
from app.config import Settings
from app.llm import LLMClient, make_llm
from app.pipeline import run_pipeline
from app.schemas import field_errors
from app.store import Store


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Re-run reports a restart cut off mid-pipeline so none stay stuck in "processing".
        store, llm = app.state.store, app.state.llm
        app.state.resumed = [
            asyncio.create_task(run_pipeline(store, llm, i)) for i in store.interrupted()
        ]
        yield

    app = FastAPI(
        lifespan=lifespan,
        title="Mission Control",
        version="2.0.0",
        description="Go/No-Go launch console: anomaly reports in, human-approved briefings out.",
    )
    app.state.settings = settings
    app.state.store = Store(settings.db_path)
    app.state.llm = llm or make_llm(settings)
    app.include_router(api.router)
    app.include_router(web.router)
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"message": "Invalid input", "errors": field_errors(exc.errors())}, status_code=422
        )

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
