"""
Market Structure API Routes
Endpoints for BOS (Break of Structure) and CHoCH (Change of Character) detection
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging

from services.market_structure import MarketStructureService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["market_structure"])

# Initialize service
market_structure_service = MarketStructureService()

# Request/Response Models

class MarketStructureRequest(BaseModel):
    """Request model for market structure analysis"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="OHLCV data")
    strength: int = Field(5, description="Swing detection strength", ge=3, le=10)

class MarketStructureResponse(BaseModel):
    """Response model for market structure analysis"""
    success: bool
    symbol: str
    data: Dict[str, Any] = None
    error: str = None

# API Endpoints

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "service": "market_structure_analysis",
        "status": "healthy",
        "features": [
            "break_of_structure_detection",
            "change_of_character_detection",
            "trend_continuation_signals",
            "reversal_signals",
            "smart_money_concepts"
        ]
    }

@router.post("/analyze", response_model=MarketStructureResponse)
async def analyze_market_structure(request: MarketStructureRequest):
    """
    Analyze market structure and detect BOS/CHoCH
    
    - Detects Break of Structure (BOS) - Continuation patterns
    - Detects Change of Character (CHoCH) - Reversal patterns
    - Provides trading signals
    - Identifies current market structure
    """
    try:
        if not request.data or len(request.data) < request.strength * 4:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data. Need at least {request.strength * 4} candles"
            )
        
        result = market_structure_service.analyze_market_structure(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Market structure analysis failed")
            )
        
        return MarketStructureResponse(
            success=True,
            symbol=request.symbol,
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing market structure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bos")
async def get_bos_events(request: MarketStructureRequest):
    """
    Get Break of Structure (BOS) events only
    
    BOS indicates trend continuation:
    - Bullish BOS: Price breaks above previous high in uptrend
    - Bearish BOS: Price breaks below previous low in downtrend
    """
    try:
        result = market_structure_service.analyze_market_structure(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "bos_events": result["data"]["bos_events"],
            "statistics": {
                "total_bos": result["data"]["statistics"]["bos_count"],
                "bos_bullish": result["data"]["statistics"]["bos_bullish"],
                "bos_bearish": result["data"]["statistics"]["bos_bearish"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting BOS events: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/choch")
async def get_choch_events(request: MarketStructureRequest):
    """
    Get Change of Character (CHoCH) events only
    
    CHoCH indicates potential trend reversal:
    - Bullish CHoCH: Price breaks structure to upside (reversal from downtrend)
    - Bearish CHoCH: Price breaks structure to downside (reversal from uptrend)
    """
    try:
        result = market_structure_service.analyze_market_structure(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "choch_events": result["data"]["choch_events"],
            "statistics": {
                "total_choch": result["data"]["statistics"]["choch_count"],
                "choch_bullish": result["data"]["statistics"]["choch_bullish"],
                "choch_bearish": result["data"]["statistics"]["choch_bearish"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting CHoCH events: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/signals")
async def get_trading_signals(request: MarketStructureRequest):
    """
    Get trading signals based on market structure
    
    Returns:
    - Current signal (buy/sell/neutral)
    - Confidence level
    - Entry suggestions
    - Stop loss recommendations
    """
    try:
        result = market_structure_service.analyze_market_structure(
            data=request.data,
            strength=request.strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "signals": result["data"]["trading_signals"],
            "current_structure": result["data"]["current_structure"]
        }
        
    except Exception as e:
        logger.error(f"Error getting trading signals: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

