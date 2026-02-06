"""
Financial Data API Routes
Manage financial data, ratios, and filings
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging
import base64
from io import BytesIO
import numpy as np

from core.database import get_db
from core.auth_dependencies import get_current_user_optional
from core.database_unified import FinancialData, FinancialRatios, StockMaster
from services.financial_ratios_service import financial_ratios_service
from services.stock_master_service import stock_master_service
from services.nse_filings_scraper import nse_filings_scraper
from services.financial_data_parser import financial_data_parser
from services.research_report_generator import research_report_generator
from services.financial_projection_service import financial_projection_service
from services.screener_scraper import screener_scraper
from services.screener_data_service import screener_data_service
from services.nifty50_financial_sync import nifty50_financial_sync
from core.data_service import data_service

logger = logging.getLogger(__name__)

router = APIRouter()

def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON serialization.
    Handles numpy.bool_, numpy.bool, numpy.int64, numpy.float64, numpy.ndarray, etc.
    This MUST be called before FastAPI's jsonable_encoder to prevent serialization errors.
    """
    # Handle None first
    if obj is None:
        return None
    
    # CRITICAL: Check for numpy types FIRST, before any other type checks
    # This prevents FastAPI from trying to iterate over numpy.bool_ objects
    
    # Method 1: Check by isinstance (most reliable for known numpy types)
    try:
        # Check for numpy.bool_ first (most common error case)
        if isinstance(obj, np.bool_) or (hasattr(np, 'bool8') and isinstance(obj, np.bool8)):
            return bool(obj)
        
        # Check for numpy integers
        if isinstance(obj, np.integer):
            return int(obj)
        
        # Check for numpy floats
        if isinstance(obj, np.floating):
            return float(obj)
        
        # Check for numpy complex
        if isinstance(obj, np.complexfloating):
            return complex(obj)
        
        # Check for numpy generic (catches all numpy scalars)
        if isinstance(obj, np.generic):
            try:
                result = obj.item()
                # Recursively convert in case item() returns another numpy type
                return convert_numpy_types(result)
            except (AttributeError, ValueError, TypeError):
                # Fallback: try direct conversion
                if 'bool' in str(type(obj)).lower():
                    return bool(obj)
                elif 'int' in str(type(obj)).lower():
                    return int(obj)
                elif 'float' in str(type(obj)).lower():
                    return float(obj)
                else:
                    return str(obj)  # Last resort
    except Exception:
        pass  # Continue to other checks
    
    # Method 2: Check by type string and module (catches edge cases)
    try:
        type_str = str(type(obj))
        type_module = type(obj).__module__ if hasattr(type(obj), '__module__') else ''
        type_name = type(obj).__name__ if hasattr(type(obj), '__name__') else ''
        
        # Check if it's a NumPy type by module or type string
        if 'numpy' in type_module.lower() or 'numpy' in type_str.lower() or type_name in ('bool_', 'bool8', 'int64', 'int32', 'float64', 'float32', 'bool'):
            # Try .item() method first (works for most numpy scalars including numpy.bool_)
            if hasattr(obj, 'item'):
                try:
                    result = obj.item()
                    # Recursively convert in case item() returns another numpy type
                    return convert_numpy_types(result)
                except (AttributeError, ValueError, TypeError):
                    pass
            
            # Explicit conversion based on type string (handles numpy.bool_ specifically)
            if 'bool' in type_str.lower() or type_name in ('bool_', 'bool8', 'bool'):
                return bool(obj)
            elif 'int' in type_str.lower() or type_name.startswith('int'):
                return int(obj)
            elif 'float' in type_str.lower() or type_name.startswith('float'):
                return float(obj)
            elif 'complex' in type_str.lower():
                return complex(obj)
    except Exception:
        pass  # Continue to other checks
    
    # Handle NumPy arrays (must check before dict/list)
    try:
        if isinstance(obj, np.ndarray):
            return [convert_numpy_types(item) for item in obj.tolist()]
    except Exception:
        pass
    
    # Handle pandas types
    try:
        if hasattr(obj, 'to_dict'):
            return convert_numpy_types(obj.to_dict())
    except Exception:
        pass
    
    # Recursively handle collections (do this AFTER all NumPy checks)
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    
    return obj

@router.get("/debug/db-info")
async def debug_db_info(
    symbol: str = Query("RELIANCE", description="Symbol to count rows for"),
    db: Session = Depends(get_db),
):
    """
    Debug helper to verify which database the running API is connected to,
    and whether required rows exist for report generation.
    """
    try:
        from core.database_unified import DATABASE_URL

        sym = (symbol or "").upper().strip()
        q_financial = (
            db.query(FinancialData)
            .filter(FinancialData.symbol == sym, FinancialData.period_type == "QUARTERLY")
            .count()
        )
        a_financial = (
            db.query(FinancialData)
            .filter(FinancialData.symbol == sym, FinancialData.period_type == "ANNUAL")
            .count()
        )
        ratios = db.query(FinancialRatios).filter(FinancialRatios.symbol == sym).count()

        return {
            "success": True,
            "data": {
                "database_url": DATABASE_URL,
                "symbol": sym,
                "counts": {
                    "financial_data_quarterly": q_financial,
                    "financial_data_annual": a_financial,
                    "financial_ratios": ratios,
                },
            },
            "message": "DB info",
        }
    except Exception as e:
        logger.error(f"Error in debug_db_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock-master")
