"""
Trendline Detection API Routes
Endpoints for automatic trendline detection, channel detection, and trendline breaks
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import numpy as np

from services.trendline_detection import TrendlineDetectionService
from core.auth_dependencies import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(tags=["trendlines"])

# Initialize service
trendline_service = TrendlineDetectionService()

def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON serialization.
    Handles numpy.bool_, numpy.bool, numpy.int64, numpy.float64, numpy.ndarray, etc.
    """
    # Handle None
    if obj is None:
        return None
    
    # Check if it's a NumPy scalar type (most common case)
    # np.generic is the base class for all NumPy scalar types
    if isinstance(obj, np.generic):
        try:
            # .item() converts any NumPy scalar to Python native type
            return obj.item()
        except (AttributeError, ValueError, TypeError):
            # Fallback: explicit conversion
            if isinstance(obj, (np.bool_, bool)) or type(obj).__name__ in ('bool_', 'bool'):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.complexfloating):
                return complex(obj)
    
    # Check by type string (catches edge cases like numpy.bool vs numpy.bool_)
    type_str = str(type(obj))
    if 'numpy' in type_str.lower():
        # Try .item() method if available
        if hasattr(obj, 'item'):
            try:
                return obj.item()
            except (AttributeError, ValueError, TypeError):
                pass
        
        # Explicit conversion based on type string
        if 'bool' in type_str.lower():
            return bool(obj)
        elif 'int' in type_str.lower():
            return int(obj)
        elif 'float' in type_str.lower():
            return float(obj)
        elif 'complex' in type_str.lower():
            return complex(obj)
    
    # Handle NumPy arrays
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Handle pandas types
    if hasattr(obj, 'to_dict'):
        try:
            return convert_numpy_types(obj.to_dict())
        except (AttributeError, ValueError, TypeError):
            pass
    
    # Recursively handle collections (do this after NumPy checks)
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    
    return obj

# Request/Response Models

