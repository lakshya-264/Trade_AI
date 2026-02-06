"""
Real-time data API routes
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple, Any
import time
import asyncio
import json
from datetime import datetime, timedelta

from core.database import get_db, MarketData
from core.data_service import data_service
from core.nse_api import NSEAPI
from core.websocket_manager import WebSocketManager
from core.price_history_utils import repair_candles
from core.cache_service import cache_service, get_cache_key
from core.api_utils import (
    api_response, 
    input_validator, 
    api_endpoint, 
    validate_and_sanitize_inputs,
    handle_api_error,
    create_error_response
)

router = APIRouter()

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Quote cache with shorter TTL for real-time data
_quote_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/quote/{symbol}")
async def get_quote(symbol: str, exchange: str = "NSE", ttl_seconds: int = 5):
    """Get live quote for a symbol with intelligent fallback: NSE → Angel One → Yahoo → Mock
    Cached for 5 seconds by default to reduce API calls while keeping data fresh.
    """
    try:
        # Simple validation - just clean the symbol
        original_symbol = symbol.strip().upper()
        
        # Check cache first
        cache_key = get_cache_key("quote", original_symbol, exchange)
        now = datetime.utcnow()
        cached = _quote_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]
        
        # Normalize NIFTY symbols for better compatibility
        # NIFTY -> ^NSEI for Yahoo Finance compatibility
        normalized_symbol = original_symbol
        if normalized_symbol in ["NIFTY", "NIFTY50", "NIFTY_50"]:
            # Try with ^NSEI first, but keep original for data_service fallback
            normalized_symbol = "^NSEI"
        elif normalized_symbol == "NIFTY 50":
            normalized_symbol = "^NSEI"
        
        # Try with normalized symbol first, then fallback to original
        quote_data = await data_service.get_quote(normalized_symbol, exchange)
        
        # Check if quote_data is valid (has last_price > 0 or is a valid error response)
        is_valid_quote = (
            quote_data and 
            isinstance(quote_data, dict) and 
            (
                quote_data.get("last_price", 0) > 0 or
                quote_data.get("data_source") == "MOCK"  # Mock data is acceptable
            )
        )
        
        # If normalized fails and we normalized, try original
        if not is_valid_quote and normalized_symbol != original_symbol:
            quote_data = await data_service.get_quote(original_symbol, exchange)
            is_valid_quote = (
                quote_data and 
                isinstance(quote_data, dict) and 
                (
                    quote_data.get("last_price", 0) > 0 or
                    quote_data.get("data_source") == "MOCK"
                )
            )
        
        # If still invalid, return error response
        if not is_valid_quote:
            error_response = create_error_response(
                error=f"No data available for {original_symbol}",
                error_code="QUOTE_NOT_FOUND",
                details={"symbol": original_symbol, "exchange": exchange, "normalized_symbol": normalized_symbol},
                status_code=404
            )
            # Cache error for shorter time to avoid hammering failed requests
            expires = now + timedelta(seconds=max(1, min(ttl_seconds // 2, 2)))
            _quote_cache[cache_key] = (expires, error_response)
            return error_response
        
        # Cache successful response
        expires = now + timedelta(seconds=max(1, min(ttl_seconds, 30)))
        _quote_cache[cache_key] = (expires, quote_data)
        
        return quote_data
        
    except Exception as e:
        return handle_api_error(e, f"get_quote({symbol}, {exchange})")

# Historical data cache
_historical_cache: Dict[str, Tuple[datetime, List[Dict]]] = {}

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str, 
    exchange: str = "NSE",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    repair: bool = Query(False, description="Apply lightweight candle cleaning/repair"),
    ttl_seconds: int = 300,  # 5 minutes cache for historical data
    db: Session = Depends(get_db)
):
    """Get historical data for a symbol with intelligent fallback: NSE → Angel One → Yahoo → Mock
    Cached for 5 minutes by default since historical data doesn't change frequently.
    """
    try:
        # Check cache first
        cache_key = get_cache_key("historical", symbol, exchange, from_date or "", to_date or "", str(repair))
        now = datetime.utcnow()
        cached = _historical_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]
        
        # Try to get from database first (if we have it cached)
        if not from_date and not to_date:  # Only for recent data queries
            try:
                # Get latest data from database (last 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                db_data = db.query(MarketData).filter(
                    MarketData.symbol == symbol.upper(),
                    MarketData.exchange == exchange,
                    MarketData.timestamp >= cutoff_date
                ).order_by(MarketData.timestamp.desc()).limit(1000).all()
                
                if db_data:
                    # Convert to API format
                    historical_data = [
                        {
                            "time": int(data.timestamp.timestamp()),
                            "open": float(data.open_price or 0),
                            "high": float(data.high_price or 0),
                            "low": float(data.low_price or 0),
                            "close": float(data.close_price or 0),
                            "volume": int(data.volume or 0),
                        }
                        for data in reversed(db_data)  # Reverse to get chronological order
                    ]
                    
                    if repair:
                        historical_data = repair_candles(historical_data)
                    
                    # Cache and return
                    expires = now + timedelta(seconds=max(60, min(ttl_seconds, 600)))
                    _historical_cache[cache_key] = (expires, historical_data)
                    return historical_data
            except Exception as e:
                # If DB query fails, continue to API fetch
                pass
        
        # Fetch from API
        historical_data = await data_service.get_historical_data(symbol, exchange, from_date, to_date)

        if repair and historical_data:
            historical_data = repair_candles(historical_data)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No historical data available for {symbol}")
        
        # Store in database for caching (batch insert for performance)
        if historical_data and len(historical_data) > 0:
            try:
                # Batch insert - only store if not exists
                existing_timestamps = set()
                if not from_date and not to_date:  # Only for recent data
                    cutoff_date = datetime.utcnow() - timedelta(days=30)
                    existing = db.query(MarketData.timestamp).filter(
                        MarketData.symbol == symbol.upper(),
                        MarketData.exchange == exchange,
                        MarketData.timestamp >= cutoff_date
                    ).all()
                    existing_timestamps = {row[0] for row in existing}
                
                new_records = []
                for data_point in historical_data:
                    # Convert timestamp
                    if isinstance(data_point.get("time"), (int, float)):
                        data_timestamp = datetime.fromtimestamp(data_point["time"])
                    else:
                        data_timestamp = datetime.now()
                    
                    # Skip if already exists
                    if data_timestamp in existing_timestamps:
                        continue
                    
                    market_data = MarketData(
                        symbol=symbol.upper(),
                        exchange=exchange,
                        open_price=data_point.get("open", 0),
                        high_price=data_point.get("high", 0),
                        low_price=data_point.get("low", 0),
                        close_price=data_point.get("close", 0),
                        volume=data_point.get("volume", 0),
                        timestamp=data_timestamp
                    )
                    new_records.append(market_data)
                
                # Batch insert
                if new_records:
                    db.bulk_insert_mappings(MarketData, [
                        {
                            "symbol": r.symbol,
                            "exchange": r.exchange,
                            "open_price": r.open_price,
                            "high_price": r.high_price,
                            "low_price": r.low_price,
                            "close_price": r.close_price,
                            "volume": r.volume,
                            "timestamp": r.timestamp,
                        }
                        for r in new_records
                    ])
                    db.commit()
            except Exception as e:
                # Don't fail the request if DB insert fails
                db.rollback()
                pass
        
        # Cache response
        expires = now + timedelta(seconds=max(60, min(ttl_seconds, 600)))
        _historical_cache[cache_key] = (expires, historical_data)
        
        return historical_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")

@router.get("/market-status")
async def get_market_status():
    """Get current market status with intelligent fallback"""
    try:
        market_status = await data_service.get_market_status()
        return market_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market status: {str(e)}")

@router.get("/top-gainers")
async def get_top_gainers(exchange: str = "NSE"):
    """Get top gaining stocks with intelligent fallback"""
    try:
        # For now, return mock data - can be enhanced to use data service
        return [
            {"symbol": "RELIANCE", "change": 2.5, "changePercent": 1.2},
            {"symbol": "TCS", "change": 1.8, "changePercent": 0.9},
            {"symbol": "HDFC", "change": 1.5, "changePercent": 0.7}
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top gainers: {str(e)}")

@router.get("/top-losers")
async def get_top_losers(exchange: str = "NSE"):
    """Get top losing stocks with intelligent fallback"""
    try:
        # For now, return mock data - can be enhanced to use data service
        return [
            {"symbol": "SOME_STOCK", "change": -2.5, "changePercent": -1.2},
            {"symbol": "ANOTHER_STOCK", "change": -1.8, "changePercent": -0.9},
            {"symbol": "YET_ANOTHER", "change": -1.5, "changePercent": -0.7}
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top losers: {str(e)}")

@router.post("/start-feed")
async def start_realtime_feed(symbol: str, exchange: str = "NSE", background_tasks: BackgroundTasks = None):
    """Start real-time feed for a symbol"""
    try:
        # Start background task for real-time updates
        if background_tasks:
            background_tasks.add_task(start_price_feed, symbol, exchange)
            
        return {"message": f"Real-time feed started for {symbol} on {exchange}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting feed: {str(e)}")

@router.post("/stop-feed")
async def stop_realtime_feed(symbol: str):
    """Stop real-time feed for a symbol"""
    try:
        # Implementation to stop the feed
        return {"message": f"Real-time feed stopped for {symbol}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping feed: {str(e)}")

async def start_price_feed(symbol: str, exchange: str):
    """Background task to start price feed with intelligent fallback"""
    try:
        while True:
            # Get latest quote using data service with fallback
            quote_data = await data_service.get_quote(symbol, exchange)
                
            if quote_data and 'error' not in quote_data:
                # Send to WebSocket subscribers
                await websocket_manager.send_to_subscribers(symbol, quote_data)
                
            # Wait 5 seconds before next update
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"Error in price feed for {symbol}: {e}")


# -------------------- Index Constituents --------------------
# Simple in-memory cache: { key: (expires_at, data) }
_index_cache: Dict[str, Tuple[datetime, List[str]]] = {}

# Static seeds to work immediately; kept short for brevity, extend as needed
_STATIC_INDEX_SEEDS: Dict[str, List[str]] = {
    "NIFTY50": [
        "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","ITC","BHARTIARTL","LT","SBIN","HINDUNILVR",
    ],
    "NIFTYNEXT50": [
        "ADANIPORTS","DMART","LTIM","PIDILITIND","BAJAJHLDNG",
    ],
    "NIFTY100": [
        "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","ITC","BHARTIARTL","LT","SBIN","HINDUNILVR",
    ],
    "NIFTY500": ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY"],
    "BANKNIFTY": ["HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","INDUSINDBK","PNB","BANKBARODA"],
    "NIFTYIT": ["TCS","INFY","WIPRO","HCLTECH","TECHM"],
    "NIFTYPHARMA": ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB"],
    "NIFTYAUTO": ["TATAMOTORS","MARUTI","EICHERMOT","M&M"],
    "NIFTYFMCG": ["HINDUNILVR","ITC","NESTLEIND","DABUR"],
    "NIFTYMETAL": ["TATASTEEL","JSWSTEEL","HINDALCO","COALINDIA"],
    "NIFTYREALTY": ["DLF","LODHA","GODREJPROP"],
    "NIFTYMEDIA": ["ZEEL","SUNTV"],
    "NIFTYPRIVATEBANK": ["HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","INDUSINDBK"],
    "NIFTYPSUBANK": ["SBIN","PNB","BANKBARODA","CANBK"],
    "SENSEX": [
        "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","ITC","BHARTIARTL","LT","SBIN","HINDUNILVR",
    ],
}

def _normalize_index(index: str) -> str:
    idx = (index or "").upper().replace(" ", "")
    # map common aliases
    alias = {
        "NIFTY 50": "NIFTY50",
        "NIFTYBANK": "BANKNIFTY",
        "BANKNIFTY": "BANKNIFTY",
        "NIFTYIT": "NIFTYIT",
        "NIFTY PHARMA": "NIFTYPHARMA",
        "NIFTY FMCG": "NIFTYFMCG",
        "NIFTY AUTO": "NIFTYAUTO",
        "NIFTY METAL": "NIFTYMETAL",
        "NIFTY REALTY": "NIFTYREALTY",
        "NIFTY MEDIA": "NIFTYMEDIA",
        "NIFTY PRIVATE BANK": "NIFTYPRIVATEBANK",
        "NIFTY PSU BANK": "NIFTYPSUBANK",
        "NIFTY NEXT 50": "NIFTYNEXT50",
        "NIFTY 100": "NIFTY100",
        "NIFTY 500": "NIFTY500",
    }
    return alias.get(index.upper(), idx)

@router.get("/index-constituents")
async def get_index_constituents(index: str, ttl_minutes: int = 30):
    """Return index constituents with simple cache.
    Fallback chain planned: NSE → Angel One → Static seeds (current impl uses seeds).
    """
    try:
        key = _normalize_index(index)
        if not key:
            raise HTTPException(status_code=400, detail="index is required")

        # cache check
        now = datetime.utcnow()
        cached = _index_cache.get(key)
        if cached and cached[0] > now:
            return {
                "index": key,
                "symbols": cached[1],
                "source": "cache",
                "cached_until": cached[0].isoformat(),
                "updated_at": now.isoformat(),
            }

        # TODO: Try NSE first via data_service when available
        symbols = _STATIC_INDEX_SEEDS.get(key)
        if not symbols:
            raise HTTPException(status_code=404, detail=f"Unknown or unsupported index: {index}")

        # update cache
        expires = now + timedelta(minutes=max(5, min(ttl_minutes, 60)))
        _index_cache[key] = (expires, symbols)

        return {
            "index": key,
            "symbols": symbols,
            "source": "static",
            "cached_until": expires.isoformat(),
            "updated_at": now.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching index constituents: {str(e)}")


# ---------- Index Quote with ticker mapping and simple backoff ----------
_index_quote_cache: Dict[str, Tuple[datetime, Dict]] = {}

_INDEX_NAME_MAP = {
    # UI key -> NSE display name in allIndices
    "NIFTY50": "NIFTY 50",
    "BANKNIFTY": "NIFTY BANK",
    "SENSEX": "SENSEX",  # some payloads may use 'S&P BSE SENSEX'; we'll fallback case-insensitive
    "NIFTYIT": "NIFTY IT",
}

def _get_index_display_name(index: str) -> Optional[str]:
    key = _normalize_index(index)
    return _INDEX_NAME_MAP.get(key, key)

async def _fetch_with_backoff(fetch_coro, retries: int = 3, base_delay: float = 0.5):
    for attempt in range(retries):
        try:
            return await fetch_coro
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "too many requests" in msg:
                delay = base_delay * (2 ** attempt) + (0.1 * attempt)
                await asyncio.sleep(delay)
                continue
            raise
    # final try
    return await fetch_coro

@router.get("/index-quote")
async def get_index_quote(index: str, ttl_minutes: int = 30):
    """Return index quote using NSE allIndices when possible, cached, with simple backoff.
    Fallback: data_service.get_quote(mappedSymbol) or minimal mock.
    """
    try:
        key = _normalize_index(index)
        now = datetime.utcnow()
        cached = _index_quote_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

        quote = None

        # 1) Try NSE allIndices by display name
        display_name = _get_index_display_name(key)
        try:
            async with NSEAPI() as nse:
                quote = await nse.get_index_quote(display_name)
        except Exception:
            quote = None

        # 2) Fallback to data_service (could be NSE equity mapping or other providers)
        if not quote or ('error' in quote):
            # Some UIs pass display names; map to a symbol if available, else use key
            fallback_symbol = key
            quote = await _fetch_with_backoff(data_service.get_quote(fallback_symbol, "NSE"))

        if not quote or ('error' in quote):
            # minimal mock or compute from constituents later
            quote = {
                "symbol": key,
                "last_price": 0,
                "change": 0,
                "change_percent": 0,
                "timestamp": now.isoformat(),
                "source": "cache_or_mock"
            }

        expires = now + timedelta(minutes=max(5, min(ttl_minutes, 60)))
        payload = { **quote, "index": key, "cached_until": expires.isoformat(), "updated_at": now.isoformat() }
        _index_quote_cache[key] = (expires, payload)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching index quote: {str(e)}")


# ---------- Technical Indicators (SMA/EMA/RSI/MACD/BBANDS) ----------

def _sma(values, period: int):
    if period <= 0 or len(values) < period:
        return []
    out = []
    window_sum = sum(values[:period])
    out.append(window_sum / period)
    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        out.append(window_sum / period)
    # pad front with None to align with input
    return [None] * (period - 1) + out

def _ema(values, period: int):
    if period <= 0 or len(values) == 0:
        return []
    k = 2 / (period + 1)
    ema_vals = []
    ema = None
    for v in values:
        ema = v if ema is None else (v - ema) * k + ema
        ema_vals.append(ema)
    return ema_vals

def _rsi(values, period: int):
    if period <= 0 or len(values) < period + 1:
        return []
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(values)):
        chg = values[i] - values[i - 1]
        gains.append(max(chg, 0.0))
        losses.append(max(-chg, 0.0))
    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period
    rsis = [None] * period
    for i in range(period + 1, len(values)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsis.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsis.append(100 - (100 / (1 + rs)))
    return rsis

def _macd(values, fast: int = 12, slow: int = 26, signal: int = 9):
    if len(values) == 0:
        return [], [], []
    ema_fast = _ema(values, fast)
    ema_slow = _ema(values, slow)
    macd_line = [ (f - s) if (f is not None and s is not None) else None for f, s in zip(ema_fast, ema_slow) ]
    # remove None at start for signal calc
    macd_clean = [m for m in macd_line if m is not None]
    signal_line_clean = _ema(macd_clean, signal)
    # align back
    pad = len(macd_line) - len(signal_line_clean)
    signal_line = [None] * pad + signal_line_clean
    histogram = [ (m - s) if (m is not None and s is not None) else None for m, s in zip(macd_line, signal_line) ]
    return macd_line, signal_line, histogram

def _bbands(values, period: int = 20, nbdev: float = 2.0):
    if period <= 0 or len(values) < period:
        return [], [], []
    sma = _sma(values, period)
    upper = []
    lower = []
    for i in range(len(values)):
        if i + 1 < period:
            upper.append(None)
            lower.append(None)
            continue
        window = values[i - period + 1:i + 1]
        mean = sma[i]
        var = sum((x - mean) ** 2 for x in window) / period
        sd = var ** 0.5
        upper.append(mean + nbdev * sd)
        lower.append(mean - nbdev * sd)
    return upper, sma, lower


_ind_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str,
                         indicator: str,
                         timeframe: str = "1D",
                         period: int = 14,
                         fastperiod: int = 12,
                         slowperiod: int = 26,
                         signalperiod: int = 9,
                         ttl_minutes: int = 30):
    """Compute technical indicators from historical close prices.
    Supported indicator values: SMA, EMA, RSI, MACD, BBANDS
    """
    try:
        key = f"ind:{symbol}:{indicator}:{timeframe}:{period}:{fastperiod}:{slowperiod}:{signalperiod}"
        now = datetime.utcnow()
        cached = _ind_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

        # fetch recent historical data (backend side supports timeframe param via services)
        # We request a reasonable window; client can adjust
        historical = await data_service.get_historical_data(symbol, "NSE")
        if not historical:
            raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")

        closes = [float(d.get("close", d.get("close_price", 0))) for d in historical]
        dates = [d.get("date") or d.get("timestamp") or "" for d in historical]

        ind = indicator.strip().upper()
        result: Dict[str, Any]

        if ind == "SMA":
            series = _sma(closes, period)
            result = {"indicator": ind, "period": period, "series": [{"t": dates[i], "v": series[i]} for i in range(len(dates))]}
        elif ind == "EMA":
            series = _ema(closes, period)
            result = {"indicator": ind, "period": period, "series": [{"t": dates[i], "v": series[i]} for i in range(len(dates))]}
        elif ind == "RSI":
            series = _rsi(closes, period)
            result = {"indicator": ind, "period": period, "series": [{"t": dates[i], "v": series[i] if i < len(series) else None} for i in range(len(dates))]}
        elif ind == "MACD":
            macd_line, signal_line, hist = _macd(closes, fastperiod, slowperiod, signalperiod)
            result = {
                "indicator": ind,
                "fastperiod": fastperiod,
                "slowperiod": slowperiod,
                "signalperiod": signalperiod,
                "macd": [{"t": dates[i], "v": macd_line[i]} for i in range(len(dates))],
                "signal": [{"t": dates[i], "v": signal_line[i]} for i in range(len(dates))],
                "histogram": [{"t": dates[i], "v": hist[i]} for i in range(len(dates))],
            }
        elif ind == "ALL":
            # Return all indicators in a single response
            sma_series = _sma(closes, period)
            ema_series = _ema(closes, period)
            rsi_series = _rsi(closes, period)
            macd_line, signal_line, hist = _macd(closes, fastperiod, slowperiod, signalperiod)
            upper_bb, mid_bb, lower_bb = _bbands(closes, period)
            
            result = {
                "indicators": {
                    "SMA": {"period": period, "series": [{"t": dates[i], "v": sma_series[i]} for i in range(len(dates))]},
                    "EMA": {"period": period, "series": [{"t": dates[i], "v": ema_series[i]} for i in range(len(dates))]},
                    "RSI": {"period": period, "series": [{"t": dates[i], "v": rsi_series[i] if i < len(rsi_series) else None} for i in range(len(dates))]},
                    "MACD": {
                        "fastperiod": fastperiod,
                        "slowperiod": slowperiod,
                        "signalperiod": signalperiod,
                        "macd": [{"t": dates[i], "v": macd_line[i]} for i in range(len(dates))],
                        "signal": [{"t": dates[i], "v": signal_line[i]} for i in range(len(dates))],
                        "histogram": [{"t": dates[i], "v": hist[i]} for i in range(len(dates))],
                    },
                    "BBANDS": {
                        "period": period,
                        "upper": [{"t": dates[i], "v": upper_bb[i]} for i in range(len(dates))],
                        "middle": [{"t": dates[i], "v": mid_bb[i]} for i in range(len(dates))],
                        "lower": [{"t": dates[i], "v": lower_bb[i]} for i in range(len(dates))],
                    }
                }
            }

        elif ind == "BBANDS":
            upper, mid, lower = _bbands(closes, period)
            result = {
                "indicator": ind,
                "period": period,
                "upper": [{"t": dates[i], "v": upper[i]} for i in range(len(dates))],
                "middle": [{"t": dates[i], "v": mid[i]} for i in range(len(dates))],
                "lower": [{"t": dates[i], "v": lower[i]} for i in range(len(dates))],
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported indicator. Use SMA, EMA, RSI, MACD, BBANDS, ALL")

        payload = {**result, "symbol": symbol, "timeframe": timeframe, "updated_at": now.isoformat()}
        expires = now + timedelta(minutes=max(5, min(ttl_minutes, 60)))
        _ind_cache[key] = (expires, payload)
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing indicators: {str(e)}")


# ---------- Sector Performance (NSE sector indices) ----------

_SECTOR_TO_INDEX: Dict[str, str] = {
    "Banking": "NIFTY BANK",
    "IT": "NIFTY IT",
    "Pharma": "NIFTY PHARMA",
    "Auto": "NIFTY AUTO",
    "FMCG": "NIFTY FMCG",
    "Energy": "NIFTY ENERGY",
    "Metals": "NIFTY METAL",
    "Real Estate": "NIFTY REALTY",
    "PSU Bank": "NIFTY PSU BANK",
    "Media": "NIFTY MEDIA",
    "Financial Services": "NIFTY FIN SERVICE",
}

_sector_cache: Dict[str, Tuple[datetime, Dict]] = {}

def _classify_trend(pct: float) -> str:
    if pct is None:
        return "Sideways"
    if pct > 0.2:
        return "Up"
    if pct < -0.2:
        return "Down"
    return "Sideways"

def _classify_momentum(pct: float) -> str:
    if pct is None:
        return "Neutral"
    a = abs(pct)
    if a >= 1.0:
        return "Strong"
    if a >= 0.3:
        return "Medium"
    return "Weak"

def _pct_change(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return (a - b) / b * 100.0

async def _sector_today_change_map() -> Dict[str, float]:
    """Fetch today's percentChange per NSE index from allIndices."""
    try:
        async with NSEAPI() as nse:
            data = await nse.get_index_quote("NIFTY 50")  # prime cookies
            # Now fetch all indices list
            # Reuse same client session to call allIndices
            # get_index_quote already called allIndices, but we need the list → call directly
            # Use private call through session
            url = f"https://www.nseindia.com/api/allIndices"
            resp = await nse.session.get(url, cookies=nse.cookies)
            if resp.status_code != 200:
                return {}
            payload = resp.json() or {}
            rows = payload.get("data", []) or []
            return { r.get("index"): r.get("percentChange") for r in rows if r.get("index") }
    except Exception:
        return {}

