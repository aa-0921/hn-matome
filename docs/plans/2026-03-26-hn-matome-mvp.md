# HN日報 MVP 実装計画

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** HackerNews Top30を毎日自動取得・日本語翻訳・AI要約し、Cloudflare Pages で静的サイトとして公開する。

**Architecture:** GitHub Actions cron（JST 8:00）で Python スクリプトを実行し、HN API からデータ取得 → OpenRouter API で翻訳・要約 → Jinja2 で静的 HTML 生成 → Pagefind で検索インデックス生成 → main ブランチに push → Cloudflare Pages が自動デプロイ。

**Tech Stack:** Python 3.11, httpx (async), Jinja2, OpenRouter API (DeepSeek R1), Pagefind, pytest, Cloudflare Pages

---

## ディレクトリ構成（完成形）

```
hn-matome/
├── scripts/
│   ├── fetch_and_generate.py   # メインオーケストレーター
│   ├── models.py               # データモデル（dataclasses）
│   ├── hn_client.py            # HN API クライアント
│   ├── llm_client.py           # OpenRouter API クライアント
│   ├── generator.py            # HTML ジェネレーター（Jinja2）
│   ├── sitemap.py              # sitemap.xml + _redirects 生成
│   └── templates/
│       ├── base.html
│       ├── archive.html
│       ├── index.html
│       ├── about.html
│       └── privacy.html
├── docs/                       # Cloudflare Pages の出力先
│   ├── index.html
│   ├── archive/
│   ├── about.html
│   ├── privacy.html
│   ├── sitemap.xml
│   ├── robots.txt
│   ├── _redirects
│   └── assets/
│       └── style.css
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_hn_client.py
│   ├── test_llm_client.py
│   ├── test_generator.py
│   └── test_sitemap.py
├── requirements.txt
├── requirements-dev.txt
└── .github/workflows/update.yml
```

---

### Task 1: プロジェクト骨格のセットアップ

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `tests/conftest.py`
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`

**Step 1: requirements.txt を作成**

```
httpx==0.27.*
jinja2==3.1.*
```

**Step 2: requirements-dev.txt を作成**

```
pytest==8.3.*
pytest-asyncio==0.24.*
respx==0.21.*
```

`respx` は httpx の async モックライブラリ。

**Step 3: pytest.ini を作成**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

**Step 4: tests/conftest.py を作成**

```python
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
```

**Step 5: ディレクトリ作成 + 空ファイル配置**

```bash
mkdir -p scripts/templates tests docs/archive docs/assets docs/plans
touch scripts/__init__.py tests/__init__.py
```

**Step 6: 依存インストール確認**

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --collect-only   # テストが 0 件で正常終了することを確認
```

Expected: `no tests ran`

**Step 7: コミット**

```bash
git add requirements.txt requirements-dev.txt pytest.ini tests/ scripts/__init__.py
git commit -m "chore: プロジェクト骨格とテスト環境をセットアップ"
```

---

### Task 2: データモデル

**Files:**
- Create: `scripts/models.py`
- Create: `tests/test_models.py`

**Step 1: テストを先に書く**

`tests/test_models.py`:

```python
from scripts.models import Comment, Story, DailyReport
from datetime import datetime, timezone


def test_comment_from_api():
    raw = {"id": 1, "text": "Hello <b>world</b>", "by": "user1", "time": 1700000000}
    c = Comment.from_api(raw)
    assert c.id == 1
    assert c.author == "user1"
    # HTML タグが除去されていること
    assert "<b>" not in c.text


def test_comment_missing_text():
    # text フィールドが欠けているコメント（削除済み等）は空文字扱い
    raw = {"id": 2, "by": "user2", "time": 1700000000}
    c = Comment.from_api(raw)
    assert c.text == ""


def test_story_from_api():
    raw = {
        "id": 100,
        "title": "Show HN: My Project",
        "url": "https://example.com",
        "score": 200,
        "descendants": 50,
        "time": 1700000000,
        "kids": [1, 2, 3],
    }
    s = Story.from_api(raw, rank=1)
    assert s.rank == 1
    assert s.title_en == "Show HN: My Project"
    assert s.hn_url == "https://news.ycombinator.com/item?id=100"
    assert s.score == 200
    assert s.comment_count == 50


def test_story_no_url():
    # Ask HN 等、外部 URL がない記事
    raw = {"id": 200, "title": "Ask HN: ...", "score": 100, "descendants": 20, "time": 1700000000}
    s = Story.from_api(raw, rank=1)
    assert s.url is None


def test_daily_report_date_str():
    stories = []
    report = DailyReport(date=datetime(2026, 3, 26, tzinfo=timezone.utc), stories=stories)
    assert report.date_str == "2026-03-26"
    assert report.date_ja == "2026年3月26日"
```

**Step 2: 失敗確認**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError: cannot import name 'Comment'`

**Step 3: モデル実装**

`scripts/models.py`:

```python
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _strip_html(text: str) -> str:
    """HN コメントの HTML タグを除去し、&amp; 等をデコードする"""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#x27;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Comment:
    id: int
    author: str
    text: str

    @classmethod
    def from_api(cls, data: dict) -> "Comment":
        return cls(
            id=data["id"],
            author=data.get("by", ""),
            text=_strip_html(data.get("text", "")),
        )


