"""
Real-time Nifty 50 Signal Execution API
Automatically executes trading signals and updates portfolio
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from core.database import get_db
from services.real_time_order_service import real_time_order_service
from services.portfolio_integration_service import portfolio_integration_service
from services.trading_performance_service import trading_performance_service
from core.database_unified import User, Portfolio
from core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/realtime-trading", tags=["Real-time Trading"])

@router.post("/execute-nifty50-signals")
async def execute_nifty50_signals(
    timeframe: str = Query("5m", description="Timeframe for signals"),
    max_trades: int = Query(5, description="Maximum trades to execute"),
    min_confidence: float = Query(0.7, description="Minimum confidence level"),
    paper_trading: bool = Query(True, description="Use paper trading mode"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute Nifty 50 trading signals in real-time
    - Analyzes signals from all strategies
    - Executes trades based on confidence levels
    - Updates portfolio holdings
    - Tracks performance and accuracy
    """
    try:
        logger.info(f"Executing Nifty50 signals for user {current_user.id}")
        
        # Step 1: Get current Nifty 50 signals
        from api.routes.comprehensive_trading import get_nifty50_trading_signals
        
        # Get signals without cache for real-time execution
        signals_response = await get_nifty50_trading_signals(
            timeframe=timeframe,
            days=1,
            current_user=current_user,
            use_cache=False
        )
        
        if not signals_response.get('success'):
            raise HTTPException(status_code=500, detail="Failed to fetch trading signals")
        
        signals_data = signals_response.get('data', [])
        logger.info(f"Received {len(signals_data)} signals")
        
        # Step 2: Filter and rank signals by confidence
        filtered_signals = _filter_high_confidence_signals(signals_data, min_confidence)
        logger.info(f"Filtered to {len(filtered_signals)} high-confidence signals")
        
        # Step 3: Select top signals for execution
        selected_signals = _select_top_signals(filtered_signals, max_trades)
        logger.info(f"Selected {len(selected_signals)} signals for execution")
        
        # Step 4: Execute trades
        executed_trades = []
        for signal in selected_signals:
            try:
                trade_result = await _execute_signal_trade(
                    signal=signal,
                    user_id=current_user.id,
                    paper_trading=paper_trading,
                    db=db
                )
                
                if trade_result.get('success'):
                    executed_trades.append({
                        'symbol': signal['symbol'],
                        'signal_type': signal['primary_signal'],
                        'confidence': signal['confidence'],
                        'execution_result': trade_result
                    })
                    logger.info(f"Executed trade for {signal['symbol']}")
                else:
                    logger.error(f"Failed to execute trade for {signal['symbol']}: {trade_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error executing trade for {signal['symbol']}: {e}")
                continue
        
        # Step 5: Update portfolio and track performance
        portfolio_update = await _update_portfolio_after_execution(
            executed_trades=executed_trades,
            user_id=current_user.id,
            db=db
        )
        
        return {
            "success": True,
            "data": {
                "total_signals": len(signals_data),
                "filtered_signals": len(filtered_signals),
                "executed_trades": len(executed_trades),
                "trades": executed_trades,
                "portfolio_update": portfolio_update,
                "execution_time": datetime.utcnow().isoformat(),
                "paper_trading": paper_trading
            },
            "message": f"Successfully executed {len(executed_trades)} trades from Nifty 50 signals"
        }
        
    except Exception as e:
        logger.error(f"Error executing Nifty50 signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute signals: {str(e)}")

