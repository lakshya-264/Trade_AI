"""
Upstox API Service
Official market data provider for TraderAI platform
Provides real-time market data, historical data, and WebSocket streaming
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import os
from enum import Enum

logger = logging.getLogger(__name__)

class UpstoxService:
    """
    Upstox API Integration Service
    Provides real-time quotes, historical data, and WebSocket support
    """
    
    def __init__(self):
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.refresh_token = os.getenv("UPSTOX_REFRESH_TOKEN")
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:3000/callback")
        
        # Cache
        self.cache = {}
        self.cache_ttl = 5  # 5 seconds for live data
        
        # API clients (lazy initialization)
        self.quote_api = None
        self.history_api = None
        self.market_data_api = None
        self.order_api = None
        
        # WebSocket
        self.ws_client = None
        self.ws_connected = False
        
        # Instrument mapping (ISIN codes)
        self.instrument_map = self._initialize_instrument_map()
        
        # Health status
        self.last_successful_call = None
        self.consecutive_failures = 0
        self.total_calls = 0
        self.successful_calls = 0
        
        logger.info("🚀 Upstox Service initialized")
    
    def _initialize_instrument_map(self) -> Dict[str, str]:
        """
        Initialize instrument mapping (Symbol -> Upstox Instrument Key)
        ISIN format: NSE_EQ|ISIN_CODE
        """
        return {
            # Popular stocks
            "RELIANCE": "NSE_EQ|INE002A01018",
            "TCS": "NSE_EQ|INE467B01029",
            "HDFCBANK": "NSE_EQ|INE040A01034",
            "INFY": "NSE_EQ|INE009A01021",
            "HINDUNILVR": "NSE_EQ|INE030A01027",
            "ICICIBANK": "NSE_EQ|INE090A01021",
            "KOTAKBANK": "NSE_EQ|INE237A01028",
            "BHARTIARTL": "NSE_EQ|INE397D01024",
            "ITC": "NSE_EQ|INE154A01025",
            "SBIN": "NSE_EQ|INE062A01020",
            "WIPRO": "NSE_EQ|INE075A01022",
            "AXISBANK": "NSE_EQ|INE238A01034",
            "ASIANPAINT": "NSE_EQ|INE021A01026",
            "MARUTI": "NSE_EQ|INE585B01010",
            "TITAN": "NSE_EQ|INE280A01028",
            "NESTLEIND": "NSE_EQ|INE239A01016",
            "SUNPHARMA": "NSE_EQ|INE044A01036",
            "ULTRACEMCO": "NSE_EQ|INE481G01011",
            "POWERGRID": "NSE_EQ|INE752E01010",
            "NTPC": "NSE_EQ|INE733E01010",
            "LT": "NSE_EQ|INE018A01030",
            "ONGC": "NSE_EQ|INE213A01029",
            "TECHM": "NSE_EQ|INE669C01036",
            "BAJFINANCE": "NSE_EQ|INE296A01024",
            "HCLTECH": "NSE_EQ|INE860A01027",
            "M&M": "NSE_EQ|INE101A01026",
            "TATASTEEL": "NSE_EQ|INE081A01020",
            "TATAMOTORS": "NSE_EQ|INE155A01022",
            "JSWSTEEL": "NSE_EQ|INE019A01038",
            "ADANIPORTS": "NSE_EQ|INE742F01042",
            
            # Indices
            "NIFTY50": "NSE_INDEX|Nifty 50",
            "NIFTYBANK": "NSE_INDEX|Nifty Bank",
            "NIFTYIT": "NSE_INDEX|Nifty IT",
        }
    
    def _lazy_init_clients(self):
        """Lazy initialization of Upstox API clients"""
        if not self.access_token:
            logger.warning("⚠️  Upstox access token not configured")
            return False
        
        try:
            # Import upstox client only when needed
            from upstox_client import Configuration, ApiClient, MarketQuoteApi, HistoryApi, MarketDataApi
            
            configuration = Configuration()
            configuration.access_token = self.access_token
            
            api_client = ApiClient(configuration)
            self.quote_api = MarketQuoteApi(api_client)
            self.history_api = HistoryApi(api_client)
            self.market_data_api = MarketDataApi(api_client)
            
            logger.info("✅ Upstox API clients initialized")
            return True
            
        except ImportError:
            logger.error("❌ upstox-client not installed. Run: pip install upstox-client")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Upstox clients: {e}")
            return False
    
    def _get_instrument_key(self, symbol: str, exchange: str = "NSE") -> str:
        """
        Convert symbol to Upstox instrument key
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: Exchange name (e.g., "NSE", "BSE")
        
        Returns:
            Upstox instrument key (e.g., "NSE_EQ|INE002A01018")
        """
        # Try to get from mapping
        instrument_key = self.instrument_map.get(symbol.upper())
        
        if instrument_key:
            return instrument_key
        
        # Fallback: construct key (this might not work for all stocks)
        if exchange == "BSE":
            return f"BSE_EQ|{symbol}"
        else:
            return f"NSE_EQ|{symbol}"
    
    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """
        Get live quote for symbol from Upstox
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: Exchange name (e.g., "NSE", "BSE")
        
        Returns:
            Quote data dictionary with standardized format
        """
        try:
            self.total_calls += 1
            cache_key = f"quote_{symbol}_{exchange}"
            
            # Check cache
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    logger.debug(f"📦 Cache hit for {symbol}")
                    return cached_data
            
            # Initialize clients if needed
            if not self.quote_api:
                if not self._lazy_init_clients():
                    raise Exception("Upstox API clients not initialized")
            
            # Get instrument key
            instrument_key = self._get_instrument_key(symbol, exchange)
            
            # Fetch quote from Upstox
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.quote_api.get_full_market_quote(instrument_key, "1.0")
                )
            except Exception as api_error:
                # Handle Upstox API errors
                logger.error(f"❌ Upstox API error for {symbol}: {api_error}")
                self.consecutive_failures += 1
                raise Exception(f"Upstox API error: {api_error}")
            
            if not response or not hasattr(response, 'data') or not response.data:
                raise Exception("No data in Upstox response")
            
            # Extract quote data
            quote_data = response.data.get(instrument_key, {})
            
            if not quote_data:
                raise Exception(f"No quote data for instrument key: {instrument_key}")
            
            ohlc = quote_data.get('ohlc', {})
            last_price = float(quote_data.get('last_price', 0))
            
            # If last_price is 0, try to get from close
            if last_price == 0:
                last_price = float(ohlc.get('close', 0))
            
            previous_close = float(ohlc.get('close', 0))
            
            # Calculate change
            change = last_price - previous_close if previous_close > 0 else 0
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            # Format to match our standard structure
            formatted_quote = {
                "symbol": symbol,
                "exchange": exchange,
                "last_price": round(last_price, 2),
                "open": float(ohlc.get('open', last_price)),
                "high": float(ohlc.get('high', last_price)),
                "low": float(ohlc.get('low', last_price)),
                "close": float(ohlc.get('close', last_price)),
                "previous_close": previous_close,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": int(quote_data.get('volume', 0)),
                "currency": "INR",
                "currency_symbol": "₹",
                "formatted_price": f"₹{last_price:,.2f}",
                "formatted_change": f"₹{change:+,.2f}",
                "formatted_change_percent": f"{change_percent:+.2f}%",
                "timestamp": datetime.now().isoformat(),
                "data_source": "UPSTOX_LIVE",
                "reliability_level": "real_time",
                "instrument_key": instrument_key
            }
            
            # Cache result
            self.cache[cache_key] = (formatted_quote, datetime.now().timestamp())
            
            # Update health status
            self.last_successful_call = datetime.now()
            self.consecutive_failures = 0
            self.successful_calls += 1
            
            logger.info(f"✅ Upstox quote: {symbol} = ₹{formatted_quote['last_price']}")
            
            return formatted_quote
            
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"❌ Error getting Upstox quote for {symbol}: {e}")
            
            # Return error response
            return {
                "symbol": symbol,
                "exchange": exchange,
                "error": str(e),
                "data_source": "UPSTOX_ERROR",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_historical_data(
        self,
        symbol: str,
        interval: str = "1day",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        exchange: str = "NSE"
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV data from Upstox
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1minute, 30minute, day, week, month)
            from_date: Start date
            to_date: End date
            exchange: Exchange name
        
        Returns:
            List of OHLCV candles
        """
        try:
            # Initialize clients if needed
            if not self.history_api:
                if not self._lazy_init_clients():
                    raise Exception("Upstox API clients not initialized")
            
            instrument_key = self._get_instrument_key(symbol, exchange)
            
            # Default date range if not provided
            if not to_date:
                to_date = datetime.now()
            if not from_date:
                from_date = to_date - timedelta(days=365)
            
            # Fetch historical data
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.history_api.get_historical_candle_data(
                        instrument_key=instrument_key,
                        interval=interval,
                        to_date=to_date.strftime("%Y-%m-%d"),
                        from_date=from_date.strftime("%Y-%m-%d")
                    )
                )
            except Exception as api_error:
                logger.error(f"❌ Upstox historical data error for {symbol}: {api_error}")
                raise Exception(f"Upstox API error: {api_error}")
            
            if not response or not hasattr(response, 'data') or not response.data:
                return []
            
            # Format candles
            candles = []
            candle_data = response.data.get('candles', [])
            
            for candle in candle_data:
                if len(candle) >= 5:
                    candles.append({
                        "time": candle[0],  # Timestamp
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": int(candle[5]) if len(candle) > 5 else 0,
                        "date": datetime.fromtimestamp(candle[0] / 1000).strftime("%Y-%m-%d") if isinstance(candle[0], (int, float)) else candle[0]
                    })
            
            logger.info(f"✅ Upstox historical data: {symbol} ({len(candles)} candles)")
            
            return candles
            
        except Exception as e:
            logger.error(f"❌ Error getting historical data for {symbol}: {e}")
            return []
    
    async def get_multiple_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols efficiently
        
        Args:
            symbols: List of stock symbols
            exchange: Exchange name
        
        Returns:
            Dictionary mapping symbol to quote data
        """
        try:
            # Process symbols in parallel
            tasks = [self.get_quote(symbol, exchange) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            quotes = {}
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error getting quote for {symbols[i]}: {result}")
                    quotes[symbols[i]] = {
                        "symbol": symbols[i],
                        "error": str(result),
                        "data_source": "UPSTOX_ERROR"
                    }
                else:
                    quotes[symbols[i]] = result
            
            return quotes
            
        except Exception as e:
            logger.error(f"❌ Error getting multiple quotes: {e}")
            return {}
    
    async def connect_websocket(self, symbols: List[str], callback):
        """
        Connect to Upstox WebSocket for real-time updates
        
        Args:
            symbols: List of symbols to subscribe
            callback: Callback function for price updates
        """
        try:
            logger.info(f"🔌 Connecting to Upstox WebSocket for {len(symbols)} symbols")
            
            # WebSocket implementation would go here
            # This requires additional Upstox WebSocket API setup
            
            # For now, mark as not implemented
            logger.warning("⚠️  Upstox WebSocket not yet implemented")
            self.ws_connected = False
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.ws_connected = False
    
    async def disconnect_websocket(self):
        """Disconnect WebSocket"""
        try:
            if self.ws_client:
                await self.ws_client.close()
            self.ws_connected = False
            logger.info("🔌 WebSocket disconnected")
        except Exception as e:
            logger.error(f"❌ Error disconnecting WebSocket: {e}")
    
    def is_healthy(self) -> bool:
        """
        Check if Upstox service is healthy
        
        Returns:
            True if service is configured and working, False otherwise
        """
        # Check if credentials are configured
        if not self.api_key or not self.access_token:
            return False
        
        # Check if too many consecutive failures
        if self.consecutive_failures >= 5:
            return False
        
        # Check if last successful call was recent (within 5 minutes)
        if self.last_successful_call:
            time_since_success = datetime.now() - self.last_successful_call
            if time_since_success > timedelta(minutes=5) and self.total_calls > 0:
                return False
        
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status of Upstox service"""
        success_rate = (self.successful_calls / self.total_calls * 100) if self.total_calls > 0 else 0
        
        return {
            "is_healthy": self.is_healthy(),
            "configured": bool(self.api_key and self.access_token),
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "success_rate": round(success_rate, 2),
            "consecutive_failures": self.consecutive_failures,
            "last_successful_call": self.last_successful_call.isoformat() if self.last_successful_call else None,
            "ws_connected": self.ws_connected,
            "supported_symbols": len(self.instrument_map),
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear the quote cache"""
        self.cache.clear()
        logger.info("🗑️  Upstox cache cleared")
    
    def add_instrument_mapping(self, symbol: str, isin_code: str, exchange: str = "NSE"):
        """
        Add custom instrument mapping
        
        Args:
            symbol: Stock symbol
            isin_code: ISIN code
            exchange: Exchange (NSE/BSE)
        """
        instrument_key = f"{exchange}_EQ|{isin_code}"
        self.instrument_map[symbol.upper()] = instrument_key
        logger.info(f"✅ Added instrument mapping: {symbol} -> {instrument_key}")

# Create singleton instance
upstox_service = UpstoxService()

