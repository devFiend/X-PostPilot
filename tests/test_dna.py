"""
Unit tests for TweetDNA Intelligence, Deduplication, Rephrasing, and Drip Delivery.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from postpilot.dna.collector import PublicTweetCollector
from postpilot.database.repositories import CreatorRepository, DraftRepository
from postpilot.scheduler.hourly_delivery import is_active_hour, safe_md
from postpilot.dna.generator import TweetDNAGenerator
from postpilot.database.models import CreatorDNA, PostStatus
from postpilot.telegram.keyboards import get_draft_keyboard


def test_public_tweet_collector_clean_text():
    collector = PublicTweetCollector()
    raw = "Building software is fun https://t.co/xyz123   check it out!   "
    clean = collector.clean_tweet_text(raw)
    assert clean == "Building software is fun check it out!"


def test_creator_repository_crud(in_memory_db):
    repo = CreatorRepository(in_memory_db)
    creator = repo.get_or_create("levelsio", display_name="Pieter Levels")
    assert creator.id is not None
    assert creator.username == "levelsio"

    # Add tweets
    tweets = [
        {"id": "t1", "text": "Ship small products quickly.", "likes": 500, "retweets": 80},
        {"id": "t2", "text": "Don't spend months building before launch.", "likes": 300, "retweets": 40},
    ]
    added = repo.add_tweets(creator.id, tweets)
    assert added == 2
    cached = repo.get_creator_tweets(creator.id)
    assert len(cached) == 2

    # Save DNA
    dna = repo.save_dna(
        creator_id=creator.id,
        tone="Direct, contrarian",
        content_pillars="Indie building, Micro-SaaS",
        hook_patterns="Bold assertion",
        vocabulary="Short words",
        writing_frameworks="Hook -> Insight",
        playbook_prompt="Write punchy tweets without corporate jargon.",
    )
    assert dna.id is not None

    retrieved_dna = repo.get_dna(creator.id)
    assert retrieved_dna is not None
    assert retrieved_dna.tone == "Direct, contrarian"


def test_creator_with_leading_underscore(in_memory_db):
    """Verify that creators whose username starts with _ are supported without error."""
    repo = CreatorRepository(in_memory_db)
    creator = repo.get_or_create("_florian", display_name="Florian")
    assert creator.id is not None
    assert creator.username == "_florian"

    # Markdown escaping should escape the underscore
    escaped = safe_md(creator.username)
    assert "\\_" in escaped


def test_draft_repository_deduplication(in_memory_db):
    """Verify Jaccard word similarity deduplication blocks identical or near-duplicate drafts."""
    draft_repo = DraftRepository(in_memory_db)
    d1 = draft_repo.create(
        content="Building micro SaaS is 90% execution and 10% idea. Ship fast and talk to real users.",
        topic="SaaS",
        category="creator_dna",
        provider="groq",
    )
    assert d1.id is not None

    # Exact or near-duplicate should be detected
    is_dup = draft_repo.is_duplicate(
        "Building micro SaaS is 90% execution and 10% idea. Ship fast and talk to real users."
    )
    assert is_dup is True

    # High similarity variant should be flagged
    high_sim = draft_repo.is_duplicate(
        "Building micro SaaS is 90% execution. Ship fast and talk to real users."
    )
    assert high_sim is True

    # Distinct content should not be flagged
    distinct = draft_repo.is_duplicate(
        "PostgreSQL indexes are the fastest way to solve database query slowdowns in production."
    )
    assert distinct is False


def test_direct_x_composer_url_in_keyboard():
    """Verify keyboard uses direct twitter.com/intent/tweet URL instead of web browser redirect."""
    keyboard = get_draft_keyboard(draft_id=42, content="Test tweet for X!")
    buttons = keyboard.inline_keyboard
    # First row first button should be the direct composer URL
    post_btn = buttons[0][0]
    assert post_btn.text == "🚀 Post to X Now"
    assert "https://twitter.com/intent/tweet?text=" in post_btn.url
    assert "Test%20tweet%20for%20X%21" in post_btn.url

    # First row second button should be 'Mark as Posted' callback
    posted_btn = buttons[0][1]
    assert posted_btn.text == "✅ Mark as Posted"
    assert posted_btn.callback_data == "posted_42"


def test_is_active_hour():
    result = is_active_hour("Africa/Lagos")
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_tweetdna_generator_length_check():
    generator = TweetDNAGenerator()
    mock_dna = CreatorDNA(
        tone="Direct",
        content_pillars="Dev",
        hook_patterns="Bold",
        vocabulary="Plain",
        writing_frameworks="Rule",
        playbook_prompt="Write well.",
    )

    with patch.object(generator.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (["This is a punchy generated tweet about building fast with clean code."], "groq")
        posts = await generator.generate_from_dna(
            dna=mock_dna,
            creator_username="levelsio",
            topic="Shipping MVP",
            count=1,
        )
        assert len(posts) == 1
        assert len(posts[0]) <= 280


@pytest.mark.asyncio
async def test_generate_rephrased_tweet():
    generator = TweetDNAGenerator()
    mock_dna = CreatorDNA(
        tone="Direct, contrarian",
        content_pillars="Dev",
        hook_patterns="Bold",
        vocabulary="Plain",
        writing_frameworks="Rule",
        playbook_prompt="Write well.",
    )

    with patch.object(generator.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (["Stop overengineering your MVP. 10 paying customers matter more than clean code."], "groq")
        rephrased = await generator.generate_rephrased_tweet(
            source_tweet="Don't spend 6 months building before launching.",
            creator_username="_florian",
            dna=mock_dna,
            niche="Micro-SaaS",
        )
        assert rephrased is not None
        assert "Stop overengineering" in rephrased
        assert len(rephrased) <= 280
