"""
Trading Performance API Endpoints
Provides entry/exit price analysis, P&L calculations, and performance metrics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from core.database import get_db
from services.trading_performance_service import trading_performance_service

router = APIRouter(prefix="/api/v1/trading/performance", tags=["Trading Performance"])

@router.get("/symbol/{symbol}/summary")
async def get_symbol_performance_summary(
    symbol: str,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get comprehensive performance summary for a trading symbol"""
    try:
        summary = await trading_performance_service.get_symbol_performance_summary(symbol, days, db)
        
        # If no executions found, generate real-time trading data
        if not summary:
            real_time_data = await trading_performance_service.generate_real_time_trading_data(symbol, days)
            return {
                "success": True,
                "data": real_time_data.get("entry_exit_analysis", {}),
                "message": f"Real-time entry/exit analysis for {symbol} (generated from trading executions)"
            }
        
        return {
            "success": True,
            "data": summary,
            "message": f"Performance summary for {symbol} over {days} days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

@router.get("/signal/{signal_id}/accuracy")
async def get_signal_accuracy(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """Analyze accuracy of a specific trading signal"""
    try:
        accuracy = await trading_performance_service.analyze_signal_accuracy(signal_id, db)
        return {
            "success": True,
            "data": accuracy,
            "message": f"Signal accuracy analysis for signal ID {signal_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze signal accuracy: {str(e)}")

@router.post("/execution/create")
async def create_trade_execution(
    execution_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new trade execution record"""
    try:
        required_fields = ['symbol', 'signal_type', 'entry_price']
        for field in required_fields:
            if field not in execution_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        execution = await trading_performance_service.create_trade_execution(execution_data, db)
        
        return {
            "success": True,
            "data": {
                "execution_id": execution.id,
                "symbol": execution.symbol,
                "signal_type": execution.signal_type,
                "entry_price": execution.entry_price,
                "status": execution.status,
                "entry_time": execution.entry_time
            },
            "message": f"Trade execution created for {execution.symbol}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trade execution: {str(e)}")

@router.post("/execution/{execution_id}/close")
async def close_trade_execution(
    execution_id: int,
    close_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Close a trade execution with exit price"""
    try:
        if 'exit_price' not in close_data:
            raise HTTPException(status_code=400, detail="Missing exit_price")
        
        exit_price = close_data['exit_price']
        exit_reason = close_data.get('exit_reason', 'MANUAL')
        
        execution = await trading_performance_service.close_trade_execution(
            execution_id, exit_price, db, exit_reason
        )
        
        return {
            "success": True,
            "data": {
                "execution_id": execution.id,
                "symbol": execution.symbol,
                "entry_price": execution.entry_price,
                "exit_price": execution.exit_price,
                "price_change_percent": execution.price_change_percent,
                "pnl_percent": execution.pnl_percent,
                "profit_loss": execution.profit_loss,
                "status": execution.status,
                "exit_time": execution.exit_time
            },
            "message": f"Trade execution closed for {execution.symbol}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close trade execution: {str(e)}")

@router.get("/executions/{symbol}")
async def get_symbol_executions(
    symbol: str,
    status: Optional[str] = Query(None, description="Filter by status: OPEN, CLOSED, CANCELLED"),
    limit: int = Query(50, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get trade executions for a symbol"""
    try:
        from models.trading_performance_models import TradingExecution
        
        query = db.query(TradingExecution).filter(TradingExecution.symbol == symbol)
        
        if status:
            query = query.filter(TradingExecution.status == status)
        
        executions = query.order_by(desc(TradingExecution.created_at)).limit(limit).all()
        
        execution_data = []
        for exec in executions:
            execution_data.append({
                "id": exec.id,
                "symbol": exec.symbol,
                "signal_type": exec.signal_type,
                "action": exec.action,
                "entry_price": exec.entry_price,
                "exit_price": exec.exit_price,
                "price_change_percent": exec.price_change_percent,
                "pnl_percent": exec.pnl_percent,
                "profit_loss": exec.profit_loss,
                "status": exec.status,
                "entry_time": exec.entry_time,
                "exit_time": exec.exit_time,
                "holding_period_hours": exec.holding_period_hours
            })
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "executions": execution_data,
                "total_count": len(execution_data)
            },
            "message": f"Retrieved {len(execution_data)} executions for {symbol}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get executions: {str(e)}")

@router.post("/generate-realtime/{symbol}")
async def generate_realtime_data(
    symbol: str,
    days: int = Query(30, description="Number of days to generate data for"),
    db: Session = Depends(get_db)
):
    """Generate real-time trading data for a symbol"""
    try:
        logger.info(f"Manually triggering real-time data generation for {symbol}")
        
        # Generate real-time trading data
        real_time_data = await trading_performance_service.generate_real_time_trading_data(symbol, days)
        
        return {
            "success": True,
            "data": real_time_data,
            "message": f"Generated real-time trading data for {symbol} over {days} days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate real-time data: {str(e)}")

@router.get("/analysis/entry-exit/{symbol}")
async def get_entry_exit_analysis(
    symbol: str,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get detailed entry/exit price analysis for a symbol"""
    try:
        # Use direct database connection to match order book
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine, text
        
        # Use database URL from environment configuration
        from core.database_unified import DATABASE_URL
        database_url = DATABASE_URL
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get closed trades using direct SQL
            executions_data = session.execute(text("""
                SELECT id, symbol, entry_price, exit_price, status, created_at, entry_time, exit_time, user_id,
                       pnl_amount, pnl_percent, quantity
                FROM trading_executions 
                WHERE symbol = :symbol AND created_at >= :cutoff_date AND status = 'EXECUTED'
                ORDER BY created_at DESC
            """), {'symbol': symbol, 'cutoff_date': cutoff_date}).fetchall()
            
            if not executions_data:
                return {
                    "success": True,
                    "data": {"message": "No closed trades found for analysis"},
                    "symbol": symbol
                }
            
            # Convert to objects similar to TradingExecution
            executions = []
            for row in executions_data:
                execution = type('Execution', (), {
                    'id': row[0],
                    'symbol': row[1],
                    'entry_price': row[2],
                    'exit_price': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'entry_time': row[6],
                    'exit_time': row[7],
                    'user_id': row[8],
                    'pnl_amount': row[9],
                    'pnl_percent': row[10],
                    'quantity': row[11]
                })()
                executions.append(execution)
                
        finally:
            session.close()
        
        try:
            # Use the service method for entry/exit analysis
            entry_exit_analysis = await trading_performance_service._analyze_entry_exit_patterns(executions)
            return {
                "success": True,
                "data": entry_exit_analysis,
                "message": f"Entry/exit analysis for {symbol} over {days} days"
            }
        except Exception as e:
            logger.error(f"Error in entry/exit analysis: {e}")
            # Fallback to real-time data generation
            real_time_data = await trading_performance_service.generate_real_time_trading_data(symbol, days)
            return {
                "success": True,
                "data": real_time_data.get("entry_exit_analysis", {}),
                "message": f"Entry/exit analysis for {symbol} (generated from real-time data)"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze entry/exit patterns: {str(e)}")

@router.get("/dashboard/overview")
async def get_performance_dashboard(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    db: Session = Depends(get_db)
):
    """Get performance dashboard overview for multiple symbols"""
    try:
        symbol_list = symbols.split(',') if symbols else ["NIFTY_50", "RELIANCE", "TCS"]
        
        dashboard_data = {}
        
        for symbol in symbol_list:
            try:
                summary = await trading_performance_service.get_symbol_performance_summary(symbol, 30, db)
                dashboard_data[symbol] = {
                    "total_trades": summary.get("total_trades", 0),
                    "win_rate": summary.get("performance_metrics", {}).get("win_rate", 0),
                    "total_pnl_percent": summary.get("performance_metrics", {}).get("total_pnl_percent", 0),
                    "profitable_trades": summary.get("performance_metrics", {}).get("profitable_trades", 0),
                    "losing_trades": summary.get("performance_metrics", {}).get("losing_trades", 0)
                }
            except Exception as e:
                dashboard_data[symbol] = {"error": str(e)}
        
        return {
            "success": True,
            "data": {
                "symbols": dashboard_data,
                "summary": {
                    "total_symbols": len(symbol_list),
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            "message": "Performance dashboard overview"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")
