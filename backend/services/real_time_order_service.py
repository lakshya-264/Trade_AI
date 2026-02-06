"""
Enhanced Order Placement with Real-time Market Prices
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from services.order_placement_service import order_placement_service
from services.market_price_service import market_price_service
from services.portfolio_integration_service import portfolio_integration_service
from core.database_unified import User

logger = logging.getLogger(__name__)

class RealTimeOrderService:
    """Service for placing orders with real-time market prices"""
    
    def __init__(self):
        self.order_types = ['MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LIMIT']
        self.price_sources = ['NSE', 'BSE', 'ALPHA_VANTAGE', 'FALLBACK']
    
    async def place_buy_order_market_price(
        self,
        symbol: str,
        quantity: int,
        user_id: int,
        db: Session,
        order_type: str = 'MARKET',
        signal_strength: str = 'MODERATE',
        confidence_score: float = 0.5,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        duration: str = 'INTRADAY',
        strategy: str = 'MANUAL',
        expected_holding_period: Optional[int] = None
    ) -> Dict[str, Any]:
        """Place BUY order at current market price"""
        try:
            logger.info(f"Placing BUY order for {symbol} at market price")
            
            # Step 1: Get current market price
            market_data = await market_price_service.get_current_price(symbol)
            
            if not market_data:
                raise ValueError(f"Unable to fetch market price for {symbol}")
            
            current_price = market_data['current_price']
            price_source = market_data.get('source', 'UNKNOWN')
            
            logger.info(f"Current price for {symbol}: ₹{current_price} (Source: {price_source})")
            
            # Step 2: Validate market status
            market_status = await market_price_service.get_market_status()
            
            if not market_status['is_market_open'] and order_type == 'MARKET':
                logger.warning(f"Market is closed, using LIMIT order instead of MARKET")
                order_type = 'LIMIT'
                # Use last known price for limit order
                target_price = current_price
            
            # Step 3: Calculate order value and validate
            order_value = current_price * quantity
            
            if order_value <= 0:
                raise ValueError("Invalid order value")
            
            # Step 4: Prepare order data with market price
            order_data = {
                'symbol': symbol,
                'order_type': order_type,
                'action': 'BUY',
                'quantity': quantity,
                'price': current_price,
                'target_price': target_price or (current_price * 1.05 if order_type == 'LIMIT' else None),  # 5% above current for limit
                'stop_loss': stop_loss,
                'signal_strength': signal_strength,
                'confidence_score': confidence_score,
                'duration': duration,
                'strategy': strategy,
                'expected_holding_period': expected_holding_period,
                'market_conditions': {
                    'market_status': market_status,
                    'price_source': price_source,
                    'volatility': market_data.get('change_percent', 0),
                    'volume': market_data.get('volume', 0),
                    'market_sentiment': self._determine_market_sentiment(market_data)
                }
            }
            
            # Step 5: Place order with portfolio integration
            result = await portfolio_integration_service.place_order_and_update_portfolio(
                order_data=order_data,
                user_id=user_id,
                db=db
            )
            
            # Step 6: Add market price information to result
            result['market_data'] = market_data
            result['order_execution_price'] = current_price
            result['price_source'] = price_source
            result['market_status'] = market_status
            
            logger.info(f"BUY order placed successfully for {symbol} at ₹{current_price}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing BUY order at market price: {e}")
            raise
    
    async def place_sell_order_market_price(
        self,
        symbol: str,
        quantity: int,
        user_id: int,
        db: Session,
        order_type: str = 'MARKET',
        signal_strength: str = 'MODERATE',
        confidence_score: float = 0.5,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        duration: str = 'INTRADAY',
        strategy: str = 'MANUAL'
    ) -> Dict[str, Any]:
        """Place SELL order at current market price"""
        try:
            logger.info(f"Placing SELL order for {symbol} at market price")
            
            # Step 1: Get current market price
            market_data = await market_price_service.get_current_price(symbol)
            
            if not market_data:
                raise ValueError(f"Unable to fetch market price for {symbol}")
            
            current_price = market_data['current_price']
            price_source = market_data.get('source', 'UNKNOWN')
            
            logger.info(f"Current price for {symbol}: ₹{current_price} (Source: {price_source})")
            
            # Step 2: Validate market status
            market_status = await market_price_service.get_market_status()
            
            if not market_status['is_market_open'] and order_type == 'MARKET':
                logger.warning(f"Market is closed, using LIMIT order instead of MARKET")
                order_type = 'LIMIT'
                target_price = current_price
            
            # Step 3: Check if user has sufficient holdings
            portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
                user_id=user_id,
                db=db
            )
            
            holdings = portfolio_result.get('data', {}).get('holdings', {})
            
            if symbol not in holdings:
                raise ValueError(f"No holdings found for {symbol}")
            
            current_holding = holdings[symbol]
            available_quantity = current_holding.get('quantity', 0)
            
            if quantity > available_quantity:
                raise ValueError(f"Insufficient holdings. Available: {available_quantity}, Requested: {quantity}")
            
            # Step 4: Calculate order value
            order_value = current_price * quantity
            
            # Step 5: Prepare order data with market price
            order_data = {
                'symbol': symbol,
                'order_type': order_type,
                'action': 'SELL',
                'quantity': quantity,
                'price': current_price,
                'target_price': target_price or (current_price * 0.95 if order_type == 'LIMIT' else None),  # 5% below current for limit
                'stop_loss': stop_loss,
                'signal_strength': signal_strength,
                'confidence_score': confidence_score,
                'duration': duration,
                'strategy': strategy,
                'market_conditions': {
                    'market_status': market_status,
                    'price_source': price_source,
                    'volatility': market_data.get('change_percent', 0),
                    'volume': market_data.get('volume', 0),
                    'market_sentiment': self._determine_market_sentiment(market_data)
                }
            }
            
            # Step 6: Place order with portfolio integration
            result = await portfolio_integration_service.place_order_and_update_portfolio(
                order_data=order_data,
                user_id=user_id,
                db=db
            )
            
            # Step 7: Add market price information to result
            result['market_data'] = market_data
            result['order_execution_price'] = current_price
            result['price_source'] = price_source
            result['market_status'] = market_status
            result['holding_before_sale'] = current_holding
            
            logger.info(f"SELL order placed successfully for {symbol} at ₹{current_price}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing SELL order at market price: {e}")
            raise
    
    async def get_order_price_preview(
        self,
        symbol: str,
        action: str,  # BUY or SELL
        quantity: int,
        order_type: str = 'MARKET'
    ) -> Dict[str, Any]:
        """Get price preview before placing order"""
        try:
            # Get current market price
            market_data = await market_price_service.get_current_price(symbol)
            
            if not market_data:
                raise ValueError(f"Unable to fetch market price for {symbol}")
            
            current_price = market_data['current_price']
            price_source = market_data.get('source', 'UNKNOWN')
            
            # Calculate order value
            order_value = current_price * quantity
            
            # Get market status
            market_status = await market_price_service.get_market_status()
            
            # Determine execution price based on order type
            if order_type == 'MARKET':
                execution_price = current_price
                execution_note = "Will execute at current market price"
            elif order_type == 'LIMIT':
                if action == 'BUY':
                    execution_price = current_price * 1.02  # 2% above current
                    execution_note = "Limit order set 2% above current price"
                else:
                    execution_price = current_price * 0.98  # 2% below current
                    execution_note = "Limit order set 2% below current price"
            else:
                execution_price = current_price
                execution_note = f"{order_type} order at market price"
            
            # Calculate estimated fees (simplified)
            brokerage_fee = max(20, order_value * 0.0003)  # 0.03% or ₹20 minimum
            stt_ctt = order_value * 0.0006 if action == 'SELL' else 0  # STT only on sells
            total_fees = brokerage_fee + stt_ctt
            
            # Net amount
            if action == 'BUY':
                net_amount = order_value + total_fees
            else:
                net_amount = order_value - total_fees
            
            return {
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'current_price': current_price,
                'execution_price': execution_price,
                'order_value': order_value,
                'brokerage_fee': brokerage_fee,
                'stt_ctt': stt_ctt,
                'total_fees': total_fees,
                'net_amount': net_amount,
                'price_source': price_source,
                'market_status': market_status,
                'execution_note': execution_note,
                'market_data': market_data
            }
            
        except Exception as e:
            logger.error(f"Error getting order price preview: {e}")
            raise
    
    async def get_bulk_price_preview(
        self,
        orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get price preview for multiple orders"""
        try:
            # Get symbols list
            symbols = list(set(order['symbol'] for order in orders))
            
            # Fetch prices for all symbols
            market_prices = await market_price_service.get_multiple_prices(symbols)
            
            # Calculate preview for each order
            previews = []
            total_order_value = 0
            total_fees = 0
            
            for order in orders:
                symbol = order['symbol']
                action = order['action']
                quantity = order['quantity']
                order_type = order.get('order_type', 'MARKET')
                
                if symbol not in market_prices:
                    continue
                
                market_data = market_prices[symbol]
                current_price = market_data['current_price']
                order_value = current_price * quantity
                
                # Calculate fees
                brokerage_fee = max(20, order_value * 0.0003)
                stt_ctt = order_value * 0.0006 if action == 'SELL' else 0
                total_order_fees = brokerage_fee + stt_ctt
                
                # Net amount
                net_amount = order_value + total_order_fees if action == 'BUY' else order_value - total_order_fees
                
                preview = {
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'current_price': current_price,
                    'order_value': order_value,
                    'total_fees': total_order_fees,
                    'net_amount': net_amount,
                    'price_source': market_data.get('source', 'UNKNOWN')
                }
                
                previews.append(preview)
                total_order_value += order_value
                total_fees += total_order_fees
            
            return {
                'previews': previews,
                'total_order_value': total_order_value,
                'total_fees': total_fees,
                'total_net_amount': total_order_value + total_fees,  # Assuming all BUY orders
                'symbols_count': len(symbols),
                'orders_count': len(orders)
            }
            
        except Exception as e:
            logger.error(f"Error getting bulk price preview: {e}")
            raise
    
    def _determine_market_sentiment(self, market_data: Dict[str, Any]) -> str:
        """Determine market sentiment from market data"""
        try:
            change_percent = market_data.get('change_percent', 0)
            volume = market_data.get('volume', 0)
            
            # Simple sentiment determination
            if change_percent > 2:
                return 'STRONGLY_BULLISH'
            elif change_percent > 0.5:
                return 'BULLISH'
            elif change_percent > -0.5:
                return 'NEUTRAL'
            elif change_percent > -2:
                return 'BEARISH'
            else:
                return 'STRONGLY_BEARISH'
                
        except Exception as e:
            logger.error(f"Error determining market sentiment: {e}")
            return 'NEUTRAL'
    
    async def validate_order_before_placement(
        self,
        symbol: str,
        action: str,
        quantity: int,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Validate order parameters before placement"""
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'recommendations': []
            }
            
            # Check market hours
            market_status = await market_price_service.get_market_status()
            
            if not market_status['is_market_open']:
                validation_result['warnings'].append("Market is currently closed")
                validation_result['recommendations'].append("Consider using LIMIT order")
            
            # Get current price
            market_data = await market_price_service.get_current_price(symbol)
            
            if not market_data:
                validation_result['errors'].append(f"Unable to fetch price for {symbol}")
                validation_result['is_valid'] = False
                return validation_result
            
            current_price = market_data['current_price']
            order_value = current_price * quantity
            
            # Check minimum order value
            if order_value < 500:
                validation_result['errors'].append("Minimum order value is ₹500")
                validation_result['is_valid'] = False
            
            # Check for SELL orders - verify holdings
            if action == 'SELL':
                portfolio_result = await portfolio_integration_service.get_portfolio_with_performance(
                    user_id=user_id,
                    db=db
                )
                
                holdings = portfolio_result.get('data', {}).get('holdings', {})
                
                if symbol not in holdings:
                    validation_result['errors'].append(f"No holdings found for {symbol}")
                    validation_result['is_valid'] = False
                else:
                    available_quantity = holdings[symbol].get('quantity', 0)
                    if quantity > available_quantity:
                        validation_result['errors'].append(
                            f"Insufficient holdings. Available: {available_quantity}, Requested: {quantity}"
                        )
                        validation_result['is_valid'] = False
            
            # Check for unusual price movements
            change_percent = market_data.get('change_percent', 0)
            if abs(change_percent) > 10:
                validation_result['warnings'].append(
                    f"High volatility detected: {change_percent:.2f}% change today"
                )
                validation_result['recommendations'].append("Consider reducing position size")
            
            # Check volume
            volume = market_data.get('volume', 0)
            if volume < 10000:  # Low volume warning
                validation_result['warnings'].append("Low trading volume - execution may be delayed")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'recommendations': []
            }

# Create global instance
real_time_order_service = RealTimeOrderService()
