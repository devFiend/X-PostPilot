"""
TweetDNA Post Generation Engine.
Assembles Creator DNA + User Profile/Niche to generate original, high-impact posts.
Never verbatim copies.
"""

from typing import List, Optional
from postpilot.ai.router import AIRouter
from postpilot.database.models import CreatorDNA


class TweetDNAGenerator:
    def __init__(self):
        self.router = AIRouter()

    async def generate_from_dna(
        self,
        dna: CreatorDNA,
        creator_username: str,
        topic: str,
        niche: str = "Software Engineering, AI, and Building Products",
        count: int = 1,
    ) -> List[str]:
        """
        Generate fresh, original X posts applying a creator's DNA to the user's topic and niche.
        """
        system_prompt = (
            f"You are PostPilot powered by TweetDNA intelligence.\n"
            f"You write high-impact X posts in the style of @{creator_username}.\n\n"
            f"Creator DNA Playbook:\n"
            f"• Tone: {dna.tone}\n"
            f"• Hook Patterns: {dna.hook_patterns}\n"
            f"• Vocabulary & Style: {dna.vocabulary}\n"
            f"• Writing Frameworks: {dna.writing_frameworks}\n\n"
            f"Guidelines:\n"
            f"{dna.playbook_prompt}\n\n"
            f"Rules:\n"
            f"1. Generate completely original posts. Never copy existing tweets.\n"
            f"2. Every post must be STRICTLY under 280 characters.\n"
            f"3. No generic corporate hashtags or AI buzzwords like 'game changer', 'dive deep', 'in today's world'.\n"
            f"4. Separate multiple posts with '---'."
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Niche/Context: {niche}\n"
            f"Please write {count} distinct X posts applying @{creator_username}'s hook and writing style."
        )

        posts, used_provider = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=count,
        )

        validated_posts = []
        for p in posts:
            clean = p.strip()
            if len(clean) > 280:
                clean = clean[:277] + "..."
            if clean:
                validated_posts.append(clean)

        return validated_posts[:count]
