"""
Database initialization and connection management for ACP Polymarket Trading Agent.
"""
import asyncio
from contextlib import asynccontextmanager
from loguru import logger

from app.db.session import init_db, close_db_session, get_db_session


async def init_db_async():
    """
    Initialize database asynchronously.
    
    This is a wrapper around the synchronous init_db function.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, init_db)
    logger.info("Database initialized successfully")


@asynccontextmanager
async def get_db():
    """
    Async context manager for database sessions.
    
    Example:
        async with get_db() as db:
            results = await db.execute(query)
    
    Yields:
        Database session
    """
    try:
        db = get_db_session()
        yield db
    finally:
        close_db_session()
