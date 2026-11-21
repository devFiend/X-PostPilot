"""
Official X API v2 Publisher.
Publishes via authorized OAuth 1.0a User Context credentials to POST https://api.twitter.com/2/tweets.
Includes graceful fallback to manual publishing if API credits are exhausted or credentials fail.
"""

import hmac
import hashlib
import time
import secrets
import urllib.parse
from typing import Dict
import httpx
from postpilot.publishers.base import BasePublisher, PublishResult
from postpilot.utils.config import settings


class XPublisher(BasePublisher):
    """
    Publisher implementation for X (Twitter) API v2.
    Supports official OAuth 1.0a User Context authentication required for posting tweets.
    """

    def __init__(self):
        self.endpoint = "https://api.twitter.com/2/tweets"
        self.consumer_key = settings.X_API_KEY
        self.consumer_secret = settings.X_API_SECRET
        self.access_token = settings.X_ACCESS_TOKEN
        self.access_token_secret = settings.X_ACCESS_TOKEN_SECRET
        self.bearer_token = settings.X_ACCESS_TOKEN  # Fallback if bearer only

    def is_configured(self) -> bool:
        return bool(
            self.consumer_key and self.consumer_secret and self.access_token and self.access_token_secret
        ) or bool(self.bearer_token)

    def _generate_oauth1_header(self, method: str, url: str) -> str:
        """Generate standard RFC 5849 OAuth 1.0a Authorization Header."""
        oauth_params: Dict[str, str] = {
            "oauth_consumer_key": self.consumer_key or "",
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.access_token or "",
            "oauth_version": "1.0",
        }

        # Parameter string
        sorted_params = sorted(oauth_params.items())
        param_str = "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
            for k, v in sorted_params
        )

        # Signature base string
        base_string = "&".join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_str, safe='')
        ])

        # Signing key
        signing_key = f"{urllib.parse.quote(self.consumer_secret or '', safe='')}&{urllib.parse.quote(self.access_token_secret or '', safe='')}".encode("utf-8")
        signature = hmac.new(signing_key, base_string.encode("utf-8"), hashlib.sha1).digest()
        import base64
        oauth_params["oauth_signature"] = base64.b64encode(signature).decode("utf-8")

        # Build Authorization header string
        header_parts = [
            f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
            for k, v in sorted(oauth_params.items())
        ]
        return "OAuth " + ", ".join(header_parts)

    async def test_connection(self) -> bool:
        if not self.is_configured():
            return False

        try:
            url = "https://api.twitter.com/2/users/me"
            if self.consumer_key and self.access_token:
                auth_header = self._generate_oauth1_header("GET", url)
                headers = {"Authorization": auth_header}
            else:
                headers = {"Authorization": f"Bearer {self.bearer_token}"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=headers)
                return res.status_code == 200
        except Exception:
            return False

    async def publish(self, content: str) -> PublishResult:
        if not self.is_configured():
            return PublishResult(
                success=False,
                method="x_api",
                error_message="X credentials not configured in .env. Switch to manual mode or configure X OAuth tokens.",
            )

        try:
            if self.consumer_key and self.access_token:
                auth_header = self._generate_oauth1_header("POST", self.endpoint)
                headers = {
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                }
            else:
                headers = {
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json",
                }

            payload = {"text": content}

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
                elif res.status_code in (401, 403):
                    # Lack of pay-per-use credits, tier restriction, or permission error
                    return PublishResult(
                        success=False,
                        method="x_api",
                        error_message=(
                            f"X API Access Denied ({res.status_code}). Likely pay-per-use credit limit "
                            f"or insufficient OAuth scopes. Error: {res.text}. "
                            f"Falling back to manual publishing is recommended."
                        ),
                    )
                elif res.status_code == 429:
                    return PublishResult(
                        success=False,
                        method="x_api",
                        error_message="X API Rate Limit Exceeded (HTTP 429). Please wait before retrying.",
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
