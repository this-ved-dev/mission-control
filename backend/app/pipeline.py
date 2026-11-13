"""Orchestrates one report. Limits run first, before any model sees the note."""

from datetime import datetime, timedelta

from app.brief_by import brief_by_minutes, effective_severity
from app.briefing import draft_and_review, verdict_warning
from app.checks import run_checks
from app.classify import classify
from app.config import Settings
from app.db import DB
from app.limits import check_limits
from app.llm.base import LLMClient
from app.prompts import fenced
from app.trace import Tracer


async def run_pipeline(db: DB, llm: LLMClient, settings: Settings, report_id: int) -> None:
    report = db.get(report_id)
    db.update_report(report_id, status="processing")
    tracer = Tracer(settings.prices(), sink=lambda step: db.add_step(report_id, step))
    try:
        with tracer.step("limits_check", kind="code") as s:
            limits = check_limits(report["wind_knots"], report["temp_c"], report["fuel_pct"])
            s["output"] = limits.model_dump()
        violations = [v.model_dump() for v in limits.violations]
        db.update_report(report_id, verdict=limits.verdict, result={"violations": violations})

        cls, fell_back = await classify(
            llm, tracer, settings.fast, report["note"], report["station"]
        )

        with tracer.step("brief_by", kind="code") as s:
            effective = effective_severity(cls.severity, bool(violations))
            minutes = brief_by_minutes(cls.severity, bool(violations))
            deadline = datetime.fromisoformat(report["created_at"]) + timedelta(minutes=minutes)
            s["output"] = {
                "model_severity": cls.severity,
                "effective_severity": effective,
                "brief_by_minutes": minutes,
            }
        db.update_report(
            report_id,
            brief_by_deadline=deadline.isoformat(timespec="milliseconds"),
            result={
                "subsystem": cls.subsystem,
                "severity": cls.severity,
                "effective_severity": effective,
                "classify_fallback": fell_back,
                "brief_by_minutes": minutes,
            },
        )

        checks, failed = await run_checks(llm, tracer, settings.fast, report["note"])
        db.update_report(report_id, result={"checks": checks.model_dump()})

        facts = {
            "station": report["station"],
            "engineer": report["name"],
            "readings": {k: report[k] for k in ("wind_knots", "temp_c", "fuel_pct")},
            "verdict": limits.verdict,
            "violations": [v["message"] for v in violations],
            "subsystem": cls.subsystem,
            "severity": effective,
            "brief_by_minutes": minutes,
            "missing_details": checks.missing.missing,
            "panicked_tone": checks.panic.panic,
            "note_flagged_as_instructions": checks.injection.flagged,
            "note_untrusted": fenced(report["note"]),
        }
        rounds = await draft_and_review(llm, tracer, settings.writer, settings.writer, facts)
        briefing = rounds[-1].draft

        warnings = []
        if checks.injection.flagged:
            warnings.append(
                "Note contains instruction-like text. Verdict computed from readings only."
            )
        warnings += [f"{name} could not run; treated cautiously." for name in failed]
        if not rounds[-1].approved:
            warnings.append(f"Reviewer not satisfied after {len(rounds)} rounds.")
        if mismatch := verdict_warning(briefing, limits.verdict):
            warnings.append(mismatch)

        with tracer.step("cost_total", kind="code") as s:
            total = tracer.total()
            s["output"] = {
                "total_usd": str(total),
                "model_steps": sum(1 for x in tracer.steps if x["kind"] == "model"),
            }
        # The pipeline only ever hands over to a person; it never sets "approved".
        status = "needs_review" if checks.injection.flagged or failed else "pending_approval"
        db.update_report(
            report_id,
            status=status,
            result={
                "rounds": [r.model_dump() for r in rounds],
                "briefing": briefing,
                "warnings": warnings,
                "total_cost_usd": str(total),
            },
        )
    except Exception as e:
        db.update_report(
            report_id,
            status="error",
            result={
                "warnings": [f"Pipeline stopped: {type(e).__name__}: {e}"[:300]],
                "total_cost_usd": str(tracer.total()),
            },
        )
