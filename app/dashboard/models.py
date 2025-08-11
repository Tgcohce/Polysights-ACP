"""
Dashboard models for ACP Polymarket Trading Agent.

This module contains Pydantic models for the agent dashboard API.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

from app.trading.strategy_engine import StrategyType, TradeDirection, ExecutionPriority


class JobStatus(str, Enum):
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


class StrategyStatus(str, Enum):
    """Status of a trading strategy."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class ChartPeriod(str, Enum):
    """Period for charts and metrics."""
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1m"
    YEAR = "1y"
    ALL = "all"


class DashboardJob(BaseModel):
    """Job information for dashboard."""
    job_id: str
    requester_id: str
    requester_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime] = None
    payment_amount: Optional[float] = None
    payment_status: Optional[str] = None
    completion_percentage: float = 0.0
    result_summary: Optional[str] = None
    error_message: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DashboardTrade(BaseModel):
    """Trade information for dashboard."""
    trade_id: str
    market_id: str
    market_name: str
    outcome_id: str
    outcome_name: str
    direction: TradeDirection
    size: float
    price: float
    timestamp: datetime
    strategy: StrategyType
    status: str
    fee: float = 0.0
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    closed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DashboardPosition(BaseModel):
    """Position information for dashboard."""
    position_id: str
    market_id: str
    market_name: str
    outcome_id: str
    outcome_name: str
    direction: TradeDirection
    size: float
    entry_price: float
    current_price: float
    timestamp: datetime
    strategy: StrategyType
    unrealized_pnl: float = 0.0
    unrealized_pnl_percentage: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    

class DashboardStrategyConfig(BaseModel):
    """Strategy configuration for dashboard."""
    strategy_type: StrategyType
    status: StrategyStatus = StrategyStatus.ACTIVE
    enabled: bool = True
    risk_weight: float = 1.0
    max_position_size: float = 1000.0
    min_confidence: float = 0.6
    custom_params: Dict[str, Any] = Field(default_factory=dict)


class DashboardStrategyPerformance(BaseModel):
    """Strategy performance metrics for dashboard."""
    strategy_type: StrategyType
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit_loss: float = 0.0
    total_profit_loss_percentage: float = 0.0
    average_trade_duration: Optional[float] = None  # In hours
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: float = 0.0
    
    @validator("win_rate", pre=True, always=True)
    def calculate_win_rate(cls, v, values):
        """Calculate win rate from other fields."""
        total = values.get("total_trades", 0)
        winners = values.get("winning_trades", 0)
        return winners / total if total > 0 else 0.0


class DashboardAgentStatus(BaseModel):
    """Agent status information for dashboard."""
    agent_id: str
    name: str
    status: str
    uptime: float  # In seconds
    cpu_usage: float  # Percentage
    memory_usage: float  # Percentage
    disk_usage: float  # Percentage
    wallet_balance: float
    active_jobs: int
    pending_trades: int
    active_positions: int
    errors_last_hour: int = 0
    warnings_last_hour: int = 0


class DashboardAgentNetwork(BaseModel):
    """Agent network information for dashboard."""
    total_agents: int = 0
    connected_agents: int = 0
    trusted_agents: int = 0
    blocked_agents: int = 0
    collaboration_requests: int = 0
    unread_messages: int = 0
    active_collaborations: int = 0


class DashboardMetrics(BaseModel):
    """Dashboard metrics information."""
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_profit_loss: float = 0.0
    total_profit_loss_percentage: float = 0.0
    daily_profit_loss: float = 0.0
    daily_trade_volume: float = 0.0
    wallet_balance: float = 0.0
    wallet_24h_change: float = 0.0
    agent_uptime: float = 0.0  # In seconds
    
    
class TimeSeriesPoint(BaseModel):
    """Time series data point for charts."""
    timestamp: datetime
    value: float


class ChartData(BaseModel):
    """Chart data for dashboard."""
    title: str
    data: List[TimeSeriesPoint]
    period: ChartPeriod
    unit: str
    color: Optional[str] = None


class DashboardAlert(BaseModel):
    """Alert information for dashboard."""
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str
    acknowledged: bool = False
    details: Optional[Dict[str, Any]] = None


class DashboardNotification(BaseModel):
    """Notification information for dashboard."""
    notification_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    read: bool = False
    action_url: Optional[str] = None
    source: str
    icon: Optional[str] = None


class DashboardFilterParams(BaseModel):
    """Filter parameters for dashboard API."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[List[str]] = None
    strategy_types: Optional[List[StrategyType]] = None
    market_ids: Optional[List[str]] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    limit: int = 100
    offset: int = 0
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "desc"


class DashboardResponse(BaseModel):
    """Base response model for dashboard API."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class DashboardOverview(BaseModel):
    """Dashboard overview data."""
    agent_status: DashboardAgentStatus
    metrics: DashboardMetrics
    recent_trades: List[DashboardTrade] = Field(default_factory=list)
    active_positions: List[DashboardPosition] = Field(default_factory=list)
    strategy_performance: List[DashboardStrategyPerformance] = Field(default_factory=list)
    recent_jobs: List[DashboardJob] = Field(default_factory=list)
    alerts: List[DashboardAlert] = Field(default_factory=list)
    notifications: List[DashboardNotification] = Field(default_factory=list)
    agent_network: DashboardAgentNetwork
    charts: Dict[str, ChartData] = Field(default_factory=dict)
