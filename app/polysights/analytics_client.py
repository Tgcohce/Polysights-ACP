#!/usr/bin/env python3
"""
POLYSIGHTS ANALYTICS CLIENT
Comprehensive client for all Polysights APIs providing market analytics
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MarketAnalytics:
    """Comprehensive market analytics data structure."""
    market_id: str
    event_name: str
    current_price: float
    volume_24h: float
    open_interest: float
    price_change_24h: float
    top_positions: List[Dict]
    insider_activity: List[Dict]
    orderbook_depth: Dict
    historical_data: List[Dict]
    
class PolysightsAnalyticsClient:
    """Client for all Polysights analytics APIs."""
    
    def __init__(self):
        self.base_urls = {
            'tables': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/tables_api',
            'open_interest': 'https://oitsapi-655880131780.us-central1.run.app/',
            'orderbook': 'https://orderbookapi1-655880131780.us-central1.run.app/',
            'wallet_tracker': 'https://wallettrackapi-655880131780.us-central1.run.app/',
            'leaderboard': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/leaderboard_api',
            'charts': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/charts_api',
            'top_buys': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/topbuysAPI'
        }
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to API endpoint."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed: {response.status} - {endpoint}")
                    return {}
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {}
    
    async def get_all_markets(self) -> List[Dict]:
        """Get all active events and markets from tables API."""
        logger.info("Fetching all active markets...")
        
        data = await self._make_request(self.base_urls['tables'])
        
        if data and 'markets' in data:
            logger.info(f"Retrieved {len(data['markets'])} markets")
            return data['markets']
        return []
    
    async def get_market_open_interest(self, market_id: str = None) -> Dict:
        """Get open interest data with time series."""
        logger.info(f"Fetching open interest data for market: {market_id or 'all'}")
        
        params = {'market_id': market_id} if market_id else {}
        return await self._make_request(self.base_urls['open_interest'], params)
    
    async def get_orderbook_data(self, market_id: str = None) -> Dict:
        """Get order book data for markets."""
        logger.info(f"Fetching orderbook data for market: {market_id or 'all'}")
        
        params = {'market_id': market_id} if market_id else {}
        return await self._make_request(self.base_urls['orderbook'], params)
    
    async def get_insider_activity(self, wallet_address: str = None) -> List[Dict]:
        """Get insider trading activity from wallet tracker."""
        logger.info(f"Fetching insider activity for wallet: {wallet_address or 'all'}")
        
        params = {'wallet': wallet_address} if wallet_address else {}
        data = await self._make_request(self.base_urls['wallet_tracker'], params)
        
        if data and 'insider_trades' in data:
            return data['insider_trades']
        return []
    
    async def get_leaderboard_metrics(self, timeframe: str = '24h') -> Dict:
        """Get leaderboard related metrics."""
        logger.info(f"Fetching leaderboard metrics for timeframe: {timeframe}")
        
        params = {'timeframe': timeframe}
        return await self._make_request(self.base_urls['leaderboard'], params)
    
    async def get_historical_charts(self, market_id: str, timeframe: str = '24h') -> Dict:
        """Get historical volume/price charts."""
        logger.info(f"Fetching charts for market {market_id}, timeframe: {timeframe}")
        
        params = {
            'market_id': market_id,
            'timeframe': timeframe
        }
        return await self._make_request(self.base_urls['charts'], params)
    
    async def get_top_buys(self, timeframe: str = '1h') -> List[Dict]:
        """Get top buys from specified timeframe (1h, 1d, 1m)."""
        logger.info(f"Fetching top buys from {timeframe} ago")
        
        params = {'timeframe': timeframe}
        data = await self._make_request(self.base_urls['top_buys'], params)
        
        if data and 'top_buys' in data:
            return data['top_buys']
        return []
    
    async def get_comprehensive_market_analysis(self, market_id: str) -> MarketAnalytics:
        """Get comprehensive analysis for a specific market."""
        logger.info(f"Generating comprehensive analysis for market: {market_id}")
        
        # Fetch data from multiple APIs concurrently
        tasks = [
            self.get_all_markets(),
            self.get_market_open_interest(market_id),
            self.get_orderbook_data(market_id),
            self.get_insider_activity(),
            self.get_historical_charts(market_id),
            self.get_top_buys('1h'),
            self.get_top_buys('1d')
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract market info
        markets = results[0] if isinstance(results[0], list) else []
        market_info = next((m for m in markets if m.get('id') == market_id), {})
        
        # Process open interest
        oi_data = results[1] if isinstance(results[1], dict) else {}
        
        # Process orderbook
        orderbook = results[2] if isinstance(results[2], dict) else {}
        
        # Process insider activity
        insider_activity = results[3] if isinstance(results[3], list) else []
        
        # Process historical data
        historical = results[4] if isinstance(results[4], dict) else {}
        
        # Process top buys
        top_buys_1h = results[5] if isinstance(results[5], list) else []
        top_buys_1d = results[6] if isinstance(results[6], list) else []
        
        # Calculate analytics
        current_price = market_info.get('price', 0.0)
        volume_24h = historical.get('volume_24h', 0.0)
        open_interest = oi_data.get('total_open_interest', 0.0)
        
        # Price change calculation
        price_history = historical.get('price_history', [])
        price_change_24h = 0.0
        if len(price_history) >= 2:
            price_change_24h = ((current_price - price_history[-24]) / price_history[-24]) * 100
        
        return MarketAnalytics(
            market_id=market_id,
            event_name=market_info.get('event_name', 'Unknown'),
            current_price=current_price,
            volume_24h=volume_24h,
            open_interest=open_interest,
            price_change_24h=price_change_24h,
            top_positions=top_buys_1d[:10],  # Top 10 positions
            insider_activity=insider_activity[:5],  # Recent insider trades
            orderbook_depth=orderbook,
            historical_data=price_history[-100:]  # Last 100 data points
        )
    
    async def get_market_sentiment_analysis(self, market_id: str) -> Dict:
        """Analyze market sentiment based on multiple data sources."""
        logger.info(f"Analyzing market sentiment for: {market_id}")
        
        # Get comprehensive data
        analysis = await self.get_comprehensive_market_analysis(market_id)
        
        # Calculate sentiment indicators
        sentiment_score = 0.0
        confidence = 0.0
        
        # Price momentum (30% weight)
        if analysis.price_change_24h > 5:
            sentiment_score += 0.3
        elif analysis.price_change_24h < -5:
            sentiment_score -= 0.3
        else:
            sentiment_score += (analysis.price_change_24h / 100) * 0.3
        
        # Volume analysis (25% weight)
        if analysis.volume_24h > 10000:  # High volume threshold
            confidence += 0.25
            if analysis.price_change_24h > 0:
                sentiment_score += 0.25
        
        # Open interest analysis (20% weight)
        if analysis.open_interest > 50000:  # High OI threshold
            confidence += 0.2
        
        # Insider activity (25% weight)
        insider_sentiment = 0.0
        for trade in analysis.insider_activity:
            if trade.get('side') == 'buy':
                insider_sentiment += trade.get('size', 0)
            else:
                insider_sentiment -= trade.get('size', 0)
        
        if insider_sentiment > 0:
            sentiment_score += 0.25
        elif insider_sentiment < 0:
            sentiment_score -= 0.25
        
        # Normalize sentiment score
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine sentiment label
        if sentiment_score > 0.3:
            sentiment = "Bullish"
        elif sentiment_score < -0.3:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"
        
        return {
            'market_id': market_id,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'analysis': {
                'price_momentum': analysis.price_change_24h,
                'volume_24h': analysis.volume_24h,
                'open_interest': analysis.open_interest,
                'insider_trades': len(analysis.insider_activity),
                'orderbook_spread': self._calculate_spread(analysis.orderbook_depth)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_spread(self, orderbook: Dict) -> float:
        """Calculate bid-ask spread from orderbook."""
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if bids and asks:
                best_bid = max(bids, key=lambda x: x.get('price', 0))
                best_ask = min(asks, key=lambda x: x.get('price', float('inf')))
                
                bid_price = best_bid.get('price', 0)
                ask_price = best_ask.get('price', 0)
                
                if bid_price and ask_price:
                    return ask_price - bid_price
            
            return 0.0
        except Exception:
            return 0.0
    
    async def get_trending_markets(self, limit: int = 10) -> List[Dict]:
        """Get trending markets based on volume and price movement."""
        logger.info(f"Finding top {limit} trending markets...")
        
        # Get all markets
        markets = await self.get_all_markets()
        
        # Get additional data for trending analysis
        trending_scores = []
        
        for market in markets[:50]:  # Analyze top 50 markets
            market_id = market.get('id')
            if not market_id:
                continue
                
            try:
                # Get market analytics
                analysis = await self.get_comprehensive_market_analysis(market_id)
                
                # Calculate trending score
                volume_score = min(analysis.volume_24h / 10000, 1.0)  # Normalize volume
                price_momentum = abs(analysis.price_change_24h) / 100  # Absolute momentum
                oi_score = min(analysis.open_interest / 50000, 1.0)  # Normalize OI
                
                trending_score = (volume_score * 0.4) + (price_momentum * 0.4) + (oi_score * 0.2)
                
                trending_scores.append({
                    'market_id': market_id,
                    'event_name': analysis.event_name,
                    'trending_score': trending_score,
                    'price_change_24h': analysis.price_change_24h,
                    'volume_24h': analysis.volume_24h,
                    'current_price': analysis.current_price
                })
                
            except Exception as e:
                logger.warning(f"Failed to analyze market {market_id}: {e}")
                continue
        
        # Sort by trending score and return top markets
        trending_scores.sort(key=lambda x: x['trending_score'], reverse=True)
        return trending_scores[:limit]

# Usage example
async def main():
    """Example usage of the analytics client."""
    async with PolysightsAnalyticsClient() as client:
        # Get trending markets
        trending = await client.get_trending_markets(5)
        print("Top 5 Trending Markets:")
        for market in trending:
            print(f"- {market['event_name']}: {market['trending_score']:.3f}")
        
        # Analyze specific market
        if trending:
            market_id = trending[0]['market_id']
            sentiment = await client.get_market_sentiment_analysis(market_id)
            print(f"\nSentiment Analysis for {market_id}:")
            print(f"Sentiment: {sentiment['sentiment']}")
            print(f"Score: {sentiment['sentiment_score']:.3f}")
            print(f"Confidence: {sentiment['confidence']:.3f}")

if __name__ == "__main__":
    asyncio.run(main())
