import asyncio
import httpx
from datetime import datetime, date, time, timedelta, timezone
from scripts.models import Comment, Story

BASE_URL = "https://hacker-news.firebaseio.com/v0"
ALGOLIA_BASE_URL = "https://hn.algolia.com/api/v1"
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

    async def fetch_top_stories_for_date(self, target_date_jst: date, limit: int = 30) -> list[Story]:
        """
        指定日の投稿を Algolia HN API から取得し、points 順で上位を返す。
        target_date_jst は JST 日付として扱う。
        """
        jst = timezone(timedelta(hours=9))
        day_start_jst = datetime.combine(target_date_jst, time.min, tzinfo=jst)
        day_end_jst = datetime.combine(target_date_jst, time.max, tzinfo=jst)
        start_ts = int(day_start_jst.astimezone(timezone.utc).timestamp())
        end_ts = int(day_end_jst.astimezone(timezone.utc).timestamp())

        resp = await self._client.get(
            f"{ALGOLIA_BASE_URL}/search",
            params={
                "tags": "story",
                "numericFilters": f"created_at_i>={start_ts},created_at_i<={end_ts}",
                "hitsPerPage": 300,
            },
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])

        candidates: list[dict] = []
        for h in hits:
            title = h.get("title") or h.get("story_title") or ""
            object_id = h.get("objectID")
            created_at_i = h.get("created_at_i")
            if not title or not object_id or not created_at_i:
                continue
            candidates.append(h)

        # その日の投稿を人気順に近い形で並べる
        candidates.sort(
            key=lambda h: (
                int(h.get("points") or 0),
                int(h.get("num_comments") or 0),
                int(h.get("created_at_i") or 0),
            ),
            reverse=True,
        )

        stories: list[Story] = []
        for rank, h in enumerate(candidates[:limit], start=1):
            item_id = int(h["objectID"])
            posted_at = datetime.fromtimestamp(int(h["created_at_i"]), tz=timezone.utc)
            stories.append(
                Story(
                    rank=rank,
                    id=item_id,
                    title_en=h.get("title") or h.get("story_title") or "",
                    title_ja="",
                    url=h.get("url"),
                    hn_url=f"https://news.ycombinator.com/item?id={item_id}",
                    score=int(h.get("points") or 0),
                    comment_count=int(h.get("num_comments") or 0),
                    posted_at=posted_at,
                )
            )
        return stories

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
