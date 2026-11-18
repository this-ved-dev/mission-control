"""Request/response shapes and the plain-English validation messages shared by API and form."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

STATIONS = ("PROP", "GNC", "COMMS", "WX", "GND", "RANGE")
Station = Literal["PROP", "GNC", "COMMS", "WX", "GND", "RANGE"]

# Plausibility ranges only. A reading past a launch limit is valid input; it just means no_go.
RANGES = {"wind_knots": (0, 200), "temp_c": (-60, 60), "fuel_pct": (0, 150)}
NOTE_MAX = 5000


class ReportIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=80)
    station: Station
    wind_knots: float = Field(ge=0, le=200, allow_inf_nan=False)
    temp_c: float = Field(ge=-60, le=60, allow_inf_nan=False)
    fuel_pct: float = Field(ge=0, le=150, allow_inf_nan=False)
    note: str = Field(min_length=1, max_length=NOTE_MAX)


class ViolationOut(BaseModel):
    reading: str
    value: float
    message: str


class StepOut(BaseModel):
    seq: int
    name: str
    kind: Literal["code", "model"]
    model: str | None
    started_at: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: str
    status: Literal["ok", "fallback", "error"]
    output: dict | list | str | None


class ReportOut(BaseModel):
    id: int
    created_at: str
    name: str
    station: Station
    wind_knots: float
    temp_c: float
    fuel_pct: float
    note: str
    verdict: Literal["go", "no_go"]
    violations: list[ViolationOut]
    status: str
    steps: list[StepOut]


class ValidationErrorOut(BaseModel):
    message: str
    errors: dict[str, str]


def field_errors(errors: list[dict]) -> dict[str, str]:
    """Turn pydantic error dicts into one clear message per field."""
    out: dict[str, str] = {}
    for e in errors:
        loc = [p for p in e["loc"] if p != "body"]
        field = str(loc[0]) if loc else "body"
        out.setdefault(field, _message(field, e))
    return out


def _message(field: str, e: dict) -> str:
    kind = e["type"]
    if kind == "missing":
        return f"{field} is required"
    if kind == "string_too_short":
        return f"{field} must not be empty"
    if kind == "string_too_long":
        return f"{field} must be {e['ctx']['max_length']} characters or fewer"
    if kind in ("float_parsing", "float_type"):
        return f"{field} must be a number"
    if kind == "finite_number":
        return f"{field} must be a finite number"
    if kind in ("greater_than_equal", "less_than_equal") and field in RANGES:
        low, high = RANGES[field]
        return f"{field} must be between {low} and {high}"
    if kind == "literal_error":
        return f"{field} must be one of {', '.join(STATIONS)}"
    return e["msg"]
