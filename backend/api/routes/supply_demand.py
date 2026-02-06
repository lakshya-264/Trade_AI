"""
Supply & Demand Zone API Routes
Endpoints for detecting institutional order blocks and zones
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging

from services.supply_demand import SupplyDemandService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["supply_demand"])

# Initialize service
sd_service = SupplyDemandService()

# Request/Response Models

class SupplyDemandRequest(BaseModel):
    """Request model for supply/demand analysis"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="OHLCV data")
    lookback_period: int = Field(100, description="Lookback period in candles", ge=20, le=500)
    min_zone_strength: float = Field(0.5, description="Minimum zone strength (0-1)", ge=0.0, le=1.0)

class SupplyDemandResponse(BaseModel):
    """Response model for supply/demand analysis"""
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
        "service": "supply_demand_analysis",
        "status": "healthy",
        "features": [
            "demand_zone_detection",
            "supply_zone_detection",
            "order_block_identification",
            "zone_strength_calculation",
            "fresh_tested_broken_classification",
            "institutional_trading_zones"
        ]
    }

@router.post("/analyze", response_model=SupplyDemandResponse)
async def analyze_supply_demand(request: SupplyDemandRequest):
    """
    Analyze and detect supply & demand zones
    
    - Identifies demand zones (order blocks before bullish moves)
    - Identifies supply zones (order blocks before bearish moves)
    - Calculates zone strength
    - Classifies zones (fresh, tested, broken)
    - Provides trading signals
    """
    try:
        if not request.data or len(request.data) < 20:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data. Need at least 20 candles"
            )
        
        result = sd_service.analyze_supply_demand(
            data=request.data,
            lookback_period=request.lookback_period,
            min_zone_strength=request.min_zone_strength
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Supply/Demand analysis failed")
            )
        
        return SupplyDemandResponse(
            success=True,
            symbol=request.symbol,
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing supply/demand: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demand")
async def get_demand_zones(request: SupplyDemandRequest):
    """
    Get demand zones only
    
    Demand zones are areas where institutional buying occurred,
    causing price to move up sharply. These act as support.
    """
    try:
        result = sd_service.analyze_supply_demand(
            data=request.data,
            lookback_period=request.lookback_period,
            min_zone_strength=request.min_zone_strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "demand_zones": result["data"]["demand_zones"],
            "active_demand_zones": result["data"]["active_demand_zones"],
            "nearest_demand": result["data"]["nearest_demand"]
        }
        
    except Exception as e:
        logger.error(f"Error getting demand zones: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/supply")
async def get_supply_zones(request: SupplyDemandRequest):
    """
    Get supply zones only
    
    Supply zones are areas where institutional selling occurred,
    causing price to move down sharply. These act as resistance.
    """
    try:
        result = sd_service.analyze_supply_demand(
            data=request.data,
            lookback_period=request.lookback_period,
            min_zone_strength=request.min_zone_strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "symbol": request.symbol,
            "supply_zones": result["data"]["supply_zones"],
            "active_supply_zones": result["data"]["active_supply_zones"],
            "nearest_supply": result["data"]["nearest_supply"]
        }
        
    except Exception as e:
        logger.error(f"Error getting supply zones: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/fresh")
async def get_fresh_zones(request: SupplyDemandRequest):
    """
    Get only fresh (untested) zones
    
    Fresh zones are the strongest because price hasn't
    revisited them yet. High probability setups.
    """
    try:
        result = sd_service.analyze_supply_demand(
            data=request.data,
            lookback_period=request.lookback_period,
            min_zone_strength=request.min_zone_strength
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error")
            }
        
        # Filter for fresh zones only
        fresh_demand = [z for z in result["data"]["active_demand_zones"] if z['status'] == 'fresh']
        fresh_supply = [z for z in result["data"]["active_supply_zones"] if z['status'] == 'fresh']
        
        return {
            "success": True,
            "symbol": request.symbol,
            "fresh_demand_zones": fresh_demand,
            "fresh_supply_zones": fresh_supply,
            "total_fresh": len(fresh_demand) + len(fresh_supply)
        }
        
    except Exception as e:
        logger.error(f"Error getting fresh zones: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/signals")
async def get_trading_signals(request: SupplyDemandRequest):
    """
    Get trading signals based on supply/demand zones
    
    Returns:
    - Current signal (buy/sell/neutral)
    - Zone being reacted to
    - Entry and stop loss suggestions
    - Target zones
    """
    try:
        result = sd_service.analyze_supply_demand(
            data=request.data,
            lookback_period=request.lookback_period,
            min_zone_strength=request.min_zone_strength
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
            "current_price": result["data"]["current_price"],
            "statistics": result["data"]["statistics"]
        }
        
    except Exception as e:
        logger.error(f"Error getting trading signals: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

