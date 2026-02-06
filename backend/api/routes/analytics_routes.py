"""
Data Analytics API Routes
Performance tracking, signal analytics, market regime, sector rotation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from core.database import get_db
from core.auth_dependencies import get_current_user
from services.data_analytics import data_analytics_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

class AnalysisAccuracyRequest(BaseModel):
    analysis_id: str
    symbol: str
    predicted_price: float
    predicted_direction: str
    actual_price: Optional[float] = None
    actual_direction: Optional[str] = None

@router.post("/track-accuracy")
async def track_analysis_accuracy(
    request: AnalysisAccuracyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track analysis accuracy"""
    try:
        result = await data_analytics_service.track_analysis_accuracy(
            analysis_id=request.analysis_id,
            symbol=request.symbol,
            predicted_price=request.predicted_price,
            predicted_direction=request.predicted_direction,
            actual_price=request.actual_price,
            actual_direction=request.actual_direction,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error tracking analysis accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signal-performance")
async def get_signal_performance(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signal performance analytics"""
    try:
        result = await data_analytics_service.analyze_signal_performance(
            user_id=user_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing signal performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-regime/{symbol}")
async def get_market_regime(
    symbol: str,
    lookback_days: int = Query(60, description="Lookback period in days"),
    current_user: dict = Depends(get_current_user)
):
    """Detect market regime"""
    try:
        result = await data_analytics_service.detect_market_regime(
            symbol=symbol,
            lookback_days=lookback_days
        )
        return result
    except Exception as e:
        logger.error(f"Error detecting market regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sector-rotation")
async def get_sector_rotation(
    sectors: Optional[List[str]] = Query(None, description="Sectors to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Analyze sector rotation"""
    try:
        result = await data_analytics_service.analyze_sector_rotation(
            sectors=sectors
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing sector rotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

