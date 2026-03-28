import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Optional, Any


class _TextExtractor(HTMLParser):
    """HN コメント本文からタグを除いたテキスト断片を収集する。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(text: str) -> str:
    """HN コメントの HTML タグを除去し、&amp; 等をデコードする"""
    if not text:
        return ""
    extractor = _TextExtractor()
    extractor.feed(text)
    extractor.close()
    text = extractor.get_text()
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

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "author": self.author, "text": self.text}

    @classmethod
    def from_dict(cls, d: dict) -> "Comment":
        return cls(id=d["id"], author=d["author"], text=d["text"])


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "id": self.id,
            "title_en": self.title_en,
            "title_ja": self.title_ja,
            "url": self.url,
            "hn_url": self.hn_url,
            "score": self.score,
            "comment_count": self.comment_count,
            "posted_at": self.posted_at.isoformat(),
            "comments": [c.to_dict() for c in self.comments],
            "summary_ja": self.summary_ja,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Story":
        return cls(
            rank=d["rank"],
            id=d["id"],
            title_en=d["title_en"],
            title_ja=d["title_ja"],
            url=d.get("url"),
            hn_url=d["hn_url"],
            score=d["score"],
            comment_count=d["comment_count"],
            posted_at=datetime.fromisoformat(d["posted_at"]),
            comments=[Comment.from_dict(c) for c in d.get("comments", [])],
            summary_ja=d.get("summary_ja", ""),
        )


@dataclass
class DailyReport:
    date: datetime
    stories: list[Story]
    slot: Optional[str] = None  # "07", "12", "23" など。None は旧形式

    @property
    def date_str(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def slug(self) -> str:
        """ファイル名キー。スロットあり: '2026-03-27_07', なし: '2026-03-27'"""
        if self.slot:
            return f"{self.date_str}_{self.slot}"
        return self.date_str

    @property
    def date_ja(self) -> str:
        return f"{self.date.year}年{self.date.month}月{self.date.day}日"

    @property
    def fetched_at(self) -> str:
        """表示用取得時刻。例: '07:00取得'。スロットなしは空文字"""
        return f"{self.slot}:00取得" if self.slot else ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "slot": self.slot,
            "stories": [s.to_dict() for s in self.stories],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DailyReport":
        return cls(
            date=datetime.fromisoformat(d["date"]),
            slot=d.get("slot"),
            stories=[Story.from_dict(s) for s in d["stories"]],
        )
