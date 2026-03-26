# HN日報 MVP 実装サマリー

> 作成日: 2026-03-26
> ステータス: MVP 実装完了

---

## 1. サービス概要

| 項目 | 内容 |
|---|---|
| サービス名 | HN日報（HackerNews 日本語まとめ） |
| ターゲット | Hacker News に興味ある日本人エンジニア |
| 提供価値 | HN トップ記事の日本語翻訳・英語コミュニティの議論要約を毎朝配信 |
| 収益モデル | Google AdSense |
| 運用コスト | 0円〜月170円（ドメイン代のみ） |

---

## 2. 最終的な技術スタック

| コンポーネント | 採用技術 | 理由 |
|---|---|---|
| データ取得 | HN 公式 Firebase API | 無料・無制限・認証不要 |
| 非同期 HTTP | httpx + asyncio | GitHub Actions 標準 Python に対応、async/await |
| HTML 生成 | Jinja2 | テンプレート継承・autoescape・実績あり |
| 翻訳・要約 | OpenRouter API（DeepSeek R1） | 無料枠あり、1日2〜5リクエストに圧縮可能 |
| 全文検索 | Pagefind | WASM ベース、日本語 n-gram 対応、サーバー不要 |
| ホスティング | Cloudflare Pages | anycast CDN・無制限帯域・`_redirects` 対応 |
| 自動実行 | GitHub Actions cron | UTC 23:00（= JST 8:00）毎日実行 |
| 言語 | Python 3.11 | GitHub Actions に標準搭載、2ライブラリで完結 |

### GitHub Pages → Cloudflare Pages 変更理由

| 比較項目 | GitHub Pages | Cloudflare Pages |
|---|---|---|
| CDN | GitHub CDN | anycast CDN（世界300拠点） |
| 帯域制限 | 100GB/月（ソフト制限） | **無制限** |
| `_redirects` | 非対応 | **対応**（`/` → 最新日付の自動リダイレクト） |
| HTTPS | 自動 | 自動 |
| デプロイ連携 | GitHub 連携 | **GitHub 連携（main push で自動デプロイ）** |

### Pagefind 採用理由（日本語検索の差別化）

| 比較 | Pagefind | Lunr.js | Algolia |
|---|---|---|---|
| 日本語対応 | **n-gram 自動対応** | 要手動設定 | 有料プラン |
| サーバー | 不要（WASM） | 不要 | 要 API キー |
| ビルド手順 | `npx pagefind --site docs` | インデックス手動生成 | クロール設定 |
| コスト | **0円** | 0円 | 有料 |

```bash
# Pagefind インデックス生成（GitHub Actions 内で実行）
npx pagefind --site docs --output-path docs/pagefind
```

```html
<!-- テンプレート側（data-pagefind-body でインデックス範囲を指定） -->
<main data-pagefind-body>
  {{ content }}
</main>
```

---

## 3. アーキテクチャ

```
HN公式API（Firebase）
  ↓
GitHub Actions cron（UTC 23:00 = JST 8:00）
  ↓
scripts/fetch_and_generate.py
  ├── HNClient.fetch_top_stories(limit=30)     # 非同期並列取得
  ├── HNClient.fetch_comments(story, max=5)    # コメント取得
  ├── LLMClient.translate_titles(titles)       # 30件を1リクエストで一括翻訳
  ├── LLMClient.summarize_comments(...)        # 記事ごとに1リクエスト
  └── HTMLGenerator + SitemapGenerator         # 静的 HTML 生成
  ↓
docs/ に出力（archive/*.html, index.html, sitemap.xml, _redirects, robots.txt）
  ↓
npx pagefind --site docs（検索インデックス生成）
  ↓
git add docs/ && git commit && git push
  ↓
Cloudflare Pages が自動デプロイ（main push トリガー）
```

---

## 4. ディレクトリ構成（完成形）

