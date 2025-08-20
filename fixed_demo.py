#!/usr/bin/env python3
"""
FIXED REAL POLYSIGHTS API DEMO - ACTUAL PARSED DATA
Pull and properly parse real data from all Polysights endpoints
"""
import asyncio
import aiohttp
import json
from datetime import datetime
import sys
import os

async def get_real_market_data():
    """Get and properly parse actual market data."""
    
    print("📊 FETCHING REAL MARKET DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/tables_api'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse the actual structure
                    if 'data' in data:
                        markets = data['data']
                        print(f"✅ Found {len(markets)} real markets")
                        
                        # Show actual market data with real fields
                        for i, market in enumerate(markets[:5]):
                            print(f"\n🏪 Market #{i+1}:")
                            # Print all available fields to see structure
                            for key, value in market.items():
                                if isinstance(value, (str, int, float)):
                                    print(f"   {key}: {value}")
                                elif isinstance(value, list) and len(value) > 0:
                                    print(f"   {key}: [{len(value)} items]")
                        
                        return markets
                    else:
                        print(f"❌ Raw response keys: {list(data.keys())}")
                        print(f"❌ Raw data sample: {str(data)[:200]}...")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def get_real_top_buys():
    """Get and properly parse top buys data."""
    
    print("\n💸 FETCHING REAL TOP BUYS DATA")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            url = 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/topbuysAPI'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"📋 Raw response keys: {list(data.keys())}")
                    
                    # Check each data key
                    all_buys = []
                    for key in ['data', 'data2', 'data3']:
                        if key in data and isinstance(data[key], list):
                            buys = data[key]
                            print(f"✅ {key}: {len(buys)} entries")
                            
                            # Show structure of first entry
                            if len(buys) > 0:
                                print(f"📋 Sample {key} structure:")
                                for field, value in buys[0].items():
                                    print(f"   {field}: {value}")
                                print()
                            
                            all_buys.extend(buys)
                    
                    return all_buys
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def get_real_orderbook():
    """Get and properly parse orderbook data."""
    
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
                        
                        # Show actual structure
                        if len(orderbook) > 0:
                            print(f"\n📋 Orderbook entry structure:")
                            for field, value in orderbook[0].items():
                                print(f"   {field}: {value}")
                        
                        return orderbook
                    else:
                        print(f"❌ No orderbook data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def get_real_insider_data():
    """Get and properly parse insider data."""
    
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
                        print(f"✅ Insider records: {len(insider_data)}")
                        
                        # Show actual structure
                        if len(insider_data) > 0:
                            print(f"\n📋 Insider data structure:")
                            for field, value in insider_data[0].items():
                                print(f"   {field}: {value}")
                        
                        return insider_data
                    else:
                        print(f"❌ No insider data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def get_real_leaderboard():
    """Get and properly parse leaderboard data."""
    
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
                        print(f"✅ Leaderboard type: {type(leaderboard)}")
                        
                        if isinstance(leaderboard, list) and len(leaderboard) > 0:
                            print(f"✅ Leaderboard entries: {len(leaderboard)}")
                            print(f"\n📋 Leaderboard structure:")
                            for field, value in leaderboard[0].items():
                                print(f"   {field}: {value}")
                        else:
                            print(f"📋 Leaderboard data: {leaderboard}")
                        
                        return leaderboard
                    else:
                        print(f"❌ No leaderboard data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def get_real_open_interest():
    """Get and properly parse open interest data."""
    
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
                        print(f"✅ OI data type: {type(oi_data)}")
                        print(f"✅ OI records: {len(oi_data) if isinstance(oi_data, list) else 'Not a list'}")
                        
                        if isinstance(oi_data, list) and len(oi_data) > 0:
                            print(f"\n📋 OI structure:")
                            for field, value in oi_data[0].items():
                                print(f"   {field}: {value}")
                        else:
                            print(f"📋 OI data sample: {str(oi_data)[:200]}...")
                        
                        return oi_data
                    else:
                        print(f"❌ No OI data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def get_real_charts():
    """Get and properly parse charts data."""
    
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
                        print(f"✅ Charts type: {type(charts)}")
                        print(f"✅ Chart records: {len(charts) if isinstance(charts, list) else 'Not a list'}")
                        
                        if isinstance(charts, list) and len(charts) > 0:
                            print(f"\n📋 Chart structure:")
                            for field, value in charts[0].items():
                                print(f"   {field}: {value}")
                        else:
                            print(f"📋 Charts data sample: {str(charts)[:200]}...")
                        
                        return charts
                    else:
                        print(f"❌ No charts data: {list(data.keys())}")
                        return []
                else:
                    print(f"❌ API Error: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

async def analyze_real_structure(markets, top_buys, orderbook, insider_data, leaderboard, oi_data, charts):
    """Analyze the actual data structures returned."""
    
    print("\n\n🔍 REAL DATA STRUCTURE ANALYSIS")
    print("=" * 50)
    
    print("\n📊 AVAILABLE DATA SUMMARY:")
    print(f"Markets: {len(markets) if markets else 0} records")
    print(f"Top Buys: {len(top_buys) if top_buys else 0} records")
    print(f"Orderbook: {len(orderbook) if orderbook else 0} records")
    print(f"Insider Data: {len(insider_data) if insider_data else 0} records")
    print(f"Leaderboard: {len(leaderboard) if isinstance(leaderboard, list) else 'Not list'}")
    print(f"Open Interest: {len(oi_data) if isinstance(oi_data, list) else 'Not list'}")
    print(f"Charts: {len(charts) if isinstance(charts, list) else 'Not list'}")
    
    # Show what we can actually work with
    if markets and len(markets) > 0:
        print(f"\n✅ MARKETS DATA IS USABLE")
        print(f"Sample market fields: {list(markets[0].keys())}")
    
    if top_buys and len(top_buys) > 0:
        print(f"\n✅ TOP BUYS DATA IS USABLE")
        print(f"Sample buy fields: {list(top_buys[0].keys())}")
    
    if orderbook and len(orderbook) > 0:
        print(f"\n✅ ORDERBOOK DATA IS USABLE")
        print(f"Sample orderbook fields: {list(orderbook[0].keys())}")
    
    if insider_data and len(insider_data) > 0:
        print(f"\n✅ INSIDER DATA IS USABLE")
        print(f"Sample insider fields: {list(insider_data[0].keys())}")

async def main():
    """Run the fixed real data demonstration."""
    
    print("🔧 FIXED POLYSIGHTS DATA DEMONSTRATION")
    print("=" * 60)
    print(f"⏰ {datetime.now().isoformat()}")
    print()
    
    # Fetch all real data and examine structures
    tasks = [
        get_real_market_data(),
        get_real_top_buys(),
        get_real_orderbook(),
        get_real_insider_data(),
        get_real_leaderboard(),
        get_real_open_interest(),
        get_real_charts()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    markets, top_buys, orderbook, insider_data, leaderboard, oi_data, charts = results
    
    # Analyze what we actually got
    await analyze_real_structure(markets, top_buys, orderbook, insider_data, leaderboard, oi_data, charts)
    
    print("\n" + "=" * 60)
    print("✅ STRUCTURE ANALYSIS COMPLETE")
    print("🔍 Now we know the actual data formats to work with")

if __name__ == "__main__":
    asyncio.run(main())
