"""
Unit tests for TweetDNA Intelligence & Hourly Delivery.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from postpilot.dna.collector import PublicTweetCollector
from postpilot.database.repositories import CreatorRepository
from postpilot.scheduler.hourly_delivery import is_active_hour
from postpilot.dna.generator import TweetDNAGenerator
from postpilot.database.models import CreatorDNA


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


def test_is_active_hour():
    # Verify is_active_hour returns boolean without crashing
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
