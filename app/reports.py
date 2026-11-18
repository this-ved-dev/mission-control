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
