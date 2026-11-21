"""
Telegram Bot Application runner.
Registers all commands, TweetDNA handlers, and inline callback query handlers.
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
    track_command,
    creators_command,
    untrack_command,
    ideas_command,
    inspire_command,
    callback_handler,
)


def run_telegram_bot():
    """Start the Telegram polling loop."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not configured in .env.")
        return

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Core commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("generate", generate_command))
    app.add_handler(CommandHandler("drafts", drafts_command))
    app.add_handler(CommandHandler("queue", queue_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))

    # TweetDNA & Creator Intelligence commands
    app.add_handler(CommandHandler("track", track_command))
    app.add_handler(CommandHandler("creators", creators_command))
    app.add_handler(CommandHandler("untrack", untrack_command))
    app.add_handler(CommandHandler("ideas", ideas_command))
    app.add_handler(CommandHandler("inspire", inspire_command))

    # Inline button callback queries
    app.add_handler(CallbackQueryHandler(callback_handler))

    print(f"PostPilot + TweetDNA Telegram Bot is running in long-polling mode (Owner ID: {settings.TELEGRAM_OWNER_ID or 'Not Set'})...")
    app.run_polling()
