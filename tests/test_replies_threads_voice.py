"""
Unit tests for Smart Replies, Viral Threads, and Voice Note Transcription.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import pytest
from postpilot.services.replies import SmartReplyService
from postpilot.services.threads import ThreadService
from postpilot.services.audio import AudioTranscriptionService


def test_smart_reply_tweet_id_extraction():
    svc = SmartReplyService()
    url1 = "https://x.com/levelsio/status/1859345678901234567"
    assert svc.extract_tweet_id(url1) == "1859345678901234567"

    url2 = "https://twitter.com/karpathy/status/999888777666"
    assert svc.extract_tweet_id(url2) == "999888777666"

    text_no_id = "Just a raw thought without any tweet link"
    assert svc.extract_tweet_id(text_no_id) is None


def test_smart_reply_composer_url():
    svc = SmartReplyService()
    url_without_id = svc.format_reply_composer_url("Great point about caching.")
    assert "https://twitter.com/intent/tweet?text=Great%20point%20about%20caching." in url_without_id
    assert "in_reply_to=" not in url_without_id

    url_with_id = svc.format_reply_composer_url("Agreed.", in_reply_to_id="123456")
    assert "https://twitter.com/intent/tweet?text=Agreed.&in_reply_to=123456" in url_with_id


@pytest.mark.asyncio
async def test_smart_reply_generation():
    svc = SmartReplyService()
    mock_raw = (
        "REPLY_1: 🛠️ We tested this in production and the database latency was cut by 60%.\n"
        "REPLY_2: 🔥 The unstated trade-off here is operational complexity for small teams.\n"
        "REPLY_3: ⚡ Clean abstractions always beat premature microservices."
    )

    with patch.object(svc.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ([mock_raw], "gemini")
        replies = await svc.generate_replies(
            source_tweet="What is your best database optimization tip?",
            tweet_id="11223344",
        )

        assert len(replies) == 3
        assert "Builder Experience" in replies[0]["angle"]
        assert "database latency" in replies[0]["content"]
        assert "in_reply_to=11223344" in replies[0]["url"]
        assert replies[0]["character_count"] <= 280

        assert "Contrarian Edge" in replies[1]["angle"]
        assert "Value-Add Punch" in replies[2]["angle"]


@pytest.mark.asyncio
async def test_viral_thread_generation():
    svc = ThreadService()
    mock_thread_raw = (
        "TWEET_1: 💡 95% of engineers overcomplicate authentication. Here is the dead-simple 3-step blueprint: 🧵\n"
        "TWEET_2: 1/ Store session tokens in HttpOnly secure cookies. Never in localStorage.\n"
        "TWEET_3: 2/ Keep token refresh rotation strict and under 15 minutes.\n"
        "TWEET_4: 🎯 Summary: simplicity beats complex auth trees. Bookmark this and follow @postpilot for more!"
    )

    with patch.object(svc.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ([mock_thread_raw], "groq")
        thread_data = await svc.generate_thread(topic="Secure Auth in FastAPI", tweet_count=4)

        assert thread_data["tweet_count"] == 4
        assert len(thread_data["tweets"]) == 4
        assert thread_data["tweets"][0]["num"] == "1/4"
        assert "overcomplicate authentication" in thread_data["tweets"][0]["content"]
        assert "https://twitter.com/intent/tweet?text=" in thread_data["hook_composer_url"]
        for t in thread_data["tweets"]:
            assert t["character_count"] <= 280


@pytest.mark.asyncio
async def test_audio_transcription_whisper():
    svc = AudioTranscriptionService(api_key="mock_groq_key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "I just deployed the new database index and query latency dropped from 400ms to 8ms."
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        transcript = await svc.transcribe_audio_bytes(b"dummy_ogg_bytes", filename="voice.ogg")

        assert "database index and query latency" in transcript
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["model"] == "whisper-large-v3"
