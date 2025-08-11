"""
Mock Polymarket API server for testing.

This script creates a simple FastAPI server that simulates the Polymarket API
for testing purposes. It provides mock responses for markets, order books, etc.
"""
import asyncio
import json
import random
import sys
import os
import uvicorn
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from fastapi import FastAPI, Query, HTTPException, Depends, Header, Request
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("FastAPI not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "fastapi", "uvicorn"])
    from fastapi import FastAPI, Query, HTTPException, Depends, Header, Request
    from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mock Polymarket API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Mock Data ----------

# Generate mock market IDs
MARKET_IDS = [
    "0x1234567890abcdef1234567890abcdef12345678",
    "0xabcdef1234567890abcdef1234567890abcdef12",
    "0x7890abcdef1234567890abcdef1234567890abcd"
]

# Generate mock markets
MOCK_MARKETS = [
    {
        "id": MARKET_IDS[0],
        "question": "Will Bitcoin exceed $100,000 by the end of 2025?",
        "description": "This market resolves to Yes if the price of Bitcoin exceeds $100,000 USD at any point before the end of 2025.",
        "volume": "1250000",
        "liquidity": "450000",
        "outcomes": [
            {"id": "YES", "name": "Yes", "price": "0.65"},
            {"id": "NO", "name": "No", "price": "0.35"}
        ],
        "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        "expires_at": (datetime.now() + timedelta(days=500)).isoformat(),
        "status": "open"
    },
    {
        "id": MARKET_IDS[1],
        "question": "Will Ethereum merge to PoS in 2025?",
        "description": "This market resolves to Yes if Ethereum completes its transition to Proof of Stake before the end of 2025.",
        "volume": "750000",
        "liquidity": "320000",
        "outcomes": [
            {"id": "YES", "name": "Yes", "price": "0.82"},
            {"id": "NO", "name": "No", "price": "0.18"}
        ],
        "created_at": (datetime.now() - timedelta(days=45)).isoformat(),
        "expires_at": (datetime.now() + timedelta(days=300)).isoformat(),
        "status": "open"
    },
    {
        "id": MARKET_IDS[2],
        "question": "Will the US have a recession in 2025?",
        "description": "This market resolves to Yes if the US economy experiences two consecutive quarters of negative GDP growth during 2025.",
        "volume": "980000",
        "liquidity": "410000",
        "outcomes": [
            {"id": "YES", "name": "Yes", "price": "0.43"},
            {"id": "NO", "name": "No", "price": "0.57"}
        ],
        "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
        "expires_at": (datetime.now() + timedelta(days=400)).isoformat(),
        "status": "open"
    }
]

# Generate mock order books
def generate_mock_orderbook(market_id: str):
    """Generate a mock order book for a given market ID."""
    # Find the market
    market = next((m for m in MOCK_MARKETS if m["id"] == market_id), None)
    if not market:
        return {"bids": [], "asks": []}
    
    # Get the current price
    yes_price = float(market["outcomes"][0]["price"])
    
    # Generate mock bids (below current price)
    bids = []
    for i in range(10):
        price = round(yes_price - (0.01 * (i + 1)), 2)
        if price <= 0:
            break
        size = random.randint(500, 5000)
        bids.append({
            "price": str(price),
            "size": str(size),
            "timestamp": datetime.now().isoformat()
        })
    
    # Generate mock asks (above current price)
    asks = []
    for i in range(10):
        price = round(yes_price + (0.01 * (i + 1)), 2)
        if price >= 1:
            break
        size = random.randint(500, 5000)
        asks.append({
            "price": str(price),
            "size": str(size),
            "timestamp": datetime.now().isoformat()
        })
    
    return {
        "bids": sorted(bids, key=lambda x: float(x["price"]), reverse=True),
        "asks": sorted(asks, key=lambda x: float(x["price"]))
    }

# Mock positions for wallet addresses
MOCK_POSITIONS = {}

# Mock orders
MOCK_ORDERS = {}

# ---------- API Routes ----------

@app.get("/markets")
async def get_markets(limit: int = Query(10, ge=1, le=100)):
    """Get available markets."""
    return {
        "markets": MOCK_MARKETS[:limit],
        "count": len(MOCK_MARKETS),
        "page": 1,
        "total_pages": 1
    }

@app.get("/markets/{market_id}")
async def get_market(market_id: str):
    """Get details for a specific market."""
    market = next((m for m in MOCK_MARKETS if m["id"] == market_id), None)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    return market

@app.get("/markets/{market_id}/orderbook")
async def get_orderbook(market_id: str):
    """Get order book for a specific market."""
    market = next((m for m in MOCK_MARKETS if m["id"] == market_id), None)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    return generate_mock_orderbook(market_id)

@app.get("/positions")
async def get_positions(wallet_address: str = Query(...)):
    """Get positions for a specific wallet address."""
    if wallet_address not in MOCK_POSITIONS:
        # Generate random positions for this wallet
        MOCK_POSITIONS[wallet_address] = []
        for market in random.sample(MOCK_MARKETS, random.randint(0, len(MOCK_MARKETS))):
            outcome = random.choice(market["outcomes"])
            MOCK_POSITIONS[wallet_address].append({
                "market_id": market["id"],
                "outcome_id": outcome["id"],
                "size": str(random.randint(100, 10000) / 100),
                "avg_price": str(round(float(outcome["price"]) * (0.9 + 0.2 * random.random()), 2)),
                "pnl": str(round(random.randint(-5000, 5000) / 100, 2)),
                "timestamp": datetime.now().isoformat()
            })
    
    return {
        "positions": MOCK_POSITIONS[wallet_address],
        "count": len(MOCK_POSITIONS[wallet_address])
    }

@app.post("/orders")
async def place_order(request: Request):
    """Place a new order."""
    try:
        body = await request.json()
        
        # Generate a random order ID
        order_id = f"order-{random.randint(100000, 999999)}"
        
        # Store the order
        MOCK_ORDERS[order_id] = {
            **body,
            "status": "filled",
            "filled_size": body.get("size", "0"),
            "filled_price": body.get("price", "0"),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "order_id": order_id,
            "status": "filled",
            "message": "Order successfully placed and filled"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid order: {str(e)}")

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get details for a specific order."""
    if order_id not in MOCK_ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return MOCK_ORDERS[order_id]

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("MOCK_API_PORT", "8765"))
    print(f"Starting Mock Polymarket API server on port {port}...")
    print(f"Server will be available at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)
