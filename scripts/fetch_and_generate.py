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
BASE_URL = "https://hn-matome-2ht.pages.dev"
JST = timezone(timedelta(hours=9))


def get_existing_slugs() -> list[str]:
    """既存のアーカイブスラグ一覧を取得する"""
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
        "--slot",
        type=str,
        default=None,
        help="取得スロット（'07', '12', '23' など）。省略時はスロットなし（旧形式）",
    )
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
    parser.add_argument(
        "--regenerate-all",
        action="store_true",
        help="docs/data/*.json を全部読んでHTMLだけ再生成（LLM APIスキップ）",
    )
    args = parser.parse_args()

    run_started_at = datetime.now(tz=JST)
    today = run_started_at.replace(hour=0, minute=0, second=0, microsecond=0)
    slot_label = f" スロット={args.slot}" if args.slot else ""
    print(f"実行日時: {today.strftime('%Y-%m-%d %H:%M')} JST{slot_label}")

    generator = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=DOCS_DIR)
    sitemap_gen = SitemapGenerator(output_dir=DOCS_DIR, base_url=BASE_URL)
    existing_slugs = get_existing_slugs()
    reports: dict[str, DailyReport] = {}
    metrics = {
        "translate_requests": 0,
        "translate_failures": 0,
        "summarize_requests": 0,
        "summarize_failures": 0,
        "summaries_success": 0,
    }

    if args.regenerate_all:
        # LLM APIを呼ばず、既存JSONから全アーカイブを再生成
        slugs = generator.get_existing_slugs()
        if not slugs:
            print("ERROR: docs/data/*.json が見つかりません", file=sys.stderr)
            sys.exit(1)
        print(f"--regenerate-all: {len(slugs)} 件のJSONからHTML再生成します")
        for slug in slugs:
            report = generator.load_report_json(slug)
            if report is not None:
                reports[slug] = report
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("ERROR: OPENROUTER_API_KEY が設定されていません", file=sys.stderr)
            sys.exit(1)

        target_dates = [today - timedelta(days=i) for i in range(max(args.backfill_days, 0), -1, -1)]
        print("生成対象日:", ", ".join([d.strftime("%Y-%m-%d") for d in target_dates]))

        async with HNClient() as hn:
            llm = LLMClient(api_key=api_key)
            for target_date in target_dates:
                target_date_str = target_date.strftime("%Y-%m-%d")
                target_slug = f"{target_date_str}_{args.slot}" if args.slot else target_date_str

                # スロット別JSONキャッシュが存在する場合はLLM APIをスキップ
                cached = generator.load_report_json(target_slug)
                if cached is not None:
                    print(f"[{target_slug}] JSONキャッシュから読み込み（LLM APIスキップ）")
                    reports[target_slug] = cached
                    continue

                if target_date_str == today.strftime("%Y-%m-%d"):
                    print(f"[{target_slug}] HN API からトップ{args.limit}記事を取得中...")
                    stories = await hn.fetch_top_stories(limit=args.limit)
                else:
                    print(f"[{target_slug}] Algolia API から過去記事トップ{args.limit}を取得中...")
                    stories = await hn.fetch_top_stories_for_date(target_date_jst=target_date.date(), limit=args.limit)

                print(f"[{target_slug}] {len(stories)} 件取得完了。コメント取得中...")
                for story in stories:
                    try:
                        story.comments = await hn.fetch_comments(story, max_comments=5)
                    except Exception as e:
                        story.comments = []
                        print(f"[WARN] [{target_slug}] story_id={story.id} コメント取得失敗: {e}")

                # LLM で翻訳・要約
                print(f"[{target_slug}] タイトルを一括翻訳中...")
                titles_en = [s.title_en for s in stories]
                metrics["translate_requests"] += 1
                try:
                    titles_ja = await llm.translate_titles(titles_en)
                except Exception as e:
                    metrics["translate_failures"] += 1
                    titles_ja = titles_en
                    print(f"[WARN] [{target_slug}] タイトル翻訳失敗のため英語タイトルを使用: {e}")
                for story, ja in zip(stories, titles_ja):
                    story.title_ja = ja

                print(f"[{target_slug}] コメントを要約中...")
                for story in stories:
                    if story.comments:
                        texts = [c.text for c in story.comments if c.text]
                        if not texts:
                            continue
                        metrics["summarize_requests"] += 1
                        try:
                            story.summary_ja = await llm.summarize_comments(story.title_en, texts)
                            metrics["summaries_success"] += 1
                        except Exception as e:
                            metrics["summarize_failures"] += 1
                            story.summary_ja = ""
                            print(
                                f"[WARN] [{target_slug}] story_id={story.id} コメント要約失敗（継続）: {e}"
                            )

                report = DailyReport(date=target_date, stories=stories, slot=args.slot)
                generator.save_report_json(report)
                print(f"[{target_slug}] JSONキャッシュを保存しました")
                reports[target_slug] = report

    # HTML 生成（prev / next を全スラグで計算）
    generated_slugs = list(reports.keys())
    all_slugs = sorted(set(existing_slugs + generated_slugs))
    for slug in generated_slugs:
        idx = all_slugs.index(slug)
        prev_date = all_slugs[idx - 1] if idx > 0 else None
        next_date = all_slugs[idx + 1] if idx < len(all_slugs) - 1 else None
        print(f"archive/{slug}.html を生成中...")
        generator.generate_archive(reports[slug], prev_date=prev_date, next_date=next_date)

    # index + サイトマップ更新
    archive_slugs = sorted(all_slugs, reverse=True)
    latest_slug = archive_slugs[0] if archive_slugs else None
    latest_report = reports.get(latest_slug) if latest_slug else None
    if latest_report is None and latest_slug:
        latest_report = generator.load_report_json(latest_slug)
    generator.generate_index(latest_report=latest_report, archive_slugs=archive_slugs)
    generator.generate_static_pages(
        last_updated_ja=f"{run_started_at.year}年{run_started_at.month}月{run_started_at.day}日"
    )
    sitemap_gen.generate(archive_slugs=archive_slugs)
    sitemap_gen.generate_redirects(latest_date=latest_slug or today.strftime("%Y-%m-%d"))
    sitemap_gen.generate_robots()

    print(
        "[METRICS] 翻訳req={translate_requests}, 翻訳失敗={translate_failures}, "
        "要約req={summarize_requests}, 要約成功={summaries_success}, 要約失敗={summarize_failures}".format(
            **metrics
        )
    )
    print("完了")


if __name__ == "__main__":
    asyncio.run(main())
