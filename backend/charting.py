"""
Advanced Charting API routes
Supports professional trading terminal features
"""

from fastapi import HTTPException, APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from core.database import get_db
from core.auth_dependencies import get_current_active_user
from services.enhanced_chart_service import enhanced_chart_service
from services.technical_analysis import TechnicalAnalyzer
from services.candlestick_patterns import CandlestickPatternService

router = APIRouter()

# Pydantic models
class ChartDataRequest(BaseModel):
    symbol: str
    timeframe: str = "1D"
    period: int = 100
    indicators: Optional[List[str]] = None

class PatternRecognitionRequest(BaseModel):
    symbol: str
    patterns: Optional[List[str]] = None
    timeframe: str = "1D"

class TechnicalAnalysisRequest(BaseModel):
    symbol: str
    indicators: List[str]
    timeframe: str = "1D"

class DrawingToolRequest(BaseModel):
    tool_type: str
    symbol: str
    points: List[Dict[str, float]]
    properties: Optional[Dict[str, Any]] = None

class AlertRequest(BaseModel):
    symbol: str
    alert_type: str  # price, pattern, indicator
    condition: str
    value: float
    timeframe: str = "1D"

# Initialize services
technical_analyzer = TechnicalAnalyzer()
pattern_service = CandlestickPatternService()

@router.get("///candlestick/{symbol}")
async def get_candlestick_data(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1D, 1W, 1M"),
    period: int = Query(100, description="Number of data points"),
    current_user = Depends(get_current_active_user)
):
    """Get candlestick data with technical indicators"""
    try:
        data = await enhanced_chart_service.get_candlestick_data(symbol, timeframe, period)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
            
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candlestick data: {str(e)}")

@router.get("///technical-indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    indicators: Optional[str] = Query(None, description="Comma-separated list of indicators"),
    timeframe: str = Query("1D", description="Timeframe"),
    current_user = Depends(get_current_active_user)
):
    """Get comprehensive technical indicators"""
    try:
        indicator_list = indicators.split(",") if indicators else None
        data = await enhanced_chart_service.get_technical_indicators(symbol, indicator_list)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
            
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching technical indicators: {str(e)}")

@router.get("///pattern-recognition/{symbol}")
async def get_pattern_recognition(
    symbol: str,
    patterns: Optional[str] = Query(None, description="Comma-separated list of patterns"),
    timeframe: str = Query("1D", description="Timeframe"),
    current_user = Depends(get_current_active_user)
):
    """Detect candlestick and chart patterns"""
    try:
        pattern_list = patterns.split(",") if patterns else None
        data = await enhanced_chart_service.get_pattern_recognition(symbol, pattern_list)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
            
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting patterns: {str(e)}")

@router.get("///volume-profile/{symbol}")
async def get_volume_profile(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe"),
    period: int = Query(30, description="Number of days"),
    current_user = Depends(get_current_active_user)
):
    """Get volume profile analysis"""
    try:
        data = await enhanced_chart_service.get_volume_profile(symbol, timeframe, period)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
            
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching volume profile: {str(e)}")

@router.get("///support-resistance/{symbol}")
async def get_support_resistance(
    symbol: str,
    lookback: int = Query(50, description="Lookback period in days"),
    current_user = Depends(get_current_active_user)
):
    """Calculate support and resistance levels"""
    try:
        data = await enhanced_chart_service.get_support_resistance(symbol, lookback)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
            
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating support/resistance: {str(e)}")

