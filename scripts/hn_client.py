import asyncio
import httpx
from scripts.models import Comment, Story

BASE_URL = "https://hacker-news.firebaseio.com/v0"
MAX_CONCURRENT = 10


class HNClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def fetch_item(self, item_id: int) -> dict:
        resp = await self._client.get(f"{BASE_URL}/item/{item_id}.json")
        resp.raise_for_status()
        return resp.json()

    async def fetch_top_ids(self, limit: int = 30) -> list[int]:
        resp = await self._client.get(f"{BASE_URL}/topstories.json")
        resp.raise_for_status()
        return resp.json()[:limit]

    async def fetch_top_stories(self, limit: int = 30) -> list[Story]:
        ids = await self.fetch_top_ids(limit)
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_one(rank: int, item_id: int) -> Story:
            async with sem:
                data = await self.fetch_item(item_id)
            return Story.from_api(data, rank=rank)

        tasks = [fetch_one(i + 1, item_id) for i, item_id in enumerate(ids)]
        return await asyncio.gather(*tasks)

    async def fetch_comments(self, story: Story, max_comments: int = 5) -> list[Comment]:
        """記事の上位コメントを取得する（第一階層のみ）"""
        if not story.comment_count:
            return []
        data = await self.fetch_item(story.id)
        kid_ids = data.get("kids", [])[:max_comments]
        if not kid_ids:
            return []

        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_comment(cid: int) -> Comment | None:
            async with sem:
                try:
                    data = await self.fetch_item(cid)
                    if data.get("deleted") or data.get("dead"):
                        return None
                    return Comment.from_api(data)
                except Exception:
                    return None

        results = await asyncio.gather(*[fetch_comment(cid) for cid in kid_ids])
        return [c for c in results if c is not None]
