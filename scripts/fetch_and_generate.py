#!/usr/bin/env python3
"""
HN日報 メインスクリプト
HN API からデータ取得 → OpenRouter で翻訳・要約 → 静的 HTML 生成
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scripts.hn_client import HNClient
from scripts.llm_client import LLMClient
from scripts.models import DailyReport
from scripts.generator import HTMLGenerator
from scripts.sitemap import SitemapGenerator

DOCS_DIR = Path(__file__).parent.parent / "docs"
TEMPLATES_DIR = Path(__file__).parent / "templates"
BASE_URL = "https://hn-matome.pages.dev"
JST = timezone(timedelta(hours=9))


def get_existing_dates() -> list[str]:
    """既存のアーカイブ日付一覧を取得する"""
    archive_dir = DOCS_DIR / "archive"
    if not archive_dir.exists():
        return []
    return sorted(
        [p.stem for p in archive_dir.glob("*.html")],
        reverse=True
    )


async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(tz=JST).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"実行日時: {today.strftime('%Y-%m-%d %H:%M')} JST")

    generator = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=DOCS_DIR)
    sitemap_gen = SitemapGenerator(output_dir=DOCS_DIR, base_url=BASE_URL)

    # HN データ取得
    print("HN API からトップ30記事を取得中...")
    async with HNClient() as hn:
        stories = await hn.fetch_top_stories(limit=30)
        print(f"{len(stories)} 件取得完了。コメント取得中...")
        for story in stories:
            story.comments = await hn.fetch_comments(story, max_comments=5)

    # LLM で翻訳・要約
    llm = LLMClient(api_key=api_key)
    print("タイトルを一括翻訳中...")
    titles_en = [s.title_en for s in stories]
    titles_ja = await llm.translate_titles(titles_en)
    for story, ja in zip(stories, titles_ja):
        story.title_ja = ja

    print("コメントを要約中...")
    for story in stories:
        if story.comments:
            texts = [c.text for c in story.comments if c.text]
            story.summary_ja = await llm.summarize_comments(story.title_en, texts)

    # HTML 生成
    report = DailyReport(date=today, stories=stories)
    existing_dates = get_existing_dates()

    # prev / next 日付を計算
    today_str = today.strftime("%Y-%m-%d")
    all_dates = sorted(set(existing_dates + [today_str]))
    idx = all_dates.index(today_str)
    prev_date = all_dates[idx - 1] if idx > 0 else None
    next_date = all_dates[idx + 1] if idx < len(all_dates) - 1 else None

    print(f"archive/{today_str}.html を生成中...")
    generator.generate_archive(report, prev_date=prev_date, next_date=next_date)

    # index + サイトマップ更新
    archive_dates = sorted(set(existing_dates + [today_str]), reverse=True)
    generator.generate_index(latest_report=report, archive_dates=archive_dates)
    generator.generate_static_pages()
    sitemap_gen.generate(archive_dates=archive_dates)
    sitemap_gen.generate_redirects(latest_date=today_str)
    sitemap_gen.generate_robots()

    print("完了")


if __name__ == "__main__":
    asyncio.run(main())
