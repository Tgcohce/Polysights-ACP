{{ ... }}
class PolymarketConfig:
    api_key: str = os.getenv("POLYMARKET_API_KEY", "")
    secret: str = os.getenv("POLYMARKET_SECRET", "")
    passphrase: str = os.getenv("POLYMARKET_PASSPHRASE", "")
    wallet_private_key: str = os.getenv("POLYMARKET_WALLET_PRIVATE_KEY", "")
    base_url: str = os.getenv("POLYMARKET_BASE_URL", "https://clob.polymarket.com")
    websocket_url: str = os.getenv("POLYMARKET_WS_URL", "wss://ws-subscriptions-clob.polymarket.com/ws/")
{{ ... }}
