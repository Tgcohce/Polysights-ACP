#!/usr/bin/env python3
"""
REAL POLYSIGHTS API DEMO - ACTUAL LIVE DATA
Pull and analyze real data from all Polysights endpoints
"""
import asyncio
import aiohttp
import json
from datetime import datetime
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def get_real_market_data():
    """Get actual market data from Polysights Tables API."""
    
    print("📊 FETCHING REAL MARKET DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/tables_api'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and isinstance(data['data'], list):
                        markets = data['data']
                        print(f"✅ Found {len(markets)} real markets")
                        
                        # Show top 5 real markets
                        for i, market in enumerate(markets[:5]):
                            print(f"\n🏪 Market #{i+1}:")
                            print(f"   Question: {market.get('question', 'N/A')}")
                            print(f"   Volume: ${market.get('volume', 0):,.0f}")
                            print(f"   Liquidity: ${market.get('liquidity', 0):,.0f}")
                            print(f"   End Date: {market.get('endDate', 'N/A')}")
                            print(f"   Category: {market.get('category', 'N/A')}")
                        
                        return markets
                    else:
                        print(f"❌ Unexpected data structure: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []

async def get_real_open_interest():
    """Get actual open interest data."""
    
    print("\n💰 FETCHING REAL OPEN INTEREST DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://oitsapi-655880131780.us-central1.run.app/'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'otisovis' in data:
                        oi_data = data['otisovis']
                        print(f"✅ Open Interest records: {len(oi_data)}")
                        
                        # Show recent OI data
                        for i, oi in enumerate(oi_data[:3]):
                            print(f"\n📈 OI Record #{i+1}:")
                            print(f"   Market: {oi.get('market', 'N/A')}")
                            print(f"   Open Interest: ${oi.get('openInterest', 0):,.0f}")
                            print(f"   Timestamp: {oi.get('timestamp', 'N/A')}")
                        
                        return oi_data
                    else:
                        print(f"❌ No otisovis data found: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching OI: {e}")
            return []

async def get_real_orderbook():
    """Get actual orderbook data."""
    
    print("\n📖 FETCHING REAL ORDERBOOK DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://orderbookapi1-655880131780.us-central1.run.app/'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'orderbook' in data:
                        orderbook = data['orderbook']
                        print(f"✅ Orderbook entries: {len(orderbook)}")
                        
                        # Show sample orderbook entries
                        for i, entry in enumerate(orderbook[:3]):
                            print(f"\n📋 Orderbook #{i+1}:")
                            print(f"   Condition ID: {entry.get('conditionId', 'N/A')[:20]}...")
                            print(f"   Market ID: {entry.get('id', 'N/A')}")
                            print(f"   Best Bid: {entry.get('bestBid', 'N/A')}")
                            print(f"   Best Ask: {entry.get('bestAsk', 'N/A')}")
                            print(f"   Spread: {entry.get('spread', 'N/A')}")
                        
                        return orderbook
                    else:
                        print(f"❌ No orderbook data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching orderbook: {e}")
            return []

async def get_real_top_buys():
    """Get actual top buys data."""
    
    print("\n💸 FETCHING REAL TOP BUYS DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/topbuysAPI'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check all possible data keys
                    top_buys = []
                    for key in ['data', 'data2', 'data3']:
                        if key in data and isinstance(data[key], list):
                            top_buys.extend(data[key])
                    
                    if top_buys:
                        print(f"✅ Top buys found: {len(top_buys)}")
                        
                        # Show top buys
                        for i, buy in enumerate(top_buys[:5]):
                            print(f"\n💰 Top Buy #{i+1}:")
                            print(f"   Amount: ${buy.get('amount', 0):,.0f}")
                            print(f"   Market: {buy.get('market', 'N/A')}")
                            print(f"   Trader: {buy.get('trader', 'N/A')}")
                            print(f"   Timestamp: {buy.get('timestamp', 'N/A')}")
                        
                        return top_buys
                    else:
                        print(f"❌ No top buys data in: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching top buys: {e}")
            return []

async def get_real_insider_data():
    """Get actual insider/wallet tracker data."""
    
    print("\n👤 FETCHING REAL INSIDER DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://wallettrackapi-655880131780.us-central1.run.app/'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data:
                        insider_data = data['data']
                        print(f"✅ Insider records: {len(insider_data) if isinstance(insider_data, list) else 'Processing...'}")
                        
                        if isinstance(insider_data, list):
                            # Show insider activity
                            for i, insider in enumerate(insider_data[:3]):
                                print(f"\n🕵️ Insider #{i+1}:")
                                print(f"   Wallet: {insider.get('wallet', 'N/A')}")
                                print(f"   Activity: {insider.get('activity', 'N/A')}")
                                print(f"   Volume: ${insider.get('volume', 0):,.0f}")
                                print(f"   Markets: {insider.get('markets', 'N/A')}")
                        
                        return insider_data
                    else:
                        print(f"❌ No insider data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching insider data: {e}")
            return []

async def get_real_leaderboard():
    """Get actual leaderboard data."""
    
    print("\n🏆 FETCHING REAL LEADERBOARD DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/leaderboard_api'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data:
                        leaderboard = data['data']
                        print(f"✅ Leaderboard entries: {len(leaderboard) if isinstance(leaderboard, list) else 'Processing...'}")
                        
                        if isinstance(leaderboard, list):
                            # Show top traders
                            for i, trader in enumerate(leaderboard[:5]):
                                print(f"\n🥇 Rank #{i+1}:")
                                print(f"   Trader: {trader.get('trader', 'N/A')}")
                                print(f"   PnL: ${trader.get('pnl', 0):,.0f}")
                                print(f"   Volume: ${trader.get('volume', 0):,.0f}")
                                print(f"   Win Rate: {trader.get('winRate', 0):.1%}")
                        
                        return leaderboard
                    else:
                        print(f"❌ No leaderboard data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return []

async def get_real_charts():
    """Get actual charts data."""
    
    print("\n📈 FETCHING REAL CHARTS DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/charts_api'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'charts' in data:
                        charts = data['charts']
                        print(f"✅ Chart data available: {len(charts) if isinstance(charts, list) else 'Processing...'}")
                        
                        if isinstance(charts, list):
                            # Show chart data
                            for i, chart in enumerate(charts[:3]):
                                print(f"\n📊 Chart #{i+1}:")
                                print(f"   Market: {chart.get('market', 'N/A')}")
                                print(f"   Price: ${chart.get('price', 0):.4f}")
                                print(f"   Volume: ${chart.get('volume', 0):,.0f}")
                                print(f"   Timestamp: {chart.get('timestamp', 'N/A')}")
                        
                        return charts
                    else:
                        print(f"❌ No charts data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching charts: {e}")
            return []

async def analyze_real_data(markets, oi_data, orderbook, top_buys, insider_data, leaderboard, charts):
    """Analyze the real data and provide insights."""
    
    print("\n\n🧠 REAL DATA ANALYSIS")
    print("=" * 50)
    
    if markets:
        print("\n🎯 TOP VOLUME MARKETS (REAL DATA)")
        print("-" * 35)
        
        # Sort by volume
        sorted_markets = sorted(markets, key=lambda x: x.get('volume', 0), reverse=True)
        
        for i, market in enumerate(sorted_markets[:5]):
            volume = market.get('volume', 0)
            liquidity = market.get('liquidity', 0)
            question = market.get('question', 'N/A')
            
            print(f"#{i+1} {question[:60]}...")
            print(f"    Volume: ${volume:,.0f}")
            print(f"    Liquidity: ${liquidity:,.0f}")
            print(f"    Category: {market.get('category', 'N/A')}")
            print()
    
    if top_buys:
        print("\n💰 LARGEST RECENT TRADES (REAL DATA)")
        print("-" * 40)
        
        # Sort by amount
        sorted_buys = sorted(top_buys, key=lambda x: x.get('amount', 0), reverse=True)
        
        for i, buy in enumerate(sorted_buys[:5]):
            amount = buy.get('amount', 0)
            market = buy.get('market', 'N/A')
            trader = buy.get('trader', 'N/A')
            
            print(f"💸 ${amount:,.0f} - {market}")
            print(f"    Trader: {trader}")
            print()
    
    if orderbook:
        print("\n📊 MARKET SPREADS (REAL DATA)")
        print("-" * 30)
        
        for i, entry in enumerate(orderbook[:5]):
            best_bid = entry.get('bestBid', 0)
            best_ask = entry.get('bestAsk', 0)
            spread = entry.get('spread', 0)
            
            if best_bid and best_ask:
                print(f"Market {entry.get('id', 'N/A')}")
                print(f"    Bid: ${best_bid:.4f}")
                print(f"    Ask: ${best_ask:.4f}")
                print(f"    Spread: {spread:.4f}")
                print()

async def main():
    """Run real data demonstration."""
    
    print("🚀 REAL POLYSIGHTS DATA DEMONSTRATION")
    print("=" * 60)
    print(f"⏰ {datetime.now().isoformat()}")
    print()
    
    # Fetch all real data concurrently
    print("🔄 FETCHING LIVE DATA FROM ALL APIS...")
    
    tasks = [
        get_real_market_data(),
        get_real_open_interest(),
        get_real_orderbook(),
        get_real_top_buys(),
        get_real_insider_data(),
        get_real_leaderboard(),
        get_real_charts()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    markets, oi_data, orderbook, top_buys, insider_data, leaderboard, charts = results
    
    # Analyze the real data
    await analyze_real_data(markets, oi_data, orderbook, top_buys, insider_data, leaderboard, charts)
    
    print("\n" + "=" * 60)
    print("✅ REAL DATA DEMONSTRATION COMPLETE")
    print("📊 All data shown above is LIVE from Polysights APIs")
    print("🎯 This is what the analytics agent will process and serve")

if __name__ == "__main__":
    asyncio.run(main())
