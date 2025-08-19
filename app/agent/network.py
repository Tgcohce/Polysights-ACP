"""
Agent Network Manager for ACP Polymarket Trading Agent.

This module handles agent discovery, collaboration, and messaging
within the ACP ecosystem. It allows the agent to find other agents,
evaluate their capabilities, and collaborate on tasks.
"""
import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
import uuid

from loguru import logger
from pydantic import BaseModel, Field, root_validator

from app.wallet.erc6551 import SmartWallet
from app.utils.config import config


class AgentCapability(str, Enum):
    """Agent capabilities within the ACP ecosystem."""
    MARKET_ANALYSIS = "market_analysis"
    TRADE_EXECUTION = "trade_execution"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    ARBITRAGE_DETECTION = "arbitrage_detection"
    DATA_PROVIDER = "data_provider"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_MANAGEMENT = "risk_management"
    EVENT_DETECTION = "event_detection"


class AgentRole(str, Enum):
    """Agent roles within the ACP ecosystem."""
    PROVIDER = "provider"
    REQUESTER = "requester"
    HYBRID = "hybrid"


class AgentTrustLevel(int, Enum):
    """Trust levels for agents in the network."""
    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


class AgentProfile(BaseModel):
    """
    Agent profile information.
    
    Contains metadata about an agent in the network.
    """
    agent_id: str
    name: str
    role: AgentRole
    capabilities: List[AgentCapability]
    description: Optional[str] = None
    wallet_address: str
    reputation_score: float = 0.0
    success_rate: float = 0.0
    completed_jobs: int = 0
    total_jobs: int = 0
    specializations: List[str] = Field(default_factory=list)
    fee_model: Dict[str, Any] = Field(default_factory=dict)
    region: Optional[str] = None
    last_active: Optional[datetime] = None
    first_seen: datetime = Field(default_factory=datetime.now)
    trust_level: AgentTrustLevel = AgentTrustLevel.MEDIUM
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class CollaborationRequest(BaseModel):
    """
    Collaboration request between agents.
    
    Used to initiate collaboration between agents.
    """
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str
    provider_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    fee_proposal: float = 0.0
    deadline: Optional[datetime] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    signature: Optional[str] = None


class CollaborationResponse(BaseModel):
    """
    Response to a collaboration request.
    
    Used by agents to respond to collaboration requests.
    """
    request_id: str
    provider_id: str
    accepted: bool
    fee_counter: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    signature: Optional[str] = None


