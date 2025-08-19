"""
Configuration management module for the ACP Polymarket Trading Agent.
"""
import os
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TradingConfig(BaseModel):
    """Trading parameters configuration."""

    max_position_size: float = Field(
        1000.0, description="Maximum position size in USD"
    )
    max_portfolio_risk: float = Field(
        0.02, description="Maximum portfolio risk as a decimal (e.g., 0.02 = 2%)"
    )
    default_sla: int = Field(
        300, description="Default SLA for jobs in seconds (5 minutes)"
    )
    min_arbitrage_threshold: float = Field(
        0.005, description="Minimum arbitrage profit threshold as a decimal"
    )
    max_concurrent_jobs: int = Field(
        5, description="Maximum number of concurrent jobs to process"
    )
    restricted_regions: List[str] = Field(
        default_factory=lambda: ["US", "UK"], description="List of restricted regions for trading"
    )
    max_position_percentage: float = Field(
        0.1, description="Maximum position size as percentage of portfolio (e.g., 0.1 = 10%)"
    )
    min_requester_reputation: float = Field(
        0.7, description="Minimum requester reputation score (0.0 to 1.0)"
    )
    max_daily_loss: float = Field(
        500.0, description="Maximum daily loss limit in USD"
    )
    stop_loss_percentage: float = Field(
        0.05, description="Stop loss percentage (e.g., 0.05 = 5%)"
    )
    take_profit_percentage: float = Field(
        0.15, description="Take profit percentage (e.g., 0.15 = 15%)"
    )
    fee_percentage: float = Field(
        0.02, description="Trading fee percentage (e.g., 0.02 = 2%)"
    )


class AcpConfig(BaseModel):
    """ACP SDK configuration."""

    service_registry_url: str = Field(
        os.getenv("ACP_SERVICE_REGISTRY_URL", "https://app.virtuals.io/acp"),
        description="ACP service registry URL",
    )
    whitelisted_wallet_private_key: Optional[str] = Field(
        os.getenv("WHITELISTED_WALLET_PRIVATE_KEY"),
        description="Private key for the whitelisted wallet",
    )
    agent_name: str = Field(
        "PolysightsTrader", description="Name of the ACP agent"
    )
    agent_description: str = Field(
        "Advanced prediction market trading agent powered by Polysights analytics",
        description="Description of the agent",
    )


class PolymarketConfig(BaseModel):
    """Polymarket API configuration."""

    api_key: Optional[str] = Field(
        os.getenv("POLYMARKET_API_KEY"), description="Polymarket API key"
    )
    secret: Optional[str] = Field(
        os.getenv("POLYMARKET_SECRET"), description="Polymarket API secret"
    )
    passphrase: Optional[str] = Field(
        os.getenv("POLYMARKET_PASSPHRASE"), description="Polymarket API passphrase"
    )
    base_url: str = Field(
        os.getenv("POLYMARKET_BASE_URL", "https://clob.polymarket.com"),
        description="Polymarket CLOB API base URL",
    )
    websocket_url: str = Field(
        os.getenv("POLYMARKET_WEBSOCKET_URL", "wss://clob.polymarket.com/ws"),
        description="Polymarket WebSocket URL",
    )


class PolysightsConfig(BaseModel):
    """Polysights API configuration."""

    api_key: Optional[str] = Field(
        os.getenv("POLYSIGHTS_API_KEY"), description="Polysights API key"
    )
    base_url: str = Field(
        os.getenv("POLYSIGHTS_BASE_URL", "https://app.polysights.xyz/api"),
        description="Polysights API base URL",
    )


class DatabaseConfig(BaseModel):
    """Database configuration."""

    connection_string: str = Field(
        os.getenv(
            "DATABASE_URL", "sqlite:///./acp_polymarket_agent.db"
        ),
        description="Database connection string",
    )
    pool_size: int = Field(
        5, description="Database connection pool size"
    )
    max_overflow: int = Field(
        10, description="Maximum number of connections to overflow"
    )


class AgentConfig(BaseModel):
    """Agent configuration."""

    agent_id: str = Field(
        os.getenv("AGENT_ID", "acp-polymarket-agent"),
        description="Unique agent identifier",
    )
    agent_name: str = Field(
        os.getenv("AGENT_NAME", "ACP Polymarket Trading Agent"),
        description="Human-readable agent name",
    )
    version: str = Field(
        os.getenv("AGENT_VERSION", "1.0.0"),
        description="Agent version",
    )


class Config:
    """Main configuration class for the application."""

    def __init__(self):
        self.trading = TradingConfig()
        self.acp = AcpConfig()
        self.polymarket = PolymarketConfig()
        self.polysights = PolysightsConfig()
        self.database = DatabaseConfig()
        self.agent = AgentConfig()
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default."""
        # Support environment variable access
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
            
        # Support nested attribute access
        if hasattr(self, key.lower()):
            return getattr(self, key.lower())
            
        return default
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (for logging/display)."""
        return {
            "trading": self.trading.dict(),
            "acp": {
                **self.acp.dict(exclude={"whitelisted_wallet_private_key"}),
                "whitelisted_wallet_private_key": "[REDACTED]" if self.acp.whitelisted_wallet_private_key else None,
            },
            "polymarket": {
                **self.polymarket.dict(exclude={"api_key", "secret", "passphrase"}),
                "api_key": "[REDACTED]" if self.polymarket.api_key else None,
                "secret": "[REDACTED]" if self.polymarket.secret else None,
                "passphrase": "[REDACTED]" if self.polymarket.passphrase else None,
            },
            "polysights": {
                **self.polysights.dict(exclude={"api_key"}),
                "api_key": "[REDACTED]" if self.polysights.api_key else None,
            },
            "database": {**self.database.dict()},
            "debug": self.debug,
        }


# Global config instance
config = Config()
