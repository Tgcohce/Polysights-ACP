"""
Job execution and SLA tracking module for the ACP Polymarket Trading Agent.

This module implements job execution, processing logic for different job types,
and SLA tracking to ensure jobs are processed within agreed time frames.
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from loguru import logger

from app.agent.job_lifecycle import (
    JobLifecycleManager,
    JobState,
    JobRecord,
    lifecycle_manager
)
from app.polymarket.client import PolymarketClient
from app.polysights.client import PolysightsClient
from app.trading.market_analyzer import MarketAnalyzer
from app.utils.config import config


class JobExecutionManager:
    """
    Manager for job execution and SLA tracking.
    
    Responsible for executing jobs based on their type, tracking SLA metrics,
    handling retries for failed operations, and transitioning job states.
    """
    
    def __init__(
        self,
        polymarket_client: PolymarketClient,
        polysights_client: PolysightsClient,
        market_analyzer: MarketAnalyzer
    ):
        """
        Initialize the JobExecutionManager.
        
        Args:
            polymarket_client: Polymarket client for trading operations
            polysights_client: Polysights client for analytics
            market_analyzer: Market analyzer for analysis operations
        """
        self.polymarket = polymarket_client
        self.polysights = polysights_client
        self.market_analyzer = market_analyzer
        
        # Job processor mapping (job_type -> processor function)
        self.job_processors = self._initialize_processors()
        
        # SLA monitoring
        self.sla_monitor_task = None
        self.sla_check_interval = 10  # seconds
        
        # Register state handlers
        lifecycle_manager.register_state_handler(
            JobState.ACCEPTED, self.handle_accepted_job
        )
        lifecycle_manager.register_state_handler(
            JobState.PROCESSING, self.handle_processing_job
        )
        
        logger.info("Initialized JobExecutionManager")
    
    def _initialize_processors(self) -> Dict[str, Callable]:
        """
        Initialize job type-specific processor functions.
        
        Returns:
            Dict mapping job types to processor functions
        """
        from app.agent.job_lifecycle import JobType
        
        processors = {
            # Market Analysis processors
            JobType.ANALYZE_MARKET: self._process_analyze_market,
            JobType.ANALYZE_OUTCOMES: self._process_analyze_outcomes,
            JobType.MARKET_REPORT: self._process_market_report,
            JobType.SENTIMENT_ANALYSIS: self._process_sentiment_analysis,
            JobType.TRADER_ANALYSIS: self._process_trader_analysis,
            
            # Trade Execution processors
            JobType.PLACE_ORDER: self._process_place_order,
            JobType.CANCEL_ORDER: self._process_cancel_order,
            JobType.MANAGE_POSITION: self._process_manage_position,
            
            # Portfolio Management processors
            JobType.OPTIMIZE_PORTFOLIO: self._process_optimize_portfolio,
            JobType.RISK_ASSESSMENT: self._process_risk_assessment,
            JobType.REBALANCE_PORTFOLIO: self._process_rebalance_portfolio,
            
            # Arbitrage Detection processors
            JobType.DETECT_ARBITRAGE: self._process_detect_arbitrage,
            JobType.EXECUTE_ARBITRAGE: self._process_execute_arbitrage,
            
            # Custom job processors
            JobType.CUSTOM_JOB: self._process_custom_job,
        }
        return processors
    
    async def start(self):
        """Start the execution manager, including SLA monitoring."""
        logger.info("Starting JobExecutionManager")
        self.sla_monitor_task = asyncio.create_task(self._sla_monitor())
    
    async def stop(self):
        """Stop the execution manager and clean up."""
        logger.info("Stopping JobExecutionManager")
        if self.sla_monitor_task:
            self.sla_monitor_task.cancel()
            try:
                await self.sla_monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _sla_monitor(self):
        """Monitor SLAs for all active jobs."""
        try:
            while True:
                # Check SLAs for jobs in ACCEPTED state
                accepted_jobs = lifecycle_manager.get_jobs_by_state(JobState.ACCEPTED)
                for job in accepted_jobs:
                    # Check if the job has exceeded its response time SLA
                    if job.specification.sla:
                        created_time = job.created_at
                        response_time_limit = job.specification.sla.response_time_seconds
                        current_time = datetime.now()
                        
                        time_since_creation = (current_time - created_time).total_seconds()
                        
                        if time_since_creation > response_time_limit:
                            # SLA breach for response time
                            await lifecycle_manager.handle_sla_breach(job, "response_time")
                
                # Check SLAs for jobs in PROCESSING state
                processing_jobs = lifecycle_manager.get_jobs_by_state(JobState.PROCESSING)
                for job in processing_jobs:
                    # Check if the job has exceeded its processing time SLA
                    if job.specification.sla and job.processing_time:
                        current_time = time.time()
                        processing_start = current_time - job.processing_time
                        processing_time_limit = job.specification.sla.processing_time_seconds
                        
                        if processing_start > processing_time_limit:
                            # SLA breach for processing time
                            await lifecycle_manager.handle_sla_breach(job, "processing_time")
                
                await asyncio.sleep(self.sla_check_interval)
        except asyncio.CancelledError:
            # Expected during shutdown
            logger.info("SLA monitor stopped")
        except Exception as e:
            logger.error(f"Error in SLA monitor: {e}")
    
    async def handle_accepted_job(self, job: JobRecord):
        """
        Handle a job in the ACCEPTED state.
        
        Args:
            job: Job record to process
        """
        # Track response time SLA
        job.response_time = (datetime.now() - job.created_at).total_seconds()
        
        # Start processing
        await lifecycle_manager.transition_job_state(
            job.job_id, JobState.PROCESSING, "Starting job processing"
        )
    
    async def handle_processing_job(self, job: JobRecord):
        """
        Handle a job in the PROCESSING state.
        
        Args:
            job: Job record to process
        """
        job_id = job.job_id
        job_type = job.specification.job_type
        
        # Only process if this is the first time or a retry
        if job.processing_time is None or job.retry_count > 0:
            logger.info(f"Processing job {job_id} of type {job_type}")
            
            # Record processing start time
            start_time = time.time()
            job.processing_time = start_time
            
            try:
                # Get the appropriate processor
                processor = self.job_processors.get(job_type)
                
                if not processor:
                    raise ValueError(f"No processor found for job type {job_type}")
                
                # Process the job
                result = await processor(job)
                
                # Calculate processing time
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Create job result
                from app.agent.job_lifecycle import JobResult
                job_result = JobResult(
                    success=True,
                    data=result,
                    completion_percentage=1.0,
                    execution_time_seconds=execution_time
                )
                
                # Update job with result
                job.result = job_result
                
                # Transition to completed state
                await lifecycle_manager.transition_job_state(
                    job_id, JobState.COMPLETED, "Job processing completed successfully"
                )
                
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                
                # Record the error
                job.last_error = str(e)
                job.error_details = {"exception": str(e), "timestamp": datetime.now().isoformat()}
                
                # Check if we should retry
                if job.retry_count < job.specification.sla.max_retries:
                    # Increment retry count
                    job.retry_count += 1
                    
                    # Reset processing time for next retry
                    job.processing_time = None
                    
                    # Schedule retry
                    await lifecycle_manager.transition_job_state(
                        job_id,
                        JobState.ACCEPTED,
                        f"Scheduling retry {job.retry_count}/{job.specification.sla.max_retries}"
                    )
                else:
                    # No more retries, mark as error
                    await lifecycle_manager.transition_job_state(
                        job_id, JobState.PROCESSING_ERROR, f"Failed after {job.retry_count} retries: {e}"
                    )
    
    # Job type-specific processors
    
    async def _process_analyze_market(self, job: JobRecord) -> Dict[str, Any]:
        """Process an ANALYZE_MARKET job."""
        params = job.specification.parameters
        market_id = params["market_id"]
        
        # Perform market analysis
        analysis = await self.market_analyzer.analyze_market(
            market_id=market_id,
            force_refresh=True
        )
        
        return analysis
    
    async def _process_analyze_outcomes(self, job: JobRecord) -> Dict[str, Any]:
        """Process an ANALYZE_OUTCOMES job."""
        params = job.specification.parameters
        market_id = params["market_id"]
        
        # Get market data from Polymarket
        market_data = await self.polymarket.get_market_data(market_id)
        
        # Get market insights from Polysights
        market_insights = await self.polysights.get_market_insights(market_id)
        
        # Analyze outcomes
        outcomes = market_data.get("outcomes", [])
        outcome_analysis = {}
        
        for outcome in outcomes:
            outcome_id = outcome.get("outcomeId")
            if outcome_id:
                # Get outcome-specific data
                price = outcome.get("price", 0)
                volume = outcome.get("volume", 0)
                
                # Get sentiment data for this outcome
                sentiment = market_insights.get("insights", {}).get("outcomes", {}).get(outcome_id, {})
                
                # Combine data
                outcome_analysis[outcome_id] = {
                    "price": price,
                    "volume": volume,
                    "sentiment": sentiment,
                    "forecast": {
                        "short_term": market_insights.get("forecast", {}).get("outcomes", {}).get(outcome_id, {}).get("short_term"),
                        "long_term": market_insights.get("forecast", {}).get("outcomes", {}).get(outcome_id, {}).get("long_term")
                    }
                }
        
        return {
            "market_id": market_id,
            "market_title": market_data.get("title", ""),
            "outcome_analysis": outcome_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_market_report(self, job: JobRecord) -> Dict[str, Any]:
        """Process a MARKET_REPORT job."""
        params = job.specification.parameters
        market_ids = params["market_ids"]
        
        # Analyze each market
        market_analyses = []
        for market_id in market_ids:
            try:
                analysis = await self.market_analyzer.analyze_market(market_id)
                market_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing market {market_id}: {e}")
                market_analyses.append({"market_id": market_id, "error": str(e)})
        
        # Generate market report
        report = {
            "report_id": str(job.job_id),
            "timestamp": datetime.now().isoformat(),
            "market_count": len(market_ids),
            "markets": market_analyses,
            "summary": self._generate_market_report_summary(market_analyses)
        }
        
        return report
    
    def _generate_market_report_summary(self, market_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary for a market report."""
        # Count markets with opportunities
        markets_with_opportunities = 0
        high_confidence_opportunities = 0
        total_opportunities = 0
        
        for analysis in market_analyses:
            opportunities = analysis.get("opportunities", [])
            if opportunities:
                markets_with_opportunities += 1
                total_opportunities += len(opportunities)
                
                # Count high confidence opportunities
                for opp in opportunities:
                    if opp.get("confidence", 0) > 0.7:
                        high_confidence_opportunities += 1
        
        return {
            "markets_with_opportunities": markets_with_opportunities,
            "total_opportunities": total_opportunities,
            "high_confidence_opportunities": high_confidence_opportunities
        }
    
    async def _process_sentiment_analysis(self, job: JobRecord) -> Dict[str, Any]:
        """Process a SENTIMENT_ANALYSIS job."""
        params = job.specification.parameters
        market_id = params["market_id"]
        sources = params.get("sources", None)
        time_window = params.get("time_window", "7d")
        
        # Get sentiment analysis from Polysights
        sentiment = await self.polysights.get_sentiment_analysis(
            market_id=market_id,
            time_window=time_window
        )
        
        # Filter by sources if specified
        if sources:
            filtered_sources = {}
            for source, data in sentiment.get("sources", {}).items():
                if source in sources:
                    filtered_sources[source] = data
            
            if "sources" in sentiment:
                sentiment["sources"] = filtered_sources
        
        return sentiment
    
    async def _process_trader_analysis(self, job: JobRecord) -> Dict[str, Any]:
        """Process a TRADER_ANALYSIS job."""
        params = job.specification.parameters
        trader_addresses = params["trader_addresses"]
        
        # Get trader analysis from Polysights
        trader_data = []
        
        for address in trader_addresses:
            trader_info = await self.polysights.get_trader_performance(address)
            trader_data.append(trader_info)
        
        # Compile trader analysis
        analysis = {
            "traders": trader_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    async def _process_place_order(self, job: JobRecord) -> Dict[str, Any]:
        """Process a PLACE_ORDER job."""
        params = job.specification.parameters
        market_id = params["market_id"]
        outcome_id = params["outcome_id"]
        side = params["side"]
        price = float(params["price"])
        size = float(params["size"])
        
        # Place the order
        order = await self.polymarket.place_order(
            market_id=market_id,
            outcome_id=outcome_id,
            side=side,
            price=price,
            size=size
        )
        
        return {
            "order_id": order.get("order_id"),
            "status": order.get("status"),
            "filled": order.get("filled"),
            "details": order
        }
    
    async def _process_cancel_order(self, job: JobRecord) -> Dict[str, Any]:
        """Process a CANCEL_ORDER job."""
        params = job.specification.parameters
        order_id = params["order_id"]
        
        # Cancel the order
        result = await self.polymarket.cancel_order(order_id)
        
        return {
            "order_id": order_id,
            "success": result.get("success", False),
            "details": result
        }
    
    async def _process_manage_position(self, job: JobRecord) -> Dict[str, Any]:
        """Process a MANAGE_POSITION job."""
        params = job.specification.parameters
        market_id = params["market_id"]
        action = params["action"]
        
        # Get current position
        position = await self.polymarket.get_position(market_id)
        
        result = {"success": False}
        
        if action == "close":
            # Close the position
            result = await self.polymarket.close_position(market_id)
        
        elif action == "reduce":
            # Reduce position
            reduce_by = params.get("percentage", 50)  # Default to 50%
            current_size = float(position.get("size", 0))
            target_size = current_size * (1 - reduce_by / 100)
            
            result = await self.polymarket.adjust_position(
                market_id=market_id,
                target_size=target_size
            )
        
        elif action == "increase":
            # Increase position
            increase_by = params.get("percentage", 50)  # Default to 50%
            current_size = float(position.get("size", 0))
            target_size = current_size * (1 + increase_by / 100)
            
            result = await self.polymarket.adjust_position(
                market_id=market_id,
                target_size=target_size
            )
        
        elif action == "hedge":
            # Hedge position
            hedge_method = params.get("method", "mirror")
            
            if hedge_method == "mirror":
                result = await self.polymarket.create_hedge_position(
                    market_id=market_id,
                    hedge_type="mirror"
                )
        
        return {
            "market_id": market_id,
            "action": action,
            "success": result.get("success", False),
            "details": result,
            "original_position": position
        }
    
    async def _process_optimize_portfolio(self, job: JobRecord) -> Dict[str, Any]:
        """Process an OPTIMIZE_PORTFOLIO job."""
        params = job.specification.parameters
        risk_tolerance = params.get("risk_tolerance", 0.5)
        time_horizon = params.get("time_horizon", "medium")
        target_return = params.get("target_return", None)
        
        # Get current positions
        positions = await self.polymarket.get_positions()
        
        # Get market analyses for all positions
        market_ids = [p.get("market_id") for p in positions]
        market_analyses = []
        
        for market_id in market_ids:
            analysis = await self.market_analyzer.analyze_market(market_id)
            market_analyses.append(analysis)
        
        # Optimize portfolio
        optimization = self._optimize_portfolio(
            positions=positions,
            analyses=market_analyses,
            risk_tolerance=risk_tolerance,
            time_horizon=time_horizon,
            target_return=target_return
        )
        
        return optimization
    
    def _optimize_portfolio(
        self,
        positions: List[Dict[str, Any]],
        analyses: List[Dict[str, Any]],
        risk_tolerance: float,
        time_horizon: str,
        target_return: Optional[float]
    ) -> Dict[str, Any]:
        """
        Optimize a portfolio based on positions and analyses.
        
        Args:
            positions: Current positions
            analyses: Market analyses
            risk_tolerance: Risk tolerance (0-1)
            time_horizon: Time horizon (short, medium, long)
            target_return: Target return or None
            
        Returns:
            Dict with optimization results
        """
        # Create position lookup by market ID
        position_by_market = {p.get("market_id"): p for p in positions}
        analysis_by_market = {a.get("market_id"): a for a in analyses}
        
        # Calculate position scores
        position_scores = []
        for position in positions:
            market_id = position.get("market_id")
            analysis = analysis_by_market.get(market_id, {})
            
            # Calculate score based on analysis and risk tolerance
            fair_value = analysis.get("fair_value", {}).get("fair_value", 0.5)
            confidence = analysis.get("fair_value", {}).get("confidence", 0.5)
            
            # Score factors
            current_price = float(position.get("price", 0.5))
            expected_profit = abs(fair_value - current_price)
            risk = 1 - confidence
            
            # Adjust for risk tolerance
            risk_adjusted_score = expected_profit * (1 - risk_tolerance * risk)
            
            position_scores.append({
                "market_id": market_id,
                "score": risk_adjusted_score,
                "current_size": float(position.get("size", 0)),
                "expected_profit": expected_profit,
                "confidence": confidence
            })
        
        # Sort positions by score
        position_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate target allocation
        total_value = sum(float(p.get("value", 0)) for p in positions)
        target_allocation = {}
        
        # Allocate based on scores
        remaining_allocation = 1.0
        for idx, score in enumerate(position_scores):
            market_id = score["market_id"]
            
            # Allocate more to higher-scored positions
            if idx == 0:
                # Top position gets most allocation
                allocation = min(0.4, remaining_allocation)
            elif idx < len(position_scores) * 0.2:
                # Top 20% get medium allocation
                allocation = min(0.2, remaining_allocation)
            else:
                # Remaining positions split the rest
                allocation = remaining_allocation / (len(position_scores) - idx)
            
            remaining_allocation -= allocation
            target_allocation[market_id] = allocation
        
        # Generate actions
        actions = []
        for position in positions:
            market_id = position.get("market_id")
            current_value = float(position.get("value", 0))
            current_allocation = current_value / total_value if total_value > 0 else 0
            target = target_allocation.get(market_id, 0)
            
            # Only generate actions for significant changes
            if abs(target - current_allocation) > 0.05:
                direction = "increase" if target > current_allocation else "reduce"
                percentage = abs(target - current_allocation) / current_allocation * 100 if current_allocation > 0 else 100
                
                actions.append({
                    "market_id": market_id,
                    "direction": direction,
                    "current_allocation": current_allocation,
                    "target_allocation": target,
                    "percentage_change": percentage,
                    "reason": "Portfolio optimization"
                })
        
        return {
            "optimized_allocation": target_allocation,
            "actions": actions,
            "risk_profile": {
                "risk_tolerance": risk_tolerance,
                "time_horizon": time_horizon,
                "target_return": target_return
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_risk_assessment(self, job: JobRecord) -> Dict[str, Any]:
        """Process a RISK_ASSESSMENT job."""
        params = job.specification.parameters
        positions = params["positions"]
        
        # Use market analyzer to perform risk assessment
        risk_assessment = await self.market_analyzer.risk_assessment({
            "positions": positions
        })
        
        return risk_assessment
    
    async def _process_rebalance_portfolio(self, job: JobRecord) -> Dict[str, Any]:
        """Process a REBALANCE_PORTFOLIO job."""
        params = job.specification.parameters
        portfolio = params["portfolio"]
        target_allocation = params["target_allocation"]
        
        # Calculate rebalancing actions
        actions = []
        current_positions = portfolio.get("positions", [])
        
        # Calculate total portfolio value
        total_value = sum(float(p.get("value", 0)) for p in current_positions)
        
        for position in current_positions:
            market_id = position.get("market_id")
            current_value = float(position.get("value", 0))
            current_allocation = current_value / total_value if total_value > 0 else 0
            
            # Get target allocation for this market
            target = target_allocation.get(market_id, 0)
            
            # Only generate actions for significant changes
            if abs(target - current_allocation) > 0.02:  # 2% threshold
                direction = "increase" if target > current_allocation else "reduce"
                target_value = total_value * target
                value_change = abs(target_value - current_value)
                
                actions.append({
                    "market_id": market_id,
                    "direction": direction,
                    "current_value": current_value,
                    "target_value": target_value,
                    "value_change": value_change
                })
        
        # Execute rebalancing actions
        results = []
        for action in actions:
            market_id = action["market_id"]
            direction = action["direction"]
            target_value = action["target_value"]
            
            # Calculate target size
            position = next((p for p in current_positions if p.get("market_id") == market_id), None)
            if position:
                current_price = float(position.get("price", 0.5))
                target_size = target_value / current_price if current_price > 0 else 0
                
                # Execute position adjustment
                try:
                    result = await self.polymarket.adjust_position(
                        market_id=market_id,
                        target_size=target_size
                    )
                    
                    action["result"] = result
                    action["success"] = result.get("success", False)
                except Exception as e:
                    action["result"] = {"error": str(e)}
                    action["success"] = False
            
            results.append(action)
        
        return {
            "portfolio_value": total_value,
            "rebalancing_actions": results,
            "success_count": sum(1 for r in results if r.get("success", False)),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_detect_arbitrage(self, job: JobRecord) -> Dict[str, Any]:
        """Process a DETECT_ARBITRAGE job."""
        params = job.specification.parameters
        market_ids = params.get("market_ids")
        min_profit_threshold = params.get("min_profit_threshold", 0.01)  # 1%
        
        # Detect arbitrage opportunities
        arbitrage_opps = await self.polymarket.detect_arbitrage(
            market_ids=market_ids,
            min_profit_threshold=min_profit_threshold
        )
        
        return {
            "arbitrage_opportunities": arbitrage_opps,
            "count": len(arbitrage_opps),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_execute_arbitrage(self, job: JobRecord) -> Dict[str, Any]:
        """Process an EXECUTE_ARBITRAGE job."""
        params = job.specification.parameters
        arbitrage_id = params["arbitrage_id"]
        max_slippage = params["max_slippage"]
        
        # Execute arbitrage
        execution_result = await self.polymarket.execute_arbitrage(
            arbitrage_id=arbitrage_id,
            max_slippage=max_slippage
        )
        
        return execution_result
    
    async def _process_custom_job(self, job: JobRecord) -> Dict[str, Any]:
        """Process a CUSTOM_JOB job."""
        params = job.specification.parameters
        description = params["job_description"]
        
        # Custom job processing would normally involve a more complex workflow
        # or integration with other systems
        
        # For now, we'll return a simple acknowledgement
        return {
            "job_description": description,
            "handled": True,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
execution_manager = None

def initialize_execution_manager(
    polymarket_client: PolymarketClient,
    polysights_client: PolysightsClient,
    market_analyzer: MarketAnalyzer
):
    """Initialize the global execution manager instance."""
    global execution_manager
    execution_manager = JobExecutionManager(
        polymarket_client=polymarket_client,
        polysights_client=polysights_client,
        market_analyzer=market_analyzer
    )
    return execution_manager
