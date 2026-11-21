"""
Unit tests for Publishing Adapters (Manual & X API).
"""

import pytest
from postpilot.publishers.manual import ManualPublisher
from postpilot.services.publishing import PublishingService
from postpilot.database.repositories import DraftRepository
from postpilot.database.models import PostStatus


@pytest.mark.asyncio
async def test_manual_publisher_intent_url():
    publisher = ManualPublisher()
    result = await publisher.publish("Test message for X")
    assert result.success is True
    assert result.method == "manual"
    assert "https://twitter.com/intent/tweet?text=Test%20message%20for%20X" in result.url


@pytest.mark.asyncio
async def test_unapproved_post_blocked(in_memory_db):
    repo = DraftRepository(in_memory_db)
    draft = repo.create(content="Unapproved draft", topic="Random", category="tips", provider="groq")
    # Draft is still in DRAFT status

    service = PublishingService(in_memory_db)
    result = await service.publish_draft(draft.id)
    assert result.success is False
    assert "Must be APPROVED" in result.error_message
