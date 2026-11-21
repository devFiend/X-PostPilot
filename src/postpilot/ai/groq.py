"""
Groq AI Provider implementation (High-speed LLaMA-3 / GPT-OSS).
"""

from typing import List
import httpx
from postpilot.ai.base import BaseAIProvider
from postpilot.utils.config import settings


class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def get_provider_name(self) -> str:
        return "groq"

    async def test_connection(self) -> bool:
        if not self.api_key:
            return False
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
                return res.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str, system_prompt: str, count: int = 1) -> List[str]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured in .env")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        user_message = (
            f"{prompt}\n\n"
            f"Please generate exactly {count} distinct post variants. "
            f"Separate each variant with '---' on its own line."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(self.endpoint, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            posts = [p.strip() for p in content.split("---") if p.strip()]
            return posts[:count]
