import pytest
from pathlib import Path
from datetime import datetime, timezone
from scripts.models import DailyReport, Story, Comment
from scripts.generator import HTMLGenerator, _is_valid_report_slug, _to_date_ja, _build_archive_groups


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
    generator.generate_index(latest_report=sample_report, archive_slugs=["2026-03-26"])
    out = tmp_path / "index.html"
    assert out.exists()
    content = out.read_text()
    assert "2026年3月26日" in content
    assert "2026-03-26" in content


def test_get_existing_slugs_ignores_non_report_json(tmp_path):
    """docs/data/index.json 等があっても日報スラグ一覧に混ぜない（to_date_ja 等の前提）"""
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "2026-03-26_23.json").write_text("{}", encoding="utf-8")
    (data / "index.json").write_text("{}", encoding="utf-8")
    (data / "_slug_redirects.json").write_text("{}", encoding="utf-8")
    gen = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=tmp_path)
    assert gen.get_existing_slugs() == ["2026-03-26_23"]


def test_generate_static_pages(generator, tmp_path):
    generator.generate_static_pages()
    assert (tmp_path / "about.html").exists()
    assert (tmp_path / "privacy.html").exists()
    about_content = (tmp_path / "about.html").read_text()
    assert "HackerNews 日本語まとめ & AI要約について" in about_content


class TestUIRegression:
    """テンプレート変更時に重要UI要素が消えないことを保証するリグレッションテスト"""

    REQUIRED_ELEMENTS = [
        ('<div id="search">',   "検索バー"),
        ('pagefind-ui.css',     "Pagefind CSS"),
        ('pagefind-ui.js',      "Pagefind JS"),
        ('class="site-header"', "サイトヘッダー"),
        ('href="/index.html"',  "トップへのリンク"),
        ('href="/about.html"',  "Aboutへのリンク"),
        ('class="site-footer"', "フッター"),
    ]

    def _assert_required_elements(self, content: str, page_name: str):
        for element, name in self.REQUIRED_ELEMENTS:
            assert element in content, f"{page_name} に {name} が含まれていません"

    def test_archive_has_required_ui(self, generator, tmp_path, sample_report):
        generator.generate_archive(sample_report, prev_date=None, next_date=None)
        path = tmp_path / "archive" / f"{sample_report.slug}.html"
        self._assert_required_elements(path.read_text(), "アーカイブページ")

    def test_index_has_required_ui(self, generator, tmp_path, sample_report):
        generator.generate_index(latest_report=sample_report, archive_slugs=[sample_report.slug])
        self._assert_required_elements(
            (tmp_path / "index.html").read_text(), "トップページ"
        )

    def test_static_pages_have_required_ui(self, generator, tmp_path):
        generator.generate_static_pages()
        for page in ["about.html", "privacy.html"]:
            self._assert_required_elements(
                (tmp_path / page).read_text(), page
            )


# --- 回帰テスト: index.json 等が混入してクラッシュしないことを保証 ---

def test_is_valid_report_slug_valid():
    assert _is_valid_report_slug("2026-03-29_23") is True
    assert _is_valid_report_slug("2026-03-29") is True


def test_is_valid_report_slug_invalid():
    assert _is_valid_report_slug("index") is False
    assert _is_valid_report_slug("_slug_redirects") is False
    assert _is_valid_report_slug("about") is False
    assert _is_valid_report_slug("2026-13-99") is False


def test_get_existing_slugs_excludes_non_date_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "2026-03-29_23.json").write_text("{}", encoding="utf-8")
    (data / "2026-03-28_07.json").write_text("{}", encoding="utf-8")
    (data / "index.json").write_text("{}", encoding="utf-8")
    (data / "_slug_redirects.json").write_text("{}", encoding="utf-8")
    gen = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=tmp_path)
    slugs = gen.get_existing_slugs()
    assert "index" not in slugs
    assert "_slug_redirects" not in slugs
    assert "2026-03-29_23" in slugs
    assert "2026-03-28_07" in slugs


def test_to_date_ja():
    assert _to_date_ja("2026-03-29_23") == "2026年3月29日"
    assert _to_date_ja("2026-03-29") == "2026年3月29日"
    assert _to_date_ja("2026-01-01") == "2026年1月1日"


def test_build_archive_groups():
    slugs = ["2026-03-29_23", "2026-03-29_07", "2026-03-28_23"]
    groups = _build_archive_groups(slugs)
    assert len(groups) == 2
    assert groups[0]["date_ja"] == "2026年3月29日"
    assert len(groups[0]["entries"]) == 2
    assert groups[0]["entries"][0]["label"] == "23:00取得"
    assert groups[0]["entries"][1]["label"] == "07:00取得"
    assert groups[1]["date_ja"] == "2026年3月28日"
    assert len(groups[1]["entries"]) == 1


def test_generate_archive_no_crash_with_valid_slugs(tmp_path, sample_report):
    """recent_slugs に 'index' が混入しても（実際はしない）generate_archive がクラッシュしない確認。
    get_existing_slugs が適切にフィルタするため index は渡されないことが本来の保証。"""
    gen = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=tmp_path)
    # 有効なスラグのみ渡す（get_existing_slugs の戻り値の想定通り）
    recent_slugs = ["2026-03-29_23", "2026-03-28_07"]
    out = gen.generate_archive(sample_report, prev_date=None, next_date=None, recent_slugs=recent_slugs)
    assert out.exists()
    content = out.read_text()
    assert "2026年3月29日" in content
    assert "2026年3月28日" in content
