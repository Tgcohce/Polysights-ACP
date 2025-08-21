"""
Job result delivery module for the ACP Polymarket Trading Agent.

This module manages the delivery of job results to requesters,
including result formatting, validation, and submission through
the ACP protocol.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from loguru import logger

from app.agent.job_lifecycle import (
    JobLifecycleManager,
    JobState,
    JobRecord,
    lifecycle_manager
)
from app.wallet.erc6551 import SmartWallet
from app.utils.config import config


class ResultDeliveryManager:
    """
    Manager for job result delivery.
    
    Responsible for formatting, validating, and delivering job results
    to requesters through the ACP protocol.
    """
    
    def __init__(self, wallet: SmartWallet):
        """
        Initialize the ResultDeliveryManager.
        
        Args:
            wallet: Smart wallet instance for signing deliveries
        """
        self.wallet = wallet
        self.max_delivery_attempts = 3
        self.delivery_retry_delay = 60  # seconds
        self.delivery_timeout = 300  # 5 minutes
        self.delivery_monitor_task = None
        self.delivery_monitor_interval = 30  # seconds
        
        # Register state handlers
        lifecycle_manager.register_state_handler(
            JobState.COMPLETED, self.handle_completed_job
        )
        lifecycle_manager.register_state_handler(
            JobState.DELIVERING, self.handle_delivering_job
        )
        
        logger.info("Initialized ResultDeliveryManager")
    
    async def start(self):
        """Start the delivery manager, including delivery monitoring."""
        logger.info("Starting ResultDeliveryManager")
        self.delivery_monitor_task = asyncio.create_task(self._monitor_deliveries())
    
    async def stop(self):
        """Stop the delivery manager and clean up."""
        logger.info("Stopping ResultDeliveryManager")
        if self.delivery_monitor_task:
            self.delivery_monitor_task.cancel()
            try:
                await self.delivery_monitor_task
            except asyncio.CancelledError:
                pass
    
    async def handle_completed_job(self, job: JobRecord):
        """
        Handle a job in the COMPLETED state for result delivery.
        
        Args:
            job: Job record to deliver results for
        """
        # Start delivery process
        await lifecycle_manager.transition_job_state(
            job.job_id, JobState.DELIVERING, "Starting result delivery"
        )
    
    async def handle_delivering_job(self, job: JobRecord):
        """
        Handle a job in the DELIVERING state.
        
        Args:
            job: Job record to process
        """
        job_id = job.job_id
        
        # Track delivery attempts
        delivery_attempts = job.error_details.get("delivery_attempts", 0) if job.error_details else 0
        
        if delivery_attempts >= self.max_delivery_attempts:
            # Too many attempts, mark as delivery error
            await lifecycle_manager.transition_job_state(
                job_id,
                JobState.DELIVERY_ERROR,
                f"Failed to deliver after {delivery_attempts} attempts"
            )
            return
        
        # Increment attempt counter
        if not job.error_details:
            job.error_details = {}
        job.error_details["delivery_attempts"] = delivery_attempts + 1
        
        # Deliver result
        try:
            delivery_result = await self.deliver_job_result(job)
            
            if delivery_result.get("success", False):
                # Mark as completed and move to payment state
                await lifecycle_manager.transition_job_state(
                    job_id, JobState.COMPLETED, "Result delivered successfully"
                )
            else:
                # Delivery failed
                error_msg = delivery_result.get("error", "Unknown delivery error")
                job.last_error = error_msg
                
                # Schedule retry after delay
                asyncio.create_task(self._retry_delivery_after_delay(job))
        except Exception as e:
            # Unhandled error
            logger.error(f"Error delivering result for job {job_id}: {e}")
            job.last_error = str(e)
            
            # Schedule retry after delay
            asyncio.create_task(self._retry_delivery_after_delay(job))
    
    async def _retry_delivery_after_delay(self, job: JobRecord):
        """
        Retry delivery after delay.
        
        Args:
            job: Job record to retry
        """
        await asyncio.sleep(self.delivery_retry_delay)
        
        # Check if job is still in DELIVERING state
        current_job = lifecycle_manager.get_job(job.job_id)
        if current_job and current_job.state == JobState.DELIVERING:
            # Retry delivery by transitioning to DELIVERING again
            # This will trigger the handle_delivering_job handler
            await lifecycle_manager.transition_job_state(
                job.job_id, JobState.DELIVERING, "Retrying result delivery"
            )
    
    async def _monitor_deliveries(self):
        """Monitor deliveries and handle timeouts."""
        try:
            while True:
                # Check for timed out deliveries
                delivering_jobs = lifecycle_manager.get_jobs_by_state(JobState.DELIVERING)
                
                for job in delivering_jobs:
                    # Check if delivery has timed out
                    time_in_state = (datetime.now() - job.updated_at).total_seconds()
                    
                    if time_in_state > self.delivery_timeout:
                        # Delivery timed out
                        await lifecycle_manager.transition_job_state(
                            job.job_id,
                            JobState.DELIVERY_ERROR,
                            f"Delivery timed out after {time_in_state:.2f} seconds"
                        )
                
                await asyncio.sleep(self.delivery_monitor_interval)
        except asyncio.CancelledError:
            # Expected during shutdown
            logger.info("Delivery monitor stopped")
        except Exception as e:
            logger.error(f"Error in delivery monitor: {e}")
    
    async def deliver_job_result(self, job: JobRecord) -> Dict[str, Any]:
        """
        Deliver job result to the requester.
        
        Args:
            job: Job record with results to deliver
            
        Returns:
            Dict with delivery status
        """
        job_id = job.job_id
        requester_id = job.specification.requester_id
        
        if not job.result:
            return {
                "success": False,
                "error": "No result available for delivery"
            }
        
        try:
            # Format the result for delivery
            formatted_result = await self._format_result(job)
            
            # Sign the result
            signed_result = await self._sign_result(job_id, formatted_result)
            
            # Deliver through ACP protocol
            delivery_result = await self._deliver_to_acp(job, signed_result)
            
            if delivery_result.get("success", False):
                logger.info(f"Successfully delivered result for job {job_id} to requester {requester_id}")
            else:
                logger.warning(f"Failed to deliver result for job {job_id}: {delivery_result.get('error')}")
            
            return delivery_result
            
        except Exception as e:
            logger.error(f"Error delivering result for job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _format_result(self, job: JobRecord) -> Dict[str, Any]:
        """
        Format job result for delivery.
        
        Args:
            job: Job record with results
            
        Returns:
            Formatted result dictionary
        """
        # Extract job metadata
        job_id = job.job_id
        job_type = job.specification.job_type
        job_category = job.specification.category
        
        # Format the result based on job type
        result_data = job.result.data if job.result else {}
        
        # Create a standardized result format
        formatted_result = {
            "job_id": job_id,
            "job_type": str(job_type),
            "job_category": str(job_category),
            "timestamp": datetime.now().isoformat(),
            "success": job.result.success if job.result else False,
            "completion_percentage": job.result.completion_percentage if job.result else 0.0,
            "execution_time_seconds": job.result.execution_time_seconds if job.result else 0.0,
            "agent_id": config.agent.agent_id,
            "data": result_data
        }
        
        return formatted_result
    
    async def _sign_result(self, job_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign job result for verification.
        
        Args:
            job_id: ID of the job
            result: Formatted result to sign
            
        Returns:
            Signed result with verification data
        """
        # Convert result to JSON string for signing
        result_json = json.dumps(result, sort_keys=True)
        
        # Sign with smart wallet
        signature = await self.wallet.sign_message(result_json)
        
        # Add verification data
        signed_result = result.copy()
        signed_result["verification"] = {
            "signature": signature,
            "signer_address": await self.wallet.get_wallet_address(),
            "timestamp": datetime.now().isoformat()
        }
        
        return signed_result
    
    async def _deliver_to_acp(self, job: JobRecord, signed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver result to the requester through ACP protocol.
        
        Args:
            job: Job record
            signed_result: Signed result data
            
        Returns:
            Dict with delivery status
        """
        job_id = job.job_id
        requester_id = job.specification.requester_id
        
        # Connect to ACP service registry
        acp_url = config.acp.service_registry_url
        
        # Prepare delivery payload
        delivery_payload = {
            "job_id": job_id,
            "requester_id": requester_id,
            "provider_id": config.agent.agent_id,
            "timestamp": datetime.now().isoformat(),
            "result": signed_result
        }
        
        # Submit result to ACP
        # In a real implementation, this would make an API call to the ACP service
        logger.info(f"Delivering result to ACP for job {job_id}")
        
        # For now, simulate a successful delivery
        # This would be replaced with actual ACP integration in production
        # Actual ACP integration implementation:
        
        try:
            # Connect to ACP service registry
            from aiohttp import ClientSession, ClientTimeout
            
            timeout = ClientTimeout(total=30)  # 30 seconds timeout
            
            async with ClientSession(timeout=timeout) as session:
                # Submit result to ACP
                async with session.post(
                    f"{acp_url}/api/v1/deliveries",
                    json=delivery_payload,
                    headers={
                        "Authorization": f"Bearer {config.acp.api_key}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        return {
                            "success": True,
                            "delivery_id": result_data.get("delivery_id"),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"ACP delivery failed with status {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"ACP delivery failed: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Error in ACP delivery: {e}")
            return {
                "success": False,
                "error": f"ACP delivery exception: {str(e)}"
            }
    
    async def get_delivery_status(self, delivery_id: str) -> Dict[str, Any]:
        """
        Check the status of a delivery.
        
        Args:
            delivery_id: ID of the delivery to check
            
        Returns:
            Dict with delivery status
        """
        # Connect to ACP service registry
        acp_url = config.acp.service_registry_url
        
        # In a real implementation, this would query the ACP service
        logger.debug(f"Would query ACP for delivery status of {delivery_id}")
        
        try:
            # Connect to ACP service registry
            from aiohttp import ClientSession, ClientTimeout
            
            timeout = ClientTimeout(total=10)  # 10 seconds timeout
            
            async with ClientSession(timeout=timeout) as session:
                # Query delivery status
                async with session.get(
                    f"{acp_url}/api/v1/deliveries/{delivery_id}",
                    headers={
                        "Authorization": f"Bearer {config.acp.api_key}"
                    }
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"ACP status query failed with status {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"ACP status query failed: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Error querying delivery status: {e}")
            return {
                "success": False,
                "error": f"Delivery status exception: {str(e)}"
            }


# Global instance
delivery_manager = None

def initialize_delivery_manager(wallet: SmartWallet):
    """Initialize the global delivery manager instance."""
    global delivery_manager
    delivery_manager = ResultDeliveryManager(wallet)
    return delivery_manager


# Alias for backward compatibility
JobDeliveryManager = ResultDeliveryManager
