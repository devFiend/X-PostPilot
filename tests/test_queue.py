"""
Unit tests for Publishing Queue state transitions and invariants.
"""

from postpilot.database.repositories import DraftRepository
from postpilot.database.models import PostStatus


def test_draft_approval_workflow(in_memory_db):
    repo = DraftRepository(in_memory_db)
    draft = repo.create(
        content="Post awaiting review",
        topic="AI",
        category="dev_tips",
        provider="gemini",
    )
    assert draft.status == PostStatus.DRAFT.value

    # Approve
    repo.update_status(draft.id, PostStatus.APPROVED.value)
    updated = repo.get_by_id(draft.id)
    assert updated.status == PostStatus.APPROVED.value
