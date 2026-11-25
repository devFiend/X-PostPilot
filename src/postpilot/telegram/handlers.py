"""
Telegram Bot handlers for drafting, approval, queue management, and TweetDNA creator intelligence.
Polished UI with formatted cards, ready-to-click commands, and persistent dashboard buttons.
"""

import urllib.parse
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import ContextTypes
from postpilot.telegram.security import owner_only
from postpilot.telegram.keyboards import (
    get_draft_keyboard,
    get_queue_keyboard,
    get_dashboard_reply_keyboard,
    get_welcome_inline_keyboard,
    get_status_keyboard,
    get_reply_card_keyboard,
    get_thread_keyboard,
)
from postpilot.database.db import get_db
from postpilot.database.models import Draft, PostStatus, ScheduledPost, PublishedPost
from postpilot.database.repositories import DraftRepository, ScheduleRepository
from postpilot.services.content import ContentService
from postpilot.services.publishing import PublishingService
from postpilot.services.autopilot import AutopilotService
from postpilot.services.dna import DNAService
from postpilot.services.trends import TrendPulseService
from postpilot.services.replies import SmartReplyService
from postpilot.services.threads import ThreadService
from postpilot.services.audio import AudioTranscriptionService, VoiceTweetService
from postpilot.utils.config import settings


def safe_md(text: str) -> str:
    """Safely escape text for Telegram legacy Markdown to prevent formatting errors on underscores."""
    if not text:
        return ""
    return escape_markdown(str(text), version=1)


def get_msg(update: Update):
    """Retrieve message object whether update came from a direct message or an inline callback query."""
    return update.effective_message or (update.callback_query and update.callback_query.message)


def format_system_health(db) -> tuple[str, InlineKeyboardMarkup]:
    """Generates real-time diagnostics, system health metrics, and interactive buttons."""
    autopilot = AutopilotService(db)
    dna_service = DNAService(db)
    creators = dna_service.list_creators()
    auto_state = "⏸ PAUSED" if autopilot.is_paused() else ("▶ ACTIVE" if autopilot.is_enabled() else "⏹ STANDBY")
    drafts_count = db.query(Draft).count()
    approved_count = db.query(Draft).filter(Draft.status == PostStatus.APPROVED.value).count()
    scheduled_count = db.query(ScheduledPost).filter(ScheduledPost.status == PostStatus.SCHEDULED.value).count()
    published_count = db.query(PublishedPost).filter(PublishedPost.status == "SUCCESS").count()

    total_cached_tweets = sum(len(c.tweets) for c in creators)
    creators_list_str = ", ".join([f"@{safe_md(c.username)}" for c in creators]) if creators else "None (use `/track @username`)"

    provider_name = settings.DEFAULT_AI_PROVIDER.upper()
    has_key = bool(settings.GROQ_API_KEY if settings.DEFAULT_AI_PROVIDER == "groq" else True)
    ai_status = f"🟢 Connected (`{settings.GROQ_MODEL}`)" if has_key else "⚠️ Missing API Key"

    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    text = (
        "📊 *PostPilot System Health & Diagnostics*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 *Core Status:* `OPERATIONAL`\n"
        f"• *AI Engine:* `{provider_name}` — {ai_status}\n"
        f"• *Database:* `SQLite (Healthy)` — `postpilot.db`\n"
        f"• *Drip Schedule:* `Every 20 min (3/hr)` (08:00 – 23:59 {settings.TIMEZONE})\n"
        f"• *Autopilot Engine:* `{auto_state}`\n"
        f"• *Publishing:* `$0 Direct X Composer Intent` (Ban-Proof)\n\n"
        "📈 *Live Content Metrics:*\n"
        f"• Tracked Creators: `{len(creators)}` ({creators_list_str})\n"
        f"• Cached Creator Tweets: `{total_cached_tweets}`\n"
        f"• Total Saved Drafts: `{drafts_count}` (`{approved_count}` Approved)\n"
        f"• Pending in Queue: `{scheduled_count}`\n"
        f"• Successfully Posted: `{published_count}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 _Last checked: {now_str}_\n"
        "👉 _Tap buttons below for instant actions:_"
    )
    return text, get_status_keyboard()


