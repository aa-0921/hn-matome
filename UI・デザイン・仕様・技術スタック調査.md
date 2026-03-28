# UI・デザイン・仕様・技術スタック調査

> 作成日: 2026-03-26
> 対象: HackerNews 日本語まとめ & AI要約（Cloudflare Pages 静的サイト）

---

## 1. UI・デザイン方針

### 1.1 レイアウト構成

ニュースリーダー型のシンプルな1カラムレイアウトを採用する。
AdSense 広告はコンテンツの邪魔にならない位置に配置し、読了率を維持する。

```
┌─────────────────────────────────────┐
│  ヘッダー（サービス名 + 日付 + nav） │
├─────────────────────────────────────┤
│  [広告: レスポンシブ横長]           │
├─────────────────────────────────────┤
│  記事一覧（#1〜#30）                │
│  ┌─────────────────────────────┐   │
│  │ #1 [日本語タイトル]         │   │
│  │ スコア: 1234  コメント: 456  │   │
│  │ 投稿: 12時間前              │   │
│  │ [HNリンク] [元記事リンク]   │   │
│  │ ▼ コミュニティの反応        │   │
│  │ （コメント要約 200字）      │   │
│  └─────────────────────────────┘   │
│  ... #2〜#10 ...                    │
├─────────────────────────────────────┤
│  [広告: コンテンツ内 中間]          │
├─────────────────────────────────────┤
│  ... #11〜#30 ...                   │
├─────────────────────────────────────┤
│  アーカイブリンク（過去30日分）     │
├─────────────────────────────────────┤
│  フッター（免責・プライバシー等）   │
└─────────────────────────────────────┘
```

### 1.2 カラーパレット

HN のオレンジ（#FF6600）をアクセントとして使いつつ、日本語の読みやすさを優先した落ち着いたトーンにする。

| 役割 | カラーコード | 用途 |
|---|---|---|
| Primary | `#E8580A` | ヘッダー背景、ランク番号、リンクホバー |
| Background | `#F6F6EF` | ページ背景（HN クラシックカラー） |
| Surface | `#FFFFFF` | 記事カード背景 |
| Text Primary | `#1A1A1A` | 本文テキスト |
| Text Secondary | `#828282` | スコア・投稿時刻等のメタ情報 |
| Border | `#E0E0E0` | カード区切り線 |
| Link | `#0066CC` | 外部リンク（アクセシビリティ考慮） |
| Link Visited | `#551A8B` | 既読リンク |

### 1.3 タイポグラフィ（日本語フォント）

```css
/* フォントスタック: system-ui を優先し、日本語を明示指定 */
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "Hiragino Sans",
  "Hiragino Kaku Gothic ProN",
  "Noto Sans JP",
  "Yu Gothic",
  sans-serif;

/* 本文サイズ・行間 */
font-size: 16px;        /* モバイルでも読める最小値 */
line-height: 1.8;       /* 日本語は1.6〜1.9が適切 */
letter-spacing: 0.02em; /* 日本語の詰まり感を緩和 */

/* タイトル */
.article-title {
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.5;
}

/* メタ情報（スコア・時刻） */
.article-meta {
  font-size: 0.8rem;
  color: #828282;
}

/* コメント要約 */
.article-summary {
  font-size: 0.9rem;
  line-height: 1.8;
  color: #444;
}
```

**Google Fonts 不使用の理由**: ページ速度への悪影響を避けるため、システムフォントのみ使用。Core Web Vitals（LCP）に有利。

### 1.4 AdSense 配置戦略

AdSense 審査通過後を見据えた配置設計。過剰な広告はポリシー違反・ユーザー離脱の原因になるため最大3枠に限定する。

| 広告枠 | 位置 | サイズ | 理由 |
|---|---|---|---|
| ヘッダー下 | 記事一覧の直前 | レスポンシブ横長 | PV単価が高いファーストビュー |
| コンテンツ内 | #10〜#11 の間 | 記事内 | スクロール中のビューアビリティ |
| フッター上 | アーカイブリンク下 | レスポンシブ | 読了後のクリック誘導 |

**注意**: AdSense 申請時は広告コードをまだ貼らない。審査は広告なし状態のコンテンツで行う。

---

## 2. 必要仕様まとめ

