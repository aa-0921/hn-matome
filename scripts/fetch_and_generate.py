#!/usr/bin/env python3
"""
HackerNews 日本語まとめ & AI要約 メインスクリプト
HN API からデータ取得 → OpenRouter で翻訳・要約 → 静的 HTML 生成
"""

import asyncio
import argparse
import json
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


def compute_target_dates(
    today: datetime,
    backfill_days: int,
    target_date_str: str | None,
) -> list[datetime]:
    """生成対象日一覧を返す。target_date_str 指定時は単日のみ。"""
    if target_date_str:
        try:
            parsed = datetime.strptime(target_date_str, "%Y-%m-%d")
        except ValueError:
            print(
                f"ERROR: --date の形式が不正です: {target_date_str} (YYYY-MM-DD を指定してください)",
                file=sys.stderr,
            )
            sys.exit(1)
        return [parsed.replace(tzinfo=today.tzinfo)]

    return [today - timedelta(days=i) for i in range(max(backfill_days, 0), -1, -1)]


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="HackerNews 日本語まとめ & AI要約の取得・翻訳・HTML生成"
    )
    parser.add_argument(
        "--slot",
        type=str,
        default=None,
        help="取得スロット（'07', '12', '23' など）。省略時はJST時刻から自動決定",
    )
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=0,
        help="過去N日分を追加生成（当日分に加えて過去分を生成）",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="生成対象日（YYYY-MM-DD）。指定時はその1日だけ生成し、--backfill-days より優先",
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

    # --slot 未指定かつデータ取得を行う場合は実際の JST 時刻をそのままスロットに設定
    if args.slot is None and not args.regenerate_all:
        jst_hour = datetime.now(tz=JST).hour
        args.slot = f"{jst_hour:02d}"
        print(f"[INFO] --slot 未指定: JST {jst_hour:02d}時 → slot={args.slot} を自動設定")

    run_started_at = datetime.now(tz=JST)
    today = run_started_at.replace(hour=0, minute=0, second=0, microsecond=0)

    slot_label = f" スロット={args.slot}" if args.slot else ""
    print(f"実行日時: {today.strftime('%Y-%m-%d %H:%M')} JST{slot_label}")

    generator = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=DOCS_DIR)
    sitemap_gen = SitemapGenerator(output_dir=DOCS_DIR, base_url=BASE_URL)
    # JSON ファイルを正規の slug 一覧とする（HTMLファイルは再生成物のため参照しない）
    existing_slugs = generator.get_existing_slugs()
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

        target_dates = compute_target_dates(
            today=today,
            backfill_days=args.backfill_days,
            target_date_str=args.date,
        )
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

    # HTML 生成（prev / next を全スラグで計算、既存スラグも再生成してナビを最新化）
    generated_slugs = list(reports.keys())
    all_slugs = sorted(set(existing_slugs + generated_slugs))
    recent_slugs_all = sorted(all_slugs, reverse=True)[:12]
    for slug in all_slugs:
        report = reports.get(slug) or generator.load_report_json(slug)
        if report is None:
            continue
        idx = all_slugs.index(slug)
        prev_date = all_slugs[idx - 1] if idx > 0 else None
        next_date = all_slugs[idx + 1] if idx < len(all_slugs) - 1 else None
        # 自身を除いた最新10件を内部リンク用に渡す
        recent_slugs = [s for s in recent_slugs_all if s != slug][:10]
        print(f"archive/{slug}.html を生成中...")
        generator.generate_archive(
            report, prev_date=prev_date, next_date=next_date, recent_slugs=recent_slugs
        )

    # index + サイトマップ更新
    archive_slugs = sorted(all_slugs, reverse=True)

    # 【重要・デグレ防止】
    # トップページには「JSONデータが存在する最新のレポート」を表示する。
    # archive_slugs の先頭スラグが archive/*.html のみ存在し docs/data/*.json が
    # 欠損しているケース（例: 当日の archive HTML のみ生成済み等）があるため、
    # JSON が見つかるまでスラグを順番に試す。
    # latest_report が None のままだと index.html の {% if latest_report %} ブロックが
    # スキップされ、トップページに記事一覧が一切表示されなくなる。
    latest_report = None
    for slug in archive_slugs:
        candidate = reports.get(slug) or generator.load_report_json(slug)
        if candidate is not None:
            latest_report = candidate
            break

    generator.generate_index(latest_report=latest_report, archive_slugs=archive_slugs)
    generator.generate_archive_index(archive_slugs=archive_slugs)
    generator.generate_static_pages(
        last_updated_ja=f"{run_started_at.year}年{run_started_at.month}月{run_started_at.day}日"
    )
    generator.generate_feed(archive_slugs=archive_slugs, base_url=BASE_URL)
    sitemap_gen.generate(archive_slugs=archive_slugs)
    # 旧形式HTML（スラグにスロットなし）の検出: 対応JSONが存在しないHTMLを削除してリダイレクトを永続保存
    redirects_cache = generator.output_dir / "data" / "_slug_redirects.json"
    slug_redirect_map: dict[str, str] = {}
    if redirects_cache.exists():
        slug_redirect_map = json.loads(redirects_cache.read_text(encoding="utf-8"))

    json_slugs = set(generator.get_existing_slugs())  # docs/data/*.json ベース
    archive_html_dir = generator.output_dir / "archive"
    if archive_html_dir.exists():
        for html_file in sorted(archive_html_dir.glob("*.html")):
            old_slug = html_file.stem
            if old_slug not in json_slugs and len(old_slug) == 10:
                candidates = sorted(s for s in json_slugs if s.startswith(old_slug + "_"))
                if candidates:
                    new_slug = candidates[-1]
                    slug_redirect_map[old_slug] = new_slug
                    html_file.unlink()
                    print(f"[INFO] 旧HTML削除・リダイレクト追加: {old_slug} → {new_slug}")

    if slug_redirect_map:
        redirects_cache.write_text(
            json.dumps(slug_redirect_map, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    latest_slug = archive_slugs[0] if archive_slugs else None
    sitemap_gen.generate_redirects(
        latest_date=latest_slug or today.strftime("%Y-%m-%d"),
        slug_redirects=list(slug_redirect_map.items()),
    )
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
