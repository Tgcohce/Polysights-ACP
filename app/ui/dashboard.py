"""
Dashboard UI components for ACP Polymarket Trading Agent.
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def dashboard_home() -> Dict[str, Any]:
    """Dashboard home page."""
    return {
        "status": "active",
        "message": "ACP Polymarket Trading Agent Dashboard"
    }

@router.get("/status")
async def dashboard_status() -> Dict[str, Any]:
    """Get dashboard status."""
    return {
        "agent_status": "running",
        "active_jobs": 0,
        "total_trades": 0,
        "uptime": "running"
    }
