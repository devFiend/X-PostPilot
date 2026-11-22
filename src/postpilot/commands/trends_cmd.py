"""
CLI command for Trend Pulse & Breaking Niche News Radar.
"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from postpilot.database.db import get_db
from postpilot.services.trends import TrendPulseService

app = typer.Typer(help="Scan live niche trends and generate viral tweet takes.")
console = Console()


@app.callback(invoke_without_command=True)
def trends_main(
    limit: int = typer.Option(3, "--limit", "-l", help="Number of trends to scan."),
):
    """Scan Hacker News and top X niche curators for breakout conversations."""
    console.print("[bold cyan]🔥 Scanning live niche trends across Hacker News & top X curators...[/]")

    db = get_db()
    try:
        service = TrendPulseService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        trends = loop.run_until_complete(service.scan_live_trends(limit=limit))
        loop.close()

        if not trends:
            console.print("[yellow]No major breakout stories detected in your niche right now.[/]")
            return

        for idx, item in enumerate(trends, start=1):
            table = Table(title=f"Trend #{idx}: {item['topic']} (Score: {item['score']})", show_header=True)
            table.add_column("Property", style="bold cyan")
            table.add_column("Details", style="white")

            table.add_row("Headline", item["headline"])
            table.add_row("Source", item["source"])
            table.add_row("Context", item["summary"])
            console.print(table)

            for take in item.get("takes", []):
                panel = Panel(
                    f"{take['content']}\n\n[dim]({take['character_count']}/280 chars)[/]",
                    title=f"[bold green]{take['angle']}[/]",
                    border_style="green",
                )
                console.print(panel)
    finally:
        db.close()
