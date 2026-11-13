import json

import httpx

from app.llm.openai_compat import OpenAICompatClient

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}


def mock_host(content: str, seen: list):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "local-model",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": {"prompt_tokens": 120, "completion_tokens": 7, "total_tokens": 127},
        }
        return httpx.Response(200, json=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_structured_call_uses_openai_chat_completions_shape():
    seen = []
    client = OpenAICompatClient(
        base_url="http://ollama.test/v1", api_key="k", http_client=mock_host('{"ok": true}', seen)
    )
    result = await client.complete(
        step="classify", system="sys", prompt="hello", schema=SCHEMA, model="local-model"
    )

    (req,) = seen
    assert req.url == "http://ollama.test/v1/chat/completions"
    sent = json.loads(req.content)
    assert sent["model"] == "local-model"
    assert sent["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
    ]
    assert sent["response_format"]["type"] == "json_schema"
    assert sent["response_format"]["json_schema"]["schema"] == SCHEMA
    assert (result.text, result.input_tokens, result.output_tokens) == ('{"ok": true}', 120, 7)


async def test_plain_text_call_sends_no_response_format():
    seen = []
    client = OpenAICompatClient(
        base_url="http://h/v1", api_key="k", http_client=mock_host("A briefing.", seen)
    )
    result = await client.complete(step="draft", system="s", prompt="p", schema=None, model="m")
    assert "response_format" not in json.loads(seen[0].content)
    assert result.text == "A briefing."


async def test_reasoning_block_is_stripped():
    seen = []
    client = OpenAICompatClient(
        base_url="http://h/v1",
        api_key="k",
        http_client=mock_host('<think>hmm</think>\n{"ok": false}', seen),
    )
    result = await client.complete(step="x", system="s", prompt="p", schema=SCHEMA, model="m")
    assert result.text == '{"ok": false}'


async def test_reasoning_effort_is_sent_when_configured():
    seen = []
    client = OpenAICompatClient(
        base_url="http://h/v1",
        api_key="k",
        http_client=mock_host("{}", seen),
        reasoning_effort="none",
    )
    await client.complete(step="x", system="s", prompt="p", schema=SCHEMA, model="m")
    assert json.loads(seen[0].content)["reasoning_effort"] == "none"


async def test_host_without_structured_output_gets_the_schema_in_the_prompt():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        if "response_format" in seen[-1]:
            return httpx.Response(
                500, json={"error": {"message": "structured output is unavailable"}}
            )
        body = {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "m",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": 'Sure:\n```json\n{"ok": true}\n```',
                    },
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 9, "total_tokens": 59},
        }
        return httpx.Response(200, json=body)

    client = OpenAICompatClient(
        base_url="http://h/v1",
        api_key="k",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.complete(step="x", system="s", prompt="p", schema=SCHEMA, model="m")
    assert "response_format" not in seen[-1]
    assert '"required": ["ok"]' in seen[-1]["messages"][0]["content"]
    assert result.text == '{"ok": true}'
