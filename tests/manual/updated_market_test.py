"""
Updated market data test for Polymarket integration with correct API endpoints.
This test focuses only on fetching market data to validate basic connectivity.
"""
import asyncio
import json
import sys
import os
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("updated_market_test")

# Create minimal PolymarketClient for testing
class SimplePolymarketClient:
    """Minimal Polymarket client for testing market data retrieval."""
    
    def __init__(self, api_key=None):
        """Initialize the client with API key."""
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY", "")
        # Updated base URL based on Polymarket API documentation
        self.base_url = "https://clob-api.polymarket.com"
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
            # Updated API endpoint path
            url = f"{self.base_url}/markets"
            logger.info(f"Fetching markets from {url}")
            
            # First try without any parameters
            async with self.session.get(
                url, 
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    markets = data.get("markets", [])
                    if isinstance(markets, list):
                        return markets[:limit]
                    return []
                else:
                    logger.error(f"Error fetching markets: {response.status} - {await response.text()}")
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
            # Updated API endpoint path
            url = f"{self.base_url}/markets/{market_id}/orderbook"
            logger.info(f"Fetching order book from {url}")
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "bids": data.get("bids", []),
                        "asks": data.get("asks", [])
                    }
                else:
                    logger.error(f"Error fetching order book: {response.status} - {await response.text()}")
                    return {"bids": [], "asks": []}
        except Exception as e:
            logger.error(f"Exception fetching order book: {str(e)}")
            return {"bids": [], "asks": []}

    async def get_market_info(self, market_id):
        """Get detailed information for a specific market."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        
        try:
            # Updated API endpoint path
            url = f"{self.base_url}/markets/{market_id}"
            logger.info(f"Fetching market info from {url}")
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching market info: {response.status} - {await response.text()}")
                    return {}
        except Exception as e:
            logger.error(f"Exception fetching market info: {str(e)}")
            return {}


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
            market_id = market.get('id', 'unknown')
            logger.info(f"  ID: {market_id}")
            logger.info(f"  Title: {market.get('title', 'unknown')}")
            logger.info(f"  Question: {market.get('question', 'unknown')}")
            
            # Get detailed info for first market only
            if idx == 0 and market_id != 'unknown':
                logger.info(f"\nFetching detailed information for {market_id}...")
                market_info = await client.get_market_info(market_id)
                if market_info:
                    logger.info(f"  Volume: {market_info.get('volume', 'unknown')}")
                    logger.info(f"  Outcomes: {[o.get('name', 'unknown') for o in market_info.get('outcomes', [])]}")
                
                # Get order book for first market
                logger.info(f"\nFetching order book for {market_id}...")
                order_book = await client.get_order_book(market_id)
                logger.info(f"  Bids: {len(order_book['bids'])}")
                logger.info(f"  Asks: {len(order_book['asks'])}")
                
                if order_book['bids']:
                    logger.info(f"  Best bid: {order_book['bids'][0].get('price', 'unknown')}")
                if order_book['asks']:
                    logger.info(f"  Best ask: {order_book['asks'][0].get('price', 'unknown')}")


if __name__ == "__main__":
    start_time = datetime.now()
    print(f"=== Polymarket Updated Market Data Test - Started at {start_time.isoformat()} ===")
    asyncio.run(test_market_data())
    end_time = datetime.now()
    print(f"\nTest completed in {(end_time - start_time).total_seconds():.2f} seconds.")
