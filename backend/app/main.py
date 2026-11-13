from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db import DB
from app.limits import LimitResult, check_limits
from app.schemas import Filed, Readings, ReportIn, ReportOut


def validation_errors(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Flatten Pydantic errors to {field: message} so the form can show them per field."""
    errors: dict[str, str] = {}
    for e in exc.errors():
        field = str(e["loc"][-1]) if len(e["loc"]) > 1 else "body"
        msg = e["msg"].removeprefix("Value error, ")
        errors.setdefault(field, f"{field}: {msg}")
    return JSONResponse({"errors": errors}, status_code=422)


def create_app(db_path: Path | str = "data/mission.db", run_pipeline: bool = True) -> FastAPI:
    app = FastAPI(title="Mission Control", version="0.1.0")
    app.add_exception_handler(RequestValidationError, validation_errors)
    db = DB(db_path)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/limits/check")
    def limits_check(readings: Readings) -> LimitResult:
        return check_limits(readings.wind_knots, readings.temp_c, readings.fuel_pct)

    @app.post("/api/reports", status_code=202)
    def file_report(report: ReportIn) -> Filed:
        return Filed(id=db.insert_report(report.model_dump()))

    @app.get("/api/reports")
    def list_reports() -> list[ReportOut]:
        return db.list()

    @app.get("/api/reports/{report_id}", responses={404: {"description": "No such report"}})
    def get_report(report_id: int) -> ReportOut:
        report = db.get(report_id)
        if report is None:
            raise HTTPException(404, f"report {report_id} not found")
        return report

    return app
