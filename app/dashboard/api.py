"""
FastAPI API endpoints for ACP Polymarket Trading Agent Dashboard.

This module provides the API endpoints for the agent dashboard.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.dashboard.models import (
    DashboardJob,
    DashboardTrade,
    DashboardPosition,
    DashboardStrategyConfig,
    DashboardStrategyPerformance,
    DashboardAgentStatus,
    DashboardAgentNetwork,
    DashboardMetrics,
    DashboardAlert,
    DashboardNotification,
    DashboardOverview,
    DashboardResponse,
    DashboardFilterParams,
    JobStatus,
    StrategyStatus,
    ChartPeriod,
)
from app.dashboard.service import DashboardService
from app.utils.deps import get_dashboard_service


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
async def get_dashboard_overview(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get dashboard overview.
    
    Returns high-level metrics, recent activities, and status information.
    """
    try:
        overview = await dashboard_service.get_dashboard_overview()
        return DashboardResponse(
            success=True,
            data=overview
        )
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting dashboard overview: {str(e)}"
        )


@router.get("/agent/status", response_model=DashboardResponse)
async def get_agent_status(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get agent status.
    
    Returns agent status information including system metrics and resources.
    """
    try:
        status = await dashboard_service.get_agent_status()
        return DashboardResponse(
            success=True,
            data=status
        )
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting agent status: {str(e)}"
        )


@router.get("/metrics", response_model=DashboardResponse)
async def get_metrics(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get dashboard metrics.
    
    Returns metrics about trades, jobs, and performance.
    """
    try:
        metrics = await dashboard_service.get_metrics()
        return DashboardResponse(
            success=True,
            data=metrics
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting metrics: {str(e)}"
        )


@router.get("/network", response_model=DashboardResponse)
async def get_agent_network(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get agent network information.
    
    Returns information about connected agents and collaborations.
    """
    try:
        network = await dashboard_service.get_agent_network()
        return DashboardResponse(
            success=True,
            data=network
        )
    except Exception as e:
        logger.error(f"Error getting agent network: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting agent network: {str(e)}"
        )


@router.get("/trades", response_model=DashboardResponse)
async def get_trades(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[List[str]] = Query(None),
    strategy_types: Optional[List[str]] = Query(None),
    market_ids: Optional[List[str]] = Query(None),
    min_size: Optional[float] = None,
    max_size: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Optional[str] = "timestamp",
    sort_order: Optional[str] = "desc",
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get trades with filtering.
    
    Returns trades matching the specified filters.
    """
    try:
        filters = DashboardFilterParams(
            start_date=start_date,
            end_date=end_date,
            status=status,
            strategy_types=strategy_types,
            market_ids=market_ids,
            min_size=min_size,
            max_size=max_size,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        trades = await dashboard_service.get_trades(filters)
        
        return DashboardResponse(
            success=True,
            data=trades
        )
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting trades: {str(e)}"
        )


@router.get("/positions", response_model=DashboardResponse)
async def get_positions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    strategy_types: Optional[List[str]] = Query(None),
    market_ids: Optional[List[str]] = Query(None),
    min_size: Optional[float] = None,
    max_size: Optional[float] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Optional[str] = "timestamp",
    sort_order: Optional[str] = "desc",
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get positions with filtering.
    
    Returns positions matching the specified filters.
    """
    try:
        filters = DashboardFilterParams(
            start_date=start_date,
            end_date=end_date,
            strategy_types=strategy_types,
            market_ids=market_ids,
            min_size=min_size,
            max_size=max_size,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        positions = await dashboard_service.get_positions(filters)
        
        return DashboardResponse(
            success=True,
            data=positions
        )
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting positions: {str(e)}"
        )


@router.get("/jobs", response_model=DashboardResponse)
async def get_jobs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[List[str]] = Query(None),
    limit: int = 100,
    offset: int = 0,
    sort_by: Optional[str] = "updated_at",
    sort_order: Optional[str] = "desc",
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get jobs with filtering.
    
    Returns jobs matching the specified filters.
    """
    try:
        filters = DashboardFilterParams(
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        jobs = await dashboard_service.get_jobs(filters)
        
        return DashboardResponse(
            success=True,
            data=jobs
        )
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting jobs: {str(e)}"
        )


@router.get("/strategy/performance", response_model=DashboardResponse)
async def get_strategy_performance(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get strategy performance metrics.
    
    Returns performance metrics for all strategies.
    """
    try:
        performance = await dashboard_service.get_strategy_performance()
        return DashboardResponse(
            success=True,
            data=performance
        )
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting strategy performance: {str(e)}"
        )


@router.get("/strategy/configs", response_model=DashboardResponse)
async def get_strategy_configs(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get strategy configurations.
    
    Returns configuration for all strategies.
    """
    try:
        configs = await dashboard_service.get_strategy_configs()
        return DashboardResponse(
            success=True,
            data=configs
        )
    except Exception as e:
        logger.error(f"Error getting strategy configurations: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting strategy configurations: {str(e)}"
        )


@router.put("/strategy/config/{strategy_type}", response_model=DashboardResponse)
async def update_strategy_config(
    strategy_type: str,
    config_updates: Dict[str, Any],
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Update strategy configuration.
    
    Updates the configuration for a specific strategy.
    """
    try:
        success = await dashboard_service.update_strategy_config(
            strategy_type=strategy_type,
            config_updates=config_updates
        )
        
        if success:
            return DashboardResponse(
                success=True,
                message=f"Updated configuration for {strategy_type} strategy"
            )
        else:
            return DashboardResponse(
                success=False,
                message=f"Failed to update configuration for {strategy_type} strategy"
            )
    except Exception as e:
        logger.error(f"Error updating strategy configuration: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error updating strategy configuration: {str(e)}"
        )


@router.get("/alerts", response_model=DashboardResponse)
async def get_alerts(
    limit: int = 10,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get recent alerts.
    
    Returns recent alerts from the dashboard.
    """
    try:
        alerts = dashboard_service.get_alerts(limit=limit)
        return DashboardResponse(
            success=True,
            data=alerts
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge", response_model=DashboardResponse)
async def acknowledge_alert(
    alert_id: str,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Acknowledge an alert.
    
    Marks the specified alert as acknowledged.
    """
    try:
        success = dashboard_service.acknowledge_alert(alert_id)
        
        if success:
            return DashboardResponse(
                success=True,
                message=f"Acknowledged alert {alert_id}"
            )
        else:
            return DashboardResponse(
                success=False,
                message=f"Alert {alert_id} not found"
            )
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error acknowledging alert: {str(e)}"
        )


@router.get("/notifications", response_model=DashboardResponse)
async def get_notifications(
    limit: int = 10,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get recent notifications.
    
    Returns recent notifications from the dashboard.
    """
    try:
        notifications = dashboard_service.get_notifications(limit=limit)
        return DashboardResponse(
            success=True,
            data=notifications
        )
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting notifications: {str(e)}"
        )


@router.post("/notifications/{notification_id}/read", response_model=DashboardResponse)
async def mark_notification_read(
    notification_id: str,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Mark a notification as read.
    
    Marks the specified notification as read.
    """
    try:
        success = dashboard_service.mark_notification_read(notification_id)
        
        if success:
            return DashboardResponse(
                success=True,
                message=f"Marked notification {notification_id} as read"
            )
        else:
            return DashboardResponse(
                success=False,
                message=f"Notification {notification_id} not found"
            )
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error marking notification as read: {str(e)}"
        )


@router.post("/notifications/read-all", response_model=DashboardResponse)
async def mark_all_notifications_read(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Mark all notifications as read.
    
    Marks all notifications as read.
    """
    try:
        count = dashboard_service.clear_all_notifications()
        
        return DashboardResponse(
            success=True,
            message=f"Marked {count} notifications as read"
        )
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error marking all notifications as read: {str(e)}"
        )


@router.get("/charts/{period}", response_model=DashboardResponse)
async def get_charts(
    period: ChartPeriod,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get chart data.
    
    Returns chart data for the specified period.
    """
    try:
        charts = await dashboard_service.get_charts(period)
        
        return DashboardResponse(
            success=True,
            data=charts
        )
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return DashboardResponse(
            success=False,
            message=f"Error getting chart data: {str(e)}"
        )
