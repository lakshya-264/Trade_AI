"""
Swing Point Analysis API Routes
Endpoints for detecting and analyzing swing points (HH/HL/LH/LL)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from services.swing_point_analysis import SwingPointAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["swing_points"])

# Initialize service
swing_service = SwingPointAnalysisService()

# Request/Response Models

class SwingPointRequest(BaseModel):
    """Request model for swing point analysis"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="OHLCV data")
    strength: int = Field(5, description="Swing detection strength", ge=3, le=10)

class SwingPointResponse(BaseModel):
    """Response model for swing point analysis"""
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
        "service": "swing_point_analysis",
        "status": "healthy",
        "features": [
            "swing_high_detection",
            "swing_low_detection",
            "hh_hl_lh_ll_labeling",
            "trend_structure_analysis",
            "market_structure_identification"
        ]
    }

@router.post("/analyze", response_model=SwingPointResponse)
async def analyze_swing_points(request: SwingPointRequest):
    """
    Analyze swing points and label them as HH/HL/LH/LL
    
    - Detects swing highs and lows
    - Labels points based on price relationship
    - Provides trend analysis
    - Returns market structure
    """
    try:
        if not request.data or len(request.data) < request.strength * 2 + 1:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data. Need at least {request.strength * 2 + 1} candles"
            )
        
        result = swing_service.analyze_swing_points(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Swing point analysis failed")
            )
        
        return SwingPointResponse(
            success=True,
            symbol=request.symbol,
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing swing points: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary")
async def get_swing_summary(request: SwingPointRequest):
    """
    Get a quick summary of swing point analysis
    
    Returns simplified view with:
    - Current trend
    - Latest swing label
    - Recent pattern sequence
    """
    try:
        if not request.data or len(request.data) < request.strength * 2 + 1:
            return {
                "success": False,
                "error": f"Insufficient data. Need at least {request.strength * 2 + 1} candles"
            }
        
        result = swing_service.get_swing_analysis_summary(
            data=request.data,
            strength=request.strength
        )
        
        return {
            "success": result.get("success", False),
            "symbol": request.symbol,
            "summary": result.get("summary"),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error getting swing summary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/recent")
async def get_recent_swings(request: SwingPointRequest):
    """
    Get only the most recent swing points (last 10)
    
    Useful for quick chart annotations
    """
    try:
        result = swing_service.analyze_swing_points(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        data = result["data"]
        
        return {
            "success": True,
            "symbol": request.symbol,
            "recent_points": data.get("recent_points", []),
            "current_structure": data.get("current_structure"),
            "trend": data["trend_analysis"]["trend"]
        }
        
    except Exception as e:
        logger.error(f"Error getting recent swings: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/trend")
async def get_trend_structure(request: SwingPointRequest):
    """
    Get trend structure analysis based on swing points
    
    Returns:
    - Overall trend (uptrend/downtrend/sideways)
    - Confidence level
    - Bullish vs bearish signals
    - Pattern counts (HH/HL/LH/LL)
    """
    try:
        result = swing_service.analyze_swing_points(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        trend_analysis = result["data"]["trend_analysis"]
        statistics = result["data"]["statistics"]
        
        return {
            "success": True,
            "symbol": request.symbol,
            "trend_analysis": trend_analysis,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trend structure: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

