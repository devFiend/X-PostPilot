"""
Intelligent Audio Transcription and Voice-to-Tweet Engine.
- Multi-provider transcription: High-precision Groq Whisper with technical domain priming + Gemini Multimodal Audio fallback.
- VoiceTweetService: Intelligent transformer that turns spoken brain dumps into 3 distinct tweet options:
  1. 🎯 Direct Polish: Preserves the user's authentic words and voice, removing verbal fillers.
  2. 🔥 High-Impact Hook: Rephrases the spoken thought into a viral, scroll-stopping hook with lively emojis.
  3. ⚡ Minimalist Punch: Distills the insight into an ultra-sharp one-liner (< 120 chars).
"""

import base64
from typing import Dict, List, Optional
import httpx
from postpilot.ai.router import AIRouter
from postpilot.utils.config import settings


class AudioTranscriptionService:
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.groq_api_key = groq_api_key or api_key or settings.GROQ_API_KEY
        self.gemini_api_key = gemini_api_key or settings.GEMINI_API_KEY
        self.whisper_endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
        self.whisper_model = "whisper-large-v3"

    async def transcribe_audio_bytes(
        self, audio_bytes: bytes, filename: str = "voice_note.ogg", mime_type: str = "audio/ogg"
    ) -> str:
        """
        Transcribes audio bytes with Groq Whisper.
        Uses tech domain vocabulary priming for maximum accuracy on tech terms and accents.
        Automatically falls back to Google Gemini if Whisper fails.
        """
        # 1. Try Groq Whisper with technical vocabulary priming
        if self.groq_api_key:
            try:
                transcript = await self._transcribe_with_whisper(audio_bytes, filename, mime_type)
                if transcript and len(transcript.strip()) > 3:
                    return transcript
            except Exception:
                pass

        # 2. Try Gemini Multimodal Audio Fallback
        if self.gemini_api_key:
            try:
                gemini_transcript = await self._transcribe_with_gemini(audio_bytes, mime_type)
                if gemini_transcript and len(gemini_transcript.strip()) > 3:
                    return gemini_transcript
            except Exception:
                pass

        raise RuntimeError("Could not transcribe audio. Please verify your GROQ_API_KEY or GEMINI_API_KEY.")

    async def _transcribe_with_whisper(self, audio_bytes: bytes, filename: str, mime_type: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
        }
        data = {
            "model": self.whisper_model,
            "response_format": "json",
            "temperature": "0.0",
            "language": "en",
            "prompt": (
                "Software engineering, tech founder, indie hacker, coding, Python, JavaScript, TypeScript, "
                "React, Next.js, FastAPI, database, PostgreSQL, Redis, API, deployment, bugs, micro-SaaS, X Twitter post."
            ),
        }
        files = {
            "file": (filename, audio_bytes, mime_type),
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(self.whisper_endpoint, headers=headers, data=data, files=files)
            res.raise_for_status()
            result = res.json()
            return result.get("text", "").strip()

    async def _transcribe_with_gemini(self, audio_bytes: bytes, mime_type: str) -> str:
        model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_audio,
                            }
                        },
                        {
                            "text": (
                                "Transcribe this audio recording word-for-word. Keep technical terms, "
                                "developer vocabulary, and natural phrasing intact. "
                                "Return ONLY the transcribed text, with zero commentary or introduction."
                            )
                        },
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()


