"""
Smart Reply Service for X (Twitter).
Generates high-signal, authentic, non-sycophantic replies to any tweet or topic.
Fetches live tweet text and author context from X/Twitter URLs so replies are 100% on-point.
Enforces authentic human peer voice (no bot formulas, no unsolicited lecturing).
"""

import re
import urllib.parse
from typing import Dict, List, Optional
import httpx
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

    async def fetch_tweet_by_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch real tweet text and author handle from an X status link using Jina Reader.
        Bypasses login walls so the AI sees the actual post instead of a bare URL.
        """
        match = re.search(r"(?:twitter\.com|x\.com)/(\w+)/status/(\d+)", url)
        if not match:
            return None
        author_username, tweet_id = match.group(1), match.group(2)
        reader_url = f"https://r.jina.ai/{url}"

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=12.0, headers=headers, follow_redirects=True) as client:
                res = await client.get(reader_url)
                if res.status_code == 200 and len(res.text) > 50:
                    text = res.text
                    # Check for title line: # @author on X: "..."
                    for line in text.split("\n"):
                        if " on X: " in line:
                            parts = line.split(" on X: ")
                            found_author = parts[0].replace("#", "").replace("@", "").strip() or author_username
                            raw_content = parts[1].strip().strip('"').strip("'")
                            if raw_content:
                                return {
                                    "author": found_author,
                                    "tweet_id": tweet_id,
                                    "text": raw_content,
                                }

                    # Fallback: check conversation body
                    if "Conversation" in text:
                        conv = text.split("Conversation", 1)[1]
                        lines = [l.strip() for l in conv.split("\n") if l.strip()]
                        for l in lines:
                            clean = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", l)
                            clean = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", clean)
                            clean = re.sub(r"https?://\S+", "", clean).strip()
                            if len(clean) > 20 and not any(bad in clean for bad in ["Log in", "Sign up", "Terms", "Image"]):
                                return {
                                    "author": author_username,
                                    "tweet_id": tweet_id,
                                    "text": clean,
                                }
        except Exception:
            pass

        return {
            "author": author_username,
            "tweet_id": tweet_id,
            "text": "",
        }

    async def generate_replies(
        self,
        source_tweet: str,
        niche: str = "Software Engineering, AI, and Building Products",
        tweet_id: Optional[str] = None,
    ) -> Dict:
        """
        Generates 3 authentic human replies:
        1. 💬 Casual Peer / Relatable Banter: Sharp, dry wit, peer developer reaction.
        2. 💡 The Insider Nuance: Thoughtful counter-perspective or unstated trade-off.
        3. ❓ The Provocative Question: High-signal question that drives replies.
        """
        extracted_id = tweet_id or self.extract_tweet_id(source_tweet)
        resolved_text = source_tweet.strip()
        author_handle = ""

        # If input contains a Twitter/X URL, fetch the actual tweet text!
        if "twitter.com/" in source_tweet or "x.com/" in source_tweet:
            fetched = await self.fetch_tweet_by_url(source_tweet)
            if fetched:
                extracted_id = fetched.get("tweet_id") or extracted_id
                author_handle = fetched.get("author", "")
                if fetched.get("text"):
                    resolved_text = fetched["text"]

        author_context = f"by @{author_handle}" if author_handle else ""

        system_prompt = (
            "You are an authentic, sharp tech creator and software builder on X (Twitter).\n"
            "You write high-signal, engaging replies under tweets to spark genuine conversation.\n\n"
            "CRITICAL HUMAN VOICE RULES (DO NOT SOUND LIKE AN AI BOT):\n"
            "1. NO PREACHY LECTURING: NEVER say 'The key takeaway here is...', 'In software engineering, one must...', "
            "'Crucial point', or offer unsolicited textbook advice.\n"
            "2. NO SYCOPHANCY: NEVER say '100% agree!', 'Great point!', 'So true!', 'Thanks for sharing'.\n"
            "3. RESPOND DIRECTLY: Your reply MUST directly reference the specific claim, humor, or situation in the tweet.\n"
            "4. SOUND LIKE A PEER: Talk like a sharp developer chatting with friends over coffee. Casual, punchy, witty.\n"
            "5. SHORT & PUNCHY: Every reply must be strictly under 180 characters.\n"
            "6. NO HASHTAGS.\n\n"
            "Generate EXACTLY 3 distinct human styles:\n"
            "REPLY_1: (Casual Peer / Relatable Banter - witty reaction or relatable human thought, 1 sentence)\n"
            "REPLY_2: (Insider Nuance - thoughtful unstated trade-off or real-world perspective)\n"
            "REPLY_3: (Provocative Question - smart, genuine question that compels people to reply)"
        )

        user_prompt = (
            f"Original Tweet {author_context}:\n"
            f"\"{resolved_text}\"\n\n"
            f"Generate REPLY_1, REPLY_2, and REPLY_3 now."
        )

        posts, _ = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
            temperature=0.85,
        )

        raw = posts[0] if posts else ""
        options = self._parse_reply_options(raw, extracted_id, resolved_text)

        return {
            "author": author_handle,
            "tweet_id": extracted_id,
            "original_text": resolved_text,
            "options": options,
        }

    def _parse_reply_options(self, raw: str, tweet_id: Optional[str] = None, original_text: str = "") -> List[Dict[str, str]]:
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
                r3 = "Wait, how does this hold up once real production load kicks in?"
            elif parts:
                r1 = parts[0]
                r2 = "The hidden trade-off here is developer cognitive load."
                r3 = "What's the alternative when scaling this past day one?"

        def clean(text: str, default: str) -> str:
            t = text.strip().strip('"').strip("'")
            if not t:
                t = default
            if len(t) > 280:
                t = t[:277] + "..."
            return t

        rep1 = clean(r1, "Honestly, the hardest part of this is dealing with the edge cases nobody talks about.")
        rep2 = clean(r2, "The hidden trade-off is maintenance cost. Looks great on paper until you have to debug it at 2 AM.")
        rep3 = clean(r3, "Curious how you're handling this when scale doubles?")

        options = [
            {
                "angle": "💬 Casual Peer / Relatable Banter",
                "content": rep1,
                "character_count": len(rep1),
                "url": self.format_reply_composer_url(rep1, tweet_id),
            },
            {
                "angle": "💡 The Insider Nuance",
                "content": rep2,
                "character_count": len(rep2),
                "url": self.format_reply_composer_url(rep2, tweet_id),
            },
            {
                "angle": "❓ The Provocative Question",
                "content": rep3,
                "character_count": len(rep3),
                "url": self.format_reply_composer_url(rep3, tweet_id),
            },
        ]
        return options
