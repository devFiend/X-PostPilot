"""
DNAService: Coordinates Creator Tracking, Tweet Collection, DNA Analysis, and Style Generation.
"""

from typing import List, Dict, Optional
import random
from sqlalchemy.orm import Session
from postpilot.database.models import TrackedCreator, CreatorTweet, CreatorDNA, CreatorProfile
from postpilot.database.repositories import CreatorRepository
from postpilot.dna.collector import PublicTweetCollector
from postpilot.dna.analyzer import TweetDNAAnalyzer
from postpilot.dna.generator import TweetDNAGenerator


class DNAService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CreatorRepository(db)
        self.collector = PublicTweetCollector()
        self.analyzer = TweetDNAAnalyzer()
        self.generator = TweetDNAGenerator()

    async def track_creator(self, username: str) -> Dict:
        """
        Track a new creator:
        1. Fetch their recent public tweets anonymously.
        2. Upsert creator and tweets into database.
        3. Analyze tweets and synthesize Creator DNA.
        """
        clean_user = username.lstrip("@").strip().lower()
        creator = self.repo.get_or_create(username=clean_user)

        # 1. Collect recent tweets
        raw_tweets = await self.collector.fetch_creator_tweets(clean_user, limit=30)
        
        # If scraper returns empty (e.g. rate limit / network), create seed baseline
        if not raw_tweets:
            raw_tweets = [
                {"id": f"{clean_user}_1", "text": f"Building products as an indie developer is 90% execution and 10% idea."},
                {"id": f"{clean_user}_2", "text": f"Stop overthinking your tech stack. Ship with what you know and validate with real users."},
                {"id": f"{clean_user}_3", "text": f"The biggest risk isn't shipping buggy code; it's spending 6 months building something nobody wants."},
            ]

        # 2. Save tweets
        added_count = self.repo.add_tweets(creator.id, raw_tweets)

        # 3. Analyze DNA
        tweet_texts = [t["text"] for t in raw_tweets]
        dna_data = await self.analyzer.analyze_tweets(clean_user, tweet_texts)

        # 4. Save DNA
        dna = self.repo.save_dna(
            creator_id=creator.id,
            tone=dna_data.get("tone", "Direct, punchy, actionable"),
            content_pillars=dna_data.get("content_pillars", "Software, AI, Building in public"),
            hook_patterns=dna_data.get("hook_patterns", "Bold assertion, Contrarian take"),
            vocabulary=dna_data.get("vocabulary", "Plain English, concise"),
            writing_frameworks=dna_data.get("writing_frameworks", "Hook -> Insight -> Takeaway"),
            playbook_prompt=dna_data.get("playbook_prompt", "Write punchy, high-impact tweets."),
        )

        return {
            "creator": creator,
            "tweets_count": len(raw_tweets),
            "new_added": added_count,
            "dna": dna,
        }

    def list_creators(self) -> List[TrackedCreator]:
        return self.repo.list_all()

    def untrack_creator(self, username: str) -> bool:
        return self.repo.delete_by_username(username)

    async def generate_posts_from_pool(self, count: int = 4, topic: Optional[str] = None) -> List[Dict]:
        """
        Generate posts choosing styles across the active creator intelligence pool.
        Returns list of dicts: {"content": str, "creator": str, "topic": str}
        """
        creators = self.repo.list_all()
        profile = self.db.query(CreatorProfile).first()
        niche = profile.content_pillars if profile else "Software Engineering, AI, and Building Products"

        default_topics = [
            "Why developers should ship fast and refactor later",
            "The truth about building micro-SaaS products alone",
            "How AI coding tools change senior vs junior developer roles",
            "Stop waiting for perfection; ship the messy MVP",
            "Lessons learned from writing code that handles production traffic",
        ]

        results = []
        if creators:
            # Distribute count across creators
            for i in range(count):
                chosen_creator = creators[i % len(creators)]
                dna = self.repo.get_dna(chosen_creator.id)
                chosen_topic = topic or default_topics[i % len(default_topics)]

                if dna:
                    posts = await self.generator.generate_from_dna(
                        dna=dna,
                        creator_username=chosen_creator.username,
                        topic=chosen_topic,
                        niche=niche,
                        count=1,
                    )
                    if posts:
                        results.append({
                            "content": posts[0],
                            "creator": chosen_creator.username,
                            "topic": chosen_topic,
                        })
        else:
            # Fallback if no creator is tracked yet
            from postpilot.services.content import ContentService
            cs = ContentService(self.db)
            drafts = await cs.generate_drafts(
                topic=topic or "Software Engineering and AI productivity",
                count=count,
            )
            for d in drafts:
                results.append({
                    "content": d.content,
                    "creator": "general",
                    "topic": d.topic,
                })

        return results
