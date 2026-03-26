import pytest
import respx
import httpx
from scripts.hn_client import HNClient


BASE = "https://hacker-news.firebaseio.com/v0"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_top_ids():
    respx.get(f"{BASE}/topstories.json").mock(
        return_value=httpx.Response(200, json=list(range(1, 501)))
    )
    async with HNClient() as client:
        ids = await client.fetch_top_ids(limit=30)
    assert ids == list(range(1, 31))


@pytest.mark.asyncio
@respx.mock
async def test_fetch_item():
    item = {"id": 42, "title": "Test", "score": 100, "descendants": 10, "time": 1700000000}
    respx.get(f"{BASE}/item/42.json").mock(return_value=httpx.Response(200, json=item))
    async with HNClient() as client:
        result = await client.fetch_item(42)
    assert result["id"] == 42


@pytest.mark.asyncio
@respx.mock
async def test_fetch_top_stories_returns_30():
    ids = list(range(1, 501))
    respx.get(f"{BASE}/topstories.json").mock(return_value=httpx.Response(200, json=ids))
    for i in range(1, 31):
        item = {
            "id": i,
            "title": f"Story {i}",
            "score": i * 10,
            "descendants": i,
            "time": 1700000000,
            "kids": [],
        }
        respx.get(f"{BASE}/item/{i}.json").mock(return_value=httpx.Response(200, json=item))
    async with HNClient() as client:
        stories = await client.fetch_top_stories(limit=30)
    assert len(stories) == 30
    assert stories[0].rank == 1
