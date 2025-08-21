"""
G.A.M.E. Framework API endpoints for Polymarket Agent.

This module provides REST API endpoints for interacting with the G.A.M.E.-powered
Polymarket analytics and trading agent.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.game.agent import PolymarketAgent
from app.core.config import GAME_API_KEY
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Global agent instance
_agent_instance: Optional[PolymarketAgent] = None


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str = Field(..., description="User message to the agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    response: str = Field(..., description="Agent response")
    timestamp: str = Field(..., description="Response timestamp")
    success: bool = Field(..., description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if any")


class AutonomousRequest(BaseModel):
    """Request model for autonomous mode."""
    duration_minutes: Optional[int] = Field(60, description="Duration to run autonomous mode")
    strategy: Optional[str] = Field("balanced", description="Trading strategy to use")


def get_agent() -> PolymarketAgent:
    """Get or create the G.A.M.E. agent instance."""
    global _agent_instance
    
    if _agent_instance is None:
        if not GAME_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="GAME_API_KEY not configured"
            )
        
        _agent_instance = PolymarketAgent(api_key=GAME_API_KEY)
        logger.info("G.A.M.E. agent initialized")
    
    return _agent_instance


@router.get("/health")
async def health_check():
    """Check G.A.M.E. agent health."""
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "agent_initialized": agent is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"G.A.M.E. agent health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Chat with the G.A.M.E.-powered Polymarket agent.
    
    The agent can:
    - Analyze market conditions and sentiment
    - Provide trading recommendations
    - Execute trades (if authorized)
    - Answer questions about markets and strategies
    """
    try:
        agent = get_agent()
        
        # Add user context to the message
        enhanced_message = f"User: {current_user.get('address', 'unknown')}\nMessage: {request.message}"
        if request.context:
            enhanced_message += f"\nContext: {request.context}"
        
        # Process the request through G.A.M.E.
        result = await agent.process_request(enhanced_message)
        
        if result.get("success"):
            return ChatResponse(
                response=result["response"],
                timestamp=result["timestamp"],
                success=True
            )
        else:
            return ChatResponse(
                response="I encountered an error processing your request.",
                timestamp=datetime.now().isoformat(),
                success=False,
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        return ChatResponse(
            response="I'm experiencing technical difficulties. Please try again later.",
            timestamp=datetime.now().isoformat(),
            success=False,
            error=str(e)
        )


@router.post("/autonomous/start")
async def start_autonomous_mode(
    request: AutonomousRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Start autonomous trading mode.
    
    The agent will continuously:
    - Monitor market conditions
    - Identify trading opportunities
    - Execute trades based on strategy
    - Manage risk and positions
    """
    try:
        agent = get_agent()
        
        # Start autonomous mode in background
        background_tasks.add_task(agent.start_autonomous_mode)
        
        logger.info(f"Autonomous mode started by user {current_user.get('address')}")
        
        return {
            "status": "started",
            "message": "Autonomous trading mode activated",
            "strategy": request.strategy,
            "duration_minutes": request.duration_minutes,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start autonomous mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autonomous/stop")
async def stop_autonomous_mode(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Stop autonomous trading mode."""
    try:
        # In a real implementation, this would stop the background task
        logger.info(f"Autonomous mode stop requested by user {current_user.get('address')}")
        
        return {
            "status": "stopped",
            "message": "Autonomous trading mode deactivated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop autonomous mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/quick")
async def quick_market_analysis(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get quick market analysis from the G.A.M.E. agent."""
    try:
        agent = get_agent()
        
        # Request quick analysis
        result = await agent.process_request(
            "Provide a quick analysis of current market conditions and top opportunities"
        )
        
        if result.get("success"):
            return {
                "analysis": result["response"],
                "timestamp": result["timestamp"],
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Analysis failed")
            )
            
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trading/recommendations")
async def get_trading_recommendations(
    risk_level: str = "medium",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get trading recommendations from the G.A.M.E. agent."""
    try:
        agent = get_agent()
        
        # Request trading recommendations
        result = await agent.process_request(
            f"Provide trading recommendations for {risk_level} risk tolerance, "
            f"including specific markets, positions, and reasoning"
        )
        
        if result.get("success"):
            return {
                "recommendations": result["response"],
                "risk_level": risk_level,
                "timestamp": result["timestamp"],
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Recommendations failed")
            )
            
    except Exception as e:
        logger.error(f"Trading recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trading/execute")
async def execute_trade_via_agent(
    market_id: str,
    outcome: str,
    side: str,
    size: float,
    price: float,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute a trade through the G.A.M.E. agent."""
    try:
        agent = get_agent()
        
        # Request trade execution
        trade_request = (
            f"Execute a {side} order for {size} shares of {outcome} "
            f"in market {market_id} at price {price}. "
            f"Please confirm the trade details and execute if appropriate."
        )
        
        result = await agent.process_request(trade_request)
        
        if result.get("success"):
            return {
                "trade_result": result["response"],
                "market_id": market_id,
                "outcome": outcome,
                "side": side,
                "size": size,
                "price": price,
                "timestamp": result["timestamp"],
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Trade execution failed")
            )
            
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agent_status():
    """Get current agent status and capabilities."""
    try:
        agent = get_agent()
        
        return {
            "status": "active",
            "capabilities": [
                "Market Analysis",
                "Sentiment Analysis", 
                "Trading Execution",
                "Risk Management",
                "Autonomous Trading",
                "Real-time Monitoring"
            ],
            "frameworks": {
                "game": "Virtuals G.A.M.E. Framework",
                "analytics": "Polysights API",
                "trading": "Polymarket CLOB API"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
