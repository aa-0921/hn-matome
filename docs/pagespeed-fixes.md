# PageSpeed Insights 改善タスク

診断日時: 2026/03/29 12:07 JST
対象URL: https://hn-matome-2ht.pages.dev/
診断条件: モバイル、低速 4G スロットリング、Lighthouse 13.0.1

## スコア概要

| カテゴリ | スコア |
|---|---|
| パフォーマンス | 98 |
| ユーザー補助 | 95 |
| おすすめの方法 | 100 |
| SEO | 100 |

### Core Web Vitals

| 指標 | 値 | 評価 |
|---|---|---|
| FCP | 1.3秒 | 良好 |
| LCP | 1.3秒 | 良好 |
| TBT | 0ms | 良好 |
| CLS | 0 | 良好 |
| Speed Index | 3.8秒 | 要注意 |

---

## 1. パフォーマンス改善（インサイト）

### [A] DOM サイズを最適化する

- **影響度**: 診断情報（スコアへの直接影響なし）
- **優先度**: 低

| 項目 | 値 |
|---|---|
| 合計要素数 | 488 |
| 最大深度 | 8（`li#story-1 > div.article-body > h2.article-title > a`） |
| 最大子要素数 | 25（`body > main#main-content > section > ol.article-list`） |

**対処方法:**
- 仮想スクロール（Virtual Scroll）の導入を検討する
- または記事表示数の上限設定（例: 初期表示 10件 + 「もっと見る」ボタン）を検討する

---

### [B] LCP の内訳

- **影響度**: 診断情報（スコアへの直接影響なし）
- **優先度**: 中

| 項目 | 値 |
|---|---|
| LCP 要素 | `body > main#main-content > h1.page-title`（HackerNews 日本語まとめ & AI要約） |
| TTFB | 0ms（問題なし） |
| 要素のレンダリング遅延 | **2,300ms**（問題あり） |

**対処方法:**
- `h1.page-title` のレンダリングをブロックしているリソース（CSS・JS）を特定する
- レンダーブロッキングリソースを排除または非同期化する

---

## 2. パフォーマンス改善（診断）

### [C] メインスレッドの長時間タスク

- **影響度**: 診断情報（スコアへの直接影響なし）
- **優先度**: 低

| 項目 | 値 |
|---|---|
| 原因ファイル | `/pagefind/pagefind-ui.js` |
| 開始タイミング | 1217ms |
| 継続時間 | 122ms |
| 関連指標 | TBT（現在 0ms のため問題なし） |

**対処方法:**
- `pagefind-ui.js` を遅延ロード（`defer` 属性または動的 `import()`）する
- 検索機能の初期化をユーザー操作後（検索ボックスフォーカス時など）に遅らせることを検討する

---

## 3. ユーザー補助改善（スコアに影響）

### [D] 背景色と前景色のコントラスト不足

- **影響度**: スコアに影響あり（現在 95/100）
- **優先度**: 高

**問題のある要素:**

| 要素 | 用途 |
|---|---|
| `span#currentDatetime` | 現在時刻表示 |
| `span.meta-comments` | コメント数 |
| `span.meta-time` | 投稿時刻 |
| `span.meta-score` | スコア |
| `li.article-item` | 記事リストアイテム |
| `body` | ページ全体 |

**対処方法:**
- WCAG AA 基準（コントラスト比 4.5:1 以上）を満たすよう文字色または背景色を調整する
- 特に薄いグレー系のメタ情報テキスト（`.meta-comments`、`.meta-time`、`.meta-score`）の色を暗くする
- WebAIM Contrast Checker などで各要素を検証してから変更を適用する

---

### [E] 同一リンクの目的統一

- **影響度**: 情報（スコアへの直接影響なし）
- **優先度**: 低

**問題の概要:**
- 同じ URL を指す複数リンクのテキストやラベルが統一されていない可能性がある

**対処方法:**
- 「元コメントを読む」「元記事を読む」などの重複リンクを整理する
- 同一 URL に複数リンクがある場合は統合するか、`aria-label` で区別する

---

## 4. セキュリティヘッダー（おすすめの方法 / 情報）

- **影響度**: 現在スコア 100（警告のみ、減点なし）
- **優先度**: 中（セキュリティ強化のため対応推奨）

**未設定のセキュリティヘッダー:**

| ヘッダー | 目的 |
|---|---|
| `Content-Security-Policy` (CSP) | XSS 攻撃対策 |
| `Strict-Transport-Security` (HSTS) | HTTPS の強制 |
| `Cross-Origin-Opener-Policy` (COOP) | オリジン分離 |
| `X-Frame-Options` または CSP `frame-ancestors` | クリックジャッキング対策 |
| `Trusted Types` | DOM ベース XSS 対策 |

**対処方法:**
- Cloudflare Pages の `_headers` ファイルでヘッダーを設定する
- 設定例:

```
/*
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Frame-Options: DENY
  Cross-Origin-Opener-Policy: same-origin
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
```

> **注意**: CSP の設定は pagefind などのサードパーティスクリプトの動作に影響する場合があるため、動作確認を行ってから適用すること。

---

## 対応状況

