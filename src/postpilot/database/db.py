"""
Database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from postpilot.database.models import Base
from postpilot.utils.config import settings

DATABASE_URL = f"sqlite:///{settings.POSTPILOT_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


# Ensure tables are created on import
init_db()


def get_db() -> Session:
    """Yield a database session context."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass
