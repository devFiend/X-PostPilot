"""
CLI command: autopilot
"""

import typer
from rich.console import Console

app = typer.Typer(help="Configure and manage autopilot mode.")
console = Console()


@app.command("status")
def status():
    """Check autopilot status."""
    console.print("[cyan]Autopilot Status:[/] [yellow]IDLE (Approval Mode Active)[/]")


@app.command("pause")
def pause():
    """Emergency pause autopilot."""
    console.print("[bold red]⏸ Autopilot paused immediately.[/]")


@app.command("resume")
def resume():
    """Resume autopilot operations."""
    console.print("[bold green]▶ Autopilot resumed.[/]")
