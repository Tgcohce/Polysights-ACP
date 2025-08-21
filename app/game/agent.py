"""
Polymarket Analytics & Trading Agent using Virtuals G.A.M.E. Framework.

This module implements the main agent using the G.A.M.E. architecture with:
- Agent (high-level planner) for strategic decision making
- Workers (low-level planners) for specific tasks
- Functions for executing actions
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from virtuals_sdk import Agent, Worker, Function
from virtuals_sdk.types import AgentConfig, WorkerConfig, FunctionConfig

from app.polysights.analytics_client import PolysightsAnalyticsClient
from app.trading.clob_client import PolymarketCLOBClient
from app.core.config import config

logger = logging.getLogger(__name__)


class PolymarketAgent:
    """
    Main Polymarket Analytics & Trading Agent using G.A.M.E. framework.
    
    Provides autonomous analytics and trading capabilities through:
    - Market analysis and insights
    - Trading strategy execution
    - Risk management
    - Performance monitoring
    """
    
    def __init__(self, api_key: str):
        """Initialize the Polymarket Agent with G.A.M.E. framework."""
        self.api_key = api_key
        self.analytics_client = PolysightsAnalyticsClient()
        self.trading_client = None
        
        # Initialize G.A.M.E. components
        self._setup_agent()
        self._setup_workers()
        self._setup_functions()
        
        logger.info("Polymarket Agent initialized with G.A.M.E. framework")
    
    def _setup_agent(self):
        """Setup the main agent (high-level planner)."""
        agent_config = AgentConfig(
            goal="Provide comprehensive Polymarket analytics and execute profitable trading strategies while managing risk",
            description="""
            You are a professional Polymarket analytics and trading agent. Your world consists of:
            
            MARKET ENVIRONMENT:
            - Polymarket prediction markets with binary outcomes
            - Real-time market data, orderbooks, and trading activity
            - Insider/whale activity tracking and smart money flows
            - Market sentiment and efficiency metrics
            
            YOUR CAPABILITIES:
            - Analyze market trends, sentiment, and opportunities
            - Execute trades using CLOB API with wallet signatures
            - Monitor positions and implement risk management
            - Provide insights and recommendations to users
            
            YOUR PERSONALITY:
            - Data-driven and analytical
            - Risk-aware but opportunistic
            - Clear and concise in communications
            - Focused on profitable outcomes
            
            Always prioritize risk management and user safety in trading decisions.
            """,
            api_key=self.api_key
        )
        
        self.agent = Agent(config=agent_config)
    
    def _setup_workers(self):
        """Setup specialized workers for different tasks."""
        
        # Analytics Worker
        analytics_config = WorkerConfig(
            description="""
            Specialized in market analysis and data processing.
            
            Responsibilities:
            - Fetch and analyze live market data from Polysights APIs
            - Calculate sentiment scores and market efficiency metrics
            - Identify trading opportunities and market anomalies
            - Track insider activity and smart money flows
            - Generate market insights and recommendations
            
            Call this worker when you need to analyze markets, understand sentiment,
            or identify trading opportunities.
            """
        )
        self.analytics_worker = Worker(config=analytics_config)
        
        # Trading Worker  
        trading_config = WorkerConfig(
            description="""
            Specialized in trade execution and portfolio management.
            
            Responsibilities:
            - Execute buy/sell orders on Polymarket CLOB
            - Monitor open positions and P&L
            - Implement stop-loss and risk management strategies
            - Track order status and fills
            - Manage wallet balances and trading limits
            
            Call this worker when you need to execute trades, manage positions,
            or implement trading strategies.
            """
        )
        self.trading_worker = Worker(config=trading_config)
        
        # Risk Management Worker
        risk_config = WorkerConfig(
            description="""
            Specialized in risk assessment and portfolio protection.
            
            Responsibilities:
            - Calculate position sizes and risk metrics
            - Monitor portfolio exposure and concentration
            - Implement stop-loss and take-profit levels
            - Assess market volatility and liquidity risks
            - Generate risk alerts and recommendations
            
            Call this worker when you need to assess risks, calculate position sizes,
            or implement protective measures.
            """
        )
        self.risk_worker = Worker(config=risk_config)
    
    def _setup_functions(self):
        """Setup executable functions for the workers."""
        
        # Analytics Functions
        self.fetch_market_data_func = Function(
            config=FunctionConfig(
                description="Fetch live market data from Polysights APIs including markets, orderbooks, insider activity, and sentiment"
            ),
            function=self._fetch_market_data
        )
        
        self.analyze_sentiment_func = Function(
            config=FunctionConfig(
                description="Analyze market sentiment and efficiency metrics to identify opportunities"
            ),
            function=self._analyze_sentiment
        )
        
        self.detect_opportunities_func = Function(
            config=FunctionConfig(
                description="Detect trading opportunities based on market analysis and insider activity"
            ),
            function=self._detect_opportunities
        )
        
        # Trading Functions
        self.execute_trade_func = Function(
            config=FunctionConfig(
                description="Execute buy or sell orders on Polymarket CLOB with specified parameters"
            ),
            function=self._execute_trade
        )
        
        self.monitor_positions_func = Function(
            config=FunctionConfig(
                description="Monitor open positions, P&L, and order status"
            ),
            function=self._monitor_positions
        )
        
        self.manage_risk_func = Function(
            config=FunctionConfig(
                description="Implement risk management including stop-loss and position sizing"
            ),
            function=self._manage_risk
        )
        
        # Register functions with workers
        self.analytics_worker.add_function(self.fetch_market_data_func)
        self.analytics_worker.add_function(self.analyze_sentiment_func)
        self.analytics_worker.add_function(self.detect_opportunities_func)
        
        self.trading_worker.add_function(self.execute_trade_func)
        self.trading_worker.add_function(self.monitor_positions_func)
        
        self.risk_worker.add_function(self.manage_risk_func)
        
        # Register workers with agent
        self.agent.add_worker(self.analytics_worker)
        self.agent.add_worker(self.trading_worker)
        self.agent.add_worker(self.risk_worker)
    
    async def _fetch_market_data(self, **kwargs) -> Dict[str, Any]:
        """Fetch live market data from Polysights APIs."""
        try:
            # Fetch all live data concurrently
            data = await self.analytics_client.fetch_all_live_data()
            
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_sentiment(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Analyze market sentiment and efficiency."""
        try:
            analysis = await self.analytics_client.analyze_market_sentiment(market_data)
            
            return {
                "success": True,
                "sentiment_score": analysis.get("sentiment_score", 0),
                "efficiency_metrics": analysis.get("efficiency_metrics", {}),
                "insights": analysis.get("insights", [])
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"success": False, "error": str(e)}
    
    async def _detect_opportunities(self, market_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Detect trading opportunities."""
        try:
            opportunities = await self.analytics_client.detect_opportunities(market_data)
            
            return {
                "success": True,
                "opportunities": opportunities,
                "count": len(opportunities)
            }
        except Exception as e:
            logger.error(f"Error detecting opportunities: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_trade(self, market_id: str, outcome: str, side: str, 
                           size: float, price: float, **kwargs) -> Dict[str, Any]:
        """Execute a trade on Polymarket CLOB."""
        try:
            if not self.trading_client:
                self.trading_client = PolymarketCLOBClient()
            
            if side.lower() == "buy":
                result = await self.trading_client.buy(market_id, outcome, size, price)
            else:
                result = await self.trading_client.sell(market_id, outcome, size, price)
            
            return {
                "success": True,
                "order_id": result.get("order_id"),
                "status": result.get("status"),
                "details": result
            }
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {"success": False, "error": str(e)}
    
    async def _monitor_positions(self, **kwargs) -> Dict[str, Any]:
        """Monitor open positions and P&L."""
        try:
            if not self.trading_client:
                self.trading_client = PolymarketCLOBClient()
            
            positions = await self.trading_client.get_positions()
            balances = await self.trading_client.get_balances()
            
            return {
                "success": True,
                "positions": positions,
                "balances": balances,
                "total_value": sum(pos.get("value", 0) for pos in positions)
            }
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            return {"success": False, "error": str(e)}
    
    async def _manage_risk(self, positions: List[Dict], **kwargs) -> Dict[str, Any]:
        """Implement risk management strategies."""
        try:
            risk_actions = []
            
            for position in positions:
                # Check for stop-loss triggers
                current_price = position.get("current_price", 0)
                entry_price = position.get("entry_price", 0)
                size = position.get("size", 0)
                
                if current_price and entry_price:
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    
                    # Stop-loss at -10%
                    if pnl_pct <= -10:
                        risk_actions.append({
                            "action": "stop_loss",
                            "market_id": position.get("market_id"),
                            "reason": f"Stop-loss triggered at {pnl_pct:.1f}% loss"
                        })
                    
                    # Take profit at +25%
                    elif pnl_pct >= 25:
                        risk_actions.append({
                            "action": "take_profit",
                            "market_id": position.get("market_id"),
                            "reason": f"Take profit at {pnl_pct:.1f}% gain"
                        })
            
            return {
                "success": True,
                "risk_actions": risk_actions,
                "recommendations": [action["reason"] for action in risk_actions]
            }
        except Exception as e:
            logger.error(f"Error managing risk: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process user request through G.A.M.E. agent."""
        try:
            # Use G.A.M.E. agent to process the request
            response = await self.agent.process(user_input)
            
            return {
                "success": True,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_autonomous_mode(self):
        """Start autonomous trading and monitoring."""
        logger.info("Starting autonomous mode...")
        
        while True:
            try:
                # Let the agent decide what to do autonomously
                autonomous_action = await self.agent.process(
                    "Analyze current market conditions and take appropriate actions for profitable trading while managing risk"
                )
                
                logger.info(f"Autonomous action completed: {autonomous_action}")
                
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in autonomous mode: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
