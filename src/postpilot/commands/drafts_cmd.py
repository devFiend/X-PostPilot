"""
CLI command: drafts
"""

import typer
from rich.console import Console
from rich.table import Table
from postpilot.database.db import get_db
from postpilot.database.repositories import DraftRepository
from postpilot.database.models import PostStatus

app = typer.Typer(help="Manage and inspect draft posts.")
console = Console()


@app.callback(invoke_without_command=True)
def list_drafts(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status (DRAFT, APPROVED, etc.)")
):
    """List all stored drafts."""
    db = get_db()
    try:
        repo = DraftRepository(db)
        drafts = repo.list_all(status=status)
        if not drafts:
            console.print("[yellow]No drafts found.[/]")
            return

        table = Table(title="PostPilot Content Drafts")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Preview", style="white")
        table.add_column("Chars", justify="right", style="dim")
        table.add_column("Status", style="green")

        for d in drafts:
            preview = d.content[:60] + "..." if len(d.content) > 60 else d.content
            table.add_row(str(d.id), d.category, preview, str(d.character_count), d.status)

        console.print(table)
    finally:
        db.close()


@app.command("approve")
def approve_draft(draft_id: int):
    """Mark a draft as APPROVED."""
    db = get_db()
    try:
        repo = DraftRepository(db)
        updated = repo.update_status(draft_id, PostStatus.APPROVED.value)
        if updated:
            console.print(f"[bold green]✔ Draft #{draft_id} marked as APPROVED.[/]")
        else:
            console.print(f"[bold red]✘ Draft #{draft_id} not found.[/]")
    finally:
        db.close()


@app.command("delete")
def delete_draft(draft_id: int):
    """Delete a draft."""
    db = get_db()
    try:
        repo = DraftRepository(db)
        if repo.delete(draft_id):
            console.print(f"[bold yellow]Draft #{draft_id} deleted.[/]")
        else:
            console.print(f"[bold red]✘ Draft #{draft_id} not found.[/]")
    finally:
        db.close()
