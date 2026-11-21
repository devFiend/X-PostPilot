"""
CLI command: config
"""

import typer
from rich.console import Console
from postpilot.utils.config import settings

app = typer.Typer(help="Manage settings and creator profile.")
console = Console()


@app.command("show")
def show_config():
    """Display active settings."""
    console.print("[bold cyan]PostPilot Active Settings:[/]")
    console.print(f"Timezone: [green]{settings.TIMEZONE}[/]")
    console.print(f"AI Provider: [green]{settings.DEFAULT_AI_PROVIDER}[/]")
    console.print(f"Publish Method: [green]{settings.DEFAULT_PUBLISH_METHOD}[/]")
    console.print(f"Publish Mode: [green]{settings.DEFAULT_PUBLISH_MODE}[/]")
    console.print(f"Max Posts/Day: [green]{settings.MAX_POSTS_PER_DAY}[/]")
