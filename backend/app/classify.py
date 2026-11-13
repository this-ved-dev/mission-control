from pydantic import BaseModel

from app.brief_by import Severity
from app.llm.base import LLMClient
from app.prompts import CLASSIFY, fenced
from app.schemas import Subsystem
from app.trace import Tracer


class Classification(BaseModel):
    subsystem: Subsystem
    severity: Severity
    rationale: str = ""


# Unknown is treated as dangerous: high severity means a 5-minute brief-by.
FALLBACK = Classification(subsystem="other", severity="high", rationale="fallback")

SCHEMA = {
    "type": "object",
    "properties": {
        "subsystem": {"type": "string", "enum": list(Subsystem.__args__)},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "rationale": {"type": "string"},
    },
    "required": ["subsystem", "severity", "rationale"],
    "additionalProperties": False,
}


async def classify(
    llm: LLMClient, tracer: Tracer, model: str, note: str, station: str
) -> tuple[Classification, bool]:
    with tracer.step("classify") as s:
        try:
            result = await llm.complete(
                step="classify",
                system=CLASSIFY,
                prompt=f"Station: {station}\n{fenced(note)}",
                schema=SCHEMA,
                model=model,
            )
            s.use(result)
            parsed = Classification.model_validate_json(result.text)
            s["output"] = parsed.model_dump()
            return parsed, False
        except Exception as e:  # bad JSON, wrong enum, host down: all fall back
            s.update(status="fallback", output={**FALLBACK.model_dump(), "error": str(e)[:300]})
            return FALLBACK, True
