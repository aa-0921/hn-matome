# UI/UX 改善点レビュー

作成日: 2026-03-29  
対象: Cloudflare Pages 静的サイト（`scripts/templates/` Jinja2 テンプレート群）

**実装反映日: 2026-03-29**（**追補: 同日** — OGP 用 PNG、`aria-expanded` 同期、フッター AI 説明を追加）— 以下の項目は `docs/assets/style.css`・`scripts/templates/*`・`scripts/generator.py` 等に反映済み。静的 HTML は `python scripts/fetch_and_generate.py --regenerate-all`（`PYTHONPATH=.`）で再生成。

---

## ■ 未対応はあるか？（先に読む）

| 質問 | 答え |
|------|------|
| このレビューの **1-1〜8-2 は未対応のままか？** | **いいえ。すべて対応済み（済）。** 下の「実装サマリ」表のとおり。 |
| **「未対応」に近いものは何か？** | 次の **2 種類** に分かれる。① **任意でまだやっていない改善**（下表 B）② **やらない／別手段にしたこと**（下表 C。項目の未実装ではない）。 |

### A. 計画項目（1-1〜8-2）としての未対応

| 状態 | 件数 |
|------|------|
| **未対応** | **0**（該当なし） |

### B. 任意・未着手（必須ではないが、やればさらに良くなるもの）

| ID | 内容 | いまの状況 |
|----|------|------------|
| （任意） | 計画 **4-4** の「**または About ページに説明追加**」 | **未実施。** スロット説明は `title` ツールチップとトップの hn-info で補足済み。長文を About に載せる作業はしていない。 |
| （任意） | 計画 **3-3** の「WebAIM Contrast Checker で確認」 | **数値の記録は未実施。** 訪問済み色は CSS で指定済み。監査として比率をドキュメントに残すのは今後でも可。 |

### C. 制約・非採用（「項目未対応」ではなく方針・運用）

| 内容 | 理由の要約 |
|------|------------|
| SVG を **Cairo 系で自動ラスタ化** | libcairo 非導入環境で失敗しやすい → **Pillow 再描画** `scripts/generate_og_png.py` にした。 |
| **CI だけ**で OG PNG を必ず再生成 | 日本語フォントが無いと **文字化け** しうる → **ローカル等で生成した PNG をコミット**する運用を推奨。 |
| **PNG と SVG の二重管理** | OGP は PNG、原本は `og-image.svg`。SVG を直したら **手順として** `generate_og_png.py` を再実行する必要あり。 |
| `<details>` に **追加の `role`** | ネイティブセマンティクスと競合しうる → **付与しない**（`aria-label` / `aria-expanded` で補足）。 |

---

## 実装サマリ（一覧）

