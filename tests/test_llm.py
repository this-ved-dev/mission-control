import asyncio
import json

import httpx2
import pytest

from app.config import Settings
from app.llm import FakeClient, FoundryClaudeClient, LLMError, make_llm

SCHEMA = {
    "type": "object",
    "properties": {"severity": {"type": "string", "enum": ["low", "high"]}},
    "required": ["severity"],
    "additionalProperties": False,
}


def message(text, stop_reason="end_turn", input_tokens=120, output_tokens=7):
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5-5",
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def foundry(handler):
    http = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    return FoundryClaudeClient(
        api_key="test-key",
        resource="meridian",
        model="claude-sonnet-5-5",
        http_client=http,
        max_retries=0,
    )


async def test_foundry_sends_schema_effort_and_note_to_the_messages_api():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json=message('{"severity": "high"}'))

    result = await foundry(handler).complete(
        step="classify", system="sys", user="<note>x</note>", schema=SCHEMA, effort="low"
    )

    assert seen["url"] == "https://meridian.services.ai.azure.com/anthropic/v1/messages"
    body = seen["body"]
    assert body["model"] == "claude-sonnet-5-5"
    assert body["system"] == "sys"
    assert body["messages"] == [{"role": "user", "content": "<note>x</note>"}]
    assert body["output_config"] == {
        "effort": "low",
        "format": {"type": "json_schema", "schema": SCHEMA},
    }
    assert result.data == {"severity": "high"}
    assert (result.model, result.input_tokens, result.output_tokens) == ("claude-sonnet-5-5", 120, 7)


async def test_foundry_without_schema_returns_text():
    client = foundry(lambda r: httpx2.Response(200, json=message("NO-GO: wind.")))
    result = await client.complete(step="draft", system="s", user="u", effort="medium")
    assert result.data == "NO-GO: wind."
    assert "format" not in json.loads(client.last_request_body)["output_config"]


async def test_foundry_returns_unparseable_json_as_text_for_the_caller_to_reject():
    client = foundry(lambda r: httpx2.Response(200, json=message("not json")))
    result = await client.complete(step="classify", system="s", user="u", schema=SCHEMA)
    assert result.data == "not json"


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
async def test_foundry_refusal_or_truncation_is_an_llm_error(stop_reason):
    client = foundry(lambda r: httpx2.Response(200, json=message("", stop_reason=stop_reason)))
    with pytest.raises(LLMError, match=stop_reason):
        await client.complete(step="classify", system="s", user="u", schema=SCHEMA)


async def test_foundry_http_error_is_an_llm_error():
    client = foundry(lambda r: httpx2.Response(500, json={"error": {"message": "boom"}}))
    with pytest.raises(LLMError, match="classify"):
        await client.complete(step="classify", system="s", user="u", schema=SCHEMA)


async def test_fake_plays_its_script_and_records_calls():
    fake = FakeClient({"classify": [{"severity": "low"}, ValueError("x")]})
    first = await fake.complete(step="classify", system="s", user="u", schema=SCHEMA)
    assert first.data == {"severity": "low"}
    assert first.model == "fake"
    assert first.input_tokens > 0 and first.output_tokens > 0
    with pytest.raises(LLMError):
        await fake.complete(step="classify", system="s", user="u2")
    assert [c["user"] for c in fake.calls] == ["u", "u2"]


async def test_fake_counts_concurrent_calls():
    fake = FakeClient({"a": [{}], "b": [{}], "c": [{}]}, delay=0.05)
    await asyncio.gather(*(fake.complete(step=s, system="", user="") for s in "abc"))
    assert fake.peak_in_flight == 3


def test_make_llm_fake():
    assert isinstance(make_llm(Settings(llm="fake")), FakeClient)


def test_make_llm_foundry_needs_credentials():
    with pytest.raises(RuntimeError, match="ANTHROPIC_FOUNDRY_API_KEY"):
        make_llm(Settings(llm="foundry"))


def test_make_llm_foundry_with_credentials():
    client = make_llm(Settings(llm="foundry", foundry_api_key="k", foundry_resource="r"))
    assert isinstance(client, FoundryClaudeClient)


def test_make_llm_rejects_unknown_provider():
    with pytest.raises(ValueError, match="MC_LLM"):
        make_llm(Settings(llm="psychic"))
