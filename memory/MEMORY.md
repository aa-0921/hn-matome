# HN日報 プロジェクト メモリ

## プロジェクト概要

HN Top30記事の日本語翻訳・コメント要約を毎日自動生成して公開する静的サイト。

- **サービス名**: HN日報
- **ホスティング**: Cloudflare Pages（`docs/` ディレクトリ）
- **自動実行**: GitHub Actions cron UTC 23:00 (= JST 8:00)
- **翻訳/要約**: OpenRouter API（DeepSeek R1）
- **検索**: Pagefind（WASM、日本語 n-gram）

## 実装ステータス

**MVP 完了**（2026-03-26）。全11タスク・21テスト通過済み。

詳細: `docs/plans/2026-03-26-implementation-summary.md`

## ディレクトリ構成

```
scripts/
  fetch_and_generate.py   # メインオーケストレーター
  models.py               # dataclasses (Story, Comment, DailyReport)
  hn_client.py            # HN Firebase API クライアント (async)
  llm_client.py           # OpenRouter API クライアント
  generator.py            # Jinja2 HTML ジェネレーター
  sitemap.py              # sitemap.xml / _redirects / robots.txt
  templates/              # base/archive/index/about/privacy.html
docs/                     # Cloudflare Pages 公開ルート
tests/                    # pytest テスト（21 passed）
.github/workflows/update.yml
```

## 残作業（手動）

1. GitHub Secrets に `OPENROUTER_API_KEY` 登録
2. Cloudflare Pages プロジェクト作成（出力ディレクトリ: `docs`）
3. Actions workflow_dispatch で動作確認
4. 独自ドメイン取得（AdSense申請用、月約170円）

## 重要な設計決定

- **リポジトリ**: private 単体推奨（月消費 ~150min、無料枠 2,000min の 8%）
- **LLMリクエスト**: タイトル一括翻訳 1req + コメント要約 最大30req = 31req/日
- **Jinja2**: `autoescape=True` で XSS 対策済み
- **検索**: Pagefind（`npx pagefind --site docs --output-path docs/pagefind`）
