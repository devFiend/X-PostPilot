"""
Ollama Local Provider implementation ($0 Offline execution).
"""

from typing import List
import httpx
from postpilot.ai.base import BaseAIProvider
from postpilot.utils.config import settings


class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

    def get_provider_name(self) -> str:
        return "ollama"

    async def test_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def generate(
        self, prompt: str, system_prompt: str, count: int = 1, temperature: float = 0.85
    ) -> List[str]:
        endpoint = f"{self.base_url}/api/generate"
        full_prompt = f"{system_prompt}\n\nUser topic: {prompt}\n\nReturn {count} post variants separated by '---'."
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(endpoint, json=payload)
            res.raise_for_status()
            data = res.json()
            response_text = data.get("response", "")
            posts = [p.strip() for p in response_text.split("---") if p.strip()]
            return posts[:count]
