"""
Fibonacci Analysis API Routes
Endpoints for Fibonacci retracement, extension, and cluster analysis
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from backend.services.fibonacci_analysis import FibonacciAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fibonacci", tags=["fibonacci"])

# Initialize service
fibonacci_service = FibonacciAnalysisService()

# Request/Response Models

class FibonacciRetracementRequest(BaseModel):
    """Request model for Fibonacci retracement calculation"""
    high: float = Field(..., description="Swing high price", gt=0)
    low: float = Field(..., description="Swing low price", gt=0)
    trend_direction: str = Field("uptrend", description="Trend direction: uptrend or downtrend")
    custom_levels: Optional[List[float]] = Field(None, description="Custom Fibonacci ratios")

class FibonacciExtensionRequest(BaseModel):
    """Request model for Fibonacci extension calculation"""
    point_a: float = Field(..., description="First swing point", gt=0)
    point_b: float = Field(..., description="Second swing point (retracement)", gt=0)
    point_c: float = Field(..., description="Third swing point (continuation)", gt=0)
    custom_levels: Optional[List[float]] = Field(None, description="Custom extension ratios")

class AutoDetectRequest(BaseModel):
    """Request model for auto-detection of Fibonacci levels"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="OHLCV data")
    lookback_period: int = Field(50, description="Number of candles to analyze", ge=10, le=200)
    min_swing_strength: int = Field(5, description="Minimum bars for swing detection", ge=3, le=10)

class PriceAnalysisRequest(BaseModel):
    """Request model for price level analysis"""
    current_price: float = Field(..., description="Current stock price", gt=0)
    fib_levels: Dict[str, float] = Field(..., description="Fibonacci levels dictionary")
    tolerance: float = Field(0.005, description="Price tolerance as decimal", ge=0.001, le=0.02)

class ClusterAnalysisRequest(BaseModel):
    """Request model for Fibonacci cluster analysis"""
    fib_setups: List[Dict[str, Any]] = Field(..., description="Multiple Fibonacci setups")
    cluster_tolerance: float = Field(0.01, description="Cluster tolerance as decimal", ge=0.005, le=0.05)

# API Endpoints

@router.post("/retracement", response_model=Dict[str, Any])
async def calculate_retracement(request: FibonacciRetracementRequest):
    """
    Calculate Fibonacci retracement levels
    
    **Parameters:**
    - **high**: Swing high price
    - **low**: Swing low price
    - **trend_direction**: "uptrend" or "downtrend"
    - **custom_levels**: Optional custom Fibonacci ratios
    
    **Returns:**
    - Fibonacci retracement levels with trading implications
    """
    try:
        logger.info(f"Calculating Fibonacci retracement: high={request.high}, low={request.low}")
        
        # Validate input
        if request.high <= request.low:
            raise HTTPException(
                status_code=400,
                detail="High price must be greater than low price"
            )
        
        if request.trend_direction not in ["uptrend", "downtrend"]:
            raise HTTPException(
                status_code=400,
                detail="Trend direction must be 'uptrend' or 'downtrend'"
            )
        
        result = fibonacci_service.calculate_fibonacci_retracement(
            high=request.high,
            low=request.low,
            trend_direction=request.trend_direction,
            custom_levels=request.custom_levels
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate Fibonacci retracement"
            )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in calculate_retracement endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extension", response_model=Dict[str, Any])
async def calculate_extension(request: FibonacciExtensionRequest):
    """
    Calculate Fibonacci extension levels for profit targets
    
    **Parameters:**
    - **point_a**: First swing point
    - **point_b**: Second swing point (retracement)
    - **point_c**: Third swing point (continuation)
    - **custom_levels**: Optional custom extension ratios
    
    **Returns:**
    - Fibonacci extension levels with profit targets
    """
    try:
        logger.info(f"Calculating Fibonacci extension: A={request.point_a}, B={request.point_b}, C={request.point_c}")
        
        result = fibonacci_service.calculate_fibonacci_extension(
            point_a=request.point_a,
            point_b=request.point_b,
            point_c=request.point_c,
            custom_levels=request.custom_levels
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate Fibonacci extension"
            )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in calculate_extension endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-detect", response_model=Dict[str, Any])
