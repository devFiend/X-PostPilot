"""
AIRouter: Intelligent routing and fallback among Groq, Gemini, and Ollama.
"""

from typing import List, Optional
from postpilot.ai.base import BaseAIProvider
from postpilot.ai.groq import GroqProvider
from postpilot.ai.gemini import GeminiProvider
from postpilot.ai.ollama import OllamaProvider
from postpilot.utils.config import settings


class AIRouter:
    def __init__(self):
        self.providers: dict[str, BaseAIProvider] = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "ollama": OllamaProvider(),
        }

    def get_provider(self, name: Optional[str] = None) -> BaseAIProvider:
        target = name.lower() if name else settings.DEFAULT_AI_PROVIDER.lower()
        if target not in self.providers:
            target = "groq"
        return self.providers[target]

    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: str,
        preferred: Optional[str] = None,
        count: int = 1,
        temperature: float = 0.85,
    ) -> tuple[List[str], str]:
        """Try preferred provider; fall back automatically if requested and needed."""
        provider_name = preferred or settings.DEFAULT_AI_PROVIDER
        candidates = [provider_name] + [p for p in ["groq", "gemini", "ollama"] if p != provider_name]

        last_error = None
        for prov_id in candidates:
            provider = self.providers[prov_id]
            try:
                results = await provider.generate(prompt, system_prompt, count=count, temperature=temperature)
                if results:
                    return results, prov_id
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All AI providers failed. Last error: {last_error}")
