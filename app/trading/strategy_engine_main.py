"""
Trading Strategy Engine for ACP Polymarket Trading Agent - Main Integration.

This module integrates the strategy engine components and provides 
the main interface for the ACP Polymarket Trading Agent.
"""
import asyncio
import os
from typing import Dict, List, Any, Optional, Set

from loguru import logger

from app.polymarket.client import PolymarketClient
from app.polysights.client import PolysightsClient
from app.trading.market_analyzer import MarketAnalyzer
from app.trading.strategy_engine import (
    ArbitrageStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    TradingStrategy,
    TradeSignal,
    TradeExecution,
    StrategyType,
    TradeDirection,
    ExecutionPriority,
    RiskParameters
)
from app.trading.strategy_engine_part2 import (
    EventDrivenStrategy,
    SmartMoneyStrategy,
    StrategyEngine
)
from app.wallet.erc6551 import SmartWallet
from app.utils.config import config


class TradingStrategyManager:
    """
    Manager for trading strategies and execution.
    
    This class provides the main interface for trading strategy execution,
    manages strategy lifecycle, and exposes API endpoints for the agent.
    """
    
    def __init__(self):
        """Initialize the trading strategy manager."""
        self.polymarket_client = None
        self.polysights_client = None
        self.market_analyzer = None
        self.wallet = None
        self.strategy_engine = None
        self.initialized = False
        self.background_tasks = []
        
        logger.info("Initialized TradingStrategyManager")
    
    async def initialize(
        self, 
        polymarket_client: PolymarketClient,
        polysights_client: PolysightsClient,
        wallet: SmartWallet
    ):
        """
        Initialize the trading strategy manager with required components.
        
        Args:
            polymarket_client: Client for Polymarket API
            polysights_client: Client for Polysights API
            wallet: Smart wallet for trade execution
        """
        if self.initialized:
            return
        
        self.polymarket_client = polymarket_client
        self.polysights_client = polysights_client
        self.wallet = wallet
        
        # Initialize market analyzer
        self.market_analyzer = MarketAnalyzer(
            self.polymarket_client,
            self.polysights_client
        )
        
        # Initialize strategy engine
        self.strategy_engine = StrategyEngine(
            self.polymarket_client,
            self.polysights_client,
            self.market_analyzer,
            self.wallet
        )
        
        self.initialized = True
        logger.info("Trading strategy manager initialized")
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available trading strategies."""
        if self.strategy_engine:
            return self.strategy_engine.get_available_strategies()
        return ["arbitrage", "momentum", "mean_reversion", "event_driven", "smart_money"]
    
    async def start(self):
        """Start the trading strategy manager and all components."""
        if not self.initialized:
            raise RuntimeError("Trading strategy manager not initialized")
        
        logger.info("Starting trading strategy manager")
        
        # Start market analyzer
        await self.market_analyzer.start()
        
        # Start strategy engine
        await self.strategy_engine.start()
        
        # Start background monitoring tasks
        self._start_background_tasks()
        
        logger.info("Trading strategy manager started")
    
    async def stop(self):
        """Stop the trading strategy manager and all components."""
        logger.info("Stopping trading strategy manager")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Stop strategy engine
        if self.strategy_engine:
            await self.strategy_engine.stop()
        
        # Stop market analyzer
        if self.market_analyzer:
            await self.market_analyzer.stop()
        
        logger.info("Trading strategy manager stopped")
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        self.background_tasks = [
            asyncio.create_task(self._monitor_portfolio()),
            asyncio.create_task(self._monitor_positions())
        ]
    
    async def _monitor_portfolio(self):
        """Monitor portfolio performance and risk."""
        try:
            while True:
                # Get current portfolio from wallet
                portfolio = await self.wallet.get_portfolio()
                
                # Update portfolio metrics
                await self._update_portfolio_metrics(portfolio)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
        except asyncio.CancelledError:
            logger.info("Portfolio monitoring stopped")
        except Exception as e:
            logger.error(f"Error in portfolio monitoring: {e}")
    
    async def _monitor_positions(self):
        """Monitor active positions and manage stop-loss/take-profit."""
        try:
            while True:
                if not self.strategy_engine:
                    await asyncio.sleep(5)
                    continue
                
                # Get positions from strategy engine
                positions = self.strategy_engine.positions
                
                # Check each position for stop-loss/take-profit
                for position_key, position in positions.items():
                    await self._check_position_limits(position_key, position)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
        except asyncio.CancelledError:
            logger.info("Position monitoring stopped")
        except Exception as e:
            logger.error(f"Error in position monitoring: {e}")
    
    async def _update_portfolio_metrics(self, portfolio: Dict[str, Any]):
        """
        Update portfolio metrics.
        
        Args:
            portfolio: Portfolio data from wallet
        """
        try:
            if self.strategy_engine:
                # Calculate portfolio value
                portfolio_value = portfolio.get("total_value", 0)
                
                # Update daily P&L if needed
                current_pnl = portfolio.get("daily_pnl", 0)
                if self.strategy_engine.daily_pnl != current_pnl:
                    self.strategy_engine.daily_pnl = current_pnl
                
                # Check risk limits
                if current_pnl < -self.strategy_engine.risk_params.max_daily_loss:
                    logger.warning(f"Daily loss limit exceeded: {current_pnl} < -{self.strategy_engine.risk_params.max_daily_loss}")
                    # In a real implementation, we might pause trading here
        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {e}")
    
    async def _check_position_limits(self, position_key: str, position: Dict[str, Any]):
        """
        Check position for stop-loss and take-profit.
        
        Args:
            position_key: Key identifying the position
            position: Position data
        """
        try:
            if not self.strategy_engine:
                return
                
            market_id = position.get("market_id")
            outcome_id = position.get("outcome_id")
            
            if not market_id or not outcome_id:
                return
                
            # Get current price
            current_price = await self._get_current_price(market_id, outcome_id)
            
            if current_price <= 0:
                return
                
            entry_price = position.get("price", 0)
            direction = position.get("direction")
            size = position.get("size", 0)
            
            if entry_price <= 0 or not direction or size <= 0:
                return
                
            # Calculate profit/loss percentage
            if direction == TradeDirection.BUY:
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Check stop-loss
            if pnl_pct <= -self.strategy_engine.risk_params.stop_loss_percentage:
                # Stop loss triggered
                logger.warning(f"Stop-loss triggered for position {position_key}: {pnl_pct:.2%}")
                await self._close_position(position_key, position, "stop_loss")
                
            # Check take-profit
            elif pnl_pct >= self.strategy_engine.risk_params.take_profit_percentage:
                # Take profit triggered
                logger.info(f"Take-profit triggered for position {position_key}: {pnl_pct:.2%}")
                await self._close_position(position_key, position, "take_profit")
                
        except Exception as e:
            logger.error(f"Error checking position limits for {position_key}: {e}")
    
    async def _close_position(self, position_key: str, position: Dict[str, Any], reason: str):
        """
        Close a position.
        
        Args:
            position_key: Key identifying the position
            position: Position data
            reason: Reason for closing (stop_loss, take_profit)
        """
        try:
            if not self.strategy_engine or not self.polymarket_client:
                return
                
            market_id = position.get("market_id")
            outcome_id = position.get("outcome_id")
            direction = position.get("direction")
            size = position.get("size", 0)
            
            if not market_id or not outcome_id or not direction or size <= 0:
                return
                
            # Close with opposite order
            close_direction = TradeDirection.SELL if direction == TradeDirection.BUY else TradeDirection.BUY
            
            # Create a market order
            result = await self.polymarket_client.place_order(
                market_id=market_id,
                outcome_id=outcome_id,
                side="sell" if close_direction == TradeDirection.SELL else "buy",
                size=size,
                price=0  # Market order
            )
            
            # Remove position
            if position_key in self.strategy_engine.positions:
                del self.strategy_engine.positions[position_key]
                
            logger.info(f"Closed position {position_key} due to {reason}")
            
        except Exception as e:
            logger.error(f"Error closing position {position_key}: {e}")
    
    async def _get_current_price(self, market_id: str, outcome_id: str) -> float:
        """
        Get current price for an outcome.
        
        Args:
            market_id: ID of the market
            outcome_id: ID of the outcome
            
        Returns:
            Current price
        """
        try:
            if not self.polymarket_client:
                return 0.0
                
            order_book = await self.polymarket_client.get_order_book(market_id)
            
            outcome_asks = [o for o in order_book.get("asks", []) if o.get("outcome_id") == outcome_id]
            outcome_bids = [o for o in order_book.get("bids", []) if o.get("outcome_id") == outcome_id]
            
            if outcome_asks and outcome_bids:
                best_ask = min(outcome_asks, key=lambda x: x.get("price", 1))
                best_bid = max(outcome_bids, key=lambda x: x.get("price", 0))
                
                return (best_ask.get("price", 1) + best_bid.get("price", 0)) / 2
                
            elif outcome_asks:
                best_ask = min(outcome_asks, key=lambda x: x.get("price", 1))
                return best_ask.get("price", 1)
                
            elif outcome_bids:
                best_bid = max(outcome_bids, key=lambda x: x.get("price", 0))
                return best_bid.get("price", 0)
                
            return 0.5  # Default midpoint
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return 0.0
    
    async def analyze_market(self, market_id: str) -> Dict[str, Any]:
        """
        Analyze a market using the market analyzer.
        
        Args:
            market_id: ID of the market to analyze
            
        Returns:
            Analysis results
        """
        if not self.market_analyzer:
            return {"error": "Market analyzer not initialized"}
            
        try:
            return await self.market_analyzer.analyze_market(market_id)
        except Exception as e:
            logger.error(f"Error analyzing market {market_id}: {e}")
            return {"error": str(e)}
    
    async def generate_signals(self, market_id: str) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a market using all strategies.
        
        Args:
            market_id: ID of the market to analyze
            
        Returns:
            List of trading signals
        """
        if not self.strategy_engine:
            return []
            
        try:
            all_signals = []
            
            # Generate signals from each strategy
            for strategy_type, strategy in self.strategy_engine.strategies.items():
                if strategy and config.trading.enabled_strategies.get(strategy_type, True):
                    signals = await strategy.analyze_market(market_id)
                    all_signals.extend(signals)
            
            # Convert to dictionaries for API response
            return [signal.dict() for signal in all_signals]
            
        except Exception as e:
            logger.error(f"Error generating signals for market {market_id}: {e}")
            return []
    
    async def execute_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading signal.
        
        Args:
            signal_data: Trading signal data
            
        Returns:
            Execution result
        """
        if not self.strategy_engine:
            return {"error": "Strategy engine not initialized"}
            
        try:
            # Convert dictionary to TradeSignal
            signal = TradeSignal(**signal_data)
            
            # Submit to strategy engine
            await self.strategy_engine.submit_signal(signal)
            
            return {"success": True, "message": f"Signal {signal.signal_id} submitted for execution"}
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all strategies.
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.strategy_engine:
            return {"error": "Strategy engine not initialized"}
            
        try:
            return self.strategy_engine.get_performance_metrics()
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get active positions.
        
        Returns:
            List of active positions
        """
        if not self.strategy_engine:
            return []
            
        try:
            return list(self.strategy_engine.positions.values())
        except Exception as e:
            logger.error(f"Error getting active positions: {e}")
            return []
    
    def get_enabled_strategies(self) -> Dict[str, bool]:
        """
        Get enabled strategies configuration.
        
        Returns:
            Dictionary of enabled strategies
        """
        return config.trading.enabled_strategies


# Global instance
trading_manager = TradingStrategyManager()

def get_trading_manager() -> TradingStrategyManager:
    """Get the global trading manager instance."""
    return trading_manager


# Alias for backward compatibility
TradingStrategyEngine = TradingStrategyManager