async def auto_detect_fibonacci(request: AutoDetectRequest):
    """
    Automatically detect Fibonacci levels from price data
    
    **Parameters:**
    - **symbol**: Stock symbol
    - **data**: OHLCV data (list of candles)
    - **lookback_period**: Number of candles to analyze (default: 50)
    - **min_swing_strength**: Minimum bars for swing detection (default: 5)
    
    **Returns:**
    - List of auto-detected Fibonacci setups with current price analysis
    """
    try:
        logger.info(f"Auto-detecting Fibonacci levels for {request.symbol}")
        
        if not request.data:
            raise HTTPException(
                status_code=400,
                detail="Price data cannot be empty"
            )
        
        if len(request.data) < request.lookback_period:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: need at least {request.lookback_period} candles"
            )
        
        result = fibonacci_service.auto_detect_fibonacci_levels(
            data=request.data,
            lookback_period=request.lookback_period,
            min_swing_strength=request.min_swing_strength
        )
        
        return {
            "success": True,
            "symbol": request.symbol,
            "setups_found": len(result),
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto_detect_fibonacci endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/price-analysis", response_model=Dict[str, Any])
async def analyze_price_at_level(request: PriceAnalysisRequest):
    """
    Analyze if current price is at or near Fibonacci levels
    
    **Parameters:**
    - **current_price**: Current stock price
    - **fib_levels**: Dictionary of Fibonacci levels
    - **tolerance**: Price tolerance as decimal (default: 0.005 = 0.5%)
    
    **Returns:**
    - Analysis of price position with trading signals
    """
    try:
        logger.info(f"Analyzing price {request.current_price} against Fibonacci levels")
        
        result = fibonacci_service.analyze_price_at_fib_level(
            current_price=request.current_price,
            fib_levels=request.fib_levels,
            tolerance=request.tolerance
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze price at Fibonacci levels"
            )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_price_at_level endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clusters", response_model=Dict[str, Any])
async def find_fibonacci_clusters(request: ClusterAnalysisRequest):
    """
    Identify Fibonacci clusters (strong support/resistance zones)
    
    **Parameters:**
    - **fib_setups**: List of multiple Fibonacci calculations
    - **cluster_tolerance**: Price tolerance for clustering (default: 0.01 = 1%)
    
    **Returns:**
    - List of identified Fibonacci clusters with strength ratings
    """
    try:
        logger.info(f"Finding Fibonacci clusters from {len(request.fib_setups)} setups")
        
        if not request.fib_setups:
            raise HTTPException(
                status_code=400,
                detail="Need at least one Fibonacci setup"
            )
        
        result = fibonacci_service.calculate_fibonacci_clusters(
            multiple_fib_setups=request.fib_setups,
            cluster_tolerance=request.cluster_tolerance
        )
        
        return {
            "success": True,
            "clusters_found": len(result),
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in find_fibonacci_clusters endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/levels/standard", response_model=Dict[str, Any])
async def get_standard_levels():
    """
    Get standard Fibonacci retracement and extension levels
    
    **Returns:**
    - Dictionary of standard Fibonacci ratios
    """
    try:
        return {
            "success": True,
            "data": {
                "retracement_levels": fibonacci_service.retracement_levels,
                "extension_levels": fibonacci_service.extension_levels,
                "description": {
                    "retracement": "Used to identify potential support/resistance during pullbacks",
                    "extension": "Used to identify profit targets beyond the original move"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_standard_levels endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for Fibonacci analysis service"""
    return {
        "success": True,
        "service": "fibonacci_analysis",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Additional utility endpoints

@router.post("/batch-analysis", response_model=Dict[str, Any])
async def batch_fibonacci_analysis(
    symbols_data: Dict[str, List[Dict[str, Any]]],
    lookback_period: int = Query(50, ge=10, le=200),
    min_swing_strength: int = Query(5, ge=3, le=10)
):
    """
    Batch analyze multiple symbols for Fibonacci levels
    
    **Parameters:**
    - **symbols_data**: Dictionary of symbol -> OHLCV data
    - **lookback_period**: Number of candles to analyze
    - **min_swing_strength**: Minimum bars for swing detection
    
    **Returns:**
    - Fibonacci analysis for all provided symbols
    """
    try:
        logger.info(f"Batch analyzing {len(symbols_data)} symbols")
        
        results = {}
        
        for symbol, data in symbols_data.items():
            try:
                fib_setups = fibonacci_service.auto_detect_fibonacci_levels(
                    data=data,
                    lookback_period=lookback_period,
                    min_swing_strength=min_swing_strength
                )
                
                results[symbol] = {
                    "success": True,
                    "setups_found": len(fib_setups),
                    "data": fib_setups
                }
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                results[symbol] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "symbols_analyzed": len(symbols_data),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch_fibonacci_analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

