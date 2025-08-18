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
        
        # Initialize database connections
        from app.db.database import init_db
        from app.db.repository import JobRepository, TradeRepository, PositionRepository, AnalysisCacheRepository
        
        logger.info("Initializing database connections...")
        await init_db()
        
        # Initialize repositories
        agent_state["repositories"] = {
            "jobs": JobRepository(),
            "trades": TradeRepository(),
            "positions": PositionRepository(),
            "analysis": AnalysisCacheRepository()
        }
        logger.info("Database connections initialized successfully")
        
        # Initialize wallet and ACP registration
        if config.wallet.enabled:
            logger.info("Initializing wallet...")
            from app.wallet.erc6551 import SmartWallet
            agent_state["wallet"] = SmartWallet()
            logger.info(f"Wallet initialized with address: {agent_state['wallet'].address}")
            
            # Register with ACP
            from app.agent.registration import register_with_acp
            success = await register_with_acp(agent_state["wallet"])
            if success:
                logger.info("Successfully registered with ACP network")
            else:
                logger.warning("Failed to register with ACP network - continuing in offline mode")
        else:
            logger.warning("Wallet functionality disabled in configuration")
        
        # Initialize Polymarket client
        logger.info("Initializing Polymarket client...")
        from app.polymarket.client import PolymarketClient
        wallet = agent_state.get("wallet", None)
        agent_state["polymarket_client"] = PolymarketClient(wallet=wallet)
        success = await agent_state["polymarket_client"].authenticate()
        if success:
            logger.info("Polymarket client authenticated successfully")
        else:
            logger.warning("Polymarket client authentication failed - some API features may be limited")
        
        # Initialize Polysights client
        logger.info("Initializing Polysights client...")
        from app.polysights.client import PolysightsClient
        agent_state["polysights_client"] = PolysightsClient()
        await agent_state["polysights_client"].initialize()
        logger.info("Polysights client initialized")
        
        # Initialize trading strategies
        logger.info("Initializing trading strategies...")
        from app.trading.strategy_engine import TradingStrategyEngine
        agent_state["strategy_engine"] = TradingStrategyEngine(
            polymarket_client=agent_state["polymarket_client"],
            polysights_client=agent_state["polysights_client"],
            wallet=agent_state.get("wallet", None),
            trade_repository=agent_state["repositories"]["trades"],
            position_repository=agent_state["repositories"]["positions"],
            analysis_repository=agent_state["repositories"]["analysis"]
        )
        await agent_state["strategy_engine"].initialize()
        logger.info("Trading strategies initialized successfully")
        
        # Initialize Virtuals Protocol client
        if agent_state.get("wallet") and config.get("VIRTUALS_ENABLED", True):
            logger.info("Initializing Virtuals Protocol client...")
            from app.virtuals.client import VirtualsClient
            agent_state["virtuals_client"] = VirtualsClient(wallet=agent_state["wallet"])
            
            # Register with Virtuals Protocol
            registration_success = await agent_state["virtuals_client"].register_agent()
            if registration_success:
                logger.info("Successfully registered with Virtuals Protocol")
            else:
                logger.warning("Failed to register with Virtuals Protocol - continuing without it")
        else:
            logger.info("Virtuals Protocol integration disabled")
        
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