async def get_stock_master(
    exchange: Optional[str] = Query(None, description="Filter by exchange (NSE/BSE)"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get stock master list"""
    try:
        stocks = stock_master_service.get_stock_master(exchange=exchange, sector=sector)
        return {
            "success": True,
            "data": stocks,
            "count": len(stocks),
            "message": "Stock master list retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting stock master: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock-master/recently-added")
async def get_recently_added_stocks(
    limit: int = Query(20, description="Number of recently added stocks to return", ge=1, le=100),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    exchange: Optional[str] = Query(None, description="Filter by exchange (NSE, BSE)"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get recently added stocks from StockMaster table.
    Returns stocks added within the specified number of days, sorted by creation date (newest first).
    """
    try:
        from datetime import timedelta
        
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = db.query(StockMaster).filter(
            StockMaster.created_at >= cutoff_date
        )
        
        # Apply exchange filter if provided
        if exchange:
            query = query.filter(StockMaster.exchange == exchange.upper())
        
        # Order by created_at descending (newest first) and limit
        recently_added = query.order_by(StockMaster.created_at.desc()).limit(limit).all()
        
        # Convert to dict format
        stocks_data = []
        for stock in recently_added:
            stocks_data.append({
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "exchange": stock.exchange,
                "sector": stock.sector,
                "sub_sector": stock.sub_sector,
                "industry": stock.industry,
                "market_cap": float(stock.market_cap) if stock.market_cap else None,
                "listing_date": stock.listing_date.isoformat() if stock.listing_date else None,
                "created_at": stock.created_at.isoformat() if stock.created_at else None,
                "updated_at": stock.updated_at.isoformat() if stock.updated_at else None,
                "days_since_added": (datetime.utcnow() - stock.created_at).days if stock.created_at else None
            })
        
        return {
            "success": True,
            "data": {
                "stocks": stocks_data,
                "total": len(stocks_data),
                "limit": limit,
                "days": days,
                "exchange": exchange or "ALL",
                "cutoff_date": cutoff_date.isoformat()
            },
            "message": f"Found {len(stocks_data)} recently added stocks"
        }
    except Exception as e:
        logger.error(f"Error getting recently added stocks: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stock-master/sync")
async def sync_stock_master(
    exchange: str = Query("NSE", description="Exchange to sync (NSE/BSE)"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Sync stock master list from NSE/BSE"""
    try:
        result = await stock_master_service.sync_stock_master(exchange=exchange)
        return {
            "success": result.get("success", False),
            "data": result,
            "message": f"Stock master sync completed for {exchange}"
        }
    except Exception as e:
        logger.error(f"Error syncing stock master: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stock-master/add-custom")
async def add_custom_stocks(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Add custom stocks to StockMaster table"""
    try:
        # Custom stocks to add
        custom_stocks = [
            {"symbol": "NMDC", "name": "NMDC Limited", "sector": "Steel", "exchange": "NSE"},
            {"symbol": "INFIBEAM", "name": "Infibeam Avenues Limited", "sector": "IT", "exchange": "NSE"},
            {"symbol": "INDIANREN", "name": "Indian Renewable Energy Development Agency", "sector": "Power", "exchange": "NSE"},
            {"symbol": "BSE", "name": "BSE Limited", "sector": "Financial Services", "exchange": "NSE"},
            {"symbol": "TANLA", "name": "Tanla Platforms Limited", "sector": "IT", "exchange": "NSE"},
            {"symbol": "BIRLASOFT", "name": "Birlasoft Limited", "sector": "IT", "exchange": "NSE"},
            {"symbol": "COALINDIA", "name": "Coal India Limited", "sector": "Mining", "exchange": "NSE"},
            {"symbol": "SUZLON", "name": "Suzlon Energy Limited", "sector": "Power", "exchange": "NSE"},
            {"symbol": "SAKSOFT", "name": "Saksoft Limited", "sector": "IT", "exchange": "NSE"},
            {"symbol": "GAIL", "name": "GAIL (India) Limited", "sector": "Oil & Gas", "exchange": "NSE"},
            {"symbol": "ADANIGREEN", "name": "Adani Green Energy Limited", "sector": "Power", "exchange": "NSE"},
            {"symbol": "NHPC", "name": "NHPC Limited", "sector": "Power", "exchange": "NSE"},
            {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Limited", "sector": "Infrastructure", "exchange": "NSE"},
            {"symbol": "IRFC", "name": "Indian Railway Finance Corporation Limited", "sector": "Financial Services", "exchange": "NSE"},
            {"symbol": "IRB", "name": "IRB Infrastructure Developers Limited", "sector": "Infrastructure", "exchange": "NSE"},
            {"symbol": "BAJAJHLDNG", "name": "Bajaj Housing Finance Limited", "sector": "Financial Services", "exchange": "NSE"},
            {"symbol": "HGIEL", "name": "Hindustan Green Energy Limited", "sector": "Power", "exchange": "NSE"},
        ]
        
        created_count = 0
        updated_count = 0
        
        for stock_data in custom_stocks:
            try:
                symbol = stock_data["symbol"].upper()
                
                # Check if stock already exists
                existing = db.query(StockMaster).filter(
                    StockMaster.symbol == symbol,
                    StockMaster.exchange == stock_data["exchange"]
                ).first()
                
                if existing:
                    # Update existing
                    existing.company_name = stock_data["name"]
                    existing.sector = stock_data["sector"]
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new entry
                    stock = StockMaster(
                        symbol=symbol,
                        company_name=stock_data["name"],
                        exchange=stock_data["exchange"],
                        sector=stock_data["sector"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    created_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing {stock_data.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Custom stocks added: {created_count} created, {updated_count} updated",
            "data": {
                "created": created_count,
                "updated": updated_count,
                "total": created_count + updated_count
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding custom stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/financial-data/{symbol}")
async def get_financial_data(
    symbol: str,
    period_type: Optional[str] = Query(None, description="QUARTERLY or ANNUAL"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get financial data for a symbol"""
    try:
        query = db.query(FinancialData).filter(FinancialData.symbol == symbol.upper())
        
        if period_type:
            query = query.filter(FinancialData.period_type == period_type.upper())
        
        financial_data = query.order_by(FinancialData.period_end.desc()).all()
        
        return {
            "success": True,
            "data": [
                {
                    "symbol": fd.symbol,
                    "period_type": fd.period_type,
                    "period_end": fd.period_end.isoformat() if fd.period_end else None,
                    "revenue": float(fd.revenue) if fd.revenue else None,
                    "net_profit": float(fd.net_profit) if fd.net_profit else None,
                    "net_worth": float(fd.net_worth) if fd.net_worth else None,
                    "eps": float(fd.eps) if fd.eps else None,
                    "book_value": float(fd.book_value) if fd.book_value else None,
                    "filing_date": fd.filing_date.isoformat() if fd.filing_date else None
                }
                for fd in financial_data
            ],
            "count": len(financial_data),
            "message": f"Financial data retrieved for {symbol}"
        }
    except Exception as e:
        logger.error(f"Error getting financial data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/financial-ratios/{symbol}")
async def get_financial_ratios(
    symbol: str,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get financial ratios for a symbol"""
    try:
        # Get latest ratios from database
        latest_ratios = db.query(FinancialRatios).filter(
            FinancialRatios.symbol == symbol.upper()
        ).order_by(FinancialRatios.period_end.desc()).first()
        
        if not latest_ratios:
            return {
                "success": False,
                "data": None,
                "message": f"No financial ratios found for {symbol}"
            }
        
        return {
            "success": True,
            "data": {
                "symbol": latest_ratios.symbol,
                "period_end": latest_ratios.period_end.isoformat() if latest_ratios.period_end else None,
                "current_price": float(latest_ratios.current_price) if latest_ratios.current_price else None,
                "pe_ratio": float(latest_ratios.pe_ratio) if latest_ratios.pe_ratio else None,
                "pb_ratio": float(latest_ratios.pb_ratio) if latest_ratios.pb_ratio else None,
                "roe": float(latest_ratios.roe) if latest_ratios.roe else None,
                "roce": float(latest_ratios.roce) if latest_ratios.roce else None,
                "debt_to_equity": float(latest_ratios.debt_to_equity) if latest_ratios.debt_to_equity else None,
                "current_ratio": float(latest_ratios.current_ratio) if latest_ratios.current_ratio else None,
                "operating_margin": float(latest_ratios.operating_margin) if latest_ratios.operating_margin else None,
                "profit_growth_5y": float(latest_ratios.profit_growth_5y) if latest_ratios.profit_growth_5y else None,
                "revenue_growth_5y": float(latest_ratios.revenue_growth_5y) if latest_ratios.revenue_growth_5y else None
            },
            "message": f"Financial ratios retrieved for {symbol}"
        }
    except Exception as e:
        logger.error(f"Error getting financial ratios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/financial-ratios/calculate/{symbol}")
async def calculate_financial_ratios(
    symbol: str,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Calculate and store financial ratios for a symbol"""
    try:
        # Get latest financial data
        financial_data = db.query(FinancialData).filter(
            FinancialData.symbol == symbol.upper()
        ).order_by(FinancialData.period_end.desc()).first()
        
        if not financial_data:
            raise HTTPException(status_code=404, detail=f"No financial data found for {symbol}")
        
        # Get current price
        quote = await data_service.get_quote(symbol, exchange="NSE")
        current_price = float(quote.get("last_price", 0)) if quote else 0
        
        # Prepare financial data dict
        fd_dict = {
            "period_end": financial_data.period_end,
            "revenue": float(financial_data.revenue) if financial_data.revenue else None,
            "net_profit": float(financial_data.net_profit) if financial_data.net_profit else None,
            "net_worth": float(financial_data.net_worth) if financial_data.net_worth else None,
            "total_assets": float(financial_data.total_assets) if financial_data.total_assets else None,
            "total_liabilities": float(financial_data.total_liabilities) if financial_data.total_liabilities else None,
            "current_assets": float(financial_data.current_assets) if financial_data.current_assets else None,
            "current_liabilities": float(financial_data.current_liabilities) if financial_data.current_liabilities else None,
            "eps": float(financial_data.eps) if financial_data.eps else None,
            "book_value": float(financial_data.book_value) if financial_data.book_value else None,
            "ebit": float(financial_data.ebit) if financial_data.ebit else None,
            "capital_employed": float(financial_data.capital_employed) if financial_data.capital_employed else None,
            "free_cash_flow": float(financial_data.free_cash_flow) if financial_data.free_cash_flow else None
        }
        
        # Calculate ratios
        ratios = financial_ratios_service.calculate_ratios(
            symbol=symbol,
            current_price=current_price,
            financial_data=fd_dict
        )
        
        # Store in database
        existing = db.query(FinancialRatios).filter(
            FinancialRatios.symbol == symbol.upper(),
            FinancialRatios.period_end == financial_data.period_end
        ).first()
        
        if existing:
            # Update
            for key, value in ratios.items():
                if key not in ["symbol", "calculated_at"] and value is not None:
                    setattr(existing, key, value)
            existing.calculated_at = datetime.utcnow()
        else:
            # Create new
            new_ratios = FinancialRatios(
                symbol=symbol.upper(),
                period_end=financial_data.period_end,
                current_price=current_price,
                pe_ratio=ratios.get("pe_ratio"),
                pb_ratio=ratios.get("pb_ratio"),
                roe=ratios.get("roe"),
                roce=ratios.get("roce"),
                debt_to_equity=ratios.get("debt_to_equity"),
                current_ratio=ratios.get("current_ratio"),
                operating_margin=ratios.get("operating_margin"),
                profit_growth_5y=ratios.get("profit_growth_5y"),
                revenue_growth_5y=ratios.get("revenue_growth_5y")
            )
            db.add(new_ratios)
        
        db.commit()
        
        return {
            "success": True,
            "data": ratios,
            "message": f"Financial ratios calculated and stored for {symbol}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error calculating financial ratios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projections/{symbol}")
async def get_financial_projections(
    symbol: str,
    years: int = Query(5, description="Projection years (max 5)"),
    base_discount_rate: float = Query(0.12, description="Discount rate for base scenario (e.g. 0.12)"),
    base_terminal_growth: float = Query(0.04, description="Terminal growth for base scenario (e.g. 0.04)"),
    base_growth_override: Optional[float] = Query(None, description="Override base growth rate (decimal, e.g. 0.10 for 10%)"),
    base_profit_margin_override: Optional[float] = Query(None, description="Override base profit margin (decimal, e.g. 0.18 for 18%)"),
    bull_growth_delta: float = Query(0.03, description="Bull growth delta added to base (decimal)"),
    bear_growth_delta: float = Query(0.03, description="Bear growth delta subtracted from base (decimal)"),
    bull_margin_delta: float = Query(0.01, description="Bull profit margin delta (decimal)"),
    bear_margin_delta: float = Query(-0.01, description="Bear profit margin delta (decimal)"),
    eps_to_fcf: float = Query(0.85, description="EPS to FCF/share conversion ratio when shares/FCF missing"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Pro-grade scenario projections + DCF valuation band + sensitivity.

    Returns Base/Bull/Bear 1..N year projections for Revenue/Net Profit/EPS/FCF (per share),
    plus DCF intrinsic value per share and sensitivity tables.
    """
    try:
        result = financial_projection_service.build_projections(
            db=db,
            symbol=symbol,
            years=years,
            base_discount_rate=base_discount_rate,
            base_terminal_growth=base_terminal_growth,
            base_growth_override=base_growth_override,
            base_profit_margin_override=base_profit_margin_override,
            bull_premium_growth=bull_growth_delta,
            bear_discount_growth=bear_growth_delta,
            bull_margin_delta=bull_margin_delta,
            bear_margin_delta=bear_margin_delta,
            eps_to_fcf=eps_to_fcf,
        )
        return {"success": True, "data": result, "message": "Projections generated"}
    except Exception as e:
        logger.error(f"Error generating projections for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research-report/{symbol}")
async def get_research_report(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe: 1D (daily), 1W (weekly), 1M (monthly), 3M (3-month), 6M (6-month)"),
    include_chart_images: bool = Query(False, description="Include chart image analysis if available"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Generate comprehensive research report for a symbol"""
    try:
        # Normalize symbol to uppercase
        symbol = symbol.upper().strip()
        logger.info(f"📊 Generating research report for {symbol} (timeframe: {timeframe})")
        # Get financial data
        financial_data = db.query(FinancialData).filter(
            FinancialData.symbol == symbol.upper()
        ).order_by(FinancialData.period_end.desc()).first()
        
        # Get financial ratios
        financial_ratios = db.query(FinancialRatios).filter(
            FinancialRatios.symbol == symbol.upper()
        ).order_by(FinancialRatios.period_end.desc()).first()
        
        # Get technical analysis and sentiment analysis from Unified AI Service
        from core.unified_ai_service import unified_ai_service
        technical_analysis = None
        sentiment_analysis = None
        try:
            analysis_result = await unified_ai_service.analyze_stock_unified(
                symbol=symbol,
                user_query="",
                analysis_depth="QUICK",
                include_news=True  # Include news sentiment analysis
            )
            # Extract technical analysis from UnifiedAnalysisResult dataclass
            # technical_analysis is already a Dict[str, Any], not an object
            if analysis_result and hasattr(analysis_result, 'technical_analysis'):
                technical_analysis = analysis_result.technical_analysis
                # Ensure it's a dict (it should be, but just in case)
                if not isinstance(technical_analysis, dict):
                    technical_analysis = {}
            
            # Extract sentiment analysis (includes news sentiment, social sentiment, market sentiment)
            if analysis_result and hasattr(analysis_result, 'sentiment_analysis'):
                sentiment_analysis = analysis_result.sentiment_analysis
                # Ensure it's a dict
                if not isinstance(sentiment_analysis, dict):
                    sentiment_analysis = {}
        except Exception as e:
            logger.warning(f"Could not get AI analysis for {symbol}: {e}")
            # Continue without analysis - report can still be generated
            technical_analysis = None
            sentiment_analysis = None
        
        # Prepare data
        fd_dict = None
        if financial_data:
            fd_dict = {
                "revenue": float(financial_data.revenue) if financial_data.revenue else None,
                "net_profit": float(financial_data.net_profit) if financial_data.net_profit else None,
                "net_worth": float(financial_data.net_worth) if financial_data.net_worth else None,
                "period_end": financial_data.period_end
            }
        
        ratios_dict = None
        if financial_ratios:
            ratios_dict = {
                "pe_ratio": float(financial_ratios.pe_ratio) if financial_ratios.pe_ratio else None,
                "pb_ratio": float(financial_ratios.pb_ratio) if financial_ratios.pb_ratio else None,
                "roe": float(financial_ratios.roe) if financial_ratios.roe else None,
                "roce": float(financial_ratios.roce) if financial_ratios.roce else None,
                "debt_to_equity": float(financial_ratios.debt_to_equity) if financial_ratios.debt_to_equity else None
            }
        
        # Generate comprehensive report with vast analysis
        from services.comprehensive_report_generator import comprehensive_report_generator
        report = await comprehensive_report_generator.generate_comprehensive_report(
            symbol=symbol,
            db=db,
            financial_data=fd_dict,
            financial_ratios=ratios_dict,
            technical_analysis=technical_analysis,
            sentiment_analysis=sentiment_analysis,
            timeframe=timeframe
        )
        
        # Ensure report symbol matches requested symbol (defensive check)
        if report and report.get("symbol"):
            if report["symbol"].upper() != symbol.upper():
                logger.warning(f"⚠️ Symbol mismatch in report: requested {symbol}, got {report['symbol']}. Fixing...")
                report["symbol"] = symbol
        
        logger.info(f"✅ Research report generated for {symbol} - report symbol: {report.get('symbol') if report else 'N/A'}")
        
        # Convert numpy types to native Python types for JSON serialization
        # This is critical to prevent "numpy.bool_ object is not iterable" errors
        # Must convert the entire report structure recursively
        if report:
            try:
                logger.debug(f"Converting numpy types in report for {symbol}...")
                report = convert_numpy_types(report)
                logger.debug(f"✅ Successfully converted numpy types in report for {symbol}")
            except Exception as conv_error:
                logger.error(f"❌ Error converting numpy types in report: {conv_error}")
                import traceback
                logger.error(traceback.format_exc())
                # Try to continue - but the error will likely still occur
        
        # Also convert the response dict itself to be safe
        response_data = {
            "success": True,
            "data": report,
            "message": f"Research report generated for {symbol}"
        }
        
        # Final conversion pass on the entire response
        try:
            response_data = convert_numpy_types(response_data)
        except Exception as conv_error:
            logger.error(f"Error converting response data: {conv_error}")
        
        return response_data
    except Exception as e:
        logger.error(f"Error generating research report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research-report/{symbol}/analyze-chart-images")
async def analyze_chart_images(
    symbol: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze chart images for a symbol
    
    Accepts multiple image files (PNG, JPG, JPEG) and analyzes them
    to detect patterns, trends, and key price levels
    """
    try:
        from services.chart_image_analysis import chart_image_analysis_service
        from core.data_service import data_service
        
        # Get current price for reference
        quote = await data_service.get_quote(symbol, exchange="NSE")
        current_price = float(quote.get("last_price", 0)) if quote else None
        
        # Process uploaded images
        images_data = []
        for file in files:
            if not file.content_type or not file.content_type.startswith('image/'):
                continue
            
            # Read image bytes
            image_bytes = await file.read()
            
            # Convert to base64 for analysis
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            images_data.append({
                "base64": image_base64,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(image_bytes)
            })
        
        if not images_data:
            raise HTTPException(
                status_code=400,
                detail="No valid image files provided. Please upload PNG, JPG, or JPEG images."
            )
        
        # Analyze images
        analysis_result = await chart_image_analysis_service.analyze_chart_images(
            images=images_data,
            symbol=symbol,
            current_price=current_price
        )
        
        if not analysis_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=analysis_result.get("error", "Image analysis failed")
            )
        
        return {
            "success": True,
            "data": analysis_result,
            "message": f"Analyzed {len(images_data)} chart image(s) for {symbol}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing chart images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research-report/{symbol}/regenerate-with-chart-images")
async def regenerate_report_with_chart_images(
    symbol: str,
    chart_image_analysis: Dict = Body(...),
    timeframe: str = Query("1D", description="Timeframe: 1D (daily), 1W (weekly), 1M (monthly), 3M (3-month), 6M (6-month)"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Regenerate comprehensive research report with chart image analysis included"""
    try:
        # Get financial data
        financial_data = db.query(FinancialData).filter(
            FinancialData.symbol == symbol.upper()
        ).order_by(FinancialData.period_end.desc()).first()
        
        # Get financial ratios
        financial_ratios = db.query(FinancialRatios).filter(
            FinancialRatios.symbol == symbol.upper()
        ).order_by(FinancialRatios.period_end.desc()).first()
        
        # Get technical analysis and sentiment analysis from Unified AI Service
        from core.unified_ai_service import unified_ai_service
        technical_analysis = None
        sentiment_analysis = None
        try:
            analysis_result = await unified_ai_service.analyze_stock_unified(
                symbol=symbol,
                user_query="",
                analysis_depth="QUICK",
                include_news=True
            )
            if analysis_result and hasattr(analysis_result, 'technical_analysis'):
                technical_analysis = analysis_result.technical_analysis
                if not isinstance(technical_analysis, dict):
                    technical_analysis = {}
            
            if analysis_result and hasattr(analysis_result, 'sentiment_analysis'):
                sentiment_analysis = analysis_result.sentiment_analysis
                if not isinstance(sentiment_analysis, dict):
                    sentiment_analysis = {}
        except Exception as e:
            logger.warning(f"Could not get AI analysis for {symbol}: {e}")
            technical_analysis = None
            sentiment_analysis = None
        
        # Prepare data
        fd_dict = None
        if financial_data:
            fd_dict = {
                "revenue": float(financial_data.revenue) if financial_data.revenue else None,
                "net_profit": float(financial_data.net_profit) if financial_data.net_profit else None,
                "net_worth": float(financial_data.net_worth) if financial_data.net_worth else None,
                "period_end": financial_data.period_end
            }
        
        ratios_dict = None
        if financial_ratios:
            ratios_dict = {
                "pe_ratio": float(financial_ratios.pe_ratio) if financial_ratios.pe_ratio else None,
                "pb_ratio": float(financial_ratios.pb_ratio) if financial_ratios.pb_ratio else None,
                "roe": float(financial_ratios.roe) if financial_ratios.roe else None,
                "roce": float(financial_ratios.roce) if financial_ratios.roce else None,
                "debt_to_equity": float(financial_ratios.debt_to_equity) if financial_ratios.debt_to_equity else None
            }
        
        # Generate comprehensive report with chart image analysis
        from services.comprehensive_report_generator import comprehensive_report_generator
        report = await comprehensive_report_generator.generate_comprehensive_report(
            symbol=symbol,
            db=db,
            financial_data=fd_dict,
            financial_ratios=ratios_dict,
            technical_analysis=technical_analysis,
            sentiment_analysis=sentiment_analysis,
            timeframe=timeframe,
            chart_image_analysis=chart_image_analysis
        )
        
        # Convert numpy types to native Python types for JSON serialization
        # This is critical to prevent "numpy.bool_ object is not iterable" errors
        if report:
            try:
                logger.debug(f"Converting numpy types in regenerated report for {symbol}...")
                report = convert_numpy_types(report)
                logger.debug(f"✅ Successfully converted numpy types in regenerated report for {symbol}")
            except Exception as conv_error:
                logger.error(f"❌ Error converting numpy types in regenerated report: {conv_error}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Also convert the response dict itself to be safe
        response_data = {
            "success": True,
            "data": report,
            "message": f"Research report regenerated for {symbol} with chart image analysis"
        }
        
        # Final conversion pass on the entire response
        try:
            response_data = convert_numpy_types(response_data)
        except Exception as conv_error:
            logger.error(f"Error converting response data: {conv_error}")
        
        return response_data
    except Exception as e:
        logger.error(f"Error regenerating research report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research-report/{symbol}/export-pdf")
async def export_research_report_pdf(
    symbol: str,
    report_data: Dict,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Export research report as PDF"""
    try:
        from services.research_report_pdf_generator import research_report_pdf_generator
        from fastapi.responses import Response
        
        # Generate PDF
        pdf_buffer = research_report_pdf_generator.generate_pdf(report_data)
        
        # Return PDF as response
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=research_report_{symbol}_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PDF generation requires reportlab library. Install with: pip install reportlab"
        )
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/screener-data/{symbol}")
async def get_screener_data(
    symbol: str,
    consolidated: bool = Query(True, description="Fetch consolidated data (True) or standalone (False)"),
    save_to_db: bool = Query(True, description="Save scraped data to database"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Fetch comprehensive company data from screener.in
    
    This endpoint scrapes real-time data from screener.in including:
    - Key financial metrics (Market Cap, PE, Book Value, ROCE, ROE, etc.)
    - Quarterly results
    - Shareholding patterns
    - Growth metrics (Compounded Sales/Profit Growth, Stock Price CAGR, ROE)
    - Balance Sheet data (Equity Capital, Reserves, Borrowings)
    - Cash Flows
    - Company information
    
    Reference: https://www.screener.in/company/{symbol}/consolidated/
    """
    try:
        logger.info(f"Fetching screener.in data for {symbol}")
        
        company_data = await screener_scraper.get_company_data(
            symbol=symbol.upper(),
            consolidated=consolidated
        )
        
        if "error" in company_data:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch data from screener.in: {company_data.get('error', 'Unknown error')}"
            )
        
        # Save to database if requested
        if save_to_db:
            try:
                # Save growth metrics
                if "growth_metrics" in company_data and company_data["growth_metrics"]:
                    screener_data_service.save_growth_metrics(
                        db, symbol, company_data["growth_metrics"]
                    )
                
                # Save balance sheet
                if "balance_sheet" in company_data and company_data["balance_sheet"]:
                    screener_data_service.save_balance_sheet(
                        db, symbol, company_data["balance_sheet"]
                    )
                
                # Save cash flows
                if "cash_flows" in company_data and company_data["cash_flows"]:
                    screener_data_service.save_cash_flows(
                        db, symbol, company_data["cash_flows"]
                    )
                
                # Save shareholding
                if "detailed_shareholding" in company_data and company_data["detailed_shareholding"]:
                    screener_data_service.save_shareholding(
                        db, symbol, company_data["detailed_shareholding"]
                    )
                
                logger.info(f"Saved screener.in data to database for {symbol}")
            except Exception as e:
                logger.warning(f"Could not save screener data to database: {e}")
                # Continue even if save fails
        
        return {
            "success": True,
            "data": company_data,
            "message": f"Screener.in data fetched successfully for {symbol}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching screener.in data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/nifty50-financial-data")
async def sync_nifty50_financial_data(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Sync financial data (quarterly/annual) for all Nifty 50 stocks from Screener.in
    
    This endpoint fetches and saves financial data for all 50 Nifty stocks.
    It may take several minutes to complete.
    """
    try:
        logger.info("🚀 Starting Nifty 50 financial data sync...")
        
        # Run sync in background (async)
        result = await nifty50_financial_sync.sync_all_nifty50(db, max_concurrent=5)
        
        return {
            "success": result.get("success", True),
            "data": result,
            "message": result.get("message", "Sync completed")
        }
    except Exception as e:
        logger.error(f"Error syncing Nifty 50 financial data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/stock-financial-data/{symbol}")
async def sync_stock_financial_data(
    symbol: str,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Sync financial data for a single stock from Screener.in
    """
    try:
        result = await nifty50_financial_sync.sync_stock_financial_data(db, symbol)
        
        return {
            "success": result.get("success", False),
            "data": result,
            "message": result.get("message", f"Sync completed for {symbol}")
        }
    except Exception as e:
        logger.error(f"Error syncing financial data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/init/database")
async def initialize_database(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Initialize database tables and seed StockMaster with Nifty 50 stocks
    This is a one-time setup that should be run after database creation
    """
    try:
        from core.database_unified import Base, engine, StockMaster
        from datetime import datetime
        
        logger.info("🚀 Starting database initialization...")
        
        # Step 1: Create all tables
        logger.info("📊 Creating all database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Step 2: Seed StockMaster
        logger.info("🌱 Seeding StockMaster table with Nifty 50 stocks...")
        
        from services.nifty50_financial_sync import NIFTY_50_SYMBOLS
        
        # Company names mapping
        COMPANY_NAMES = {
            "RELIANCE": "Reliance Industries Ltd",
            "TCS": "Tata Consultancy Services Ltd",
            "HDFCBANK": "HDFC Bank Ltd",
            "INFY": "Infosys Ltd",
            "HINDUNILVR": "Hindustan Unilever Ltd",
            "ICICIBANK": "ICICI Bank Ltd",
            "KOTAKBANK": "Kotak Mahindra Bank Ltd",
            "HDFC": "Housing Development Finance Corporation Ltd",
            "ITC": "ITC Ltd",
            "BHARTIARTL": "Bharti Airtel Ltd",
            "SBIN": "State Bank of India",
            "BAJFINANCE": "Bajaj Finance Ltd",
            "ASIANPAINT": "Asian Paints Ltd",
            "AXISBANK": "Axis Bank Ltd",
            "MARUTI": "Maruti Suzuki India Ltd",
            "SUNPHARMA": "Sun Pharmaceutical Industries Ltd",
            "TITAN": "Titan Company Ltd",
            "ULTRACEMCO": "UltraTech Cement Ltd",
            "NESTLEIND": "Nestle India Ltd",
            "POWERGRID": "Power Grid Corporation of India Ltd",
            "NTPC": "NTPC Ltd",
            "TECHM": "Tech Mahindra Ltd",
            "WIPRO": "Wipro Ltd",
            "HCLTECH": "HCL Technologies Ltd",
            "LT": "Larsen & Toubro Ltd",
            "BAJAJFINSV": "Bajaj Finserv Ltd",
            "DRREDDY": "Dr. Reddy's Laboratories Ltd",
            "TATAMOTORS": "Tata Motors Ltd",
            "BRITANNIA": "Britannia Industries Ltd",
            "EICHERMOT": "Eicher Motors Ltd",
            "SHREECEM": "Shree Cement Ltd",
            "JSWSTEEL": "JSW Steel Ltd",
            "TATASTEEL": "Tata Steel Ltd",
            "INDUSINDBK": "IndusInd Bank Ltd",
            "COALINDIA": "Coal India Ltd",
            "GRASIM": "Grasim Industries Ltd",
            "CIPLA": "Cipla Ltd",
            "ONGC": "Oil and Natural Gas Corporation Ltd",
            "TATACONSUM": "Tata Consumer Products Ltd",
            "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd",
            "ADANIPORTS": "Adani Ports and Special Economic Zone Ltd",
            "BPCL": "Bharat Petroleum Corporation Ltd",
            "HEROMOTOCO": "Hero MotoCorp Ltd",
            "DIVISLAB": "Divis Laboratories Ltd",
            "UPL": "UPL Ltd",
            "BAJAJ-AUTO": "Bajaj Auto Ltd",
            "TATAPOWER": "Tata Power Company Ltd",
            "ADANIENT": "Adani Enterprises Ltd",
            "SBILIFE": "SBI Life Insurance Company Ltd",
            "HINDALCO": "Hindalco Industries Ltd"
        }
        
        created_count = 0
        updated_count = 0
        
        for symbol in NIFTY_50_SYMBOLS:
            try:
                existing = db.query(StockMaster).filter(
                    StockMaster.symbol == symbol.upper()
                ).first()
                
                if existing:
                    if not existing.company_name:
                        existing.company_name = COMPANY_NAMES.get(symbol, symbol)
                    if not existing.exchange:
                        existing.exchange = "NSE"
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    stock = StockMaster(
                        symbol=symbol.upper(),
                        company_name=COMPANY_NAMES.get(symbol, symbol),
                        exchange="NSE",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    created_count += 1
            except Exception as e:
                logger.warning(f"Error processing {symbol}: {e}")
                continue
        
        db.commit()
        
        # Verify
        total_stocks = db.query(StockMaster).filter(
            StockMaster.symbol.in_([s.upper() for s in NIFTY_50_SYMBOLS])
        ).count()
        
        return {
            "success": True,
            "data": {
                "tables_created": True,
                "stocks_created": created_count,
                "stocks_updated": updated_count,
                "total_stocks": total_stocks,
                "expected_stocks": len(NIFTY_50_SYMBOLS)
            },
            "message": f"Database initialized: {created_count} stocks created, {updated_count} updated, {total_stocks}/{len(NIFTY_50_SYMBOLS)} total"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/init/database-and-sync")
async def initialize_database_and_sync(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Complete initialization: Create tables, seed StockMaster, and sync financial data for all Nifty 50 stocks
    This is a comprehensive setup that does everything in one go
    """
    try:
        from core.database_unified import Base, engine, StockMaster
        from datetime import datetime
        
        results = {
            "tables_created": False,
            "stocks_seeded": 0,
            "financial_sync": None
        }
        
        # Step 1: Create all tables
        logger.info("📊 Step 1: Creating all database tables...")
        Base.metadata.create_all(bind=engine)
        results["tables_created"] = True
        logger.info("✅ Tables created")
        
        # Step 2: Seed StockMaster
        logger.info("🌱 Step 2: Seeding StockMaster table with Nifty 50 stocks...")
        
        from services.nifty50_financial_sync import NIFTY_50_SYMBOLS
        
        COMPANY_NAMES = {
            "RELIANCE": "Reliance Industries Ltd",
            "TCS": "Tata Consultancy Services Ltd",
            "HDFCBANK": "HDFC Bank Ltd",
            "INFY": "Infosys Ltd",
            "HINDUNILVR": "Hindustan Unilever Ltd",
            "ICICIBANK": "ICICI Bank Ltd",
            "KOTAKBANK": "Kotak Mahindra Bank Ltd",
            "HDFC": "Housing Development Finance Corporation Ltd",
            "ITC": "ITC Ltd",
            "BHARTIARTL": "Bharti Airtel Ltd",
            "SBIN": "State Bank of India",
            "BAJFINANCE": "Bajaj Finance Ltd",
            "ASIANPAINT": "Asian Paints Ltd",
            "AXISBANK": "Axis Bank Ltd",
            "MARUTI": "Maruti Suzuki India Ltd",
            "SUNPHARMA": "Sun Pharmaceutical Industries Ltd",
            "TITAN": "Titan Company Ltd",
            "ULTRACEMCO": "UltraTech Cement Ltd",
            "NESTLEIND": "Nestle India Ltd",
            "POWERGRID": "Power Grid Corporation of India Ltd",
            "NTPC": "NTPC Ltd",
            "TECHM": "Tech Mahindra Ltd",
            "WIPRO": "Wipro Ltd",
            "HCLTECH": "HCL Technologies Ltd",
            "LT": "Larsen & Toubro Ltd",
            "BAJAJFINSV": "Bajaj Finserv Ltd",
            "DRREDDY": "Dr. Reddy's Laboratories Ltd",
            "TATAMOTORS": "Tata Motors Ltd",
            "BRITANNIA": "Britannia Industries Ltd",
            "EICHERMOT": "Eicher Motors Ltd",
            "SHREECEM": "Shree Cement Ltd",
            "JSWSTEEL": "JSW Steel Ltd",
            "TATASTEEL": "Tata Steel Ltd",
            "INDUSINDBK": "IndusInd Bank Ltd",
            "COALINDIA": "Coal India Ltd",
            "GRASIM": "Grasim Industries Ltd",
            "CIPLA": "Cipla Ltd",
            "ONGC": "Oil and Natural Gas Corporation Ltd",
            "TATACONSUM": "Tata Consumer Products Ltd",
            "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd",
            "ADANIPORTS": "Adani Ports and Special Economic Zone Ltd",
            "BPCL": "Bharat Petroleum Corporation Ltd",
            "HEROMOTOCO": "Hero MotoCorp Ltd",
            "DIVISLAB": "Divis Laboratories Ltd",
            "UPL": "UPL Ltd",
            "BAJAJ-AUTO": "Bajaj Auto Ltd",
            "TATAPOWER": "Tata Power Company Ltd",
            "ADANIENT": "Adani Enterprises Ltd",
            "SBILIFE": "SBI Life Insurance Company Ltd",
            "HINDALCO": "Hindalco Industries Ltd"
        }
        
        created_count = 0
        updated_count = 0
        
        for symbol in NIFTY_50_SYMBOLS:
            try:
                existing = db.query(StockMaster).filter(
                    StockMaster.symbol == symbol.upper()
                ).first()
                
                if existing:
                    if not existing.company_name:
                        existing.company_name = COMPANY_NAMES.get(symbol, symbol)
                    if not existing.exchange:
                        existing.exchange = "NSE"
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    stock = StockMaster(
                        symbol=symbol.upper(),
                        company_name=COMPANY_NAMES.get(symbol, symbol),
                        exchange="NSE",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(stock)
                    created_count += 1
            except Exception as e:
                logger.warning(f"Error processing {symbol}: {e}")
                continue
        
        db.commit()
        results["stocks_seeded"] = created_count + updated_count
        logger.info(f"✅ StockMaster seeded: {created_count} created, {updated_count} updated")
        
        # Step 3: Sync Financial Data
        logger.info("🔄 Step 3: Starting financial data sync for all Nifty 50 stocks...")
        logger.info("⏳ This may take several minutes...")
        
        try:
            sync_result = await nifty50_financial_sync.sync_all_nifty50(db, max_concurrent=5)
            results["financial_sync"] = {
                "success": sync_result.get("success", False),
                "total_symbols": sync_result.get("total_symbols", 0),
                "successful": sync_result.get("successful", 0),
                "failed": sync_result.get("failed", 0),
                "total_quarters_saved": sync_result.get("total_quarters_saved", 0),
                "message": sync_result.get("message", "")
            }
            logger.info(f"✅ Financial data sync completed: {sync_result.get('message', 'Done')}")
        except Exception as e:
            logger.error(f"❌ Error in financial data sync: {e}")
            results["financial_sync"] = {
                "success": False,
                "error": str(e)
            }
        
        # Summary
        total_stocks = db.query(StockMaster).filter(
            StockMaster.symbol.in_([s.upper() for s in NIFTY_50_SYMBOLS])
        ).count()
        
        return {
            "success": True,
            "data": {
                **results,
                "total_stocks_in_master": total_stocks,
                "expected_stocks": len(NIFTY_50_SYMBOLS)
            },
            "message": f"Complete initialization done! Tables created, {results['stocks_seeded']} stocks seeded, Financial sync: {results['financial_sync'].get('successful', 0) if results['financial_sync'] else 0}/{len(NIFTY_50_SYMBOLS)} stocks synced"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in complete initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

