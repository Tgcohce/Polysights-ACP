"""
Database models for ACP Polymarket Trading Agent.

This module contains SQLAlchemy models for storing trades, jobs, and analysis cache.
"""
from datetime import datetime
import enum
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Status of a job in the ACP ecosystem."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    AWAITING_PAYMENT = "awaiting_payment"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TradeStatus(str, enum.Enum):
    """Status of a trade."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TradeDirection(str, enum.Enum):
    """Direction of a trade."""
    BUY = "buy"
    SELL = "sell"


class StrategyType(str, enum.Enum):
    """Type of trading strategy."""
    ARBITRAGE = "arbitrage"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    EVENT_DRIVEN = "event_driven"
    SMART_MONEY = "smart_money"
    MANUAL = "manual"


class ExecutionPriority(str, enum.Enum):
    """Priority for trade execution."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Job(Base):
    """
    Job model for tracking ACP jobs.
    
    Represents a job in the ACP ecosystem.
    """
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    requester_id = Column(String(64), nullable=False, index=True)
    requester_name = Column(String(128))
    title = Column(String(256), nullable=False)
    description = Column(Text)
    job_type = Column(String(64), nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = Column(DateTime)
    payment_amount = Column(Float)
    payment_token = Column(String(64))
    payment_status = Column(String(32))
    completion_percentage = Column(Float, default=0.0)
    result_summary = Column(Text)
    error_message = Column(Text)
    parameters = Column(JSON)
    extra_data = Column(JSON)
    
    # Relationships
    trades = relationship("Trade", back_populates="job")
    
    # Indices
    __table_args__ = (
        Index("idx_jobs_status_created", status, created_at),
        Index("idx_jobs_requester_status", requester_id, status)
    )
    
    def __repr__(self):
        return f"<Job(job_id='{self.job_id}', title='{self.title}', status='{self.status}')>"


class Trade(Base):
    """
    Trade model for tracking trades.
    
    Represents a trade executed by the agent.
    """
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(String(64), unique=True, nullable=False, index=True)
    market_id = Column(String(64), nullable=False, index=True)
    market_name = Column(String(256))
    outcome_id = Column(String(64), nullable=False)
    outcome_name = Column(String(256))
    direction = Column(Enum(TradeDirection), nullable=False)
    size = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    filled_size = Column(Float, default=0.0)
    filled_price = Column(Float)
    status = Column(Enum(TradeStatus), nullable=False, default=TradeStatus.PENDING)
    strategy = Column(Enum(StrategyType), nullable=False)
    job_id = Column(String(64), ForeignKey("jobs.job_id"), index=True)
    signal_id = Column(String(64), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    fee = Column(Float, default=0.0)
    profit_loss = Column(Float)
    profit_loss_percentage = Column(Float)
    execution_priority = Column(Enum(ExecutionPriority), default=ExecutionPriority.NORMAL)
    error_message = Column(Text)
    extra_data = Column(JSON)
    
    # Relationships
    job = relationship("Job", back_populates="trades")
    positions = relationship("Position", back_populates="trade")
    
    # Indices
    __table_args__ = (
        Index("idx_trades_strategy_created", strategy, created_at),
        Index("idx_trades_market_direction", market_id, direction),
        Index("idx_trades_status_created", status, created_at)
    )
    
    def __repr__(self):
        return f"<Trade(trade_id='{self.trade_id}', market_id='{self.market_id}', direction='{self.direction}', size={self.size}, price={self.price})>"


class Position(Base):
    """
    Position model for tracking open positions.
    
    Represents an active trading position.
    """
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    position_id = Column(String(64), unique=True, nullable=False, index=True)
    market_id = Column(String(64), nullable=False, index=True)
    market_name = Column(String(256))
    outcome_id = Column(String(64), nullable=False)
    outcome_name = Column(String(256))
    direction = Column(Enum(TradeDirection), nullable=False)
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    strategy = Column(Enum(StrategyType), nullable=False)
    trade_id = Column(String(64), ForeignKey("trades.trade_id"), index=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percentage = Column(Float, default=0.0)
    realized_pnl = Column(Float)
    realized_pnl_percentage = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    is_active = Column(Boolean, default=True, index=True)
    extra_data = Column(JSON)
    
    # Relationships
    trade = relationship("Trade", back_populates="positions")
    
    # Indices
    __table_args__ = (
        Index("idx_positions_active_strategy", is_active, strategy),
        Index("idx_positions_market_active", market_id, is_active)
    )
    
    def __repr__(self):
        return f"<Position(position_id='{self.position_id}', market_id='{self.market_id}', direction='{self.direction}', size={self.size}, entry_price={self.entry_price})>"


class AnalysisCache(Base):
    """
    Analysis cache model for storing market analysis results.
    
    Caches results of market analysis to avoid redundant computation.
    """
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(String(64), nullable=False, index=True)
    analysis_type = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    expiration = Column(DateTime, nullable=False)
    data = Column(JSON, nullable=False)
    parameters = Column(JSON)
    
    # Indices and constraints
    __table_args__ = (
        UniqueConstraint("market_id", "analysis_type", name="uq_analysis_market_type"),
        Index("idx_analysis_expiration", expiration)
    )
    
    def __repr__(self):
        return f"<AnalysisCache(market_id='{self.market_id}', analysis_type='{self.analysis_type}', timestamp='{self.timestamp}')>"


class MarketData(Base):
    """
    Market data model for storing historical market data.
    
    Stores time series data for markets.
    """
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(String(64), nullable=False, index=True)
    outcome_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    liquidity = Column(Float)
    open_interest = Column(Float)
    bid_price = Column(Float)
    ask_price = Column(Float)
    mid_price = Column(Float)
    
    # Indices
    __table_args__ = (
        Index("idx_market_data_market_time", market_id, outcome_id, timestamp),
        Index("idx_market_data_recent", timestamp.desc())
    )
    
    def __repr__(self):
        return f"<MarketData(market_id='{self.market_id}', outcome_id='{self.outcome_id}', timestamp='{self.timestamp}', price={self.price})>"


class Event(Base):
    """
    Event model for storing events from the event monitor.
    
    Stores events detected by the event monitoring system.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    category = Column(String(32), nullable=False, index=True)
    source = Column(String(32), nullable=False)
    severity = Column(String(32), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    data = Column(JSON)
    market_id = Column(String(64), index=True)
    outcome_id = Column(String(64))
    processed = Column(Boolean, default=False, index=True)
    processed_timestamp = Column(DateTime)
    
    # Indices
    __table_args__ = (
        Index("idx_events_category_timestamp", category, timestamp.desc()),
        Index("idx_events_source_timestamp", source, timestamp.desc()),
        Index("idx_events_market_timestamp", market_id, timestamp.desc())
    )
    
    def __repr__(self):
        return f"<Event(event_id='{self.event_id}', title='{self.title}', category='{self.category}', timestamp='{self.timestamp}')>"


class TriggerResult(Base):
    """
    Trigger result model for storing results of trigger evaluations.
    
    Stores the results of event triggers.
    """
    __tablename__ = "trigger_results"
    
    id = Column(Integer, primary_key=True)
    trigger_id = Column(String(64), nullable=False, index=True)
    event_id = Column(String(64), ForeignKey("events.event_id"), nullable=False)
    matched = Column(Boolean, nullable=False)
    match_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    condition_results = Column(JSON)
    action_results = Column(JSON)
    
    # Indices
    __table_args__ = (
        Index("idx_trigger_results_matched", matched, match_time.desc()),
        Index("idx_trigger_results_trigger_time", trigger_id, match_time.desc())
    )
    
    def __repr__(self):
        return f"<TriggerResult(trigger_id='{self.trigger_id}', event_id='{self.event_id}', matched={self.matched}, match_time='{self.match_time}')>"


class EventTrigger(Base):
    """
    Event trigger model for storing trigger definitions.
    
    Stores trigger configurations for the event monitor.
    """
    __tablename__ = "event_triggers"
    
    id = Column(Integer, primary_key=True)
    trigger_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True, index=True)
    categories = Column(JSON)  # List of categories
    sources = Column(JSON)  # List of sources
    min_severity = Column(String(32), nullable=False)
    conditions = Column(JSON)  # List of condition objects
    condition_type = Column(String(32), default="all")
    actions = Column(JSON)  # List of action objects
    cooldown_seconds = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiration = Column(DateTime)
    market_ids = Column(JSON)  # List of market IDs
    outcome_ids = Column(JSON)  # List of outcome IDs
    tags = Column(JSON)  # List of tags
    
    def __repr__(self):
        return f"<EventTrigger(trigger_id='{self.trigger_id}', name='{self.name}', enabled={self.enabled})>"


class AgentProfile(Base):
    """
    Agent profile model for storing information about other agents.
    
    Stores profiles of agents in the ACP ecosystem.
    """
    __tablename__ = "agent_profiles"
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)
    capabilities = Column(JSON)  # List of capabilities
    description = Column(Text)
    wallet_address = Column(String(64), nullable=False)
    reputation_score = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    completed_jobs = Column(Integer, default=0)
    total_jobs = Column(Integer, default=0)
    specializations = Column(JSON)  # List of specializations
    fee_model = Column(JSON)  # Fee model data
    region = Column(String(64))
    last_active = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow)
    trust_level = Column(Integer, default=2)
    custom_attributes = Column(JSON)  # Custom attributes
    
    # Indices
    __table_args__ = (
        Index("idx_agent_profiles_trust", trust_level),
        Index("idx_agent_profiles_active", last_active.desc())
    )
    
    def __repr__(self):
        return f"<AgentProfile(agent_id='{self.agent_id}', name='{self.name}', role='{self.role}')>"


class Collaboration(Base):
    """
    Collaboration model for storing collaboration data.
    
    Tracks collaborations with other agents.
    """
    __tablename__ = "collaborations"
    
    id = Column(Integer, primary_key=True)
    collaboration_id = Column(String(64), unique=True, nullable=False, index=True)
    request_id = Column(String(64), unique=True, nullable=False)
    requester_id = Column(String(64), nullable=False, index=True)
    provider_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    description = Column(Text)
    parameters = Column(JSON)
    fee = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = Column(DateTime)
    completed_at = Column(DateTime)
    result = Column(JSON)
    
    # Indices
    __table_args__ = (
        Index("idx_collaborations_status", status, created_at.desc()),
        Index("idx_collaborations_provider_status", provider_id, status)
    )
    
    def __repr__(self):
        return f"<Collaboration(collaboration_id='{self.collaboration_id}', requester_id='{self.requester_id}', provider_id='{self.provider_id}', status='{self.status}')>"


class Message(Base):
    """
    Message model for storing agent-to-agent messages.
    
    Stores messages exchanged with other agents.
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(64), unique=True, nullable=False, index=True)
    sender_id = Column(String(64), nullable=False, index=True)
    recipient_id = Column(String(64), nullable=False, index=True)
    subject = Column(String(256), nullable=False)
    content = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reply_to = Column(String(64), index=True)
    read = Column(Boolean, default=False, index=True)
    encrypted = Column(Boolean, default=False)
    urgent = Column(Boolean, default=False)
    
    # Indices
    __table_args__ = (
        Index("idx_messages_conversation", sender_id, recipient_id, timestamp.desc()),
        Index("idx_messages_unread", recipient_id, read, timestamp.desc())
    )
    
    def __repr__(self):
        return f"<Message(message_id='{self.message_id}', sender_id='{self.sender_id}', recipient_id='{self.recipient_id}', subject='{self.subject}')>"


class SystemMetrics(Base):
    """
    System metrics model for storing performance metrics.
    
    Stores historical metrics about system performance.
    """
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_type = Column(String(64), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(32))
    tags = Column(JSON)  # Additional tags for filtering
    
    # Indices
    __table_args__ = (
        Index("idx_system_metrics_type_time", metric_type, timestamp.desc()),
    )
    
    def __repr__(self):
        return f"<SystemMetrics(metric_type='{self.metric_type}', timestamp='{self.timestamp}', value={self.value})>"