```
hn-matome/
├── scripts/
│   ├── fetch_and_generate.py   # メインオーケストレーター
│   ├── models.py               # データモデル（dataclasses）
│   ├── hn_client.py            # HN API クライアント（async）
│   ├── llm_client.py           # OpenRouter API クライアント
│   ├── generator.py            # HTML ジェネレーター（Jinja2）
│   ├── sitemap.py              # sitemap.xml + _redirects + robots.txt 生成
│   └── templates/
│       ├── base.html           # Pagefind UI・OGP・JSON-LD 含む
│       ├── archive.html        # 日付別アーカイブページ
│       ├── index.html          # トップページ（アーカイブ一覧）
│       ├── about.html          # サービス説明・免責事項
│       └── privacy.html        # プライバシーポリシー（AdSense 対応）
├── docs/                       # Cloudflare Pages の出力先（公開ルート）
│   ├── index.html
│   ├── archive/
│   │   └── YYYY-MM-DD.html
│   ├── about.html
│   ├── privacy.html
│   ├── sitemap.xml
│   ├── robots.txt
│   ├── _redirects              # / → 最新アーカイブへ 302 リダイレクト
│   ├── pagefind/               # Pagefind 検索インデックス（自動生成）
│   └── assets/
│       └── style.css
├── tests/
│   ├── conftest.py
│   ├── test_models.py          # 5テスト
│   ├── test_hn_client.py       # 3テスト
│   ├── test_llm_client.py      # 4テスト
│   ├── test_generator.py       # 4テスト
│   └── test_sitemap.py         # 5テスト
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .github/workflows/update.yml
```

---

## 5. 実装詳細

### 5.1 LLM リクエスト削減設計

OpenRouter 無料枠 50 req/日 の制約に対し、一括処理でリクエストを最小化:

| 処理 | 単純実装 | 最適化後 |
|---|---|---|
| タイトル翻訳 30件 | 30 req | **1 req（一括）** |
| コメント要約 30記事 | 30 req | **30 req（記事ごと1 req）** |
| 合計 | 60 req | **2〜31 req** |

コメントがない記事（Ask HN 等）は API 呼び出しをスキップするため、実際はさらに少なくなる。

### 5.2 データモデル

```python
@dataclass
class Comment:
    id: int
    author: str
    text: str  # HTML タグ除去・エンティティデコード済み

@dataclass
class Story:
    rank: int; id: int
    title_en: str; title_ja: str
    url: str | None; hn_url: str
    score: int; comment_count: int; posted_at: datetime
    comments: list[Comment]
    summary_ja: str  # AI 要約（日本語）

@dataclass
class DailyReport:
    date: datetime
    stories: list[Story]
    # date_str: "2026-03-26"
    # date_ja: "2026年3月26日"
```

### 5.3 GitHub Actions ワークフロー

```yaml
# .github/workflows/update.yml
on:
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00 = JST 8:00
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python -m scripts.fetch_and_generate
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
      - run: npx pagefind --site docs --output-path docs/pagefind
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/
          git diff --cached --quiet || git commit -m "Update: $(TZ=Asia/Tokyo date +%Y-%m-%d)"
          git push
```

### 5.4 テスト環境

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

```
requirements.txt:      httpx==0.27.*  jinja2==3.1.*
requirements-dev.txt:  pytest==8.3.*  pytest-asyncio==0.24.*  respx==0.21.*
```

HN API・OpenRouter API のモックには `respx.mock` を使用。

---

## 6. テスト結果（MVP 完了時）

```
tests/test_models.py      5 passed
tests/test_hn_client.py   3 passed
tests/test_llm_client.py  4 passed
tests/test_generator.py   4 passed
tests/test_sitemap.py     5 passed
----------------------------------
合計                      21 passed
```

---

## 7. コミット履歴

```
4a67e3f feat: GitHub Actions 毎日更新ワークフローを追加
e7a6d82 feat: メインオーケストレーター（fetch_and_generate.py）を実装
4f54fb2 fix: sitemap の mkdir 漏れ・XML宣言処理の堅牢化・テスト強化
51f05af feat: sitemap.xml / _redirects / robots.txt 自動生成を実装
a643aa7 fix: generator の mkdir 漏れを修正し generate_static_pages テストを追加
5af6dbd feat: HTML ジェネレーターを実装（Jinja2 テンプレートレンダリング）
7fe17b4 feat: Jinja2 テンプレートと CSS を作成
213e3a6 feat: OpenRouter LLM クライアントを実装（一括翻訳・コメント要約）
76eb824 feat: HN API クライアントを実装（非同期・並列取得）
4279e1b feat: データモデル（Story, Comment, DailyReport）を実装
99148b2 chore: プロジェクト骨格とテスト環境をセットアップ
```

---

## 8. リポジトリ構成の検討（private vs public 分離）

### 検討の背景

GitHub Actions の無料枠を最大活用しつつ、コアロジックのコピーを防ぎたいという要件から、以下の2構成を比較した。

### 案A: private repo 単体（推奨）