@router.get("/sector/performance")
async def get_sector_performance(ttl_minutes: int = 30):
    """Return sector performance similar to AlphaVantage sectors, based on NSE sector indices.
    Provides real-time percent change plus simple trend/momentum classification.
    """
    try:
        now = datetime.utcnow()
        cache_key = "sector_perf"
        cached = _sector_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        today_map = await _sector_today_change_map()

        results = []
        for sector, index_name in _SECTOR_TO_INDEX.items():
            pct_today = today_map.get(index_name)
            entry = {
                "sector": sector,
                "index": index_name,
                "realtime": pct_today,
                "trend": _classify_trend(pct_today if isinstance(pct_today, (int, float)) else 0),
                "volume": "Medium",  # placeholder; NSE allIndices doesn't expose reliable index volume consistently
                "momentum": _classify_momentum(pct_today if isinstance(pct_today, (int, float)) else 0),
            }
            results.append(entry)

        payload = {
            "as_of": now.isoformat(),
            "source": "nse_allIndices",
            "sectors": results,
        }
        expires = now + timedelta(minutes=max(5, min(ttl_minutes, 60)))
        _sector_cache[cache_key] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sector performance: {str(e)}")


# ---------- Fast Info (aggregated quick quote + stats) ----------

_fastinfo_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/fast-info/{symbol}")
async def get_fast_info(symbol: str, ttl_seconds: int = 120):
    try:
        now = datetime.utcnow()
        cached = _fastinfo_cache.get(symbol)
        if cached and cached[0] > now:
            return cached[1]

        # Live quote (uses NSE-first via data_service)
        quote = await data_service.get_quote(symbol, "NSE")
        if not quote or ('error' in quote):
            raise HTTPException(status_code=404, detail=f"No quote for {symbol}")

        # Historical candles for rolling stats
        candles = await data_service.get_historical_data(symbol, "NSE")
        candles = repair_candles(candles or [])

        closes = [c.get("close", 0) for c in candles]
        volumes = [c.get("volume", 0) for c in candles]

        def avg(lst, n):
            return None if not lst else float(sum(lst[-n:]) / max(1, min(n, len(lst))))

        fifty_ma = avg(closes, 50)
        twohundred_ma = avg(closes, 200)
        ten_day_vol = avg(volumes, 10)
        three_month_vol = None
        if candles:
            three_month_vol = avg(volumes, min(65, len(volumes)))

        year_high = max(closes[-252:], default=max(closes) if closes else 0) if closes else None
        year_low = min(closes[-252:], default=min(closes) if closes else 0) if closes else None
        year_change = None
        if closes and len(closes) >= 2:
            base = closes[max(0, len(closes) - 252)] if len(closes) >= 252 else closes[0]
            if base:
                year_change = (closes[-1] - base) / base

        previous_close = None
        if closes and len(closes) >= 2:
            previous_close = closes[-2]

        payload = {
            "symbol": symbol,
            "currency": quote.get("currency", "INR"),
            "exchange": quote.get("exchange", "NSE"),
            "timezone": quote.get("timezone", "Asia/Kolkata"),
            "last_price": quote.get("last_price") or quote.get("lastPrice"),
            "open": quote.get("open"),
            "day_high": quote.get("high"),
            "day_low": quote.get("low"),
            "last_volume": quote.get("volume") or quote.get("day_volume"),
            "previous_close": previous_close,
            "regular_market_previous_close": previous_close,
            "fifty_day_average": fifty_ma,
            "two_hundred_day_average": twohundred_ma,
            "ten_day_average_volume": int(ten_day_vol) if isinstance(ten_day_vol, float) else ten_day_vol,
            "three_month_average_volume": int(three_month_vol) if isinstance(three_month_vol, float) else three_month_vol,
            "year_high": year_high,
            "year_low": year_low,
            "year_change": year_change,
            "updated_at": now.isoformat(),
        }

        expires = now + timedelta(seconds=max(30, min(ttl_seconds, 600)))
        _fastinfo_cache[symbol] = (expires, payload)
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building fast info: {str(e)}")


