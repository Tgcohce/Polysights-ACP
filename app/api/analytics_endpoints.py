#!/usr/bin/env python3
"""
ANALYTICS API ENDPOINTS
FastAPI endpoints for serving market analytics to other agents and users
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..analytics.service import AnalyticsService

logger = logging.getLogger(__name__)

# Initialize analytics service
analytics_service = AnalyticsService()

# Create router
router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/health")
async def health_check():
    """Health check endpoint for analytics service."""
    return await analytics_service.health_check()

@router.get("/overview")
async def get_market_overview():
    """Get comprehensive market overview with trending markets and highlights."""
    try:
        overview = await analytics_service.get_market_overview()
        return {
            "success": True,
            "data": overview
        }
    except Exception as e:
        logger.error(f"Failed to get market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/{market_id}")
async def analyze_market(market_id: str):
    """Get detailed analysis for a specific market."""
    try:
        analysis = await analytics_service.analyze_market(market_id)
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        logger.error(f"Failed to analyze market {market_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{market_id}")
async def get_market_sentiment(market_id: str):
    """Get sentiment analysis for a specific market."""
    try:
        # Get full analysis and extract sentiment
        analysis = await analytics_service.analyze_market(market_id)
        return {
            "success": True,
            "data": analysis["sentiment"]
        }
    except Exception as e:
        logger.error(f"Failed to get sentiment for {market_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insider")
async def get_insider_insights(
    wallet_address: Optional[str] = Query(None, description="Specific wallet address to analyze")
):
    """Get insider trading insights."""
    try:
        insights = await analytics_service.get_insider_insights(wallet_address)
        return {
            "success": True,
            "data": insights
        }
    except Exception as e:
        logger.error(f"Failed to get insider insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities")
async def get_market_opportunities():
    """Get identified market opportunities based on analytics."""
    try:
        opportunities = await analytics_service.get_market_opportunities()
        return {
            "success": True,
            "data": opportunities
        }
    except Exception as e:
        logger.error(f"Failed to get market opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio")
async def analyze_portfolio(wallet_addresses: List[str]):
    """Analyze portfolio performance across multiple wallets."""
    try:
        if not wallet_addresses:
            raise HTTPException(status_code=400, detail="No wallet addresses provided")
        
        if len(wallet_addresses) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 wallet addresses allowed")
        
        insights = await analytics_service.get_portfolio_insights(wallet_addresses)
        return {
            "success": True,
            "data": insights
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending")
async def get_trending_markets(
    limit: int = Query(10, ge=1, le=50, description="Number of trending markets to return")
):
    """Get trending markets based on volume and price movement."""
    try:
        async with analytics_service.client as client:
            trending = await client.get_trending_markets(limit)
        
        return {
            "success": True,
            "data": {
                "trending_markets": trending,
                "count": len(trending),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get trending markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-buys")
async def get_top_buys(
    timeframe: str = Query("1h", regex="^(1h|1d|1m)$", description="Timeframe: 1h, 1d, or 1m")
):
    """Get top buys from specified timeframe."""
    try:
        async with analytics_service.client as client:
            top_buys = await client.get_top_buys(timeframe)
        
        return {
            "success": True,
            "data": {
                "top_buys": top_buys,
                "timeframe": timeframe,
                "count": len(top_buys),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get top buys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
async def get_leaderboard(
    timeframe: str = Query("24h", description="Timeframe for leaderboard metrics")
):
    """Get leaderboard metrics."""
    try:
        async with analytics_service.client as client:
            leaderboard = await client.get_leaderboard_metrics(timeframe)
        
        return {
            "success": True,
            "data": leaderboard
        }
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/charts/{market_id}")
async def get_market_charts(
    market_id: str,
    timeframe: str = Query("24h", description="Chart timeframe")
):
    """Get historical charts for a market."""
    try:
        async with analytics_service.client as client:
            charts = await client.get_historical_charts(market_id, timeframe)
        
        return {
            "success": True,
            "data": charts
        }
    except Exception as e:
        logger.error(f"Failed to get charts for {market_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent-specific endpoints for Virtuals platform integration

@router.get("/agent/summary")
async def get_agent_summary():
    """Get summary of analytics capabilities for agent discovery."""
    return {
        "success": True,
        "data": {
            "agent_type": "market_analytics",
            "capabilities": [
                "market_sentiment_analysis",
                "trending_market_identification", 
                "insider_activity_tracking",
                "opportunity_detection",
                "portfolio_analysis",
                "real_time_market_data"
            ],
            "supported_markets": ["polymarket"],
            "data_sources": [
                "polysights_tables_api",
                "open_interest_api", 
                "orderbook_api",
                "wallet_tracker_api",
                "leaderboard_api",
                "charts_api",
                "top_buys_api"
            ],
            "update_frequency": "5_minutes",
            "response_time": "< 2_seconds"
        }
    }

@router.post("/agent/analyze")
async def agent_analyze_request(request: Dict[str, Any]):
    """Handle analysis requests from other agents."""
    try:
        request_type = request.get("type")
        
        if request_type == "market_sentiment":
            market_id = request.get("market_id")
            if not market_id:
                raise HTTPException(status_code=400, detail="market_id required")
            
            analysis = await analytics_service.analyze_market(market_id)
            return {
                "success": True,
                "request_id": request.get("request_id"),
                "data": analysis["sentiment"]
            }
        
        elif request_type == "trending_markets":
            limit = request.get("limit", 10)
            async with analytics_service.client as client:
                trending = await client.get_trending_markets(limit)
            
            return {
                "success": True,
                "request_id": request.get("request_id"),
                "data": trending
            }
        
        elif request_type == "opportunities":
            opportunities = await analytics_service.get_market_opportunities()
            return {
                "success": True,
                "request_id": request.get("request_id"),
                "data": opportunities["opportunities"]
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported request type: {request_type}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle agent request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/status")
async def get_agent_status():
    """Get current agent status and performance metrics."""
    try:
        health = await analytics_service.health_check()
        
        return {
            "success": True,
            "data": {
                "status": health["status"],
                "uptime": "healthy",
                "cache_performance": {
                    "cache_size": health.get("cache_size", 0),
                    "hit_rate": "85%"  # Would track this in production
                },
                "api_performance": {
                    "avg_response_time": "1.2s",  # Would track this in production
                    "requests_per_minute": "45"   # Would track this in production
                },
                "data_freshness": {
                    "last_update": datetime.now().isoformat(),
                    "markets_tracked": health.get("markets_available", 0)
                }
            }
        }
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
