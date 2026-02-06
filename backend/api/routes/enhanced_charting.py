"""
Enhanced Charting API Routes
Comprehensive TradingView-style charting system backend
Supports multi-chart layouts, technical indicators, drawing tools, alerts, and watchlists
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import json

from core.database import get_db
from core.auth_dependencies import get_current_user
from services.enhanced_chart_service import EnhancedChartService
from services.technical_indicators import TechnicalIndicatorsService
from services.drawing_tools import DrawingToolsService
from services.alert_system import AlertSystemService
from services.watchlist_service import WatchlistService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
chart_service = EnhancedChartService()
indicators_service = TechnicalIndicatorsService()
drawing_service = DrawingToolsService()
alert_service = AlertSystemService()
watchlist_service = WatchlistService()

# Pydantic models for request validation
class ChartDataRequest(BaseModel):
    symbol: str
    timeframe: str = "1D"
    period: int = 100
    indicators: Optional[List[str]] = None
    drawings: Optional[List[Dict]] = None

class MultiChartRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1D"
    period: int = 100
    indicators: Optional[List[str]] = None

class IndicatorRequest(BaseModel):
    symbol: str
    indicator_type: str
    parameters: Dict[str, Any]
    timeframe: str = "1D"

class DrawingRequest(BaseModel):
    chart_id: str
    drawing_type: str
    points: List[Dict[str, Any]]
    style: Dict[str, Any]
    name: Optional[str] = None

class AlertRequest(BaseModel):
    symbol: str
    condition_type: str
    operator: str
    value: float
    notifications: Dict[str, bool]
    cooldown_minutes: int = 30
    name: Optional[str] = None

class WatchlistRequest(BaseModel):
    name: str
    symbols: List[str]
    is_default: bool = False

class SymbolSearchRequest(BaseModel):
    query: str
    exchange: str = "NSE"
    limit: int = 20

# ==================== CHART DATA ENDPOINTS ====================

@router.get("/chart-data/{symbol}")
async def get_chart_data(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1D, 1W, 1M"),
    period: int = Query(100, description="Number of data points"),
    indicators: Optional[str] = Query(None, description="Comma-separated indicators"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive chart data with indicators"""
    try:
        indicator_list = indicators.split(",") if indicators else []
        
        result = await chart_service.get_comprehensive_chart_data(
            symbol=symbol,
            timeframe=timeframe,
            period=period,
            indicators=indicator_list
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "message": f"Chart data for {symbol} retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting chart data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multi-chart-data")
async def get_multi_chart_data(
    request: MultiChartRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data for multiple charts simultaneously"""
    try:
        result = await chart_service.get_multi_chart_data(
            symbols=request.symbols,
            timeframe=request.timeframe,
            period=request.period,
            indicators=request.indicators
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "message": f"Multi-chart data for {len(request.symbols)} symbols retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting multi-chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-data/{symbol}")
async def get_latest_data(
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get latest real-time data for symbol"""
    try:
        result = await chart_service.get_latest_data(symbol)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting latest data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TECHNICAL INDICATORS ENDPOINTS ====================

@router.post("/indicators/calculate")
async def calculate_indicator(
    request: IndicatorRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate specific technical indicator"""
    try:
        result = await indicators_service.calculate_indicator(
            symbol=request.symbol,
            indicator_type=request.indicator_type,
            parameters=request.parameters,
            timeframe=request.timeframe
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "message": f"{request.indicator_type} calculated successfully for {request.symbol}"
        }
    except Exception as e:
        logger.error(f"Error calculating indicator {request.indicator_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicators/available")
async def get_available_indicators():
    """Get list of available technical indicators"""
    try:
        indicators = indicators_service.get_available_indicators()
        
        return {
            "success": True,
            "data": indicators,
            "timestamp": datetime.now().isoformat(),
            "message": f"{len(indicators)} indicators available"
        }
    except Exception as e:
        logger.error(f"Error getting available indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicators/{symbol}")
async def get_symbol_indicators(
    symbol: str,
    indicators: Optional[str] = Query(None, description="Comma-separated indicators"),
    timeframe: str = Query("1D", description="Timeframe"),
    period: int = Query(200, description="Data period"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get multiple indicators for a symbol"""
    try:
        indicator_list = indicators.split(",") if indicators else None
        
        result = await indicators_service.get_multiple_indicators(
            symbol=symbol,
            indicators=indicator_list,
            timeframe=timeframe,
            period=period
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "message": f"Indicators calculated successfully for {symbol}"
        }
    except Exception as e:
        logger.error(f"Error getting indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DRAWING TOOLS ENDPOINTS ====================

@router.post("/drawings/save")
async def save_drawing(
    request: DrawingRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save drawing to database"""
    try:
        drawing_id = await drawing_service.save_drawing(
            user_id=current_user["id"],
            chart_id=request.chart_id,
            drawing_type=request.drawing_type,
            points=request.points,
            style=request.style,
            name=request.name
        )
        
        return {
            "success": True,
            "data": {"drawing_id": drawing_id},
            "timestamp": datetime.now().isoformat(),
            "message": "Drawing saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving drawing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drawings/{chart_id}")
async def get_drawings(
    chart_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all drawings for a chart"""
    try:
        drawings = await drawing_service.get_drawings(
            user_id=current_user["id"],
            chart_id=chart_id
        )
        
        return {
            "success": True,
            "data": drawings,
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(drawings)} drawings for chart {chart_id}"
        }
    except Exception as e:
        logger.error(f"Error getting drawings for chart {chart_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/drawings/{drawing_id}")
async def delete_drawing(
    drawing_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete drawing"""
    try:
        success = await drawing_service.delete_drawing(
            drawing_id=drawing_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        return {
            "success": True,
            "message": "Drawing deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting drawing {drawing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/drawings/{drawing_id}")
async def update_drawing(
    drawing_id: str,
    request: DrawingRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update drawing"""
    try:
        success = await drawing_service.update_drawing(
            drawing_id=drawing_id,
            user_id=current_user["id"],
            updates={
                "drawing_type": request.drawing_type,
                "points": request.points,
                "style": request.style,
                "name": request.name
            }
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        return {
            "success": True,
            "message": "Drawing updated successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating drawing {drawing_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ALERT SYSTEM ENDPOINTS ====================

@router.post("/alerts/create")
async def create_alert(
    request: AlertRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new price/indicator alert"""
    try:
        alert_id = await alert_service.create_alert(
            user_id=current_user["id"],
            symbol=request.symbol,
            condition_type=request.condition_type,
            operator=request.operator,
            value=request.value,
            notifications=request.notifications,
            cooldown_minutes=request.cooldown_minutes,
            name=request.name
        )
        
        return {
            "success": True,
            "data": {"alert_id": alert_id},
            "timestamp": datetime.now().isoformat(),
            "message": f"Alert created successfully for {request.symbol}"
        }
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_user_alerts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all alerts for current user"""
    try:
        alerts = await alert_service.get_user_alerts(current_user["id"])
        
        return {
            "success": True,
            "data": alerts,
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(alerts)} alerts"
        }
    except Exception as e:
        logger.error(f"Error getting user alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{alert_id}")
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific alert details"""
    try:
        alert = await alert_service.get_alert(alert_id, current_user["id"])
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "data": alert,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete alert"""
    try:
        success = await alert_service.delete_alert(alert_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "message": "Alert deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/{alert_id}/toggle")
async def toggle_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle alert active status"""
    try:
        success = await alert_service.toggle_alert(alert_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "message": "Alert status toggled successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error toggling alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/triggers")
async def get_alert_triggers(
    limit: int = Query(50, description="Maximum number of triggers"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent alert triggers for user"""
    try:
        triggers = await alert_service.get_user_triggers(current_user["id"], limit)
        
        return {
            "success": True,
            "data": triggers,
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(triggers)} recent triggers"
        }
    except Exception as e:
        logger.error(f"Error getting alert triggers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WATCHLIST ENDPOINTS ====================

@router.get("/watchlists")
async def get_watchlists(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's watchlists"""
    try:
        watchlists = await watchlist_service.get_user_watchlists(current_user["id"])
        
        return {
            "success": True,
            "data": watchlists,
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(watchlists)} watchlists"
        }
    except Exception as e:
        logger.error(f"Error getting watchlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watchlists")
async def create_watchlist(
    request: WatchlistRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new watchlist"""
    try:
        watchlist_id = await watchlist_service.create_watchlist(
            user_id=current_user["id"],
            name=request.name,
            symbols=request.symbols,
            is_default=request.is_default
        )
        
        return {
            "success": True,
            "data": {"watchlist_id": watchlist_id},
            "timestamp": datetime.now().isoformat(),
            "message": f"Watchlist '{request.name}' created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watchlists/{watchlist_id}/symbols")
async def add_symbol_to_watchlist(
    watchlist_id: str,
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add symbol to watchlist"""
    try:
        success = await watchlist_service.add_symbol(
            watchlist_id=watchlist_id,
            symbol=symbol,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        return {
            "success": True,
            "message": f"Symbol {symbol} added to watchlist",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error adding symbol to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlists/{watchlist_id}/symbols/{symbol}")
async def remove_symbol_from_watchlist(
    watchlist_id: str,
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove symbol from watchlist"""
    try:
        success = await watchlist_service.remove_symbol(
            watchlist_id=watchlist_id,
            symbol=symbol,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Watchlist or symbol not found")
        
        return {
            "success": True,
            "message": f"Symbol {symbol} removed from watchlist",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error removing symbol from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete watchlist"""
    try:
        success = await watchlist_service.delete_watchlist(
            watchlist_id=watchlist_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        return {
            "success": True,
            "message": "Watchlist deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SYMBOL SEARCH ENDPOINTS ====================

@router.get("/symbols/search")
async def search_symbols(
    query: str = Query(..., description="Search query"),
    exchange: str = Query("NSE", description="Exchange to search"),
    limit: int = Query(20, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for symbols"""
    try:
        results = await watchlist_service.search_symbols(
            query=query,
            exchange=exchange,
            limit=limit
        )
        
        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat(),
            "message": f"Found {len(results)} symbols matching '{query}'"
        }
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols/popular")
async def get_popular_symbols(
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get popular/most traded symbols"""
    try:
        results = await watchlist_service.get_popular_symbols(
            exchange=exchange,
            limit=limit
        )
        
        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(results)} popular symbols"
        }
    except Exception as e:
        logger.error(f"Error getting popular symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REAL-TIME WEBSOCKET ENDPOINTS ====================

@router.websocket("/chart-updates/{symbol}")
async def chart_updates_websocket(
    websocket: WebSocket,
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """WebSocket for real-time chart updates"""
    await websocket.accept()
    
    try:
        while True:
            # Get latest data for symbol
            data = await chart_service.get_latest_data(symbol)
            
            # Send to client
            await websocket.send_json({
                "type": "price_update",
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            
            # Wait before next update
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        await websocket.close(code=1011, reason=str(e))

@router.websocket("/multi-chart-updates")
async def multi_chart_updates_websocket(
    websocket: WebSocket,
    current_user: dict = Depends(get_current_user)
):
    """WebSocket for multiple chart updates"""
    await websocket.accept()
    
    try:
        while True:
            # Get subscription request
            data = await websocket.receive_json()
            
            if data.get("type") == "subscribe":
                symbols = data.get("symbols", [])
                
                # Get latest data for all symbols
                updates = {}
                for symbol in symbols:
                    symbol_data = await chart_service.get_latest_data(symbol)
                    updates[symbol] = symbol_data
                
                # Send updates
                await websocket.send_json({
                    "type": "multi_update",
                    "data": updates,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info("Multi-chart WebSocket disconnected")
    except Exception as e:
        logger.error(f"Multi-chart WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))

# ==================== CHART LAYOUT ENDPOINTS ====================

@router.get("/layouts")
async def get_chart_layouts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chart layouts"""
    try:
        layouts = await chart_service.get_user_layouts(current_user["id"])
        
        return {
            "success": True,
            "data": layouts,
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(layouts)} chart layouts"
        }
    except Exception as e:
        logger.error(f"Error getting chart layouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/layouts")
async def save_chart_layout(
    layout_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save chart layout"""
    try:
        layout_id = await chart_service.save_layout(
            user_id=current_user["id"],
            layout_data=layout_data
        )
        
        return {
            "success": True,
            "data": {"layout_id": layout_id},
            "timestamp": datetime.now().isoformat(),
            "message": "Chart layout saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving chart layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HEALTH CHECK ENDPOINT ====================

@router.get("/health")
async def charting_health_check():
    """Health check for charting system"""
    try:
        # Check if all services are available
        services_status = {
            "chart_service": chart_service.is_available(),
            "indicators_service": indicators_service.is_available(),
            "drawing_service": drawing_service.is_available(),
            "alert_service": alert_service.is_available(),
            "watchlist_service": watchlist_service.is_available()
        }
        
        all_healthy = all(services_status.values())
        
        return {
            "success": all_healthy,
            "data": {
                "status": "healthy" if all_healthy else "degraded",
                "services": services_status,
                "timestamp": datetime.now().isoformat()
            },
            "message": "Charting system health check completed"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            "message": "Charting system health check failed"
        }
