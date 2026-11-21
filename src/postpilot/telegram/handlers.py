"""
Telegram Bot handlers for drafting, approval, and queue management.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from postpilot.telegram.security import owner_only
from postpilot.database.db import get_db
from postpilot.database.models import Draft, PostStatus
from postpilot.services.content import ContentService
from postpilot.services.publishing import PublishingService


@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Welcome to PostPilot!*\n\n"
        "Your personal AI social media copilot for X.\n\n"
        "Commands:\n"
        "• `/generate <topic>` - Draft new X posts with AI\n"
        "• `/drafts` - Inspect drafts and approve them\n"
        "• `/queue` - View scheduled & publishing queue\n"
        "• `/status` - Check system & provider health\n"
        "• `/pause` - Emergency pause autopilot\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


@owner_only
async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/generate <topic>`\nExample: `/generate Why developers should learn AI`", parse_mode="Markdown")
        return

    topic = " ".join(args)
    await update.message.reply_text(f"🧠 Generating posts for topic: *{topic}*...", parse_mode="Markdown")

    db = get_db()
    try:
        service = ContentService(db)
        drafts = await service.generate_drafts(topic=topic, count=3)
        for draft in drafts:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{draft.id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft.id}"),
                ],
                [
                    InlineKeyboardButton("📋 Copy Post", callback_data=f"copy_{draft.id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"📝 *Draft #{draft.id}* ({draft.character_count} chars):\n\n`{draft.content}`"
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()
