"""SQLite on disk. One short-lived connection per call keeps threads and the event loop safe."""

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL, station TEXT NOT NULL,
    wind_knots REAL NOT NULL, temp_c REAL NOT NULL, fuel_pct REAL NOT NULL,
    note TEXT NOT NULL,
    status TEXT NOT NULL,
    verdict TEXT,
    brief_by_deadline TEXT,
    approved_by TEXT, approved_at TEXT,
    result TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    data TEXT NOT NULL
);
"""

FIELDS = ("name", "station", "wind_knots", "temp_c", "fuel_pct", "note")


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class DB:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _run(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        """For writes: lastrowid and rowcount stay readable after the connection closes."""
        with closing(self._conn()) as c, c:
            return c.execute(sql, args)

    def _fetch(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with closing(self._conn()) as c:
            return c.execute(sql, args).fetchall()

    def insert_report(self, data: dict[str, Any]) -> int:
        cols = ", ".join(FIELDS)
        marks = ", ".join("?" for _ in FIELDS)
        cur = self._run(
            f"INSERT INTO reports (created_at, status, {cols}) VALUES (?, 'received', {marks})",
            (now(), *(data[f] for f in FIELDS)),
        )
        return cur.lastrowid

    def update_report(self, report_id: int, **cols: Any) -> None:
        """Set top-level columns; a `result` dict is merged into the stored JSON."""
        result = cols.pop("result", None)
        if result is not None:
            merged = {**self.get_result(report_id), **result}
            cols["result"] = json.dumps(merged)
        sets = ", ".join(f"{k} = ?" for k in cols)
        self._run(f"UPDATE reports SET {sets} WHERE id = ?", (*cols.values(), report_id))

    def approve(self, report_id: int, approver: str) -> bool:
        """Atomic: only a report waiting on a human can move to approved."""
        cur = self._run(
            "UPDATE reports SET status = 'approved', approved_by = ?, approved_at = ? "
            "WHERE id = ? AND status IN ('pending_approval', 'needs_review')",
            (approver, now(), report_id),
        )
        return cur.rowcount == 1

    def get_result(self, report_id: int) -> dict[str, Any]:
        rows = self._fetch("SELECT result FROM reports WHERE id = ?", (report_id,))
        return json.loads(rows[0]["result"]) if rows else {}

    def add_step(self, report_id: int, step: dict[str, Any]) -> None:
        self._run(
            "INSERT INTO steps (report_id, data) VALUES (?, ?)", (report_id, json.dumps(step))
        )

    def steps(self, report_id: int) -> list[dict[str, Any]]:
        rows = self._fetch("SELECT data FROM steps WHERE report_id = ? ORDER BY id", (report_id,))
        return [json.loads(r["data"]) for r in rows]

    def get(self, report_id: int) -> dict[str, Any] | None:
        rows = self._fetch("SELECT * FROM reports WHERE id = ?", (report_id,))
        return self._full(rows[0]) if rows else None

    def list(self) -> list[dict[str, Any]]:
        rows = self._fetch(
            "SELECT * FROM reports ORDER BY status = 'approved', "
            "brief_by_deadline IS NULL, brief_by_deadline, id DESC"
        )
        return [self._full(r) for r in rows]

    def _full(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data.update(json.loads(data.pop("result")))
        data["steps"] = self.steps(data["id"])
        return data
