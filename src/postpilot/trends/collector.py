"""
Real-time Trend Pulse Collector.
Pulls live breakout stories from Hacker News and X niche curators with zero paid APIs.
"""

import asyncio
from typing import List, Dict, Optional
import httpx
from postpilot.dna.collector import PublicTweetCollector

# Default niche curator accounts monitored for breaking announcements & tech debates
DEFAULT_TREND_CURATORS = [
    "therundownai",
    "rowancheung",
    "levelsio",
    "swyx",
    "techcrunch",
]


class TrendPulseCollector:
    def __init__(self):
        self.tweet_collector = PublicTweetCollector()

    async def fetch_hacker_news_top(self, limit: int = 15) -> List[Dict]:
        """
        Fetch top trending stories from official public Hacker News Firebase API.
        100% free, official, zero authentication required.
        """
        stories: List[Dict] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                if res.status_code != 200:
                    return stories

                top_ids = res.json()[:limit]

                async def fetch_item(item_id: int):
                    try:
                        r = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
                        if r.status_code == 200:
                            data = r.json()
                            if data and data.get("title"):
                                return {
                                    "title": data.get("title"),
                                    "source": "HackerNews",
                                    "url": data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                                    "score": data.get("score", 0),
                                    "by": data.get("by", "hn"),
                                }
                    except Exception:
                        pass
                    return None

                tasks = [fetch_item(iid) for iid in top_ids]
                results = await asyncio.gather(*tasks)
                for item in results:
                    if item:
                        stories.append(item)
        except Exception:
            pass

        return stories

    async def fetch_curator_trends(self, curators: Optional[List[str]] = None, limit_per_curator: int = 5) -> List[Dict]:
        """
        Scan breaking posts from top tech curators on X via ban-proof syndication.
        """
        target_curators = curators or DEFAULT_TREND_CURATORS
        items: List[Dict] = []

        for handle in target_curators[:3]:
            try:
                tweets = await self.tweet_collector.fetch_creator_tweets(handle, limit=limit_per_curator)
                for tw in tweets:
                    # Ignore short replies or trivial updates
                    if len(tw.get("text", "")) > 40:
                        items.append({
                            "title": tw["text"][:120] + ("..." if len(tw["text"]) > 120 else ""),
                            "source": f"X: @{handle}",
                            "url": f"https://x.com/{handle}",
                            "score": tw.get("likes", 100),
                            "text": tw["text"],
                        })
            except Exception:
                continue

        return items

    async def collect_all_candidates(self, curators: Optional[List[str]] = None) -> List[Dict]:
        """Collect and combine all live trend candidates across Hacker News and X curators."""
        hn_task = self.fetch_hacker_news_top(limit=15)
        x_task = self.fetch_curator_trends(curators=curators, limit_per_curator=4)

        hn_items, x_items = await asyncio.gather(hn_task, x_task)
        combined = hn_items + x_items

        # Sort by engagement/score descending
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        return combined
