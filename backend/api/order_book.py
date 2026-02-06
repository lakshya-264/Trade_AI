"""
ORDER BOOK API ENDPOINT - Show executed orders for tester2
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from datetime import datetime, timedelta

from core.database import get_db
from core.database_unified import User
from models.trading_performance_models import TradingExecution
from core.auth_dependencies import get_current_active_user

router = APIRouter(prefix="/api/v1/order-book", tags=["Order Book"])

@router.get("/executed-orders")
async def get_executed_orders(
    current_user: User = Depends(get_current_active_user),
    days: int = 30
):
    """Get all executed orders for the current user"""
    try:
        # Use direct database connection to ensure correct database
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
        database_url = "sqlite:///./trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        print(f"🔍 ORDER BOOK API: Using database: {database_url}")
        
        # Get user ID from the dict or object
        if isinstance(current_user, dict):
            user_id = current_user.get('id')
        else:
            user_id = current_user.id
        
        print(f"🔍 Fetching orders for user_id: {user_id}")
        
        # Get recent executions for specific user
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        executions = db.query(TradingExecution).filter(
            TradingExecution.user_id == user_id,
            TradingExecution.created_at >= cutoff_date
        ).order_by(TradingExecution.created_at.desc()).all()
        
        print(f"📊 Found {len(executions)} executions for user {user_id}")
        
        # Format executions for order book
        formatted_orders = []
        for exec in executions:
            # Calculate P&L if trade is closed
            pnl_amount = exec.pnl_amount
            pnl_percent = exec.pnl_percent
            
            # Determine order status
            status = exec.status
            if status == "OPEN":
                status_display = "ACTIVE"
            elif status == "CLOSED":
                status_display = "CLOSED"
            else:
                status_display = status
            
            order_data = {
                'id': exec.id,
                'symbol': exec.symbol,
                'signal_type': exec.signal_type,
                'action': exec.action,
                'quantity': exec.quantity,
                'entry_price': exec.entry_price,
                'entry_value': exec.entry_value,
                'exit_price': exec.exit_price,
                'exit_value': exec.exit_value,
                'pnl_amount': pnl_amount,
                'pnl_percent': pnl_percent,
                'status': status_display,
                'entry_time': exec.entry_time.isoformat() if exec.entry_time else None,
                'exit_time': exec.exit_time.isoformat() if exec.exit_time else None,
                'holding_period_hours': exec.holding_period_hours,
                'created_at': exec.created_at.isoformat() if exec.created_at else None,
                'updated_at': exec.updated_at.isoformat() if exec.updated_at else None,
                'notes': exec.notes
            }
            
            # Add additional info from notes
            if exec.notes:
                try:
                    # Parse strategy info from notes
                    notes_str = exec.notes
                    if 'Strategy:' in notes_str:
                        parts = notes_str.split(',')
                        for part in parts:
                            if 'Strategy:' in part:
                                order_data['strategy'] = part.split(':')[1].strip()
                            elif 'Confidence:' in part:
                                order_data['confidence'] = float(part.split(':')[1].strip())
                            elif 'Signal Strength:' in part:
                                order_data['signal_strength'] = part.split(':')[1].strip()
                            elif 'Target:' in part:
                                order_data['target_price'] = float(part.split(':')[1].strip())
                            elif 'Stop Loss:' in part:
                                order_data['stop_loss'] = float(part.split(':')[1].strip())
                except:
                    pass
            
            formatted_orders.append(order_data)
        
        # Calculate summary statistics
        total_orders = len(formatted_orders)
        active_orders = len([o for o in formatted_orders if o['status'] == 'ACTIVE'])
        closed_orders = len([o for o in formatted_orders if o['status'] == 'CLOSED'])
        
        # Calculate total P&L for closed orders
        total_pnl = sum([o['pnl_amount'] or 0 for o in formatted_orders if o['pnl_amount'] is not None])
        
        try:
            return {
                'success': True,
                'data': {
                    'orders': formatted_orders,
                    'summary': {
                        'total_orders': total_orders,
                        'active_orders': active_orders,
                        'closed_orders': closed_orders,
                        'total_pnl': total_pnl,
                        'period_days': days
                    }
                },
                'message': f'Order book for user - Last {days} days'
            }
        finally:
            db.close()
        
    except Exception as e:
        if 'db' in locals():
            db.close()
        raise HTTPException(status_code=500, detail=f"Failed to get order book: {str(e)}")

@router.get("/order-summary")
async def get_order_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get order summary statistics"""
    try:
        # Get all executions
        executions = db.query(TradingExecution).filter(
            TradingExecution.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        # Calculate statistics
        total_orders = len(executions)
        buy_orders = len([e for e in executions if e.signal_type == 'BUY'])
        sell_orders = len([e for e in executions if e.signal_type == 'SELL'])
        
        # Status breakdown
        active_orders = len([e for e in executions if e.status == 'OPEN'])
        closed_orders = len([e for e in executions if e.status == 'CLOSED'])
        
        # P&L calculations
        profitable_trades = len([e for e in executions if e.pnl_amount and e.pnl_amount > 0])
        losing_trades = len([e for e in executions if e.pnl_amount and e.pnl_amount < 0])
        total_pnl = sum([e.pnl_amount or 0 for e in executions])
        
        # Win rate
        closed_with_pnl = [e for e in executions if e.pnl_amount is not None]
        win_rate = (profitable_trades / len(closed_with_pnl) * 100) if closed_with_pnl else 0
        
        return {
            'success': True,
            'data': {
                'total_orders': total_orders,
                'buy_orders': buy_orders,
                'sell_orders': sell_orders,
                'active_orders': active_orders,
                'closed_orders': closed_orders,
                'profitable_trades': profitable_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'win_rate': win_rate
            },
            'message': f'Order summary for {current_user.username}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order summary: {str(e)}")