class VoiceTweetService:
    """
    Intelligently polishes spoken voice notes into 3 tweet-ready options.
    Honors the user's authentic voice rather than generating unrelated generic topics.
    """

    def __init__(self):
        self.router = AIRouter()

    async def transform_voice_to_tweets(self, transcript: str) -> List[Dict[str, str]]:
        system_prompt = (
            "You are an elite ghostwriter for tech founders and builders on X (Twitter).\n"
            "The user just recorded a raw, spoken voice note or audio memo.\n\n"
            "CRITICAL INSTRUCTION:\n"
            "Their voice note might ALREADY be tweet-worthy! Do NOT ignore their words or invent an unrelated generic post.\n"
            "Your job is to adapt their exact thought into 3 distinct, high-impact options:\n\n"
            "TAKE_1: (Direct Polish - 'My Words, Tightened')\n"
            "Preserve the user's authentic personal voice, exact vocabulary, and rhythm. "
            "Simply strip verbal filler ('um', 'like', 'you know', 'basically', 'man'), fix run-on phrasing, and tighten into a crisp, tweet-ready version of what they actually said.\n\n"
            "TAKE_2: (The Viral Hook / Engagement Spin)\n"
            "Rephrase their spoken insight into a high-impact, scroll-stopping hook with 1-2 lively emojis (e.g. 💡, 🔥, ⚡, 🛠️).\n\n"
            "TAKE_3: (The Minimalist Cut)\n"
            "Distill their core spoken thought into an ultra-sharp, punchy one-liner under 120 characters with zero fluff.\n\n"
            "STRICT RULES:\n"
            "1. Every single tweet must be STRICTLY under 280 characters.\n"
            "2. No generic hashtags.\n"
            "3. Format your response EXACTLY as:\n"
            "TAKE_1: [content]\n"
            "TAKE_2: [content]\n"
            "TAKE_3: [content]"
        )

        user_prompt = (
            f"User's Spoken Voice Note:\n"
            f"\"{transcript}\"\n\n"
            f"Generate TAKE_1, TAKE_2, and TAKE_3 now."
        )

        posts, provider_used = await self.router.generate_with_fallback(
            prompt=user_prompt,
            system_prompt=system_prompt,
            count=1,
            temperature=0.85,
        )

        raw = posts[0] if posts else ""
        return self._parse_voice_takes(raw, transcript)

    def _parse_voice_takes(self, raw: str, original_transcript: str) -> List[Dict[str, str]]:
        lines = raw.split("\n")
        t1_lines, t2_lines, t3_lines = [], [], []
        current = None

        for line in lines:
            if "TAKE_1:" in line:
                current = 1
                t1_lines.append(line.replace("TAKE_1:", "").strip())
            elif "TAKE_2:" in line:
                current = 2
                t2_lines.append(line.replace("TAKE_2:", "").strip())
            elif "TAKE_3:" in line:
                current = 3
                t3_lines.append(line.replace("TAKE_3:", "").strip())
            elif current == 1:
                t1_lines.append(line)
            elif current == 2:
                t2_lines.append(line)
            elif current == 3:
                t3_lines.append(line)

        take_1 = "\n".join(t1_lines).strip().strip('"')
        take_2 = "\n".join(t2_lines).strip().strip('"')
        take_3 = "\n".join(t3_lines).strip().strip('"')

        # Fallback if delimiter parsing failed
        if not take_1 and not take_2:
            parts = [p.strip().strip('"') for p in raw.split("---") if p.strip()]
            if len(parts) >= 3:
                take_1, take_2, take_3 = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                take_1, take_2 = parts[0], parts[1]
                take_3 = original_transcript[:120]
            elif parts:
                take_1 = parts[0]
                take_2 = f"💡 {original_transcript}"
                take_3 = original_transcript[:120]

        def clean(text: str, fallback: str) -> str:
            t = text.strip().strip('"').strip("'")
            if not t:
                t = fallback
            if len(t) > 280:
                t = t[:277] + "..."
            return t

        t1_clean = clean(take_1, original_transcript)
        t2_clean = clean(take_2, f"💡 {original_transcript}")
        t3_clean = clean(take_3, original_transcript[:120])

        return [
            {
                "angle": "🎯 Direct Polish (Your Words, Tightened)",
                "content": t1_clean,
                "character_count": len(t1_clean),
            },
            {
                "angle": "🔥 High-Impact Hook",
                "content": t2_clean,
                "character_count": len(t2_clean),
            },
            {
                "angle": "⚡ Minimalist Punch",
                "content": t3_clean,
                "character_count": len(t3_clean),
            },
        ]
