"""
Enhanced Order Placement API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from core.database import get_db
from services.order_placement_service import order_placement_service
from services.duration_analysis_service import duration_analysis_service
from core.auth_dependencies import get_current_active_user
from core.database_unified import User

router = APIRouter(prefix="/api/v1/order-placement", tags=["Order Placement"])

@router.post("/place")
async def place_order_with_analysis(
    order_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Place order with comprehensive analysis"""
    try:
        result = await order_placement_service.place_order_with_analysis(
            symbol=order_data['symbol'],
            order_type=order_data['order_type'],
            action=order_data['action'],
            quantity=order_data['quantity'],
            price=order_data['price'],
            user_id=current_user.id,
            db=db,
            signal_strength=order_data.get('signal_strength', 'MODERATE'),
            target_price=order_data.get('target_price'),
            stop_loss=order_data.get('stop_loss'),
            duration=order_data.get('duration', 'INTRADAY'),
            strategy=order_data.get('strategy', 'MANUAL'),
            confidence_score=order_data.get('confidence_score', 0.5),
            expected_holding_period=order_data.get('expected_holding_period'),
            market_conditions=order_data.get('market_conditions')
        )
        
        return {
            'success': True,
            'data': result,
            'message': 'Order placed and analyzed successfully'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")

@router.get("/order-types")
async def get_available_order_types():
    """Get available order types and their descriptions"""
    try:
        order_types = {
            'MARKET': {
                'name': 'Market Order',
                'description': 'Execute immediately at current market price',
                'pros': ['Guaranteed execution', 'Simple to use'],
                'cons': ['Price uncertainty', 'May get unfavorable price'],
                'best_for': ['High liquidity stocks', 'Urgent trades']
            },
            'LIMIT': {
                'name': 'Limit Order',
                'description': 'Execute only at specified price or better',
                'pros': ['Price control', 'No slippage'],
                'cons': ['No execution guarantee', 'May miss opportunity'],
                'best_for': ['Price sensitive trades', 'Large positions']
            },
            'STOP_LOSS': {
                'name': 'Stop Loss Order',
                'description': 'Sell when price falls below specified level',
                'pros': ['Risk protection', 'Automated exit'],
                'cons': ['May trigger prematurely', 'Fixed stop price'],
                'best_for': ['Risk management', 'Protecting profits']
            },
            'STOP_LIMIT': {
                'name': 'Stop Limit Order',
                'description': 'Combination of stop and limit orders',
                'pros': ['Price control with protection', 'Flexible execution'],
                'cons': ['Complex', 'May not execute'],
                'best_for': ['Precise risk management', 'Experienced traders']
            }
        }
        
        return {
            'success': True,
            'data': order_types,
            'message': 'Available order types retrieved successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order types: {str(e)}")

@router.get("/signal-strengths")
async def get_signal_strength_levels():
    """Get available signal strength levels"""
    try:
        signal_strengths = {
            'WEAK': {
                'name': 'Weak Signal',
                'score_range': [0.0, 0.25],
                'description': 'Low confidence signal',
                'recommended_action': 'Reduce position size',
                'risk_level': 'HIGH'
            },
            'MODERATE': {
                'name': 'Moderate Signal',
                'score_range': [0.25, 0.5],
                'description': 'Decent confidence signal',
                'recommended_action': 'Normal position size',
                'risk_level': 'MEDIUM'
            },
            'STRONG': {
                'name': 'Strong Signal',
                'score_range': [0.5, 0.75],
                'description': 'High confidence signal',
                'recommended_action': 'Consider larger position',
                'risk_level': 'LOW-MEDIUM'
            },
            'VERY_STRONG': {
                'name': 'Very Strong Signal',
                'score_range': [0.75, 1.0],
                'description': 'Very high confidence signal',
                'recommended_action': 'Maximum position size',
                'risk_level': 'LOW'
            }
        }
        
        return {
            'success': True,
            'data': signal_strengths,
            'message': 'Signal strength levels retrieved successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signal strengths: {str(e)}")

@router.get("/durations")
async def get_duration_categories():
    """Get available duration categories"""
    try:
        durations = {
            'SCALP': {
                'name': 'Scalp Trading',
                'hours_range': '0-1 hours',
                'description': 'Very short-term trades for small profits',
                'target_win_rate': 0.6,
                'target_return': 0.5,
                'risk_level': 'HIGH',
                'required_attention': 'VERY HIGH'
            },
            'INTRADAY': {
                'name': 'Intraday Trading',
                'hours_range': '1-6 hours',
                'description': 'Same-day trades with no overnight risk',
                'target_win_rate': 0.55,
                'target_return': 1.0,
                'risk_level': 'MEDIUM-HIGH',
                'required_attention': 'HIGH'
            },
            'SWING': {
                'name': 'Swing Trading',
                'hours_range': '6-72 hours',
                'description': 'Multi-day trades capturing price swings',
                'target_win_rate': 0.5,
                'target_return': 2.0,
                'risk_level': 'MEDIUM',
                'required_attention': 'MEDIUM'
            },
            'POSITIONAL': {
                'name': 'Positional Trading',
                'hours_range': '3-7 days',
                'description': 'Week-long trades following trends',
                'target_win_rate': 0.45,
                'target_return': 3.0,
                'risk_level': 'MEDIUM-LOW',
                'required_attention': 'LOW-MEDIUM'
            },
            'LONG_TERM': {
                'name': 'Long-term Trading',
                'hours_range': '7+ days',
                'description': 'Long-term investments based on fundamentals',
                'target_win_rate': 0.4,
                'target_return': 5.0,
                'risk_level': 'LOW',
                'required_attention': 'LOW'
            }
        }
        
        return {
            'success': True,
            'data': durations,
            'message': 'Duration categories retrieved successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get durations: {str(e)}")

@router.get("/validate")
async def validate_order_parameters(
    symbol: str = Query(...),
    order_type: str = Query(...),
    action: str = Query(...),
    quantity: int = Query(...),
    price: float = Query(...),
    target_price: Optional[float] = Query(None),
    stop_loss: Optional[float] = Query(None)
):
    """Validate order parameters before placing"""
    try:
        validation_result = order_placement_service._validate_order_parameters(
            symbol, order_type, action, quantity, price, target_price, stop_loss
        )
        
        return {
            'success': True,
            'data': validation_result,
            'message': 'Order validation completed'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/calculate-metrics")
async def calculate_order_metrics(
    symbol: str = Query(...),
    order_type: str = Query(...),
    action: str = Query(...),
    quantity: int = Query(...),
    price: float = Query(...),
    target_price: Optional[float] = Query(None),
    stop_loss: Optional[float] = Query(None),
    signal_strength: str = Query('MODERATE'),
    confidence_score: float = Query(0.5),
    market_conditions: Optional[Dict[str, Any]] = None
):
    """Calculate order metrics before placing"""
    try:
        metrics = order_placement_service._calculate_order_metrics(
            symbol, order_type, action, quantity, price, target_price, stop_loss,
            signal_strength, confidence_score, market_conditions
        )
        
        return {
            'success': True,
            'data': metrics,
            'message': 'Order metrics calculated successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics calculation failed: {str(e)}")

@router.get("/duration-analysis")
async def get_duration_analysis(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive duration analysis"""
    try:
        result = await duration_analysis_service.analyze_trade_durations(
            user_id=current_user.id,
            days=days,
            db=db
        )
        
        return {
            'success': True,
            'data': result.get('data', {}),
            'message': f'Duration analysis for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duration analysis failed: {str(e)}")

@router.get("/holding-patterns")
async def get_holding_patterns(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed holding patterns analysis"""
    try:
        # Get duration analysis first
        duration_result = await duration_analysis_service.analyze_trade_durations(
            user_id=current_user.id,
            days=days,
            db=db
        )
        
        holding_patterns = duration_result.get('data', {}).get('holding_patterns', {})
        
        return {
            'success': True,
            'data': holding_patterns,
            'message': f'Holding patterns for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Holding patterns analysis failed: {str(e)}")

@router.get("/optimal-duration")
async def get_optimal_duration(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get optimal duration recommendation"""
    try:
        # Get duration analysis
        duration_result = await duration_analysis_service.analyze_trade_durations(
            user_id=current_user.id,
            days=days,
            db=db
        )
        
        optimal_duration = duration_result.get('data', {}).get('optimal_duration', {})
        
        return {
            'success': True,
            'data': optimal_duration,
            'message': 'Optimal duration recommendation'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimal duration analysis failed: {str(e)}")

@router.get("/performance-by-duration")
async def get_performance_by_duration(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance breakdown by duration category"""
    try:
        # Get duration analysis
        duration_result = await duration_analysis_service.analyze_trade_durations(
            user_id=current_user.id,
            days=days,
            db=db
        )
        
        performance_by_duration = duration_result.get('data', {}).get('performance_by_duration', {})
        
        return {
            'success': True,
            'data': performance_by_duration,
            'message': f'Performance by duration for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance by duration analysis failed: {str(e)}")

@router.post("/simulate-order")
async def simulate_order_placement(
    order_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Simulate order placement without actually executing"""
    try:
        # Calculate metrics
        metrics = order_placement_service._calculate_order_metrics(
            symbol=order_data['symbol'],
            order_type=order_data['order_type'],
            action=order_data['action'],
            quantity=order_data['quantity'],
            price=order_data['price'],
            target_price=order_data.get('target_price'),
            stop_loss=order_data.get('stop_loss'),
            signal_strength=order_data.get('signal_strength', 'MODERATE'),
            confidence_score=order_data.get('confidence_score', 0.5),
            market_conditions=order_data.get('market_conditions')
        )
        
        # Validate parameters
        validation = order_placement_service._validate_order_parameters(
            symbol=order_data['symbol'],
            order_type=order_data['order_type'],
            action=order_data['action'],
            quantity=order_data['quantity'],
            price=order_data['price'],
            target_price=order_data.get('target_price'),
            stop_loss=order_data.get('stop_loss')
        )
        
        # Get user's historical data for placement analysis
        user_history = await order_placement_service._get_user_order_history(
            current_user.id, db
        )
        
        # Simulate placement analysis
        timing_analysis = order_placement_service._analyze_order_timing(
            type('MockExecution', (), {
                'entry_time': datetime.utcnow(),
                'symbol': order_data['symbol']
            })(),
            user_history
        )
        
        size_analysis = order_placement_service._analyze_order_size(
            type('MockExecution', (), {
                'entry_value': order_data['price'] * order_data['quantity']
            })(),
            user_history
        )
        
        risk_analysis = order_placement_service._analyze_risk_reward(
            type('MockExecution', (), {
                'order_metrics': metrics
            })()
        )
        
        recommendations = order_placement_service._generate_order_recommendations(
            type('MockExecution', (), {
                'order_type': order_data['order_type'],
                'signal_strength': order_data.get('signal_strength', 'MODERATE')
            })(),
            timing_analysis,
            size_analysis,
            risk_analysis
        )
        
        simulation_result = {
            'validation': validation,
            'metrics': metrics,
            'timing_analysis': timing_analysis,
            'size_analysis': size_analysis,
            'risk_analysis': risk_analysis,
            'recommendations': recommendations,
            'overall_score': order_placement_service._calculate_placement_score(
                timing_analysis, size_analysis, risk_analysis
            )
        }
        
        return {
            'success': True,
            'data': simulation_result,
            'message': 'Order simulation completed successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order simulation failed: {str(e)}")
