"""
Market analysis engine for the ACP Polymarket Trading Agent.

This module provides comprehensive market analysis by integrating data from
Polymarket and Polysights to generate trading signals and identify opportunities.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import uuid

from loguru import logger
import numpy as np

from app.polymarket.client import PolymarketClient
from app.polysights.client import PolysightsClient
from app.utils.config import config
from pydantic import BaseModel
from enum import Enum


class RecommendationType(Enum):
    """Types of trading recommendations."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"


class TradingRecommendation(BaseModel):
    """Trading recommendation with confidence and reasoning."""
    
    market_id: str
    outcome_id: str
    recommendation: RecommendationType
    confidence: float  # 0.0 to 1.0
    price_target: Optional[float] = None
    size_recommendation: Optional[float] = None
    reasoning: str
    risk_level: str  # "low", "medium", "high"
    timestamp: datetime
    
    class Config:
        use_enum_values = True


class MarketAnalyzer:
    """
    Advanced market analysis using multiple data sources.
    
    This class integrates Polymarket order book data with Polysights analytics
    to provide comprehensive market analysis and generate trading signals.
    """
    
    def __init__(self, polysights_client: PolysightsClient, polymarket_client: PolymarketClient):
        """
        Initialize the Market Analyzer.
        
        Args:
            polysights_client: Initialized Polysights client
            polymarket_client: Initialized Polymarket client
        """
        self.polysights = polysights_client
        self.polymarket = polymarket_client
        
        # Analysis cache (market_id -> analysis result)
        self.analysis_cache = {}
        self.cache_ttl = 300  # seconds
        
        # Signal history
        self.signal_history = []
        self.max_signal_history = 100
        
        logger.info("Initialized MarketAnalyzer")
    
    async def analyze_market(self, market_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Comprehensive market analysis.
        
        Args:
            market_id: ID of the market to analyze
            force_refresh: Whether to force a refresh of cached data
            
        Returns:
            Dict[str, Any]: Market analysis results
        """
        try:
            # Check cache
            current_time = asyncio.get_event_loop().time()
            if (
                not force_refresh and 
                market_id in self.analysis_cache and 
                current_time - self.analysis_cache[market_id]["timestamp"] < self.cache_ttl
            ):
                logger.debug(f"Using cached analysis for market {market_id}")
                return self.analysis_cache[market_id]["data"]
            
            logger.info(f"Analyzing market {market_id}")
            
            # Gather data from multiple sources in parallel
            market_data_task = self.polymarket.get_market_data(market_id)
            polysights_data_task = self.polysights.get_combined_market_analysis(market_id)
            
            results = await asyncio.gather(market_data_task, polysights_data_task)
            market_data = results[0]
            polysights_data = results[1]
            
            if "error" in market_data:
                logger.error(f"Error fetching market data: {market_data['error']}")
                return {"error": f"Market data unavailable: {market_data['error']}"}
            
            # Extract relevant information
            order_book = market_data.get("orderBook", {})
            
            # Calculate market metrics
            metrics = self._calculate_market_metrics(market_data, order_book)
            
            # Incorporate Polysights analytics
            insights = {}
            if "error" not in polysights_data:
                insights = self._extract_polysights_insights(polysights_data)
            
            # Calculate fair value
            fair_value = self._calculate_fair_value(metrics, insights)
            
            # Identify trading opportunities
            opportunities = self._identify_opportunities(metrics, insights, fair_value)
            
            # Compile analysis result
            analysis_result = {
                "market_id": market_id,
                "market_title": market_data.get("title", ""),
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "insights": insights,
                "fair_value": fair_value,
                "opportunities": opportunities,
                "trading_recommendation": self._generate_recommendation(opportunities, metrics, insights)
            }
            
            # Cache the result
            self.analysis_cache[market_id] = {
                "timestamp": current_time,
                "data": analysis_result
            }
            
            logger.info(f"Completed analysis for market {market_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing market {market_id}: {e}")
            return {"error": str(e)}
    
    def _calculate_market_metrics(
        self, 
        market_data: Dict[str, Any],
        order_book: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate market metrics from order book and market data.
        
        Args:
            market_data: Market information from Polymarket
            order_book: Order book data
            
        Returns:
            Dict[str, Any]: Calculated market metrics
        """
        # Extract bid and ask data
        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])
        
        # Calculate metrics
        bid_ask_spread = 0
        midpoint_price = 0
        liquidity_depth = {"bid": 0, "ask": 0}
        price_impact = {"bid": {}, "ask": {}}
        
        # Bid-ask spread
        if bids and asks:
            best_bid = float(bids[0]["price"]) if bids else 0
            best_ask = float(asks[0]["price"]) if asks else 1.0
            
            bid_ask_spread = best_ask - best_bid
            midpoint_price = (best_bid + best_ask) / 2
            
            # Calculate liquidity depth (sum of sizes up to 5% from best price)
            bid_depth = 0
            for bid in bids:
                bid_price = float(bid["price"])
                if bid_price >= best_bid * 0.95:
                    bid_depth += float(bid["size"]) * bid_price
            
            ask_depth = 0
            for ask in asks:
                ask_price = float(ask["price"])
                if ask_price <= best_ask * 1.05:
                    ask_depth += float(ask["size"]) * ask_price
            
            liquidity_depth = {
                "bid": bid_depth,
                "ask": ask_depth,
                "total": bid_depth + ask_depth,
                "imbalance": bid_depth / (ask_depth + 1e-10)
            }
            
            # Calculate price impact for different order sizes
            order_sizes = [1000, 5000, 10000, 25000]  # USD
            
            for size in order_sizes:
                # Buy impact (moving up the ask book)
                ask_impact = 0
                remaining_size = size
                executed_price_sum = 0
                
                for ask in asks:
                    ask_price = float(ask["price"])
                    ask_size = float(ask["size"]) * ask_price  # Convert to USD
                    
                    if remaining_size <= ask_size:
                        executed_price_sum += remaining_size * ask_price / size
                        remaining_size = 0
                        break
                    else:
                        executed_price_sum += ask_size * ask_price / size
                        remaining_size -= ask_size
                
                if remaining_size > 0:
                    # Not enough liquidity
                    ask_impact = 0.5  # Arbitrary large impact for insufficient liquidity
                else:
                    # Calculate weighted average execution price
                    avg_execution_price = executed_price_sum
                    ask_impact = (avg_execution_price - best_ask) / best_ask
                
                price_impact["ask"][str(size)] = ask_impact
                
                # Sell impact (moving down the bid book)
                bid_impact = 0
                remaining_size = size
                executed_price_sum = 0
                
                for bid in bids:
                    bid_price = float(bid["price"])
                    bid_size = float(bid["size"]) * bid_price  # Convert to USD
                    
                    if remaining_size <= bid_size:
                        executed_price_sum += remaining_size * bid_price / size
                        remaining_size = 0
                        break
                    else:
                        executed_price_sum += bid_size * bid_price / size
                        remaining_size -= bid_size
                
                if remaining_size > 0:
                    # Not enough liquidity
                    bid_impact = 0.5  # Arbitrary large impact for insufficient liquidity
                else:
                    # Calculate weighted average execution price
                    avg_execution_price = executed_price_sum
                    bid_impact = (best_bid - avg_execution_price) / best_bid
                
                price_impact["bid"][str(size)] = bid_impact
        
        # Volume and price data
        volume_24h = market_data.get("volume24h", 0)
        
        # Outcome information
        outcomes = market_data.get("outcomes", [])
        outcome_probabilities = {}
        
        for outcome in outcomes:
            outcome_id = outcome.get("outcomeId")
            outcome_price = outcome.get("price", 0)
            if outcome_id and outcome_price:
                outcome_probabilities[outcome_id] = float(outcome_price)
        
        # Market status and metadata
        status = market_data.get("status", "unknown")
        end_date = market_data.get("endDate")
        time_remaining = None
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                time_remaining = (end_datetime - datetime.now()).total_seconds()
            except Exception:
                pass
        
        # Compile metrics
        return {
            "best_bid": best_bid if "best_bid" in locals() else 0,
            "best_ask": best_ask if "best_ask" in locals() else 1.0,
            "bid_ask_spread": bid_ask_spread,
            "midpoint_price": midpoint_price,
            "liquidity_depth": liquidity_depth,
            "price_impact": price_impact,
            "volume_24h": volume_24h,
            "status": status,
            "time_remaining": time_remaining,
            "outcome_probabilities": outcome_probabilities
        }
    
    def _extract_polysights_insights(self, polysights_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant insights from Polysights data.
        
        Args:
            polysights_data: Combined data from Polysights API
            
        Returns:
            Dict[str, Any]: Extracted insights
        """
        insights = {}
        
        # Extract market insights
        if "insights" in polysights_data and polysights_data["insights"]:
            market_insights = polysights_data["insights"]
            insights["implied_probability"] = market_insights.get("insights", {}).get("implied_probability")
            insights["analyst_consensus"] = market_insights.get("insights", {}).get("analyst_consensus")
            insights["price_movement"] = market_insights.get("insights", {}).get("price_movement", {})
            insights["volatility"] = market_insights.get("insights", {}).get("volatility", {})
            insights["key_events"] = market_insights.get("insights", {}).get("key_events", [])
            insights["forecast"] = market_insights.get("forecast", {})
        
        # Extract efficiency metrics
        if "efficiency" in polysights_data and polysights_data["efficiency"]:
            efficiency = polysights_data["efficiency"]
            insights["efficiency_score"] = efficiency.get("efficiency_score")
            insights["price_discovery"] = efficiency.get("metrics", {}).get("price_discovery")
            insights["arbitrage"] = efficiency.get("arbitrage_opportunities", {})
        
        # Extract sentiment analysis
        if "sentiment" in polysights_data and polysights_data["sentiment"]:
            sentiment = polysights_data["sentiment"]
            insights["sentiment_score"] = sentiment.get("overall_sentiment", {}).get("score")
            insights["sentiment_confidence"] = sentiment.get("overall_sentiment", {}).get("confidence")
            insights["sentiment_sources"] = sentiment.get("sources", {})
            insights["sentiment_correlation"] = sentiment.get("correlation", {})
        
        return insights
    
    def _calculate_fair_value(
        self, 
        metrics: Dict[str, Any], 
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate fair value based on market metrics and insights.
        
        Args:
            metrics: Market metrics
            insights: Polysights insights
            
        Returns:
            Dict[str, Any]: Fair value calculation
        """
        # Start with the midpoint price as a baseline
        midpoint_price = metrics.get("midpoint_price", 0.5)
        
        # Weight factors for different signals
        weights = {
            "midpoint": 0.4,
            "implied_probability": 0.2,
            "analyst_consensus": 0.15,
            "sentiment_score": 0.1,
            "forecast_short_term": 0.15
        }
        
        # Collect signals
        signals = {
            "midpoint": midpoint_price,
            "implied_probability": insights.get("implied_probability", midpoint_price),
            "analyst_consensus": insights.get("analyst_consensus", midpoint_price),
            "sentiment_score": (insights.get("sentiment_score", 0) + 1) / 2,  # Convert -1 to 1 scale to 0 to 1
            "forecast_short_term": insights.get("forecast", {}).get("short_term", {}).get("price", midpoint_price)
        }
        
        # Calculate weighted fair value
        weighted_sum = 0
        total_weight = 0
        
        for signal_name, weight in weights.items():
            signal_value = signals.get(signal_name)
            if signal_value is not None:
                weighted_sum += signal_value * weight
                total_weight += weight
        
        # Default to midpoint if we couldn't calculate
        fair_value = weighted_sum / total_weight if total_weight > 0 else midpoint_price
        
        # Calculate confidence based on agreement between signals
        signal_values = [v for v in signals.values() if v is not None]
        confidence = 0.5
        
        if len(signal_values) >= 3:
            # Use standard deviation of signals to measure confidence
            std_dev = np.std(signal_values)
            # Convert to confidence (lower std_dev = higher confidence)
            confidence = max(0.1, min(0.9, 1 - 2 * std_dev))
        
        return {
            "fair_value": fair_value,
            "confidence": confidence,
            "signals": signals,
            "weights": weights
        }
    
    def _identify_opportunities(
        self, 
        metrics: Dict[str, Any], 
        insights: Dict[str, Any],
        fair_value: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify trading opportunities based on analysis.
        
        Args:
            metrics: Market metrics
            insights: Polysights insights
            fair_value: Fair value calculation
            
        Returns:
            List[Dict[str, Any]]: Identified opportunities
        """
        opportunities = []
        
        # Extract key values
        best_bid = metrics.get("best_bid", 0)
        best_ask = metrics.get("best_ask", 1.0)
        calculated_fair = fair_value.get("fair_value", 0.5)
        confidence = fair_value.get("confidence", 0.5)
        
        # Mispricing opportunity (when fair value differs significantly from market price)
        bid_threshold = 0.03  # 3% threshold for opportunity
        ask_threshold = 0.03
        
        # Adjust thresholds based on confidence
        bid_threshold = bid_threshold * (2 - confidence)  # Higher confidence = lower threshold
        ask_threshold = ask_threshold * (2 - confidence)
        
        # Check for buy opportunity (fair value > best ask + threshold)
        if calculated_fair > best_ask * (1 + bid_threshold):
            opportunity_size = min(
                10000,  # Default max size
                metrics.get("liquidity_depth", {}).get("ask", 1000)  # Available liquidity
            )
            
            opportunities.append({
                "type": "value_buy",
                "side": "buy",
                "price": best_ask,
                "size": opportunity_size,
                "expected_profit": calculated_fair - best_ask,
                "confidence": confidence,
                "reason": "Fair value significantly higher than best ask price"
            })
        
        # Check for sell opportunity (fair value < best bid - threshold)
        if calculated_fair < best_bid * (1 - ask_threshold):
            opportunity_size = min(
                10000,  # Default max size
                metrics.get("liquidity_depth", {}).get("bid", 1000)  # Available liquidity
            )
            
            opportunities.append({
                "type": "value_sell",
                "side": "sell",
                "price": best_bid,
                "size": opportunity_size,
                "expected_profit": best_bid - calculated_fair,
                "confidence": confidence,
                "reason": "Fair value significantly lower than best bid price"
            })
        
        # Check for sentiment-driven opportunities
        sentiment_score = insights.get("sentiment_score")
        sentiment_confidence = insights.get("sentiment_confidence", 0)
        
        if sentiment_score is not None and sentiment_confidence > 0.7:
            # Strong positive sentiment not yet reflected in price
            if sentiment_score > 0.7 and calculated_fair < 0.6:
                opportunities.append({
                    "type": "sentiment_buy",
                    "side": "buy",
                    "price": best_ask,
                    "size": 5000,  # Default size
                    "expected_profit": 0.1,  # Expected price movement
                    "confidence": sentiment_confidence,
                    "reason": "Strong positive sentiment not yet reflected in price"
                })
            
            # Strong negative sentiment not yet reflected in price
            if sentiment_score < -0.7 and calculated_fair > 0.4:
                opportunities.append({
                    "type": "sentiment_sell",
                    "side": "sell",
                    "price": best_bid,
                    "size": 5000,  # Default size
                    "expected_profit": 0.1,  # Expected price movement
                    "confidence": sentiment_confidence,
                    "reason": "Strong negative sentiment not yet reflected in price"
                })
        
        # Check for liquidity imbalance opportunities
        imbalance = metrics.get("liquidity_depth", {}).get("imbalance", 1.0)
        
        if imbalance > 2.0:  # Significantly more bids than asks
            opportunities.append({
                "type": "liquidity_imbalance",
                "side": "sell",
                "price": best_bid,
                "size": 2500,
                "expected_profit": 0.01,
                "confidence": 0.6,
                "reason": "Significant liquidity imbalance with excess bids"
            })
        elif imbalance < 0.5:  # Significantly more asks than bids
            opportunities.append({
                "type": "liquidity_imbalance",
                "side": "buy",
                "price": best_ask,
                "size": 2500,
                "expected_profit": 0.01,
                "confidence": 0.6,
                "reason": "Significant liquidity imbalance with excess asks"
            })
        
        # Sort opportunities by confidence * expected_profit
        for opp in opportunities:
            opp["score"] = opp["confidence"] * opp["expected_profit"]
            
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        
        return opportunities
    
    def _generate_recommendation(
        self, 
        opportunities: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a trading recommendation based on opportunities.
        
        Args:
            opportunities: Identified trading opportunities
            metrics: Market metrics
            insights: Polysights insights
            
        Returns:
            Dict[str, Any]: Trading recommendation
        """
        if not opportunities:
            return {
                "action": "hold",
                "confidence": 0.5,
                "reason": "No compelling opportunities identified"
            }
        
        # Use the highest-scoring opportunity
        best_opportunity = opportunities[0]
        
        # Generate recommendation based on best opportunity
        recommendation = {
            "action": best_opportunity["side"],
            "price": best_opportunity["price"],
            "size": best_opportunity["size"],
            "confidence": best_opportunity["confidence"],
            "expected_profit": best_opportunity["expected_profit"],
            "reason": best_opportunity["reason"],
            "opportunity_type": best_opportunity["type"]
        }
        
        # Add urgency based on market conditions
        liquidity = metrics.get("liquidity_depth", {}).get("total", 0)
        
        if liquidity < 5000:
            recommendation["urgency"] = "high"
            recommendation["urgency_reason"] = "Low liquidity environment"
        elif best_opportunity["confidence"] > 0.8:
            recommendation["urgency"] = "high"
            recommendation["urgency_reason"] = "High confidence opportunity"
        else:
            recommendation["urgency"] = "medium"
            recommendation["urgency_reason"] = "Standard execution"
        
        return recommendation
    
    async def generate_trading_signals(
        self, 
        market_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate buy/sell signals based on analysis.
        
        Args:
            market_ids: List of market IDs to analyze, or None for all active markets
            
        Returns:
            List[Dict[str, Any]]: Trading signals
        """
        try:
            signals = []
            
            # If no market IDs provided, get active markets
            if not market_ids:
                markets = await self.polymarket.get_markets({"status": "open"})
                market_ids = [m["marketId"] for m in markets]
                
                # Limit to 10 markets for performance
                if len(market_ids) > 10:
                    market_ids = market_ids[:10]
            
            # Analyze each market
            for market_id in market_ids:
                analysis = await self.analyze_market(market_id)
                
                if "error" in analysis:
                    logger.warning(f"Skipping signal for market {market_id}: {analysis['error']}")
                    continue
                
                # Extract recommendation
                recommendation = analysis.get("trading_recommendation", {})
                
                if recommendation.get("action") in ["buy", "sell"]:
                    signal = {
                        "id": str(uuid.uuid4()),
                        "market_id": market_id,
                        "market_title": analysis.get("market_title", ""),
                        "timestamp": datetime.now().isoformat(),
                        "action": recommendation["action"],
                        "price": recommendation["price"],
                        "size": recommendation["size"],
                        "confidence": recommendation["confidence"],
                        "reason": recommendation["reason"],
                        "type": recommendation.get("opportunity_type", "value"),
                        "urgency": recommendation.get("urgency", "medium")
                    }
                    
                    signals.append(signal)
                    
                    # Add to signal history
                    self.signal_history.append(signal)
                    if len(self.signal_history) > self.max_signal_history:
                        self.signal_history = self.signal_history[-self.max_signal_history:]
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return []
    
    async def risk_assessment(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate portfolio risk and suggest adjustments.
        
        Args:
            portfolio: Current portfolio positions
            
        Returns:
            Dict[str, Any]: Risk assessment and adjustment suggestions
        """
        try:
            positions = portfolio.get("positions", [])
            total_exposure = sum(float(p.get("value", 0)) for p in positions)
            
            # Calculate risk metrics
            risk_metrics = {
                "total_exposure": total_exposure,
                "position_count": len(positions),
                "max_position_size": 0,
                "concentration_risk": 0,
                "correlation_risk": "low"
            }
            
            if positions:
                # Calculate concentration metrics
                position_values = [float(p.get("value", 0)) for p in positions]
                max_position = max(position_values)
                risk_metrics["max_position_size"] = max_position
                risk_metrics["concentration_risk"] = max_position / total_exposure if total_exposure else 0
                
                # Analyze correlations between positions
                market_categories = {}
                for position in positions:
                    market_id = position.get("market_id")
                    if not market_id:
                        continue
                        
                    # Get market data to determine category
                    # This is simplified - would need actual category data
                    market_category = position.get("category", "unknown")
                    market_categories[market_category] = market_categories.get(market_category, 0) + float(position.get("value", 0))
                
                # Check if more than 50% of portfolio is in one category
                max_category_exposure = max(market_categories.values()) if market_categories else 0
                category_concentration = max_category_exposure / total_exposure if total_exposure else 0
                
                if category_concentration > 0.5:
                    risk_metrics["correlation_risk"] = "high"
                    risk_metrics["concentration_category"] = max(
                        market_categories, 
                        key=lambda k: market_categories[k]
                    )
            
            # Generate risk assessment
            risk_level = "low"
            if risk_metrics["concentration_risk"] > 0.3:
                risk_level = "high"
            elif risk_metrics["correlation_risk"] == "high":
                risk_level = "high"
            elif len(positions) < 3 and total_exposure > 10000:
                risk_level = "medium"
            
            # Suggest adjustments
            adjustments = []
            
            if risk_metrics["concentration_risk"] > 0.3:
                adjustments.append({
                    "type": "reduce_position",
                    "position_id": next(
                        (p.get("position_id") for p in positions if float(p.get("value", 0)) == risk_metrics["max_position_size"]), 
                        None
                    ),
                    "reason": "Position concentration too high",
                    "target_size": risk_metrics["max_position_size"] * 0.5
                })
            
            if risk_metrics["correlation_risk"] == "high":
                adjustments.append({
                    "type": "diversify",
                    "category": risk_metrics.get("concentration_category", "unknown"),
                    "reason": "Too much exposure to correlated markets",
                    "recommendation": "Reduce positions in this category by 30%"
                })
            
            # Final assessment
            assessment = {
                "risk_level": risk_level,
                "risk_metrics": risk_metrics,
                "timestamp": datetime.now().isoformat(),
                "adjustments": adjustments
            }
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {"error": str(e)}