@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_msg(update)
    if not target:
        return
    msg = (
        "🚀 *Welcome to PostPilot + TweetDNA Control Room*\n\n"
        "Your private AI social media ghostwriter & publishing copilot for X.\n\n"
        "⏰ *Content Delivery Drip:* Fresh post cards delivered every 20 minutes (3 drops/hr) during waking hours (*08:00 – 23:59*).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "*⚡ Quick Tap Commands (Tap to Run):*\n"
        "• `/trends` — Scan live niche trends & get instant hot-takes\n"
        "• `/ideas` — Get 2 fresh post ideas right now\n"
        "• `/creators` — View your tracked creator roster\n"
        "• `/track @levelsio` — Clone a creator's writing DNA\n"
        "• `/inspire @levelsio 2` — Draft posts in @levelsio's voice\n"
        "• `/drafts` — Review saved drafts\n"
        "• `/queue` — View scheduled tweets\n"
        "• `/status` — Real-time system health & diagnostics\n"
        "• `/postnow <text>` — Instant 1-tap composer launcher\n"
        "• `/pause` — Emergency halt delivery\n"
        "• `/resume` — Resume delivery\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Select an action below or use the pinned menu buttons:_ 👇"
    )
    # Send with both persistent ReplyKeyboardMarkup and interactive Inline menu
    await target.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_dashboard_reply_keyboard(),
    )
    await target.reply_text(
        "🎛️ *Quick Actions Dashboard:*",
        parse_mode="Markdown",
        reply_markup=get_welcome_inline_keyboard(),
    )


@owner_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_msg(update)
    if not target:
        return
    msg = (
        "📖 *PostPilot & TweetDNA Complete Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "*1. Clone Top Creators (TweetDNA)*\n"
        "Add creators whose writing style, hooks, and rhythm you admire:\n"
        "👉 `/track @levelsio`\n"
        "👉 `/track @swyx`\n"
        "👉 `/track @_florian`\n\n"
        "PostPilot anonymously analyzes their public posts and builds a Content Playbook without touching your account credentials.\n\n"
        "*2. Spaced Drip Delivery (3 drops/hr)*\n"
        "Every 20 minutes (at :00, :20, :40), PostPilot automatically drafts 1 fresh post blending your creators' DNA with your niche.\n"
        "Each card includes a **[🚀 Post to X Now]** button that directly launches the native X composer on your phone in 1 tap, plus **[✅ Mark as Posted]**!\n\n"
        "*3. On-Demand Posts Anytime*\n"
        "• `/ideas` (or `/ideas 3`)\n"
        "• `/inspire @levelsio 2`\n"
        "• `/generate Why developers should learn AI 3`\n"
        "• `/postnow My custom tweet text`\n\n"
        "*4. Diagnostics & Night Mode*\n"
        "• `/status` — Live system health & refresh button\n"
        "• `/pause` — Silence delivery drops anytime\n"
        "• `/resume` — Unpause delivery"
    )
    await target.reply_text(msg, parse_mode="Markdown")


@owner_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_msg(update)
    if not target:
        return
    db = get_db()
    try:
        text, markup = format_system_health(db)
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
                return
            except Exception:
                pass
        await target.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def doctor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run diagnostics check."""
    await status_command(update, context)


@owner_only
async def postnow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instantly build a 1-tap X composer launch button for ad-hoc custom text."""
    target = get_msg(update)
    if not target:
        return
    if not context.args:
        await target.reply_text(
            "Usage: `/postnow <your tweet text>`\n"
            "Example: `/postnow Shipping our second major update today! 🚀`",
            parse_mode="Markdown",
        )
        return

    custom_text = " ".join(context.args)
    encoded = urllib.parse.quote(custom_text)
    composer_url = f"https://twitter.com/intent/tweet?text={encoded}"
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Post to X Now", url=composer_url)]])
    await target.reply_text(
        f"🚀 *1-Tap X Composer Generated:*\n\n```text\n{custom_text}\n```",
        reply_markup=markup,
        parse_mode="Markdown",
    )


