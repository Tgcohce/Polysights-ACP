"""
PyTest configuration for ACP Polymarket Trading Agent.

This module provides fixtures and configuration for tests.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app.db.models import Base
from app.utils.config import config


@pytest.fixture(scope="session")
def test_db_url():
    """Return the database URL for testing."""
    # Use in-memory SQLite for tests
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create a test database engine."""
    engine = create_engine(test_db_url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_tables(test_engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, test_tables):
    """Create a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_config():
    """Provide a test configuration."""
    original_config = config.copy()
    
    # Override with test settings
    config["DEVELOPMENT_MODE"] = True
    config["DATABASE_URL"] = "sqlite:///:memory:"
    config["DATABASE_ECHO"] = False
    
    yield config
    
    # Restore original config
    for key, value in original_config.items():
        config[key] = value