| 項目 | 状態 | 主な変更箇所 |
|------|------|----------------|
| 1-1 | **済** | `style.css` — `a/button/summary/input` の `:focus-visible`、ヘッダー内は白アウトライン |
| 1-2 | **済** | `base.html` — `.skip-link` + `main#main-content` |
| 1-3 | **済** | 上記に加え `base.html` — 全 `<details>` の `<summary>` に `aria-expanded` を JS で開閉同期 |
| 1-4 | **済** | 1-1 と同時（`summary:focus-visible`） |
| 2-1 | **済** | `style.css` — `@media (max-width: 900px)` / `768px` / `600px` |
| 2-2 | **済** | `base.html` + `style.css` — 600px 以下でハンバーガー・検索トグル |
| 2-3 | **済** | `style.css` — `.date-nav-link` 等で `min-height: 44px`、padding 拡大 |
| 3-1 | **済** | `base.html` — `formatRelativeTime()` を日本語（たった今・分前・時間前・日前） |
| 3-2 | **済** | `style.css` — `.summary-preview` に左ボーダー・`font-size: 0.9em` 等 |
| 3-3 | **済** | `style.css` — CSS 変数 `--link-visited`（ライト `#5C3D8B`、ダーク調整） |
| 4-1 | **済** | `base.html` ナビ + `archive_index.html` 新規 + `generate_archive_index` + サイトマップ |
| 4-2 | **済** | `archive.html` + `slug_nav_label` フィルター — 前後日付ラベル・中央に現在 |
| 4-3 | **済** | `base.html` — `.back-to-top`（スクロール約 400px 以上で表示） |
| 4-4 | **済** | `fetch-slot`・`archive-slot-link` に `title`（取得時刻の説明） |
| 5-1 | **済** | `base.html` — `sessionStorage`（キー `hnMatomeDetailState`、パス + `story-N`） |
| 5-2 | **済** | `index.html` / `archive.html` — 「全て開く」「全て閉じる」ツールバー |
| 5-3 | **済** | `style.css` — `.article-title a[target="_blank"]:not(.meta-link)::after`（↗） |
| 5-4 | **済** | `style.css` — `.site-header` を `sticky` + `backdrop-filter` |
| 6-1 | **済** | `style.css` — `:root` 変数 + `prefers-color-scheme: dark` |
| 7-1 | **済** | `base.html` — Pagefind CSS を `preload` + `onload`、`<noscript>` でフォールバック |
| 7-2 | **済** | `docs/assets/og-image.png`（1200×630）を追加し `og:image` / Twitter を PNG に変更。`og:image:type` 追加。再生成は `scripts/generate_og_png.py`（要 Pillow） |
| 8-1 | **済** | 記事 `<summary>` の `title` に加え、フッターに `.footer-ai-note` で同一趣旨の説明文を追加 |
| 8-2 | **済** | `base.html` フッター — About / プライバシー / アーカイブ |

補足: `_redirects` に `/archive/ → /archive/index.html` を追加。ナビのリンクは `/archive/index.html`（計画案の `/archive/` もリダイレクトで到達可）。

---

## 影響度・コスト凡例

- 影響度: 高 / 中 / 低
- 実装コスト: 小（CSS/HTML のみ） / 中（JS追加） / 大（設計変更・ビルド変更）

---

## 1. アクセシビリティ

### 1-1. `:focus-visible` が検索入力以外に未設定

- **根拠**: `base.html` の CSS で `input[type="search"]:focus` のみ focus スタイルが定義されており、ナビリンク・`<details>` 要素・外部リンク等にはキーボードフォーカスの視覚指示がない。
- **影響度**: 高（WCAG 2.4.7 準拠）
- **実装コスト**: 小
- **対応案**: 全インタラクティブ要素に `:focus-visible { outline: 2px solid #ff6600; outline-offset: 2px; }` を一括適用。
- **対応状況: 済**
- **実装内容**: `docs/assets/style.css` で `a, button, summary, input, textarea, select` に `:focus-visible` を定義（`--focus-ring` 使用）。`.site-header` 内のリンク・ボタンは視認性のため `outline-color: #fff`。

### 1-2. スキップナビゲーションリンクなし

- **根拠**: `base.html` の `<body>` 直下にスキップリンクが存在しない。スクリーンリーダー・キーボードユーザーがメインコンテンツへ直接ジャンプできない。
- **影響度**: 高（WCAG 2.4.1）
- **実装コスト**: 小
- **対応案**: `<body>` 先頭に `<a class="skip-link" href="#main-content">コンテンツへスキップ</a>` を追加し、平常時は `position: absolute; left: -9999px;` で非表示、フォーカス時に表示。
- **対応状況: 済**
- **実装内容**: `scripts/templates/base.html` にスキップリンクを配置。`main` に `id="main-content"`。`.skip-link:focus` で画面上部に固定表示するスタイルを `style.css` に追加。

### 1-3. `<details>` 要素に ARIA 属性未設定

