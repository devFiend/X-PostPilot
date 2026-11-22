"""
Unit tests for Telegram Bot Security, Diagnostics, and Command Handlers.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from postpilot.telegram.security import owner_only
from postpilot.telegram.handlers import format_system_health, status_command, postnow_command
from postpilot.telegram.keyboards import get_status_keyboard
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


def test_format_system_health(in_memory_db):
    """Verify system health report formats without error and includes diagnostic metrics."""
    text, keyboard = format_system_health(in_memory_db)
    assert "PostPilot System Health & Diagnostics" in text
    assert "Core Status:" in text
    assert "AI Engine:" in text
    assert "Database:" in text
    assert "Drip Schedule:" in text

    # Verify refresh button exists in keyboard
    buttons = keyboard.inline_keyboard
    assert any("refresh_status" == btn.callback_data for row in buttons for btn in row)


@pytest.mark.asyncio
async def test_status_command_with_callback_query(in_memory_db, monkeypatch):
    """Verify status_command handles callback queries where update.message is None."""
    monkeypatch.setattr(settings, "TELEGRAM_OWNER_ID", 123456789)

    update = MagicMock()
    update.effective_user.id = 123456789
    update.message = None  # Crucial: callback queries have update.message == None
    query = MagicMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query
    update.effective_message = query.message
    context = MagicMock()

    with patch("postpilot.telegram.handlers.get_db", return_value=in_memory_db):
        await status_command(update, context)

    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args[0]
    assert "System Health & Diagnostics" in call_args[0]


@pytest.mark.asyncio
async def test_postnow_command(monkeypatch):
    """Verify /postnow command generates direct X compose intent URL."""
    monkeypatch.setattr(settings, "TELEGRAM_OWNER_ID", 123456789)

    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_message = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.message = update.effective_message

    context = MagicMock()
    context.args = ["Launching", "v2.0", "today!"]

    await postnow_command(update, context)

    update.effective_message.reply_text.assert_called_once()
    reply_kwargs = update.effective_message.reply_text.call_args[1]
    keyboard = reply_kwargs.get("reply_markup")
    assert keyboard is not None
    post_btn = keyboard.inline_keyboard[0][0]
    assert "https://twitter.com/intent/tweet?text=" in post_btn.url
    assert "Launching%20v2.0%20today%21" in post_btn.url
