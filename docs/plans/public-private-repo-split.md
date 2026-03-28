# public/private リポジトリ分割手順

## 採用方針（このプロジェクトの現行方針）

本プロジェクトは **public/private 分離構成を採用** する。

- public: `hn-matome`（workflow、`docs/`、運用ドキュメント）
- private: `hn-matome-core`（`scripts/`）
- 運用に必要な GitHub Secrets:
  - `CORE_REPO_TOKEN`
  - `OPENROUTER_API_KEY`

## 概要

GitHub Actions を public リポジトリで実行することで、private リポジトリの無料枠（月 2,000 分）を消費せずに毎日更新を実現する。

- **`hn-matome`（public）**: workflow・テンプレート・生成済み HTML
- **`hn-matome-core`（private）**: Python スクリプト本体

参考実装: `qiita-auto-first`（public）→ `qiita-auto-core`（private）の成功パターン

---

## ディレクトリ分割

### hn-matome（public）

```
.github/workflows/update.yml
templates/
docs/
requirements.txt
tests/（任意）
```

### hn-matome-core（private）

```
scripts/
  fetch_and_generate.py
  hn_client.py
  llm_client.py
  generator.py
  sitemap.py
  models.py
```

---

## 手順

### Step 1: hn-matome-core（private）リポジトリを作成

1. GitHub で新規リポジトリ `hn-matome-core` を作成（Private）
2. ローカルで `scripts/` ディレクトリを push

```bash
cd /Users/aa/projects/ClaudeCode/products/hn-matome

# 一時ディレクトリで core リポジトリを初期化
mkdir /tmp/hn-matome-core
cp -r scripts/ /tmp/hn-matome-core/scripts/
cd /tmp/hn-matome-core

git init
git remote add origin git@github.com:aa-0921/hn-matome-core.git
git add .
git commit -m "feat: scripts を hn-matome-core に移動"
git push -u origin main
```

---

### Step 2: Personal Access Token（PAT）を発行

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 「Generate new token (classic)」をクリック
3. 設定:
   - **Note**: `hn-matome-core access`
   - **Expiration**: No expiration（または適切な期間）
   - **Scopes**: `repo` にチェック
4. 生成されたトークンをコピー（再表示不可）

> qiita-auto-first で使用している `CORE_REPO_TOKEN` と同じトークンを使い回す場合は、このステップをスキップしてよい。

---

### Step 3: public リポジトリに Secrets を登録

1. `hn-matome`（public）リポジトリ → Settings → Secrets and variables → Actions
2. 以下の Secret を追加:

| Name | Value |
|------|-------|
| `CORE_REPO_TOKEN` | Step 2 で発行した PAT |
| `OPENROUTER_API_KEY` | 既存の API キー（移行済みなら不要） |

---

### Step 4: hn-matome を public に変更（または新規作成）

#### 既存リポジトリを public 化する場合

1. `hn-matome` → Settings → General → Danger Zone
2. 「Change repository visibility」→ Public に変更

#### 新規に public リポジトリを作る場合

```bash
cd /Users/aa/projects/ClaudeCode/products/hn-matome

# scripts/ を除外した状態で push
echo "scripts/" >> .gitignore

git remote set-url origin git@github.com:aa-0921/hn-matome.git
git add .
git commit -m "feat: public リポジトリとして再構成"
git push -u origin main
```

---

### Step 5: update.yml を更新

`.github/workflows/update.yml` を以下に差し替える:

```yaml
name: "HackerNews 日本語まとめ & AI要約 毎日更新"

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

      - name: hn-matome-core（scripts）をチェックアウト
        uses: actions/checkout@v4
        with:
          repository: aa-0921/hn-matome-core
          path: scripts
          ref: main
          token: ${{ secrets.CORE_REPO_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 依存インストール
        run: pip install -r requirements.txt

      - name: HN データ取得・翻訳・HTML 生成
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: python -m scripts.fetch_and_generate

      - name: Pagefind 検索インデックスを生成
        run: npx pagefind --site docs --output-path docs/pagefind

      - name: 変更をコミット・プッシュ
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/
          git diff --cached --quiet || git commit -m "Update: $(TZ=Asia/Tokyo date +%Y-%m-%d)"
          git push
```

---

### Step 6: 動作確認

1. `hn-matome` → Actions → 「HackerNews 日本語まとめ & AI要約 毎日更新」→ Run workflow
2. ジョブが成功することを確認
3. `docs/` に HTML が生成・コミットされることを確認

---

## 注意事項

- `scripts/` を public リポジトリの `.gitignore` に追加すること（コード漏洩防止）
- PAT は `repo` スコープだけで十分。`workflow` スコープは不要
- Cloudflare Pages は `hn-matome`（public）の `docs/` を参照するため、設定変更は不要
- `requirements.txt` は public リポジトリに置く（`scripts/` の依存関係を記述）

---

## コスト比較

| 構成 | Actions 消費 |
|------|------------|
| 現状（private 単体） | ~150 分/月（無料枠の 8%） |
| 変更後（public + private） | **0 分/月**（public は無制限） |

---

## Q&A: 1つのローカルディレクトリから2つのGitHubリポジトリへ push できるか？

### 結論: 可能。ただし「ネストした別 git repo」として管理する

1つのローカルディレクトリ（`/Users/aa/projects/ClaudeCode/products/hn-matome/`）から
`hn-matome`（public）と `hn-matome-core`（private）の2つに push する場合、
**単一の `.git` で2リポジトリに異なるコンテンツを push することは git の仕様上できない**。

正しいアプローチ: `scripts/` ディレクトリを**独立した git リポジトリ**として初期化する。

### 現在の状態（確認済み: 2026-03-28）

| 項目 | 状態 |
|------|------|
| ローカル root の remote | `git@github.com:aa-0921/hn-matome.git` |
| `.gitignore` に `scripts/` | 記載済み（public に漏洩しない） |
| `scripts/` の git 初期化 | **未実施** |

### 正しいローカル構成

```
/Users/aa/projects/ClaudeCode/products/hn-matome/   ← git repo #1
  .git/                                               remote: hn-matome (public)
  .gitignore  (scripts/ を除外)
  .github/workflows/update.yml
  docs/
  scripts/                                            ← git repo #2（ネスト）
    .git/                                             remote: hn-matome-core (private)
    fetch_and_generate.py
    ...
```

git は `.gitignore` で `scripts/` を無視するため、root と `scripts/` は完全に独立した別 repo として動作する。これはモノレポ内のネスト git repo として一般的なパターン。

### scripts/ を git repo として初期化する手順

```bash
cd /Users/aa/projects/ClaudeCode/products/hn-matome/scripts

git init
git remote add origin git@github.com:aa-0921/hn-matome-core.git
git add .
git commit -m "feat: scripts を hn-matome-core に初期 push"
git push -u origin main
```

### 日常的な push の違い

| 対象 | 操作ディレクトリ | push 先 |
|------|----------------|---------|
| workflow / docs の変更 | `/Users/aa/projects/ClaudeCode/products/hn-matome/` | `hn-matome` (public) |
| scripts/ の変更 | `/Users/aa/projects/ClaudeCode/products/hn-matome/scripts/` | `hn-matome-core` (private) |

それぞれのディレクトリで `git add`, `git commit`, `git push` を行う。
root からの `git push` が `scripts/` に影響することはない（`.gitignore` で除外されているため）。
