"""
TweetDNA Post Generation & Sentence Rephrasing Engine.
Adapts real creator tweets and DNA frameworks to generate high-impact, authentic X posts.
Eliminates corporate fluff and produces real, tweet-like rhythms with varied angles and lively emojis.
"""

from typing import List, Optional
from postpilot.ai.router import AIRouter
from postpilot.database.models import CreatorDNA


class TweetDNAGenerator:
    def __init__(self):
        self.router = AIRouter()

    async def generate_rephrased_tweet(
        self,
        source_tweet: str,
        creator_username: str,
        dna: Optional[CreatorDNA] = None,
        niche: str = "Software Engineering, AI, and Building Products",
    ) -> Optional[str]:
        """
        Takes an actual high-performing tweet from a tracked creator and remixes its core lesson
        with fresh angles, varied hooks, lively emojis, and cadence tailored for the user's niche.
        Produces authentic, raw, human-sounding tweets rather than mechanical word swaps.
        """
        tone_str = dna.tone if dna else "Direct, punchy, contrarian, conversational"
        system_prompt = (
            f"You are an elite ghostwriter for top tech founders and creators on X (Twitter).\n"
            f"Your job is to take an actual tweet from @{creator_username} and extract its core insight, "
            f"then rewrite it from a fresh, original angle tailored for the niche: {niche}.\n\n"
            f"Creator Voice & Tone: {tone_str}\n\n"
            f"STRICT TWEET-LIKE QUALITY RULES:\n"
            f"1. Must sound 100% like a REAL human creator on X: bold, casual, punchy, insightful.\n"
            f"2. AVOID MECHANICAL PARAPHRASING: Do not just swap synonyms into the same sentence template. "
            f"Reinvent the hook, angle, and framing so it feels like a genuine, original tweet inspired by the lesson.\n"
            f"3. INJECT LIFE WITH EMOJIS: Use 1 or 2 relevant emojis naturally (e.g. 🔥, 💡, ⚡, 🛠️, 🎯, 👀) "
            f"to give visual energy and punch to the hook or key takeaway.\n"
            f"4. ZERO corporate marketing jargon: NEVER use words like 'dive deep', 'game changer', 'supercharge', "
            f"'in today's world', 'crucial', 'paradigm shift', 'elevate'.\n"
            f"5. ZERO hashtag spam: High-status creators rarely use hashtags.\n"
            f"6. Natural formatting: 1 to 3 short sentences or concise line breaks. Total length MUST be strictly under 280 characters.\n"
            f"7. Output ONLY the final tweet text. No quotes, no intro, no explanation."
        )

        user_prompt = (
            f"Original Tweet from @{creator_username}:\n"
            f"\"{source_tweet}\"\n\n"
            f"Reinvent this tweet for the niche '{niche}'. "
            f"Take the core lesson and write a fresh, engaging tweet with lively phrasing and an energetic hook."
        )

        posts, _ = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
            temperature=0.88,
        )

        if not posts:
            return None

        clean = posts[0].strip().strip('"').strip("'")
        if len(clean) > 280:
            clean = clean[:277] + "..."
        return clean if clean else None

    async def generate_from_dna(
        self,
        dna: CreatorDNA,
        creator_username: str,
        topic: str,
        niche: str = "Software Engineering, AI, and Building Products",
        count: int = 1,
        sample_tweets: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Generate fresh, original X posts applying a creator's DNA + sample tweets to a topic and niche.
        """
        sample_section = ""
        if sample_tweets:
            formatted_samples = "\n".join([f'- "{t}"' for t in sample_tweets[:3]])
            sample_section = f"\n\nReal Example Tweets from @{creator_username}:\n{formatted_samples}\n"

        system_prompt = (
            f"You are PostPilot powered by TweetDNA intelligence.\n"
            f"You write high-impact, authentic X posts matching the exact voice of @{creator_username}.\n\n"
            f"Creator DNA:\n"
            f"• Tone: {dna.tone}\n"
            f"• Hook Patterns: {dna.hook_patterns}\n"
            f"• Style & Vocabulary: {dna.vocabulary}\n"
            f"• Writing Frameworks: {dna.writing_frameworks}\n"
            f"{sample_section}\n"
            f"STRICT RULES:\n"
            f"1. Make posts sound like real viral tweets: punchy, authentic, raw, direct.\n"
            f"2. Every post must be STRICTLY under 280 characters.\n"
            f"3. Inject life: use 1 or 2 purposeful emojis naturally where they add pop to the hook.\n"
            f"4. Vary sentence length and structure across variants.\n"
            f"5. No generic corporate hashtags or AI buzzwords like 'game changer', 'dive deep', 'in today's fast-paced world'.\n"
            f"6. Separate multiple posts with '---'."
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Niche/Context: {niche}\n"
            f"Write {count} distinct, authentic X posts with varied angles following @{creator_username}'s cadence."
        )

        posts, used_provider = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=count,
            temperature=0.88,
        )

        validated_posts = []
        for p in posts:
            clean = p.strip().strip('"').strip("'")
            if len(clean) > 280:
                clean = clean[:277] + "..."
            if clean:
                validated_posts.append(clean)

        return validated_posts[:count]
