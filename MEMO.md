# HackerNews 日本語まとめ & AI要約

Hacker News のトップ記事・コメントを毎日日本語に翻訳・AI要約して公開するサービス。

## コンセプト

- HN のトップ記事タイトルを日本語翻訳
- 上位コメント（英語コミュニティの反応）を AI で日本語要約
- 毎日 GitHub Actions が自動実行 → 静的 HTML → GitHub Pages で公開
- 運用コスト: ドメインなし 0円 / ドメインあり 月約170円

## 差別化ポイント

1. **コメント・議論の日本語要約**（最大の差別化 — HN API で完結）
2. **アーカイブ・検索** （静的 HTML の蓄積による）
3. **モバイル最適化**

## 技術スタック（予定）

| コンポーネント | 技術 |
|---|---|
| データ取得 | HN 公式 Firebase API（無料・無制限） |
| 翻訳・要約 | OpenRouter 無料枠（DeepSeek R1 等） |
| 自動実行 | GitHub Actions cron |
| ホスティング | GitHub Pages（静的 HTML） |

## ドキュメント

| ファイル | 内容 |
|---|---|
| `海外テックニュース日本語翻訳サービス調査.md` | 競合調査・実現可能性・差別化評価 |
| `サービス設計書.md` | アーキテクチャ・MVP仕様 |
| `GitHub_Actions定期実行_収益化アイデア集.md` | GitHub Actions cron 活用事例 |
| `GitHub_Actions_cron収益化アイデア調査.md` | インフラ調査 |

## 開発フェーズ

- [ ] MVP: HN API 取得 → 翻訳 → 静的 HTML → GitHub Pages
- [ ] コメント要約追加
- [ ] アーカイブ・検索
- [ ] モバイル最適化 / PWA
