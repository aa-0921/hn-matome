#!/usr/bin/env python3
"""
HN日報 メインスクリプト
HN API からデータ取得 → OpenRouter で翻訳・要約 → 静的 HTML 生成
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

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
    load_dotenv()

    parser = argparse.ArgumentParser(description="HN日報の取得・翻訳・HTML生成")
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=0,
        help="過去N日分を追加生成（当日分に加えて過去分を生成）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="1日あたりの取得記事数",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(tz=JST).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"実行日時: {today.strftime('%Y-%m-%d %H:%M')} JST")
    target_dates = [today - timedelta(days=i) for i in range(max(args.backfill_days, 0), -1, -1)]
    print("生成対象日:", ", ".join([d.strftime("%Y-%m-%d") for d in target_dates]))

    generator = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=DOCS_DIR)
    sitemap_gen = SitemapGenerator(output_dir=DOCS_DIR, base_url=BASE_URL)
    existing_dates = get_existing_dates()
    reports_by_date: dict[str, DailyReport] = {}

    async with HNClient() as hn:
        llm = LLMClient(api_key=api_key)
        for target_date in target_dates:
            target_date_str = target_date.strftime("%Y-%m-%d")
            if target_date_str == today.strftime("%Y-%m-%d"):
                print(f"[{target_date_str}] HN API からトップ{args.limit}記事を取得中...")
                stories = await hn.fetch_top_stories(limit=args.limit)
            else:
                print(f"[{target_date_str}] Algolia API から過去記事トップ{args.limit}を取得中...")
                stories = await hn.fetch_top_stories_for_date(target_date_jst=target_date.date(), limit=args.limit)

            print(f"[{target_date_str}] {len(stories)} 件取得完了。コメント取得中...")
            for story in stories:
                story.comments = await hn.fetch_comments(story, max_comments=5)

            # LLM で翻訳・要約
            print(f"[{target_date_str}] タイトルを一括翻訳中...")
            titles_en = [s.title_en for s in stories]
            titles_ja = await llm.translate_titles(titles_en)
            for story, ja in zip(stories, titles_ja):
                story.title_ja = ja

            print(f"[{target_date_str}] コメントを要約中...")
            for story in stories:
                if story.comments:
                    texts = [c.text for c in story.comments if c.text]
                    story.summary_ja = await llm.summarize_comments(story.title_en, texts)

            reports_by_date[target_date_str] = DailyReport(date=target_date, stories=stories)

    # HTML 生成（prev / next を全日付で計算）
    generated_dates = list(reports_by_date.keys())
    all_dates = sorted(set(existing_dates + generated_dates))
    for date_str in generated_dates:
        idx = all_dates.index(date_str)
        prev_date = all_dates[idx - 1] if idx > 0 else None
        next_date = all_dates[idx + 1] if idx < len(all_dates) - 1 else None
        print(f"archive/{date_str}.html を生成中...")
        generator.generate_archive(reports_by_date[date_str], prev_date=prev_date, next_date=next_date)

    # index + サイトマップ更新
    archive_dates = sorted(all_dates, reverse=True)
    latest_date = archive_dates[0] if archive_dates else None
    latest_report = reports_by_date.get(latest_date) if latest_date else None
    generator.generate_index(latest_report=latest_report, archive_dates=archive_dates)
    generator.generate_static_pages()
    sitemap_gen.generate(archive_dates=archive_dates)
    sitemap_gen.generate_redirects(latest_date=latest_date or today.strftime("%Y-%m-%d"))
    sitemap_gen.generate_robots()

    print("完了")


if __name__ == "__main__":
    asyncio.run(main())
