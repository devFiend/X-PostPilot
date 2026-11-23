"""
Unit tests for DraftRepository, Content Management, Archetypes, and Diversity Guardrails.
"""

from unittest.mock import AsyncMock, patch
import pytest
from postpilot.database.repositories import DraftRepository
from postpilot.database.models import PostStatus
from postpilot.services.content import ContentService, TWEET_ARCHETYPES


def test_create_and_retrieve_draft(in_memory_db):
    repo = DraftRepository(in_memory_db)
    draft = repo.create(
        content="Test tweet content #1",
        topic="Tech",
        category="educational",
        provider="groq",
    )
    assert draft.id is not None
    assert draft.status == PostStatus.DRAFT.value
    assert draft.character_count == len("Test tweet content #1")

    retrieved = repo.get_by_id(draft.id)
    assert retrieved is not None
    assert retrieved.content == "Test tweet content #1"


@pytest.mark.asyncio
async def test_content_service_generates_with_archetype_and_history(in_memory_db):
    repo = DraftRepository(in_memory_db)
    # Pre-populate an existing draft
    repo.create(
        content="🚀 Clean code is debt that compounds if ignored.",
        topic="Coding",
        category="educational",
        provider="groq",
    )

    service = ContentService(in_memory_db)

    with patch.object(service.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = (
            [
                "🔥 Stop refactoring code that nobody uses. Validate user demand before obsessing over architecture.",
                "⚡ Shipping fast is better than perfect abstractions.",
            ],
            "groq",
        )

        drafts = await service.generate_drafts(
            topic="Software Engineering",
            category="educational",
            count=2,
            archetype="Contrarian",
        )

        assert len(drafts) == 2
        assert "Stop refactoring code" in drafts[0].content

        # Verify that prompt received negative history and archetype instructions
        call_kwargs = mock_gen.call_args[1]
        system_prompt = call_kwargs["system_prompt"]
        assert "DO NOT REPEAT OR MIMIC RECENT POSTS" in system_prompt
        assert "Clean code is debt" in system_prompt
        assert "INJECT LIFE WITH EMOJIS" in system_prompt
        assert "Contrarian" in system_prompt


@pytest.mark.asyncio
async def test_content_service_deduplicates_repetitive_drafts(in_memory_db):
    repo = DraftRepository(in_memory_db)
    # Pre-populate draft with high keyword overlap
    repo.create(
        content="Building micro SaaS is 90% execution and 10% idea. Ship fast and talk to real users.",
        topic="SaaS",
        category="educational",
        provider="groq",
    )

    service = ContentService(in_memory_db)

    with patch.object(service.router, "generate_with_fallback", new_callable=AsyncMock) as mock_gen:
        # First post is near-identical duplicate, second post is fresh
        mock_gen.return_value = (
            [
                "Building micro SaaS is 90% execution and 10% idea. Ship fast and talk to real users.",
                "🛠️ Always add database indexes on foreign keys before shipping to production.",
            ],
            "groq",
        )

        drafts = await service.generate_drafts(
            topic="SaaS",
            category="educational",
            count=2,
        )

        # The duplicate should be rejected, only the fresh draft should be saved
        assert len(drafts) == 1
        assert "Always add database indexes" in drafts[0].content