@router.get("/signal-accuracy")
async def get_signal_accuracy(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get accuracy metrics for executed signals"""
    try:
        # Get performance data for user's trades
        performance_data = await trading_performance_service.get_symbol_performance_summary(
            symbol="ALL",  # Get all symbols
            days=days,
            db=db
        )
        
        # Calculate accuracy metrics
        accuracy_metrics = _calculate_signal_accuracy(performance_data)
        
        return {
            "success": True,
            "data": accuracy_metrics,
            "message": f"Signal accuracy for the last {days} days"
        }
        
    except Exception as e:
        logger.error(f"Error getting signal accuracy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signal accuracy: {str(e)}")

@router.get("/portfolio-holdings")
async def get_portfolio_holdings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current portfolio holdings from executed trades"""
    try:
        # Get portfolio holdings
        holdings = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id,
            Portfolio.quantity > 0  # Only show active holdings
        ).all()
        
        # Format holdings data
        formatted_holdings = []
        for holding in holdings:
            formatted_holdings.append({
                'symbol': holding.symbol,
                'quantity': holding.quantity,
                'avg_price': holding.avg_price,
                'current_price': holding.current_price,
                'total_value': holding.total_value,
                'pnl': holding.pnl,
                'pnl_percent': holding.pnl_percent,
                'last_updated': holding.updated_at
            })
        
        return {
            "success": True,
            "data": {
                "holdings": formatted_holdings,
                "total_value": sum(h['total_value'] for h in formatted_holdings),
                "total_pnl": sum(h['pnl'] for h in formatted_holdings),
                "count": len(formatted_holdings)
            },
            "message": f"Portfolio holdings for {len(formatted_holdings)} stocks"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio holdings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio holdings: {str(e)}")

# Helper functions
def _filter_high_confidence_signals(signals: List[Dict], min_confidence: float) -> List[Dict]:
    """Filter signals by minimum confidence level"""
    filtered = []
    for signal in signals:
        # Calculate overall confidence from all strategies
        confidence = _calculate_signal_confidence(signal)
        if confidence >= min_confidence:
            signal['confidence'] = confidence
            filtered.append(signal)
    
    # Sort by confidence (highest first)
    filtered.sort(key=lambda x: x['confidence'], reverse=True)
    return filtered

def _calculate_signal_confidence(signal: Dict) -> float:
    """Calculate overall confidence from all strategy signals"""
    strategies = ['vwap_signal', 'momentum_signal', 'breakout_signal', 'mean_reversion_signal', 'scalping_signal']
    confidence_scores = []
    
    for strategy in strategies:
        if strategy in signal:
            signal_strength = signal.get(f"{strategy.replace('_signal', '_strength')}", 'WEAK')
            score = _get_strength_score(signal_strength)
            confidence_scores.append(score)
    
    # Return average confidence
    return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

def _get_strength_score(strength: str) -> float:
    """Convert strength string to numeric score"""
    strength_scores = {
        'VERY_STRONG': 1.0,
        'STRONG': 0.8,
        'MODERATE': 0.6,
        'WEAK': 0.4,
        'VERY_WEAK': 0.2
    }
    return strength_scores.get(strength, 0.5)

def _select_top_signals(signals: List[Dict], max_trades: int) -> List[Dict]:
    """Select top signals for execution"""
    return signals[:max_trades]

async def _execute_signal_trade(signal: Dict, user_id: int, paper_trading: bool, db: Session) -> Dict:
    """Execute a single signal trade"""
    try:
        symbol = signal['symbol']
        primary_signal = signal.get('primary_signal', 'HOLD')
        
        if primary_signal == 'BUY':
            # Determine quantity based on signal strength
            quantity = _calculate_trade_quantity(signal, paper_trading)
            
            result = await real_time_order_service.place_buy_order_market_price(
                symbol=symbol,
                quantity=quantity,
                user_id=user_id,
                db=db,
                strategy='NIFTY50_AUTO',
                paper_trading=paper_trading
            )
        elif primary_signal == 'SELL':
            quantity = _calculate_trade_quantity(signal, paper_trading)
            
            result = await real_time_order_service.place_sell_order_market_price(
                symbol=symbol,
                quantity=quantity,
                user_id=user_id,
                db=db,
                strategy='NIFTY50_AUTO',
                paper_trading=paper_trading
            )
        else:
            return {'success': False, 'error': 'No actionable signal'}
        
        return result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def _calculate_trade_quantity(signal: Dict, paper_trading: bool) -> int:
    """Calculate trade quantity based on signal strength and risk"""
    # Base quantity for paper trading
    base_quantity = 10 if paper_trading else 100
    
    # Adjust based on confidence
    confidence = signal.get('confidence', 0.5)
    multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1.0x based on confidence
    
    return int(base_quantity * multiplier)

async def _update_portfolio_after_execution(executed_trades: List[Dict], user_id: int, db: Session) -> Dict:
    """Update portfolio after trade execution"""
    try:
        # The portfolio integration service should have already updated holdings
        # This function can be used for additional tracking or notifications
        
        return {
            'success': True,
            'updated_holdings': len(executed_trades),
            'message': 'Portfolio updated successfully'
        }
        
    except Exception as e:
        logger.error(f"Error updating portfolio: {e}")
        return {'success': False, 'error': str(e)}

def _calculate_signal_accuracy(performance_data: Dict) -> Dict:
    """Calculate signal accuracy metrics"""
    try:
        total_trades = performance_data.get('total_trades', 0)
        win_rate = performance_data.get('win_rate', 0)
        total_pnl = performance_data.get('total_pnl_percent', 0)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl_percent': total_pnl,
            'profitable_trades': performance_data.get('profitable_trades', 0),
            'losing_trades': performance_data.get('losing_trades', 0),
            'accuracy_score': win_rate * (1 + total_pnl/100) if total_pnl > 0 else win_rate
        }
        
    except Exception as e:
        logger.error(f"Error calculating accuracy: {e}")
        return {'error': str(e)}
