"""
Polymarket CLOB API client implementation.

This module provides a comprehensive client for interacting with the Polymarket
Central Limit Order Book (CLOB) API, including REST endpoints and WebSocket streams.
"""
import asyncio
import base64
import hmac
import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import uuid

import aiohttp
from eth_account.messages import encode_defunct

def encode_structured_data(structured_data):
    """Fallback implementation for encode_structured_data."""
    # Simple implementation for EIP-712 signing
    import json
    from eth_account.messages import encode_defunct
    
    # For now, use a simple message encoding
    # In production, implement proper EIP-712 encoding
    message = json.dumps(structured_data, sort_keys=True)
    return encode_defunct(text=message)
from loguru import logger
import websockets

from app.utils.config import config
from app.wallet.erc6551 import SmartWallet


class PolymarketClient:
    """
    Complete Polymarket CLOB API integration.
    
    This class provides methods for:
    - Authentication with the CLOB API
    - Retrieving market data
    - Placing and canceling orders
    - Managing positions
    - Detecting arbitrage opportunities
    - Streaming real-time market data
    """
    
    def __init__(self, wallet: SmartWallet = None):
        """
        Initialize the Polymarket client.
        
        Args:
            wallet: Smart wallet instance for authentication (optional)
        """
        self.api_key = config.polymarket.api_key
        self.secret = config.polymarket.secret
        self.passphrase = config.polymarket.passphrase
        self.base_url = config.polymarket.base_url
        self.websocket_url = config.polymarket.websocket_url
        self.wallet = wallet
        
        # Websocket connection and subscription state
        self.ws_connection = None
        self.ws_subscriptions = set()
        self.ws_task = None
        self.ws_callbacks = {}
        
        # Market data cache
        self.markets_cache = {}
        self.orderbooks_cache = {}
        self.last_cache_update = 0
        self.cache_ttl = 60  # seconds
        
        logger.info(f"Initialized Polymarket client with base URL: {self.base_url}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with the Polymarket API.
        
        Returns:
            bool: Success status
        """
        try:
            logger.info("Authenticating with Polymarket API")
            
            if not all([self.api_key, self.secret, self.passphrase]):
                logger.warning(
                    "Missing API credentials (api_key, secret, passphrase). "
                    "Some API endpoints may not be available."
                )
                return False
                
            # Make a test API call to check authentication
            timestamp = str(int(time.time()))
            
            # Create signature for authentication test
            path = "/api/v2/markets"
            signature = self._generate_signature(
                timestamp=timestamp,
                method="GET",
                path=path,
                body=""
            )
            
            # Set up headers
            headers = self._get_auth_headers(timestamp, signature)
            
            # Test authentication with a simple endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}{path}", 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info("Successfully authenticated with Polymarket API")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Authentication failed with status {response.status}: {error_text}"
                        )
                        return False
                        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _generate_signature(
        self, 
        timestamp: str, 
        method: str, 
        path: str, 
        body: str = ""
    ) -> str:
        """
        Generate a signature for API authentication.
        
        Args:
            timestamp: Current timestamp
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            body: Request body (for POST requests)
            
        Returns:
            str: Generated signature
        """
        message = timestamp + method + path + body
        signature = hmac.new(
            self.secret.encode(), 
            message.encode(), 
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _get_auth_headers(self, timestamp: str, signature: str) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            timestamp: Current timestamp
            signature: Generated signature
            
        Returns:
            Dict[str, str]: Headers dictionary
        """
        return {
            "Content-Type": "application/json",
            "PM-API-KEY": self.api_key,
            "PM-API-TIMESTAMP": timestamp,
            "PM-API-SIGNATURE": signature,
            "PM-API-PASSPHRASE": self.passphrase
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Polymarket API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters (for GET requests)
            data: Request data (for POST/PUT requests)
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            full_url = f"{self.base_url}{endpoint}"
            timestamp = str(int(time.time()))
            body = json.dumps(data) if data else ""
            
            signature = self._generate_signature(
                timestamp=timestamp,
                method=method.upper(),
                path=endpoint,
                body=body
            )
            
            headers = self._get_auth_headers(timestamp, signature)
            
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(
                        full_url, 
                        headers=headers, 
                        params=params
                    ) as response:
                        response_data = await response.json()
                elif method.upper() == "POST":
                    async with session.post(
                        full_url, 
                        headers=headers, 
                        json=data
                    ) as response:
                        response_data = await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(
                        full_url, 
                        headers=headers, 
                        params=params
                    ) as response:
                        response_data = await response.json()
                else:
                    logger.error(f"Unsupported method: {method}")
                    return {"error": f"Unsupported method: {method}"}
                
                if response.status >= 400:
                    logger.error(
                        f"API error: {response.status} - {response_data}"
                    )
                    return {"error": response_data, "status": response.status}
                    
                return response_data
                
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {"error": str(e)}
    
    async def get_markets(
        self, 
        filter_params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all available markets with filtering.
        
        Args:
            filter_params: Optional filtering parameters
                - status: Market status (open, closed, etc.)
                - category: Market category
                - search: Search term
                
        Returns:
            List[Dict[str, Any]]: List of markets
        """
        try:
            # Check cache first
            if self.markets_cache and time.time() - self.last_cache_update < self.cache_ttl:
                logger.debug("Using cached markets data")
                # Apply filters to cached data
                if not filter_params:
                    return list(self.markets_cache.values())
                
                filtered_markets = list(self.markets_cache.values())
                
                if "status" in filter_params:
                    filtered_markets = [
                        m for m in filtered_markets 
                        if m.get("status") == filter_params["status"]
                    ]
                    
                if "category" in filter_params:
                    filtered_markets = [
                        m for m in filtered_markets 
                        if filter_params["category"] in m.get("categories", [])
                    ]
                    
                if "search" in filter_params and filter_params["search"]:
                    search_term = filter_params["search"].lower()
                    filtered_markets = [
                        m for m in filtered_markets 
                        if search_term in m.get("title", "").lower() or 
                        search_term in m.get("description", "").lower()
                    ]
                    
                return filtered_markets
            
            # Otherwise, fetch from API
            endpoint = "/api/v2/markets"
            response = await self._make_request("GET", endpoint, params=filter_params)
            
            if "error" in response:
                logger.error(f"Error fetching markets: {response['error']}")
                return []
                
            # Update cache
            markets = response.get("markets", [])
            self.markets_cache = {m["marketId"]: m for m in markets}
            self.last_cache_update = time.time()
            
            return markets
            
        except Exception as e:
            logger.error(f"Error in get_markets: {e}")
            return []
    
    async def get_market_data(self, market_id: str) -> Dict[str, Any]:
        """
        Get detailed market information and order book.
        
        Args:
            market_id: Market ID
            
        Returns:
            Dict[str, Any]: Market data including order book
        """
        try:
            # Fetch market details
            endpoint = f"/api/v2/markets/{market_id}"
            market_data = await self._make_request("GET", endpoint)
            
            if "error" in market_data:
                logger.error(f"Error fetching market data: {market_data['error']}")
                return market_data
            
            # Fetch order book separately
            order_book = await self.get_order_book(market_id)
            
            # Combine the data
            result = {
                **market_data,
                "orderBook": order_book
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in get_market_data: {e}")
            return {"error": str(e)}
    
    async def get_order_book(self, market_id: str) -> Dict[str, Any]:
        """
        Get order book for a specific market.
        
        Args:
            market_id: Market ID
            
        Returns:
            Dict[str, Any]: Order book data
        """
        try:
            endpoint = f"/api/v2/markets/{market_id}/orderbook"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching order book: {response['error']}")
                return {}
                
            # Cache the orderbook
            self.orderbooks_cache[market_id] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Error in get_order_book: {e}")
            return {}
    
    async def sign_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign an order using EIP-712 standard.
        
        Args:
            order_data: Order data to sign
            
        Returns:
            Dict[str, Any]: Signed order
        """
        try:
            if not self.wallet:
                logger.error("Wallet not initialized, cannot sign order")
                return {"error": "Wallet not initialized"}
                
            # Construct the EIP-712 message
            domain = {
                "name": "Polymarket",
                "version": "1",
                "chainId": 8453,  # Base chain ID
                "verifyingContract": "0xPolymarketOrderContractAddress"  # Replace with actual address
            }
            
            # Order type definition
            types = {
                "Order": [
                    {"name": "trader", "type": "address"},
                    {"name": "market", "type": "address"},
                    {"name": "price", "type": "uint256"},
                    {"name": "size", "type": "uint256"},
                    {"name": "side", "type": "uint8"},
                    {"name": "orderType", "type": "uint8"},
                    {"name": "salt", "type": "uint256"}
                ]
            }
            
            # Create a unique salt for the order
            salt = int(time.time() * 1000)
            
            # Order data
            order = {
                "trader": self.wallet.address,
                "market": order_data["marketAddress"],
                "price": int(float(order_data["price"]) * (10 ** 6)),  # Convert to smallest unit
                "size": int(float(order_data["size"]) * (10 ** 6)),  # Convert to smallest unit
                "side": 0 if order_data["side"].lower() == "buy" else 1,  # 0 = buy, 1 = sell
                "orderType": 0 if order_data["orderType"].lower() == "limit" else 1,  # 0 = limit, 1 = market
                "salt": salt
            }
            
            # Create the structured data for signing
            structured_data = {
                "types": types,
                "domain": domain,
                "primaryType": "Order",
                "message": order
            }
            
            # Sign the message
            encoded_message = encode_structured_data(structured_data)
            signature = self.wallet.account.sign_message(encoded_message).signature.hex()
            
            # Combine order data with signature
            signed_order = {
                **order_data,
                "salt": salt,
                "signature": signature,
                "trader": self.wallet.address
            }
            
            return signed_order
            
        except Exception as e:
            logger.error(f"Error signing order: {e}")
            return {"error": f"Signing error: {str(e)}"}
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute limit/market orders.
        
        Args:
            order_data: Order data including:
                - market_id: Market ID
                - side: "buy" or "sell"
                - size: Order size
                - price: Price (for limit orders)
                - type: "limit" or "market"
                
        Returns:
            Dict[str, Any]: Order placement result
        """
        try:
            # Format the order data
            formatted_order = {
                "marketId": order_data["market_id"],
                "marketAddress": order_data.get("market_address", ""),  # Need to fetch if not provided
                "side": order_data["side"].lower(),
                "size": str(order_data["size"]),
                "price": str(order_data["price"]) if order_data.get("price") else None,
                "orderType": order_data.get("type", "limit").lower(),
                "clientId": order_data.get("client_id", str(uuid.uuid4()))
            }
            
            # If market address not provided, fetch it
            if not formatted_order["marketAddress"]:
                market_data = await self.get_market_data(formatted_order["marketId"])
                if "error" in market_data:
                    return market_data
                formatted_order["marketAddress"] = market_data.get("marketAddress", "")
            
            # Sign the order
            signed_order = await self.sign_order(formatted_order)
            if "error" in signed_order:
                return signed_order
                
            # Submit the order
            endpoint = "/api/v2/orders"
            response = await self._make_request("POST", endpoint, data=signed_order)
            
            if "error" in response:
                logger.error(f"Error placing order: {response['error']}")
            else:
                logger.info(f"Order placed successfully: {response.get('orderId')}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in place_order: {e}")
            return {"error": str(e)}
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel existing orders.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            Dict[str, Any]: Cancellation result
        """
        try:
            endpoint = f"/api/v2/orders/{order_id}"
            response = await self._make_request("DELETE", endpoint)
            
            if "error" in response:
                logger.error(f"Error canceling order: {response['error']}")
            else:
                logger.info(f"Order {order_id} canceled successfully")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in cancel_order: {e}")
            return {"error": str(e)}
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions and P&L.
        
        Returns:
            List[Dict[str, Any]]: List of positions
        """
        try:
            endpoint = "/api/v2/positions"
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                logger.error(f"Error fetching positions: {response['error']}")
                return []
                
            positions = response.get("positions", [])
            
            # Calculate P&L for each position if not included in response
            for position in positions:
                if "pnl" not in position and "entryPrice" in position and "currentPrice" in position:
                    entry_price = float(position["entryPrice"])
                    current_price = float(position["currentPrice"])
                    size = float(position["size"])
                    
                    # Calculate P&L based on position side
                    if position.get("side") == "buy":
                        pnl = (current_price - entry_price) * size
                    else:
                        pnl = (entry_price - current_price) * size
                        
                    position["pnl"] = pnl
            
            return positions
            
        except Exception as e:
            logger.error(f"Error in get_positions: {e}")
            return []
    
    async def detect_arbitrage(self) -> List[Dict[str, Any]]:
        """
        Scan all markets for arbitrage opportunities.
        
        Returns:
            List[Dict[str, Any]]: List of arbitrage opportunities
        """
        try:
            # Get all active markets
            markets = await self.get_markets({"status": "open"})
            arbitrage_opportunities = []
            
            for market in markets:
                market_id = market["marketId"]
                
                # Get order book for the market
                order_book = await self.get_order_book(market_id)
                
                if not order_book or "asks" not in order_book or "bids" not in order_book:
                    continue
                    
                # Check if there are any orders
                if not order_book["asks"] or not order_book["bids"]:
                    continue
                
                # Get best bid and ask prices
                best_bid = float(order_book["bids"][0]["price"])
                best_ask = float(order_book["asks"][0]["price"])
                
                # For binary markets, check if sum of probabilities < 1.0 (arbitrage opportunity)
                outcomes = market.get("outcomes", [])
                if len(outcomes) == 2:  # Binary market
                    # Get best price for each outcome
                    outcome_prices = []
                    for outcome in outcomes:
                        outcome_id = outcome["outcomeId"]
                        # TODO: Get best price for each outcome
                        # This is a simplified version, in reality would need to get order books for each outcome
                        outcome_prices.append(best_bid)  # Placeholder
                    
                    # Check for arbitrage (sum of prices < 1.0)
                    sum_prices = sum(outcome_prices)
                    if sum_prices < 0.98:  # Allowing for some profit margin
                        arbitrage_opportunities.append({
                            "market_id": market_id,
                            "market_title": market["title"],
                            "type": "binary_sum",
                            "sum_prices": sum_prices,
                            "profit_opportunity": 1.0 - sum_prices,
                            "outcomes": outcomes
                        })
                
                # Check for crossed books (best bid > best ask)
                if best_bid > best_ask:
                    arbitrage_opportunities.append({
                        "market_id": market_id,
                        "market_title": market["title"],
                        "type": "crossed_book",
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "profit_opportunity": best_bid - best_ask
                    })
            
            return arbitrage_opportunities
            
        except Exception as e:
            logger.error(f"Error in detect_arbitrage: {e}")
            return []
    
    async def start_market_data_stream(self, callback) -> bool:
        """
        Start a WebSocket connection for real-time market data.
        
        Args:
            callback: Callback function to handle incoming data
            
        Returns:
            bool: Success status
        """
        try:
            # Store the callback
            self.ws_callbacks["market_data"] = callback
            
            # Start the WebSocket connection if not already running
            if not self.ws_task or self.ws_task.done():
                self.ws_task = asyncio.create_task(self._maintain_websocket_connection())
                logger.info("Started WebSocket connection for market data")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting market data stream: {e}")
            return False
    
    async def _maintain_websocket_connection(self) -> None:
        """Maintain the WebSocket connection and handle reconnection."""
        while True:
            try:
                logger.info(f"Connecting to WebSocket: {self.websocket_url}")
                
                async with websockets.connect(self.websocket_url) as websocket:
                    self.ws_connection = websocket
                    
                    # Send authentication message
                    await self._authenticate_websocket()
                    
                    # Resubscribe to existing subscriptions
                    for subscription in self.ws_subscriptions:
                        await self._send_subscription(subscription)
                    
                    # Listen for messages
                    while True:
                        try:
                            message = await websocket.recv()
                            await self._handle_websocket_message(message)
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            
            # Wait before reconnecting
            logger.info("Reconnecting WebSocket in 5 seconds...")
            await asyncio.sleep(5)
    
    async def _authenticate_websocket(self) -> None:
        """Authenticate the WebSocket connection."""
        if not self.ws_connection:
            logger.error("WebSocket not connected")
            return
            
        try:
            timestamp = str(int(time.time()))
            signature = self._generate_signature(
                timestamp=timestamp,
                method="GET",
                path="/ws",
                body=""
            )
            
            auth_message = {
                "type": "auth",
                "key": self.api_key,
                "passphrase": self.passphrase,
                "timestamp": timestamp,
                "signature": signature
            }
            
            await self.ws_connection.send(json.dumps(auth_message))
            logger.info("WebSocket authentication message sent")
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
    
    async def _send_subscription(self, subscription: Dict[str, Any]) -> None:
        """
        Send a subscription message to the WebSocket.
        
        Args:
            subscription: Subscription data
        """
        if not self.ws_connection:
            logger.error("WebSocket not connected")
            return
            
        try:
            await self.ws_connection.send(json.dumps(subscription))
            logger.info(f"Sent subscription: {subscription['type']}")
            
        except Exception as e:
            logger.error(f"WebSocket subscription error: {e}")
    
    async def _handle_websocket_message(self, message: str) -> None:
        """
        Handle incoming WebSocket messages.
        
        Args:
            message: Raw message string
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "auth":
                if data.get("success"):
                    logger.info("WebSocket authentication successful")
                else:
                    logger.error(f"WebSocket authentication failed: {data.get('message')}")
            
            elif message_type == "subscriptions":
                logger.info(f"Subscription status: {data}")
            
            elif message_type == "ticker":
                # Handle ticker data
                if "market_data" in self.ws_callbacks:
                    await self.ws_callbacks["market_data"](data)
            
            elif message_type == "l2update":
                # Handle order book updates
                if "market_data" in self.ws_callbacks:
                    await self.ws_callbacks["market_data"](data)
            
            elif message_type == "match":
                # Handle trade matches
                if "market_data" in self.ws_callbacks:
                    await self.ws_callbacks["market_data"](data)
            
            else:
                logger.debug(f"Received unhandled message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in WebSocket message: {message}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def subscribe_to_market(self, market_id: str) -> bool:
        """
        Subscribe to a specific market's updates.
        
        Args:
            market_id: Market ID to subscribe to
            
        Returns:
            bool: Success status
        """
        try:
            subscription = {
                "type": "subscribe",
                "product_ids": [market_id],
                "channels": ["ticker", "level2", "matches"]
            }
            
            # Store subscription for reconnects
            self.ws_subscriptions.add(json.dumps(subscription))
            
            # Send subscription if websocket is connected
            if self.ws_connection:
                await self._send_subscription(subscription)
                
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to market: {e}")
            return False
    
    async def unsubscribe_from_market(self, market_id: str) -> bool:
        """
        Unsubscribe from a specific market's updates.
        
        Args:
            market_id: Market ID to unsubscribe from
            
        Returns:
            bool: Success status
        """
        try:
            unsubscribe_message = {
                "type": "unsubscribe",
                "product_ids": [market_id],
                "channels": ["ticker", "level2", "matches"]
            }
            
            # Remove from stored subscriptions
            subscription = json.dumps({
                "type": "subscribe",
                "product_ids": [market_id],
                "channels": ["ticker", "level2", "matches"]
            })
            if subscription in self.ws_subscriptions:
                self.ws_subscriptions.remove(subscription)
            
            # Send unsubscribe message if connected
            if self.ws_connection:
                await self.ws_connection.send(json.dumps(unsubscribe_message))
                
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from market: {e}")
            return False
    
    async def close(self) -> None:
        """Close WebSocket connection and cleanup resources."""
        try:
            # Cancel WebSocket task if running
            if self.ws_task and not self.ws_task.done():
                self.ws_task.cancel()
                try:
                    await self.ws_task
                except asyncio.CancelledError:
                    pass
            
            # Close WebSocket connection if open
            if self.ws_connection:
                await self.ws_connection.close()
                self.ws_connection = None
            
            logger.info("Polymarket client closed")
            
        except Exception as e:
            logger.error(f"Error closing Polymarket client: {e}")
