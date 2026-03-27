import pytest
import respx
import httpx
from datetime import date
from scripts.hn_client import HNClient


BASE = "https://hacker-news.firebaseio.com/v0"
ALGOLIA_BASE = "https://hn.algolia.com/api/v1"


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


@pytest.mark.asyncio
@respx.mock
async def test_fetch_top_stories_for_date_from_algolia():
    hits = [
        {
            "objectID": "101",
            "title": "Story A",
            "url": "https://example.com/a",
            "points": 120,
            "num_comments": 40,
            "created_at_i": 1711543200,
        },
        {
            "objectID": "102",
            "title": "Story B",
            "url": "https://example.com/b",
            "points": 300,
            "num_comments": 10,
            "created_at_i": 1711546800,
        },
        {
            "objectID": "103",
            "title": "Story C",
            "url": "https://example.com/c",
            "points": 300,
            "num_comments": 11,
            "created_at_i": 1711540000,
        },
    ]
    respx.get(f"{ALGOLIA_BASE}/search").mock(
        return_value=httpx.Response(200, json={"hits": hits})
    )

    async with HNClient() as client:
        stories = await client.fetch_top_stories_for_date(
            target_date_jst=date(2026, 3, 27),
            limit=2,
        )

    assert len(stories) == 2
    # points が同じ場合は num_comments が多い方が上位
    assert stories[0].id == 103
    assert stories[0].rank == 1
    assert stories[1].id == 102