@dataclass
class Story:
    rank: int
    id: int
    title_en: str
    title_ja: str
    url: Optional[str]
    hn_url: str
    score: int
    comment_count: int
    posted_at: datetime
    comments: list[Comment] = field(default_factory=list)
    summary_ja: str = ""

    @classmethod
    def from_api(cls, data: dict, rank: int) -> "Story":
        return cls(
            rank=rank,
            id=data["id"],
            title_en=data.get("title", ""),
            title_ja="",  # 翻訳後にセット
            url=data.get("url"),
            hn_url=f"https://news.ycombinator.com/item?id={data['id']}",
            score=data.get("score", 0),
            comment_count=data.get("descendants", 0),
            posted_at=datetime.fromtimestamp(data.get("time", 0), tz=timezone.utc),
        )


@dataclass
class DailyReport:
    date: datetime
    stories: list[Story]

    @property
    def date_str(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def date_ja(self) -> str:
        return f"{self.date.year}年{self.date.month}月{self.date.day}日"
```

**Step 4: テスト通過確認**

```bash
pytest tests/test_models.py -v
```

Expected: 全テスト PASS

**Step 5: コミット**

```bash
git add scripts/models.py tests/test_models.py
git commit -m "feat: データモデル（Story, Comment, DailyReport）を実装"
```

---

### Task 3: HN API クライアント

**Files:**
- Create: `scripts/hn_client.py`
- Create: `tests/test_hn_client.py`

**Step 1: テストを書く**

`tests/test_hn_client.py`:

```python
import pytest
import respx
import httpx
from scripts.hn_client import HNClient


BASE = "https://hacker-news.firebaseio.com/v0"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_top_ids():
    respx.get(f"{BASE}/topstories.json").mock(
        return_value=httpx.Response(200, json=list(range(1, 501)))
    )
    async with HNClient() as client:
        ids = await client.fetch_top_ids(limit=30)
    assert ids == list(range(1, 31))


@pytest.mark.asyncio
@respx.mock
async def test_fetch_item():
    item = {"id": 42, "title": "Test", "score": 100, "descendants": 10, "time": 1700000000}
    respx.get(f"{BASE}/item/42.json").mock(return_value=httpx.Response(200, json=item))
    async with HNClient() as client:
        result = await client.fetch_item(42)
    assert result["id"] == 42


@pytest.mark.asyncio
@respx.mock
async def test_fetch_top_stories_returns_30():
    ids = list(range(1, 501))
    respx.get(f"{BASE}/topstories.json").mock(return_value=httpx.Response(200, json=ids))
    for i in range(1, 31):
        item = {"id": i, "title": f"Story {i}", "score": i * 10, "descendants": i, "time": 1700000000, "kids": []}
        respx.get(f"{BASE}/item/{i}.json").mock(return_value=httpx.Response(200, json=item))
    async with HNClient() as client:
        stories = await client.fetch_top_stories(limit=30)
    assert len(stories) == 30
    assert stories[0].rank == 1
```

**Step 2: 失敗確認**

```bash
pytest tests/test_hn_client.py -v
```

Expected: `ImportError`

**Step 3: HN クライアント実装**

`scripts/hn_client.py`:

```python
import asyncio
import httpx
from scripts.models import Comment, Story

BASE_URL = "https://hacker-news.firebaseio.com/v0"
MAX_CONCURRENT = 10  # 同時リクエスト数の上限


class HNClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def fetch_item(self, item_id: int) -> dict:
        resp = await self._client.get(f"{BASE_URL}/item/{item_id}.json")
        resp.raise_for_status()
        return resp.json()

    async def fetch_top_ids(self, limit: int = 30) -> list[int]:
        resp = await self._client.get(f"{BASE_URL}/topstories.json")
        resp.raise_for_status()
        return resp.json()[:limit]

    async def fetch_top_stories(self, limit: int = 30) -> list[Story]:
        ids = await self.fetch_top_ids(limit)
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_one(rank: int, item_id: int) -> Story:
            async with sem:
                data = await self.fetch_item(item_id)
            return Story.from_api(data, rank=rank)

        tasks = [fetch_one(i + 1, item_id) for i, item_id in enumerate(ids)]
        return await asyncio.gather(*tasks)

    async def fetch_comments(self, story: Story, max_comments: int = 5) -> list[Comment]:
        """記事の上位コメントを取得する（再帰せず第一階層のみ）"""
        if not story.comment_count:
            return []
        # HN API の kids フィールドは story データに含まれていない場合があるため再取得
        data = await self.fetch_item(story.id)
        kid_ids = data.get("kids", [])[:max_comments]
        if not kid_ids:
            return []

        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch_comment(cid: int) -> Comment | None:
            async with sem:
                try:
                    data = await self.fetch_item(cid)
                    if data.get("deleted") or data.get("dead"):
                        return None
                    return Comment.from_api(data)
                except Exception:
                    return None

        results = await asyncio.gather(*[fetch_comment(cid) for cid in kid_ids])
        return [c for c in results if c is not None]
```

**Step 4: テスト通過確認**

```bash
pytest tests/test_hn_client.py -v
```

Expected: 全テスト PASS

**Step 5: コミット**

```bash
git add scripts/hn_client.py tests/test_hn_client.py
git commit -m "feat: HN API クライアントを実装（非同期・並列取得）"
```

---

### Task 4: OpenRouter LLM クライアント

**Files:**
- Create: `scripts/llm_client.py`
- Create: `tests/test_llm_client.py`

**Step 1: テストを書く**

`tests/test_llm_client.py`:

```python
import pytest
import respx
import httpx
import os
from scripts.llm_client import LLMClient


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def make_response(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


@pytest.fixture
def client():
    return LLMClient(api_key="test-key")


@pytest.mark.asyncio
@respx.mock
async def test_translate_titles(client):
    translated = "\n".join([f"{i+1}. 翻訳タイトル{i+1}" for i in range(3)])
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response(translated))
    )
    titles = ["Title 1", "Title 2", "Title 3"]
    result = await client.translate_titles(titles)
    assert len(result) == 3
    assert result[0] == "翻訳タイトル1"
    assert result[1] == "翻訳タイトル2"


