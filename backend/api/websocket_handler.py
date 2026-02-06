"""
WebSocket Handler for Real-Time Nifty50 Updates
Provides live trading signals and technical indicators
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import random

from services.technical_indicators import TechnicalIndicatorsService
from services.realtime_websocket_broadcaster import broadcaster

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Store active connections by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.technical_service = TechnicalIndicatorsService()
        
    async def connect(self, websocket: WebSocket, channel: str = "default"):
        """Connect a WebSocket to a specific channel"""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}. Total connections: {len(self.active_connections[channel])}")
        
        # Add to real-time broadcaster if it's a nifty50 channel
        if channel == "nifty50_updates":
            broadcaster.add_connection(websocket)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "data": {"status": "connected", "channel": channel},
            "timestamp": datetime.now().isoformat()
        }))
    
    def disconnect(self, websocket: WebSocket, channel: str = "default"):
        """Disconnect a WebSocket from a channel"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(f"WebSocket disconnected from channel: {channel}. Remaining connections: {len(self.active_connections[channel])}")
            
            # Remove from real-time broadcaster if it's a nifty50 channel
            if channel == "nifty50_updates":
                broadcaster.remove_connection(websocket)
            
            # Clean up empty channels
            if len(self.active_connections[channel]) == 0:
                del self.active_connections[channel]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast a message to all WebSockets in a channel"""
        if channel not in self.active_connections:
            return
        
        message_str = json.dumps({
            "type": message.get("type", "update"),
            "data": message.get("data", {}),
            "timestamp": datetime.now().isoformat()
        })
        
        # Create a list of connections to remove if they fail
        to_remove = []
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                to_remove.append(connection)
        
        # Remove failed connections
        for connection in to_remove:
            self.active_connections[channel].discard(connection)
    
    async def broadcast_nifty50_updates(self):
        """Broadcast real-time Nifty50 trading signals"""
        # All 66 Nifty50 symbols
        nifty50_symbols = [
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
        
        # Generate real-time updates for a few random symbols
        symbols_to_update = random.sample(nifty50_symbols, min(5, len(nifty50_symbols)))
        
        for symbol in symbols_to_update:
            try:
                # Generate sample real-time data
                base_price = random.uniform(1000, 5000)
                change = random.uniform(-5, 5)
                volume = random.randint(1000, 100000)
                
                # Generate trading signals
                signals = {
                    "vwap_signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "momentum_signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "breakout_signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "mean_reversion_signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "scalping_signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "comprehensive_signal": random.choice(["BUY", "SELL", "HOLD"])
                }
                
                # Generate technical indicators
                technical_indicators = {
                    "rsi": random.uniform(20, 80),
                    "macd": random.uniform(-2, 2),
                    "bollinger_upper": base_price * 1.02,
                    "bollinger_lower": base_price * 0.98,
                    "sma_20": base_price * random.uniform(0.98, 1.02),
                    "ema_12": base_price * random.uniform(0.99, 1.01),
                    "atr": base_price * random.uniform(0.01, 0.03),
                    "volume_sma": random.uniform(5000, 50000)
                }
                
                # Create update message
                update_data = {
                    "symbol": symbol,
                    "price": base_price,
                    "change": change,
                    "changePercent": change,
                    "volume": volume,
                    "timestamp": datetime.now().isoformat(),
                    "signals": signals,
                    "technical_indicators": technical_indicators
                }
                
                # Broadcast to nifty50_updates channel
                await self.broadcast_to_channel("nifty50_updates", {
                    "type": "stock_update",
                    "data": update_data
                })
                
            except Exception as e:
                logger.error(f"Error generating update for {symbol}: {e}")
    
    async def start_broadcast_scheduler(self):
        """Start the background task to broadcast updates"""
        while True:
            try:
                await self.broadcast_nifty50_updates()
                await asyncio.sleep(5)  # Broadcast every 5 seconds
            except Exception as e:
                logger.error(f"Error in broadcast scheduler: {e}")
                await asyncio.sleep(10)  # Wait longer if there's an error

# Global WebSocket manager instance
manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket, channel: str = "default"):
    """WebSocket endpoint handler"""
    await manager.connect(websocket, channel)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "subscribe":
                    # Handle subscription requests
                    await websocket.send_text(json.dumps({
                        "type": "subscription_ack",
                        "data": {"channel": message.get("data", {}).get("channel", channel)},
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message.get("type") == "ping":
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)

# Start the broadcast scheduler when the module is imported
async def start_websocket_scheduler():
    """Start the WebSocket broadcast scheduler"""
    asyncio.create_task(manager.start_broadcast_scheduler())
