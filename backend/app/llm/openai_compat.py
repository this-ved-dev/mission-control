"""Any OpenAI-compatible Chat Completions host: Ollama, LM Studio, vLLM, OpenAI, OpenRouter."""

import json
import re
from typing import Any

import httpx
from openai import APIError, AsyncOpenAI

from app.llm.base import LLMResult

THINK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def json_block(text: str) -> str:
    """The JSON object inside a free-text reply (fenced or not)."""
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if 0 <= start < end else text


class OpenAICompatClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        http_client: httpx.AsyncClient | None = None,
        reasoning_effort: str = "",
    ):
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, http_client=http_client, timeout=180, max_retries=1
        )
        # "none" turns off long hidden reasoning on local models; empty sends nothing.
        self._extra = {"reasoning_effort": reasoning_effort} if reasoning_effort else {}

    async def _create(self, model: str, system: str, prompt: str, **extra: Any):
        return await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.2,
            **self._extra,
            **extra,
        )

    async def complete(
        self, *, step: str, system: str, prompt: str, schema: dict[str, Any] | None, model: str
    ) -> LLMResult:
        prose = schema is None
        if prose:
            resp = await self._create(model, system, prompt)
        else:
            fmt = {
                "type": "json_schema",
                "json_schema": {"name": step, "schema": schema, "strict": True},
            }
            try:
                resp = await self._create(model, system, prompt, response_format=fmt)
            except APIError:
                # Some hosts (e.g. MLX builds in Ollama) refuse structured output: ask in words.
                system += (
                    f"\nReply with only a JSON object matching this schema: {json.dumps(schema)}"
                )
                resp = await self._create(model, system, prompt)
        # Reasoning models may inline their thinking; only the answer is the reply.
        text = THINK.sub("", resp.choices[0].message.content or "").strip()
        usage = resp.usage
        return LLMResult(
            text=text if prose else json_block(text),
            model=model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
