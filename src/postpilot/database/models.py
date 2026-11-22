"""
SQLAlchemy ORM models for PostPilot.
Includes Creator Intelligence & TweetDNA models.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PublishMethod(str, Enum):
    MANUAL = "manual"
    X_API = "x_api"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id = Column(String(50), nullable=True, unique=True)
    timezone = Column(String(50), default="Africa/Lagos")
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("CreatorProfile", back_populates="user", uselist=False)


class CreatorProfile(Base):
    __tablename__ = "creator_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), default="Creator")
    tone = Column(String(100), default="Direct, conversational, insightful")
    content_pillars = Column(Text, default="Software Engineering, AI & Automation, Building in Public")
    writing_preferences = Column(Text, default="Strong opening hooks, concise sentences, no corporate jargon")
    excluded_phrases = Column(Text, default="In today's fast-paced world, Game changer, Dive deep")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="profile")


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    topic = Column(String(255), nullable=True)
    category = Column(String(50), default="educational")
    provider = Column(String(50), default="groq")
    status = Column(String(50), default=PostStatus.DRAFT.value)
    character_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    schedules = relationship("ScheduledPost", back_populates="draft", cascade="all, delete-orphan")
    publications = relationship("PublishedPost", back_populates="draft", cascade="all, delete-orphan")


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    timezone = Column(String(50), default="Africa/Lagos")
    status = Column(String(50), default=PostStatus.SCHEDULED.value)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    draft = relationship("Draft", back_populates="schedules")


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    platform = Column(String(50), default="X")
    platform_post_id = Column(String(100), nullable=True)
    published_at = Column(DateTime, default=utc_now)
    publication_method = Column(String(50), default=PublishMethod.MANUAL.value)
    status = Column(String(50), default="SUCCESS")
    error_message = Column(Text, nullable=True)

    draft = relationship("Draft", back_populates="publications")


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


# -----------------------------------------------------------------------------
# TweetDNA & Creator Intelligence Models
# -----------------------------------------------------------------------------

class TrackedCreator(Base):
    __tablename__ = "tracked_creators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    last_synced_at = Column(DateTime, nullable=True)

    tweets = relationship("CreatorTweet", back_populates="creator", cascade="all, delete-orphan")
    dna = relationship("CreatorDNA", back_populates="creator", uselist=False, cascade="all, delete-orphan")


class CreatorTweet(Base):
    __tablename__ = "creator_tweets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("tracked_creators.id"), nullable=False)
    tweet_id = Column(String(100), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    likes_count = Column(Integer, default=0)
    retweets_count = Column(Integer, default=0)
    tweet_created_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    creator = relationship("TrackedCreator", back_populates="tweets")


class CreatorDNA(Base):
    __tablename__ = "creator_dna"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("tracked_creators.id"), nullable=False, unique=True)
    tone = Column(String(255), default="Direct, contrarian, actionable")
    content_pillars = Column(Text, default="")
    hook_patterns = Column(Text, default="")
    vocabulary = Column(Text, default="")
    writing_frameworks = Column(Text, default="")
    playbook_prompt = Column(Text, default="")
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    creator = relationship("TrackedCreator", back_populates="dna")


# -----------------------------------------------------------------------------
# Trend Pulse & Real-Time Niche News Models
# -----------------------------------------------------------------------------

class TrendingStory(Base):
    __tablename__ = "trending_stories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)  # e.g., "HackerNews", "X: @therundownai"
    external_url = Column(String(500), nullable=True)
    score = Column(Integer, default=0)
    category = Column(String(100), default="Tech")
    is_alerted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
