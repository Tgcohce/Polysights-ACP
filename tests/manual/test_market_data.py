import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.polymarket.client import PolymarketClient
from app.utils.config import load_config

async def test_market_data():
    print("Loading configuration...")
    config = load_config()
    
    print(f"Initializing Polymarket client with API key: {config.get('POLYMARKET_API_KEY', 'NOT_FOUND')[:5]}...")
    client = PolymarketClient(api_key=config.get("POLYMARKET_API_KEY"))
    
    print("Fetching available markets...")
    markets = await client.get_markets(limit=5)  # Limit to 5 markets for testing
    
    print(f"\nRetrieved {len(markets)} markets:")
    for idx, market in enumerate(markets):
        print(f"\nMarket {idx+1}:")
        print(f"  ID: {market['id']}")
        print(f"  Question: {market['question']}")
        print(f"  Volume: {market.get('volume', 'N/A')}")
        print(f"  Outcomes: {[o['name'] for o in market.get('outcomes', [])]}")
        
        # Get order book for first market only
        if idx == 0:
            market_id = market['id']
            print(f"\nFetching order book for {market_id}...")
            order_book = await client.get_order_book(market_id)
            print(f"  Bids: {len(order_book['bids'])}")
            print(f"  Asks: {len(order_book['asks'])}")
            
            if order_book['bids']:
                print(f"  Best bid: {order_book['bids'][0]['price']}")
            if order_book['asks']:
                print(f"  Best ask: {order_book['asks'][0]['price']}")

if __name__ == "__main__":
    print("=== Polymarket Market Data Test ===")
    asyncio.run(test_market_data())
    print("\nTest completed.")
