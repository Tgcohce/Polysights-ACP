"""
Event monitoring system for ACP Polymarket Trading Agent.

This module provides real-time monitoring of events and triggers
for market conditions, price movements, and other relevant signals.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable, Awaitable, Union
import uuid

from loguru import logger

from app.trading.event_models import (
    Event, 
    EventTrigger,
    TriggerResult,
    EventCategory,
    EventSource,
    EventSeverity,
    ActionType,
    TriggerAction
)
from app.polymarket.client import PolymarketClient
from app.polysights.client import PolysightsClient
from app.dashboard.service import DashboardService
from app.trading.strategy_engine_main import TradingStrategyManager
from app.utils.config import config


class EventMonitor:
    """
    Core event monitoring system.
    
    This class is responsible for detecting, processing, and responding to events
    across the trading system. It manages triggers and executes actions when
    conditions are met.
    """
    
    def __init__(
        self,
        polymarket_client: PolymarketClient,
        polysights_client: PolysightsClient,
        trading_manager: Optional[TradingStrategyManager] = None,
        dashboard_service: Optional[DashboardService] = None
    ):
        """
        Initialize the event monitor.
        
        Args:
            polymarket_client: Client for Polymarket API
            polysights_client: Client for Polysights API
            trading_manager: Trading strategy manager (optional)
            dashboard_service: Dashboard service (optional)
        """
        self.polymarket_client = polymarket_client
        self.polysights_client = polysights_client
        self.trading_manager = trading_manager
        self.dashboard_service = dashboard_service
        
        # Event storage
        self.events: List[Event] = []
        self.max_events = 1000  # Maximum events to keep in memory
        
        # Trigger storage
        self.triggers: Dict[str, EventTrigger] = {}
        
        # Trigger results
        self.trigger_results: List[TriggerResult] = []
        self.max_results = 1000  # Maximum results to keep in memory
        
        # Background tasks
        self.running = False
        self.tasks = []
        
        # Monitoring intervals (seconds)
        self.price_interval = 30
        self.volume_interval = 60
        self.social_interval = 300
        self.news_interval = 600
        self.onchain_interval = 120
        
        # Event listeners
        self.event_listeners: List[Callable[[Event], Awaitable[None]]] = []
        
        logger.info("Initialized EventMonitor")
    
    async def start(self):
        """Start the event monitor."""
        if self.running:
            return
        
        logger.info("Starting EventMonitor")
        self.running = True
        
        # Start monitoring tasks
        self.tasks = [
            asyncio.create_task(self._monitor_prices()),
            asyncio.create_task(self._monitor_volumes()),
            asyncio.create_task(self._monitor_social()),
            asyncio.create_task(self._process_events())
        ]
    
    async def stop(self):
        """Stop the event monitor."""
        if not self.running:
            return
        
        logger.info("Stopping EventMonitor")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks = []
    
    async def add_event(self, event: Event) -> str:
        """
        Add a new event to the monitor.
        
        Args:
            event: Event to add
            
        Returns:
            Event ID
        """
        # Store event
        self.events.append(event)
        
        # Prune old events if needed
        if len(self.events) > self.max_events:
            # Remove oldest events, keeping the most recent max_events
            self.events = sorted(
                self.events, 
                key=lambda x: x.timestamp, 
                reverse=True
            )[:self.max_events]
        
        # Notify listeners
        for listener in self.event_listeners:
            try:
                await listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
        
        logger.debug(f"Added event: {event.title} ({event.event_id})")
        return event.event_id
    
    def add_trigger(self, trigger: EventTrigger) -> str:
        """
        Add a new trigger to the monitor.
        
        Args:
            trigger: Trigger to add
            
        Returns:
            Trigger ID
        """
        self.triggers[trigger.trigger_id] = trigger
        logger.debug(f"Added trigger: {trigger.name} ({trigger.trigger_id})")
        return trigger.trigger_id
    
    def remove_trigger(self, trigger_id: str) -> bool:
        """
        Remove a trigger from the monitor.
        
        Args:
            trigger_id: ID of the trigger to remove
            
        Returns:
            True if the trigger was removed, False otherwise
        """
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            logger.debug(f"Removed trigger {trigger_id}")
            return True
        
        logger.warning(f"Trigger {trigger_id} not found")
        return False
    
    def get_trigger(self, trigger_id: str) -> Optional[EventTrigger]:
        """
        Get a trigger by ID.
        
        Args:
            trigger_id: ID of the trigger
            
        Returns:
            Trigger if found, None otherwise
        """
        return self.triggers.get(trigger_id)
    
    def get_triggers(
        self, 
        category: Optional[EventCategory] = None, 
        source: Optional[EventSource] = None
    ) -> List[EventTrigger]:
        """
        Get triggers filtered by category and source.
        
        Args:
            category: Category to filter by (optional)
            source: Source to filter by (optional)
            
        Returns:
            List of matching triggers
        """
        result = []
        
        for trigger in self.triggers.values():
            if not trigger.enabled:
                continue
                
            if category and category not in trigger.categories:
                continue
                
            if source and source not in trigger.sources:
                continue
                
            result.append(trigger)
        
        return result
    
    def get_events(
        self,
        category: Optional[EventCategory] = None,
        source: Optional[EventSource] = None,
        min_severity: Optional[EventSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        market_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events filtered by various criteria.
        
        Args:
            category: Category to filter by (optional)
            source: Source to filter by (optional)
            min_severity: Minimum severity level (optional)
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
            market_id: Market ID filter (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of matching events
        """
        result = []
        
        for event in self.events:
            if category and event.category != category:
                continue
                
            if source and event.source != source:
                continue
                
            if min_severity and event.severity.value < min_severity.value:
                continue
                
            if start_time and event.timestamp < start_time:
                continue
                
            if end_time and event.timestamp > end_time:
                continue
                
            if market_id and event.market_id != market_id:
                continue
                
            result.append(event)
        
        # Sort by timestamp (newest first)
        result = sorted(result, key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        return result[:limit]
    
    async def process_event(self, event: Event) -> List[TriggerResult]:
        """
        Process an event against all triggers.
        
        Args:
            event: Event to process
            
        Returns:
            List of trigger results
        """
        results = []
        
        # Get relevant triggers for this event
        triggers = self.get_triggers(category=event.category, source=event.source)
        
        # Process each trigger
        for trigger in triggers:
            result = await self._evaluate_trigger(trigger, event)
            
            if result:
                results.append(result)
                
                # Execute actions if the trigger matched
                if result.matched:
                    await self._execute_actions(trigger, event, result)
        
        # Store results
        self.trigger_results.extend(results)
        
        # Prune old results if needed
        if len(self.trigger_results) > self.max_results:
            # Remove oldest results
            self.trigger_results = sorted(
                self.trigger_results,
                key=lambda x: x.match_time,
                reverse=True
            )[:self.max_results]
        
        return results
    
    async def _evaluate_trigger(
        self, 
        trigger: EventTrigger, 
        event: Event
    ) -> Optional[TriggerResult]:
        """
        Evaluate a trigger against an event.
        
        Args:
            trigger: Trigger to evaluate
            event: Event to evaluate against
            
        Returns:
            Trigger result if evaluation was performed, None otherwise
        """
        # Skip if trigger is not enabled
        if not trigger.enabled:
            return None
        
        # Skip if event severity is below trigger minimum
        if event.severity.value < trigger.min_severity.value:
            return None
        
        # Skip if trigger is on cooldown
        if (trigger.last_triggered and trigger.cooldown_seconds > 0 and
            (datetime.now() - trigger.last_triggered).total_seconds() < trigger.cooldown_seconds):
            return None
        
        # Skip if trigger is expired
        if trigger.expiration and datetime.now() > trigger.expiration:
            return None
        
        # Check market/outcome filters
        if trigger.market_ids and event.market_id not in trigger.market_ids:
            return None
        
        if trigger.outcome_ids and event.outcome_id not in trigger.outcome_ids:
            return None
        
        # Initialize result
        result = TriggerResult(
            trigger_id=trigger.trigger_id,
            event_id=event.event_id,
            matched=False
        )
        
        # Evaluate conditions
        condition_results = {}
        for i, condition in enumerate(trigger.conditions):
            try:
                condition_met = await self._evaluate_condition(condition, event, trigger)
                condition_results[f"condition_{i}"] = condition_met
            except Exception as e:
                logger.error(f"Error evaluating condition: {e}")
                condition_results[f"condition_{i}"] = False
        
        result.condition_results = condition_results
        
        # Determine if trigger matches
        if trigger.condition_type == "all":
            result.matched = all(condition_results.values())
        elif trigger.condition_type == "any":
            result.matched = any(condition_results.values())
        else:
            result.matched = False
        
        # Update last triggered time
        if result.matched:
            trigger.last_triggered = datetime.now()
        
        return result
    
    async def _evaluate_condition(
        self, 
        condition: Dict[str, Any], 
        event: Event,
        trigger: EventTrigger
    ) -> bool:
        """
        Evaluate a single condition against an event.
        
        Args:
            condition: Condition to evaluate
            event: Event to evaluate against
            trigger: Parent trigger
            
        Returns:
            True if condition is met, False otherwise
        """
        # This is a simplified condition evaluator
        # In a real implementation, this would handle different condition types
        
        # Example: Check if a field in the event data matches a value
        if "field" in condition and "value" in condition:
            field = condition["field"]
            value = condition["value"]
            operator = condition.get("operator", "eq")
            
            # Check if the field exists in event data
            if field in event.data:
                event_value = event.data[field]
                
                if operator == "eq":
                    return event_value == value
                elif operator == "neq":
                    return event_value != value
                elif operator == "gt":
                    return event_value > value
                elif operator == "lt":
                    return event_value < value
                elif operator == "gte":
                    return event_value >= value
                elif operator == "lte":
                    return event_value <= value
                elif operator == "contains":
                    return value in event_value
                elif operator == "not_contains":
                    return value not in event_value
        
        return False
    
    async def _execute_actions(
        self, 
        trigger: EventTrigger, 
        event: Event, 
        result: TriggerResult
    ):
        """
        Execute actions for a triggered event.
        
        Args:
            trigger: Triggered trigger
            event: Event that triggered
            result: Trigger result
        """
        action_results = []
        
        for action in trigger.actions:
            action_result = {
                "action_type": action.action_type,
                "success": False,
                "message": None
            }
            
            try:
                if action.action_type == ActionType.NOTIFY:
                    success, message = await self._execute_notify_action(action, trigger, event)
                    action_result["success"] = success
                    action_result["message"] = message
                    
                elif action.action_type == ActionType.ALERT:
                    success, message = await self._execute_alert_action(action, trigger, event)
                    action_result["success"] = success
                    action_result["message"] = message
                    
                elif action.action_type == ActionType.TRADE:
                    success, message = await self._execute_trade_action(action, trigger, event)
                    action_result["success"] = success
                    action_result["message"] = message
                    
                elif action.action_type == ActionType.ADJUST_STRATEGY:
                    success, message = await self._execute_strategy_action(action, trigger, event)
                    action_result["success"] = success
                    action_result["message"] = message
                    
                elif action.action_type == ActionType.LOG:
                    # Just log the event
                    logger.info(f"Trigger {trigger.name} fired: {event.title}")
                    action_result["success"] = True
                    action_result["message"] = "Logged successfully"
                    
                else:
                    action_result["success"] = False
                    action_result["message"] = f"Unsupported action type: {action.action_type}"
                
            except Exception as e:
                logger.error(f"Error executing action {action.action_type}: {e}")
                action_result["success"] = False
                action_result["message"] = f"Error: {str(e)}"
            
            action_results.append(action_result)
        
        result.action_results = action_results
    
    async def _execute_notify_action(
        self, 
        action: TriggerAction, 
        trigger: EventTrigger, 
        event: Event
    ) -> Tuple[bool, str]:
        """
        Execute a notify action.
        
        Args:
            action: Action to execute
            trigger: Trigger that fired
            event: Event that triggered
            
        Returns:
            Success status and message
        """
        if not self.dashboard_service:
            return False, "Dashboard service not available"
        
        try:
            # Create notification
            from app.dashboard.models import DashboardNotification
            
            title = action.params.get("title", f"Event: {event.title}")
            message = action.params.get("message", event.description)
            
            notification = DashboardNotification(
                title=title,
                message=message,
                source=f"EventMonitor: {trigger.name}",
                action_url=action.params.get("action_url")
            )
            
            # Add to dashboard
            self.dashboard_service.add_notification(notification)
            
            return True, f"Created notification: {title}"
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return False, f"Error: {str(e)}"
    
    async def _execute_alert_action(
        self, 
        action: TriggerAction, 
        trigger: EventTrigger, 
        event: Event
    ) -> Tuple[bool, str]:
        """
        Execute an alert action.
        
        Args:
            action: Action to execute
            trigger: Trigger that fired
            event: Event that triggered
            
        Returns:
            Success status and message
        """
        if not self.dashboard_service:
            return False, "Dashboard service not available"
        
        try:
            # Create alert
            from app.dashboard.models import DashboardAlert
            
            title = action.params.get("title", f"Alert: {event.title}")
            message = action.params.get("message", event.description)
            severity = action.params.get("severity", "warning")
            
            alert = DashboardAlert(
                title=title,
                message=message,
                severity=severity,
                source=f"EventMonitor: {trigger.name}",
                details={
                    "event_id": event.event_id,
                    "trigger_id": trigger.trigger_id,
                    "category": event.category.value,
                    "market_id": event.market_id
                }
            )
            
            # Add to dashboard
            self.dashboard_service.add_alert(alert)
            
            return True, f"Created alert: {title} ({severity})"
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return False, f"Error: {str(e)}"
    
    async def _execute_trade_action(
        self, 
        action: TriggerAction, 
        trigger: EventTrigger, 
        event: Event
    ) -> Tuple[bool, str]:
        """
        Execute a trade action.
        
        Args:
            action: Action to execute
            trigger: Trigger that fired
            event: Event that triggered
            
        Returns:
            Success status and message
        """
        if not self.trading_manager:
            return False, "Trading manager not available"
        
        try:
            from app.trading.strategy_engine import TradeSignal, StrategyType, TradeDirection, ExecutionPriority
            
            # Extract trade parameters
            market_id = action.params.get("market_id") or event.market_id
            if not market_id:
                return False, "No market ID specified"
                
            outcome_id = action.params.get("outcome_id") or event.outcome_id
            if not outcome_id:
                return False, "No outcome ID specified"
                
            direction_str = action.params.get("direction", "BUY").upper()
            direction = TradeDirection[direction_str]
            
            size = float(action.params.get("size", 10.0))
            price = float(action.params.get("price", 0.0))
            
            strategy_type_str = action.params.get("strategy_type", "EVENT_DRIVEN").upper()
            strategy_type = StrategyType[strategy_type_str]
            
            priority_str = action.params.get("priority", "NORMAL").upper()
            priority = ExecutionPriority[priority_str]
            
            # Create trade signal
            signal = TradeSignal(
                signal_id=str(uuid.uuid4()),
                market_id=market_id,
                outcome_id=outcome_id,
                direction=direction,
                size=size,
                price=price,
                confidence=float(action.params.get("confidence", 0.8)),
                strategy=strategy_type,
                priority=priority,
                expiration=datetime.now() + timedelta(minutes=5),
                metadata={
                    "trigger_id": trigger.trigger_id,
                    "event_id": event.event_id,
                    "action": "automatic"
                }
            )
            
            # Submit signal
            result = await self.trading_manager.execute_signal(signal.dict())
            
            if result.get("success"):
                return True, f"Trade signal submitted: {market_id} {direction_str} {size} units"
            else:
                return False, f"Error submitting trade: {result.get('error', 'Unknown error')}"
            
        except Exception as e:
            logger.error(f"Error executing trade action: {e}")
            return False, f"Error: {str(e)}"
    
    async def _execute_strategy_action(
        self, 
        action: TriggerAction, 
        trigger: EventTrigger, 
        event: Event
    ) -> Tuple[bool, str]:
        """
        Execute a strategy adjustment action.
        
        Args:
            action: Action to execute
            trigger: Trigger that fired
            event: Event that triggered
            
        Returns:
            Success status and message
        """
        if not self.trading_manager:
            return False, "Trading manager not available"
        
        try:
            # Get action parameters
            strategy_type = action.params.get("strategy_type")
            adjustment = action.params.get("adjustment", {})
            
            if not strategy_type:
                return False, "No strategy type specified"
                
            if not adjustment:
                return False, "No adjustment specified"
                
            # Update strategy configuration
            if self.dashboard_service:
                await self.dashboard_service.update_strategy_config(
                    strategy_type=strategy_type,
                    config_updates=adjustment
                )
                
                return True, f"Updated strategy configuration for {strategy_type}"
            else:
                return False, "Dashboard service not available for strategy updates"
            
        except Exception as e:
            logger.error(f"Error executing strategy action: {e}")
            return False, f"Error: {str(e)}"
    
    def add_event_listener(self, listener: Callable[[Event], Awaitable[None]]):
        """
        Add an event listener.
        
        Args:
            listener: Async function to call when an event is added
        """
        self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable[[Event], Awaitable[None]]) -> bool:
        """
        Remove an event listener.
        
        Args:
            listener: Listener to remove
            
        Returns:
            True if listener was removed, False otherwise
        """
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
            return True
        
        return False
