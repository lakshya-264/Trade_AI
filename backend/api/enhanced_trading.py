"""
Enhanced Trading API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from core.database import get_db
from services.enhanced_trading_service import enhanced_trading_service
from core.auth_dependencies import get_current_active_user
from core.database_unified import User

router = APIRouter(prefix="/api/v1/enhanced-trading", tags=["Enhanced Trading"])

@router.post("/execute")
async def execute_trade_with_portfolio(
    trade_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute trade and automatically update portfolio"""
    try:
        result = await enhanced_trading_service.execute_trade_with_portfolio_update(
            symbol=trade_data['symbol'],
            action=trade_data['action'],  # BUY or SELL
            quantity=trade_data['quantity'],
            price=trade_data['price'],
            user_id=current_user.id,
            db=db,
            strategy=trade_data.get('strategy', 'MANUAL'),
            signal_confidence=trade_data.get('signal_confidence', 0.5)
        )
        
        return {
            'success': True,
            'data': result,
            'message': 'Trade executed and portfolio updated successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

@router.post("/close/{execution_id}")
async def close_trade_with_portfolio(
    execution_id: int,
    close_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Close trade and update portfolio"""
    try:
        result = await enhanced_trading_service.close_trade_with_portfolio_update(
            execution_id=execution_id,
            exit_price=close_data['exit_price'],
            user_id=current_user.id,
            db=db,
            exit_reason=close_data.get('exit_reason', 'MANUAL')
        )
        
        return {
            'success': True,
            'data': result,
            'message': 'Trade closed and portfolio updated successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade closure failed: {str(e)}")

@router.get("/unified-performance")
async def get_unified_performance(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get unified trading and portfolio performance"""
    try:
        result = await enhanced_trading_service.get_unified_performance_summary(
            user_id=current_user.id,
            days=days,
            db=db
        )
        
        return {
            'success': True,
            'data': result,
            'message': f'Unified performance for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unified performance: {str(e)}")

@router.get("/portfolio-impact")
async def get_portfolio_impact(
    trade_value: float = Query(..., description="Value of proposed trade"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate impact of proposed trade on portfolio"""
    try:
        impact = await enhanced_trading_service._calculate_portfolio_impact(
            user_id=current_user.id,
            trade_value=trade_value,
            db=db
        )
        
        return {
            'success': True,
            'data': impact,
            'message': 'Portfolio impact calculated successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate portfolio impact: {str(e)}")
