"""
Job Lifecycle Management for ACP Polymarket Trading Agent.

This module defines the core job lifecycle states and transitions for
managing jobs within the ACP ecosystem. It provides the foundation for
job handling including state management, persistence, and basic operations.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable
import uuid

from loguru import logger
from pydantic import BaseModel, Field

from app.utils.config import config


class JobState(str, Enum):
    """Job lifecycle states within the ACP ecosystem."""
    
    # Initial states
    PENDING = "pending"                # Job submitted but not yet accepted
    VALIDATING = "validating"          # Job is being validated
    REJECTED = "rejected"              # Job rejected due to validation failure
    
    # Processing states
    ACCEPTED = "accepted"              # Job accepted, awaiting processing
    PROCESSING = "processing"          # Job is being processed
    PROCESSING_ERROR = "processing_error"  # Error during processing
    
    # Payment states
    AWAITING_PAYMENT = "awaiting_payment"  # Waiting for payment
    PAYMENT_ERROR = "payment_error"    # Error during payment
    
    # Completion states
    COMPLETED = "completed"            # Job completed successfully
    DELIVERING = "delivering"          # Delivering job results
    DELIVERY_ERROR = "delivery_error"  # Error during delivery
    
    # Final states
    FINALIZED = "finalized"            # Job finalized with payment settled
    CANCELLED = "cancelled"            # Job cancelled (by either party)
    DISPUTED = "disputed"              # Job in dispute resolution


class JobPriority(str, Enum):
    """Priority levels for ACP jobs."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class JobCategory(str, Enum):
    """Categories of jobs supported by this agent."""
    
    MARKET_ANALYSIS = "market_analysis"
    TRADE_EXECUTION = "trade_execution"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    ARBITRAGE_DETECTION = "arbitrage_detection"
    CUSTOM = "custom"


class JobType(str, Enum):
    """Specific job types within each category."""
    
    # Market Analysis jobs
    ANALYZE_MARKET = "analyze_market"
    ANALYZE_OUTCOMES = "analyze_outcomes"
    MARKET_REPORT = "market_report"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TRADER_ANALYSIS = "trader_analysis"
    
    # Trade Execution jobs
    PLACE_ORDER = "place_order"
    CANCEL_ORDER = "cancel_order"
    MANAGE_POSITION = "manage_position"
    
    # Portfolio Management jobs
    OPTIMIZE_PORTFOLIO = "optimize_portfolio"
    RISK_ASSESSMENT = "risk_assessment"
    REBALANCE_PORTFOLIO = "rebalance_portfolio"
    
    # Arbitrage Detection jobs
    DETECT_ARBITRAGE = "detect_arbitrage"
    EXECUTE_ARBITRAGE = "execute_arbitrage"
    
    # Custom jobs
    CUSTOM_JOB = "custom_job"


class PaymentStatus(str, Enum):
    """Payment status for ACP jobs."""
    
    NOT_STARTED = "not_started"
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SLAConfig(BaseModel):
    """SLA configuration for a job."""
    
    response_time_seconds: int = Field(
        default=60,
        description="Maximum time to respond to job request in seconds"
    )
    
    processing_time_seconds: int = Field(
        default=300,
        description="Maximum time to complete job processing in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed operations"
    )
    
    completion_threshold: float = Field(
        default=0.95,
        description="Threshold for successful completion (0.0-1.0)"
    )


class JobSpec(BaseModel):
    """Specification for an ACP job request."""
    
    category: JobCategory
    job_type: JobType
    parameters: Dict[str, Any]
    priority: JobPriority = JobPriority.MEDIUM
    deadline: Optional[datetime] = None
    requester_id: str
    requester_address: str
    max_payment: Optional[float] = None
    payment_token: str = "VIRTUAL"
    sla: Optional[SLAConfig] = None


class JobResult(BaseModel):
    """Results of a completed job."""
    
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    completion_percentage: float = 1.0
    execution_time_seconds: float


