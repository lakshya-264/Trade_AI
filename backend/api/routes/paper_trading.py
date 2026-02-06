"""
Paper Trading API Routes
Virtual trading accounts for strategy testing and practice
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from core.database import get_db
from core.auth_dependencies import get_current_user
from core.database_unified import PaperAccount, PaperOrder, PaperPosition

logger = logging.getLogger(__name__)
router = APIRouter()

class PaperAccountCreate(BaseModel):
    """Create paper trading account"""
    account_name: str = Field(..., description="Account name")
    initial_capital: float = Field(100000, description="Initial capital in ₹")

class PaperOrderRequest(BaseModel):
    """Place paper trading order"""
    symbol: str = Field(..., description="Stock symbol")
    order_type: str = Field(..., description="Order type: MARKET, LIMIT, SL, SL_LIMIT")
    side: str = Field(..., description="BUY or SELL")
    quantity: int = Field(..., description="Number of shares")
    price: Optional[float] = Field(None, description="Limit price (for LIMIT orders)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    target: Optional[float] = Field(None, description="Target price")

class PaperOrderCancel(BaseModel):
    """Cancel paper trading order"""
    order_id: str = Field(..., description="Order ID")

@router.post("/account/create")
async def create_paper_account(
    account: PaperAccountCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new paper trading account"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        username = current_user.get('username', 'unknown')
        
        logger.info(f"Creating paper account for user_id={user_id}, username={username}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Ensure user_id is an integer for consistency
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id type: {type(user_id)}, value: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Generate unique account_id
        account_id = f"{user_id}_{account.account_name}_{int(datetime.now().timestamp())}"
        
        # Check if account_id already exists
        existing = db.query(PaperAccount).filter(PaperAccount.account_id == account_id).first()
        if existing:
            account_id = f"{account_id}_{int(datetime.now().timestamp())}"
        
        # Create new paper account in database
        paper_account = PaperAccount(
            account_id=account_id,
            user_id=user_id,
            account_name=account.account_name,
            initial_capital=float(account.initial_capital),
            available_capital=float(account.initial_capital),
            invested_capital=0.0,
            current_value=float(account.initial_capital),
            total_pnl=0.0,
            total_pnl_percent=0.0,
            is_active=True
        )
        
        db.add(paper_account)
        db.commit()
        db.refresh(paper_account)
        
        logger.info(f"Created paper account {account_id} for user {user_id}")
        
        return {
            "success": True,
            "account_id": account_id,
            "account": {
                "account_id": paper_account.account_id,
                "user_id": paper_account.user_id,
                "account_name": paper_account.account_name,
                "initial_capital": float(paper_account.initial_capital),
                "available_capital": float(paper_account.available_capital),
                "invested_capital": float(paper_account.invested_capital),
                "current_value": float(paper_account.current_value),
                "total_pnl": float(paper_account.total_pnl),
                "total_pnl_percent": float(paper_account.total_pnl_percent),
                "created_at": paper_account.created_at.isoformat() if paper_account.created_at else None,
                "updated_at": paper_account.updated_at.isoformat() if paper_account.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating paper account: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/list")
async def list_paper_accounts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all paper trading accounts for current user"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        username = current_user.get('username', 'unknown')
        
        # Ensure user_id is an integer for consistency
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id type: {type(user_id)}, value: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        logger.info(f"Listing paper accounts for user_id={user_id}, username={username}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Query database for user's accounts - ensure user_id comparison is consistent
        db_accounts = db.query(PaperAccount).filter(
            PaperAccount.user_id == user_id,
            PaperAccount.is_active == True
        ).all()
        
        logger.info(f"Found {len(db_accounts)} accounts for user_id={user_id}")
        
        user_accounts = []
        for acc in db_accounts:
            try:
                user_accounts.append({
                    "account_id": acc.account_id if hasattr(acc, 'account_id') else str(acc.id),
                    "id": acc.id,
                    "user_id": acc.user_id,
                    "account_name": acc.account_name,
                    "initial_capital": float(acc.initial_capital),
                    "available_capital": float(acc.available_capital),
                    "invested_capital": float(acc.invested_capital),
                    "current_value": float(acc.current_value),
                    "total_pnl": float(acc.total_pnl),
                    "total_pnl_percent": float(acc.total_pnl_percent),
                    "created_at": acc.created_at.isoformat() if acc.created_at else None,
                    "updated_at": acc.updated_at.isoformat() if acc.updated_at else None
                })
            except Exception as e:
                logger.error(f"Error processing account {acc.id}: {e}")
                continue
        
        return {
            "success": True,
            "accounts": user_accounts
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing paper accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/{account_id}")
async def get_paper_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paper trading account details"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        username = current_user.get('username', 'unknown')
        
        # Ensure user_id is an integer for consistency
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id type: {type(user_id)}, value: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        logger.info(f"Getting account details for user_id={user_id}, username={username}, account_id={account_id}")
        
        # Query database for account
        account = db.query(PaperAccount).filter(
            PaperAccount.account_id == account_id,
            PaperAccount.is_active == True
        ).first()
        
        if not account:
            logger.error(f"Account not found: {account_id}")
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Ensure account.user_id is also an integer for comparison
        account_user_id = int(account.user_id) if account.user_id else None
        
        logger.info(f"Account user_id={account_user_id}, Request user_id={user_id}")
        
        if account_user_id != user_id:
            logger.warning(f"Access denied: Account belongs to user_id={account_user_id}, but request is from user_id={user_id}")
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. This account belongs to a different user."
            )
        
        # Get positions and orders from database
        positions = db.query(PaperPosition).filter(
            PaperPosition.account_id == account_id
        ).all()
        
        orders = db.query(PaperOrder).filter(
            PaperOrder.account_id == account_id
        ).order_by(PaperOrder.created_at.desc()).all()
        
        # Update current value based on positions
        current_value = float(account.available_capital)
        for position in positions:
            current_value += float(position.current_value)
        
        # Update account values
        account.current_value = current_value
        account.total_pnl = current_value - float(account.initial_capital)
        account.total_pnl_percent = ((current_value - float(account.initial_capital)) / float(account.initial_capital)) * 100 if float(account.initial_capital) > 0 else 0.0
        account.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "account": {
                "account_id": account.account_id,
                "id": account.id,
                "user_id": account.user_id,
                "account_name": account.account_name,
                "initial_capital": float(account.initial_capital),
                "available_capital": float(account.available_capital),
                "invested_capital": float(account.invested_capital),
                "current_value": float(account.current_value),
                "total_pnl": float(account.total_pnl),
                "total_pnl_percent": float(account.total_pnl_percent),
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "updated_at": account.updated_at.isoformat() if account.updated_at else None
            },
            "positions": [
                {
                    "id": pos.id,
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "average_price": float(pos.average_price),
                    "current_price": float(pos.current_price),
                    "invested_value": float(pos.invested_value),
                    "current_value": float(pos.current_value),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "unrealized_pnl_percent": float(pos.unrealized_pnl_percent),
                    "created_at": pos.created_at.isoformat() if pos.created_at else None,
                    "updated_at": pos.updated_at.isoformat() if pos.updated_at else None
                }
                for pos in positions
            ],
            "orders": [
                {
                    "id": ord.id,
                    "order_id": ord.order_id,
                    "symbol": ord.symbol,
                    "order_type": ord.order_type,
                    "side": ord.side,
                    "quantity": ord.quantity,
                    "price": float(ord.price) if ord.price else None,
                    "stop_loss": float(ord.stop_loss) if ord.stop_loss else None,
                    "target": float(ord.target) if ord.target else None,
                    "status": ord.status,
                    "executed_price": float(ord.executed_price) if ord.executed_price else None,
                    "executed_quantity": ord.executed_quantity,
                    "created_at": ord.created_at.isoformat() if ord.created_at else None,
                    "executed_at": ord.executed_at.isoformat() if ord.executed_at else None,
                    "cancelled_at": ord.cancelled_at.isoformat() if ord.cancelled_at else None
                }
                for ord in orders
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper account: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order/place")
async def place_paper_order(
    order: PaperOrderRequest,
    account_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place a paper trading order"""
    try:
        logger.info(f"Placing paper order: account_id={account_id}, symbol={order.symbol}, side={order.side}, quantity={order.quantity}, order_type={order.order_type}")
        
        # Validate order data
        if not order.symbol or not order.symbol.strip():
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        if order.order_type == "LIMIT" and (not order.price or order.price <= 0):
            raise HTTPException(status_code=400, detail="Limit price is required and must be greater than 0 for LIMIT orders")
        
        user_id = current_user.get('id') or current_user.get('user_id')
        username = current_user.get('username', 'unknown')
        
        # Ensure user_id is an integer for consistency
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id type: {type(user_id)}, value: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        logger.info(f"Placing order for user_id={user_id}, username={username}, account_id={account_id}")
        
        # Query database for account
        account = db.query(PaperAccount).filter(
            PaperAccount.account_id == account_id,
            PaperAccount.is_active == True
        ).first()
        
        if not account:
            logger.error(f"Account not found: {account_id}")
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Ensure account.user_id is also an integer for comparison
        account_user_id = int(account.user_id) if account.user_id else None
        
        logger.info(f"Account user_id={account_user_id}, Request user_id={user_id}")
        
        if account_user_id != user_id:
            logger.warning(f"Access denied: Account belongs to user_id={account_user_id}, but request is from user_id={user_id}")
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. This account belongs to a different user."
            )
        
        # Get current price (simplified - in production, fetch from market data)
        from services.data_fetcher import fetch_historical_data
        candles = await fetch_historical_data(order.symbol, timeframe="1d", days=1)
        current_price = candles[-1]['close'] if candles else order.price or 100.0
        
        # Calculate order value
        if order.order_type == "MARKET":
            execution_price = current_price
        elif order.order_type == "LIMIT":
            if not order.price or order.price <= 0:
                raise HTTPException(status_code=400, detail="Limit price is required and must be greater than 0")
            execution_price = order.price
        else:
            execution_price = current_price
        
        if execution_price <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid execution price: {execution_price}")
        
        order_value = execution_price * order.quantity
        logger.info(f"Order value: {order_value}, Available capital: {account.available_capital}")
        
        # Check if enough capital for BUY orders
        if order.side == "BUY" and float(account.available_capital) < order_value:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient capital. Required: ₹{order_value:.2f}, Available: ₹{float(account.available_capital):.2f}"
            )
        
        # Check if enough quantity for SELL orders
        if order.side == "SELL":
            existing_positions = db.query(PaperPosition).filter(
                PaperPosition.account_id == account_id,
                PaperPosition.symbol == order.symbol
            ).all()
            total_quantity = sum(pos.quantity for pos in existing_positions)
            if total_quantity < order.quantity:
                raise HTTPException(status_code=400, detail="Insufficient quantity")
        
        # Create order in database
        order_id = f"PAPER_{account_id}_{int(datetime.now().timestamp())}"
        paper_order = PaperOrder(
            order_id=order_id,
            account_id=account_id,
            symbol=order.symbol,
            order_type=order.order_type,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            stop_loss=float(order.stop_loss) if order.stop_loss else None,
            target=float(order.target) if order.target else None,
            status="EXECUTED",  # Paper trading executes immediately
            executed_price=execution_price,
            executed_quantity=order.quantity,
            executed_at=datetime.now()
        )
        
        db.add(paper_order)
        
        # Update account
        if order.side == "BUY":
            account.available_capital = float(account.available_capital) - order_value
            account.invested_capital = float(account.invested_capital) + order_value
            
            # Add or update position
            existing_position = db.query(PaperPosition).filter(
                PaperPosition.account_id == account_id,
                PaperPosition.symbol == order.symbol
            ).first()
            
            if existing_position:
                # Update existing position
                total_cost = (float(existing_position.average_price) * existing_position.quantity) + order_value
                total_quantity = existing_position.quantity + order.quantity
                existing_position.quantity = total_quantity
                existing_position.average_price = total_cost / total_quantity
                existing_position.invested_value = total_cost
                existing_position.current_price = current_price
                existing_position.current_value = total_quantity * current_price
                existing_position.unrealized_pnl = existing_position.current_value - existing_position.invested_value
                existing_position.unrealized_pnl_percent = ((existing_position.unrealized_pnl / existing_position.invested_value) * 100) if existing_position.invested_value > 0 else 0.0
                existing_position.updated_at = datetime.now()
            else:
                # Create new position
                new_position = PaperPosition(
                    account_id=account_id,
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_price=execution_price,
                    current_price=current_price,
                    invested_value=order_value,
                    current_value=order.quantity * current_price,
                    unrealized_pnl=0.0,
                    unrealized_pnl_percent=0.0
                )
                db.add(new_position)
        else:  # SELL
            # Remove from position
            remaining_quantity = order.quantity
            positions = db.query(PaperPosition).filter(
                PaperPosition.account_id == account_id,
                PaperPosition.symbol == order.symbol
            ).all()
            
            for position in positions:
                if position.quantity >= remaining_quantity:
                    # Calculate P&L
                    pnl = (execution_price - float(position.average_price)) * remaining_quantity
                    account.available_capital = float(account.available_capital) + order_value
                    account.invested_capital = float(account.invested_capital) - (float(position.average_price) * remaining_quantity)
                    
                    position.quantity -= remaining_quantity
                    if position.quantity == 0:
                        db.delete(position)
                    else:
                        position.invested_value = position.quantity * float(position.average_price)
                        position.current_price = current_price
                        position.current_value = position.quantity * current_price
                        position.unrealized_pnl = position.current_value - position.invested_value
                        position.unrealized_pnl_percent = ((position.unrealized_pnl / position.invested_value) * 100) if position.invested_value > 0 else 0.0
                        position.updated_at = datetime.now()
                    
                    remaining_quantity = 0
                    break
        
        # Update account totals
        account.updated_at = datetime.now()
        account.current_value = float(account.available_capital) + float(account.invested_capital)
        account.total_pnl = account.current_value - float(account.initial_capital)
        account.total_pnl_percent = ((account.total_pnl / float(account.initial_capital)) * 100) if float(account.initial_capital) > 0 else 0.0
        
        db.commit()
        db.refresh(paper_order)
        
        logger.info(f"Placed paper order {order_id} for account {account_id}")
        
        return {
            "success": True,
            "order": {
                "id": paper_order.id,
                "order_id": paper_order.order_id,
                "account_id": paper_order.account_id,
                "symbol": paper_order.symbol,
                "order_type": paper_order.order_type,
                "side": paper_order.side,
                "quantity": paper_order.quantity,
                "price": float(paper_order.price) if paper_order.price else None,
                "stop_loss": float(paper_order.stop_loss) if paper_order.stop_loss else None,
                "target": float(paper_order.target) if paper_order.target else None,
                "status": paper_order.status,
                "executed_price": float(paper_order.executed_price) if paper_order.executed_price else None,
                "executed_quantity": paper_order.executed_quantity,
                "created_at": paper_order.created_at.isoformat() if paper_order.created_at else None,
                "executed_at": paper_order.executed_at.isoformat() if paper_order.executed_at else None
            },
            "account": {
                "account_id": account.account_id,
                "available_capital": float(account.available_capital),
                "invested_capital": float(account.invested_capital),
                "current_value": float(account.current_value),
                "total_pnl": float(account.total_pnl),
                "total_pnl_percent": float(account.total_pnl_percent)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing paper order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order/cancel")
async def cancel_paper_order(
    account_id: str,
    cancel_request: PaperOrderCancel,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a paper trading order"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        
        # Verify account exists and belongs to user
        account = db.query(PaperAccount).filter(
            PaperAccount.account_id == account_id,
            PaperAccount.is_active == True
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if account.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Find order in database
        order = db.query(PaperOrder).filter(
            PaperOrder.order_id == cancel_request.order_id,
            PaperOrder.account_id == account_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != "PENDING":
            raise HTTPException(status_code=400, detail="Can only cancel pending orders")
        
        order.status = "CANCELLED"
        order.cancelled_at = datetime.now()
        
        db.commit()
        db.refresh(order)
        
        return {
            "success": True,
            "order": {
                "id": order.id,
                "order_id": order.order_id,
                "status": order.status,
                "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling paper order: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions/{account_id}")
async def get_paper_positions(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all positions for a paper trading account"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        
        # Verify account exists and belongs to user
        account = db.query(PaperAccount).filter(
            PaperAccount.account_id == account_id,
            PaperAccount.is_active == True
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if account.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get positions from database
        positions = db.query(PaperPosition).filter(
            PaperPosition.account_id == account_id
        ).all()
        
        # Update current values (in production, fetch real-time prices)
        total_pnl = 0.0
        for position in positions:
            # In production, fetch real-time price here
            # For now, use current_price from database
            total_pnl += float(position.unrealized_pnl)
        
        return {
            "success": True,
            "positions": [
                {
                    "id": pos.id,
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "average_price": float(pos.average_price),
                    "current_price": float(pos.current_price),
                    "invested_value": float(pos.invested_value),
                    "current_value": float(pos.current_value),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "unrealized_pnl_percent": float(pos.unrealized_pnl_percent),
                    "created_at": pos.created_at.isoformat() if pos.created_at else None,
                    "updated_at": pos.updated_at.isoformat() if pos.updated_at else None
                }
                for pos in positions
            ],
            "total_pnl": total_pnl
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper positions: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{account_id}")
async def get_paper_orders(
    account_id: str,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all orders for a paper trading account"""
    try:
        user_id = current_user.get('id') or current_user.get('user_id')
        
        # Verify account exists and belongs to user
        account = db.query(PaperAccount).filter(
            PaperAccount.account_id == account_id,
            PaperAccount.is_active == True
        ).first()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if account.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get orders from database
        query = db.query(PaperOrder).filter(PaperOrder.account_id == account_id)
        
        if status:
            query = query.filter(PaperOrder.status == status)
        
        orders = query.order_by(PaperOrder.created_at.desc()).all()
        
        return {
            "success": True,
            "orders": [
                {
                    "id": ord.id,
                    "order_id": ord.order_id,
                    "account_id": ord.account_id,
                    "symbol": ord.symbol,
                    "order_type": ord.order_type,
                    "side": ord.side,
                    "quantity": ord.quantity,
                    "price": float(ord.price) if ord.price else None,
                    "stop_loss": float(ord.stop_loss) if ord.stop_loss else None,
                    "target": float(ord.target) if ord.target else None,
                    "status": ord.status,
                    "executed_price": float(ord.executed_price) if ord.executed_price else None,
                    "executed_quantity": ord.executed_quantity,
                    "created_at": ord.created_at.isoformat() if ord.created_at else None,
                    "executed_at": ord.executed_at.isoformat() if ord.executed_at else None,
                    "cancelled_at": ord.cancelled_at.isoformat() if ord.cancelled_at else None
                }
                for ord in orders
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper orders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

