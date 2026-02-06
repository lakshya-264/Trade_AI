"""
Real-time Parameter Tuning Service
Continuously optimizes parameters and adjusts thresholds automatically
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from scipy.optimize import minimize, differential_evolution
import json

logger = logging.getLogger(__name__)

class RealTimeParameterTuning:
    """Continuously optimize parameters in real-time"""
    
    def __init__(self):
        self.parameter_history = defaultdict(list)  # {model_name: [{params, performance, timestamp}]}
        self.current_parameters = {}  # {model_name: {param: value}}
        self.optimization_targets = {}  # {model_name: 'accuracy' | 'mse' | 'sharpe'}
        
        # Parameter bounds (can be customized per model)
        self.default_bounds = {
            'n_estimators': (50, 500),
            'max_depth': (3, 20),
            'learning_rate': (0.01, 0.3),
            'min_samples_split': (2, 20),
            'min_samples_leaf': (1, 10),
            'subsample': (0.5, 1.0),
            'colsample_bytree': (0.5, 1.0),
            'confidence_threshold': (0.5, 0.95),
            'stop_loss_percent': (0.5, 5.0),
            'take_profit_percent': (1.0, 10.0)
        }
        
        # Tuning frequency
        self.tuning_interval = timedelta(hours=1)  # Tune every hour
        self.last_tuning = {}  # {model_name: timestamp}
        
    def optimize_parameters(
        self,
        model_name: str,
        current_performance: Dict[str, float],
        parameter_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        optimization_target: str = 'accuracy'
    ) -> Dict[str, Any]:
        """
        Optimize parameters based on current performance
        
        Args:
            model_name: Name of the model
            current_performance: Current performance metrics
            parameter_bounds: Custom parameter bounds (optional)
            optimization_target: What to optimize ('accuracy', 'mse', 'sharpe')
        
        Returns:
            Dict with optimized parameters
        """
        try:
            # Check if tuning is needed
            if not self._should_tune(model_name):
                return {
                    "optimized": False,
                    "reason": "Tuning interval not reached",
                    "current_parameters": self.current_parameters.get(model_name, {})
                }
            
            # Get parameter bounds
            bounds = parameter_bounds or self.default_bounds
            
            # Get current parameters
            current_params = self.current_parameters.get(model_name, {})
            
            # Optimize parameters
            optimized_params = self._optimize(
                model_name,
                current_performance,
                bounds,
                optimization_target,
                current_params
            )
            
            # Update current parameters
            if model_name not in self.current_parameters:
                self.current_parameters[model_name] = {}
            
            self.current_parameters[model_name].update(optimized_params)
            
            # Store in history
            self._store_parameter_history(
                model_name,
                optimized_params,
                current_performance
            )
            
            # Update last tuning time
            self.last_tuning[model_name] = datetime.now()
            
            logger.info(f"Optimized parameters for {model_name}: {optimized_params}")
            
            return {
                "optimized": True,
                "model_name": model_name,
                "old_parameters": current_params,
                "new_parameters": optimized_params,
                "performance": current_performance,
                "optimization_target": optimization_target,
                "changes": self._calculate_changes(current_params, optimized_params)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing parameters for {model_name}: {e}")
            return {
                "optimized": False,
                "error": str(e)
            }
    
    def _should_tune(self, model_name: str) -> bool:
        """Check if parameters should be tuned"""
        if model_name not in self.last_tuning:
            return True
        
        time_since_tuning = datetime.now() - self.last_tuning[model_name]
        return time_since_tuning >= self.tuning_interval
    
    def _optimize(
        self,
        model_name: str,
        performance: Dict[str, float],
        bounds: Dict[str, Tuple[float, float]],
        target: str,
        current_params: Dict[str, float]
    ) -> Dict[str, float]:
        """Optimize parameters using gradient-free optimization"""
        try:
            # Get parameter names and bounds
            param_names = list(bounds.keys())
            param_bounds_list = [bounds[name] for name in param_names]
            
            # Get current values as starting point
            x0 = [current_params.get(name, (bounds[name][0] + bounds[name][1]) / 2) for name in param_names]
            
            # Objective function (minimize negative of target metric)
            def objective(params):
                # Convert to dict
                param_dict = dict(zip(param_names, params))
                
                # Estimate performance based on parameter values
                # This is a simplified model - in practice, you'd evaluate on validation set
                estimated_performance = self._estimate_performance(
                    model_name,
                    param_dict,
                    performance,
                    target
                )
                
                # Return negative (for minimization)
                return -estimated_performance
            
            # Optimize using differential evolution (robust to local minima)
            result = differential_evolution(
                objective,
                param_bounds_list,
                seed=42,
                maxiter=50,
                popsize=10
            )
            
            # Convert result to dict
            optimized = dict(zip(param_names, result.x))
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error in optimization: {e}")
            # Return current parameters if optimization fails
            return current_params
    
    def _estimate_performance(
        self,
        model_name: str,
        params: Dict[str, float],
        current_performance: Dict[str, float],
        target: str
    ) -> float:
        """Estimate performance based on parameters (simplified model)"""
        # This is a heuristic - in practice, you'd evaluate on validation set
        
        # Base performance
        base_performance = current_performance.get(target, 0.5)
        
        # Adjust based on parameter values
        # Higher n_estimators generally improves accuracy (with diminishing returns)
        if 'n_estimators' in params:
            n_est = params['n_estimators']
            improvement = min(0.1, (n_est - 100) / 1000)  # Max 10% improvement
            base_performance += improvement
        
        # Optimal learning rate improves performance
        if 'learning_rate' in params:
            lr = params['learning_rate']
            optimal_lr = 0.1
            lr_penalty = abs(lr - optimal_lr) * 0.5
            base_performance -= lr_penalty
        
        # Optimal max_depth improves performance
        if 'max_depth' in params:
            depth = params['max_depth']
            optimal_depth = 8
            depth_penalty = abs(depth - optimal_depth) * 0.01
            base_performance -= depth_penalty
        
        return max(0, min(1, base_performance))  # Clamp to [0, 1]
    
    def _calculate_changes(
        self,
        old_params: Dict[str, float],
        new_params: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate parameter changes"""
        changes = {}
        for param in new_params:
            if param in old_params:
                old_val = old_params[param]
                new_val = new_params[param]
                change = new_val - old_val
                change_percent = (change / old_val * 100) if old_val != 0 else 0
                
                changes[param] = {
                    "old": old_val,
                    "new": new_val,
                    "change": change,
                    "change_percent": change_percent
                }
            else:
                changes[param] = {
                    "old": None,
                    "new": new_params[param],
                    "change": new_params[param],
                    "change_percent": None
                }
        
        return changes
    
    def _store_parameter_history(
        self,
        model_name: str,
        parameters: Dict[str, float],
        performance: Dict[str, float]
    ):
        """Store parameter history"""
        self.parameter_history[model_name].append({
            'parameters': parameters.copy(),
            'performance': performance.copy(),
            'timestamp': datetime.now()
        })
        
        # Keep only last 100 entries
        if len(self.parameter_history[model_name]) > 100:
            self.parameter_history[model_name] = self.parameter_history[model_name][-100:]
    
    def adjust_threshold(
        self,
        threshold_name: str,
        current_value: float,
        performance_feedback: Dict[str, float],
        adjustment_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        Adjust a threshold based on performance feedback
        
        Args:
            threshold_name: Name of threshold ('confidence_threshold', 'stop_loss_percent', etc.)
            current_value: Current threshold value
            performance_feedback: Performance metrics
            adjustment_rate: How aggressively to adjust (0-1)
        
        Returns:
            Adjusted threshold value
        """
        try:
            # Determine adjustment direction based on performance
            accuracy = performance_feedback.get('accuracy', 0.5)
            false_positive_rate = performance_feedback.get('false_positive_rate', 0.5)
            false_negative_rate = performance_feedback.get('false_negative_rate', 0.5)
            
            adjustment = 0.0
            
            if threshold_name == 'confidence_threshold':
                # If too many false positives, increase threshold
                # If too many false negatives, decrease threshold
                if false_positive_rate > 0.3:
                    adjustment = adjustment_rate * 0.05  # Increase threshold
                elif false_negative_rate > 0.3:
                    adjustment = -adjustment_rate * 0.05  # Decrease threshold
                elif accuracy < 0.7:
                    # Low accuracy - adjust towards optimal
                    adjustment = adjustment_rate * 0.02 if current_value < 0.75 else -adjustment_rate * 0.02
            
            elif threshold_name == 'stop_loss_percent':
                # If too many stop losses hit, increase threshold
                # If too many losses exceed stop loss, decrease threshold
                stop_loss_hit_rate = performance_feedback.get('stop_loss_hit_rate', 0.5)
                if stop_loss_hit_rate > 0.4:
                    adjustment = adjustment_rate * 0.1  # Increase stop loss
                elif stop_loss_hit_rate < 0.1:
                    adjustment = -adjustment_rate * 0.1  # Decrease stop loss
            
            elif threshold_name == 'take_profit_percent':
                # If too few take profits hit, decrease threshold
                # If take profits hit too early, increase threshold
                take_profit_hit_rate = performance_feedback.get('take_profit_hit_rate', 0.5)
                if take_profit_hit_rate < 0.2:
                    adjustment = -adjustment_rate * 0.1  # Decrease take profit
                elif take_profit_hit_rate > 0.8:
                    adjustment = adjustment_rate * 0.1  # Increase take profit
            
            # Apply adjustment
            new_value = current_value + adjustment
            
            # Clamp to bounds
            bounds = self.default_bounds.get(threshold_name, (0, 1))
            new_value = max(bounds[0], min(bounds[1], new_value))
            
            logger.info(f"Adjusted {threshold_name}: {current_value:.4f} -> {new_value:.4f} (change: {adjustment:+.4f})")
            
            return {
                "success": True,
                "threshold_name": threshold_name,
                "old_value": current_value,
                "new_value": new_value,
                "adjustment": adjustment,
                "reason": self._get_adjustment_reason(threshold_name, performance_feedback)
            }
            
        except Exception as e:
            logger.error(f"Error adjusting threshold {threshold_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "old_value": current_value,
                "new_value": current_value
            }
    
    def _get_adjustment_reason(
        self,
        threshold_name: str,
        performance_feedback: Dict[str, float]
    ) -> str:
        """Get reason for threshold adjustment"""
        if threshold_name == 'confidence_threshold':
            fp_rate = performance_feedback.get('false_positive_rate', 0)
            fn_rate = performance_feedback.get('false_negative_rate', 0)
            if fp_rate > 0.3:
                return f"High false positive rate ({fp_rate:.2%}) - increasing threshold"
            elif fn_rate > 0.3:
                return f"High false negative rate ({fn_rate:.2%}) - decreasing threshold"
            else:
                return "Optimizing for better accuracy"
        
        return "Adjusting based on performance feedback"
    
    def get_current_parameters(self, model_name: str) -> Dict[str, float]:
        """Get current parameters for a model"""
        return self.current_parameters.get(model_name, {})
    
    def get_parameter_history(self, model_name: str, days: int = 7) -> List[Dict]:
        """Get parameter history for a model"""
        if model_name not in self.parameter_history:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        return [
            entry for entry in self.parameter_history[model_name]
            if entry['timestamp'] > cutoff
        ]

# Global instance
realtime_parameter_tuning = RealTimeParameterTuning()

