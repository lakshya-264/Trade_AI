"""
Advanced Risk Management Service
Enhanced VaR, position sizing, and risk controls
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AdvancedRiskManagement:
    """Advanced risk management with sophisticated VaR and position sizing"""
    
    def __init__(self):
        self.portfolio_data = {}
        self.risk_metrics = {}
        self.position_limits = {}
        self.correlation_matrix = None
        
        # Risk parameters
        self.confidence_levels = [0.95, 0.99, 0.999]
        self.time_horizons = [1, 5, 10, 20]  # Days
        self.max_portfolio_var = 0.05  # 5% max portfolio VaR
        self.max_position_size = 0.1  # 10% max position size
        self.max_correlation = 0.7  # Max correlation between positions
        
        # Models directory
        self.models_dir = "models/risk_management"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Risk models
        self.var_models = {}
        self.copula_models = {}
        self.stress_test_scenarios = {}
        
    def calculate_parametric_var(self, returns: pd.Series, confidence_level: float = 0.95, 
                                time_horizon: int = 1) -> Dict:
        """Calculate parametric VaR assuming normal distribution"""
        try:
            if len(returns) < 30:
                return {"error": "Insufficient data for VaR calculation"}
            
            # Calculate parameters
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Parametric VaR
            z_score = stats.norm.ppf(1 - confidence_level)
            var = -(mean_return - z_score * std_return) * np.sqrt(time_horizon)
            
            # Expected Shortfall (Conditional VaR)
            es = -(mean_return - std_return * stats.norm.pdf(z_score) / (1 - confidence_level)) * np.sqrt(time_horizon)
            
            return {
                "var": float(var),
                "expected_shortfall": float(es),
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "mean_return": float(mean_return),
                "volatility": float(std_return),
                "method": "parametric"
            }
            
        except Exception as e:
            logger.error(f"Error calculating parametric VaR: {e}")
            return {"error": str(e)}
    
    def calculate_historical_var(self, returns: pd.Series, confidence_level: float = 0.95, 
                               time_horizon: int = 1) -> Dict:
        """Calculate historical VaR using empirical distribution"""
        try:
            if len(returns) < 100:
                return {"error": "Insufficient data for historical VaR calculation"}
            
            # Scale returns for time horizon
            scaled_returns = returns * np.sqrt(time_horizon)
            
            # Historical VaR
            var_percentile = (1 - confidence_level) * 100
            var = -np.percentile(scaled_returns, var_percentile)
            
            # Expected Shortfall
            var_threshold = -var
            tail_returns = scaled_returns[scaled_returns <= var_threshold]
            es = -tail_returns.mean() if len(tail_returns) > 0 else var
            
            return {
                "var": float(var),
                "expected_shortfall": float(es),
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "tail_observations": len(tail_returns),
                "method": "historical"
            }
            
        except Exception as e:
            logger.error(f"Error calculating historical VaR: {e}")
            return {"error": str(e)}
    
    def calculate_monte_carlo_var(self, returns: pd.Series, confidence_level: float = 0.95, 
                                time_horizon: int = 1, n_simulations: int = 10000) -> Dict:
        """Calculate VaR using Monte Carlo simulation"""
        try:
            if len(returns) < 30:
                return {"error": "Insufficient data for Monte Carlo VaR calculation"}
            
            # Fit distribution to returns
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Generate Monte Carlo scenarios
            np.random.seed(42)  # For reproducibility
            simulated_returns = np.random.normal(mean_return, std_return, n_simulations)
            
            # Scale for time horizon
            scaled_returns = simulated_returns * np.sqrt(time_horizon)
            
            # Calculate VaR
            var_percentile = (1 - confidence_level) * 100
            var = -np.percentile(scaled_returns, var_percentile)
            
            # Expected Shortfall
            var_threshold = -var
            tail_returns = scaled_returns[scaled_returns <= var_threshold]
            es = -tail_returns.mean() if len(tail_returns) > 0 else var
            
            return {
                "var": float(var),
                "expected_shortfall": float(es),
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "n_simulations": n_simulations,
                "method": "monte_carlo"
            }
            
        except Exception as e:
            logger.error(f"Error calculating Monte Carlo VaR: {e}")
            return {"error": str(e)}
    
    def calculate_portfolio_var(self, portfolio_returns: pd.DataFrame, weights: Dict[str, float], 
                              confidence_level: float = 0.95, time_horizon: int = 1) -> Dict:
        """Calculate portfolio VaR using covariance matrix approach"""
        try:
            if len(portfolio_returns) < 30:
                return {"error": "Insufficient data for portfolio VaR calculation"}
            
            # Prepare data
            symbols = list(weights.keys())
            returns_matrix = portfolio_returns[symbols].dropna()
            
            if len(returns_matrix) == 0:
                return {"error": "No valid return data for portfolio VaR"}
            
            # Calculate portfolio statistics
            portfolio_weights = np.array([weights[symbol] for symbol in symbols])
            portfolio_mean = np.dot(portfolio_weights, returns_matrix.mean())
            portfolio_variance = np.dot(portfolio_weights, np.dot(returns_matrix.cov(), portfolio_weights))
            portfolio_std = np.sqrt(portfolio_variance)
            
            # Scale for time horizon
            portfolio_std_scaled = portfolio_std * np.sqrt(time_horizon)
            
            # Portfolio VaR
            z_score = stats.norm.ppf(1 - confidence_level)
            portfolio_var = -(portfolio_mean - z_score * portfolio_std_scaled)
            
            # Expected Shortfall
            portfolio_es = -(portfolio_mean - portfolio_std_scaled * stats.norm.pdf(z_score) / (1 - confidence_level))
            
            # Individual position contributions
            position_vars = {}
            for i, symbol in enumerate(symbols):
                position_weight = portfolio_weights[i]
                position_std = returns_matrix[symbol].std() * np.sqrt(time_horizon)
                position_var = position_weight * position_std * z_score
                position_vars[symbol] = float(position_var)
            
            return {
                "portfolio_var": float(portfolio_var),
                "portfolio_expected_shortfall": float(portfolio_es),
                "portfolio_volatility": float(portfolio_std_scaled),
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "position_vars": position_vars,
                "portfolio_weights": weights,
                "method": "covariance_matrix"
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {e}")
            return {"error": str(e)}
    
    def calculate_conditional_var(self, returns: pd.Series, confidence_level: float = 0.95) -> Dict:
        """Calculate Conditional VaR (Expected Shortfall)"""
        try:
            if len(returns) < 100:
                return {"error": "Insufficient data for Conditional VaR calculation"}
            
            # Calculate VaR threshold
            var_percentile = (1 - confidence_level) * 100
            var_threshold = -np.percentile(returns, var_percentile)
            
            # Calculate Expected Shortfall
            tail_returns = returns[returns <= var_threshold]
            conditional_var = -tail_returns.mean() if len(tail_returns) > 0 else 0
            
            # Additional tail risk metrics
            tail_probability = len(tail_returns) / len(returns)
            tail_volatility = tail_returns.std() if len(tail_returns) > 1 else 0
            
            return {
                "conditional_var": float(conditional_var),
                "var_threshold": float(var_threshold),
                "tail_probability": float(tail_probability),
                "tail_volatility": float(tail_volatility),
                "tail_observations": len(tail_returns),
                "confidence_level": confidence_level
            }
            
        except Exception as e:
            logger.error(f"Error calculating Conditional VaR: {e}")
            return {"error": str(e)}
    
    def calculate_maximum_drawdown(self, prices: pd.Series) -> Dict:
        """Calculate maximum drawdown and related metrics"""
        try:
            if len(prices) < 2:
                return {"error": "Insufficient data for drawdown calculation"}
            
            # Calculate cumulative returns
            cumulative_returns = (1 + prices.pct_change()).cumprod()
            
            # Calculate running maximum
            running_max = cumulative_returns.expanding().max()
            
            # Calculate drawdown
            drawdown = (cumulative_returns - running_max) / running_max
            
            # Maximum drawdown
            max_drawdown = drawdown.min()
            
            # Find drawdown period
            max_dd_idx = drawdown.idxmin()
            peak_idx = running_max.loc[:max_dd_idx].idxmax()
            
            # Drawdown duration
            drawdown_duration = (max_dd_idx - peak_idx).days if hasattr(max_dd_idx - peak_idx, 'days') else 0
            
            # Recovery time
            recovery_idx = drawdown.loc[max_dd_idx:].where(drawdown.loc[max_dd_idx:] >= 0).first_valid_index()
            recovery_time = (recovery_idx - max_dd_idx).days if recovery_idx and hasattr(recovery_idx - max_dd_idx, 'days') else None
            
            return {
                "max_drawdown": float(max_drawdown),
                "max_drawdown_percent": float(max_drawdown * 100),
                "peak_date": peak_idx.isoformat() if hasattr(peak_idx, 'isoformat') else str(peak_idx),
                "trough_date": max_dd_idx.isoformat() if hasattr(max_dd_idx, 'isoformat') else str(max_dd_idx),
                "drawdown_duration_days": drawdown_duration,
                "recovery_time_days": recovery_time,
                "current_drawdown": float(drawdown.iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating maximum drawdown: {e}")
            return {"error": str(e)}
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> Dict:
        """Calculate Sharpe ratio and related risk-adjusted metrics"""
        try:
            if len(returns) < 30:
                return {"error": "Insufficient data for Sharpe ratio calculation"}
            
            # Annualize returns and risk-free rate
            annualized_returns = returns.mean() * 252
            annualized_volatility = returns.std() * np.sqrt(252)
            annualized_rf_rate = risk_free_rate
            
            # Sharpe ratio
            excess_returns = annualized_returns - annualized_rf_rate
            sharpe_ratio = excess_returns / annualized_volatility if annualized_volatility > 0 else 0
            
            # Sortino ratio (downside deviation)
            downside_returns = returns[returns < 0]
            downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = excess_returns / downside_volatility if downside_volatility > 0 else 0
            
            # Calmar ratio (return / max drawdown)
            drawdown_info = self.calculate_maximum_drawdown(returns.cumsum())
            max_dd = abs(drawdown_info.get('max_drawdown', 0))
            calmar_ratio = annualized_returns / max_dd if max_dd > 0 else 0
            
            return {
                "sharpe_ratio": float(sharpe_ratio),
                "sortino_ratio": float(sortino_ratio),
                "calmar_ratio": float(calmar_ratio),
                "annualized_return": float(annualized_returns),
                "annualized_volatility": float(annualized_volatility),
                "excess_return": float(excess_returns),
                "risk_free_rate": risk_free_rate
            }
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return {"error": str(e)}
    
    def calculate_optimal_position_size(self, expected_return: float, volatility: float, 
                                      risk_tolerance: float = 0.02, max_position: float = 0.1) -> Dict:
        """Calculate optimal position size using Kelly Criterion and risk budgeting"""
        try:
            # Kelly Criterion
            kelly_fraction = expected_return / (volatility ** 2) if volatility > 0 else 0
            kelly_fraction = max(0, min(kelly_fraction, max_position))  # Constrain to max position
            
            # Risk budgeting approach
            risk_budget = risk_tolerance / volatility if volatility > 0 else 0
            risk_budget = max(0, min(risk_budget, max_position))
            
            # Volatility targeting
            target_volatility = 0.15  # 15% target volatility
            vol_target_fraction = target_volatility / volatility if volatility > 0 else 0
            vol_target_fraction = max(0, min(vol_target_fraction, max_position))
            
            # Conservative approach (half Kelly)
            conservative_fraction = kelly_fraction * 0.5
            
            # Equal weight approach
            equal_weight = 1.0 / 10  # Assume 10 positions max
            
            return {
                "kelly_fraction": float(kelly_fraction),
                "risk_budget_fraction": float(risk_budget),
                "volatility_target_fraction": float(vol_target_fraction),
                "conservative_fraction": float(conservative_fraction),
                "equal_weight_fraction": float(equal_weight),
                "recommended_fraction": float(conservative_fraction),  # Default to conservative
                "expected_return": expected_return,
                "volatility": volatility,
                "risk_tolerance": risk_tolerance
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimal position size: {e}")
            return {"error": str(e)}
    
    def calculate_portfolio_optimization(self, returns: pd.DataFrame, target_return: float = None) -> Dict:
        """Calculate optimal portfolio weights using mean-variance optimization"""
        try:
            if len(returns) < 30:
                return {"error": "Insufficient data for portfolio optimization"}
            
            # Calculate expected returns and covariance matrix
            expected_returns = returns.mean() * 252  # Annualized
            cov_matrix = returns.cov() * 252  # Annualized
            
            n_assets = len(expected_returns)
            
            # Objective function (minimize portfolio variance)
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Constraints
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]  # Weights sum to 1
            
            # Bounds (0 <= weight <= 1 for each asset)
            bounds = tuple((0, 1) for _ in range(n_assets))
            
            # Initial guess (equal weights)
            x0 = np.array([1/n_assets] * n_assets)
            
            # Optimize
            result = minimize(portfolio_variance, x0, method='SLSQP', bounds=bounds, constraints=constraints)
            
            if not result.success:
                return {"error": "Portfolio optimization failed"}
            
            optimal_weights = result.x
            optimal_weights_dict = {asset: float(weight) for asset, weight in zip(expected_returns.index, optimal_weights)}
            
            # Calculate portfolio metrics
            portfolio_return = np.dot(optimal_weights, expected_returns)
            portfolio_variance = portfolio_variance(optimal_weights)
            portfolio_volatility = np.sqrt(portfolio_variance)
            portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            return {
                "optimal_weights": optimal_weights_dict,
                "portfolio_return": float(portfolio_return),
                "portfolio_volatility": float(portfolio_volatility),
                "portfolio_sharpe": float(portfolio_sharpe),
                "optimization_success": result.success,
                "n_assets": n_assets
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio optimization: {e}")
            return {"error": str(e)}
    
    def calculate_stress_test(self, portfolio_returns: pd.DataFrame, weights: Dict[str, float], 
                            stress_scenarios: Dict[str, float]) -> Dict:
        """Calculate portfolio performance under stress scenarios"""
        try:
            if len(portfolio_returns) < 30:
                return {"error": "Insufficient data for stress testing"}
            
            stress_results = {}
            
            for scenario_name, stress_factor in stress_scenarios.items():
                # Apply stress to returns
                stressed_returns = portfolio_returns * stress_factor
                
                # Calculate portfolio return under stress
                portfolio_weights = np.array([weights.get(symbol, 0) for symbol in portfolio_returns.columns])
                stressed_portfolio_return = np.dot(portfolio_weights, stressed_returns.mean()) * 252
                
                # Calculate portfolio volatility under stress
                stressed_cov = stressed_returns.cov() * 252
                stressed_portfolio_variance = np.dot(portfolio_weights, np.dot(stressed_cov, portfolio_weights))
                stressed_portfolio_volatility = np.sqrt(stressed_portfolio_variance)
                
                # Calculate VaR under stress
                stressed_var = self.calculate_parametric_var(
                    stressed_returns.sum(axis=1), confidence_level=0.95
                )
                
                stress_results[scenario_name] = {
                    "portfolio_return": float(stressed_portfolio_return),
                    "portfolio_volatility": float(stressed_portfolio_volatility),
                    "var_95": stressed_var.get("var", 0),
                    "stress_factor": stress_factor
                }
            
            return {
                "stress_scenarios": stress_results,
                "base_portfolio_return": float(np.dot(portfolio_weights, portfolio_returns.mean()) * 252),
                "base_portfolio_volatility": float(np.sqrt(np.dot(portfolio_weights, np.dot(portfolio_returns.cov() * 252, portfolio_weights))))
            }
            
        except Exception as e:
            logger.error(f"Error calculating stress test: {e}")
            return {"error": str(e)}
    
    def calculate_correlation_risk(self, returns: pd.DataFrame) -> Dict:
        """Calculate correlation risk metrics"""
        try:
            if len(returns) < 30:
                return {"error": "Insufficient data for correlation analysis"}
            
            # Calculate correlation matrix
            corr_matrix = returns.corr()
            
            # Average correlation
            upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            avg_correlation = upper_triangle.stack().mean()
            
            # Maximum correlation
            max_correlation = upper_triangle.stack().max()
            
            # Correlation concentration (Gini coefficient)
            correlations = upper_triangle.stack().dropna()
            correlations_sorted = np.sort(correlations)
            n = len(correlations_sorted)
            cumsum = np.cumsum(correlations_sorted)
            gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
            
            # Correlation stability (rolling correlation)
            rolling_corr = returns.rolling(60).corr()
            corr_volatility = rolling_corr.groupby(level=0).apply(lambda x: x.stack().std()).mean()
            
            return {
                "correlation_matrix": corr_matrix.to_dict(),
                "average_correlation": float(avg_correlation),
                "max_correlation": float(max_correlation),
                "correlation_gini": float(gini),
                "correlation_volatility": float(corr_volatility),
                "n_assets": len(returns.columns)
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {e}")
            return {"error": str(e)}
    
    def get_comprehensive_risk_report(self, portfolio_data: Dict) -> Dict:
        """Generate comprehensive risk report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "risk_metrics": {},
                "recommendations": []
            }
            
            # Extract data
            returns = portfolio_data.get('returns', pd.Series())
            prices = portfolio_data.get('prices', pd.Series())
            weights = portfolio_data.get('weights', {})
            
            if len(returns) == 0:
                return {"error": "No return data available for risk analysis"}
            
            # VaR calculations
            for confidence in self.confidence_levels:
                var_result = self.calculate_parametric_var(returns, confidence)
                if "error" not in var_result:
                    report["risk_metrics"][f"var_{int(confidence*100)}"] = var_result
            
            # Maximum drawdown
            if len(prices) > 0:
                drawdown_result = self.calculate_maximum_drawdown(prices)
                if "error" not in drawdown_result:
                    report["risk_metrics"]["max_drawdown"] = drawdown_result
            
            # Sharpe ratio
            sharpe_result = self.calculate_sharpe_ratio(returns)
            if "error" not in sharpe_result:
                report["risk_metrics"]["sharpe_ratio"] = sharpe_result
            
            # Generate recommendations
            if "var_95" in report["risk_metrics"]:
                var_95 = report["risk_metrics"]["var_95"]["var"]
                if var_95 > self.max_portfolio_var:
                    report["recommendations"].append(f"Portfolio VaR ({var_95:.2%}) exceeds limit ({self.max_portfolio_var:.2%})")
            
            if "max_drawdown" in report["risk_metrics"]:
                max_dd = abs(report["risk_metrics"]["max_drawdown"]["max_drawdown"])
                if max_dd > 0.2:  # 20% max drawdown
                    report["recommendations"].append(f"Maximum drawdown ({max_dd:.2%}) is high")
            
            if "sharpe_ratio" in report["risk_metrics"]:
                sharpe = report["risk_metrics"]["sharpe_ratio"]["sharpe_ratio"]
                if sharpe < 1.0:
                    report["recommendations"].append(f"Sharpe ratio ({sharpe:.2f}) is below target (1.0)")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive risk report: {e}")
            return {"error": str(e)}
    
    def save_models(self):
        """Save risk management models and parameters"""
        try:
            # Save risk parameters
            risk_params = {
                "confidence_levels": self.confidence_levels,
                "time_horizons": self.time_horizons,
                "max_portfolio_var": self.max_portfolio_var,
                "max_position_size": self.max_position_size,
                "max_correlation": self.max_correlation
            }
            
            joblib.dump(risk_params, os.path.join(self.models_dir, 'risk_parameters.pkl'))
            
            logger.info("Risk management models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load risk management models and parameters"""
        try:
            # Load risk parameters
            params_path = os.path.join(self.models_dir, 'risk_parameters.pkl')
            if os.path.exists(params_path):
                risk_params = joblib.load(params_path)
                self.confidence_levels = risk_params.get('confidence_levels', [0.95, 0.99, 0.999])
                self.time_horizons = risk_params.get('time_horizons', [1, 5, 10, 20])
                self.max_portfolio_var = risk_params.get('max_portfolio_var', 0.05)
                self.max_position_size = risk_params.get('max_position_size', 0.1)
                self.max_correlation = risk_params.get('max_correlation', 0.7)
                logger.info("Risk management parameters loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
