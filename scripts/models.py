import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _strip_html(text: str) -> str:
    """HN コメントの HTML タグを除去し、&amp; 等をデコードする"""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#x27;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Comment:
    id: int
    author: str
    text: str

    @classmethod
    def from_api(cls, data: dict) -> "Comment":
        return cls(
            id=data["id"],
            author=data.get("by", ""),
            text=_strip_html(data.get("text", "")),
        )


@dataclass
class Story:
    rank: int
    id: int
    title_en: str
    title_ja: str
    url: Optional[str]
    hn_url: str
    score: int
    comment_count: int
    posted_at: datetime
    comments: list[Comment] = field(default_factory=list)
    summary_ja: str = ""

    @classmethod
    def from_api(cls, data: dict, rank: int) -> "Story":
        return cls(
            rank=rank,
            id=data["id"],
            title_en=data.get("title", ""),
            title_ja="",  # 翻訳後にセット
            url=data.get("url"),
            hn_url=f"https://news.ycombinator.com/item?id={data['id']}",
            score=data.get("score", 0),
            comment_count=data.get("descendants", 0),
            posted_at=datetime.fromtimestamp(data.get("time", 0), tz=timezone.utc),
        )


@dataclass
class DailyReport:
    date: datetime
    stories: list[Story]

    @property
    def date_str(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def date_ja(self) -> str:
        return f"{self.date.year}年{self.date.month}月{self.date.day}日"
