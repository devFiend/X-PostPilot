"""
Abstract base class for AI Providers.
"""

from abc import ABC, abstractmethod
from typing import List


class BaseAIProvider(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, system_prompt: str, count: int = 1, temperature: float = 0.85
    ) -> List[str]:
        """Generate a list of candidate social posts."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify API key and provider availability."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier name."""
        pass
