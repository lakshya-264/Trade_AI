"""
Data Fetcher Service
Fetches historical candle data for backtesting and analysis
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Import from shared utility
from utils.symbol_normalizer import normalize_symbol_for_yahoo

def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol using shared utility"""
    return normalize_symbol_for_yahoo(symbol)

async def fetch_historical_data(
    symbol: str,
    timeframe: str = "1d",
    days: int = 180
) -> Optional[List[Dict]]:
    """
    Fetch historical candle data
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE") or Index (e.g., "NIFTY")
        timeframe: Candle timeframe ("1d", "1h", etc.)
        days: Number of days of historical data
    
    Returns:
        List of candle dictionaries with time, open, high, low, close, volume
    """
    try:
        # Normalize symbol (handle indices vs stocks vs commodities)
        # For commodities (ending with =F), don't normalize - use as-is
        if '=' in symbol:
            normalized_symbol = symbol
            logger.info(f"Commodity symbol detected, using as-is: {symbol}")
        else:
            normalized_symbol = _normalize_symbol(symbol)
        logger.info(f"Normalized symbol: {symbol} -> {normalized_symbol}")
        
        # Calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Map timeframe to yfinance interval
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "1d": "1d",
            "1w": "1wk",
            "1M": "1mo"
        }
        
        yf_interval = interval_map.get(timeframe, "1d")
        logger.info(f"📊 Fetching data: symbol={normalized_symbol}, requested_timeframe={timeframe}, yf_interval={yf_interval}, days={days}")
        
        # Upstox API integration removed - using yfinance only
        # if yf_interval in ["1m", "5m", "15m", "30m", "1h"]:
        #     candles = await _try_upstox_intraday_data(symbol, timeframe, days)
        #     if candles:
        #         logger.info(f"✅ Fetched {len(candles)} intraday candles from Upstox for {symbol}")
        #         return candles
        
        # Fallback to yfinance for daily/weekly/monthly data
        # Fetch data with better error handling
        ticker = yf.Ticker(normalized_symbol)
        
        # Note: yfinance has limitations for intraday data on Indian stocks
        # Intraday intervals (1m, 5m, 15m, 30m, 1h) may not work for .NS symbols
        actual_interval_used = yf_interval
        df = pd.DataFrame()
        
        try:
            # Fetch historical data first
            df = ticker.history(start=start_date, end=end_date, interval=yf_interval)
            
            # Get current price from the most recent data
            if not df.empty:
                current_price = df['Close'].iloc[-1]
                logger.info(f"Current price for {normalized_symbol} from historical data: {current_price}")
            else:
                # Fallback to ticker.info if no historical data
                info = ticker.info
                current_price = info.get('regularMarketPrice', 0)
                if current_price <= 0:
                    logger.warning(f"Invalid current price for {normalized_symbol}: {current_price}")
                    # Try alternative price sources
                    current_price = info.get('previousClose', 0)
                
                logger.info(f"Current price for {normalized_symbol} from ticker.info: {current_price}")
                # Try to get historical data as fallback
                df = ticker.history(start=start_date, end=end_date, interval=yf_interval)
            
            # Check if data is valid
            if df.empty:
                if yf_interval in ["1m", "5m", "15m", "30m", "1h"]:
                    # Empty result for intraday - try daily as fallback
                    logger.warning(f"Empty result for intraday interval {yf_interval} for {normalized_symbol}, trying daily fallback")
                    df = ticker.history(start=start_date, end=end_date, interval="1d")
                    if not df.empty:
                        actual_interval_used = "1d"
                        logger.info(f"⚠️ Using daily data as fallback for {normalized_symbol} (requested {yf_interval}, got {actual_interval_used})")
                        # Update current price from daily data
                        current_price = df['Close'].iloc[-1]
                        logger.info(f"Updated current price from daily data: {current_price}")
                else:
                    logger.warning(f"No data found for {normalized_symbol} with interval {yf_interval}")
                    return None
            else:
                # Validate the data has realistic prices
                latest_close = df['Close'].iloc[-1]
                if latest_close <= 0:
                    logger.warning(f"Invalid closing price in data for {normalized_symbol}: {latest_close}")
                    return None
                
                # Update current price from historical data
                current_price = latest_close
                logger.info(f"Updated current price from historical data: {current_price}")
                logger.info(f"Valid data received for {normalized_symbol}, price range: {df['Close'].min():.2f} - {df['Close'].max():.2f}")
                
        except Exception as e:
            # If intraday data fails, try daily data as fallback for intraday timeframes
            if yf_interval in ["1m", "5m", "15m", "30m", "1h"]:
                logger.warning(f"Intraday data ({yf_interval}) not available for {normalized_symbol} via yfinance. This is a known limitation for Indian stocks/indices. Error: {e}")
                # Try daily data as fallback
                try:
                    df = ticker.history(start=start_date, end=end_date, interval="1d")
                    if not df.empty:
                        actual_interval_used = "1d"
                        logger.info(f"⚠️ Using daily data as fallback for {normalized_symbol} (requested {yf_interval}, got {actual_interval_used})")
                        
                        # Validate daily data
                        if df['Close'].iloc[-1] <= 0:
                            logger.warning(f"Invalid daily data for {normalized_symbol}")
                            df = pd.DataFrame()
                    else:
                        logger.info(f"Valid daily data received for {normalized_symbol}, price range: {df['Close'].min():.2f} - {df['Close'].max():.2f}")
                except Exception as fallback_error:
                    logger.error(f"Fallback to daily data also failed: {fallback_error}")
                    df = pd.DataFrame()
            else:
                logger.error(f"Failed to fetch data for {normalized_symbol} with interval {yf_interval}: {e}")
                df = pd.DataFrame()
        
        if df.empty:
            # For indices, try alternative symbols
            if normalized_symbol.startswith("^"):
                logger.warning(f"No data found for {normalized_symbol} (requested interval: {yf_interval}, actual: {actual_interval_used})")
                # Try without the ^ prefix as fallback
                alt_symbol = normalized_symbol[1:]
                try:
                    alt_ticker = yf.Ticker(alt_symbol)
                    df = alt_ticker.history(start=start_date, end=end_date, interval=yf_interval)
                    if df.empty:
                        logger.warning(f"Alternative symbol {alt_symbol} also returned no data")
                        return None
                    logger.info(f"Using alternative symbol {alt_symbol} for {normalized_symbol}")
                except Exception as e:
                    logger.debug(f"Alternative symbol {alt_symbol} failed: {e}")
                    return None
            else:
                logger.warning(f"No data found for {normalized_symbol} (requested interval: {yf_interval}, actual: {actual_interval_used})")
                return None
        
        # Convert to list of dicts with validation
        candles = []
        for index, row in df.iterrows():
            # Validate each candle data point
            try:
                open_price = float(row['Open'])
                high_price = float(row['High'])
                low_price = float(row['Low'])
                close_price = float(row['Close'])
                volume = int(row['Volume'])
                
                # Basic validation
                if open_price <= 0 or high_price <= 0 or low_price <= 0 or close_price <= 0:
                    logger.warning(f"Invalid price data for {normalized_symbol} at {index}: O={open_price}, H={high_price}, L={low_price}, C={close_price}")
                    continue
                
                # Check if high >= low and low <= open and close
                if not (low_price <= high_price):
                    logger.warning(f"Invalid price relationship for {normalized_symbol} at {index}: Low ({low_price}) > High ({high_price})")
                    continue
                
                if not (low_price <= close_price <= high_price):
                    logger.warning(f"Close price outside range for {normalized_symbol} at {index}: {close_price} not between Low ({low_price}) and High ({high_price})")
                    continue
                
                # Volume validation (can be 0 for some data sources)
                if volume < 0:
                    volume = 0
                
                candle = {
                    'time': int(index.timestamp()),
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                }
                
                candles.append(candle)
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing candle data for {normalized_symbol} at {index}: {e}")
                continue
        
        if not candles:
            logger.warning(f"No valid candles found for {normalized_symbol}")
            return None
        
        logger.info(f"✅ Fetched {len(candles)} valid candles for {normalized_symbol} (original: {symbol}, requested: {timeframe}, actual: {actual_interval_used})")
        
        # Log price range for verification
        if candles:
            prices = [c['close'] for c in candles]
            logger.info(f"Price range for {normalized_symbol}: {min(prices):.2f} - {max(prices):.2f}")
        
        return candles
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

