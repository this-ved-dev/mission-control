"""Server-rendered Flight Director console and filing form. Same use cases as the JSON API."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import reports
from app.limits import FUEL_MAX_PCT, FUEL_MIN_PCT, TEMP_MIN_C, WIND_MAX_KNOTS
from app.pipeline import run_pipeline
from app.schemas import NOTE_MAX, ApproveIn, ReportIn, field_errors

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

STATIONS = {
    "PROP": "Propulsion",
    "GNC": "Guidance & nav",
    "COMMS": "Communications",
    "WX": "Weather",
    "GND": "Ground systems",
    "RANGE": "Range safety",
}
SUBSYSTEMS = {
    "propulsion": "PROPULSION",
    "avionics": "AVIONICS",
    "communications": "COMMS",
    "weather": "WEATHER",
    "ground_systems": "GROUND",
    "range_safety": "RANGE",
    "other": "OTHER",
}
EXPECTED_STEPS = 8  # limits, classify, brief_by, 3 checks, one draft and one review
AWAITING = ("pending_approval", "needs_review")


def usd(value: str | Decimal) -> str:
    return f"${Decimal(value):.4f}"


templates.env.filters["usd"] = usd
templates.env.filters["clock"] = lambda iso: iso[11:16] if iso else "—"


def readings(report: dict) -> list[dict]:
    """Reading cells for the pass. ✓/✕ follow the code verdict; the margin is display only."""
    broken = {v["reading"] for v in report["violations"]}
    wind, temp, fuel = report["wind_knots"], report["temp_c"], report["fuel_pct"]
    fuel_margin = min(fuel - FUEL_MIN_PCT, FUEL_MAX_PCT - fuel)
    cells = [
        (
            "wind_knots",
            "WIND",
            f"{wind:g}",
            "KT",
            f"≤ {WIND_MAX_KNOTS}",
            WIND_MAX_KNOTS - wind,
            "kt",
        ),
        ("temp_c", "TEMP", f"{temp:g}", "°C", f"≥ {TEMP_MIN_C}", temp - TEMP_MIN_C, "°C"),
        ("fuel_pct", "FUEL", f"{fuel:g}", "%", f"{FUEL_MIN_PCT}–{FUEL_MAX_PCT}", fuel_margin, "%"),
    ]
    return [
        {
            "key": key,
            "label": label,
            "value": value,
            "unit": unit,
            "limit": limit,
            "ok": key not in broken,
            "margin": f"{abs(margin):.3g} {u} {'margin' if margin >= 0 else 'over'}",
        }
        for key, label, value, unit, limit, margin, u in cells
    ]


def trace_rows(steps: list[dict]) -> list[list[dict]]:
    """Group the three concurrent checks into one row so the trace shows they ran together."""
    rows: list[list[dict]] = []
    for step in steps:
        if step["name"].startswith("check_") and rows and rows[-1][0]["name"].startswith("check_"):
            rows[-1].append(step)
        else:
            rows.append([step])
    return rows


def barcode(report_id: int) -> list[tuple[int, int]]:
    """Decorative bars derived from the report id, a nod to the boarding-pass reference."""
    bars, x, seed = [], 0, report_id * 2654435761 % 2**32
    while x < 300:
        seed = (seed * 1103515245 + 12345) % 2**31
        width = 1 + seed % 4
        bars.append((x, width))
        x += width + 1 + (seed >> 8) % 3
    return bars


def console(request: Request, report_id: int | None = None, status_code: int = 200, **extra):
    store = request.app.state.store
    board = reports.list_by_urgency(store)
    selected = None
    if report_id is not None:
        selected = store.get_report(report_id)
        if selected is None:
            raise HTTPException(404, f"report {report_id} not found")
    elif board:
        selected = board[0]
    awaiting = [r for r in board if r["status"] in AWAITING]
    context = {
        "board": board,
        "r": selected,
        "live": any(r["status"] in ("received", "processing") for r in board),
        "counts": {
            "no_go": sum(r["verdict"] == "no_go" and r["status"] != "approved" for r in board),
            "awaiting": len(awaiting),
            "next_deadline": min(
                (r["brief_by_at"] for r in awaiting if r["brief_by_at"]), default=None
            ),
        },
        "stations": STATIONS,
        "subsystems": SUBSYSTEMS,
        "expected_steps": EXPECTED_STEPS,
        **extra,
    }
    if selected:
        context |= {
            "cells": readings(selected),
            "rows": trace_rows(selected["steps"]),
            "bars": barcode(selected["id"]),
            "max_tokens": max(s["input_tokens"] + s["output_tokens"] for s in selected["steps"])
            or 1,
        }
    context["now_clock"] = datetime.now(UTC).strftime("%H:%M")
    return templates.TemplateResponse(request, "console.html", context, status_code=status_code)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return console(request)


@router.get("/reports/{report_id}", response_class=HTMLResponse)
def report_page(request: Request, report_id: int):
    return console(request, report_id)


@router.post("/reports/{report_id}/approve", response_class=HTMLResponse)
async def approve_from_console(request: Request, report_id: int):
    form = await request.form()
    try:
        body = ApproveIn(
            approver=form.get("approver", ""),
            acknowledge_flags=form.get("acknowledge_flags") == "on",
        )
        reports.approve(request.app.state.store, report_id, body.approver, body.acknowledge_flags)
    except ValidationError as e:
        return console(request, report_id, 422, decision_error=field_errors(e.errors())["approver"])
    except reports.NotFound as e:
        raise HTTPException(404, str(e)) from e
    except reports.NeedsAcknowledgement as e:
        return console(request, report_id, 422, decision_error=str(e))
    except reports.Conflict as e:
        return console(request, report_id, 409, decision_error=str(e))
    return RedirectResponse(f"/reports/{report_id}", status_code=303)


@router.get("/file", response_class=HTMLResponse)
def file_form(request: Request):
    return form_page(request, {}, {})


@router.post("/file", response_class=HTMLResponse)
async def file_submit(request: Request, background: BackgroundTasks):
    values = {k: str(v) for k, v in (await request.form()).items()}
    try:
        # An empty box means "not given", so it reads "is required" rather than "not a number".
        report = ReportIn.model_validate({k: v for k, v in values.items() if v.strip()})
    except ValidationError as e:
        return form_page(request, values, field_errors(e.errors()), 422)
    store = request.app.state.store
    report_id = reports.file_report(store, report)
    background.add_task(run_pipeline, store, request.app.state.llm, report_id)
    return RedirectResponse(f"/reports/{report_id}", status_code=303)


def form_page(request: Request, values: dict, errors: dict, status_code: int = 200):
    context = {
        "values": values,
        "errors": errors,
        "stations": STATIONS,
        "note_max": NOTE_MAX,
        "limits": {
            "wind_knots": f"LIMIT ≤ {WIND_MAX_KNOTS}",
            "temp_c": f"LIMIT ≥ {TEMP_MIN_C}",
            "fuel_pct": f"LIMIT {FUEL_MIN_PCT}–{FUEL_MAX_PCT}",
        },
    }
    return templates.TemplateResponse(request, "file.html", context, status_code=status_code)
