# セキュリティ監査レポート

調査日: 2026-03-29
対象: hn-matome プロジェクト全体

---

## 優先度別 問題一覧

### HIGH

#### 2. `requirements.txt` のバージョン指定がパッチバージョン浮動

- **ファイル**: `requirements.txt`
- **内容**: `httpx==0.27.*` 等、パッチバージョンが固定されていない
- **リスク**: パッチバージョンに悪意のある変更が含まれた場合に自動適用される（サプライチェーン攻撃）

**推奨対応**:

```
# 現状（不完全）
httpx==0.27.*

# 推奨（完全固定）
httpx==0.27.2
```

すべての依存パッケージをマイナー・パッチバージョンまで固定する。

#### 3. GitHub Actions の外部アクションがメジャーバージョンのみ固定

- **ファイル**: `.github/workflows/update.yml`
- **内容**: `actions/checkout@v4` 等、コミットハッシュによる固定がされていない
- **リスク**: メジャーバージョンタグが書き換えられた場合に悪意のあるコードが実行される

**推奨対応**:

```yaml
# 現状（不完全）
uses: actions/checkout@v4

# 推奨（コミットハッシュで固定）
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

---

### MEDIUM

#### 4. HTML ストリッピングが簡易正規表現のみ

- **ファイル**: `scripts/models.py`
- **内容**: `re.sub(r"<[^>]+>", " ", text)` のみで HTML を除去している
- **リスク**: 不正な HTML（入れ子タグ、CDATA、スクリプトブロック等）が正規表現をバイパスする可能性がある

**推奨対応**:

```python
# 現状
import re
text = re.sub(r"<[^>]+>", " ", text)

# 推奨（標準ライブラリの html.parser を使用）
from html.parser import HTMLParser

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)

def strip_html(text: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(text)
    return extractor.get_text()
```

#### 5. GitHub Actions パーミッションのさらなる最小化

- **ファイル**: `.github/workflows/update.yml`
- **内容**: `contents: write` のみ設定されており、他パーミッションはデフォルト（read）
- **リスク**: 現状は低いが、ジョブ単位でのパーミッション分離が可能

**推奨対応**:

```yaml
# ワークフローレベルで全拒否し、ジョブ単位で必要なものだけ許可
permissions: {}

jobs:
  update:
    permissions:
      contents: write
```

---

## 問題なし（安全確認済み）

| 項目 | 確認内容 |
|------|---------|
| XSS 対策 | Jinja2 テンプレートで `autoescape=True` が有効 |
| パストラバーサル | `pathlib` を使用しており、任意パス操作のリスクなし |
| コマンドインジェクション | シェルコマンド実行系の関数が未使用 |
| 危険なシリアライズ | JSON のみ使用（バイナリシリアライズ形式は不使用） |
| シークレット管理（CI） | GitHub Actions では `secrets` コンテキストから正しく参照 |
| `.env` の Git 管理 | `.gitignore` に記載済み・Git 追跡履歴なし（コミット済みの実績なし） |

---

## 対応優先度まとめ

| 優先度 | 問題 | 対応 |
|--------|------|------|
| HIGH | `requirements.txt` バージョン浮動 | **対応済み**（2026-03-29） |
| HIGH | GitHub Actions アクションのハッシュ固定なし | **対応済み**（2026-03-29） |
| MEDIUM | HTML ストリッピングの堅牢化 | **対応済み**（2026-03-29） |
| MEDIUM | GitHub Actions パーミッション分離 | **対応済み**（2026-03-29） |

---

## 対応履歴・ステータス（2026-03-29 追記）

### 本リポジトリで実施した対応

| 監査項 | 変更内容 |
|--------|----------|
| **#2** `requirements.txt` | `httpx==0.27.2`、`jinja2==3.1.6`、`python-dotenv==1.2.2` に完全固定 |
| **#3** GitHub Actions | `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`（v4.2.2）、`actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`（v5.6.0）で固定（`update.yml` 内の 3 箇所） |
| **#4** HTML 除去 | `scripts/models.py` の `_strip_html` を `html.parser.HTMLParser` ベースに変更（既存の実体参照置換・空白正規化は維持） |
| **#5** パーミッション | ワークフロー先頭を `permissions: {}`、ジョブ `update` のみ `contents: write` を付与 |

**補足**: 日次更新ワークフローは `hn-matome-core` をチェックアウトして `python -m scripts.fetch_and_generate` を実行する。CI 上で HTML 除去の変更を反映するには、**core 側の `scripts/models.py` に同等の修正をマージする**必要がある（本リポジトリのみの変更では core の実行コードは変わらない）。

### 監査時点ですでに完了しているタスク（問題なし・確認済み）

以下は監査時に追加のコード変更を要さない項目として確認済み。運用・依存更新後も定期的に再確認すること。

| 項目 | 状態 |
|------|------|
| XSS 対策（Jinja2 `autoescape`） | 監査時点で適切 |
| パストラバーサル（`pathlib`） | 監査時点で適切 |
| コマンドインジェクション | 該当パターンなし（監査時点） |
| シリアライズ | JSON のみ |
| CI のシークレット参照 | `secrets` コンテキストで正しく参照 |
| `.env` の Git 管理 | `.gitignore` 済み・追跡なし（監査時点） |

詳細な根拠は上記「問題なし（安全確認済み）」の表を参照。
