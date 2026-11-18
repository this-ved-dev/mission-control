"""Opt-in smoke test against the real Foundry deployment: uv run pytest -m live --no-cov"""

import pytest

from app.config import Settings
from app.llm import make_llm

pytestmark = [pytest.mark.live, pytest.mark.enable_socket]


async def test_sonnet_on_foundry_answers_in_schema():
    settings = Settings.from_env()
    if not (settings.foundry_api_key and settings.foundry_resource):
        pytest.skip("ANTHROPIC_FOUNDRY_API_KEY / ANTHROPIC_FOUNDRY_RESOURCE not set")
    llm = make_llm(Settings(**{**settings.__dict__, "llm": "foundry"}))
    schema = {
        "type": "object",
        "properties": {"severity": {"type": "string", "enum": ["low", "medium", "high"]}},
        "required": ["severity"],
        "additionalProperties": False,
    }
    result = await llm.complete(
        step="classify",
        system="Rate the severity of this launch anomaly.",
        user="<note>Main engine fuel line is leaking.</note>",
        schema=schema,
        effort="low",
    )
    assert result.data["severity"] in {"low", "medium", "high"}
    assert result.input_tokens > 0 and result.output_tokens > 0
