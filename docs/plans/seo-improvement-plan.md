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

- [ ] **about.html の canonical URL が誤っている** ← 2026-03-27 監査で発見
  `docs/about.html:9` が `https://hn-matome-2ht.pages.dev/` (トップページ) を指している
  → Google が about.html をトップページの重複と判断し、インデックス除外の恐れ
  Fix: `scripts/templates/about.html` に追加:
  ```
  {% block canonical %}<link rel="canonical" href="https://hn-matome-2ht.pages.dev/about.html">{% endblock %}
  ```

- [ ] **favicon** 未設定
  `<link rel="icon" href="/favicon.ico">` をbase.htmlに追加
  → ブラウザタブ表示 + Googleサーチ結果のブランド感に影響

- [ ] **OG画像 (og:image)** 未設定
  Twitter/Facebook/Slackでシェアされたときに画像が表示されない
  → 静的OG画像 `/assets/og-image.png` を作成して全ページに追加
  推奨サイズ: 1200x630px
  ```html
  <meta property="og:image" content="https://hn-matome-2ht.pages.dev/assets/og-image.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  ```

- [ ] **twitter:title / twitter:description / twitter:image** 未設定
  `<meta name="twitter:card">` だけでは不十分
  → base.html に追加:
  ```html
  <meta name="twitter:title" content="{% block twitter_title %}HackerNews 日本語まとめ & AI要約{% endblock %}">
  <meta name="twitter:description" content="{% block twitter_description %}HackerNewsのトップ記事を毎日日本語翻訳・AI要約。毎朝JST8時更新。{% endblock %}">
  <meta name="twitter:image" content="https://hn-matome-2ht.pages.dev/assets/og-image.png">
  ```

- [ ] **archive ページの og:description がデフォルト文言のまま** ← 2026-03-27 監査で発見
  `archive.html` テンプレートに `{% block og_description %}` が未定義
  → 全アーカイブページで同一の汎用 og:description が出力される（重複 description）
  Fix: `scripts/templates/archive.html` に追加:
  ```
  {% block og_description %}{{ report.date_ja }}のHacker Newsトップ{{ report.stories|length }}記事を日本語翻訳・AI要約。{% endblock %}
  ```

- [ ] **sitemap.xml に privacy.html が未掲載**
  `scripts/sitemap.py` の `add_url(f"{self.base_url}/about.html", ...)` の後に追加:
  ```python
  add_url(f"{self.base_url}/privacy.html", "monthly", "0.2")
  ```

- [ ] **`<details>` タグ内のコメント要約がインデックスされない可能性**
  GoogleはJSレンダリング後にインデックスするが `<details>` は折りたたみ状態のためクロール優先度が低い
  → AI要約の冒頭数文を `<details>` 外に `<p class="summary-preview">` として出力することを検討

### 優先度: 中（構造化データ・リッチリザルト）

- [ ] **JSON-LD: WebSite に SearchAction を追加**（サイトリンク検索ボックス）
  ```json
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://hn-matome-2ht.pages.dev/?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
  ```

- [ ] **JSON-LD: NewsArticle の publisher に logo を追加**
  ```json
  "publisher": {
    "@type": "Organization",
    "name": "HN日報",
    "logo": {
      "@type": "ImageObject",
      "url": "https://hn-matome-2ht.pages.dev/assets/logo.png"
    }
  }
  ```

- [ ] **JSON-LD: BreadcrumbList を archive ページに追加**
  ```json
  {
    "@type": "BreadcrumbList",
    "itemListElement": [
      {"@type": "ListItem", "position": 1, "name": "トップ", "item": "https://..."},
      {"@type": "ListItem", "position": 2, "name": "2026年3月27日", "item": "https://.../archive/2026-03-27.html"}
    ]
  }
  ```

- [ ] **JSON-LD: NewsArticle の `dateModified` を再収集時に更新する**
  現状は `datePublished` と同値。スロット更新時に正しい時刻を反映する

- [ ] **JSON-LD: NewsArticle に `image` フィールドを追加**
  リッチリザルトの条件: image が必須
  → OG画像と同じURLで設定可能

### 優先度: 中（パフォーマンス・Core Web Vitals）

- [ ] **CSS のプリロード**
  `<link rel="preload" href="/assets/style.css" as="style">` を追加
  レンダーブロッキングを軽減

- [ ] **pagefind-ui.js の遅延ロード**
  検索UIは初期レンダリングに不要。`defer` または動的ロードに変更
  ```html
  <script src="/pagefind/pagefind-ui.js" defer></script>
  ```

- [ ] **画像の `width` / `height` 属性指定**
  OG画像・ロゴ等を追加する際は必ずサイズ指定でCLS(累積レイアウトシフト)を防ぐ

### 優先度: 低（長期的な評価向上）

- [ ] **RSS / Atom フィード** の追加
  `docs/feed.xml` を生成。`<link rel="alternate" type="application/rss+xml">` をheadに追加
  → RSSリーダー経由の流入 + Googleのクロール頻度向上

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

※ 2026-03-27 の `/seo-audit` 実行結果を踏まえて更新

| 順 | タスク | 対象ファイル | 工数 | 効果 |
|----|--------|-------------|------|------|
| 1 | about.html の canonical バグ修正 | `templates/about.html` | 5分 | インデックス正常化 |
| 2 | pagefind-ui.js に `defer` 追加 | `templates/base.html` | 1分 | LCP改善 |
| 3 | archive の og:description ブロック追加 | `templates/archive.html` | 10分 | SNS/SERP CTR向上 |
| 4 | sitemap.xml に privacy.html 追加 | `scripts/sitemap.py` | 5分 | クロール漏れ解消 |
| 5 | favicon 作成・設定 | `templates/base.html` + 画像 | 30分 | ブランド認知 |
| 6 | OG画像作成・全ページ og:image 設定 | `templates/base.html` + 画像 | 1〜2h | SNS CTR向上 |
| 7 | Twitter meta タグ補完 | `templates/base.html` | 10分 | Twitter/X表示改善 |
| 8 | JSON-LD: image + publisher logo 追加 | `templates/archive.html` | 30分 | リッチリザルト取得 |
| 9 | JSON-LD: BreadcrumbList 追加 | `templates/archive.html` | 20分 | パンくずリッチリザルト |
| 10 | `<details>` 外への要約プレビュー出力 | `templates/archive.html` | 1h | コンテンツインデックス向上 |
| 11 | RSS フィード生成 | `scripts/generator.py` | 2h | クロール頻度・流入強化 |

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
