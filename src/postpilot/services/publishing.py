"""
Publishing Service: Coordinates manual vs X API publishing, enforces approval checks.
"""

from sqlalchemy.orm import Session
from postpilot.database.models import Draft, PublishedPost, PostStatus
from postpilot.database.repositories import DraftRepository
from postpilot.publishers.base import BasePublisher, PublishResult
from postpilot.publishers.manual import ManualPublisher
from postpilot.publishers.x_publisher import XPublisher
from postpilot.utils.config import settings


class PublishingService:
    def __init__(self, db: Session):
        self.db = db
        self.draft_repo = DraftRepository(db)
        self.manual_publisher = ManualPublisher()
        self.x_publisher = XPublisher()

    def get_publisher(self, method: str | None = None) -> BasePublisher:
        chosen = method or settings.DEFAULT_PUBLISH_METHOD
        if chosen == "x_api":
            return self.x_publisher
        return self.manual_publisher

    async def publish_draft(self, draft_id: int, method: str | None = None) -> PublishResult:
        draft = self.draft_repo.get_by_id(draft_id)
        if not draft:
            return PublishResult(success=False, method="unknown", error_message=f"Draft {draft_id} not found.")

        # Invariant check: post must be approved before publishing
        if draft.status not in (PostStatus.APPROVED.value, PostStatus.SCHEDULED.value):
            return PublishResult(
                success=False,
                method=method or settings.DEFAULT_PUBLISH_METHOD,
                error_message=f"Draft #{draft_id} cannot be published because its status is {draft.status}. Must be APPROVED.",
            )

        publisher = self.get_publisher(method)
        result = await publisher.publish(draft.content)

        # Record in published_posts
        record = PublishedPost(
            draft_id=draft.id,
            platform=result.platform,
            platform_post_id=result.post_id,
            publication_method=result.method,
            status="SUCCESS" if result.success else "FAILED",
            error_message=result.error_message,
        )
        self.db.add(record)

        if result.success:
            draft.status = PostStatus.PUBLISHED.value
        else:
            draft.status = PostStatus.FAILED.value
        self.db.commit()

        return result
