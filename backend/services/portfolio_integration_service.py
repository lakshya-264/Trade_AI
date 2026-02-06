"""
Portfolio Integration Service - Connect orders to portfolio holdings
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import logging

from core.database import get_db
from models.trading_performance_models import TradingExecution
from core.database_unified import User, PortfolioMetadata
from services.enhanced_trading_service import enhanced_trading_service
from services.order_placement_service import order_placement_service

logger = logging.getLogger(__name__)

class PortfolioIntegrationService:
    """Service for integrating order placement with portfolio holdings"""
    
    def __init__(self):
        self.holding_status = ['ACTIVE', 'CLOSED', 'PARTIAL']
        self.portfolio_sections = ['holdings', 'watchlist', 'orders', 'performance']
    
    async def place_order_and_update_portfolio(
        self,
        order_data: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Place order and immediately update portfolio holdings"""
        try:
            logger.info(f"Placing order and updating portfolio for user {user_id}")
            
            # Step 1: Place the order with analysis
            order_result = await order_placement_service.place_order_with_analysis(
                symbol=order_data['symbol'],
                order_type=order_data['order_type'],
                action=order_data['action'],
                quantity=order_data['quantity'],
                price=order_data['price'],
                user_id=user_id,
                db=db,
                signal_strength=order_data.get('signal_strength', 'MODERATE'),
                target_price=order_data.get('target_price'),
                stop_loss=order_data.get('stop_loss'),
                duration=order_data.get('duration', 'INTRADAY'),
                strategy=order_data.get('strategy', 'MANUAL'),
                confidence_score=order_data.get('confidence_score', 0.5),
                expected_holding_period=order_data.get('expected_holding_period'),
                market_conditions=order_data.get('market_conditions')
            )
            
            # Step 2: Update portfolio holdings immediately
            portfolio_update = await self._update_portfolio_holdings(
                order_result['execution'], user_id, db
            )
            
            # Step 3: Create portfolio entry record
            portfolio_entry = await self._create_portfolio_entry(
                order_result['execution'], portfolio_update, user_id, db
            )
            
            # Step 4: Update portfolio metadata
            portfolio_metadata = await self._update_portfolio_metadata(
                user_id, order_result['execution'], db
            )
            
            # Step 5: Generate portfolio performance snapshot
            performance_snapshot = await self._generate_portfolio_performance_snapshot(
                user_id, db
            )
            
            return {
                'success': True,
                'order_result': order_result,
                'portfolio_update': portfolio_update,
                'portfolio_entry': portfolio_entry,
                'portfolio_metadata': portfolio_metadata,
                'performance_snapshot': performance_snapshot,
                'message': 'Order placed and portfolio updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in place_order_and_update_portfolio: {e}")
            db.rollback()
            raise
    
    async def _update_portfolio_holdings(
        self,
        execution: TradingExecution,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Update portfolio holdings based on order execution"""
        try:
            # Get user's current portfolio
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            if not portfolio:
                # Create new portfolio if doesn't exist
                portfolio = PortfolioMetadata(
                    user_id=user_id,
                    holdings={},
                    total_value=0.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(portfolio)
                db.flush()
            
            current_holdings = portfolio.holdings or {}
            symbol = execution.symbol
            action = execution.signal_type  # BUY or SELL
            quantity = execution.quantity
            price = execution.entry_price
            
            # Update holdings based on action
            if action == 'BUY':
                if symbol in current_holdings:
                    # Update existing holding
                    holding = current_holdings[symbol]
                    old_quantity = holding['quantity']
                    old_avg_price = holding['avg_price']
                    old_total_value = holding['total_value']
                    
                    # Calculate new average price
                    new_quantity = old_quantity + quantity
                    new_total_value = old_total_value + (quantity * price)
                    new_avg_price = new_total_value / new_quantity
                    
                    current_holdings[symbol] = {
                        'quantity': new_quantity,
                        'avg_price': new_avg_price,
                        'total_value': new_total_value,
                        'last_price': price,
                        'last_updated': datetime.utcnow().isoformat(),
                        'status': 'ACTIVE',
                        'execution_ids': holding.get('execution_ids', []) + [execution.id]
                    }
                else:
                    # Create new holding
                    current_holdings[symbol] = {
                        'quantity': quantity,
                        'avg_price': price,
                        'total_value': quantity * price,
                        'last_price': price,
                        'last_updated': datetime.utcnow().isoformat(),
                        'status': 'ACTIVE',
                        'execution_ids': [execution.id],
                        'first_purchase_date': datetime.utcnow().isoformat()
                    }
            
            elif action == 'SELL':
                if symbol in current_holdings:
                    holding = current_holdings[symbol]
                    current_quantity = holding['quantity']
                    
                    if quantity >= current_quantity:
                        # Complete sell - remove holding
                        del current_holdings[symbol]
                    else:
                        # Partial sell - update holding
                        new_quantity = current_quantity - quantity
                        new_total_value = holding['total_value'] * (new_quantity / current_quantity)
                        
                        current_holdings[symbol] = {
                            'quantity': new_quantity,
                            'avg_price': holding['avg_price'],
                            'total_value': new_total_value,
                            'last_price': price,
                            'last_updated': datetime.utcnow().isoformat(),
                            'status': 'ACTIVE',
                            'execution_ids': holding.get('execution_ids', []) + [execution.id]
                        }
                else:
                    # Selling without holding - this shouldn't happen in normal flow
                    logger.warning(f"Attempted to sell {symbol} without holding")
            
            # Update portfolio metadata
            portfolio.holdings = current_holdings
            portfolio.total_value = sum(h['total_value'] for h in current_holdings.values())
            portfolio.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                'updated_holdings': current_holdings,
                'total_portfolio_value': portfolio.total_value,
                'holding_count': len(current_holdings),
                'action_performed': action,
                'symbol_affected': symbol
            }
            
        except Exception as e:
            logger.error(f"Error updating portfolio holdings: {e}")
            raise
    
    async def _create_portfolio_entry(
        self,
        execution: TradingExecution,
        portfolio_update: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Create detailed portfolio entry record"""
        try:
            portfolio_entry = {
                'execution_id': execution.id,
                'user_id': user_id,
                'symbol': execution.symbol,
                'action': execution.signal_type,
                'quantity': execution.quantity,
                'price': execution.entry_price,
                'total_value': execution.entry_value,
                'order_type': execution.order_type,
                'signal_strength': execution.signal_strength,
                'confidence_score': execution.signal_confidence,
                'expected_duration': execution.expected_duration,
                'target_price': execution.target_price,
                'stop_loss': execution.stop_loss,
                'order_metrics': execution.order_metrics,
                'market_conditions': execution.market_conditions,
                'portfolio_update': portfolio_update,
                'entry_time': execution.entry_time.isoformat(),
                'status': 'ACTIVE',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # In a real implementation, save to PortfolioEntry table
            logger.info(f"Created portfolio entry for {execution.symbol}")
            
            return portfolio_entry
            
        except Exception as e:
            logger.error(f"Error creating portfolio entry: {e}")
            raise
    
    async def _update_portfolio_metadata(
        self,
        user_id: int,
        execution: TradingExecution,
        db: Session
    ) -> Dict[str, Any]:
        """Update portfolio metadata with latest information"""
        try:
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            if not portfolio:
                return {'error': 'Portfolio not found'}
            
            # Calculate portfolio metrics
            holdings = portfolio.holdings or {}
            
            # Portfolio composition
            portfolio_composition = {}
            for symbol, holding in holdings.items():
                portfolio_composition[symbol] = {
                    'quantity': holding['quantity'],
                    'value': holding['total_value'],
                    'percentage': (holding['total_value'] / portfolio.total_value * 100) if portfolio.total_value > 0 else 0
                }
            
            # Sector allocation (simplified - would need symbol-to-sector mapping)
            sector_allocation = self._calculate_sector_allocation(holdings)
            
            # Risk metrics
            risk_metrics = self._calculate_portfolio_risk_metrics(holdings, db)
            
            # Performance metrics
            performance_metrics = await self._calculate_portfolio_performance_metrics(
                user_id, holdings, db
            )
            
            # Update portfolio metadata
            portfolio.portfolio_composition = portfolio_composition
            portfolio.sector_allocation = sector_allocation
            portfolio.risk_metrics = risk_metrics
            portfolio.performance_metrics = performance_metrics
            portfolio.last_order_symbol = execution.symbol
            portfolio.last_order_time = execution.entry_time
            portfolio.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                'portfolio_composition': portfolio_composition,
                'sector_allocation': sector_allocation,
                'risk_metrics': risk_metrics,
                'performance_metrics': performance_metrics,
                'total_value': portfolio.total_value,
                'holding_count': len(holdings)
            }
            
        except Exception as e:
            logger.error(f"Error updating portfolio metadata: {e}")
            raise
    
    def _calculate_sector_allocation(
        self,
        holdings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate sector allocation (simplified)"""
        try:
            # Simplified sector mapping - in real implementation, use comprehensive mapping
            sector_mapping = {
                'RELIANCE': 'ENERGY',
                'TCS': 'IT',
                'INFY': 'IT',
                'HDFC': 'BANKING',
                'ICICIBANK': 'BANKING',
                'SBIN': 'BANKING',
                'HINDUNILVR': 'FMCG',
                'ITC': 'FMCG',
                'MARUTI': 'AUTO',
                'TATAMOTORS': 'AUTO'
            }
            
            sector_allocation = {}
            total_value = sum(h['total_value'] for h in holdings.values())
            
            for symbol, holding in holdings.items():
                sector = sector_mapping.get(symbol, 'OTHERS')
                sector_value = holding['total_value']
                
                if sector not in sector_allocation:
                    sector_allocation[sector] = {
                        'value': 0,
                        'percentage': 0,
                        'symbols': []
                    }
                
                sector_allocation[sector]['value'] += sector_value
                sector_allocation[sector]['symbols'].append(symbol)
            
            # Calculate percentages
            for sector, data in sector_allocation.items():
                data['percentage'] = (data['value'] / total_value * 100) if total_value > 0 else 0
            
            return sector_allocation
            
        except Exception as e:
            logger.error(f"Error calculating sector allocation: {e}")
            return {}
    
    def _calculate_portfolio_risk_metrics(
        self,
        holdings: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        try:
            if not holdings:
                return {
                    'concentration_risk': 0,
                    'diversification_score': 100,
                    'volatility': 0,
                    'max_drawdown': 0
                }
            
            # Concentration risk (largest holding percentage)
            total_value = sum(h['total_value'] for h in holdings.values())
            max_holding_value = max(h['total_value'] for h in holdings.values())
            concentration_risk = (max_holding_value / total_value * 100) if total_value > 0 else 0
            
            # Diversification score (inverse of concentration risk)
            diversification_score = max(0, 100 - concentration_risk)
            
            # Simplified volatility calculation
            # In real implementation, use historical price data
            volatility = 15.0  # Placeholder
            
            # Simplified max drawdown
            max_drawdown = 5.0  # Placeholder
            
            return {
                'concentration_risk': concentration_risk,
                'diversification_score': diversification_score,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'risk_level': self._get_risk_level(concentration_risk, volatility)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk metrics: {e}")
            return {}
    
    def _get_risk_level(self, concentration_risk: float, volatility: float) -> str:
        """Determine overall risk level"""
        risk_score = (concentration_risk / 100) * 0.6 + (volatility / 30) * 0.4
        
        if risk_score > 0.7:
            return 'HIGH'
        elif risk_score > 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    async def _calculate_portfolio_performance_metrics(
        self,
        user_id: int,
        holdings: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        try:
            # Get user's recent trades
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Note: Need to add user_id to TradingExecution model
            recent_trades = db.query(TradingExecution).filter(
                and_(
                    # TradingExecution.user_id == user_id,
                    TradingExecution.status == 'CLOSED',
                    TradingExecution.created_at >= cutoff_date
                )
            ).all()
            
            if not recent_trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_return': 0,
                    'avg_return': 0,
                    'sharpe_ratio': 0,
                    'max_profit': 0,
                    'max_loss': 0
                }
            
            # Calculate performance metrics
            profitable_trades = [t for t in recent_trades if t.pnl_percent and t.pnl_percent > 0]
            win_rate = len(profitable_trades) / len(recent_trades)
            
            returns = [t.pnl_percent or 0 for t in recent_trades]
            total_return = sum(returns)
            avg_return = total_return / len(recent_trades)
            
            max_profit = max(returns)
            max_loss = min(returns)
            
            # Calculate Sharpe ratio
            if len(returns) > 1:
                avg_ret = sum(returns) / len(returns)
                variance = sum((r - avg_ret) ** 2 for r in returns) / len(returns)
                volatility = variance ** 0.5
                sharpe_ratio = avg_ret / volatility if volatility > 0 else 0
            else:
                sharpe_ratio = 0
            
            return {
                'total_trades': len(recent_trades),
                'win_rate': win_rate,
                'total_return': total_return,
                'avg_return': avg_return,
                'sharpe_ratio': sharpe_ratio,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'performance_period_days': 30
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance metrics: {e}")
            return {}
    
    async def _generate_portfolio_performance_snapshot(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Generate comprehensive portfolio performance snapshot"""
        try:
            # Get portfolio metadata
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            if not portfolio:
                return {'error': 'Portfolio not found'}
            
            # Get unified performance
            unified_performance = await enhanced_trading_service.get_unified_performance_summary(
                user_id=user_id, days=30, db=db
            )
            
            # Create snapshot
            snapshot = {
                'snapshot_time': datetime.utcnow().isoformat(),
                'portfolio_value': portfolio.total_value,
                'holding_count': len(portfolio.holdings or {}),
                'portfolio_composition': portfolio.portfolio_composition,
                'sector_allocation': portfolio.sector_allocation,
                'risk_metrics': portfolio.risk_metrics,
                'performance_metrics': portfolio.performance_metrics,
                'unified_performance': unified_performance.get('unified_metrics', {}),
                'last_updated': portfolio.updated_at.isoformat()
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error generating portfolio performance snapshot: {e}")
            raise
    
    async def get_portfolio_with_performance(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get complete portfolio with performance details"""
        try:
            # Get portfolio metadata
            portfolio = db.query(PortfolioMetadata).filter(
                PortfolioMetadata.user_id == user_id
            ).first()
            
            if not portfolio:
                return {
                    'success': True,
                    'data': {
                        'holdings': {},
                        'total_value': 0,
                        'holding_count': 0,
                        'performance': {},
                        'risk_metrics': {},
                        'sector_allocation': {}
                    },
                    'message': 'No portfolio found'
                }
            
            # Get detailed performance for each holding
            holdings_with_performance = await self._get_holdings_with_performance(
                portfolio.holdings or {}, user_id, db
            )
            
            # Get overall portfolio performance
            overall_performance = await self._calculate_overall_portfolio_performance(
                portfolio, user_id, db
            )
            
            return {
                'success': True,
                'data': {
                    'holdings': holdings_with_performance,
                    'total_value': portfolio.total_value,
                    'holding_count': len(portfolio.holdings or {}),
                    'portfolio_composition': portfolio.portfolio_composition,
                    'sector_allocation': portfolio.sector_allocation,
                    'risk_metrics': portfolio.risk_metrics,
                    'performance_metrics': portfolio.performance_metrics,
                    'overall_performance': overall_performance,
                    'last_updated': portfolio.updated_at.isoformat()
                },
                'message': 'Portfolio retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio with performance: {e}")
            raise
    
    async def _get_holdings_with_performance(
        self,
        holdings: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get holdings with individual performance metrics"""
        try:
            holdings_with_performance = {}
            
            for symbol, holding in holdings.items():
                # Get trading performance for this symbol
                symbol_performance = await self._get_symbol_performance_for_portfolio(
                    symbol, user_id, db
                )
                
                # Calculate current P&L
                current_price = holding['last_price']  # In real implementation, get current market price
                current_value = holding['quantity'] * current_price
                cost_basis = holding['total_value']
                unrealized_pnl = current_value - cost_basis
                unrealized_pnl_percent = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                holdings_with_performance[symbol] = {
                    **holding,
                    'current_price': current_price,
                    'current_value': current_value,
                    'cost_basis': cost_basis,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_percent': unrealized_pnl_percent,
                    'performance': symbol_performance,
                    'days_held': self._calculate_days_held(holding.get('first_purchase_date')),
                    'status': self._get_holding_status(unrealized_pnl_percent)
                }
            
            return holdings_with_performance
            
        except Exception as e:
            logger.error(f"Error getting holdings with performance: {e}")
            return holdings
    
    async def _get_symbol_performance_for_portfolio(
        self,
        symbol: str,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific symbol"""
        try:
            # Get all trades for this symbol
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            trades = db.query(TradingExecution).filter(
                and_(
                    # TradingExecution.user_id == user_id,
                    TradingExecution.symbol == symbol,
                    TradingExecution.created_at >= cutoff_date
                )
            ).all()
            
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'avg_return': 0,
                    'total_return': 0
                }
            
            # Calculate metrics
            closed_trades = [t for t in trades if t.status == 'CLOSED']
            profitable_trades = [t for t in closed_trades if t.pnl_percent and t.pnl_percent > 0]
            
            win_rate = len(profitable_trades) / len(closed_trades) if closed_trades else 0
            returns = [t.pnl_percent or 0 for t in closed_trades]
            avg_return = sum(returns) / len(returns) if returns else 0
            total_return = sum(returns)
            
            return {
                'total_trades': len(trades),
                'closed_trades': len(closed_trades),
                'win_rate': win_rate,
                'avg_return': avg_return,
                'total_return': total_return,
                'best_trade': max(returns) if returns else 0,
                'worst_trade': min(returns) if returns else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol performance: {e}")
            return {}
    
    def _calculate_days_held(self, first_purchase_date: Optional[str]) -> int:
        """Calculate days held for a position"""
        try:
            if not first_purchase_date:
                return 0
            
            purchase_date = datetime.fromisoformat(first_purchase_date.replace('Z', '+00:00'))
            days_held = (datetime.utcnow() - purchase_date).days
            return max(0, days_held)
            
        except Exception as e:
            logger.error(f"Error calculating days held: {e}")
            return 0
    
    def _get_holding_status(self, unrealized_pnl_percent: float) -> str:
        """Get holding status based on P&L"""
        if unrealized_pnl_percent > 5:
            return 'PROFITABLE'
        elif unrealized_pnl_percent > 0:
            return 'POSITIVE'
        elif unrealized_pnl_percent > -5:
            return 'BREAKEVEN'
        else:
            return 'LOSING'
    
    async def _calculate_overall_portfolio_performance(
        self,
        portfolio: PortfolioMetadata,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Calculate overall portfolio performance"""
        try:
            holdings = portfolio.holdings or {}
            
            if not holdings:
                return {
                    'total_invested': 0,
                    'current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'best_performer': None,
                    'worst_performer': None
                }
            
            # Calculate total invested and current value
            total_invested = sum(h['total_value'] for h in holdings.values())
            current_value = sum(h['quantity'] * h['last_price'] for h in holdings.values())
            total_pnl = current_value - total_invested
            total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            # Find best and worst performers
            performer_metrics = []
            for symbol, holding in holdings.items():
                current_price = holding['last_price']
                cost_basis = holding['total_value']
                pnl = (current_price * holding['quantity']) - cost_basis
                pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                performer_metrics.append({
                    'symbol': symbol,
                    'pnl_percent': pnl_percent,
                    'pnl': pnl
                })
            
            best_performer = max(performer_metrics, key=lambda x: x['pnl_percent']) if performer_metrics else None
            worst_performer = min(performer_metrics, key=lambda x: x['pnl_percent']) if performer_metrics else None
            
            return {
                'total_invested': total_invested,
                'current_value': current_value,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'best_performer': best_performer,
                'worst_performer': worst_performer,
                'daily_change': self._calculate_daily_change(holdings),
                'weekly_change': self._calculate_weekly_change(holdings)
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall portfolio performance: {e}")
            return {}
    
    def _calculate_daily_change(self, holdings: Dict[str, Any]) -> float:
        """Calculate daily portfolio change (simplified)"""
        # In real implementation, use actual price changes
        return 0.5  # Placeholder
    
    def _calculate_weekly_change(self, holdings: Dict[str, Any]) -> float:
        """Calculate weekly portfolio change (simplified)"""
        # In real implementation, use actual price changes
        return 2.1  # Placeholder

# Create global instance
portfolio_integration_service = PortfolioIntegrationService()
