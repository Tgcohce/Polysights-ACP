"""
Job intake and validation module for the ACP Polymarket Trading Agent.

This module handles the intake, validation, and acceptance of job requests
from the ACP network, ensuring they meet the agent's specifications and
capabilities before being queued for processing.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, ValidationError

from app.agent.job_lifecycle import (
    JobLifecycleManager, 
    JobState, 
    JobSpec,
    JobCategory,
    JobType,
    lifecycle_manager,
)
from app.utils.config import config
from app.wallet.erc6551 import SmartWallet


class ValidationResult(BaseModel):
    """Result of job validation."""
    
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    estimated_cost: float = 0.0


class JobIntakeManager:
    """
    Manager for job intake and validation.
    
    Responsible for validating incoming job requests, checking requester
    credentials, estimating costs, and determining if the agent can accept
    the job based on current capacity and capabilities.
    """
    
    def __init__(self, wallet: SmartWallet):
        """
        Initialize the JobIntakeManager.
        
        Args:
            wallet: Smart wallet instance for payment verification
        """
        self.wallet = wallet
        self.max_concurrent_jobs = config.trading.max_concurrent_jobs
        self.job_type_validators = self._initialize_validators()
        self.geographic_restrictions = config.trading.restricted_regions
        self.min_requester_reputation = config.trading.min_requester_reputation
        
        # Register state handlers
        lifecycle_manager.register_state_handler(
            JobState.PENDING, self.handle_pending_job
        )
        
        logger.info("Initialized JobIntakeManager")
    
    def _initialize_validators(self) -> Dict[JobType, callable]:
        """
        Initialize job type-specific validators.
        
        Returns:
            Dict mapping job types to validator functions
        """
        validators = {
            # Market Analysis validators
            JobType.ANALYZE_MARKET: self._validate_analyze_market,
            JobType.ANALYZE_OUTCOMES: self._validate_analyze_outcomes,
            JobType.MARKET_REPORT: self._validate_market_report,
            JobType.SENTIMENT_ANALYSIS: self._validate_sentiment_analysis,
            JobType.TRADER_ANALYSIS: self._validate_trader_analysis,
            
            # Trade Execution validators
            JobType.PLACE_ORDER: self._validate_place_order,
            JobType.CANCEL_ORDER: self._validate_cancel_order,
            JobType.MANAGE_POSITION: self._validate_manage_position,
            
            # Portfolio Management validators
            JobType.OPTIMIZE_PORTFOLIO: self._validate_optimize_portfolio,
            JobType.RISK_ASSESSMENT: self._validate_risk_assessment,
            JobType.REBALANCE_PORTFOLIO: self._validate_rebalance_portfolio,
            
            # Arbitrage Detection validators
            JobType.DETECT_ARBITRAGE: self._validate_detect_arbitrage,
            JobType.EXECUTE_ARBITRAGE: self._validate_execute_arbitrage,
            
            # Custom job validators
            JobType.CUSTOM_JOB: self._validate_custom_job,
        }
        return validators
    
    async def handle_pending_job(self, job_record):
        """
        Handle a job in the PENDING state.
        
        Args:
            job_record: Job record to process
        """
        job_id = job_record.job_id
        logger.info(f"Processing pending job {job_id}")
        
        # Transition to validating
        await lifecycle_manager.transition_job_state(
            job_id, JobState.VALIDATING, "Starting job validation"
        )
        
        # Validate the job
        validation_result = await self.validate_job(job_record.specification)
        
        if not validation_result.valid:
            # Reject the job
            error_message = "; ".join(validation_result.errors)
            await lifecycle_manager.transition_job_state(
                job_id, JobState.REJECTED, f"Validation failed: {error_message}"
            )
            return
        
        # Check if we're under capacity
        current_active_jobs = len(lifecycle_manager.get_jobs_by_state(JobState.PROCESSING))
        
        if current_active_jobs >= self.max_concurrent_jobs:
            await lifecycle_manager.transition_job_state(
                job_id,
                JobState.REJECTED,
                f"Agent at maximum capacity ({self.max_concurrent_jobs} jobs)"
            )
            return
        
        # Set the cost based on validation
        job_record.payment_amount = validation_result.estimated_cost
        
        # Accept the job
        await lifecycle_manager.transition_job_state(
            job_id, JobState.ACCEPTED, "Job validated and accepted"
        )
    
    async def validate_job(self, job_spec: JobSpec) -> ValidationResult:
        """
        Validate a job specification.
        
        Args:
            job_spec: Job specification to validate
            
        Returns:
            ValidationResult: Result of validation
        """
        errors = []
        warnings = []
        
        # Check if we support this job type
        if job_spec.job_type not in self.job_type_validators:
            errors.append(f"Unsupported job type: {job_spec.job_type}")
            return ValidationResult(valid=False, errors=errors)
        
        # Check requester reputation
        requester_reputation = await self._get_requester_reputation(job_spec.requester_id)
        if requester_reputation < self.min_requester_reputation:
            errors.append(
                f"Requester reputation too low: {requester_reputation} " 
                f"(minimum: {self.min_requester_reputation})"
            )
        
        # Check geographic restrictions
        requester_region = await self._get_requester_region(job_spec.requester_id)
        if requester_region in self.geographic_restrictions:
            errors.append(f"Service not available in region: {requester_region}")
        
        # Check if parameters are valid for this job type
        validator = self.job_type_validators[job_spec.job_type]
        validator_result = await validator(job_spec.parameters)
        
        errors.extend(validator_result.get("errors", []))
        warnings.extend(validator_result.get("warnings", []))
        
        # Check deadline if provided
        if job_spec.deadline and job_spec.deadline < datetime.now():
            errors.append("Deadline is in the past")
        
        # Calculate cost
        estimated_cost = lifecycle_manager.calculate_job_cost(
            lifecycle_manager.jobs[job_spec.job_id] if hasattr(job_spec, "job_id") else 
            await lifecycle_manager.create_job(job_spec)
        )
        
        # Check if max_payment is sufficient
        if job_spec.max_payment is not None and estimated_cost > job_spec.max_payment:
            errors.append(
                f"Estimated cost ({estimated_cost}) exceeds max payment ({job_spec.max_payment})"
            )
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            estimated_cost=estimated_cost
        )
    
    async def process_job_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming job request from the ACP network.
        
        Args:
            request_data: Raw job request data
            
        Returns:
            Dict containing job ID and status
        """
        try:
            # Convert request data to JobSpec
            job_spec = JobSpec(**request_data)
            
            # Create job record
            job_record = await lifecycle_manager.create_job(job_spec)
            
            return {
                "job_id": job_record.job_id,
                "status": "accepted_for_validation",
                "message": "Job request received and queued for validation"
            }
            
        except ValidationError as e:
            logger.error(f"Invalid job request: {e}")
            return {
                "status": "rejected",
                "message": f"Invalid job request format: {str(e)}",
                "errors": [str(err) for err in e.errors()]
            }
        except Exception as e:
            logger.error(f"Error processing job request: {e}")
            return {
                "status": "error",
                "message": f"Internal error: {str(e)}"
            }
    
    async def _get_requester_reputation(self, requester_id: str) -> float:
        """
        Get the reputation score for a requester.
        
        Args:
            requester_id: ID of the requester
            
        Returns:
            float: Reputation score (0.0-1.0)
        """
        # This would be implemented by querying the ACP network
        # For now, return a default value
        logger.debug(f"Would query reputation for requester {requester_id}")
        return 0.8  # Default value
    
    async def _get_requester_region(self, requester_id: str) -> str:
        """
        Get the region for a requester.
        
        Args:
            requester_id: ID of the requester
            
        Returns:
            str: Region code
        """
        # This would be implemented by querying the ACP network
        # For now, return a default value
        logger.debug(f"Would query region for requester {requester_id}")
        return "US"  # Default value
    
    # Job type-specific validators
    
    async def _validate_analyze_market(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for ANALYZE_MARKET jobs."""
        errors = []
        warnings = []
        
        required_params = ["market_id"]
        optional_params = ["depth", "include_sentiment", "include_trader_analysis"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types
        if "market_id" in parameters and not isinstance(parameters["market_id"], str):
            errors.append("market_id must be a string")
        
        if "depth" in parameters and not isinstance(parameters["depth"], (int, float)):
            errors.append("depth must be a number")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_analyze_outcomes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for ANALYZE_OUTCOMES jobs."""
        errors = []
        warnings = []
        
        required_params = ["market_id"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_market_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for MARKET_REPORT jobs."""
        errors = []
        warnings = []
        
        required_params = ["market_ids"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types
        if "market_ids" in parameters:
            if not isinstance(parameters["market_ids"], list):
                errors.append("market_ids must be a list")
            elif not all(isinstance(mid, str) for mid in parameters["market_ids"]):
                errors.append("All market IDs must be strings")
            elif len(parameters["market_ids"]) > 10:
                warnings.append("Large number of markets requested, processing may take longer")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_sentiment_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for SENTIMENT_ANALYSIS jobs."""
        errors = []
        warnings = []
        
        required_params = ["market_id"]
        optional_params = ["sources", "time_window"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_trader_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for TRADER_ANALYSIS jobs."""
        errors = []
        warnings = []
        
        required_params = ["trader_addresses"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types
        if "trader_addresses" in parameters:
            if not isinstance(parameters["trader_addresses"], list):
                errors.append("trader_addresses must be a list")
            elif not all(isinstance(addr, str) for addr in parameters["trader_addresses"]):
                errors.append("All trader addresses must be strings")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_place_order(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for PLACE_ORDER jobs."""
        errors = []
        warnings = []
        
        required_params = ["market_id", "outcome_id", "side", "price", "size"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types and values
        if "side" in parameters:
            if parameters["side"] not in ["buy", "sell"]:
                errors.append("side must be 'buy' or 'sell'")
        
        if "price" in parameters:
            try:
                price = float(parameters["price"])
                if not 0 < price < 1:
                    errors.append("price must be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("price must be a valid number")
        
        if "size" in parameters:
            try:
                size = float(parameters["size"])
                if size <= 0:
                    errors.append("size must be greater than 0")
            except (ValueError, TypeError):
                errors.append("size must be a valid number")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_cancel_order(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for CANCEL_ORDER jobs."""
        errors = []
        warnings = []
        
        required_params = ["order_id"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_manage_position(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for MANAGE_POSITION jobs."""
        errors = []
        warnings = []
        
        required_params = ["market_id", "action"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter values
        if "action" in parameters:
            valid_actions = ["close", "reduce", "increase", "hedge"]
            if parameters["action"] not in valid_actions:
                errors.append(f"action must be one of {valid_actions}")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_optimize_portfolio(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for OPTIMIZE_PORTFOLIO jobs."""
        errors = []
        warnings = []
        
        optional_params = ["risk_tolerance", "time_horizon", "target_return"]
        
        # Check parameter types
        if "risk_tolerance" in parameters:
            try:
                rt = float(parameters["risk_tolerance"])
                if not 0 <= rt <= 1:
                    errors.append("risk_tolerance must be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("risk_tolerance must be a valid number")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_risk_assessment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for RISK_ASSESSMENT jobs."""
        errors = []
        warnings = []
        
        required_params = ["positions"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types
        if "positions" in parameters:
            if not isinstance(parameters["positions"], list):
                errors.append("positions must be a list")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_rebalance_portfolio(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for REBALANCE_PORTFOLIO jobs."""
        errors = []
        warnings = []
        
        required_params = ["portfolio", "target_allocation"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_detect_arbitrage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for DETECT_ARBITRAGE jobs."""
        errors = []
        warnings = []
        
        optional_params = ["market_ids", "min_profit_threshold"]
        
        # Check parameter types
        if "min_profit_threshold" in parameters:
            try:
                threshold = float(parameters["min_profit_threshold"])
                if threshold <= 0:
                    errors.append("min_profit_threshold must be greater than 0")
            except (ValueError, TypeError):
                errors.append("min_profit_threshold must be a valid number")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_execute_arbitrage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for EXECUTE_ARBITRAGE jobs."""
        errors = []
        warnings = []
        
        required_params = ["arbitrage_id", "max_slippage"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check parameter types
        if "max_slippage" in parameters:
            try:
                slippage = float(parameters["max_slippage"])
                if not 0 <= slippage <= 0.1:
                    errors.append("max_slippage must be between 0 and 0.1 (10%)")
            except (ValueError, TypeError):
                errors.append("max_slippage must be a valid number")
        
        # High risk warning
        warnings.append("Executing arbitrage is a high-risk operation with potential for slippage")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_custom_job(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for CUSTOM_JOB jobs."""
        errors = []
        warnings = []
        
        required_params = ["job_description"]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Custom jobs require manual review
        warnings.append("Custom job requires manual review and may have longer processing time")
        
        return {"errors": errors, "warnings": warnings}


# Global instance for easy access
intake_manager = None

def initialize_intake_manager(wallet: SmartWallet):
    """Initialize the global intake manager instance."""
    global intake_manager
    intake_manager = JobIntakeManager(wallet)
    return intake_manager
