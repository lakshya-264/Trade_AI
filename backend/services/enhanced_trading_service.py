"""
Enhanced trading service with portfolio integration
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

class EnhancedTradingService:
    """Enhanced trading service with portfolio integration"""
    
    def __init__(self):
        self.portfolio_service = None  # Will be injected
    
    async def execute_trade_with_portfolio_update(
        self,
        symbol: str,
        action: str,  # BUY or SELL
        quantity: int,
        price: float,
        user_id: int,
        db: Session,
        strategy: str = "MANUAL",
        signal_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """Execute trade and automatically update portfolio"""
        try:
            logger.info(f"Executing {action} trade for {symbol}: {quantity} shares at ₹{price}")
            
            # Create TradingExecution record
            execution = TradingExecution(
                symbol=symbol,
                signal_type=action,
                action='ENTRY',
                entry_price=price,
                quantity=quantity,
                entry_value=price * quantity,
                status='OPEN',
                strategy=strategy,
                signal_confidence=signal_confidence,
                entry_time=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(execution)
            db.flush()  # Get the ID without committing
            
            # Update portfolio holdings
            portfolio_updated = await self._update_portfolio_holdings(
                symbol, action, quantity, price, user_id, db
            )
            
            # Calculate portfolio impact
            portfolio_impact = await self._calculate_portfolio_impact(
                user_id, price * quantity, db
            )
            
            # Record the transaction
            transaction_record = {
                'execution_id': execution.id,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'total_value': price * quantity,
                'user_id': user_id,
                'portfolio_updated': portfolio_updated,
                'portfolio_impact': portfolio_impact,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            db.commit()
            
            logger.info(f"Trade executed successfully: {symbol} {action} {quantity}@{price}")
            
            return {
                'success': True,
                'execution': execution,
                'transaction': transaction_record,
                'message': f'Trade executed and portfolio updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            db.rollback()
            raise
    
    async def _update_portfolio_holdings(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        user_id: int,
        db: Session
    ) -> bool:
        """Update portfolio holdings after trade execution"""
        try:
            # Get user's portfolio
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            if not portfolio:
                # Create new portfolio if doesn't exist
                portfolio = PortfolioMetadata(
                    user_id=user_id,
                    holdings={},
                    total_value=0,
                    last_updated=datetime.utcnow()
                )
                db.add(portfolio)
                db.flush()
            
            # Update holdings
            current_holdings = portfolio.holdings or {}
            
            if action == 'BUY':
                current_holdings[symbol] = current_holdings.get(symbol, 0) + quantity
                portfolio.total_value = portfolio.total_value + (price * quantity)
            elif action == 'SELL':
                current_quantity = current_holdings.get(symbol, 0)
                if current_quantity >= quantity:
                    current_holdings[symbol] = current_quantity - quantity
                    portfolio.total_value = portfolio.total_value - (price * quantity)
                else:
                    raise ValueError(f"Insufficient holdings for {symbol}: have {current_quantity}, trying to sell {quantity}")
            
            # Remove zero holdings
            if current_holdings.get(symbol, 0) == 0:
                del current_holdings[symbol]
            
            portfolio.holdings = current_holdings
            portfolio.last_updated = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating portfolio holdings: {e}")
            return False
    
    async def _calculate_portfolio_impact(
        self,
        user_id: int,
        trade_value: float,
        db: Session
    ) -> Dict[str, Any]:
        """Calculate the impact of trade on portfolio"""
        try:
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            if not portfolio or portfolio.total_value == 0:
                return {
                    'portfolio_value': 0,
                    'trade_impact_percent': 0,
                    'concentration_risk': 0,
                    'diversification_score': 0
                }
            
            # Calculate impact
            trade_impact_percent = (trade_value / portfolio.total_value) * 100
            
            # Calculate concentration risk
            holdings = portfolio.holdings or {}
            max_concentration = 0
            if holdings:
                max_concentration = max(holdings.values()) / sum(holdings.values()) * 100
            
            # Calculate diversification score
            diversification_score = min(100, len(holdings) * 10)  # Simple scoring
            
            return {
                'portfolio_value': portfolio.total_value,
                'trade_impact_percent': trade_impact_percent,
                'concentration_risk': max_concentration,
                'diversification_score': diversification_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio impact: {e}")
            return {}
    
    async def get_unified_performance_summary(
        self,
        user_id: int,
        days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get unified performance combining trading and portfolio"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get trading performance
            executions = db.query(TradingExecution).filter(
                TradingExecution.created_at >= cutoff_date
            ).all()
            
            # Calculate trading metrics
            trading_metrics = self._calculate_trading_metrics(executions)
            
            # Get portfolio performance
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            portfolio_metrics = self._calculate_portfolio_metrics(portfolio, days)
            
            # Calculate unified metrics
            unified_metrics = self._calculate_unified_metrics(
                trading_metrics, portfolio_metrics
            )
            
            return {
                'success': True,
                'period_days': days,
                'trading_performance': trading_metrics,
                'portfolio_performance': portfolio_metrics,
                'unified_metrics': unified_metrics,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting unified performance: {e}")
            raise
    
    def _calculate_trading_metrics(self, executions: List[TradingExecution]) -> Dict[str, Any]:
        """Calculate trading performance metrics"""
        if not executions:
            return {
                'total_trades': 0,
                'closed_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_return': 0
            }
        
        closed_trades = [e for e in executions if e.status == 'CLOSED']
        profitable_trades = [e for e in closed_trades if e.pnl_percent and e.pnl_percent > 0]
        
        total_pnl = sum(e.pnl_amount or 0 for e in closed_trades)
        win_rate = len(profitable_trades) / len(closed_trades) if closed_trades else 0
        avg_return = sum(e.pnl_percent or 0 for e in closed_trades) / len(closed_trades) if closed_trades else 0
        
        return {
            'total_trades': len(executions),
            'closed_trades': len(closed_trades),
            'profitable_trades': len(profitable_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_return': avg_return,
            'max_profit': max(e.pnl_percent or 0 for e in closed_trades) if closed_trades else 0,
            'max_loss': min(e.pnl_percent or 0 for e in closed_trades) if closed_trades else 0
        }
    
    def _calculate_portfolio_metrics(self, portfolio: PortfolioMetadata, days: int) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        if not portfolio:
            return {
                'total_value': 0,
                'holdings_count': 0,
                'diversification_score': 0,
                'concentration_risk': 0
            }
        
        holdings = portfolio.holdings or {}
        total_shares = sum(holdings.values())
        
        # Simple metrics (can be enhanced with current market data)
        diversification_score = min(100, len(holdings) * 10)
        concentration_risk = max(holdings.values()) / total_shares * 100 if holdings else 0
        
        return {
            'total_value': portfolio.total_value,
            'holdings_count': len(holdings),
            'diversification_score': diversification_score,
            'concentration_risk': concentration_risk,
            'holdings': holdings,
            'last_updated': portfolio.last_updated.isoformat() if portfolio.last_updated else None
        }
    
    def _calculate_unified_metrics(
        self, 
        trading_metrics: Dict[str, Any], 
        portfolio_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate unified performance metrics"""
        # Calculate overall score (0-100)
        trading_score = 0
        if trading_metrics['win_rate'] > 0:
            trading_score = trading_metrics['win_rate'] * 50  # 0-50 points
        
        portfolio_score = 0
        if portfolio_metrics['diversification_score'] > 0:
            portfolio_score = portfolio_metrics['diversification_score'] * 0.3  # 0-30 points
        
        risk_score = 0
        if portfolio_metrics['concentration_risk'] < 50:  # Lower risk is better
            risk_score = (50 - portfolio_metrics['concentration_risk']) * 0.4  # 0-20 points
        
        overall_score = trading_score + portfolio_score + risk_score
        
        return {
            'overall_score': min(100, overall_score),
            'trading_score': trading_score,
            'portfolio_score': portfolio_score,
            'risk_score': risk_score,
            'grade': self._get_performance_grade(overall_score),
            'recommendations': self._generate_recommendations(
                trading_metrics, portfolio_metrics, overall_score
            )
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Get performance grade based on score"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        else:
            return 'D'
    
    def _generate_recommendations(
        self, 
        trading_metrics: Dict[str, Any], 
        portfolio_metrics: Dict[str, Any], 
        overall_score: float
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Trading recommendations
        if trading_metrics['win_rate'] < 0.5:
            recommendations.append("Improve trading strategy - current win rate is below 50%")
        
        if trading_metrics['avg_return'] < 0:
            recommendations.append("Review entry/exit criteria - average return is negative")
        
        # Portfolio recommendations
        if portfolio_metrics['diversification_score'] < 50:
            recommendations.append("Increase portfolio diversification - consider adding more stocks")
        
        if portfolio_metrics['concentration_risk'] > 30:
            recommendations.append("Reduce concentration risk - avoid overexposure to single stocks")
        
        # Overall recommendations
        if overall_score < 60:
            recommendations.append("Focus on fundamentals - review both trading and portfolio strategy")
        elif overall_score > 85:
            recommendations.append("Excellent performance - consider scaling up gradually")
        
        return recommendations

# Create global instance
enhanced_trading_service = EnhancedTradingService()
