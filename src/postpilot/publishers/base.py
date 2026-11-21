"""
Abstract publisher interface and response structures.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional


class PublishResult(BaseModel):
    success: bool
    platform: str = "X"
    post_id: Optional[str] = None
    url: Optional[str] = None
    method: str  # "manual" or "x_api"
    error_message: Optional[str] = None


class BasePublisher(ABC):
    @abstractmethod
    async def publish(self, content: str) -> PublishResult:
        """Publish post or prepare manual handoff."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connection or readiness."""
        pass