# ---------- Holders (placeholder structure, provider pluggable) ----------

_holders_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/holders/{symbol}")
async def get_holders(symbol: str, ttl_minutes: int = 10):
    """Return ownership/holders structure. Currently provider is not wired.
    We return an empty but well-structured payload so frontend can consume safely.
    """
    try:
        now = datetime.utcnow()
        cached = _holders_cache.get(symbol)
        if cached and cached[0] > now:
            return cached[1]

        payload = {
            "symbol": symbol,
            "source": "unavailable",
            "message": "Ownership data provider not configured; returning empty structures",
            "major": [],
            "institutional": [],
            "mutualfund": [],
            "insider_transactions": [],
            "insider_purchases": [],
            "insider_roster": [],
            "updated_at": now.isoformat(),
        }

        expires = now + timedelta(minutes=max(5, min(ttl_minutes, 60)))
        _holders_cache[symbol] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching holders: {str(e)}")


# ---------- Fundamentals (placeholder tables) ----------

_fundamentals_cache: Dict[str, Tuple[datetime, Dict]] = {}

def _empty_table(columns: Optional[List[str]] = None) -> Dict:
    return {"columns": columns or [], "rows": []}

@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str, ttl_minutes: int = 60):
    """Return fundamentals tables in a stable schema. Provider not yet wired.
    Tables are empty but structured so the frontend can render safely.
    """
    try:
        now = datetime.utcnow()
        cached = _fundamentals_cache.get(symbol)
        if cached and cached[0] > now:
            return cached[1]

        payload = {
            "symbol": symbol,
            "source": "unavailable",
            "message": "Fundamentals provider not configured; tables are empty",
            "income": {
                "yearly": _empty_table(["metric", "value", "asOfDate"]),
                "quarterly": _empty_table(["metric", "value", "asOfDate"]),
                "trailing": _empty_table(["metric", "ttmValue", "asOfDate"]),
            },
            "balance_sheet": {
                "yearly": _empty_table(["metric", "value", "asOfDate"]),
                "quarterly": _empty_table(["metric", "value", "asOfDate"]),
            },
            "cash_flow": {
                "yearly": _empty_table(["metric", "value", "asOfDate"]),
                "quarterly": _empty_table(["metric", "value", "asOfDate"]),
                "trailing": _empty_table(["metric", "ttmValue", "asOfDate"]),
            },
            "updated_at": now.isoformat(),
        }

        expires = now + timedelta(minutes=max(15, min(ttl_minutes, 240)))
        _fundamentals_cache[symbol] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fundamentals: {str(e)}")


