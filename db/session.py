"""
session.py
SQLAlchemy database connection setup.
Reads DATABASE_URL from environment variables.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base


# Read from environment — set in .env or docker-compose.yml
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://reviewlens:password@localhost:5432/reviewlens"
)


def get_engine():
    """
    Create SQLAlchemy engine.
    TODO:
      return create_engine(DATABASE_URL, echo=False)
      echo=True for debugging (logs all SQL), False for production
    """
    pass


def get_session_factory():
    """
    Create session factory bound to engine.
    TODO:
      engine = get_engine()
      return sessionmaker(autocommit=False, autoflush=False, bind=engine)
    """
    pass


def create_tables():
    """
    Create all tables defined in models.py.
    Run once on first startup.
    TODO:
      engine = get_engine()
      Base.metadata.create_all(bind=engine)
    """
    pass


def get_db():
    """
    FastAPI dependency — yields a database session per request.
    Closes session after request completes (success or error).
    TODO:
      SessionLocal = get_session_factory()
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
    """
    pass