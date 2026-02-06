"""
Real-time Order API Endpoints - Market Price Integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.database import get_db
from services.real_time_order_service import real_time_order_service
from services.market_price_service import market_price_service
from core.auth_dependencies import get_current_active_user
from core.database_unified import User

router = APIRouter(prefix="/api/v1/realtime-orders", tags=["Real-time Orders"])

@router.post("/buy-market-price")
async def buy_at_market_price(
    order_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Place BUY order at current market price"""
    try:
        result = await real_time_order_service.place_buy_order_market_price(
            symbol=order_data['symbol'],
            quantity=order_data['quantity'],
            user_id=current_user.id,
            db=db,
            order_type=order_data.get('order_type', 'MARKET'),
            signal_strength=order_data.get('signal_strength', 'MODERATE'),
            confidence_score=order_data.get('confidence_score', 0.5),
            target_price=order_data.get('target_price'),
            stop_loss=order_data.get('stop_loss'),
            duration=order_data.get('duration', 'INTRADAY'),
            strategy=order_data.get('strategy', 'MANUAL'),
            expected_holding_period=order_data.get('expected_holding_period')
        )
        
        return {
            'success': True,
            'data': result,
            'message': f'BUY order placed for {order_data["symbol"]} at market price'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place BUY order: {str(e)}")

@router.post("/sell-market-price")
async def sell_at_market_price(
    order_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Place SELL order at current market price"""
    try:
        result = await real_time_order_service.place_sell_order_market_price(
            symbol=order_data['symbol'],
            quantity=order_data['quantity'],
            user_id=current_user.id,
            db=db,
            order_type=order_data.get('order_type', 'MARKET'),
            signal_strength=order_data.get('signal_strength', 'MODERATE'),
            confidence_score=order_data.get('confidence_score', 0.5),
            target_price=order_data.get('target_price'),
            stop_loss=order_data.get('stop_loss'),
            duration=order_data.get('duration', 'INTRADAY'),
            strategy=order_data.get('strategy', 'MANUAL')
        )
        
        return {
            'success': True,
            'data': result,
            'message': f'SELL order placed for {order_data["symbol"]} at market price'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place SELL order: {str(e)}")

@router.get("/price-preview/{symbol}")
async def get_price_preview(
    symbol: str,
    action: str = Query(..., description="BUY or SELL"),
    quantity: int = Query(..., description="Number of shares"),
    order_type: str = Query('MARKET', description="Order type"),
    current_user: User = Depends(get_current_active_user)
):
    """Get price preview before placing order"""
    try:
        preview = await real_time_order_service.get_order_price_preview(
            symbol=symbol,
            action=action,
            quantity=quantity,
            order_type=order_type
        )
        
        return {
            'success': True,
            'data': preview,
            'message': f'Price preview for {symbol}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price preview: {str(e)}")

@router.post("/bulk-price-preview")
async def get_bulk_price_preview(
    orders: List[Dict[str, Any]],
    current_user: User = Depends(get_current_active_user)
):
    """Get price preview for multiple orders"""
    try:
        preview = await real_time_order_service.get_bulk_price_preview(orders)
        
        return {
            'success': True,
            'data': preview,
            'message': f'Bulk price preview for {len(orders)} orders'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bulk price preview: {str(e)}")

@router.get("/current-price/{symbol}")
async def get_current_price(
    symbol: str,
    use_cache: bool = Query(True, description="Use cached price")
):
    """Get current market price for a symbol"""
    try:
        price_data = await market_price_service.get_current_price(symbol, use_cache)
        
        return {
            'success': True,
            'data': price_data,
            'message': f'Current price for {symbol}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current price: {str(e)}")

@router.get("/multiple-prices")
async def get_multiple_prices(
    symbols: List[str] = Query(..., description="List of symbols"),
    use_cache: bool = Query(True, description="Use cached prices")
):
    """Get current prices for multiple symbols"""
    try:
        prices = await market_price_service.get_multiple_prices(symbols, use_cache)
        
        return {
            'success': True,
            'data': prices,
            'message': f'Prices for {len(symbols)} symbols'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get multiple prices: {str(e)}")

@router.get("/market-status")
async def get_market_status():
    """Get current market status"""
    try:
        status = await market_price_service.get_market_status()
        
        return {
            'success': True,
            'data': status,
            'message': 'Market status'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market status: {str(e)}")

@router.post("/validate-order")
async def validate_order(
    order_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate order before placement"""
    try:
        validation = await real_time_order_service.validate_order_before_placement(
            symbol=order_data['symbol'],
            action=order_data['action'],
            quantity=order_data['quantity'],
            user_id=current_user.id,
            db=db
        )
        
        return {
            'success': True,
            'data': validation,
            'message': 'Order validation completed'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate order: {str(e)}")

@router.get("/order-confirmation/{symbol}")
async def get_order_confirmation(
    symbol: str,
    action: str = Query(..., description="BUY or SELL"),
    quantity: int = Query(..., description="Number of shares"),
    order_type: str = Query('MARKET', description="Order type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete order confirmation with validation and preview"""
    try:
        # Get price preview
        preview = await real_time_order_service.get_order_price_preview(
            symbol=symbol,
            action=action,
            quantity=quantity,
            order_type=order_type
        )
        
        # Validate order
        validation = await real_time_order_service.validate_order_before_placement(
            symbol=symbol,
            action=action,
            quantity=quantity,
            user_id=current_user.id,
            db=db
        )
        
        # Get market status
        market_status = await market_price_service.get_market_status()
        
        confirmation_data = {
            'preview': preview,
            'validation': validation,
            'market_status': market_status,
            'can_place_order': validation['is_valid'] and len(validation['errors']) == 0,
            'recommendations': validation['recommendations'],
            'warnings': validation['warnings'],
            'errors': validation['errors']
        }
        
        return {
            'success': True,
            'data': confirmation_data,
            'message': f'Order confirmation for {symbol}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order confirmation: {str(e)}")

@router.get("/portfolio-quick-buy/{symbol}")
async def quick_buy_from_portfolio(
    symbol: str,
    quantity: int = Query(1, description="Number of shares"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Quick buy from portfolio view"""
    try:
        # Get order confirmation
        confirmation = await get_order_confirmation(symbol, 'BUY', quantity, 'MARKET', current_user, db)
        
        if not confirmation['data']['can_place_order']:
            return {
                'success': False,
                'data': confirmation['data'],
                'message': 'Cannot place order - validation failed'
            }
        
        # Place the order
        order_data = {
            'symbol': symbol,
            'quantity': quantity,
            'order_type': 'MARKET',
            'signal_strength': 'MODERATE',
            'confidence_score': 0.5
        }
        
        result = await real_time_order_service.place_buy_order_market_price(
            symbol=symbol,
            quantity=quantity,
            user_id=current_user.id,
            db=db,
            **order_data
        )
        
        return {
            'success': True,
            'data': result,
            'message': f'Quick BUY order placed for {symbol}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place quick buy order: {str(e)}")

@router.get("/portfolio-quick-sell/{symbol}")
async def quick_sell_from_portfolio(
    symbol: str,
    quantity: int = Query(1, description="Number of shares"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Quick sell from portfolio view"""
    try:
        # Get order confirmation
        confirmation = await get_order_confirmation(symbol, 'SELL', quantity, 'MARKET', current_user, db)
        
        if not confirmation['data']['can_place_order']:
            return {
                'success': False,
                'data': confirmation['data'],
                'message': 'Cannot place order - validation failed'
            }
        
        # Place the order
        order_data = {
            'symbol': symbol,
            'quantity': quantity,
            'order_type': 'MARKET',
            'signal_strength': 'MODERATE',
            'confidence_score': 0.5
        }
        
        result = await real_time_order_service.place_sell_order_market_price(
            symbol=symbol,
            quantity=quantity,
            user_id=current_user.id,
            db=db,
            **order_data
        )
        
        return {
            'success': True,
            'data': result,
            'message': f'Quick SELL order placed for {symbol}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place quick sell order: {str(e)}")

@router.get("/price-alerts")
async def get_price_alerts(
    symbols: List[str] = Query(..., description="Symbols to monitor"),
    current_user: User = Depends(get_current_active_user)
):
    """Get price alerts for monitored symbols"""
    try:
        # Get current prices
        prices = await market_price_service.get_multiple_prices(symbols)
        
        # Generate alerts
        alerts = []
        for symbol, price_data in prices.items():
            change_percent = price_data.get('change_percent', 0)
            
            # Generate alerts based on price movement
            if change_percent > 5:
                alerts.append({
                    'symbol': symbol,
                    'type': 'PRICE_UP',
                    'message': f'{symbol} is up {change_percent:.2f}%',
                    'current_price': price_data['current_price'],
                    'change_percent': change_percent,
                    'severity': 'HIGH' if change_percent > 10 else 'MEDIUM'
                })
            elif change_percent < -5:
                alerts.append({
                    'symbol': symbol,
                    'type': 'PRICE_DOWN',
                    'message': f'{symbol} is down {abs(change_percent):.2f}%',
                    'current_price': price_data['current_price'],
                    'change_percent': change_percent,
                    'severity': 'HIGH' if abs(change_percent) > 10 else 'MEDIUM'
                })
        
        return {
            'success': True,
            'data': {
                'alerts': alerts,
                'total_alerts': len(alerts),
                'monitored_symbols': symbols,
                'generated_at': datetime.utcnow().isoformat()
            },
            'message': f'Price alerts for {len(symbols)} symbols'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price alerts: {str(e)}")
