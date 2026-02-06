"""
Real-Time WebSocket Broadcaster for Nifty50
Broadcasts live market data to connected clients
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from services.realtime_data_service import realtime_service

logger = logging.getLogger(__name__)

class RealTimeWebSocketBroadcaster:
    def __init__(self):
        self.active_connections: Set[any] = set()
        self.broadcast_interval = 5  # 5 seconds
        self.is_running = False
        self.broadcast_task = None
        
        # All 66 Nifty50 symbols to broadcast
        self.nifty50_symbols = [
            # Core Nifty50 stocks (50)
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "HDFC", "ITC", "BHARTIARTL",
            "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID",
            "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA", "EICHERMOT",
            "SHREECEM", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "COALINDIA", "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP",
            "ADANIPORTS", "BPCL", "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", "ADANIENT", "SBILIFE", "HINDALCO",
            # Recently added stocks (16)
            "NMDC", "INFIBEAM", "INDIANREN", "BSE", "TANLA", "BIRLASOFT", "SUZLON", "SAKSOFT", "GAIL",
            "ADANIGREEN", "NHPC", "COCHINSHIP", "IRFC", "IRB", "BAJAJHLDNG", "HGIEL"
        ]
    
    def add_connection(self, websocket):
        """Add a WebSocket connection to the broadcaster"""
        self.active_connections.add(websocket)
        logger.info(f"Added WebSocket connection. Total connections: {len(self.active_connections)}")
    
    def remove_connection(self, websocket):
        """Remove a WebSocket connection from the broadcaster"""
        self.active_connections.discard(websocket)
        logger.info(f"Removed WebSocket connection. Remaining connections: {len(self.active_connections)}")
    
    async def start_broadcasting(self):
        """Start the real-time broadcasting task"""
        if self.is_running:
            return
        
        self.is_running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("Started real-time WebSocket broadcasting")
    
    async def stop_broadcasting(self):
        """Stop the real-time broadcasting task"""
        self.is_running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            self.broadcast_task = None
        logger.info("Stopped real-time WebSocket broadcasting")
    
    async def _broadcast_loop(self):
        """Main broadcasting loop"""
        while self.is_running:
            try:
                await self._broadcast_nifty50_updates()
                await asyncio.sleep(self.broadcast_interval)
            except asyncio.CancelledError:
                logger.info("Broadcast loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(10)  # Wait longer if there's an error
    
    async def _broadcast_nifty50_updates(self):
        """Broadcast real-time updates for Nifty50 symbols"""
        try:
            # Get batch quotes for all Nifty50 symbols
            async with realtime_service as service:
                quotes = await service.get_batch_quotes(self.nifty50_symbols, "NSE")
            
            # Broadcast to all connected clients
            if self.active_connections and quotes:
                message = {
                    "type": "nifty50_realtime_update",
                    "data": {
                        "quotes": quotes,
                        "timestamp": datetime.now().isoformat(),
                        "count": len(quotes)
                    }
                }
                
                message_str = json.dumps(message)
                disconnected = set()
                
                for connection in self.active_connections:
                    try:
                        await connection.send_text(message_str)
                    except Exception as e:
                        logger.error(f"Error sending to WebSocket: {e}")
                        disconnected.add(connection)
                
                # Remove disconnected connections
                for connection in disconnected:
                    self.remove_connection(connection)
                
                logger.debug(f"Broadcasted updates for {len(quotes)} symbols to {len(self.active_connections)} clients")
        
        except Exception as e:
            logger.error(f"Error broadcasting Nifty50 updates: {e}")
    
    async def broadcast_single_symbol_update(self, symbol: str, quote_data: Dict):
        """Broadcast update for a single symbol"""
        try:
            message = {
                "type": "single_symbol_update",
                "data": {
                    "symbol": symbol,
                    "quote": quote_data,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            message_str = json.dumps(message)
            disconnected = set()
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error sending single update: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.remove_connection(connection)
        
        except Exception as e:
            logger.error(f"Error broadcasting single symbol update: {e}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

# Global broadcaster instance
broadcaster = RealTimeWebSocketBroadcaster()
