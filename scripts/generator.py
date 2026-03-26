from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from scripts.models import DailyReport


class HTMLGenerator:
    def __init__(self, templates_dir: Path, output_dir: Path):
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

    def generate_archive(
        self,
        report: DailyReport,
        prev_date: str | None,
        next_date: str | None,
    ) -> Path:
        tmpl = self.env.get_template("archive.html")
        html = tmpl.render(report=report, prev_date=prev_date, next_date=next_date)
        out = self.output_dir / "archive" / f"{report.date_str}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        return out

    def generate_index(
        self,
        latest_report: DailyReport | None,
        archive_dates: list[str],
    ) -> Path:
        tmpl = self.env.get_template("index.html")
        html = tmpl.render(latest_report=latest_report, archive_dates=archive_dates)
        out = self.output_dir / "index.html"
        out.write_text(html, encoding="utf-8")
        return out

    def generate_static_pages(self) -> None:
        """about.html と privacy.html を生成する"""
        for page in ("about", "privacy"):
            tmpl = self.env.get_template(f"{page}.html")
            html = tmpl.render()
            out = self.output_dir / f"{page}.html"
            out.write_text(html, encoding="utf-8")
