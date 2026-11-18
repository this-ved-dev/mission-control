"""JSON API under /api. This is what openapi.json documents."""

from fastapi import APIRouter, HTTPException, Request

from app.reports import file_report
from app.schemas import ReportIn, ReportOut, ValidationErrorOut

router = APIRouter(prefix="/api", tags=["reports"])

INVALID = {422: {"model": ValidationErrorOut, "description": "Invalid report"}}


@router.post("/reports", status_code=201, response_model=ReportOut, responses=INVALID)
def create_report(report: ReportIn, request: Request) -> dict:
    store = request.app.state.store
    return store.get_report(file_report(store, report))


@router.get("/reports", response_model=list[ReportOut])
def list_reports(request: Request) -> list[dict]:
    return request.app.state.store.list_reports()


@router.get("/reports/{report_id}", response_model=ReportOut, responses={404: {}})
def get_report(report_id: int, request: Request) -> dict:
    report = request.app.state.store.get_report(report_id)
    if report is None:
        raise HTTPException(404, f"report {report_id} not found")
    return report
