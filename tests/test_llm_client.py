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


@pytest.mark.asyncio
@respx.mock
async def test_call_falls_back_to_next_model_on_429(client):
    # :free は upstream の 429 が日常的に起きるため、次モデルへ進めること
    respx.post(OPENROUTER_URL).mock(
        side_effect=[
            httpx.Response(429, json={"error": {"message": "rate-limited upstream"}}),
            httpx.Response(200, json=make_response("1. 翻訳タイトル1")),
        ]
    )
    result = await client.translate_titles(["Title 1"])
    assert result == ["翻訳タイトル1"]


@pytest.mark.asyncio
@respx.mock
async def test_call_skips_model_returning_empty_body(client):
    # 推論だけして本文を返さないモデルは失敗扱いにして次へ進む
    respx.post(OPENROUTER_URL).mock(
        side_effect=[
            httpx.Response(200, json=make_response("   ")),
            httpx.Response(200, json=make_response("要約本文")),
        ]
    )
    result = await client.summarize_comments("Test Article", ["comment 1"])
    assert result == "要約本文"


@pytest.mark.asyncio
@respx.mock
async def test_call_returns_empty_when_whole_chain_fails(client):
    # チェーン全滅時は例外を投げず空文字（翻訳全滅は update.yml 側が検知する）
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(429, json={"error": {"message": "rate-limited"}})
    )
    result = await client.summarize_comments("Test Article", ["comment 1"])
    assert result == ""


def test_model_chain_is_all_free():
    # 有料モデルが紛れ込むと課金が発生するため :free 固定を保証する
    from scripts.llm_client import MODEL_CHAIN

    assert MODEL_CHAIN, "チェーンが空"
    assert all(m.endswith(":free") for m in MODEL_CHAIN)
    assert len(set(MODEL_CHAIN)) == len(MODEL_CHAIN), "重複あり"
