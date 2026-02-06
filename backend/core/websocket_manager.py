"""
Enhanced WebSocket Manager for Real-time Updates
Handles live price feeds, portfolio updates, and notifications
With throttling, batching, and performance optimizations
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta
import uuid
from collections import deque
import time

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Subscriptions by user_id -> set of symbols
        self.subscriptions: Dict[str, Set[str]] = {}
        # Price update tasks
        self.price_update_tasks: Dict[str, asyncio.Task] = {}
        # Portfolio update tasks
        self.portfolio_update_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance optimizations
        self.message_buffers: Dict[str, deque] = {}  # Buffer messages for batching
        self.last_send_time: Dict[str, float] = {}  # Track last send time per connection
        self.message_counts: Dict[str, int] = {}  # Track message count per second
        
        # Rate limiting (messages per second per connection)
        self.max_messages_per_second = 10
        self.batch_interval = 0.1  # Batch messages every 100ms
        
        # Order book subscriptions
        self.order_book_subscriptions: Dict[str, Set[str]] = {}  # user_id -> symbols
        self.trade_feed_subscriptions: Dict[str, Set[str]] = {}  # user_id -> symbols
        self.options_chain_subscriptions: Dict[str, Set[str]] = {}  # user_id -> symbols
        
        # Data caches for delta updates
        self.last_order_book: Dict[str, Dict] = {}  # symbol -> last order book state
        self.last_options_chain: Dict[str, Dict] = {}  # symbol -> last options chain state
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and initialize user data"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.subscriptions[user_id] = set()
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to live data feed",
            "timestamp": datetime.now().isoformat()
        }, user_id)
        
        # Start price update task for this user
        await self.start_user_updates(user_id)
    
    def disconnect(self, user_id: str):
        """Remove WebSocket connection and cleanup"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.subscriptions:
            del self.subscriptions[user_id]
        
        # Cancel update tasks
        if user_id in self.price_update_tasks:
            self.price_update_tasks[user_id].cancel()
            del self.price_update_tasks[user_id]
        
        if user_id in self.portfolio_update_tasks:
            self.portfolio_update_tasks[user_id].cancel()
            del self.portfolio_update_tasks[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: str, throttle: bool = True):
        """Send message to specific user with throttling and batching"""
        if user_id not in self.active_connections:
            return
        
        # Initialize buffers if needed
        if user_id not in self.message_buffers:
            self.message_buffers[user_id] = deque(maxlen=100)
            self.last_send_time[user_id] = time.time()
            self.message_counts[user_id] = 0
        
        current_time = time.time()
        
        # Reset message count if 1 second has passed
        if current_time - self.last_send_time[user_id] >= 1.0:
            self.message_counts[user_id] = 0
            self.last_send_time[user_id] = current_time
        
        # Throttle if rate limit exceeded
        if throttle and self.message_counts[user_id] >= self.max_messages_per_second:
            # Add to buffer for batching
            self.message_buffers[user_id].append(message)
            return
        
        # Add to buffer
        self.message_buffers[user_id].append(message)
        self.message_counts[user_id] += 1
        
        # Send immediately or batch
        if len(self.message_buffers[user_id]) >= 5 or not throttle:
            await self._flush_buffer(user_id)
        else:
            # Schedule batch send
            asyncio.create_task(self._batch_send(user_id))
    
    async def _batch_send(self, user_id: str):
        """Send batched messages after interval"""
        await asyncio.sleep(self.batch_interval)
        await self._flush_buffer(user_id)
    
    async def _flush_buffer(self, user_id: str):
        """Flush message buffer for a user"""
        if user_id not in self.active_connections or user_id not in self.message_buffers:
            return
        
        if len(self.message_buffers[user_id]) == 0:
            return
        
        try:
            websocket = self.active_connections[user_id]
            messages = list(self.message_buffers[user_id])
            self.message_buffers[user_id].clear()
            
            # Send as batch if multiple messages
            if len(messages) > 1:
                await websocket.send_text(json.dumps({
                    "type": "batch_update",
                    "messages": messages,
                    "count": len(messages),
                    "timestamp": datetime.now().isoformat()
                }))
            else:
                await websocket.send_text(json.dumps(messages[0]))
                
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            # Remove broken connection
            self.disconnect(user_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected users"""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    async def subscribe_to_symbol(self, user_id: str, symbol: str):
        """Subscribe user to price updates for a symbol"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].add(symbol)
            logger.info(f"User {user_id} subscribed to {symbol}")
            
            # Send confirmation
            await self.send_personal_message({
                "type": "subscription_confirmed",
                "symbol": symbol,
                "message": f"Subscribed to {symbol} price updates",
                "timestamp": datetime.now().isoformat()
            }, user_id)
    
    async def unsubscribe_from_symbol(self, user_id: str, symbol: str):
        """Unsubscribe user from price updates for a symbol"""
        if user_id in self.subscriptions and symbol in self.subscriptions[user_id]:
            self.subscriptions[user_id].remove(symbol)
            logger.info(f"User {user_id} unsubscribed from {symbol}")
            
            # Send confirmation
            await self.send_personal_message({
                "type": "unsubscription_confirmed",
                "symbol": symbol,
                "message": f"Unsubscribed from {symbol} price updates",
                "timestamp": datetime.now().isoformat()
            }, user_id)
    
    async def start_user_updates(self, user_id: str):
        """Start price and portfolio update tasks for a user"""
        # Start price update task
        if user_id not in self.price_update_tasks:
            self.price_update_tasks[user_id] = asyncio.create_task(
                self.price_update_loop(user_id)
            )
        
        # Start portfolio update task
        if user_id not in self.portfolio_update_tasks:
            self.portfolio_update_tasks[user_id] = asyncio.create_task(
                self.portfolio_update_loop(user_id)
            )
    
    async def price_update_loop(self, user_id: str):
        """Continuously send price updates for subscribed symbols"""
        try:
            while user_id in self.active_connections:
                if user_id in self.subscriptions and self.subscriptions[user_id]:
                    # Get live prices for subscribed symbols
                    from core.data_service import data_service
                    
                    symbols = list(self.subscriptions[user_id])
                    quotes = await data_service.get_multiple_quotes(symbols)
                    
                    # Send price updates
                    for symbol, quote in quotes.items():
                        await self.send_personal_message({
                            "type": "price_update",
                            "symbol": symbol,
                            "data": quote,
                            "timestamp": datetime.now().isoformat()
                        }, user_id)
                
                # Wait before next update (every 5 seconds)
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info(f"Price update loop cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in price update loop for user {user_id}: {e}")
    
    async def portfolio_update_loop(self, user_id: str):
        """Continuously send portfolio updates"""
        try:
            while user_id in self.active_connections:
                # Get portfolio data (this would integrate with your portfolio service)
                portfolio_data = await self.get_user_portfolio_data(user_id)
                
                if portfolio_data:
                    await self.send_personal_message({
                        "type": "portfolio_update",
                        "data": portfolio_data,
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
                
                # Wait before next update (every 30 seconds)
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info(f"Portfolio update loop cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in portfolio update loop for user {user_id}: {e}")
    
    async def get_user_portfolio_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's portfolio data for real-time updates"""
        try:
            # This would integrate with your portfolio service
            # For now, return mock data
            return {
                "total_value": 150000.0,
                "total_pnl": 2500.0,
                "total_pnl_percent": 1.67,
                "positions": [
                    {
                        "symbol": "RELIANCE",
                        "quantity": 50,
                        "current_price": 2450.50,
                        "pnl": 1250.0,
                        "pnl_percent": 1.02
                    }
                ],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting portfolio data for user {user_id}: {e}")
            return None
    
    async def send_trading_signal(self, user_id: str, signal_data: Dict[str, Any]):
        """Send trading signal to specific user"""
        await self.send_personal_message({
            "type": "trading_signal",
            "data": signal_data,
            "timestamp": datetime.now().isoformat()
        }, user_id)
    
    async def send_alert(self, user_id: str, alert_data: Dict[str, Any]):
        """Send alert to specific user"""
        await self.send_personal_message({
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }, user_id)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_user_subscriptions(self, user_id: str) -> Set[str]:
        """Get user's subscribed symbols"""
        return self.subscriptions.get(user_id, set())
    
    async def handle_message(self, websocket: WebSocket, user_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe":
                symbol = message.get("symbol")
                if symbol:
                    await self.subscribe_to_symbol(user_id, symbol)
            
            elif message_type == "unsubscribe":
                symbol = message.get("symbol")
                if symbol:
                    await self.unsubscribe_from_symbol(user_id, symbol)
            
            elif message_type == "ping":
                await self.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, user_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()