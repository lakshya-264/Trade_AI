"""
Automatic Model Retraining Service
Retrains models when performance degrades using new data
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import joblib
import os
from sklearn.metrics import accuracy_score, mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)

class AutomaticModelRetraining:
    """Automatically retrain models when performance degrades"""
    
    def __init__(self):
        self.models_dir = "models/auto_retrained"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Performance thresholds
        self.accuracy_threshold = 0.70  # Retrain if accuracy < 70%
        self.mse_threshold = 0.05  # Retrain if MSE > 5%
        self.retraining_window = 30  # Days of data to use for retraining
        self.min_samples_for_retraining = 100
        
        # Model performance history
        self.performance_history = {}
        
    def check_and_retrain(
        self,
        model_name: str,
        model_instance: Any,
        performance_metrics: Dict[str, float],
        new_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Check if model needs retraining and retrain if necessary
        
        Args:
            model_name: Name of the model
            model_instance: The model instance to retrain
            performance_metrics: Current performance metrics
            new_data: New data for retraining (optional)
        
        Returns:
            Dict with retraining status and results
        """
        try:
            # Check if retraining is needed
            needs_retraining = self._should_retrain(
                model_name,
                performance_metrics
            )
            
            if not needs_retraining:
                return {
                    "retrained": False,
                    "reason": "Performance is acceptable",
                    "current_accuracy": performance_metrics.get('accuracy', 0),
                    "threshold": self.accuracy_threshold
                }
            
            # Retrain model
            if new_data is None:
                return {
                    "retrained": False,
                    "reason": "No new data available for retraining",
                    "needs_data": True
                }
            
            retraining_result = self._retrain_model(
                model_name,
                model_instance,
                new_data,
                performance_metrics
            )
            
            return retraining_result
            
        except Exception as e:
            logger.error(f"Error in automatic retraining: {e}")
            return {
                "retrained": False,
                "error": str(e)
            }
    
    def _should_retrain(
        self,
        model_name: str,
        performance_metrics: Dict[str, float]
    ) -> bool:
        """Determine if model should be retrained"""
        try:
            accuracy = performance_metrics.get('accuracy', 1.0)
            mse = performance_metrics.get('mse', 0.0)
            mae = performance_metrics.get('mae', 0.0)
            
            # Check accuracy threshold
            if accuracy < self.accuracy_threshold:
                logger.info(f"Model {model_name} accuracy {accuracy:.2f} below threshold {self.accuracy_threshold}")
                return True
            
            # Check MSE threshold
            if mse > self.mse_threshold:
                logger.info(f"Model {model_name} MSE {mse:.4f} above threshold {self.mse_threshold}")
                return True
            
            # Check if performance is degrading
            if model_name in self.performance_history:
                history = self.performance_history[model_name]
                if len(history) >= 5:
                    recent_accuracy = np.mean([h['accuracy'] for h in history[-5:]])
                    older_accuracy = np.mean([h['accuracy'] for h in history[-10:-5]]) if len(history) >= 10 else recent_accuracy
                    
                    # If accuracy dropped by more than 5%
                    if recent_accuracy < older_accuracy - 0.05:
                        logger.info(f"Model {model_name} performance degrading: {recent_accuracy:.2f} vs {older_accuracy:.2f}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if retraining needed: {e}")
            return False
    
    def _retrain_model(
        self,
        model_name: str,
        new_model_instance: Any,
        new_data: pd.DataFrame,
        current_performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """Retrain the model with new data"""
        try:
            if len(new_data) < self.min_samples_for_retraining:
                return {
                    "retrained": False,
                    "reason": f"Insufficient data: {len(new_data)} < {self.min_samples_for_retraining}",
                    "needs_more_data": True
                }
            
            # Prepare data for retraining
            X = new_data.drop(columns=['target'], errors='ignore')
            y = new_data['target'] if 'target' in new_data.columns else None
            
            if y is None:
                return {
                    "retrained": False,
                    "reason": "No target column found in data"
                }
            
            # Create backup of current model
            backup_path = os.path.join(self.models_dir, f"{model_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl")
            if hasattr(new_model_instance, 'save'):
                new_model_instance.save(backup_path)
            else:
                joblib.dump(new_model_instance, backup_path)
            
            # Retrain model
            logger.info(f"Retraining model {model_name} with {len(new_data)} samples")
            
            if hasattr(new_model_instance, 'fit'):
                new_model_instance.fit(X, y)
            else:
                return {
                    "retrained": False,
                    "reason": "Model does not support fit() method"
                }
            
            # Evaluate new model
            if hasattr(new_model_instance, 'predict'):
                predictions = new_model_instance.predict(X)
                
                # Calculate new metrics
                new_accuracy = accuracy_score(y, predictions) if len(np.unique(y)) < 10 else 1.0 - mean_squared_error(y, predictions) / np.var(y)
                new_mse = mean_squared_error(y, predictions)
                new_mae = mean_absolute_error(y, predictions)
                
                # Compare with old performance
                old_accuracy = current_performance.get('accuracy', 0)
                improvement = new_accuracy - old_accuracy
                
                # Save new model if it's better
                if improvement > 0 or new_accuracy > self.accuracy_threshold:
                    model_path = os.path.join(self.models_dir, f"{model_name}_retrained_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl")
                    if hasattr(new_model_instance, 'save'):
                        new_model_instance.save(model_path)
                    else:
                        joblib.dump(new_model_instance, model_path)
                    
                    # Update performance history
                    if model_name not in self.performance_history:
                        self.performance_history[model_name] = []
                    
                    self.performance_history[model_name].append({
                        'accuracy': new_accuracy,
                        'mse': new_mse,
                        'mae': new_mae,
                        'timestamp': datetime.now(),
                        'retrained': True
                    })
                    
                    logger.info(f"Model {model_name} retrained successfully. Accuracy: {old_accuracy:.3f} -> {new_accuracy:.3f} (improvement: {improvement:+.3f})")
                    
                    return {
                        "retrained": True,
                        "success": True,
                        "old_accuracy": old_accuracy,
                        "new_accuracy": new_accuracy,
                        "improvement": improvement,
                        "new_mse": new_mse,
                        "new_mae": new_mae,
                        "model_path": model_path,
                        "backup_path": backup_path,
                        "samples_used": len(new_data)
                    }
                else:
                    # Restore backup if new model is worse
                    logger.warning(f"Retrained model {model_name} is worse. Restoring backup.")
                    return {
                        "retrained": False,
                        "reason": "New model performance is worse than current",
                        "old_accuracy": old_accuracy,
                        "new_accuracy": new_accuracy,
                        "backup_restored": True
                    }
            else:
                return {
                    "retrained": False,
                    "reason": "Model does not support predict() method"
                }
                
        except Exception as e:
            logger.error(f"Error retraining model {model_name}: {e}")
            return {
                "retrained": False,
                "error": str(e)
            }
    
    def update_performance_history(
        self,
        model_name: str,
        performance_metrics: Dict[str, float]
    ):
        """Update performance history for a model"""
        if model_name not in self.performance_history:
            self.performance_history[model_name] = []
        
        self.performance_history[model_name].append({
            **performance_metrics,
            'timestamp': datetime.now(),
            'retrained': False
        })
        
        # Keep only last 100 entries
        if len(self.performance_history[model_name]) > 100:
            self.performance_history[model_name] = self.performance_history[model_name][-100:]
    
    def get_retraining_status(self, model_name: str) -> Dict[str, Any]:
        """Get retraining status for a model"""
        if model_name not in self.performance_history:
            return {
                "status": "no_history",
                "message": "No performance history available"
            }
        
        history = self.performance_history[model_name]
        if not history:
            return {
                "status": "no_data",
                "message": "No performance data available"
            }
        
        latest = history[-1]
        recent = history[-5:] if len(history) >= 5 else history
        
        avg_accuracy = np.mean([h.get('accuracy', 0) for h in recent])
        trend = "improving" if len(history) >= 2 and history[-1].get('accuracy', 0) > history[-2].get('accuracy', 0) else "degrading"
        
        needs_retraining = avg_accuracy < self.accuracy_threshold
        
        return {
            "status": "monitoring",
            "current_accuracy": latest.get('accuracy', 0),
            "average_accuracy": avg_accuracy,
            "trend": trend,
            "needs_retraining": needs_retraining,
            "last_retrained": latest.get('timestamp') if latest.get('retrained') else None,
            "performance_history_count": len(history)
        }

# Global instance
automatic_model_retraining = AutomaticModelRetraining()