# ---------- Funds (ETF/Mutual Fund profile placeholder) ----------

_funds_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/funds/{symbol}")
async def get_fund_profile(symbol: str, ttl_minutes: int = 60):
    """Return fund profile/top-holdings style schema. Provider not wired yet.
    """
    try:
        now = datetime.utcnow()
        cached = _funds_cache.get(symbol)
        if cached and cached[0] > now:
            return cached[1]

        payload = {
            "symbol": symbol,
            "source": "unavailable",
            "message": "Fund profile provider not configured; returning empty structures",
            "quote_type": None,
            "description": "",
            "fund_overview": {"categoryName": None, "family": None, "legalType": None},
            "fund_operations": {
                "columns": ["Attributes", symbol, "Category Average"],
                "rows": [
                    ["Annual Report Expense Ratio", None, None],
                    ["Annual Holdings Turnover", None, None],
                    ["Total Net Assets", None, None],
                ],
            },
            "asset_classes": {
                "cashPosition": None,
                "stockPosition": None,
                "bondPosition": None,
                "preferredPosition": None,
                "convertiblePosition": None,
                "otherPosition": None,
            },
            "top_holdings": {
                "columns": ["Symbol", "Name", "Holding Percent"],
                "rows": [],
            },
            "equity_holdings": {
                "columns": ["Average", symbol, "Category Average"],
                "rows": [
                    ["Price/Earnings", None, None],
                    ["Price/Book", None, None],
                    ["Price/Sales", None, None],
                    ["Price/Cashflow", None, None],
                    ["Median Market Cap", None, None],
                    ["3 Year Earnings Growth", None, None],
                ],
            },
            "bond_holdings": {
                "columns": ["Average", symbol, "Category Average"],
                "rows": [
                    ["Duration", None, None],
                    ["Maturity", None, None],
                    ["Credit Quality", None, None],
                ],
            },
            "bond_ratings": {},
            "sector_weightings": {},
            "updated_at": now.isoformat(),
        }

        expires = now + timedelta(minutes=max(15, min(ttl_minutes, 240)))
        _funds_cache[symbol] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fund profile: {str(e)}")


