"""
Configuration management module for the ACP Polymarket Trading Agent.
"""
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

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


class Config:
    """Main configuration class for the application."""

    def __init__(self):
        self.trading = TradingConfig()
        self.acp = AcpConfig()
        self.polymarket = PolymarketConfig()
        self.polysights = PolysightsConfig()
        self.database = DatabaseConfig()
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

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
