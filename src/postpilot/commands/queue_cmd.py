"""
CLI command: queue
"""

import typer
from rich.console import Console
from rich.table import Table
from postpilot.database.db import get_db
from postpilot.database.repositories import ScheduleRepository

app = typer.Typer(help="Manage post publishing queue.")
console = Console()


@app.callback(invoke_without_command=True)
def show_queue():
    """Display pending scheduled queue."""
    db = get_db()
    try:
        repo = ScheduleRepository(db)
        pending = repo.list_pending()
        if not pending:
            console.print("[dim]Publishing queue is currently empty.[/]")
            return

        table = Table(title="PostPilot Scheduled Queue")
        table.add_column("Schedule ID", justify="right", style="cyan")
        table.add_column("Draft ID", justify="right", style="yellow")
        table.add_column("Scheduled At", style="green")
        table.add_column("Timezone", style="dim")
        table.add_column("Status", style="magenta")

        for item in pending:
            table.add_row(
                str(item.id),
                str(item.draft_id),
                item.scheduled_at.strftime("%Y-%m-%d %H:%M"),
                item.timezone,
                item.status,
            )

        console.print(table)
    finally:
        db.close()
