"""
Trading API routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from core.database_unified import get_db, Portfolio, Order, User, Position
from core.auth_dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class OrderRequest(BaseModel):
    symbol: str
    order_type: str  # BUY, SELL
    quantity: int
    price: Optional[float] = None  # Optional for MARKET orders, required for LIMIT
    order_side: str = "MARKET"  # MARKET, LIMIT, STOP
    is_demo: bool = True  # Default to demo/paper trading mode

class PortfolioResponse(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_percentage: float
    total_value: float

@router.get("/portfolio")
async def get_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: This endpoint is deprecated. Use /api/portfolio-allocation/holdings instead.
    Get user portfolio with live price updates
    """
    try:
        # Redirect to new unified service
        from services.portfolio_allocation_service import portfolio_allocation_service
        
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.get_holdings(user_id, db)
        
        # Return in old format for backward compatibility
        return {
            "success": True,
            "portfolio": result.get("holdings", []),
            "total_value": result.get("total_value", 0.0),
            "total_pnl": result.get("total_pnl", 0.0),
            "currency": "INR",
            "currency_symbol": "₹",
            "formatted_total_value": result.get("formatted_total_value", "₹0.00"),
            "formatted_total_pnl": result.get("formatted_total_pnl", "₹0.00"),
            "last_updated": result.get("last_updated", datetime.now().isoformat()),
            "deprecated": True,
            "message": "This endpoint is deprecated. Please use /api/portfolio-allocation/holdings"
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")

@router.get("/orders")
async def get_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/real orders"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    order_type: Optional[str] = Query(None, description="Filter by order type (BUY/SELL)"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """Get user orders with filtering and pagination"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        query = db.query(Order).filter(Order.user_id == user_id)
        
        # Apply filters
        if is_demo is not None:
            query = query.filter(Order.is_demo == is_demo)
        if order_type:
            query = query.filter(Order.order_type == order_type.upper())
        if symbol:
            query = query.filter(Order.symbol == symbol.upper())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        orders = query.order_by(Order.order_time.desc()).offset(offset).limit(limit).all()
        
        orders_data = []
        for order in orders:
            # Safely get execution_time if it exists
            execution_time = None
            if hasattr(order, 'execution_time') and getattr(order, 'execution_time', None):
                try:
                    execution_time = order.execution_time.isoformat()
                except:
                    execution_time = None
            
            # Get order_side if it exists, otherwise default based on order_type or MARKET
            order_side = getattr(order, 'order_side', None)
            if not order_side:
                # Try to infer from other fields or default to MARKET
                order_side = 'MARKET'
            
            orders_data.append({
                "id": order.id,
                "symbol": order.symbol,
                "order_type": order.order_type,
                "order_side": order_side,
                "quantity": order.quantity,
                "price": float(order.price) if order.price else 0.0,
                "order_status": order.order_status,
                "created_at": order.order_time.isoformat() if order.order_time else None,
                "order_time": order.order_time.isoformat() if order.order_time else None,
                "execution_time": execution_time,
                "filled_time": order.filled_time.isoformat() if order.filled_time else None,
                "filled_price": float(order.filled_price) if order.filled_price else None,
                "is_demo": getattr(order, 'is_demo', True),
                "total_value": float(order.quantity * order.price) if order.price else 0.0
            })
            
        return {
            "orders": orders_data,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

@router.post("/place-order")
async def place_order(
    order_request: OrderRequest, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Place a new order (supports demo/paper trading)"""
    try:
        # Log incoming request for debugging
        logger.info(f"Place order request: symbol={order_request.symbol}, type={order_request.order_type}, "
                   f"quantity={order_request.quantity}, price={order_request.price}, "
                   f"order_side={order_request.order_side}, is_demo={order_request.is_demo}")
        
        # Validate order data
        if order_request.quantity <= 0:
            logger.warning(f"Invalid quantity: {order_request.quantity}")
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        # Validate symbol
        if not order_request.symbol or not order_request.symbol.strip():
            logger.warning(f"Invalid symbol: {order_request.symbol}")
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Validate order_type
        if order_request.order_type not in ["BUY", "SELL"]:
            logger.warning(f"Invalid order_type: {order_request.order_type}")
            raise HTTPException(status_code=400, detail="Order type must be BUY or SELL")
        
        # Validate order_side
        if order_request.order_side not in ["MARKET", "LIMIT", "STOP"]:
            logger.warning(f"Invalid order_side: {order_request.order_side}")
            raise HTTPException(status_code=400, detail="Order side must be MARKET, LIMIT, or STOP")
        
        # Fetch current market price
        market_price = None
        execution_price = None

        # Try multiple methods to get current price
        try:
            from services.data_fetcher import fetch_historical_data
            # Use a wider window to survive weekends/holidays (days=1 can easily return empty)
            candles = await fetch_historical_data(order_request.symbol, timeframe="1d", days=7)
            if candles and len(candles) > 0:
                market_price = float(candles[-1].get('close', 0))
        except Exception as e:
            logger.warning(f"Could not fetch price from data_fetcher: {e}")

        if not market_price or market_price <= 0:
            try:
                from core.data_service import data_service
                quote = await data_service.get_quote(order_request.symbol.upper(), exchange="NSE")
                if quote and quote.get("last_price"):
                    market_price = float(quote.get("last_price"))
            except Exception as quote_error:
                logger.warning(f"Could not fetch price from data_service: {quote_error}")
        
        # Determine execution price based on order_side
        if order_request.order_side == "MARKET":
            # For MARKET orders, use current market price
            if not market_price or market_price <= 0:
                # Demo/paper trading fallback: allow provided price when live market price is unavailable
                if order_request.is_demo and order_request.price and order_request.price > 0:
                    execution_price = float(order_request.price)
                    logger.warning(
                        f"MARKET demo order fallback: Using provided price ₹{execution_price:.2f} for {order_request.symbol} "
                        f"because market price could not be fetched"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Unable to fetch current market price for {order_request.symbol}. "
                            "Please try again during market hours or use LIMIT order."
                        )
                    )
            else:
                execution_price = market_price
                logger.info(f"MARKET order: Using current market price ₹{execution_price:.2f} for {order_request.symbol}")
        elif order_request.order_side == "LIMIT":
            # For LIMIT orders, price is required
            if not order_request.price or order_request.price <= 0:
                raise HTTPException(status_code=400, detail="Limit price is required and must be greater than 0 for LIMIT orders")
            execution_price = order_request.price
            logger.info(f"LIMIT order: Using limit price ₹{execution_price:.2f} for {order_request.symbol}")
        else:
            # Default to market price if order_side is not recognized
            if not market_price or market_price <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unable to determine execution price for {order_request.symbol}"
                )
            execution_price = market_price
        
        # Price validation for LIMIT orders: Check deviation from market price
        if order_request.order_side == "LIMIT" and market_price and market_price > 0:
            max_deviation = 0.10 if order_request.is_demo else 0.05
            price_deviation = abs(execution_price - market_price) / market_price
            if price_deviation > max_deviation:
                logger.warning(
                    f"Price deviation {price_deviation*100:.2f}% exceeds limit. "
                    f"Market: ₹{market_price:.2f}, Order: ₹{execution_price:.2f}"
                )
                # For demo, allow but warn. For real, reject.
                if not order_request.is_demo:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Price deviation too high. Market price: ₹{market_price:.2f}, Order price: ₹{execution_price:.2f}"
                    )
        
        # Get user_id - handle both dict and object
        user_id = None
        try:
            if hasattr(current_user, 'id'):
                user_id = current_user.id
            elif isinstance(current_user, dict):
                user_id = current_user.get('id')
            else:
                logger.error(f"Unexpected current_user type: {type(current_user)}, value: {current_user}")
        except Exception as e:
            logger.error(f"Error extracting user_id: {e}")
        
        if not user_id:
            logger.error(f"Invalid user - user_id is None. current_user type: {type(current_user)}, value: {current_user}")
            raise HTTPException(status_code=400, detail="Invalid user: Unable to determine user ID. Please login again.")
        
        # Fetch actual User object from database to get cash balances
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Cash balance validation for BUY orders
        if order_request.order_type == "BUY":
            total_cost = order_request.quantity * execution_price
            if order_request.is_demo:
                # Get demo cash balance from database
                demo_balance = float(db_user.demo_cash_balance) if db_user.demo_cash_balance is not None else 1000000.0
                
                if demo_balance < total_cost:
                    logger.info(f"Demo order exceeds balance. Required: ₹{total_cost:.2f}, Available: ₹{demo_balance:.2f}")
                    # For demo, allow but track the balance
                    db_user.demo_cash_balance = 0.0
                else:
                    db_user.demo_cash_balance = demo_balance - total_cost
            else:
                # Real order - check real cash balance from database
                real_balance = float(db_user.real_cash_balance) if db_user.real_cash_balance is not None else 0.0
                
                if real_balance < total_cost:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient funds. Required: ₹{total_cost:.2f}, Available: ₹{real_balance:.2f}"
                    )
                
                db_user.real_cash_balance = real_balance - total_cost
        
        # Create new order
        new_order = Order(
            user_id=user_id,
            symbol=order_request.symbol.upper(),
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=execution_price,  # Use execution_price (market or limit)
            order_status="PENDING",
            is_demo=order_request.is_demo
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        # Simulate order execution (in real implementation, this would integrate with broker API)
        if order_request.order_side == "MARKET":
            # MARKET orders execute immediately at current market price
            new_order.order_status = "EXECUTED"
            new_order.execution_time = datetime.utcnow()
            new_order.filled_time = datetime.utcnow()
            new_order.filled_price = execution_price
            
            # Create/update position for executed order (like Sensibull)
            try:
                from services.position_service import position_service
                
                if order_request.order_type == "BUY":
                    await position_service.add_to_position(
                        db=db,
                        user_id=user_id,
                        symbol=order_request.symbol.upper(),
                        instrument_type="EQUITY",
                        quantity=order_request.quantity,
                        price=execution_price,
                        lot_size=1,
                        is_demo=order_request.is_demo
                    )
                else:  # SELL
                    # For sell, reduce position (find and reduce existing position)
                    positions = await position_service.get_user_positions(
                        db=db,
                        user_id=user_id,
                        is_demo=order_request.is_demo
                    )
                    matching_positions = [p for p in positions if p.symbol == order_request.symbol.upper() and p.instrument_type == "EQUITY"]
                    if matching_positions:
                        await position_service.reduce_position(
                            db=db,
                            position_id=matching_positions[0].id,
                            quantity=order_request.quantity
                        )
            except Exception as position_error:
                logger.warning(f"Could not create/update position: {position_error}. Order still placed.")
            
            # Update portfolio using portfolio allocation service
            try:
                from services.portfolio_allocation_service import portfolio_allocation_service
                order_data = {
                    "symbol": order_request.symbol.upper(),
                    "order_type": order_request.order_type,
                    "quantity": order_request.quantity,
                    "price": execution_price
                }
                await portfolio_allocation_service.update_portfolio_on_order(user_id, order_data, db)
            except Exception as portfolio_error:
                logger.warning(f"Could not update portfolio: {portfolio_error}. Order still placed.")
                # Continue even if portfolio update fails
            
            # For SELL orders, add cash back
            if order_request.order_type == "SELL":
                proceeds = order_request.quantity * execution_price
                if order_request.is_demo:
                    current_balance = float(db_user.demo_cash_balance) if db_user.demo_cash_balance is not None else 1000000.0
                    db_user.demo_cash_balance = current_balance + proceeds
                else:
                    current_balance = float(db_user.real_cash_balance) if db_user.real_cash_balance is not None else 0.0
                    db_user.real_cash_balance = current_balance + proceeds
        elif order_request.order_side == "LIMIT":
            # LIMIT orders stay PENDING until price reaches limit
            # In a real system, you would have a background job checking prices
            # For now, we'll keep it as PENDING and let the user know
            new_order.order_status = "PENDING"
            logger.info(f"LIMIT order {new_order.id} placed for {order_request.symbol} at ₹{execution_price:.2f}. Will execute when price reaches limit.")
            
        db.commit()
        
        order_status_text = "executed" if order_request.order_side == "MARKET" else f"pending (LIMIT @ ₹{execution_price:.2f})"
        
        return {
            "success": True,
            "order_id": new_order.id,
            "status": "success",
            "order_status": new_order.order_status,
            "message": f"{'Demo' if order_request.is_demo else 'Real'} {order_request.order_side} order placed successfully for {order_request.quantity} shares of {order_request.symbol} at ₹{execution_price:.2f}. Status: {order_status_text}",
            "is_demo": order_request.is_demo,
            "execution_price": execution_price,
            "remaining_balance": (
                float(db_user.demo_cash_balance) if db_user.demo_cash_balance is not None else 1000000.0
                if order_request.is_demo
                else float(db_user.real_cash_balance) if db_user.real_cash_balance is not None else 0.0
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error placing order: {str(e)}")

@router.delete("/cancel-order/{order_id}")
async def cancel_order(
    order_id: int, 
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel an order"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        order = db.query(Order).filter(
            Order.id == order_id, 
            Order.user_id == user_id,
            Order.order_status == "PENDING"
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
            
        order.order_status = "CANCELLED"
        db.commit()
        
        return {
            "order_id": order_id,
            "status": "cancelled",
            "message": "Order cancelled successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")

# DEPRECATED: update_portfolio function moved to portfolio_allocation_service
# This function is kept for backward compatibility but redirects to the service
async def update_portfolio(user_id: int, order_request: OrderRequest, db: Session):
    """DEPRECATED: Update portfolio after order execution - now uses portfolio_allocation_service"""
    try:
        from services.portfolio_allocation_service import portfolio_allocation_service
        
        order_data = {
            "symbol": order_request.symbol,
            "order_type": order_request.order_type,
            "quantity": order_request.quantity,
            "price": order_request.price
        }
        
        result = await portfolio_allocation_service.update_portfolio_on_order(user_id, order_data, db)
        
        if not result.get("success"):
            logger.warning(f"Portfolio update failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error updating portfolio: {e}")
        db.rollback()

# Technical Analysis Routes
@router.get("/technical-indicators")
async def get_technical_indicators(
    symbol: str = "NIFTY",
    current_user: User = Depends(get_current_active_user)
):
    """Get technical indicators for trading analysis"""
    try:
        # Mock data for now - replace with real implementation
        indicators = {
            "symbol": symbol,
            "sma_20": 150.25,
            "sma_50": 148.75,
            "ema_12": 151.00,
            "rsi": 65.5,
            "macd": 2.15,
            "timestamp": datetime.now().isoformat()
        }
        return {"success": True, "data": indicators}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting technical indicators: {str(e)}")

@router.get("/candlestick-patterns")
async def get_candlestick_patterns(
    symbol: str = "NIFTY",
    current_user: User = Depends(get_current_active_user)
):
    """Get candlestick pattern analysis"""
    try:
        # Mock data for now - replace with real implementation
        patterns = {
            "symbol": symbol,
            "doji": {"count": 3, "significance": "high"},
            "hammer": {"count": 2, "significance": "medium"},
            "engulfing": {"count": 1, "significance": "high"},
            "timestamp": datetime.now().isoformat()
        }
        return {"success": True, "data": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting candlestick patterns: {str(e)}")

@router.get("/signals")
async def get_trading_signals(
    current_user: User = Depends(get_current_active_user)
):
    """Get trading signals and recommendations"""
    try:
        # Mock data for now - replace with real implementation
        signals = {
            "buy_signals": [
                {"symbol": "AAPL", "strength": "strong", "reason": "RSI oversold"},
                {"symbol": "GOOGL", "strength": "medium", "reason": "Golden cross"}
            ],
            "sell_signals": [
                {"symbol": "TSLA", "strength": "weak", "reason": "Resistance level"}
            ],
            "timestamp": datetime.now().isoformat()
        }
        return {"success": True, "data": signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trading signals: {str(e)}")

# Auto-generated endpoints for frontend compatibility

@router.get("/analytics/overview")
async def analytics_overview(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get portfolio analytics overview"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        # Get user's portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        
        if not portfolio:
            return {
                "success": True,
                "data": {
                    "total_value": 0,
                    "total_pnl": 0,
                    "total_pnl_percent": 0,
                    "positions_count": 0,
                    "active_orders": 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get active orders count
        active_orders = db.query(Order).filter(
            Order.user_id == user_id,
            Order.order_status == "PENDING"
        ).count()
        
        # Calculate portfolio metrics
        total_value = portfolio.total_value or 0
        total_pnl = portfolio.total_pnl or 0
        total_pnl_percent = (total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total_value": total_value,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "positions_count": len(portfolio.holdings or []),
                "active_orders": active_orders
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in analytics_overview: {str(e)}")


@router.get("/analytics/performance")
async def analytics_performance():
    """Auto-generated endpoint for Analytics component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /analytics/performance is working",
            "data": {},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in analytics_performance: {str(e)}")


# ==================== ARPIT EDUCATION ENDPOINTS (COMMENTED OUT - KEEPING FOR FUTURE USE) ====================

# @router.get("/arpit-education/lessons")
# async def arpit_education_lessons():
#     """Auto-generated endpoint for api component"""
#     try:
#         # TODO: Implement actual logic
#         return {
#             "success": True,
#             "message": "Endpoint /arpit-education/lessons is working",
#             "data": {},
#             "timestamp": datetime.now().isoformat()
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error in arpit_education_lessons: {str(e)}")


# @router.get("/arpit-education/progress")
# async def arpit_education_progress():
#     """Auto-generated endpoint for api component"""
#     try:
#         # TODO: Implement actual logic
#         return {
#             "success": True,
#             "message": "Endpoint /arpit-education/progress is working",
#             "data": {},
#             "timestamp": datetime.now().isoformat()
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error in arpit_education_progress: {str(e)}")


# @router.get("/arpit-education/certificates")
# async def arpit_education_certificates():
#     """Auto-generated endpoint for api component"""
#     try:
#         # TODO: Implement actual logic
#         return {
#             "success": True,
#             "message": "Endpoint /arpit-education/certificates is working",
#             "data": {},
#             "timestamp": datetime.now().isoformat()
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error in arpit_education_certificates: {str(e)}")


@router.get("/intelligent-trading/sector-rotation")
async def intelligent_trading_sector_rotation():
    """Get sector rotation analysis"""
    try:
        # Basic sector rotation data
        # In production, this would analyze actual market data
        sectors = {
            "IT": {"trend": "bullish", "strength": 0.75},
            "Banking": {"trend": "neutral", "strength": 0.50},
            "FMCG": {"trend": "bullish", "strength": 0.65},
            "Pharma": {"trend": "bearish", "strength": 0.40},
            "Energy": {"trend": "bullish", "strength": 0.70}
        }
        
        return {
            "success": True,
            "data": {
                "sectors": sectors,
                "top_sector": "IT",
                "bottom_sector": "Pharma"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in intelligent_trading_sector_rotation: {str(e)}")


@router.get("/intelligent-trading/market-timing")
async def intelligent_trading_market_timing():
    """Get market timing indicators"""
    try:
        # Basic market timing indicators
        # In production, this would use actual market data
        return {
            "success": True,
            "data": {
                "market_phase": "bullish",
                "volatility": "medium",
                "trend_strength": 0.65,
                "support_level": 18000,
                "resistance_level": 20000,
                "recommendation": "moderate_buy"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in intelligent_trading_market_timing: {str(e)}")


@router.get("/intelligent-trading/market-overview")
async def intelligent_trading_market_overview():
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /intelligent-trading/market-overview is working",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in intelligent_trading_market_overview: {str(e)}")


@router.get("/portfolio-allocation/allocation-strategies")
async def portfolio_allocation_allocation_strategies():
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /portfolio-allocation/allocation-strategies is working",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in portfolio_allocation_allocation_strategies: {str(e)}")


@router.get("/portfolio-allocation/rebalancing-triggers")
async def portfolio_allocation_rebalancing_triggers():
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /portfolio-allocation/rebalancing-triggers is working",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in portfolio_allocation_rebalancing_triggers: {str(e)}")


@router.get("/portfolio-allocation/market-insights")
async def portfolio_allocation_market_insights():
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /portfolio-allocation/market-insights is working",
            "data": {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in portfolio_allocation_market_insights: {str(e)}")


@router.post("/intelligent-trading/stock-recommendations")
async def intelligent_trading_stock_recommendations(request_data: dict = None):
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /intelligent-trading/stock-recommendations is working",
            "data": request_data or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in intelligent_trading_stock_recommendations: {str(e)}")


@router.post("/intelligent-trading/custom-scan")
async def intelligent_trading_custom_scan(request_data: dict = None):
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /intelligent-trading/custom-scan is working",
            "data": request_data or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in intelligent_trading_custom_scan: {str(e)}")


@router.post("/portfolio-allocation/allocation-guidance")
async def portfolio_allocation_allocation_guidance(request_data: dict = None):
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /portfolio-allocation/allocation-guidance is working",
            "data": request_data or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in portfolio_allocation_allocation_guidance: {str(e)}")


@router.post("/portfolio-allocation/rebalancing-recommendations")
async def portfolio_allocation_rebalancing_recommendations(request_data: dict = None):
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /portfolio-allocation/rebalancing-recommendations is working",
            "data": request_data or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in portfolio_allocation_rebalancing_recommendations: {str(e)}")


@router.post("/portfolio-allocation/create-dca-plan")
async def portfolio_allocation_create_dca_plan(request_data: dict = None):
    """Auto-generated endpoint for api component"""
    try:
        # TODO: Implement actual logic
        return {
            "success": True,
            "message": "Endpoint /portfolio-allocation/create-dca-plan is working",
            "data": request_data or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in portfolio_allocation_create_dca_plan: {str(e)}")


@router.get("/positions")
async def get_positions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    is_demo: Optional[bool] = Query(None, description="Filter by demo/real positions"),
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID")
):
    """Get user's current positions (similar to Sensibull)"""
    try:
        from services.position_service import position_service
        
        user_id = current_user.id if isinstance(current_user, User) else current_user.get("id")
        
        positions = await position_service.get_user_positions(
            db=db,
            user_id=user_id,
            is_demo=is_demo,
            strategy_id=strategy_id
        )
        
        # Format positions for response
        formatted_positions = []
        total_value = 0.0
        total_pnl = 0.0
        
        for pos in positions:
            formatted_pos = {
                "id": pos.id,
                "symbol": pos.symbol,
                "instrumentType": pos.instrument_type,
                "quantity": pos.quantity,
                "lotSize": pos.lot_size,
                "totalQuantity": pos.quantity * pos.lot_size,
                "averagePrice": float(pos.average_price),
                "currentPrice": float(pos.current_price),
                "investedValue": float(pos.invested_value),
                "currentValue": float(pos.current_value),
                "unrealizedPnl": float(pos.unrealized_pnl),
                "unrealizedPnlPercent": float(pos.unrealized_pnl_percent),
                "strikePrice": float(pos.strike_price) if pos.strike_price else None,
                "expiryDate": pos.expiry_date.isoformat() if pos.expiry_date else None,
                "optionType": pos.option_type,
                "strategyId": pos.strategy_id,
                "strategyName": pos.strategy_name,
                "legId": pos.leg_id,
                "delta": float(pos.delta) if pos.delta else None,
                "gamma": float(pos.gamma) if pos.gamma else None,
                "theta": float(pos.theta) if pos.theta else None,
                "vega": float(pos.vega) if pos.vega else None,
                "isDemo": pos.is_demo,
                "entryTime": pos.entry_time.isoformat() if pos.entry_time else None,
                "updatedAt": pos.updated_at.isoformat() if pos.updated_at else None
            }
            formatted_positions.append(formatted_pos)
            total_value += float(pos.current_value)
            total_pnl += float(pos.unrealized_pnl)
        
        return {
            "success": True,
            "data": {
                "positions": formatted_positions,
                "totalValue": total_value,
                "totalPnl": total_pnl,
                "totalPnlPercent": (total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) > 0 else 0.0,
                "count": len(formatted_positions)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")

class StrategyLegRequest(BaseModel):
    id: Optional[str] = None
    action: str  # BUY or SELL
    instrument: str  # EQUITY, CE, PE, FUT
    expiry: Optional[str] = None
    strike: Optional[float] = None
    quantity: int
    price: float
    lotSize: int = 50

class ExecuteStrategyRequest(BaseModel):
    strategy_name: str
    symbol: str
    legs: List[StrategyLegRequest]
    is_demo: bool = True

@router.post("/execute-strategy")
async def execute_strategy(
    request: ExecuteStrategyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute a multi-leg strategy trade and create positions (like Sensibull)"""
    try:
        from services.position_service import position_service
        from datetime import datetime as dt
        
        user_id = current_user.id if isinstance(current_user, User) else current_user.get("id")
        
        # Convert legs to format expected by position service
        legs_data = []
        for leg in request.legs:
            expiry_date = None
            if leg.expiry:
                try:
                    # Try parsing various date formats
                    expiry_date = dt.strptime(leg.expiry, "%d %b")  # "30 Dec"
                    expiry_date = expiry_date.replace(year=dt.now().year)
                    if expiry_date < dt.now():
                        expiry_date = expiry_date.replace(year=dt.now().year + 1)
                except:
                    try:
                        expiry_date = dt.fromisoformat(leg.expiry.replace('Z', '+00:00'))
                    except:
                        logger.warning(f"Could not parse expiry date: {leg.expiry}")
            
            # For SELL positions, use negative quantity (not negative price)
            # Price should always be positive - direction is tracked via quantity sign
            leg_quantity = leg.quantity if leg.action == "BUY" else -leg.quantity
            
            leg_data = {
                "id": leg.id,
                "instrument": leg.instrument,
                "quantity": leg_quantity,  # Negative for SELL (short), positive for BUY (long)
                "price": leg.price,  # Always positive - direction tracked via quantity sign
                "lotSize": leg.lotSize,
                "strike": leg.strike,
                "expiry": expiry_date,
                "action": leg.action  # Store action for reference
            }
            legs_data.append(leg_data)
        
        # Execute strategy trade
        positions = await position_service.execute_strategy_trade(
            db=db,
            user_id=user_id,
            strategy_name=request.strategy_name,
            symbol=request.symbol.upper(),
            legs=legs_data,
            is_demo=request.is_demo
        )
        
        # Format response
        formatted_positions = []
        total_premium = 0.0
        
        for pos in positions:
            formatted_pos = {
                "id": pos.id,
                "symbol": pos.symbol,
                "instrumentType": pos.instrument_type,
                "quantity": pos.quantity,
                "averagePrice": float(pos.average_price),
                "currentPrice": float(pos.current_price),
                "unrealizedPnl": float(pos.unrealized_pnl),
                "strategyId": pos.strategy_id,
                "legId": pos.leg_id
            }
            formatted_positions.append(formatted_pos)
            total_premium += abs(float(pos.invested_value))
        
        return {
            "success": True,
            "message": f"Strategy '{request.strategy_name}' executed successfully",
            "strategyId": positions[0].strategy_id if positions else None,
            "positions": formatted_positions,
            "totalPremium": total_premium,
            "legsCount": len(positions)
        }
        
    except Exception as e:
        logger.error(f"Error executing strategy: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error executing strategy: {str(e)}")
