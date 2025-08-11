"""
Polysights analytics platform client implementation.

This module provides a client for interacting with the Polysights analytics platform,
allowing access to market insights, trader performance data, and other prediction
market analytics.
"""
import json
from typing import Dict, Any, List, Optional, Union

import aiohttp
from loguru import logger

from app.utils.config import config


class PolysightsClient:
    """
    Integration with Polysights analytics platform.
    
    This class provides methods to access Polysights analytics data including:
    - Market insights
    - Trader performance
    - Smart money activity
    - Market efficiency metrics
    - Sentiment analysis
    - Historical accuracy
    """
    
    def __init__(self):
        """Initialize the Polysights client."""
        self.api_key = config.polysights.api_key
        self.base_url = config.polysights.base_url
        logger.info(f"Initialized Polysights client with base URL: {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict[str, str]: Headers dictionary
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Polysights API.
        
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
                logger.warning("API key not set, using mock data")
                return self._get_mock_data(endpoint)
                
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
                                f"API error ({response.status}): {error_text}"
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
                                f"API error ({response.status}): {error_text}"
                            )
                            return {"error": error_text, "status": response.status}
                else:
                    logger.error(f"Unsupported method: {method}")
                    return {"error": f"Unsupported method: {method}"}
                    
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {"error": str(e)}
    
    def _get_mock_data(self, endpoint: str) -> Dict[str, Any]:
        """
        Get mock data for development when API key is not available.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Dict[str, Any]: Mock data
        """
        # Extract the resource type from the endpoint
        parts = endpoint.strip("/").split("/")
        resource_type = parts[-1] if len(parts) > 0 else "unknown"
        
        # Generate mock data based on resource type
        if "market-insights" in endpoint:
            market_id = parts[-2] if len(parts) > 1 else "123"
            return self._mock_market_insights(market_id)
        elif "trader-performance" in endpoint:
            trader_address = parts[-2] if len(parts) > 1 else "0x123"
            return self._mock_trader_performance(trader_address)
        elif "smart-money" in endpoint:
            return self._mock_smart_money_activity()
        elif "market-efficiency" in endpoint:
            market_id = parts[-2] if len(parts) > 1 else "123"
            return self._mock_market_efficiency_metrics(market_id)
        elif "sentiment" in endpoint:
            market_id = parts[-2] if len(parts) > 1 else "123"
            return self._mock_sentiment_analysis(market_id)
        elif "historical-accuracy" in endpoint:
            market_type = parts[-2] if len(parts) > 1 else "politics"
            return self._mock_historical_accuracy(market_type)
        else:
            return {"error": f"No mock data available for endpoint: {endpoint}"}
    
    def _mock_market_insights(self, market_id: str) -> Dict[str, Any]:
        """Generate mock market insights data."""
        return {
            "market_id": market_id,
            "insights": {
                "implied_probability": 0.65,
                "analyst_consensus": 0.72,
                "volume_24h": 45000,
                "liquidity_depth": {
                    "buy_side": 12500,
                    "sell_side": 9800
                },
                "price_movement": {
                    "1h": 0.02,
                    "24h": -0.05,
                    "7d": 0.15
                },
                "volatility": {
                    "1h": 0.03,
                    "24h": 0.08,
                    "7d": 0.12
                },
                "key_events": [
                    {
                        "timestamp": "2025-08-10T14:30:00Z",
                        "event": "Major news release",
                        "impact": "high",
                        "price_change": 0.08
                    },
                    {
                        "timestamp": "2025-08-09T18:15:00Z",
                        "event": "Large trader position",
                        "impact": "medium",
                        "price_change": 0.03
                    }
                ]
            },
            "forecast": {
                "short_term": {
                    "price": 0.68,
                    "confidence": 0.75,
                    "horizon": "24h"
                },
                "medium_term": {
                    "price": 0.72,
                    "confidence": 0.60,
                    "horizon": "7d"
                }
            },
            "related_markets": [
                {
                    "market_id": "market_456",
                    "correlation": 0.82,
                    "relationship": "positive"
                },
                {
                    "market_id": "market_789",
                    "correlation": -0.65,
                    "relationship": "negative"
                }
            ]
        }
    
    def _mock_trader_performance(self, trader_address: str) -> Dict[str, Any]:
        """Generate mock trader performance data."""
        return {
            "trader": {
                "address": trader_address,
                "first_trade": "2024-12-01T00:00:00Z",
                "total_trades": 235,
                "total_volume": 125000,
                "roi": 0.18,
                "sharpe_ratio": 1.35,
                "win_rate": 0.68
            },
            "categories": {
                "politics": {
                    "trade_count": 85,
                    "roi": 0.22,
                    "win_rate": 0.75
                },
                "sports": {
                    "trade_count": 120,
                    "roi": 0.14,
                    "win_rate": 0.62
                },
                "crypto": {
                    "trade_count": 30,
                    "roi": 0.25,
                    "win_rate": 0.70
                }
            },
            "recent_activity": [
                {
                    "timestamp": "2025-08-10T10:15:00Z",
                    "market_id": "market_123",
                    "side": "buy",
                    "size": 1000,
                    "price": 0.65
                },
                {
                    "timestamp": "2025-08-09T14:30:00Z",
                    "market_id": "market_456",
                    "side": "sell",
                    "size": 1500,
                    "price": 0.78
                }
            ],
            "performance_over_time": {
                "daily": [
                    {"date": "2025-08-10", "roi": 0.05},
                    {"date": "2025-08-09", "roi": -0.02},
                    {"date": "2025-08-08", "roi": 0.03}
                ],
                "weekly": [
                    {"week": "2025-W32", "roi": 0.08},
                    {"week": "2025-W31", "roi": 0.12},
                    {"week": "2025-W30", "roi": -0.05}
                ],
                "monthly": [
                    {"month": "2025-08", "roi": 0.15},
                    {"month": "2025-07", "roi": 0.10},
                    {"month": "2025-06", "roi": 0.20}
                ]
            }
        }
    
    def _mock_smart_money_activity(self) -> Dict[str, Any]:
        """Generate mock smart money activity data."""
        return {
            "top_traders": [
                {
                    "address": "0xabcd1234",
                    "roi": 0.35,
                    "trade_count": 450,
                    "recent_markets": ["market_123", "market_456"]
                },
                {
                    "address": "0xefgh5678",
                    "roi": 0.28,
                    "trade_count": 320,
                    "recent_markets": ["market_789", "market_123"]
                }
            ],
            "recent_activity": [
                {
                    "timestamp": "2025-08-10T12:00:00Z",
                    "trader": "0xabcd1234",
                    "market_id": "market_123",
                    "side": "buy",
                    "size": 5000,
                    "price": 0.63
                },
                {
                    "timestamp": "2025-08-10T10:30:00Z",
                    "trader": "0xefgh5678",
                    "market_id": "market_789",
                    "side": "sell",
                    "size": 8000,
                    "price": 0.82
                }
            ],
            "active_markets": [
                {
                    "market_id": "market_123",
                    "smart_money_flow": 12000,
                    "flow_direction": "positive",
                    "trader_count": 5
                },
                {
                    "market_id": "market_456",
                    "smart_money_flow": -8000,
                    "flow_direction": "negative",
                    "trader_count": 3
                }
            ]
        }
    
    def _mock_market_efficiency_metrics(self, market_id: str) -> Dict[str, Any]:
        """Generate mock market efficiency metrics."""
        return {
            "market_id": market_id,
            "efficiency_score": 0.85,
            "metrics": {
                "bid_ask_spread": 0.02,
                "price_impact": {
                    "small_order": 0.005,
                    "medium_order": 0.015,
                    "large_order": 0.045
                },
                "liquidity_depth": {
                    "1%": 10000,
                    "2%": 25000,
                    "5%": 60000
                },
                "price_discovery": 0.92,
                "information_incorporation": 0.88
            },
            "historical": [
                {"timestamp": "2025-08-10T00:00:00Z", "efficiency_score": 0.85},
                {"timestamp": "2025-08-09T00:00:00Z", "efficiency_score": 0.82},
                {"timestamp": "2025-08-08T00:00:00Z", "efficiency_score": 0.79}
            ],
            "arbitrage_opportunities": {
                "frequency": "low",
                "last_detected": "2025-08-08T14:25:00Z",
                "average_profit": 0.01
            },
            "comparison": {
                "similar_markets": 0.82,
                "all_markets": 0.76
            }
        }
    
    def _mock_sentiment_analysis(self, market_id: str) -> Dict[str, Any]:
        """Generate mock sentiment analysis data."""
        return {
            "market_id": market_id,
            "overall_sentiment": {
                "score": 0.65,  # -1.0 to 1.0, positive is bullish
                "confidence": 0.82,
                "sources_analyzed": 120
            },
            "sources": {
                "social_media": {
                    "sentiment": 0.72,
                    "volume": "high",
                    "trending": True,
                    "platforms": {
                        "twitter": 0.75,
                        "reddit": 0.68,
                        "discord": 0.65
                    }
                },
                "news": {
                    "sentiment": 0.58,
                    "volume": "medium",
                    "trending": False,
                    "top_sources": ["Bloomberg", "Reuters", "CNBC"]
                },
                "expert_opinions": {
                    "sentiment": 0.62,
                    "count": 15,
                    "consensus": "moderate agreement"
                }
            },
            "topics": [
                {
                    "name": "regulation",
                    "sentiment": 0.45,
                    "frequency": 0.25
                },
                {
                    "name": "technology",
                    "sentiment": 0.82,
                    "frequency": 0.40
                }
            ],
            "historical": [
                {"timestamp": "2025-08-10T00:00:00Z", "sentiment": 0.65},
                {"timestamp": "2025-08-09T00:00:00Z", "sentiment": 0.60},
                {"timestamp": "2025-08-08T00:00:00Z", "sentiment": 0.52}
            ],
            "correlation": {
                "sentiment_to_price": 0.78,
                "leading_indicator": True,
                "lag_hours": 4
            }
        }
    
    def _mock_historical_accuracy(self, market_type: str) -> Dict[str, Any]:
        """Generate mock historical prediction accuracy data."""
        return {
            "market_type": market_type,
            "overall_accuracy": 0.82,
            "markets_analyzed": 235,
            "time_periods": {
                "last_30_days": 0.84,
                "last_90_days": 0.82,
                "last_year": 0.80,
                "all_time": 0.78
            },
            "probability_calibration": [
                {"predicted": 0.1, "actual": 0.12},
                {"predicted": 0.3, "actual": 0.28},
                {"predicted": 0.5, "actual": 0.51},
                {"predicted": 0.7, "actual": 0.72},
                {"predicted": 0.9, "actual": 0.88}
            ],
            "by_subtypes": {
                "elections": 0.86,
                "policy": 0.82,
                "international": 0.78
            } if market_type == "politics" else {
                "team_sports": 0.84,
                "individual_sports": 0.79,
                "esports": 0.81
            } if market_type == "sports" else {
                "price_predictions": 0.72,
                "protocol_events": 0.85,
                "governance": 0.78
            },
            "resolution_speed": {
                "average_days": 45,
                "fastest": 1,
                "slowest": 180
            }
        }
    
    async def get_market_insights(self, market_id: str) -> Dict[str, Any]:
        """
        Fetch Polysights analytics for specific market.
        
        Args:
            market_id: Market ID to analyze
            
        Returns:
            Dict[str, Any]: Market insights data
        """
        try:
            endpoint = f"/markets/{market_id}/insights"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching market insights: {response['error']}")
            else:
                logger.info(f"Retrieved market insights for market {market_id}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_market_insights: {e}")
            return {"error": str(e)}
    
    async def get_trader_performance(self, trader_address: str) -> Dict[str, Any]:
        """
        Get historical trader performance data.
        
        Args:
            trader_address: Ethereum address of the trader
            
        Returns:
            Dict[str, Any]: Trader performance data
        """
        try:
            endpoint = f"/traders/{trader_address}/performance"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching trader performance: {response['error']}")
            else:
                logger.info(f"Retrieved performance data for trader {trader_address}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_trader_performance: {e}")
            return {"error": str(e)}
    
    async def get_smart_money_activity(self) -> Dict[str, Any]:
        """
        Track smart money movements.
        
        Returns:
            Dict[str, Any]: Smart money activity data
        """
        try:
            endpoint = "/smart-money"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching smart money activity: {response['error']}")
            else:
                logger.info("Retrieved smart money activity data")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_smart_money_activity: {e}")
            return {"error": str(e)}
    
    async def get_market_efficiency_metrics(self, market_id: str) -> Dict[str, Any]:
        """
        Calculate market efficiency indicators.
        
        Args:
            market_id: Market ID to analyze
            
        Returns:
            Dict[str, Any]: Market efficiency metrics
        """
        try:
            endpoint = f"/markets/{market_id}/efficiency"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching market efficiency: {response['error']}")
            else:
                logger.info(f"Retrieved efficiency metrics for market {market_id}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_market_efficiency_metrics: {e}")
            return {"error": str(e)}
    
    async def get_sentiment_analysis(self, market_id: str) -> Dict[str, Any]:
        """
        Market sentiment from various sources.
        
        Args:
            market_id: Market ID to analyze
            
        Returns:
            Dict[str, Any]: Sentiment analysis data
        """
        try:
            endpoint = f"/markets/{market_id}/sentiment"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching sentiment analysis: {response['error']}")
            else:
                logger.info(f"Retrieved sentiment analysis for market {market_id}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_sentiment_analysis: {e}")
            return {"error": str(e)}
    
    async def get_historical_accuracy(self, market_type: str) -> Dict[str, Any]:
        """
        Historical prediction accuracy for market category.
        
        Args:
            market_type: Type of market (e.g., politics, sports, crypto)
            
        Returns:
            Dict[str, Any]: Historical accuracy data
        """
        try:
            endpoint = f"/markets/{market_type}/historical-accuracy"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching historical accuracy: {response['error']}")
            else:
                logger.info(f"Retrieved historical accuracy for {market_type} markets")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in get_historical_accuracy: {e}")
            return {"error": str(e)}
    
    async def get_combined_market_analysis(self, market_id: str) -> Dict[str, Any]:
        """
        Get comprehensive market analysis combining multiple data sources.
        
        Args:
            market_id: Market ID to analyze
            
        Returns:
            Dict[str, Any]: Combined analysis data
        """
        try:
            # Fetch multiple data points in parallel
            tasks = [
                self.get_market_insights(market_id),
                self.get_market_efficiency_metrics(market_id),
                self.get_sentiment_analysis(market_id)
            ]
            
            import asyncio
            results = await asyncio.gather(*tasks)
            
            # Check for errors in any of the results
            if any("error" in result for result in results):
                error_messages = [result["error"] for result in results if "error" in result]
                logger.warning(f"Some analysis components failed: {error_messages}")
            
            # Combine all results
            combined = {
                "market_id": market_id,
                "insights": results[0] if "error" not in results[0] else {},
                "efficiency": results[1] if "error" not in results[1] else {},
                "sentiment": results[2] if "error" not in results[2] else {},
                "timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info(f"Generated combined analysis for market {market_id}")
            return combined
            
        except Exception as e:
            logger.error(f"Error in get_combined_market_analysis: {e}")
            return {"error": str(e)}
