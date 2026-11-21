"""
CLI command: autopilot
"""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from postpilot.database.db import get_db
from postpilot.services.autopilot import AutopilotService

app = typer.Typer(help="Configure and manage autopilot mode.")
console = Console()


@app.command("status")
def status():
    """Check autopilot status and settings."""
    db = get_db()
    try:
        service = AutopilotService(db)
        enabled = service.is_enabled()
        paused = service.is_paused()
        mode = service.get_mode()

        status_str = "[bold red]PAUSED[/]" if paused else ("[bold green]ENABLED[/]" if enabled else "[yellow]DISABLED[/]")
        console.print(f"Autopilot State: {status_str}")
        console.print(f"Mode: [cyan]{mode}[/] (approval = prepares drafts for review | autopilot = auto-publishes)")
    finally:
        db.close()


@app.command("enable")
def enable():
    """Enable autopilot."""
    db = get_db()
    try:
        service = AutopilotService(db)
        service.enable()
        console.print("[bold green]✔ Autopilot enabled.[/]")
    finally:
        db.close()


@app.command("disable")
def disable():
    """Disable autopilot."""
    db = get_db()
    try:
        service = AutopilotService(db)
        service.disable()
        console.print("[yellow]Autopilot disabled.[/]")
    finally:
        db.close()


@app.command("pause")
def pause():
    """Emergency pause autopilot immediately."""
    db = get_db()
    try:
        service = AutopilotService(db)
        service.pause()
        console.print("[bold red]⏸ Emergency Pause activated. Autopilot halted.[/]")
    finally:
        db.close()


@app.command("resume")
def resume():
    """Resume autopilot operations."""
    db = get_db()
    try:
        service = AutopilotService(db)
        service.resume()
        console.print("[bold green]▶ Autopilot resumed.[/]")
    finally:
        db.close()


@app.command("run-cycle")
def run_cycle(topic: str = typer.Option(None, "--topic", "-t", help="Optional topic override")):
    """Trigger a single autopilot generation and rotation cycle immediately."""
    console.print("[bold cyan]🔄 Running Autopilot cycle...[/]")
    db = get_db()
    try:
        service = AutopilotService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        drafts = loop.run_until_complete(service.execute_cycle(topic=topic))
        for d in drafts:
            console.print(
                Panel(
                    d.content,
                    title=f"[bold green]Autopilot Draft #{d.id}[/] ([cyan]{d.category}[/]) - Status: [magenta]{d.status}[/]",
                    border_style="cyan",
                )
            )
    except Exception as e:
        console.print(f"[bold red]✘ Autopilot cycle failed: {e}[/]")
    finally:
        db.close()