| タスク | 優先度 | 影響度 | 状態 |
|---|---|---|---|
| [A] DOM サイズ最適化 | 低 | なし | 見送り |
| [B] LCP レンダリング遅延解消 | 中 | なし | 一部（間接） |
| [C] pagefind-ui.js 遅延ロード | 低 | なし | 完了 |
| [D] コントラスト不足の修正 | **高** | **スコアに影響** | 完了 |
| [E] 同一リンクの目的統一 | 低 | なし | 完了 |
| セキュリティヘッダー設定 | 中 | なし（推奨） | 完了 |

---

## 実施ログ（対応の追記）

### 2026-03-29 — [D] コントラスト（WCAG AA）

- **変更ファイル**: `docs/assets/style.css`
- **内容**:
  - `:root` の `--text-meta` を `#828282` → `#5a5a5a` に変更（白 / クリーム背景上の小さめ文字で 4.5:1 以上を狙う）。
  - ダークモードの `--text-meta` を `#9a9a9a` → `#b5b5b5` に調整。
  - スコア・順位表示用に `--accent-muted` を追加（ライト `#a84609`、ダーク `#ff9f5c`）。`.article-rank` と `.meta-score` は `var(--accent)` の代わりに `var(--accent-muted)` を使用（オレンジの視認性は保ちつつ AA を意識）。
- **仕様**: 記事件数・レイアウト・文言・リンク先は変更なし。CTA ボタン等の `--accent` は従来どおり。

### 2026-03-29 — [E] 同一 URL のリンク（タイトルと「元記事を読む」）

- **変更ファイル**: `scripts/templates/index.html`, `scripts/templates/archive.html`（`python scripts/fetch_and_generate.py --regenerate-all` で `docs/index.html`・`docs/archive/*.html` を再生成）
- **内容**: `story.url` があるとき、タイトル行の `<a>` と「元記事を読む ↗」が同一 URL になるため、補助技術向けに「元記事」側に `aria-label="{{ 記事タイトル }}"` を付与。表示テキストは従来どおり。タイトルリンクの算出（`story.url or story.hn_url`）も変更なし。

### 2026-03-29 — [C] pagefind-ui.js の遅延読み込み

- **変更ファイル**: `scripts/templates/base.html`（再生成で `docs/*.html` に反映）
- **内容**:
  - `<head>` の同期相当だった `pagefind-ui.js` の `<script defer>` を削除。
  - `DOMContentLoaded` 後に `requestIdleCallback`（未対応ブラウザは `setTimeout` 約 2.5s）で `/pagefind/pagefind-ui.js` を `async` 動的挿入し、読み込み完了時に従来どおり `PagefindUI` を初期化。
  - 検索パネルへの `focusin`、およびモバイルで検索トグルを開いたときは即座に読み込みを開始し、従来どおり入力へフォーカス。
- **仕様**: 検索の挙動・プレースホルダ文言・結果クリック時の `hl` 付与は変更なし。初回表示直後のみ検索 UI の出現がアイドル後まで遅れる場合がある（ワイド画面では従来も検索は空の `#search` からマウントされるため、体感は近い）。

### 2026-03-29 — [A] DOM サイズ最適化（見送り）

- **理由**: 仮想スクロールや「もっと見る」による件数制限は、表示件数・スクロール挙動という**既存仕様の変更**にあたるため実施しない。

### 2026-03-29 — [B] LCP レンダリング遅延（補足）

- **方針**: メインの `style.css` を非同期化すると FOUC（未スタイルの一瞬表示）のリスクがあり、見た目の仕様を変えない方針のため **未実施**。
- **間接対応**: 上記 [C] により初期のメインスレッド長時間タスクを後ろにずらし、h1 周辺のレンダリング競合を緩和しうる。

### 2026-03-29 — セキュリティヘッダー（Cloudflare Pages）

- **追加ファイル**: `docs/_headers`（[Pages の Headers 設定](https://developers.cloudflare.com/pages/configuration/headers/) に従いサイトルートに配置）
- **設定内容**: `Strict-Transport-Security`（2 年・サブドメイン・preload）、`X-Frame-Options: DENY`、`Cross-Origin-Opener-Policy: same-origin`、`Content-Security-Policy`（`default-src 'self'`、インライン script/style は既存の `<script>` / 属性スタイルのため `unsafe-inline` を許可、`img-src` に `https:` を含む外部画像リンク先のプレビュー等に備える）
- **未設定**: ドキュメントにあった `Trusted Types` は、現状のインラインスクリプトと相性が悪いため入れていない。
- **注意**: Google AdSense 等を `base.html` で有効化する場合は、`script-src` / `frame-src` 等に Google ドメインを追加する必要がある。

---

## 本ドキュメントのクローズ（2026-03-29）

**対応状況表に挙げた項目について、フォローアップはすべて完了した。**

| 区分 | 内容 |
|---|---|
| 実装済み | [C] Pagefind 遅延読込、[D] コントラスト、[E] `aria-label`、セキュリティヘッダー（`docs/_headers`。Trusted Types は意図的に未設定） |
| 仕様維持のため未実施（記録済み） | [A] DOM 最適化（仮想スクロール・件数制限は行わない） |
| 縮小・間接対応でクローズ（記録済み） | [B] LCP 内訳のレンダリング遅延 — メイン CSS の非同期化は FOUC 回避のため行わず、[C] による間接的な負荷分散に留めた |

スコア概要の **Speed Index（要注意）** は、本リストでは個別タスク化しておらず、上記パフォーマンス関連対応の範囲に含めて扱う。

再診断や新たな Lighthouse 指摘が出た場合は、別メモまたは本ファイルにセクションを追加して追記すること。