async def get_current_price(symbol: str) -> Dict:
    """Get current price directly from Yahoo Finance"""
    try:
        # Normalize symbol for Yahoo Finance
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            normalized_symbol = f"{symbol}.NS"
        else:
            normalized_symbol = symbol
        
        ticker = yf.Ticker(normalized_symbol)
        
        # Get current price info
        info = ticker.info
        
        # Try multiple price sources
        current_price = info.get('regularMarketPrice', 0)
        if current_price <= 0:
            current_price = info.get('currentPrice', 0)
        if current_price <= 0:
            current_price = info.get('previousClose', 0)
        
        # Get previous close for change calculation
        previous_close = info.get('previousClose', current_price)
        if previous_close <= 0:
            previous_close = current_price
        
        # Calculate change
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close > 0 else 0
        
        # Get volume
        volume = info.get('regularMarketVolume', 0)
        
        if current_price > 0:
            logger.info(f"Current price for {symbol} from ticker.info: {current_price}")
            return {
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'YAHOO_FINANCE_CURRENT',
                'currency': 'INR',
                'market_state': info.get('marketState', 'CLOSED')
            }
        else:
            logger.warning(f"Invalid current price for {symbol}: {current_price}")
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
            
    except Exception as e:
        logger.error(f"Error getting current price for {symbol}: {e}")
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