- **根拠**: 各記事の要約展開に `<details>/<summary>` を使用しているが、`role` や `aria-expanded` の明示的な付与がない。一部スクリーンリーダーで状態を正しく伝えない場合がある。
- **影響度**: 中
- **実装コスト**: 小
- **対応案**: `<summary>` に `aria-label="[記事タイトル]の要約を展開"` を付与。または JS で `aria-expanded` を同期。
- **対応状況: 済**
- **実装内容**: 記事の `<summary>` に `aria-label="{{ タイトル }}のコメント要約を展開"`（アーカイブは「全文」表記）。`hn-info-box` の `<summary>` に「…の説明を展開」の `aria-label`。**追補**: `base.html` の JS で `document` の `toggle`（capture）により、対象 `<details>` の子 `<summary>` に `aria-expanded="true"|"false"` を同期。初期表示・`sessionStorage` 復元後・一括開閉・`hl` ハイライトで開いた直後も `refreshDetailsAriaExpanded()` で整合。**補足**: ネイティブ `<details>` だけでも支援技術は状態を扱えることが多いが、計画案の「明示」に合わせて冗長でも付与している。

### 1-4. キーボード操作で `article-summary` の開閉が操作しにくい

- **根拠**: `<details>` は `Enter` で開閉できるが、フォーカスリングが未設定のため現在フォーカス位置が不明。
- **影響度**: 中
- **実装コスト**: 小（1-1 の対応と同時）
- **対応状況: 済**
- **実装内容**: 1-1 の `summary:focus-visible` で対応。

---

## 2. モバイル / レスポンシブ

### 2-1. ブレークポイントが 600px 1点のみ

- **根拠**: `@media (max-width: 600px)` の1段階のみ。768px（タブレット）やそれ以上の中間サイズで崩れの可能性がある。
- **影響度**: 中
- **実装コスト**: 小〜中
- **対応案**: 768px を追加ブレークポイントとして導入。カード幅・フォントサイズを3段階で調整。
- **対応状況: 済**
- **実装内容**: `max-width: 900px`（本文・見出し・コンテナ padding）、`768px`（記事カード・タイトル）、既存 `600px` を維持しつつモバイルナビと併用。

### 2-2. ヘッダーでロゴ・ナビ・検索が縦積みで密集

- **根拠**: モバイルビューで `header` 内の `.site-title`・`nav`・`.search-box` が縦に並び、スクロール前に本文が見えにくい。
- **影響度**: 中
- **実装コスト**: 中
- **対応案**: ハンバーガーメニュー or 検索をアイコンボタン化してヘッダー高さを削減。
- **対応状況: 済**
- **実装内容**: `max-width: 600px` でナビを折りたたみ（`.nav-menu-toggle`）、検索行をデフォルト非表示にし `.header-search-toggle` で開閉。`#site-header` に `is-nav-open` / `is-search-open` を付与する JS を `base.html` に追加。`min-width: 601px` で従来の横並びナビに復帰。

### 2-3. date-nav の「前/次」リンクのタップ領域が小さい

- **根拠**: `date-nav` の `<a>` 要素の padding が小さく、モバイルでのタップターゲットが Apple HIG 推奨 44×44px を下回る可能性がある。
- **影響度**: 高（モバイルユーザー比率が高いと仮定）
- **実装コスト**: 小
- **対応案**: `date-nav a { padding: 10px 16px; min-height: 44px; display: inline-flex; align-items: center; }` に変更。
- **対応状況: 済**
- **実装内容**: `.date-nav-link` に `padding: 10px 16px`、`min-height: 44px`、`inline-flex`。中央の `.date-nav-current` も同様に高さを確保。狭い画面では `.date-nav-links` を縦積みに変更。

---

## 3. タイポグラフィ・可読性

### 3-1. 相対時刻が英語（"minutes ago" 等）

