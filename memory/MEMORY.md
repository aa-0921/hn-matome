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

1. Cloudflare Pages の Production 設定最終確認（branch=`main`, output=`docs`）
2. Actions `workflow_dispatch` 実行結果の最終確認（`docs/archive`, `docs/pagefind`, `docs/sitemap.xml`）
3. Search Console 登録・サイトマップ送信
4. 30日蓄積後の AdSense 申請

## 重要な設計決定

- **リポジトリ**: public/private 分離を採用
  - public: `hn-matome`（workflow + docs）
  - private: `hn-matome-core`（scripts）
  - 必須 secret: `CORE_REPO_TOKEN`, `OPENROUTER_API_KEY`
- **LLMリクエスト**: タイトル一括翻訳 1req + コメント要約 最大30req = 31req/日
- **Jinja2**: `autoescape=True` で XSS 対策済み
- **検索**: Pagefind（`npx pagefind --site docs --output-path docs/pagefind`）
