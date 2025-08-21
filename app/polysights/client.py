"""
Polysights Analytics Client - Clean implementation without mock data.

This client provides real-time access to Polysights APIs for market analytics,
trading insights, and prediction market data.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class PolysightsClient:
    """
    Client for accessing Polysights analytics APIs.
    
    Provides access to:
    - Market insights and analytics
    - Trader performance metrics
    - Smart money activity tracking
    - Market efficiency analysis
    - Sentiment analysis
    - Historical accuracy data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Polysights client.
        
        Args:
            api_key: Polysights API key for authentication
        """
        self.api_key = api_key
        self.base_url = "https://api.polysights.com/v1"
        
        if not self.api_key:
            logger.warning("No API key provided - client will fail on real requests")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ACP-Polymarket-Agent/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request to Polysights.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters (for GET requests)
            data: Request data (for POST/PUT requests)
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            if not self.api_key:
                logger.error("API key not set - cannot fetch real data")
                raise ValueError("Polysights API key is required for live data")
                
            full_url = f"{self.base_url}{endpoint}"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(
                        full_url, 
                        headers=headers, 
                        params=params
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"API request failed: {response.status} - {error_text}"
                            )
                            return {"error": error_text, "status": response.status}
                elif method.upper() == "POST":
                    async with session.post(
                        full_url, 
                        headers=headers, 
                        json=data
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"API request failed: {response.status} - {error_text}"
                            )
                            return {"error": error_text, "status": response.status}
                else:
                    logger.error(f"Unsupported method: {method}")
                    return {"error": f"Unsupported method: {method}"}
                    
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {"error": str(e)}
    
    async def get_market_insights(self, market_id: str) -> Dict[str, Any]:
        """Get comprehensive market insights for a specific market."""
        return await self._make_request("GET", f"/market-insights/{market_id}")
    
    async def get_trader_performance(self, trader_address: str) -> Dict[str, Any]:
        """Get performance metrics for a specific trader."""
        return await self._make_request("GET", f"/trader-performance/{trader_address}")
    
    async def get_smart_money_activity(self) -> Dict[str, Any]:
        """Get smart money and whale activity data."""
        return await self._make_request("GET", "/smart-money")
    
    async def get_market_efficiency_metrics(self, market_id: str) -> Dict[str, Any]:
        """Get market efficiency and arbitrage opportunity data."""
        return await self._make_request("GET", f"/market-efficiency/{market_id}")
    
    async def get_sentiment_analysis(self, market_id: str) -> Dict[str, Any]:
        """Get sentiment analysis for a specific market."""
        return await self._make_request("GET", f"/sentiment/{market_id}")
    
    async def get_historical_accuracy(self, market_type: str) -> Dict[str, Any]:
        """Get historical prediction accuracy data by market type."""
        return await self._make_request("GET", f"/historical-accuracy/{market_type}")
    
    async def get_all_markets(self, limit: int = 50) -> Dict[str, Any]:
        """Get all available markets with basic info."""
        return await self._make_request("GET", "/markets", params={"limit": limit})
    
    async def get_top_markets(self, timeframe: str = "24h") -> Dict[str, Any]:
        """Get top performing markets by volume or activity."""
        return await self._make_request("GET", "/top-markets", params={"timeframe": timeframe})
    
    async def search_markets(self, query: str) -> Dict[str, Any]:
        """Search markets by keyword or category."""
        return await self._make_request("GET", "/search", params={"q": query})
