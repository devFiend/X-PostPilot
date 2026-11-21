"""
Telegram Bot handlers for drafting, approval, queue management, and TweetDNA creator intelligence.
Polished UI with formatted cards, ready-to-click commands, and persistent dashboard buttons.
"""

import urllib.parse
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from postpilot.telegram.security import owner_only
from postpilot.telegram.keyboards import (
    get_draft_keyboard,
    get_queue_keyboard,
    get_dashboard_reply_keyboard,
    get_welcome_inline_keyboard,
)
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
        "🚀 *Welcome to PostPilot + TweetDNA Control Room*\n\n"
        "Your private AI social media ghostwriter & publishing copilot for X.\n\n"
        "⏰ *Hourly Drops:* 4–5 fresh post cards sent individually every hour (*08:00 – 23:59*).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "*⚡ Quick Tap Commands (Tap to Run):*\n"
        "• `/ideas` — Get 2 fresh post ideas right now\n"
        "• `/ideas 4` — Request 4 custom ideas\n"
        "• `/creators` — View your tracked creator roster\n"
        "• `/track @levelsio` — Clone a creator's writing DNA\n"
        "• `/inspire @levelsio 2` — Draft posts in @levelsio's voice\n"
        "• `/drafts` — Review saved drafts\n"
        "• `/queue` — View scheduled tweets\n"
        "• `/status` — Check system health & stats\n"
        "• `/pause` — Emergency halt hourly drops\n"
        "• `/resume` — Resume hourly drops\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Select an action below or use the pinned menu buttons:_ 👇"
    )
    # Send with both persistent ReplyKeyboardMarkup and interactive Inline menu
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_dashboard_reply_keyboard(),
    )
    await update.message.reply_text(
        "🎛️ *Quick Actions Dashboard:*",
        parse_mode="Markdown",
        reply_markup=get_welcome_inline_keyboard(),
    )


@owner_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 *PostPilot & TweetDNA Complete Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "*1. Clone Top Creators (TweetDNA)*\n"
        "Add creators whose writing style, hooks, and rhythm you admire:\n"
        "👉 `/track @levelsio`\n"
        "👉 `/track @swyx`\n"
        "👉 `/track @shl`\n\n"
        "PostPilot anonymously analyzes their public posts and builds a Content Playbook without touching your account credentials.\n\n"
        "*2. Hourly Delivery (08:00 – 23:59)*\n"
        "Every hour, PostPilot automatically drafts 4–5 posts blending your creators' DNA with your niche.\n"
        "Each card includes a **[🚀 Post to X Now]** button that auto-approves the draft in SQLite and launches the pre-filled X composer on your phone in 1 tap!\n\n"
        "*3. On-Demand Posts Anytime*\n"
        "• `/ideas` (or `/ideas 3`)\n"
        "• `/inspire @levelsio 2`\n"
        "• `/generate Why developers should learn AI 3`\n\n"
        "*4. Night Mode / Silence*\n"
        "During the night (12:00 AM – 7:59 AM), the bot stays completely quiet. Use `/pause` if you want to silence hourly drops at any other time."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


