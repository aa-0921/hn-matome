import pytest
import respx
import httpx
from scripts.llm_client import LLMClient


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def make_response(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


@pytest.fixture
def client():
    return LLMClient(api_key="test-key")


@pytest.mark.asyncio
@respx.mock
async def test_translate_titles(client):
    translated = "\n".join([f"{i+1}. 翻訳タイトル{i+1}" for i in range(3)])
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response(translated))
    )
    titles = ["Title 1", "Title 2", "Title 3"]
    result = await client.translate_titles(titles)
    assert len(result) == 3
    assert result[0] == "翻訳タイトル1"
    assert result[1] == "翻訳タイトル2"


@pytest.mark.asyncio
@respx.mock
async def test_translate_titles_fallback_on_count_mismatch(client):
    # LLM が件数不一致の応答を返した場合は元のタイトルをフォールバック
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response("1. 翻訳のみ"))
    )
    titles = ["Title 1", "Title 2", "Title 3"]
    result = await client.translate_titles(titles)
    assert len(result) == 3
    assert result[1] == "Title 2"  # フォールバック


@pytest.mark.asyncio
@respx.mock
async def test_summarize_comments(client):
    summary = "コミュニティでは主にパフォーマンスについて議論されていました。"
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response(summary))
    )
    result = await client.summarize_comments("Test Article", ["comment 1", "comment 2"])
    assert result == summary


@pytest.mark.asyncio
async def test_summarize_comments_empty(client):
    # コメントがない場合は API を呼ばない（respx.mock なしで通ること）
    result = await client.summarize_comments("Test Article", [])
    assert result == ""


@pytest.mark.asyncio
@respx.mock
async def test_translate_titles_fallback_when_content_is_null(client):
    # API が content=null を返しても例外にせずフォールバックする
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response(None))
    )
    titles = ["Title 1", "Title 2"]
    result = await client.translate_titles(titles)
    assert result == titles