- **根拠**: `base.html` の JS `timeAgo()` 関数が英語テキストを返す（"just now", "minutes ago", "hours ago" 等）。サイト全体が日本語なのに時刻表示だけ英語で一貫性がない。
- **影響度**: 中（UX 一貫性・ブランド品質）
- **実装コスト**: 小
- **対応案**: `timeAgo()` の返り値を日本語化（"たった今", "X分前", "X時間前", "X日前"）。
- **対応状況: 済**
- **実装内容**: `formatRelativeTime()` を「たった今」「N分前」「N時間前」「N日前」に変更（関数名は `formatRelativeTime` のまま）。

### 3-2. `.summary-preview` に専用スタイルなし

- **根拠**: アーカイブページの記事プレビュー（`.summary-preview`）が独自スタイルを持たず、通常の `.article-summary p` と区別できない。コンテンツ階層が曖昧。
- **影響度**: 低
- **実装コスト**: 小
- **対応案**: `.summary-preview { font-size: 0.9em; color: #555; border-left: 3px solid #e0d9d0; padding-left: 8px; }` 等で視覚的に区分。
- **対応状況: 済**
- **実装内容**: `.summary-preview` に `font-size: 0.9em`、左ボーダー（`color-mix` で `--text-meta` 系）、`padding-left`、`line-height` を指定。ダークモードでは変数経由で追随。

### 3-3. 訪問済みリンク色のコントラスト不足の可能性

- **根拠**: 訪問済みリンクがブラウザデフォルトの紫（`#551A8B`）になる場合、背景 `#F6F6EF` との明度差が WCAG AA 基準（4.5:1）を下回る可能性がある。
- **影響度**: 中（WCAG 1.4.3）
- **実装コスト**: 小
- **対応案**: `a:visited { color: #7B5EA7; }` 等コントラスト比を計算して設定（確認ツール: WebAIM Contrast Checker）。
- **対応状況: 済**
- **実装内容**: `.article-title a:visited` を `--link-visited`（ライト `#5C3D8B`）に統一。ダーク時は `--link-visited: #c9a8e8`。フッター訪問済みは `color-mix` で微調整。
- **未対応（任意）**: 対応案の **WebAIM 等でのコントラスト比の記録** はドキュメント化していない（色指定のみ実施）。

---

## 4. ナビゲーション・情報設計

### 4-1. グローバルナビにアーカイブリンクが存在しない

- **根拠**: `base.html` のヘッダーナビは `About` のみ。アーカイブページへの導線がなく、初訪問ユーザーがアーカイブを発見しにくい。
- **影響度**: 高（SEO・直帰率にも影響）
- **実装コスト**: 小
- **対応案**: ナビに `<a href="/archive/">アーカイブ</a>` を追加。
- **対応状況: 済**
- **実装内容**: ナビに `/archive/index.html` を追加。`scripts/templates/archive_index.html` と `HTMLGenerator.generate_archive_index()` を新設。`fetch_and_generate.py` から一覧を生成。`sitemap.xml` に `archive/index.html` を追加。`_redirects` に `/archive/ /archive/index.html 200`。トップのアーカイブ欄に一覧ページへの一文を追加。

### 4-2. date-nav に日付テキストがなく文脈不明

- **根拠**: `date-nav` に「前へ」「次へ」のみ表示され、現在日付と前後の日付テキストが見えない。どの日付に移動するか分からない。
- **影響度**: 中
- **実装コスト**: 小〜中
- **対応案**: `← 2026-03-28 | 2026-03-29 | 2026-03-30 →` のように現在日付と隣接日付を表示。
- **対応状況: 済**
- **実装内容**: `generator.py` に `_slug_nav_label` / フィルター `slug_nav_label` を追加。`archive.html` の `date-nav` を「前リンク＋ラベル | 現在（`aria-current="page"`）| 次リンク＋ラベル」構成に変更。

### 4-3. 長ページに「ページ上部へ戻る」ボタンなし

