"""
Unit tests for DraftRepository and Content Management.
"""

from postpilot.database.repositories import DraftRepository
from postpilot.database.models import PostStatus


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
