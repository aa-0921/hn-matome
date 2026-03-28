# HackerNews 日本語まとめ & AI要約 開発メモ

Hacker News のトップ記事とコメントを毎日日本語に翻訳・要約して公開するプロジェクト。

## 現在の運用アーキテクチャ

- 公開リポジトリ `hn-matome`:
  - `.github/workflows/update.yml`
  - `docs/`（公開用成果物）
  - `requirements.txt` など運用補助ファイル
- 非公開リポジトリ `hn-matome-core`:
  - `scripts/`（取得・翻訳・要約・生成ロジック）
- 実行フロー:
  - GitHub Actions（`HackerNews 日本語まとめ & AI要約 毎日更新`）が `hn-matome-core` を checkout
  - `core/scripts/fetch_and_generate.py` 実行で `core/docs` を生成
  - `core/docs` を公開リポジトリの `docs/` に同期
  - `npx pagefind --site docs` を実行
  - `docs/` の差分をコミットして Cloudflare Pages が自動デプロイ

## 進捗

- [x] MVP 実装（取得・翻訳・要約・静的生成）
- [x] コメント要約表示
- [x] アーカイブ・検索（Pagefind）
- [x] モバイル表示対応（基本）
- [x] Cloudflare Pages 公開構成
- [x] public/private 分離運用

## 運用上の必須事項

- GitHub Secrets:
  - `OPENROUTER_API_KEY`
  - `CORE_REPO_TOKEN`
- Cloudflare Pages:
  - Production branch: `main`
  - Build command: 空欄
  - Build output directory: `docs`

## 方針メモ

- README は公開しない（情報漏えい対策）
- プロジェクト情報は本 `MEMO.md` と `memory/MEMORY.md` を一次情報として管理
