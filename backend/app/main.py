from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings
from app.db import DB
from app.limits import LimitResult, check_limits
from app.llm.base import LLMClient
from app.pipeline import run_pipeline as process
from app.schemas import Approval, Filed, Readings, ReportIn, ReportOut

NOT_FOUND = {404: {"description": "No such report"}}
CONFLICT = {409: {"description": "Report is not in a state that allows this"}}


def validation_errors(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Flatten Pydantic errors to {field: message} so the form can show them per field."""
    errors: dict[str, str] = {}
    for e in exc.errors():
        field = str(e["loc"][-1]) if len(e["loc"]) > 1 else "body"
        msg = e["msg"].removeprefix("Value error, ")
        errors.setdefault(field, f"{field}: {msg}")
    return JSONResponse({"errors": errors}, status_code=422)


def create_app(
    db_path: Path | str = "data/mission.db",
    llm: LLMClient | None = None,
    settings: Settings | None = None,
    run_pipeline: bool = True,
) -> FastAPI:
    settings = settings or Settings.from_env()
    llm = llm or settings.client()
    app = FastAPI(title="Mission Control", version="0.1.0")
    app.add_exception_handler(RequestValidationError, validation_errors)
    db = DB(db_path)
    db.mark_interrupted()

    def get_or_404(report_id: int) -> dict:
        report = db.get(report_id)
        if report is None:
            raise HTTPException(404, f"report {report_id} not found")
        return report

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/limits/check")
    def limits_check(readings: Readings) -> LimitResult:
        return check_limits(readings.wind_knots, readings.temp_c, readings.fuel_pct)

    @app.post("/api/reports", status_code=202)
    def file_report(report: ReportIn, tasks: BackgroundTasks) -> Filed:
        report_id = db.insert_report(report.model_dump())
        if run_pipeline:
            tasks.add_task(process, db, llm, settings, report_id)
        return Filed(id=report_id)

    @app.get("/api/reports")
    def list_reports() -> list[ReportOut]:
        return db.list()

    @app.get("/api/reports/{report_id}", responses=NOT_FOUND)
    def get_report(report_id: int) -> ReportOut:
        return get_or_404(report_id)

    @app.post("/api/reports/{report_id}/retry", status_code=202, responses=NOT_FOUND | CONFLICT)
    def retry(report_id: int, tasks: BackgroundTasks) -> Filed:
        if get_or_404(report_id)["status"] != "error":
            raise HTTPException(409, "only a report whose pipeline failed can be retried")
        db.clear_steps(report_id)
        db.update_report(report_id, status="received")
        tasks.add_task(process, db, llm, settings, report_id)
        return Filed(id=report_id)

    @app.post("/api/reports/{report_id}/approve", responses=NOT_FOUND | CONFLICT)
    def approve(report_id: int, body: Approval) -> ReportOut:
        """The only way a briefing becomes approved: a person, by name."""
        report = get_or_404(report_id)
        if report["status"] == "needs_review" and not body.acknowledged_flag:
            raise HTTPException(409, "acknowledge the flagged note before approving")
        if not db.approve(report_id, body.approver):
            raise HTTPException(
                409,
                f"report is {report['status']}; only a briefing awaiting approval can be approved",
            )
        return get_or_404(report_id)

    return app
