"""
Test script that works with the mock Polymarket API server.

This script demonstrates how to test the ACP Polymarket Trading Agent's
market data fetching and trade execution capabilities using the mock API.

Usage:
1. First start the mock server: python tests/manual/mock_polymarket_server.py
2. Then run this script: python tests/manual/test_with_mock.py
"""
import asyncio
import json
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mock_test")

# Import from the project (optional - can use a simple client instead)
try:
    from app.polymarket.client import PolymarketClient
    from app.wallet.erc6551 import SmartWallet
    USING_AGENT_CODE = True
    logger.info("Using agent's PolymarketClient implementation")
except ImportError:
    USING_AGENT_CODE = False
    logger.warning("Agent code not importable, using simplified client")


class SimpleMockClient:
    """Simple client for testing with the mock Polymarket API."""
    
    def __init__(self, base_url="http://localhost:8765"):
        """Initialize the client with the mock API URL."""
        self.base_url = base_url
        self.session = None
        logger.info(f"Initialized SimpleMockClient with base URL: {self.base_url}")
    
    async def __aenter__(self):
        """Set up the client session."""
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the client session."""
        if self.session:
            await self.session.close()
    
    async def health_check(self):
        """Check if the mock server is running."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.base_url}/health"
            logger.info(f"Checking mock server health at {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "ok"
                return False
        except Exception as e:
            logger.error(f"Mock server health check failed: {str(e)}")
            return False
    
    async def get_markets(self, limit=5):
        """Get available markets from the mock API."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.base_url}/markets"
            logger.info(f"Fetching markets from {url}")
            
            async with self.session.get(url, params={"limit": limit}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("markets", [])
                else:
                    logger.error(f"Error fetching markets: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Exception fetching markets: {str(e)}")
            return []
    
    async def get_market_info(self, market_id):
        """Get detailed information for a specific market."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.base_url}/markets/{market_id}"
            logger.info(f"Fetching market info from {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error fetching market info: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Exception fetching market info: {str(e)}")
            return {}
    
    async def get_order_book(self, market_id):
        """Get order book for a specific market."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.base_url}/markets/{market_id}/orderbook"
            logger.info(f"Fetching order book from {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Error fetching order book: {response.status}")
                    return {"bids": [], "asks": []}
        except Exception as e:
            logger.error(f"Exception fetching order book: {str(e)}")
            return {"bids": [], "asks": []}
    
    async def place_order(self, market_id, outcome_id, size, price, direction):
        """Place a mock order."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.base_url}/orders"
            logger.info(f"Placing order at {url}")
            
            order_data = {
                "market_id": market_id,
                "outcome_id": outcome_id,
                "size": str(size),
                "price": str(price),
                "direction": direction  # "buy" or "sell"
            }
            
            async with self.session.post(url, json=order_data) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Error placing order: {response.status}")
                    content = await response.text()
                    logger.error(f"Response: {content}")
                    return {"error": "Failed to place order", "status": "failed"}
        except Exception as e:
            logger.error(f"Exception placing order: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def get_positions(self, wallet_address):
        """Get positions for a wallet address."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        
        try:
            url = f"{self.base_url}/positions"
            logger.info(f"Fetching positions from {url}")
            
            async with self.session.get(url, params={"wallet_address": wallet_address}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("positions", [])
                else:
                    logger.error(f"Error fetching positions: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Exception fetching positions: {str(e)}")
            return []


async def test_market_data_fetch():
    """Test fetching market data from the mock server."""
    async with SimpleMockClient() as client:
        # Health check
        is_healthy = await client.health_check()
        if not is_healthy:
            logger.error("Mock server not running or not healthy. Start it with: python tests/manual/mock_polymarket_server.py")
            return
        
        # Fetch markets
        logger.info("\nFetching markets...")
        markets = await client.get_markets(limit=3)
        logger.info(f"Retrieved {len(markets)} markets")
        
        if not markets:
            logger.warning("No markets found")
            return
        
        # Print market details
        for idx, market in enumerate(markets):
            logger.info(f"\nMarket {idx+1}:")
            logger.info(f"  ID: {market.get('id', 'unknown')}")
            logger.info(f"  Question: {market.get('question', 'unknown')}")
            logger.info(f"  Volume: {market.get('volume', 'unknown')}")
            
            # For the first market, get more details and order book
            if idx == 0:
                market_id = market.get('id')
                if market_id:
                    # Get detailed market info
                    logger.info(f"\nGetting details for market {market_id}...")
                    market_info = await client.get_market_info(market_id)
                    if market_info:
                        logger.info(f"  Status: {market_info.get('status', 'unknown')}")
                        logger.info(f"  Outcomes:")
                        for outcome in market_info.get('outcomes', []):
                            logger.info(f"    - {outcome.get('name')}: {outcome.get('price')}")
                    
                    # Get order book
                    logger.info(f"\nGetting order book for market {market_id}...")
                    order_book = await client.get_order_book(market_id)
                    logger.info(f"  Bids: {len(order_book.get('bids', []))}")
                    logger.info(f"  Asks: {len(order_book.get('asks', []))}")
                    
                    if order_book.get('bids'):
                        logger.info(f"  Top 3 bids:")
                        for i, bid in enumerate(order_book.get('bids')[:3]):
                            logger.info(f"    {i+1}. Price: {bid.get('price')}, Size: {bid.get('size')}")
                    
                    if order_book.get('asks'):
                        logger.info(f"  Top 3 asks:")
                        for i, ask in enumerate(order_book.get('asks')[:3]):
                            logger.info(f"    {i+1}. Price: {ask.get('price')}, Size: {ask.get('size')}")


async def test_trade_execution():
    """Test trade execution functionality with the mock server."""
    async with SimpleMockClient() as client:
        # Health check
        is_healthy = await client.health_check()
        if not is_healthy:
            logger.error("Mock server not running or not healthy. Start it with: python tests/manual/mock_polymarket_server.py")
            return
        
        # Get markets
        markets = await client.get_markets(limit=1)
        if not markets:
            logger.warning("No markets found")
            return
        
        # Get the first market for testing
        market = markets[0]
        market_id = market.get('id')
        
        # Get market details to get outcomes
        market_info = await client.get_market_info(market_id)
        if not market_info or not market_info.get('outcomes'):
            logger.warning("No market outcomes found")
            return
        
        # Get the YES outcome
        yes_outcome = next((o for o in market_info.get('outcomes', []) if o.get('id') == 'YES'), None)
        if not yes_outcome:
            logger.warning("YES outcome not found")
            return
        
        outcome_id = yes_outcome.get('id')
        current_price = float(yes_outcome.get('price', 0.5))
        
        # Calculate a reasonable bid price (slightly below market)
        bid_price = round(max(0.01, current_price - 0.02), 2)
        
        # Place a test buy order
        logger.info(f"\nPlacing test BUY order for {market_id}, outcome {outcome_id}:")
        logger.info(f"  Price: {bid_price}, Size: 100")
        
        order_result = await client.place_order(
            market_id=market_id,
            outcome_id=outcome_id,
            size=100,
            price=bid_price,
            direction="buy"
        )
        
        logger.info(f"Order result: {json.dumps(order_result, indent=2)}")
        
        # If the order was placed successfully, check wallet positions
        if order_result.get('status') == 'filled':
            logger.info("\nChecking mock wallet positions:")
            positions = await client.get_positions("0xMockWalletAddress")
            
            logger.info(f"Retrieved {len(positions)} positions:")
            for pos in positions:
                logger.info(f"  Market: {pos.get('market_id')}")
                logger.info(f"  Outcome: {pos.get('outcome_id')}")
                logger.info(f"  Size: {pos.get('size')}")
                logger.info(f"  Avg Price: {pos.get('avg_price')}")
                logger.info(f"  PnL: {pos.get('pnl')}")


async def run_all_tests():
    """Run all tests in sequence."""
    logger.info("===== Testing Market Data Fetching =====")
    await test_market_data_fetch()
    
    logger.info("\n\n===== Testing Trade Execution =====")
    await test_trade_execution()


if __name__ == "__main__":
    start_time = datetime.now()
    print(f"=== ACP Polymarket Trading Agent Mock Tests - Started at {start_time.isoformat()} ===")
    
    # Run all tests
    asyncio.run(run_all_tests())
    
    end_time = datetime.now()
    print(f"\nTests completed in {(end_time - start_time).total_seconds():.2f} seconds.")
