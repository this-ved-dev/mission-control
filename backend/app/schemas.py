from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.brief_by import Severity
from app.limits import LimitResult, Verdict, Violation

Status = Literal["received", "processing", "pending_approval", "needs_review", "approved", "error"]
Subsystem = Literal[
    "propulsion", "avionics", "communications", "weather", "ground_systems", "range_safety", "other"
]


class Readings(BaseModel):
    wind_knots: float = Field(ge=0, le=200, allow_inf_nan=False)
    temp_c: float = Field(ge=-80, le=80, allow_inf_nan=False)
    # Up to 150 so a slight over-read (100.1) is accepted and judged no_go by the limits.
    fuel_pct: float = Field(ge=0, le=150, allow_inf_nan=False)


class ReportIn(Readings):
    name: str = Field(max_length=80)
    station: str = Field(max_length=40)
    note: str = Field(max_length=5000)

    @field_validator("name", "station", "note")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v


class Filed(BaseModel):
    id: int


class Injection(BaseModel):
    flagged: bool
    reason: str = ""
    phrases: list[str] = []


class Missing(BaseModel):
    missing: list[str] = []
    complete: bool = True


class Panic(BaseModel):
    panic: bool
    reason: str = ""


class Checks(BaseModel):
    injection: Injection
    missing: Missing
    panic: Panic


class Round(BaseModel):
    round: int
    draft: str
    approved: bool
    feedback: str


class Step(BaseModel):
    seq: int
    step: str
    kind: Literal["code", "model"]
    model: str | None
    started_at: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: str
    status: Literal["ok", "fallback", "error"]
    output: dict[str, Any]


class ReportOut(ReportIn):
    id: int
    created_at: str
    status: Status
    verdict: Verdict | None = None
    violations: list[Violation] = []
    subsystem: Subsystem | None = None
    severity: Severity | None = None
    effective_severity: Severity | None = None
    classify_fallback: bool = False
    brief_by_minutes: int | None = None
    brief_by_deadline: str | None = None
    checks: Checks | None = None
    rounds: list[Round] = []
    briefing: str | None = None
    warnings: list[str] = []
    total_cost_usd: str = "0"
    approved_by: str | None = None
    approved_at: str | None = None
    steps: list[Step] = []


class Approval(BaseModel):
    approver: str = Field(max_length=80)
    acknowledged_flag: bool = False

    @field_validator("approver")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()


__all__ = ["LimitResult"]
