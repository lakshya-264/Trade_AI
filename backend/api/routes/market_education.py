"""
Market Education API Routes
Comprehensive education endpoints for IPO, CPR, Regulators, Corporate Actions, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from core.auth_dependencies import get_current_user, get_current_user_optional
from services.ipo_markets_service import IPOMarketsService
from services.central_pivot_range_service import CentralPivotRangeService
from services.regulators_education_service import RegulatorsEducationService
from services.corporate_actions_service import CorporateActionsService
from services.market_education_services import (
    DowTheoryService, ClearingSettlementService, 
    GlossaryService, Level3DataService, TradingRoutineService, RightsOFSService
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
ipo_service = IPOMarketsService()
cpr_service = CentralPivotRangeService()
regulators_service = RegulatorsEducationService()
corporate_actions_service = CorporateActionsService()
dow_theory_service = DowTheoryService()
clearing_service = ClearingSettlementService()
glossary_service = GlossaryService()
level3_service = Level3DataService()
routine_service = TradingRoutineService()
rights_service = RightsOFSService()

# ==================== IPO MARKETS ====================

@router.get("/ipo/lessons")
async def get_ipo_lessons(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get all IPO education lessons"""
    try:
        result = ipo_service.get_ipo_lessons()
        return result
    except Exception as e:
        logger.error(f"Error fetching IPO lessons: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ipo/jargons")
async def get_ipo_jargons(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get IPO jargons dictionary"""
    try:
        result = ipo_service.get_ipo_jargons()
        return result
    except Exception as e:
        logger.error(f"Error fetching IPO jargons: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ipo/analyze")
async def analyze_ipo(
    ipo_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user_optional)
):
    """Analyze an IPO"""
    try:
        result = ipo_service.analyze_ipo(ipo_data)
        return result
    except Exception as e:
        logger.error(f"Error analyzing IPO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ipo/calculate-metrics")
async def calculate_ipo_metrics(
    inputs: Dict[str, Any],
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate IPO valuation metrics"""
    try:
        result = ipo_service.calculate_ipo_metrics(inputs)
        return result
    except Exception as e:
        logger.error(f"Error calculating IPO metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ipo/calculate-listing-gain")
async def calculate_listing_gain(
    ipo_price: float = Query(...),
    listing_price: float = Query(...),
    shares: int = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate listing gain"""
    try:
        result = ipo_service.calculate_listing_gain(ipo_price, listing_price, shares)
        return result
    except Exception as e:
        logger.error(f"Error calculating listing gain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CENTRAL PIVOT RANGE ====================

@router.post("/cpr/calculate")
async def calculate_cpr(
    high: float = Query(...),
    low: float = Query(...),
    close: float = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate Central Pivot Range"""
    try:
        result = cpr_service.calculate_cpr(high, low, close)
        return result
    except Exception as e:
        logger.error(f"Error calculating CPR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cpr/calculate-from-ohlc")
async def calculate_cpr_from_ohlc(
    ohlc_data: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate CPR from OHLC data"""
    try:
        result = cpr_service.calculate_cpr_from_ohlc(ohlc_data)
        return result
    except Exception as e:
        logger.error(f"Error calculating CPR from OHLC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cpr/education")
async def get_cpr_education(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get CPR education content"""
    try:
        result = cpr_service.get_cpr_education()
        return result
    except Exception as e:
        logger.error(f"Error fetching CPR education: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REGULATORS ====================

@router.get("/regulators/info")
async def get_regulators_info(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get comprehensive regulators information"""
    try:
        result = regulators_service.get_regulators_info()
        return result
    except Exception as e:
        logger.error(f"Error fetching regulators info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regulators/analyze-market-structure")
async def analyze_market_structure(
    market_data: Optional[Dict] = None,
    current_user: dict = Depends(get_current_user_optional)
):
    """Analyze market structure"""
    try:
        result = regulators_service.analyze_market_structure(market_data)
        return result
    except Exception as e:
        logger.error(f"Error analyzing market structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CORPORATE ACTIONS ====================

@router.get("/corporate-actions/info")
async def get_corporate_actions_info(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get corporate actions information"""
    try:
        result = corporate_actions_service.get_corporate_actions_info()
        return result
    except Exception as e:
        logger.error(f"Error fetching corporate actions info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/corporate-actions/calculate-dividend-impact")
async def calculate_dividend_impact(
    current_price: float = Query(...),
    dividend_per_share: float = Query(...),
    shares_held: int = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate dividend impact"""
    try:
        result = corporate_actions_service.calculate_dividend_impact(
            current_price, dividend_per_share, shares_held
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating dividend impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/corporate-actions/calculate-split-impact")
async def calculate_split_impact(
    current_price: float = Query(...),
    split_ratio: str = Query(...),
    shares_held: int = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate stock split impact"""
    try:
        result = corporate_actions_service.calculate_split_impact(
            current_price, split_ratio, shares_held
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating split impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/corporate-actions/calculate-bonus-impact")
async def calculate_bonus_impact(
    current_price: float = Query(...),
    bonus_ratio: str = Query(...),
    shares_held: int = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate bonus issue impact"""
    try:
        result = corporate_actions_service.calculate_bonus_impact(
            current_price, bonus_ratio, shares_held
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating bonus impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/corporate-actions/calculate-rights-impact")
async def calculate_rights_impact(
    current_price: float = Query(...),
    rights_ratio: str = Query(...),
    rights_price: float = Query(...),
    shares_held: int = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate rights issue impact"""
    try:
        result = corporate_actions_service.calculate_rights_impact(
            current_price, rights_ratio, rights_price, shares_held
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating rights impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DOW THEORY ====================

@router.post("/dow-theory/detect-signals")
async def detect_dow_theory_signals(
    price_data: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user_optional)
):
    """Detect Dow Theory trading signals"""
    try:
        result = dow_theory_service.detect_dow_theory_signals(price_data)
        return result
    except Exception as e:
        logger.error(f"Error detecting Dow Theory signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CLEARING & SETTLEMENT ====================

@router.post("/settlement/calculate-date")
async def calculate_settlement_date(
    trade_date: str = Query(...),
    settlement_days: int = Query(1),
    current_user: dict = Depends(get_current_user_optional)
):
    """Calculate settlement date"""
    try:
        trade_dt = datetime.fromisoformat(trade_date)
        result = clearing_service.calculate_settlement_date(trade_dt, settlement_days)
        return result
    except Exception as e:
        logger.error(f"Error calculating settlement date: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GLOSSARY ====================

@router.get("/glossary/search")
async def search_glossary(
    term: str = Query(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Search glossary"""
    try:
        result = glossary_service.search_glossary(term)
        return result
    except Exception as e:
        logger.error(f"Error searching glossary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LEVEL 3 DATA ====================

@router.get("/level3/education")
async def get_level3_education(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get Level 3 data education"""
    try:
        return {
            "success": True,
            "education": level3_service.level3_content
        }
    except Exception as e:
        logger.error(f"Error fetching Level 3 education: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TRADING ROUTINE ====================

@router.get("/trading-routine")
async def get_trading_routine(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get trading routine guide"""
    try:
        return {
            "success": True,
            "routines": routine_service.routines
        }
    except Exception as e:
        logger.error(f"Error fetching trading routine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== RIGHTS/OFS/FPO ====================

@router.get("/rights-ofs-fpo")
async def get_rights_ofs_fpo(
    current_user: dict = Depends(get_current_user_optional)
):
    """Get Rights, OFS, FPO education"""
    try:
        return {
            "success": True,
            "content": rights_service.content
        }
    except Exception as e:
        logger.error(f"Error fetching Rights/OFS/FPO content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

