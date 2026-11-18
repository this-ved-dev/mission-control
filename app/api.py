"""JSON API under /api. This is what openapi.json documents."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse

from app import reports
from app.pipeline import run_pipeline
from app.schemas import ApproveIn, ReportIn, ReportOut, ValidationErrorOut

router = APIRouter(prefix="/api", tags=["reports"])

INVALID = {422: {"model": ValidationErrorOut, "description": "Invalid input"}}
NOT_FOUND = {404: {"description": "No such report"}}


@router.post("/reports", status_code=201, response_model=ReportOut, responses=INVALID)
def create_report(report: ReportIn, request: Request, background: BackgroundTasks) -> dict:
    """File a report. The verdict is set from the readings now; the model pipeline runs after."""
    store = request.app.state.store
    report_id = reports.file_report(store, report)
    background.add_task(run_pipeline, store, request.app.state.llm, report_id)
    return store.get_report(report_id)


@router.get("/reports", response_model=list[ReportOut])
def list_reports(request: Request) -> list[dict]:
    """All reports, the ones needing the Flight Director first."""
    return reports.list_by_urgency(request.app.state.store)


@router.get("/reports/{report_id}", response_model=ReportOut, responses=NOT_FOUND)
def get_report(report_id: int, request: Request) -> dict:
    report = request.app.state.store.get_report(report_id)
    if report is None:
        raise HTTPException(404, f"report {report_id} not found")
    return report


@router.post(
    "/reports/{report_id}/approve",
    response_model=ReportOut,
    responses={**NOT_FOUND, 409: {"description": "Not awaiting approval"}, **INVALID},
)
def approve_report(report_id: int, body: ApproveIn, request: Request):
    """Human sign-off. Flagged reports need acknowledge_flags=true."""
    try:
        return reports.approve(
            request.app.state.store, report_id, body.approver, body.acknowledge_flags
        )
    except reports.NotFound as e:
        raise HTTPException(404, str(e)) from e
    except reports.Conflict as e:
        raise HTTPException(409, str(e)) from e
    except reports.NeedsAcknowledgement as e:
        return JSONResponse(
            {"message": "Invalid input", "errors": {"acknowledge_flags": str(e)}}, status_code=422
        )
