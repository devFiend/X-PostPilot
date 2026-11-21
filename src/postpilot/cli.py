"""
Command-Line Interface for PostPilot using Typer and Rich.
"""

import typer
from rich.console import Console

from postpilot import __app_name__, __version__
from postpilot.commands import (
    autopilot_cmd,
    config_cmd,
    doctor_cmd,
    drafts_cmd,
    generate_cmd,
    init_cmd,
    publish_cmd,
    queue_cmd,
    schedule_cmd,
)

app = typer.Typer(
    name=__app_name__,
    help="PostPilot: AI-powered content management & publishing assistant for X (Twitter).",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]{__app_name__}[/] version [bold green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Personal AI-powered content management and publishing assistant."""
    pass


# Register CLI Subcommands
app.add_typer(init_cmd.app, name="init", help="Initialize PostPilot configuration and database.")
app.add_typer(generate_cmd.app, name="generate", help="Generate draft posts using AI.")
app.add_typer(drafts_cmd.app, name="drafts", help="Manage and inspect draft posts.")
app.add_typer(queue_cmd.app, name="queue", help="Manage post publishing queue.")
app.add_typer(schedule_cmd.app, name="schedule", help="Schedule posts for publication.")
app.add_typer(publish_cmd.app, name="publish", help="Publish approved posts immediately.")
app.add_typer(autopilot_cmd.app, name="autopilot", help="Configure and manage autopilot mode.")
app.add_typer(config_cmd.app, name="config", help="Manage settings and creator profile.")
app.add_typer(doctor_cmd.app, name="doctor", help="Run system diagnostics and connectivity checks.")


@app.command("status")
def status():
    """Display system health, active AI provider, and queue summary."""
    from postpilot.commands.status_cmd import run_status
    run_status()


@app.command("run")
def run_worker():
    """Run the scheduler and background worker process."""
    from postpilot.scheduler.worker import start_worker
    start_worker()


@app.command("telegram")
def run_telegram():
    """Start the Telegram Bot long-polling service."""
    from postpilot.telegram.bot import run_telegram_bot
    run_telegram_bot()


if __name__ == "__main__":
    app()
