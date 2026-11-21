"""
APScheduler Background Worker with SQLite persistence and reboot recovery.
Includes hourly content delivery cron job (08:00 - 23:59).
"""

import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console
from postpilot.database.db import get_db, DATABASE_URL
from postpilot.database.models import ScheduledPost, PostStatus
from postpilot.services.publishing import PublishingService
from postpilot.scheduler.hourly_delivery import run_hourly_delivery_sync
from postpilot.utils.config import settings

console = Console()

jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}

scheduler = BackgroundScheduler(jobstores=jobstores)


def execute_scheduled_post(draft_id: int):
    """Callback triggered by APScheduler when post publication is due."""
    db = get_db()
    try:
        service = PublishingService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(service.publish_draft(draft_id))
        if result.success:
            console.print(f"[bold green]✔ Successfully published scheduled post #{draft_id} via {result.method}![/]")
        else:
            console.print(f"[bold red]✘ Failed to publish scheduled post #{draft_id}: {result.error_message}[/]")
    finally:
        db.close()


def configure_hourly_delivery_job():
    """Register the hourly content drop job in APScheduler (runs at minute 0 between 8-23)."""
    try:
        scheduler.add_job(
            run_hourly_delivery_sync,
            trigger=CronTrigger(minute=0, hour="8-23", timezone=settings.TIMEZONE),
            id="hourly_tweetdna_delivery",
            name="Hourly TweetDNA Content Drop",
            replace_existing=True,
        )
        console.print(f"[bold green]✔ Hourly TweetDNA content delivery scheduled (08:00 - 23:59 {settings.TIMEZONE}).[/]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not schedule hourly delivery: {e}[/]")


def start_worker():
    """Start the scheduler background loop with recovery of pending jobs."""
    console.print("[bold cyan]Starting PostPilot Background Scheduler...[/]")
    db = get_db()
    try:
        pending = (
            db.query(ScheduledPost)
            .filter(ScheduledPost.status == PostStatus.SCHEDULED.value)
            .all()
        )
        console.print(f"[yellow]Loaded {len(pending)} pending scheduled posts from database.[/]")
    finally:
        db.close()

    configure_hourly_delivery_job()
    scheduler.start()
    console.print("[bold green]Scheduler active. Press Ctrl+C to stop.[/]")
    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        console.print("[yellow]Scheduler safely stopped.[/]")
