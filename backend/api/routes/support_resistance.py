"""
Support & Resistance API Routes
Endpoints for detecting and analyzing key price levels
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from services.support_resistance import SupportResistanceService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["support_resistance"])

# Initialize service
sr_service = SupportResistanceService()

# Request/Response Models

class SupportResistanceRequest(BaseModel):
    """Request model for S&R analysis"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="OHLCV data")
    min_touches: int = Field(2, description="Minimum touches for level confirmation", ge=2, le=10)
    tolerance_percent: float = Field(0.5, description="Price tolerance for level grouping (%)", ge=0.1, le=2.0)
    lookback_period: int = Field(100, description="Lookback period in candles", ge=20, le=500)

class SupportResistanceResponse(BaseModel):
    """Response model for S&R analysis"""
    success: bool
    symbol: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# API Endpoints

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "service": "support_resistance_analysis",
        "status": "healthy",
        "features": [
            "support_level_detection",
            "resistance_level_detection",
            "level_strength_calculation",
            "touch_counting",
            "trading_zone_identification"
        ]
    }

@router.post("/analyze", response_model=SupportResistanceResponse)
async def analyze_support_resistance(request: SupportResistanceRequest):
    """
    Analyze and detect support & resistance levels
    
    - Identifies horizontal price levels
    - Calculates level strength
    - Counts touches
    - Provides nearest levels
    - Generates trading zones
    """
    try:
        if not request.data or len(request.data) < 20:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data. Need at least 20 candles"
            )
        
        result = sr_service.analyze_support_resistance(
            data=request.data,
            min_touches=request.min_touches,
            tolerance_percent=request.tolerance_percent,
            lookback_period=request.lookback_period,
            check_double_top=True  # Explicitly enable double top detection
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "S&R analysis failed")
            )
        
        return SupportResistanceResponse(
            success=True,
            symbol=request.symbol,
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing S&R: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/support")
async def get_support_levels(request: SupportResistanceRequest):
    """Get support levels only"""
    try:
        result = sr_service.analyze_support_resistance(
            data=request.data,
            min_touches=request.min_touches,
            tolerance_percent=request.tolerance_percent,
            lookback_period=request.lookback_period,
            check_double_top=True  # Explicitly enable double top detection
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "support_levels": result["data"]["support_levels"],
            "nearest_support": result["data"]["nearest_support"]
        }
        
    except Exception as e:
        logger.error(f"Error getting support levels: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/resistance")
async def get_resistance_levels(request: SupportResistanceRequest):
    """Get resistance levels only"""
    try:
        result = sr_service.analyze_support_resistance(
            data=request.data,
            min_touches=request.min_touches,
            tolerance_percent=request.tolerance_percent,
            lookback_period=request.lookback_period,
            check_double_top=True  # Explicitly enable double top detection
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "resistance_levels": result["data"]["resistance_levels"],
            "nearest_resistance": result["data"]["nearest_resistance"]
        }
        
    except Exception as e:
        logger.error(f"Error getting resistance levels: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/zones")
async def get_trading_zones(request: SupportResistanceRequest):
    """
    Get trading zones based on S&R levels
    
    Returns:
    - Current trading zone (upper/middle/lower)
    - Range size and percentage
    - Zone-specific trading advice
    """
    try:
        result = sr_service.analyze_support_resistance(
            data=request.data,
            min_touches=request.min_touches,
            tolerance_percent=request.tolerance_percent,
            lookback_period=request.lookback_period,
            check_double_top=True  # Explicitly enable double top detection
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "trading_zones": result["data"]["trading_zones"],
            "current_price": result["data"]["current_price"]
        }
        
    except Exception as e:
        logger.error(f"Error getting trading zones: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

