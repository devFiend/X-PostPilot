"""
Official X API v2 Publisher.
Publishes via authorized OAuth credentials to POST https://api.twitter.com/2/tweets.
"""

import httpx
from postpilot.publishers.base import BasePublisher, PublishResult
from postpilot.utils.config import settings


class XPublisher(BasePublisher):
    def __init__(self):
        self.endpoint = "https://api.twitter.com/2/tweets"
        self.bearer_token = settings.X_ACCESS_TOKEN

    async def test_connection(self) -> bool:
        if not self.bearer_token:
            return False
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://api.twitter.com/2/users/me", headers=headers)
                return res.status_code == 200
        except Exception:
            return False

    async def publish(self, content: str) -> PublishResult:
        if not self.bearer_token:
            return PublishResult(
                success=False,
                method="x_api",
                error_message="X credentials not configured in .env. Switch to manual mode or add tokens.",
            )

        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": content}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.endpoint, json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json().get("data", {})
                    tweet_id = data.get("id")
                    return PublishResult(
                        success=True,
                        post_id=tweet_id,
                        url=f"https://x.com/i/web/status/{tweet_id}",
                        method="x_api",
                    )
                else:
                    return PublishResult(
                        success=False,
                        method="x_api",
                        error_message=f"X API error {res.status_code}: {res.text}",
                    )
        except Exception as e:
            return PublishResult(
                success=False,
                method="x_api",
                error_message=str(e),
            )