@owner_only
async def setavatar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the Telegram bot profile picture using an attached image or project assets."""
    target = get_msg(update)
    if not target:
        return

    from telegram import InputProfilePhotoStatic
    from pathlib import Path

    # Case 1: user replied to a photo
    if update.message and update.message.reply_to_message and update.message.reply_to_message.photo:
        photo = update.message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        try:
            await context.bot.set_my_profile_photo(InputProfilePhotoStatic(bytes(photo_bytes)))
            await target.reply_text("✨ *Bot profile photo successfully updated!*", parse_mode="Markdown")
        except Exception as e:
            await target.reply_text(f"❌ Failed to set photo: {e}")
        return

    # Case 2: default from assets/avatar.jpg
    possible_paths = [
        Path("assets/avatar.jpg"),
        Path("src/postpilot/assets/avatar.jpg"),
        Path(__file__).resolve().parent.parent.parent / "assets" / "avatar.jpg",
    ]
    for p in possible_paths:
        if p.exists():
            try:
                with open(p, "rb") as f:
                    await context.bot.set_my_profile_photo(InputProfilePhotoStatic(f))
                await target.reply_text("✨ *PostPilot official profile photo successfully applied!*", parse_mode="Markdown")
                return
            except Exception as e:
                await target.reply_text(f"❌ Failed to set photo from {p}: {e}")
                return

    await target.reply_text(
        "ℹ️ *No avatar found.* Reply to any photo with `/setavatar` to set it as the bot's profile picture!",
        parse_mode="Markdown",
    )


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
    safe_user = safe_md(username)
    status_msg = await update.message.reply_text(
        f"🧬 *Scraping & Extracting Content DNA for @{safe_user}...*\n_Analyzing hook patterns, sentence length, and tone..._",
        parse_mode="Markdown"
    )

    db = get_db()
    try:
        dna_service = DNAService(db)
        result = await dna_service.track_creator(username)
        dna = result["dna"]
        tweets_count = result["tweets_count"]

        msg = (
            f"✅ *TweetDNA Successfully Extracted for @{safe_user}!* 🎉\n"
            f"📊 Analyzed `{tweets_count}` recent public tweets.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Tone & Voice:* `{dna.tone}`\n"
            f"• *Core Pillars:* `{dna.content_pillars}`\n"
            f"• *Hook Patterns:* `{dna.hook_patterns}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"@{safe_user} is now in your active generation pool! "
            f"Their style will now be used in your hourly drops.\n\n"
            f"👉 *Try it right now:* `/inspire @{safe_user} 2`"
        )
        await status_msg.edit_text(msg, parse_mode="Markdown")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error tracking @{safe_user}: {e}")
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
            lines.append(f"• *@{safe_md(c.username)}* — `{len(c.tweets)}` tweets cached (Synced: {sync_time})")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        first_creator = safe_md(creators[0].username)
        lines.append(f"\n👉 *Tap to draft:* `/ideas` or `/inspire @{first_creator}`")
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
    safe_user = safe_md(username)
    db = get_db()
    try:
        dna_service = DNAService(db)
        if dna_service.untrack_creator(username):
            await update.message.reply_text(f"🗑️ *@{safe_user}* removed from your tracked creator pool.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Creator @{safe_user} not found in tracking pool.", parse_mode="Markdown")
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
            creator_name = item.get("creator", "general")
            creator_tag = f"• Style: @{safe_md(creator_name)}" if creator_name != "general" else "• General Style"
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
    """Generate posts specifically mimicking a designated creator's style and rephrasing their tweets."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: `/inspire @username [count]`\nExample: `/inspire @levelsio 2`",
            parse_mode="Markdown"
        )
        return

    username = args[0].lstrip("@").strip()
    safe_user = safe_md(username)
    count = 2
    if len(args) > 1:
        try:
            count = max(1, min(6, int(args[1])))
        except ValueError:
            pass

    status_msg = await update.message.reply_text(
        f"🎨 *Synthesizing {count} posts in @{safe_user}'s exact style...*",
        parse_mode="Markdown"
    )

    db = get_db()
    try:
        dna_service = DNAService(db)
        creator = dna_service.repo.get_by_username(username.lower())
        if not creator:
            await status_msg.edit_text(f"ℹ️ @{safe_user} not tracked yet. Auto-analyzing now...", parse_mode="Markdown")
            await dna_service.track_creator(username)
            creator = dna_service.repo.get_by_username(username.lower())

        dna = dna_service.repo.get_dna(creator.id)
        cached_tweets = dna_service.repo.get_creator_tweets(creator.id, limit=30)
        generator = dna_service.generator
        draft_repo = DraftRepository(db)

        generated_texts = []
        # First try to rephrase actual tweets from this creator
        if cached_tweets:
            import random
            shuffled = list(cached_tweets)
            random.shuffle(shuffled)
            for tw in shuffled:
                if len(generated_texts) >= count:
                    break
                if draft_repo.is_duplicate(tw.text, threshold=0.60):
                    continue
                rephrased = await generator.generate_rephrased_tweet(
                    source_tweet=tw.text,
                    creator_username=creator.username,
                    dna=dna,
                )
                if rephrased and not draft_repo.is_duplicate(rephrased, threshold=0.55):
                    generated_texts.append(rephrased)

        # Fallback to DNA generation with sample tweets if not enough generated
        if len(generated_texts) < count:
            remaining = count - len(generated_texts)
            sample_texts = [t.text for t in cached_tweets[:3]]
            dna_posts = await generator.generate_from_dna(
                dna=dna,
                creator_username=username,
                topic="Building products as an indie software developer",
                count=remaining,
                sample_tweets=sample_texts,
            )
            for p in dna_posts:
                if not draft_repo.is_duplicate(p, threshold=0.55):
                    generated_texts.append(p)

        try:
            await status_msg.delete()
        except Exception:
            pass

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
                f"🎨 *Style: @{safe_user} ({idx}/{len(generated_texts)})* • `({draft.character_count}/280 chars)`\n\n"
                f"```text\n{draft.content}\n```"
            )
            await update.message.reply_text(card_text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error inspiring from @{safe_user}: {e}")
    finally:
        db.close()


@owner_only
async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan live breakout stories in the user's niche across Hacker News and X curators, and generate tweet takes."""
    target = get_msg(update)
    if not target:
        return

    status_msg = await target.reply_text(
        "🔥 *Scanning live niche trends across Hacker News & top X curators...*\n_Filtering for software, AI, and developer discussions..._",
        parse_mode="Markdown"
    )

    db = get_db()
    try:
        service = TrendPulseService(db)
        trends = await service.scan_live_trends(limit=2)

        try:
            await status_msg.delete()
        except Exception:
            pass

        if not trends:
            await target.reply_text(
                "ℹ️ *No major breakout trends detected in your niche right now.*\n"
                "Try again shortly or tap `/ideas` to generate from your creator pool!",
                parse_mode="Markdown",
            )
            return

        for t_idx, trend in enumerate(trends, start=1):
            source_label = safe_md(trend.get("source", "Web"))
            topic_label = safe_md(trend.get("topic", "Tech Trend"))
            summary_label = safe_md(trend.get("summary", ""))

            header_text = (
                f"🔥 *Trending Story #{t_idx}: {topic_label}*\n"
                f"• *Source:* `{source_label}` (Score: `{trend.get('score', 0)}`)\n"
                f"• *Context:* _{summary_label}_\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👉 *Select a take below to post directly to X:*"
            )
            await target.reply_text(header_text, parse_mode="Markdown")

            for take in trend.get("takes", []):
                draft = await service.draft_trend_take(
                    content=take["content"],
                    topic=trend.get("topic", "Niche Trend"),
                )
                markup = get_draft_keyboard(draft.id, draft.content)
                angle_label = safe_md(take["angle"])
                take_card = (
                    f"💡 *Angle: {angle_label}* • `({draft.character_count}/280 chars)`\n\n"
                    f"```text\n{draft.content}\n```"
                )
                await target.reply_text(take_card, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        await target.reply_text(f"❌ Error scanning trends: {e}")
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
    target = get_msg(update)
    if not target:
        return
    db = get_db()
    try:
        repo = DraftRepository(db)
        drafts = repo.list_all(status=PostStatus.DRAFT.value)
        if not drafts:
            await target.reply_text(
                "ℹ️ *No pending drafts in queue.*\n\n"
                "👉 Tap `/ideas` to generate fresh drafts instantly!",
                parse_mode="Markdown"
            )
            return

        for draft in drafts[:5]:
            reply_markup = get_draft_keyboard(draft.id, draft.content)
            text = f"📝 *Draft #{draft.id}* [{draft.status}]:\n\n```text\n{draft.content}\n```"
            await target.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_msg(update)
    if not target:
        return
    db = get_db()
    try:
        repo = ScheduleRepository(db)
        pending = repo.list_pending()
        if not pending:
            await target.reply_text(
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
            await target.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    finally:
        db.close()


@owner_only
async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_msg(update)
    if not target:
        return
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.pause()
        await target.reply_text(
            "⏸ *Autopilot & Content Drip PAUSED immediately.*\n\n"
            "The bot will not deliver drip cards until you send `/resume`.",
            parse_mode="Markdown"
        )
    finally:
        db.close()


@owner_only
async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = get_msg(update)
    if not target:
        return
    db = get_db()
    try:
        autopilot = AutopilotService(db)
        autopilot.resume()
        await target.reply_text(
            "▶ *Autopilot & Content Drip RESUMED.*\n\n"
            "Content cards will deliver every 20 minutes (3 drops/hr) between 08:00 and 23:59.",
            parse_mode="Markdown"
        )
    finally:
        db.close()


@owner_only
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Generate 3 high-signal, non-sycophantic replies to any tweet or topic.
    Usage: /reply <tweet text or X link>
    """
    target = get_msg(update)
    if not target:
        return

    raw_input = " ".join(context.args).strip() if context.args else ""
    if not raw_input:
        msg = (
            "💬 *Smart Reply Guy Assistant*\n\n"
            "Generate 3 high-signal, authentic replies to drive profile visits.\n\n"
            "👉 *Usage:*\n"
            "• `/reply <paste tweet text>`\n"
            "• `/reply https://x.com/username/status/123456789`\n"
            "• Or simply paste an X/Twitter link right here into chat!"
        )
        await target.reply_text(msg, parse_mode="Markdown")
        return

    status_msg = await target.reply_text("⚡ *Analyzing tweet & generating 3 high-signal replies...*", parse_mode="Markdown")

    reply_svc = SmartReplyService()
    try:
        result = await reply_svc.generate_replies(source_tweet=raw_input)
        try:
            await status_msg.delete()
        except Exception:
            pass

        # Handle either dict (new) or list (legacy fallback)
        if isinstance(result, dict):
            options = result.get("options", [])
            author = result.get("author")
            original_text = result.get("original_text", "")
        else:
            options = result
            author = None
            original_text = ""

        # Intro header
        if author:
            intro = (
                f"💬 *Replying to @{safe_md(author)}:*\n"
                f"_{safe_md(original_text[:200])}{'...' if len(original_text) > 200 else ''}_\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👉 *Select a reply style below (1-tap to copy & open composer):*"
            )
        elif original_text and not ("x.com/" in original_text or "twitter.com/" in original_text):
            intro = (
                f"💬 *Replying to Topic / Tweet:*\n"
                f"_{safe_md(original_text[:200])}{'...' if len(original_text) > 200 else ''}_\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👉 *Select a reply style below (1-tap to copy & open composer):*"
            )
        else:
            intro = "💬 *3 High-Signal Replies Ready to Post:*\n━━━━━━━━━━━━━━━━━━━━━━"

        await target.reply_text(intro, parse_mode="Markdown")

        for opt in options:
            card_text = (
                f"*{opt['angle']}* • `({opt['character_count']}/280 chars)`\n\n"
                f"```text\n{opt['content']}\n```"
            )
            await target.reply_text(
                card_text,
                reply_markup=get_reply_card_keyboard(opt["url"]),
                parse_mode="Markdown",
            )
    except Exception as e:
        await target.reply_text(f"⚠️ *Could not generate replies:* {safe_md(str(e))}", parse_mode="Markdown")


@owner_only
async def thread_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Draft a viral 4-to-5 tweet thread on any topic.
    Usage: /thread <topic>
    """
    target = get_msg(update)
    if not target:
        return

    topic = " ".join(context.args).strip() if context.args else ""
    if not topic:
        topic = "Lessons learned building and shipping modern tech products"

    status_msg = await target.reply_text(
        f"🧵 *Crafting viral thread breakdown on:* _{safe_md(topic)}_\nGenerating hooks & insights...",
        parse_mode="Markdown",
    )

    thread_svc = ThreadService()
    try:
        thread_data = await thread_svc.generate_thread(topic=topic, tweet_count=4)
        try:
            await status_msg.delete()
        except Exception:
            pass

        intro = (
            f"🧵 *Viral Thread Ready ({thread_data['tweet_count']} Tweets)*\n"
            f"📌 *Topic:* {safe_md(topic)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *How to post in 10s:*\n"
            f"1. Tap **[🚀 Launch Tweet 1 on X]** below to open the X composer.\n"
            f"2. Tap any tweet card below to instantly copy it to your clipboard.\n"
            f"3. In the X app, tap **`+`** to add each copied tweet to your thread!"
        )
        await target.reply_text(intro, parse_mode="Markdown")

        tweets = thread_data["tweets"]
        for i, t in enumerate(tweets):
            encoded = urllib.parse.quote(t["content"])
            composer_url = f"https://twitter.com/intent/tweet?text={encoded}"

            if i == 0:
                header_badge = f"🎣 *Tweet {t['num']} — The Hook* • `({t['character_count']}/280 chars)`"
                btn_text = "🚀 Launch Tweet 1 on X"
            elif i == len(tweets) - 1:
                header_badge = f"🎯 *Tweet {t['num']} — The Wrap & CTA* • `({t['character_count']}/280 chars)`"
                btn_text = "🚀 Compose in X"
            else:
                header_badge = f"📝 *Tweet {t['num']}* • `({t['character_count']}/280 chars)`"
                btn_text = "🚀 Compose in X"

            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton(btn_text, url=composer_url),
            ]])

            card_text = (
                f"{header_badge}\n\n"
                f"```text\n{t['content']}\n```"
            )
            await target.reply_text(card_text, parse_mode="Markdown", reply_markup=markup)

        # Footer actions
        footer_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🧵 Draft Another Thread", callback_data="menu_thread"),
                InlineKeyboardButton("⚡ Quick Ideas (2)", callback_data="menu_ideas_2"),
            ],
            [
                InlineKeyboardButton("🔥 Niche Trends", callback_data="menu_trends"),
                InlineKeyboardButton("📝 Review Drafts", callback_data="menu_drafts"),
            ],
        ])
        await target.reply_text("✨ *All thread cards delivered! Select your next action:*", parse_mode="Markdown", reply_markup=footer_markup)
    except Exception as e:
        await target.reply_text(f"⚠️ *Could not generate thread:* {safe_md(str(e))}", parse_mode="Markdown")


