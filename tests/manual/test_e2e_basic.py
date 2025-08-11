import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.polymarket.client import PolymarketClient
from app.wallet.erc6551 import ERC6551Wallet
from app.utils.config import load_config

async def test_e2e_basic():
    print("Loading configuration...")
    config = load_config()
    
    print("Initializing components...")
    client = PolymarketClient(
        api_key=config.get("POLYMARKET_API_KEY"),
        paper_trading=True
    )
    
    wallet = ERC6551Wallet(
        private_key=config.get("WALLET_PRIVATE_KEY"),
        chain_id=int(config.get("CHAIN_ID", 137))
    )
    
    print("Wallet address:", wallet.address)
    
    # Fetch available markets
    print("\nFetching markets...")
    markets = await client.get_markets(limit=3)
    print(f"Found {len(markets)} markets")
    
    if not markets:
        print("No markets found. Exiting test.")
        return
    
    # Select first market
    market = markets[0]
    print(f"\nSelected market: {market['question']}")
    
    # Get order book
    print(f"\nFetching order book for market {market['id']}...")
    order_book = await client.get_order_book(market['id'])
    print(f"Order book has {len(order_book['bids'])} bids and {len(order_book['asks'])} asks")
    
    if order_book['bids']:
        print(f"Best bid: {order_book['bids'][0]['price']}")
    if order_book['asks']:
        print(f"Best ask: {order_book['asks'][0]['price']}")
    
    # Place paper trade
    outcome = market['outcomes'][0]
    price = 0.65  # Example price point
    
    print(f"\nPlacing paper trade on outcome: {outcome['name']} at price {price}")
    
    order_params = {
        "market_id": market['id'],
        "outcome_id": outcome['id'],
        "direction": "buy",
        "size": "5",  # 5 USDC
        "price": str(price),
    }
    
    # Sign order
    print("Signing order...")
    signed_order = await wallet.sign_order(order_params)
    
    # Place order
    print("Submitting paper trade order...")
    result = await client.place_order(signed_order, paper=True)
    
    print("\nOrder result:")
    print(json.dumps(result, indent=2))
    
    # Try to get current positions
    print("\nFetching current positions...")
    try:
        positions = await client.get_positions(wallet.address)
        print(f"Current positions: {len(positions)}")
        if positions:
            print(json.dumps(positions[:1], indent=2))  # Show first position only
    except Exception as e:
        print(f"Error fetching positions: {str(e)}")
    
    print("\nBasic E2E test completed successfully")

if __name__ == "__main__":
    print("=== Polymarket Basic E2E Test ===")
    asyncio.run(test_e2e_basic())
    print("\nTest completed.")
