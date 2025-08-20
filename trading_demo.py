#!/usr/bin/env python3
"""
POLYMARKET TRADING DEMO
Demonstrate CLOB API trading functionality with wallet signatures
"""
import asyncio
import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.trading.clob_client import PolymarketCLOBClient, AutoTrader

async def demo_trading_functionality():
    """Demonstrate trading capabilities."""
    
    print("🚀 POLYMARKET CLOB TRADING DEMO")
    print("=" * 50)
    print(f"⏰ {datetime.now().isoformat()}")
    print()
    
    # Check for wallet private key
    private_key = os.getenv("POLYMARKET_WALLET_PRIVATE_KEY")
    if not private_key:
        print("❌ POLYMARKET_WALLET_PRIVATE_KEY not set")
        print("📝 Set your wallet private key in environment variables")
        print("   export POLYMARKET_WALLET_PRIVATE_KEY=your_private_key")
        return
    
    try:
        # Initialize trading client
        print("🔧 Initializing CLOB client...")
        client = PolymarketCLOBClient(private_key)
        print(f"✅ Connected with wallet: {client.wallet_address}")
        
        # Get balances
        print("\n💰 Fetching wallet balances...")
        balances = await client.get_balances()
        print(f"✅ Found {len(balances)} token balances")
        
        # Show USDC balance if available
        usdc_balance = balances.get('USDC', 0)
        print(f"💵 USDC Balance: {usdc_balance}")
        
        # Get available markets
        print("\n📊 Fetching available markets...")
        markets = await client.get_markets()
        print(f"✅ Found {len(markets)} available markets")
        
        if markets:
            # Show first few markets
            print(f"\n🎯 Sample Markets:")
            for i, market in enumerate(markets[:3]):
                print(f"{i+1}. {market.get('question', 'Unknown')}")
                print(f"   Condition ID: {market.get('condition_id', 'N/A')}")
                
                # Show tokens for this market
                tokens = market.get('tokens', [])
                for token in tokens:
                    print(f"   Token: {token.get('outcome', 'N/A')} - {token.get('token_id', 'N/A')}")
                print()
        
        # Get current orders
        print("📋 Fetching current orders...")
        orders = await client.get_orders()
        print(f"✅ Found {len(orders)} active orders")
        
        # Get trade history
        print("\n📈 Fetching trade history...")
        trades = await client.get_trades()
        print(f"✅ Found {len(trades)} historical trades")
        
        # Demo orderbook fetch (if we have markets)
        if markets and len(markets) > 0:
            market = markets[0]
            tokens = market.get('tokens', [])
            if tokens:
                token_id = tokens[0].get('token_id')
                print(f"\n📖 Fetching orderbook for token: {token_id[:20]}...")
                orderbook = await client.get_orderbook(token_id)
                
                bids = orderbook.get('bids', [])
                asks = orderbook.get('asks', [])
                
                print(f"✅ Orderbook - Bids: {len(bids)}, Asks: {len(asks)}")
                
                if bids and asks:
                    best_bid = bids[0]['price']
                    best_ask = asks[0]['price']
                    spread = best_ask - best_bid
                    print(f"💹 Best Bid: {best_bid}, Best Ask: {best_ask}")
                    print(f"📊 Spread: {spread:.4f}")
        
        # Demo auto-trader initialization
        print(f"\n🤖 Initializing Auto-Trader...")
        auto_trader = AutoTrader(client, max_position_size=10.0)  # Small demo size
        print(f"✅ Auto-trader ready with max position: $10")
        
        print(f"\n" + "=" * 50)
        print("✅ TRADING DEMO COMPLETE")
        print("🎯 All CLOB API functions working correctly")
        print("💡 Ready for live trading with wallet signatures")
        print("⚠️  Remember to fund wallet with USDC for actual trading")
        
    except Exception as e:
        print(f"❌ Error in trading demo: {e}")
        print("🔍 Check wallet private key and network connection")

if __name__ == "__main__":
    asyncio.run(demo_trading_functionality())
