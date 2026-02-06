"""
Adaptive Algorithm Selection Service
Chooses best algorithm for each symbol and switches between models dynamically
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class AdaptiveAlgorithmSelection:
    """Adaptively select best algorithm for each symbol"""
    
    def __init__(self):
        self.algorithm_performance = defaultdict(dict)  # {symbol: {algorithm: performance}}
        self.current_selections = {}  # {symbol: best_algorithm}
        self.performance_history = defaultdict(list)  # {symbol: [{algorithm, metrics, timestamp}]}
        
        # Available algorithms
        self.available_algorithms = [
            'xgboost',
            'lightgbm',
            'random_forest',
            'gradient_boosting',
            'lstm',
            'transformer',
            'linear_regression'
        ]
        
        # Performance evaluation window (days)
        self.evaluation_window = 7
        self.min_evaluations = 5  # Minimum evaluations before switching
        
    def select_best_algorithm(
        self,
        symbol: str,
        algorithm_performances: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Select best algorithm for a symbol
        
        Args:
            symbol: Stock symbol
            algorithm_performances: Dict of {algorithm: {metrics}} (optional)
        
        Returns:
            Dict with selected algorithm and reasoning
        """
        try:
            # Update performance data if provided
            if algorithm_performances:
                self._update_performance(symbol, algorithm_performances)
            
            # Get best algorithm
            best_algorithm = self._get_best_algorithm(symbol)
            
            # Update current selection
            previous_algorithm = self.current_selections.get(symbol)
            self.current_selections[symbol] = best_algorithm
            
            # Check if algorithm changed
            algorithm_changed = previous_algorithm and previous_algorithm != best_algorithm
            
            return {
                "success": True,
                "symbol": symbol,
                "selected_algorithm": best_algorithm,
                "previous_algorithm": previous_algorithm,
                "algorithm_changed": algorithm_changed,
                "reasoning": self._get_selection_reasoning(symbol, best_algorithm),
                "all_performances": self.algorithm_performance.get(symbol, {})
            }
            
        except Exception as e:
            logger.error(f"Error selecting algorithm for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_performance(
        self,
        symbol: str,
        algorithm_performances: Dict[str, Dict[str, float]]
    ):
        """Update performance data for algorithms"""
        for algorithm, metrics in algorithm_performances.items():
            if symbol not in self.algorithm_performance:
                self.algorithm_performance[symbol] = {}
            
            if algorithm not in self.algorithm_performance[symbol]:
                self.algorithm_performance[symbol][algorithm] = {
                    'accuracy': [],
                    'mse': [],
                    'mae': [],
                    'sharpe': [],
                    'total_return': []
                }
            
            # Store metrics
            for metric_name, metric_value in metrics.items():
                if metric_name in self.algorithm_performance[symbol][algorithm]:
                    self.algorithm_performance[symbol][algorithm][metric_name].append(metric_value)
                    
                    # Keep only last 100 values
                    if len(self.algorithm_performance[symbol][algorithm][metric_name]) > 100:
                        self.algorithm_performance[symbol][algorithm][metric_name] = \
                            self.algorithm_performance[symbol][algorithm][metric_name][-100:]
            
            # Store in history
            self.performance_history[symbol].append({
                'algorithm': algorithm,
                'metrics': metrics,
                'timestamp': datetime.now()
            })
            
            # Keep only recent history
            cutoff = datetime.now() - timedelta(days=self.evaluation_window * 2)
            self.performance_history[symbol] = [
                h for h in self.performance_history[symbol]
                if h['timestamp'] > cutoff
            ]
    
    def _get_best_algorithm(self, symbol: str) -> str:
        """Get best performing algorithm for symbol"""
        if symbol not in self.algorithm_performance:
            # Default algorithm if no data
            return 'xgboost'
        
        performances = self.algorithm_performance[symbol]
        
        if not performances:
            return 'xgboost'
        
        # Calculate composite scores for each algorithm
        algorithm_scores = {}
        
        for algorithm, metrics in performances.items():
            # Get average metrics
            avg_accuracy = np.mean(metrics.get('accuracy', [0.5])) if metrics.get('accuracy') else 0.5
            avg_mse = np.mean(metrics.get('mse', [1.0])) if metrics.get('mse') else 1.0
            avg_sharpe = np.mean(metrics.get('sharpe', [0.0])) if metrics.get('sharpe') else 0.0
            avg_return = np.mean(metrics.get('total_return', [0.0])) if metrics.get('total_return') else 0.0
            
            # Calculate composite score
            # Higher accuracy, lower MSE, higher Sharpe, higher return = better
            composite_score = (
                avg_accuracy * 0.4 +  # 40% weight on accuracy
                (1 - min(avg_mse, 1.0)) * 0.2 +  # 20% weight on low MSE
                max(avg_sharpe, -2) / 2 * 0.2 +  # 20% weight on Sharpe (normalized)
                max(avg_return, -1) * 0.2  # 20% weight on return (normalized)
            )
            
            algorithm_scores[algorithm] = composite_score
        
        # Return algorithm with highest score
        best_algorithm = max(algorithm_scores.items(), key=lambda x: x[1])[0]
        
        return best_algorithm
    
    def _get_selection_reasoning(
        self,
        symbol: str,
        algorithm: str
    ) -> str:
        """Get reasoning for algorithm selection"""
        if symbol not in self.algorithm_performance:
            return f"No performance data available. Using default algorithm: {algorithm}"
        
        performances = self.algorithm_performance[symbol]
        if algorithm not in performances:
            return f"Algorithm {algorithm} selected as default"
        
        metrics = performances[algorithm]
        avg_accuracy = np.mean(metrics.get('accuracy', [0.5])) if metrics.get('accuracy') else 0.5
        avg_mse = np.mean(metrics.get('mse', [1.0])) if metrics.get('mse') else 1.0
        
        return (
            f"Selected {algorithm} for {symbol} based on performance: "
            f"accuracy={avg_accuracy:.3f}, MSE={avg_mse:.4f}. "
            f"This algorithm has shown best results for this symbol."
        )
    
    def should_switch_algorithm(
        self,
        symbol: str,
        current_algorithm: str,
        new_algorithm_performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Determine if algorithm should be switched
        
        Args:
            symbol: Stock symbol
            current_algorithm: Currently used algorithm
            new_algorithm_performance: Performance of alternative algorithm
        
        Returns:
            Dict with switch recommendation
        """
        try:
            if symbol not in self.algorithm_performance:
                return {
                    "should_switch": False,
                    "reason": "Insufficient performance data"
                }
            
            current_perf = self.algorithm_performance[symbol].get(current_algorithm)
            if not current_perf:
                return {
                    "should_switch": False,
                    "reason": "No performance data for current algorithm"
                }
            
            # Calculate current algorithm score
            current_accuracy = np.mean(current_perf.get('accuracy', [0.5])) if current_perf.get('accuracy') else 0.5
            current_mse = np.mean(current_perf.get('mse', [1.0])) if current_perf.get('mse') else 1.0
            
            # Calculate new algorithm score
            new_accuracy = new_algorithm_performance.get('accuracy', 0.5)
            new_mse = new_algorithm_performance.get('mse', 1.0)
            
            # Check if new algorithm is significantly better
            accuracy_improvement = new_accuracy - current_accuracy
            mse_improvement = current_mse - new_mse  # Lower MSE is better
            
            # Switch if improvement is significant (5% accuracy or 10% MSE)
            should_switch = (
                accuracy_improvement > 0.05 or
                mse_improvement > 0.1 or
                (accuracy_improvement > 0.02 and mse_improvement > 0.05)
            )
            
            if should_switch:
                return {
                    "should_switch": True,
                    "reason": f"New algorithm shows improvement: accuracy +{accuracy_improvement:.3f}, MSE -{mse_improvement:.4f}",
                    "current_accuracy": current_accuracy,
                    "new_accuracy": new_accuracy,
                    "current_mse": current_mse,
                    "new_mse": new_mse
                }
            else:
                return {
                    "should_switch": False,
                    "reason": "Current algorithm performance is acceptable",
                    "current_accuracy": current_accuracy,
                    "new_accuracy": new_accuracy
                }
                
        except Exception as e:
            logger.error(f"Error checking algorithm switch: {e}")
            return {
                "should_switch": False,
                "error": str(e)
            }
    
    def get_algorithm_recommendations(self, symbol: str) -> Dict[str, Any]:
        """Get algorithm recommendations for a symbol"""
        if symbol not in self.algorithm_performance:
            return {
                "recommendations": [
                    {
                        "algorithm": "xgboost",
                        "reason": "Default recommendation - no performance data available"
                    }
                ]
            }
        
        performances = self.algorithm_performance[symbol]
        
        # Rank algorithms by performance
        ranked = []
        for algorithm, metrics in performances.items():
            avg_accuracy = np.mean(metrics.get('accuracy', [0.5])) if metrics.get('accuracy') else 0.5
            avg_mse = np.mean(metrics.get('mse', [1.0])) if metrics.get('mse') else 1.0
            
            ranked.append({
                "algorithm": algorithm,
                "accuracy": avg_accuracy,
                "mse": avg_mse,
                "score": avg_accuracy * (1 - min(avg_mse, 1.0))
            })
        
        # Sort by score
        ranked.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "recommendations": ranked[:5],  # Top 5
            "current_selection": self.current_selections.get(symbol, "xgboost")
        }
    
    def get_current_selection(self, symbol: str) -> Optional[str]:
        """Get currently selected algorithm for symbol"""
        return self.current_selections.get(symbol)

# Global instance
adaptive_algorithm_selection = AdaptiveAlgorithmSelection()

