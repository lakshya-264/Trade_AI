"""
Model Performance Monitoring Service
Tracks model accuracy and performance over time
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score

logger = logging.getLogger(__name__)

class ModelMonitoringService:
    """Monitor ML model performance"""
    
    def __init__(self):
        self.monitoring_dir = "models/monitoring"
        os.makedirs(self.monitoring_dir, exist_ok=True)
        self.performance_history_file = os.path.join(self.monitoring_dir, "performance_history.json")
        self.predictions_log_file = os.path.join(self.monitoring_dir, "predictions_log.jsonl")
    
    def log_prediction(
        self,
        model_name: str,
        symbol: str,
        prediction: Any,
        actual_value: Optional[float] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """Log a prediction for later evaluation"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "symbol": symbol,
                "prediction": float(prediction) if isinstance(prediction, (int, float, np.number)) else str(prediction),
                "actual_value": float(actual_value) if actual_value is not None else None,
                "confidence": float(confidence) if confidence is not None else None,
                "metadata": metadata or {}
            }
            
            with open(self.predictions_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.debug(f"Logged prediction for {model_name} on {symbol}")
            
        except Exception as e:
            logger.error(f"Error logging prediction: {e}")
    
    def evaluate_predictions(
        self,
        model_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Evaluate model predictions over the last N days"""
        try:
            # Read prediction logs
            predictions = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if not os.path.exists(self.predictions_log_file):
                return {"error": "No prediction logs found"}
            
            with open(self.predictions_log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time >= cutoff_date and entry['model_name'] == model_name:
                            if entry['actual_value'] is not None:
                                predictions.append(entry)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            if not predictions:
                return {"error": f"No predictions with actual values found for {model_name} in last {days} days"}
            
            # Calculate metrics
            pred_values = [p['prediction'] for p in predictions]
            actual_values = [p['actual_value'] for p in predictions]
            
            mse = mean_squared_error(actual_values, pred_values)
            mae = mean_absolute_error(actual_values, pred_values)
            rmse = np.sqrt(mse)
            
            # Calculate accuracy for classification (if applicable)
            accuracy = None
            if all(isinstance(p, (int, float)) for p in pred_values):
                # For regression, calculate percentage within 5%
                errors = [abs(p - a) / a for p, a in zip(pred_values, actual_values) if a != 0]
                accuracy = sum(1 for e in errors if e <= 0.05) / len(errors) if errors else 0
            
            # Calculate directional accuracy (for price predictions)
            directional_accuracy = None
            if len(predictions) > 1:
                pred_directions = [1 if pred_values[i] > pred_values[i-1] else -1 for i in range(1, len(pred_values))]
                actual_directions = [1 if actual_values[i] > actual_values[i-1] else -1 for i in range(1, len(actual_values))]
                directional_accuracy = sum(1 for p, a in zip(pred_directions, actual_directions) if p == a) / len(pred_directions) if pred_directions else 0
            
            return {
                "model_name": model_name,
                "period_days": days,
                "n_predictions": len(predictions),
                "metrics": {
                    "mse": float(mse),
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "accuracy": float(accuracy) if accuracy is not None else None,
                    "directional_accuracy": float(directional_accuracy) if directional_accuracy is not None else None
                },
                "evaluation_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error evaluating predictions: {e}")
            return {"error": str(e)}
    
    def save_performance_history(self, model_name: str, metrics: Dict[str, Any]):
        """Save performance metrics to history"""
        try:
            # Load existing history
            history = {}
            if os.path.exists(self.performance_history_file):
                with open(self.performance_history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new entry
            if model_name not in history:
                history[model_name] = []
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }
            
            history[model_name].append(entry)
            
            # Keep only last 100 entries per model
            if len(history[model_name]) > 100:
                history[model_name] = history[model_name][-100:]
            
            # Save
            with open(self.performance_history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Saved performance history for {model_name}")
            
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")
    
    def get_performance_history(self, model_name: str, limit: int = 10) -> List[Dict]:
        """Get performance history for a model"""
        try:
            if not os.path.exists(self.performance_history_file):
                return []
            
            with open(self.performance_history_file, 'r') as f:
                history = json.load(f)
            
            if model_name not in history:
                return []
            
            return history[model_name][-limit:]
            
        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return []
    
    def check_model_degradation(self, model_name: str, threshold: float = 0.1) -> Dict[str, Any]:
        """Check if model performance has degraded"""
        try:
            history = self.get_performance_history(model_name, limit=10)
            
            if len(history) < 2:
                return {
                    "status": "insufficient_data",
                    "message": "Not enough history to check degradation"
                }
            
            # Compare recent vs older performance
            recent = history[-3:]  # Last 3 evaluations
            older = history[-6:-3] if len(history) >= 6 else history[:-3]
            
            if not older:
                return {
                    "status": "insufficient_data",
                    "message": "Not enough history to compare"
                }
            
            # Calculate average RMSE
            recent_rmse = np.mean([e['metrics'].get('rmse', 0) for e in recent if 'rmse' in e.get('metrics', {})])
            older_rmse = np.mean([e['metrics'].get('rmse', 0) for e in older if 'rmse' in e.get('metrics', {})])
            
            if recent_rmse == 0 or older_rmse == 0:
                return {
                    "status": "insufficient_data",
                    "message": "Missing RMSE metrics"
                }
            
            degradation = (recent_rmse - older_rmse) / older_rmse
            
            if degradation > threshold:
                return {
                    "status": "degraded",
                    "degradation_percent": float(degradation * 100),
                    "recent_rmse": float(recent_rmse),
                    "older_rmse": float(older_rmse),
                    "message": f"Model performance degraded by {degradation*100:.2f}%"
                }
            else:
                return {
                    "status": "stable",
                    "degradation_percent": float(degradation * 100),
                    "recent_rmse": float(recent_rmse),
                    "older_rmse": float(older_rmse),
                    "message": "Model performance is stable"
                }
                
        except Exception as e:
            logger.error(f"Error checking model degradation: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report for all models"""
        try:
            report = {
                "report_date": datetime.now().isoformat(),
                "models": {}
            }
            
            model_names = ["ai_engine", "gradient_boosting", "meta_learner", "temporal"]
            
            for model_name in model_names:
                try:
                    evaluation = self.evaluate_predictions(model_name, days=30)
                    degradation = self.check_model_degradation(model_name)
                    
                    report["models"][model_name] = {
                        "evaluation": evaluation,
                        "degradation_check": degradation
                    }
                except Exception as e:
                    report["models"][model_name] = {
                        "error": str(e)
                    }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

# Global instance
model_monitoring = ModelMonitoringService()

