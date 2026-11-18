"""The one door every model call goes through.

The pipeline only knows `LLMClient`. Adapters: Claude on Azure AI Foundry for real runs, and a
scripted fake for tests and offline demos. Another provider is one more adapter class.
"""

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from anthropic import APIError, AsyncAnthropicFoundry

from app.config import Settings


@dataclass(frozen=True)
class LLMResult:
    data: Any  # parsed JSON when a schema was requested (or the raw text if it didn't parse)
    model: str
    input_tokens: int
    output_tokens: int


class LLMError(Exception):
    """The model call failed: network/API error, refusal, or truncated output."""


class LLMClient(Protocol):
    async def complete(
        self,
        *,
        step: str,
        system: str,
        user: str,
        schema: dict | None = None,
        effort: str = "low",
        max_tokens: int = 4096,
    ) -> LLMResult: ...


class FoundryClaudeClient:
    def __init__(
        self, *, api_key: str, resource: str, model: str, http_client=None, max_retries: int = 2
    ):
        self.model = model
        self._client = AsyncAnthropicFoundry(
            api_key=api_key,
            resource=resource,
            timeout=60,
            max_retries=max_retries,
            http_client=http_client,
        )

    async def complete(
        self,
        *,
        step: str,
        system: str,
        user: str,
        schema: dict | None = None,
        effort: str = "low",
        max_tokens: int = 4096,
    ) -> LLMResult:
        output_config: dict[str, Any] = {"effort": effort}
        if schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        try:
            msg = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config=output_config,
            )
        except APIError as e:
            raise LLMError(f"{step}: {e}") from e
        if msg.stop_reason in ("refusal", "max_tokens"):
            raise LLMError(f"{step}: stopped with {msg.stop_reason}")
        text = "".join(b.text for b in msg.content if b.type == "text")
        return LLMResult(
            data=_parse(text) if schema is not None else text,
            model=msg.model,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
        )


def _parse(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


class FakeClient:
    """Scripted stand-in. Each step pops its next scripted reply (an Exception is raised);
    when a step has no script left it falls back to a simple keyword-based demo reply."""

    model = "fake"

    def __init__(self, script: dict[str, list] | None = None, delay: float = 0.0):
        self.script = {step: list(replies) for step, replies in (script or {}).items()}
        self.delay = delay
        self.calls: list[dict] = []
        self.in_flight = 0
        self.peak_in_flight = 0

    async def complete(
        self,
        *,
        step: str,
        system: str,
        user: str,
        schema: dict | None = None,
        effort: str = "low",
        max_tokens: int = 4096,
    ) -> LLMResult:
        self.calls.append({"step": step, "system": system, "user": user, "effort": effort})
        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            queue = self.script.get(step)
            reply = queue.pop(0) if queue else demo_reply(step, user)
        finally:
            self.in_flight -= 1
        if isinstance(reply, Exception):
            raise LLMError(f"{step}: {reply}") from reply
        # Rough token estimate (~4 chars per token) so the demo trace and cost look realistic.
        out = reply if isinstance(reply, str) else json.dumps(reply)
        return LLMResult(reply, self.model, (len(system) + len(user)) // 4 + 1, len(out) // 4 + 1)


def make_llm(settings: Settings) -> LLMClient:
    if settings.llm == "fake":
        return FakeClient()
    if settings.llm == "foundry":
        if not (settings.foundry_api_key and settings.foundry_resource):
            raise RuntimeError(
                "ANTHROPIC_FOUNDRY_API_KEY and ANTHROPIC_FOUNDRY_RESOURCE must be set "
                "(see .env.example), or set MC_LLM=fake for the offline demo"
            )
        return FoundryClaudeClient(
            api_key=settings.foundry_api_key,
            resource=settings.foundry_resource,
            model=settings.model,
        )
    raise ValueError(f"unknown MC_LLM {settings.llm!r}: use 'foundry' or 'fake'")


# --- offline demo replies -------------------------------------------------------------------
# Used only by FakeClient when unscripted (MC_LLM=fake). They read the <note> and <facts> blocks
# the pipeline puts in every prompt.

INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above) instructions|you are now|set (the )?verdict|"
    r"\bsystem\s*:|disregard",
    re.IGNORECASE,
)
SUBSYSTEM_WORDS = {
    "propulsion": r"valve|fuel|lox|engine|tank|propellant|pressur|thrust",
    "communications": r"telemetry|link|radio|comm|antenna|signal",
    "weather": r"wind|weather|lightning|cloud|rain|temperature",
    "ground_systems": r"pad|camera|umbilical|power|ground|tower|crane",
    "avionics": r"guidance|sensor|computer|imu|avionics|software|gps",
    "range_safety": r"range|airspace|boat|ship|aircraft|flight termination",
}


def demo_reply(step: str, user: str) -> Any:
    note = _between(user, "note")
    facts = json.loads(_between(user, "facts") or "{}")
    if step == "classify":
        subsystem = next(
            (s for s, words in SUBSYSTEM_WORDS.items() if re.search(words, note, re.I)), "other"
        )
        if re.search(r"leak|fire|fail|abort|critical|crack|explo", note, re.I):
            severity = "high"
        elif re.search(r"drop|slow|longer|odd|intermittent|spike|late|froze", note, re.I):
            severity = "medium"
        else:
            severity = "low"
        return {"subsystem": subsystem, "severity": severity, "reason": "Keyword match (demo)."}
    if step == "check_injection":
        hit = INJECTION.search(note)
        reason = f"Contains {hit.group(0)!r}." if hit else "No instructions to the system."
        return {"flagged": bool(hit), "reason": reason}
    if step == "check_missing":
        missing = [] if re.search(r"\d", note) else ["observed value or measurement"]
        if not re.search(r"\b(at|since|after|during|on the|last|\d{1,2}:\d{2}|T-)", note, re.I):
            missing.append("when it happened")
        return {"missing": missing}
    if step == "check_panic":
        letters = [c for c in note if c.isalpha()]
        shouting = letters and sum(c.isupper() for c in letters) / len(letters) > 0.4
        panic = bool(shouting or "!!" in note or re.search(r"\burgent|disaster|panic", note, re.I))
        return {"panic": panic, "reason": "Capitals or alarm words." if panic else "Calm tone."}
    if step == "draft":
        verdict = "NO-GO" if facts.get("verdict") == "no_go" else "GO"
        reasons = "; ".join(v["message"] for v in facts.get("violations", []))
        first = re.split(r"(?<=[.!?])\s", INJECTION.split(note)[0].strip())[0][:160]
        lead = f"{verdict}: {reasons}." if reasons else f"{verdict}: all readings within limits."
        return f"{lead} {facts.get('station', '')} reports: {first}".strip()
    if step == "review":
        return {"approved": True, "feedback": "Accurate and concise."}
    return {}


def _between(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>\n?(.*?)\n?</{tag}>", text, re.S)
    return match.group(1) if match else ""