```
hn-matome（private）
├── .github/workflows/update.yml
├── scripts/           ← コアロジック（非公開）
└── docs/              ← Cloudflare Pages が参照（静的 HTML のみ公開）
```

**GitHub Actions 消費量試算:**

| 条件 | 計算 |
|---|---|
| 1回の実行時間 | 約 3〜5分 |
| 月間実行回数 | 30回 |
| 月間消費分 | 90〜150分 |
| private 無料枠 | **2,000分/月** |

→ **無料枠の 8〜10% しか使わない。余裕で収まる。**

**メリット:**
- 設定がシンプル（追加の鍵管理不要）
- Cloudflare Pages との連携がそのまま使える
- 運用コスト・設定コストが最小

### 案B: public（workflow）+ private（core）分離

```
hn-matome（public）               hn-matome-core（private）
├── .github/workflows/update.yml  ├── scripts/
└── runner.py（呼び出しのみ）      └── templates/
```

**実装方法（Deploy Key 方式）:**

```yaml
# public repo の workflow 内
- name: コアリポジトリをチェックアウト
  uses: actions/checkout@v4
  with:
    repository: your-username/hn-matome-core
    ssh-key: ${{ secrets.CORE_DEPLOY_KEY }}
    path: core

- name: 実行
  run: python core/scripts/fetch_and_generate.py
```

**Deploy Key 設定手順:**
1. `ssh-keygen -t ed25519 -f hn_core_key` でキーペア生成
2. **公開鍵** → `hn-matome-core`（private）の Deploy Keys に登録
3. **秘密鍵** → `hn-matome`（public）の Secrets に `CORE_DEPLOY_KEY` として登録

**デメリット:**
- Cloudflare Pages は public repo の `docs/` を参照するが、HTML 生成は private repo のコードが行う → cross-repo push の設計が必要
- Deploy Key の管理が増える
- ワークフロー自体は public なので「何をしているか」は概ねわかる
- 設定コストが増す

### 結論

**案A（private repo 単体）を推奨。**

HN日報の月間 Actions 消費量は約 90〜150分で、private repo の無料枠 2,000分/月の 10% 以下。コードを守りたい場合も、private repo 単体で十分に目的を達成できる。

案B（分離構成）は、複数サービスで core を共有する場合や、月間消費量が 2,000分に近づいた場合に改めて検討する。

---

## 9. 次のステップ（手動作業）

### 9.1 必須設定

1. **GitHub Secrets に API キーを登録**
   - `Settings > Secrets and variables > Actions > New repository secret`
   - Name: `OPENROUTER_API_KEY`
   - Value: OpenRouter のAPIキー

2. **Cloudflare Pages プロジェクトを作成**
   - Workers & Pages → Create application → Pages → Connect to Git
   - ビルドコマンド: （空欄）
   - 出力ディレクトリ: `docs`
   - Save and Deploy

3. **GitHub Actions を手動実行して動作確認**
   - Actions タブ → "HN日報 毎日更新" → "Run workflow"
   - `docs/archive/YYYY-MM-DD.html` が生成され、Cloudflare Pages に反映されることを確認

### 9.2 AdSense 申請前に必要なもの

| 条件 | 対応 |
|---|---|
| 独自ドメイン | Cloudflare でドメイン取得（約170円/月） |
| コンテンツ蓄積 | 20〜30日分のアーカイブ |
| プライバシーポリシー | `privacy.html` 実装済み |
| AdSense コード配置 | `base.html` の `<head>` に追記 |

### 9.3 想定収益

| PV/月 | 広告単価（テック系） | 月収 |
|---|---|---|
| 1,000 | 2〜5円/PV | 2,000〜5,000円 |
| 5,000 | 2〜5円/PV | 10,000〜25,000円 |
| 10,000 | 2〜5円/PV | 20,000〜50,000円 |

---

## 10. リスクと対策

| リスク | 対策 |
|---|---|
| OpenRouter 無料枠の変更 | 一括リクエスト設計で最小化。有料化しても月数百円以内 |
| Cloudflare Pages の制限 | 商用プランへの移行を検討（$20/月〜） |
| Y Combinator 商標クレーム | フォールバック名: `HN日報`、`ハクニチ`、`テックまとめJP` |
| 翻訳精度 | footer に「AI翻訳につき正確性を保証しない」免責事項を記載済み |
| private repo の Action 無料枠超過 | 月150分程度の消費で 2,000分枠の 8%。超過リスクほぼなし |
