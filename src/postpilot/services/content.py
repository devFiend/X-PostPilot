"""
Content and Draft Application Services.
Provides diverse, human-sounding tweet generation with archetype rotation,
tasteful emoji injection, deduplication against recent history, and anti-repetition guardrails.
"""

import random
from typing import List, Optional
from sqlalchemy.orm import Session
from postpilot.ai.router import AIRouter
from postpilot.database.repositories import DraftRepository
from postpilot.database.models import Draft, PostStatus


TWEET_ARCHETYPES = [
    {
        "name": "🔥 Contrarian / Hard Truth",
        "instruction": "Present an uncomfortable industry truth or challenge popular conventional wisdom. Start with a bold, punchy claim that stops the scroll.",
    },
    {
        "name": "⚡ Minimalist Punch",
        "instruction": "Ultra-concise, razor-sharp observation (under 140 characters). Zero filler, zero fluff. Make every single word carry weight.",
    },
    {
        "name": "🛠️ Builder Lesson / Trench Story",
        "instruction": "Share a realistic practitioner takeaway or lesson from shipping real software. Practical, grounded in reality, relatable to builders.",
    },
    {
        "name": "💡 Actionable Rule of Thumb",
        "instruction": "Offer a practical heuristic, mental model, or 'do X instead of Y' insight that developers or founders can use immediately.",
    },
    {
        "name": "💬 Conversational Spark",
        "instruction": "State an intriguing technical observation or dilemma and end with an open, thought-provoking question that compels replies.",
    },
]


class ContentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DraftRepository(db)
        self.router = AIRouter()

    async def generate_drafts(
        self,
        topic: str,
        category: str = "educational",
        count: int = 3,
        provider: Optional[str] = None,
        archetype: Optional[str] = None,
        temperature: float = 0.88,
    ) -> List[Draft]:
        # 1. Select archetype instruction
        if archetype:
            selected_archetype = next((a for a in TWEET_ARCHETYPES if archetype.lower() in a["name"].lower()), None)
            archetype_instruction = f"{selected_archetype['name']}: {selected_archetype['instruction']}" if selected_archetype else archetype
        else:
            chosen = random.choice(TWEET_ARCHETYPES)
            archetype_instruction = f"{chosen['name']}: {chosen['instruction']}"

        # 2. Fetch recent post contents to prevent repetitive phrases and ideas
        recent_posts = self.repo.get_recent_contents(limit=8)
        negative_history = ""
        if recent_posts:
            samples = "\n".join([f'- "{p[:120]}..."' if len(p) > 120 else f'- "{p}"' for p in recent_posts[:6]])
            negative_history = (
                f"\n\nDO NOT REPEAT OR MIMIC RECENT POSTS:\n"
                f"The user has already recently posted these ideas or structures:\n{samples}\n"
                f"Use a COMPLETELY DIFFERENT hook, metaphor, and angle. Do not use the same formula."
            )

        system_prompt = (
            "You are PostPilot, an elite tech ghostwriter on X (Twitter).\n"
            "You craft authentic, high-impact tweets with varied cadence, rhythm, and perspective.\n\n"
            "STRICT QUALITY & DIVERSITY RULES:\n"
            "1. VARY THE FORMAT: Never repeat the same syntactic template (e.g. don't always do 'Question? Answer. Lesson.').\n"
            "2. INJECT LIFE WITH EMOJIS: Use 1 to 3 relevant emojis naturally to inject energy, emotion, and visual pop "
            "(e.g. 🔥, 💡, ⚡, 🛠️, 🚨, 🎯, 🚀, 👀). Place them where they accentuate the hook or key punchline, not as mindless clutter.\n"
            "3. ZERO CORPORATE BUZZWORDS: Ban words like 'dive deep', 'game changer', 'supercharge', 'in today's world', 'paradigm shift'.\n"
            "4. NO HASHTAG SPAM: At most 0 or 1 natural hashtag only if essential. High-signal creators rarely spam tags.\n"
            "5. STRICT 280-CHAR LIMIT: Every individual post must be strictly under 280 characters.\n"
            f"6. TARGET ANGLE: {archetype_instruction}\n"
            f"{negative_history}"
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Category: {category}\n"
            f"Please generate {count} distinct, creative X posts with completely different hooks and perspectives."
        )

        posts, used_provider = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            preferred=provider,
            count=count,
            temperature=temperature,
        )

        saved_drafts = []
        for post_text in posts:
            clean_text = post_text.strip().strip('"').strip("'")
            # Enforce 280-char guardrail
            if len(clean_text) > 280:
                clean_text = clean_text[:277] + "..."

            if not clean_text:
                continue

            # Check deduplication against recent drafts in the database
            if self.repo.is_duplicate(clean_text, threshold=0.60):
                continue

            draft = self.repo.create(
                content=clean_text,
                topic=topic,
                category=category,
                provider=used_provider,
                status=PostStatus.DRAFT.value,
            )
            saved_drafts.append(draft)

        # Fallback if all were flagged duplicate
        if not saved_drafts and posts:
            fallback_text = posts[0].strip().strip('"').strip("'")
            if len(fallback_text) > 280:
                fallback_text = fallback_text[:277] + "..."
            draft = self.repo.create(
                content=fallback_text,
                topic=topic,
                category=category,
                provider=used_provider,
                status=PostStatus.DRAFT.value,
            )
            saved_drafts.append(draft)

        return saved_drafts
