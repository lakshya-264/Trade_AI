"""
Real-Time Data Service for Nifty50 Stocks
Fetches live market data from multiple sources
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class RealTimeDataService:
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_duration = 60  # 60 seconds cache
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_real_time_quote(self, symbol: str, exchange: str = "NSE") -> Dict:
        """Get real-time quote for a symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{exchange}"
            now = datetime.now()
            
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (now - timestamp).total_seconds() < self.cache_duration:
                    return cached_data
            
            # Try multiple data sources
            quote_data = await self._fetch_from_multiple_sources(symbol, exchange)
            
            # Cache the result
            self.cache[cache_key] = (quote_data, now)
            
            return quote_data
            
        except Exception as e:
            logger.error(f"Error getting real-time quote for {symbol}: {e}")
            return self._generate_fallback_quote(symbol)
    
    async def _fetch_from_multiple_sources(self, symbol: str, exchange: str) -> Dict:
        """Try multiple data sources for real-time data"""
        
        # Source 1: Yahoo Finance
        yahoo_data = await self._fetch_from_yahoo_finance(symbol)
        if yahoo_data:
            return yahoo_data
        
        # Source 2: NSE API (if available)
        nse_data = await self._fetch_from_nse(symbol)
        if nse_data:
            return nse_data
        
        # Source 3: Alpha Vantage (if API key available)
        alpha_data = await self._fetch_from_alpha_vantage(symbol)
        if alpha_data:
            return alpha_data
        
        # Fallback to realistic mock data
        return self._generate_realistic_quote(symbol)
    
    async def _fetch_from_yahoo_finance(self, symbol: str) -> Optional[Dict]:
        """Fetch from Yahoo Finance API"""
        try:
            # Normalize symbol for Yahoo Finance
            yahoo_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('chart') and data['chart']['result']:
                        result = data['chart']['result'][0]
                        
                        # Extract quote data
                        meta = result.get('meta', {})
                        current_price = meta.get('regularMarketPrice', 0)
                        previous_close = meta.get('chartPreviousClose', 0)
                        
                        if current_price > 0:
                            change = current_price - previous_close
                            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                            
                            return {
                                'symbol': symbol,
                                'price': current_price,
                                'change': change,
                                'change_percent': change_percent,
                                'volume': meta.get('regularMarketVolume', 0),
                                'timestamp': datetime.now().isoformat(),
                                'data_source': 'YAHOO_FINANCE',
                                'currency': meta.get('currency', 'INR'),
                                'market_state': meta.get('marketState', 'CLOSED')
                            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
        
        return None
    
    async def _fetch_from_nse(self, symbol: str) -> Optional[Dict]:
        """Fetch from NSE API"""
        try:
            # NSE API endpoint (this would need actual implementation)
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.nseindia.com/'
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'priceInfo' in data:
                        price_info = data['priceInfo']
                        current_price = price_info.get('lastPrice', 0)
                        previous_close = price_info.get('previousClose', 0)
                        
                        if current_price > 0:
                            change = current_price - previous_close
                            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                            
                            return {
                                'symbol': symbol,
                                'price': current_price,
                                'change': change,
                                'change_percent': change_percent,
                                'volume': price_info.get('totalTradedVolume', 0),
                                'timestamp': datetime.now().isoformat(),
                                'data_source': 'NSE',
                                'currency': 'INR',
                                'market_state': data.get('marketStatus', 'CLOSED')
                            }
            
        except Exception as e:
            logger.error(f"NSE API error for {symbol}: {e}")
        
        return None
    
    async def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch from Alpha Vantage API"""
        try:
            # Check if API key is available
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                return None
            
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}.BSE&apikey={api_key}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        current_price = float(quote.get('05. price', 0))
                        previous_close = float(quote.get('08. previous close', 0))
                        
                        if current_price > 0:
                            change = current_price - previous_close
                            change_percent = float(quote.get('10. change percent', '0').replace('%', ''))
                            
                            return {
                                'symbol': symbol,
                                'price': current_price,
                                'change': change,
                                'change_percent': change_percent,
                                'volume': int(quote.get('06. volume', 0)),
                                'timestamp': datetime.now().isoformat(),
                                'data_source': 'ALPHA_VANTAGE',
                                'currency': 'INR',
                                'market_state': 'CLOSED'
                            }
            
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
        
        return None
    
    def _generate_realistic_quote(self, symbol: str) -> Dict:
        """Generate realistic mock data based on typical stock ranges"""
        try:
            # Base prices for all 66 Nifty50 stocks
            stock_prices = {
                # Core Nifty50 stocks
                'RELIANCE': 2800, 'TCS': 3500, 'HDFCBANK': 1600, 'INFY': 1500, 'HINDUNILVR': 2500,
                'ICICIBANK': 900, 'KOTAKBANK': 1800, 'HDFC': 2600, 'ITC': 400, 'BHARTIARTL': 900,
                'SBIN': 600, 'BAJFINANCE': 7000, 'ASIANPAINT': 3000, 'AXISBANK': 800, 'MARUTI': 10000,
                'SUNPHARMA': 1000, 'TITAN': 2300, 'ULTRACEMCO': 10000, 'NESTLEIND': 20000, 'POWERGRID': 200,
                'NTPC': 300, 'TECHM': 1300, 'WIPRO': 400, 'HCLTECH': 1200, 'LT': 3000,
                'BAJAJFINSV': 15000, 'DRREDDY': 5000, 'TATAMOTORS': 800, 'BRITANNIA': 5000, 'EICHERMOT': 3500,
                'SHREECEM': 25000, 'JSWSTEEL': 600, 'TATASTEEL': 120, 'INDUSINDBK': 1000, 'COALINDIA': 200,
                'GRASIM': 1800, 'CIPLA': 1000, 'ONGC': 200, 'TATACONSUM': 800, 'APOLLOHOSP': 4000,
                'ADANIPORTS': 800, 'BPCL': 500, 'HEROMOTOCO': 4000, 'DIVISLAB': 5000, 'UPL': 800,
                'BAJAJ-AUTO': 9000, 'TATAPOWER': 200, 'ADANIENT': 2500, 'SBILIFE': 600, 'HINDALCO': 500,
                # Recently added stocks (16 additional stocks)
                'NMDC': 200, 'INFIBEAM': 50, 'INDIANREN': 100, 'BSE': 6000, 'TANLA': 1000,
                'BIRLASOFT': 500, 'SUZLON': 20, 'SAKSOFT': 300, 'GAIL': 150, 'ADANIGREEN': 3000,
                'NHPC': 100, 'COCHINSHIP': 400, 'IRFC': 30, 'IRB': 200, 'BAJAJHLDNG': 7000, 'HGIEL': 100
            }
            
            base_price = stock_prices.get(symbol, 1000)
            
            # Add realistic variation
            variation = np.random.uniform(-0.05, 0.05)  # ±5% variation
            current_price = base_price * (1 + variation)
            
            # Generate realistic change
            change = np.random.uniform(-50, 50)
            change_percent = (change / base_price) * 100
            
            # Generate realistic volume
            volume = np.random.randint(100000, 10000000)
            
            return {
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'REALISTIC_MOCK',
                'currency': 'INR',
                'market_state': 'CLOSED'
            }
            
        except Exception as e:
            logger.error(f"Error generating realistic quote for {symbol}: {e}")
            return self._generate_fallback_quote(symbol)
    
    def _generate_fallback_quote(self, symbol: str) -> Dict:
        """Generate basic fallback quote"""
        return {
            'symbol': symbol,
            'price': 1000.0,
            'change': 0.0,
            'change_percent': 0.0,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'FALLBACK',
            'currency': 'INR',
            'market_state': 'CLOSED'
        }
    
    async def get_batch_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict]:
        """Get real-time quotes for multiple symbols"""
        try:
            quotes = {}
            
            # Fetch quotes concurrently
            tasks = []
            for symbol in symbols:
                task = self.get_real_time_quote(symbol, exchange)
                tasks.append((symbol, task))
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (symbol, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Error getting quote for {symbol}: {result}")
                    quotes[symbol] = self._generate_fallback_quote(symbol)
                else:
                    quotes[symbol] = result
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting batch quotes: {e}")
            return {symbol: self._generate_fallback_quote(symbol) for symbol in symbols}
    
    async def get_historical_data(self, symbol: str, timeframe: str, days: int = 7) -> List[Dict]:
        """Get historical data for technical indicators"""
        try:
            # For now, generate realistic historical data
            # In production, this would fetch from real data sources
            
            base_price = 1000  # Would get from real-time quote
            data_points = days * (24 if timeframe == '1h' else 1)  # Adjust for timeframe
            
            historical_data = []
            current_time = datetime.now()
            
            for i in range(data_points):
                timestamp = current_time - timedelta(hours=i)
                
                # Generate realistic price movement
                price_change = np.random.normal(0, 0.02)  # 2% volatility
                price = base_price * (1 + price_change)
                
                historical_data.append({
                    'timestamp': timestamp.isoformat(),
                    'open': price * (1 + np.random.uniform(-0.01, 0.01)),
                    'high': price * (1 + np.random.uniform(0, 0.02)),
                    'low': price * (1 - np.random.uniform(0, 0.02)),
                    'close': price,
                    'volume': np.random.randint(100000, 1000000)
                })
            
            return historical_data[::-1]  # Reverse to get chronological order
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

# Singleton instance
realtime_service = RealTimeDataService()
