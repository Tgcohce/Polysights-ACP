"""
Database package for ACP Polymarket Trading Agent.

This package provides database models, sessions, and repositories
for persistent storage of trades, jobs, and analysis data.
"""
from app.db.models import (
    Job, Trade, Position, AnalysisCache, MarketData,
    Event, EventTrigger, TriggerResult, AgentProfile, 
    Collaboration, Message, SystemMetrics,
    JobStatus, TradeStatus, TradeDirection, StrategyType, ExecutionPriority,
    Base
)
from app.db.session import (
    get_db_session, close_db_session, init_db, reset_db,
    engine, db_session, get_database_url
)
from app.db.repository import (
    job_repository, trade_repository, position_repository,
    analysis_cache_repository, event_repository, trigger_repository,
    get_repositories
)


__all__ = [
    # Models
    "Job", "Trade", "Position", "AnalysisCache", "MarketData",
    "Event", "EventTrigger", "TriggerResult", "AgentProfile",
    "Collaboration", "Message", "SystemMetrics",
    "JobStatus", "TradeStatus", "TradeDirection", "StrategyType", "ExecutionPriority",
    "Base",
    
    # Session
    "get_db_session", "close_db_session", "init_db", "reset_db",
    "engine", "db_session", "get_database_url",
    
    # Repository
    "job_repository", "trade_repository", "position_repository",
    "analysis_cache_repository", "event_repository", "trigger_repository",
    "get_repositories"
]
