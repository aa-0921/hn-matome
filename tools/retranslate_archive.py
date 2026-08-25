#!/usr/bin/env python3
"""過去アーカイブの英語残りスロットを再翻訳する（1回限りの復旧用スクリプト）。

背景:
  2026-04-16 頃から翻訳が全滅し、docs/data/*.json に英語のままのスロットが
  344 件たまった。原因の LLM モデル廃止は llm_client.py の MODEL_CHAIN 化で
  修正済みだが、fetch_and_generate.py は JSON が存在すると LLM をスキップする
  ため、既存 JSON はそのままでは日本語化されない。

方式:
  JSON には title_en と comments[].text が保存されているので、HN API / Algolia
  を再取得する必要はない。既存 JSON の英語部分だけを LLM に通し、title_ja と
  summary_ja を埋めて書き戻す。HTML は次回の日次実行が全スロット再生成するため
  ここでは触らない。

無料枠の都合:
  OpenRouter の :free は日次リクエスト上限があるため --max-requests で区切って
  複数日に分割実行する。スロット単位で書き戻すので途中で止めても再開できる
  （既に日本語のスロット・story はスキップされる）。
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 本番（core リポ）と同じプロンプトを使うため scripts/scripts/llm_client.py を読む
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.llm_client import LLMClient  # noqa: E402

JA_RE = re.compile(r"[ぁ-んァ-ヶ一-龥]")
# stories のうち日本語タイトルがこの比率未満なら「翻訳が失われたスロット」と見なす
JA_TITLE_RATIO_THRESHOLD = 0.7
# 連続失敗がこの回数に達したらレート制限・チェーン全滅と判断して中断する
MAX_CONSECUTIVE_FAILURES = 5


def is_japanese(text: str | None) -> bool:
    return bool(text) and bool(JA_RE.search(text))


def slot_needs_translation(stories: list[dict]) -> bool:
    if not stories:
        return False
    ja_count = sum(1 for s in stories if is_japanese(s.get("title_ja")))
    return ja_count / len(stories) < JA_TITLE_RATIO_THRESHOLD


def story_needs_summary(story: dict) -> bool:
    if is_japanese(story.get("summary_ja")):
        return False
    return any(c.get("text") for c in story.get("comments", []))


def load_api_key() -> str:
    env_path = ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    print(f"ERROR: OPENROUTER_API_KEY が {env_path} に見つかりません", file=sys.stderr)
    sys.exit(1)


def save_slot(path: Path, data: dict) -> None:
    # generator.save_report_json と同じ書式（差分を書式ゆれで汚さない）
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def process_slot(llm: LLMClient, path: Path, budget: dict, stats: dict) -> str:
    """1スロットを再翻訳して書き戻す。戻り値は 'done' / 'skip' / 'abort'"""
    data = json.loads(path.read_text(encoding="utf-8"))
    stories = data.get("stories", [])

    need_title = slot_needs_translation(stories)
    summary_targets = [s for s in stories if story_needs_summary(s)]
    if not need_title and not summary_targets:
        return "skip"

    dirty = False

    if need_title:
        if budget["remaining"] <= 0:
            return "abort"
        titles_en = [s.get("title_en", "") for s in stories]
        budget["remaining"] -= 1
        stats["translate_requests"] += 1
        titles_ja = await llm.translate_titles(titles_en)
        # チェーン全滅時は _parse_numbered_list が元の英語をそのまま返す
        if titles_ja == titles_en:
            stats["translate_failures"] += 1
            stats["consecutive_failures"] += 1
            print(f"  [WARN] {path.stem} タイトル翻訳が英語のまま（LLM 応答なしの疑い）")
        else:
            stats["consecutive_failures"] = 0
            for story, ja in zip(stories, titles_ja):
                story["title_ja"] = ja
            dirty = True

        if stats["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
            if dirty:
                save_slot(path, data)
            return "abort"

    for story in summary_targets:
        if budget["remaining"] <= 0:
            break
        texts = [c["text"] for c in story.get("comments", []) if c.get("text")]
        if not texts:
            continue
        budget["remaining"] -= 1
        stats["summarize_requests"] += 1
        summary = await llm.summarize_comments(story.get("title_en", ""), texts)
        if summary:
            story["summary_ja"] = summary
            stats["summaries_success"] += 1
            stats["consecutive_failures"] = 0
            dirty = True
        else:
            stats["summarize_failures"] += 1
            stats["consecutive_failures"] += 1
            if stats["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                if dirty:
                    save_slot(path, data)
                return "abort"

    if dirty:
        save_slot(path, data)
    return "done"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-requests",
        type=int,
        default=900,
        help="1回の実行で使う LLM リクエストの上限（:free の日次枠から日次運用分を引いた値）",
    )
    parser.add_argument("--limit-slots", type=int, default=0, help="処理するスロット数の上限（0=無制限）")
    parser.add_argument("--dry-run", action="store_true", help="対象を数えるだけで LLM を呼ばない")
    args = parser.parse_args()

    data_dir = ROOT / "docs" / "data"
    paths = sorted(p for p in data_dir.glob("*.json") if not p.stem.startswith("_"))

    targets = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        stories = data.get("stories", [])
        n_title = 1 if slot_needs_translation(stories) else 0
        n_summary = sum(1 for s in stories if story_needs_summary(s))
        if n_title or n_summary:
            targets.append((path, n_title + n_summary))

    total_req = sum(n for _, n in targets)
    print(f"全 {len(paths)} スロット中 未処理 {len(targets)} スロット / 必要 req {total_req}")

    if args.dry_run:
        for path, n in targets[:10]:
            print(f"  {path.stem}: {n} req")
        if len(targets) > 10:
            print(f"  ... 他 {len(targets) - 10} スロット")
        return

    llm = LLMClient(api_key=load_api_key())
    budget = {"remaining": args.max_requests}
    stats = {
        "translate_requests": 0,
        "translate_failures": 0,
        "summarize_requests": 0,
        "summaries_success": 0,
        "summarize_failures": 0,
        "consecutive_failures": 0,
    }

    processed = 0
    aborted = False
    for path, need in targets:
        if budget["remaining"] <= 0:
            print("[INFO] リクエスト上限に到達したので停止します")
            break
        if args.limit_slots and processed >= args.limit_slots:
            print("[INFO] --limit-slots に到達したので停止します")
            break

        print(f"[{path.stem}] 処理中（想定 {need} req / 残 {budget['remaining']}）")
        result = await process_slot(llm, path, budget, stats)
        if result == "abort":
            print(
                f"[ERROR] 連続失敗 {stats['consecutive_failures']} 回。"
                "レート制限かチェーン全滅の可能性があるため中断します（再実行で続きから再開できます）",
                file=sys.stderr,
            )
            aborted = True
            break
        if result == "done":
            processed += 1

    print(
        "\n[SUMMARY] 処理スロット={p} 翻訳req={translate_requests} 翻訳失敗={translate_failures} "
        "要約req={summarize_requests} 要約成功={summaries_success} 要約失敗={summarize_failures} "
        "残りreq枠={r}".format(p=processed, r=budget["remaining"], **stats)
    )
    remaining_slots = len(targets) - processed
    print(f"[SUMMARY] 未処理スロット 残り約 {remaining_slots} 件")
    if aborted:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
