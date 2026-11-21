"""
Content and Draft Application Services.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from postpilot.ai.router import AIRouter
from postpilot.database.repositories import DraftRepository
from postpilot.database.models import Draft, PostStatus


class ContentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DraftRepository(db)
        self.router = AIRouter()

    async def generate_drafts(
        self, topic: str, category: str = "educational", count: int = 3, provider: Optional[str] = None
    ) -> List[Draft]:
        system_prompt = (
            "You are PostPilot, an expert social media ghostwriter for X. "
            "Your output must be concise, punchy, and under 280 characters per post. "
            "Avoid generic buzzwords like 'game changer', 'dive deep', 'in today's world'. "
            "Write engaging hooks that stop the scroll."
        )
        user_prompt = f"Topic: {topic}\nCategory: {category}\nPlease write {count} distinct X posts."

        posts, used_provider = await self.router.generate_with_fallback(
            prompt=user_prompt, system_prompt=system_prompt, preferred=provider, count=count
        )

        saved_drafts = []
        for post_text in posts:
            clean_text = post_text.strip()
            # Enforce 280-char guardrail
            if len(clean_text) > 280:
                clean_text = clean_text[:277] + "..."
            draft = self.repo.create(
                content=clean_text,
                topic=topic,
                category=category,
                provider=used_provider,
                status=PostStatus.DRAFT.value,
            )
            saved_drafts.append(draft)

        return saved_drafts
