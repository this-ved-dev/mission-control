"""Draft with one model call, review with another, feed the review back in. At most 3 rounds."""

import json
import re
from typing import Any

from pydantic import BaseModel

from app.llm.base import LLMClient
from app.prompts import DRAFT, REVIEW
from app.schemas import Round
from app.trace import Tracer

MAX_ROUNDS = 3


class Review(BaseModel):
    approved: bool
    feedback: str


REVIEW_SCHEMA = {
    "type": "object",
    "properties": {"approved": {"type": "boolean"}, "feedback": {"type": "string"}},
    "required": ["approved", "feedback"],
    "additionalProperties": False,
}


async def draft_and_review(
    llm: LLMClient, tracer: Tracer, writer: str, reviewer: str, facts: dict[str, Any]
) -> list[Round]:
    facts_json = json.dumps(facts, indent=2)
    rounds: list[Round] = []
    for n in range(1, MAX_ROUNDS + 1):
        prompt = f"Facts (computed by code, authoritative):\n{facts_json}"
        if rounds:
            last = rounds[-1]
            prompt += (
                f"\n\nYour previous draft:\n{last.draft}\n\n"
                f"Reviewer feedback to fix in this draft:\n{last.feedback}"
            )
        with tracer.step(f"draft_{n}") as s:
            result = await llm.complete(
                step="draft", system=DRAFT, prompt=prompt, schema=None, model=writer
            )
            s.use(result)
            draft = result.text
            s["output"] = {"draft": draft}

        with tracer.step(f"review_{n}") as s:
            try:
                result = await llm.complete(
                    step="review",
                    system=REVIEW,
                    prompt=f"Facts:\n{facts_json}\n\nBriefing to review:\n{draft}",
                    schema=REVIEW_SCHEMA,
                    model=reviewer,
                )
                s.use(result)
                review = Review.model_validate_json(result.text)
            except Exception as e:
                s["status"] = "fallback"
                review = Review(
                    approved=False,
                    feedback=f"Review failed ({str(e)[:120]}); "
                    "restate the verdict and every violation exactly.",
                )
            s["output"] = review.model_dump()

        rounds.append(Round(round=n, draft=draft, **review.model_dump()))
        if review.approved:
            break
    return rounds


NO_GO = re.compile(r"\bno[\s-]?go\b", re.IGNORECASE)
GO = re.compile(r"\bgo\b", re.IGNORECASE)


def verdict_warning(briefing: str, verdict: str) -> str | None:
    """Code gets the last word: the briefing must state the verdict the limits produced."""
    says_no_go = bool(NO_GO.search(briefing))
    says_go = bool(GO.search(NO_GO.sub("", briefing)))
    if verdict == "no_go" and not says_no_go:
        return "Briefing does not state NO-GO, but the launch limits say NO-GO."
    if verdict == "go" and (says_no_go or not says_go):
        return "Briefing does not state GO cleanly, but the launch limits say GO."
    return None
