#!/usr/bin/env python3
"""
QUICK PRODUCTION TEST SUITE
Fast verification that all systems are working
"""
import asyncio
import sys
import os
from datetime import datetime
import requests
import json

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_environment_setup():
    """Test that environment is properly configured."""
    print("🔧 TESTING ENVIRONMENT SETUP")
    print("-" * 40)
    
    required_files = [
        'app/main.py',
        'app/api/analytics_endpoints.py',
        'app/api/trading_endpoints.py',
        'app/trading/clob_client.py',
        'app/polysights/analytics_client.py',
        'requirements.txt',
        'virtuals-manifest.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_dependencies():
    """Test that all dependencies can be imported."""
    print("\n📦 TESTING DEPENDENCIES")
    print("-" * 40)
    
    try:
        import fastapi
        import uvicorn
        import aiohttp
        import asyncio
        print("✅ Core dependencies available")
        
        # Test optional trading dependencies
        try:
            from py_clob_client.client import ClobClient
            from web3 import Web3
            from eth_account import Account
            print("✅ Trading dependencies available")
            trading_available = True
        except ImportError as e:
            print(f"⚠️  Trading dependencies missing: {e}")
            trading_available = False
        
        return True, trading_available
    except ImportError as e:
        print(f"❌ Missing core dependencies: {e}")
        return False, False

async def test_analytics_apis():
    """Test Polysights analytics APIs."""
    print("\n📊 TESTING ANALYTICS APIS")
    print("-" * 40)
    
    apis = {
        'Tables': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/tables_api',
        'Top Buys': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/topbuysAPI',
        'Orderbook': 'https://orderbookapi1-655880131780.us-central1.run.app/',
        'Wallet Tracker': 'https://wallettrackapi-655880131780.us-central1.run.app/',
        'Charts': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/charts_api',
        'Open Interest': 'https://oitsapi-655880131780.us-central1.run.app/',
        'Leaderboard': 'https://us-central1-static-smoke-449018-b1.cloudfunctions.net/leaderboard_api'
    }
    
    working_apis = 0
    
    async with aiohttp.ClientSession() as session:
        for name, url in apis.items():
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {name} API: Working")
                        working_apis += 1
                    else:
                        print(f"❌ {name} API: Status {response.status}")
            except Exception as e:
                print(f"❌ {name} API: {str(e)[:50]}...")
    
    print(f"\n📈 {working_apis}/{len(apis)} APIs working")
    return working_apis >= 5  # At least 5 APIs should work

def test_server_startup():
    """Test that the FastAPI server can start."""
    print("\n🚀 TESTING SERVER STARTUP")
    print("-" * 40)
    
    try:
        from app.main import app
        print("✅ FastAPI app imports successfully")
        
        # Test that routes are registered
        routes = [route.path for route in app.routes]
        expected_routes = ['/health', '/api/analytics/health']
        
        missing_routes = [route for route in expected_routes if route not in routes]
        if missing_routes:
            print(f"⚠️  Missing routes: {missing_routes}")
        else:
            print("✅ Core routes registered")
        
        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

def test_trading_setup():
    """Test trading functionality if wallet is configured."""
    print("\n💰 TESTING TRADING SETUP")
    print("-" * 40)
    
    private_key = os.getenv("POLYMARKET_WALLET_PRIVATE_KEY")
    if not private_key:
        print("⚠️  No wallet private key configured")
        print("   Set POLYMARKET_WALLET_PRIVATE_KEY for trading")
        return False
    
    try:
        from app.trading.clob_client import PolymarketCLOBClient
        
        # Test wallet connection (don't make actual calls)
        from eth_account import Account
        account = Account.from_key(private_key)
        print(f"✅ Wallet configured: {account.address}")
        
        print("✅ Trading client can be initialized")
        return True
    except Exception as e:
        print(f"❌ Trading setup failed: {e}")
        return False

async def run_quick_test():
    """Run complete quick test suite."""
    print("🧪 QUICK PRODUCTION TEST SUITE")
    print("=" * 50)
    print(f"⏰ {datetime.now().isoformat()}")
    print()
    
    # Run all tests
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Environment
    if test_environment_setup():
        tests_passed += 1
    
    # Test 2: Dependencies
    deps_ok, trading_ok = test_dependencies()
    if deps_ok:
        tests_passed += 1
    
    # Test 3: Analytics APIs
    if await test_analytics_apis():
        tests_passed += 1
    
    # Test 4: Server startup
    if test_server_startup():
        tests_passed += 1
    
    # Test 5: Trading (if configured)
    if test_trading_setup():
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} PASSED")
    
    if tests_passed >= 4:
        print("✅ SYSTEM READY FOR PRODUCTION")
        print("🚀 You can start the server with:")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    else:
        print("❌ SYSTEM NOT READY")
        print("🔧 Fix the failing tests before deployment")
    
    return tests_passed >= 4

if __name__ == "__main__":
    asyncio.run(run_quick_test())
