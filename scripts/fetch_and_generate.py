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
from scripts.models import DailyReport, WeeklyAnalysis, TrendSection
from scripts.generator import HTMLGenerator, _is_valid_report_slug
from scripts.sitemap import SitemapGenerator

DOCS_DIR = Path(__file__).parent.parent / "docs"
TEMPLATES_DIR = Path(__file__).parent / "templates"
BASE_URL = "https://hn-matome-2ht.pages.dev"
JST = timezone(timedelta(hours=9))


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
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="過去7日分のデータから週間トレンド分析を生成する",
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
        "editor_note_requests": 0,
        "editor_note_failures": 0,
        "categorize_requests": 0,
        "categorize_failures": 0,
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

                # ひとこと解説を一括生成
                print(f"[{target_slug}] ひとこと解説を生成中...")
                titles_ja_list = [s.title_ja or s.title_en for s in stories]
                titles_en_list = [s.title_en for s in stories]
                metrics["editor_note_requests"] += 1
                try:
                    editor_notes = await llm.generate_editor_notes(titles_ja_list, titles_en_list)
                    for story, note in zip(stories, editor_notes):
                        story.editor_note = note
                except Exception as e:
                    metrics["editor_note_failures"] += 1
                    print(f"[WARN] [{target_slug}] ひとこと解説生成失敗（継続）: {e}")

                # カテゴリ分類を一括生成
                print(f"[{target_slug}] カテゴリ分類中...")
                metrics["categorize_requests"] += 1
                try:
                    categories = await llm.categorize_stories(titles_en_list)
                    for story, cat in zip(stories, categories):
                        story.category = cat
                except Exception as e:
                    metrics["categorize_failures"] += 1
                    print(f"[WARN] [{target_slug}] カテゴリ分類失敗（継続）: {e}")

                report = DailyReport(date=target_date, stories=stories, slot=args.slot)
                generator.save_report_json(report)
                print(f"[{target_slug}] JSONキャッシュを保存しました")
                reports[target_slug] = report

    # HTML 生成（prev / next を全スラグで計算、既存スラグも再生成してナビを最新化）
    generated_slugs = list(reports.keys())
    all_slugs = sorted(
        {s for s in existing_slugs + generated_slugs if _is_valid_report_slug(s)}
    )
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

    # 週間トレンド分析の生成
    if args.weekly:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("ERROR: --weekly には OPENROUTER_API_KEY が必要です", file=sys.stderr)
            sys.exit(1)

        week_end = today.date() if hasattr(today, 'date') else today
        if hasattr(week_end, 'date'):
            week_end = week_end.date()
        else:
            from datetime import date as date_type
            week_end = date_type(today.year, today.month, today.day)
        week_start = week_end - timedelta(days=6)
        weekly_slug = f"{week_start.isoformat()}_{week_end.isoformat()}"

        cached_weekly = generator.load_weekly_json(weekly_slug)
        if cached_weekly is not None:
            print(f"[週間分析] {weekly_slug} はキャッシュ済み（スキップ）")
        else:
            print(f"[週間分析] {week_start} 〜 {week_end} の記事を集約中...")
            weekly_stories = []
            for slug in all_slugs:
                date_part = slug[:10]
                if week_start.isoformat() <= date_part <= week_end.isoformat():
                    report = reports.get(slug) or generator.load_report_json(slug)
                    if report:
                        for s in report.stories:
                            weekly_stories.append(f"- {s.title_ja or s.title_en} (▲{s.score}点, 💬{s.comment_count}件)")

            if weekly_stories:
                stories_text = f"期間: {week_start} 〜 {week_end}\n記事数: {len(weekly_stories)}\n\n" + "\n".join(weekly_stories[:100])
                llm = LLMClient(api_key=api_key)
                print(f"[週間分析] LLMで分析生成中...")
                try:
                    raw = await llm.generate_weekly_analysis(stories_text)
                    # JSON部分を抽出
                    import re as _re
                    json_match = _re.search(r'\{[\s\S]*\}', raw)
                    if json_match:
                        analysis_data = json.loads(json_match.group())
                        trend_sections = []
                        for t in analysis_data.get("trends", []):
                            trend_sections.append(TrendSection(
                                topic=t.get("topic", ""),
                                analysis=t.get("analysis", ""),
                                impact=t.get("impact", ""),
                                related_titles=t.get("related_titles", []),
                            ))
                        weekly_analysis = WeeklyAnalysis(
                            week_start=week_start,
                            week_end=week_end,
                            overview=analysis_data.get("overview", ""),
                            trend_sections=trend_sections,
                            editorial_comment=analysis_data.get("editorial_comment", ""),
                        )
                        generator.save_weekly_json(weekly_analysis)
                        print(f"[週間分析] {weekly_slug} を保存しました")
                    else:
                        print(f"[WARN] 週間分析: LLMレスポンスからJSONを抽出できませんでした")
                except Exception as e:
                    print(f"[WARN] 週間分析生成失敗: {e}")
            else:
                print(f"[週間分析] 対象期間のデータがありません")

    # 週間分析HTMLの生成（キャッシュ含む全件）
    weekly_slugs_list = generator.get_existing_weekly_slugs()
    for i, ws in enumerate(weekly_slugs_list):
        wa = generator.load_weekly_json(ws)
        if wa is None:
            continue
        prev_w = weekly_slugs_list[i + 1] if i + 1 < len(weekly_slugs_list) else None
        next_w = weekly_slugs_list[i - 1] if i > 0 else None
        generator.generate_weekly(wa, prev_weekly=prev_w, next_weekly=next_w)
    # 週間一覧ページ
    weekly_index_items = []
    for ws in weekly_slugs_list:
        wa = generator.load_weekly_json(ws)
        if wa:
            weekly_index_items.append({"slug": ws, "title": wa.title})
    generator.generate_weekly_index(weekly_index_items)

    sitemap_gen.generate(archive_slugs=archive_slugs, weekly_slugs=weekly_slugs_list)
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
        "要約req={summarize_requests}, 要約成功={summaries_success}, 要約失敗={summarize_failures}, "
        "解説req={editor_note_requests}, 解説失敗={editor_note_failures}, "
        "分類req={categorize_requests}, 分類失敗={categorize_failures}".format(
            **metrics
        )
    )
    print("完了")


if __name__ == "__main__":
    asyncio.run(main())
