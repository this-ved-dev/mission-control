"""SQLite persistence. One short-lived connection per call keeps it thread- and task-safe."""

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.cost import report_cost

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL,
    station TEXT NOT NULL,
    wind_knots REAL NOT NULL,
    temp_c REAL NOT NULL,
    fuel_pct REAL NOT NULL,
    note TEXT NOT NULL,
    verdict TEXT NOT NULL,
    violations TEXT NOT NULL,
    status TEXT NOT NULL,
    subsystem TEXT,
    severity TEXT,
    model_severity TEXT,
    brief_by_minutes INTEGER,
    checks TEXT,
    briefing TEXT,
    briefing_rounds INTEGER,
    reviewer_approved INTEGER,
    review_feedback TEXT,
    warnings TEXT NOT NULL DEFAULT '[]',
    approved_by TEXT,
    approved_at TEXT
);
CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    seq INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    model TEXT,
    started_at TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd TEXT NOT NULL,
    status TEXT NOT NULL,
    output TEXT
);
"""

JSON_COLUMNS = ("violations", "checks", "warnings")


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def create_report(self, fields: dict[str, Any]) -> int:
        fields = {"created_at": now(), **_encode(fields)}
        cols = ", ".join(fields)
        marks = ", ".join("?" * len(fields))
        with closing(self._connect()) as db, db:
            sql = f"INSERT INTO reports ({cols}) VALUES ({marks})"
            return db.execute(sql, list(fields.values())).lastrowid

    def update_report(self, report_id: int, **fields: Any) -> None:
        fields = _encode(fields)
        sets = ", ".join(f"{k} = ?" for k in fields)
        with closing(self._connect()) as db, db:
            db.execute(f"UPDATE reports SET {sets} WHERE id = ?", [*fields.values(), report_id])

    def get_report(self, report_id: int) -> dict | None:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
            if row is None:
                return None
            steps = db.execute(
                "SELECT * FROM steps WHERE report_id = ? ORDER BY seq", (report_id,)
            ).fetchall()
        report = _decode(dict(row))
        report["steps"] = [_decode_step(dict(s)) for s in steps]
        report["cost_usd"] = str(report_cost(report["steps"]))
        report["input_tokens"] = sum(s["input_tokens"] for s in report["steps"])
        report["output_tokens"] = sum(s["output_tokens"] for s in report["steps"])
        report["brief_by_at"] = None
        if report["brief_by_minutes"] is not None:
            created = datetime.fromisoformat(report["created_at"])
            deadline = created + timedelta(minutes=report["brief_by_minutes"])
            report["brief_by_at"] = deadline.isoformat()
        return report

    def list_reports(self) -> list[dict]:
        with closing(self._connect()) as db:
            ids = [r[0] for r in db.execute("SELECT id FROM reports ORDER BY id")]
        return [self.get_report(i) for i in ids]

    def approve(self, report_id: int, approver: str) -> bool:
        """Atomically move a report awaiting a person to approved. False if it wasn't waiting."""
        with closing(self._connect()) as db, db:
            cur = db.execute(
                "UPDATE reports SET status = 'approved', approved_by = ?, approved_at = ? "
                "WHERE id = ? AND status IN ('pending_approval', 'needs_review')",
                (approver, now(), report_id),
            )
            return cur.rowcount == 1

    def interrupted(self) -> list[int]:
        """Reports a restart cut off mid-pipeline. Their model steps are cleared for a re-run."""
        with closing(self._connect()) as db, db:
            ids = [
                r[0]
                for r in db.execute(
                    "SELECT id FROM reports WHERE status IN ('received', 'processing')"
                )
            ]
            for report_id in ids:
                db.execute(
                    "DELETE FROM steps WHERE report_id = ? AND name != 'limits_check'",
                    (report_id,),
                )
        return ids

    def add_step(self, report_id: int, **step: Any) -> None:
        step["cost_usd"] = str(step.get("cost_usd", Decimal(0)))
        step["output"] = json.dumps(step.get("output"))
        with closing(self._connect()) as db, db:
            (seq,) = db.execute(
                "SELECT COUNT(*) FROM steps WHERE report_id = ?", (report_id,)
            ).fetchone()
            step = {"report_id": report_id, "seq": seq + 1, **step}
            cols = ", ".join(step)
            marks = ", ".join("?" * len(step))
            db.execute(f"INSERT INTO steps ({cols}) VALUES ({marks})", list(step.values()))


def _encode(fields: dict) -> dict:
    return {k: json.dumps(v) if k in JSON_COLUMNS else v for k, v in fields.items()}


def _decode(row: dict) -> dict:
    for k in JSON_COLUMNS:
        if row.get(k) is not None:
            row[k] = json.loads(row[k])
    return row


def _decode_step(row: dict) -> dict:
    row["output"] = json.loads(row["output"]) if row["output"] else None
    return row