# ---------- Screener (minimal NSE-based) ----------

_screener_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/screener")
async def screen(
    preset: Optional[str] = Query("day_gainers", description="day_gainers|day_losers|most_actives"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_volume: Optional[int] = None,
    count: int = 25,
    ttl_seconds: int = 60,
):
    """Minimal screener using existing NSE data endpoints and quote fetches.
    Supports presets and basic filters; returns top 'count' results.
    """
    try:
        key = f"scr:{preset}:{min_price}:{max_price}:{min_volume}:{count}"
        now = datetime.utcnow()
        cached = _screener_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

        # Seed from NSE top gainers/losers if available via data_service
        symbols: List[str] = []
        try:
            async with NSEAPI() as nse:
                if preset == "day_gainers":
                    listing = await nse.get_top_gainers()
                elif preset == "day_losers":
                    listing = await nse.get_top_losers()
                else:
                    # most_actives approximated by top gainers + losers union
                    g = await nse.get_top_gainers()
                    l = await nse.get_top_losers()
                    listing = (g or []) + (l or [])
                symbols = [row.get("symbol") for row in (listing or []) if row.get("symbol")]
        except Exception:
            symbols = []

        # Fallback: if empty, use a small static universe
        if not symbols:
            symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "ITC", "LT"]

        # Fetch quotes and apply filters
        results = []
        for sym in symbols:
            try:
                q = await data_service.get_quote(sym, "NSE")
                if not q or ('error' in q):
                    continue
                price = q.get("last_price") or q.get("lastPrice") or 0
                vol = q.get("volume") or q.get("day_volume") or 0
                if min_price is not None and (price is None or price < min_price):
                    continue
                if max_price is not None and (price is None or price > max_price):
                    continue
                if min_volume is not None and (vol is None or vol < min_volume):
                    continue
                change_pct = q.get("change_percent") or q.get("pChange") or 0
                results.append({
                    "symbol": sym,
                    "last_price": price,
                    "change_percent": change_pct,
                    "volume": vol,
                    "source": q.get("source", "nse"),
                })
            except Exception:
                continue

        # Sort based on preset intent
        if preset == "day_gainers":
            results.sort(key=lambda r: (r["change_percent"] or 0), reverse=True)
        elif preset == "day_losers":
            results.sort(key=lambda r: (r["change_percent"] or 0))
        else:
            results.sort(key=lambda r: (r["volume"] or 0), reverse=True)

        payload = {
            "preset": preset,
            "filters": {"min_price": min_price, "max_price": max_price, "min_volume": min_volume},
            "count": count,
            "results": results[: max(1, min(count, 250))],
            "updated_at": now.isoformat(),
            "source": "nse_derived",
        }

        expires = now + timedelta(seconds=max(15, min(ttl_seconds, 300)))
        _screener_cache[key] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running screener: {str(e)}")


