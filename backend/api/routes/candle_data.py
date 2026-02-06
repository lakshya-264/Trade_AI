"""
Candlestick Data API Routes
Provides historical OHLCV candle data for charting
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/candles/{symbol}")
async def get_candle_data(
    symbol: str,
    interval: str = Query(default="1d", description="Candle interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"),
    range: str = Query(default="1mo", description="Time range: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max")
):
    """
    Get historical candlestick (OHLCV) data for a symbol
    
    Example:
        GET /api/candles/RELIANCE?interval=1d&range=1mo
        GET /api/candles/NIFTY_50?interval=1h&range=5d
    """
    try:
        from core.yahoo_finance_scraper import yahoo_finance_scraper
        
        logger.info(f"📊 Fetching candles for {symbol} ({interval}, {range})")
        
        # Get candle data from Yahoo Finance
        candles = await yahoo_finance_scraper.get_historical_candles(
            symbol=symbol,
            interval=interval,
            range_period=range
        )
        
        if not candles:
            return {
                "success": False,
                "message": f"No candle data available for {symbol}",
                "data": [],
                "count": 0
            }
        
        return {
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "range": range,
            "data": candles,
            "count": len(candles),
            "timestamp": datetime.now().isoformat(),
            "data_source": "YAHOO_FINANCE_API"
        }
        
    except Exception as e:
        logger.error(f"Error getting candle data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles/{symbol}/latest")
async def get_latest_candle(
    symbol: str,
    interval: str = Query(default="1d", description="Candle interval")
):
    """
    Get the latest (most recent) candle for a symbol
    
    Example:
        GET /api/candles/RELIANCE/latest?interval=1d
    """
    try:
        from core.yahoo_finance_scraper import yahoo_finance_scraper
        
        # Get recent candles (last 2)
        candles = await yahoo_finance_scraper.get_historical_candles(
            symbol=symbol,
            interval=interval,
            range_period="1d"
        )
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "message": f"No candle data available for {symbol}",
                "data": None
            }
        
        # Return the most recent candle
        latest_candle = candles[-1]
        
        return {
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "data": latest_candle,
            "timestamp": datetime.now().isoformat(),
            "data_source": "YAHOO_FINANCE_API"
        }
        
    except Exception as e:
        logger.error(f"Error getting latest candle for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles/{symbol}/ohlc")
async def get_ohlc_summary(
    symbol: str,
    interval: str = Query(default="1d"),
    range: str = Query(default="1mo")
):
    """
    Get OHLC summary statistics
    
    Returns:
        - First candle (open)
        - Last candle (close)
        - Highest candle
        - Lowest candle
        - Total volume
    """
    try:
        from core.yahoo_finance_scraper import yahoo_finance_scraper
        
        candles = await yahoo_finance_scraper.get_historical_candles(
            symbol=symbol,
            interval=interval,
            range_period=range
        )
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "message": f"No candle data available for {symbol}"
            }
        
        # Calculate summary
        first_candle = candles[0]
        last_candle = candles[-1]
        
        highest_candle = max(candles, key=lambda x: x['high'])
        lowest_candle = min(candles, key=lambda x: x['low'])
        
        total_volume = sum(c['volume'] for c in candles)
        avg_volume = total_volume / len(candles) if len(candles) > 0 else 0
        
        price_change = last_candle['close'] - first_candle['open']
        price_change_percent = (price_change / first_candle['open'] * 100) if first_candle['open'] > 0 else 0
        
        return {
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "range": range,
            "candle_count": len(candles),
            "summary": {
                "first_open": first_candle['open'],
                "last_close": last_candle['close'],
                "highest_high": highest_candle['high'],
                "lowest_low": lowest_candle['low'],
                "total_volume": total_volume,
                "average_volume": round(avg_volume, 2),
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2)
            },
            "first_candle": first_candle,
            "last_candle": last_candle,
            "highest_candle": highest_candle,
            "lowest_candle": lowest_candle,
            "timestamp": datetime.now().isoformat(),
            "data_source": "YAHOO_FINANCE_API"
        }
        
    except Exception as e:
        logger.error(f"Error getting OHLC summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles/available-intervals")
async def get_available_intervals():
    """Get list of available candle intervals"""
    return {
        "success": True,
        "intervals": [
            {"value": "1m", "label": "1 Minute", "description": "1-minute candles"},
            {"value": "5m", "label": "5 Minutes", "description": "5-minute candles"},
            {"value": "15m", "label": "15 Minutes", "description": "15-minute candles"},
            {"value": "30m", "label": "30 Minutes", "description": "30-minute candles"},
            {"value": "1h", "label": "1 Hour", "description": "Hourly candles"},
            {"value": "1d", "label": "1 Day", "description": "Daily candles"},
            {"value": "1wk", "label": "1 Week", "description": "Weekly candles"},
            {"value": "1mo", "label": "1 Month", "description": "Monthly candles"}
        ],
        "ranges": [
            {"value": "1d", "label": "1 Day"},
            {"value": "5d", "label": "5 Days"},
            {"value": "1mo", "label": "1 Month"},
            {"value": "3mo", "label": "3 Months"},
            {"value": "6mo", "label": "6 Months"},
            {"value": "1y", "label": "1 Year"},
            {"value": "2y", "label": "2 Years"},
            {"value": "5y", "label": "5 Years"},
            {"value": "10y", "label": "10 Years"},
            {"value": "ytd", "label": "Year to Date"},
            {"value": "max", "label": "Maximum Available"}
        ]
    }

