"""
Autopilot Service: Orchestrates automated scheduling, content pillar rotation,
daily posting quotas, and emergency safety pauses.
"""

from datetime import datetime, time as dtime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from postpilot.database.models import Draft, PostStatus, CreatorProfile, ActivityLog
from postpilot.database.repositories import DraftRepository, ScheduleRepository, SettingsRepository
from postpilot.services.content import ContentService
from postpilot.utils.config import settings


class AutopilotService:
    DEFAULT_SCHEDULE_SLOTS = [
        dtime(9, 0),    # 9:00 AM - Educational / Morning Thought
        dtime(13, 0),   # 1:00 PM - Developer Observations / Technical Tips
        dtime(18, 30),  # 6:30 PM - Contrarian / Discussion
        dtime(20, 0),   # 8:00 PM - Build in public / Recap
    ]

    CATEGORY_ROTATION = [
        "educational",
        "developer observations",
        "contrarian opinion",
        "build in public",
        "technical tips",
    ]

    def __init__(self, db: Session):
        self.db = db
        self.draft_repo = DraftRepository(db)
        self.schedule_repo = ScheduleRepository(db)
        self.settings_repo = SettingsRepository(db)
        self.content_service = ContentService(db)

    def is_enabled(self) -> bool:
        val = self.settings_repo.get("AUTOPILOT_ENABLED", "false")
        return val.lower() == "true"

    def is_paused(self) -> bool:
        val = self.settings_repo.get("AUTOPILOT_PAUSED", "false")
        return val.lower() == "true"

    def enable(self) -> None:
        self.settings_repo.set("AUTOPILOT_ENABLED", "true")
        self.settings_repo.set("AUTOPILOT_PAUSED", "false")

    def disable(self) -> None:
        self.settings_repo.set("AUTOPILOT_ENABLED", "false")

    def pause(self) -> None:
        self.settings_repo.set("AUTOPILOT_PAUSED", "true")

    def resume(self) -> None:
        self.settings_repo.set("AUTOPILOT_PAUSED", "false")

    def get_mode(self) -> str:
        """'approval' (Assisted Autopilot) or 'autonomous'."""
        return self.settings_repo.get("AUTOPILOT_MODE", settings.DEFAULT_PUBLISH_MODE)

    def set_mode(self, mode: str) -> None:
        self.settings_repo.set("AUTOPILOT_MODE", mode)

    async def execute_cycle(self, topic: Optional[str] = None) -> List[Draft]:
        """
        Execute an autopilot cycle:
        1. Guard: Check if enabled and not paused.
        2. Guard: Respect MAX_POSTS_PER_DAY.
        3. Pick topic & category via rotation.
        4. Generate content.
        5. If autonomous: mark approved & schedule for next slot.
           If approval mode: save as PENDING_APPROVAL and notify.
        """
        if not self.is_enabled():
            raise RuntimeError("Autopilot is disabled. Enable it with 'postpilot autopilot enable'.")

        if self.is_paused():
            raise RuntimeError("Autopilot is currently paused. Resume with 'postpilot autopilot resume'.")

        # Check today's generated/scheduled posts count
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_schedules = (
            self.db.query(Draft)
            .filter(Draft.created_at >= today_start)
            .count()
        )
        if recent_schedules >= settings.MAX_POSTS_PER_DAY:
            raise RuntimeError(f"Daily post limit reached ({settings.MAX_POSTS_PER_DAY} posts/day).")

        # Determine category from rotation index
        current_idx = int(self.settings_repo.get("AUTOPILOT_ROTATION_IDX", "0"))
        category = self.CATEGORY_ROTATION[current_idx % len(self.CATEGORY_ROTATION)]
        self.settings_repo.set("AUTOPILOT_ROTATION_IDX", str((current_idx + 1) % len(self.CATEGORY_ROTATION)))

        profile = self.db.query(CreatorProfile).first()
        topic_to_use = topic or (profile.content_pillars.split(",")[0] if profile else "Software Engineering and AI")

        # Generate posts
        drafts = await self.content_service.generate_drafts(
            topic=topic_to_use,
            category=category,
            count=1,
        )

        mode = self.get_mode()
        for draft in drafts:
            if mode == "autopilot":
                # Autonomous mode: approve and schedule for next hour
                self.draft_repo.update_status(draft.id, PostStatus.APPROVED.value)
                target_time = datetime.now(timezone.utc) + timedelta(hours=2)
                self.schedule_repo.schedule(draft.id, target_time, settings.TIMEZONE)
                self.draft_repo.update_status(draft.id, PostStatus.SCHEDULED.value)
            else:
                # Approval mode (Assisted): mark PENDING_APPROVAL
                self.draft_repo.update_status(draft.id, PostStatus.PENDING_APPROVAL.value)

        return drafts
