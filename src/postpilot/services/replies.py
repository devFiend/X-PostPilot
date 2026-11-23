"""
Smart Reply Service for X (Twitter).
Generates high-signal, authentic, non-sycophantic replies to any tweet or topic.
Enables rapid engagement and follower growth for early-stage creator accounts.
"""

import re
import urllib.parse
from typing import Dict, List, Optional
from postpilot.ai.router import AIRouter


class SmartReplyService:
    def __init__(self):
        self.router = AIRouter()

    @staticmethod
    def extract_tweet_id(url_or_text: str) -> Optional[str]:
        """Extract tweet numeric status ID from an X or Twitter URL if present."""
        match = re.search(r"(?:twitter\.com|x\.com)/\w+/status/(\d+)", url_or_text)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def format_reply_composer_url(reply_text: str, in_reply_to_id: Optional[str] = None) -> str:
        """Create a direct 1-tap Twitter web intent composer link."""
        encoded = urllib.parse.quote(reply_text)
        base = f"https://twitter.com/intent/tweet?text={encoded}"
        if in_reply_to_id:
            base += f"&in_reply_to={in_reply_to_id}"
        return base

    async def generate_replies(
        self,
        source_tweet: str,
        niche: str = "Software Engineering, AI, and Building Products",
        tweet_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Generates 3 distinct high-status replies:
        1. 🛠️ Builder / Realist: Practical nuance, edge-case, or hands-on experience.
        2. 🔥 The Contrarian Edge: Respectfully challenges an assumption with a counter-point.
        3. ⚡ The Value-Add Punch: High-signal 1-liner that adds immediate insight.
        """
        extracted_id = tweet_id or self.extract_tweet_id(source_tweet)

        system_prompt = (
            "You are an elite tech creator and senior engineer on X (Twitter).\n"
            "You write high-signal, engaging replies under popular tech tweets to drive profile visits.\n\n"
            "STRICT REPLY RULES:\n"
            "1. NO SYCOPHANCY: NEVER say 'Great point!', 'So true!', '100% agree', 'Thanks for sharing'.\n"
            "2. SOUND 100% HUMAN: Casual, punchy, direct, respectful.\n"
            "3. INJECT LIFE WITH 1 EMOJI: Use 1 relevant emoji naturally to give pop.\n"
            "4. NO HASHTAGS: High-status commenters never use hashtags.\n"
            "5. STRICT LENGTH: Under 240 characters per reply.\n"
            "6. Output EXACTLY 3 options separated by '---':\n"
            "REPLY_1: (Builder / Real-world experience - practical takeaway from the trenches)\n"
            "REPLY_2: (The Contrarian Edge - respectful counter-perspective or unstated trade-off)\n"
            "REPLY_3: (The Value-Add Punch - sharp 1-2 sentence micro-insight)"
        )

        user_prompt = (
            f"Original Tweet / Topic:\n"
            f"\"{source_tweet}\"\n\n"
            f"Niche/Audience: {niche}\n"
            f"Generate REPLY_1, REPLY_2, and REPLY_3 now."
        )

        posts, _ = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
            temperature=0.88,
        )

        raw = posts[0] if posts else ""
        return self._parse_reply_options(raw, extracted_id)

    def _parse_reply_options(self, raw: str, tweet_id: Optional[str] = None) -> List[Dict[str, str]]:
        lines = raw.split("\n")
        r1_lines, r2_lines, r3_lines = [], [], []
        current = None

        for line in lines:
            if "REPLY_1:" in line:
                current = 1
                r1_lines.append(line.replace("REPLY_1:", "").strip())
            elif "REPLY_2:" in line:
                current = 2
                r2_lines.append(line.replace("REPLY_2:", "").strip())
            elif "REPLY_3:" in line:
                current = 3
                r3_lines.append(line.replace("REPLY_3:", "").strip())
            elif current == 1:
                r1_lines.append(line)
            elif current == 2:
                r2_lines.append(line)
            elif current == 3:
                r3_lines.append(line)

        r1 = "\n".join(r1_lines).strip().strip('"')
        r2 = "\n".join(r2_lines).strip().strip('"')
        r3 = "\n".join(r3_lines).strip().strip('"')

        # Fallback if delimiters weren't strictly returned
        if not r1 and not r2:
            parts = [p.strip().strip('"') for p in raw.split("---") if p.strip()]
            if len(parts) >= 3:
                r1, r2, r3 = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                r1, r2 = parts[0], parts[1]
                r3 = "🛠️ The real challenge isn't building it; it's maintaining it when production load hits."
            elif parts:
                r1 = parts[0]
                r2 = "🔥 The flip side: optimizing this too early wastes cycles you needed for distribution."
                r3 = "⚡ Simplicity wins every single time."

        def clean(text: str, default: str) -> str:
            t = text.strip().strip('"').strip("'")
            if not t:
                t = default
            if len(t) > 280:
                t = t[:277] + "..."
            return t

        rep1 = clean(r1, "🛠️ We saw this firsthand in production: the bottleneck wasn't compute, it was db query indexing.")
        rep2 = clean(r2, "🔥 The hidden trade-off here is developer cognitive load. More abstractions usually mean slower debugging.")
        rep3 = clean(r3, "⚡ 90% of architectural complexity can be replaced by one good cache and cleaner data models.")

        options = [
            {
                "angle": "🛠️ Builder Experience",
                "content": rep1,
                "character_count": len(rep1),
                "url": self.format_reply_composer_url(rep1, tweet_id),
            },
            {
                "angle": "🔥 Contrarian Edge",
                "content": rep2,
                "character_count": len(rep2),
                "url": self.format_reply_composer_url(rep2, tweet_id),
            },
            {
                "angle": "⚡ Value-Add Punch",
                "content": rep3,
                "character_count": len(rep3),
                "url": self.format_reply_composer_url(rep3, tweet_id),
            },
        ]
        return options
