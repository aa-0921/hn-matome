from scripts.models import Comment, Story, DailyReport
from datetime import datetime, timezone


def test_comment_from_api():
    raw = {"id": 1, "text": "Hello <b>world</b>", "by": "user1", "time": 1700000000}
    c = Comment.from_api(raw)
    assert c.id == 1
    assert c.author == "user1"
    # HTML タグが除去されていること
    assert "<b>" not in c.text
    assert "world" in c.text


def test_comment_missing_text():
    # text フィールドが欠けているコメント（削除済み等）は空文字扱い
    raw = {"id": 2, "by": "user2", "time": 1700000000}
    c = Comment.from_api(raw)
    assert c.text == ""


def test_story_from_api():
    raw = {
        "id": 100,
        "title": "Show HN: My Project",
        "url": "https://example.com",
        "score": 200,
        "descendants": 50,
        "time": 1700000000,
        "kids": [1, 2, 3],
    }
    s = Story.from_api(raw, rank=1)
    assert s.rank == 1
    assert s.title_en == "Show HN: My Project"
    assert s.hn_url == "https://news.ycombinator.com/item?id=100"
    assert s.score == 200
    assert s.comment_count == 50


def test_story_no_url():
    # Ask HN 等、外部 URL がない記事
    raw = {"id": 200, "title": "Ask HN: ...", "score": 100, "descendants": 20, "time": 1700000000}
    s = Story.from_api(raw, rank=1)
    assert s.url is None


def test_daily_report_date_str():
    stories = []
    report = DailyReport(date=datetime(2026, 3, 26, tzinfo=timezone.utc), stories=stories)
    assert report.date_str == "2026-03-26"
    assert report.date_ja == "2026年3月26日"
