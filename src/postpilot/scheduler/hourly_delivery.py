"""
Hourly Content Delivery Job.
Runs at the top of every hour between 08:00 and 23:59 (in user's configured timezone).
Generates 4-5 fresh post drafts using TweetDNA multi-creator intelligence
and delivers them individually to Telegram with 1-tap 'Post to X Now' buttons.
"""

import asyncio
from datetime import datetime, timezone
import pytz
import httpx
from rich.console import Console

from postpilot.database.db import get_db
from postpilot.database.models import PostStatus
from postpilot.database.repositories import DraftRepository
from postpilot.services.dna import DNAService
from postpilot.telegram.keyboards import get_draft_keyboard
from postpilot.utils.config import settings

console = Console()


def is_active_hour(tz_name: str = "Africa/Lagos") -> bool:
    """Check if current time is within 08:00 to 23:59 in the given timezone."""
    try:
        tz = pytz.timezone(tz_name)
        now_local = datetime.now(tz)
        hour = now_local.hour
        # Active hours: 8 AM (8) through 11:59 PM (23)
        return 8 <= hour <= 23
    except Exception:
        # Fallback to local system time
        hour = datetime.now().hour
        return 8 <= hour <= 23


async def deliver_hourly_posts(count: int = 4):
    """Generate 4-5 posts from creator intelligence pool and dispatch individually to Telegram."""
    if not is_active_hour(settings.TIMEZONE):
        console.print(f"[dim]Outside active hours (08:00 - 23:59 {settings.TIMEZONE}). Skipping hourly drop.[/]")
        return

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_OWNER_ID:
        console.print("[yellow]Notice: Telegram credentials not set. Saving hourly drafts to DB only.[/]")
        db = get_db()
        try:
            dna_service = DNAService(db)
            posts = await dna_service.generate_posts_from_pool(count=count)
            draft_repo = DraftRepository(db)
            for item in posts:
                draft_repo.create(
                    content=item["content"],
                    topic=item.get("topic", "Hourly drop"),
                    category="creator_dna",
                    provider=settings.DEFAULT_AI_PROVIDER,
                    status=PostStatus.PENDING_APPROVAL.value,
                )
            console.print(f"[bold green]✔ Saved {len(posts)} hourly drafts into database.[/]")
        finally:
            db.close()
        return

    console.print(f"[bold cyan]⏰ Running Hourly Content Drop for Telegram ({count} posts)...[/]")
    db = get_db()
    try:
        dna_service = DNAService(db)
        posts = await dna_service.generate_posts_from_pool(count=count)
        draft_repo = DraftRepository(db)

        # Telegram endpoint
        send_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        async with httpx.AsyncClient(timeout=15.0) as client:
            for idx, item in enumerate(posts, start=1):
                # 1. Save to DB
                draft = draft_repo.create(
                    content=item["content"],
                    topic=item.get("topic", "Hourly drop"),
                    category="creator_dna",
                    provider=settings.DEFAULT_AI_PROVIDER,
                    status=PostStatus.PENDING_APPROVAL.value,
                )

                # 2. Build keyboard
                markup = get_draft_keyboard(draft.id, draft.content)
                reply_markup_dict = markup.to_dict()

                creator_tag = f"• Style: @{item['creator']}" if item.get('creator') != 'general' else ""
                card_text = (
                    f"💡 *Hourly Drop ({idx}/{len(posts)})* {creator_tag}\n\n"
                    f"```text\n{draft.content}\n```"
                )

                payload = {
                    "chat_id": settings.TELEGRAM_OWNER_ID,
                    "text": card_text,
                    "parse_mode": "Markdown",
                    "reply_markup": reply_markup_dict,
                }

                await client.post(send_url, json=payload)
                # Small pause between messages so they arrive sequentially
                await asyncio.sleep(0.5)

        console.print(f"[bold green]✔ Delivered {len(posts)} individual post cards to Telegram owner {settings.TELEGRAM_OWNER_ID}![/]")
    except Exception as e:
        console.print(f"[bold red]✘ Error in hourly delivery: {e}[/]")
    finally:
        db.close()


def run_hourly_delivery_sync():
    """Synchronous runner for APScheduler cron job."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(deliver_hourly_posts(count=4))
    finally:
        loop.close()
