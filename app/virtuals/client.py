"""
Virtuals Protocol integration for AI agent deployment.

This module handles registration, lifecycle management, and communication
with the Virtuals ecosystem.
"""
import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger
import aiohttp

from app.utils.config import config
from app.wallet.erc6551 import SmartWallet


class VirtualsClient:
    """
    Client for interacting with the Virtuals Protocol.
    
    Handles agent registration, task management, and protocol communication.
    """
    
    def __init__(self, wallet: SmartWallet):
        self.wallet = wallet
        self.base_url = config.get("VIRTUALS_API_URL", "https://api.virtuals.io")
        self.agent_id = None
        self.registered = False
        
    async def register_agent(self) -> bool:
        """
        Register this agent with the Virtuals Protocol.
        
        Returns:
            bool: Registration success
        """
        try:
            agent_metadata = {
                "name": "ACP Polymarket Trading Agent",
                "description": "Autonomous prediction market trading agent",
                "capabilities": [
                    "market_data_analysis",
                    "order_execution", 
                    "risk_management",
                    "arbitrage_detection"
                ],
                "wallet_address": self.wallet.address,
                "version": "1.0.0",
                "protocols": ["ACP", "Polymarket", "ERC-6551"]
            }
            
            # Sign registration payload
            payload = json.dumps(agent_metadata, sort_keys=True)
            signature = self.wallet.sign_message(payload)
            
            registration_data = {
                "metadata": agent_metadata,
                "signature": signature,
                "wallet_address": self.wallet.address
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/agents/register",
                    json=registration_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.agent_id = result.get("agent_id")
                        self.registered = True
                        logger.info(f"Successfully registered with Virtuals Protocol: {self.agent_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Registration failed: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error registering with Virtuals Protocol: {e}")
            return False
    
    async def report_status(self, status: Dict[str, Any]) -> bool:
        """
        Report agent status to Virtuals Protocol.
        
        Args:
            status: Current agent status and metrics
            
        Returns:
            bool: Success status
        """
        if not self.registered:
            logger.warning("Agent not registered with Virtuals Protocol")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/agents/{self.agent_id}/status",
                    json=status,
                    headers={"Authorization": f"Bearer {self.agent_id}"}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error reporting status to Virtuals: {e}")
            return False
    
    async def get_tasks(self) -> list:
        """
        Retrieve pending tasks from Virtuals Protocol.
        
        Returns:
            list: List of pending tasks
        """
        if not self.registered:
            return []
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/agents/{self.agent_id}/tasks",
                    headers={"Authorization": f"Bearer {self.agent_id}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("tasks", [])
                    return []
                    
        except Exception as e:
            logger.error(f"Error retrieving tasks from Virtuals: {e}")
            return []
