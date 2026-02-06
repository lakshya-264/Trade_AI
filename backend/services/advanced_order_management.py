"""
Advanced Order Management Service
Bracket orders, OCO orders, OMS integration, position sizing, trade journal
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session
import uuid

logger = logging.getLogger(__name__)

class AdvancedOrderManagement:
    """Advanced order management system"""
    
    def __init__(self):
        self.order_cache = {}  # Cache for performance
    
    async def create_bracket_order(
        self,
        user_id: int,
        symbol: str,
        side: str,  # BUY or SELL
        quantity: int,
        entry_price: float,
        stop_loss: float,
        target: float,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create bracket order (entry + stop loss + target)"""
        try:
            from core.database_unified import BracketOrder
            
            order_id = str(uuid.uuid4())
            
            bracket_order = BracketOrder(
                id=order_id,
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                status="PENDING",
                created_at=datetime.now()
            )
            
            db.add(bracket_order)
            db.commit()
            
            logger.info(f"Bracket order created: {order_id}")
            
            return {
                "success": True,
                "order_id": order_id,
                "order": self._format_bracket_order(bracket_order)
            }
            
        except Exception as e:
            logger.error(f"Error creating bracket order: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    async def create_oco_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        quantity: int,
        price1: float,
        price2: float,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create OCO (One-Cancels-Other) order"""
        try:
            from core.database_unified import OCOOrder
            
            order_id = str(uuid.uuid4())
            
            oco_order = OCOOrder(
                id=order_id,
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price1=price1,
                price2=price2,
                status="PENDING",
                created_at=datetime.now()
            )
            
            db.add(oco_order)
            db.commit()
            
            logger.info(f"OCO order created: {order_id}")
            
            return {
                "success": True,
                "order_id": order_id,
                "order": self._format_oco_order(oco_order)
            }
            
        except Exception as e:
            logger.error(f"Error creating OCO order: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def calculate_position_size(
        self,
        account_balance: float,
        risk_per_trade: float,  # Percentage (e.g., 2 for 2%)
        entry_price: float,
        stop_loss_price: float
    ) -> Dict[str, Any]:
        """Calculate position size based on risk"""
        try:
            # Risk amount
            risk_amount = account_balance * (risk_per_trade / 100)
            
            # Risk per share
            risk_per_share = abs(entry_price - stop_loss_price)
            
            if risk_per_share == 0:
                return {"success": False, "error": "Invalid stop loss"}
            
            # Position size
            position_size = int(risk_amount / risk_per_share)
            
            # Position value
            position_value = position_size * entry_price
            
            # Actual risk
            actual_risk = position_size * risk_per_share
            actual_risk_pct = (actual_risk / account_balance) * 100
            
            return {
                "success": True,
                "position_size": position_size,
                "position_value": round(position_value, 2),
                "risk_amount": round(risk_amount, 2),
                "risk_per_share": round(risk_per_share, 2),
                "actual_risk": round(actual_risk, 2),
                "actual_risk_pct": round(actual_risk_pct, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_trade_to_journal(
        self,
        user_id: int,
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: int,
        side: str,
        entry_time: datetime,
        exit_time: datetime,
        notes: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Add trade to trade journal"""
        try:
            from core.database_unified import TradeJournal
            
            trade_id = str(uuid.uuid4())
            
            pnl = (exit_price - entry_price) * quantity if side == "BUY" else (entry_price - exit_price) * quantity
            pnl_percent = ((exit_price - entry_price) / entry_price * 100) if side == "BUY" else ((entry_price - exit_price) / entry_price * 100)
            
            journal_entry = TradeJournal(
                id=trade_id,
                user_id=user_id,
                symbol=symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=quantity,
                side=side,
                pnl=pnl,
                pnl_percent=pnl_percent,
                entry_time=entry_time,
                exit_time=exit_time,
                notes=notes,
                created_at=datetime.now()
            )
            
            db.add(journal_entry)
            db.commit()
            
            logger.info(f"Trade added to journal: {trade_id}")
            
            return {
                "success": True,
                "trade_id": trade_id,
                "trade": self._format_journal_entry(journal_entry)
            }
            
        except Exception as e:
            logger.error(f"Error adding trade to journal: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def _format_bracket_order(self, order) -> Dict:
        """Format bracket order for response"""
        return {
            "id": order.id,
            "user_id": order.user_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "entry_price": order.entry_price,
            "stop_loss": order.stop_loss,
            "target": order.target,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
    
    def _format_oco_order(self, order) -> Dict:
        """Format OCO order for response"""
        return {
            "id": order.id,
            "user_id": order.user_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "price1": order.price1,
            "price2": order.price2,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
    
    def _format_journal_entry(self, entry) -> Dict:
        """Format journal entry for response"""
        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "symbol": entry.symbol,
            "entry_price": entry.entry_price,
            "exit_price": entry.exit_price,
            "quantity": entry.quantity,
            "side": entry.side,
            "pnl": entry.pnl,
            "pnl_percent": entry.pnl_percent,
            "entry_time": entry.entry_time.isoformat() if entry.entry_time else None,
            "exit_time": entry.exit_time.isoformat() if entry.exit_time else None,
            "notes": entry.notes
        }

# Create singleton instance
advanced_order_management = AdvancedOrderManagement()

