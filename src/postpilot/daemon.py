"""
Unified PostPilot Daemon.
Runs the APScheduler worker, Telegram Bot polling loop, and an HTTP server with auto-approval redirect.
Compatible with Render (Free Web Service / Background Worker), Fly.io, Railway, and Docker.
"""

import os
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from rich.console import Console

from postpilot.database.db import init_db, get_db
from postpilot.database.models import Draft, PostStatus, PublishedPost
from postpilot.database.repositories import DraftRepository
from postpilot.scheduler.worker import scheduler
from postpilot.telegram.bot import run_telegram_bot
from postpilot.utils.config import settings

console = Console()


class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    HTTP handler:
    - Answers Render Web Service health checks on / and /health.
    - Handles /post/{draft_id}: Automatically marks draft as APPROVED and PUBLISHED in DB,
      then sends a 302 redirect to the official Twitter Compose intent!
    """

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "PostPilot", "version": "0.1.0"}')

        elif self.path.startswith("/post/"):
            try:
                raw_id = self.path.split("/post/")[1].split("?")[0]
                draft_id = int(raw_id)
                db = get_db()
                try:
                    repo = DraftRepository(db)
                    draft = repo.get_by_id(draft_id)
                    if draft:
                        # Auto-approve and mark as published/handed off!
                        repo.update_status(draft_id, PostStatus.APPROVED.value)

                        pub = PublishedPost(
                            draft_id=draft.id,
                            platform="X",
                            platform_post_id="manual_handoff",
                            publication_method="manual",
                            status="SUCCESS",
                        )
                        db.add(pub)
                        db.commit()

                        encoded = urllib.parse.quote(draft.content)
                        redirect_target = f"https://twitter.com/intent/tweet?text={encoded}"

                        console.print(f"[bold green]✔ Auto-approved and redirected Draft #{draft_id} to X Composer![/]")
                        self.send_response(302)
                        self.send_header("Location", redirect_target)
                        self.end_headers()
                        return
                finally:
                    db.close()
            except Exception as e:
                console.print(f"[red]Error in /post/ auto-approve redirect: {e}[/]")

            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Draft not found")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence routine health check log noise
        pass


def run_http_server(port: int):
    """Run lightweight HTTP server on the assigned port."""
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    console.print(f"[bold green]✔ HTTP server listening on 0.0.0.0:{port} (Health check + Auto-Approve redirect)[/]")
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
