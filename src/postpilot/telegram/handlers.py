"""
Telegram Bot handlers for drafting, approval, queue management, and autopilot controls.
"""

import urllib.parse
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes
from postpilot.telegram.security import owner_only
from postpilot.telegram.keyboards import get_draft_keyboard, get_queue_keyboard
from postpilot.database.db import get_db
from postpilot.database.models import Draft, PostStatus, ScheduledPost
from postpilot.database.repositories import DraftRepository, ScheduleRepository
from postpilot.services.content import ContentService
from postpilot.services.publishing import PublishingService
from postpilot.services.autopilot import AutopilotService
from postpilot.utils.config import settings


@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🚀 *Welcome to PostPilot Control Center*\n\n"
        "Your private, $0-first social media copilot for X.\n\n"
        "*Core Commands:*\n"
        "• `/generate <topic>` — AI post draft generator\n"
        "• `/drafts` — Review and approve pending drafts\n"
        "• `/queue` — View scheduled posts\n"
        "• `/status` — System health & provider check\n"
        "• `/pause` — Emergency stop / pause autopilot\n"
        "• `/resume` — Resume autopilot\n"
        "• `/help` — Detailed guidance\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


@owner_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 *PostPilot Usage Guide*\n\n"
        "*1. Generating Content*\n"
        "Type `/generate Why developers love clean architecture` to generate 3 post variants.\n"
        "Each card provides `[Approve]`, `[Reject]`, `[Copy Post]`, and `[Schedule]` buttons.\n\n"
        "*2. Publishing*\n"
        "• When scheduled posts are due in Manual Mode ($0), you get an instant notification with a one-tap copy block.\n"
        "• In X API mode, approved posts publish directly.\n\n"
        "*3. Autopilot*\n"
        "Use `/pause` or `/resume` at any time to halt automated actions."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


@owner_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        auto_state = "⏸ PAUSED" if autopilot.is_paused() else ("▶ ENABLED" if autopilot.is_enabled() else "⏹ DISABLED")
        drafts_count = db.query(Draft).count()
        scheduled_count = db.query(ScheduledPost).filter(ScheduledPost.status == PostStatus.SCHEDULED.value).count()

        msg = (
            "📊 *PostPilot Health Status*\n\n"
            f"• *AI Provider:* `{settings.DEFAULT_AI_PROVIDER.upper()}`\n"
            f"• *Publish Method:* `{settings.DEFAULT_PUBLISH_METHOD.upper()}`\n"
            f"• *Autopilot:* `{auto_state}`\n"
            f"• *Drafts in DB:* `{drafts_count}`\n"
            f"• *Pending Scheduled:* `{scheduled_count}`\n"
            f"• *Timezone:* `{settings.TIMEZONE}`\n"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/generate <topic>`\nExample: `/generate Why developers should learn AI`", parse_mode="Markdown")
        return

    topic = " ".join(args)
    await update.message.reply_text(f"🧠 *Generating 3 post options for:* _{topic}_...", parse_mode="Markdown")

    db = get_db()
    try:
        service = ContentService(db)
        drafts = await service.generate_drafts(topic=topic, count=3)
        for draft in drafts:
            reply_markup = get_draft_keyboard(draft.id)
            encoded = urllib.parse.quote(draft.content)
            intent_url = f"https://twitter.com/intent/tweet?text={encoded}"
            text = (
                f"📝 *Draft #{draft.id}* ({draft.character_count} chars):\n\n"
                f"```text\n{draft.content}\n```\n\n"
                f"[Open in X Composer]({intent_url})"
            )
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating posts: {e}")
    finally:
        db.close()


@owner_only
async def drafts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        repo = DraftRepository(db)
        drafts = repo.list_all(status=PostStatus.DRAFT.value)
        if not drafts:
            await update.message.reply_text("ℹ️ No drafts pending review. Use `/generate <topic>` to create some!")
            return

        for draft in drafts[:5]:
            reply_markup = get_draft_keyboard(draft.id)
            text = f"📝 *Draft #{draft.id}* [{draft.status}]:\n\n```text\n{draft.content}\n```"
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        repo = ScheduleRepository(db)
        pending = repo.list_pending()
        if not pending:
            await update.message.reply_text("ℹ️ Publishing queue is currently empty.")
            return

        for sp in pending[:5]:
            draft = db.query(Draft).filter(Draft.id == sp.draft_id).first()
            content_preview = draft.content[:100] + "..." if draft else "(Content not found)"
            sched_time = sp.scheduled_at.strftime("%Y-%m-%d %H:%M UTC")
            reply_markup = get_queue_keyboard(sp.id)
            text = f"🗓️ *Schedule #{sp.id}* (Draft #{sp.draft_id})\nTime: `{sched_time}`\n\n_{content_preview}_"
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.pause()
        await update.message.reply_text("⏸ *Autopilot has been PAUSED immediately.*", parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.resume()
        await update.message.reply_text("▶ *Autopilot has been RESUMED.*", parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button presses from inline keyboards."""
    query = update.callback_query
    await query.answer()

    data = query.data
    db = get_db()
    try:
        draft_repo = DraftRepository(db)
        sched_repo = ScheduleRepository(db)

        if data.startswith("approve_"):
            draft_id = int(data.split("_")[1])
            draft_repo.update_status(draft_id, PostStatus.APPROVED.value)
            await query.edit_message_text(f"✅ *Draft #{draft_id} marked as APPROVED!*", parse_mode="Markdown")

        elif data.startswith("reject_"):
            draft_id = int(data.split("_")[1])
            draft_repo.update_status(draft_id, PostStatus.CANCELLED.value)
            await query.edit_message_text(f"❌ *Draft #{draft_id} REJECTED.*", parse_mode="Markdown")

        elif data.startswith("copy_"):
            draft_id = int(data.split("_")[1])
            draft = draft_repo.get_by_id(draft_id)
            if draft:
                encoded = urllib.parse.quote(draft.content)
                intent_url = f"https://twitter.com/intent/tweet?text={encoded}"
                await query.message.reply_text(
                    f"📋 *Ready to Post on X:*\n\n```text\n{draft.content}\n```\n\n[Open in X Composer]({intent_url})",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )

        elif data.startswith("sched_"):
            draft_id = int(data.split("_")[1])
            draft_repo.update_status(draft_id, PostStatus.APPROVED.value)
            target = datetime.now(timezone.utc) + timedelta(hours=2)
            sched_repo.schedule(draft_id, target, settings.TIMEZONE)
            draft_repo.update_status(draft_id, PostStatus.SCHEDULED.value)
            await query.edit_message_text(
                f"🗓️ *Draft #{draft_id} scheduled for {target.strftime('%Y-%m-%d %H:%M UTC')}!*",
                parse_mode="Markdown",
            )

        elif data.startswith("cancelsched_"):
            sched_id = int(data.split("_")[1])
            sched_repo.cancel(sched_id)
            await query.edit_message_text(f"🚫 *Schedule #{sched_id} CANCELLED.*", parse_mode="Markdown")

    finally:
        db.close()