class JobRecord(BaseModel):
    """Complete record of a job in the ACP ecosystem."""
    
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    specification: JobSpec
    
    # State management
    state: JobState = JobState.PENDING
    previous_states: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # SLA tracking
    response_time: Optional[float] = None
    processing_time: Optional[float] = None
    retry_count: int = 0
    
    # Payment information
    payment_status: PaymentStatus = PaymentStatus.NOT_STARTED
    payment_amount: float = 0
    payment_txid: Optional[str] = None
    
    # Results
    result: Optional[JobResult] = None
    
    # Error tracking
    last_error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    def update_state(self, new_state: JobState, reason: Optional[str] = None):
        """
        Update the job state and record the transition.
        
        Args:
            new_state: New state to transition to
            reason: Optional reason for the state change
        """
        # Record the previous state
        self.previous_states.append({
            "state": self.state,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        # Update to the new state
        self.state = new_state
        self.updated_at = datetime.now()


class JobLifecycleManager:
    """
    Core manager for ACP job lifecycle.
    
    This class manages job state transitions, persistence, and provides
    a foundation for the complete job handling process.
    """
    
    def __init__(self):
        """Initialize the JobLifecycleManager."""
        self.jobs = {}  # In-memory job storage (job_id -> JobRecord)
        self._state_handlers = self._initialize_state_handlers()
        logger.info("Initialized JobLifecycleManager")
    
    def _initialize_state_handlers(self) -> Dict[JobState, List[Callable]]:
        """
        Initialize handlers for each job state.
        
        Returns:
            Dict mapping job states to handler functions
        """
        return {
            JobState.PENDING: [],
            JobState.VALIDATING: [],
            JobState.REJECTED: [],
            JobState.ACCEPTED: [],
            JobState.PROCESSING: [],
            JobState.PROCESSING_ERROR: [],
            JobState.AWAITING_PAYMENT: [],
            JobState.PAYMENT_ERROR: [],
            JobState.COMPLETED: [],
            JobState.DELIVERING: [],
            JobState.DELIVERY_ERROR: [],
            JobState.FINALIZED: [],
            JobState.CANCELLED: [],
            JobState.DISPUTED: [],
        }
    
    def register_state_handler(self, state: JobState, handler: Callable):
        """
        Register a handler for a specific job state.
        
        Args:
            state: Job state to handle
            handler: Handler function to call when a job enters this state
        """
        if state not in self._state_handlers:
            raise ValueError(f"Unknown job state: {state}")
        
        self._state_handlers[state].append(handler)
        logger.debug(f"Registered handler for state {state}")
    
    async def create_job(self, spec: JobSpec) -> JobRecord:
        """
        Create a new job record from a job specification.
        
        Args:
            spec: Job specification
            
        Returns:
            JobRecord: Newly created job record
        """
        job = JobRecord(
            job_id=str(uuid.uuid4()),
            specification=spec,
            state=JobState.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.jobs[job.job_id] = job
        logger.info(f"Created job {job.job_id} of type {spec.job_type}")
        
        # Trigger handlers for the initial state
        await self._trigger_state_handlers(job)
        
        return job
    
    async def transition_job_state(
        self,
        job_id: str,
        new_state: JobState,
        reason: Optional[str] = None
    ) -> JobRecord:
        """
        Transition a job to a new state.
        
        Args:
            job_id: ID of the job to transition
            new_state: New state to transition to
            reason: Optional reason for the transition
            
        Returns:
            JobRecord: Updated job record
            
        Raises:
            ValueError: If job_id is not found
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        # Record state change
        old_state = job.state
        job.update_state(new_state, reason)
        
        logger.info(f"Job {job_id} transitioned from {old_state} to {new_state}: {reason}")
        
        # Trigger handlers for the new state
        await self._trigger_state_handlers(job)
        
        return job
    
    async def _trigger_state_handlers(self, job: JobRecord):
        """
        Trigger all handlers for the current state of a job.
        
        Args:
            job: Job record to process
        """
        handlers = self._state_handlers.get(job.state, [])
        for handler in handlers:
            try:
                await handler(job)
            except Exception as e:
                logger.error(f"Error in state handler for job {job.job_id}: {e}")
    
    def get_job(self, job_id: str) -> Optional[JobRecord]:
        """
        Get a job record by ID.
        
        Args:
            job_id: ID of the job to retrieve
            
        Returns:
            JobRecord or None if not found
        """
        return self.jobs.get(job_id)
    
    def get_jobs_by_state(self, state: JobState) -> List[JobRecord]:
        """
        Get all jobs in a specific state.
        
        Args:
            state: State to filter by
            
        Returns:
            List of job records
        """
        return [job for job in self.jobs.values() if job.state == state]
    
    def get_jobs_by_requester(self, requester_id: str) -> List[JobRecord]:
        """
        Get all jobs from a specific requester.
        
        Args:
            requester_id: ID of the requester
            
        Returns:
            List of job records
        """
        return [
            job for job in self.jobs.values() 
            if job.specification.requester_id == requester_id
        ]
    
    async def handle_sla_breach(self, job: JobRecord, breach_type: str):
        """
        Handle an SLA breach for a job.
        
        Args:
            job: The job that has breached an SLA
            breach_type: Type of SLA breach
        """
        logger.warning(f"SLA breach ({breach_type}) for job {job.job_id}")
        
        # Depending on breach type, take appropriate action
        if breach_type == "response_time":
            # We failed to respond in time
            await self.transition_job_state(
                job.job_id,
                JobState.REJECTED,
                f"SLA breach: Failed to respond within {job.specification.sla.response_time_seconds}s"
            )
        
        elif breach_type == "processing_time":
            # Processing is taking too long
            if job.retry_count < job.specification.sla.max_retries:
                # Retry processing
                job.retry_count += 1
                await self.transition_job_state(
                    job.job_id,
                    JobState.PROCESSING,
                    f"Retrying after SLA breach (attempt {job.retry_count})"
                )
            else:
                # Failed after max retries
                await self.transition_job_state(
                    job.job_id,
                    JobState.PROCESSING_ERROR,
                    f"SLA breach: Failed to process within time limit after {job.retry_count} attempts"
                )
    
    async def persist_jobs(self):
        """Placeholder for job persistence to database."""
        # This would be implemented with database connections
        # For now, just log the number of jobs
        logger.info(f"Would persist {len(self.jobs)} jobs to database")
    
    async def load_jobs(self):
        """Placeholder for loading jobs from database."""
        # This would be implemented with database connections
        logger.info("Would load jobs from database")
    
    async def cancel_job(self, job_id: str, reason: str) -> JobRecord:
        """
        Cancel a job.
        
        Args:
            job_id: ID of the job to cancel
            reason: Reason for cancellation
            
        Returns:
            JobRecord: Updated job record
            
        Raises:
            ValueError: If job_id is not found
        """
        return await self.transition_job_state(job_id, JobState.CANCELLED, reason)
    
    def calculate_job_cost(self, job: JobRecord) -> float:
        """
        Calculate the cost of a job based on its type, complexity, and other factors.
        
        Args:
            job: Job to calculate cost for
            
        Returns:
            float: Cost in VIRTUAL tokens
        """
        # Base cost by job category
        base_costs = {
            JobCategory.MARKET_ANALYSIS: 10.0,
            JobCategory.TRADE_EXECUTION: 15.0,
            JobCategory.PORTFOLIO_MANAGEMENT: 20.0,
            JobCategory.ARBITRAGE_DETECTION: 25.0,
            JobCategory.CUSTOM: 30.0
        }
        
        # Priority multipliers
        priority_multipliers = {
            JobPriority.LOW: 0.8,
            JobPriority.MEDIUM: 1.0,
            JobPriority.HIGH: 1.5,
            JobPriority.URGENT: 2.0
        }
        
        # Calculate base cost
        base_cost = base_costs.get(job.specification.category, 10.0)
        
        # Apply priority multiplier
        priority_multiplier = priority_multipliers.get(job.specification.priority, 1.0)
        
        # Apply any job-specific modifiers based on parameters
        params = job.specification.parameters
        param_multiplier = 1.0
        
        # Example parameter modifiers (would be customized based on job types)
        if "complexity" in params:
            complexity = params["complexity"]
            if complexity == "high":
                param_multiplier *= 1.5
            elif complexity == "very_high":
                param_multiplier *= 2.0
        
        if "data_volume" in params:
            data_volume = params["data_volume"]
            if data_volume == "large":
                param_multiplier *= 1.3
            elif data_volume == "very_large":
                param_multiplier *= 1.6
        
        # Calculate final cost
        final_cost = base_cost * priority_multiplier * param_multiplier
        
        # Round to 2 decimal places
        return round(final_cost, 2)


# Singleton instance for global access
lifecycle_manager = JobLifecycleManager()
