"""
Simple Portfolio API - Direct database access for tester2 orders
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from core.database import get_db
from core.database_unified import User, PortfolioMetadata, Portfolio
from models.trading_performance_models import TradingExecution
from core.auth_dependencies import get_current_active_user

router = APIRouter(prefix="/api/v1/simple-portfolio", tags=["Simple Portfolio"])

@router.get("/holdings")
async def get_portfolio_holdings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get portfolio holdings directly from database"""
    try:
        # Get portfolio metadata
        portfolio_metadata = db.query(PortfolioMetadata).filter(
            PortfolioMetadata.user_id == current_user.id
        ).first()
        
        if not portfolio_metadata:
            return {
                'success': True,
                'data': {
                    'holdings': {},
                    'total_value': 0,
                    'holding_count': 0,
                    'portfolio_metadata': None
                },
                'message': 'No portfolio found'
            }
        
        # Get portfolio holdings
        holdings = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).all()
        
        # Format holdings for frontend
        formatted_holdings = {}
        total_value = 0
        
        for holding in holdings:
            formatted_holdings[holding.symbol] = {
                'quantity': holding.quantity,
                'avg_price': holding.average_price,
                'current_price': holding.current_price,
                'total_value': holding.quantity * holding.current_price,
                'cost_basis': holding.quantity * holding.average_price,
                'unrealized_pnl': (holding.current_price - holding.average_price) * holding.quantity,
                'unrealized_pnl_percent': ((holding.current_price - holding.average_price) / holding.average_price * 100) if holding.average_price > 0 else 0,
                'status': 'ACTIVE',
                'days_held': (datetime.utcnow() - holding.created_at).days if holding.created_at else 0,
                'created_at': holding.created_at.isoformat() if holding.created_at else None,
                'updated_at': holding.updated_at.isoformat() if holding.updated_at else None
            }
            total_value += formatted_holdings[holding.symbol]['total_value']
        
        return {
            'success': True,
            'data': {
                'holdings': formatted_holdings,
                'total_value': total_value,
                'holding_count': len(holdings),
                'portfolio_metadata': {
                    'name': portfolio_metadata.name,
                    'description': portfolio_metadata.description,
                    'total_value': portfolio_metadata.total_value,
                    'created_at': portfolio_metadata.created_at.isoformat(),
                    'updated_at': portfolio_metadata.updated_at.isoformat()
                }
            },
            'message': 'Portfolio holdings retrieved successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio holdings: {str(e)}")

@router.get("/trades")
async def get_recent_trades(
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, description="Number of days to fetch"),
    db: Session = Depends(get_db)
):
    """Get recent trading executions"""
    try:
        # Get recent executions
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        executions = db.query(TradingExecution).filter(
            TradingExecution.created_at >= cutoff_date
        ).order_by(TradingExecution.created_at.desc()).all()
        
        # Format executions
        formatted_executions = []
        for exec in executions:
            formatted_executions.append({
                'id': exec.id,
                'symbol': exec.symbol,
                'signal_type': exec.signal_type,
                'action': exec.action,
                'quantity': exec.quantity,
                'entry_price': exec.entry_price,
                'entry_value': exec.entry_value,
                'exit_price': exec.exit_price,
                'exit_value': exec.exit_value,
                'pnl_amount': exec.pnl_amount,
                'pnl_percent': exec.pnl_percent,
                'status': exec.status,
                'entry_time': exec.entry_time.isoformat() if exec.entry_time else None,
                'exit_time': exec.exit_time.isoformat() if exec.exit_time else None,
                'holding_period_hours': exec.holding_period_hours,
                'created_at': exec.created_at.isoformat() if exec.created_at else None,
                'updated_at': exec.updated_at.isoformat() if exec.updated_at else None,
                'notes': exec.notes
            })
        
        return {
            'success': True,
            'data': {
                'executions': formatted_executions,
                'total_executions': len(formatted_executions),
                'period_days': days
            },
            'message': f'Recent trades for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent trades: {str(e)}")

@router.get("/dashboard")
async def get_portfolio_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete portfolio dashboard"""
    try:
        # Get portfolio metadata
        portfolio_metadata = db.query(PortfolioMetadata).filter(
            PortfolioMetadata.user_id == current_user.id
        ).first()
        
        # Get holdings
        holdings = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).all()
        
        # Get recent trades
        recent_trades = db.query(TradingExecution).filter(
            TradingExecution.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(TradingExecution.created_at.desc()).limit(10).all()
        
        # Calculate metrics
        total_value = sum(h.quantity * h.current_price for h in holdings)
        total_cost = sum(h.quantity * h.average_price for h in holdings)
        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # Format holdings
        formatted_holdings = {}
        for holding in holdings:
            formatted_holdings[holding.symbol] = {
                'quantity': holding.quantity,
                'avg_price': holding.average_price,
                'current_price': holding.current_price,
                'total_value': holding.quantity * holding.current_price,
                'unrealized_pnl': (holding.current_price - holding.average_price) * holding.quantity,
                'unrealized_pnl_percent': ((holding.current_price - holding.average_price) / holding.average_price * 100) if holding.average_price > 0 else 0
            }
        
        # Format recent trades
        formatted_trades = []
        for trade in recent_trades:
            formatted_trades.append({
                'symbol': trade.symbol,
                'signal_type': trade.signal_type,
                'quantity': trade.quantity,
                'entry_price': trade.entry_price,
                'entry_value': trade.entry_value,
                'pnl_amount': trade.pnl_amount,
                'pnl_percent': trade.pnl_percent,
                'status': trade.status,
                'created_at': trade.created_at.isoformat()
            })
        
        return {
            'success': True,
            'data': {
                'holdings': formatted_holdings,
                'total_value': total_value,
                'holding_count': len(holdings),
                'total_cost': total_cost,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'recent_trades': formatted_trades,
                'portfolio_metadata': {
                    'name': portfolio_metadata.name if portfolio_metadata else 'Default Portfolio',
                    'total_value': portfolio_metadata.total_value if portfolio_metadata else total_value,
                    'created_at': portfolio_metadata.created_at.isoformat() if portfolio_metadata else None
                } if portfolio_metadata else None
            },
            'message': 'Portfolio dashboard data'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")

@router.get("/check-data")
async def check_database_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check what data exists in database for current user"""
    try:
        # Check user
        user_info = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        }
        
        # Check portfolio metadata
        portfolio_metadata = db.query(PortfolioMetadata).filter(
            PortfolioMetadata.user_id == current_user.id
        ).first()
        
        portfolio_info = None
        if portfolio_metadata:
            portfolio_info = {
                'id': portfolio_metadata.id,
                'name': portfolio_metadata.name,
                'total_value': portfolio_metadata.total_value,
                'created_at': portfolio_metadata.created_at.isoformat()
            }
        
        # Check holdings
        holdings = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).all()
        
        holdings_info = []
        for holding in holdings:
            holdings_info.append({
                'symbol': holding.symbol,
                'quantity': holding.quantity,
                'average_price': holding.average_price,
                'current_price': holding.current_price,
                'pnl': holding.pnl,
                'created_at': holding.created_at.isoformat()
            })
        
        # Check executions
        executions = db.query(TradingExecution).filter(
            TradingExecution.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        executions_info = []
        for exec in executions:
            executions_info.append({
                'symbol': exec.symbol,
                'signal_type': exec.signal_type,
                'quantity': exec.quantity,
                'entry_price': exec.entry_price,
                'status': exec.status,
                'created_at': exec.created_at.isoformat()
            })
        
        return {
            'success': True,
            'data': {
                'user': user_info,
                'portfolio_metadata': portfolio_info,
                'holdings': holdings_info,
                'executions': executions_info,
                'summary': {
                    'portfolio_exists': portfolio_metadata is not None,
                    'holdings_count': len(holdings_info),
                    'executions_count': len(executions_info),
                    'total_portfolio_value': sum(h['quantity'] * h['current_price'] for h in holdings_info)
                }
            },
            'message': 'Database data check completed'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check database data: {str(e)}")
