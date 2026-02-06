"""
Real-time Order Book Service
Level 2 market data with delta updates and throttling
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import time

logger = logging.getLogger(__name__)

class RealtimeOrderBook:
    """Real-time order book with delta updates"""
    
    def __init__(self):
        self.order_books: Dict[str, Dict] = {}  # symbol -> order book data
        self.update_intervals: Dict[str, float] = {}  # symbol -> last update time
        self.min_update_interval = 0.1  # 100ms minimum between updates (10 updates/sec)
        
    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """Get current order book for symbol"""
        try:
            # This would integrate with your market data provider
            # For now, return mock data structure
            if symbol not in self.order_books:
                self.order_books[symbol] = {
                    "symbol": symbol,
                    "bids": [],
                    "asks": [],
                    "timestamp": datetime.now().isoformat()
                }
            
            return self.order_books[symbol]
        except Exception as e:
            logger.error(f"Error getting order book for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_delta_update(self, symbol: str, last_state: Optional[Dict] = None) -> Dict[str, Any]:
        """Get delta update (only changes) for order book"""
        try:
            current_book = await self.get_order_book(symbol)
            
            if last_state is None:
                return current_book
            
            # Calculate delta
            delta = {
                "symbol": symbol,
                "bids_changed": [],
                "asks_changed": [],
                "bids_removed": [],
                "asks_removed": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Compare bids
            last_bids = {b["price"]: b for b in last_state.get("bids", [])}
            current_bids = {b["price"]: b for b in current_book.get("bids", [])}
            
            for price, bid in current_bids.items():
                if price not in last_bids:
                    delta["bids_changed"].append(bid)
                elif bid["quantity"] != last_bids[price]["quantity"]:
                    delta["bids_changed"].append(bid)
            
            for price in last_bids:
                if price not in current_bids:
                    delta["bids_removed"].append(price)
            
            # Compare asks
            last_asks = {a["price"]: a for a in last_state.get("asks", [])}
            current_asks = {a["price"]: a for a in current_book.get("asks", [])}
            
            for price, ask in current_asks.items():
                if price not in last_asks:
                    delta["asks_changed"].append(ask)
                elif ask["quantity"] != last_asks[price]["quantity"]:
                    delta["asks_changed"].append(ask)
            
            for price in last_asks:
                if price not in current_asks:
                    delta["asks_removed"].append(price)
            
            return delta
            
        except Exception as e:
            logger.error(f"Error getting delta update for {symbol}: {e}")
            return {"error": str(e)}
    
    def should_update(self, symbol: str) -> bool:
        """Check if enough time has passed for update"""
        current_time = time.time()
        last_update = self.update_intervals.get(symbol, 0)
        
        if current_time - last_update >= self.min_update_interval:
            self.update_intervals[symbol] = current_time
            return True
        return False

# Create singleton instance
realtime_orderbook = RealtimeOrderBook()

