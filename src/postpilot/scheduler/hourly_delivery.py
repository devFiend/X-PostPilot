"""
Content Delivery Drip Job.
Runs spaced out during waking hours (08:00 - 23:59 in user's configured timezone).
Delivers 1 fresh post card at a time (3 times per hour: :00, :20, :40) using TweetDNA multi-creator intelligence.
Provides 1-tap direct 'Post to X Now' button launching the official native X composer.
"""

import asyncio
from datetime import datetime, timezone
import pytz
import httpx
from rich.console import Console
from telegram.helpers import escape_markdown

from postpilot.database.db import get_db
from postpilot.database.models import PostStatus
from postpilot.database.repositories import DraftRepository
from postpilot.services.dna import DNAService
from postpilot.telegram.keyboards import get_draft_keyboard
from postpilot.utils.config import settings

console = Console()


def safe_md(text: str) -> str:
    """Escape text for Telegram legacy Markdown to prevent parser errors on underscores."""
    if not text:
        return ""
    return escape_markdown(str(text), version=1)


def is_active_hour(tz_name: str = "Africa/Lagos") -> bool:
    """Check if current time is within 08:00 to 23:59 in the given timezone."""
    try:
        tz = pytz.timezone(tz_name)
        now_local = datetime.now(tz)
        hour = now_local.hour
        return 8 <= hour <= 23
    except Exception:
        hour = datetime.now().hour
        return 8 <= hour <= 23


async def deliver_drip_post(count: int = 1):
    """
    Generate 1 (or requested count) fresh post from creator pool and dispatch individually to Telegram.
    Runs 3 times an hour (every 20 minutes) so the user receives a steady, spaced drip of content.
    """
    if not is_active_hour(settings.TIMEZONE):
        console.print(f"[dim]Outside active hours (08:00 - 23:59 {settings.TIMEZONE}). Skipping drip drop.[/]")
        return

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_OWNER_ID:
        console.print("[yellow]Notice: Telegram credentials not set. Saving drip draft to DB only.[/]")
        db = get_db()
        try:
            dna_service = DNAService(db)
            posts = await dna_service.generate_posts_from_pool(count=count)
            draft_repo = DraftRepository(db)
            for item in posts:
                draft_repo.create(
                    content=item["content"],
                    topic=item.get("topic", "Drip drop"),
                    category="creator_dna",
                    provider=settings.DEFAULT_AI_PROVIDER,
                    status=PostStatus.PENDING_APPROVAL.value,
                )
            console.print(f"[bold green]✔ Saved {len(posts)} drip draft(s) into database.[/]")
        finally:
            db.close()
        return

    console.print(f"[bold cyan]⏰ Running Content Drip Drop for Telegram ({count} post)...[/]")
    db = get_db()
    try:
        dna_service = DNAService(db)
        posts = await dna_service.generate_posts_from_pool(count=count)
        draft_repo = DraftRepository(db)

        # Telegram endpoint
        send_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        async with httpx.AsyncClient(timeout=15.0) as client:
            for item in posts:
                # 1. Save to DB
                draft = draft_repo.create(
                    content=item["content"],
                    topic=item.get("topic", "Content drip"),
                    category="creator_dna",
                    provider=settings.DEFAULT_AI_PROVIDER,
                    status=PostStatus.PENDING_APPROVAL.value,
                )

                # 2. Build keyboard with direct native X compose intent & Mark as Posted
                markup = get_draft_keyboard(draft.id, draft.content)
                reply_markup_dict = markup.to_dict()

                creator_name = item.get("creator", "general")
                safe_creator = safe_md(creator_name)
                creator_tag = f"• Style: @{safe_creator}" if creator_name != "general" else "• Curated Style"

                card_text = (
                    f"💡 *Content Drop* {creator_tag} • `({draft.character_count}/280 chars)`\n\n"
                    f"```text\n{draft.content}\n```"
                )

                payload = {
                    "chat_id": settings.TELEGRAM_OWNER_ID,
                    "text": card_text,
                    "parse_mode": "Markdown",
                    "reply_markup": reply_markup_dict,
                }

                res = await client.post(send_url, json=payload)
                if res.status_code != 200:
                    console.print(f"[red]Telegram send failed ({res.status_code}): {res.text}[/]")

        console.print(f"[bold green]✔ Delivered {len(posts)} drip post card(s) to Telegram owner {settings.TELEGRAM_OWNER_ID}![/]")
    except Exception as e:
        console.print(f"[bold red]✘ Error in drip delivery: {e}[/]")
    finally:
        db.close()


# Backward-compatible alias
deliver_hourly_posts = deliver_drip_post


def run_hourly_delivery_sync():
    """Synchronous runner for APScheduler cron job (runs every 15 mins during active hours)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(deliver_drip_post(count=1))
    finally:
        loop.close()
