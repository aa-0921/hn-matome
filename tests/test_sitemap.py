import pytest
from pathlib import Path
from scripts.sitemap import SitemapGenerator

BASE_URL = "https://hn-matome-2ht.pages.dev"


@pytest.fixture
def gen(tmp_path):
    return SitemapGenerator(output_dir=tmp_path, base_url=BASE_URL)


def test_generate_sitemap(gen, tmp_path):
    gen.generate(archive_dates=["2026-03-25", "2026-03-26"])
    sitemap = tmp_path / "sitemap.xml"
    assert sitemap.exists()
    content = sitemap.read_text()
    assert f"{BASE_URL}/" in content
    assert "2026-03-26" in content
    assert "<urlset" in content


def test_generate_redirects(gen, tmp_path):
    gen.generate_redirects(latest_date="2026-03-26")
    redirects = tmp_path / "_redirects"
    assert redirects.exists()
    content = redirects.read_text()
    assert "/ /index.html 200" in content


def test_sitemap_xml_declaration(gen, tmp_path):
    gen.generate(archive_dates=[])
    content = (tmp_path / "sitemap.xml").read_text()
    assert content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert content.count("<?xml") == 1  # 宣言が重複していない


def test_sitemap_has_xmlns(gen, tmp_path):
    gen.generate(archive_dates=[])
    content = (tmp_path / "sitemap.xml").read_text()
    assert 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' in content


def test_generate_robots(gen, tmp_path):
    gen.generate_robots()
    robots = tmp_path / "robots.txt"
    assert robots.exists()
    content = robots.read_text()
    assert "Sitemap:" in content
    assert f"{BASE_URL}/sitemap.xml" in content
