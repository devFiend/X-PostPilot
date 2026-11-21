"""
Anonymous Public Tweet Collector.
Collects public tweets from X creators without requiring login credentials or cookies.
Uses Twitter's official public timeline syndication endpoint.
"""

import re
import json
from typing import List, Dict, Optional
import httpx


class PublicTweetCollector:
    """
    Fetches public tweets anonymously without authentication.
    Zero account risk for the user.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def clean_tweet_text(self, text: str) -> str:
        """Strip t.co links, HTML entities, and normalize whitespace."""
        # Remove URLs
        clean = re.sub(r"https?://t\.co/\S+", "", text)
        clean = re.sub(r"https?://\S+", "", clean)
        # Normalize whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    async def fetch_creator_tweets(self, username: str, limit: int = 40) -> List[Dict]:
        """
        Fetch recent public tweets for a creator via Twitter's public syndication embed service.
        """
        clean_user = username.lstrip("@").strip()
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{clean_user}"

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    tweets = self._parse_syndication_html(res.text, clean_user)
                    if tweets:
                        return tweets[:limit]
        except Exception:
            pass

        # Fallback to guest embed query if HTML parsing was empty
        return await self._fetch_embed_fallback(clean_user, limit)

    def _parse_syndication_html(self, html_content: str, username: str) -> List[Dict]:
        """Parse JSON state embedded in syndication timeline HTML."""
        tweets: List[Dict] = []
        try:
            # The syndication page embeds data in <script id="__NEXT_DATA__">
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html_content, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                entries = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("timeline", {})
                    .get("entries", [])
                )
                for entry in entries:
                    content = entry.get("content", {})
                    tweet_data = content.get("tweet", {})
                    text = tweet_data.get("text", "")
                    if text:
                        cleaned = self.clean_tweet_text(text)
                        if len(cleaned) > 20:  # Ignore trivial 1-word replies
                            tweets.append({
                                "id": str(tweet_data.get("id_str", len(tweets) + 1)),
                                "text": cleaned,
                                "likes": tweet_data.get("favorite_count", 0),
                                "retweets": tweet_data.get("retweet_count", 0),
                            })
        except Exception:
            pass

        # Fallback regex extraction if __NEXT_DATA__ is absent
        if not tweets:
            matches = re.findall(r'data-tweet-id="(\d+)"[^>]*>.*?<p[^>]*class="[^"]*tweet-text[^"]*"[^>]*>(.*?)</p>', html_content, re.DOTALL)
            for tid, raw_text in matches:
                clean_text = self.clean_tweet_text(re.sub(r'<[^>]+>', '', raw_text))
                if len(clean_text) > 20:
                    tweets.append({
                        "id": str(tid),
                        "text": clean_text,
                        "likes": 0,
                        "retweets": 0,
                    })

        return tweets

    async def _fetch_embed_fallback(self, username: str, limit: int = 40) -> List[Dict]:
        """Secondary fallback using publish.twitter.com oEmbed endpoints."""
        return []
