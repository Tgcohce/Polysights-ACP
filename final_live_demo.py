#!/usr/bin/env python3
"""
FINAL LIVE POLYSIGHTS ANALYTICS DEMO
Real data parsing with actual market insights and sentiment analysis
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
import sys
import os

async def fetch_all_live_data():
    """Fetch all live data from Polysights APIs."""
    
    print("🔄 FETCHING LIVE DATA FROM ALL POLYSIGHTS APIS...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Markets Data
        print("📊 Markets API...")
        try:
            async with session.get('https://us-central1-static-smoke-449018-b1.cloudfunctions.net/tables_api') as response:
                markets_data = await response.json() if response.status == 200 else {}
                markets = markets_data.get('data', [])
                print(f"   ✅ {len(markets)} markets")
        except Exception as e:
            markets = []
            print(f"   ❌ Error: {e}")
        
        # Top Buys Data
        print("💸 Top Buys API...")
        try:
            async with session.get('https://us-central1-static-smoke-449018-b1.cloudfunctions.net/topbuysAPI') as response:
                buys_data = await response.json() if response.status == 200 else {}
                top_buys = []
                for key in ['data', 'data2', 'data3']:
                    if key in buys_data and isinstance(buys_data[key], list):
                        top_buys.extend(buys_data[key])
                print(f"   ✅ {len(top_buys)} recent trades")
        except Exception as e:
            top_buys = []
            print(f"   ❌ Error: {e}")
        
        # Orderbook Data
        print("📖 Orderbook API...")
        try:
            async with session.get('https://orderbookapi1-655880131780.us-central1.run.app/') as response:
                orderbook_data = await response.json() if response.status == 200 else {}
                orderbook = orderbook_data.get('orderbook', [])
                print(f"   ✅ {len(orderbook)} orderbook entries")
        except Exception as e:
            orderbook = []
            print(f"   ❌ Error: {e}")
        
        # Insider/Wallet Tracker Data
        print("👤 Insider Tracker API...")
        try:
            async with session.get('https://wallettrackapi-655880131780.us-central1.run.app/') as response:
                insider_data_raw = await response.json() if response.status == 200 else {}
                insider_data = insider_data_raw.get('data', [])
                print(f"   ✅ {len(insider_data)} insider records")
        except Exception as e:
            insider_data = []
            print(f"   ❌ Error: {e}")
        
        # Charts Data
        print("📈 Charts API...")
        try:
            async with session.get('https://us-central1-static-smoke-449018-b1.cloudfunctions.net/charts_api') as response:
                charts_data = await response.json() if response.status == 200 else {}
                charts = charts_data.get('charts', [])
                print(f"   ✅ {len(charts)} chart records")
        except Exception as e:
            charts = []
            print(f"   ❌ Error: {e}")
        
        # Open Interest Data
        print("💰 Open Interest API...")
        try:
            async with session.get('https://oitsapi-655880131780.us-central1.run.app/') as response:
                oi_data_raw = await response.json() if response.status == 200 else {}
                oi_data = oi_data_raw.get('otisovis', {})
                print(f"   ✅ OI data available")
        except Exception as e:
            oi_data = {}
            print(f"   ❌ Error: {e}")
        
        # Leaderboard Data
        print("🏆 Leaderboard API...")
        try:
            async with session.get('https://us-central1-static-smoke-449018-b1.cloudfunctions.net/leaderboard_api') as response:
                leaderboard_data = await response.json() if response.status == 200 else {}
                leaderboard = leaderboard_data.get('data', [])
                print(f"   ✅ Leaderboard data available")
        except Exception as e:
            leaderboard = []
            print(f"   ❌ Error: {e}")
    
    return {
        'markets': markets,
        'top_buys': top_buys,
        'orderbook': orderbook,
        'insider_data': insider_data,
        'charts': charts,
        'oi_data': oi_data,
        'leaderboard': leaderboard
    }

def analyze_top_trades(top_buys):
    """Analyze recent large trades for market sentiment."""
    
    print("\n💰 RECENT LARGE TRADES ANALYSIS")
    print("-" * 40)
    
    if not top_buys:
        print("❌ No trade data available")
        return
    
    # Parse trade amounts and outcomes
    trades_with_amounts = []
    for trade in top_buys:
        try:
            amount = float(trade.get('makerAmountFilled', 0))
            if amount > 0:
                trades_with_amounts.append({
                    'amount': amount,
                    'outcome': trade.get('outcome', 'Unknown'),
                    'question': trade.get('question', 'Unknown'),
                    'timestamp': trade.get('timestamp', 0)
                })
        except (ValueError, TypeError):
            continue
    
    if not trades_with_amounts:
        print("❌ No valid trade amounts found")
        return
    
    # Sort by amount
    trades_with_amounts.sort(key=lambda x: x['amount'], reverse=True)
    
    print(f"✅ Analyzed {len(trades_with_amounts)} trades with valid amounts")
    
    # Show top 5 trades
    print(f"\n🔥 TOP 5 LARGEST TRADES:")
    for i, trade in enumerate(trades_with_amounts[:5]):
        print(f"{i+1}. ${trade['amount']:,.2f} on '{trade['outcome']}'")
        print(f"   Market: {trade['question'][:60]}...")
        print()
    
    # Sentiment analysis based on Yes/No outcomes
    yes_volume = sum(t['amount'] for t in trades_with_amounts if 'yes' in t['outcome'].lower())
    no_volume = sum(t['amount'] for t in trades_with_amounts if 'no' in t['outcome'].lower())
    total_volume = yes_volume + no_volume
    
    if total_volume > 0:
        yes_pct = (yes_volume / total_volume) * 100
        no_pct = (no_volume / total_volume) * 100
        
        print(f"📊 MARKET SENTIMENT FROM TRADES:")
        print(f"   Bullish (Yes): {yes_pct:.1f}% (${yes_volume:,.0f})")
        print(f"   Bearish (No): {no_pct:.1f}% (${no_volume:,.0f})")
        
        if yes_pct > 60:
            print("   🟢 BULLISH SENTIMENT DETECTED")
        elif no_pct > 60:
            print("   🔴 BEARISH SENTIMENT DETECTED")
        else:
            print("   🟡 NEUTRAL SENTIMENT")

def analyze_insider_activity(insider_data):
    """Analyze insider/whale activity for market insights."""
    
    print("\n👤 INSIDER ACTIVITY ANALYSIS")
    print("-" * 40)
    
    if not insider_data:
        print("❌ No insider data available")
        return
    
    print(f"✅ Tracking {len(insider_data)} insider positions")
    
    # Analyze by market volume
    market_volumes = {}
    total_insider_volume = 0
    
    for insider in insider_data:
        try:
            volume = float(insider.get('user_volume_traded', 0))
            market = insider.get('question', 'Unknown')
            outcome = insider.get('outcome', 'Unknown')
            
            if volume > 0:
                total_insider_volume += volume
                if market not in market_volumes:
                    market_volumes[market] = {'total': 0, 'yes': 0, 'no': 0}
                
                market_volumes[market]['total'] += volume
                if 'yes' in outcome.lower():
                    market_volumes[market]['yes'] += volume
                elif 'no' in outcome.lower():
                    market_volumes[market]['no'] += volume
        except (ValueError, TypeError):
            continue
    
    if market_volumes:
        # Sort markets by insider volume
        sorted_markets = sorted(market_volumes.items(), key=lambda x: x[1]['total'], reverse=True)
        
        print(f"\n🎯 TOP MARKETS BY INSIDER VOLUME:")
        for i, (market, data) in enumerate(sorted_markets[:5]):
            print(f"{i+1}. {market[:50]}...")
            print(f"   Total Volume: ${data['total']:,.0f}")
            
            if data['total'] > 0:
                yes_pct = (data['yes'] / data['total']) * 100
                no_pct = (data['no'] / data['total']) * 100
                print(f"   Yes: {yes_pct:.1f}% | No: {no_pct:.1f}%")
            print()
        
        print(f"💼 Total Insider Volume: ${total_insider_volume:,.0f}")

def analyze_orderbook_spreads(orderbook):
    """Analyze orderbook data for market efficiency."""
    
    print("\n📖 ORDERBOOK SPREAD ANALYSIS")
    print("-" * 40)
    
    if not orderbook:
        print("❌ No orderbook data available")
        return
    
    spreads = []
    
    for entry in orderbook[:20]:  # Analyze top 20 markets
        try:
            yes_book = entry.get('yes_orderbook', {})
            no_book = entry.get('no_orderbook', {})
            
            # Get best bid/ask for Yes
            yes_bids = yes_book.get('bids', [])
            yes_asks = yes_book.get('asks', [])
            
            if yes_bids and yes_asks:
                best_bid = max(yes_bids, key=lambda x: x['price'])['price']
                best_ask = min(yes_asks, key=lambda x: x['price'])['price']
                spread = best_ask - best_bid
                
                if spread >= 0:
                    spreads.append({
                        'market_id': entry.get('id', 'Unknown'),
                        'spread': spread,
                        'best_bid': best_bid,
                        'best_ask': best_ask
                    })
        except (KeyError, ValueError, TypeError):
            continue
    
    if spreads:
        spreads.sort(key=lambda x: x['spread'])
        
        print(f"✅ Analyzed {len(spreads)} market spreads")
        
        avg_spread = sum(s['spread'] for s in spreads) / len(spreads)
        print(f"📊 Average Spread: {avg_spread:.4f}")
        
        print(f"\n🎯 TIGHTEST SPREADS (Most Efficient Markets):")
        for i, spread_data in enumerate(spreads[:5]):
            print(f"{i+1}. Market {spread_data['market_id']}")
            print(f"   Spread: {spread_data['spread']:.4f}")
            print(f"   Bid: {spread_data['best_bid']:.4f} | Ask: {spread_data['best_ask']:.4f}")
            print()
        
        # Market efficiency insights
        tight_spreads = [s for s in spreads if s['spread'] < 0.02]
        wide_spreads = [s for s in spreads if s['spread'] > 0.05]
        
        print(f"🟢 Efficient Markets (< 2% spread): {len(tight_spreads)}")
        print(f"🔴 Inefficient Markets (> 5% spread): {len(wide_spreads)}")

def analyze_market_opportunities(charts, orderbook):
    """Identify potential trading opportunities."""
    
    print("\n🎯 MARKET OPPORTUNITIES")
    print("-" * 40)
    
    opportunities = []
    
    if charts:
        print(f"✅ Analyzing {len(charts)} chart records for price trends")
        
        # Look for price volatility and volume
        for chart in charts[:10]:
            try:
                # Get recent prices
                yes_prices = [
                    chart.get('YesPrice1', 0),
                    chart.get('YesPrice2', 0),
                    chart.get('YesPrice3', 0),
                    chart.get('YesPrice4', 0),
                    chart.get('YesPrice5', 0)
                ]
                
                volumes = [
                    chart.get('volume24hrClob_1', 0),
                    chart.get('volume24hrClob_2', 0),
                    chart.get('volume24hrClob_3', 0),
                    chart.get('volume24hrClob_4', 0) or 0,
                    chart.get('volume24hrClob_5', 0)
                ]
                
                # Calculate price volatility
                valid_prices = [p for p in yes_prices if p > 0]
                valid_volumes = [v for v in volumes if v > 0]
                
                if len(valid_prices) >= 3:
                    price_range = max(valid_prices) - min(valid_prices)
                    avg_price = sum(valid_prices) / len(valid_prices)
                    volatility = price_range / avg_price if avg_price > 0 else 0
                    
                    total_volume = sum(valid_volumes)
                    
                    if volatility > 0.1 and total_volume > 1000:  # High volatility + volume
                        opportunities.append({
                            'token1': chart.get('token1', 'Unknown'),
                            'volatility': volatility,
                            'volume': total_volume,
                            'avg_price': avg_price,
                            'opportunity_score': volatility * (total_volume / 10000)
                        })
            except (ValueError, TypeError):
                continue
    
    if opportunities:
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        print(f"\n🚀 TOP OPPORTUNITIES (High Volatility + Volume):")
        for i, opp in enumerate(opportunities[:5]):
            print(f"{i+1}. Token: {opp['token1'][:20]}...")
            print(f"   Volatility: {opp['volatility']:.1%}")
            print(f"   24h Volume: ${opp['volume']:,.0f}")
            print(f"   Avg Price: ${opp['avg_price']:.4f}")
            print(f"   Opportunity Score: {opp['opportunity_score']:.2f}")
            print()
    else:
        print("📊 No high-volatility opportunities detected in current data")

async def main():
    """Run the complete live analytics demonstration."""
    
    print("🚀 POLYSIGHTS LIVE ANALYTICS DEMONSTRATION")
    print("=" * 70)
    print(f"⏰ {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Fetch all live data
    data = await fetch_all_live_data()
    
    print(f"\n📊 DATA SUMMARY:")
    print(f"Markets: {len(data['markets'])}")
    print(f"Recent Trades: {len(data['top_buys'])}")
    print(f"Orderbook Entries: {len(data['orderbook'])}")
    print(f"Insider Records: {len(data['insider_data'])}")
    print(f"Chart Records: {len(data['charts'])}")
    
    # Run analytics
    analyze_top_trades(data['top_buys'])
    analyze_insider_activity(data['insider_data'])
    analyze_orderbook_spreads(data['orderbook'])
    analyze_market_opportunities(data['charts'], data['orderbook'])
    
    print("\n" + "=" * 70)
    print("✅ LIVE ANALYTICS DEMONSTRATION COMPLETE")
    print("🎯 This showcases real-time market intelligence capabilities")
    print("📈 Ready for production deployment as analytics-only agent")

if __name__ == "__main__":
    asyncio.run(main())
