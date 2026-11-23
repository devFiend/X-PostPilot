"""
Audio Transcription Service powered by Groq Whisper.
Converts Telegram voice messages and audio memos into instant, accurate text transcriptions.
"""

from typing import Optional
import httpx
from postpilot.utils.config import settings


class AudioTranscriptionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
        self.model = "whisper-large-v3"

    async def transcribe_audio_bytes(
        self, audio_bytes: bytes, filename: str = "voice_note.ogg", mime_type: str = "audio/ogg"
    ) -> str:
        """
        Send raw voice note bytes to Groq Whisper for near-instant transcription.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for voice note transcription with Whisper.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": self.model,
            "response_format": "json",
            "temperature": "0.0",
        }
        files = {
            "file": (filename, audio_bytes, mime_type),
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(self.endpoint, headers=headers, data=data, files=files)
            res.raise_for_status()
            result = res.json()
            return result.get("text", "").strip()
