"""
Unit tests for Scheduler and Database Job Recovery.
"""

from datetime import datetime, timedelta
from postpilot.database.repositories import DraftRepository, ScheduleRepository
from postpilot.database.models import PostStatus


def test_schedule_persists_in_db(in_memory_db):
    draft_repo = DraftRepository(in_memory_db)
    draft = draft_repo.create(content="Scheduled post", topic="Dev", category="tips", provider="groq")
    draft_repo.update_status(draft.id, PostStatus.APPROVED.value)

    schedule_repo = ScheduleRepository(in_memory_db)
    future_time = datetime.utcnow() + timedelta(days=1)
    sp = schedule_repo.schedule(draft_id=draft.id, scheduled_at=future_time, timezone="Africa/Lagos")

    assert sp.id is not None
    pending = schedule_repo.list_pending()
    assert len(pending) == 1
    assert pending[0].draft_id == draft.id
