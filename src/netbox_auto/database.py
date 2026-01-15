"""Database initialization and session management for netbox-auto.

Provides SQLAlchemy engine, session factory, and database initialization.
Database is created lazily when init_db() is called.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from netbox_auto.config import get_config
from netbox_auto.models import Base

# Module-level cached engine and session factory
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine.

    Uses the database path from configuration.

    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine

    if _engine is None:
        config = get_config()
        db_path = Path(config.database.path)

        # Create parent directories if needed
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)

        # Use sqlite:/// URL format
        db_url = f"sqlite:///{db_path}"
        _engine = create_engine(db_url, echo=False)

    return _engine


def init_db() -> str:
    """Initialize the database, creating all tables if they don't exist.

    Returns:
        Path to the database file.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)

    config = get_config()
    return config.database.path


def get_session() -> Session:
    """Get a new database session.

    Returns:
        SQLAlchemy Session instance.
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)

    return _session_factory()