- **根拠**: 30記事分のコンテンツが縦に並ぶため、スクロール後に上部検索・ナビへ戻る手段がない。
- **影響度**: 中
- **実装コスト**: 小
- **対応案**: `position: fixed; bottom: 20px; right: 20px;` に戻るボタンを配置。スクロール量が一定以上のとき表示。
- **対応状況: 済**
- **実装内容**: `#backToTop` ボタン（`aria-label="ページ上部へ戻る"`）。`scrollY > 400` で `.is-visible`。`style.css` で `position: fixed; bottom: 20px; right: 20px`。

### 4-4. アーカイブのスロットラベルが初見に分かりにくい

- **根拠**: "07:00取得", "12:00取得", "23:00取得" というラベルが何を意味するか説明がない。「HN トップ記事を取得した時刻」という背景知識が必要。
- **影響度**: 低
- **実装コスト**: 小
- **対応案**: スロットラベルに `title="毎日この時刻にHackerNewsのトップ記事を取得しています"` 等の tooltip を付与。または About ページに説明追加。
- **対応状況: 済**
- **実装内容**: `.fetch-slot`（index / archive の見出し）、`.archive-slot-link`（index・アーカイブ一覧・他日報リンク）、`archive_index.html` のスロットリンクに、文言を少し具体化した `title` を付与（「毎日この時刻（JST）に Hacker News の…」）。
- **未対応（任意）**: 対応案の **「または About ページに説明追加」** は未実施。上記ツールチップ等で代替。About に専用段落を足す場合は別タスク。

---

## 5. インタラクション・UX

### 5-1. ページ遷移で `<details>` の展開状態がリセット

- **根拠**: `<details>` の open/close 状態は DOM に紐付くため、ページ遷移（前後の日付移動等）でリセットされる。
- **影響度**: 低（静的サイトの制約の範囲内）
- **実装コスト**: 中（sessionStorage での状態保存）
- **対応案**: 各 `<details>` に一意の `id` を付与し、`sessionStorage` で open 状態を保持。ページロード時に復元。
- **対応状況: 済**
- **実装内容**: 記事は既存の `.article-item#story-N` をキーに、`sessionStorage` キー `hnMatomeDetailState` で `pathname` ごとのマップを保存。`toggle` イベントで更新、ロード時に `.article-summary` の `open` を復元。同一タブのセッション内・同一パス単位で有効。

### 5-2. 「全要約を開く/閉じる」一括トグルボタンなし

- **根拠**: 30記事の要約を個別に開く必要があり、全文を確認したいユーザーの操作コストが高い。
- **影響度**: 中
- **実装コスト**: 小（JS 数行）
- **対応案**: ページ上部に「全て開く / 全て閉じる」トグルボタンを設置。`document.querySelectorAll('details')` で一括制御。
- **対応状況: 済**
- **実装内容**: トップ（最新記事見出し直後）と各アーカイブページで `.summary-toolbar` に「全て開く」「全て閉じる」。`querySelectorAll('details.article-summary')` で制御し、`sessionStorage` の状態も同期。

### 5-3. 外部リンクに新規タブで開く視覚的示唆なし

- **根拠**: HN リンク・元記事リンクが `target="_blank"` で開くが、アイコン等の視覚的インジケーターがない。WCAG 3.2.5 の観点でも事前告知が望ましい。
- **影響度**: 低
- **実装コスト**: 小
- **対応案**: `a[target="_blank"]::after { content: " ↗"; font-size: 0.75em; }` で外部リンクアイコンを付与。
- **対応状況: 済**
- **実装内容**: `.article-title a[target="_blank"]:not(.meta-link)::after { content: " ↗"; }`。`.meta-link` は文言に既に ↗ があるため除外。

### 5-4. スクロール後に検索ボックスが視界から外れる

