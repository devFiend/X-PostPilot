"""
Database repositories for PostPilot entities.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from postpilot.database.models import Draft, ScheduledPost, PublishedPost, CreatorProfile, PostStatus, ActivityLog


class DraftRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, content: str, topic: str, category: str, provider: str, status: str = PostStatus.DRAFT.value) -> Draft:
        draft = Draft(
            content=content,
            topic=topic,
            category=category,
            provider=provider,
            status=status,
            character_count=len(content),
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def get_by_id(self, draft_id: int) -> Optional[Draft]:
        return self.db.query(Draft).filter(Draft.id == draft_id).first()

    def list_all(self, status: Optional[str] = None) -> List[Draft]:
        query = self.db.query(Draft)
        if status:
            query = query.filter(Draft.status == status)
        return query.order_by(Draft.created_at.desc()).all()

    def update_status(self, draft_id: int, status: str) -> Optional[Draft]:
        draft = self.get_by_id(draft_id)
        if draft:
            draft.status = status
            draft.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(draft)
        return draft

    def update_content(self, draft_id: int, new_content: str) -> Optional[Draft]:
        draft = self.get_by_id(draft_id)
        if draft:
            draft.content = new_content
            draft.character_count = len(new_content)
            draft.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(draft)
        return draft

    def delete(self, draft_id: int) -> bool:
        draft = self.get_by_id(draft_id)
        if draft:
            self.db.delete(draft)
            self.db.commit()
            return True
        return False


class ScheduleRepository:
    def __init__(self, db: Session):
        self.db = db

    def schedule(self, draft_id: int, scheduled_at: datetime, timezone: str) -> ScheduledPost:
        post = ScheduledPost(
            draft_id=draft_id,
            scheduled_at=scheduled_at,
            timezone=timezone,
            status=PostStatus.SCHEDULED.value,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def list_pending(self) -> List[ScheduledPost]:
        return (
            self.db.query(ScheduledPost)
            .filter(ScheduledPost.status == PostStatus.SCHEDULED.value)
            .order_by(ScheduledPost.scheduled_at.asc())
            .all()
        )

    def mark_published(self, schedule_id: int) -> None:
        sp = self.db.query(ScheduledPost).filter(ScheduledPost.id == schedule_id).first()
        if sp:
            sp.status = PostStatus.PUBLISHED.value
            self.db.commit()
