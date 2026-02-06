"""
Consolidated Analysis API Routes
Provides comprehensive analysis combining all features
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
import logging
from core.auth_dependencies import get_current_user
from services.consolidated_analysis_service import ConsolidatedAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Consolidated Analysis"])

consolidated_service = ConsolidatedAnalysisService()

@router.get("/consolidated")
async def get_consolidated_analysis(
    symbol: str = Query(..., description="Stock symbol (e.g., RELIANCE)"),
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 1D, 1W, 1M"),
    days: int = Query(100, ge=10, le=365, description="Number of days of historical data"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive consolidated analysis for a symbol
    
    Combines:
    - Price Action (Support/Resistance, Pivot Points)
    - Levels (HH/HL/LH/LL classification)
    - Gap Detection & Filling Status
    - Trendline Analysis with Retest Signals
    - Trading Signals
    
    Returns:
        Complete analysis with all features
    """
    try:
        result = await consolidated_service.get_consolidated_analysis(
            symbol=symbol,
            timeframe=timeframe,
            days=days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to generate consolidated analysis")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in consolidated analysis endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
