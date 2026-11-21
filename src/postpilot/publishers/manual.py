"""
Manual Publisher: $0-First, zero ban risk publishing adapter.
Prepares Twitter web intent URL, copies text to clipboard, and facilitates Telegram copy.
"""

import urllib.parse
from postpilot.publishers.base import BasePublisher, PublishResult


class ManualPublisher(BasePublisher):
    def __init__(self):
        pass

    async def test_connection(self) -> bool:
        return True

    async def publish(self, content: str) -> PublishResult:
        # Generate Web Intent URL
        encoded_text = urllib.parse.quote(content)
        intent_url = f"https://twitter.com/intent/tweet?text={encoded_text}"

        # Attempt to copy to system clipboard if pyperclip is available
        try:
            import pyperclip
            pyperclip.copy(content)
        except Exception:
            pass

        return PublishResult(
            success=True,
            platform="X",
            post_id="manual_handoff",
            url=intent_url,
            method="manual",
            error_message=None,
        )
