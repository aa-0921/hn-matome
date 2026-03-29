# SP（スマートフォン）表示デザイン修正リスト

対象ファイル:
- `docs/assets/style.css`
- `scripts/templates/archive.html`

---

## 優先度: 高

### 1. タップ目標サイズ不足 — `.archive-slot-link`
- **ファイル**: `docs/assets/style.css`
- **問題**: `min-height: 40px` で WCAG 推奨の 44px 未満
- **修正**: `min-height: 44px` に変更、padding を調整

### 2. タップ目標サイズ不足 — `.btn-summary-bulk`
- **ファイル**: `docs/assets/style.css`
- **問題**: `min-height: 40px` で 44px 未満
- **修正**: `min-height: 44px` に変更

### 3. 検索 input の font-size が 16px 未満
- **ファイル**: `docs/assets/style.css`
- **問題**: `font-size: 0.95rem`（≈15.2px）で iOS Safari の自動ズームが発動して UX 悪化
- **修正**: `font-size: 1rem`（=16px）に変更

---

## 優先度: 中

### 4. article-title の長文折り返し対応なし
- **ファイル**: `docs/assets/style.css`
- **問題**: `word-break` / `overflow-wrap` が未指定 → 英語長文がはみ出す可能性
- **修正**: `overflow-wrap: break-word` を追加

### 5. SP 時の article-item gap が狭い
- **ファイル**: `docs/assets/style.css`（`@media max-width: 600px`）
- **問題**: `gap: 4px` でランク番号と記事本体が詰まって見える
- **修正**: `gap: 8px` に変更

### 6. サイトタイトルの SP 時 font-size
- **ファイル**: `docs/assets/style.css`
- **問題**: "HackerNews 日本語まとめ & AI要約" が長く、375px 幅で折り返す可能性
- **修正**: SP 用メディアクエリで `font-size: 0.95rem` に縮小

### 7. ナビゲーションリンクの左右 padding が狭い
- **ファイル**: `docs/assets/style.css`（`@media max-width: 600px`）
- **問題**: `padding: 10px 4px` で左右が 4px のみ → タッチ余白不足
- **修正**: `padding: 10px 8px` に変更

### 8. `.meta-link` のタップ領域が狭い
- **ファイル**: `docs/assets/style.css`
- **問題**: インラインリンクにタップ領域拡張用の padding がない
- **修正**: `padding: 4px 0` を追加

---

## 優先度: 低

### 9. `scroll-padding-top` が SP でも 100px
- **ファイル**: `docs/assets/style.css`
- **問題**: SP 画面高さの 25-30% をスクロール padding が占める
- **修正**: SP 用メディアクエリで `scroll-padding-top: 60px` に削減

### 10. `.archive-date-label` の min-width
- **ファイル**: `docs/assets/style.css`
- **問題**: `min-width: 120px` で SP（375px）ではスロットリンク領域を圧迫
- **修正**: SP 用メディアクエリで `min-width: 100px` に削減

### 11. date-nav-label の日付テキストが長い
- **ファイル**: `docs/assets/style.css`
- **問題**: "2026年3月29日（07:00）" が長く SP で複数行折り返し
- **修正**: SP 時に `white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 120px;` を追加
