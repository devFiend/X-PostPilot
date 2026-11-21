"""
Telegram Bot Application runner.
"""

from telegram.ext import ApplicationBuilder, CommandHandler
from postpilot.utils.config import settings
from postpilot.telegram.handlers import start_command, generate_command


def run_telegram_bot():
    """Start the Telegram polling loop."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not configured in .env.")
        return

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("generate", generate_command))

    print("PostPilot Telegram Bot is running in long-polling mode...")
    app.run_polling()
