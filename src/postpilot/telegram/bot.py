"""
Telegram Bot Application runner.
Registers native menu commands (set_my_commands), dashboard buttons, and callback query handlers.
Includes automatic bot profile branding (name, description, and avatar icon).
"""

from pathlib import Path
from telegram import BotCommand, InputProfilePhotoStatic
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
    doctor_command,
    postnow_command,
    setavatar_command,
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
    Registers native command menu and applies bot profile branding (name, description, avatar).
    """
    commands = [
        BotCommand("ideas", "⚡ Generate on-demand post ideas"),
        BotCommand("creators", "👥 View your tracked creator pool"),
        BotCommand("track", "🧬 Track and analyze a creator"),
        BotCommand("inspire", "🎨 Draft posts in a creator's style"),
        BotCommand("drafts", "📝 Review pending drafts"),
        BotCommand("queue", "🗓️ Inspect scheduled queue"),
        BotCommand("status", "📊 Real-time health & diagnostics"),
        BotCommand("postnow", "🚀 1-tap custom post composer"),
        BotCommand("doctor", "🩺 Run system diagnostics"),
        BotCommand("setavatar", "🖼️ Set bot profile photo"),
        BotCommand("pause", "⏸ Pause content delivery"),
        BotCommand("resume", "▶ Resume content delivery"),
        BotCommand("help", "📖 User guide & commands"),
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception as e:
        print(f"Notice: Could not register Telegram menu commands: {e}")

    # Set bot profile name and descriptions
    try:
        await application.bot.set_my_name("PostPilot | X Copilot")
        await application.bot.set_my_description(
            "Your personal AI content management & publishing copilot for X (Twitter).\n"
            "Blends creator intelligence, TweetDNA style cloning, and ban-proof 1-tap publishing."
        )
        await application.bot.set_my_short_description("AI Content Management & Publishing Copilot for X")
    except Exception:
        pass

    # Auto-apply official bot avatar if present
    possible_paths = [
        Path(__file__).resolve().parent.parent / "assets" / "avatar.jpg",
        Path(__file__).resolve().parent.parent.parent / "assets" / "avatar.jpg",
        Path("assets/avatar.jpg"),
        Path("src/postpilot/assets/avatar.jpg"),
    ]
    for p in possible_paths:
        if p.exists():
            try:
                with open(p, "rb") as f:
                    await application.bot.set_my_profile_photo(InputProfilePhotoStatic(f))
                print(f"✔ Applied official PostPilot avatar to Telegram bot from {p.name}")
                break
            except Exception:
                # May fail if avatar is already set or rate limited by Telegram
                pass


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
    app.add_handler(CommandHandler("doctor", doctor_command))
    app.add_handler(CommandHandler("postnow", postnow_command))
    app.add_handler(CommandHandler("setavatar", setavatar_command))
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
