# SEO改善計画 - HN日報

作成日: 2026-03-27
対象URL: https://hn-matome-2ht.pages.dev/

---

## 使用推奨スキル

| スキル名 | 用途 | 実行タイミング |
|---|---|---|
| `seo-audit` | SEO診断・問題洗い出し | 改善実装前後の検証 |
| `audit-website` | 230+ルールの総合監査（SEO/パフォーマンス/セキュリティ/コンテンツ） | 実装完了後の最終確認 |
| `ui-design-review` | UI/UXがクロールしやすさ・CTRに影響する部分の確認 | デザイン変更時 |

使い方例:
```
/seo-audit
/audit-website
```

---

## 現状の実装済み項目（良い点）

- [x] `<html lang="ja">` 言語宣言
- [x] `<meta charset>` / `<meta viewport>`
- [x] `<title>` / `<meta name="description">` (全ページ)
- [x] `<meta name="robots" content="index, follow">`
- [x] canonical URL (全ページ)
- [x] OG タグ (og:type / title / description / url / site_name / locale)
- [x] `<meta name="twitter:card">`
- [x] JSON-LD: `WebSite` (index) / `NewsArticle` (archive)
- [x] sitemap.xml + lastmod
- [x] robots.txt (Sitemap ディレクティブ付き)
- [x] Google Search Console 認証ファイル
- [x] 日付ナビゲーション (prev/next)

---

## 改善が必要な項目

### 優先度: 高（クロール・インデックスに直結）

- [x] **about.html の canonical URL が誤っている** ← 2026-03-27 修正済み
  `scripts/templates/about.html` に `{% block canonical %}` を追加

- [x] **favicon** 未設定 ← 2026-03-27 対応済み
  `docs/assets/favicon.svg`（HNオレンジ #ff6600）を作成、`base.html` に `<link rel="icon">` 追加

- [x] **OG画像 (og:image)** 未設定 ← 2026-03-27 対応済み
  `docs/assets/og-image.svg`（1200x630）を作成、`base.html` に og:image / og:image:width / og:image:height 追加

- [x] **twitter:title / twitter:description / twitter:image** 未設定 ← 2026-03-27 対応済み
  `base.html` に twitter:title / twitter:description / twitter:image 追加。
  twitter:card を `summary` → `summary_large_image` に変更

- [x] **archive ページの og:description がデフォルト文言のまま** ← 2026-03-27 修正済み
  `scripts/templates/archive.html` に `{% block og_description %}` を追加

- [x] **sitemap.xml に privacy.html が未掲載** ← 2026-03-27 対応済み
  `scripts/sitemap.py` に `add_url(privacy.html, "monthly", "0.2")` を追加

- [x] **`<details>` タグ内のコメント要約がインデックスされない可能性** ← 2026-03-27 対応済み
  `archive.html` で `summary_ja` の冒頭1文を `<p class="summary-preview">` として `<details>` 外に出力

### 優先度: 中（構造化データ・リッチリザルト）

- [ ] **JSON-LD: WebSite に SearchAction を追加**（サイトリンク検索ボックス、未対応）
  ```json
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://hn-matome-2ht.pages.dev/?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
  ```

- [x] **JSON-LD: NewsArticle の publisher に logo を追加** ← 2026-03-27 対応済み
  `favicon.svg` を logo URL として使用

- [x] **JSON-LD: BreadcrumbList を archive ページに追加** ← 2026-03-27 対応済み
  `archive.html` の `{% block head_extra %}` に BreadcrumbList JSON-LD を追加

- [ ] **JSON-LD: NewsArticle の `dateModified` を再収集時に更新する**
  現状は `datePublished` と同値。スロット更新時に正しい時刻を反映する（未対応）

- [x] **JSON-LD: NewsArticle に `image` フィールドを追加** ← 2026-03-27 対応済み
  `og-image.svg` を image URL として設定

### 優先度: 中（パフォーマンス・Core Web Vitals）

- [ ] **CSS のプリロード**
  `<link rel="preload" href="/assets/style.css" as="style">` を追加
  レンダーブロッキングを軽減（未対応）

- [x] **pagefind-ui.js の遅延ロード** ← 2026-03-27 対応済み
  `base.html` の pagefind-ui.js script タグに `defer` を追加

- [ ] **画像の `width` / `height` 属性指定**
  OG画像・ロゴ等を追加する際は必ずサイズ指定でCLS(累積レイアウトシフト)を防ぐ（SVGのためviewBox指定済み）

### 優先度: 低（長期的な評価向上）