@pytest.mark.asyncio
@respx.mock
async def test_translate_titles_fallback_on_count_mismatch(client):
    # LLM が異なる件数を返した場合、元の英語タイトルをフォールバックとして使う
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response("1. 翻訳のみ"))
    )
    titles = ["Title 1", "Title 2", "Title 3"]
    result = await client.translate_titles(titles)
    assert len(result) == 3
    assert result[1] == "Title 2"  # フォールバック


@pytest.mark.asyncio
@respx.mock
async def test_summarize_comments(client):
    summary = "コミュニティでは主にパフォーマンスについて議論されていました。"
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=make_response(summary))
    )
    result = await client.summarize_comments("Test Article", ["comment 1", "comment 2"])
    assert result == summary


@pytest.mark.asyncio
@respx.mock
async def test_summarize_comments_empty(client):
    # コメントがない場合は API を呼ばない
    result = await client.summarize_comments("Test Article", [])
    assert result == ""
```

**Step 2: 失敗確認**

```bash
pytest tests/test_llm_client.py -v
```

**Step 3: LLM クライアント実装**

`scripts/llm_client.py`:

```python
import re
import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-r1"


class LLMClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model

    async def _call(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hn-matome.pages.dev",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(OPENROUTER_URL, headers=headers, json=body)
            resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    async def translate_titles(self, titles: list[str]) -> list[str]:
        """タイトル一覧を一括翻訳する。LLM の応答件数が不一致の場合は元のタイトルをフォールバック"""
        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
        prompt = (
            "以下の英語タイトルを自然な日本語に翻訳してください。\n"
            "番号はそのまま保持し、技術用語はカタカナまたは原語で残してください。\n"
            "翻訳結果のみを出力し、説明は不要です。\n\n"
            f"{numbered}"
        )
        raw = await self._call(prompt)
        return self._parse_numbered_list(raw, fallback=titles)

    async def summarize_comments(self, title: str, comments: list[str]) -> str:
        """コメント群を日本語で要約する"""
        if not comments:
            return ""
        joined = "\n\n".join(comments)
        prompt = (
            f'以下は Hacker News の記事「{title}」に対する英語コメントです。\n'
            "コメント全体を読み、議論の要点を日本語で200字以内にまとめてください。\n"
            "要約のみを出力し、説明は不要です。\n\n"
            f"{joined}"
        )
        return await self._call(prompt)

    @staticmethod
    def _parse_numbered_list(text: str, fallback: list[str]) -> list[str]:
        """'1. xxx' 形式の番号付きリストをパースする"""
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        results = []
        for line in lines:
            m = re.match(r"^\d+\.\s+(.+)$", line)
            if m:
                results.append(m.group(1))
        if len(results) != len(fallback):
            # 件数が不一致の場合は取得できた分だけ使い、残りは元のタイトルで補完
            merged = []
            for i, orig in enumerate(fallback):
                merged.append(results[i] if i < len(results) else orig)
            return merged
        return results
```

**Step 4: テスト通過確認**

```bash
pytest tests/test_llm_client.py -v
```

Expected: 全テスト PASS

**Step 5: コミット**

```bash
git add scripts/llm_client.py tests/test_llm_client.py
git commit -m "feat: OpenRouter LLM クライアントを実装（一括翻訳・コメント要約）"
```

---

### Task 5: Jinja2 テンプレート + CSS

**Files:**
- Create: `scripts/templates/base.html`
- Create: `scripts/templates/archive.html`
- Create: `scripts/templates/index.html`
- Create: `docs/assets/style.css`

**Step 1: base.html を作成**

`scripts/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}HN日報 | HackerNews日本語まとめ{% endblock %}</title>
  <meta name="description" content="{% block description %}HackerNewsのトップ記事を毎日日本語翻訳・AI要約。毎朝JST8時更新。{% endblock %}">
  <meta name="robots" content="index, follow">
  {% block canonical %}<link rel="canonical" href="https://hn-matome.pages.dev/">{% endblock %}
  <!-- OGP -->
  <meta property="og:type" content="{% block og_type %}website{% endblock %}">
  <meta property="og:title" content="{% block og_title %}HN日報{% endblock %}">
  <meta property="og:description" content="{% block og_description %}HackerNewsのトップ記事を毎日日本語翻訳・AI要約{% endblock %}">
  <meta property="og:url" content="{% block og_url %}https://hn-matome.pages.dev/{% endblock %}">
  <meta property="og:site_name" content="HN日報">
  <meta property="og:locale" content="ja_JP">
  <meta name="twitter:card" content="summary">
  <link rel="stylesheet" href="/assets/style.css">
  <!-- Pagefind 検索 -->
  <link href="/pagefind/pagefind-ui.css" rel="stylesheet">
  <script src="/pagefind/pagefind-ui.js"></script>
  {% block head_extra %}{% endblock %}
