"""
Unit tests for Telegram Bot Security & Owner Authorization.
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from postpilot.telegram.security import owner_only
from postpilot.utils.config import settings


@pytest.mark.asyncio
async def test_owner_security_blocks_unauthorized_user(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_OWNER_ID", 123456789)

    mock_func = AsyncMock()
    decorated = owner_only(mock_func)

    # Simulate unauthorized user update
    update = MagicMock()
    update.effective_user.id = 999999999  # attacker or stranger
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await decorated(update, context)

    # Verify protected function was NEVER called
    mock_func.assert_not_called()
    update.message.reply_text.assert_called_once()
    assert "Unauthorized" in update.message.reply_text.call_args[0][0]
