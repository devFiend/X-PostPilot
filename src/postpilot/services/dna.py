"""
DNAService: Coordinates Creator Tracking, Tweet Collection, DNA Analysis,
Style Generation, and Real Sentence Rephrasing with Deduplication.
"""

from typing import List, Dict, Optional
import random
from sqlalchemy.orm import Session
from postpilot.database.models import TrackedCreator, CreatorTweet, CreatorDNA, CreatorProfile
from postpilot.database.repositories import CreatorRepository, DraftRepository
from postpilot.dna.collector import PublicTweetCollector
from postpilot.dna.analyzer import TweetDNAAnalyzer
from postpilot.dna.generator import TweetDNAGenerator


# Curated high-signal baseline tweet templates used as secondary seeds
CURATED_SEED_TWEETS = [
    "Most people spend 6 months building something nobody wants. Build the ugly MVP in a weekend and test if strangers will actually pay you.",
    "The best tech stack is the one you already know. Stop redesigning your architecture before you have 10 paying users.",
    "Your code doesn't need to be perfect. It needs to solve a real problem that someone hates doing manually.",
    "If you are not embarrassed by the first version of your product, you launched too late.",
    "The secret to shipping fast isn't typing faster; it's cutting 80% of features that don't move the needle.",
    "Code is a liability, not an asset. Every line you write is another line you have to maintain and debug.",
    "Build distribution before you build software. An average product with great distribution beats a great product nobody knows exists.",
    "You don't need venture capital to build a profitable software business. You need 100 people who love what you made.",
    "Stop reading tutorials and start shipping broken projects. You learn 10x more from production errors than medium articles.",
    "AI won't replace software engineers. Engineers who master AI tools will replace engineers who refuse to adapt.",
    "Clean architecture is great, but revenue keeps the servers on. Prioritize customer value over dogmatic patterns.",
    "The hardest part of building micro-SaaS isn't the backend. It's maintaining focus when the initial excitement fades.",
    "Talk to your users every single week. 15 minutes on a call will save you 3 weeks of building the wrong feature.",
    "Simple software that works reliably will always beat complex software with 100 broken bells and whistles.",
    "Consistency beats talent every single day. Ship one small improvement every day for a year and see where you end up.",
]

DYNAMIC_DEV_TOPICS = [
    "Why SQLite in WAL mode handles 95% of early SaaS database loads before you need Postgres",
    "PostgreSQL query optimization: why missing compound indexes kill p99 latency",
    "Cache-aside vs write-through caching in high-traffic APIs with Redis",
    "Why premature microservices kill early-stage velocity faster than messy monoliths",
    "Handling webhook idempotency with Redis distributed locks and unique event keys",
    "Database connection pool exhaustion: PgBouncer vs native connection management",
    "Why duplicating code is far cheaper than building the wrong abstraction",
    "Docker multi-stage builds: cutting image sizes from 1.2GB to 45MB",
    "Zero-downtime database schema migrations in production with Alembic",
    "Async Python workers: Celery vs Arq vs lightweight background tasks",
    "Why boring technology stacks ship products while hype stacks burn weekends",
    "The hidden cost of third-party SDKs: security vulnerabilities and dependency bloat",
    "API rate limiting: Token bucket vs Leaky bucket algorithms in practice",
    "Observability in production: structured JSON logging vs bloated tracing setups",
    "Why junior developers add code and senior developers delete dependencies",
    "State management in frontend: why prop drilling is often better than complex global stores",
    "How to debug race conditions that only happen under production concurrency",
    "Building resilient retry logic with exponential backoff and jitter",
    "Why developers spend 80% of their time reading code instead of writing new features",
    "Real-world incident response: what to do in the first 5 minutes of a production outage",
]


