"""
Unified Portfolio Management Service
Combines stock holdings tracking with asset allocation optimization
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import math
import logging
import numpy as np
from sqlalchemy import text
import sqlalchemy.exc as sa_exc

logger = logging.getLogger(__name__)

class PortfolioAllocationService:
    """Service for portfolio allocation and rebalancing guidance"""
    
    def __init__(self):
        self.allocation_strategies = self._initialize_allocation_strategies()
        self.rebalancing_triggers = self._initialize_rebalancing_triggers()
    
    # ========== Portfolio Holdings Management (from Portfolio feature) ==========
    
    async def get_holdings(self, user_id: int, db) -> Dict[str, Any]:
        """Get user's stock holdings with live price updates and PnL calculations"""
        try:
            from core.database_unified import Portfolio
            from core.data_service import data_service
            import sqlalchemy.exc as sa_exc
            
            # Check if database connection is valid
            try:
                db.execute(text("SELECT 1"))
            except Exception as conn_error:
                logger.error(f"Database connection error: {conn_error}")
                return {
                    "success": False,
                    "error": "Database connection error. Please try again.",
                    "holdings": [],
                    "total_value": 0.0,
                    "total_pnl": 0.0
                }
            
            logger.info(f"Fetching holdings for user_id: {user_id}")
            portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            logger.info(f"Found {len(portfolio_items)} portfolio items for user {user_id}")
            
            if not portfolio_items:
                return {
                    "success": True,
                    "holdings": [],
                    "total_value": 0.0,
                    "total_pnl": 0.0,
                    "total_pnl_percent": 0.0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            holdings_data = []
            total_value = 0.0
            total_invested = 0.0
            total_pnl = 0.0
            
            for item in portfolio_items:
                try:
                    # Fetch live price for the symbol
                    live_quote = await data_service.get_quote(item.symbol, exchange="NSE")
                    live_price = live_quote.get("last_price", item.current_price) if live_quote else item.current_price
                    
                    # Update current price in database
                    item.current_price = live_price
                    db.commit()
                    
                except Exception as e:
                    logger.warning(f"Could not fetch live price for {item.symbol}: {e}")
                    live_price = item.current_price
                
                # Calculate metrics with live price
                current_value = item.quantity * live_price
                invested_value = item.quantity * item.average_price
                pnl = current_value - invested_value
                pnl_percent = (pnl / invested_value * 100) if invested_value > 0 else 0
                
                total_value += current_value
                total_invested += invested_value
                total_pnl += pnl
                
                holdings_data.append({
                    "symbol": item.symbol,
                    "quantity": item.quantity,
                    "average_price": item.average_price,
                    "current_price": live_price,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "total_value": current_value,
                    "invested_value": invested_value,
                    "currency": "INR",
                    "currency_symbol": "₹",
                    "formatted_average_price": f"₹{item.average_price:,.2f}",
                    "formatted_current_price": f"₹{live_price:,.2f}",
                    "formatted_pnl": f"₹{pnl:+,.2f}",
                    "formatted_total_value": f"₹{current_value:,.2f}",
                    "created_at": item.created_at.isoformat() if item.created_at else datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
            
            total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            return {
                "success": True,
                "holdings": holdings_data,
                "total_value": total_value,
                "total_invested": total_invested,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "currency": "INR",
                "currency_symbol": "₹",
                "formatted_total_value": f"₹{total_value:,.2f}",
                "formatted_total_pnl": f"₹{total_pnl:+,.2f}",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific SQLite connection errors
            if isinstance(e, (sa_exc.ProgrammingError, sa_exc.OperationalError)) and "closed database" in error_msg.lower():
                logger.error(f"Database connection closed error: {e}")
                error_msg = "Database connection error. Please refresh the page."
            else:
                logger.error(f"Error fetching holdings: {e}")
            
            return {
                "success": False,
                "error": error_msg,
                "holdings": [],
                "total_value": 0.0,
                "total_pnl": 0.0
            }
    
    async def add_demo_holding(self, user_id: int, holding_data: Dict[str, Any], db) -> Dict[str, Any]:
        """Add a demo holding to the portfolio (saved to database)"""
        try:
            from core.database_unified import Portfolio
            from core.data_service import data_service
            
            symbol = holding_data.get("symbol", "").upper()
            quantity = int(holding_data.get("quantity", 0))
            average_price = float(holding_data.get("average_price", 0))
            
            if not symbol or quantity <= 0 or average_price <= 0:
                return {"success": False, "error": "Invalid holding data"}
            
            # Fetch current price
            try:
                quote = await data_service.get_quote(symbol, exchange="NSE")
                current_price = float(quote.get("last_price", average_price)) if quote else average_price
            except:
                current_price = average_price
            
            # Check if holding already exists
            existing = db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.symbol == symbol
            ).first()
            
            if existing:
                # Update existing holding
                total_quantity = existing.quantity + quantity
                total_value = (existing.quantity * existing.average_price) + (quantity * average_price)
                new_avg_price = total_value / total_quantity
                
                existing.quantity = total_quantity
                existing.average_price = new_avg_price
                existing.current_price = current_price
                existing.updated_at = datetime.utcnow()
            else:
                # Create new holding
                new_holding = Portfolio(
                    user_id=user_id,
                    symbol=symbol,
                    quantity=quantity,
                    average_price=average_price,
                    current_price=current_price,
                    pnl=0.0
                )
                db.add(new_holding)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Demo holding added: {quantity} shares of {symbol}",
                "symbol": symbol,
                "quantity": quantity,
                "average_price": average_price,
                "current_price": current_price
            }
        except Exception as e:
            logger.error(f"Error adding demo holding: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}

    async def update_portfolio_on_order(self, user_id: int, order_data: Dict[str, Any], db) -> Dict[str, Any]:
        """Update portfolio after order execution (from Portfolio feature)"""
        try:
            from core.database_unified import Portfolio
            
            symbol = order_data.get("symbol")
            order_type = order_data.get("order_type")  # "BUY" or "SELL"
            quantity = order_data.get("quantity", 0)
            price = order_data.get("price", 0.0)
            
            if not symbol or not order_type or quantity <= 0 or price <= 0:
                return {"success": False, "error": "Invalid order data"}
            
            # Check if position already exists
            existing_position = db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.symbol == symbol
            ).first()
            
            if existing_position:
                if order_type == "BUY":
                    # Add to existing position - calculate new average price
                    total_quantity = existing_position.quantity + quantity
                    total_value = (existing_position.quantity * existing_position.average_price) + \
                                 (quantity * price)
                    new_average_price = total_value / total_quantity
                    
                    existing_position.quantity = total_quantity
                    existing_position.average_price = new_average_price
                    existing_position.current_price = price
                    existing_position.updated_at = datetime.utcnow()
                else:  # SELL
                    # Reduce position
                    if existing_position.quantity < quantity:
                        return {"success": False, "error": "Insufficient quantity to sell"}
                    
                    existing_position.quantity -= quantity
                    existing_position.current_price = price
                    existing_position.updated_at = datetime.utcnow()
                    
                    if existing_position.quantity <= 0:
                        db.delete(existing_position)
            else:
                if order_type == "BUY":
                    # Create new position
                    new_position = Portfolio(
                        user_id=user_id,
                        symbol=symbol,
                        quantity=quantity,
                        average_price=price,
                        current_price=price,
                        pnl=0.0
                    )
                    db.add(new_position)
                else:
                    return {"success": False, "error": "Cannot sell stock not in portfolio"}
            
            db.commit()
            return {"success": True, "message": f"Portfolio updated for {order_type} order of {quantity} {symbol}"}
            
        except Exception as e:
            logger.error(f"Error updating portfolio on order: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def calculate_allocation_from_holdings(self, holdings: List[Dict[str, Any]], total_value: float) -> Dict[str, Any]:
        """Calculate asset class allocation from individual holdings"""
        try:
            if total_value == 0:
                return {
                    "equity": 0.0,
                    "bonds": 0.0,
                    "cash": 0.0,
                    "commodities": 0.0,
                    "total": 0.0
                }
            
            # For now, all stocks are considered equity
            # In future, can categorize by sector or asset class
            equity_value = sum(h.get("total_value", 0) for h in holdings)
            equity_percent = (equity_value / total_value * 100) if total_value > 0 else 0
            
            # Cash and bonds would come from other sources (not in current holdings)
            # This is a simplified version - can be enhanced
            return {
                "equity": round(equity_percent, 1),
                "bonds": 0.0,  # Can be enhanced to track bonds separately
                "cash": round(100 - equity_percent, 1) if equity_percent < 100 else 0.0,
                "commodities": 0.0,  # Can be enhanced to track commodities
                "total": 100.0
            }
        except Exception as e:
            logger.error(f"Error calculating allocation from holdings: {e}")
            return {
                "equity": 0.0,
                "bonds": 0.0,
                "cash": 0.0,
                "commodities": 0.0,
                "total": 0.0
            }
    
    def _initialize_allocation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize allocation strategies"""
        return {
            'conservative': {
                'name': 'Conservative',
                'description': 'Capital preservation focus',
                'equity_range': (25, 40),
                'bond_range': (60, 75),
                'cash_range': (5, 10),
                'risk_tolerance': 'Low',
                'time_horizon': 'Short to Medium'
            },
            'moderate': {
                'name': 'Moderate',
                'description': 'Balanced growth and income',
                'equity_range': (50, 70),
                'bond_range': (30, 50),
                'cash_range': (0, 10),
                'risk_tolerance': 'Medium',
                'time_horizon': 'Medium to Long'
            },
            'aggressive': {
                'name': 'Aggressive',
                'description': 'Growth focus',
                'equity_range': (70, 90),
                'bond_range': (10, 30),
                'cash_range': (0, 5),
                'risk_tolerance': 'High',
                'time_horizon': 'Long'
            },
            'dynamic': {
                'name': 'Dynamic',
                'description': 'Market condition based',
                'equity_range': (25, 90),
                'bond_range': (10, 75),
                'cash_range': (0, 15),
                'risk_tolerance': 'Variable',
                'time_horizon': 'Flexible'
            }
        }
    
    def _initialize_rebalancing_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rebalancing triggers"""
        return {
            'threshold': {
                'name': 'Threshold Rebalancing',
                'description': 'Rebalance when allocation drifts beyond threshold',
                'equity_threshold': 0.05,  # 5% drift
                'bond_threshold': 0.05,
                'frequency': 'As needed'
            },
            'calendar': {
                'name': 'Calendar Rebalancing',
                'description': 'Rebalance at regular intervals',
                'frequency': 'Quarterly',
                'months': [3, 6, 9, 12]
            },
            'hybrid': {
                'name': 'Hybrid Rebalancing',
                'description': 'Combination of threshold and calendar',
                'threshold': 0.05,
                'frequency': 'Quarterly',
                'max_drift': 0.10  # Force rebalance at 10% drift
            }
        }
    
    # New: expose strategies as list for API
    async def get_allocation_strategies(self) -> Dict[str, Any]:
        return {
            'strategies': [
                { 'id': key, **value } for key, value in self.allocation_strategies.items()
            ]
        }

    def get_allocation_guidance(self, 
                              user_profile: Dict[str, Any],
                              market_conditions: Dict[str, Any],
                              current_portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Get portfolio allocation guidance"""
        try:
            # Determine appropriate strategy
            strategy = self._determine_strategy(user_profile, market_conditions)
            
            # Calculate target allocation
            target_allocation = self._calculate_target_allocation(strategy, market_conditions)
            
            # Analyze current vs target
            allocation_analysis = self._analyze_allocation(current_portfolio, target_allocation)
            
            # Generate rebalancing recommendations
            rebalancing_recommendations = self._generate_rebalancing_recommendations(
                allocation_analysis, strategy
            )
            
            return {
                'strategy': strategy,
                'target_allocation': target_allocation,
                'current_allocation': current_portfolio.get('allocation', {}),
                'allocation_analysis': allocation_analysis,
                'rebalancing_recommendations': rebalancing_recommendations,
                'market_conditions': market_conditions,
                'guidance_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f"Allocation guidance error: {str(e)}",
                'user_profile': user_profile
            }
    
    def _determine_strategy(self, user_profile: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Determine appropriate allocation strategy"""
        try:
            age = user_profile.get('age', 35)
            risk_tolerance = user_profile.get('risk_tolerance', 'medium')
            time_horizon = user_profile.get('time_horizon', 'medium')
            income_stability = user_profile.get('income_stability', 'stable')
            
            # Base strategy selection
            if risk_tolerance == 'low' or age > 60:
                base_strategy = 'conservative'
            elif risk_tolerance == 'high' and age < 40:
                base_strategy = 'aggressive'
            else:
                base_strategy = 'moderate'
            
            # Adjust for market conditions
            market_volatility = market_conditions.get('volatility', 'medium')
            market_valuation = market_conditions.get('valuation', 'fair')
            
            if market_volatility == 'high' and market_valuation == 'expensive':
                # Reduce equity allocation
                if base_strategy == 'aggressive':
                    base_strategy = 'moderate'
                elif base_strategy == 'moderate':
                    base_strategy = 'conservative'
            
            elif market_volatility == 'low' and market_valuation == 'cheap':
                # Increase equity allocation
                if base_strategy == 'conservative':
                    base_strategy = 'moderate'
                elif base_strategy == 'moderate':
                    base_strategy = 'aggressive'
            
            strategy_config = self.allocation_strategies[base_strategy].copy()
            strategy_config['strategy_id'] = base_strategy
            
            return strategy_config
            
        except Exception as e:
            return self.allocation_strategies['moderate']
    
    def _calculate_target_allocation(self, strategy: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate target allocation based on strategy and market conditions"""
        try:
            strategy_id = strategy.get('strategy_id', 'moderate')
            
            if strategy_id == 'dynamic':
                return self._calculate_dynamic_allocation(market_conditions)
            
            # Get base ranges
            equity_range = strategy['equity_range']
            bond_range = strategy['bond_range']
            cash_range = strategy['cash_range']
            
            # Calculate specific targets within ranges
            market_volatility = market_conditions.get('volatility', 'medium')
            market_valuation = market_conditions.get('valuation', 'fair')
            
            # Adjust for market conditions
            if market_volatility == 'high':
                equity_target = equity_range[0] + (equity_range[1] - equity_range[0]) * 0.3
                bond_target = bond_range[1] - (bond_range[1] - bond_range[0]) * 0.2
            elif market_volatility == 'low':
                equity_target = equity_range[1] - (equity_range[1] - equity_range[0]) * 0.2
                bond_target = bond_range[0] + (bond_range[1] - bond_range[0]) * 0.3
            else:
                equity_target = sum(equity_range) / 2
                bond_target = sum(bond_range) / 2
            
            # Adjust for valuation
            if market_valuation == 'expensive':
                equity_target *= 0.9
                bond_target *= 1.1
            elif market_valuation == 'cheap':
                equity_target *= 1.1
                bond_target *= 0.9
            
            # Ensure allocations sum to 100%
            total = equity_target + bond_target
            equity_target = (equity_target / total) * 100
            bond_target = (bond_target / total) * 100
            
            cash_target = sum(cash_range) / 2
            
            return {
                'equity': round(equity_target, 1),
                'bonds': round(bond_target, 1),
                'cash': round(cash_target, 1),
                'total': 100.0,
                'reasoning': f"Based on {strategy['name']} strategy and current market conditions"
            }
            
        except Exception as e:
            return {
                'equity': 60.0,
                'bonds': 35.0,
                'cash': 5.0,
                'total': 100.0,
                'error': f"Target allocation error: {str(e)}"
            }
    
    def _calculate_dynamic_allocation(self, market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate dynamic allocation based on market conditions"""
        try:
            # Market indicators
            pe_ratio = market_conditions.get('pe_ratio', 20)
            volatility = market_conditions.get('volatility_index', 20)
            yield_spread = market_conditions.get('yield_spread', 0.02)
            
            # Dynamic equity allocation based on market conditions
            # Lower PE = higher equity allocation
            pe_factor = max(0.3, min(1.0, 25 / pe_ratio))
            
            # Lower volatility = higher equity allocation
            vol_factor = max(0.3, min(1.0, 1 - (volatility - 10) / 30))
            
            # Higher yield spread = higher equity allocation
            yield_factor = max(0.5, min(1.2, 1 + (yield_spread - 0.01) * 10))
            
            # Combine factors
            equity_multiplier = (pe_factor + vol_factor + yield_factor) / 3
            
            # Calculate allocations
            base_equity = 50  # Base 50% equity
            equity_target = base_equity * equity_multiplier
            equity_target = max(25, min(90, equity_target))  # Constrain between 25-90%
            
            bond_target = 100 - equity_target - 5  # Leave 5% cash
            bond_target = max(10, min(70, bond_target))  # Constrain between 10-70%
            
            cash_target = 100 - equity_target - bond_target
            
            return {
                'equity': round(equity_target, 1),
                'bonds': round(bond_target, 1),
                'cash': round(cash_target, 1),
                'total': 100.0,
                'reasoning': f"Dynamic allocation based on PE ratio ({pe_ratio}), volatility ({volatility}), and yield spread ({yield_spread})"
            }
            
        except Exception as e:
            return {
                'equity': 60.0,
                'bonds': 35.0,
                'cash': 5.0,
                'total': 100.0,
                'error': f"Dynamic allocation error: {str(e)}"
            }
    
    def _analyze_allocation(self, current_portfolio: Dict[str, Any], target_allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current vs target allocation"""
        try:
            current = current_portfolio.get('allocation', {})
            
            equity_drift = current.get('equity', 0) - target_allocation['equity']
            bond_drift = current.get('bonds', 0) - target_allocation['bonds']
            cash_drift = current.get('cash', 0) - target_allocation['cash']
            
            max_drift = max(abs(equity_drift), abs(bond_drift), abs(cash_drift))
            
            # Determine if rebalancing is needed
            rebalancing_threshold = 5.0  # 5% drift threshold
            needs_rebalancing = max_drift > rebalancing_threshold
            
            return {
                'equity_drift': round(equity_drift, 1),
                'bond_drift': round(bond_drift, 1),
                'cash_drift': round(cash_drift, 1),
                'max_drift': round(max_drift, 1),
                'needs_rebalancing': needs_rebalancing,
                'drift_severity': self._assess_drift_severity(max_drift)
            }
            
        except Exception as e:
            return {
                'error': f"Allocation analysis error: {str(e)}",
                'needs_rebalancing': False
            }
    
    def _assess_drift_severity(self, max_drift: float) -> str:
        """Assess severity of allocation drift"""
        if max_drift <= 2:
            return 'Minimal'
        elif max_drift <= 5:
            return 'Moderate'
        elif max_drift <= 10:
            return 'Significant'
        else:
            return 'Severe'
    
    def _generate_rebalancing_recommendations(self, 
                                            allocation_analysis: Dict[str, Any],
                                            strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rebalancing recommendations"""
        try:
            if not allocation_analysis.get('needs_rebalancing', False):
                return {
                    'action': 'No Action Required',
                    'reasoning': 'Portfolio allocation is within acceptable range',
                    'next_review': 'Next quarter or if drift exceeds 5%'
                }
            
            # Generate specific recommendations
            recommendations = []
            
            equity_drift = allocation_analysis.get('equity_drift', 0)
            bond_drift = allocation_analysis.get('bond_drift', 0)
            cash_drift = allocation_analysis.get('cash_drift', 0)
            
            if equity_drift > 0:
                recommendations.append(f"Reduce equity allocation by {abs(equity_drift):.1f}%")
            elif equity_drift < 0:
                recommendations.append(f"Increase equity allocation by {abs(equity_drift):.1f}%")
            
            if bond_drift > 0:
                recommendations.append(f"Reduce bond allocation by {abs(bond_drift):.1f}%")
            elif bond_drift < 0:
                recommendations.append(f"Increase bond allocation by {abs(bond_drift):.1f}%")
            
            if cash_drift > 0:
                recommendations.append(f"Reduce cash allocation by {abs(cash_drift):.1f}%")
            elif cash_drift < 0:
                recommendations.append(f"Increase cash allocation by {abs(cash_drift):.1f}%")
            
            # Determine urgency
            drift_severity = allocation_analysis.get('drift_severity', 'Minimal')
            if drift_severity in ['Significant', 'Severe']:
                urgency = 'High'
                timeline = 'Within 1-2 weeks'
            else:
                urgency = 'Medium'
                timeline = 'Within 1 month'
            
            return {
                'action': 'Rebalance Portfolio',
                'urgency': urgency,
                'timeline': timeline,
                'recommendations': recommendations,
                'reasoning': f"Portfolio drift of {allocation_analysis.get('max_drift', 0):.1f}% exceeds threshold",
                'strategy': strategy['name'],
                'next_review': 'Monthly or if drift exceeds 5%'
            }
            
        except Exception as e:
            return {
                'action': 'Review Portfolio',
                'urgency': 'Low',
                'reasoning': f'Rebalancing recommendation error: {str(e)}'
            }
    
    def create_dca_plan(self, 
                       symbol: str,
                       amount: float,
                       frequency: str,
                       duration_months: int,
                       user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create Rupee-Cost Averaging (RCA) plan"""
        try:
            # Validate inputs
            if amount <= 0 or duration_months <= 0:
                return {'error': 'Invalid amount or duration'}
            
            # Calculate schedule
            frequency_map = {
                'weekly': 4.33,  # Average weeks per month
                'monthly': 1,
                'quarterly': 0.33
            }
            
            intervals_per_month = frequency_map.get(frequency, 1)
            total_intervals = int(duration_months * intervals_per_month)
            amount_per_interval = amount / total_intervals
            
            # Generate schedule
            schedule = []
            current_date = datetime.utcnow()
            
            for i in range(total_intervals):
                if frequency == 'weekly':
                    interval_date = current_date + timedelta(weeks=i)
                elif frequency == 'monthly':
                    interval_date = current_date + timedelta(days=30*i)
                else:  # quarterly
                    interval_date = current_date + timedelta(days=90*i)
                
                schedule.append({
                    'interval': i + 1,
                    'date': interval_date.strftime('%Y-%m-%d'),
                    'amount': round(amount_per_interval, 2),
                    'symbol': symbol
                })
            
            # Calculate expected results
            expected_total_invested = amount
            expected_shares = expected_total_invested / 100  # Assuming ₹100 average price
            
            return {
                'symbol': symbol,
                'total_amount': amount,
                'frequency': frequency,
                'duration_months': duration_months,
                'amount_per_interval': round(amount_per_interval, 2),
                'total_intervals': total_intervals,
                'schedule': schedule,
                'expected_results': {
                    'total_invested': expected_total_invested,
                    'expected_shares': round(expected_shares, 2),
                    'average_price': 100  # Placeholder
                },
                'benefits': [
                    'Reduces impact of market volatility',
                    'Eliminates timing risk',
                    'Builds discipline in investing',
                    'Smooths out market fluctuations'
                ],
                'created_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f"DCA plan creation error: {str(e)}",
                'symbol': symbol
            }

    async def optimize_allocation(
        self,
        user_preferences: Dict[str, Any],
        risk_tolerance: str = "medium",
        investment_amount: float = 100000
    ) -> Dict[str, Any]:
        """Optimize portfolio allocation using AI"""
        try:
            # Determine strategy based on risk tolerance
            strategy = self.allocation_strategies.get(risk_tolerance.lower(), self.allocation_strategies['moderate'])
            
            # Calculate target allocation
            market_conditions = user_preferences.get("market_conditions", {
                "volatility": "medium",
                "valuation": "fair"
            })
            
            target_allocation = self._calculate_target_allocation(strategy, market_conditions)
            
            # Generate recommendations
            recommendations = {
                "strategy": strategy['name'],
                "target_allocation": target_allocation,
                "investment_amount": investment_amount,
                "recommended_breakdown": {
                    "equity": {
                        "amount": investment_amount * (target_allocation['equity'] / 100),
                        "percentage": target_allocation['equity']
                    },
                    "bonds": {
                        "amount": investment_amount * (target_allocation['bonds'] / 100),
                        "percentage": target_allocation['bonds']
                    },
                    "cash": {
                        "amount": investment_amount * (target_allocation['cash'] / 100),
                        "percentage": target_allocation['cash']
                    }
                },
                "reasoning": f"Based on {risk_tolerance} risk tolerance and current market conditions"
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error optimizing allocation: {e}")
            return {
                "error": str(e),
                "target_allocation": {
                    "equity": 60.0,
                    "bonds": 35.0,
                    "cash": 5.0
                }
            }
    
    async def rebalance_portfolio(
        self,
        current_portfolio: Dict[str, Any],
        frequency: str = "quarterly"
    ) -> Dict[str, Any]:
        """Rebalance existing portfolio"""
        try:
            current_allocation = current_portfolio.get("allocation", {})
            target_allocation = current_portfolio.get("target_allocation", {
                "equity": 60.0,
                "bonds": 35.0,
                "cash": 5.0
            })
            
            # Analyze allocation drift
            allocation_analysis = self._analyze_allocation(
                {"allocation": current_allocation},
                target_allocation
            )
            
            # Generate rebalancing recommendations
            rebalancing_recommendations = self._generate_rebalancing_recommendations(
                allocation_analysis,
                {"name": "Current Strategy"}
            )
            
            return {
                "current_allocation": current_allocation,
                "target_allocation": target_allocation,
                "allocation_analysis": allocation_analysis,
                "rebalancing_recommendations": rebalancing_recommendations,
                "frequency": frequency,
                "last_rebalanced": current_portfolio.get("last_rebalanced", datetime.utcnow().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {e}")
            return {
                "error": str(e),
                "rebalancing_needed": False
            }

    async def get_ai_signals_from_reports(self, user_id: int, db) -> Dict[str, Any]:
        """Get AI signals from research reports for portfolio holdings"""
        try:
            from services.comprehensive_report_generator import ComprehensiveReportGenerator
            from core.database_unified import Portfolio
            
            holdings = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            
            if not holdings:
                return {
                    "success": True,
                    "signals": [],
                    "message": "No holdings found"
                }
            
            report_generator = ComprehensiveReportGenerator()
            ai_signals = []
            
            for holding in holdings:
                try:
                    # Generate research report for each holding
                    report = await report_generator.generate_comprehensive_report(
                        symbol=holding.symbol,
                        db=db,
                        timeframe="1D"
                    )
                    
                    # Extract signals from report
                    sections = report.get("sections", {})
                    price_predictions = sections.get("price_predictions", {})
                    recommendation = sections.get("recommendation", {})
                    risk_assessment = sections.get("risk_assessment", {})
                    
                    # Get prediction data
                    pred_1m = price_predictions.get("1M", {})
                    pred_3m = price_predictions.get("3M", {})
                    
                    signal = {
                        "symbol": holding.symbol,
                        "action": recommendation.get("action", "HOLD"),
                        "confidence": recommendation.get("confidence", 0.5),
                        "price_target_1m": pred_1m.get("expected_price"),
                        "price_target_3m": pred_3m.get("expected_price"),
                        "current_price": holding.current_price,
                        "risk_level": risk_assessment.get("overall_risk", "MEDIUM"),
                        "reasoning": recommendation.get("summary", ""),
                        "report_date": report.get("report_date", datetime.utcnow().isoformat())
                    }
                    ai_signals.append(signal)
                except Exception as e:
                    logger.warning(f"Could not generate report for {holding.symbol}: {e}")
                    continue
            
            return {
                "success": True,
                "signals": ai_signals,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting AI signals from reports: {e}")
            return {"success": False, "signals": [], "error": str(e)}

    async def calculate_real_risk_metrics(self, user_id: int, db, period_days: int = 252) -> Dict[str, Any]:
        """Calculate real Sharpe ratio, Beta, and other risk metrics from historical data"""
        try:
            from core.database_unified import Portfolio
            from core.data_service import data_service
            
            holdings = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            
            if not holdings:
                return {"success": False, "error": "No holdings found"}
            
            # Get historical prices for all holdings
            portfolio_returns_list = []
            benchmark_returns = []
            
            # Fetch historical data for each holding
            for holding in holdings:
                try:
                    hist_data = await data_service.get_historical_data(
                        symbol=holding.symbol,
                        exchange="NSE",
                        period=f"{period_days}d"
                    )
                    
                    if hist_data and len(hist_data) > 1:
                        prices = [float(d.get("close", 0)) for d in hist_data if d.get("close")]
                        if len(prices) > 1:
                            returns = np.diff(prices) / np.array(prices[:-1])  # Daily returns
                            portfolio_returns_list.append(returns.tolist())
                except Exception as e:
                    logger.warning(f"Could not fetch historical data for {holding.symbol}: {e}")
                    continue
            
            # Get benchmark (NIFTY50) returns
            try:
                benchmark_data = await data_service.get_historical_data(
                    symbol="NIFTY50",
                    exchange="NSE",
                    period=f"{period_days}d"
                )
                if benchmark_data and len(benchmark_data) > 1:
                    benchmark_prices = [float(d.get("close", 0)) for d in benchmark_data if d.get("close")]
                    if len(benchmark_prices) > 1:
                        benchmark_returns = (np.diff(benchmark_prices) / np.array(benchmark_prices[:-1])).tolist()
            except Exception as e:
                logger.warning(f"Could not fetch benchmark data: {e}")
            
            if not portfolio_returns_list:
                return {"success": False, "error": "Insufficient historical data"}
            
            # Calculate portfolio weighted returns
            total_value = sum(h.quantity * h.current_price for h in holdings)
            weights = []
            aligned_returns = []
            
            for i, holding in enumerate(holdings):
                if i < len(portfolio_returns_list) and total_value > 0:
                    weight = (holding.quantity * holding.current_price) / total_value
                    weights.append(weight)
                    aligned_returns.append(portfolio_returns_list[i])
            
            if not aligned_returns:
                return {"success": False, "error": "No valid returns data"}
            
            # Align returns arrays to same length
            min_length = min(len(r) for r in aligned_returns)
            aligned_returns = [r[:min_length] for r in aligned_returns]
            weights = weights[:len(aligned_returns)]
            
            # Normalize weights
            total_weight = sum(weights)
            weights = [w / total_weight if total_weight > 0 else 0 for w in weights]
            
            # Weighted portfolio returns
            portfolio_daily_returns = np.array([np.array(r) * w for r, w in zip(aligned_returns, weights)]).sum(axis=0)
            
            # Calculate metrics
            risk_free_rate = 0.06 / 252  # 6% annual, daily rate
            mean_return = np.mean(portfolio_daily_returns)
            std_return = np.std(portfolio_daily_returns)
            
            # Sharpe Ratio
            sharpe_ratio = (mean_return - risk_free_rate) / std_return * np.sqrt(252) if std_return > 0 else 0
            
            # Beta (correlation with benchmark)
            beta = 1.0
            if len(benchmark_returns) > 0 and len(portfolio_daily_returns) > 0:
                min_len = min(len(benchmark_returns), len(portfolio_daily_returns))
                benchmark_aligned = np.array(benchmark_returns[:min_len])
                portfolio_aligned = portfolio_daily_returns[:min_len]
                
                covariance = np.cov(portfolio_aligned, benchmark_aligned)[0][1]
                benchmark_variance = np.var(benchmark_aligned)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
            
            # Max Drawdown
            cumulative = np.cumprod(1 + portfolio_daily_returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
            
            # Volatility (annualized)
            volatility = std_return * np.sqrt(252) * 100
            
            return {
                "success": True,
                "sharpe_ratio": round(float(sharpe_ratio), 2),
                "beta": round(float(beta), 2),
                "max_drawdown": round(float(max_drawdown), 2),
                "volatility": round(float(volatility), 2),
                "annualized_return": round(float(mean_return * 252 * 100), 2),
                "period_days": period_days,
                "calculated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {"success": False, "error": str(e)}

    async def get_sector_allocation(self, user_id: int, db) -> Dict[str, Any]:
        """Map holdings to actual sectors and calculate sector allocation"""
        try:
            from core.database_unified import Portfolio, StockMaster
            
            holdings = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            
            if not holdings:
                return {
                    "success": True,
                    "sector_allocation": {},
                    "total_value": 0.0,
                    "message": "No holdings found"
                }
            
            sector_allocation = {}
            total_value = 0.0
            
            for holding in holdings:
                # Get sector from StockMaster
                stock = db.query(StockMaster).filter(StockMaster.symbol == holding.symbol).first()
                sector = stock.sector if stock and stock.sector else "Unknown"
                
                holding_value = holding.quantity * holding.current_price
                total_value += holding_value
                
                if sector not in sector_allocation:
                    sector_allocation[sector] = {
                        "value": 0.0,
                        "percentage": 0.0,
                        "holdings": []
                    }
                
                sector_allocation[sector]["value"] += holding_value
                sector_allocation[sector]["holdings"].append({
                    "symbol": holding.symbol,
                    "value": holding_value,
                    "quantity": holding.quantity,
                    "current_price": holding.current_price
                })
            
            # Calculate percentages
            for sector in sector_allocation:
                sector_allocation[sector]["percentage"] = (
                    sector_allocation[sector]["value"] / total_value * 100
                ) if total_value > 0 else 0
            
            return {
                "success": True,
                "sector_allocation": sector_allocation,
                "total_value": total_value,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting sector allocation: {e}")
            return {"success": False, "error": str(e)}

    async def get_volume_analysis(self, user_id: int, db) -> Dict[str, Any]:
        """Get real volume analysis for portfolio holdings"""
        try:
            from core.database_unified import Portfolio
            from core.data_service import data_service
            
            holdings = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            
            if not holdings:
                return {
                    "success": True,
                    "analysis": {
                        "total_volume": 0,
                        "average_volume": 0,
                        "volume_trend": "NEUTRAL",
                        "high_volume_stocks": [],
                        "low_volume_stocks": [],
                        "volume_signals": []
                    },
                    "message": "No holdings found"
                }
            
            volume_analysis = {
                "total_volume": 0,
                "average_volume": 0,
                "volume_trend": "NEUTRAL",
                "high_volume_stocks": [],
                "low_volume_stocks": [],
                "volume_signals": [],
                "stock_details": []
            }
            
            stock_volumes = []
            
            for holding in holdings:
                try:
                    quote = await data_service.get_quote(holding.symbol, exchange="NSE")
                    if quote and "error" not in quote:
                        current_volume = int(quote.get("volume", 0))
                        avg_volume = int(quote.get("average_volume", 0)) or current_volume
                        
                        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                        
                        stock_volumes.append({
                            "symbol": holding.symbol,
                            "current_volume": current_volume,
                            "average_volume": avg_volume,
                            "volume_ratio": round(volume_ratio, 2),
                            "volume_trend": "HIGH" if volume_ratio > 1.5 else "LOW" if volume_ratio < 0.5 else "NORMAL"
                        })
                        
                        volume_analysis["total_volume"] += current_volume
                        
                        if volume_ratio > 1.5:
                            volume_analysis["high_volume_stocks"].append(holding.symbol)
                            volume_analysis["volume_signals"].append({
                                "symbol": holding.symbol,
                                "signal": "VOLUME_BREAKOUT",
                                "strength": "HIGH" if volume_ratio > 2.0 else "MEDIUM",
                                "volume_ratio": round(volume_ratio, 2)
                            })
                        elif volume_ratio < 0.5:
                            volume_analysis["low_volume_stocks"].append(holding.symbol)
                except Exception as e:
                    logger.warning(f"Could not fetch volume for {holding.symbol}: {e}")
                    continue
            
            if stock_volumes:
                volume_analysis["average_volume"] = volume_analysis["total_volume"] / len(stock_volumes) if stock_volumes else 0
                volume_analysis["stock_details"] = stock_volumes
                
                # Determine overall trend
                high_volume_count = len(volume_analysis["high_volume_stocks"])
                if high_volume_count > len(stock_volumes) * 0.5:
                    volume_analysis["volume_trend"] = "INCREASING"
                elif high_volume_count < len(stock_volumes) * 0.2:
                    volume_analysis["volume_trend"] = "DECREASING"
            
            return {
                "success": True,
                "analysis": volume_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting volume analysis: {e}")
            return {"success": False, "error": str(e)}

    async def get_market_intelligence_insights(self, user_id: int, db) -> Dict[str, Any]:
        """Get AI insights from market intelligence for portfolio"""
        try:
            from services.intelligent_stock_selector import IntelligentStockSelector
            
            intelligent_selector = IntelligentStockSelector()
            market_intelligence = await intelligent_selector.fetch_live_market_intelligence()
            
            if not market_intelligence.get("success"):
                return {
                    "success": False,
                    "error": "Could not fetch market intelligence",
                    "insights": {}
                }
            
            # Extract relevant insights
            insights = {
                "market_sentiment": market_intelligence.get("sentiment_score", 0.5),
                "market_outlook": market_intelligence.get("market_outlook", {}),
                "key_insights": market_intelligence.get("key_insights", []),
                "trading_recommendations": market_intelligence.get("trading_recommendations", []),
                "sector_performance": market_intelligence.get("sector_performance", {}),
                "volatility_analysis": market_intelligence.get("volatility_analysis", {}),
                "news_summary": market_intelligence.get("news_data", [])[:5]  # Top 5 news
            }
            
            return {
                "success": True,
                "insights": insights,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market intelligence insights: {e}")
            return {"success": False, "error": str(e)}

# Create service instance
portfolio_allocation_service = PortfolioAllocationService()
