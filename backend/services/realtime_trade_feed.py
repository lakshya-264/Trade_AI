"""
Real-time Trade Feed Service
Real-time trade execution feed with aggregation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import time

logger = logging.getLogger(__name__)

class RealtimeTradeFeed:
    """Real-time trade feed with aggregation"""
    
    def __init__(self):
        self.trade_feeds: Dict[str, deque] = {}  # symbol -> recent trades
        self.max_trades_per_symbol = 1000  # Keep last 1000 trades
        self.aggregation_window = 1.0  # Aggregate trades within 1 second
        self.min_update_interval = 0.2  # 200ms minimum (5 updates/sec)
        self.last_update_time: Dict[str, float] = {}
        
    async def get_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for symbol"""
        try:
            if symbol not in self.trade_feeds:
                self.trade_feeds[symbol] = deque(maxlen=self.max_trades_per_symbol)
            
            # Return last N trades
            trades = list(self.trade_feeds[symbol])[-limit:]
            return trades
            
        except Exception as e:
            logger.error(f"Error getting trades for {symbol}: {e}")
            return []
    
    async def add_trade(self, symbol: str, trade: Dict[str, Any]):
        """Add new trade to feed"""
        try:
            if symbol not in self.trade_feeds:
                self.trade_feeds[symbol] = deque(maxlen=self.max_trades_per_symbol)
            
            trade_data = {
                "symbol": symbol,
                "price": trade.get("price", 0.0),
                "quantity": trade.get("quantity", 0),
                "timestamp": trade.get("timestamp", datetime.now().isoformat()),
                "side": trade.get("side", "UNKNOWN"),  # BUY or SELL
                "trade_id": trade.get("trade_id", "")
            }
            
            self.trade_feeds[symbol].append(trade_data)
            
        except Exception as e:
            logger.error(f"Error adding trade for {symbol}: {e}")
    
    async def get_aggregated_trades(self, symbol: str, window_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Get aggregated trades within time window"""
        try:
            trades = await self.get_trades(symbol, limit=1000)
            if not trades:
                return []
            
            current_time = datetime.now()
            window_start = current_time.timestamp() - window_seconds
            
            # Filter trades in window
            recent_trades = [
                t for t in trades
                if datetime.fromisoformat(t["timestamp"]).timestamp() >= window_start
            ]
            
            # Aggregate by price level
            aggregated = {}
            for trade in recent_trades:
                price = trade["price"]
                if price not in aggregated:
                    aggregated[price] = {
                        "price": price,
                        "total_quantity": 0,
                        "buy_quantity": 0,
                        "sell_quantity": 0,
                        "trade_count": 0,
                        "last_trade_time": trade["timestamp"]
                    }
                
                aggregated[price]["total_quantity"] += trade["quantity"]
                aggregated[price]["trade_count"] += 1
                
                if trade["side"] == "BUY":
                    aggregated[price]["buy_quantity"] += trade["quantity"]
                else:
                    aggregated[price]["sell_quantity"] += trade["quantity"]
            
            return list(aggregated.values())
            
        except Exception as e:
            logger.error(f"Error getting aggregated trades for {symbol}: {e}")
            return []
    
    def should_update(self, symbol: str) -> bool:
        """Check if enough time has passed for update"""
        current_time = time.time()
        last_update = self.last_update_time.get(symbol, 0)
        
        if current_time - last_update >= self.min_update_interval:
            self.last_update_time[symbol] = current_time
            return True
        return False

# Create singleton instance
realtime_trade_feed = RealtimeTradeFeed()

