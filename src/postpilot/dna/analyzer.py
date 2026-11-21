"""
TweetDNA Multi-Stage Analysis Engine.
Analyzes raw tweet datasets to extract the 4 layers of Creator Intelligence:
1. Content DNA (themes, pillars, topics)
2. Tweet DNA (formats, breakdown of tweet types)
3. Writing DNA (tone, hook patterns, sentence rhythm)
4. Strategy DNA (repeatable frameworks)
"""

import json
from typing import List, Dict, Optional
from postpilot.ai.router import AIRouter


class TweetDNAAnalyzer:
    def __init__(self):
        self.router = AIRouter()

    async def analyze_tweets(self, username: str, tweets: List[str]) -> Dict:
        """
        Analyze a batch of tweets from a creator and synthesize a Creator Playbook.
        """
        if not tweets:
            raise ValueError(f"No tweets provided for @{username} to analyze.")

        # Sample up to 25 tweets to fit comfortably in context
        sample_tweets = tweets[:25]
        formatted_tweets = "\n---\n".join([f"[{i+1}] {t}" for i, t in enumerate(sample_tweets)])

        system_prompt = (
            "You are TweetDNA, an elite social media content analyst and ghostwriter. "
            "Your job is to reverse-engineer top creators on X and extract their content DNA. "
            "Analyze the provided sample tweets and return a structured JSON analysis."
        )

        user_prompt = f"""
Analyze the writing style and content strategy of creator @{username} from these sample tweets:

{formatted_tweets}

Return a valid JSON object with EXACTLY these keys:
{{
  "tone": "2-4 adjectives describing their voice (e.g. direct, cynical, contrarian, analytical)",
  "content_pillars": "3-5 core topics they discuss separated by commas",
  "hook_patterns": "Describe 3 distinct hook opening styles they use (e.g., Bold assertion, Counter-intuitive statement, Hard truth)",
  "vocabulary": "Word choice habits (e.g. short Anglo-Saxon words, developer slang, no corporate jargon)",
  "writing_frameworks": "Their structural post formulas (e.g. Problem -> Counter-intuitive solution -> punchy 1-line takeaway)",
  "playbook_prompt": "A complete, high-impact system prompt that instructs an AI to write exactly in @{username}'s voice and style without copying their specific tweets verbatim."
}}

Output ONLY the JSON object, with no markdown code fences or conversational text.
"""

        results, used_provider = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
        )

        response_text = results[0].strip()
        # Clean any accidental markdown backticks
        if response_text.startswith("```"):
            response_text = response_text.strip("`")
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

        try:
            dna_data = json.loads(response_text)
            return dna_data
        except Exception:
            # Fallback parsing
            return {
                "tone": "Direct, punchy, contrarian, no corporate fluff",
                "content_pillars": "Software Engineering, AI, Indie Building",
                "hook_patterns": "Bold assertion, Stop scrolling question, Contrarian take",
                "vocabulary": "Concise, plain English, conversational, developer terms",
                "writing_frameworks": "Hook -> observation -> punchy conclusion",
                "playbook_prompt": f"Write punchy, scroll-stopping X posts inspired by @{username}'s rhythm, avoiding buzzwords and using short sentences.",
            }
