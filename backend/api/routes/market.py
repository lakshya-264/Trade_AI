"""
Market API Routes
Provides index constituents, market screeners, and real-time stock data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

# Static fallbacks (can be replaced with live sources later)
NIFTY50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "HDFC", "ITC", "BHARTIARTL",
    "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID",
    "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA", "EICHERMOT",
    "SHREECEM", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "COALINDIA", "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP",
    "ADANIPORTS", "BPCL", "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", "ADANIENT", "SBILIFE", "HINDALCO"
]

SENSEX = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "ITC", "BHARTIARTL", "SBIN", "ASIANPAINT",
    "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT",
    "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "NESTLEIND", "POWERGRID", "HDFC", "ONGC", "TATASTEEL", "JSWSTEEL", "HINDALCO"
]

# Index mappings with Yahoo Finance support
INDEX_MAP: Dict[str, List[str]] = {
    "NIFTY50": NIFTY50,
    "NIFTY_50": NIFTY50,
    "NIFTY": NIFTY50,
    "SENSEX": SENSEX,
}

# Indexes available on Yahoo Finance
YAHOO_FINANCE_INDEXES = {
    "NIFTY_50": "Nifty 50",
    "NIFTY50": "Nifty 50",
    "NIFTY": "Nifty 50",
    "SENSEX": "SENSEX",
    "NIFTYBANK": "Bank Nifty",
    "NIFTY_BANK": "Bank Nifty",
    "BANKNIFTY": "Bank Nifty",
    "NIFTY_IT": "Nifty IT",
    "NIFTYIT": "Nifty IT",
    "NIFTY_PSU_BANK": "Nifty PSU Bank",
    "NIFTYPSUBANK": "Nifty PSU Bank",
    "NIFTY_AUTO": "Nifty Auto",
    "NIFTYAUTO": "Nifty Auto",
}

@router.get("/index-constituents/{index_id}")
async def get_index_constituents(index_id: str):
    """
    Return index constituents for known indices.
    Tries Yahoo Finance first, falls back to static lists.
    Supports: NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT, NIFTY PSU BANK, NIFTY AUTO
    """
    try:
        key = index_id.upper()
        
        # Try Yahoo Finance first for supported indexes
        if key in YAHOO_FINANCE_INDEXES:
            try:
                from core.yahoo_finance_scraper import YahooFinanceScraper
                scraper = YahooFinanceScraper()
                await scraper._ensure_initialized()
                
                constituents = await scraper.get_index_constituents(key)
                if constituents:
                    return {
                        "success": True,
                        "data": {
                            "index": YAHOO_FINANCE_INDEXES[key],
                            "index_symbol": key,
                            "count": len(constituents),
                            "constituents": constituents,
                            "source": "yahoo_finance",
                            "last_updated": datetime.utcnow().isoformat()
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Constituents for {YAHOO_FINANCE_INDEXES[key]}"
                    }
            except Exception as e:
                logger.warning(f"Yahoo Finance failed for {key}, using fallback: {e}")
        
        # Fallback to static lists
        symbols = INDEX_MAP.get(key)
        if not symbols:
            # Check if it's a Yahoo Finance supported index but not in static map
            if key in YAHOO_FINANCE_INDEXES:
                # Try to get from Yahoo Finance scraper's static method
                try:
                    from core.yahoo_finance_scraper import YahooFinanceScraper
                    scraper = YahooFinanceScraper()
                    constituents = scraper._get_static_constituents(key)
                    if constituents:
                        return {
                            "success": True,
                            "data": {
                                "index": YAHOO_FINANCE_INDEXES[key],
                                "index_symbol": key,
                                "count": len(constituents),
                                "constituents": constituents,
                                "source": "static_fallback",
                                "last_updated": datetime.utcnow().isoformat()
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                            "message": f"Constituents for {YAHOO_FINANCE_INDEXES[key]}"
                        }
                except Exception as e:
                    logger.warning(f"Static fallback failed for {key}: {e}")
            
            raise HTTPException(status_code=404, detail=f"Index '{index_id}' not found or not supported")

        data = [{"symbol": s, "weight": None} for s in symbols]
        return {
            "success": True,
            "data": {
                "index": key,
                "index_symbol": key,
                "count": len(data),
                "constituents": data,
                "source": "static",
                "last_updated": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Constituents for {key}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting constituents for {index_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MARKET SCREENERS WITH REAL DATA ====================

SECTOR_MAP = {
    "Banking": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM"],
    "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "BIOCON", "LUPIN"],
    "Auto": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT"],
    "Oil & Gas": ["RELIANCE", "ONGC", "BPCL", "IOC", "HINDPETRO", "GAIL"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO"],
    "Metals": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "JINDALSTEL", "SAIL"],
    "Telecom": ["BHARTIARTL", "RELIANCE", "VODAFONE", "TATACOMM"]
}

async def get_real_stock_data(symbols: List[str]) -> List[Dict]:
    """Fetch real stock data using data_service"""
    try:
        from core.data_service import data_service
        
        stock_data = []
        for symbol in symbols:
            try:
                quote = await data_service.get_quote(symbol, exchange="NSE")
                if quote and "error" not in quote:
                    stock_data.append({
                        "symbol": symbol,
                        "name": f"{symbol} Limited",
                        "price": float(quote.get("last_price", 0)),
                        "change": float(quote.get("change", 0)),
                        "changePercent": float(quote.get("change_percent", 0)),
                        "volume": int(quote.get("volume", 0)),
                        "marketCap": f"₹{round(float(quote.get('last_price', 0)) * 100000 / 10000000, 1)}L Cr",
                        "sector": _get_sector_for_symbol(symbol),
                        "high": float(quote.get("high", 0)),
                        "low": float(quote.get("low", 0)),
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                continue
        
        return stock_data
    except Exception as e:
        logger.error(f"Error fetching stock data: {e}")
        return []

def _get_sector_for_symbol(symbol: str) -> str:
    """Get sector for a symbol"""
    for sector, symbols in SECTOR_MAP.items():
        if symbol in symbols:
            return sector
    return "Others"

@router.get("/screeners/top-gainers")
async def get_top_gainers(limit: int = Query(default=50, ge=1, le=100)):
    """Get top gaining stocks with real-time data"""
    try:
        # Fetch data for all NIFTY 50 stocks
        stock_data = await get_real_stock_data(NIFTY50)
        
        # Sort by change percent (descending)
        sorted_stocks = sorted(stock_data, key=lambda x: x["changePercent"], reverse=True)
        
        # Return top N
        return {
            "success": True,
            "data": sorted_stocks[:limit],
            "count": len(sorted_stocks[:limit]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting top gainers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screeners/top-losers")
async def get_top_losers(limit: int = Query(default=50, ge=1, le=100)):
    """Get top losing stocks with real-time data"""
    try:
        # Fetch data for all NIFTY 50 stocks
        stock_data = await get_real_stock_data(NIFTY50)
        
        # Sort by change percent (ascending)
        sorted_stocks = sorted(stock_data, key=lambda x: x["changePercent"])
        
        # Return top N losers
        return {
            "success": True,
            "data": sorted_stocks[:limit],
            "count": len(sorted_stocks[:limit]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting top losers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screeners/volume-shockers")
async def get_volume_shockers(limit: int = Query(default=50, ge=1, le=100)):
    """Get stocks with unusual volume activity"""
    try:
        # Fetch data for all NIFTY 50 stocks
        stock_data = await get_real_stock_data(NIFTY50)
        
        # Sort by volume (descending)
        sorted_stocks = sorted(stock_data, key=lambda x: x["volume"], reverse=True)
        
        # Return top N by volume
        return {
            "success": True,
            "data": sorted_stocks[:limit],
            "count": len(sorted_stocks[:limit]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting volume shockers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screeners/most-active")
async def get_most_active(limit: int = Query(default=50, ge=1, le=100)):
    """Get most actively traded stocks"""
    try:
        # Same as volume shockers for now
        return await get_volume_shockers(limit)
    except Exception as e:
        logger.error(f"Error getting most active: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screeners/only-buyers")
async def get_only_buyers(limit: int = Query(default=50, ge=1, le=100)):
    """Get stocks with only buy orders (strong positive momentum)"""
    try:
        # Fetch data for all NIFTY 50 stocks
        stock_data = await get_real_stock_data(NIFTY50)
        
        # Filter stocks with positive change > 3%
        buyers_stocks = [s for s in stock_data if s["changePercent"] > 3.0]
        
        # Sort by change percent
        sorted_stocks = sorted(buyers_stocks, key=lambda x: x["changePercent"], reverse=True)
        
        return {
            "success": True,
            "data": sorted_stocks[:limit],
            "count": len(sorted_stocks[:limit]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting only buyers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screeners/only-sellers")
async def get_only_sellers(limit: int = Query(default=50, ge=1, le=100)):
    """Get stocks with only sell orders (strong negative momentum)"""
    try:
        # Fetch data for all NIFTY 50 stocks
        stock_data = await get_real_stock_data(NIFTY50)
        
        # Filter stocks with negative change < -3%
        sellers_stocks = [s for s in stock_data if s["changePercent"] < -3.0]
        
        # Sort by change percent
        sorted_stocks = sorted(sellers_stocks, key=lambda x: x["changePercent"])
        
        return {
            "success": True,
            "data": sorted_stocks[:limit],
            "count": len(sorted_stocks[:limit]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting only sellers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indices/live")
async def get_live_indices():
    """Get live data for major indices"""
    try:
        from core.data_service import data_service
        
        indices_data = []
        indices = [
            {"symbol": "NIFTY_50", "name": "NIFTY 50"},
            {"symbol": "SENSEX", "name": "SENSEX"},
            {"symbol": "NIFTY_BANK", "name": "BANK NIFTY"},
            {"symbol": "NIFTY_IT", "name": "NIFTY IT"}
        ]
        
        for index in indices:
            try:
                quote = await data_service.get_quote(index["symbol"], exchange="NSE")
                if quote and "error" not in quote:
                    indices_data.append({
                        "name": index["name"],
                        "value": float(quote.get("last_price", 0)),
                        "change": float(quote.get("change", 0)),
                        "changePercent": float(quote.get("change_percent", 0))
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch {index['symbol']}: {e}")
                continue
        
        return {
            "success": True,
            "data": indices_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting live indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


