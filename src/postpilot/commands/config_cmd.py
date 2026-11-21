"""
CLI command: config
"""

import typer
from rich.console import Console
from postpilot.database.db import get_db
from postpilot.database.repositories import SettingsRepository
from postpilot.utils.config import settings

app = typer.Typer(help="Manage settings and creator profile.")
console = Console()


@app.command("show")
def show_config():
    """Display active settings."""
    db = get_db()
    try:
        repo = SettingsRepository(db)
        pub_method = repo.get("DEFAULT_PUBLISH_METHOD", settings.DEFAULT_PUBLISH_METHOD)
        ai_provider = repo.get("DEFAULT_AI_PROVIDER", settings.DEFAULT_AI_PROVIDER)

        console.print("[bold cyan]PostPilot Active Configuration:[/]")
        console.print(f"Timezone: [green]{settings.TIMEZONE}[/]")
        console.print(f"AI Provider: [green]{ai_provider}[/]")
        console.print(f"Publish Method: [green]{pub_method}[/] (manual: $0 free | x_api: paid official)")
        console.print(f"Publish Mode: [green]{settings.DEFAULT_PUBLISH_MODE}[/]")
        console.print(f"Max Posts/Day: [green]{settings.MAX_POSTS_PER_DAY}[/]")
    finally:
        db.close()


@app.command("set-publisher")
def set_publisher(method: str = typer.Argument(..., help="Publishing method: manual or x_api")):
    """Switch default publishing method between 'manual' ($0 fallback) and 'x_api'."""
    val = method.lower()
    if val not in ("manual", "x_api"):
        console.print("[bold red]✘ Invalid method. Choose 'manual' or 'x_api'.[/]")
        return

    db = get_db()
    try:
        repo = SettingsRepository(db)
        repo.set("DEFAULT_PUBLISH_METHOD", val)
        console.print(f"[bold green]✔ Default publish method set to: [cyan]{val}[/][/]")
    finally:
        db.close()


@app.command("set-provider")
def set_provider(provider: str = typer.Argument(..., help="AI provider: groq, gemini, or ollama")):
    """Switch default AI provider."""
    val = provider.lower()
    if val not in ("groq", "gemini", "ollama"):
        console.print("[bold red]✘ Invalid provider. Choose 'groq', 'gemini', or 'ollama'.[/]")
        return

    db = get_db()
    try:
        repo = SettingsRepository(db)
        repo.set("DEFAULT_AI_PROVIDER", val)
        console.print(f"[bold green]✔ Default AI provider set to: [cyan]{val}[/][/]")
    finally:
        db.close()