### 2.1 ページ構成

```
docs/
├── index.html              # トップページ（最新日付にリダイレクト or 最新コンテンツ）
├── archive/
│   ├── 2026-03-26.html    # 日付別アーカイブ
│   ├── 2026-03-27.html
│   └── ...
├── about.html              # サービス説明ページ（AdSense審査用コンテンツ）
├── privacy.html            # プライバシーポリシー（AdSense審査必須）
├── sitemap.xml             # SEO: サイトマップ
├── robots.txt              # SEO: クローラー制御
└── assets/
    └── style.css
```

### 2.2 各ページの必須要素

#### index.html / archive/YYYY-MM-DD.html（共通）

| 要素 | 内容 |
|---|---|
| `<title>` | アーカイブ: `YYYY年MM月DD日 \| HackerNews 日本語まとめ & AI要約`／トップ: `HackerNews 日本語まとめ & AI要約 - 毎日更新` |
| `<meta description>` | `YYYY年MM月DD日のHacker Newsトップ記事30件を日本語に翻訳・AI要約。エンジニア向け最新テック情報を毎日更新。` |
| OGP タグ | `og:title`, `og:description`, `og:url`, `og:type` |
| JSON-LD | NewsArticle 構造化データ |
| canonical URL | `<link rel="canonical" href="...">` |
| prev/next リンク | アーカイブ間のページネーション |
| 記事リスト | ランク番号・日本語タイトル・スコア・コメント数・投稿時刻・コメント要約 |

#### about.html

- サービスの説明（何を、誰に、どのように提供するか）
- 更新頻度の説明
- 免責事項（AI翻訳の誤訳リスク）
- 問い合わせ情報（GitHub Issues or メールアドレス）
- **AdSense 審査では about.html の存在が信頼性評価に影響する**

#### privacy.html

AdSense 利用には必須。以下を記載する:

- 取得する情報（アクセスログ、Cookie）
- 第三者配信事業者（Google）によるクッキー使用
- オプトアウト方法
- 作成日・最終更新日

### 2.3 AdSense 申請に必要なコンテンツ要件

| 要件 | 対応方法 |
|---|---|
| 独自ドメイン | `hn-matome.com` 等を取得（月170円） |
| コンテンツ量 | 30日以上 = 30ページ以上のアーカイブ蓄積 |
| プライバシーポリシー | `privacy.html` に記載 |
| 連絡先情報 | `about.html` に記載 |
| コンテンツの独自性 | AI 翻訳 + 要約 = 独自コンテンツとして認定される（HN 本文コピーはNG） |
| ナビゲーション | ヘッダーにトップ・アーカイブ・aboutへのリンク |

---

## 3. SEO 重要性と施策

### 3.1 このサービスで SEO が最重要な理由

収益源が Google AdSense のみ = **PV 数 = 収益** という直接的な関係がある。
ソーシャル流入は日次の波があるが、検索流入は安定したベースラインを作る。

```
月収試算:
  PV 5,000/月 × 広告単価 ¥3/PV = ¥15,000/月
  PV の 30% が検索流入だとすると 1,500 PV が検索由来

→ SEO で検索流入を 2倍にするだけで月収 +¥4,500 の安定収入増
```

検索意図の想定クエリ:
- `hacker news 日本語`
- `HN まとめ 今日`
- `ハッカーニュース 翻訳`
- `YYYY年MM月DD日 テックニュース まとめ`（日付検索）

### 3.2 構造化データ設計（JSON-LD）

各アーカイブページに NewsArticle スキーマを埋め込む。

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "2026年3月26日 HackerNews 日本語まとめ トップ30記事",
  "description": "2026年3月26日のHacker Newsトップ30記事を日本語翻訳・AI要約。",
  "datePublished": "2026-03-26T08:00:00+09:00",
  "dateModified": "2026-03-26T08:00:00+09:00",
  "author": {
    "@type": "Organization",
    "name": "HackerNews 日本語まとめ & AI要約"
  },
  "publisher": {
    "@type": "Organization",
    "name": "HackerNews 日本語まとめ & AI要約",
    "url": "https://hn-matome.com"
  },
  "inLanguage": "ja",
  "url": "https://hn-matome.com/archive/2026-03-26.html"
}
</script>
```

加えて、トップページに `WebSite` スキーマ + `SearchAction` を設定するとサイトリンク検索ボックスが表示される可能性がある。

### 3.3 メタタグ・OGP 設計

```html
<!-- 基本メタ -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="YYYY年MM月DD日のHacker Newsトップ30記事を日本語翻訳・AI要約。毎日JST8時更新。">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://hn-matome.com/archive/YYYY-MM-DD.html">

