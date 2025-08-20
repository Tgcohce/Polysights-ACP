#!/usr/bin/env python3
"""
ANALYTICS SERVICE
Main service providing market analytics to other agents and users
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import json

from ..polysights.analytics_client import PolysightsAnalyticsClient, MarketAnalytics

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Main analytics service for providing market insights."""
    
    def __init__(self):
        self.client = PolysightsAnalyticsClient()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    async def get_market_overview(self) -> Dict:
        """Get comprehensive market overview."""
        cache_key = "market_overview"
        
        # Check cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        logger.info("Generating market overview...")
        
        async with self.client as client:
            # Get trending markets
            trending = await client.get_trending_markets(10)
            
            # Get top buys from different timeframes
            top_buys_1h = await client.get_top_buys('1h')
            top_buys_1d = await client.get_top_buys('1d')
            
            # Get leaderboard metrics
            leaderboard = await client.get_leaderboard_metrics('24h')
            
            overview = {
                'timestamp': datetime.now().isoformat(),
                'trending_markets': trending,
                'top_buys': {
                    '1h': top_buys_1h[:5],
                    '1d': top_buys_1d[:5]
                },
                'leaderboard_highlights': leaderboard,
                'market_summary': {
                    'total_trending': len(trending),
                    'avg_price_change': sum(m['price_change_24h'] for m in trending) / len(trending) if trending else 0,
                    'total_volume_24h': sum(m['volume_24h'] for m in trending)
                }
            }
        
        # Cache result
        self._cache_data(cache_key, overview)
        return overview
    
    async def analyze_market(self, market_id: str) -> Dict:
        """Get detailed analysis for specific market."""
        cache_key = f"market_analysis_{market_id}"
        
        # Check cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        logger.info(f"Analyzing market: {market_id}")
        
        async with self.client as client:
            # Get comprehensive analysis
            analysis = await client.get_comprehensive_market_analysis(market_id)
            
            # Get sentiment analysis
            sentiment = await client.get_market_sentiment_analysis(market_id)
            
            # Get historical charts
            charts = await client.get_historical_charts(market_id, '24h')
            
            result = {
                'market_id': market_id,
                'analysis': asdict(analysis),
                'sentiment': sentiment,
                'charts': charts,
                'insights': self._generate_insights(analysis, sentiment),
                'timestamp': datetime.now().isoformat()
            }
        
        # Cache result
        self._cache_data(cache_key, result)
        return result
    
    async def get_insider_insights(self, wallet_address: str = None) -> Dict:
        """Get insider trading insights."""
        cache_key = f"insider_insights_{wallet_address or 'all'}"
        
        # Check cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        logger.info(f"Getting insider insights for: {wallet_address or 'all wallets'}")
        
        async with self.client as client:
            insider_activity = await client.get_insider_activity(wallet_address)
            
            # Analyze insider patterns
            insights = {
                'total_trades': len(insider_activity),
                'recent_activity': insider_activity[:10],
                'patterns': self._analyze_insider_patterns(insider_activity),
                'timestamp': datetime.now().isoformat()
            }
        
        # Cache result
        self._cache_data(cache_key, insights)
        return insights
    
    async def get_market_opportunities(self) -> Dict:
        """Identify market opportunities based on analytics."""
        cache_key = "market_opportunities"
        
        # Check cache
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        logger.info("Identifying market opportunities...")
        
        async with self.client as client:
            # Get trending markets
            trending = await client.get_trending_markets(20)
            
            opportunities = []
            
            for market in trending:
                market_id = market['market_id']
                
                try:
                    # Get detailed analysis
                    sentiment = await client.get_market_sentiment_analysis(market_id)
                    
                    # Identify opportunities
                    opportunity_score = self._calculate_opportunity_score(market, sentiment)
                    
                    if opportunity_score > 0.6:  # High opportunity threshold
                        opportunities.append({
                            'market_id': market_id,
                            'event_name': market['event_name'],
                            'opportunity_score': opportunity_score,
                            'sentiment': sentiment['sentiment'],
                            'confidence': sentiment['confidence'],
                            'reasoning': self._generate_opportunity_reasoning(market, sentiment)
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze opportunity for {market_id}: {e}")
                    continue
            
            # Sort by opportunity score
            opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
            
            result = {
                'opportunities': opportunities[:10],  # Top 10 opportunities
                'analysis_timestamp': datetime.now().isoformat(),
                'total_analyzed': len(trending),
                'opportunities_found': len(opportunities)
            }
        
        # Cache result
        self._cache_data(cache_key, result)
        return result
    
    async def get_portfolio_insights(self, wallet_addresses: List[str]) -> Dict:
        """Analyze portfolio performance across multiple wallets."""
        logger.info(f"Analyzing portfolio for {len(wallet_addresses)} wallets")
        
        portfolio_data = []
        
        async with self.client as client:
            for wallet in wallet_addresses:
                try:
                    insider_data = await client.get_insider_activity(wallet)
                    
                    # Calculate wallet performance
                    performance = self._calculate_wallet_performance(insider_data)
                    portfolio_data.append({
                        'wallet': wallet,
                        'performance': performance,
                        'recent_trades': insider_data[:5]
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze wallet {wallet}: {e}")
                    continue
        
        # Aggregate portfolio insights
        total_pnl = sum(w['performance']['total_pnl'] for w in portfolio_data)
        avg_win_rate = sum(w['performance']['win_rate'] for w in portfolio_data) / len(portfolio_data) if portfolio_data else 0
        
        return {
            'portfolio_summary': {
                'total_wallets': len(wallet_addresses),
                'analyzed_wallets': len(portfolio_data),
                'total_pnl': total_pnl,
                'average_win_rate': avg_win_rate
            },
            'wallet_details': portfolio_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_insights(self, analysis: MarketAnalytics, sentiment: Dict) -> List[str]:
        """Generate human-readable insights from analysis."""
        insights = []
        
        # Price momentum insights
        if analysis.price_change_24h > 10:
            insights.append(f"Strong bullish momentum with {analysis.price_change_24h:.1f}% price increase")
        elif analysis.price_change_24h < -10:
            insights.append(f"Significant bearish pressure with {analysis.price_change_24h:.1f}% price decline")
        
        # Volume insights
        if analysis.volume_24h > 50000:
            insights.append(f"High trading activity with ${analysis.volume_24h:,.0f} in 24h volume")
        
        # Open interest insights
        if analysis.open_interest > 100000:
            insights.append(f"Strong market interest with ${analysis.open_interest:,.0f} open interest")
        
        # Sentiment insights
        if sentiment['confidence'] > 0.7:
            insights.append(f"High confidence {sentiment['sentiment'].lower()} sentiment")
        
        # Insider activity insights
        if len(analysis.insider_activity) > 5:
            insights.append(f"Elevated insider activity with {len(analysis.insider_activity)} recent trades")
        
        return insights
    
    def _analyze_insider_patterns(self, insider_activity: List[Dict]) -> Dict:
        """Analyze patterns in insider trading activity."""
        if not insider_activity:
            return {}
        
        buy_trades = [t for t in insider_activity if t.get('side') == 'buy']
        sell_trades = [t for t in insider_activity if t.get('side') == 'sell']
        
        return {
            'buy_sell_ratio': len(buy_trades) / len(sell_trades) if sell_trades else float('inf'),
            'avg_buy_size': sum(t.get('size', 0) for t in buy_trades) / len(buy_trades) if buy_trades else 0,
            'avg_sell_size': sum(t.get('size', 0) for t in sell_trades) / len(sell_trades) if sell_trades else 0,
            'most_active_hours': self._get_most_active_hours(insider_activity)
        }
    
    def _get_most_active_hours(self, trades: List[Dict]) -> List[int]:
        """Get most active trading hours."""
        hour_counts = {}
        
        for trade in trades:
            timestamp = trade.get('timestamp')
            if timestamp:
                try:
                    hour = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                except:
                    continue
        
        # Return top 3 most active hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def _calculate_opportunity_score(self, market: Dict, sentiment: Dict) -> float:
        """Calculate opportunity score for a market."""
        score = 0.0
        
        # Volume factor (0-0.3)
        volume_score = min(market['volume_24h'] / 100000, 0.3)
        score += volume_score
        
        # Price momentum factor (0-0.3)
        momentum = abs(market['price_change_24h'])
        momentum_score = min(momentum / 20, 0.3)  # Normalize to 20% max
        score += momentum_score
        
        # Sentiment confidence factor (0-0.4)
        confidence_score = sentiment['confidence'] * 0.4
        score += confidence_score
        
        return min(score, 1.0)
    
    def _generate_opportunity_reasoning(self, market: Dict, sentiment: Dict) -> str:
        """Generate reasoning for why this is an opportunity."""
        reasons = []
        
        if market['volume_24h'] > 50000:
            reasons.append("high trading volume")
        
        if abs(market['price_change_24h']) > 10:
            reasons.append("significant price movement")
        
        if sentiment['confidence'] > 0.7:
            reasons.append(f"strong {sentiment['sentiment'].lower()} sentiment")
        
        return f"Opportunity identified due to: {', '.join(reasons)}"
    
    def _calculate_wallet_performance(self, trades: List[Dict]) -> Dict:
        """Calculate performance metrics for a wallet."""
        if not trades:
            return {'total_pnl': 0, 'win_rate': 0, 'total_trades': 0}
        
        total_pnl = 0
        winning_trades = 0
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            total_pnl += pnl
            if pnl > 0:
                winning_trades += 1
        
        win_rate = winning_trades / len(trades) if trades else 0
        
        return {
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'avg_trade_size': sum(t.get('size', 0) for t in trades) / len(trades)
        }
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid."""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]['timestamp']
        return (datetime.now() - cache_time).seconds < self.cache_ttl
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp."""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    async def health_check(self) -> Dict:
        """Health check for the analytics service."""
        try:
            async with self.client as client:
                # Test API connectivity
                markets = await client.get_all_markets()
                
                return {
                    'status': 'healthy',
                    'api_connectivity': 'ok',
                    'markets_available': len(markets),
                    'cache_size': len(self.cache),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
