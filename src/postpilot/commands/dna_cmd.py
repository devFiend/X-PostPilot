"""
CLI command: dna (TweetDNA Creator Intelligence & Hourly Drop Controls)
"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from postpilot.database.db import get_db, init_db
from postpilot.services.dna import DNAService
from postpilot.scheduler.hourly_delivery import deliver_hourly_posts

app = typer.Typer(help="TweetDNA creator intelligence and style cloning commands.")
console = Console()


@app.command("track")
def track(username: str = typer.Argument(..., help="X handle of the creator to track (e.g. @levelsio)")):
    """Scrape and extract Content DNA for a creator."""
    init_db()
    clean_user = username.lstrip("@").strip()
    console.print(f"[bold cyan]🧬 Analyzing and extracting Content DNA for @{clean_user}...[/]")

    db = get_db()
    try:
        service = DNAService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(service.track_creator(clean_user))

        dna = result["dna"]
        console.print(f"[bold green]✔ Successfully analyzed @{clean_user} ({result['tweets_count']} tweets analyzed)![/]")
        console.print(f"• Tone: [cyan]{dna.tone}[/]")
        console.print(f"• Content Pillars: [yellow]{dna.content_pillars}[/]")
        console.print(f"• Hook Styles: [magenta]{dna.hook_patterns}[/]")
        console.print(f"[green]Added to your hourly generation pool! Posts will now reflect this creator's style.[/]")
    finally:
        db.close()


@app.command("list")
def list_creators():
    """List all tracked creators in your intelligence pool."""
    init_db()
    db = get_db()
    try:
        service = DNAService(db)
        creators = service.list_creators()
        if not creators:
            console.print("[yellow]No creators tracked yet. Track one with: postpilot dna track @username[/]")
            return

        table = Table(title="TweetDNA Tracked Creator Pool")
        table.add_column("Username", style="cyan")
        table.add_column("Tweets Cached", justify="right", style="green")
        table.add_column("Tone", style="white")
        table.add_column("Last Synced", style="dim")

        for c in creators:
            tone = c.dna.tone if c.dna else "Analyzing"
            last_synced = c.last_synced_at.strftime("%Y-%m-%d %H:%M") if c.last_synced_at else "Recent"
            table.add_row(f"@{c.username}", str(len(c.tweets)), tone, last_synced)

        console.print(table)
    finally:
        db.close()


@app.command("untrack")
def untrack(username: str = typer.Argument(..., help="X handle to remove")):
    """Remove a creator from the tracking pool."""
    init_db()
    clean_user = username.lstrip("@").strip()
    db = get_db()
    try:
        service = DNAService(db)
        if service.untrack_creator(clean_user):
            console.print(f"[bold yellow]✔ Removed @{clean_user} from tracked creators.[/]")
        else:
            console.print(f"[bold red]✘ Creator @{clean_user} not found.[/]")
    finally:
        db.close()


@app.command("ideas")
def ideas(
    count: int = typer.Option(4, "--count", "-c", help="Number of posts to generate"),
    topic: str = typer.Option(None, "--topic", "-t", help="Optional specific topic"),
):
    """Generate fresh posts synthesized from your creator pool."""
    init_db()
    console.print(f"[bold cyan]⚡ Generating {count} posts from your creator intelligence pool...[/]")
    db = get_db()
    try:
        service = DNAService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        posts = loop.run_until_complete(service.generate_posts_from_pool(count=count, topic=topic))

        for idx, item in enumerate(posts, start=1):
            creator_tag = f"Style: @{item['creator']}" if item.get('creator') != 'general' else "General Style"
            console.print(
                Panel(
                    item["content"],
                    title=f"[bold green]Post #{idx}[/] ([cyan]{creator_tag}[/]) - [dim]{len(item['content'])} chars[/]",
                    border_style="green",
                )
            )
    finally:
        db.close()


@app.command("drop-now")
def drop_now(count: int = typer.Option(4, "--count", "-c", help="Number of posts to deliver")):
    """Trigger an immediate test run of the hourly content delivery."""
    init_db()
    console.print(f"[bold cyan]🚀 Triggering immediate hourly delivery test ({count} posts)...[/]")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(deliver_hourly_posts(count=count))
        console.print("[bold green]✔ Delivery test complete![/]")
    finally:
        loop.close()
