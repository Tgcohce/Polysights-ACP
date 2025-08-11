"""
Simple market data test for Polymarket integration.
This test focuses only on fetching market data to validate basic connectivity.
"""
import asyncio
import json
import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simple_market_test")

# Create minimal PolymarketClient for testing
class SimplePolymarketClient:
    """Minimal Polymarket client for testing market data retrieval."""
    
    def __init__(self, api_key=None, base_url="https://clob.polymarket.com"):
        """Initialize the client with API key and base URL."""
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY", "")
        self.base_url = base_url
        self.session = None
        logger.info(f"Initialized SimplePolymarketClient with base URL: {self.base_url}")
    
    async def __aenter__(self):
        """Set up the client session."""
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the client session."""
        if self.session:
            await self.session.close()
    
    async def get_markets(self, limit=5):
        """Get available markets from Polymarket."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        
        try:
            url = f"{self.base_url}/api/v1/markets"
            logger.info(f"Fetching markets from {url}")
            
            async with self.session.get(
                url, 
                headers=headers,
                params={"limit": limit}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("markets", [])
                else:
                    logger.error(f"Error fetching markets: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Exception fetching markets: {str(e)}")
            return []
    
    async def get_order_book(self, market_id):
        """Get order book for a specific market."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        
        try:
            url = f"{self.base_url}/api/v1/markets/{market_id}/orderbook"
            logger.info(f"Fetching order book from {url}")
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "bids": data.get("bids", []),
                        "asks": data.get("asks", [])
                    }
                else:
                    logger.error(f"Error fetching order book: {response.status}")
                    return {"bids": [], "asks": []}
        except Exception as e:
            logger.error(f"Exception fetching order book: {str(e)}")
            return {"bids": [], "asks": []}


async def test_market_data():
    """Run a simple test to fetch market data."""
    api_key = os.getenv("POLYMARKET_API_KEY", "")
    if not api_key:
        logger.warning("No POLYMARKET_API_KEY found in environment variables")
    
    async with SimplePolymarketClient(api_key=api_key) as client:
        logger.info("Fetching available markets...")
        markets = await client.get_markets(limit=3)
        
        logger.info(f"Retrieved {len(markets)} markets:")
        for idx, market in enumerate(markets):
            logger.info(f"\nMarket {idx+1}:")
            logger.info(f"  ID: {market.get('id', 'unknown')}")
            logger.info(f"  Title: {market.get('title', 'unknown')}")
            logger.info(f"  Question: {market.get('question', 'unknown')}")
            
            # Get order book for first market only
            if idx == 0 and market.get('id'):
                market_id = market['id']
                logger.info(f"\nFetching order book for {market_id}...")
                order_book = await client.get_order_book(market_id)
                logger.info(f"  Bids: {len(order_book['bids'])}")
                logger.info(f"  Asks: {len(order_book['asks'])}")
                
                if order_book['bids']:
                    logger.info(f"  Best bid: {order_book['bids'][0].get('price', 'unknown')}")
                if order_book['asks']:
                    logger.info(f"  Best ask: {order_book['asks'][0].get('price', 'unknown')}")


if __name__ == "__main__":
    print("=== Polymarket Simple Market Data Test ===")
    asyncio.run(test_market_data())
    print("\nTest completed.")
