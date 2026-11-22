"""
TrendPulseService: Orchestrates live trend scanning, niche filtering, and dual-angle tweet drafting.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from postpilot.database.models import CreatorProfile, Draft, PostStatus
from postpilot.database.repositories import TrendRepository, DraftRepository
from postpilot.trends.collector import TrendPulseCollector
from postpilot.trends.analyzer import TrendPulseAnalyzer
from postpilot.trends.generator import TrendTweetGenerator
from postpilot.utils.config import settings


class TrendPulseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TrendRepository(db)
        self.draft_repo = DraftRepository(db)
        self.collector = TrendPulseCollector()
        self.analyzer = TrendPulseAnalyzer()
        self.generator = TrendTweetGenerator()

    async def get_niche(self) -> str:
        profile = self.db.query(CreatorProfile).first()
        return profile.content_pillars if profile else "Software Engineering, AI, and Building Products"

    async def scan_live_trends(self, limit: int = 3) -> List[Dict]:
        """
        Scan Hacker News and X curators, filter by user's niche,
        and generate 2 distinct tweet takes for each breakout story.
        """
        niche = await self.get_niche()

        # 1. Collect candidates
        candidates = await self.collector.collect_all_candidates()
        if not candidates:
            return []

        # 2. Filter by niche
        niche_candidates = self.analyzer.filter_niche_trends(candidates, niche=niche)

        results = []
        for cand in niche_candidates:
            if len(results) >= limit:
                break

            title = cand.get("title", "")
            # Check if this exact story was analyzed in past 48 hours
            is_recent = self.repo.is_recently_tracked(title)

            # Store in database if new
            story = None
            if not is_recent:
                story = self.repo.add_story(
                    title=title,
                    source=cand.get("source", "Web"),
                    external_url=cand.get("url"),
                    score=cand.get("score", 0),
                    category="Niche Trend",
                )

            # 3. Analyze context
            context = await self.analyzer.analyze_trend_context(cand, niche=niche)

            # 4. Generate takes
            takes = await self.generator.generate_trend_takes(context, niche=niche)

            results.append({
                "story_id": story.id if story else None,
                "headline": title,
                "source": cand.get("source", "HackerNews"),
                "url": cand.get("url", ""),
                "score": cand.get("score", 0),
                "topic": context.get("topic", title[:40]),
                "summary": context.get("summary", ""),
                "debate": context.get("debate", ""),
                "takes": takes,
            })

        return results

    async def draft_trend_take(self, content: str, topic: str) -> Draft:
        """Save a selected trend take as an approved or pending draft in SQLite."""
        return self.draft_repo.create(
            content=content,
            topic=f"Trend: {topic}",
            category="niche_trend",
            provider=settings.DEFAULT_AI_PROVIDER,
            status=PostStatus.PENDING_APPROVAL.value,
        )
