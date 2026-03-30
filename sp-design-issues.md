# SP（スマホ）表示 デザイン修正リスト

## 1. ヘッダー検索ボタンの虫眼鏡アイコンが小さい

- 場所: `scripts/templates/base.html` の `.header-search-toggle` ボタン（`⌕` 文字）
- 現状: font-size が body から継承（SP では 15px）。アイコンが視認しにくい
- 修正: `docs/assets/style.css` の `.header-search-toggle` に `font-size: 1.4rem` を追加
- ステータス: 修正済み（2026-03-30）

## 2. メタ行（件数・投稿時刻・リンク）が複数行に折り返される

- 場所: `docs/assets/style.css` の `.article-meta`
- 現状: `flex-wrap: wrap` + `gap: 10px` により SP 画面幅でアイテムが折り返す
- 修正: `@media (max-width: 600px)` 内で `.article-meta` に以下を追加
  - `flex-wrap: nowrap`
  - `overflow-x: auto`
  - `-webkit-overflow-scrolling: touch`
  - `gap: 8px`
- ステータス: 修正済み（2026-03-30）
