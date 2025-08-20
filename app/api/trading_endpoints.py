#!/usr/bin/env python3
"""
TRADING API ENDPOINTS
REST endpoints for manual and automated trading
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..trading.clob_client import PolymarketCLOBClient, AutoTrader
from ..core.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class PlaceOrderRequest(BaseModel):
    token_id: str
    price: float
    size: float
    side: str  # "BUY" or "SELL"
    order_type: str = "GTC"

class BuyRequest(BaseModel):
    token_id: str
    amount_usdc: float
    max_price: float = 0.99

class SellRequest(BaseModel):
    token_id: str
    size: float
    min_price: float = 0.01

class AutoTradeRequest(BaseModel):
    token_id: str
    strategy: str  # "momentum", "arbitrage", "stop_loss"
    parameters: Dict[str, Any] = {}

# Global trading client (initialized on startup)
trading_client: Optional[PolymarketCLOBClient] = None
auto_trader: Optional[AutoTrader] = None

async def get_trading_client():
    """Dependency to get trading client."""
    global trading_client
    if not trading_client:
        private_key = config.polymarket.wallet_private_key
        if not private_key:
            raise HTTPException(status_code=500, detail="Trading wallet not configured")
        trading_client = PolymarketCLOBClient(private_key)
    return trading_client

async def get_auto_trader():
    """Dependency to get auto trader."""
    global auto_trader
    if not auto_trader:
        client = await get_trading_client()
        auto_trader = AutoTrader(client)
    return auto_trader

@router.get("/health")
async def trading_health():
    """Trading service health check."""
    try:
        client = await get_trading_client()
        balances = await client.get_balances()
        return {
            "status": "healthy",
            "wallet_address": client.wallet_address,
            "balances_available": len(balances) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Trading health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/markets")
async def get_markets(client: PolymarketCLOBClient = Depends(get_trading_client)):
    """Get all available markets."""
    try:
        markets = await client.get_markets()
        return {"markets": markets, "count": len(markets)}
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balances")
async def get_balances(client: PolymarketCLOBClient = Depends(get_trading_client)):
    """Get wallet balances."""
    try:
        balances = await client.get_balances()
        return {"balances": balances, "wallet": client.wallet_address}
    except Exception as e:
        logger.error(f"Error fetching balances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders")
async def get_orders(client: PolymarketCLOBClient = Depends(get_trading_client)):
    """Get all orders."""
    try:
        orders = await client.get_orders()
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades")
async def get_trades(client: PolymarketCLOBClient = Depends(get_trading_client)):
    """Get trade history."""
    try:
        trades = await client.get_trades()
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orderbook/{token_id}")
async def get_orderbook(token_id: str, client: PolymarketCLOBClient = Depends(get_trading_client)):
    """Get orderbook for specific token."""
    try:
        orderbook = await client.get_orderbook(token_id)
        return {"token_id": token_id, "orderbook": orderbook}
    except Exception as e:
        logger.error(f"Error fetching orderbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/place")
async def place_order(
    request: PlaceOrderRequest,
    client: PolymarketCLOBClient = Depends(get_trading_client)
):
    """Place a new order."""
    try:
        result = await client.place_order(
            token_id=request.token_id,
            price=request.price,
            size=request.size,
            side=request.side,
            order_type=request.order_type
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to place order")
        
        return {"success": True, "order": result}
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    client: PolymarketCLOBClient = Depends(get_trading_client)
):
    """Cancel an order."""
    try:
        success = await client.cancel_order(order_id)
        return {"success": success, "order_id": order_id}
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/buy/yes")
async def buy_yes(
    request: BuyRequest,
    client: PolymarketCLOBClient = Depends(get_trading_client)
):
    """Buy YES tokens."""
    try:
        result = await client.buy_yes(
            token_id=request.token_id,
            amount_usdc=request.amount_usdc,
            max_price=request.max_price
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to buy YES tokens")
        
        return {"success": True, "order": result}
    except Exception as e:
        logger.error(f"Error buying YES: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/buy/no")
async def buy_no(
    request: BuyRequest,
    client: PolymarketCLOBClient = Depends(get_trading_client)
):
    """Buy NO tokens."""
    try:
        result = await client.buy_no(
            token_id=request.token_id,
            amount_usdc=request.amount_usdc,
            max_price=request.max_price
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to buy NO tokens")
        
        return {"success": True, "order": result}
    except Exception as e:
        logger.error(f"Error buying NO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sell")
async def sell_position(
    request: SellRequest,
    client: PolymarketCLOBClient = Depends(get_trading_client)
):
    """Sell position."""
    try:
        result = await client.sell_position(
            token_id=request.token_id,
            size=request.size,
            min_price=request.min_price
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to sell position")
        
        return {"success": True, "order": result}
    except Exception as e:
        logger.error(f"Error selling position: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-trade/start")
async def start_auto_trading(
    request: AutoTradeRequest,
    trader: AutoTrader = Depends(get_auto_trader)
):
    """Start automated trading strategy."""
    try:
        if request.strategy == "momentum":
            await trader.momentum_strategy(
                token_id=request.token_id,
                **request.parameters
            )
        elif request.strategy == "arbitrage":
            await trader.arbitrage_strategy(
                token_id=request.token_id,
                **request.parameters
            )
        elif request.strategy == "stop_loss":
            await trader.stop_loss_monitor(
                token_id=request.token_id,
                **request.parameters
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown strategy")
        
        return {
            "success": True,
            "strategy": request.strategy,
            "token_id": request.token_id,
            "parameters": request.parameters
        }
    except Exception as e:
        logger.error(f"Error starting auto-trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auto-trade/status")
async def get_auto_trade_status(trader: AutoTrader = Depends(get_auto_trader)):
    """Get status of automated trading strategies."""
    return {
        "active_strategies": trader.active_strategies,
        "max_position_size": trader.max_position_size
    }
