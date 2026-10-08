"""
session.py
SQLAlchemy database connection setup.
Reads DATABASE_URL from environment variables.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Must stay above the os.getenv calls below — and above anything that imports
# this module. override=False by default, so docker-compose env vars still win.
load_dotenv()

# Read from environment — set in .env or docker-compose.yml
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

SQL_ECHO = os.getenv("SQL_ECHO", "False").lower() in ("true", "1", "yes")

def get_engine():
    """
    Create SQLAlchemy engine.
    TODO:
      return create_engine(DATABASE_URL, echo=False)
      echo=True for debugging (logs all SQL), False for production
    """
    return create_engine(DATABASE_URL,echo=SQL_ECHO) # Close the firehose


def get_session_factory():
    """
    Create session factory bound to engine.
    TODO:
      engine = get_engine()
      return sessionmaker(autocommit=False, autoflush=False, bind=engine)
    """
    engine = get_engine()
    return sessionmaker(autoflush=False,bind=engine)

    # removing autocommit arugument as it is deprecated in SQLORM version 2.0.x 
    # Will use session.begin() in get_db() instead which replaces this behaviour


def create_tables():
    """
    Create all tables defined in models.py.
    Run once on first startup.
    TODO:
      engine = get_engine()
      Base.metadata.create_all(bind=engine)
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # Creation of tables ; does not returns anything

SessionLocal = get_session_factory()

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

    db = SessionLocal()
    try:
      yield db
    except Exception:
      db.rollback()
      raise
    finally:
      db.close()