@owner_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        dna_service = DNAService(db)
        creators = dna_service.list_creators()
        auto_state = "⏸ PAUSED" if autopilot.is_paused() else ("▶ ACTIVE" if autopilot.is_enabled() else "⏹ STANDBY")
        drafts_count = db.query(Draft).count()
        scheduled_count = db.query(ScheduledPost).filter(ScheduledPost.status == PostStatus.SCHEDULED.value).count()

        creators_list_str = ", ".join([f"@{c.username}" for c in creators]) if creators else "None (use `/track @username`)"

        msg = (
            "📊 *PostPilot Health & TweetDNA Status*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Hourly Schedule:* `08:00 – 23:59` ({settings.TIMEZONE})\n"
            f"• *Autopilot State:* `{auto_state}`\n"
            f"• *AI Provider:* `{settings.DEFAULT_AI_PROVIDER.upper()}`\n"
            f"• *Publish Method:* `{settings.DEFAULT_PUBLISH_METHOD.upper()}` (1-Tap Compose: Free $0)\n"
            f"• *Tracked Creators ({len(creators)}):* {creators_list_str}\n"
            f"• *Saved Drafts in DB:* `{drafts_count}`\n"
            f"• *Pending Scheduled:* `{scheduled_count}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Ready for requests. Try `/ideas` or `/track @levelsio`."
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ *Missing creator handle.*\n\n"
            "Usage: `/track @username`\n"
            "Example: `/track @levelsio` or `/track @swyx`",
            parse_mode="Markdown"
        )
        return

    username = args[0].lstrip("@").strip()
    status_msg = await update.message.reply_text(
        f"🧬 *Scraping & Extracting Content DNA for @{username}...*\n_Analyzing hook patterns, sentence length, and tone..._",
        parse_mode="Markdown"
    )

    db = get_db()
    try:
        dna_service = DNAService(db)
        result = await dna_service.track_creator(username)
        dna = result["dna"]
        tweets_count = result["tweets_count"]

        msg = (
            f"✅ *TweetDNA Successfully Extracted for @{username}!* 🎉\n"
            f"📊 Analyzed `{tweets_count}` recent public tweets.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Tone & Voice:* `{dna.tone}`\n"
            f"• *Core Pillars:* `{dna.content_pillars}`\n"
            f"• *Hook Patterns:* `{dna.hook_patterns}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"@{username} is now in your active generation pool! "
            f"Their style will now be used in your hourly drops.\n\n"
            f"👉 *Try it right now:* `/inspire @{username} 2`"
        )
        await status_msg.edit_text(msg, parse_mode="Markdown")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error tracking @{username}: {e}")
    finally:
        db.close()


