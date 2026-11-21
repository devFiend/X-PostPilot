"""
CLI command: generate
"""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from postpilot.database.db import get_db
from postpilot.services.content import ContentService

app = typer.Typer(help="Generate social posts using AI.")
console = Console()


@app.callback(invoke_without_command=True)
def generate(
    topic: str = typer.Option(..., "--topic", "-t", help="Topic or premise of the post"),
    count: int = typer.Option(3, "--count", "-c", help="Number of distinct variants to generate"),
    category: str = typer.Option("educational", "--category", help="Category: educational, contrarian, dev_tips, etc."),
    provider: str = typer.Option(None, "--provider", "-p", help="Provider override: groq, gemini, or ollama"),
):
    """Generate X post variants and save them as drafts."""
    console.print(f"[bold cyan]🤖 Generating {count} posts for topic:[/] [yellow]'{topic}'[/] using [magenta]{provider or 'auto'}[/]...")

    db = get_db()
    try:
        service = ContentService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        drafts = loop.run_until_complete(
            service.generate_drafts(topic=topic, category=category, count=count, provider=provider)
        )

        for d in drafts:
            console.print(
                Panel(
                    d.content,
                    title=f"[bold green]Draft #{d.id}[/] ([cyan]{d.category}[/]) - [dim]{d.character_count} chars[/]",
                    border_style="green",
                )
            )
        console.print("[dim]Use 'postpilot drafts' or 'postpilot approve <id>' to take action.[/]")
    finally:
        db.close()
