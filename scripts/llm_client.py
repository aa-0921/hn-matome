import re
import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-r1:free"


class LLMClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model

    async def _call(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hn-matome-2ht.pages.dev",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(OPENROUTER_URL, headers=headers, json=body)
            resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        if content is None:
            return ""
        if isinstance(content, str):
            return content.strip()
        return str(content).strip()

    async def translate_titles(self, titles: list[str]) -> list[str]:
        """タイトル一覧を一括翻訳する。件数不一致の場合は元のタイトルをフォールバック"""
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
            "コメント全体を読み、議論の要点を日本語で300〜400字でまとめてください。\n"
            "以下の構成で書いてください:\n"
            "・主な議論点（コミュニティで最も議論されたポイント）\n"
            "・賛否両論（意見が分かれた点があれば）\n"
            "・注目コメント（特に洞察のあるコメントがあれば紹介）\n"
            "要約のみを出力し、説明は不要です。\n\n"
            f"{joined}"
        )
        return await self._call(prompt)

    async def generate_editor_notes(self, titles_ja: list[str], titles_en: list[str]) -> list[str]:
        """各記事について日本の開発者向けの「ひとこと解説」を一括生成する"""
        numbered = "\n".join(
            f"{i+1}. {ja} ({en})" for i, (ja, en) in enumerate(zip(titles_ja, titles_en))
        )
        prompt = (
            "あなたはテック系メディアの編集者です。以下のHacker News記事について、\n"
            "日本の開発者向けの「ひとこと解説」を各記事100〜150字で書いてください。\n\n"
            "【重要なルール】\n"
            "・単なる記事の要約ではなく、独自の視点を含めてください\n"
            "・なぜ今この記事が注目されているか、背景を説明してください\n"
            "・日本のテック業界との関連性があれば触れてください\n"
            "・です/ます調で書いてください\n"
            "・番号はそのまま保持してください\n"
            "・解説のみを出力し、前置きや説明は不要です\n\n"
            f"{numbered}"
        )
        raw = await self._call(prompt)
        return self._parse_numbered_list(raw, fallback=[""] * len(titles_ja))

    async def categorize_stories(self, titles_en: list[str]) -> list[str]:
        """記事を技術カテゴリに分類する"""
        categories = [
            "AI/ML", "Web開発", "システム/インフラ", "セキュリティ",
            "プログラミング言語", "スタートアップ/ビジネス", "OSS",
            "データベース", "モバイル", "DevOps", "キャリア/働き方", "その他"
        ]
        numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles_en))
        prompt = (
            "以下のHacker News記事を、最も適切なカテゴリ1つに分類してください。\n\n"
            f"カテゴリ一覧: {', '.join(categories)}\n\n"
            "番号はそのまま保持し、「番号. カテゴリ名」の形式で出力してください。\n"
            "分類結果のみを出力し、説明は不要です。\n\n"
            f"{numbered}"
        )
        raw = await self._call(prompt)
        return self._parse_numbered_list(raw, fallback=["その他"] * len(titles_en))

    async def generate_weekly_analysis(self, stories_text: str) -> str:
        """1週間分の記事データからトレンド分析を生成する。返値はJSON文字列"""
        prompt = (
            "あなたは日本のテックメディアの編集者です。以下は今週のHacker Newsトップ記事一覧です。\n"
            "これらの記事からテクノロジートレンドを分析し、日本の開発者にとっての意味を解説してください。\n"
            "単なる要約ではなく、独自の視点と分析を含めてください。\n\n"
            "以下のJSON形式で出力してください（JSONのみ、説明不要）:\n"
            '{\n'
            '  "overview": "今週の概要（200字程度）",\n'
            '  "trends": [\n'
            '    {\n'
            '      "topic": "トレンドのテーマ名",\n'
            '      "analysis": "分析（400〜600字）",\n'
            '      "impact": "日本の開発者への影響（200字程度）",\n'
            '      "related_titles": ["関連記事タイトル1", "関連記事タイトル2"]\n'
            '    }\n'
            '  ],\n'
            '  "editorial_comment": "編集者の一言（150字程度、来週への展望）"\n'
            '}\n\n'
            "トレンドは3〜5個を特定してください。\n\n"
            f"{stories_text}"
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
            merged = []
            for i, orig in enumerate(fallback):
                merged.append(results[i] if i < len(results) else orig)
            return merged
        return results
