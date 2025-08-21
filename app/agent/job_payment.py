"""
Job payment handling for the ACP Polymarket Trading Agent.

This module manages payment flows for jobs, including escrow creation,
payment verification, fee calculation, and payment settlement using
the ERC-6551 smart wallet.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from loguru import logger

from app.agent.job_lifecycle import (
    JobLifecycleManager,
    JobState,
    JobRecord,
    PaymentStatus,
    lifecycle_manager
)
from app.wallet.erc6551 import SmartWallet
from app.utils.config import config


class PaymentProcessor:
    """
    Handler for job payment processing in the ACP ecosystem.
    
    This class manages the payment lifecycle including escrow creation,
    payment verification, fee calculation, and settlement using the
    ERC-6551 smart wallet.
    """
    
    def __init__(self, wallet: SmartWallet):
        """
        Initialize the PaymentProcessor.
        
        Args:
            wallet: Smart wallet instance for blockchain operations
        """
        self.wallet = wallet
        self.payment_verification_interval = 30  # seconds
        self.payment_timeout = 1800  # 30 minutes
        self.fee_percentage = config.trading.fee_percentage
        self.payment_verification_task = None
        self.min_payment_amount = 1.0  # Minimum VIRTUAL tokens
        
        # Register state handlers
        lifecycle_manager.register_state_handler(
            JobState.COMPLETED, self.handle_completed_job
        )
        lifecycle_manager.register_state_handler(
            JobState.AWAITING_PAYMENT, self.handle_awaiting_payment
        )
        
        logger.info("Initialized PaymentProcessor")
    
    async def start(self):
        """Start the payment processor, including payment verification."""
        logger.info("Starting PaymentProcessor")
        self.payment_verification_task = asyncio.create_task(self._verify_pending_payments())
    
    async def stop(self):
        """Stop the payment processor and clean up."""
        logger.info("Stopping PaymentProcessor")
        if self.payment_verification_task:
            self.payment_verification_task.cancel()
            try:
                await self.payment_verification_task
            except asyncio.CancelledError:
                pass
    
    async def _verify_pending_payments(self):
        """Periodically verify pending payments."""
        try:
            while True:
                # Get jobs awaiting payment
                pending_jobs = lifecycle_manager.get_jobs_by_state(JobState.AWAITING_PAYMENT)
                
                for job in pending_jobs:
                    # Check payment status
                    payment_status = await self._check_payment_status(job)
                    
                    if payment_status == PaymentStatus.COMPLETED:
                        # Payment received, move to finalized state
                        await lifecycle_manager.transition_job_state(
                            job.job_id,
                            JobState.FINALIZED,
                            "Payment verified and completed"
                        )
                    
                    elif payment_status == PaymentStatus.FAILED:
                        # Payment failed or timed out
                        await lifecycle_manager.transition_job_state(
                            job.job_id,
                            JobState.PAYMENT_ERROR,
                            "Payment failed or timed out"
                        )
                
                await asyncio.sleep(self.payment_verification_interval)
        except asyncio.CancelledError:
            # Expected during shutdown
            logger.info("Payment verification stopped")
        except Exception as e:
            logger.error(f"Error in payment verification: {e}")
    
    async def handle_completed_job(self, job: JobRecord):
        """
        Handle a job in the COMPLETED state.
        
        Args:
            job: Job record to process
        """
        # Check if payment is required
        if job.payment_amount <= 0:
            # No payment needed, move directly to finalized state
            await lifecycle_manager.transition_job_state(
                job.job_id,
                JobState.FINALIZED,
                "No payment required"
            )
            return
        
        # Check if payment amount is below minimum
        if job.payment_amount < self.min_payment_amount:
            logger.warning(f"Payment amount {job.payment_amount} below minimum {self.min_payment_amount}, waiving payment")
            await lifecycle_manager.transition_job_state(
                job.job_id,
                JobState.FINALIZED,
                f"Payment waived (below minimum threshold of {self.min_payment_amount})"
            )
            return
        
        # Request payment
        payment_request = await self._request_payment(job)
        
        if payment_request.get("immediate_payment", False):
            # Payment was handled immediately
            job.payment_status = PaymentStatus.COMPLETED
            job.payment_txid = payment_request.get("txid")
            
            await lifecycle_manager.transition_job_state(
                job.job_id,
                JobState.FINALIZED,
                "Payment processed immediately"
            )
        else:
            # Move to awaiting payment state
            job.payment_status = PaymentStatus.PENDING
            
            await lifecycle_manager.transition_job_state(
                job.job_id,
                JobState.AWAITING_PAYMENT,
                "Waiting for payment confirmation"
            )
    
    async def handle_awaiting_payment(self, job: JobRecord):
        """
        Handle a job in the AWAITING_PAYMENT state.
        
        Args:
            job: Job record to process
        """
        # Check how long we've been waiting
        time_waiting = (datetime.now() - job.updated_at).total_seconds()
        
        if time_waiting > self.payment_timeout:
            # Payment timeout
            await lifecycle_manager.transition_job_state(
                job.job_id,
                JobState.PAYMENT_ERROR,
                f"Payment timed out after {time_waiting:.2f} seconds"
            )
    
    async def _request_payment(self, job: JobRecord) -> Dict[str, Any]:
        """
        Request payment for a completed job.
        
        Args:
            job: Job record to request payment for
            
        Returns:
            Dict with payment request details
        """
        requester_address = job.specification.requester_address
        payment_amount = job.payment_amount
        payment_token = job.specification.payment_token
        
        logger.info(f"Requesting payment of {payment_amount} {payment_token} from {requester_address} for job {job.job_id}")
        
        try:
            # Check if we're using escrow or direct payment
            if self._is_escrow_payment(job):
                # Release from escrow
                payment_result = await self._release_from_escrow(job)
            else:
                # Request direct payment
                payment_result = await self._request_direct_payment(job)
            
            return payment_result
            
        except Exception as e:
            logger.error(f"Error requesting payment for job {job.job_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "immediate_payment": False
            }
    
    def _is_escrow_payment(self, job: JobRecord) -> bool:
        """
        Determine if the job uses escrow payment.
        
        Args:
            job: Job record to check
            
        Returns:
            bool: True if escrow is used, False for direct payment
        """
        # High value jobs and certain job types use escrow
        high_value = job.payment_amount > 100  # 100 VIRTUAL tokens
        
        # Specific job types that require escrow
        from app.agent.job_lifecycle import JobCategory
        escrow_categories = [
            JobCategory.TRADE_EXECUTION,
            JobCategory.PORTFOLIO_MANAGEMENT
        ]
        
        return high_value or job.specification.category in escrow_categories
    
    async def _release_from_escrow(self, job: JobRecord) -> Dict[str, Any]:
        """
        Release payment from escrow for a job.
        
        Args:
            job: Job record to release payment for
            
        Returns:
            Dict with release result details
        """
        job_id = job.job_id
        escrow_id = f"escrow-{job_id}"
        
        try:
            # Calculate fees
            payment_amount = job.payment_amount
            fee_amount = payment_amount * self.fee_percentage / 100
            agent_amount = payment_amount - fee_amount
            
            # Release from escrow
            release_result = await self.wallet.release_from_escrow(
                escrow_id=escrow_id,
                agent_amount=agent_amount,
                fee_amount=fee_amount
            )
            
            logger.info(f"Released {agent_amount} VIRTUAL from escrow for job {job_id}")
            
            return {
                "success": True,
                "txid": release_result.get("txid"),
                "immediate_payment": True,
                "fee_amount": fee_amount,
                "agent_amount": agent_amount
            }
            
        except Exception as e:
            logger.error(f"Error releasing from escrow for job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "immediate_payment": False
            }
    
    async def _request_direct_payment(self, job: JobRecord) -> Dict[str, Any]:
        """
        Request direct payment for a job.
        
        Args:
            job: Job record to request payment for
            
        Returns:
            Dict with payment request details
        """
        job_id = job.job_id
        requester_address = job.specification.requester_address
        payment_amount = job.payment_amount
        
        try:
            # Calculate fees
            fee_amount = payment_amount * self.fee_percentage / 100
            agent_amount = payment_amount - fee_amount
            
            # Create a payment request on the ACP protocol
            payment_request = await self._create_acp_payment_request(
                job_id=job_id,
                requester_address=requester_address,
                agent_amount=agent_amount,
                fee_amount=fee_amount
            )
            
            logger.info(f"Created payment request for job {job_id} for {payment_amount} VIRTUAL")
            
            return {
                "success": True,
                "payment_request_id": payment_request.get("request_id"),
                "immediate_payment": False,
                "fee_amount": fee_amount,
                "agent_amount": agent_amount
            }
            
        except Exception as e:
            logger.error(f"Error creating payment request for job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "immediate_payment": False
            }
    
    async def _create_acp_payment_request(
        self,
        job_id: str,
        requester_address: str,
        agent_amount: float,
        fee_amount: float
    ) -> Dict[str, Any]:
        """
        Create a payment request on the ACP protocol.
        
        Args:
            job_id: ID of the job
            requester_address: Address of the requester
            agent_amount: Amount for the agent
            fee_amount: Fee amount
            
        Returns:
            Dict with payment request details
        """
        agent_wallet_address = await self.wallet.get_wallet_address()
        agent_signature = await self.wallet.sign_message(
            f"Payment request for job {job_id}: {agent_amount + fee_amount} VIRTUAL"
        )
        
        # Connect to ACP service registry
        acp_url = config.acp.service_registry_url
        
        # Create payment request payload
        payment_request = {
            "job_id": job_id,
            "requester_address": requester_address,
            "agent_address": agent_wallet_address,
            "agent_signature": agent_signature,
            "agent_amount": agent_amount,
            "fee_amount": fee_amount,
            "token_address": config.wallet.virtual_token_address,
            "timestamp": datetime.now().isoformat()
        }
        
        # Submit payment request to ACP
        # In a real implementation, this would make an API call to the ACP service
        logger.info(f"Would submit payment request to ACP: {payment_request}")
        
        # Return response with generated request ID
        import uuid
        request_id = f"pr-{str(uuid.uuid4())}"
        
        return {
            "request_id": request_id,
            "status": "pending",
            "expiry": (datetime.now() + timedelta(minutes=30)).isoformat()
        }
    
    async def _check_payment_status(self, job: JobRecord) -> PaymentStatus:
        """
        Check the status of a payment.
        
        Args:
            job: Job record to check payment status for
            
        Returns:
            PaymentStatus: Current payment status
        """
        job_id = job.job_id
        
        try:
            # In a real implementation, this would query the blockchain or ACP service
            # to check the payment status
            
            # Check how long we've been waiting
            time_waiting = (datetime.now() - job.updated_at).total_seconds()
            
            if time_waiting > self.payment_timeout:
                logger.warning(f"Payment for job {job_id} timed out")
                return PaymentStatus.FAILED
            
            # Query the ACP protocol for payment status
            payment_status = await self._query_acp_payment_status(job_id)
            
            if payment_status.get("status") == "completed":
                # Update job with payment transaction info
                job.payment_txid = payment_status.get("txid")
                job.payment_status = PaymentStatus.COMPLETED
                
                logger.info(f"Payment for job {job_id} completed with txid {job.payment_txid}")
                return PaymentStatus.COMPLETED
                
            elif payment_status.get("status") == "failed":
                logger.warning(f"Payment for job {job_id} failed: {payment_status.get('reason')}")
                return PaymentStatus.FAILED
                
            else:
                # Still pending
                return PaymentStatus.PENDING
                
        except Exception as e:
            logger.error(f"Error checking payment status for job {job_id}: {e}")
            # Don't change status on error, just return current status
            return job.payment_status
    
    async def _query_acp_payment_status(self, job_id: str) -> Dict[str, Any]:
        """
        Query the ACP protocol for payment status.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Dict with payment status details
        """
        # In a real implementation, this would query the ACP protocol
        # or blockchain for payment status
        
        # Connect to ACP service registry
        acp_url = config.acp.service_registry_url
        
        # Query payment status
        logger.debug(f"Would query ACP for payment status of job {job_id}")
        
        # For now, simulate a response
        # In a real implementation, we would check for transaction confirmation
        # on the blockchain or a status from the ACP protocol
        
        # For demo purposes, randomly simulate payment completion
        # This would be replaced with actual verification in production
        import random
        if random.random() < 0.2:  # 20% chance of payment completion in each check
            return {
                "status": "completed",
                "txid": f"0x{random.randint(0, 2**64):x}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "pending",
                "reason": "Waiting for payment confirmation"
            }
    
    async def refund_payment(self, job: JobRecord, reason: str) -> Dict[str, Any]:
        """
        Process a refund for a job payment.
        
        Args:
            job: Job record to refund
            reason: Reason for the refund
            
        Returns:
            Dict with refund result details
        """
        job_id = job.job_id
        
        try:
            if job.payment_status != PaymentStatus.COMPLETED:
                return {
                    "success": False,
                    "error": f"Cannot refund job {job_id} with status {job.payment_status}"
                }
            
            # Process refund
            refund_amount = job.payment_amount
            requester_address = job.specification.requester_address
            
            # Execute refund transaction
            refund_result = await self.wallet.transfer_tokens(
                recipient=requester_address,
                amount=refund_amount,
                token_address=config.wallet.virtual_token_address
            )
            
            # Update job payment status
            job.payment_status = PaymentStatus.REFUNDED
            
            logger.info(f"Refunded {refund_amount} VIRTUAL to {requester_address} for job {job_id}")
            
            return {
                "success": True,
                "refund_amount": refund_amount,
                "txid": refund_result.get("txid"),
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error processing refund for job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
payment_processor = None

def initialize_payment_processor(wallet: SmartWallet):
    """Initialize the global payment processor instance."""
    global payment_processor
    payment_processor = PaymentProcessor(wallet)
    return payment_processor


# Alias for backward compatibility
JobPaymentProcessor = PaymentProcessor
