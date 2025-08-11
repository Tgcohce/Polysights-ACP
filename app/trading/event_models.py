"""
Event models for ACP Polymarket Trading Agent.

This module defines event and trigger models for the real-time event monitor.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
import uuid

from pydantic import BaseModel, Field, validator


class EventSeverity(str, Enum):
    """Severity level of an event."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Category of an event."""
    MARKET = "market"
    PRICE = "price"
    VOLUME = "volume"
    LIQUIDITY = "liquidity"
    SOCIAL = "social"
    NEWS = "news"
    ONCHAIN = "onchain"
    AGENT = "agent"
    SYSTEM = "system"
    WALLET = "wallet"
    TRADE = "trade"
    JOB = "job"


class EventSource(str, Enum):
    """Source of an event."""
    POLYMARKET = "polymarket"
    POLYSIGHTS = "polysights"
    BLOCKCHAIN = "blockchain"
    INTERNAL = "internal"
    EXTERNAL = "external"
    TWITTER = "twitter"
    NEWS_API = "news_api"
    AGENT_NETWORK = "agent_network"


class TriggerCondition(str, Enum):
    """Condition type for a trigger."""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"
    NOT_EQUAL_TO = "not_equal_to"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does_not_contain"
    PERCENTAGE_CHANGE = "percentage_change"
    THRESHOLD_CROSS = "threshold_cross"
    PATTERN_MATCH = "pattern_match"
    ANOMALY = "anomaly"
    VOLUME_SPIKE = "volume_spike"
    LIQUIDITY_CHANGE = "liquidity_change"
    TIME_WINDOW = "time_window"
    COMPOSITE = "composite"


class ActionType(str, Enum):
    """Type of action to take when a trigger fires."""
    NOTIFY = "notify"
    ALERT = "alert"
    TRADE = "trade"
    ADJUST_STRATEGY = "adjust_strategy"
    PAUSE_TRADING = "pause_trading"
    RESUME_TRADING = "resume_trading"
    EXECUTE_CUSTOM = "execute_custom"
    LOG = "log"


class Event(BaseModel):
    """
    Event model for the event monitor.
    
    Represents a single event in the system.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    category: EventCategory
    source: EventSource
    severity: EventSeverity = EventSeverity.INFO
    title: str
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)
    market_id: Optional[str] = None
    outcome_id: Optional[str] = None
    related_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    processed: bool = False
    processed_timestamp: Optional[datetime] = None


class TriggerAction(BaseModel):
    """
    Action to take when a trigger fires.
    
    Represents an action in response to a trigger.
    """
    action_type: ActionType
    params: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class EventTrigger(BaseModel):
    """
    Event trigger model.
    
    Represents a trigger for monitoring events.
    """
    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    enabled: bool = True
    categories: List[EventCategory] = Field(default_factory=list)
    sources: List[EventSource] = Field(default_factory=list)
    min_severity: EventSeverity = EventSeverity.INFO
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    condition_type: str = "all"  # "all" or "any"
    actions: List[TriggerAction] = Field(default_factory=list)
    cooldown_seconds: int = 0
    last_triggered: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expiration: Optional[datetime] = None
    market_ids: List[str] = Field(default_factory=list)
    outcome_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class PriceTrigger(EventTrigger):
    """
    Price-specific trigger.
    
    Monitors price changes in markets.
    """
    target_price: float
    comparison: TriggerCondition
    percentage_threshold: Optional[float] = None
    timeframe_seconds: Optional[int] = None
    
    def __init__(self, **data):
        # Set defaults for price triggers
        if "categories" not in data:
            data["categories"] = [EventCategory.PRICE]
        if "sources" not in data:
            data["sources"] = [EventSource.POLYMARKET]
        
        super().__init__(**data)


class VolumeTrigger(EventTrigger):
    """
    Volume-specific trigger.
    
    Monitors trading volume in markets.
    """
    target_volume: float
    comparison: TriggerCondition
    percentage_threshold: Optional[float] = None
    timeframe_seconds: Optional[int] = None
    
    def __init__(self, **data):
        # Set defaults for volume triggers
        if "categories" not in data:
            data["categories"] = [EventCategory.VOLUME]
        if "sources" not in data:
            data["sources"] = [EventSource.POLYMARKET]
        
        super().__init__(**data)


class SocialTrigger(EventTrigger):
    """
    Social media trigger.
    
    Monitors social media for keywords or sentiment.
    """
    keywords: List[str] = Field(default_factory=list)
    sentiment_threshold: Optional[float] = None
    volume_threshold: Optional[int] = None
    
    def __init__(self, **data):
        # Set defaults for social triggers
        if "categories" not in data:
            data["categories"] = [EventCategory.SOCIAL]
        if "sources" not in data:
            data["sources"] = [EventSource.TWITTER, EventSource.POLYSIGHTS]
        
        super().__init__(**data)


class NewsTrigger(EventTrigger):
    """
    News trigger.
    
    Monitors news sources for relevant articles.
    """
    keywords: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    sentiment_threshold: Optional[float] = None
    
    def __init__(self, **data):
        # Set defaults for news triggers
        if "categories" not in data:
            data["categories"] = [EventCategory.NEWS]
        if "sources" not in data:
            data["sources"] = [EventSource.NEWS_API, EventSource.POLYSIGHTS]
        
        super().__init__(**data)


class OnchainTrigger(EventTrigger):
    """
    On-chain trigger.
    
    Monitors blockchain events.
    """
    contract_addresses: List[str] = Field(default_factory=list)
    event_signatures: List[str] = Field(default_factory=list)
    min_transaction_value: Optional[float] = None
    
    def __init__(self, **data):
        # Set defaults for onchain triggers
        if "categories" not in data:
            data["categories"] = [EventCategory.ONCHAIN]
        if "sources" not in data:
            data["sources"] = [EventSource.BLOCKCHAIN]
        
        super().__init__(**data)


class CompositeTrigger(EventTrigger):
    """
    Composite trigger.
    
    Combines multiple trigger conditions.
    """
    sub_triggers: List[Dict[str, Any]] = Field(default_factory=list)
    join_type: str = "and"  # "and" or "or"
    
    def __init__(self, **data):
        # Set defaults for composite triggers
        if "condition_type" not in data:
            data["condition_type"] = "composite"
        
        super().__init__(**data)


class TriggerResult(BaseModel):
    """
    Result of a trigger evaluation.
    
    Contains information about a triggered event.
    """
    trigger_id: str
    event_id: str
    matched: bool
    match_time: datetime = Field(default_factory=datetime.now)
    condition_results: Dict[str, bool] = Field(default_factory=dict)
    action_results: List[Dict[str, Any]] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
