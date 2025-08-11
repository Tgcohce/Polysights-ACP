"""
Dependency injection utilities for ACP Polymarket Trading Agent.

This module provides dependency injection functions for FastAPI.
"""
from typing import Generator

from fastapi import Depends

from app.agent.job_lifecycle import get_job_manager
from app.agent.network import AgentNetworkManager
from app.dashboard.service import DashboardService
from app.polymarket.client import get_polymarket_client
from app.polysights.client import get_polysights_client
from app.trading.strategy_engine_main import get_trading_manager
from app.wallet.erc6551 import get_wallet


def get_dashboard_service() -> Generator[DashboardService, None, None]:
    """
    Get the dashboard service instance.
    
    Returns:
        Dashboard service
    """
    trading_manager = get_trading_manager()
    job_manager = get_job_manager()
    wallet = get_wallet()
    polymarket_client = get_polymarket_client()
    
    # Get the agent network manager
    # In a real implementation, this would be a singleton
    # For now, we create a new instance, but in production this would be retrieved
    network_manager = AgentNetworkManager(wallet)
    
    # Create dashboard service
    service = DashboardService(
        trading_manager=trading_manager,
        job_manager=job_manager,
        network_manager=network_manager,
        polymarket_client=polymarket_client,
        wallet=wallet
    )
    
    yield service
