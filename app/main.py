"""
Main application entry point for the ACP Polymarket Trading Agent.
"""
import asyncio
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from loguru import logger

from app.utils.config import config
from app.agent.profile import AGENT_CONFIG

# Initialize FastAPI app
app = FastAPI(
    title="ACP Polymarket Trading Agent",
    description="Advanced prediction market trading agent powered by Polysights analytics",
    version="0.1.0",
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.info("Starting ACP Polymarket Trading Agent")

# Global agent state
agent_state = {
    "initialized": False,
    "trading_active": False,
    "services": [],
    "jobs": {},
}


@app.on_event("startup")
async def startup_event():
    """Initialize all necessary components during startup."""
    try:
        logger.info("Initializing ACP Polymarket Trading Agent...")
        logger.info(f"Using configuration: {config.as_dict()}")
        
        # TODO: Initialize database connections
        
        # TODO: Initialize wallet and ACP registration
        
        # TODO: Initialize Polymarket client
        
        # TODO: Initialize Polysights client
        
        # TODO: Initialize trading strategies
        
        # Initialize agent services from profile configuration
        agent_state["services"] = AGENT_CONFIG["services"]
        agent_state["initialized"] = True
        
        logger.info("ACP Polymarket Trading Agent initialized successfully")
    except Exception as e:
        logger.exception(f"Failed to initialize agent: {e}")
        agent_state["initialized"] = False


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint - provides basic agent information."""
    return {
        "name": AGENT_CONFIG["name"],
        "description": AGENT_CONFIG["description"],
        "role": AGENT_CONFIG["role"],
        "status": "active" if agent_state["initialized"] else "initializing",
        "trading_active": agent_state["trading_active"],
        "services_available": len(agent_state["services"]),
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    if not agent_state["initialized"]:
        raise HTTPException(status_code=503, detail="Agent is still initializing")
    return {"status": "healthy"}


@app.get("/services")
async def get_services() -> Dict[str, Any]:
    """Get all available services offered by this agent."""
    return {
        "services": agent_state["services"],
        "total": len(agent_state["services"])
    }


# Import router modules
# This is done after app initialization to avoid circular imports
from app.agent.routes import router as agent_router
from app.trading.routes import router as trading_router
from app.ui.dashboard import router as dashboard_router

# Register routers
app.include_router(agent_router, prefix="/agent", tags=["agent"])
app.include_router(trading_router, prefix="/trading", tags=["trading"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
