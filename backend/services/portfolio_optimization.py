"""
Portfolio Optimization Service
Implements Modern Portfolio Theory (MPT) and advanced optimization algorithms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PortfolioOptimizationService:
    """Portfolio optimization using Modern Portfolio Theory"""
    
    def __init__(self):
        self.risk_free_rate = 0.06  # 6% risk-free rate (assumed)
    
    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate returns from price data"""
        return prices.pct_change().dropna()
    
    def calculate_covariance_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate covariance matrix from returns"""
        return returns.cov() * 252  # Annualized
    
    def calculate_expected_returns(self, returns: pd.DataFrame) -> pd.Series:
        """Calculate expected returns (mean)"""
        return returns.mean() * 252  # Annualized
    
    def calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        expected_returns: pd.Series,
        covariance_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate portfolio return, risk, and Sharpe ratio"""
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_variance = np.dot(weights.T, np.dot(covariance_matrix, weights))
        portfolio_std = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std if portfolio_std > 0 else 0
        
        return {
            "return": portfolio_return,
            "volatility": portfolio_std,
            "sharpe_ratio": sharpe_ratio,
            "variance": portfolio_variance
        }
    
    def optimize_portfolio(
        self,
        expected_returns: pd.Series,
        covariance_matrix: pd.DataFrame,
        optimization_type: str = "max_sharpe",
        target_return: Optional[float] = None,
        target_risk: Optional[float] = None,
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio weights
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix
            optimization_type: "max_sharpe", "min_volatility", "max_return", "efficient_frontier"
            target_return: Target return (for efficient frontier)
            target_risk: Target risk (for efficient frontier)
            constraints: Additional constraints
        """
        num_assets = len(expected_returns)
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / num_assets] * num_assets)
        
        # Constraints: weights sum to 1
        constraints_list = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        
        # Bounds: weights between 0 and 1 (long only)
        bounds = tuple((0, 1) for _ in range(num_assets))
        
        # Add custom constraints
        if constraints:
            if 'max_weight' in constraints:
                max_weight = constraints['max_weight']
                bounds = tuple((0, max_weight) for _ in range(num_assets))
            if 'min_weight' in constraints:
                min_weight = constraints['min_weight']
                bounds = tuple((min_weight, 1) for _ in range(num_assets))
        
        if optimization_type == "max_sharpe":
            # Maximize Sharpe ratio
            def objective(weights):
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_std = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
                sharpe = -(portfolio_return - self.risk_free_rate) / portfolio_std if portfolio_std > 0 else -999
                return sharpe
            
            result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
        elif optimization_type == "min_volatility":
            # Minimize volatility
            def objective(weights):
                return np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
            
            result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
        elif optimization_type == "max_return":
            # Maximize return
            def objective(weights):
                return -np.dot(weights, expected_returns)
            
            result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
        elif optimization_type == "efficient_frontier":
            # Optimize for target return or risk
            if target_return:
                def objective(weights):
                    return np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
                
                constraints_list.append({
                    'type': 'eq',
                    'fun': lambda w: np.dot(w, expected_returns) - target_return
                })
                result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints_list)
            elif target_risk:
                def objective(weights):
                    return -np.dot(weights, expected_returns)
                
                constraints_list.append({
                    'type': 'eq',
                    'fun': lambda w: np.sqrt(np.dot(w.T, np.dot(covariance_matrix, w))) - target_risk
                })
                result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints_list)
            else:
                # Default to max Sharpe
                return self.optimize_portfolio(expected_returns, covariance_matrix, "max_sharpe")
        else:
            raise ValueError(f"Unknown optimization type: {optimization_type}")
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
            # Fallback to equal weights
            optimal_weights = initial_weights
        else:
            optimal_weights = result.x
        
        # Calculate metrics
        metrics = self.calculate_portfolio_metrics(optimal_weights, expected_returns, covariance_matrix)
        
        return {
            "weights": optimal_weights.tolist(),
            "symbols": expected_returns.index.tolist(),
            "metrics": metrics,
            "optimization_type": optimization_type,
            "success": result.success
        }
    
    def generate_efficient_frontier(
        self,
        expected_returns: pd.Series,
        covariance_matrix: pd.DataFrame,
        num_points: int = 50
    ) -> List[Dict[str, Any]]:
        """Generate efficient frontier points"""
        min_return = expected_returns.min()
        max_return = expected_returns.max()
        target_returns = np.linspace(min_return, max_return, num_points)
        
        frontier_points = []
        for target_ret in target_returns:
            try:
                result = self.optimize_portfolio(
                    expected_returns,
                    covariance_matrix,
                    optimization_type="efficient_frontier",
                    target_return=target_ret
                )
                if result["success"]:
                    frontier_points.append({
                        "return": result["metrics"]["return"],
                        "volatility": result["metrics"]["volatility"],
                        "sharpe_ratio": result["metrics"]["sharpe_ratio"]
                    })
            except Exception as e:
                logger.debug(f"Could not optimize for return {target_ret}: {e}")
                continue
        
        return frontier_points
    
    def optimize_with_holdings(
        self,
        holdings: List[Dict[str, Any]],
        available_symbols: List[str],
        optimization_type: str = "max_sharpe",
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio considering current holdings
        
        Args:
            holdings: Current portfolio holdings
            available_symbols: Available symbols to invest in
            optimization_type: Optimization strategy
            constraints: Additional constraints
        """
        # This would require historical price data
        # For now, return a recommendation based on current allocation
        current_allocation = {}
        total_value = sum(h.get("total_value", 0) for h in holdings)
        
        for holding in holdings:
            symbol = holding.get("symbol")
            value = holding.get("total_value", 0)
            if total_value > 0:
                current_allocation[symbol] = value / total_value
        
        # Calculate current metrics
        current_metrics = {
            "return": 0.12,  # Placeholder
            "volatility": 0.18,  # Placeholder
            "sharpe_ratio": 0.33  # Placeholder
        }
        
        return {
            "current_allocation": current_allocation,
            "current_metrics": current_metrics,
            "recommendation": "Rebalance portfolio for optimal risk-return",
            "optimization_type": optimization_type
        }
    
    def calculate_rebalancing_actions(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        total_value: float
    ) -> List[Dict[str, Any]]:
        """Calculate rebalancing actions needed"""
        actions = []
        
        all_symbols = set(current_weights.keys()) | set(target_weights.keys())
        
        for symbol in all_symbols:
            current_weight = current_weights.get(symbol, 0.0)
            target_weight = target_weights.get(symbol, 0.0)
            difference = target_weight - current_weight
            
            if abs(difference) > 0.01:  # Only show if difference > 1%
                current_value = current_weight * total_value
                target_value = target_weight * total_value
                action_value = difference * total_value
                
                actions.append({
                    "symbol": symbol,
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "current_value": current_value,
                    "target_value": target_value,
                    "action": "BUY" if difference > 0 else "SELL",
                    "action_value": abs(action_value),
                    "action_percent": abs(difference) * 100
                })
        
        return sorted(actions, key=lambda x: abs(x["action_value"]), reverse=True)
    
    def risk_parity_optimization(
        self,
        covariance_matrix: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Risk Parity Portfolio Optimization
        Equal risk contribution from each asset
        """
        num_assets = len(covariance_matrix)
        initial_weights = np.array([1.0 / num_assets] * num_assets)
        
        def risk_contribution(weights):
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
            marginal_contrib = np.dot(covariance_matrix, weights) / portfolio_std
            contrib = weights * marginal_contrib
            return contrib
        
        def objective(weights):
            contrib = risk_contribution(weights)
            # Minimize variance of risk contributions
            return np.sum((contrib - contrib.mean()) ** 2)
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = tuple((0, 1) for _ in range(num_assets))
        
        result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            optimal_weights = result.x
            metrics = {
                "return": 0.0,  # Would need expected returns
                "volatility": np.sqrt(np.dot(optimal_weights.T, np.dot(covariance_matrix, optimal_weights))),
                "sharpe_ratio": 0.0
            }
            
            return {
                "weights": optimal_weights.tolist(),
                "symbols": covariance_matrix.index.tolist(),
                "metrics": metrics,
                "optimization_type": "risk_parity",
                "success": True
            }
        else:
            return {
                "weights": initial_weights.tolist(),
                "symbols": covariance_matrix.index.tolist(),
                "metrics": {},
                "optimization_type": "risk_parity",
                "success": False
            }

# Singleton instance
portfolio_optimization_service = PortfolioOptimizationService()

