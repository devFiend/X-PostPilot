"""
Trend Pulse Analyzer.
Filters raw candidate stories against the user's content pillars and extracts viral tweet angles.
"""

from typing import List, Dict, Optional
import re
from postpilot.ai.router import AIRouter

DEFAULT_NICHE_KEYWORDS = [
    "ai", "llm", "model", "agent", "software", "developer", "code", "coding", "python",
    "javascript", "typescript", "saas", "startup", "build", "cloud", "database", "api",
    "engineer", "open source", "github", "tech", "indie", "product", "gpu", "cursor",
    "claude", "gpt", "openai", "deepseek", "anthropic", "gemini", "llama", "framework",
    "compiler", "rust", "linux", "backend", "frontend", "server", "infra", "app"
]


class TrendPulseAnalyzer:
    def __init__(self):
        self.router = AIRouter()

    def matches_niche(self, text: str, niche: str = "") -> bool:
        """Determines if a trend headline matches user's tech / software / AI niche."""
        lower = text.lower()
        # Custom niche words
        if niche:
            custom_words = [w.strip().lower() for w in re.split(r"[,/|;]+", niche) if len(w.strip()) > 2]
            if any(cw in lower for cw in custom_words):
                return True

        # Check default tech keywords with flexible pluralization/suffixes
        return any(re.search(rf"\b{kw}(?:s|ed|ing|ers)?\b", lower) for kw in DEFAULT_NICHE_KEYWORDS)

    def filter_niche_trends(self, candidates: List[Dict], niche: str = "") -> List[Dict]:
        """Filters out non-tech / irrelevant stories and keeps top-ranked niche items."""
        filtered = []
        for c in candidates:
            title = c.get("title", "")
            if self.matches_niche(title, niche):
                filtered.append(c)

        # Fallback to candidates if filter was overly restrictive
        return filtered if filtered else candidates[:5]

    async def analyze_trend_context(self, item: Dict, niche: str = "Software Engineering & AI") -> Dict:
        """
        Uses AI to extract the core angle and debate of the trending topic.
        """
        headline = item.get("title", "")
        source = item.get("source", "Web")

        system_prompt = (
            "You are an elite tech news editor and viral social media strategist on X (Twitter).\n"
            "Analyze the given trending tech headline and extract:\n"
            "1. Core Topic (3-6 words)\n"
            "2. What Happened (1 concise sentence)\n"
            "3. The Debate / Controversy / Big Insight (1 sentence explaining why developers or tech founders care)\n\n"
            "Format your answer as:\n"
            "TOPIC: <topic>\n"
            "SUMMARY: <summary>\n"
            "DEBATE: <debate>"
        )

        user_prompt = f"Trending Headline from {source}:\n\"{headline}\"\nNiche: {niche}"

        responses, _ = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
        )

        res_text = responses[0] if responses else ""
        topic_match = re.search(r"TOPIC:\s*(.+)", res_text)
        summary_match = re.search(r"SUMMARY:\s*(.+)", res_text)
        debate_match = re.search(r"DEBATE:\s*(.+)", res_text)

        return {
            "title": headline,
            "source": source,
            "url": item.get("url", ""),
            "score": item.get("score", 0),
            "topic": topic_match.group(1).strip() if topic_match else headline[:50],
            "summary": summary_match.group(1).strip() if summary_match else headline,
            "debate": debate_match.group(1).strip() if debate_match else "Why this matters for builders.",
        }
