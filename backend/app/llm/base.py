"""The one door every model call goes through. Real hosts and the test fake both fit it."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMClient(Protocol):
    async def complete(
        self, *, step: str, system: str, prompt: str, schema: dict[str, Any] | None, model: str
    ) -> LLMResult: ...
