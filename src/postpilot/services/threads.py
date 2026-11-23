"""
Viral Thread Architect Service.
Transforms any topic, framework, or lesson into a high-engagement, scroll-stopping 4-5 tweet thread.
Enforces authentic tone, numbered structure, and clean call-to-action wraps.
"""

import urllib.parse
from typing import Dict, List
from postpilot.ai.router import AIRouter


class ThreadService:
    def __init__(self):
        self.router = AIRouter()

    async def generate_thread(
        self,
        topic: str,
        niche: str = "Software Engineering, AI, and Building Products",
        tweet_count: int = 4,
    ) -> Dict:
        """
        Generates a cohesive 4-to-5 tweet thread:
        - Tweet 1: Scroll-stopping hook ending with 🧵 or 👇.
        - Tweets 2 to (N-1): High-signal, actionable breakdown tweets.
        - Tweet N: Takeaway summary + follow/bookmark CTA.
        """
        system_prompt = (
            "You are an elite ghostwriter for viral tech threads on X (Twitter).\n"
            f"Your job is to write a cohesive, high-retention {tweet_count}-tweet thread.\n\n"
            "STRICT THREAD STRUCTURE:\n"
            "TWEET_1 (The Hook): A bold, scroll-stopping promise or contrarian frame that creates intense curiosity. "
            "End with 'Here's the breakdown: 🧵' or '👇'.\n"
            f"TWEET_2 to TWEET_{tweet_count-1} (The Value): Clear, numbered points (1/, 2/, 3/). "
            "Zero corporate fluff. Practical, punchy, actionable advice with 1 tasteful emoji per tweet.\n"
            f"TWEET_{tweet_count} (The Wrap & CTA): A 1-sentence synthesis + friendly prompt to bookmark and retweet.\n\n"
            "STRICT RULES:\n"
            "1. Every single tweet must be STRICTLY under 280 characters.\n"
            "2. No generic hashtags.\n"
            "3. Format each tweet labeled with TWEET_1:, TWEET_2:, etc."
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Target Audience/Niche: {niche}\n"
            f"Write the complete {tweet_count}-tweet thread now."
        )

        posts, provider_used = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
            temperature=0.88,
        )

        raw = posts[0] if posts else ""
        tweets = self._parse_thread(raw, topic, tweet_count)

        hook_url = ""
        if tweets:
            hook_text = urllib.parse.quote(tweets[0]["content"])
            hook_url = f"https://twitter.com/intent/tweet?text={hook_text}"

        full_thread_text = "\n\n---\n\n".join([f"[{t['num']}] {t['content']}" for t in tweets])

        return {
            "topic": topic,
            "provider": provider_used,
            "tweet_count": len(tweets),
            "tweets": tweets,
            "hook_composer_url": hook_url,
            "full_text": full_thread_text,
        }

    def _parse_thread(self, raw: str, topic: str, count: int) -> List[Dict]:
        lines = raw.split("\n")
        tweet_map = {}
        current_num = None

        for line in lines:
            line_str = line.strip()
            # Check TWEET_X:
            matched = False
            for i in range(1, count + 2):
                tag = f"TWEET_{i}:"
                if tag in line_str:
                    current_num = i
                    content = line_str.replace(tag, "").strip()
                    tweet_map[current_num] = [content] if content else []
                    matched = True
                    break
            if not matched and current_num is not None:
                if line_str:
                    tweet_map[current_num].append(line_str)

        tweets_list = []
        for i in range(1, count + 1):
            if i in tweet_map and tweet_map[i]:
                text = "\n".join(tweet_map[i]).strip().strip('"')
            else:
                text = ""

            if not text:
                if i == 1:
                    text = f"💡 Most developers struggle with {topic} because they overcomplicate the basics. Here is the 3-step playbook that actually works: 🧵"
                elif i == count:
                    text = f"🎯 Quick summary: keep systems simple, automate early, and iterate daily. If this was helpful, bookmark this thread and follow for more engineering breakdowns!"
                else:
                    text = f"{i-1}/ Focus on clean abstractions and measurable outcomes before scaling prematurely."

            # Guard 280 chars
            clean = text.strip().strip('"').strip("'")
            if len(clean) > 280:
                clean = clean[:277] + "..."

            tweets_list.append({
                "num": f"{i}/{count}",
                "content": clean,
                "character_count": len(clean),
            })

        return tweets_list
