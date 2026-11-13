"""Any OpenAI-compatible Chat Completions host: Ollama, LM Studio, vLLM, OpenAI, OpenRouter."""

import re
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.llm.base import LLMResult

THINK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


class OpenAICompatClient:
    def __init__(self, base_url: str, api_key: str, http_client: httpx.AsyncClient | None = None):
        self._client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, http_client=http_client, timeout=180, max_retries=1
        )

    async def complete(
        self, *, step: str, system: str, prompt: str, schema: dict[str, Any] | None, model: str
    ) -> LLMResult:
        extra: dict[str, Any] = {}
        if schema is not None:
            extra["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": step, "schema": schema, "strict": True},
            }
        resp = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.2,
            **extra,
        )
        # Reasoning models may inline their thinking; only the answer is the reply.
        text = THINK.sub("", resp.choices[0].message.content or "").strip()
        usage = resp.usage
        return LLMResult(
            text=text,
            model=model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