<!-- OGP -->
<meta property="og:type" content="article">
<meta property="og:title" content="YYYY年MM月DD日 | HackerNews 日本語まとめ & AI要約">
<meta property="og:description" content="今日のHacker Newsトップ記事30件を日本語に翻訳・AI要約しました。">
<meta property="og:url" content="https://hn-matome.com/archive/YYYY-MM-DD.html">
<meta property="og:site_name" content="HackerNews 日本語まとめ & AI要約">
<meta property="og:locale" content="ja_JP">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="YYYY年MM月DD日 HackerNews 日本語まとめ & AI要約">
<meta name="twitter:description" content="今日のHacker Newsトップ記事30件を日本語まとめ。">
```

OGP 画像は初期は省略し、テキストのみで対応。後からテキスト合成画像（Pillow で自動生成）を追加できる。

### 3.4 URL 設計

| ページ | URL | 備考 |
|---|---|---|
| トップ | `https://hn-matome.com/` | index.html |
| 日付アーカイブ | `https://hn-matome.com/archive/2026-03-26.html` | 日付が URL に含まれると検索クリック率向上 |
| About | `https://hn-matome.com/about.html` | |
| Privacy | `https://hn-matome.com/privacy.html` | |

### 3.5 サイトマップ・robots.txt

**sitemap.xml**（Python で自動生成）:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://hn-matome.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://hn-matome.com/archive/2026-03-26.html</loc>
    <lastmod>2026-03-26</lastmod>
    <changefreq>never</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- ... -->
</urlset>
```

**robots.txt**:

```
User-agent: *
Allow: /
Sitemap: https://hn-matome.com/sitemap.xml
```

### 3.6 内部リンク設計

- 各アーカイブページに「前日 / 翌日」のナビゲーションを設置（クローラーが全ページを辿れる）
- トップページから最新30日分のアーカイブリンクを羅列
- フッターに about.html・privacy.html へのリンク

### 3.7 Google Search Console 設定

サイト公開後すぐに行うこと:

1. `search.google.com/search-console` でサイト追加
2. GitHub Pages + 独自ドメインの所有権確認（DNS TXT レコードまたは HTML ファイル）
3. sitemap.xml を送信
4. カバレッジレポートで全アーカイブがインデックスされているか確認

### 3.8 Core Web Vitals 対策

静的 HTML のため元々有利だが、以下を遵守する。
Cloudflare Pages のグローバル CDN により LCP はさらに短縮できる:

| 指標 | 目標値 | 対策 |
|---|---|---|
| LCP | < 2.5s | 外部フォント不使用、CSS インライン化検討 |
| FID/INP | < 100ms | JavaScript 最小化（ほぼゼロ JS） |
| CLS | < 0.1 | 画像に width/height 明示、広告エリアにスペース予約 |

---

## 4. 技術スタック推奨

### 4.1 Python 側

**Python を採用する理由**:
- GitHub Actions に Python がプリインストールされており、追加セットアップが不要
- Jinja2 は HTML テンプレート生成ライブラリとして最も成熟しており、エスケープ・継承・フィルタが揃っている
- httpx の async モードで HN API の並列取得が自然に書ける
- 外部ライブラリを 2 つに絞れる軽量な構成が実現できる
- Node.js/TypeScript でも同等に実装可能だが、このスクリプト的ユースケースでは Python が最もシンプル

| コンポーネント | 採用技術 | 理由 |
|---|---|---|
| テンプレートエンジン | **Jinja2** | HTML 生成に最適。ループ・条件分岐・フィルタが揃っている |
| HTTP クライアント | **httpx** (async) | HN API の並列取得で高速化 |
| 翻訳・要約 | **OpenRouter API** (httpx) | 無料枠あり。DeepSeek R1 等を使用 |
| サイトマップ生成 | **xml.etree.ElementTree** (標準ライブラリ) | 外部ライブラリ不要 |
| 日時処理 | **datetime** + **zoneinfo** (標準ライブラリ) | JST 変換に使用 |
| HTML エスケープ | Jinja2 の autoescaping | XSS 対策として自動エスケープを有効化 |
| 検索インデックス生成 | **Pagefind CLI** (npx 経由) | Python ビルド後に HTML を解析してインデックスを生成 |

**requirements.txt 想定**:

```
httpx==0.27.*
jinja2==3.1.*
```

2ライブラリのみ。依存が軽い。

### 4.2 フロントエンド（CSS 方針）

**Plain CSS（フレームワークなし）を採用する。**

理由:
- ページ速度: Tailwind CDN を使うと 300KB+ の読み込みが発生し LCP に悪影響
- シンプルさ: このサイトに必要な CSS は 200〜300 行程度で収まる
- 依存ゼロ: CDN 障害・バージョン変更に影響されない

Tailwind を使う場合は CDN ではなく `tailwindcss` CLI で purge したものをバンドルするべきだが、Python 環境で Node.js を追加する複雑さは不要。

**CSS 設計方針**:

```css
/* リセット: box-sizing のみ */
*, *::before, *::after { box-sizing: border-box; }

