"""
Backtesting System API Routes
Test historical performance of trading strategies and signals
"""

from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import statistics

from services.strategy_optimizer import strategy_optimizer

logger = logging.getLogger(__name__)
router = APIRouter()

class BacktestRequest(BaseModel):
    """Request for backtesting"""
    symbol: str = Field(..., description="Stock symbol")
    strategy_type: str = Field(..., description="Strategy: 'sd_zones', 'sr_levels', 'structure_breaks'")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    entry_threshold: float = Field(0.5, description="Entry threshold %")
    stop_loss: float = Field(2.0, description="Stop loss %")
    take_profit: float = Field(4.0, description="Take profit %")

class BacktestResponse(BaseModel):
    """Backtesting results"""
    success: bool
    symbol: str
    strategy: str
    metrics: Optional[Dict] = None
    trades: Optional[List[Dict]] = None
    equity_curve: Optional[List[Dict]] = None

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "service": "backtesting",
        "status": "healthy",
        "features": [
            "zone_success_rate",
            "pattern_win_rate",
            "equity_curve",
            "performance_metrics"
        ]
    }

@router.post("/run")
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """
    Run backtest on historical data
    
    Tests the profitability of a strategy using historical price data
    """
    try:
        logger.info(f"🧪 Running backtest for {request.symbol} - {request.strategy_type}")
        
        # Import required services
        from services.backtesting_engine import BacktestingEngine
        
        engine = BacktestingEngine()
        
        # Run backtest based on strategy type
        if request.strategy_type == "sd_zones":
            results = await engine.backtest_supply_demand_zones(
                symbol=request.symbol,
                entry_threshold=request.entry_threshold,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit
            )
        elif request.strategy_type == "sr_levels":
            results = await engine.backtest_support_resistance(
                symbol=request.symbol,
                entry_threshold=request.entry_threshold,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit
            )
        elif request.strategy_type == "structure_breaks":
            results = await engine.backtest_structure_breaks(
                symbol=request.symbol,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown strategy type: {request.strategy_type}"
            )
        
        return BacktestResponse(
            success=True,
            symbol=request.symbol,
            strategy=request.strategy_type,
            metrics=results.get('metrics'),
            trades=results.get('trades', []),
            equity_curve=results.get('equity_curve', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zone-success-rate")
async def calculate_zone_success_rate(
    symbol: str = Body(...),
    timeframe: str = Body("1d"),
    lookback_days: int = Body(90)
) -> Dict:
    """
    Calculate success rate for S&D zones
    
    Returns:
    - Demand zone bounce rate
    - Supply zone rejection rate
    - Average hold time
    - Average bounce/rejection percentage
    """
    try:
        logger.info(f"📊 Calculating zone success rate for {symbol}")
        
        from services.backtesting_engine import BacktestingEngine
        
        engine = BacktestingEngine()
        results = await engine.analyze_zone_success_rate(
            symbol=symbol,
            timeframe=timeframe,
            lookback_days=lookback_days
        )
        
        return {
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating zone success rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pattern-winrate")
async def calculate_pattern_winrate(
    symbol: str = Body(...),
    pattern_type: str = Body(...),  # e.g., "HH_HL_continuation"
    lookback_days: int = Body(90)
) -> Dict:
    """Calculate win rate for specific swing point patterns"""
    try:
        logger.info(f"📊 Calculating pattern win rate for {symbol} - {pattern_type}")
        
        from services.backtesting_engine import BacktestingEngine
        
        engine = BacktestingEngine()
        results = await engine.analyze_pattern_winrate(
            symbol=symbol,
            pattern_type=pattern_type,
            lookback_days=lookback_days
        )
        
        return {
            'success': True,
            'symbol': symbol,
            'pattern': pattern_type,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating pattern win rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_strategy(
    symbol: str = Query(..., description="Stock symbol"),
    strategy_type: str = Query(..., description="Strategy type"),
    param_ranges: Dict = Body(..., description="Parameter ranges"),
    objective: str = Query("sharpe_ratio", description="Optimization objective")
):
    """Optimize strategy parameters"""
    try:
        result = await strategy_optimizer.grid_search_optimization(
            symbol=symbol,
            strategy_type=strategy_type,
            param_ranges=param_ranges,
            objective=objective
        )
        return result
    except Exception as e:
        logger.error(f"Error optimizing strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/walk-forward")
async def walk_forward_analysis(
    symbol: str = Query(..., description="Stock symbol"),
    strategy_type: str = Query(..., description="Strategy type"),
    optimization_period: int = Query(60, description="Optimization period in days"),
    test_period: int = Query(30, description="Test period in days")
):
    """Walk-forward analysis"""
    try:
        result = await strategy_optimizer.walk_forward_analysis(
            symbol=symbol,
            strategy_type=strategy_type,
            optimization_period=optimization_period,
            test_period=test_period
        )
        return result
    except Exception as e:
        logger.error(f"Error in walk-forward analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def get_available_strategies():
    """Get list of available backtesting strategies"""
    return {
        'success': True,
        'strategies': [
            {
                'id': 'sd_zones',
                'name': 'Supply & Demand Zones',
                'description': 'Test zone bounces and rejections',
                'parameters': ['entry_threshold', 'stop_loss', 'take_profit']
            },
            {
                'id': 'sr_levels',
                'name': 'Support & Resistance Levels',
                'description': 'Test level bounces and breaks',
                'parameters': ['entry_threshold', 'stop_loss', 'take_profit']
            },
            {
                'id': 'structure_breaks',
                'name': 'Structure Breaks (BOS/CHoCH)',
                'description': 'Trade on structure confirmations',
                'parameters': ['stop_loss', 'take_profit']
            }
        ]
    }

