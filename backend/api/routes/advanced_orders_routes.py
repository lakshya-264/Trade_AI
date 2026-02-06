"""
Advanced Order Management API Routes
Bracket orders, OCO orders, position sizing, trade journal
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from core.database import get_db
from core.auth_dependencies import get_current_user
from services.advanced_order_management import advanced_order_management

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/advanced-orders", tags=["Advanced Orders"])

class BracketOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: int
    entry_price: float
    stop_loss: float
    target: float

class OCOOrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    price1: float
    price2: float

class PositionSizeRequest(BaseModel):
    account_balance: float
    risk_per_trade: float
    entry_price: float
    stop_loss_price: float

class TradeJournalRequest(BaseModel):
    symbol: str
    entry_price: float
    exit_price: float
    quantity: int
    side: str
    entry_time: datetime
    exit_time: datetime
    notes: Optional[str] = None

@router.post("/bracket")
async def create_bracket_order(
    order: BracketOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create bracket order"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        result = await advanced_order_management.create_bracket_order(
            user_id=user_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            entry_price=order.entry_price,
            stop_loss=order.stop_loss,
            target=order.target,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error creating bracket order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/oco")
async def create_oco_order(
    order: OCOOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create OCO order"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        result = await advanced_order_management.create_oco_order(
            user_id=user_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price1=order.price1,
            price2=order.price2,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error creating OCO order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/position-size")
async def calculate_position_size(
    request: PositionSizeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate position size based on risk"""
    try:
        result = advanced_order_management.calculate_position_size(
            account_balance=request.account_balance,
            risk_per_trade=request.risk_per_trade,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/journal/add")
async def add_trade_to_journal(
    trade: TradeJournalRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add trade to journal"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        result = await advanced_order_management.add_trade_to_journal(
            user_id=user_id,
            symbol=trade.symbol,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            quantity=trade.quantity,
            side=trade.side,
            entry_time=trade.entry_time,
            exit_time=trade.exit_time,
            notes=trade.notes,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error adding trade to journal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

