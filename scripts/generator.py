import json
from collections import OrderedDict
from datetime import date as date_type, datetime, timezone, timedelta
from email.utils import formatdate
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from jinja2 import Environment, FileSystemLoader
from scripts.models import DailyReport


def _to_date_ja(date_str: str) -> str:
    """'YYYY-MM-DD' → 'YYYY年M月D日'"""
    d = date_type.fromisoformat(date_str[:10])
    return f"{d.year}年{d.month}月{d.day}日"


def _slug_to_parts(slug: str) -> tuple[str, str | None]:
    """'2026-03-27_07' → ('2026-03-27', '07'), '2026-03-27' → ('2026-03-27', None)"""
    if len(slug) > 10 and slug[10] == "_":
        return slug[:10], slug[11:]
    return slug, None


def _build_archive_groups(slugs: list[str]) -> list[dict]:
    """スラグ一覧を日付ごとにグループ化して返す（新しい順）"""
    groups: dict[str, list] = OrderedDict()
    for slug in slugs:
        date_part, slot = _slug_to_parts(slug)
        if date_part not in groups:
            groups[date_part] = []
        label = f"{slot}:00取得" if slot else ""
        groups[date_part].append({"slug": slug, "label": label})
    return [
        {"date_str": d, "date_ja": _to_date_ja(d), "entries": entries}
        for d, entries in groups.items()
    ]


class HTMLGenerator:
    def __init__(self, templates_dir: Path, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )
        self.env.filters["to_date_ja"] = _to_date_ja

    def generate_archive(
        self,
        report: DailyReport,
        prev_date: str | None,
        next_date: str | None,
        recent_slugs: list[str] | None = None,
    ) -> Path:
        tmpl = self.env.get_template("archive.html")
        html = tmpl.render(
            report=report,
            prev_date=prev_date,
            next_date=next_date,
            recent_slugs=recent_slugs or [],
        )
        out = self.output_dir / "archive" / f"{report.slug}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        return out

    def generate_index(
        self,
        latest_report: DailyReport | None,
        archive_slugs: list[str],
    ) -> Path:
        archive_groups = _build_archive_groups(archive_slugs)
        tmpl = self.env.get_template("index.html")
        html = tmpl.render(latest_report=latest_report, archive_groups=archive_groups)
        out = self.output_dir / "index.html"
        out.write_text(html, encoding="utf-8")
        return out

    def save_report_json(self, report: DailyReport) -> Path:
        data_dir = self.output_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        out = data_dir / f"{report.slug}.json"
        out.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out

    def load_report_json(self, slug: str) -> DailyReport | None:
        json_path = self.output_dir / "data" / f"{slug}.json"
        if not json_path.exists():
            return None
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return DailyReport.from_dict(data)

    def get_existing_slugs(self) -> list[str]:
        data_dir = self.output_dir / "data"
        if not data_dir.exists():
            return []
        return sorted([p.stem for p in data_dir.glob("*.json")], reverse=True)

    def generate_feed(
        self,
        archive_slugs: list[str],
        base_url: str = "https://hn-matome-2ht.pages.dev",
        max_items: int = 20,
    ) -> Path:
        """RSS 2.0 フィードを docs/feed.xml として生成する"""
        jst = timezone(timedelta(hours=9))

        rss = Element("rss")
        rss.set("version", "2.0")
        channel = SubElement(rss, "channel")
        SubElement(channel, "title").text = "HN日報 - HackerNews 日本語まとめ & AI要約"
        SubElement(channel, "link").text = f"{base_url}/"
        SubElement(channel, "description").text = "HackerNewsのトップ記事を毎日日本語翻訳・AI要約して配信"
        SubElement(channel, "language").text = "ja"
        SubElement(channel, "lastBuildDate").text = formatdate(usegmt=True)

        for slug in archive_slugs[:max_items]:
            report = self.load_report_json(slug)
            if report is None:
                continue
            date_part = slug[:10]
            slot = slug[11:] if len(slug) > 10 and slug[10] == "_" else None
            hour = int(slot) if slot else 8
            pub_dt = datetime(
                *[int(x) for x in date_part.split("-")], hour, 0, 0, tzinfo=jst
            )

            description_lines = []
            for story in report.stories[:10]:
                title = story.title_ja or story.title_en
                description_lines.append(f"#{story.rank} {title}")
            description_text = "\n".join(description_lines)

            item = SubElement(channel, "item")
            SubElement(item, "title").text = (
                f"{report.date_ja}"
                + (f"（{slot}:00取得）" if slot else "")
                + " HackerNews トップ記事"
            )
            SubElement(item, "link").text = f"{base_url}/archive/{slug}.html"
            SubElement(item, "guid").text = f"{base_url}/archive/{slug}.html"
            SubElement(item, "pubDate").text = formatdate(pub_dt.timestamp(), usegmt=True)
            SubElement(item, "description").text = description_text

        xml_str = parseString(tostring(rss, encoding="unicode")).toprettyxml(indent="  ")
        lines = xml_str.splitlines()
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines)

        out = self.output_dir / "feed.xml"
        out.write_text(xml_str, encoding="utf-8")
        return out

    def generate_static_pages(self, last_updated_ja: str | None = None) -> None:
        """about.html と privacy.html を生成する"""
        if last_updated_ja is None:
            jst_now = datetime.now(timezone(timedelta(hours=9)))
            last_updated_ja = f"{jst_now.year}年{jst_now.month}月{jst_now.day}日"

        for page in ("about", "privacy"):
            tmpl = self.env.get_template(f"{page}.html")
            html = tmpl.render(last_updated_ja=last_updated_ja)
            out = self.output_dir / f"{page}.html"
            out.write_text(html, encoding="utf-8")
