"""
Order Placement and Duration Analysis System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import logging

from core.database import get_db
from models.trading_performance_models import TradingExecution
from core.database_unified import User, PortfolioMetadata

logger = logging.getLogger(__name__)

class OrderPlacementService:
    """Service for order placement and duration analysis"""
    
    def __init__(self):
        self.order_types = ['MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LIMIT']
        self.durations = ['INTRADAY', 'SHORT_TERM', 'MEDIUM_TERM', 'LONG_TERM']
        self.signal_strength_levels = ['WEAK', 'MODERATE', 'STRONG', 'VERY_STRONG']
    
    async def place_order_with_analysis(
        self,
        symbol: str,
        order_type: str,
        action: str,  # BUY or SELL
        quantity: int,
        price: float,
        user_id: int,
        db: Session,
        signal_strength: str = "MODERATE",
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        duration: str = "INTRADAY",
        strategy: str = "MANUAL",
        confidence_score: float = 0.5,
        expected_holding_period: Optional[int] = None,  # in hours
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Place order with comprehensive analysis tracking"""
        try:
            logger.info(f"Placing {order_type} {action} order for {symbol}: {quantity} shares")
            
            # Validate order parameters
            validation_result = self._validate_order_parameters(
                symbol, order_type, action, quantity, price, target_price, stop_loss
            )
            
            if not validation_result['is_valid']:
                raise ValueError(f"Order validation failed: {validation_result['reason']}")
            
            # Calculate order metrics
            order_metrics = self._calculate_order_metrics(
                symbol, order_type, action, quantity, price, target_price, stop_loss,
                signal_strength, confidence_score, market_conditions
            )
            
            # Determine expected duration based on strategy and signal
            expected_duration = self._determine_expected_duration(
                duration, strategy, signal_strength, expected_holding_period
            )
            
            # Determine initial status based on order type
            initial_status = 'PENDING' if order_type == 'LIMIT' else 'EXECUTED'
            
            # Create enhanced trading execution record
            execution = TradingExecution(
                user_id=user_id,  # Add user_id
                symbol=symbol,
                signal_type=action,
                action='ENTRY',
                entry_price=price,
                quantity=quantity,
                entry_value=price * quantity,
                status=initial_status,
                strategy=strategy,
                signal_confidence=confidence_score,
                signal_strength=signal_strength,
                order_type=order_type,
                target_price=target_price,
                stop_loss=stop_loss,
                expected_duration=expected_duration,
                expected_holding_period_hours=expected_holding_period,
                order_metrics=order_metrics,
                market_conditions=market_conditions or {},
                entry_time=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(execution)
            db.flush()
            
            # Create order placement analysis
            placement_analysis = await self._analyze_order_placement(
                execution, user_id, db
            )
            
            # Record the transaction
            transaction_record = {
                'execution_id': execution.id,
                'symbol': symbol,
                'order_type': order_type,
                'action': action,
                'quantity': quantity,
                'price': price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'signal_strength': signal_strength,
                'confidence_score': confidence_score,
                'expected_duration': expected_duration,
                'order_metrics': order_metrics,
                'placement_analysis': placement_analysis,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            db.commit()
            
            logger.info(f"Order placed successfully: {symbol} {order_type} {action} {quantity}@{price}")
            
            return {
                'success': True,
                'execution': execution,
                'transaction': transaction_record,
                'placement_analysis': placement_analysis,
                'message': f'Order placed and analyzed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            db.rollback()
            raise
    
    def _validate_order_parameters(
        self,
        symbol: str,
        order_type: str,
        action: str,
        quantity: int,
        price: float,
        target_price: Optional[float],
        stop_loss: Optional[float]
    ) -> Dict[str, Any]:
        """Validate order parameters"""
        try:
            # Basic validations
            if not symbol or not symbol.strip():
                return {'is_valid': False, 'reason': 'Symbol is required'}
            
            if order_type not in self.order_types:
                return {'is_valid': False, 'reason': f'Invalid order type: {order_type}'}
            
            if action not in ['BUY', 'SELL']:
                return {'is_valid': False, 'reason': f'Invalid action: {action}'}
            
            if quantity <= 0:
                return {'is_valid': False, 'reason': 'Quantity must be positive'}
            
            if price <= 0:
                return {'is_valid': False, 'reason': 'Price must be positive'}
            
            # Order type specific validations
            if order_type == 'LIMIT' and not target_price:
                return {'is_valid': False, 'reason': 'Target price required for limit orders'}
            
            if order_type == 'STOP_LOSS' and not stop_loss:
                return {'is_valid': False, 'reason': 'Stop loss required for stop loss orders'}
            
            if order_type == 'STOP_LIMIT' and (not target_price or not stop_loss):
                return {'is_valid': False, 'reason': 'Both target and stop loss required for stop limit orders'}
            
            # Price logic validations
            if target_price and stop_loss:
                if action == 'BUY' and stop_loss >= target_price:
                    return {'is_valid': False, 'reason': 'Stop loss must be below target price for BUY orders'}
                
                if action == 'SELL' and stop_loss <= target_price:
                    return {'is_valid': False, 'reason': 'Stop loss must be above target price for SELL orders'}
            
            return {'is_valid': True, 'reason': 'Order parameters valid'}
            
        except Exception as e:
            logger.error(f"Error validating order parameters: {e}")
            return {'is_valid': False, 'reason': f'Validation error: {str(e)}'}
    
    def _calculate_order_metrics(
        self,
        symbol: str,
        order_type: str,
        action: str,
        quantity: int,
        price: float,
        target_price: Optional[float],
        stop_loss: Optional[float],
        signal_strength: str,
        confidence_score: float,
        market_conditions: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate comprehensive order metrics"""
        try:
            total_value = price * quantity
            
            # Risk-reward calculation
            potential_profit = 0
            potential_loss = 0
            risk_reward_ratio = 0
            
            if target_price and stop_loss:
                if action == 'BUY':
                    potential_profit = (target_price - price) * quantity
                    potential_loss = (price - stop_loss) * quantity
                else:  # SELL
                    potential_profit = (price - target_price) * quantity
                    potential_loss = (stop_loss - price) * quantity
                
                risk_reward_ratio = abs(potential_profit / potential_loss) if potential_loss != 0 else 0
            
            # Order type scoring
            order_type_score = self._get_order_type_score(order_type, market_conditions)
            
            # Signal strength scoring
            signal_strength_score = self._get_signal_strength_score(signal_strength)
            
            # Market condition adjustment
            market_adjustment = self._get_market_condition_adjustment(market_conditions)
            
            # Overall order quality score
            order_quality_score = (
                (confidence_score * 0.3) +
                (signal_strength_score * 0.3) +
                (order_type_score * 0.2) +
                (market_adjustment * 0.2)
            ) * 100
            
            return {
                'total_value': total_value,
                'potential_profit': potential_profit,
                'potential_loss': potential_loss,
                'risk_reward_ratio': risk_reward_ratio,
                'order_type_score': order_type_score,
                'signal_strength_score': signal_strength_score,
                'market_adjustment': market_adjustment,
                'order_quality_score': order_quality_score,
                'risk_per_share': abs(price - stop_loss) if stop_loss else 0,
                'profit_per_share': abs(target_price - price) if target_price else 0,
                'position_size_score': min(100, (total_value / 100000) * 10),  # Simple scoring
                'liquidity_score': self._estimate_liquidity_score(symbol, total_value)
            }
            
        except Exception as e:
            logger.error(f"Error calculating order metrics: {e}")
            return {}
    
    def _get_order_type_score(self, order_type: str, market_conditions: Optional[Dict[str, Any]]) -> float:
        """Get score for order type based on market conditions"""
        base_scores = {
            'MARKET': 0.7,
            'LIMIT': 0.9,
            'STOP_LOSS': 0.8,
            'STOP_LIMIT': 0.85
        }
        
        base_score = base_scores.get(order_type, 0.5)
        
        # Adjust based on market volatility
        if market_conditions:
            volatility = market_conditions.get('volatility', 0.5)
            if volatility > 0.8:  # High volatility - limit orders better
                if order_type == 'LIMIT':
                    base_score += 0.1
                elif order_type == 'MARKET':
                    base_score -= 0.1
        
        return min(1.0, base_score)
    
    def _get_signal_strength_score(self, signal_strength: str) -> float:
        """Get score for signal strength"""
        strength_scores = {
            'WEAK': 0.25,
            'MODERATE': 0.5,
            'STRONG': 0.75,
            'VERY_STRONG': 1.0
        }
        return strength_scores.get(signal_strength, 0.5)
    
    def _get_market_condition_adjustment(self, market_conditions: Optional[Dict[str, Any]]) -> float:
        """Get adjustment factor based on market conditions"""
        if not market_conditions:
            return 0.5  # Neutral
        
        # Simple scoring based on market sentiment
        sentiment = market_conditions.get('sentiment', 'NEUTRAL')
        volatility = market_conditions.get('volatility', 0.5)
        trend = market_conditions.get('trend', 'SIDEWAYS')
        
        base_score = 0.5
        
        # Sentiment adjustment
        if sentiment == 'BULLISH':
            base_score += 0.2
        elif sentiment == 'BEARISH':
            base_score -= 0.1
        
        # Volatility adjustment
        if volatility > 0.8:
            base_score -= 0.1  # High volatility - more cautious
        elif volatility < 0.3:
            base_score += 0.1  # Low volatility - more confident
        
        # Trend adjustment
        if trend == 'UP':
            base_score += 0.1
        elif trend == 'DOWN':
            base_score -= 0.05
        
        return max(0.1, min(1.0, base_score))
    
    def _estimate_liquidity_score(self, symbol: str, total_value: float) -> float:
        """Estimate liquidity score for the symbol"""
        # Simplified liquidity estimation
        # In real implementation, use actual volume data
        
        # Assume large-cap stocks have high liquidity
        large_cap_stocks = ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'HINDUNILVR', 'ICICIBANK']
        
        if symbol in large_cap_stocks:
            if total_value < 100000:  # < 1L
                return 1.0
            elif total_value < 1000000:  # < 10L
                return 0.9
            else:
                return 0.8
        else:
            if total_value < 50000:  # < 50K
                return 0.8
            elif total_value < 200000:  # < 2L
                return 0.6
            else:
                return 0.4
    
    def _determine_expected_duration(
        self,
        duration: str,
        strategy: str,
        signal_strength: str,
        expected_holding_period: Optional[int]
    ) -> str:
        """Determine expected duration based on multiple factors"""
        if expected_holding_period:
            # Convert hours to duration category
            if expected_holding_period <= 6:
                return 'INTRADAY'
            elif expected_holding_period <= 24:
                return 'SHORT_TERM'
            elif expected_holding_period <= 168:  # 1 week
                return 'MEDIUM_TERM'
            else:
                return 'LONG_TERM'
        
        # Adjust based on signal strength
        if signal_strength == 'VERY_STRONG':
            if duration == 'INTRADAY':
                return 'SHORT_TERM'  # Upgrade for strong signals
        elif signal_strength == 'WEAK':
            if duration in ['MEDIUM_TERM', 'LONG_TERM']:
                return 'SHORT_TERM'  # Downgrade for weak signals
        
        return duration
    
    async def _analyze_order_placement(
        self,
        execution: TradingExecution,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze the order placement for insights"""
        try:
            # Get user's historical performance
            user_history = await self._get_user_order_history(user_id, db)
            
            # Analyze order timing
            timing_analysis = self._analyze_order_timing(execution, user_history)
            
            # Analyze order size
            size_analysis = self._analyze_order_size(execution, user_history)
            
            # Analyze risk-reward
            risk_analysis = self._analyze_risk_reward(execution)
            
            # Generate recommendations
            recommendations = self._generate_order_recommendations(
                execution, timing_analysis, size_analysis, risk_analysis
            )
            
            return {
                'timing_analysis': timing_analysis,
                'size_analysis': size_analysis,
                'risk_analysis': risk_analysis,
                'recommendations': recommendations,
                'overall_score': self._calculate_placement_score(
                    timing_analysis, size_analysis, risk_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order placement: {e}")
            return {}
    
    async def _get_user_order_history(
        self,
        user_id: int,
        db: Session,
        days: int = 30
    ) -> List[TradingExecution]:
        """Get user's order history"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Filter by user_id and date
            history = db.query(TradingExecution).filter(
                and_(
                    TradingExecution.user_id == user_id,
                    TradingExecution.created_at >= cutoff_date
                )
            ).all()
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting user order history: {e}")
            return []
    
    def _analyze_order_timing(
        self,
        execution: TradingExecution,
        user_history: List[TradingExecution]
    ) -> Dict[str, Any]:
        """Analyze order timing"""
        try:
            current_time = execution.entry_time.time()
            current_hour = current_time.hour
            
            # Analyze user's preferred trading times
            user_hours = [h.entry_time.hour for h in user_history]
            preferred_hours = {}
            
            for hour in user_hours:
                preferred_hours[hour] = preferred_hours.get(hour, 0) + 1
            
            # Market session analysis
            if 9 <= current_hour < 15:  # Regular trading hours
                session = 'REGULAR'
                session_score = 0.8
            elif 15 <= current_hour < 16:  # Closing session
                session = 'CLOSING'
                session_score = 0.6
            else:
                session = 'AFTER_HOURS'
                session_score = 0.3
            
            # Day of week analysis
            day_of_week = execution.entry_time.weekday()
            day_scores = {
                0: 0.7,  # Monday
                1: 0.9,  # Tuesday
                2: 0.9,  # Wednesday
                3: 0.8,  # Thursday
                4: 0.6,  # Friday
            }
            
            return {
                'current_hour': current_hour,
                'session': session,
                'session_score': session_score,
                'day_of_week': day_of_week,
                'day_score': day_scores.get(day_of_week, 0.5),
                'preferred_hours': preferred_hours,
                'timing_score': (session_score + day_scores.get(day_of_week, 0.5)) / 2
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order timing: {e}")
            return {}
    
    def _analyze_order_size(
        self,
        execution: TradingExecution,
        user_history: List[TradingExecution]
    ) -> Dict[str, Any]:
        """Analyze order size relative to user history"""
        try:
            current_value = execution.entry_value
            
            if not user_history:
                return {
                    'current_value': current_value,
                    'avg_value': current_value,
                    'size_percentile': 50,
                    'size_score': 0.5,
                    'recommendation': 'First order - size is reasonable'
                }
            
            # Calculate user's average order size
            user_values = [h.entry_value for h in user_history if h.entry_value]
            avg_value = sum(user_values) / len(user_values)
            
            # Calculate percentile
            sorted_values = sorted(user_values)
            rank = sum(1 for v in sorted_values if v <= current_value)
            percentile = (rank / len(sorted_values)) * 100
            
            # Size scoring
            if 0.8 <= percentile <= 0.95:  # Not too small, not too large
                size_score = 0.8
            elif percentile < 0.3:  # Very small
                size_score = 0.4
            elif percentile > 0.95:  # Very large
                size_score = 0.3
            else:
                size_score = 0.6
            
            return {
                'current_value': current_value,
                'avg_value': avg_value,
                'size_percentile': percentile,
                'size_score': size_score,
                'recommendation': self._get_size_recommendation(percentile, size_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order size: {e}")
            return {}
    
    def _analyze_risk_reward(
        self,
        execution: TradingExecution
    ) -> Dict[str, Any]:
        """Analyze risk-reward ratio"""
        try:
            order_metrics = execution.order_metrics or {}
            risk_reward_ratio = order_metrics.get('risk_reward_ratio', 0)
            
            # Risk-reward scoring
            if risk_reward_ratio >= 3:
                rr_score = 1.0
                rr_grade = 'EXCELLENT'
            elif risk_reward_ratio >= 2:
                rr_score = 0.8
                rr_grade = 'GOOD'
            elif risk_reward_ratio >= 1:
                rr_score = 0.6
                rr_grade = 'FAIR'
            elif risk_reward_ratio >= 0.5:
                rr_score = 0.4
                rr_grade = 'POOR'
            else:
                rr_score = 0.2
                rr_grade = 'VERY_POOR'
            
            # Risk analysis
            potential_loss = order_metrics.get('potential_loss', 0)
            total_value = execution.entry_value
            risk_percentage = (potential_loss / total_value) * 100 if total_value > 0 else 0
            
            risk_score = 1.0 - min(1.0, risk_percentage / 10)  # 10% risk = 0 score
            
            return {
                'risk_reward_ratio': risk_reward_ratio,
                'rr_score': rr_score,
                'rr_grade': rr_grade,
                'potential_loss': potential_loss,
                'risk_percentage': risk_percentage,
                'risk_score': risk_score,
                'overall_rr_score': (rr_score + risk_score) / 2
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk-reward: {e}")
            return {}
    
    def _generate_order_recommendations(
        self,
        execution: TradingExecution,
        timing_analysis: Dict[str, Any],
        size_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate order placement recommendations"""
        try:
            recommendations = []
            
            # Timing recommendations
            timing_score = timing_analysis.get('timing_score', 0.5)
            if timing_score < 0.5:
                recommendations.append("Consider placing orders during regular trading hours (9 AM - 3 PM)")
            
            # Size recommendations
            size_score = size_analysis.get('size_score', 0.5)
            if size_score < 0.5:
                recommendations.append("Order size is unusual - consider aligning with your typical position size")
            
            # Risk-reward recommendations
            rr_score = risk_analysis.get('overall_rr_score', 0.5)
            if rr_score < 0.5:
                recommendations.append("Risk-reward ratio is suboptimal - consider adjusting target or stop-loss levels")
            
            # Order type recommendations
            order_type = execution.order_type
            if order_type == 'MARKET' and timing_analysis.get('session') == 'REGULAR':
                recommendations.append("Consider using limit orders during regular hours for better price execution")
            
            # General recommendations
            if execution.signal_strength == 'WEAK':
                recommendations.append("Signal strength is weak - consider reducing position size")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _calculate_placement_score(
        self,
        timing_analysis: Dict[str, Any],
        size_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall placement score"""
        try:
            timing_score = timing_analysis.get('timing_score', 0.5)
            size_score = size_analysis.get('size_score', 0.5)
            rr_score = risk_analysis.get('overall_rr_score', 0.5)
            
            # Weighted average
            overall_score = (timing_score * 0.3) + (size_score * 0.3) + (rr_score * 0.4)
            
            return round(overall_score * 100, 1)
            
        except Exception as e:
            logger.error(f"Error calculating placement score: {e}")
            return 50.0

# Create global instance
order_placement_service = OrderPlacementService()
