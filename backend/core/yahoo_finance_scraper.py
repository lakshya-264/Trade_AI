"""
Yahoo Finance API Scraper as Alternative
Since Investing.com is also blocking us, let's use Yahoo Finance
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class YahooFinanceScraper:
    def __init__(self):
        self.session = None
        self.is_initialized = False
        
        # Yahoo Finance API endpoints
        self.base_url = "https://query1.finance.yahoo.com"
        self.quote_url = f"{self.base_url}/v8/finance/chart"
        
        # NSE symbol mappings to Yahoo Finance format
        self.symbol_mappings = {
            # NIFTY 50 Stocks (Complete List)
            "RELIANCE": "RELIANCE.NS",
            "TCS": "TCS.NS", 
            "INFY": "INFY.NS",
            "HDFCBANK": "HDFCBANK.NS",
            "HDFC": "HDFCBANK.NS",
            "ICICIBANK": "ICICIBANK.NS",
            "SBIN": "SBIN.NS",
            "BHARTIARTL": "BHARTIARTL.NS",
            "ITC": "ITC.NS",
            "KOTAKBANK": "KOTAKBANK.NS",
            "LT": "LT.NS",
            "ASIANPAINT": "ASIANPAINT.NS",
            "MARUTI": "MARUTI.NS",
            "AXISBANK": "AXISBANK.NS",
            "NESTLEIND": "NESTLEIND.NS",
            "ULTRACEMCO": "ULTRACEMCO.NS",
            "TITAN": "TITAN.NS",
            "POWERGRID": "POWERGRID.NS",
            "NTPC": "NTPC.NS",
            "ONGC": "ONGC.NS",
            "COALINDIA": "COALINDIA.NS",
            "HINDUNILVR": "HINDUNILVR.NS",
            "BAJFINANCE": "BAJFINANCE.NS",
            "SUNPHARMA": "SUNPHARMA.NS",
            "TECHM": "TECHM.NS",
            "WIPRO": "WIPRO.NS",
            "HCLTECH": "HCLTECH.NS",
            "BAJAJFINSV": "BAJAJFINSV.NS",
            "DRREDDY": "DRREDDY.NS",
            "TATAMOTORS": "TATAMOTORS.NS",
            "BRITANNIA": "BRITANNIA.NS",
            "EICHERMOT": "EICHERMOT.NS",
            "SHREECEM": "SHREECEM.NS",
            "JSWSTEEL": "JSWSTEEL.NS",
            "TATASTEEL": "TATASTEEL.NS",
            "INDUSINDBK": "INDUSINDBK.NS",
            "GRASIM": "GRASIM.NS",
            "CIPLA": "CIPLA.NS",
            "TATACONSUM": "TATACONSUM.NS",
            "APOLLOHOSP": "APOLLOHOSP.NS",
            "ADANIPORTS": "ADANIPORTS.NS",
            "BPCL": "BPCL.NS",
            "HEROMOTOCO": "HEROMOTOCO.NS",
            "DIVISLAB": "DIVISLAB.NS",
            "UPL": "UPL.NS",
            "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
            "TATAPOWER": "TATAPOWER.NS",
            "ADANIENT": "ADANIENT.NS",
            "SBILIFE": "SBILIFE.NS",
            "HINDALCO": "HINDALCO.NS",
            "HDFCLIFE": "HDFCLIFE.NS",
            "M&M": "M&M.NS",
            "INDIGO": "INDIGO.NS",
            "VEDL": "VEDL.NS",
            "ADANIGREEN": "ADANIGREEN.NS",
            "ADANITRANS": "ADANITRANS.NS",
            
            # Market Indices (Yahoo Finance format)
            "NIFTY": "^NSEI",
            "NIFTY50": "^NSEI",
            "NIFTY_50": "^NSEI",
            "^NSEI": "^NSEI",
            "SENSEX": "^BSESN",
            "^BSESN": "^BSESN",
            "NIFTYBANK": "^NSEBANK",
            "NIFTY_BANK": "^NSEBANK",
            "BANKNIFTY": "^NSEBANK",
            "^NSEBANK": "^NSEBANK",
            "NIFTYIT": "^CNXIT",
            "NIFTY_IT": "^CNXIT",
            "^CNXIT": "^CNXIT",
            # Additional NIFTY Indexes
            # Note: These may not be available on Yahoo Finance - will use fallback
            "NIFTYMIDCAP50": "^NSEMDCP50",  # May not exist, fallback will handle
            "NIFTY_MIDCAP_50": "^NSEMDCP50",
            "NIFTYMIDCAP": "^NSEMDCP50",
            "^NSEMDCP50": "^NSEMDCP50",
            "NIFTYFIN": "^CNXFIN",  # May not exist, fallback will handle
            "NIFTY_FIN": "^CNXFIN",
            "NIFTYFINANCIALSERVICES": "^CNXFIN",
            "NIFTY_FINANCIAL_SERVICES": "^CNXFIN",
            "^CNXFIN": "^CNXFIN",
            # BSE Indexes
            "BANKEX": "^BSE-BANKEX",  # May not exist, fallback will handle
            "^BSE-BANKEX": "^BSE-BANKEX",
        }
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://finance.yahoo.com/',
            'Origin': 'https://finance.yahoo.com'
        }
    
    async def _ensure_initialized(self):
        """Initialize aiohttp session"""
        if not self.is_initialized:
            try:
                connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
                timeout = aiohttp.ClientTimeout(total=30)
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=self.headers
                )
                self.is_initialized = True
                logger.info("✅ Yahoo Finance scraper initialized")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Yahoo Finance scraper: {e}")
                return False
        return True
    
    def _get_yahoo_symbol(self, symbol: str) -> str:
        """Convert NSE/BSE symbol to Yahoo Finance symbol"""
        # Normalize symbol: uppercase and strip whitespace
        symbol = symbol.upper().strip()
        
        # Check if already in correct format
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol
        
        # Check if it's a commodity/futures symbol (contains =)
        # Yahoo Finance uses =F for futures, =X for currencies, etc.
        if '=' in symbol:
            return symbol
        
        # Check our mappings first (case-insensitive)
        if symbol in self.symbol_mappings:
            return self.symbol_mappings[symbol]
        
        # For any NSE stock, try .NS suffix (default)
        return f"{symbol}.NS"
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock quote from Yahoo Finance"""
        try:
            if not await self._ensure_initialized():
                return None
            
            logger.info(f"📈 Fetching Yahoo Finance data for {symbol}...")
            
            # Convert symbol to Yahoo format
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Construct API URL
            api_url = f"{self.quote_url}/{yahoo_symbol}"
            
            # Add parameters
            params = {
                'range': '1d',
                'interval': '1m',
                'includePrePost': 'true',
                'useYfid': 'true',
                'corsDomain': 'finance.yahoo.com'
            }
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(0.5)
            
            # Add timeout to prevent hanging
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            
            async with self.session.get(api_url, params=params, timeout=timeout) as response:
                logger.info(f"Yahoo Finance response status for {symbol}: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract price data from Yahoo Finance response
                    quote_data = self._extract_yahoo_data(data, symbol)
                    
                    if quote_data:
                        logger.info(f"✅ Yahoo Finance success for {symbol}: ₹{quote_data['last_price']}")
                        return quote_data
                    else:
                        logger.warning(f"Could not extract price data for {symbol}")
                        return None
                        
                elif response.status == 429:
                    logger.warning(f"HTTP 429 for {symbol} - Rate limited")
                    await asyncio.sleep(5)
                    return None
                elif response.status == 404:
                    # Some indexes may not be available on Yahoo Finance
                    # This is expected for certain NSE/BSE indexes
                    # Fallback system will handle with estimated/mock data
                    known_unavailable_indexes = ['NIFTYMIDCAP50', 'NIFTYFIN', 'BANKEX', 'NIFTY_MIDCAP_50', 'NIFTY_FIN', 'NIFTYFINANCIALSERVICES', 'NSEMDCP50', 'CNXFIN', 'BSE-BANKEX']
                    symbol_upper = symbol.upper()
                    if any(idx in symbol_upper for idx in known_unavailable_indexes):
                        # Use DEBUG level instead of ERROR for expected failures
                        logger.debug(f"Index {symbol} not available on Yahoo Finance (expected), fallback system will provide data")
                    else:
                        # Log warning for symbols not found (excluding known unavailable indexes)
                        logger.warning(f"HTTP 404 for {symbol} - Symbol not found on Yahoo Finance")
                    return None
                else:
                    # Log warning for non-404 HTTP errors
                    logger.warning(f"HTTP {response.status} for {symbol} - Will use fallback data")
                    return None
                    
        except Exception as e:
            # Don't log errors for indexes that are expected to fail
            known_unavailable_indexes = ['NIFTYMIDCAP50', 'NIFTYFIN', 'BANKEX', 'NIFTY_MIDCAP_50', 'NIFTY_FIN', 'NIFTYFINANCIALSERVICES', 'NSEMDCP50', 'CNXFIN', 'BSE-BANKEX']
            symbol_upper = symbol.upper()
            if any(idx in symbol_upper for idx in known_unavailable_indexes):
                logger.debug(f"Exception for {symbol} (expected - index not on Yahoo Finance): {e}")
            else:
                # Log error for unexpected failures (not known unavailable indexes)
                logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    def _extract_yahoo_data(self, data: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
        """Extract price data from Yahoo Finance API response"""
        try:
            # Check if we have chart data
            if 'chart' not in data or 'result' not in data['chart']:
                logger.warning("No chart data in Yahoo Finance response")
                return None
            
            result = data['chart']['result']
            if not result:
                logger.warning("Empty result in Yahoo Finance response")
                return None
            
            # Get the first result (most recent data)
            chart_data = result[0]
            
            # Extract meta information
            meta = chart_data.get('meta', {})
            if not meta:
                logger.warning("No meta data in Yahoo Finance response")
                return None
            
            # Extract price information
            # Note: After market close, Yahoo may not provide regularMarketPrice for some tickers.
            # In that case, fall back to previous close or last available candle close.
            market_state = meta.get('marketState') or meta.get('market_state')

            last_price = meta.get('regularMarketPrice', 0) or 0
            price_type = "regularMarketPrice" if last_price else None

            # First fallback: previous close fields in meta
            if not last_price:
                last_price = (
                    meta.get('previousClose')
                    or meta.get('regularMarketPreviousClose')
                    or meta.get('chartPreviousClose')
                    or 0
                )
                if last_price:
                    price_type = "previousClose"

            # Second fallback: last non-null candle close in the chart
            if not last_price:
                try:
                    quote_series = chart_data.get('indicators', {}).get('quote', [])
                    quote0 = quote_series[0] if quote_series else {}
                    closes = quote0.get('close', []) if isinstance(quote0, dict) else []
                    for v in reversed(closes or []):
                        if v is not None:
                            last_price = v
                            price_type = "lastCandleClose"
                            break
                except Exception:
                    pass

            if not last_price:
                logger.warning("No price data in Yahoo Finance response")
                return None
            
            # Extract other data
            previous_close = meta.get('previousClose', last_price)
            change = last_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            # Extract additional data
            high = meta.get('dayHigh', last_price)
            low = meta.get('dayLow', last_price)
            open_price = meta.get('regularMarketOpen', last_price)
            volume = meta.get('regularMarketVolume', 0)
            
            quote = self._format_quote_data(symbol, last_price, change, change_percent, high, low, open_price, volume)
            if market_state:
                quote["market_state"] = market_state
            if price_type:
                quote["price_type"] = price_type
            return quote
            
        except Exception as e:
            logger.error(f"Error extracting Yahoo Finance data: {e}")
            return None
    
    def _format_quote_data(self, symbol: str, last_price: float, change: float, change_percent: float, 
                          high: float, low: float, open_price: float, volume: int) -> Dict[str, Any]:
        """Format quote data in standard format"""
        # Check for stale data (same price for OHLC indicates stale data)
        is_stale_data = (high == low == open_price == last_price)
        
        return {
            "symbol": symbol,
            "last_price": round(last_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": volume,
            "high": round(high, 2),
            "low": round(low, 2),
            "open": round(open_price, 2),
            "previous_close": round(last_price - change, 2),
            "currency": "INR",
            "currency_symbol": "₹",
            "formatted_price": f"₹{last_price:,.2f}",
            "formatted_change": f"₹{change:+,.2f}",
            "formatted_change_percent": f"{change_percent:+.2f}%",
            "exchange": "NSE",
            "data_source": "YAHOO_FINANCE_API",
            "timestamp": datetime.now().isoformat(),
            "reliability_level": "NEAR_REAL_TIME" if is_stale_data else "REAL_TIME",
            "extraction_method": "yahoo_finance_api",
            "price_type": "regularMarketPrice",
            "is_stale": is_stale_data,
            "stale_warning": "Data appears to be stale (OHLC prices are identical)" if is_stale_data else None
        }
    
    async def get_historical_candles(
        self, 
        symbol: str, 
        interval: str = "1d", 
        range_period: str = "1mo"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical candlestick (OHLC) data from Yahoo Finance
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            interval: Candle interval (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
            range_period: Time range (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            List of candle dictionaries with OHLCV data
        """
        try:
            if not await self._ensure_initialized():
                return None
            
            logger.info(f"📊 Fetching historical candles for {symbol} ({interval}, {range_period})...")
            
            # Convert symbol to Yahoo format
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Construct API URL
            api_url = f"{self.quote_url}/{yahoo_symbol}"
            
            # Add parameters
            params = {
                'range': range_period,
                'interval': interval,
                'includePrePost': 'false',
                'useYfid': 'true',
                'corsDomain': 'finance.yahoo.com'
            }
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(0.5)
            
            # Add timeout
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with self.session.get(api_url, params=params, timeout=timeout) as response:
                logger.info(f"Yahoo Finance candles response status for {symbol}: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract candle data
                    candles = self._extract_candle_data(data, symbol)
                    
                    if candles:
                        logger.info(f"✅ Got {len(candles)} candles for {symbol}")
                        return candles
                    else:
                        logger.warning(f"Could not extract candle data for {symbol}")
                        return None
                        
                elif response.status == 429:
                    logger.warning(f"HTTP 429 for {symbol} - Rate limited")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.error(f"HTTP {response.status} for {symbol}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting candles for {symbol}: {e}")
            return None
    
    def _extract_candle_data(self, data: Dict[str, Any], symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Extract candle (OHLCV) data from Yahoo Finance API response"""
        try:
            # Check if we have chart data
            if 'chart' not in data or 'result' not in data['chart']:
                logger.warning("No chart data in Yahoo Finance response")
                return None
            
            result = data['chart']['result']
            if not result:
                logger.warning("Empty result in Yahoo Finance response")
                return None
            
            # Get the first result
            chart_data = result[0]
            
            # Extract timestamp and quote data
            timestamps = chart_data.get('timestamp', [])
            quote_data = chart_data.get('indicators', {}).get('quote', [])
            
            if not timestamps or not quote_data:
                logger.warning("No timestamps or quote data")
                return None
            
            # Get OHLCV arrays
            quote = quote_data[0] if quote_data else {}
            opens = quote.get('open', [])
            highs = quote.get('high', [])
            lows = quote.get('low', [])
            closes = quote.get('close', [])
            volumes = quote.get('volume', [])
            
            # Build candles list
            candles = []
            for i in range(len(timestamps)):
                # Skip if any value is None
                if (i >= len(opens) or i >= len(highs) or i >= len(lows) or 
                    i >= len(closes) or i >= len(volumes)):
                    continue
                
                # Skip if values are None
                if (opens[i] is None or highs[i] is None or lows[i] is None or 
                    closes[i] is None or volumes[i] is None):
                    continue
                
                candle = {
                    "time": timestamps[i],  # Unix timestamp
                    "timestamp": datetime.fromtimestamp(timestamps[i]).isoformat(),
                    "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d %H:%M:%S"),
                    "open": round(float(opens[i]), 2),
                    "high": round(float(highs[i]), 2),
                    "low": round(float(lows[i]), 2),
                    "close": round(float(closes[i]), 2),
                    "volume": int(volumes[i]),
                    "symbol": symbol
                }
                candles.append(candle)
            
            return candles
            
        except Exception as e:
            logger.error(f"Error extracting candle data: {e}")
            return None
    
    async def get_index_constituents(self, index_symbol: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get index constituents from Yahoo Finance
        For indexes available on Yahoo Finance: NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT, NIFTY PSU BANK, NIFTY AUTO
        """
        try:
            # Map index symbols to Yahoo Finance tickers
            index_ticker_map = {
                "NIFTY_50": "^NSEI",
                "NIFTY50": "^NSEI",
                "NIFTY": "^NSEI",
                "SENSEX": "^BSESN",
                "NIFTYBANK": "^NSEBANK",
                "NIFTY_BANK": "^NSEBANK",
                "BANKNIFTY": "^NSEBANK",
                "NIFTYIT": "^CNXIT",
                "NIFTY_IT": "^CNXIT",
                "NIFTYPSUBANK": "^CNXPSU",
                "NIFTY_PSU_BANK": "^CNXPSU",
                "NIFTYAUTO": "^CNXAUTO",
                "NIFTY_AUTO": "^CNXAUTO",
            }
            
            yahoo_ticker = index_ticker_map.get(index_symbol.upper())
            if not yahoo_ticker:
                logger.warning(f"Index {index_symbol} not mapped for Yahoo Finance constituents")
                return None
            
            # Try using yfinance library if available
            try:
                import yfinance as yf
                ticker = yf.Ticker(yahoo_ticker)
                info = ticker.info
                
                # Some indexes have constituents in the info
                if 'constituents' in info:
                    constituents = info['constituents']
                    return [{"symbol": sym.replace('.NS', ''), "weight": None} for sym in constituents]
            except ImportError:
                logger.debug("yfinance not available, will try static lists")
            except Exception as e:
                logger.debug(f"yfinance failed for {index_symbol}: {e}, using static lists")
            
            # Fallback: Use static lists for known indexes
            return self._get_static_constituents(index_symbol)
            
        except Exception as e:
            logger.error(f"Error getting index constituents for {index_symbol}: {e}")
            return None
    
    def _get_static_constituents(self, index_symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Get static constituents list for indexes (fallback)"""
        static_constituents = {
            "NIFTY_50": [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", 
                "ITC", "BHARTIARTL", "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", 
                "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID", "NTPC", "TECHM", 
                "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA", 
                "EICHERMOT", "SHREECEM", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "COALINDIA", 
                "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP", "ADANIPORTS", "BPCL", 
                "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", "ADANIENT", "SBILIFE", 
                "HINDALCO", "HDFCLIFE", "M&M", "INDIGO"
            ],
            "SENSEX": [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "ITC", 
                "BHARTIARTL", "SBIN", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", 
                "ULTRACEMCO", "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", 
                "TATAMOTORS", "NESTLEIND", "POWERGRID", "ONGC", "TATASTEEL", "JSWSTEEL", "HINDALCO"
            ],
            "NIFTYBANK": [
                "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK", 
                "FEDERALBNK", "PNB", "BANKBARODA", "IDFCFIRSTB", "AUBANK", "BANDHANBNK"
            ],
            "NIFTY_IT": [
                "TCS", "INFY", "HCLTECH", "TECHM", "WIPRO", "LTIM", "MPHASIS", "PERSISTENT", 
                "COFORGE", "ZENSAR", "MINDTREE", "LTI"
            ],
            "NIFTY_PSU_BANK": [
                "SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK", "INDIANB", "CENTRALBK", 
                "IOB", "UCOBANK", "BANKINDIA"
            ],
            "NIFTY_AUTO": [
                "MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", 
                "ASHOKLEY", "TVSMOTOR", "FORCEMOT", "BALKRISIND"
            ]
        }
        
        key = index_symbol.upper()
        # Try exact match first
        if key in static_constituents:
            return [{"symbol": sym, "weight": None} for sym in static_constituents[key]]
        
        # Try variations
        variations = {
            "NIFTY50": "NIFTY_50",
            "NIFTY": "NIFTY_50",
            "NIFTY_BANK": "NIFTYBANK",
            "BANKNIFTY": "NIFTYBANK",
            "NIFTYIT": "NIFTY_IT",
            "NIFTYPSUBANK": "NIFTY_PSU_BANK",
            "NIFTYAUTO": "NIFTY_AUTO"
        }
        
        if key in variations:
            mapped_key = variations[key]
            if mapped_key in static_constituents:
                return [{"symbol": sym, "weight": None} for sym in static_constituents[mapped_key]]
        
        return None
    
    async def close(self):
        """Close session and cleanup"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_initialized = False
            logger.info("Yahoo Finance scraper closed")
        except Exception as e:
            logger.error(f"Error closing Yahoo Finance scraper: {e}")

# Global instance
yahoo_finance_scraper = YahooFinanceScraper()

# Cleanup function
async def cleanup_yahoo_finance_scraper():
    """Cleanup Yahoo Finance scraper resources"""
    await yahoo_finance_scraper.close()