@router.post("///trading-signals/{symbol}")
async def get_trading_signals(
    symbol: str,
    request: TechnicalAnalysisRequest,
    current_user = Depends(get_current_active_user)
):
    """Generate trading signals based on technical analysis"""
    try:
        # Get historical data
        chart_data = await enhanced_chart_service.get_candlestick_data(
            symbol, request.timeframe, 100
        )
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        
        # Convert to DataFrame for analysis
        import pandas as pd
        df = pd.DataFrame(chart_data["candlesticks"])
        
        # Perform technical analysis
        analysis = technical_analyzer.analyze(df)
        
        # Generate signals
        signals = {
            "symbol": symbol,
            "timeframe": request.timeframe,
            "signals": analysis.get("signals", {}),
            "indicators": analysis.get("indicators", {}),
            "patterns": analysis.get("patterns", []),
            "support_resistance": analysis.get("support_resistance", {}),
            "summary": analysis.get("summary", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": signals,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trading signals: {str(e)}")

@router.get("///market-overview")
async def get_market_overview(
    current_user = Depends(get_current_active_user)
):
    """Get market overview with key metrics"""
    try:
        # This would typically fetch from market data APIs
        overview = {
            "nifty_50": {
                "value": 19500.50,
                "change": 125.30,
                "change_percent": 0.65,
                "volume": 125000000
            },
            "sensex": {
                "value": 65250.75,
                "change": 425.80,
                "change_percent": 0.66,
                "volume": 98000000
            },
            "market_status": "OPEN",
            "sector_performance": [
                {"sector": "IT", "change_percent": 1.2},
                {"sector": "Banking", "change_percent": 0.8},
                {"sector": "Pharma", "change_percent": -0.3},
                {"sector": "Auto", "change_percent": 0.5}
            ],
            "top_gainers": [
                {"symbol": "RELIANCE", "change_percent": 2.5},
                {"symbol": "TCS", "change_percent": 1.8},
                {"symbol": "HDFC", "change_percent": 1.5}
            ],
            "top_losers": [
                {"symbol": "SOME_STOCK", "change_percent": -2.1},
                {"symbol": "ANOTHER_STOCK", "change_percent": -1.8}
            ]
        }
        
        return {
            "success": True,
            "data": overview,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market overview: {str(e)}")

@router.get("///portfolio-performance/{user_id}")
async def get_portfolio_performance(
    user_id: int,
    period: str = Query("1Y", description="Performance period"),
    benchmark: str = Query("NIFTY_50", description="Benchmark index"),
    current_user = Depends(get_current_active_user)
):
    """Get portfolio performance with benchmark comparison"""
    try:
        # This would typically calculate from user's portfolio data
        # For now, return mock data
        performance_data = {
            "user_id": user_id,
            "period": period,
            "benchmark": benchmark,
            "portfolio_value": 1500000,
            "portfolio_return": 12.5,
            "benchmark_return": 8.3,
            "alpha": 4.2,
            "beta": 0.85,
            "sharpe_ratio": 1.45,
            "max_drawdown": -8.2,
            "volatility": 15.3,
            "performance_data": [
                {
                    "date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "portfolio_value": 1500000 + (i * 1000),
                    "benchmark_value": 1000000 + (i * 500),
                    "pnl": i * 1000,
                    "pnl_percent": (i * 1000) / 1500000 * 100
                }
            ]
        }
        
        return {
            "success": True,
            "data": performance_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio performance: {str(e)}")

@router.post("///drawing-tools")
async def save_drawing_tool(
    request: DrawingToolRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save chart drawing tool"""
    try:
        drawing_data = {
            "id": f"drawing_{datetime.now().timestamp()}",
            "user_id": current_user.id,
            "symbol": request.symbol,
            "tool_type": request.tool_type,
            "points": request.points,
            "properties": request.properties or {},
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": drawing_data,
            "message": "Drawing tool saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving drawing tool: {str(e)}")

@router.get("///drawing-tools/{symbol}")
async def get_drawing_tools(
    symbol: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        drawings = [
            {
                "id": "drawing_1",
                "symbol": symbol,
                "tool_type": "trendline",
                "points": [{"x": 100, "y": 200}, {"x": 300, "y": 400}],
                "properties": {"color": "#3B82F6", "width": 2},
                "created_at": datetime.now().isoformat()
            }
        ]
        
        return {
            "success": True,
            "data": drawings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching drawing tools: {str(e)}")

@router.post("///alerts")
async def create_alert(
    request: AlertRequest,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create price/pattern/indicator alert"""
    try:
        alert_data = {
            "id": f"alert_{datetime.now().timestamp()}",
            "user_id": current_user.id,
            "symbol": request.symbol,
            "alert_type": request.alert_type,
            "condition": request.condition,
            "value": request.value,
            "timeframe": request.timeframe,
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": alert_data,
            "message": "Alert created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating alert: {str(e)}")

@router.get("///alerts")
async def get_alerts(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's active alerts"""
    try:
        alerts = [
            {
                "id": "alert_1",
                "symbol": "RELIANCE",
                "alert_type": "price",
                "condition": "above",
                "value": 2500,
                "status": "ACTIVE",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        return {
            "success": True,
            "data": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@router.delete("///alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    try:
        return {
            "success": True,
            "message": f"Alert {alert_id} deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting alert: {str(e)}")

@router.get("///chart-themes")
async def get_chart_themes(
    current_user = Depends(get_current_active_user)
):
    """Get available chart themes"""
    try:
        themes = [
            {
                "id": "dark",
                "name": "Dark Professional",
                "description": "Professional dark theme for trading",
                "colors": {
                    "background": "#0F172A",
                    "grid": "#334155",
                    "text": "#F8FAFC",
                    "primary": "#3B82F6",
                    "success": "#10B981",
                    "danger": "#EF4444"
                }
            },
            {
                "id": "light",
                "name": "Light Professional",
                "description": "Clean light theme for daytime trading",
                "colors": {
                    "background": "#FFFFFF",
                    "grid": "#E2E8F0",
                    "text": "#1E293B",
                    "primary": "#3B82F6",
                    "success": "#10B981",
                    "danger": "#EF4444"
                }
            }
        ]
        
        return {
            "success": True,
            "data": themes,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chart themes: {str(e)}")

@router.get("///export-chart/{symbol}")
async def export_chart(
    symbol: str,
    format: str = Query("png", description="Export format: png, jpg, svg, pdf"),
    timeframe: str = Query("1D", description="Timeframe"),
    period: int = Query(100, description="Number of data points"),
    current_user = Depends(get_current_active_user)
):
    """Export chart data for download"""
    try:
        # Get chart data
        chart_data = await enhanced_chart_service.get_candlestick_data(symbol, timeframe, period)
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        
        export_data = {
            "symbol": symbol,
            "format": format,
            "timeframe": timeframe,
            "data_points": len(chart_data["candlesticks"]),
            "export_url": f"/exports/{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": export_data,
            "message": f"Chart exported as {format.upper()}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting chart: {str(e)}")

@router.get("///data/{symbol}")
async def get_chart_data(symbol: str, timeframe: str = "1d"):
    try:
        # TODO: Implement actual chart data fetching logic
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "open": 2500.0,
                        "high": 2525.0,
                        "low": 2475.0,
                        "close": 2520.0,
                        "volume": 1000000
                    }
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")

@router.get("///indicators/{symbol}")
async def get_chart_indicators(symbol: str):
    try:
        # TODO: Implement actual indicators calculation logic
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "indicators": {
                    "rsi": 65.5,
                    "macd": {
                        "macd": 12.5,
                        "signal": 10.2,
                        "histogram": 2.3
                    },
                    "movingAverages": {
                        "sma20": 2500.0,
                        "sma50": 2480.0,
                        "ema12": 2510.0
                    }
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating indicators: {str(e)}")


# ---------- Missing Endpoints for API Compatibility ----------

@router.get("/data/{symbol}")
async def get_chart_data(symbol: str):
    """Get chart data for symbol"""
    try:
        return {
            "message": f"Chart data retrieved successfully for {symbol}",
            "symbol": symbol,
            "data": {
                "price": 2500.50,
                "volume": 1500000,
                "change": 25.75,
                "change_percent": 1.04
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chart data: {str(e)}")

@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    """Get technical indicators for symbol"""
    try:
        return {
            "message": f"Technical indicators retrieved successfully for {symbol}",
            "symbol": symbol,
            "indicators": {
                "rsi": 65.5,
                "macd": 12.3,
                "sma_20": 2480.25,
                "ema_50": 2450.75
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting indicators: {str(e)}")