- **根拠**: 検索ボックスがヘッダー内に配置されており、スクロール後は画面外に隠れる。検索したい場合は上部まで戻る必要がある。
- **影響度**: 中
- **実装コスト**: 中（sticky ヘッダー化）
- **対応案**: `header { position: sticky; top: 0; z-index: 100; }` で sticky ヘッダー化。背景の半透明化（`backdrop-filter: blur`）を合わせて検討。
- **対応状況: 済**
- **実装内容**: `.site-header` に `position: sticky; top: 0; z-index: 100`、`backdrop-filter` / `-webkit-backdrop-filter`、`background: var(--header-bg)`（半透明）。

---

## 6. ダークモード

### 6-1. `prefers-color-scheme: dark` 未対応

- **根拠**: ベージュ背景（`#F6F6EF`）・白カード（`#fff`）固定。夜間・ダークモード環境で画面が眩しく、目の疲労につながる。
- **影響度**: 中（ユーザー体験・滞在時間に影響）
- **実装コスト**: 中（CSS variables 化が必要）
- **対応案**:
  1. カラーを CSS custom properties（`--bg`, `--card-bg`, `--text` 等）に置き換え
  2. `@media (prefers-color-scheme: dark)` で上書き定義
  3. ダーク時のカラー例: 背景 `#1a1a1a`、カード `#252525`、テキスト `#e0e0e0`、アクセント `#ff6600`
- **対応状況: 済**
- **実装内容**: `style.css` で `:root` に `--bg`, `--card-bg`, `--text`, `--accent`, `--summary-bg` 等を定義し、`@media (prefers-color-scheme: dark)` でダーク用に上書き（背景・カード・リンク・ヘッダー・フッター・Pagefind 結果エリア等）。

---

## 7. パフォーマンス体感

### 7-1. Pagefind CSS が `<head>` で同期ロード

- **根拠**: `base.html` の `<head>` に `<link rel="stylesheet" href="/pagefind/pagefind-ui.css">` が同期で記述されており、Pagefind CSS がレンダリングをブロックする可能性がある。
- **影響度**: 低〜中（LCP/FCP に軽微な影響）
- **実装コスト**: 小
- **対応案**: `<link rel="preload" as="style" onload="this.rel='stylesheet'">` パターンでノンブロッキングロードに変更、または `media="print"` trick を使用。
- **対応状況: 済**
- **実装内容**: `preload` + `onload="this.onload=null;this.rel='stylesheet'"` と `<noscript>` 内の通常 `link` を併用。

### 7-2. `og-image.svg` の存在確認が必要

- **根拠**: `base.html` の `<meta property="og:image">` で `/og-image.svg` が参照されているが、`docs/` に実ファイルが存在するか未確認。OGP 画像が欠落すると SNS シェア時に画像なしになる。
- **影響度**: 中（SNS 流入に影響）
- **実装コスト**: 小（ファイル作成のみ）
- **対応案**: `docs/og-image.svg` の存在を確認。未存在の場合はシンプルな OGP 画像（1200×630）を作成。PNG 形式が望ましい（SVG は一部 SNS で未対応）。
- **対応状況: 済**
- **実装内容**: `docs/assets/og-image.png`（1200×630）を追加。`og:image` / `twitter:image` / アーカイブ JSON-LD の `image` を `…/og-image.png` に変更し、`og:image:type` に `image/png` を追加。**`og-image.svg` はデザイン原本としてリポジトリに残置**（サイト表示用ではなくメタは PNG 優先）。
- **対応しなかった代替（技術理由）**: **SVG をそのままラスタライズするパイプライン**（例: `cairosvg`）は **システムの libcairo** が無い環境（多くのローカル macOS / 最小 CI）では動かないため、本リポジトリの標準手順には組み込まない。代わりに **Pillow で同色・同文言を再描画**する `scripts/generate_og_png.py` を用意した（`pip install pillow` が必要）。

---

## 8. コンテンツ・コピー

### 8-1. 「AIコメント要約」ラベルの説明が薄い

