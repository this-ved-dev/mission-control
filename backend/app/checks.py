"""Three independent model checks on the note, run at the same time."""

import asyncio
import re

from pydantic import BaseModel

from app.llm.base import LLMClient
from app.prompts import INJECTION, MISSING, PANIC, fenced
from app.schemas import Checks, Injection, Missing, Panic
from app.trace import Tracer

# Cheap code backstop: a model can miss an injection, these phrases cannot.
SUSPICIOUS = re.compile(
    r"ignore (all |any )?(previous|prior|above|earlier) instructions?"
    r"|disregard (the |all )?(rules|limits|instructions)"
    r"|you are now [^.]*"
    r"|\bsystem\s*:"
    r"|set (the )?verdict to \w+"
    r"|(mark|set) (the )?severity (to )?\w+"
    r"|override (mode|the limits?)"
    r"|ignore (the )?limits",
    re.IGNORECASE,
)


def keyword_flags(note: str) -> list[str]:
    return [m.group(0) for m in SUSPICIOUS.finditer(note)]


def _schema(props: dict, required: list[str]) -> dict:
    return {
        "type": "object",
        "properties": props,
        "required": required,
        "additionalProperties": False,
    }


SPECS: dict[str, tuple[str, type[BaseModel], dict]] = {
    "injection": (
        INJECTION,
        Injection,
        _schema(
            {"flagged": {"type": "boolean"}, "reason": {"type": "string"}}, ["flagged", "reason"]
        ),
    ),
    "missing": (
        MISSING,
        Missing,
        _schema(
            {
                "missing": {"type": "array", "items": {"type": "string"}},
                "complete": {"type": "boolean"},
            },
            ["missing", "complete"],
        ),
    ),
    "panic": (
        PANIC,
        Panic,
        _schema({"panic": {"type": "boolean"}, "reason": {"type": "string"}}, ["panic", "reason"]),
    ),
}

# What a check means when it could not run: the cautious reading.
FAILED = {
    "injection": Injection(flagged=True, reason="check failed; treat as suspicious"),
    "missing": Missing(missing=["completeness check failed"], complete=False),
    "panic": Panic(panic=False, reason="check failed"),
}


async def _check(llm: LLMClient, tracer: Tracer, model: str, kind: str, note: str):
    system, out_type, schema = SPECS[kind]
    with tracer.step(f"check_{kind}") as s:
        try:
            result = await llm.complete(
                step=kind, system=system, prompt=fenced(note), schema=schema, model=model
            )
            s.use(result)
            parsed = out_type.model_validate_json(result.text)
            s["output"] = parsed.model_dump()
            return parsed, False
        except Exception as e:
            s.update(status="fallback", output={**FAILED[kind].model_dump(), "error": str(e)[:300]})
            return FAILED[kind], True


async def run_checks(
    llm: LLMClient, tracer: Tracer, model: str, note: str
) -> tuple[Checks, list[str]]:
    kinds = ("injection", "missing", "panic")
    results = await asyncio.gather(*(_check(llm, tracer, model, k, note) for k in kinds))
    (injection, _), (missing, _), (panic, _) = results
    phrases = keyword_flags(note)
    if phrases:
        reason = injection.reason or "instruction-like phrases found in the note"
        injection = Injection(flagged=True, reason=reason, phrases=phrases)
    failed = [f"check_{k}" for k, (_, bad) in zip(kinds, results, strict=True) if bad]
    return Checks(injection=injection, missing=missing, panic=panic), failed