class AgentMessage(BaseModel):
    """
    Message between agents in the network.
    
    Used for agent-to-agent communication.
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: str
    subject: str
    content: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    signature: Optional[str] = None
    reply_to: Optional[str] = None
    encrypted: bool = False
    urgent: bool = False
    read: bool = False


class AgentDiscoveryFilter(BaseModel):
    """
    Filter for agent discovery.
    
    Used to find agents with specific characteristics.
    """
    capabilities: Optional[List[AgentCapability]] = None
    min_reputation: float = 0.0
    min_success_rate: float = 0.0
    roles: Optional[List[AgentRole]] = None
    regions: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    min_trust_level: AgentTrustLevel = AgentTrustLevel.UNTRUSTED
    active_since: Optional[datetime] = None
    custom_filters: Dict[str, Any] = Field(default_factory=dict)


class AgentNetworkManager:
    """
    Manager for agent discovery and collaboration within the ACP ecosystem.
    
    This class handles finding other agents, evaluating their capabilities,
    establishing collaborations, and messaging between agents.
    """
    
    def __init__(self, wallet: SmartWallet = None):
        """
        Initialize the agent network manager.
        
        Args:
            wallet: Smart wallet for agent authentication and messaging
        """
        self.wallet = wallet
        self.agent_id = config.agent.agent_id
        self.agent_name = config.agent.agent_name
        self.registry_url = config.acp.service_registry_url
        self.registry_refresh_interval = 300  # 5 minutes
        
        # Local cache of agents
        self.known_agents: Dict[str, AgentProfile] = {}
        self.trusted_agents: Set[str] = set()
        self.blocked_agents: Set[str] = set()
        
        # Collaboration tracking
        self.active_collaborations: Dict[str, Any] = {}
        self.collaboration_history: List[Dict[str, Any]] = []
        
        # Messaging
        self.unread_messages: List[AgentMessage] = []
        self.message_history: Dict[str, List[AgentMessage]] = {}
        
        # Background tasks
        self.registry_refresh_task = None
        self.message_polling_task = None
        
        logger.info(f"Initialized AgentNetworkManager for agent {self.agent_id}")
    
    async def start(self):
        """Start the agent network manager."""
        logger.info("Starting AgentNetworkManager")
        
        # Start background tasks
        self.registry_refresh_task = asyncio.create_task(self._refresh_agent_registry())
        self.message_polling_task = asyncio.create_task(self._poll_for_messages())
    
    async def stop(self):
        """Stop the agent network manager."""
        logger.info("Stopping AgentNetworkManager")
        
        # Stop background tasks
        if self.registry_refresh_task:
            self.registry_refresh_task.cancel()
            try:
                await self.registry_refresh_task
            except asyncio.CancelledError:
                pass
        
        if self.message_polling_task:
            self.message_polling_task.cancel()
            try:
                await self.message_polling_task
            except asyncio.CancelledError:
                pass
    
    async def discover_agents(
        self, 
        filter_params: Optional[AgentDiscoveryFilter] = None
    ) -> List[AgentProfile]:
        """
        Discover agents in the ACP ecosystem.
        
        Args:
            filter_params: Filter parameters for discovery
            
        Returns:
            List of discovered agent profiles
        """
        filter_params = filter_params or AgentDiscoveryFilter()
        
        try:
            # Query ACP service registry
            agents = await self._query_agent_registry(filter_params)
            
            # Update local cache
            for agent in agents:
                self.known_agents[agent.agent_id] = agent
            
            logger.info(f"Discovered {len(agents)} agents matching criteria")
            return agents
            
        except Exception as e:
            logger.error(f"Error discovering agents: {e}")
            return []
    
    async def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """
        Get an agent's profile.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent profile if found, None otherwise
        """
        # Check local cache first
        if agent_id in self.known_agents:
            return self.known_agents[agent_id]
        
        try:
            # Query ACP service registry
            profile = await self._get_agent_from_registry(agent_id)
            
            if profile:
                # Update local cache
                self.known_agents[agent_id] = profile
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent profile for {agent_id}: {e}")
            return None
    
    async def send_collaboration_request(
        self,
        provider_id: str,
        task_type: str,
        description: str,
        parameters: Dict[str, Any],
        fee_proposal: float = 0.0,
        deadline: Optional[datetime] = None
    ) -> Optional[CollaborationRequest]:
        """
        Send a collaboration request to another agent.
        
        Args:
            provider_id: ID of the provider agent
            task_type: Type of task for collaboration
            description: Description of the collaboration task
            parameters: Task parameters
            fee_proposal: Proposed fee for the task
            deadline: Deadline for task completion
            
        Returns:
            Collaboration request if sent successfully, None otherwise
        """
        try:
            # Create collaboration request
            request = CollaborationRequest(
                requester_id=self.agent_id,
                provider_id=provider_id,
                task_type=task_type,
                description=description,
                parameters=parameters,
                fee_proposal=fee_proposal,
                deadline=deadline
            )
            
            # Sign the request
            request_data = request.dict(exclude={"signature"})
            request.signature = await self.wallet.sign_message(
                json.dumps(request_data, default=str)
            )
            
            # Send to ACP service registry
            response = await self._submit_collaboration_request(request)
            
            if response:
                logger.info(f"Sent collaboration request {request.request_id} to agent {provider_id}")
                
                # Track in active collaborations
                self.active_collaborations[request.request_id] = {
                    "request": request.dict(),
                    "status": "pending",
                    "timestamp": datetime.now()
                }
                
                return request
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending collaboration request to {provider_id}: {e}")
            return None
    
    async def respond_to_collaboration(
        self,
        request_id: str,
        accepted: bool,
        fee_counter: Optional[float] = None,
        estimated_completion_time: Optional[datetime] = None,
        message: Optional[str] = None
    ) -> Optional[CollaborationResponse]:
        """
        Respond to a collaboration request.
        
        Args:
            request_id: ID of the collaboration request
            accepted: Whether to accept the collaboration
            fee_counter: Counter-proposed fee (if any)
            estimated_completion_time: Estimated completion time
            message: Additional message
            
        Returns:
            Collaboration response if sent successfully, None otherwise
        """
        try:
            # Create collaboration response
            response = CollaborationResponse(
                request_id=request_id,
                provider_id=self.agent_id,
                accepted=accepted,
                fee_counter=fee_counter,
                estimated_completion_time=estimated_completion_time,
                message=message
            )
            
            # Sign the response
            response_data = response.dict(exclude={"signature"})
            response.signature = await self.wallet.sign_message(
                json.dumps(response_data, default=str)
            )
            
            # Send to ACP service registry
            result = await self._submit_collaboration_response(response)
            
            if result:
                logger.info(f"Sent collaboration response for request {request_id}, accepted: {accepted}")
                
                # Update active collaborations if this was for an active request
                if request_id in self.active_collaborations:
                    self.active_collaborations[request_id]["status"] = "accepted" if accepted else "rejected"
                    self.active_collaborations[request_id]["response"] = response.dict()
                
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error responding to collaboration request {request_id}: {e}")
            return None
    
    async def send_message(
        self,
        recipient_id: str,
        subject: str,
        content: Dict[str, Any],
        reply_to: Optional[str] = None,
        encrypted: bool = False,
        urgent: bool = False
    ) -> Optional[AgentMessage]:
        """
        Send a message to another agent.
        
        Args:
            recipient_id: ID of the recipient agent
            subject: Message subject
            content: Message content
            reply_to: ID of message being replied to (if any)
            encrypted: Whether the message should be encrypted
            urgent: Whether the message is urgent
            
        Returns:
            Sent message if successful, None otherwise
        """
        try:
            # Create message
            message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                subject=subject,
                content=content,
                reply_to=reply_to,
                encrypted=encrypted,
                urgent=urgent
            )
            
            # Sign the message
            message_data = message.dict(exclude={"signature"})
            message.signature = await self.wallet.sign_message(
                json.dumps(message_data, default=str)
            )
            
            # Encrypt if needed
            if encrypted:
                # In a real implementation, this would use the recipient's public key
                # to encrypt the message content
                # For now, we just mark it as encrypted
                pass
            
            # Send to ACP messaging service
            result = await self._submit_message(message)
            
            if result:
                logger.info(f"Sent message {message.message_id} to agent {recipient_id}")
                
                # Track in message history
                if recipient_id not in self.message_history:
                    self.message_history[recipient_id] = []
                
                self.message_history[recipient_id].append(message)
                
                return message
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending message to {recipient_id}: {e}")
            return None
    
    async def get_messages(self) -> List[AgentMessage]:
        """
        Get unread messages.
        
        Returns:
            List of unread messages
        """
        return self.unread_messages.copy()
    
    def mark_message_read(self, message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: ID of the message to mark
            
        Returns:
            True if message was marked, False otherwise
        """
        for i, message in enumerate(self.unread_messages):
            if message.message_id == message_id:
                message.read = True
                self.unread_messages.pop(i)
                return True
        
        return False
    
    async def get_conversation_history(self, agent_id: str) -> List[AgentMessage]:
        """
        Get conversation history with an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of messages exchanged with the agent
        """
        try:
            # Get history from local cache
            history = self.message_history.get(agent_id, [])
            
            # Fetch additional history from ACP if needed
            if not history:
                history = await self._fetch_message_history(agent_id)
                self.message_history[agent_id] = history
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history with {agent_id}: {e}")
            return []
    
    def trust_agent(self, agent_id: str) -> bool:
        """
        Add an agent to the trusted list.
        
        Args:
            agent_id: ID of the agent to trust
            
        Returns:
            True if agent was added to trusted list
        """
        self.trusted_agents.add(agent_id)
        
        if agent_id in self.blocked_agents:
            self.blocked_agents.remove(agent_id)
        
        if agent_id in self.known_agents:
            self.known_agents[agent_id].trust_level = AgentTrustLevel.HIGH
        
        logger.info(f"Added agent {agent_id} to trusted list")
        return True
    
    def block_agent(self, agent_id: str) -> bool:
        """
        Add an agent to the blocked list.
        
        Args:
            agent_id: ID of the agent to block
            
        Returns:
            True if agent was added to blocked list
        """
        self.blocked_agents.add(agent_id)
        
        if agent_id in self.trusted_agents:
            self.trusted_agents.remove(agent_id)
        
        if agent_id in self.known_agents:
            self.known_agents[agent_id].trust_level = AgentTrustLevel.UNTRUSTED
        
        logger.info(f"Added agent {agent_id} to blocked list")
        return True
    
    def is_agent_trusted(self, agent_id: str) -> bool:
        """
        Check if an agent is trusted.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            True if agent is trusted
        """
        return agent_id in self.trusted_agents
    
    def is_agent_blocked(self, agent_id: str) -> bool:
        """
        Check if an agent is blocked.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            True if agent is blocked
        """
        return agent_id in self.blocked_agents
    
    async def _refresh_agent_registry(self):
        """Periodically refresh the agent registry."""
        try:
            while True:
                # Refresh registry
                logger.debug("Refreshing agent registry")
                
                # Get all agents from registry
                filter_params = AgentDiscoveryFilter(
                    min_reputation=0.0,
                    min_success_rate=0.0,
                    min_trust_level=AgentTrustLevel.UNTRUSTED
                )
                
                agents = await self._query_agent_registry(filter_params)
                
                # Update local cache
                for agent in agents:
                    self.known_agents[agent.agent_id] = agent
                
                # Wait for next refresh
                await asyncio.sleep(self.registry_refresh_interval)
                
        except asyncio.CancelledError:
            logger.info("Agent registry refresh task cancelled")
        except Exception as e:
            logger.error(f"Error in agent registry refresh task: {e}")
    
    async def _poll_for_messages(self):
        """Periodically poll for new messages."""
        try:
            while True:
                # Poll for messages
                logger.debug("Polling for messages")
                
                # Get unread messages from ACP
                messages = await self._fetch_unread_messages()
                
                # Update unread messages and history
                for message in messages:
                    self.unread_messages.append(message)
                    
                    # Add to conversation history
                    sender_id = message.sender_id
                    if sender_id not in self.message_history:
                        self.message_history[sender_id] = []
                    
                    self.message_history[sender_id].append(message)
                
                # Wait before next poll
                await asyncio.sleep(30)  # Poll every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Message polling task cancelled")
        except Exception as e:
            logger.error(f"Error in message polling task: {e}")