</head>
<body>
  <header class="site-header">
    <div class="container">
      <a href="/" class="site-title">HN日報</a>
      <nav class="site-nav">
        <a href="/">トップ</a>
        <a href="/about.html">About</a>
      </nav>
    </div>
    <div class="container search-container">
      <div id="search"></div>
    </div>
  </header>
  <main class="container" {% block body_attr %}{% endblock %}>
    {% block content %}{% endblock %}
  </main>
  <footer class="site-footer">
    <div class="container">
      <p>翻訳・要約は AI によるものです。内容の正確性は保証しません。</p>
      <p><a href="/about.html">About</a> · <a href="/privacy.html">プライバシーポリシー</a></p>
    </div>
  </footer>
  <script>
    new PagefindUI({ element: "#search", showSubResults: false, translations: { placeholder: "過去記事を検索..." } });
  </script>
</body>
</html>
```

**Step 2: archive.html を作成**

`scripts/templates/archive.html`:

```html
{% extends "base.html" %}

{% block title %}{{ report.date_ja }} HN日報 | HackerNews日本語まとめ{% endblock %}
{% block description %}{{ report.date_ja }}のHacker Newsトップ{{ report.stories|length }}記事を日本語翻訳・AI要約。{% endblock %}
{% block canonical %}<link rel="canonical" href="https://hn-matome.pages.dev/archive/{{ report.date_str }}.html">{% endblock %}
{% block og_type %}article{% endblock %}
{% block og_title %}{{ report.date_ja }} HN日報{% endblock %}
{% block og_url %}https://hn-matome.pages.dev/archive/{{ report.date_str }}.html{% endblock %}

{% block head_extra %}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{{ report.date_ja }} HackerNews 日本語まとめ トップ{{ report.stories|length }}記事",
  "datePublished": "{{ report.date_str }}T08:00:00+09:00",
  "dateModified": "{{ report.date_str }}T08:00:00+09:00",
  "author": {"@type": "Organization", "name": "HN日報"},
  "publisher": {"@type": "Organization", "name": "HN日報"},
  "inLanguage": "ja",
  "url": "https://hn-matome.pages.dev/archive/{{ report.date_str }}.html"
}
</script>
{% endblock %}

{% block body_attr %}data-pagefind-body{% endblock %}

{% block content %}
<h1 class="page-title">{{ report.date_ja }} のトップ記事</h1>
<nav class="date-nav">
  {% if prev_date %}<a href="/archive/{{ prev_date }}.html">← 前日</a>{% endif %}
  {% if next_date %}<a href="/archive/{{ next_date }}.html">翌日 →</a>{% endif %}
</nav>

<ol class="article-list">
{% for story in report.stories %}
<li class="article-item" id="story-{{ story.rank }}">
  <div class="article-rank">#{{ story.rank }}</div>
  <div class="article-body">
    <h2 class="article-title">
      <a href="{{ story.url or story.hn_url }}" target="_blank" rel="noopener">{{ story.title_ja or story.title_en }}</a>
    </h2>
    <div class="article-meta">
      <span>{{ story.score }}点</span>
      <span>{{ story.comment_count }}コメント</span>
      <a href="{{ story.hn_url }}" target="_blank" rel="noopener">HNで見る</a>
      {% if story.url %}<a href="{{ story.url }}" target="_blank" rel="noopener">元記事</a>{% endif %}
    </div>
    {% if story.summary_ja %}
    <details class="article-summary">
      <summary>コミュニティの反応</summary>
      <p>{{ story.summary_ja }}</p>
    </details>
    {% endif %}
  </div>
</li>
{% endfor %}
</ol>
{% endblock %}
```

**Step 3: index.html テンプレートを作成**

`scripts/templates/index.html`:

```html
{% extends "base.html" %}

{% block title %}HN日報 | HackerNews日本語まとめ - 毎日更新{% endblock %}

{% block head_extra %}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "HN日報",
  "url": "https://hn-matome.pages.dev/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://hn-matome.pages.dev/?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
</script>
{% endblock %}

{% block content %}
<h1 class="page-title">HN日報 — HackerNews 日本語まとめ</h1>
<p class="site-description">Hacker Newsのトップ記事を毎朝JST 8時に日本語翻訳・AI要約してお届けします。</p>

{% if latest_report %}
<section>
  <h2>最新: {{ latest_report.date_ja }}</h2>
  <a href="/archive/{{ latest_report.date_str }}.html" class="btn-latest">今日のまとめを読む</a>