def _eval_op(field_value: Any, op: str, operand: Any) -> bool:
    try:
        if op == "EQ":
            return field_value == operand
        if op == "GT":
            return field_value is not None and operand is not None and field_value > operand
        if op == "GTE":
            return field_value is not None and operand is not None and field_value >= operand
        if op == "LT":
            return field_value is not None and operand is not None and field_value < operand
        if op == "LTE":
            return field_value is not None and operand is not None and field_value <= operand
        return False
    except Exception:
        return False


@router.post("/screener/query")
async def screen_query(
    query: Dict[str, Any],
    count: int = 50,
    ttl_seconds: int = 60,
):
    """Evaluate a simple boolean screener query over basic fields.
    Query shape:
    {
      "operator": "AND|OR",
      "operands": [
         { "field": "price|change_percent|volume", "op": "EQ|GT|LT|GTE|LTE", "value": number },
         { "operator": "OR", "operands": [ ... ] }
      ]
    }
    """
    try:
        key = f"sq:{json.dumps(query, sort_keys=True)}:{count}"
        now = datetime.utcnow()
        cached = _screener_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

        # Universe from NSE gainers+losers to keep small and fast
        universe: List[str] = []
        try:
            async with NSEAPI() as nse:
                g = await nse.get_top_gainers()
                l = await nse.get_top_losers()
                for row in (g or []) + (l or []):
                    sym = row.get("symbol")
                    if sym and sym not in universe:
                        universe.append(sym)
        except Exception:
            universe = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "ITC", "LT"]

        async def get_fields(sym: str) -> Dict[str, Any]:
            q = await data_service.get_quote(sym, "NSE")
            return {
                "price": q.get("last_price") or q.get("lastPrice") or 0,
                "change_percent": q.get("change_percent") or q.get("pChange") or 0,
                "volume": q.get("volume") or q.get("day_volume") or 0,
            } if q and 'error' not in q else {"price": 0, "change_percent": 0, "volume": 0}

        async def eval_node(node: Dict[str, Any], fields: Dict[str, Any]) -> bool:
            if "operator" in node:
                op = node["operator"].upper()
                parts = node.get("operands", [])
                if op == "AND":
                    for p in parts:
                        if not await eval_node(p, fields):
                            return False
                    return True
                if op == "OR":
                    for p in parts:
                        if await eval_node(p, fields):
                            return True
                    return False
                return False
            else:
                field = node.get("field")
                op = node.get("op", "EQ").upper()
                val = node.get("value")
                if field not in ("price", "change_percent", "volume"):
                    return False
                return _eval_op(fields.get(field), op, val)

        results = []
        for sym in universe:
            try:
                f = await get_fields(sym)
                if await eval_node(query, f):
                    results.append({"symbol": sym, **f})
            except Exception:
                continue

        # Default sort by price desc
        results.sort(key=lambda r: r.get("price") or 0, reverse=True)
        payload = {
            "results": results[: max(1, min(count, 250))],
            "updated_at": now.isoformat(),
            "source": "nse_derived",
        }
        expires = now + timedelta(seconds=max(15, min(ttl_seconds, 300)))
        _screener_cache[key] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running screener query: {str(e)}")


