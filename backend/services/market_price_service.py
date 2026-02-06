"""
Market Price Service - Real-time market data integration
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging
import asyncio
import aiohttp
import json

from core.database import get_db

logger = logging.getLogger(__name__)

class MarketPriceService:
    """Service for fetching real-time market prices"""
    
    def __init__(self):
        self.cache_timeout = 60  # Cache prices for 60 seconds
        self.price_cache = {}
        self.market_apis = {
            'primary': 'https://api.nseindia.com/api/quote-equity',
            'backup': 'https://api.bseindia.com/api/quote',
            'fallback': 'https://www.alphavantage.co/query'  # Free API as fallback
        }
        self.session = None
    
    async def get_current_price(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get current market price for a symbol"""
        try:
            # Check cache first
            if use_cache and self._is_cached(symbol):
                logger.info(f"Returning cached price for {symbol}")
                return self.price_cache[symbol]['data']
            
            # Fetch from market APIs
            price_data = await self._fetch_market_price(symbol)
            
            if price_data:
                # Cache the result
                self._cache_price(symbol, price_data)
                return price_data
            else:
                # Return fallback data
                return self._get_fallback_price(symbol)
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return self._get_fallback_price(symbol)
    
    async def get_multiple_prices(
        self,
        symbols: List[str],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get current prices for multiple symbols"""
        try:
            results = {}
            
            # Check cache first
            if use_cache:
                for symbol in symbols:
                    if self._is_cached(symbol):
                        results[symbol] = self.price_cache[symbol]['data']
            
            # Fetch remaining symbols
            uncached_symbols = [s for s in symbols if s not in results]
            
            if uncached_symbols:
                # Fetch in parallel
                tasks = [self._fetch_market_price(symbol) for symbol in uncached_symbols]
                price_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for symbol, price_data in zip(uncached_symbols, price_results):
                    if isinstance(price_data, Exception):
                        results[symbol] = self._get_fallback_price(symbol)
                    elif price_data:
                        results[symbol] = price_data
                        self._cache_price(symbol, price_data)
                    else:
                        results[symbol] = self._get_fallback_price(symbol)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return {symbol: self._get_fallback_price(symbol) for symbol in symbols}
    
    async def _fetch_market_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from market APIs"""
        try:
            # Try primary API (NSE)
            price_data = await self._fetch_from_nse(symbol)
            if price_data:
                return price_data
            
            # Try backup API (BSE)
            price_data = await self._fetch_from_bse(symbol)
            if price_data:
                return price_data
            
            # Try fallback API
            price_data = await self._fetch_from_alphavantage(symbol)
            if price_data:
                return price_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market price for {symbol}: {e}")
            return None
    
    async def _fetch_from_nse(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from NSE API"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # NSE API endpoint
            url = f"{self.market_apis['primary']}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            params = {
                'symbol': symbol,
                'series': 'EQ'
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse NSE response
                    if 'priceInfo' in data and 'lastPrice' in data['priceInfo']:
                        price_info = data['priceInfo']
                        market_info = data.get('marketDeptOrderBook', {}).get('tradeInfo', {})
                        
                        return {
                            'symbol': symbol,
                            'current_price': price_info['lastPrice'],
                            'open_price': price_info.get('open', 0),
                            'high_price': price_info.get('high', 0),
                            'low_price': price_info.get('low', 0),
                            'close_price': price_info.get('previousClose', 0),
                            'volume': market_info.get('totalTradedVolume', 0),
                            'value': market_info.get('totalTradedValue', 0),
                            'change': price_info.get('change', 0),
                            'change_percent': price_info.get('pChange', 0),
                            'timestamp': datetime.utcnow().isoformat(),
                            'source': 'NSE'
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from NSE for {symbol}: {e}")
            return None
    
    async def _fetch_from_bse(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from BSE API"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # BSE API endpoint
            url = f"{self.market_apis['backup']}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            params = {
                'scripcode': self._get_bse_code(symbol),
                'series': 'EQ'
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse BSE response
                    if 'data' in data and len(data['data']) > 0:
                        stock_data = data['data'][0]
                        
                        return {
                            'symbol': symbol,
                            'current_price': stock_data.get('ltp', 0),
                            'open_price': stock_data.get('open', 0),
                            'high_price': stock_data.get('high', 0),
                            'low_price': stock_data.get('low', 0),
                            'close_price': stock_data.get('closePrice', 0),
                            'volume': stock_data.get('totalTradedVolume', 0),
                            'value': stock_data.get('totalTradedValue', 0),
                            'change': stock_data.get('change', 0),
                            'change_percent': stock_data.get('pChange', 0),
                            'timestamp': datetime.utcnow().isoformat(),
                            'source': 'BSE'
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from BSE for {symbol}: {e}")
            return None
    
    async def _fetch_from_alphavantage(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch price from Alpha Vantage API (fallback)"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Alpha Vantage API (free tier)
            api_key = 'YOUR_ALPHA_VANTAGE_API_KEY'  # Need to configure
            url = f"{self.market_apis['fallback']}"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': f'{symbol}.BSE',  # Add .BSE for Indian stocks
                'apikey': api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse Alpha Vantage response
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        
                        return {
                            'symbol': symbol,
                            'current_price': float(quote.get('05. price', 0)),
                            'open_price': float(quote.get('02. open', 0)),
                            'high_price': float(quote.get('03. high', 0)),
                            'low_price': float(quote.get('04. low', 0)),
                            'close_price': float(quote.get('08. previous close', 0)),
                            'volume': int(quote.get('06. volume', 0)),
                            'change': float(quote.get('09. change', 0)),
                            'change_percent': float(quote.get('10. change percent', 0).replace('%', '')),
                            'timestamp': datetime.utcnow().isoformat(),
                            'source': 'ALPHA_VANTAGE'
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage for {symbol}: {e}")
            return None
    
    def _get_fallback_price(self, symbol: str) -> Dict[str, Any]:
        """Get fallback price when APIs fail"""
        try:
            # Use last known price or estimated price
            fallback_prices = {
                'RELIANCE': 2500.0,
                'TCS': 3500.0,
                'INFY': 1500.0,
                'HDFC': 1600.0,
                'ICICIBANK': 900.0,
                'HINDUNILVR': 2800.0,
                'ITC': 400.0,
                'SBIN': 600.0,
                'MARUTI': 10000.0,
                'TATAMOTORS': 500.0
            }
            
            base_price = fallback_prices.get(symbol, 1000.0)
            
            # Add small random variation to simulate market movement
            import random
            variation = random.uniform(-0.02, 0.02)  # ±2% variation
            current_price = base_price * (1 + variation)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'open_price': base_price,
                'high_price': base_price * 1.05,
                'low_price': base_price * 0.95,
                'close_price': base_price,
                'volume': 1000000,
                'value': current_price * 1000000,
                'change': current_price - base_price,
                'change_percent': ((current_price - base_price) / base_price) * 100,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'FALLBACK',
                'is_simulated': True
            }
            
        except Exception as e:
            logger.error(f"Error getting fallback price for {symbol}: {e}")
            return {
                'symbol': symbol,
                'current_price': 1000.0,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'FALLBACK',
                'is_simulated': True
            }
    
    def _get_bse_code(self, symbol: str) -> str:
        """Get BSE code for symbol"""
        # Mapping of NSE symbols to BSE codes
        bse_codes = {
            'RELIANCE': '500325',
            'TCS': '532940',
            'INFY': '500209',
            'HDFC': '500180',
            'ICICIBANK': '532174',
            'HINDUNILVR': '500896',
            'ITC': '500875',
            'SBIN': '500112',
            'MARUTI': '532877',
            'TATAMOTORS': '500570'
        }
        return bse_codes.get(symbol, symbol)
    
    def _is_cached(self, symbol: str) -> bool:
        """Check if price is cached and not expired"""
        try:
            if symbol not in self.price_cache:
                return False
            
            cache_entry = self.price_cache[symbol]
            cache_time = datetime.fromisoformat(cache_entry['timestamp'].replace('Z', '+00:00'))
            
            return (datetime.utcnow() - cache_time).total_seconds() < self.cache_timeout
            
        except Exception as e:
            logger.error(f"Error checking cache for {symbol}: {e}")
            return False
    
    def _cache_price(self, symbol: str, price_data: Dict[str, Any]):
        """Cache price data"""
        try:
            self.price_cache[symbol] = {
                'data': price_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error caching price for {symbol}: {e}")
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            now = datetime.utcnow()
            ist_time = now + timedelta(hours=5, minutes=30)  # Convert to IST
            
            # Check if market is open (9:15 AM to 3:30 PM IST on weekdays)
            is_weekday = ist_time.weekday() < 5  # Monday to Friday
            market_open = ist_time.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = ist_time.replace(hour=15, minute=30, second=0, microsecond=0)
            
            is_market_open = is_weekday and market_open <= ist_time <= market_close
            
            return {
                'is_market_open': is_market_open,
                'current_time_ist': ist_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                'market_open_time': market_open.strftime('%H:%M:%S IST'),
                'market_close_time': market_close.strftime('%H:%M:%S IST'),
                'is_weekday': is_weekday,
                'next_session': self._get_next_session_time(ist_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {
                'is_market_open': False,
                'current_time_ist': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S IST'),
                'error': str(e)
            }
    
    def _get_next_session_time(self, current_time: datetime) -> str:
        """Get next market session time"""
        try:
            if current_time.weekday() >= 5:  # Weekend
                # Next Monday
                days_until_monday = 7 - current_time.weekday()
                next_session = current_time + timedelta(days=days_until_monday)
            elif current_time.hour > 15 or (current_time.hour == 15 and current_time.minute > 30):
                # Next day
                next_session = current_time + timedelta(days=1)
            else:
                # Today
                next_session = current_time
            
            return next_session.strftime('%Y-%m-%d %H:%M:%S IST')
            
        except Exception as e:
            logger.error(f"Error getting next session time: {e}")
            return "Unknown"
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

# Create global instance
market_price_service = MarketPriceService()
