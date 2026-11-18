"""Use cases shared by the JSON API and the HTML console."""

import time
from dataclasses import asdict

from app.limits import check_limits
from app.schemas import ReportIn
from app.store import Store, now


def file_report(store: Store, report: ReportIn) -> int:
    started_at, t0 = now(), time.perf_counter()
    # The verdict is fixed here, from the readings alone, before any model sees the note.
    limits = check_limits(report.wind_knots, report.temp_c, report.fuel_pct)
    violations = [asdict(v) for v in limits.violations]
    report_id = store.create_report(
        {
            **report.model_dump(),
            "verdict": limits.verdict,
            "violations": violations,
            "status": "received",
        }
    )
    store.add_step(
        report_id,
        name="limits_check",
        kind="code",
        model=None,
        started_at=started_at,
        duration_ms=round((time.perf_counter() - t0) * 1000),
        input_tokens=0,
        output_tokens=0,
        status="ok",
        output={"verdict": limits.verdict, "violations": violations},
    )
    return report_id


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class NeedsAcknowledgement(Exception):
    pass


def approve(store: Store, report_id: int, approver: str, acknowledge_flags: bool) -> dict:
    """The only way a briefing becomes approved: a named person, through this function."""
    report = store.get_report(report_id)
    if report is None:
        raise NotFound(f"report {report_id} not found")
    if report["status"] == "needs_review" and not acknowledge_flags:
        raise NeedsAcknowledgement(
            "This note was flagged. Read it and acknowledge the flags before approving."
        )
    if not store.approve(report_id, approver):
        raise Conflict(f"report {report_id} is {report['status']}, not pending approval")
    store.add_step(
        report_id,
        name="approval",
        kind="human",
        model=None,
        started_at=now(),
        duration_ms=0,
        input_tokens=0,
        output_tokens=0,
        status="ok",
        output={"approver": approver},
    )
    return store.get_report(report_id)


def list_by_urgency(store: Store) -> list[dict]:
    """Reports needing a person first (soonest brief-by deadline on top), then in progress,
    then approved (most recent first)."""

    def key(r: dict) -> tuple:
        if r["status"] == "approved":
            return (2, "", -r["id"])
        if r["status"] in ("received", "processing"):
            return (1, "", r["id"])
        return (0, r["brief_by_at"] or "", r["id"])

    return sorted(store.list_reports(), key=key)
