{{ ... }}
class PolymarketConfig:
    api_key: str = os.getenv("POLYMARKET_API_KEY", "")
    secret: str = os.getenv("POLYMARKET_SECRET", "")
    passphrase: str = os.getenv("POLYMARKET_PASSPHRASE", "")
    wallet_private_key: str = os.getenv("POLYMARKET_WALLET_PRIVATE_KEY", "")
    base_url: str = os.getenv("POLYMARKET_BASE_URL", "https://clob.polymarket.com")
    websocket_url: str = os.getenv("POLYMARKET_WS_URL", "wss://ws-subscriptions.polymarket.com/ws/market")

{{ ... }}

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./polymarket_agent.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

# Virtuals G.A.M.E. Framework Configuration
GAME_API_KEY = os.getenv("GAME_API_KEY")
VIRTUALS_ACP_API_KEY = os.getenv("VIRTUALS_ACP_API_KEY")

# Polymarket Trading Configuration
POLYMARKET_WALLET_PRIVATE_KEY = os.getenv("POLYMARKET_WALLET_PRIVATE_KEY")
POLYMARKET_BASE_URL = os.getenv("POLYMARKET_BASE_URL", "https://clob.polymarket.com")
POLYMARKET_WS_URL = os.getenv("POLYMARKET_WS_URL", "wss://ws-subscriptions.polymarket.com/ws/market")

# Polysights Analytics API
POLYSIGHTS_API_KEY = os.getenv("POLYSIGHTS_API_KEY")
{{ ... }}
