"""
Unit tests for Smart Replies, Viral Threads, and Voice Note Transcription.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import pytest
from postpilot.services.replies import SmartReplyService
from postpilot.services.threads import ThreadService
from postpilot.services.audio import AudioTranscriptionService
from postpilot.telegram.handlers import thread_command
from postpilot.utils.config import settings


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
        "REPLY_1: Honestly, the hardest part of this is dealing with the edge cases nobody talks about.\n"
        "REPLY_2: The hidden trade-off is maintenance cost. Looks great on paper until you have to debug it at 2 AM.\n"
        "REPLY_3: Curious how you're handling this when scale doubles?"
    )

    with patch.object(svc.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ([mock_raw], "gemini")
        result = await svc.generate_replies(
            source_tweet="What is your best database optimization tip?",
            tweet_id="11223344",
        )

        assert isinstance(result, dict)
        replies = result["options"]
        assert len(replies) == 3
        assert "Casual Peer" in replies[0]["angle"]
        assert "edge cases" in replies[0]["content"]
        assert "in_reply_to=11223344" in replies[0]["url"]
        assert replies[0]["character_count"] <= 280

        assert "Insider Nuance" in replies[1]["angle"]
        assert "Provocative Question" in replies[2]["angle"]


@pytest.mark.asyncio
async def test_smart_reply_fetch_tweet_by_url():
    svc = SmartReplyService()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.text = (
        "Title: @levelsio on X\n\n"
        "# @levelsio on X: \"Shipping fast is not about cutting corners, it is about eliminating meetings.\"\n\n"
        "Conversation details..."
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        data = await svc.fetch_tweet_by_url("https://x.com/levelsio/status/1899123456789")

        assert data is not None
        assert data["author"] == "levelsio"
        assert data["tweet_id"] == "1899123456789"
        assert "Shipping fast" in data["text"]


@pytest.mark.asyncio
async def test_reply_command_delivers_cards(monkeypatch):
    from postpilot.telegram.handlers import reply_command
    monkeypatch.setattr(settings, "TELEGRAM_OWNER_ID", 123456789)

    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_message = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.message = update.effective_message

    context = MagicMock()
    context.args = ["https://x.com/levelsio/status/1899123456789"]

    mock_result = {
        "author": "levelsio",
        "tweet_id": "1899123456789",
        "original_text": "Shipping fast is not about cutting corners, it is about eliminating meetings.",
        "options": [
            {
                "angle": "💬 Casual Peer / Relatable Banter",
                "content": "Every 30-minute sync costs 3 hours of deep work.",
                "character_count": 48,
                "url": "https://twitter.com/intent/tweet?text=Every...&in_reply_to=1899123456789",
            },
            {
                "angle": "💡 The Insider Nuance",
                "content": "Async updates work only when engineers write clearly.",
                "character_count": 52,
                "url": "https://twitter.com/intent/tweet?text=Async...&in_reply_to=1899123456789",
            },
            {
                "angle": "❓ The Provocative Question",
                "content": "What is the single biggest meeting time sink in your org right now?",
                "character_count": 67,
                "url": "https://twitter.com/intent/tweet?text=What...&in_reply_to=1899123456789",
            },
        ],
    }

    with patch("postpilot.telegram.handlers.SmartReplyService.generate_replies", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_result
        await reply_command(update, context)

        # 1 status msg + 1 intro + 3 reply cards = 5 reply_text calls
        assert update.effective_message.reply_text.call_count == 5
        calls = update.effective_message.reply_text.call_args_list

        intro_call = calls[1][0][0]
        assert "Replying to @levelsio" in intro_call
        assert "Shipping fast" in intro_call

        card_call_1 = calls[2][0][0]
        assert "```text\nEvery 30-minute sync costs 3 hours of deep work.\n```" in card_call_1
        assert "Casual Peer" in card_call_1


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


@pytest.mark.asyncio
async def test_thread_command_delivers_individual_cards(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_OWNER_ID", 123456789)

    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_message = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.message = update.effective_message

    context = MagicMock()
    context.args = ["Building", "micro-SaaS"]

    mock_thread_data = {
        "topic": "Building micro-SaaS",
        "provider": "groq",
        "tweet_count": 3,
        "hook_composer_url": "https://twitter.com/intent/tweet?text=Hook",
        "tweets": [
            {"num": "1/3", "content": "Hook text 🧵", "character_count": 11},
            {"num": "2/3", "content": "Value point 1", "character_count": 13},
            {"num": "3/3", "content": "Wrap and CTA", "character_count": 12},
        ],
    }

    with patch("postpilot.telegram.handlers.ThreadService.generate_thread", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_thread_data
        await thread_command(update, context)

        # 1 status msg + 1 intro + 3 tweet cards + 1 footer = 6 messages sent!
        assert update.effective_message.reply_text.call_count == 6
        calls = update.effective_message.reply_text.call_args_list

        # Verify tweet cards have code blocks for 1-tap copy
        card_call_1 = calls[2][0][0]
        assert "```text\nHook text 🧵\n```" in card_call_1
        assert "Tweet 1/3 — The Hook" in card_call_1

        card_call_2 = calls[3][0][0]
        assert "```text\nValue point 1\n```" in card_call_2


@pytest.mark.asyncio
async def test_voice_tweet_service_generates_3_takes():
    from postpilot.services.audio import VoiceTweetService

    svc = VoiceTweetService()
    raw_takes = (
        "TAKE_1: Why do developers spend weeks arguing about state management when prop drilling works for 90% of apps?\n"
        "TAKE_2: 💡 State management is a trap. 90% of web apps only ever need prop drilling. Keep it dead simple.\n"
        "TAKE_3: ⚡ Stop over-engineering state management. Prop drilling is fine."
    )

    with patch.object(svc.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ([raw_takes], "gemini")
        takes = await svc.transform_voice_to_tweets(
            "Why do developers spend weeks arguing about state management when prop drilling works for 90% of apps?"
        )

        assert len(takes) == 3
        assert "Direct Polish" in takes[0]["angle"]
        assert "state management" in takes[0]["content"]
        assert takes[0]["character_count"] <= 280

        assert "High-Impact Hook" in takes[1]["angle"]
        assert "Minimalist Punch" in takes[2]["angle"]


@pytest.mark.asyncio
async def test_audio_transcription_gemini_fallback():
    # Verify fallback to Gemini when Groq fails
    svc = AudioTranscriptionService(groq_api_key="bad_groq_key", gemini_api_key="good_gemini_key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Gemini transcribed this audio perfectly."}]
                }
            }
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch.object(svc, "_transcribe_with_whisper", side_effect=Exception("Groq error")), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        transcript = await svc.transcribe_audio_bytes(b"dummy_bytes")
        assert transcript == "Gemini transcribed this audio perfectly."

