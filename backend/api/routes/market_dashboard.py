"""
Market Dashboard API - Using Web Scraper Data
Provides real-time stock data for the dashboard using the same scraper as Stock Browser
"""

from fastapi import APIRouter, Query
from typing import List, Dict
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()

# Import the working data service
from core.data_service import data_service

# Top stocks to display
NIFTY50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", 
    "ITC", "BHARTIARTL", "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", 
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID", "NTPC", "TECHM", 
    "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA"
]

SECTOR_MAP = {
    "Banking": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
    "Pharma": ["SUNPHARMA", "DRREDDY"],
    "Auto": ["MARUTI", "TATAMOTORS"],
    "Oil & Gas": ["RELIANCE", "ONGC", "BPCL"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA"],
    "Telecom": ["BHARTIARTL"]
}

def _get_sector(symbol: str) -> str:
    """Get sector for symbol"""
    for sector, symbols in SECTOR_MAP.items():
        if symbol in symbols:
            return sector
    return "Others"

async def fetch_stock_data(symbols: List[str]) -> List[Dict]:
    """Fetch real stock data using web scraper"""
    stock_data = []
    
    for symbol in symbols:
        try:
            # Use the same method as Stock Browser
            quote = await data_service.get_quote(symbol, exchange="NSE")
            
            if quote and "error" not in quote:
                price = float(quote.get("last_price", 0))
                change = float(quote.get("change", 0))
                change_percent = float(quote.get("change_percent", 0))
                
                stock_data.append({
                    "symbol": symbol,
                    "name": f"{symbol}",
                    "price": price,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": int(quote.get("volume", 0)),
                    "marketCap": f"₹{round(price * 100000 / 10000000, 1)}L Cr",
                    "sector": _get_sector(symbol),
                    "high": float(quote.get("high", 0)),
                    "low": float(quote.get("low", 0)),
                })
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            continue
    
    return stock_data

@router.get("/dashboard/top-gainers")
async def get_top_gainers_dashboard(limit: int = Query(default=100, ge=1, le=500)):
    """Get top gaining stocks - Returns all available gainers"""
    try:
        # Fetch data for NIFTY stocks
        stock_data = await fetch_stock_data(NIFTY50)
        
        # Sort by change percent (descending) - Get ALL gainers
        sorted_stocks = sorted(
            [s for s in stock_data if s["changePercent"] > 0],
            key=lambda x: x["changePercent"],
            reverse=True
        )
        
        # Return all stocks up to limit
        result_data = sorted_stocks[:limit] if limit < len(sorted_stocks) else sorted_stocks
        
        return {
            "success": True,
            "data": result_data,
            "count": len(result_data),
            "total_available": len(sorted_stocks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting top gainers: {e}")
        return {"success": False, "data": [], "error": str(e)}

@router.get("/dashboard/top-losers")
async def get_top_losers_dashboard(limit: int = Query(default=100, ge=1, le=500)):
    """Get top losing stocks - Returns all available losers"""
    try:
        stock_data = await fetch_stock_data(NIFTY50)
        
        # Sort by change percent (ascending - most negative) - Get ALL losers
        sorted_stocks = sorted(
            [s for s in stock_data if s["changePercent"] < 0],
            key=lambda x: x["changePercent"]
        )
        
        # Return all stocks up to limit
        result_data = sorted_stocks[:limit] if limit < len(sorted_stocks) else sorted_stocks
        
        return {
            "success": True,
            "data": result_data,
            "count": len(result_data),
            "total_available": len(sorted_stocks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting top losers: {e}")
        return {"success": False, "data": [], "error": str(e)}

@router.get("/dashboard/only-buyers")
async def get_only_buyers_dashboard(limit: int = Query(default=100, ge=1, le=500)):
    """Get stocks with only buyers (high positive change) - Returns all available"""
    try:
        stock_data = await fetch_stock_data(NIFTY50)
        
        # Filter stocks with change > 1% (more inclusive)
        sorted_stocks = sorted(
            [s for s in stock_data if s["changePercent"] > 1.0],
            key=lambda x: x["changePercent"],
            reverse=True
        )
        
        # Return all stocks up to limit
        result_data = sorted_stocks[:limit] if limit < len(sorted_stocks) else sorted_stocks
        
        return {
            "success": True,
            "data": result_data,
            "count": len(result_data),
            "total_available": len(sorted_stocks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting only buyers: {e}")
        return {"success": False, "data": [], "error": str(e)}

@router.get("/dashboard/only-sellers")
async def get_only_sellers_dashboard(limit: int = Query(default=100, ge=1, le=500)):
    """Get stocks with only sellers (high negative change) - Returns all available"""
    try:
        stock_data = await fetch_stock_data(NIFTY50)
        
        # Filter stocks with change < -1% (more inclusive)
        sorted_stocks = sorted(
            [s for s in stock_data if s["changePercent"] < -1.0],
            key=lambda x: x["changePercent"]
        )
        
        # Return all stocks up to limit
        result_data = sorted_stocks[:limit] if limit < len(sorted_stocks) else sorted_stocks
        
        return {
            "success": True,
            "data": result_data,
            "count": len(result_data),
            "total_available": len(sorted_stocks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting only sellers: {e}")
        return {"success": False, "data": [], "error": str(e)}

@router.get("/dashboard/volume-shockers")
async def get_volume_shockers_dashboard(limit: int = Query(default=100, ge=1, le=500)):
    """Get stocks with high volume - Returns all available"""
    try:
        stock_data = await fetch_stock_data(NIFTY50)
        
        # Sort by volume (descending) - Get ALL stocks sorted by volume
        sorted_stocks = sorted(
            stock_data,
            key=lambda x: x["volume"],
            reverse=True
        )
        
        # Return all stocks up to limit
        result_data = sorted_stocks[:limit] if limit < len(sorted_stocks) else sorted_stocks
        
        return {
            "success": True,
            "data": result_data,
            "count": len(result_data),
            "total_available": len(sorted_stocks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting volume shockers: {e}")
        return {"success": False, "data": [], "error": str(e)}

@router.get("/dashboard/most-active")
async def get_most_active_dashboard(limit: int = Query(default=100, ge=1, le=500)):
    """Get most active stocks by volume - Returns all available"""
    try:
        stock_data = await fetch_stock_data(NIFTY50)
        
        # Sort by volume (descending) - Get ALL stocks sorted by volume
        sorted_stocks = sorted(
            stock_data,
            key=lambda x: x["volume"],
            reverse=True
        )
        
        # Return all stocks up to limit
        result_data = sorted_stocks[:limit] if limit < len(sorted_stocks) else sorted_stocks
        
        return {
            "success": True,
            "data": result_data,
            "count": len(result_data),
            "total_available": len(sorted_stocks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting most active: {e}")
        return {"success": False, "data": [], "error": str(e)}

@router.get("/dashboard/indices")
async def get_indices_dashboard():
    """Get live indices data using Yahoo Finance"""
    try:
        indices = []
        index_symbols = [
            ("NIFTY 50", "NIFTY_50"),
            ("SENSEX", "SENSEX"),
            ("BANK NIFTY", "NIFTY_BANK"),
            ("NIFTY IT", "NIFTY_IT")
        ]
        
        for name, symbol in index_symbols:
            try:
                # Fetch real index data from Yahoo Finance via data_service
                logger.info(f"Fetching index data for {name} ({symbol})")
                quote = await data_service.get_quote(symbol, exchange="NSE")
                
                if quote and "error" not in quote and quote.get("last_price", 0) > 0:
                    indices.append({
                        "name": name,
                        "value": round(float(quote.get("last_price", 0)), 2),
                        "change": round(float(quote.get("change", 0)), 2),
                        "changePercent": round(float(quote.get("change_percent", 0)), 2),
                        "data_source": quote.get("data_source", "unknown")
                    })
                    logger.info(f"✅ {name}: {quote.get('last_price')}")
                else:
                    logger.warning(f"⚠️  Failed to fetch {name}: Invalid data")
            except Exception as e:
                logger.warning(f"Failed to fetch {name}: {e}")
                continue
        
        # Add fallback dummy data only if ALL indices failed
        if not indices:
            logger.warning("⚠️  All index data failed, using fallback values")
            indices = [
                {"name": "NIFTY 50", "value": 19500.0, "change": 50.0, "changePercent": 0.26, "data_source": "fallback"},
                {"name": "SENSEX", "value": 65000.0, "change": 150.0, "changePercent": 0.23, "data_source": "fallback"},
            ]
        
        return {
            "success": True,
            "data": indices,
            "count": len(indices),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting indices: {e}")
        return {"success": False, "data": [], "error": str(e)}

