"""
Unit tests for Trend Pulse & Breaking Niche News Radar.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from postpilot.trends.collector import TrendPulseCollector
from postpilot.trends.analyzer import TrendPulseAnalyzer
from postpilot.trends.generator import TrendTweetGenerator
from postpilot.database.repositories import TrendRepository
from postpilot.services.trends import TrendPulseService


def test_trend_repository_crud(in_memory_db):
    repo = TrendRepository(in_memory_db)
    story = repo.add_story(
        title="OpenAI releases new open model weights for developers",
        source="HackerNews",
        external_url="https://news.ycombinator.com/item?id=12345",
        score=450,
        category="AI",
    )
    assert story.id is not None
    assert story.title == "OpenAI releases new open model weights for developers"

    # Test duplicate detection
    is_dup = repo.is_recently_tracked("OpenAI releases new open model weights for developers")
    assert is_dup is True

    # Test distinct headline
    distinct = repo.is_recently_tracked("NASA rover lands on new crater on Mars")
    assert distinct is False


def test_trend_analyzer_niche_matching():
    analyzer = TrendPulseAnalyzer()

    # Tech / AI headlines should match
    assert analyzer.matches_niche("Claude 3.7 launched with hybrid reasoning models") is True
    assert analyzer.matches_niche("Why developers are replacing Redis with SQLite") is True
    assert analyzer.matches_niche("GitHub introduces automated pull request reviews") is True

    # Non-niche headlines should not match default tech keywords
    assert analyzer.matches_niche("Premier league football scores and match highlights") is False
    assert analyzer.matches_niche("Hollywood celebrity spotted at award ceremony") is False


@pytest.mark.asyncio
async def test_trend_tweet_generator_output():
    generator = TrendTweetGenerator()

    mock_context = {
        "topic": "Cursor AI Agents",
        "summary": "Engineers debate if automated agent workflows make code reviews obsolete.",
        "debate": "Will developers write less code or review more PRs?",
    }

    mock_llm_response = (
        "TAKE_1: Automated coding agents won't replace engineers. They'll just expose who actually understands systems versus who was copying StackOverflow.\n"
        "TAKE_2: The best way to use Cursor AI isn't letting it write whole apps. It's using it to automate tedious test cases and boilerplate."
    )

    with patch.object(generator.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ([mock_llm_response], "groq")
        takes = await generator.generate_trend_takes(mock_context, niche="Software Engineering")

        assert len(takes) == 2
        assert "Contrarian" in takes[0]["angle"]
        assert "Builder Breakdown" in takes[1]["angle"]
        assert len(takes[0]["content"]) <= 280
        assert len(takes[1]["content"]) <= 280


@pytest.mark.asyncio
async def test_trend_collector_hn_mock():
    collector = TrendPulseCollector()

    mock_top = [101]
    mock_item = {"id": 101, "title": "SQLite as an application file format", "url": "https://sqlite.org", "score": 300}

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp_top = MagicMock(status_code=200, json=lambda: mock_top)
        mock_resp_item = MagicMock(status_code=200, json=lambda: mock_item)
        mock_get.side_effect = [mock_resp_top, mock_resp_item]

        stories = await collector.fetch_hacker_news_top(limit=1)
        assert len(stories) == 1
        assert stories[0]["title"] == "SQLite as an application file format"
        assert stories[0]["source"] == "HackerNews"


@pytest.mark.asyncio
async def test_trend_service_scan(in_memory_db):
    service = TrendPulseService(in_memory_db)

    mock_candidates = [
        {
            "title": "DeepSeek introduces new open inference framework",
            "source": "HackerNews",
            "url": "https://example.com/deepseek",
            "score": 500,
        }
    ]

    with patch.object(service.collector, "collect_all_candidates", new_callable=AsyncMock) as mock_coll, \
         patch.object(service.generator.router, "generate_with_fallback", new_callable=AsyncMock) as mock_llm:

        mock_coll.return_value = mock_candidates
        mock_llm.return_value = (["TAKE_1: Open inference models are winning the long game.\nTAKE_2: How to host your own inference stack for $10/mo."], "groq")

        results = await service.scan_live_trends(limit=1)
        assert len(results) == 1
        assert results[0]["source"] == "HackerNews"
        assert len(results[0]["takes"]) == 2