/* レスポンシブ: モバイルファースト */
/* base: スマホ (〜767px) */
/* @media (min-width: 768px): タブレット */
/* @media (min-width: 1024px): デスクトップ */

/* コンテナ: max-width 800px、中央揃え */
.container { max-width: 800px; margin: 0 auto; padding: 0 16px; }

/* 記事カード */
.article-item { border-bottom: 1px solid #E0E0E0; padding: 16px 0; }
```

### 4.3 静的アセット構成（最終形）

```
docs/
├── index.html
├── archive/
│   └── YYYY-MM-DD.html
├── about.html
├── privacy.html
├── sitemap.xml
├── robots.txt
├── assets/
│   └── style.css          # 単一 CSS ファイル（200〜300行）
└── pagefind/              # Pagefind が自動生成（git管理外でも可）
    ├── pagefind.js
    ├── pagefind-ui.js
    ├── pagefind-ui.css
    └── *.pf_meta          # 検索インデックス（バイナリ）
```

JavaScript ファイルは原則不要。AdSense コードのみ `<script async>` で読み込む。
検索 UI は Pagefind が提供する `pagefind-ui.js` のみを使用する。

### 4.3b 検索機能（Pagefind）

**既存サービスとの差別化として、過去の全記事を日本語・英語で全文検索できる機能を提供する。**

#### Pagefind を採用する理由

| 比較軸 | Pagefind | Lunr.js | Algolia |
|---|---|---|---|
| 日本語対応 | WASM で文字単位 n-gram | 別途形態素解析が必要 | 有料プランで対応 |
| 静的サイト対応 | ネイティブ対応 | JS バンドル要 | 外部 API 依存 |
| インデックスサイズ | 圧縮効率が良い | 全量 JS に含む | 外部管理 |
| 無料 | 完全無料 | 完全無料 | 無料枠に制限あり |
| セットアップ | `npx pagefind` のみ | 要実装 | 要登録・設定 |

#### ビルドフロー

```bash
# 1. Python でHTML生成
python scripts/fetch_and_generate.py

# 2. Pagefind で検索インデックスをビルド
npx pagefind --site docs --output-path docs/pagefind
```

GitHub Actions のワークフローに上記を順番に組み込む。

#### 検索UIの組み込み

```html
<!-- index.html の <head> に追加 -->
<link href="/pagefind/pagefind-ui.css" rel="stylesheet">
<script src="/pagefind/pagefind-ui.js"></script>

<!-- 検索ボックスの設置場所（ヘッダー下） -->
<div id="search"></div>
<script>
  new PagefindUI({ element: "#search", showSubResults: false });
</script>
```

#### 検索対象の制御

各アーカイブページに `data-pagefind-body` 属性を設定することで、
記事一覧部分のみを検索対象にする（ヘッダー・フッターを除外）。

```html
<!-- archive/YYYY-MM-DD.html の記事一覧部分に付与 -->
<main data-pagefind-body>
  <!-- 日本語タイトル + コメント要約がインデックスされる -->
</main>
```

翻訳後の日本語タイトルと、元の英語タイトル・コメント要約の両方がインデックスに含まれるため、
日本語・英語どちらのキーワードでも検索可能になる。

### 4.4 Jinja2 テンプレート構成

```
scripts/
├── fetch_and_generate.py  # メインスクリプト
├── templates/
│   ├── base.html          # 共通レイアウト（head, header, footer, 検索ボックス）
│   ├── archive.html       # 日付アーカイブページ（base.html を継承）
│   ├── index.html         # トップページ（最新 + アーカイブ一覧）
│   ├── about.html         # about ページ
│   └── privacy.html       # プライバシーポリシー（静的内容）
└── requirements.txt
```

### 4.5 OGP 画像（将来対応）

初期は画像なし。PV が増えてきた段階で Python の `Pillow` ライブラリでテキスト合成画像を自動生成する。

```python
# 将来追加: Pillow で OGP 画像を自動生成
# from PIL import Image, ImageDraw, ImageFont
# 1200x630px に日付 + サービス名を描画 → docs/assets/ogp/YYYY-MM-DD.png
```

---

## 5. ホスティング: Cloudflare Pages

### 5.1 GitHub Pages ではなく Cloudflare Pages を採用する理由

| 比較軸 | GitHub Pages | Cloudflare Pages |
|---|---|---|
| CDN | GitHubのCDN（拠点数限定） | Anycast グローバルエッジ（日本拠点多数） |
| 帯域制限 | 100GB/月ソフトリミット | **無制限** |
| カスタムドメイン SSL | 無料 | 無料 |
| リダイレクト設定 | 不便 | `_redirects` ファイルで簡単 |
| デプロイ連携 | GitHub連携OK | GitHub リポジトリと直接連携 |
| アクセス分析 | なし | Cloudflare Analytics あり |
| 将来の拡張 | 制限あり | Cloudflare Workers で動的機能追加可 |

AdSense 収益は PV 数に直結するため CDN 性能は重要。
Cloudflare の日本拠点経由で配信されることで LCP が短縮される。

### 5.2 デプロイフロー

```
GitHub リポジトリ（main ブランチ）
  └── GitHub Actions（毎日 JST 8:00 cron）
        ├── python scripts/fetch_and_generate.py  → docs/ に HTML 生成
        ├── npx pagefind --site docs              → docs/pagefind/ に検索インデックス生成
        └── git push → main ブランチに push
              └── Cloudflare Pages が自動検出 → docs/ フォルダをデプロイ
```

Cloudflare Pages の「ビルドコマンド」を空にして「出力ディレクトリ」を `docs` に設定するだけ。
GitHub Actions 側でビルドを完結させ、成果物を push する方式にする。

### 5.3 設定手順

1. Cloudflare Pages でプロジェクト作成 → GitHub リポジトリを連携
2. ビルドコマンド: なし（空欄）
3. 出力ディレクトリ: `docs`
4. カスタムドメインを設定（Cloudflare DNS に委任すると自動設定）
5. `_redirects` ファイルを `docs/` に追加:

```
/ /archive/YYYY-MM-DD.html 302
```

（毎日 Python スクリプトが最新日付にリダイレクトする `_redirects` を自動上書き生成）

---

## 6. まとめ・実装優先順位

| 優先度 | タスク |
|---|---|
| 必須（Day 1） | `fetch_and_generate.py` 骨格、Jinja2 テンプレート、style.css |
| 必須（Day 1） | `robots.txt`、`privacy.html`（静的）、`about.html`（静的） |
| 必須（Day 1） | Cloudflare Pages セットアップ、独自ドメイン取得・連携 |
| 必須（Week 1） | JSON-LD 構造化データ、メタタグ・OGP タグ、sitemap.xml 自動生成 |
| 必須（Week 1） | Pagefind 検索インデックス生成をビルドフローに組み込み |
| 必須（Week 1） | 検索ボックスをヘッダーに設置（`data-pagefind-body` 属性設定含む） |
| 推奨（Month 1） | Google Search Console 登録 |
| 推奨（Month 1） | アーカイブ 30日分蓄積 → AdSense 申請 |
| 将来 | OGP 画像自動生成、PWA 対応 |