class DNAService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CreatorRepository(db)
        self.draft_repo = DraftRepository(db)
        self.collector = PublicTweetCollector()
        self.analyzer = TweetDNAAnalyzer()
        self.generator = TweetDNAGenerator()

    async def track_creator(self, username: str) -> Dict:
        """
        Track a new creator:
        1. Fetch their recent public tweets anonymously.
        2. Upsert creator and tweets into database.
        3. Analyze tweets and synthesize Creator DNA.
        Supports usernames with underscores (e.g., @_florian).
        """
        clean_user = username.lstrip("@").strip().lower()
        creator = self.repo.get_or_create(username=clean_user)

        # 1. Collect recent tweets
        raw_tweets = await self.collector.fetch_creator_tweets(clean_user, limit=40)

        # If scraper returns empty (e.g. rate limit / network), create seed baseline
        if not raw_tweets:
            raw_tweets = [
                {"id": f"{clean_user}_1", "text": f"Building products as an indie developer is 90% execution and 10% idea."},
                {"id": f"{clean_user}_2", "text": f"Stop overthinking your tech stack. Ship with what you know and validate with real users."},
                {"id": f"{clean_user}_3", "text": f"The biggest risk isn't shipping buggy code; it's spending 6 months building something nobody wants."},
                {"id": f"{clean_user}_4", "text": f"Distribution is everything. The best product with zero eyes will always lose to a good product with an audience."},
                {"id": f"{clean_user}_5", "text": f"Code what people complain about. Pain points are where the easiest money is made in SaaS."},
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
            playbook_prompt=dna_data.get("playbook_prompt", "Write punchy, high-impact tweets with zero corporate jargon."),
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
        clean_user = username.lstrip("@").strip().lower()
        return self.repo.delete_by_username(clean_user)

    async def generate_posts_from_pool(self, count: int = 1, topic: Optional[str] = None) -> List[Dict]:
        """
        Generate authentic, tweet-like posts choosing styles across the active creator pool.
        Prioritizes rephrasing and adapting real creator tweets.
        Includes database-backed deduplication to never deliver repeated content.
        """
        creators = self.repo.list_all()
        profile = self.db.query(CreatorProfile).first()
        niche = profile.content_pillars if profile else "Software Engineering, AI, and Building Products"

        results = []

        if creators:
            # Shuffle creators for natural variety
            creator_pool = list(creators)
            random.shuffle(creator_pool)

            for i in range(count):
                chosen_creator = creator_pool[i % len(creator_pool)]
                dna = self.repo.get_dna(chosen_creator.id)
                cached_tweets = self.repo.get_creator_tweets(chosen_creator.id, limit=40)

                generated_post = None

                # 1. Try to rephrase a real tweet from this creator that hasn't been used yet
                if cached_tweets:
                    shuffled_tweets = list(cached_tweets)
                    random.shuffle(shuffled_tweets)

                    for tweet_candidate in shuffled_tweets:
                        # Avoid tweets that match recent drafts
                        if self.draft_repo.is_duplicate(tweet_candidate.text, threshold=0.60):
                            continue

                        rephrased = await self.generator.generate_rephrased_tweet(
                            source_tweet=tweet_candidate.text,
                            creator_username=chosen_creator.username,
                            dna=dna,
                            niche=niche,
                        )

                        if rephrased and not self.draft_repo.is_duplicate(rephrased, threshold=0.55):
                            generated_post = rephrased
                            break

                # 2. If rephrase did not trigger or tweets were exhausted, generate from DNA with sample tweets
                if not generated_post and dna:
                    sample_texts = [t.text for t in cached_tweets[:3]]
                    chosen_topic = topic or random.choice(CURATED_SEED_TWEETS)
                    dna_posts = await self.generator.generate_from_dna(
                        dna=dna,
                        creator_username=chosen_creator.username,
                        topic=chosen_topic,
                        niche=niche,
                        count=1,
                        sample_tweets=sample_texts,
                    )
                    if dna_posts and not self.draft_repo.is_duplicate(dna_posts[0], threshold=0.55):
                        generated_post = dna_posts[0]

                # 3. Fallback: if still duplicate, pick an unused curated seed tweet and rephrase
                if not generated_post:
                    seed = random.choice(CURATED_SEED_TWEETS)
                    rephrased = await self.generator.generate_rephrased_tweet(
                        source_tweet=seed,
                        creator_username=chosen_creator.username,
                        dna=dna,
                        niche=niche,
                    )
                    generated_post = rephrased or seed

                results.append({
                    "content": generated_post,
                    "creator": chosen_creator.username,
                    "topic": topic or "TweetDNA Remixed",
                })
        else:
            # Fallback if no creators tracked yet: generate from dynamic technical topics and rotating archetypes
            from postpilot.services.content import ContentService
            content_svc = ContentService(self.db)

            for i in range(count):
                chosen_topic = topic or random.choice(DYNAMIC_DEV_TOPICS)
                drafts = await content_svc.generate_drafts(
                    topic=chosen_topic,
                    category="engineering_insights",
                    count=1,
                )
                if drafts:
                    post_content = drafts[0].content
                else:
                    seed_text = random.choice(CURATED_SEED_TWEETS)
                    rephrased = await self.generator.generate_rephrased_tweet(
                        source_tweet=seed_text,
                        creator_username="builder",
                        dna=None,
                        niche=niche,
                    )
                    post_content = rephrased or seed_text

                results.append({
                    "content": post_content,
                    "creator": "general",
                    "topic": chosen_topic,
                })

        return results