# ---------- Market Summary (status + key indices) ----------

_market_summary_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/market/summary")
async def get_market_summary(ttl_seconds: int = 120):
    """Return consolidated market status and a snapshot of key indices (NSE-first)."""
    try:
        now = datetime.utcnow()
        cached = _market_summary_cache.get("summary")
        if cached and cached[0] > now:
            return cached[1]

        # Status via data service (NSE-first)
        status = await data_service.get_market_status()

        # Key indices snapshot - TEMPORARILY USING DATA SERVICE INSTEAD OF NSE API
        keys = ["NIFTY50", "BANKNIFTY", "SENSEX", "NIFTYIT"]
        indices = []
        try:
            # Commented out NSE API calls - using data service instead
            # async with NSEAPI() as nse:
            #     for k in keys:
            #         display = _get_index_display_name(k)
            #         q = await nse.get_index_quote(display)
            #         if not q:
            #             continue
            #         indices.append({
            #             "index": k,
            #             "display": display,
            #             "last_price": q.get("last_price"),
            #             "change": q.get("change"),
            #             "change_percent": q.get("change_percent"),
            #             "updated_at": q.get("timestamp") or now.isoformat(),
            #             "source": q.get("source", "nse_allIndices"),
            #         })
            
            # Use data service instead for indices
            for k in keys:
                try:
                    q = await data_service.get_quote(k, "NSE")
                    if q and not q.get("error"):
                        indices.append({
                            "index": k,
                            "display": k,
                            "last_price": q.get("last_price"),
                            "change": q.get("change"),
                            "change_percent": q.get("change_percent"),
                            "updated_at": q.get("timestamp") or now.isoformat(),
                            "source": q.get("data_source", "yahoo_finance"),
                        })
                except Exception:
                    continue
        except Exception:
            indices = []

        payload = {
            "status": status or {},
            "indices": indices,
            "updated_at": now.isoformat(),
            "source": "yahoo_finance_primary",
        }

        expires = now + timedelta(seconds=max(30, min(ttl_seconds, 600)))
        _market_summary_cache["summary"] = (expires, payload)
        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building market summary: {str(e)}")


