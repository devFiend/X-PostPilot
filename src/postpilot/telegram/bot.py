"""
Telegram Bot Application runner.
Registers all commands and inline callback query handlers.
"""

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from postpilot.utils.config import settings
from postpilot.telegram.handlers import (
    start_command,
    help_command,
    status_command,
    generate_command,
    drafts_command,
    queue_command,
    pause_command,
    resume_command,
    callback_handler,
)


def run_telegram_bot():
    """Start the Telegram polling loop."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not configured in .env.")
        return

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("generate", generate_command))
    app.add_handler(CommandHandler("drafts", drafts_command))
    app.add_handler(CommandHandler("queue", queue_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))

    # Register callback query handler for inline button clicks
    app.add_handler(CallbackQueryHandler(callback_handler))

    print(f"PostPilot Telegram Bot is running in long-polling mode (Owner ID: {settings.TELEGRAM_OWNER_ID or 'Not Set'})...")
    app.run_polling()
