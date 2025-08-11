#!/usr/bin/env python
"""
Database Initialization Script for ACP Polymarket Trading Agent.

This script initializes the database tables based on SQLAlchemy models.
Run this script before starting the application for the first time.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.db.models import Base
from app.db.session import engine, init_db
from app.utils.config import config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    try:
        # Create tables
        init_db()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


if __name__ == "__main__":
    logger.info("Initializing database...")
    create_tables()
    logger.info("Database initialization complete.")
