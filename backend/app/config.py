"""Settings from the environment. Swapping model hosts is a .env change, not a code change."""

import os
from dataclasses import dataclass
from decimal import Decimal

from app.cost import Price
from app.llm.base import LLMClient


@dataclass(frozen=True)
class Settings:
    provider: str = "openai_compat"
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"
    model: str = "gemma4:12b"
    model_fast: str = ""
    model_writer: str = ""
    reasoning_effort: str = ""
    price_input_per_m: Decimal = Decimal(0)
    price_output_per_m: Decimal = Decimal(0)

    @property
    def fast(self) -> str:
        return self.model_fast or self.model

    @property
    def writer(self) -> str:
        return self.model_writer or self.model

    def prices(self) -> dict[str, Price]:
        price = Price(self.price_input_per_m, self.price_output_per_m)
        return {m: price for m in (self.model, self.fast, self.writer)}

    def client(self) -> LLMClient:
        if self.provider == "fake":
            from app.llm.fake import FakeClient

            return FakeClient()
        from app.llm.openai_compat import OpenAICompatClient

        return OpenAICompatClient(
            self.base_url, self.api_key, reasoning_effort=self.reasoning_effort
        )

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ.get
        return cls(
            provider=env("LLM_PROVIDER", cls.provider),
            base_url=env("LLM_BASE_URL", cls.base_url),
            api_key=env("LLM_API_KEY", cls.api_key),
            model=env("LLM_MODEL", cls.model),
            model_fast=env("LLM_MODEL_FAST", ""),
            model_writer=env("LLM_MODEL_WRITER", ""),
            reasoning_effort=env("LLM_REASONING_EFFORT", ""),
            price_input_per_m=Decimal(env("LLM_PRICE_INPUT_PER_M", "0")),
            price_output_per_m=Decimal(env("LLM_PRICE_OUTPUT_PER_M", "0")),
        )
