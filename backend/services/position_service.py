"""
Position Service - Manages position tracking similar to Sensibull
Handles creation, updates, and P&L calculations for equity and options positions
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
import logging

from core.database_unified import Position, User
from services.data_fetcher import fetch_historical_data

logger = logging.getLogger(__name__)


class PositionService:
    """Service for managing trading positions"""
    
    def __init__(self):
        pass
    
    async def create_position(
        self,
        db: Session,
        user_id: int,
        symbol: str,
        instrument_type: str,  # EQUITY, CE, PE, FUT
        quantity: int,
        average_price: float,
        lot_size: int = 1,
        strike_price: Optional[float] = None,
        expiry_date: Optional[datetime] = None,
        option_type: Optional[str] = None,  # CE or PE
        strategy_id: Optional[str] = None,
        strategy_name: Optional[str] = None,
        leg_id: Optional[str] = None,
        is_demo: bool = True
    ) -> Position:
        """Create a new position"""
        try:
            # Calculate initial values
            total_quantity = quantity * lot_size
            invested_value = total_quantity * average_price
            
            # Get current price
            current_price = await self._get_current_price(symbol)
            
            # Create position
            position = Position(
                user_id=user_id,
                symbol=symbol.upper(),
                instrument_type=instrument_type,
                quantity=quantity,
                average_price=Decimal(str(average_price)),
                current_price=Decimal(str(current_price)),
                lot_size=lot_size,
                strike_price=strike_price,
                expiry_date=expiry_date,
                option_type=option_type,
                invested_value=Decimal(str(invested_value)),
                current_value=Decimal(str(total_quantity * current_price)),
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                leg_id=leg_id,
                is_demo=is_demo,
                is_active=True,
                entry_time=datetime.utcnow()
            )
            
            # Calculate P&L
            self._calculate_pnl(position)
            
            db.add(position)
            db.commit()
            db.refresh(position)
            
            logger.info(f"Created position: {position.id} for user {user_id}, {symbol} {instrument_type}")
            return position
            
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            db.rollback()
            raise
    
    async def update_position(
        self,
        db: Session,
        position_id: int,
        quantity: Optional[int] = None,
        price: Optional[float] = None
    ) -> Position:
        """Update an existing position"""
        try:
            position = db.query(Position).filter(Position.id == position_id).first()
            if not position:
                raise ValueError(f"Position {position_id} not found")
            
            # Update quantity if provided
            if quantity is not None:
                if quantity == 0:
                    # Close position
                    position.is_active = False
                else:
                    # Update average price (weighted average)
                    old_value = float(position.invested_value)
                    new_value = quantity * position.lot_size * (price or float(position.current_price))
                    total_quantity = quantity * position.lot_size
                    
                    position.quantity = quantity
                    position.average_price = Decimal(str((old_value + new_value) / (2 * total_quantity)))
            
            # Update current price
            if price is not None:
                position.current_price = Decimal(str(price))
            else:
                # Fetch latest price
                current_price = await self._get_current_price(position.symbol)
                position.current_price = Decimal(str(current_price))
            
            # Recalculate values
            total_quantity = position.quantity * position.lot_size
            position.invested_value = Decimal(str(position.quantity * position.lot_size * float(position.average_price)))
            position.current_value = Decimal(str(total_quantity * float(position.current_price)))
            
            # Calculate P&L
            self._calculate_pnl(position)
            
            position.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(position)
            
            return position
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            db.rollback()
            raise
    
    async def add_to_position(
        self,
        db: Session,
        user_id: int,
        symbol: str,
        instrument_type: str,
        quantity: int,
        price: float,
        lot_size: int = 1,
        strike_price: Optional[float] = None,
        expiry_date: Optional[datetime] = None,
        option_type: Optional[str] = None,
        is_demo: bool = True
    ) -> Position:
        """Add to existing position or create new one"""
        try:
            # Find existing position
            query = db.query(Position).filter(
                Position.user_id == user_id,
                Position.symbol == symbol.upper(),
                Position.instrument_type == instrument_type,
                Position.is_active == True,
                Position.is_demo == is_demo
            )
            
            if instrument_type in ['CE', 'PE']:
                query = query.filter(
                    Position.strike_price == strike_price,
                    Position.expiry_date == expiry_date
                )
            
            existing_position = query.first()
            
            if existing_position:
                # Add to existing position
                old_quantity = existing_position.quantity
                old_avg_price = float(existing_position.average_price)
                old_invested = float(existing_position.invested_value)
                
                new_quantity = old_quantity + quantity
                new_invested = old_invested + (quantity * lot_size * price)
                
                # Check if position would be closed or flipped (division by zero protection)
                if new_quantity == 0:
                    # Position is being closed - close it instead of calculating new average
                    existing_position.is_active = False
                    existing_position.quantity = 0
                    existing_position.invested_value = Decimal('0.0')
                    existing_position.current_value = Decimal('0.0')
                    existing_position.unrealized_pnl = Decimal('0.0')
                    existing_position.unrealized_pnl_percent = Decimal('0.0')
                    
                    # Update current price for record keeping
                    current_price = await self._get_current_price(symbol)
                    existing_position.current_price = Decimal(str(current_price))
                    existing_position.updated_at = datetime.utcnow()
                    
                    db.commit()
                    db.refresh(existing_position)
                    return existing_position
                
                # Check if position direction is flipping (e.g., long to short or vice versa)
                # This happens when old_quantity and new_quantity have opposite signs
                if (old_quantity > 0 and new_quantity < 0) or (old_quantity < 0 and new_quantity > 0):
                    # Position direction is flipping - treat as closing old and opening new
                    # Close the old position
                    existing_position.is_active = False
                    existing_position.quantity = 0
                    existing_position.invested_value = Decimal('0.0')
                    existing_position.current_value = Decimal('0.0')
                    existing_position.unrealized_pnl = Decimal('0.0')
                    existing_position.unrealized_pnl_percent = Decimal('0.0')
                    existing_position.updated_at = datetime.utcnow()
                    db.commit()
                    
                    # Create new position with remaining quantity
                    return await self.create_position(
                        db=db,
                        user_id=user_id,
                        symbol=symbol,
                        instrument_type=instrument_type,
                        quantity=new_quantity,
                        average_price=price,
                        lot_size=lot_size,
                        strike_price=strike_price,
                        expiry_date=expiry_date,
                        option_type=option_type,
                        is_demo=is_demo
                    )
                
                # Normal case: same direction, calculate weighted average
                new_avg_price = new_invested / (new_quantity * lot_size)
                
                existing_position.quantity = new_quantity
                existing_position.average_price = Decimal(str(new_avg_price))
                existing_position.invested_value = Decimal(str(new_invested))
                
                # Update current price
                current_price = await self._get_current_price(symbol)
                existing_position.current_price = Decimal(str(current_price))
                
                # Recalculate
                total_quantity = new_quantity * lot_size
                existing_position.current_value = Decimal(str(total_quantity * current_price))
                self._calculate_pnl(existing_position)
                existing_position.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(existing_position)
                
                return existing_position
            else:
                # Create new position
                return await self.create_position(
                    db=db,
                    user_id=user_id,
                    symbol=symbol,
                    instrument_type=instrument_type,
                    quantity=quantity,
                    average_price=price,
                    lot_size=lot_size,
                    strike_price=strike_price,
                    expiry_date=expiry_date,
                    option_type=option_type,
                    is_demo=is_demo
                )
                
        except Exception as e:
            logger.error(f"Error adding to position: {e}")
            db.rollback()
            raise
    
    async def reduce_position(
        self,
        db: Session,
        position_id: int,
        quantity: int
    ) -> Position:
        """Reduce position quantity"""
        try:
            position = db.query(Position).filter(Position.id == position_id).first()
            if not position:
                raise ValueError(f"Position {position_id} not found")
            
            # Handle reduction correctly for both long and short positions
            # For long positions (positive quantity): reduce by subtracting
            # For short positions (negative quantity): reduce by adding (buying back the short)
            if position.quantity > 0:
                # Long position: subtract quantity
                new_quantity = position.quantity - quantity
            else:
                # Short position: add quantity (buying back makes quantity less negative)
                new_quantity = position.quantity + quantity
            
            # Check if reduction would close or flip the position
            # If quantity becomes 0 or flips direction, close the position
            if new_quantity == 0 or (position.quantity > 0 and new_quantity < 0) or (position.quantity < 0 and new_quantity > 0):
                # Close position
                position.is_active = False
                position.quantity = 0
            else:
                # Update quantity
                position.quantity = new_quantity
            
            # Recalculate values
            total_quantity = position.quantity * position.lot_size
            position.invested_value = Decimal(str(position.quantity * position.lot_size * float(position.average_price)))
            
            # Update current price
            current_price = await self._get_current_price(position.symbol)
            position.current_price = Decimal(str(current_price))
            position.current_value = Decimal(str(total_quantity * current_price))
            
            # Calculate P&L
            self._calculate_pnl(position)
            position.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(position)
            
            return position
            
        except Exception as e:
            logger.error(f"Error reducing position: {e}")
            db.rollback()
            raise
    
    async def get_user_positions(
        self,
        db: Session,
        user_id: int,
        is_demo: Optional[bool] = None,
        strategy_id: Optional[str] = None
    ) -> List[Position]:
        """Get all active positions for a user"""
        try:
            query = db.query(Position).filter(
                Position.user_id == user_id,
                Position.is_active == True
            )
            
            if is_demo is not None:
                query = query.filter(Position.is_demo == is_demo)
            
            if strategy_id:
                query = query.filter(Position.strategy_id == strategy_id)
            
            positions = query.order_by(Position.updated_at.desc()).all()
            
            # Update current prices and P&L for all positions
            for position in positions:
                try:
                    current_price = await self._get_current_price(position.symbol)
                    position.current_price = Decimal(str(current_price))
                    total_quantity = position.quantity * position.lot_size
                    position.current_value = Decimal(str(total_quantity * current_price))
                    self._calculate_pnl(position)
                except Exception as e:
                    logger.warning(f"Could not update price for {position.symbol}: {e}")
            
            db.commit()
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting user positions: {e}")
            raise
    
    async def execute_strategy_trade(
        self,
        db: Session,
        user_id: int,
        strategy_name: str,
        symbol: str,
        legs: List[Dict[str, Any]],
        is_demo: bool = True
    ) -> List[Position]:
        """Execute a multi-leg strategy trade and create positions"""
        try:
            strategy_id = f"STRATEGY_{user_id}_{int(datetime.utcnow().timestamp())}"
            created_positions = []
            
            for leg in legs:
                # Quantity is already signed: negative for SELL (short), positive for BUY (long)
                leg_quantity = leg.get('quantity', 1)
                leg_price = leg.get('price', 0)
                
                # Ensure price is always positive (should already be, but validate)
                if leg_price < 0:
                    logger.warning(f"Negative price detected for leg {leg.get('id')}, converting to positive")
                    leg_price = abs(leg_price)
                
                # Create position with signed quantity (negative for short, positive for long)
                # Price is always positive - direction is tracked via quantity sign
                position = await self.create_position(
                    db=db,
                    user_id=user_id,
                    symbol=symbol,
                    instrument_type=leg.get('instrument', 'EQUITY'),
                    quantity=leg_quantity,  # Keep signed quantity: negative for SELL, positive for BUY
                    average_price=leg_price,  # Always positive
                    lot_size=leg.get('lotSize', 50),
                    strike_price=leg.get('strike'),
                    expiry_date=leg.get('expiry'),
                    option_type=leg.get('instrument') if leg.get('instrument') in ['CE', 'PE'] else None,
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    leg_id=leg.get('id'),
                    is_demo=is_demo
                )
                created_positions.append(position)
            
            logger.info(f"Executed strategy {strategy_name} with {len(created_positions)} legs")
            return created_positions
            
        except Exception as e:
            logger.error(f"Error executing strategy trade: {e}")
            db.rollback()
            raise
    
    def _calculate_pnl(self, position: Position):
        """Calculate P&L for a position (handles both long and short positions)"""
        try:
            total_quantity = position.quantity * position.lot_size
            invested_value = float(position.invested_value)
            current_value = float(position.current_value)
            
            # Calculate P&L: current_value - invested_value
            # For long positions: both positive, normal calculation
            # For short positions: invested_value is negative, current_value is negative
            # P&L = (-current_value) - (-invested_value) = invested_value - current_value
            # But we store it as current_value - invested_value for consistency
            position.unrealized_pnl = Decimal(str(current_value - invested_value))
            
            # Calculate P&L percentage using absolute value of invested_value
            # This works for both long (positive) and short (negative) positions
            abs_invested_value = abs(invested_value)
            
            if abs_invested_value > 0:
                position.unrealized_pnl_percent = Decimal(str((float(position.unrealized_pnl) / abs_invested_value) * 100))
            else:
                position.unrealized_pnl_percent = Decimal('0.0')
                
        except Exception as e:
            logger.error(f"Error calculating P&L: {e}")
            position.unrealized_pnl = Decimal('0.0')
            position.unrealized_pnl_percent = Decimal('0.0')
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        try:
            from core.data_service import data_service
            quote = await data_service.get_quote(symbol.upper(), exchange="NSE")
            if quote and quote.get("last_price"):
                return float(quote.get("last_price"))
        except Exception as e:
            logger.warning(f"Could not fetch price for {symbol}: {e}")
        
        # Fallback: try historical data
        try:
            candles = await fetch_historical_data(symbol, timeframe="1d", days=1)
            if candles and len(candles) > 0:
                return float(candles[-1].get('close', 0))
        except Exception as e:
            logger.warning(f"Could not fetch historical price for {symbol}: {e}")
        
        return 0.0


# Create singleton instance
position_service = PositionService()
