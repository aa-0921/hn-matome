from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


class SitemapGenerator:
    def __init__(self, output_dir: Path, base_url: str):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")

    def generate(self, archive_dates: list[str]) -> Path:
        root = Element("urlset")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        def add_url(loc: str, changefreq: str, priority: str, lastmod: str | None = None):
            url = SubElement(root, "url")
            SubElement(url, "loc").text = loc
            if lastmod:
                SubElement(url, "lastmod").text = lastmod
            SubElement(url, "changefreq").text = changefreq
            SubElement(url, "priority").text = priority

        add_url(f"{self.base_url}/", "daily", "1.0")
        add_url(f"{self.base_url}/about.html", "monthly", "0.3")

        for date_str in sorted(archive_dates, reverse=True):
            add_url(
                f"{self.base_url}/archive/{date_str}.html",
                "never", "0.8", lastmod=date_str
            )

        xml_str = parseString(tostring(root, encoding="unicode")).toprettyxml(indent="  ")
        # minidom が追加する XML 宣言を差し替える（1行目が宣言の場合のみスキップ）
        lines = xml_str.splitlines()
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines)

        out = self.output_dir / "sitemap.xml"
        out.write_text(xml_str, encoding="utf-8")
        return out

    def generate_redirects(self, latest_date: str) -> Path:
        # 本番/ローカルでの遷移挙動を揃えるため、ルートは index.html へ固定する
        content = "/ /index.html 200\n"
        out = self.output_dir / "_redirects"
        out.write_text(content, encoding="utf-8")
        return out

    def generate_robots(self) -> Path:
        content = f"User-agent: *\nAllow: /\nSitemap: {self.base_url}/sitemap.xml\n"
        out = self.output_dir / "robots.txt"
        out.write_text(content, encoding="utf-8")
        return out
