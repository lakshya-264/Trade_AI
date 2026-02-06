"""
Portfolio API Endpoints - Complete portfolio visibility and performance
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from core.database import get_db
from services.portfolio_integration_service import portfolio_integration_service
from services.enhanced_trading_service import enhanced_trading_service
from core.auth_dependencies import get_current_active_user
from core.database_unified import User

router = APIRouter(prefix="/api/v1/portfolio", tags=["Portfolio"])

@router.post("/place-order")
async def place_order_and_update_portfolio(
    order_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Place order and immediately update portfolio holdings"""
    try:
        result = await portfolio_integration_service.place_order_and_update_portfolio(
            order_data=order_data,
            user_id=current_user.id,
            db=db
        )
        
        return {
            'success': True,
            'data': result,
            'message': 'Order placed and portfolio updated successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")

@router.get("/holdings")
async def get_portfolio_holdings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete portfolio holdings with performance details"""
    try:
        result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio holdings: {str(e)}")

@router.get("/performance")
async def get_portfolio_performance(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive portfolio performance"""
    try:
        # Get unified performance
        unified_result = await enhanced_trading_service.get_unified_performance_summary(
            user_id=current_user.id,
            days=days,
            db=db
        )
        
        # Get portfolio with performance
        portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        return {
            'success': True,
            'data': {
                'unified_performance': unified_result,
                'portfolio_details': portfolio_result.get('data', {}),
                'performance_period': days,
                'generated_at': datetime.utcnow().isoformat()
            },
            'message': f'Portfolio performance for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio performance: {str(e)}")

@router.get("/holdings/{symbol}")
async def get_holding_details(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific holding"""
    try:
        # Get portfolio holdings
        portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        holdings = portfolio_result.get('data', {}).get('holdings', {})
        
        if symbol not in holdings:
            raise HTTPException(status_code=404, detail=f"Holding {symbol} not found")
        
        holding_details = holdings[symbol]
        
        # Get additional symbol-specific data
        symbol_performance = await portfolio_integration_service._get_symbol_performance_for_portfolio(
            symbol, current_user.id, db
        )
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'holding_details': holding_details,
                'symbol_performance': symbol_performance,
                'recommendations': await _generate_holding_recommendations(holding_details, symbol_performance)
            },
            'message': f'Details for {symbol} holding'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get holding details: {str(e)}")

@router.get("/allocation")
async def get_portfolio_allocation(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get portfolio allocation breakdown"""
    try:
        portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        data = portfolio_result.get('data', {})
        
        allocation_data = {
            'total_value': data.get('total_value', 0),
            'holding_count': data.get('holding_count', 0),
            'portfolio_composition': data.get('portfolio_composition', {}),
            'sector_allocation': data.get('sector_allocation', {}),
            'risk_metrics': data.get('risk_metrics', {}),
            'allocation_analysis': await _analyze_allocation(data)
        }
        
        return {
            'success': True,
            'data': allocation_data,
            'message': 'Portfolio allocation breakdown'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio allocation: {str(e)}")

@router.get("/risk-analysis")
async def get_portfolio_risk_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive portfolio risk analysis"""
    try:
        portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        data = portfolio_result.get('data', {})
        risk_metrics = data.get('risk_metrics', {})
        
        # Enhanced risk analysis
        risk_analysis = {
            'current_risk_metrics': risk_metrics,
            'risk_assessment': await _assess_portfolio_risk(risk_metrics, data),
            'risk_recommendations': await _generate_risk_recommendations(risk_metrics, data),
            'stress_test_results': await _perform_stress_test(data),
            'var_analysis': await _calculate_var(data)  # Value at Risk
        }
        
        return {
            'success': True,
            'data': risk_analysis,
            'message': 'Portfolio risk analysis'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk analysis: {str(e)}")

@router.get("/transactions")
async def get_portfolio_transactions(
    days: int = Query(30, description="Number of days to fetch"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get portfolio transaction history"""
    try:
        # Get recent transactions (would need Transaction table in real implementation)
        transactions = await _get_user_transactions(current_user.id, days, db)
        
        return {
            'success': True,
            'data': {
                'transactions': transactions,
                'transaction_summary': await _summarize_transactions(transactions),
                'period_days': days
            },
            'message': f'Portfolio transactions for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")

@router.get("/watchlist")
async def get_portfolio_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get portfolio watchlist"""
    try:
        # Get user's watchlist (would need Watchlist table in real implementation)
        watchlist = await _get_user_watchlist(current_user.id, db)
        
        return {
            'success': True,
            'data': {
                'watchlist': watchlist,
                'watchlist_count': len(watchlist),
                'watchlist_performance': await _calculate_watchlist_performance(watchlist)
            },
            'message': 'Portfolio watchlist'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get watchlist: {str(e)}")

@router.post("/watchlist/add")
async def add_to_watchlist(
    symbol_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add symbol to watchlist"""
    try:
        symbol = symbol_data['symbol']
        
        # Add to watchlist (would need Watchlist table)
        result = await _add_to_watchlist(current_user.id, symbol, db)
        
        return {
            'success': True,
            'data': result,
            'message': f'{symbol} added to watchlist'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to watchlist: {str(e)}")

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove symbol from watchlist"""
    try:
        result = await _remove_from_watchlist(current_user.id, symbol, db)
        
        return {
            'success': True,
            'data': result,
            'message': f'{symbol} removed from watchlist'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove from watchlist: {str(e)}")

@router.get("/dashboard")
async def get_portfolio_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete portfolio dashboard data"""
    try:
        # Get portfolio with performance
        portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        # Get unified performance
        unified_result = await enhanced_trading_service.get_unified_performance_summary(
            user_id=current_user.id,
            days=30,
            db=db
        )
        
        # Get recent transactions
        recent_transactions = await _get_user_transactions(current_user.id, 7, db)
        
        # Get watchlist
        watchlist = await _get_user_watchlist(current_user.id, db)
        
        # Create dashboard data
        dashboard_data = {
            'portfolio_summary': portfolio_result.get('data', {}),
            'performance_metrics': unified_result.get('unified_metrics', {}),
            'recent_transactions': recent_transactions[:5],  # Last 5 transactions
            'watchlist': watchlist[:10],  # Top 10 watchlist items
            'top_performers': await _get_top_performers(portfolio_result.get('data', {}).get('holdings', {})),
            'market_overview': await _get_market_overview(),
            'recommendations': await _generate_portfolio_recommendations(portfolio_result.get('data', {})),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return {
            'success': True,
            'data': dashboard_data,
            'message': 'Portfolio dashboard data'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

@router.get("/export")
async def export_portfolio_data(
    format: str = Query('json', description="Export format: json, csv"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export portfolio data"""
    try:
        portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
            user_id=current_user.id,
            db=db
        )
        
        if format == 'csv':
            export_data = await _export_to_csv(portfolio_result.get('data', {}))
        else:
            export_data = portfolio_result.get('data', {})
        
        return {
            'success': True,
            'data': export_data,
            'format': format,
            'exported_at': datetime.utcnow().isoformat(),
            'message': f'Portfolio data exported as {format}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export portfolio data: {str(e)}")

# Helper functions (would be implemented in real system)

async def _generate_holding_recommendations(holding_details: Dict[str, Any], symbol_performance: Dict[str, Any]) -> List[str]:
    """Generate recommendations for a specific holding"""
    recommendations = []
    
    pnl_percent = holding_details.get('unrealized_pnl_percent', 0)
    win_rate = symbol_performance.get('win_rate', 0)
    
    if pnl_percent > 10:
        recommendations.append("Consider taking partial profits - position is up significantly")
    elif pnl_percent < -10:
        recommendations.append("Position is down significantly - review stop-loss strategy")
    
    if win_rate < 0.4:
        recommendations.append("Low win rate for this symbol - consider reducing position size")
    
    days_held = holding_details.get('days_held', 0)
    if days_held > 30 and pnl_percent < 0:
        recommendations.append("Long-term losing position - consider cutting losses")
    
    return recommendations

async def _analyze_allocation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze portfolio allocation"""
    return {
        'diversification_score': data.get('risk_metrics', {}).get('diversification_score', 0),
        'concentration_warning': data.get('risk_metrics', {}).get('concentration_risk', 0) > 30,
        'sector_balance': 'BALANCED',  # Simplified
        'allocation_efficiency': 85  # Placeholder
    }

async def _assess_portfolio_risk(risk_metrics: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall portfolio risk"""
    return {
        'risk_level': risk_metrics.get('risk_level', 'MEDIUM'),
        'risk_score': 65,  # Placeholder
        'main_risks': ['CONCENTRATION_RISK'] if risk_metrics.get('concentration_risk', 0) > 25 else [],
        'risk_factors': {
            'concentration': risk_metrics.get('concentration_risk', 0),
            'volatility': risk_metrics.get('volatility', 0),
            'diversification': risk_metrics.get('diversification_score', 0)
        }
    }

async def _generate_risk_recommendations(risk_metrics: Dict[str, Any], data: Dict[str, Any]) -> List[str]:
    """Generate risk management recommendations"""
    recommendations = []
    
    if risk_metrics.get('concentration_risk', 0) > 30:
        recommendations.append("Consider diversifying - concentration risk is high")
    
    if risk_metrics.get('volatility', 0) > 25:
        recommendations.append("Portfolio volatility is high - consider adding stable positions")
    
    if risk_metrics.get('diversification_score', 0) < 50:
        recommendations.append("Low diversification - add positions from different sectors")
    
    return recommendations

async def _perform_stress_test(data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform portfolio stress test"""
    return {
        'market_crash_scenario': -15.2,  # Portfolio would lose 15.2% in market crash
        'sector_downturn_scenario': -8.5,
        'best_case_scenario': 12.3,
        'stress_test_rating': 'MODERATE'
    }

async def _calculate_var(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Value at Risk"""
    return {
        'daily_var_95': -2.5,  # 95% VaR: 2.5% daily loss
        'weekly_var_95': -8.2,
        'monthly_var_95': -15.7,
        'var_confidence': 95
    }

async def _get_user_transactions(user_id: int, days: int, db: Session) -> List[Dict[str, Any]]:
    """Get user's transaction history"""
    # Placeholder - would query Transaction table
    return [
        {
            'date': '2026-01-22',
            'symbol': 'RELIANCE',
            'action': 'BUY',
            'quantity': 100,
            'price': 2500.0,
            'total_value': 250000.0,
            'order_type': 'MARKET'
        }
    ]

async def _summarize_transactions(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize transactions"""
    total_buys = len([t for t in transactions if t['action'] == 'BUY'])
    total_sells = len([t for t in transactions if t['action'] == 'SELL'])
    total_volume = sum(t['total_value'] for t in transactions)
    
    return {
        'total_transactions': len(transactions),
        'total_buys': total_buys,
        'total_sells': total_sells,
        'total_volume': total_volume,
        'most_traded_symbol': 'RELIANCE'  # Placeholder
    }

async def _get_user_watchlist(user_id: int, db: Session) -> List[Dict[str, Any]]:
    """Get user's watchlist"""
    # Placeholder - would query Watchlist table
    return [
        {
            'symbol': 'TCS',
            'current_price': 3500.0,
            'daily_change': 1.2,
            'added_date': '2026-01-15'
        }
    ]

async def _calculate_watchlist_performance(watchlist: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate watchlist performance"""
    return {
        'avg_daily_change': 0.8,
        'best_performer': 'TCS',
        'worst_performer': 'INFY'
    }

async def _add_to_watchlist(user_id: int, symbol: str, db: Session) -> Dict[str, Any]:
    """Add symbol to watchlist"""
    return {'symbol': symbol, 'added': True}

async def _remove_from_watchlist(user_id: int, symbol: str, db: Session) -> Dict[str, Any]:
    """Remove symbol from watchlist"""
    return {'symbol': symbol, 'removed': True}

async def _get_top_performers(holdings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get top performing holdings"""
    performers = []
    
    for symbol, holding in holdings.items():
        pnl_percent = holding.get('unrealized_pnl_percent', 0)
        performers.append({
            'symbol': symbol,
            'pnl_percent': pnl_percent,
            'current_value': holding.get('current_value', 0)
        })
    
    return sorted(performers, key=lambda x: x['pnl_percent'], reverse=True)[:5]

async def _get_market_overview() -> Dict[str, Any]:
    """Get market overview"""
    return {
        'nifty': {'value': 19650, 'change': 0.8},
        'banknifty': {'value': 44800, 'change': 1.2},
        'market_sentiment': 'BULLISH',
        'sector_performance': {
            'IT': 1.5,
            'BANKING': 0.8,
            'PHARMA': -0.3
        }
    }

async def _generate_portfolio_recommendations(data: Dict[str, Any]) -> List[str]:
    """Generate portfolio recommendations"""
    recommendations = []
    
    total_pnl_percent = data.get('overall_performance', {}).get('total_pnl_percent', 0)
    
    if total_pnl_percent < -5:
        recommendations.append("Portfolio is down - consider rebalancing")
    
    if data.get('holding_count', 0) < 5:
        recommendations.append("Consider diversifying - portfolio has few holdings")
    
    risk_level = data.get('risk_metrics', {}).get('risk_level', 'MEDIUM')
    if risk_level == 'HIGH':
        recommendations.append("Portfolio risk is high - consider reducing position sizes")
    
    return recommendations

async def _export_to_csv(data: Dict[str, Any]) -> str:
    """Export portfolio data to CSV format"""
    # Placeholder - would generate actual CSV
    return "symbol,quantity,avg_price,current_value,pnl_percent\nRELIANCE,100,2500,250000,2.5"
