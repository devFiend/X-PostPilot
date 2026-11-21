"""
Telegram Bot handlers for drafting, approval, queue management, and TweetDNA creator intelligence.
"""

import urllib.parse
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from postpilot.telegram.security import owner_only
from postpilot.telegram.keyboards import get_draft_keyboard, get_queue_keyboard
from postpilot.database.db import get_db
from postpilot.database.models import Draft, PostStatus, ScheduledPost
from postpilot.database.repositories import DraftRepository, ScheduleRepository
from postpilot.services.content import ContentService
from postpilot.services.publishing import PublishingService
from postpilot.services.autopilot import AutopilotService
from postpilot.services.dna import DNAService
from postpilot.utils.config import settings


@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🚀 *Welcome to PostPilot + TweetDNA Control Center*\n\n"
        "Your private AI social media copilot & style clone engine for X.\n\n"
        "*Hourly Drops:* 4-5 fresh post cards sent individually every hour (08:00 - 23:59).\n\n"
        "*🧬 Creator Intelligence Commands:*\n"
        "• `/track @creator` — Scrape and extract a creator's Content DNA\n"
        "• `/creators` — List your tracked creator pool\n"
        "• `/untrack @creator` — Remove a creator from pool\n"
        "• `/ideas [count]` — Instant on-demand post cards (e.g. `/ideas 3`)\n"
        "• `/inspire @creator [count]` — Draft posts in a specific creator's style\n\n"
        "*⚙️ Core Commands:*\n"
        "• `/generate <topic>` — AI post draft generator on any topic\n"
        "• `/drafts` — Review and approve pending drafts\n"
        "• `/queue` — View scheduled posts\n"
        "• `/status` — System health & creator stats\n"
        "• `/pause` & `/resume` — Emergency autopilot pause"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


@owner_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 *PostPilot + TweetDNA Guide*\n\n"
        "*1. Clone Creator Styles (TweetDNA)*\n"
        "Type `/track @levelsio` or `/track @swyx` to analyze how top creators write.\n"
        "PostPilot reverse-engineers their hooks, tone, and sentence length.\n\n"
        "*2. Hourly Delivery (8 AM - 11:59 PM)*\n"
        "Every hour, PostPilot automatically drafts 4–5 posts blending your creators' DNA with your niche.\n"
        "Each card has a **[🚀 Post to X Now]** button that auto-approves and opens your X composer in 1 tap!\n\n"
        "*3. On-Demand Posts*\n"
        "Need posts right now? Type `/ideas 2` or `/inspire @levelsio 2`."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


