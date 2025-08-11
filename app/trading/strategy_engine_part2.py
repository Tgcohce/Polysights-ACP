"""
Trading Strategy Engine for ACP Polymarket Trading Agent - Part 2.

This module implements the remaining strategy classes (EventDriven and SmartMoney)
and the main StrategyEngine class that coordinates all strategies.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple

from loguru import logger

from app.polymarket.client import PolymarketClient
from app.polysights.client import PolysightsClient
from app.trading.market_analyzer import MarketAnalyzer
from app.trading.strategy_engine import (
    TradingStrategy,
    TradeSignal,
    TradeExecution,
    StrategyType,
    TradeDirection,
    ExecutionPriority,
    RiskParameters,
    StrategyParameters,
    EventDrivenParameters,
    SmartMoneyParameters,
    ArbitrageStrategy,
    MomentumStrategy,
    MeanReversionStrategy
)
from app.wallet.erc6551 import SmartWallet
from app.utils.config import config


class EventDrivenStrategy(TradingStrategy):
    """
    Event-driven trading strategy.
    
    Identifies trading opportunities based on external events like news,
    social media sentiment, and on-chain activities.
    """
    
    def _default_params(self) -> StrategyParameters:
        return EventDrivenParameters()
    
    def strategy_type(self) -> StrategyType:
        return StrategyType.EVENT_DRIVEN
    
    async def analyze_market(self, market_id: str) -> List[TradeSignal]:
        """
        Analyze a market for event-driven opportunities.
        
        Args:
            market_id: ID of the market to analyze
            
        Returns:
            List of trade signals for event-driven opportunities
        """
        signals = []
        
        try:
            # Get market data
            market_data = await self.polymarket_client.get_market(market_id)
            if not market_data:
                return signals
            
            params = self.strategy_params
            if not isinstance(params, EventDrivenParameters):
                params = EventDrivenParameters()
            
            # Get market metadata
            market_title = market_data.get("title", "")
            market_description = market_data.get("description", "")
            market_category = market_data.get("category", "")
            
            # Fetch relevant events from Polysights
            events = await self.polysights_client.get_events(
                query=market_title,
                categories=params.event_types,
                limit=10,
                min_confidence=0.6
            )
            
            if not events:
                return signals
            
            # Group events by outcome
            outcome_events = {}
            for outcome in market_data.get("outcomes", []):
                outcome_id = outcome.get("id")
                outcome_title = outcome.get("title", "")
                
                # Find events relevant to this outcome
                relevant_events = []
                for event in events:
                    # Check if event is related to outcome
                    # This is a simplified check - in a real implementation,
                    # we would use NLP to determine relevance
                    if outcome_title.lower() in event.get("text", "").lower():
                        relevance_score = event.get("relevance", 0.5)
                        if relevance_score > 0.7:
                            relevant_events.append(event)
                
                if relevant_events:
                    outcome_events[outcome_id] = relevant_events
            
            # Process events for each outcome
            for outcome_id, events in outcome_events.items():
                # Calculate aggregate sentiment
                sentiments = [event.get("sentiment", 0) for event in events]
                if not sentiments:
                    continue
                    
                avg_sentiment = sum(sentiments) / len(sentiments)
                
                # Check if sentiment exceeds threshold
                if abs(avg_sentiment) > params.sentiment_threshold:
                    # Check volume spike
                    volume_spike = await self._check_volume_spike(market_id, outcome_id, params.volume_spike_threshold)
                    
                    # Only proceed if volume confirms sentiment
                    if volume_spike:
                        # Higher sentiment and more events = higher confidence
                        direction = TradeDirection.BUY if avg_sentiment > 0 else TradeDirection.SELL
                        confidence = min(0.9, 0.6 + abs(avg_sentiment) * 0.5)
                        
                        # Get current price
                        current_price = await self._get_current_price(market_id, outcome_id)
                        if current_price <= 0:
                            continue
                            
                        # Calculate position size
                        position_size = self.risk_params.max_position_size * confidence * 0.8  # More conservative
                        
                        # Get source count
                        source_count = len(set(event.get("source") for event in events if event.get("source")))
                        
                        # Only generate signal if we have multiple sources
                        if source_count >= params.confirmation_sources:
                            signal = TradeSignal(
                                strategy_type=StrategyType.EVENT_DRIVEN,
                                market_id=market_id,
                                outcome_id=outcome_id,
                                direction=direction,
                                price=current_price,
                                size=position_size,
                                confidence=confidence,
                                priority=ExecutionPriority.HIGH if abs(avg_sentiment) > 0.8 else ExecutionPriority.MEDIUM,
                                expiry=datetime.now() + timedelta(minutes=params.reaction_time_seconds / 60),
                                reason=f"Event-driven signal with sentiment {avg_sentiment:.2f} from {len(events)} events",
                                metadata={
                                    "sentiment": avg_sentiment,
                                    "event_count": len(events),
                                    "source_count": source_count,
                                    "volume_spike": volume_spike
                                },
                                source_data={
                                    "events": [e.get("text") for e in events][:3]  # Include top 3 events
                                }
                            )
                            signals.append(signal)
            
            self.signals_generated += len(signals)
            return signals
            
        except Exception as e:
            logger.error(f"Error in event-driven analysis for market {market_id}: {e}")
            return []
    
    async def _check_volume_spike(self, market_id: str, outcome_id: str, threshold: float) -> bool:
        """
        Check if there's a volume spike for an outcome.
        
        Args:
            market_id: ID of the market
            outcome_id: ID of the outcome
            threshold: Volume spike threshold
            
        Returns:
            True if volume spike detected
        """
        try:
            # Get volume history
            volume_history = await self.polymarket_client.get_volume_history(
                market_id=market_id,
                time_resolution="5m",
                limit=24  # Last 2 hours (5m intervals)
            )
            
            outcome_volumes = [v for v in volume_history if v.get("outcome_id") == outcome_id]
            
            if len(outcome_volumes) < 3:
                return False
                
            # Calculate recent volume vs earlier volume
            recent_volume = sum(v.get("volume", 0) for v in outcome_volumes[:3])
            earlier_volume = sum(v.get("volume", 0) for v in outcome_volumes[3:12]) / 3  # Average over 9 periods
            
            if earlier_volume <= 0:
                return False
                
            volume_ratio = recent_volume / earlier_volume
            return volume_ratio > threshold
            
        except Exception as e:
            logger.error(f"Error checking volume spike: {e}")
            return False
    
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


class SmartMoneyStrategy(TradingStrategy):
    """
    Smart Money tracking strategy.
    
    Identifies and follows trades made by profitable wallets
    (whales and historically successful traders).
    """
    
    def _default_params(self) -> StrategyParameters:
        return SmartMoneyParameters()
    
    def strategy_type(self) -> StrategyType:
        return StrategyType.SMART_MONEY
    
    async def analyze_market(self, market_id: str) -> List[TradeSignal]:
        """
        Analyze a market for smart money opportunities.
        
        Args:
            market_id: ID of the market to analyze
            
        Returns:
            List of trade signals for smart money opportunities
        """
        signals = []
        
        try:
            # Get market data
            market_data = await self.polymarket_client.get_market(market_id)
            if not market_data:
                return signals
            
            params = self.strategy_params
            if not isinstance(params, SmartMoneyParameters):
                params = SmartMoneyParameters()
            
            # Get smart money wallets from Polysights
            smart_wallets = await self.polysights_client.get_smart_wallets(
                min_trade_value=params.whale_threshold,
                min_wallet_age_days=params.min_wallet_age_days,
                limit=20
            )
            
            if not smart_wallets:
                return signals
            
            # Get recent trades for this market
            recent_trades = await self.polymarket_client.get_recent_trades(
                market_id=market_id,
                limit=100
            )
            
            if not recent_trades:
                return signals
            
            # Filter trades by smart wallets
            smart_wallet_addresses = {w.get("address") for w in smart_wallets}
            smart_trades = [
                trade for trade in recent_trades
                if trade.get("wallet_address") in smart_wallet_addresses
                and trade.get("value", 0) >= params.whale_threshold
            ]
            
            if not smart_trades:
                return signals
            
            # Group trades by outcome and direction
            outcome_directions = {}
            
            for trade in smart_trades:
                outcome_id = trade.get("outcome_id")
                direction = trade.get("direction")
                
                if not outcome_id or not direction:
                    continue
                    
                key = (outcome_id, direction)
                if key not in outcome_directions:
                    outcome_directions[key] = []
                    
                outcome_directions[key].append(trade)
            
            # Look for consensus among smart money
            for (outcome_id, direction), trades in outcome_directions.items():
                # Check if we have enough smart money wallets moving in same direction
                if len(trades) >= params.follow_threshold:
                    # Check if trades are within time window
                    now = datetime.now()
                    recent_trades = [
                        t for t in trades
                        if now - datetime.fromisoformat(t.get("timestamp")) <= timedelta(minutes=params.time_window_minutes)
                    ]
                    
                    if len(recent_trades) >= params.follow_threshold:
                        # Smart money consensus found
                        # Calculate average position size and price
                        avg_size = sum(t.get("size", 0) for t in recent_trades) / len(recent_trades)
                        avg_price = sum(t.get("price", 0) * t.get("size", 0) for t in recent_trades) / sum(t.get("size", 0) for t in recent_trades)
                        
                        # Calculate confidence based on number of wallets and their success rate
                        wallet_success_rates = [
                            w.get("success_rate", 0.5) for w in smart_wallets
                            if w.get("address") in {t.get("wallet_address") for t in recent_trades}
                        ]
                        
                        avg_success_rate = sum(wallet_success_rates) / len(wallet_success_rates) if wallet_success_rates else 0.7
                        confidence = min(0.95, avg_success_rate)
                        
                        # Get current price
                        current_price = await self._get_current_price(market_id, outcome_id)
                        if current_price <= 0:
                            continue
                        
                        # Generate trade signal
                        trade_direction = TradeDirection.BUY if direction == "buy" else TradeDirection.SELL
                        
                        signal = TradeSignal(
                            strategy_type=StrategyType.SMART_MONEY,
                            market_id=market_id,
                            outcome_id=outcome_id,
                            direction=trade_direction,
                            price=current_price,
                            size=min(avg_size, self.risk_params.max_position_size),  # Cap at max position size
                            confidence=confidence,
                            priority=ExecutionPriority.HIGH,  # Smart money is high priority
                            expiry=datetime.now() + timedelta(hours=4),  # Longer expiry for smart money signals
                            reason=f"Smart money consensus with {len(recent_trades)} wallets",
                            metadata={
                                "wallet_count": len(recent_trades),
                                "avg_success_rate": avg_success_rate,
                                "avg_trade_size": avg_size,
                                "avg_trade_price": avg_price
                            },
                            source_data={
                                "smart_wallets": [t.get("wallet_address") for t in recent_trades[:5]]
                            }
                        )
                        signals.append(signal)
            
            self.signals_generated += len(signals)
            return signals
            
        except Exception as e:
            logger.error(f"Error in smart money analysis for market {market_id}: {e}")
            return []
    
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


class StrategyEngine:
    """
    Trading strategy engine that coordinates multiple trading strategies.
    
    This class manages strategy execution, signal processing, risk management,
    and portfolio allocation across different strategies.
    """
    
    def __init__(
        self,
        polymarket_client: PolymarketClient,
        polysights_client: PolysightsClient,
        market_analyzer: MarketAnalyzer,
        wallet: SmartWallet
    ):
        """
        Initialize the strategy engine.
        
        Args:
            polymarket_client: Client for Polymarket API
            polysights_client: Client for Polysights API
            market_analyzer: Market analyzer for market data and analysis
            wallet: Smart wallet for trade execution
        """
        self.polymarket_client = polymarket_client
        self.polysights_client = polysights_client
        self.market_analyzer = market_analyzer
        self.wallet = wallet
        
        # Initialize risk parameters
        self.risk_params = RiskParameters(
            max_position_size=config.trading.max_position_size,
            max_position_percentage=config.trading.max_position_percentage,
            max_daily_loss=config.trading.max_daily_loss,
            stop_loss_percentage=config.trading.stop_loss_percentage,
            take_profit_percentage=config.trading.take_profit_percentage
        )
        
        # Initialize strategies
        self.strategies = {}
        self._initialize_strategies()
        
        # Signal processing
        self.signal_processor_task = None
        self.signal_queue = asyncio.Queue()
        self.execution_history = []
        self.active_signals = set()
        
        # Portfolio tracking
        self.positions = {}
        self.daily_pnl = 0.0
        self.trade_count = 0
        self.active = False
        
        logger.info("Initialized StrategyEngine")
    
    def _initialize_strategies(self):
        """Initialize trading strategies."""
        # Create strategy instances
        self.strategies[StrategyType.ARBITRAGE] = ArbitrageStrategy(
            self.polymarket_client,
            self.polysights_client,
            self.market_analyzer,
            self.wallet,
            self.risk_params
        )
        
        self.strategies[StrategyType.MOMENTUM] = MomentumStrategy(
            self.polymarket_client,
            self.polysights_client,
            self.market_analyzer,
            self.wallet,
            self.risk_params
        )
        
        self.strategies[StrategyType.MEAN_REVERSION] = MeanReversionStrategy(
            self.polymarket_client,
            self.polysights_client,
            self.market_analyzer,
            self.wallet,
            self.risk_params
        )
        
        self.strategies[StrategyType.EVENT_DRIVEN] = EventDrivenStrategy(
            self.polymarket_client,
            self.polysights_client,
            self.market_analyzer,
            self.wallet,
            self.risk_params
        )
        
        self.strategies[StrategyType.SMART_MONEY] = SmartMoneyStrategy(
            self.polymarket_client,
            self.polysights_client,
            self.market_analyzer,
            self.wallet,
            self.risk_params
        )
    
    async def start(self):
        """Start the strategy engine and all strategies."""
        if self.active:
            return
            
        logger.info("Starting StrategyEngine")
        self.active = True
        
        # Start signal processor
        self.signal_processor_task = asyncio.create_task(self._process_signals())
        
        # Start strategies
        for strategy_type, strategy in self.strategies.items():
            if strategy and config.trading.enabled_strategies.get(strategy_type, True):
                await strategy.start()
    
    async def stop(self):
        """Stop the strategy engine and all strategies."""
        if not self.active:
            return
            
        logger.info("Stopping StrategyEngine")
        self.active = False
        
        # Stop strategies
        for strategy in self.strategies.values():
            if strategy:
                await strategy.stop()
        
        # Stop signal processor
        if self.signal_processor_task:
            self.signal_processor_task.cancel()
            try:
                await self.signal_processor_task
            except asyncio.CancelledError:
                pass
    
    async def submit_signal(self, signal: TradeSignal):
        """
        Submit a trade signal for processing.
        
        Args:
            signal: Trade signal to process
        """
        if not self.active:
            logger.warning("Strategy engine is not active, signal ignored")
            return
            
        logger.info(f"Received {signal.strategy_type} signal for market {signal.market_id}")
        await self.signal_queue.put(signal)
    
    async def _process_signals(self):
        """Process trade signals from the queue."""
        try:
            while self.active:
                # Get signal from queue
                signal = await self.signal_queue.get()
                
                try:
                    # Check if signal is still valid
                    if datetime.now() > signal.expiry:
                        logger.warning(f"Signal {signal.signal_id} expired, skipping")
                        continue
                    
                    # Check if signal is unique (no duplicate processing)
                    if signal.signal_id in self.active_signals:
                        logger.warning(f"Signal {signal.signal_id} already being processed, skipping")
                        continue
                    
                    self.active_signals.add(signal.signal_id)
                    
                    # Apply portfolio-level risk management
                    if not self._validate_portfolio_risk(signal):
                        logger.warning(f"Signal {signal.signal_id} rejected by portfolio risk management")
                        self.active_signals.remove(signal.signal_id)
                        continue
                    
                    # Execute trade
                    strategy = self.strategies.get(signal.strategy_type)
                    if strategy:
                        execution = await strategy._execute_signal(signal)
                        
                        # Record execution
                        self.execution_history.append(execution)
                        
                        # Update positions if successful
                        if execution.status == "executed":
                            await self._update_positions(signal, execution)
                            
                            # Track daily P&L
                            self.trade_count += 1
                    
                    # Remove from active signals
                    self.active_signals.remove(signal.signal_id)
                    
                except Exception as e:
                    logger.error(f"Error processing signal {signal.signal_id}: {e}")
                    
                    # Remove from active signals on error
                    if signal.signal_id in self.active_signals:
                        self.active_signals.remove(signal.signal_id)
                
                finally:
                    # Mark task as done
                    self.signal_queue.task_done()
                
        except asyncio.CancelledError:
            logger.info("Signal processor stopped")
        except Exception as e:
            logger.error(f"Error in signal processor: {e}")
    
    def _validate_portfolio_risk(self, signal: TradeSignal) -> bool:
        """
        Apply portfolio-level risk management to a signal.
        
        Args:
            signal: Trade signal to validate
            
        Returns:
            True if signal passes portfolio risk validation
        """
        # Check if we've hit daily loss limit
        if self.daily_pnl < -self.risk_params.max_daily_loss:
            logger.warning(f"Daily loss limit reached: {self.daily_pnl} < -{self.risk_params.max_daily_loss}")
            return False
        
        # Check maximum number of concurrent positions
        if len(self.positions) >= self.risk_params.max_concurrent_positions:
            logger.warning(f"Maximum concurrent positions reached: {len(self.positions)} >= {self.risk_params.max_concurrent_positions}")
            return False
        
        # Check exposure to this market
        market_exposure = sum(
            p.get("value", 0) for p in self.positions.values()
            if p.get("market_id") == signal.market_id
        )
        
        # Calculate total portfolio value (simplified)
        portfolio_value = 10000  # In a real implementation, we would get this from wallet
        
        # Check if adding this position would exceed max market exposure
        position_value = signal.price * signal.size
        new_exposure = market_exposure + position_value
        max_exposure = portfolio_value * self.risk_params.max_position_percentage
        
        if new_exposure > max_exposure:
            logger.warning(f"Market exposure limit reached: {new_exposure} > {max_exposure}")
            return False
        
        # Check for conflicting positions (e.g., both long and short on same outcome)
        position_key = f"{signal.market_id}_{signal.outcome_id}"
        if position_key in self.positions:
            existing_position = self.positions[position_key]
            existing_direction = existing_position.get("direction")
            
            # If directions conflict, reject the signal
            if existing_direction != signal.direction:
                logger.warning(f"Conflicting positions for {position_key}: {existing_direction} vs {signal.direction}")
                return False
        
        return True
    
    async def _update_positions(self, signal: TradeSignal, execution: TradeExecution):
        """
        Update positions after a trade execution.
        
        Args:
            signal: Trade signal that was executed
            execution: Execution result
        """
        position_key = f"{signal.market_id}_{signal.outcome_id}"
        position_value = execution.executed_price * execution.executed_size
        
        # Update position
        if position_key in self.positions:
            # Update existing position
            existing_position = self.positions[position_key]
            
            # Calculate new average price and size
            existing_size = existing_position.get("size", 0)
            existing_price = existing_position.get("price", 0)
            existing_value = existing_size * existing_price
            
            new_size = existing_size + execution.executed_size
            new_value = existing_value + position_value
            new_price = new_value / new_size if new_size > 0 else 0
            
            # Update position
            self.positions[position_key] = {
                "market_id": signal.market_id,
                "outcome_id": signal.outcome_id,
                "direction": signal.direction,
                "price": new_price,
                "size": new_size,
                "value": new_value,
                "last_updated": datetime.now()
            }
        else:
            # Create new position
            self.positions[position_key] = {
                "market_id": signal.market_id,
                "outcome_id": signal.outcome_id,
                "direction": signal.direction,
                "price": execution.executed_price,
                "size": execution.executed_size,
                "value": position_value,
                "last_updated": datetime.now()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all strategies.
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = {
            "total_trades": self.trade_count,
            "active_positions": len(self.positions),
            "daily_pnl": self.daily_pnl,
            "strategies": {}
        }
        
        # Add metrics for each strategy
        for strategy_type, strategy in self.strategies.items():
            if strategy:
                metrics["strategies"][strategy_type] = strategy.get_performance_metrics()
        
        return metrics


# Global instance
strategy_engine = None

def initialize_strategy_engine(
    polymarket_client: PolymarketClient,
    polysights_client: PolysightsClient,
    market_analyzer: MarketAnalyzer,
    wallet: SmartWallet
):
    """Initialize the global strategy engine instance."""
    global strategy_engine
    strategy_engine = StrategyEngine(polymarket_client, polysights_client, market_analyzer, wallet)
    return strategy_engine
