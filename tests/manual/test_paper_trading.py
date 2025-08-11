import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.polymarket.client import PolymarketClient
from app.wallet.erc6551 import ERC6551Wallet
from app.utils.config import load_config

async def test_paper_trading():
    print("Loading configuration...")
    config = load_config()
    
    print("Initializing components...")
    client = PolymarketClient(
        api_key=config.get("POLYMARKET_API_KEY"),
        paper_trading=True  # Enable paper trading mode
    )
    
    # Initialize wallet with test private key
    wallet = ERC6551Wallet(
        private_key=config.get("WALLET_PRIVATE_KEY"),
        chain_id=int(config.get("CHAIN_ID", 137))
    )
    
    print("Wallet address:", wallet.address)
    
    # Fetch a market to trade on
    print("Fetching available markets...")
    markets = await client.get_markets(limit=1)
    if not markets:
        print("No markets available for testing")
        return
    
    market = markets[0]
    market_id = market['id']
    
    print(f"\nSelected market: {market['question']}")
    print(f"Market ID: {market_id}")
    
    # Get market outcomes
    print("\nAvailable outcomes:")
    for idx, outcome in enumerate(market['outcomes']):
        print(f"  {idx+1}. {outcome['name']} (ID: {outcome['id']})")
    
    outcome_id = market['outcomes'][0]['id']  # First outcome
    outcome_name = market['outcomes'][0]['name']
    
    # Create a paper trade order
    print(f"\nPreparing paper trade for outcome: {outcome_name}")
    
    order_params = {
        "market_id": market_id,
        "outcome_id": outcome_id,
        "direction": "buy",
        "size": "10",  # Amount in USDC
        "price": "0.65",  # Price between 0 and 1
    }
    
    # Simulate signing the order
    print("Signing order...")
    signed_order = await wallet.sign_order(order_params)
    
    # Simulate submitting the order
    print("Submitting paper trade order...")
    result = await client.place_order(signed_order, paper=True)
    
    print("\nOrder result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("=== Polymarket Paper Trading Test ===")
    asyncio.run(test_paper_trading())
    print("\nTest completed.")
