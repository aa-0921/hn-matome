import pytest
from pathlib import Path
from datetime import datetime, timezone
from scripts.models import DailyReport, Story, Comment
from scripts.generator import HTMLGenerator


TEMPLATES_DIR = Path(__file__).parent.parent / "scripts" / "templates"


@pytest.fixture
def generator(tmp_path):
    return HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=tmp_path)


@pytest.fixture
def sample_story():
    return Story(
        rank=1, id=100, title_en="Test Story", title_ja="テストストーリー",
        url="https://example.com", hn_url="https://news.ycombinator.com/item?id=100",
        score=200, comment_count=50,
        posted_at=datetime(2026, 3, 26, tzinfo=timezone.utc),
        summary_ja="コミュニティでは主に性能について議論されていました。"
    )


@pytest.fixture
def sample_report(sample_story):
    return DailyReport(date=datetime(2026, 3, 26, tzinfo=timezone.utc), stories=[sample_story])


def test_generate_archive(generator, sample_report, tmp_path):
    generator.generate_archive(sample_report, prev_date=None, next_date=None)
    out = tmp_path / "archive" / "2026-03-26.html"
    assert out.exists()
    content = out.read_text()
    assert "テストストーリー" in content
    assert "2026年3月26日" in content
    assert "data-pagefind-body" in content  # Pagefind のインデックス対象


def test_generate_archive_includes_summary(generator, sample_report, tmp_path):
    generator.generate_archive(sample_report, prev_date=None, next_date=None)
    content = (tmp_path / "archive" / "2026-03-26.html").read_text()
    assert "コミュニティでは主に性能" in content


def test_generate_index(generator, sample_report, tmp_path):
    generator.generate_index(latest_report=sample_report, archive_dates=["2026-03-26"])
    out = tmp_path / "index.html"
    assert out.exists()
    content = out.read_text()
    assert "2026年3月26日" in content
    assert "2026-03-26" in content


def test_generate_static_pages(generator, tmp_path):
    generator.generate_static_pages()
    assert (tmp_path / "about.html").exists()
    assert (tmp_path / "privacy.html").exists()
    about_content = (tmp_path / "about.html").read_text()
    assert "HN日報について" in about_content
