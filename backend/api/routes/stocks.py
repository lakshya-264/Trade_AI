"""
NSE & BSE Stock List API Routes
Provides comprehensive stock data from web scrapers
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from core.nse_bse_stock_scraper import nse_bse_scraper
from core.api_utils import api_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/all")
async def get_all_stocks(
    force_refresh: bool = Query(False, description="Bypass in-memory cache and re-fetch lists")
):
    """Get complete list of all NSE and BSE stocks"""
    try:
        logger.info("📊 Fetching all NSE & BSE stocks...")

        if force_refresh:
            try:
                nse_bse_scraper.stock_cache.pop("nse_stocks", None)
                nse_bse_scraper.stock_cache.pop("bse_stocks", None)
            except Exception:
                pass
        
        stocks_data = await nse_bse_scraper.get_all_stocks()
        
        return api_response(
            data=stocks_data,
            message=f"Successfully fetched {stocks_data['total_stocks']} stocks",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error fetching all stocks: {e}")
        return handle_api_error(e, "get_all_stocks")

@router.get("/nse")
async def get_nse_stocks(
    force_refresh: bool = Query(False, description="Bypass in-memory cache and re-fetch list")
):
    """Get complete list of NSE stocks"""
    try:
        logger.info("📈 Fetching NSE stocks...")

        if force_refresh:
            try:
                nse_bse_scraper.stock_cache.pop("nse_stocks", None)
            except Exception:
                pass
        
        nse_stocks = await nse_bse_scraper.get_nse_stock_list()
        
        return api_response(
            data={
                'stocks': nse_stocks,
                'total': len(nse_stocks),
                'exchange': 'NSE',
                'last_updated': datetime.now().isoformat()
            },
            message=f"Successfully fetched {len(nse_stocks)} NSE stocks",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error fetching NSE stocks: {e}")
        return handle_api_error(e, "get_nse_stocks")

@router.get("/bse")
async def get_bse_stocks():
    """Get complete list of BSE stocks"""
    try:
        logger.info("📈 Fetching BSE stocks...")
        
        bse_stocks = await nse_bse_scraper.get_bse_stock_list()
        
        return api_response(
            data={
                'stocks': bse_stocks,
                'total': len(bse_stocks),
                'exchange': 'BSE',
                'last_updated': datetime.now().isoformat()
            },
            message=f"Successfully fetched {len(bse_stocks)} BSE stocks",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error fetching BSE stocks: {e}")
        return handle_api_error(e, "get_bse_stocks")

@router.get("/search")
async def search_stocks(
    query: str = Query(..., description="Search term (symbol or company name)"),
    exchange: str = Query("ALL", description="Exchange filter: NSE, BSE, or ALL"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Search stocks by symbol or company name"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        logger.info(f"🔍 Searching stocks: '{query}' in {exchange}")
        
        results = await nse_bse_scraper.search_stocks(query.strip(), exchange)
        
        # Limit results
        limited_results = results[:limit]
        
        return api_response(
            data={
                'stocks': limited_results,
                'total_found': len(results),
                'returned': len(limited_results),
                'query': query,
                'exchange': exchange,
                'last_updated': datetime.now().isoformat()
            },
            message=f"Found {len(results)} stocks matching '{query}'",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return handle_api_error(e, "search_stocks")

@router.get("/{symbol}")
async def get_stock_details(
    symbol: str,
    exchange: str = Query("ALL", description="Exchange filter: NSE, BSE, or ALL")
):
    """Get detailed information for a specific stock"""
    try:
        logger.info(f"📊 Getting details for {symbol} from {exchange}")
        
        stock_details = await nse_bse_scraper.get_stock_by_symbol(symbol, exchange)
        
        if not stock_details:
            raise HTTPException(
                status_code=404, 
                detail=f"Stock '{symbol}' not found in {exchange}"
            )
        
        return api_response(
            data=stock_details,
            message=f"Successfully fetched details for {symbol}",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock details: {e}")
        return handle_api_error(e, "get_stock_details")

@router.get("/sectors")
async def get_stocks_by_sector():
    """Get stocks grouped by sector"""
    try:
        logger.info("🏭 Fetching stocks grouped by sector...")
        
        all_stocks = await nse_bse_scraper.get_all_stocks()
        
        sectors = {}
        
        # Group NSE stocks by sector
        for stock in all_stocks['nse']:
            sector = stock.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = {'nse': [], 'bse': []}
            sectors[sector]['nse'].append(stock)
        
        # Group BSE stocks by sector
        for stock in all_stocks['bse']:
            sector = stock.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = {'nse': [], 'bse': []}
            sectors[sector]['bse'].append(stock)
        
        # Calculate totals
        sector_summary = {}
        for sector, stocks in sectors.items():
            sector_summary[sector] = {
                'nse_count': len(stocks['nse']),
                'bse_count': len(stocks['bse']),
                'total_count': len(stocks['nse']) + len(stocks['bse']),
                'stocks': stocks
            }
        
        return api_response(
            data={
                'sectors': sector_summary,
                'total_sectors': len(sectors),
                'last_updated': datetime.now().isoformat()
            },
            message=f"Successfully grouped stocks by {len(sectors)} sectors",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error getting stocks by sector: {e}")
        return handle_api_error(e, "get_stocks_by_sector")

@router.get("/top-by-marketcap")
async def get_top_stocks_by_marketcap(
    limit: int = Query(50, description="Number of top stocks to return"),
    exchange: str = Query("ALL", description="Exchange filter: NSE, BSE, or ALL")
):
    """Get top stocks by market capitalization"""
    try:
        logger.info(f"💰 Fetching top {limit} stocks by market cap from {exchange}")
        
        all_stocks = await nse_bse_scraper.get_all_stocks()
        
        # Combine all stocks
        all_stocks_list = []
        if exchange in ['ALL', 'NSE']:
            all_stocks_list.extend(all_stocks['nse'])
        if exchange in ['ALL', 'BSE']:
            all_stocks_list.extend(all_stocks['bse'])
        
        # Sort by market cap (descending)
        sorted_stocks = sorted(
            all_stocks_list, 
            key=lambda x: x.get('market_cap', 0), 
            reverse=True
        )
        
        # Limit results
        top_stocks = sorted_stocks[:limit]
        
        return api_response(
            data={
                'stocks': top_stocks,
                'total_returned': len(top_stocks),
                'exchange': exchange,
                'last_updated': datetime.now().isoformat()
            },
            message=f"Successfully fetched top {len(top_stocks)} stocks by market cap",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error getting top stocks by market cap: {e}")
        return handle_api_error(e, "get_top_stocks_by_marketcap")
