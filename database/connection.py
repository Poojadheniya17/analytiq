# database/connection.py
# Analytiq — Database connection with SQLAlchemy
# Supports both PostgreSQL (production) and SQLite (development fallback)

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from database.models import Base

# ── Connection string ─────────────────────────────────────────
# Production:  set DATABASE_URL=postgresql://user:pass@host/db
# Development: falls back to SQLite automatically
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL — production
    if DATABASE_URL.startswith("postgres://"):
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,   # test connections before using
        pool_recycle=300,     # recycle connections every 5 minutes
        echo=False
    )
else:
    # SQLite — development fallback
    SQLITE_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "analytiq.db")
    )
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Health check — returns True if DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
