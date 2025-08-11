"""
Dashboard service for ACP Polymarket Trading Agent.

This module provides service functions for the dashboard API.
"""
import asyncio
from datetime import datetime, timedelta
import psutil
import time
from typing import Dict, List, Any, Optional, Set, Tuple

from loguru import logger

from app.agent.job_lifecycle import JobLifecycleManager
from app.agent.network import AgentNetworkManager
from app.dashboard.models import (
    DashboardJob,
    DashboardTrade,
    DashboardPosition,
    DashboardStrategyConfig,
    DashboardStrategyPerformance,
    DashboardAgentStatus,
    DashboardAgentNetwork,
    DashboardMetrics,
    TimeSeriesPoint,
    ChartData,
    DashboardAlert,
    DashboardNotification,
    DashboardOverview,
    DashboardResponse,
    DashboardFilterParams,
    JobStatus,
    StrategyStatus,
    ChartPeriod,
)
from app.polymarket.client import PolymarketClient
from app.trading.strategy_engine_main import TradingStrategyManager
from app.wallet.erc6551 import SmartWallet
from app.utils.config import config


class DashboardService:
    """
    Service for the agent dashboard.
    
    This class provides functionality for the dashboard API.
    """
    
    def __init__(
        self,
        trading_manager: TradingStrategyManager,
        job_manager: JobLifecycleManager,
        network_manager: AgentNetworkManager,
        polymarket_client: PolymarketClient,
        wallet: SmartWallet
    ):
        """
        Initialize the dashboard service.
        
        Args:
            trading_manager: Trading strategy manager
            job_manager: Job lifecycle manager
            network_manager: Agent network manager
            polymarket_client: Polymarket client
            wallet: Smart wallet
        """
        self.trading_manager = trading_manager
        self.job_manager = job_manager
        self.network_manager = network_manager
        self.polymarket_client = polymarket_client
        self.wallet = wallet
        
        self.start_time = time.time()
        
        # In-memory storage for dashboard data
        # In a production system, this would be stored in a database
        self.alerts: List[DashboardAlert] = []
        self.notifications: List[DashboardNotification] = []
        
        # Metrics history for charts
        self.metrics_history: Dict[str, List[TimeSeriesPoint]] = {
            "pnl": [],
            "wallet_balance": [],
            "trade_volume": [],
            "active_positions": []
        }
        
        logger.info("Initialized DashboardService")
    
    async def get_dashboard_overview(self) -> DashboardOverview:
        """
        Get dashboard overview.
        
        Returns:
            Dashboard overview data
        """
        # Get all components in parallel
        agent_status, metrics, agent_network = await asyncio.gather(
            self.get_agent_status(),
            self.get_metrics(),
            self.get_agent_network()
        )
        
        # Get recent trades and positions
        recent_trades = await self.get_trades(
            DashboardFilterParams(limit=5, sort_by="timestamp", sort_order="desc")
        )
        
        active_positions = await self.get_positions(
            DashboardFilterParams(limit=5, sort_by="timestamp", sort_order="desc")
        )
        
        # Get recent jobs
        recent_jobs = await self.get_jobs(
            DashboardFilterParams(limit=5, sort_by="updated_at", sort_order="desc")
        )
        
        # Get strategy performance
        strategy_performance = await self.get_strategy_performance()
        
        # Get alerts and notifications
        alerts = self.get_alerts(limit=5)
        notifications = self.get_notifications(limit=5)
        
        # Get charts
        charts = await self.get_charts(ChartPeriod.DAY)
        
        return DashboardOverview(
            agent_status=agent_status,
            metrics=metrics,
            recent_trades=recent_trades,
            active_positions=active_positions,
            strategy_performance=strategy_performance,
            recent_jobs=recent_jobs,
            alerts=alerts,
            notifications=notifications,
            agent_network=agent_network,
            charts=charts
        )
    
    async def get_agent_status(self) -> DashboardAgentStatus:
        """
        Get agent status.
        
        Returns:
            Agent status information
        """
        # Get system metrics
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        disk = psutil.disk_usage("/")
        disk_usage = disk.percent
        
        # Get wallet balance
        wallet_balance = await self.wallet.get_balance()
        
        # Get job and trade counts
        active_jobs = await self.count_active_jobs()
        pending_trades = 0  # Would come from strategy engine
        active_positions = len(self.trading_manager.get_active_positions())
        
        # Calculate uptime
        uptime = time.time() - self.start_time
        
        # Count recent errors and warnings (would come from log analysis)
        errors_last_hour = 0
        warnings_last_hour = 0
        
        return DashboardAgentStatus(
            agent_id=config.agent.agent_id,
            name=config.agent.agent_name,
            status="online",
            uptime=uptime,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            wallet_balance=wallet_balance,
            active_jobs=active_jobs,
            pending_trades=pending_trades,
            active_positions=active_positions,
            errors_last_hour=errors_last_hour,
            warnings_last_hour=warnings_last_hour
        )
    
    async def get_metrics(self) -> DashboardMetrics:
        """
        Get dashboard metrics.
        
        Returns:
            Dashboard metrics information
        """
        # Get performance metrics from trading manager
        performance_metrics = self.trading_manager.get_performance_metrics()
        
        # Get wallet balance and change
        wallet_balance = await self.wallet.get_balance()
        wallet_24h_change = 0.0  # Would come from historical tracking
        
        # Count jobs
        total_jobs = await self.count_total_jobs()
        completed_jobs = await self.count_jobs_by_status(JobStatus.COMPLETED)
        failed_jobs = await self.count_jobs_by_status([JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED])
        
        # Calculate uptime
        uptime = time.time() - self.start_time
        
        return DashboardMetrics(
            total_trades=performance_metrics.get("total_trades", 0),
            successful_trades=performance_metrics.get("successful_trades", 0),
            failed_trades=performance_metrics.get("failed_trades", 0),
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            total_profit_loss=performance_metrics.get("total_pnl", 0.0),
            total_profit_loss_percentage=performance_metrics.get("total_pnl_percentage", 0.0),
            daily_profit_loss=performance_metrics.get("daily_pnl", 0.0),
            daily_trade_volume=performance_metrics.get("daily_volume", 0.0),
            wallet_balance=wallet_balance,
            wallet_24h_change=wallet_24h_change,
            agent_uptime=uptime
        )
    
    async def get_agent_network(self) -> DashboardAgentNetwork:
        """
        Get agent network information.
        
        Returns:
            Agent network information
        """
        # Get network information from network manager
        known_agents = len(self.network_manager.known_agents)
        trusted_agents = len(self.network_manager.trusted_agents)
        blocked_agents = len(self.network_manager.blocked_agents)
        
        # Count connected agents (those active recently)
        connected_agents = 0
        for agent_id, profile in self.network_manager.known_agents.items():
            if profile.last_active and (datetime.now() - profile.last_active).total_seconds() < 3600:
                connected_agents += 1
        
        # Count collaboration requests and active collaborations
        collaboration_requests = 0
        active_collaborations = 0
        for req_id, collab in self.network_manager.active_collaborations.items():
            if collab["status"] == "pending":
                collaboration_requests += 1
            elif collab["status"] == "accepted":
                active_collaborations += 1
        
        # Count unread messages
        unread_messages = len(self.network_manager.unread_messages)
        
        return DashboardAgentNetwork(
            total_agents=known_agents,
            connected_agents=connected_agents,
            trusted_agents=trusted_agents,
            blocked_agents=blocked_agents,
            collaboration_requests=collaboration_requests,
            unread_messages=unread_messages,
            active_collaborations=active_collaborations
        )
    
    async def get_trades(
        self,
        filters: DashboardFilterParams
    ) -> List[DashboardTrade]:
        """
        Get trades with filtering.
        
        Args:
            filters: Filter parameters
            
        Returns:
            List of trades matching filters
        """
        # This would query the database in a real implementation
        # For now, return empty list as a placeholder
        return []
    
    async def get_positions(
        self,
        filters: DashboardFilterParams
    ) -> List[DashboardPosition]:
        """
        Get positions with filtering.
        
        Args:
            filters: Filter parameters
            
        Returns:
            List of positions matching filters
        """
        # Get positions from trading manager
        positions = self.trading_manager.get_active_positions()
        
        # Apply filters
        filtered_positions = []
        for position in positions:
            # Convert to dashboard model
            dashboard_position = DashboardPosition(
                position_id=position.get("position_id", ""),
                market_id=position.get("market_id", ""),
                market_name=position.get("market_name", ""),
                outcome_id=position.get("outcome_id", ""),
                outcome_name=position.get("outcome_name", ""),
                direction=position.get("direction"),
                size=position.get("size", 0.0),
                entry_price=position.get("price", 0.0),
                current_price=position.get("current_price", 0.0),
                timestamp=position.get("timestamp", datetime.now()),
                strategy=position.get("strategy"),
                unrealized_pnl=position.get("unrealized_pnl", 0.0),
                unrealized_pnl_percentage=position.get("unrealized_pnl_percentage", 0.0),
                stop_loss=position.get("stop_loss"),
                take_profit=position.get("take_profit")
            )
            
            filtered_positions.append(dashboard_position)
        
        # Apply limit and offset
        start = filters.offset
        end = start + filters.limit
        return filtered_positions[start:end]
    
    async def get_jobs(
        self,
        filters: DashboardFilterParams
    ) -> List[DashboardJob]:
        """
        Get jobs with filtering.
        
        Args:
            filters: Filter parameters
            
        Returns:
            List of jobs matching filters
        """
        # This would query the database in a real implementation
        # For now, return empty list as a placeholder
        return []
    
    async def get_strategy_performance(self) -> List[DashboardStrategyPerformance]:
        """
        Get strategy performance metrics.
        
        Returns:
            List of strategy performance metrics
        """
        # Get performance metrics from trading manager
        performance_metrics = self.trading_manager.get_performance_metrics()
        
        # Extract strategy-specific metrics
        strategy_metrics = performance_metrics.get("strategies", {})
        
        # Convert to dashboard models
        performance_list = []
        for strategy_type, metrics in strategy_metrics.items():
            performance = DashboardStrategyPerformance(
                strategy_type=strategy_type,
                total_trades=metrics.get("total_trades", 0),
                winning_trades=metrics.get("winning_trades", 0),
                losing_trades=metrics.get("losing_trades", 0),
                total_profit_loss=metrics.get("total_pnl", 0.0),
                total_profit_loss_percentage=metrics.get("total_pnl_percentage", 0.0),
                average_trade_duration=metrics.get("avg_duration"),
                sharpe_ratio=metrics.get("sharpe_ratio"),
                max_drawdown=metrics.get("max_drawdown")
            )
            
            performance_list.append(performance)
        
        return performance_list
    
    def get_alerts(self, limit: int = 10) -> List[DashboardAlert]:
        """
        Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        # Sort by timestamp (newest first)
        sorted_alerts = sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        return sorted_alerts[:limit]
    
    def get_notifications(self, limit: int = 10) -> List[DashboardNotification]:
        """
        Get recent notifications.
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of recent notifications
        """
        # Sort by timestamp (newest first)
        sorted_notifications = sorted(self.notifications, key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        return sorted_notifications[:limit]
    
    async def get_charts(self, period: ChartPeriod) -> Dict[str, ChartData]:
        """
        Get chart data.
        
        Args:
            period: Time period for charts
            
        Returns:
            Dictionary of chart data
        """
        # Calculate start time based on period
        now = datetime.now()
        if period == ChartPeriod.HOUR:
            start_time = now - timedelta(hours=1)
        elif period == ChartPeriod.DAY:
            start_time = now - timedelta(days=1)
        elif period == ChartPeriod.WEEK:
            start_time = now - timedelta(weeks=1)
        elif period == ChartPeriod.MONTH:
            start_time = now - timedelta(days=30)
        elif period == ChartPeriod.YEAR:
            start_time = now - timedelta(days=365)
        else:  # ChartPeriod.ALL
            start_time = datetime.min
        
        # Filter metrics history by time period
        filtered_metrics = {}
        for metric_name, data_points in self.metrics_history.items():
            filtered_metrics[metric_name] = [
                point for point in data_points if point.timestamp >= start_time
            ]
        
        # Create chart data
        charts = {}
        
        # P&L chart
        if filtered_metrics.get("pnl"):
            charts["pnl"] = ChartData(
                title="Profit/Loss",
                data=filtered_metrics["pnl"],
                period=period,
                unit="$",
                color="#4CAF50"  # Green
            )
        
        # Wallet balance chart
        if filtered_metrics.get("wallet_balance"):
            charts["wallet_balance"] = ChartData(
                title="Wallet Balance",
                data=filtered_metrics["wallet_balance"],
                period=period,
                unit="$",
                color="#2196F3"  # Blue
            )
        
        # Trade volume chart
        if filtered_metrics.get("trade_volume"):
            charts["trade_volume"] = ChartData(
                title="Trade Volume",
                data=filtered_metrics["trade_volume"],
                period=period,
                unit="$",
                color="#9C27B0"  # Purple
            )
        
        # Active positions chart
        if filtered_metrics.get("active_positions"):
            charts["active_positions"] = ChartData(
                title="Active Positions",
                data=filtered_metrics["active_positions"],
                period=period,
                unit="count",
                color="#FF9800"  # Orange
            )
        
        return charts
    
    def add_alert(self, alert: DashboardAlert):
        """
        Add an alert to the dashboard.
        
        Args:
            alert: Alert to add
        """
        self.alerts.append(alert)
        
        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:100]
    
    def add_notification(self, notification: DashboardNotification):
        """
        Add a notification to the dashboard.
        
        Args:
            notification: Notification to add
        """
        self.notifications.append(notification)
        
        # Keep only recent notifications (last 100)
        if len(self.notifications) > 100:
            self.notifications = sorted(self.notifications, key=lambda x: x.timestamp, reverse=True)[:100]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            
        Returns:
            True if alert was acknowledged, False otherwise
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        
        return False
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification to mark
            
        Returns:
            True if notification was marked, False otherwise
        """
        for notification in self.notifications:
            if notification.notification_id == notification_id:
                notification.read = True
                return True
        
        return False
    
    def clear_all_notifications(self) -> int:
        """
        Mark all notifications as read.
        
        Returns:
            Number of notifications marked as read
        """
        count = 0
        for notification in self.notifications:
            if not notification.read:
                notification.read = True
                count += 1
        
        return count
    
    async def update_strategy_config(
        self,
        strategy_type: str,
        config_updates: Dict[str, Any]
    ) -> bool:
        """
        Update strategy configuration.
        
        Args:
            strategy_type: Type of strategy to update
            config_updates: Configuration updates
            
        Returns:
            True if configuration was updated, False otherwise
        """
        # This would update the strategy configuration
        # For now, return True as a placeholder
        return True
    
    async def add_metric_datapoint(self, metric_name: str, value: float):
        """
        Add a datapoint to metric history.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        if metric_name in self.metrics_history:
            datapoint = TimeSeriesPoint(timestamp=datetime.now(), value=value)
            self.metrics_history[metric_name].append(datapoint)
            
            # Keep only recent datapoints (last 1000)
            if len(self.metrics_history[metric_name]) > 1000:
                self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]
    
    async def count_active_jobs(self) -> int:
        """
        Count active jobs.
        
        Returns:
            Number of active jobs
        """
        # This would query the job manager or database
        # For now, return 0 as a placeholder
        return 0
    
    async def count_total_jobs(self) -> int:
        """
        Count total jobs.
        
        Returns:
            Total number of jobs
        """
        # This would query the job manager or database
        # For now, return 0 as a placeholder
        return 0
    
    async def count_jobs_by_status(self, status: JobStatus | List[JobStatus]) -> int:
        """
        Count jobs by status.
        
        Args:
            status: Job status or list of statuses
            
        Returns:
            Number of jobs with the specified status
        """
        # This would query the job manager or database
        # For now, return 0 as a placeholder
        return 0
    
    async def get_strategy_configs(self) -> List[DashboardStrategyConfig]:
        """
        Get strategy configurations.
        
        Returns:
            List of strategy configurations
        """
        # This would get the current strategy configurations
        # For now, return an empty list as a placeholder
        return []