# ---------- Industry summary (approx via sector indices) ----------

_industry_cache: Dict[str, Tuple[datetime, Dict]] = {}

@router.get("/industry/summary")
async def get_industry_summary(sector: str = Query("IT", description="Sector key like IT, Pharma, Banking"), ttl_minutes: int = 30):
    """Return a minimal industry-like summary: sector name, and top companies approximated from index constituents.
    Since NSE doesn't expose an 'industry' API here, we use index constituents + live quotes.
    """
    try:
        now = datetime.utcnow()
        key = f"{sector}".upper()
        cached = _industry_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

        sector_to_index = {
            "BANKING": "BANKNIFTY",
            "IT": "NIFTYIT",
            "PHARMA": "NIFTYPHARMA",
            "AUTO": "NIFTYAUTO",
            "FMCG": "NIFTYFMCG",
            "METALS": "NIFTYMETAL",
            "REALTY": "NIFTYREALTY",
            "MEDIA": "NIFTYMEDIA",
            "PSU BANK": "NIFTYPSUBANK",
            "FINANCIAL SERVICES": "NIFTYFIN"  # placeholder
        }

        index_key = sector_to_index.get(key, None)
        if not index_key:
            raise HTTPException(status_code=404, detail=f"Unsupported sector: {sector}")

        # Get constituents from our index endpoint/cache
        cons_resp = await get_index_constituents(index_key)
        symbols = cons_resp.get("symbols", [])

        top_perf = []
        top_growth = []
        for sym in symbols:
            try:
                q = await data_service.get_quote(sym, "NSE")
                if not q or ('error' in q):
                    continue
                last_price = q.get("last_price") or q.get("lastPrice")
                change_pct = q.get("change_percent") or q.get("pChange")
                target_price = None  # not available from NSE endpoint
                # Top performing by daily % change
                top_perf.append({
                    "symbol": sym,
                    "name": q.get("short_name", sym),
                    "ytd_return": None,  # placeholder
                    "last_price": last_price,
                    "target_price": target_price,
                    "change_percent": change_pct,
                })
                # Top growth proxy: use change_percent as a crude stand-in
                top_growth.append({
                    "symbol": sym,
                    "name": q.get("short_name", sym),
                    "ytd_return": None,
                    "growth_estimate": change_pct,
                })
            except Exception:
                continue

        top_perf.sort(key=lambda x: (x.get("change_percent") or 0), reverse=True)
        top_growth.sort(key=lambda x: (x.get("growth_estimate") or 0), reverse=True)

        payload = {
            "sector_key": key,
            "sector_name": sector.title(),
            "top_performing_companies": top_perf[:10],
            "top_growth_companies": top_growth[:10],
            "updated_at": now.isoformat(),
            "source": "nse_constituents",
        }

        expires = now + timedelta(minutes=max(10, min(ttl_minutes, 60)))
        _industry_cache[key] = (expires, payload)
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building industry summary: {str(e)}")


# ---------- Missing Endpoints for API Compatibility ----------

@router.get("/market-data")
async def get_market_data():
    """Get market data (alias for quotes)"""
    try:
        # Use the existing quotes endpoint
        return await get_batch_quotes(symbols="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data: {str(e)}")

@router.get("/stock-prices")
async def get_stock_prices():
    """Get stock prices (alias for quotes)"""
    try:
        # Use the existing quotes endpoint
        return await get_batch_quotes(symbols="RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stock prices: {str(e)}")

# ---------- Batch quotes (optimize list fetching) ----------

_batch_quotes_cache: Dict[str, Tuple[datetime, List[Dict]]] = {}

@router.get("/quotes")
async def get_batch_quotes(symbols: str, ttl_seconds: int = 60):
    """Return normalized quotes for a comma-separated list of symbols.
    Example: /api/realtime/quotes?symbols=RELIANCE,TCS,INFY
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="symbols is required")

        # Parse and normalize symbols
        requested = [s.strip().upper() for s in symbols.split(',') if s.strip()]
        if not requested:
            raise HTTPException(status_code=400, detail="no valid symbols provided")

        # Cache key is stable ordering
        cache_key = ','.join(sorted(set(requested)))
        now = datetime.utcnow()
        cached = _batch_quotes_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        # Fetch all in parallel
        tasks = [data_service.get_quote(sym, "NSE") for sym in requested]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        normalized: List[Dict] = []
        for sym, res in zip(requested, results):
            try:
                if isinstance(res, Exception) or not res or ('error' in res):
                    continue
                normalized.append({
                    "symbol": sym,
                    "last_price": res.get("last_price") or res.get("lastPrice") or 0,
                    "change": res.get("change") or 0,
                    "change_percent": res.get("change_percent") or res.get("pChange") or 0,
                    "volume": res.get("volume") or res.get("day_volume") or 0,
                    "timestamp": res.get("timestamp") or now.isoformat(),
                    "source": res.get("source", "nse"),
                })
            except Exception:
                continue

        # Cache and return
        expires = now + timedelta(seconds=max(30, min(ttl_seconds, 300)))
        _batch_quotes_cache[cache_key] = (expires, normalized)
        return normalized

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching batch quotes: {str(e)}")


# Auto-generated endpoints for frontend compatibility


