"""
Telegram Bot Application runner.
Registers native menu commands (set_my_commands), dashboard buttons, and callback query handlers.
"""

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
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
    dashboard_text_handler,
    callback_handler,
)


async def setup_bot_commands(application):
    """
    Registers the native command menu visible as the blue 'Menu' button in Telegram.
    Users can tap the button to see all commands with descriptions.
    """
    commands = [
        BotCommand("ideas", "⚡ Generate on-demand post ideas"),
        BotCommand("creators", "👥 View your tracked creator pool"),
        BotCommand("track", "🧬 Track and analyze a creator"),
        BotCommand("inspire", "🎨 Draft posts in a creator's style"),
        BotCommand("drafts", "📝 Review pending drafts"),
        BotCommand("queue", "🗓️ Inspect scheduled queue"),
        BotCommand("status", "📊 System health & stats"),
        BotCommand("pause", "⏸ Pause hourly delivery"),
        BotCommand("resume", "▶ Resume hourly delivery"),
        BotCommand("help", "📖 User guide & commands"),
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception as e:
        print(f"Notice: Could not register Telegram menu commands: {e}")


def run_telegram_bot():
    """Start the Telegram polling loop."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not configured in .env.")
        return

    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(setup_bot_commands)
        .build()
    )

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

    # Persistent Reply Keyboard text handler (Quick Ideas, Review Drafts, etc.)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dashboard_text_handler))

    # Inline button callback queries
    app.add_handler(CallbackQueryHandler(callback_handler))

    print(f"PostPilot + TweetDNA Telegram Bot is running in long-polling mode (Owner ID: {settings.TELEGRAM_OWNER_ID or 'Not Set'})...")
    app.run_polling()
