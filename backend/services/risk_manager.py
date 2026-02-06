"""
Risk Management Service
Advanced risk management and position sizing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.max_position_size = 100000  # Maximum position size
        self.max_portfolio_risk = 0.02   # Maximum 2% portfolio risk per trade
        self.default_stop_loss = 0.05    # Default 5% stop loss
        self.default_take_profit = 0.10  # Default 10% take profit
        self.max_correlation = 0.7       # Maximum correlation between positions
        self.max_concentration = 0.20    # Maximum 20% concentration in single stock
        
    def calculate_position_size(self, current_price: float, risk_percentage: float, 
                              stop_loss_percentage: float, portfolio_value: float) -> Dict:
        """Calculate optimal position size based on risk parameters"""
        try:
            # Calculate risk amount
            risk_amount = portfolio_value * (risk_percentage / 100)
            
            # Calculate stop loss price
            stop_loss_price = current_price * (1 - stop_loss_percentage / 100)
            
            # Calculate position size
            price_risk = current_price - stop_loss_price
            position_size = risk_amount / price_risk if price_risk > 0 else 0
            
            # Apply maximum position size limit
            max_shares = self.max_position_size / current_price
            position_size = min(position_size, max_shares)
            
            # Calculate position value
            position_value = position_size * current_price
            
            return {
                "quantity": int(position_size),
                "position_value": round(position_value, 2),
                "risk_amount": round(risk_amount, 2),
                "stop_loss_price": round(stop_loss_price, 2),
                "risk_percentage": risk_percentage,
                "stop_loss_percentage": stop_loss_percentage
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                "quantity": 0,
                "position_value": 0,
                "risk_amount": 0,
                "stop_loss_price": current_price * 0.95,
                "risk_percentage": risk_percentage,
                "stop_loss_percentage": stop_loss_percentage
            }
    
    def calculate_portfolio_risk(self, positions: List[Dict], total_value: float) -> Dict:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            if not positions or total_value <= 0:
                return self._get_empty_risk_metrics()
            
            # Calculate individual position metrics
            position_values = []
            weights = []
            
            for pos in positions:
                # Handle both 'position_value' and 'value' keys
                position_value = pos.get("position_value", pos.get("value", 0))
                position_values.append(position_value)
                
                # Calculate weight as percentage of total portfolio
                weight = position_value / total_value if total_value > 0 else 0
                weights.append(weight)
            
            # Value at Risk (VaR) calculation
            var_1d = self._calculate_var(position_values, 0.01)  # 1% VaR
            var_5d = self._calculate_var(position_values, 0.05)  # 5% VaR
            
            # Sharpe ratio (simplified)
            sharpe_ratio = self._calculate_sharpe_ratio(positions)
            
            # Maximum drawdown
            max_drawdown = self._calculate_max_drawdown(positions)
            
            # Beta calculation (simplified)
            beta = self._calculate_beta(positions)
            
            # Concentration risk
            concentration_risk = max(weights) if weights else 0
            
            # Correlation risk
            correlation_risk = self._calculate_correlation_risk(positions)
            
            return {
                "var_1d": round(var_1d, 2),
                "var_5d": round(var_5d, 2),
                "sharpe_ratio": round(sharpe_ratio, 4),
                "max_drawdown": round(max_drawdown, 4),
                "beta": round(beta, 4),
                "concentration_risk": round(concentration_risk, 4),
                "correlation_risk": round(correlation_risk, 4),
                "total_positions": len(positions),
                "portfolio_value": round(total_value, 2),
                # UI compatibility: some components expect `total_value`
                "total_value": round(total_value, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return self._get_empty_risk_metrics()
    
    def validate_trade(self, symbol: str, order_type: str, quantity: int, 
                      price: float, current_portfolio_value: float, 
                      existing_positions: List) -> Dict:
        """Validate a trade against risk criteria"""
        try:
            validation_result = {
                "is_valid": True,
                "reasons": [],
                "warnings": [],
                "portfolio_impact": 0
            }
            
            # Calculate trade value
            trade_value = quantity * price
            portfolio_impact = trade_value / current_portfolio_value if current_portfolio_value > 0 else 0
            validation_result["portfolio_impact"] = portfolio_impact
            
            # Check position size limit
            if trade_value > self.max_position_size:
                validation_result["is_valid"] = False
                validation_result["reasons"].append(f"Position size {trade_value} exceeds maximum limit {self.max_position_size}")
            
            # Check portfolio impact
            if portfolio_impact > self.max_concentration:
                validation_result["is_valid"] = False
                validation_result["reasons"].append(f"Position would represent {portfolio_impact:.1%} of portfolio, exceeding {self.max_concentration:.1%} limit")
            
            # Check for existing position
            existing_position = next((pos for pos in existing_positions if pos.symbol == symbol), None)
            if existing_position and order_type == "BUY":
                new_total_value = (existing_position.quantity * existing_position.average_price) + trade_value
                new_concentration = new_total_value / current_portfolio_value if current_portfolio_value > 0 else 0
                
                if new_concentration > self.max_concentration:
                    validation_result["is_valid"] = False
                    validation_result["reasons"].append(f"Adding to existing position would exceed concentration limit")
            
            # Check portfolio diversification
            if len(existing_positions) >= 10 and not existing_position:
                validation_result["warnings"].append("Portfolio already has 10+ positions, consider consolidation")
            
            # Check correlation risk
            if existing_position:
                correlation_risk = self._check_correlation_risk(symbol, existing_positions)
                if correlation_risk > self.max_correlation:
                    validation_result["warnings"].append(f"High correlation risk with existing positions: {correlation_risk:.2f}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating trade: {e}")
            return {
                "is_valid": False,
                "reasons": [f"Validation error: {str(e)}"],
                "warnings": [],
                "portfolio_impact": 0
            }
    
    def generate_recommendations(self, portfolio_risk: Dict) -> List[Dict]:
        """Generate risk management recommendations"""
        try:
            recommendations = []
            
            # Concentration risk recommendations
            if portfolio_risk.get("concentration_risk", 0) > self.max_concentration:
                recommendations.append({
                    "type": "CONCENTRATION",
                    "priority": "HIGH",
                    "message": f"Portfolio concentration risk is {portfolio_risk['concentration_risk']:.1%}, consider diversifying",
                    "action": "Reduce position sizes or add more positions"
                })
            
            # Correlation risk recommendations
            if portfolio_risk.get("correlation_risk", 0) > self.max_correlation:
                recommendations.append({
                    "type": "CORRELATION",
                    "priority": "MEDIUM",
                    "message": f"High correlation between positions: {portfolio_risk['correlation_risk']:.2f}",
                    "action": "Add uncorrelated assets to portfolio"
                })
            
            # VaR recommendations
            if portfolio_risk.get("var_1d", 0) > portfolio_risk.get("portfolio_value", 0) * 0.02:
                recommendations.append({
                    "type": "VAR",
                    "priority": "HIGH",
                    "message": f"1-day VaR is {portfolio_risk['var_1d']:.2f}, consider reducing risk",
                    "action": "Reduce position sizes or add hedging"
                })
            
            # Sharpe ratio recommendations
            if portfolio_risk.get("sharpe_ratio", 0) < 1.0:
                recommendations.append({
                    "type": "PERFORMANCE",
                    "priority": "MEDIUM",
                    "message": f"Sharpe ratio is {portfolio_risk['sharpe_ratio']:.2f}, consider improving risk-adjusted returns",
                    "action": "Review position selection and risk management"
                })
            
            # Max drawdown recommendations
            if portfolio_risk.get("max_drawdown", 0) > 0.15:
                recommendations.append({
                    "type": "DRAWDOWN",
                    "priority": "HIGH",
                    "message": f"Maximum drawdown is {portfolio_risk['max_drawdown']:.1%}, consider risk reduction",
                    "action": "Implement stop-losses and position sizing"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    # New: expose simple metrics aggregation for the API route
    async def get_risk_metrics(self, user_id: int = None) -> Dict:
        """Return overall risk metrics with live portfolio data.
        If user_id provided, fetches real portfolio data; otherwise uses mock data.
        """
        try:
            if user_id:
                # Fetch real portfolio data from database
                from core.database_unified import SessionLocal, Portfolio
                db = SessionLocal()
                try:
                    portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
                    
                    if portfolio_items:
                        # Import data service for live prices
                        from services.data_service import data_service
                        
                        positions = []
                        total_value = 0.0
                        
                        for item in portfolio_items:
                            try:
                                # Fetch live price
                                live_quote = await data_service.get_quote(item.symbol, exchange="NSE")
                                live_price = live_quote.get("last_price", item.current_price)
                                current_value = item.quantity * live_price
                                
                                # Calculate P&L percentage
                                invested_value = item.quantity * item.average_price
                                pnl_percentage = ((current_value - invested_value) / invested_value) if invested_value > 0 else 0
                                
                                positions.append({
                                    "symbol": item.symbol,
                                    "value": current_value,
                                    "pnl_percentage": pnl_percentage,
                                    "weight": 0.0  # Will be calculated below
                                })
                                
                                total_value += current_value
                                
                            except Exception as e:
                                logger.warning(f"Could not fetch live price for {item.symbol}: {e}")
                                # Use stored values
                                current_value = item.quantity * item.current_price
                                invested_value = item.quantity * item.average_price
                                pnl_percentage = ((current_value - invested_value) / invested_value) if invested_value > 0 else 0
                                
                                positions.append({
                                    "symbol": item.symbol,
                                    "value": current_value,
                                    "pnl_percentage": pnl_percentage,
                                    "weight": 0.0
                                })
                                
                                total_value += current_value
                        
                        # Calculate weights
                        for position in positions:
                            position["weight"] = position["value"] / total_value if total_value > 0 else 0
                        
                    else:
                        # No portfolio items, return empty metrics
                        positions = []
                        total_value = 0.0
                        
                finally:
                    db.close()
            else:
                # Use mock data for backward compatibility
                positions = [
                    {"symbol": "RELIANCE", "value": 50000, "pnl_percentage": 0.02, "weight": 0.5},
                    {"symbol": "TCS", "value": 50000, "pnl_percentage": -0.01, "weight": 0.5},
                ]
                total_value = sum(p.get("value", 0) for p in positions)
            
            # Calculate risk metrics
            metrics = self.calculate_portfolio_risk(positions, total_value)
            recommendations = self.generate_recommendations(metrics)
            
            return {
                "portfolio_value": total_value,
                "total_value": total_value,  # Added for frontend compatibility
                "metrics": metrics,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {
                "portfolio_value": 0,
                "total_value": 0,  # Added for frontend compatibility
                "metrics": self._get_empty_risk_metrics(), 
                "recommendations": [], 
                "error": str(e)
            }
    
    def get_risk_limits(self) -> Dict:
        """Get current risk limits and thresholds"""
        return {
            "max_position_size": self.max_position_size,
            "max_portfolio_risk": self.max_portfolio_risk,
            "default_stop_loss": self.default_stop_loss,
            "default_take_profit": self.default_take_profit,
            "max_correlation": self.max_correlation,
            "max_concentration": self.max_concentration,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_var(self, position_values: List[float], confidence_level: float) -> float:
        """Calculate Value at Risk"""
        try:
            if not position_values:
                return 0
            
            # Simple VaR calculation using historical simulation
            # In practice, this would use more sophisticated methods
            total_value = sum(position_values)
            var_multiplier = 2.33 if confidence_level == 0.01 else 1.65  # 99% and 95% confidence
            volatility = 0.02  # Assume 2% daily volatility
            
            return total_value * var_multiplier * volatility
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return 0
    
    def _calculate_sharpe_ratio(self, positions: List[Dict]) -> float:
        """Calculate Sharpe ratio"""
        try:
            if not positions:
                return 0
            
            # Simplified Sharpe ratio calculation
            # In practice, this would use actual returns and risk-free rate
            returns = [pos.get("pnl_percentage", 0) for pos in positions]
            if not returns:
                return 0
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0
            
            risk_free_rate = 0.05  # Assume 5% risk-free rate
            return (mean_return - risk_free_rate) / std_return
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0
    
    def _calculate_max_drawdown(self, positions: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        try:
            if not positions:
                return 0
            
            # Simplified max drawdown calculation
            # In practice, this would use actual price history
            pnl_percentages = [pos.get("pnl_percentage", 0) for pos in positions]
            if not pnl_percentages:
                return 0
            
            # Calculate cumulative returns
            cumulative_returns = np.cumsum(pnl_percentages)
            
            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative_returns)
            
            # Calculate drawdown
            drawdown = cumulative_returns - running_max
            
            return abs(np.min(drawdown)) if len(drawdown) > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0
    
    def _calculate_beta(self, positions: List[Dict]) -> float:
        """Calculate portfolio beta"""
        try:
            if not positions:
                return 1.0
            
            # Simplified beta calculation
            # In practice, this would use actual market data
            weights = [pos.get("weight", 0) for pos in positions]
            
            # Assume average beta of 1.0 for simplicity
            # In practice, this would be calculated using actual stock betas
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return 1.0
    
    def _calculate_correlation_risk(self, positions: List[Dict]) -> float:
        """Calculate correlation risk between positions"""
        try:
            if len(positions) < 2:
                return 0
            
            # Simplified correlation risk calculation
            # In practice, this would use actual correlation data
            symbols = [pos.get("symbol", "") for pos in positions]
            
            # Assume some correlation based on sector/industry
            # This is a simplified approach
            return 0.3  # Assume 30% average correlation
            
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {e}")
            return 0
    
    def _check_correlation_risk(self, symbol: str, existing_positions: List) -> float:
        """Check correlation risk for a specific symbol"""
        try:
            # Simplified correlation check
            # In practice, this would use actual correlation data
            return 0.3  # Assume 30% correlation
            
        except Exception as e:
            logger.error(f"Error checking correlation risk: {e}")
            return 0
    
    def _get_empty_risk_metrics(self) -> Dict:
        """Return empty risk metrics"""
        return {
            "var_1d": 0,
            "var_5d": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "beta": 1.0,
            "concentration_risk": 0,
            "correlation_risk": 0,
            "total_positions": 0,
            "portfolio_value": 0,
            "total_value": 0
        }

    async def stress_test(self, portfolio: Dict, scenarios: List[str]) -> Dict:
        """Run simple mock stress tests for given scenarios and return UI-compatible structure.
        Expects portfolio to optionally contain positions as a list under keys: 'positions' or 'portfolio_data'.
        Each position should have at least { symbol, quantity?, current_price? or value }.
        """
        try:
            # Extract positions and compute total value in a tolerant way
            positions = portfolio.get("positions") or portfolio.get("portfolio_data") or []
            if not isinstance(positions, list):
                positions = []

            total_value = 0.0
            for pos in positions:
                if isinstance(pos, dict):
                    if "value" in pos:
                        total_value += float(pos.get("value", 0) or 0)
                    else:
                        qty = float(pos.get("quantity", 0) or 0)
                        price = float(pos.get("current_price", 0) or 0)
                        total_value += qty * price

            # Fallback if no portfolio provided
            if total_value <= 0:
                total_value = 100000.0  # assume 1L mock portfolio

            # Define simple scenario impact assumptions
            scenario_impact_map = {
                "market_crash": {"loss_pct": 0.18, "worst_day": 8.0, "recovery": "6-12 months"},
                "recession": {"loss_pct": 0.12, "worst_day": 5.5, "recovery": "9-18 months"},
                "sector_rotation": {"loss_pct": 0.06, "worst_day": 3.5, "recovery": "4-8 weeks"},
                "volatility_spike": {"loss_pct": 0.04, "worst_day": 3.0, "recovery": "2-6 weeks"},
                "rate_hike": {"loss_pct": 0.07, "worst_day": 3.8, "recovery": "2-4 months"},
            }

            # Normalize scenario names
            normalized = []
            for name in scenarios or []:
                key = str(name).strip().lower()
                normalized.append(key)
            if not normalized:
                normalized = ["market_crash", "volatility_spike"]

            test_results: List[Dict] = []
            worst_case = (None, -1.0)  # (name, loss_amount)

            for sc in normalized:
                impact = scenario_impact_map.get(sc, {"loss_pct": 0.05, "worst_day": 3.0, "recovery": "4-12 weeks"})
                loss_pct = float(impact.get("loss_pct", 0.05))
                total_loss = round(total_value * loss_pct)
                loss_percentage = round(loss_pct * 100, 2)
                worst_day_loss = float(impact.get("worst_day", 3.0))
                recovery_time = str(impact.get("recovery", "4-12 weeks"))

                if total_loss > worst_case[1]:
                    worst_case = (sc, total_loss)

                # Simple recommendation set
                recs = [
                    {"description": "Reduce exposure to high-beta positions", "priority": "high" if loss_pct >= 0.1 else "medium"},
                    {"description": "Increase cash buffer to manage drawdowns", "priority": "medium"},
                    {"description": "Consider hedging with index options", "priority": "medium"},
                ]

                test_results.append({
                    "scenario_name": sc.replace("_", " ").title(),
                    "portfolio_impact": {
                        "total_loss": total_loss,
                        "loss_percentage": loss_percentage,
                        "worst_day_loss": worst_day_loss,
                        "recovery_time": recovery_time,
                    },
                    "recommendations": recs,
                })

            summary = {
                "worst_case_scenario": (worst_case[0] or "market_crash").replace("_", " ").title(),
                "maximum_loss": worst_case[1] if worst_case[1] >= 0 else round(total_value * 0.18),
                "overall_portfolio_resilience": "moderate" if (worst_case[1] / total_value) < 0.15 else "low",
            }

            return {"summary": summary, "test_results": test_results}

        except Exception as e:
            logger.error(f"Error running stress test: {e}")
            # Safe fallback structure
            return {
                "summary": {
                    "worst_case_scenario": "Unknown",
                    "maximum_loss": 0,
                    "overall_portfolio_resilience": "unknown",
                },
                "test_results": []
            }

# Create a global instance
risk_manager = RiskManager()