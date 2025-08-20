#!/usr/bin/env python3
"""
POLYMARKET CLOB TRADING CLIENT
Direct trading using wallet signatures - no KYC required
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
from datetime import datetime

from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from py_clob_client.order_builder.constants import BUY, SELL
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

class PolymarketCLOBClient:
    """Direct CLOB trading client using wallet signatures."""
    
    def __init__(self, private_key: str, chain_id: int = POLYGON):
        """Initialize CLOB client with private key for signing."""
        self.private_key = private_key
        self.chain_id = chain_id
        
        # Initialize account from private key
        self.account = Account.from_key(private_key)
        self.wallet_address = self.account.address
        
        # Initialize CLOB client
        self.client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=chain_id
        )
        
        logger.info(f"Initialized CLOB client for wallet: {self.wallet_address}")
    
    async def get_markets(self) -> List[Dict]:
        """Get all available markets."""
        try:
            markets = self.client.get_markets()
            logger.info(f"Retrieved {len(markets)} markets")
            return markets
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    async def get_market(self, condition_id: str) -> Optional[Dict]:
        """Get specific market by condition ID."""
        try:
            market = self.client.get_market(condition_id)
            return market
        except Exception as e:
            logger.error(f"Error fetching market {condition_id}: {e}")
            return None
    
    async def get_orderbook(self, token_id: str) -> Dict:
        """Get orderbook for specific token."""
        try:
            orderbook = self.client.get_order_book(token_id)
            return orderbook
        except Exception as e:
            logger.error(f"Error fetching orderbook for {token_id}: {e}")
            return {}
    
    async def get_balances(self) -> Dict:
        """Get wallet balances."""
        try:
            balances = self.client.get_balances()
            return balances
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
            return {}
    
    async def place_order(
        self,
        token_id: str,
        price: float,
        size: float,
        side: str,  # BUY or SELL
        order_type: str = "GTC"  # Good Till Cancelled
    ) -> Optional[Dict]:
        """Place a new order."""
        try:
            # Build order
            order = self.client.create_order(
                token_id=token_id,
                price=price,
                size=size,
                side=side,
                order_type=order_type
            )
            
            # Submit order
            result = self.client.post_order(order)
            
            logger.info(f"Order placed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        try:
            result = self.client.cancel_order(order_id)
            logger.info(f"Order {order_id} cancelled: {result}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_orders(self) -> List[Dict]:
        """Get all orders for this wallet."""
        try:
            orders = self.client.get_orders()
            return orders
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    async def get_trades(self) -> List[Dict]:
        """Get trade history for this wallet."""
        try:
            trades = self.client.get_trades()
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    async def buy_yes(self, token_id: str, amount_usdc: float, max_price: float = 0.99) -> Optional[Dict]:
        """Buy YES tokens with USDC amount limit."""
        try:
            # Calculate size based on price
            current_price = await self._get_current_price(token_id, "yes")
            if not current_price:
                logger.error("Could not get current price")
                return None
            
            # Use current price or max price, whichever is lower
            price = min(current_price * 1.01, max_price)  # 1% slippage
            size = amount_usdc / price
            
            return await self.place_order(token_id, price, size, BUY)
            
        except Exception as e:
            logger.error(f"Error buying YES tokens: {e}")
            return None
    
    async def buy_no(self, token_id: str, amount_usdc: float, max_price: float = 0.99) -> Optional[Dict]:
        """Buy NO tokens with USDC amount limit."""
        try:
            # Get NO token ID (usually the paired token)
            market = await self.get_market_by_token(token_id)
            if not market:
                return None
            
            # Find NO token ID
            no_token_id = None
            for token in market.get('tokens', []):
                if token.get('outcome') == 'No':
                    no_token_id = token.get('token_id')
                    break
            
            if not no_token_id:
                logger.error("Could not find NO token ID")
                return None
            
            current_price = await self._get_current_price(no_token_id, "no")
            if not current_price:
                return None
            
            price = min(current_price * 1.01, max_price)
            size = amount_usdc / price
            
            return await self.place_order(no_token_id, price, size, BUY)
            
        except Exception as e:
            logger.error(f"Error buying NO tokens: {e}")
            return None
    
    async def sell_position(self, token_id: str, size: float, min_price: float = 0.01) -> Optional[Dict]:
        """Sell existing position."""
        try:
            current_price = await self._get_current_price(token_id)
            if not current_price:
                return None
            
            # Sell at current price minus small slippage
            price = max(current_price * 0.99, min_price)
            
            return await self.place_order(token_id, price, size, SELL)
            
        except Exception as e:
            logger.error(f"Error selling position: {e}")
            return None
    
    async def _get_current_price(self, token_id: str, side: str = "yes") -> Optional[float]:
        """Get current market price for token."""
        try:
            orderbook = await self.get_orderbook(token_id)
            
            if side.lower() == "yes":
                # For buying YES, look at asks (what sellers want)
                asks = orderbook.get('asks', [])
                if asks:
                    return float(asks[0]['price'])
            else:
                # For buying NO, look at bids (what buyers offer)
                bids = orderbook.get('bids', [])
                if bids:
                    return float(bids[0]['price'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    async def get_market_by_token(self, token_id: str) -> Optional[Dict]:
        """Find market containing this token."""
        try:
            markets = await self.get_markets()
            for market in markets:
                for token in market.get('tokens', []):
                    if token.get('token_id') == token_id:
                        return market
            return None
        except Exception as e:
            logger.error(f"Error finding market for token {token_id}: {e}")
            return None

class AutoTrader:
    """Automated trading strategies."""
    
    def __init__(self, clob_client: PolymarketCLOBClient, max_position_size: float = 100.0):
        self.client = clob_client
        self.max_position_size = max_position_size
        self.active_strategies = {}
        
    async def momentum_strategy(
        self,
        token_id: str,
        price_threshold: float = 0.05,  # 5% price move
        position_size: float = 50.0
    ):
        """Simple momentum trading strategy."""
        try:
            # Get recent price history
            orderbook = await self.client.get_orderbook(token_id)
            current_price = await self.client._get_current_price(token_id)
            
            if not current_price:
                return
            
            # Check if price moved significantly
            # This is simplified - in practice you'd track price history
            if current_price > 0.7:  # Strong YES momentum
                logger.info(f"Strong YES momentum detected at {current_price}")
                await self.client.buy_yes(token_id, position_size, max_price=0.95)
                
            elif current_price < 0.3:  # Strong NO momentum  
                logger.info(f"Strong NO momentum detected at {current_price}")
                await self.client.buy_no(token_id, position_size, max_price=0.95)
                
        except Exception as e:
            logger.error(f"Error in momentum strategy: {e}")
    
    async def arbitrage_strategy(self, token_id: str, min_spread: float = 0.02):
        """Look for arbitrage opportunities."""
        try:
            orderbook = await self.client.get_orderbook(token_id)
            
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return
            
            best_bid = float(bids[0]['price'])
            best_ask = float(asks[0]['price'])
            spread = best_ask - best_bid
            
            if spread > min_spread:
                logger.info(f"Arbitrage opportunity: spread {spread:.4f}")
                # Place orders to capture spread
                # This is simplified - real arbitrage needs more sophisticated logic
                
        except Exception as e:
            logger.error(f"Error in arbitrage strategy: {e}")
    
    async def stop_loss_monitor(self, token_id: str, stop_loss_pct: float = 0.10):
        """Monitor positions for stop-loss triggers."""
        try:
            balances = await self.client.get_balances()
            current_price = await self.client._get_current_price(token_id)
            
            # Check if we have position in this token
            token_balance = balances.get(token_id, 0)
            if token_balance > 0 and current_price:
                # Simplified stop-loss logic
                # In practice, you'd track entry price and calculate P&L
                if current_price < 0.2:  # Emergency exit
                    logger.warning(f"Stop-loss triggered for {token_id}")
                    await self.client.sell_position(token_id, token_balance)
                    
        except Exception as e:
            logger.error(f"Error in stop-loss monitor: {e}")
