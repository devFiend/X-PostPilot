"""
CLI command: publish
"""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from postpilot.database.db import get_db
from postpilot.services.publishing import PublishingService

app = typer.Typer(help="Publish approved posts immediately.")
console = Console()


@app.callback(invoke_without_command=True)
def publish(
    draft_id: int = typer.Argument(..., help="Draft ID to publish"),
    method: str = typer.Option(None, "--method", "-m", help="Publishing method: manual or x_api"),
):
    """Dispatch an approved post."""
    db = get_db()
    try:
        service = PublishingService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(service.publish_draft(draft_id, method=method))

        if result.success:
            if result.method == "manual":
                console.print(
                    Panel(
                        f"[bold green]Post copied to clipboard![/]\n\n"
                        f"[cyan]X Web Intent URL:[/] {result.url}\n\n"
                        f"[dim]Paste on X and click Post.[/]",
                        title=f"[bold green]✔ Manual Publishing Handoff (#{draft_id})[/]",
                        border_style="green",
                    )
                )
            else:
                console.print(f"[bold green]✔ Successfully published directly to X! URL: {result.url}[/]")
        else:
            console.print(f"[bold red]✘ Publishing failed: {result.error_message}[/]")
    finally:
        db.close()