@owner_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        dna_service = DNAService(db)
        creators = dna_service.list_creators()
        auto_state = "⏸ PAUSED" if autopilot.is_paused() else ("▶ ENABLED" if autopilot.is_enabled() else "⏹ DISABLED")
        drafts_count = db.query(Draft).count()
        scheduled_count = db.query(ScheduledPost).filter(ScheduledPost.status == PostStatus.SCHEDULED.value).count()

        creators_list_str = ", ".join([f"@{c.username}" for c in creators]) if creators else "None (use /track @user)"

        msg = (
            "📊 *PostPilot Health & TweetDNA Pool*\n\n"
            f"• *AI Provider:* `{settings.DEFAULT_AI_PROVIDER.upper()}`\n"
            f"• *Publish Method:* `{settings.DEFAULT_PUBLISH_METHOD.upper()}`\n"
            f"• *Autopilot:* `{auto_state}`\n"
            f"• *Active Hours:* `08:00 - 23:59 {settings.TIMEZONE}`\n"
            f"• *Tracked Creators ({len(creators)}):* {creators_list_str}\n"
            f"• *Drafts in DB:* `{drafts_count}`\n"
            f"• *Pending Scheduled:* `{scheduled_count}`\n"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/track @username`\nExample: `/track @levelsio`", parse_mode="Markdown")
        return

    username = args[0].lstrip("@").strip()
    await update.message.reply_text(f"🧬 *Scraping and extracting Content DNA for @{username}...*\n_This takes ~5 seconds..._", parse_mode="Markdown")

    db = get_db()
    try:
        dna_service = DNAService(db)
        result = await dna_service.track_creator(username)
        dna = result["dna"]
        tweets_count = result["tweets_count"]

        msg = (
            f"✅ *TweetDNA Extracted for @{username}!* ({tweets_count} tweets analyzed)\n\n"
            f"• *Tone:* `{dna.tone}`\n"
            f"• *Pillars:* `{dna.content_pillars}`\n"
            f"• *Hook Styles:* `{dna.hook_patterns}`\n\n"
            f"@{username} is now in your active generation pool! "
            f"Posts will now arrive in your hourly drops. Try `/inspire @{username} 2` to test!"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error tracking @{username}: {e}")
    finally:
        db.close()


@owner_only
async def creators_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        dna_service = DNAService(db)
        creators = dna_service.list_creators()
        if not creators:
            await update.message.reply_text("ℹ️ No creators tracked yet. Add some using `/track @username` (e.g. `/track @levelsio`)!", parse_mode="Markdown")
            return

        lines = ["👥 *Your Tracked Creator Intelligence Pool:*\n"]
        for c in creators:
            sync_time = c.last_synced_at.strftime("%Y-%m-%d %H:%M") if c.last_synced_at else "Just now"
            lines.append(f"• *@{c.username}* — {len(c.tweets)} tweets cached (Synced: {sync_time})")

        lines.append("\nTip: Use `/inspire @username` to generate posts in that creator's style.")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def untrack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/untrack @username`", parse_mode="Markdown")
        return

    username = args[0].lstrip("@").strip()
    db = get_db()
    try:
        dna_service = DNAService(db)
        if dna_service.untrack_creator(username):
            await update.message.reply_text(f"🗑️ *@{username}* removed from your tracked creator pool.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Creator @{username} not found in tracking pool.", parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def ideas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate 1, 2, or requested count of on-demand post cards immediately."""
    count = 2
    if context.args:
        try:
            count = max(1, min(10, int(context.args[0])))
        except ValueError:
            pass

    await update.message.reply_text(f"⚡ *Generating {count} on-demand post cards from creator pool...*", parse_mode="Markdown")

    db = get_db()
    try:
        dna_service = DNAService(db)
        posts = await dna_service.generate_posts_from_pool(count=count)
        draft_repo = DraftRepository(db)

        for idx, item in enumerate(posts, start=1):
            draft = draft_repo.create(
                content=item["content"],
                topic=item.get("topic", "On-demand idea"),
                category="creator_dna",
                provider=settings.DEFAULT_AI_PROVIDER,
                status=PostStatus.PENDING_APPROVAL.value,
            )
            reply_markup = get_draft_keyboard(draft.id, draft.content)
            creator_tag = f"• Style: @{item['creator']}" if item.get('creator') != 'general' else ""
            card_text = (
                f"💡 *Idea ({idx}/{len(posts)})* {creator_tag}\n\n"
                f"```text\n{draft.content}\n```"
            )
            await update.message.reply_text(card_text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating ideas: {e}")
    finally:
        db.close()


@owner_only
async def inspire_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate posts specifically mimicking a designated creator's style."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/inspire @username [count]`\nExample: `/inspire @levelsio 2`", parse_mode="Markdown")
        return

    username = args[0].lstrip("@").strip()
    count = 2
    if len(args) > 1:
        try:
            count = max(1, min(10, int(args[1])))
        except ValueError:
            pass

    await update.message.reply_text(f"🎨 *Synthesizing {count} posts in @{username}'s exact style...*", parse_mode="Markdown")

    db = get_db()
    try:
        dna_service = DNAService(db)
        creator = dna_service.repo.get_by_username(username)
        if not creator:
            # Auto-track creator if not already present
            await update.message.reply_text(f"ℹ️ @{username} not tracked yet. Auto-analyzing now...", parse_mode="Markdown")
            await dna_service.track_creator(username)
            creator = dna_service.repo.get_by_username(username)

        dna = dna_service.repo.get_dna(creator.id)
        generator = dna_service.generator
        generated_texts = await generator.generate_from_dna(
            dna=dna,
            creator_username=username,
            topic="Building products as an indie software developer",
            count=count,
        )

        draft_repo = DraftRepository(db)
        for idx, text in enumerate(generated_texts, start=1):
            draft = draft_repo.create(
                content=text,
                topic=f"Inspired by @{username}",
                category="creator_dna",
                provider=settings.DEFAULT_AI_PROVIDER,
                status=PostStatus.PENDING_APPROVAL.value,
            )
            reply_markup = get_draft_keyboard(draft.id, draft.content)
            card_text = (
                f"🎨 *Style: @{username} ({idx}/{len(generated_texts)})*\n\n"
                f"```text\n{draft.content}\n```"
            )
            await update.message.reply_text(card_text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error inspiring from @{username}: {e}")
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
            reply_markup = get_draft_keyboard(draft.id, draft.content)
            text = (
                f"📝 *Draft #{draft.id}* ({draft.character_count} chars):\n\n"
                f"```text\n{draft.content}\n```"
            )
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
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
            await update.message.reply_text("ℹ️ No drafts pending review. Use `/ideas` or `/generate <topic>` to create some!")
            return

        for draft in drafts[:5]:
            reply_markup = get_draft_keyboard(draft.id, draft.content)
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
            content_preview = draft.content if draft else "(Content not found)"
            sched_time = sp.scheduled_at.strftime("%Y-%m-%d %H:%M UTC")
            reply_markup = get_queue_keyboard(sp.id, sp.draft_id, draft.content if draft else "")
            text = f"🗓️ *Schedule #{sp.id}* (Draft #{sp.draft_id})\nTime: `{sched_time}`\n\n```text\n{content_preview}\n```"
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.pause()
        await update.message.reply_text("⏸ *Autopilot and Hourly Drops PAUSED immediately.*", parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.resume()
        await update.message.reply_text("▶ *Autopilot and Hourly Drops RESUMED.*", parse_mode="Markdown")
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
            draft = draft_repo.get_by_id(draft_id)
            draft_repo.update_status(draft_id, PostStatus.APPROVED.value)
            
            keyboard = []
            if draft:
                encoded = urllib.parse.quote(draft.content)
                composer_url = f"https://twitter.com/intent/tweet?text={encoded}"
                keyboard.append([InlineKeyboardButton("🚀 Post to X Now", url=composer_url)])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await query.edit_message_text(
                f"✅ *Draft #{draft_id} marked as APPROVED!*\nReady to dispatch or schedule.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif data.startswith("reject_"):
            draft_id = int(data.split("_")[1])
            draft_repo.update_status(draft_id, PostStatus.CANCELLED.value)
            await query.edit_message_text(f"❌ *Draft #{draft_id} REJECTED / DISMISSED.*", parse_mode="Markdown")

        elif data.startswith("sched_"):
            draft_id = int(data.split("_")[1])
            draft = draft_repo.get_by_id(draft_id)
            draft_repo.update_status(draft_id, PostStatus.APPROVED.value)
            target = datetime.now(timezone.utc) + timedelta(hours=2)
            sched_repo.schedule(draft_id, target, settings.TIMEZONE)
            draft_repo.update_status(draft_id, PostStatus.SCHEDULED.value)
            
            keyboard = []
            if draft:
                encoded = urllib.parse.quote(draft.content)
                composer_url = f"https://twitter.com/intent/tweet?text={encoded}"
                keyboard.append([InlineKeyboardButton("🚀 Post to X Now (Early)", url=composer_url)])

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await query.edit_message_text(
                f"🗓️ *Draft #{draft_id} scheduled for {target.strftime('%Y-%m-%d %H:%M UTC')}!*",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        elif data.startswith("cancelsched_"):
            sched_id = int(data.split("_")[1])
            sched_repo.cancel(sched_id)
            await query.edit_message_text(f"🚫 *Schedule #{sched_id} CANCELLED.*", parse_mode="Markdown")

    finally:
        db.close()
