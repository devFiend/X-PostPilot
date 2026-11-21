"""
Database repositories for PostPilot and TweetDNA entities.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from postpilot.database.models import (
    Draft,
    ScheduledPost,
    PublishedPost,
    CreatorProfile,
    PostStatus,
    ActivityLog,
    Setting,
    TrackedCreator,
    CreatorTweet,
    CreatorDNA,
)


def utc_now():
    return datetime.now(timezone.utc)


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
            draft.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(draft)
        return draft

    def update_content(self, draft_id: int, new_content: str) -> Optional[Draft]:
        draft = self.get_by_id(draft_id)
        if draft:
            draft.content = new_content
            draft.character_count = len(new_content)
            draft.updated_at = utc_now()
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

    def cancel(self, schedule_id: int) -> bool:
        sp = self.db.query(ScheduledPost).filter(ScheduledPost.id == schedule_id).first()
        if sp:
            sp.status = PostStatus.CANCELLED.value
            self.db.commit()
            return True
        return False


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else default

    def set(self, key: str, value: str) -> None:
        setting = self.db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
            setting.updated_at = utc_now()
        else:
            setting = Setting(key=key, value=value)
            self.db.add(setting)
        self.db.commit()


class CreatorRepository:
    """Repository for Tracked Creators, Tweets, and Creator DNA."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, username: str, display_name: Optional[str] = None, bio: Optional[str] = None) -> TrackedCreator:
        clean_user = username.lstrip("@").lower().strip()
        creator = self.db.query(TrackedCreator).filter(TrackedCreator.username == clean_user).first()
        if not creator:
            creator = TrackedCreator(
                username=clean_user,
                display_name=display_name or clean_user,
                bio=bio or "",
            )
            self.db.add(creator)
            self.db.commit()
            self.db.refresh(creator)
        return creator

    def get_by_username(self, username: str) -> Optional[TrackedCreator]:
        clean_user = username.lstrip("@").lower().strip()
        return self.db.query(TrackedCreator).filter(TrackedCreator.username == clean_user).first()

    def list_all(self) -> List[TrackedCreator]:
        return self.db.query(TrackedCreator).order_by(TrackedCreator.created_at.desc()).all()

    def delete_by_username(self, username: str) -> bool:
        creator = self.get_by_username(username)
        if creator:
            self.db.delete(creator)
            self.db.commit()
            return True
        return False

    def add_tweets(self, creator_id: int, tweets_data: List[dict]) -> int:
        """Upsert a list of tweets for a creator. Returns count of new tweets added."""
        new_count = 0
        for item in tweets_data:
            tweet_id = str(item.get("id"))
            existing = self.db.query(CreatorTweet).filter(CreatorTweet.tweet_id == tweet_id).first()
            if not existing:
                tweet = CreatorTweet(
                    creator_id=creator_id,
                    tweet_id=tweet_id,
                    text=item.get("text", "").strip(),
                    likes_count=item.get("likes", 0),
                    retweets_count=item.get("retweets", 0),
                )
                self.db.add(tweet)
                new_count += 1

        creator = self.db.query(TrackedCreator).filter(TrackedCreator.id == creator_id).first()
        if creator:
            creator.last_synced_at = utc_now()

        self.db.commit()
        return new_count

    def get_creator_tweets(self, creator_id: int, limit: int = 50) -> List[CreatorTweet]:
        return (
            self.db.query(CreatorTweet)
            .filter(CreatorTweet.creator_id == creator_id)
            .order_by(CreatorTweet.likes_count.desc(), CreatorTweet.created_at.desc())
            .limit(limit)
            .all()
        )

    def save_dna(
        self,
        creator_id: int,
        tone: str,
        content_pillars: str,
        hook_patterns: str,
        vocabulary: str,
        writing_frameworks: str,
        playbook_prompt: str,
    ) -> CreatorDNA:
        dna = self.db.query(CreatorDNA).filter(CreatorDNA.creator_id == creator_id).first()
        if not dna:
            dna = CreatorDNA(
                creator_id=creator_id,
                tone=tone,
                content_pillars=content_pillars,
                hook_patterns=hook_patterns,
                vocabulary=vocabulary,
                writing_frameworks=writing_frameworks,
                playbook_prompt=playbook_prompt,
            )
            self.db.add(dna)
        else:
            dna.tone = tone
            dna.content_pillars = content_pillars
            dna.hook_patterns = hook_patterns
            dna.vocabulary = vocabulary
            dna.writing_frameworks = writing_frameworks
            dna.playbook_prompt = playbook_prompt
            dna.updated_at = utc_now()

        self.db.commit()
        self.db.refresh(dna)
        return dna

    def get_dna(self, creator_id: int) -> Optional[CreatorDNA]:
        return self.db.query(CreatorDNA).filter(CreatorDNA.creator_id == creator_id).first()