@owner_only
async def creators_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        dna_service = DNAService(db)
        creators = dna_service.list_creators()
        if not creators:
            await update.message.reply_text(
                "ℹ️ *No creators tracked yet.*\n\n"
                "Add creators you want to clone/learn from:\n"
                "• `/track @levelsio`\n"
                "• `/track @swyx`\n"
                "• `/track @shl`",
                parse_mode="Markdown"
            )
            return

        lines = ["👥 *Your Tracked Creator Intelligence Pool:*\n", "━━━━━━━━━━━━━━━━━━━━━━"]
        for c in creators:
            sync_time = c.last_synced_at.strftime("%b %d, %H:%M") if c.last_synced_at else "Recent"
            lines.append(f"• *@{c.username}* — `{len(c.tweets)}` tweets cached (Synced: {sync_time})")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("\n👉 *Tap to draft:* `/ideas` or `/inspire @{}`".format(creators[0].username))
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def untrack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/untrack @username`\nExample: `/untrack @levelsio`", parse_mode="Markdown")
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
            count = max(1, min(6, int(context.args[0])))
        except ValueError:
            pass

    status_msg = await update.message.reply_text(
        f"⚡ *Synthesizing {count} fresh post cards from your creator pool...*",
        parse_mode="Markdown"
    )

    db = get_db()
    try:
        dna_service = DNAService(db)
        posts = await dna_service.generate_posts_from_pool(count=count)
        draft_repo = DraftRepository(db)

        # Delete the temporary loading message
        try:
            await status_msg.delete()
        except Exception:
            pass

        for idx, item in enumerate(posts, start=1):
            draft = draft_repo.create(
                content=item["content"],
                topic=item.get("topic", "On-demand idea"),
                category="creator_dna",
                provider=settings.DEFAULT_AI_PROVIDER,
                status=PostStatus.PENDING_APPROVAL.value,
            )
            reply_markup = get_draft_keyboard(draft.id, draft.content)
            creator_tag = f"• Style: @{item['creator']}" if item.get('creator') != 'general' else "• General Style"
            card_text = (
                f"💡 *Idea ({idx}/{len(posts)})* {creator_tag} • `({draft.character_count}/280 chars)`\n\n"
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
        await update.message.reply_text(
            "Usage: `/inspire @username [count]`\nExample: `/inspire @levelsio 2`",
            parse_mode="Markdown"
        )
        return

    username = args[0].lstrip("@").strip()
    count = 2
    if len(args) > 1:
        try:
            count = max(1, min(6, int(args[1])))
        except ValueError:
            pass

    status_msg = await update.message.reply_text(
        f"🎨 *Synthesizing {count} posts in @{username}'s exact style...*",
        parse_mode="Markdown"
    )

    db = get_db()
    try:
        dna_service = DNAService(db)
        creator = dna_service.repo.get_by_username(username)
        if not creator:
            await status_msg.edit_text(f"ℹ️ @{username} not tracked yet. Auto-analyzing now...", parse_mode="Markdown")
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

        try:
            await status_msg.delete()
        except Exception:
            pass

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
                f"🎨 *Style: @{username} ({idx}/{len(generated_texts)})* • `({draft.character_count}/280 chars)`\n\n"
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
        await update.message.reply_text(
            "Usage: `/generate <topic>`\n"
            "Example: `/generate Why developers should learn Python`",
            parse_mode="Markdown"
        )
        return

    topic = " ".join(args)
    status_msg = await update.message.reply_text(f"🧠 *Generating 3 post options for:* _{topic}_...", parse_mode="Markdown")

    db = get_db()
    try:
        service = ContentService(db)
        drafts = await service.generate_drafts(topic=topic, count=3)
        try:
            await status_msg.delete()
        except Exception:
            pass

        for draft in drafts:
            reply_markup = get_draft_keyboard(draft.id, draft.content)
            text = (
                f"📝 *Draft #{draft.id}* (`{draft.character_count}/280 chars`):\n\n"
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
            await update.message.reply_text(
                "ℹ️ *No pending drafts in queue.*\n\n"
                "👉 Tap `/ideas` to generate fresh drafts instantly!",
                parse_mode="Markdown"
            )
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
            await update.message.reply_text(
                "ℹ️ *Publishing queue is currently empty.*\n\n"
                "Tip: Click `[🗓️ Schedule (2h)]` on any post card to add it to your queue.",
                parse_mode="Markdown"
            )
            return

        for sp in pending[:5]:
            draft = db.query(Draft).filter(Draft.id == sp.draft_id).first()
            content_preview = draft.content if draft else "(Content not found)"
            sched_time = sp.scheduled_at.strftime("%b %d, %H:%M UTC")
            reply_markup = get_queue_keyboard(sp.id, sp.draft_id, draft.content if draft else "")
            text = f"🗓️ *Schedule #{sp.id}* (Draft #{sp.draft_id})\nTarget Time: `{sched_time}`\n\n```text\n{content_preview}\n```"
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.pause()
        await update.message.reply_text(
            "⏸ *Autopilot & Hourly Drops PAUSED immediately.*\n\n"
            "The bot will not deliver hourly cards until you send `/resume`.",
            parse_mode="Markdown"
        )
    finally:
        db.close()


@owner_only
async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.resume()
        await update.message.reply_text(
            "▶ *Autopilot & Hourly Drops RESUMED.*\n\n"
            "Hourly content cards will deliver between 08:00 and 23:59.",
            parse_mode="Markdown"
        )
    finally:
        db.close()


@owner_only
async def dashboard_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text clicks from the persistent 2x3 reply keyboard grid."""
    text = update.message.text.strip()
    if text == "⚡ Quick Ideas (2)":
        await ideas_command(update, context)
    elif text == "👥 Tracked Creators":
        await creators_command(update, context)
    elif text == "📝 Review Drafts":
        await drafts_command(update, context)
    elif text == "🗓️ View Queue":
        await queue_command(update, context)
    elif text == "📊 System Status":
        await status_command(update, context)
    elif text == "📖 Guide & Help":
        await help_command(update, context)


@owner_only
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button presses from inline keyboards."""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handle Welcome Menu Callbacks
    if data == "menu_ideas_2":
        # Create a synthetic update
        context.args = ["2"]
        await ideas_command(update, context)
        return
    elif data == "menu_creators":
        await creators_command(update, context)
        return
    elif data == "menu_drafts":
        await drafts_command(update, context)
        return
    elif data == "menu_queue":
        await queue_command(update, context)
        return
    elif data == "menu_status":
        await status_command(update, context)
        return
    elif data == "menu_help":
        await help_command(update, context)
        return

    # Handle Post Card Actions
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
            await query.edit_message_text(f"❌ *Draft #{draft_id} DISMISSED.*", parse_mode="Markdown")

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