- [x] **RSS / Atom フィード** ← 2026-03-27 対応済み
  `generator.generate_feed()` を追加。次回実行時に `docs/feed.xml` 自動生成。
  `base.html` に `<link rel="alternate" type="application/rss+xml">` 追加済み

- [ ] **カスタムドメイン取得**
  `hn-matome-2ht.pages.dev` はCFのサブドメイン。独自ドメインで信頼性・ブランド力向上
  例: `hn-daily.jp` / `hnmatome.com` など

- [ ] **内部リンクの強化**
  各アーカイブページの末尾に「他の日付を見る」リンクを追加
  → ページランクの均一な分散

- [ ] **`hreflang` 不要**（日本語のみのサイトのため対応不要）

- [ ] **Google Search Console のサイトマップ送信確認**（手動作業）
  → すでに `MEMO.md` に記載済みの残作業

---

## 優先実装順序（推奨）

※ 2026-03-27 の `/seo-audit` 実行結果を踏まえて更新。全11タスク完了済み（2026-03-27）

| 順 | タスク | 対象ファイル | 状態 |
|----|--------|-------------|------|
| 1 | about.html の canonical バグ修正 | `templates/about.html` | 完了 |
| 2 | pagefind-ui.js に `defer` 追加 | `templates/base.html` | 完了 |
| 3 | archive の og:description ブロック追加 | `templates/archive.html` | 完了 |
| 4 | sitemap.xml に privacy.html 追加 | `scripts/sitemap.py` | 完了 |
| 5 | favicon 作成・設定（SVG） | `docs/assets/favicon.svg` + `base.html` | 完了 |
| 6 | OG画像作成・全ページ og:image 設定（SVG 1200x630） | `docs/assets/og-image.svg` + `base.html` | 完了 |
| 7 | Twitter meta タグ補完（summary_large_image） | `templates/base.html` | 完了 |
| 8 | JSON-LD: image + publisher logo 追加 | `templates/archive.html` | 完了 |
| 9 | JSON-LD: BreadcrumbList 追加 | `templates/archive.html` | 完了 |
| 10 | `<details>` 外への要約プレビュー出力 | `templates/archive.html` | 完了 |
| 11 | RSS フィード生成 | `scripts/generator.py` + `fetch_and_generate.py` | 完了 |

### 残課題（未対応）

| タスク | 理由 |
|--------|------|
| JSON-LD: NewsArticle の `dateModified` をスロット更新時に正しい時刻に更新 | 設計変更が必要 |
| JSON-LD: WebSite に SearchAction を追加 | Pagefind の URL 構造と要検討 |
| CSS のプリロード | 効果が小さいため後回し |
| カスタムドメイン取得 | 手動作業・費用が発生 |
| 内部リンク強化（アーカイブページ末尾に「他の日付を見る」リンク） | 低優先度 |
| Google Search Console のサイトマップ送信確認 | 手動作業 |

---

## SEOスコア確認方法

### PageSpeed Insights
1. `https://pagespeed.web.dev/` にアクセス
2. `https://hn-matome-2ht.pages.dev/` を入力して分析
3. **モバイル・デスクトップ両方**でスコアを確認
4. Core Web Vitals（LCP / FID / CLS）の実測値を記録

### Rich Results Test（構造化データ確認）
1. `https://search.google.com/test/rich-results` にアクセス
2. `https://hn-matome-2ht.pages.dev/` を入力
3. WebSite（SearchAction）・NewsArticle・BreadcrumbList が検出されることを確認

### Google Search Console (GSC)
1. GSC に `https://hn-matome-2ht.pages.dev/` を登録済み（認証ファイル設置済み）
2. 「サイトマップ」→ `https://hn-matome-2ht.pages.dev/sitemap.xml` を送信
3. 「URL 検査」でインデックス状態を確認

---

## 次の実装タスク

| タスク | 対象ファイル | 状態 |
|--------|-------------|------|
| CSS プリロード追加 | `templates/base.html` | 完了（2026-03-27） |
| JSON-LD: WebSite に SearchAction 追加 | `templates/index.html` | 完了（2026-03-27） |
| 内部リンク強化（アーカイブページ末尾に「他の日付を見る」） | `templates/archive.html` | 完了（2026-03-27） |
| JSON-LD: NewsArticle の `dateModified` をスロット更新時に正しい時刻に更新 | `scripts/generator.py` | 未対応（設計変更必要） |
| カスタムドメイン取得 | — | 手動作業・費用発生 |

---

## 参考: スキルの実行方法

```bash
# SEO監査（現状診断）
# Claude Code セッション内で:
/seo-audit

# 総合監査（230+ルール）
/audit-website
```

これらのスキルは改善実装後に実行して、残課題を洗い出すことを推奨。

