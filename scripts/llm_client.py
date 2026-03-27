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
            "HTTP-Referer": "https://hn-matome-2ht.pages.dev",
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
            merged = []
            for i, orig in enumerate(fallback):
                merged.append(results[i] if i < len(results) else orig)
            return merged
        return results
