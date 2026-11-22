"""
Trend Tweet Generator.
Transforms analyzed breaking trends into high-impact, viral X posts with distinct angles:
Take 1: Contrarian / Hot-Take
Take 2: Practical Builder Breakdown
"""

from typing import List, Dict, Optional
from postpilot.ai.router import AIRouter


class TrendTweetGenerator:
    def __init__(self):
        self.router = AIRouter()

    async def generate_trend_takes(
        self,
        trend_context: Dict,
        niche: str = "Software Engineering, AI, and Building Products",
    ) -> List[Dict]:
        """
        Generates 2 high-impact tweet options with distinct angles:
        - Take 1: Contrarian / Hot-Take (Challenges hype, offers bold perspective)
        - Take 2: Practical Builder Takeaway (What software developers / founders should actually do)
        """
        topic = trend_context.get("topic", "")
        summary = trend_context.get("summary", "")
        debate = trend_context.get("debate", "")

        system_prompt = (
            "You are an elite tech ghostwriter on X (Twitter).\n"
            "You write authentic, punchy, high-engagement tweets riding breaking tech news.\n\n"
            "STRICT QUALITY RULES:\n"
            "1. Must sound 100% like a REAL human creator: bold, conversational, high-signal.\n"
            "2. NO corporate marketing fluff: NO 'In today's fast-paced world', NO 'game changer', "
            "NO 'dive deep', NO 'supercharge', NO 'paradigm shift'.\n"
            "3. ZERO hashtags: Top tech founders rarely use hashtags.\n"
            "4. Every tweet must be STRICTLY under 280 characters.\n"
            "5. Provide two completely different takes:\n"
            "TAKE_1: (Contrarian / Hot-Take — bold assertion challenging conventional wisdom)\n"
            "TAKE_2: (Builder Breakdown — practical implication for engineers and founders)"
        )

        user_prompt = (
            f"Breaking Topic: {topic}\n"
            f"What Happened: {summary}\n"
            f"The Debate: {debate}\n"
            f"Niche/Audience: {niche}\n\n"
            "Write TAKE_1 and TAKE_2 now."
        )

        responses, _ = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
        )

        raw = responses[0] if responses else ""
        take_1 = ""
        take_2 = ""

        lines = raw.split("\n")
        current_take = None
        t1_lines, t2_lines = [], []

        for line in lines:
            if "TAKE_1:" in line:
                current_take = 1
                t1_lines.append(line.replace("TAKE_1:", "").strip())
            elif "TAKE_2:" in line:
                current_take = 2
                t2_lines.append(line.replace("TAKE_2:", "").strip())
            elif current_take == 1:
                t1_lines.append(line)
            elif current_take == 2:
                t2_lines.append(line)

        take_1 = "\n".join(t1_lines).strip().strip('"')
        take_2 = "\n".join(t2_lines).strip().strip('"')

        # Fallback if delimiter parsing failed
        if not take_1 and not take_2 and raw:
            parts = [p.strip() for p in raw.split("---") if p.strip()]
            if len(parts) >= 2:
                take_1, take_2 = parts[0], parts[1]
            else:
                take_1 = raw.strip()
                take_2 = f"Everyone is talking about {topic}. The real lesson for builders: focus on solving user pain, not riding headlines."

        def clean_tweet(text: str) -> str:
            clean = text.strip().strip('"').strip("'")
            if len(clean) > 280:
                clean = clean[:277] + "..."
            return clean

        take_1_clean = clean_tweet(take_1 or f"The hype around {topic} is missing the real point. Execution beats new tools every single time.")
        take_2_clean = clean_tweet(take_2 or f"How to actually use {topic} as a developer: strip away 90% of the noise and automate one tedious step.")

        return [
            {
                "angle": "🔥 Hot-Take / Contrarian",
                "content": take_1_clean,
                "character_count": len(take_1_clean),
            },
            {
                "angle": "🛠️ Builder Breakdown",
                "content": take_2_clean,
                "character_count": len(take_2_clean),
            },
        ]