---

## 次回実装タスク（2026-03-27 追加調査分）

### 緊急（クロール破壊リスク）

| タスク | ファイル | 内容 |
|--------|----------|------|
| docs/robots.txt のドメイン修正 | `docs/robots.txt:3` | 完了（2026-03-27） |
| docs/sitemap.xml のドメイン統一 + privacy追加 | `docs/sitemap.xml` | 完了（2026-03-27） |

**背景:** `scripts/sitemap.py` と `fetch_and_generate.py` は正しく `hn-matome-2ht.pages.dev` を使用するが、
現在の `docs/` 静的ファイルは旧ドメインのまま。スクリプト再実行で自動修正されるが、直接編集で即時修正可能。

### 中優先度（on-page SEO 補完）

| タスク | ファイル | 内容 |
|--------|----------|------|
| about.html に description ブロック追加 | `scripts/templates/about.html` | 完了（2026-03-27） |
| privacy.html に canonical + description 追加 | `scripts/templates/privacy.html` | 完了（2026-03-27） |

### 低優先度

| タスク | ファイル | 内容 |
|--------|----------|------|
| アーカイブ末尾に「他の日付を見る」内部リンク | `scripts/generator.py` + `scripts/templates/archive.html` | 完了（2026-03-27） |
| dateModified の動的更新 | モデル + generator + archive.html | report に `last_updated_at` フィールド追加（設計変更大） |

---

完了しました。実施内容のサマリーです。                

  ---                                                                                               
  実施内容（全4タスク）
                                                                                                    
  緊急修正（クロール破壊リスク解消）                                                             
  - docs/robots.txt — Sitemap URL のドメインを hn-matome-2ht.pages.dev に修正
  - docs/sitemap.xml — 旧ドメイン混在を全統一、privacy.html エントリを追加

  テンプレート meta 補完
  - scripts/templates/about.html — {% block description %} 追加（固有の説明文）
  - scripts/templates/privacy.html — {% block canonical %} と {% block description %} 追加

  内部リンク強化
  - scripts/generator.py — generate_archive() に recent_slugs パラメータ追加
  - scripts/fetch_and_generate.py — 自身を除いた最新10件のスラグを計算して渡す
  - scripts/templates/archive.html — ページ末尾に「他の日報を見る」リンクリストを追加

  テスト: 27 passed（全通過）

  ---
  残課題（手動作業 or 大きな設計変更が必要なため未対応）:
  - dateModified の動的更新（モデル設計変更が必要）
  - カスタムドメイン取得（費用・手動作業）
  - Google Search Console サイトマップ送信確認（手動作業）

## 監査ログ

### 2026-03-27 `/seo-audit` 実行

- **ツール:** Claude Code `/seo-audit` スキル
- **対象:** 全テンプレート・生成済みHTML・sitemap.xml を静的解析

**新規発見（既存計画未記載）:**
1. `about.html` の canonical が `/` を指す誤り（HIGH）
2. `archive.html` テンプレートに `og_description` ブロックがなく、全アーカイブで重複 description が出力（HIGH）
3. `twitter:image` が `twitter:card` / `twitter:title` / `twitter:description` と共に未設定（HIGH）

**確認済み既知課題（変化なし）:**
- favicon 未設定
- og:image 未設定
- pagefind-ui.js に defer なし
- privacy.html が sitemap 未掲載
- JSON-LD NewsArticle に image / publisher.logo / BreadcrumbList 未設定

### 2026-03-27 全11タスク実装完了

- **実施:** `executing-plans` スキルで優先実装順序の全タスクを順次実装
- **テスト:** 27 passed（全テスト通過）

**実装内容:**
1. `about.html` canonical 修正（`/` → `/about.html`）
2. `pagefind-ui.js` に `defer` 追加
3. `archive.html` に `{% block og_description %}` 追加
4. `sitemap.py` に `privacy.html` 追加
5. `docs/assets/favicon.svg` 作成（HNオレンジ #ff6600）、`base.html` に `<link rel="icon">` 追加
6. `docs/assets/og-image.svg` 作成（1200x630）、`base.html` に og:image メタ追加
7. `base.html` に twitter:title / twitter:description / twitter:image 追加、card を `summary_large_image` に変更
8. `archive.html` JSON-LD NewsArticle に image・publisher.logo 追加
9. `archive.html` に BreadcrumbList JSON-LD 追加
10. `archive.html` の summary_ja 冒頭1文を `<p class="summary-preview">` として `<details>` 外に出力
11. `generator.py` に `generate_feed()` メソッド追加（RSS 2.0）、`fetch_and_generate.py` から呼び出し
