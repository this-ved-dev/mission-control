"""Scripted stand-in for a model host: no network, no key, same interface."""

import asyncio
import json
import re
from typing import Any

from app.llm.base import LLMResult

Reply = str | dict[str, Any] | Exception


class FakeClient:
    def __init__(self, replies: dict[str, list[Reply]] | None = None, delay: float = 0.0):
        self.replies = {k: list(v) for k, v in (replies or {}).items()}
        self.delay = delay
        self.calls: list[dict[str, Any]] = []
        self.in_flight = 0
        self.max_in_flight = 0

    async def complete(
        self, *, step: str, system: str, prompt: str, schema: dict[str, Any] | None, model: str
    ) -> LLMResult:
        self.calls.append({"step": step, "system": system, "prompt": prompt, "model": model})
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            queue = self.replies.get(step)
            reply = queue.pop(0) if queue else demo_reply(step, prompt)
        finally:
            self.in_flight -= 1
        if isinstance(reply, Exception):
            raise reply
        text = reply if isinstance(reply, str) else json.dumps(reply)
        return LLMResult(text, model, len(prompt) // 4 + 20, len(text) // 4 + 1)


def demo_reply(step: str, prompt: str) -> Reply:
    """Plausible offline answers so the app runs end to end without a model (LLM_PROVIDER=fake)."""
    note = prompt.split("<note>")[-1].split("</note>")[0].lower() if "<note>" in prompt else ""
    if step == "classify":
        table = [
            ("propulsion", r"valve|lox|engine|tank|fuel|pressure"),
            ("communications", r"telemetry|link|radio|s-band|comms"),
            ("weather", r"wind|lightning|cloud|weather"),
            ("ground_systems", r"pad|camera|umbilical|tower|power"),
            ("avionics", r"computer|sensor|imu|avionics"),
        ]
        sub = next((s for s, pat in table if re.search(pat, note)), "other")
        sev = "high" if re.search(r"urgent|fail|leak|!!", note) else "medium"
        return {"subsystem": sub, "severity": sev, "rationale": "keyword demo"}
    if step == "injection":
        hit = bool(re.search(r"ignore|you are now|set the verdict|system:", note))
        return {"flagged": hit, "reason": "note addresses the system" if hit else ""}
    if step == "missing":
        gaps = [] if re.search(r"\d", note) else ["time or measured value"]
        return {"missing": gaps, "complete": not gaps}
    if step == "panic":
        hit = bool(re.search(r"!!|urgent|asap", note)) or note.isupper()
        return {"panic": hit, "reason": "alarmed tone" if hit else ""}
    if step == "review":
        return {"approved": True, "feedback": ""}
    verdict = "NO-GO" if '"verdict": "no_go"' in prompt else "GO"
    return f"{verdict}: demo briefing drafted offline from the report facts."