</section>
{% endif %}

<section class="archive-section">
  <h2>アーカイブ</h2>
  <ul class="archive-list">
  {% for date_str in archive_dates %}
    <li><a href="/archive/{{ date_str }}.html">{{ date_str }}</a></li>
  {% endfor %}
  </ul>
</section>
{% endblock %}
```

**Step 4: style.css を作成**

`docs/assets/style.css`:

```css
*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans",
    "Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", sans-serif;
  font-size: 16px;
  line-height: 1.8;
  letter-spacing: 0.02em;
  color: #1A1A1A;
  background: #F6F6EF;
  margin: 0;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 16px;
}

/* ヘッダー */
.site-header {
  background: #E8580A;
  color: #fff;
  padding: 12px 0 8px;
}

.site-header .container {
  display: flex;
  align-items: center;
  gap: 16px;
}

.site-title {
  color: #fff;
  font-weight: 700;
  font-size: 1.2rem;
  text-decoration: none;
}

.site-nav a {
  color: #fff;
  text-decoration: none;
  margin-left: 16px;
  font-size: 0.9rem;
}

.search-container {
  padding-top: 8px;
  padding-bottom: 4px;
}

/* 記事リスト */
.article-list {
  list-style: none;
  padding: 0;
  margin: 24px 0;
}

.article-item {
  display: flex;
  gap: 12px;
  border-bottom: 1px solid #E0E0E0;
  padding: 16px 0;
  background: #fff;
  margin-bottom: 4px;
  padding: 16px;
  border-radius: 4px;
}

.article-rank {
  font-size: 1.2rem;
  font-weight: 700;
  color: #E8580A;
  min-width: 2.5rem;
  text-align: right;
}

.article-title {
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.5;
  margin: 0 0 6px;
}

.article-title a {
  color: #0066CC;
  text-decoration: none;
}