- **根拠**: 各記事に「AIコメント要約」というラベルが表示されるが、何のAIが・どのコメントを・どう要約したかの説明がない。信頼性・透明性に課題。
- **影響度**: 低〜中（ユーザーの信頼形成）
- **実装コスト**: 小
- **対応案**: ラベルに `title="HackerNewsの上位コメントをAI（DeepSeek）で日本語要約しています"` を付与。またはフッターに簡単な説明を追加。
- **対応状況: 済**
- **実装内容**: 記事 `<summary>` に `title="Hacker News の上位コメントを AI（DeepSeek）で日本語要約しています"`。**追補**: フッターに `.footer-ai-note` で同趣旨の一文を常時表示（各記事にホバーしなくても読める）。

### 8-2. About ページへの導線がヘッダーナビのみ

- **根拠**: フッターに About リンクが存在しない。フッターまでスクロールしたユーザーが About にアクセスしにくい。
- **影響度**: 低
- **実装コスト**: 小
- **対応案**: フッターに `About | プライバシーポリシー | アーカイブ` のリンク群を追加。
- **対応状況: 済**
- **実装内容**: `base.html` フッターに `.footer-links` で About・プライバシー・アーカイブ（区切り `|`）。既存の注意書き段落は維持。

---

## 優先実装順（推奨）

| 優先度 | 項目 | 根拠 | 状態 |
|--------|------|------|------|
| 1 | 4-1: ナビにアーカイブリンク追加 | コスト最小・SEO 改善効果大 | **済** |
| 2 | 2-3: date-nav タップ領域拡大 | モバイルユーザー直撃・コスト小 | **済** |
| 3 | 3-1: 相対時刻の日本語化 | 品質一貫性・コスト小 | **済** |
| 4 | 1-1 + 1-2: focus-visible + スキップリンク | アクセシビリティ基礎・コスト小 | **済** |
| 5 | 5-2: 全要約一括トグル | UX 改善・コスト小 | **済** |
| 6 | 5-4: sticky ヘッダー | 検索利便性・コスト中 | **済** |
| 7 | 6-1: ダークモード対応 | ユーザー要望多い・コスト中 | **済** |
| 8 | 7-2: og-image.svg 確認・作成 | SNS 流入・コスト小 | **済**（PNG 追加・メタ差し替え済） |

---

## 未対応・制約・運用（対応できない／難しい点の整理）

計画の**項目として未着手のものはない**（いずれも「済」または「済＋補足」）。以下は **技術・運用上の制約** と **今後の注意**。

| 内容 | 理由・推奨運用 |
|------|----------------|
| **SVG→PNG の完全自動（Cairo 系）** | `cairosvg` 等は **ネイティブ Cairo ライブラリ** が必須で、環境によってはインストール困難。採用せず、Pillow による再描画にした。 |
| **CI での `generate_og_png.py` 必須化** | Linux ランナーに **日本語フォントが無い** と、スクリプトはビットマップフォールバックになり **日本語が正しく描画されない** 可能性がある。**推奨**: 見た目を変えるときはローカル等でフォントが揃った環境で PNG を生成し、**生成物をコミット**する。 |
| **PNG と SVG の二重管理** | OGP は PNG、原本デザインは SVG の **二ファイル** になる。SVG を直したら **手順として** `python scripts/generate_og_png.py` を再実行するか、手動で PNG を揃える。 |
| **`details` に冗長な `role` 付与** | ネイティブ `<details>` に追加の `role` を付けると、支援技術との解釈が競合する恐れがあるため **付与していない**（`aria-label` / `aria-expanded` で補足）。 |

---

## その他メモ（実装時の付随修正）

- **`archive.html`**: `元記事` リンクが空テキストになっていた箇所を「元記事を読む ↗」に修正。
- **`base.html` の JS**: 相対時刻は `#search` の有無に依存せず常に適用。検索・`hl` ハイライトのみ `#search` 必須。
