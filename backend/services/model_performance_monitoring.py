"""
Model Performance Monitoring Service
Tracks model performance and triggers retraining when needed
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import os
import json
from collections import defaultdict
from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

class ModelPerformanceMonitoring:
    """Monitor model performance and trigger retraining"""
    
    def __init__(self):
        self.performance_history = defaultdict(list)
        self.prediction_history = defaultdict(list)
        self.metrics_thresholds = {
            "accuracy_min": 0.70,
            "mse_max": 0.05,
            "mae_max": 0.03,
            "r2_min": 0.60
        }
        self.retraining_triggers = {
            "accuracy_drop": 0.05,  # Retrain if accuracy drops by 5%
            "consecutive_failures": 5,  # Retrain after 5 consecutive failures
            "days_since_training": 30  # Retrain if not trained in 30 days
        }
        
        # Performance database
        self.performance_db_path = "data/model_performance.json"
        self._load_performance_history()
    
    def log_prediction(
        self,
        model_name: str,
        symbol: str,
        prediction: float,
        actual_value: Optional[float] = None,
        confidence: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        """Log a model prediction"""
        try:
            prediction_record = {
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "symbol": symbol,
                "prediction": float(prediction),
                "actual_value": float(actual_value) if actual_value is not None else None,
                "confidence": float(confidence),
                "metadata": metadata or {}
            }
            
            self.prediction_history[model_name].append(prediction_record)
            
            # Calculate metrics if actual value is available
            if actual_value is not None:
                self._calculate_metrics(model_name, prediction, actual_value)
            
            # Save periodically
            if len(self.prediction_history[model_name]) % 100 == 0:
                self._save_performance_history()
                
        except Exception as e:
            logger.error(f"Error logging prediction: {e}")
    
    def _calculate_metrics(
        self,
        model_name: str,
        prediction: float,
        actual_value: float
    ):
        """Calculate performance metrics"""
        try:
            # Get recent predictions with actual values
            recent_predictions = [
                p for p in self.prediction_history[model_name][-100:]
                if p.get("actual_value") is not None
            ]
            
            if len(recent_predictions) < 10:
                return  # Need at least 10 predictions
            
            predictions = [p["prediction"] for p in recent_predictions]
            actuals = [p["actual_value"] for p in recent_predictions]
            
            # Calculate metrics
            mse = mean_squared_error(actuals, predictions)
            mae = mean_absolute_error(actuals, predictions)
            r2 = r2_score(actuals, predictions)
            
            # For classification, calculate accuracy
            # Assuming binary classification (price up/down)
            if len(set(actuals)) <= 2:
                pred_direction = [1 if p > 0 else 0 for p in predictions]
                actual_direction = [1 if a > 0 else 0 for a in actuals]
                accuracy = accuracy_score(actual_direction, pred_direction)
            else:
                # For regression, use R² as accuracy proxy
                accuracy = max(0, min(1, r2))
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "accuracy": float(accuracy),
                "mse": float(mse),
                "mae": float(mae),
                "r2": float(r2),
                "sample_size": len(recent_predictions)
            }
            
            self.performance_history[model_name].append(metrics)
            
            # Check if retraining is needed
            if self._should_retrain(model_name, metrics):
                logger.warning(f"⚠️ Model {model_name} performance degraded. Retraining recommended.")
                self._trigger_retraining(model_name, metrics)
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
    
    def _should_retrain(self, model_name: str, metrics: Dict) -> bool:
        """Determine if model should be retrained"""
        try:
            # Check accuracy threshold
            if metrics["accuracy"] < self.metrics_thresholds["accuracy_min"]:
                return True
            
            # Check MSE threshold
            if metrics["mse"] > self.metrics_thresholds["mse_max"]:
                return True
            
            # Check R² threshold
            if metrics["r2"] < self.metrics_thresholds["r2_min"]:
                return True
            
            # Check accuracy drop
            if len(self.performance_history[model_name]) > 1:
                previous_accuracy = self.performance_history[model_name][-2]["accuracy"]
                accuracy_drop = previous_accuracy - metrics["accuracy"]
                if accuracy_drop > self.retraining_triggers["accuracy_drop"]:
                    return True
            
            # Check consecutive failures
            recent_metrics = self.performance_history[model_name][-self.retraining_triggers["consecutive_failures"]:]
            if len(recent_metrics) >= self.retraining_triggers["consecutive_failures"]:
                all_below_threshold = all(
                    m["accuracy"] < self.metrics_thresholds["accuracy_min"]
                    for m in recent_metrics
                )
                if all_below_threshold:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking retraining condition: {e}")
            return False
    
    def _trigger_retraining(self, model_name: str, metrics: Dict):
        """Trigger model retraining"""
        try:
            from services.automatic_model_retraining import automatic_model_retraining
            
            retraining_request = {
                "model_name": model_name,
                "reason": "Performance degradation detected",
                "current_metrics": metrics,
                "thresholds": self.metrics_thresholds
            }
            
            # Log retraining request
            logger.info(f"🔄 Triggering retraining for {model_name}: {retraining_request['reason']}")
            
            # This would be handled by the automated training pipeline
            # For now, just log it
            
        except Exception as e:
            logger.error(f"Error triggering retraining: {e}")
    
    def get_performance_summary(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for model(s)"""
        try:
            if model_name:
                if model_name not in self.performance_history:
                    return {"error": f"No performance data for {model_name}"}
                
                metrics = self.performance_history[model_name]
                if not metrics:
                    return {"error": f"No metrics available for {model_name}"}
                
                latest = metrics[-1]
                return {
                    "model_name": model_name,
                    "latest_metrics": latest,
                    "trend": self._calculate_trend(metrics),
                    "status": self._get_status(latest),
                    "retraining_recommended": self._should_retrain(model_name, latest)
                }
            else:
                # Return summary for all models
                summary = {}
                for model_name in self.performance_history.keys():
                    summary[model_name] = self.get_performance_summary(model_name)
                return summary
                
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def _calculate_trend(self, metrics: List[Dict]) -> str:
        """Calculate performance trend"""
        if len(metrics) < 2:
            return "insufficient_data"
        
        recent = metrics[-5:] if len(metrics) >= 5 else metrics
        accuracies = [m["accuracy"] for m in recent]
        
        if len(accuracies) < 2:
            return "insufficient_data"
        
        # Simple linear trend
        trend_slope = (accuracies[-1] - accuracies[0]) / len(accuracies)
        
        if trend_slope > 0.01:
            return "improving"
        elif trend_slope < -0.01:
            return "degrading"
        else:
            return "stable"
    
    def _get_status(self, metrics: Dict) -> str:
        """Get model status"""
        if metrics["accuracy"] >= self.metrics_thresholds["accuracy_min"]:
            return "healthy"
        elif metrics["accuracy"] >= self.metrics_thresholds["accuracy_min"] * 0.9:
            return "warning"
        else:
            return "critical"
    
    def _load_performance_history(self):
        """Load performance history from disk"""
        try:
            if os.path.exists(self.performance_db_path):
                with open(self.performance_db_path, 'r') as f:
                    data = json.load(f)
                    self.performance_history = defaultdict(list, data.get("performance_history", {}))
                    self.prediction_history = defaultdict(list, data.get("prediction_history", {}))
        except Exception as e:
            logger.warning(f"Could not load performance history: {e}")
    
    def _save_performance_history(self):
        """Save performance history to disk"""
        try:
            os.makedirs(os.path.dirname(self.performance_db_path), exist_ok=True)
            
            # Keep only last 1000 records per model
            for model_name in self.performance_history:
                if len(self.performance_history[model_name]) > 1000:
                    self.performance_history[model_name] = self.performance_history[model_name][-1000:]
            
            for model_name in self.prediction_history:
                if len(self.prediction_history[model_name]) > 1000:
                    self.prediction_history[model_name] = self.prediction_history[model_name][-1000:]
            
            data = {
                "performance_history": dict(self.performance_history),
                "prediction_history": dict(self.prediction_history),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.performance_db_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")

# Create singleton instance
model_performance_monitoring = ModelPerformanceMonitoring()