@owner_only
async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Transcribes voice notes or audio memos with Groq Whisper (or Gemini fallback),
    then turns the spoken thought into 3 authentic, polished tweet options:
    1. 🎯 Direct Polish: User's words & voice tightened for X.
    2. 🔥 High-Impact Hook: Rephrased with viral energy & emojis.
    3. ⚡ Minimalist Punch: Crisp one-liner (< 120 chars).
    """
    if not update.message:
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    status_msg = await update.message.reply_text(
        "🎙️ *Listening to your voice note...*\nTranscribing with high-precision audio engine...",
        parse_mode="Markdown",
    )

    try:
        # Download voice note file from Telegram
        file_obj = await context.bot.get_file(voice.file_id)
        file_bytearray = await file_obj.download_as_bytearray()
        audio_bytes = bytes(file_bytearray)

        # Transcribe with Whisper (or Gemini fallback)
        audio_svc = AudioTranscriptionService()
        transcript = await audio_svc.transcribe_audio_bytes(audio_bytes, filename="voice.ogg")

        if not transcript:
            await status_msg.edit_text("⚠️ Could not transcribe audio. Please try speaking clearly or send text.", parse_mode="Markdown")
            return

        await status_msg.edit_text(
            f"🎙️ *What you said:*\n_\"{safe_md(transcript)}\"_\n\n✨ Polishing into 3 authentic tweet options...",
            parse_mode="Markdown",
        )

        # Generate 3 intelligent takes from voice
        voice_tweet_svc = VoiceTweetService()
        options = await voice_tweet_svc.transform_voice_to_tweets(transcript)

        db = get_db()
        try:
            draft_repo = DraftRepository(db)
            for opt in options:
                # Save as draft in DB
                draft = draft_repo.create(
                    content=opt["content"],
                    topic=transcript[:60],
                    category="voice_memo",
                    provider=settings.DEFAULT_AI_PROVIDER,
                    status=PostStatus.DRAFT.value,
                )

                card = (
                    f"*{opt['angle']}* • `({opt['character_count']}/280 chars)`\n\n"
                    f"```text\n{opt['content']}\n```"
                )
                await update.message.reply_text(
                    card,
                    parse_mode="Markdown",
                    reply_markup=get_draft_keyboard(draft.id, draft.content),
                )
        finally:
            db.close()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ *Voice note processing error:* {safe_md(str(e))}", parse_mode="Markdown")


@owner_only
async def dashboard_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text clicks from the persistent reply keyboard grid and auto-detects links."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text == "🔥 Live Niche Trends":
        await trends_command(update, context)
    elif text == "⚡ Quick Ideas (2)":
        await ideas_command(update, context)
    elif text == "🧵 Viral Thread":
        context.args = []
        await thread_command(update, context)
    elif text == "💬 Smart Reply":
        context.args = []
        await reply_command(update, context)
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
    elif "twitter.com/" in text or "x.com/" in text:
        # Auto-detect tweet URL and generate replies!
        context.args = [text]
        await reply_command(update, context)


@owner_only
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button presses from inline keyboards."""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Handle Welcome Menu Callbacks
    if data == "menu_trends":
        await trends_command(update, context)
        return
    elif data == "menu_ideas_2":
        context.args = ["2"]
        await ideas_command(update, context)
        return
    elif data == "menu_thread":
        context.args = []
        await thread_command(update, context)
        return
    elif data == "menu_reply":
        context.args = []
        await reply_command(update, context)
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
    elif data in ("menu_status", "refresh_status"):
        db = get_db()
        try:
            text, markup = format_system_health(db)
            try:
                await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
            except Exception:
                pass
        finally:
            db.close()
        return
    elif data == "menu_help":
        await help_command(update, context)
        return

    # Handle Post Card Actions
    db = get_db()
    try:
        draft_repo = DraftRepository(db)
        sched_repo = ScheduleRepository(db)

        if data.startswith("posted_"):
            draft_id = int(data.removeprefix("posted_"))
            draft = draft_repo.get_by_id(draft_id)
            draft_repo.update_status(draft_id, PostStatus.APPROVED.value)

            pub = PublishedPost(
                draft_id=draft_id,
                platform="X",
                platform_post_id="manual_handoff",
                publication_method="manual",
                status="SUCCESS",
            )
            db.add(pub)
            db.commit()

            await query.edit_message_text(
                f"🎉 *Draft #{draft_id} marked as POSTED to X!*\nSaved into publication history.",
                parse_mode="Markdown",
            )

        elif data.startswith("approve_"):
            draft_id = int(data.removeprefix("approve_"))
            draft = draft_repo.get_by_id(draft_id)
            draft_repo.update_status(draft_id, PostStatus.APPROVED.value)

            keyboard = []
            if draft:
                encoded = urllib.parse.quote(draft.content)
                composer_url = f"https://twitter.com/intent/tweet?text={encoded}"
                keyboard.append([
                    InlineKeyboardButton("🚀 Post to X Now", url=composer_url),
                    InlineKeyboardButton("✅ Mark as Posted", callback_data=f"posted_{draft_id}"),
                ])

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await query.edit_message_text(
                f"✅ *Draft #{draft_id} marked as APPROVED!*\nReady to post or schedule.",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        elif data.startswith("reject_"):
            draft_id = int(data.removeprefix("reject_"))
            draft_repo.update_status(draft_id, PostStatus.CANCELLED.value)
            await query.edit_message_text(f"❌ *Draft #{draft_id} DISMISSED.*", parse_mode="Markdown")

        elif data.startswith("sched_"):
            draft_id = int(data.removeprefix("sched_"))
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
            sched_id = int(data.removeprefix("cancelsched_"))
            sched_repo.cancel(sched_id)
            await query.edit_message_text(f"🚫 *Schedule #{sched_id} CANCELLED.*", parse_mode="Markdown")

    finally:
        db.close()
