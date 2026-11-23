"""
Google Gemini Provider implementation (Generous Free Quota).
"""

from typing import List
import httpx
from postpilot.ai.base import BaseAIProvider
from postpilot.utils.config import settings


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model

    def get_provider_name(self) -> str:
        return "gemini"

    async def test_connection(self) -> bool:
        if not self.api_key:
            return False
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                return res.status_code == 200
        except Exception:
            return False

    async def generate(
        self, prompt: str, system_prompt: str, count: int = 1, temperature: float = 0.85
    ) -> List[str]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        full_prompt = f"{system_prompt}\n\nTask:\n{prompt}\n\nPlease output exactly {count} distinct post options separated by '---'."
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            posts = [p.strip() for p in text.split("---") if p.strip()]
            return posts[:count]