class TrendlineDetectionRequest(BaseModel):
    """Request model for trendline detection"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[Dict[str, Any]] = Field(..., description="OHLCV data")
    min_touches: int = Field(2, description="Minimum touches required", ge=2, le=5)
    lookback_period: int = Field(100, description="Number of candles to analyze", ge=20, le=500)

class TrendlineBreakAlert(BaseModel):
    """Model for trendline break alerts"""
    symbol: str
    trendline_type: str
    break_direction: str
    break_price: float
    break_percentage: float

# API Endpoints

@router.post("/detect", response_model=Dict[str, Any])
async def detect_trendlines(request: TrendlineDetectionRequest):
    """
    Automatically detect trendlines, channels, and support/resistance
    
    **Parameters:**
    - **symbol**: Stock symbol
    - **data**: OHLCV price data
    - **min_touches**: Minimum touches required (default: 2)
    - **lookback_period**: Number of candles to analyze (default: 100)
    
    **Returns:**
    - Uptrend lines
    - Downtrend lines
    - Horizontal support/resistance
    - Channels
    - Swing points
    - Current trend analysis
    - Recent trendline breaks
    """
    try:
        logger.info(f"Detecting trendlines for {request.symbol}")
        
        if not request.data or len(request.data) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data: need at least 10 candles"
            )
        
        result = trendline_service.detect_all_trendlines(
            data=request.data,
            min_touches=request.min_touches,
            lookback_period=request.lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types for JSON serialization
        result = convert_numpy_types(result)
        
        return {
            "success": True,
            "symbol": request.symbol,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_trendlines endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/uptrends", response_model=Dict[str, Any])
async def detect_uptrends_only(
    symbol: str,
    data: List[Dict[str, Any]],
    min_touches: int = Query(2, ge=2, le=5),
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Detect only uptrend lines (connecting swing lows)
    
    **Use Case:** When you only want to see support trendlines
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=min_touches,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        return {
            "success": True,
            "symbol": symbol,
            "uptrend_lines": result.get("uptrend_lines", []),
            "best_uptrend": result.get("best_uptrend"),
            "swing_lows": result.get("swing_lows", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting uptrends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/downtrends", response_model=Dict[str, Any])
async def detect_downtrends_only(
    symbol: str,
    data: List[Dict[str, Any]],
    min_touches: int = Query(2, ge=2, le=5),
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Detect only downtrend lines (connecting swing highs)
    
    **Use Case:** When you only want to see resistance trendlines
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=min_touches,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        return {
            "success": True,
            "symbol": symbol,
            "downtrend_lines": result.get("downtrend_lines", []),
            "best_downtrend": result.get("best_downtrend"),
            "swing_highs": result.get("swing_highs", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting downtrends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/channels", response_model=Dict[str, Any])
async def detect_channels(
    symbol: str,
    data: List[Dict[str, Any]],
    min_touches: int = Query(2, ge=2, le=5),
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Detect price channels (parallel trendlines)
    
    **Returns:**
    - Ascending channels (uptrend + parallel resistance)
    - Descending channels (downtrend + parallel support)
    - Channel width and percentage
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=min_touches,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        return {
            "success": True,
            "symbol": symbol,
            "channels": result.get("channels", []),
            "channel_count": len(result.get("channels", [])),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/horizontal", response_model=Dict[str, Any])
async def detect_horizontal_levels(
    symbol: str,
    data: List[Dict[str, Any]],
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Detect horizontal support and resistance levels
    
    **Returns:**
    - Key price levels where price repeatedly reacted
    - Strength of each level
    - Number of touches
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=2,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        return {
            "success": True,
            "symbol": symbol,
            "horizontal_lines": result.get("horizontal_lines", []),
            "count": len(result.get("horizontal_lines", [])),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting horizontal levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/breaks", response_model=Dict[str, Any])
async def detect_trendline_breaks(
    symbol: str,
    data: List[Dict[str, Any]],
    min_touches: int = Query(2, ge=2, le=5),
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Detect recent trendline breaks (bullish or bearish signals)
    
    **Returns:**
    - Recently broken trendlines
    - Break direction and strength
    - Potential trading signals
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=min_touches,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        breaks = result.get("recent_breaks", [])
        
        # Generate trading signals from breaks (using enhanced break information)
        signals = []
        for break_info in breaks:
            # Use enhanced break information if available
            break_direction = break_info.get("break_direction", 
                "BEARISH" if break_info["trendline_type"] == "uptrend" else "BULLISH")
            break_strength = break_info.get("break_strength", "weak")
            signal_quality = break_info.get("signal_quality", "LOW")
            volume_confirmed = break_info.get("volume_confirmed", False)
            retest = break_info.get("retest", {})
            
            # Build reason message
            reason_parts = []
            if break_info["trendline_type"] == "uptrend":
                reason_parts.append("Uptrend line broken")
            else:
                reason_parts.append("Downtrend line broken")
            
            if volume_confirmed:
                reason_parts.append("with volume confirmation")
            
            if retest.get("retested", False):
                reason_parts.append(f"and retested as {retest.get('retest_type', 'level')}")
            
            reason = " - ".join(reason_parts) + " - potential reversal"
            
            # Map break strength to signal strength
            strength_map = {
                "very_strong": "VERY_STRONG",
                "strong": "STRONG",
                "moderate": "MODERATE",
                "weak": "WEAK"
            }
            signal_strength = strength_map.get(break_strength, "MODERATE")
            
            signal = {
                "type": break_direction,
                "reason": reason,
                "strength": signal_strength,
                "quality": signal_quality,
                "break_type": break_info.get("break_type", "close"),
                "volume_confirmed": volume_confirmed,
                "retested": retest.get("retested", False)
            }
            
            signals.append({
                **break_info,
                "signal": signal
            })
        
        return {
            "success": True,
            "symbol": symbol,
            "breaks": breaks,
            "trading_signals": signals,
            "has_recent_breaks": len(breaks) > 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting trendline breaks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/current-trend", response_model=Dict[str, Any])
async def get_current_trend(
    symbol: str,
    data: List[Dict[str, Any]],
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Determine current trend based on trendline analysis
    
    **Returns:**
    - Current trend: uptrend, downtrend, or sideways
    - Confidence level
    - Supporting trendline data
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=2,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        current_trend = result.get("current_trend", {})
        
        return {
            "success": True,
            "symbol": symbol,
            "trend": current_trend.get("trend", "unknown"),
            "confidence": current_trend.get("confidence", "low"),
            "trendline": current_trend.get("trendline"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/swing-points", response_model=Dict[str, Any])
async def get_swing_points(
    symbol: str,
    data: List[Dict[str, Any]],
    lookback_period: int = Query(100, ge=20, le=500),
    strength: int = Query(5, description="Swing detection strength", ge=3, le=10)
):
    """
    Get swing high and swing low points
    
    **Parameters:**
    - **strength**: Number of bars on each side for swing detection (3-10)
    
    **Returns:**
    - Swing highs
    - Swing lows
    - Recent swing points highlighted
    """
    try:
        result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=2,
            lookback_period=lookback_period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Convert NumPy types to native Python types
        result = convert_numpy_types(result)
        
        return {
            "success": True,
            "symbol": symbol,
            "swing_highs": result.get("swing_highs", []),
            "swing_lows": result.get("swing_lows", []),
            "total_swing_highs": len(result.get("swing_highs", [])),
            "total_swing_lows": len(result.get("swing_lows", [])),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting swing points: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for trendline detection service"""
    return {
        "success": True,
        "service": "trendline_detection",
        "status": "healthy",
        "features": [
            "auto_trendline_detection",
            "channel_detection",
            "horizontal_support_resistance",
            "trendline_break_detection",
            "swing_point_detection",
            "trend_analysis"
        ],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/batch-detection", response_model=Dict[str, Any])
async def batch_trendline_detection(
    symbols_data: Dict[str, List[Dict[str, Any]]],
    min_touches: int = Query(2, ge=2, le=5),
    lookback_period: int = Query(100, ge=20, le=500)
):
    """
    Batch detect trendlines for multiple symbols
    
    **Use Case:** Scan entire watchlist for trendline setups
    """
    try:
        logger.info(f"Batch detecting trendlines for {len(symbols_data)} symbols")
        
        results = {}
        
        for symbol, data in symbols_data.items():
            try:
                result = trendline_service.detect_all_trendlines(
                    data=data,
                    min_touches=min_touches,
                    lookback_period=lookback_period
                )
                
                # Convert NumPy types to native Python types
                result = convert_numpy_types(result)
                
                results[symbol] = {
                    "success": True,
                    "data": result
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
        logger.error(f"Error in batch trendline detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MANUAL TRENDLINE ENDPOINTS ====================

class ManualTrendlineRequest(BaseModel):
    """Request model for saving manual trendline"""
    symbol: str
    start_time: Union[int, float]
    start_price: float
    end_time: Union[int, float]
    end_price: float
    type: str = Field("manual", description="Trendline type: manual, uptrend, downtrend, horizontal")
    color: Optional[str] = Field("#3B82F6", description="Line color")
    line_width: Optional[int] = Field(2, description="Line width")
    notes: Optional[str] = Field(None, description="User notes")

@router.post("/manual/save", response_model=Dict[str, Any])
async def save_manual_trendline(
    request: ManualTrendlineRequest,
    current_user = Depends(get_current_user_optional)
):
    """
    Save a manually drawn trendline
    
    **Use Case:** User draws trendline on chart and wants to save it
    """
    try:
        from services.drawing_tools import DrawingToolsService
        drawing_service = DrawingToolsService()
        
        user_id = None
        if current_user:
            user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id") if isinstance(current_user, dict) else None)
        
        chart_id = f"{request.symbol}_trendlines"
        
        # Calculate slope and intercept for the trendline
        # Convert time to index for calculation
        time_diff = request.end_time - request.start_time if isinstance(request.end_time, (int, float)) and isinstance(request.start_time, (int, float)) else 1
        slope = (request.end_price - request.start_price) / time_diff if time_diff != 0 else 0
        intercept = request.start_price - slope * request.start_time if isinstance(request.start_time, (int, float)) else request.start_price
        
        # Determine trendline type based on slope
        trendline_type = request.type
        if trendline_type == "manual":
            if slope > 0:
                trendline_type = "uptrend"
            elif slope < 0:
                trendline_type = "downtrend"
            else:
                trendline_type = "horizontal"
        
        # Save as drawing tool
        drawing_id = await drawing_service.save_drawing(
            user_id=user_id,
            chart_id=chart_id,
            drawing_type="trendline",
            points=[
                {"x": request.start_time, "y": request.start_price},
                {"x": request.end_time, "y": request.end_price}
            ],
            style={
                "color": request.color,
                "lineWidth": request.line_width,
                "type": trendline_type,
                "slope": slope,
                "intercept": intercept,
                "notes": request.notes
            },
            name=f"Manual {trendline_type} trendline"
        )
        
        return {
            "success": True,
            "data": {
                "id": drawing_id,
                "symbol": request.symbol,
                "type": trendline_type,
                "start_time": request.start_time,
                "start_price": request.start_price,
                "end_time": request.end_time,
                "end_price": request.end_price,
                "slope": slope,
                "intercept": intercept,
                "color": request.color,
                "line_width": request.line_width,
                "notes": request.notes
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error saving manual trendline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/manual/{symbol}", response_model=Dict[str, Any])
async def get_manual_trendlines(
    symbol: str,
    current_user = Depends(get_current_user_optional)
):
    """
    Get all manual trendlines for a symbol
    
    **Returns:** List of manually drawn trendlines
    """
    try:
        from services.drawing_tools import DrawingToolsService
        drawing_service = DrawingToolsService()
        
        user_id = None
        if current_user:
            user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id") if isinstance(current_user, dict) else None)
        
        chart_id = f"{symbol}_trendlines"
        drawings = await drawing_service.get_drawings(user_id=user_id, chart_id=chart_id)
        
        # Filter for trendline type and convert to trendline format
        manual_trendlines = []
        for drawing in drawings:
            if drawing.get("drawing_type") == "trendline":
                style = drawing.get("style", {})
                points = drawing.get("points", [])
                
                if len(points) >= 2:
                    manual_trendlines.append({
                        "id": drawing.get("id"),
                        "type": style.get("type", "manual"),
                        "start_time": points[0].get("x"),
                        "start_price": points[0].get("y"),
                        "end_time": points[1].get("x"),
                        "end_price": points[1].get("y"),
                        "slope": style.get("slope", 0),
                        "intercept": style.get("intercept", 0),
                        "color": style.get("color", "#3B82F6"),
                        "line_width": style.get("lineWidth", 2),
                        "notes": style.get("notes"),
                        "is_manual": True,
                        "created_at": drawing.get("created_at")
                    })
        
        return {
            "success": True,
            "symbol": symbol,
            "manual_trendlines": manual_trendlines,
            "count": len(manual_trendlines),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching manual trendlines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/manual/{trendline_id}", response_model=Dict[str, Any])
async def delete_manual_trendline(
    trendline_id: str,
    current_user = Depends(get_current_user_optional)
):
    """
    Delete a manual trendline
    
    **Use Case:** User wants to remove a manually drawn trendline
    """
    try:
        from services.drawing_tools import DrawingToolsService
        drawing_service = DrawingToolsService()
        
        user_id = None
        if current_user:
            user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id") if isinstance(current_user, dict) else None)
        
        # Delete drawing
        await drawing_service.delete_drawing(user_id=user_id, drawing_id=trendline_id)
        
        return {
            "success": True,
            "message": "Manual trendline deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error deleting manual trendline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/project", response_model=Dict[str, Any])
async def project_trendline(
    symbol: str,
    data: List[Dict[str, Any]],
    trendline: Dict[str, Any],
    future_bars: int = Query(20, ge=5, le=100, description="Number of bars to project into future")
):
    """
    Project a trendline into the future and calculate price targets
    
    **Parameters:**
    - **symbol**: Stock symbol
    - **data**: OHLCV price data (for time calculation)
    - **trendline**: Trendline object to project
    - **future_bars**: Number of bars to project (5-100)
    
    **Returns:**
    - Projected prices at each future bar
    - Target zones (upper/lower bounds)
    - Key targets (short/medium/long term)
    """
    try:
        result = trendline_service.project_trendline(
            trendline=trendline,
            future_bars=future_bars,
            data=data
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "symbol": symbol,
            "projection": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error projecting trendline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/project-all", response_model=Dict[str, Any])
async def project_all_trendlines(
    symbol: str,
    data: List[Dict[str, Any]],
    min_touches: int = Query(2, ge=2, le=5),
    lookback_period: int = Query(100, ge=20, le=500),
    future_bars: int = Query(20, ge=5, le=100)
):
    """
    Detect trendlines and project all of them into the future
    
    **Use Case:** Get price targets for all significant trendlines
    
    **Returns:**
    - All detected trendlines
    - Projections for each trendline
    - Combined target zones
    """
    try:
        # First detect all trendlines
        detection_result = trendline_service.detect_all_trendlines(
            data=data,
            min_touches=min_touches,
            lookback_period=lookback_period
        )
        
        if "error" in detection_result:
            raise HTTPException(status_code=400, detail=detection_result["error"])
        
        # Combine all trendlines
        all_trendlines = (
            detection_result.get("uptrend_lines", []) +
            detection_result.get("downtrend_lines", []) +
            detection_result.get("horizontal_lines", [])
        )
        
        # Project all trendlines
        projection_result = trendline_service.project_all_trendlines(
            trendlines=all_trendlines[:10],  # Top 10 trendlines
            future_bars=future_bars,
            data=data
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "trendlines": detection_result,
            "projections": projection_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in project_all_trendlines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

