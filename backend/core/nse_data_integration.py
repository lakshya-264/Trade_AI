"""
NSE Real Data Integration Service
Handles real-time data from NSE (National Stock Exchange of India)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class NSEDataService:
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds for live data
        
        # NSE API endpoints
        self.base_url = "https://www.nseindia.com"
        self.api_endpoints = {
            "quote": "/api/quote-equity",
            "historical": "/api/historical/cm/equity",
            "market_status": "/api/marketStatus",
            "top_gainers": "/api/live-analysis-variations",
            "top_losers": "/api/live-analysis-variations"
        }
        
        # Headers required for NSE API
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en,gu;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nseindia.com/"
        }
    
    async def _get_session(self):
        """Get or create aiohttp session with proper headers"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _get_cookies_and_headers(self):
        """Get required cookies and headers from NSE"""
        try:
            session = await self._get_session()
            
            # First, visit the main page to establish session and get cookies
            async with session.get(self.base_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    cookies = response.cookies
                    
                    # Update headers with cookies
                    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                    self.headers["Cookie"] = cookie_header
                    
                    logger.info("NSE session established successfully")
                    return True
                else:
                    logger.error(f"Failed to establish NSE session: {response.status}")
                    return False
            
        except asyncio.CancelledError:
            logger.warning("NSE session establishment cancelled")
            return False
        except Exception as e:
            logger.error(f"Error getting NSE cookies: {e}")
            return False
    
    async def get_real_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real quote from NSE"""
        try:
            # Check cache first
            cache_key = f"nse_quote_{symbol}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Get cookies and headers
            if not await self._get_cookies_and_headers():
                raise Exception("Failed to get NSE cookies")
            
            session = await self._get_session()
            
            # Make API call to NSE
            url = f"{self.base_url}{self.api_endpoints['quote']}"
            params = {"symbol": symbol}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process NSE response
                    quote_data = self._process_nse_quote_response(data, symbol)
                    
                    # Cache the result
                    self.cache[cache_key] = (quote_data, datetime.now().timestamp())
                    
                    logger.info(f"Real NSE quote for {symbol}: ₹{quote_data['last_price']}")
                    return quote_data
                else:
                    logger.error(f"NSE API error for {symbol}: {response.status}")
                    raise Exception(f"NSE API returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"Error getting real NSE quote for {symbol}: {e}")
            # Return fallback mock data
            return self._get_fallback_quote(symbol)
    
    def _process_nse_quote_response(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Process NSE API response into standardized format"""
        try:
            # Extract data from NSE response structure
            info = data.get("info", {})
            price_info = data.get("priceInfo", {})
            pre_open_market = data.get("preOpenMarket", {})
            
            # Get current price
            last_price = price_info.get("lastPrice", 0)
            open_price = price_info.get("open", 0)
            high_price = price_info.get("intraDayHighLow", {}).get("max", 0)
            low_price = price_info.get("intraDayHighLow", {}).get("min", 0)
            previous_close = price_info.get("previousClose", 0)
            
            # Calculate change
            change = last_price - previous_close if previous_close > 0 else 0
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            # Get volume
            total_traded_volume = price_info.get("totalTradedVolume", 0)
            
            return {
                "symbol": symbol,
                "last_price": round(last_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": total_traded_volume,
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "open": round(open_price, 2),
                "previous_close": round(previous_close, 2),
                "currency": "INR",
                "currency_symbol": "₹",
                "formatted_price": f"₹{last_price:,.2f}",
                "formatted_change": f"₹{change:+,.2f}",
                "formatted_change_percent": f"{change_percent:+.2f}%",
                "exchange": "NSE",
                "data_source": "NSE_REAL",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing NSE response for {symbol}: {e}")
            return self._get_fallback_quote(symbol)
    
    def _get_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback to mock data if NSE API fails"""
        # Generate realistic mock data directly instead of using asyncio.run
        import random
        from datetime import datetime
        
        # Base prices for different symbols
        base_prices = {
            "RELIANCE": 2400,
            "TCS": 3800,
            "HDFCBANK": 1500,
            "INFY": 1800,
            "HINDUNILVR": 2500,
            "ITC": 400,
            "SBIN": 500,
            "BHARTIARTL": 800,
            "KOTAKBANK": 1800,
            "ASIANPAINT": 3000
        }
        
        base_price = base_prices.get(symbol, 1000)
        
        # Generate realistic price movement
        change_percent = random.uniform(-3, 3)  # -3% to +3% change
        change_amount = base_price * (change_percent / 100)
        current_price = base_price + change_amount
        
        # Generate volume
        volume = random.randint(100000, 5000000)
        
        # Generate OHLC data
        high_price = current_price * random.uniform(1.0, 1.05)
        low_price = current_price * random.uniform(0.95, 1.0)
        open_price = base_price * random.uniform(0.98, 1.02)
        
        return {
            "symbol": symbol,
            "last_price": round(current_price, 2),
            "change": round(change_amount, 2),
            "change_percent": round(change_percent, 2),
            "volume": volume,
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "open": round(open_price, 2),
            "previous_close": round(base_price, 2),
            "currency": "INR",
            "currency_symbol": "₹",
            "formatted_price": f"₹{current_price:,.2f}",
            "formatted_change": f"₹{change_amount:+,.2f}",
            "formatted_change_percent": f"{change_percent:+.2f}%",
            "data_source": "NSE_FALLBACK",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_multiple_real_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get real quotes for multiple symbols"""
        try:
            quotes = {}
            
            # Process symbols in parallel with rate limiting
            semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
            
            async def fetch_quote(symbol: str):
                async with semaphore:
                    return await self.get_real_quote(symbol)
            
            tasks = [fetch_quote(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error getting real quote for {symbols[i]}: {result}")
                    quotes[symbols[i]] = self._get_fallback_quote(symbols[i])
                else:
                    quotes[symbols[i]] = result
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting multiple real quotes: {e}")
            return {}
    
    async def get_real_market_status(self) -> Dict[str, Any]:
        """Get real market status from NSE"""
        try:
            session = await self._get_session()
            
            if not await self._get_cookies_and_headers():
                raise Exception("Failed to get NSE cookies")
            
            url = f"{self.base_url}{self.api_endpoints['market_status']}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process market status
                    market_status = self._process_market_status_response(data)
                    return market_status
                else:
                    logger.error(f"NSE market status API error: {response.status}")
                    raise Exception(f"NSE API returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"Error getting real market status: {e}")
            # Return fallback status
            return {
                "nse": {"status": "unknown", "error": str(e)},
                "bse": {"status": "unknown", "error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_market_status_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process NSE market status response"""
        try:
            # Extract market status from NSE response
            market_status = data.get("marketState", [])
            
            nse_status = "closed"
            bse_status = "closed"
            
            for market in market_status:
                if market.get("market") == "NSE":
                    nse_status = "open" if market.get("marketStatus") == "Open" else "closed"
                elif market.get("market") == "BSE":
                    bse_status = "open" if market.get("marketStatus") == "Open" else "closed"
            
            return {
                "nse": {
                    "status": nse_status,
                    "current_time": datetime.now().isoformat()
                },
                "bse": {
                    "status": bse_status,
                    "current_time": datetime.now().isoformat()
                },
                "data_source": "NSE_REAL",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing market status: {e}")
            return {
                "nse": {"status": "unknown"},
                "bse": {"status": "unknown"},
                "error": str(e)
            }
    
    async def get_real_top_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get real top gainers from NSE"""
        try:
            session = await self._get_session()
            
            if not await self._get_cookies_and_headers():
                raise Exception("Failed to get NSE cookies")
            
            url = f"{self.base_url}{self.api_endpoints['top_gainers']}"
            params = {"index": "gainers"}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process top gainers
                    gainers = self._process_top_gainers_response(data, limit)
                    return gainers
                else:
                    logger.error(f"NSE top gainers API error: {response.status}")
                    raise Exception(f"NSE API returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"Error getting real top gainers: {e}")
            return []
    
    def _process_top_gainers_response(self, data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Process NSE top gainers response"""
        try:
            gainers = []
            data_list = data.get("data", [])
            
            for item in data_list[:limit]:
                symbol = item.get("symbol", "")
                last_price = item.get("lastPrice", 0)
                change = item.get("change", 0)
                change_percent = item.get("pChange", 0)
                volume = item.get("totalTradedVolume", 0)
                
                gainers.append({
                    "symbol": symbol,
                    "last_price": round(last_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": volume,
                    "currency": "INR",
                    "currency_symbol": "₹",
                    "formatted_price": f"₹{last_price:,.2f}",
                    "formatted_change": f"₹{change:+,.2f}",
                    "formatted_change_percent": f"{change_percent:+.2f}%",
                    "data_source": "NSE_REAL"
                })
            
            return gainers
            
        except Exception as e:
            logger.error(f"Error processing top gainers: {e}")
            return []

# Global NSE data service instance
nse_data_service = NSEDataService()