.article-title a:visited { color: #551A8B; }
.article-title a:hover { text-decoration: underline; }

.article-meta {
  font-size: 0.8rem;
  color: #828282;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.article-meta a {
  color: #828282;
  text-decoration: none;
}

.article-meta a:hover { text-decoration: underline; }

/* コメント要約 */
.article-summary {
  margin-top: 8px;
  font-size: 0.9rem;
}

.article-summary summary {
  cursor: pointer;
  color: #555;
  font-size: 0.85rem;
}

.article-summary p {
  margin: 8px 0 0;
  color: #444;
  line-height: 1.8;
}

/* 日付ナビ */
.date-nav {
  display: flex;
  justify-content: space-between;
  margin: 16px 0;
}

.date-nav a {
  color: #0066CC;
  text-decoration: none;
}

/* アーカイブリスト */
.archive-list {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
}

.archive-list a {
  color: #0066CC;
  text-decoration: none;
}

/* フッター */
.site-footer {
  background: #1A1A1A;
  color: #aaa;
  padding: 24px 0;
  margin-top: 48px;
  font-size: 0.85rem;
}

.site-footer a { color: #ccc; }

/* レスポンシブ */
@media (max-width: 600px) {
  .article-item { flex-direction: column; gap: 4px; }
  .article-rank { text-align: left; }
}
```

**Step 5: コミット**

```bash
git add scripts/templates/ docs/assets/style.css
git commit -m "feat: Jinja2 テンプレートと CSS を作成"
```

---

### Task 6: HTML ジェネレーター

**Files:**
- Create: `scripts/generator.py`
- Create: `tests/test_generator.py`

**Step 1: テストを書く**

`tests/test_generator.py`:

```python
import pytest
from pathlib import Path
from datetime import datetime, timezone
from scripts.models import DailyReport, Story, Comment
from scripts.generator import HTMLGenerator


TEMPLATES_DIR = Path(__file__).parent.parent / "scripts" / "templates"


@pytest.fixture
def generator(tmp_path):
    return HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=tmp_path)


@pytest.fixture
def sample_story():
    return Story(
        rank=1, id=100, title_en="Test Story", title_ja="テストストーリー",
        url="https://example.com", hn_url="https://news.ycombinator.com/item?id=100",
        score=200, comment_count=50,
        posted_at=datetime(2026, 3, 26, tzinfo=timezone.utc),
        summary_ja="コミュニティでは主に性能について議論されていました。"
    )


@pytest.fixture
def sample_report(sample_story):
    return DailyReport(date=datetime(2026, 3, 26, tzinfo=timezone.utc), stories=[sample_story])


def test_generate_archive(generator, sample_report, tmp_path):
    generator.generate_archive(sample_report, prev_date=None, next_date=None)
    out = tmp_path / "archive" / "2026-03-26.html"
    assert out.exists()
    content = out.read_text()
    assert "テストストーリー" in content
    assert "2026年3月26日" in content
    assert "data-pagefind-body" in content  # Pagefind のインデックス対象


def test_generate_archive_includes_summary(generator, sample_report, tmp_path):
    generator.generate_archive(sample_report, prev_date=None, next_date=None)
    content = (tmp_path / "archive" / "2026-03-26.html").read_text()
    assert "コミュニティでは主に性能" in content


def test_generate_index(generator, sample_report, tmp_path):
    generator.generate_index(latest_report=sample_report, archive_dates=["2026-03-26"])
    out = tmp_path / "index.html"
    assert out.exists()
    content = out.read_text()
    assert "2026年3月26日" in content
    assert "2026-03-26" in content
```

**Step 2: 失敗確認**

```bash
pytest tests/test_generator.py -v
```

**Step 3: ジェネレーター実装**

`scripts/generator.py`:

```python
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from scripts.models import DailyReport


class HTMLGenerator:
    def __init__(self, templates_dir: Path, output_dir: Path):
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

    def generate_archive(
        self,
        report: DailyReport,
        prev_date: str | None,
        next_date: str | None,
    ) -> Path:
        tmpl = self.env.get_template("archive.html")
        html = tmpl.render(report=report, prev_date=prev_date, next_date=next_date)
        out = self.output_dir / "archive" / f"{report.date_str}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        return out

    def generate_index(
        self,
        latest_report: DailyReport | None,
        archive_dates: list[str],
    ) -> Path:
        tmpl = self.env.get_template("index.html")
        html = tmpl.render(latest_report=latest_report, archive_dates=archive_dates)
        out = self.output_dir / "index.html"
        out.write_text(html, encoding="utf-8")
        return out
```

**Step 4: テスト通過確認**

```bash
pytest tests/test_generator.py -v
```

Expected: 全テスト PASS

**Step 5: コミット**

```bash
git add scripts/generator.py tests/test_generator.py
git commit -m "feat: HTML ジェネレーターを実装（Jinja2 テンプレートレンダリング）"
```

---

### Task 7: サイトマップ・_redirects 生成

**Files:**
- Create: `scripts/sitemap.py`
- Create: `tests/test_sitemap.py`

**Step 1: テストを書く**

`tests/test_sitemap.py`:

```python
import pytest
from pathlib import Path
from scripts.sitemap import SitemapGenerator

BASE_URL = "https://hn-matome.pages.dev"


@pytest.fixture
def gen(tmp_path):
    return SitemapGenerator(output_dir=tmp_path, base_url=BASE_URL)


def test_generate_sitemap(gen, tmp_path):
    gen.generate(archive_dates=["2026-03-25", "2026-03-26"])
    sitemap = tmp_path / "sitemap.xml"
    assert sitemap.exists()
    content = sitemap.read_text()
    assert f"{BASE_URL}/" in content
    assert "2026-03-26" in content
    assert "<urlset" in content


def test_generate_redirects(gen, tmp_path):
    gen.generate_redirects(latest_date="2026-03-26")
    redirects = tmp_path / "_redirects"
    assert redirects.exists()
    content = redirects.read_text()
    assert "/archive/2026-03-26.html" in content


def test_generate_robots(gen, tmp_path):
    gen.generate_robots()
    robots = tmp_path / "robots.txt"
    assert robots.exists()
    content = robots.read_text()
    assert "Sitemap:" in content
    assert f"{BASE_URL}/sitemap.xml" in content
```

**Step 2: 失敗確認**

```bash
pytest tests/test_sitemap.py -v
```

**Step 3: サイトマップ生成実装**

`scripts/sitemap.py`:

```python
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


class SitemapGenerator:
    def __init__(self, output_dir: Path, base_url: str):
        self.output_dir = output_dir
        self.base_url = base_url.rstrip("/")

    def generate(self, archive_dates: list[str]) -> Path:
        root = Element("urlset")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        def add_url(loc: str, changefreq: str, priority: str, lastmod: str | None = None):
            url = SubElement(root, "url")
            SubElement(url, "loc").text = loc
            if lastmod:
                SubElement(url, "lastmod").text = lastmod
            SubElement(url, "changefreq").text = changefreq
            SubElement(url, "priority").text = priority

        add_url(f"{self.base_url}/", "daily", "1.0")
        add_url(f"{self.base_url}/about.html", "monthly", "0.3")

        for date_str in sorted(archive_dates, reverse=True):
            add_url(
                f"{self.base_url}/archive/{date_str}.html",
                "never", "0.8", lastmod=date_str
            )

        xml_str = parseString(tostring(root, encoding="unicode")).toprettyxml(indent="  ")
        # minidom が追加する XML 宣言を差し替える
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(xml_str.splitlines()[1:])

        out = self.output_dir / "sitemap.xml"
        out.write_text(xml_str, encoding="utf-8")
        return out

    def generate_redirects(self, latest_date: str) -> Path:
        content = f"/ /archive/{latest_date}.html 302\n"
        out = self.output_dir / "_redirects"
        out.write_text(content, encoding="utf-8")
        return out

    def generate_robots(self) -> Path:
        content = f"User-agent: *\nAllow: /\nSitemap: {self.base_url}/sitemap.xml\n"
        out = self.output_dir / "robots.txt"
        out.write_text(content, encoding="utf-8")
        return out
```

**Step 4: テスト通過確認**

```bash
pytest tests/test_sitemap.py -v
```

**Step 5: コミット**

```bash
git add scripts/sitemap.py tests/test_sitemap.py
git commit -m "feat: sitemap.xml / _redirects / robots.txt 自動生成を実装"
```

---

### Task 8: 静的ページ（about.html / privacy.html）

**Files:**
- Create: `scripts/templates/about.html`
- Create: `scripts/templates/privacy.html`
- Modify: `scripts/generator.py`

**Step 1: about.html テンプレート**

`scripts/templates/about.html`:

```html
{% extends "base.html" %}
{% block title %}About | HN日報{% endblock %}
{% block content %}
<h1>HN日報について</h1>
<p>HN日報は、世界最大級のテック系ニュースサイト <a href="https://news.ycombinator.com" target="_blank" rel="noopener">Hacker News</a> のトップ記事を、毎朝 JST 8時に自動で日本語翻訳・AI要約して公開するサービスです。</p>
<h2>提供内容</h2>
<ul>
  <li>Hacker News 上位30記事のタイトル日本語翻訳</li>
  <li>英語コミュニティのコメント・議論の日本語要約</li>
  <li>日付別アーカイブ（過去記事の閲覧・検索）</li>
</ul>
<h2>免責事項</h2>
<p>翻訳・要約は AI（大規模言語モデル）によるものです。内容の正確性・完全性は保証しません。重要な情報は必ず原文をご確認ください。</p>
<h2>お問い合わせ</h2>
<p>GitHub Issues よりご連絡ください。</p>
{% endblock %}
```

**Step 2: privacy.html テンプレート**

`scripts/templates/privacy.html`:

```html
{% extends "base.html" %}
{% block title %}プライバシーポリシー | HN日報{% endblock %}
{% block content %}
<h1>プライバシーポリシー</h1>
<p>最終更新: 2026年3月26日</p>
<h2>取得する情報</h2>
<p>当サービスはアクセスログ（IPアドレス、ブラウザ情報、参照元URL）を収集します。個人を特定できる情報は収集しません。</p>
<h2>広告について</h2>
<p>当サービスは Google AdSense を利用しており、Google およびその提携企業がクッキーを使用して広告を配信する場合があります。</p>
<p>Google による広告のカスタマイズを無効にするには、<a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google 広告設定</a>をご利用ください。</p>
<h2>アクセス解析</h2>
<p>Cloudflare Analytics を使用しています。収集データは匿名化されており、個人を特定しません。</p>
{% endblock %}
```

**Step 3: generator.py に静的ページ生成を追加**

`scripts/generator.py` の `HTMLGenerator` クラスに以下を追加:

```python
def generate_static_pages(self) -> None:
    """about.html と privacy.html を生成する（初回のみ実行すれば十分）"""
    for page in ("about", "privacy"):
        tmpl = self.env.get_template(f"{page}.html")
        html = tmpl.render()
        out = self.output_dir / f"{page}.html"
        out.write_text(html, encoding="utf-8")
```

**Step 4: コミット**

```bash
git add scripts/templates/about.html scripts/templates/privacy.html scripts/generator.py
git commit -m "feat: about / privacy 静的ページを追加"
```

---

### Task 9: メインオーケストレーター

**Files:**
- Create: `scripts/fetch_and_generate.py`

**Step 1: メインスクリプト実装**

`scripts/fetch_and_generate.py`:

```python
#!/usr/bin/env python3
"""
HN日報 メインスクリプト
HN API からデータ取得 → OpenRouter で翻訳・要約 → 静的 HTML 生成
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scripts.hn_client import HNClient
from scripts.llm_client import LLMClient
from scripts.models import DailyReport
from scripts.generator import HTMLGenerator
from scripts.sitemap import SitemapGenerator

DOCS_DIR = Path(__file__).parent.parent / "docs"
TEMPLATES_DIR = Path(__file__).parent / "templates"
BASE_URL = "https://hn-matome.pages.dev"
JST = timezone(timedelta(hours=9))


def get_existing_dates() -> list[str]:
    """既存のアーカイブ日付一覧を取得する"""
    archive_dir = DOCS_DIR / "archive"
    if not archive_dir.exists():
        return []
    return sorted(
        [p.stem for p in archive_dir.glob("*.html")],
        reverse=True
    )


async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(tz=JST).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"実行日時: {today.strftime('%Y-%m-%d %H:%M')} JST")

    generator = HTMLGenerator(templates_dir=TEMPLATES_DIR, output_dir=DOCS_DIR)
    sitemap_gen = SitemapGenerator(output_dir=DOCS_DIR, base_url=BASE_URL)

    # HN データ取得
    print("HN API からトップ30記事を取得中...")
    async with HNClient() as hn:
        stories = await hn.fetch_top_stories(limit=30)
        print(f"{len(stories)} 件取得完了。コメント取得中...")
        for story in stories:
            story.comments = await hn.fetch_comments(story, max_comments=5)

    # LLM で翻訳・要約
    llm = LLMClient(api_key=api_key)
    print("タイトルを一括翻訳中...")
    titles_en = [s.title_en for s in stories]
    titles_ja = await llm.translate_titles(titles_en)
    for story, ja in zip(stories, titles_ja):
        story.title_ja = ja

    print("コメントを要約中...")
    for story in stories:
        if story.comments:
            texts = [c.text for c in story.comments if c.text]
            story.summary_ja = await llm.summarize_comments(story.title_en, texts)

    # HTML 生成
    report = DailyReport(date=today, stories=stories)
    existing_dates = get_existing_dates()

    # prev / next 日付を計算
    today_str = today.strftime("%Y-%m-%d")
    all_dates = sorted(set(existing_dates + [today_str]))
    idx = all_dates.index(today_str)
    prev_date = all_dates[idx - 1] if idx > 0 else None
    next_date = all_dates[idx + 1] if idx < len(all_dates) - 1 else None

    print(f"archive/{today_str}.html を生成中...")
    generator.generate_archive(report, prev_date=prev_date, next_date=next_date)

    # index + サイトマップ更新
    archive_dates = sorted(set(existing_dates + [today_str]), reverse=True)
    generator.generate_index(latest_report=report, archive_dates=archive_dates)
    generator.generate_static_pages()
    sitemap_gen.generate(archive_dates=archive_dates)
    sitemap_gen.generate_redirects(latest_date=today_str)
    sitemap_gen.generate_robots()

    print("完了")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: 動作確認（ドライラン）**

実際の API を呼ぶため、環境変数を設定してから実行する:

```bash
OPENROUTER_API_KEY=your_key_here python -m scripts.fetch_and_generate
```

Expected: `docs/archive/YYYY-MM-DD.html` が生成される

**Step 3: コミット**

```bash
git add scripts/fetch_and_generate.py
git commit -m "feat: メインオーケストレーター（fetch_and_generate.py）を実装"
```

---

### Task 10: GitHub Actions ワークフロー

**Files:**
- Create: `.github/workflows/update.yml`

**Step 1: ワークフロー作成**

`.github/workflows/update.yml`:

```yaml
name: HN日報 毎日更新

on:
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00 = JST 8:00
  workflow_dispatch:       # 手動実行用

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

**Step 2: GitHub Secrets に API キーを登録**

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を追加:

- `OPENROUTER_API_KEY`: OpenRouter のAPIキー

**Step 3: 手動実行でテスト**

```
GitHub Actions タブ → "HN日報 毎日更新" → "Run workflow"
```

ジョブが成功し `docs/` に HTML が生成されることを確認。

**Step 4: コミット**

```bash
git add .github/workflows/update.yml
git commit -m "feat: GitHub Actions 毎日更新ワークフローを追加"
```

---

### Task 11: Cloudflare Pages セットアップ

**これはコード変更ではなくインフラ設定作業のため、手順のみ記載する。**

**Step 1: Cloudflare Pages プロジェクト作成**

1. Cloudflare Dashboard にログイン
2. Workers & Pages → Create application → Pages
3. "Connect to Git" → GitHub リポジトリを選択
4. ビルド設定:
   - ビルドコマンド: **（空欄）**
   - 出力ディレクトリ: `docs`
5. "Save and Deploy"

**Step 2: カスタムドメインの設定（任意）**

1. Cloudflare で独自ドメインを取得（例: `hn-matome.com`）
2. Pages プロジェクトの "Custom domains" → ドメインを追加
3. DNS は Cloudflare が自動設定

**Step 3: デプロイ確認**

`docs/` フォルダが存在し index.html があれば初回デプロイ完了。
URL は `https://hn-matome.pages.dev` 形式で発行される。

---

### Task 12: 全テストの実行・最終確認

**Step 1: 全テストを実行**

```bash
pytest -v
```

Expected: 全テスト PASS

**Step 2: ローカルで生成物を確認**

```bash
# Python の簡易サーバーで確認
python -m http.server 8000 --directory docs
# ブラウザで http://localhost:8000 を開く
```

確認項目:
- [ ] トップページが表示される
- [ ] アーカイブリンクが機能する
- [ ] 日本語タイトルが正しく表示される
- [ ] コメント要約が `<details>` で表示される
- [ ] prev/next ナビゲーションが機能する
- [ ] モバイル表示（幅 375px）でレイアウトが崩れない

**Step 3: Pagefind を手動実行して検索を確認**

```bash
npx pagefind --site docs --output-path docs/pagefind
python -m http.server 8000 --directory docs
# 検索ボックスに "AI" 等を入力して結果が表示されることを確認
```

**Step 4: 最終コミット**

```bash
git add .
git diff --cached --quiet || git commit -m "docs: 初期アーカイブとサイト生成物を追加"
git push
```

---

## 完了チェックリスト

- [ ] Task 1: プロジェクト骨格
- [ ] Task 2: データモデル
- [ ] Task 3: HN API クライアント
- [ ] Task 4: OpenRouter LLM クライアント
- [ ] Task 5: Jinja2 テンプレート + CSS
- [ ] Task 6: HTML ジェネレーター
- [ ] Task 7: サイトマップ・_redirects 生成
- [ ] Task 8: 静的ページ（about / privacy）
- [ ] Task 9: メインオーケストレーター
- [ ] Task 10: GitHub Actions ワークフロー
- [ ] Task 11: Cloudflare Pages セットアップ
- [ ] Task 12: 全テスト・最終確認

## 次のステップ（MVP 後）

- Google Search Console にサイトを登録・sitemap.xml を送信
- 30日分のアーカイブが蓄積したら AdSense 申請
- OGP 画像（Pillow で自動生成）を追加
