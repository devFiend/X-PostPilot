"""
CLI command: status
"""

import asyncio
from rich.console import Console
from rich.table import Table
from postpilot.database.db import get_db
from postpilot.database.models import Draft, ScheduledPost
from postpilot.ai.router import AIRouter
from postpilot.publishers.manual import ManualPublisher
from postpilot.publishers.x_publisher import XPublisher
from postpilot.utils.config import settings

console = Console()


def run_status():
    """Check health of AI providers, publishers, and queue."""
    console.print("[bold cyan]🔎 PostPilot System Status & Health Check[/]\n")

    # Provider Readiness
    router = AIRouter()
    table = Table(title="AI Providers Readiness ($0-First)")
    table.add_column("Provider", style="cyan")
    table.add_column("Configured", style="yellow")
    table.add_column("Status", style="green")

    groq_ok = bool(settings.GROQ_API_KEY)
    gemini_ok = bool(settings.GEMINI_API_KEY)
    table.add_row("Groq (Llama-3)", "Yes" if groq_ok else "No", "Ready" if groq_ok else "Missing API Key")
    table.add_row("Gemini (Free Tier)", "Yes" if gemini_ok else "No", "Ready" if gemini_ok else "Missing API Key")
    table.add_row("Ollama (Local $0)", "Localhost", "Offline/Local")
    console.print(table)
    console.print()

    # Publishing Adapters
    pub_table = Table(title="Publishing Adapters")
    pub_table.add_column("Adapter", style="cyan")
    pub_table.add_column("Cost", style="green")
    pub_table.add_column("Status", style="white")

    pub_table.add_row("Manual ($0 Fallback)", "$0 Free (Safe)", "[bold green]Ready (Active)[/]")
    has_x = bool(settings.X_ACCESS_TOKEN)
    pub_table.add_row("Official X API v2", "Pay-per-use ($0.015+)", "[bold green]Configured[/]" if has_x else "[yellow]Unconfigured (Optional)[/]")
    console.print(pub_table)
    console.print()

    # DB Stats
    db = get_db()
    try:
        drafts_count = db.query(Draft).count()
        scheduled_count = db.query(ScheduledPost).count()
        console.print(f"📊 [bold]Local Database:[/] [cyan]{drafts_count}[/] drafts stored | [yellow]{scheduled_count}[/] scheduled posts.")
    finally:
        db.close()
