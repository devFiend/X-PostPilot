"""
CLI command: schedule
"""

from datetime import datetime
import typer
from rich.console import Console
from postpilot.database.db import get_db
from postpilot.database.repositories import DraftRepository, ScheduleRepository
from postpilot.database.models import PostStatus
from postpilot.utils.config import settings

app = typer.Typer(help="Schedule posts for publication.")
console = Console()


@app.callback(invoke_without_command=True)
def schedule_post(
    draft_id: int = typer.Argument(..., help="ID of draft to schedule"),
    at: str = typer.Option(..., "--at", help="Target timestamp (format: YYYY-MM-DD HH:MM)"),
):
    """Schedule an approved draft for future publication."""
    db = get_db()
    try:
        draft_repo = DraftRepository(db)
        draft = draft_repo.get_by_id(draft_id)
        if not draft:
            console.print(f"[bold red]✘ Draft #{draft_id} not found.[/]")
            return

        if draft.status not in (PostStatus.APPROVED.value, PostStatus.DRAFT.value):
            console.print(f"[bold red]✘ Cannot schedule draft with status {draft.status}.[/]")
            return

        try:
            target_time = datetime.strptime(at, "%Y-%m-%d %H:%M")
        except ValueError:
            console.print("[bold red]✘ Invalid date format. Use 'YYYY-MM-DD HH:MM'.[/]")
            return

        schedule_repo = ScheduleRepository(db)
        schedule_repo.schedule(draft_id=draft_id, scheduled_at=target_time, timezone=settings.TIMEZONE)
        draft_repo.update_status(draft_id, PostStatus.SCHEDULED.value)

        console.print(f"[bold green]✔ Draft #{draft_id} scheduled for {at} ({settings.TIMEZONE}).[/]")
    finally:
        db.close()
