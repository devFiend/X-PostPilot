"""
CLI command: init
"""

import typer
from rich.console import Console
from rich.prompt import Prompt
from postpilot.database.db import init_db, get_db
from postpilot.database.models import User, CreatorProfile

app = typer.Typer(help="Initialize PostPilot local database and configuration.")
console = Console()


@app.callback(invoke_without_command=True)
def init_main():
    """Run interactive setup for PostPilot."""
    console.print("[bold cyan]🚀 Initializing PostPilot ($0-First Setup)...[/]")
    init_db()

    db = get_db()
    try:
        user = db.query(User).first()
        if not user:
            name = Prompt.ask("Enter your Creator Name", default="DevFiend")
            timezone = Prompt.ask("Enter your Timezone", default="Africa/Lagos")
            pillars = Prompt.ask("Content Pillars (comma-separated)", default="Software Engineering, AI, Startups")

            user = User(timezone=timezone)
            db.add(user)
            db.commit()
            db.refresh(user)

            profile = CreatorProfile(
                user_id=user.id,
                name=name,
                content_pillars=pillars,
            )
            db.add(profile)
            db.commit()
            console.print("[bold green]✔ Initialized creator profile and SQLite database successfully![/]")
        else:
            console.print("[yellow]PostPilot database is already initialized.[/]")
    finally:
        db.close()
