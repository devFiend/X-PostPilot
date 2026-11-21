"""
Telegram Bot Engine and Security Middleware.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from postpilot.utils.config import settings


def owner_only(func):
    """Decorator to ensure only the authorized TELEGRAM_OWNER_ID can invoke commands."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or (settings.TELEGRAM_OWNER_ID and user.id != settings.TELEGRAM_OWNER_ID):
            if update.message:
                await update.message.reply_text("⛔ Unauthorized. This PostPilot bot is private to its owner.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
