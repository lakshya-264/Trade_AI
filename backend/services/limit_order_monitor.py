"""
🔄 LIMIT ORDER PRICE MONITORING SERVICE
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, sessionmaker

from core.database_unified import TradingExecution
from core.data_service import data_service

logger = logging.getLogger(__name__)

class LimitOrderMonitor:
    def __init__(self):
        self.database_url = "sqlite:///./trading_ai.db"
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.monitoring = False
        self.check_interval = 30  # Check every 30 seconds
        
    async def start_monitoring(self):
        """Start monitoring pending limit orders"""
        if self.monitoring:
            logger.warning("Limit order monitoring already started")
            return
            
        self.monitoring = True
        logger.info("🔄 Starting limit order price monitoring")
        
        while self.monitoring:
            try:
                await self.check_pending_orders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in limit order monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop monitoring limit orders"""
        self.monitoring = False
        logger.info("⏹️ Stopped limit order price monitoring")
    
    async def check_pending_orders(self):
        """Check all pending limit orders and execute if price matches"""
        session = self.Session()
        try:
            # Get all pending limit orders
            pending_orders = session.query(TradingExecution).filter(
                TradingExecution.status == 'PENDING',
                TradingExecution.order_type == 'LIMIT'
            ).all()
            
            if not pending_orders:
                return
            
            logger.info(f"📊 Checking {len(pending_orders)} pending limit orders")
            
            for order in pending_orders:
                await self.check_single_order(order, session)
                
            session.commit()
            
        except Exception as e:
            logger.error(f"Error checking pending orders: {e}")
            session.rollback()
        finally:
            session.close()
    
    async def check_single_order(self, order: TradingExecution, session: Session):
        """Check if a single limit order should be executed"""
        try:
            # Get current market price
            current_price_data = await data_service.get_current_price(order.symbol)
            
            if not current_price_data or 'current_price' not in current_price_data:
                logger.warning(f"Could not get current price for {order.symbol}")
                return
            
            current_price = current_price_data['current_price']
            target_price = order.target_price
            signal_type = order.signal_type
            
            logger.info(f"🔍 Checking {order.symbol}: Target={target_price}, Current={current_price}, Action={signal_type}")
            
            # Check if price matches for execution
            should_execute = False
            
            if signal_type == 'BUY':
                # Buy order: execute when current price <= target price
                should_execute = current_price <= target_price
            else:  # SELL
                # Sell order: execute when current price >= target price
                should_execute = current_price >= target_price
            
            if should_execute:
                logger.info(f"✅ Executing limit order: {order.symbol} at {current_price}")
                
                # Update order to executed status
                order.status = 'EXECUTED'
                order.exit_price = current_price
                order.exit_value = current_price * order.quantity
                order.exit_time = datetime.utcnow()
                
                # Calculate P&L
                if signal_type == 'BUY':
                    order.pnl_amount = (current_price - order.entry_price) * order.quantity
                else:
                    order.pnl_amount = (order.entry_price - current_price) * order.quantity
                
                order.pnl_percent = (order.pnl_amount / order.entry_value) * 100 if order.entry_value != 0 else 0
                
                # Update profit/loss status
                if order.pnl_amount > 0:
                    order.profit_loss = 'PROFIT'
                elif order.pnl_amount < 0:
                    order.profit_loss = 'LOSS'
                else:
                    order.profit_loss = 'BREAKEVEN'
                
                logger.info(f"💰 Order executed: P&L={order.pnl_amount:.2f}, Status={order.profit_loss}")
                
            else:
                # Order still pending
                logger.debug(f"⏳ Order still pending: {order.symbol}")
                
        except Exception as e:
            logger.error(f"Error checking order {order.id}: {e}")

# Global monitor instance
limit_order_monitor = LimitOrderMonitor()

async def start_limit_order_monitoring():
    """Start the limit order monitoring service"""
    await limit_order_monitor.start_monitoring()

def stop_limit_order_monitoring():
    """Stop the limit order monitoring service"""
    limit_order_monitor.stop_monitoring()
