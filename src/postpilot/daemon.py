"""
Unified PostPilot Daemon.
Runs the APScheduler worker, Telegram Bot polling loop, and an optional HTTP health check server.
Compatible with Render (Free Web Service / Background Worker), Fly.io, Railway, and Docker.
"""

import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from rich.console import Console

from postpilot.database.db import init_db
from postpilot.scheduler.worker import scheduler, start_worker
from postpilot.telegram.bot import run_telegram_bot
from postpilot.utils.config import settings

console = Console()


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler to satisfy Render Web Service health checks."""

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "PostPilot", "version": "0.1.0"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence routine health check log noise
        pass


def run_http_server(port: int):
    """Run lightweight HTTP server on the assigned port."""
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    console.print(f"[bold green]✔ HTTP Health Check server listening on 0.0.0.0:{port}[/]")
    server.serve_forever()


def start_daemon():
    """Launch all services in a single unified process."""
    console.print("[bold cyan]🚀 Starting PostPilot Unified Daemon...[/]\n")

    # 1. Initialize DB tables
    init_db()

    # 2. Check if running inside Render/Cloud with an assigned HTTP PORT
    port_env = os.environ.get("PORT")
    if port_env:
        try:
            port = int(port_env)
            http_thread = threading.Thread(target=run_http_server, args=(port,), daemon=True)
            http_thread.start()
        except Exception as e:
            console.print(f"[yellow]Warning: Could not bind HTTP port {port_env}: {e}[/]")

    # 3. Start APScheduler in background thread
    if not scheduler.running:
        scheduler.start()
        console.print("[bold green]✔ APScheduler active & persistent jobstore online.[/]")

    # 4. Start Telegram Bot in main loop (if configured)
    if settings.TELEGRAM_BOT_TOKEN:
        console.print(f"[bold green]✔ Starting Telegram Bot (Owner ID: {settings.TELEGRAM_OWNER_ID or 'Not Set'})...[/]")
        run_telegram_bot()
    else:
        console.print("[yellow]Notice: TELEGRAM_BOT_TOKEN not configured. Running scheduler in stand-alone daemon mode.[/]")
        import time
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            console.print("[yellow]Scheduler safely shut down.[/]")


if __name__ == "__main__":
    start_daemon()
