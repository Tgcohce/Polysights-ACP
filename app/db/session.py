"""
Database session management for ACP Polymarket Trading Agent.

This module provides database connection and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextvars import ContextVar
from typing import Optional

from app.utils.config import config


# Context variable to track the current session
_session_ctx_var: ContextVar[Optional[scoped_session]] = ContextVar("session", default=None)


def get_database_url() -> str:
    """
    Get the database URL from configuration.
    
    Returns:
        Database URL string
    """
    db_user = config.get("DATABASE_USER", "postgres")
    db_password = config.get("DATABASE_PASSWORD", "password")
    db_host = config.get("DATABASE_HOST", "localhost")
    db_port = config.get("DATABASE_PORT", "5432")
    db_name = config.get("DATABASE_NAME", "acp_agent")
    
    # Check for connection string override
    connection_string = config.get("DATABASE_URL")
    if connection_string:
        return connection_string
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def create_db_engine(echo: bool = False):
    """
    Create database engine with appropriate configuration.
    
    Args:
        echo: Whether to echo SQL statements
    
    Returns:
        SQLAlchemy Engine
    """
    database_url = get_database_url()
    
    # Configure engine with appropriate options for production
    engine = create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        connect_args={"connect_timeout": 10}
    )
    
    return engine


# Create engine
engine = create_db_engine(echo=config.get("DATABASE_ECHO", False))

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session
db_session = scoped_session(SessionLocal)


def get_db_session():
    """
    Get database session for the current context.
    
    Returns:
        Scoped session
    """
    session = _session_ctx_var.get()
    if session is None:
        session = db_session()
        _session_ctx_var.set(session)
    return session


def close_db_session():
    """
    Close the database session for the current context.
    """
    session = _session_ctx_var.get()
    if session is not None:
        session.close()
        _session_ctx_var.set(None)


def init_db():
    """
    Initialize database tables.
    
    Creates all tables if they don't exist.
    """
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)


def reset_db():
    """
    Reset database tables.
    
    Drops and recreates all tables. USE WITH CAUTION!
    Only available in development mode.
    """
    from app.db.models import Base
    
    # Check if we're in development mode
    if not config.get("DEVELOPMENT_MODE", False):
        raise RuntimeError("Cannot reset database in production mode")
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
