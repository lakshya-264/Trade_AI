"""
Simplified NSE API without external dependencies
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)

class NSEAPI:
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api"
        self.session = None
        self.cookies = None
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get NSE quote - simplified version"""
        try:
            # Return mock data for now
            return self._get_mock_quote(symbol)
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return self._get_mock_quote(symbol)
    
    async def get_historical_data(self, symbol: str, period: str = "1mo") -> List[Dict[str, Any]]:
        """Get historical data - simplified version"""
        return self._get_mock_historical_data(symbol)
    
    async def get_index_quote(self, index_name: str) -> Dict[str, Any]:
        """Get index quote - simplified version"""
        return self._get_mock_index_quote(index_name)
    
    async def get_top_gainers(self) -> List[Dict[str, Any]]:
        """Get top gainers - simplified version"""
        return self._get_mock_top_gainers()
    
    async def get_top_losers(self) -> List[Dict[str, Any]]:
        """Get top losers - simplified version"""
        return self._get_mock_top_losers()
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Generate mock quote data"""
        base_price = 1000 + hash(symbol) % 5000
        change = random.uniform(-50, 50)
        change_percent = (change / base_price) * 100
        
        return {
            "symbol": symbol,
            "last_price": round(base_price + change, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": random.randint(100000, 1000000),
            "high": round(base_price + change + random.uniform(0, 20), 2),
            "low": round(base_price + change - random.uniform(0, 20), 2),
            "open": round(base_price + random.uniform(-10, 10), 2),
            "close": round(base_price + change, 2),
            "timestamp": datetime.now().isoformat(),
            "source": "mock_nse"
        }
    
    def _get_mock_historical_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Generate mock historical data"""
        data = []
        base_price = 1000 + hash(symbol) % 5000
        
        for i in range(30):  # 30 days
            price = base_price + random.uniform(-100, 100)
            data.append({
                "date": (datetime.now().timestamp() - i * 86400) * 1000,  # Unix timestamp in ms
                "open": round(price + random.uniform(-5, 5), 2),
                "high": round(price + random.uniform(0, 10), 2),
                "low": round(price - random.uniform(0, 10), 2),
                "close": round(price, 2),
                "volume": random.randint(100000, 1000000)
            })
        
        return data
    
    def _get_mock_index_quote(self, index_name: str) -> Dict[str, Any]:
        """Generate mock index quote"""
        base_value = 20000 + hash(index_name) % 10000
        change = random.uniform(-200, 200)
        change_percent = (change / base_value) * 100
        
        return {
            "index": index_name,
            "last_price": round(base_value + change, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "timestamp": datetime.now().isoformat(),
            "source": "mock_nse"
        }
    
    def _get_mock_top_gainers(self) -> List[Dict[str, Any]]:
        """Generate mock top gainers"""
        symbols = ["RELIANCE", "TCS", "HDFC", "INFY", "ICICIBANK"]
        gainers = []
        
        for symbol in symbols:
            gainers.append({
                "symbol": symbol,
                "last_price": round(1000 + random.uniform(0, 500), 2),
                "change": round(random.uniform(10, 50), 2),
                "change_percent": round(random.uniform(1, 5), 2),
                "volume": random.randint(100000, 1000000)
            })
        
        return gainers
    
    def _get_mock_top_losers(self) -> List[Dict[str, Any]]:
        """Generate mock top losers"""
        symbols = ["SOME_STOCK", "ANOTHER_STOCK", "YET_ANOTHER", "LOSING_STOCK", "BAD_STOCK"]
        losers = []
        
        for symbol in symbols:
            losers.append({
                "symbol": symbol,
                "last_price": round(1000 + random.uniform(0, 500), 2),
                "change": round(random.uniform(-50, -10), 2),
                "change_percent": round(random.uniform(-5, -1), 2),
                "volume": random.randint(100000, 1000000)
            })
        
        return losers
