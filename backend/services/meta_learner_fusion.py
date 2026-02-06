"""
Meta-Learner/Fusion Layer Service
Optimal model weighting and ensemble fusion for trading decisions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import cross_val_score
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MetaLearnerFusion:
    """Meta-learner for optimal model weighting and ensemble fusion"""
    
    def __init__(self):
        self.meta_models = {}
        self.model_weights = {}
        self.performance_history = {}
        self.adaptive_weights = True
        
        # Models directory
        self.models_dir = "models/meta_learner"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Base models to combine
        self.base_models = {
            'temporal_lstm': None,
            'temporal_transformer': None,
            'technical_xgboost': None,
            'technical_lightgbm': None,
            'technical_random_forest': None,
            'alternative_text_cnn': None,
            'alternative_onchain_transformer': None,
            'alternative_multimodal': None,
            'bayesian_regime': None,
            'bayesian_correlation': None
        }
        
        # Meta-learner models
        self.meta_learner_models = {
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=0.1),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
        }
        
        # Performance tracking
        self.performance_window = 100  # Last 100 predictions
        self.min_performance_samples = 20
        
        # Weight adaptation parameters
        self.learning_rate = 0.01
        self.momentum = 0.9
        self.weight_decay = 0.001
        
    def initialize_base_models(self, model_instances: Dict):
        """Initialize base model instances"""
        try:
            for model_name, model_instance in model_instances.items():
                if model_name in self.base_models:
                    self.base_models[model_name] = model_instance
                    logger.info(f"Initialized {model_name} model")
            
            # Initialize equal weights
            active_models = [name for name, model in self.base_models.items() if model is not None]
            if active_models:
                equal_weight = 1.0 / len(active_models)
                self.model_weights = {model: equal_weight for model in active_models}
            
        except Exception as e:
            logger.error(f"Error initializing base models: {e}")
    
    def train_meta_learner(self, training_data: List[Dict]) -> Dict:
        """Train meta-learner on historical predictions and outcomes"""
        try:
            if not training_data:
                return {"error": "No training data provided"}
            
            # Prepare training data
            X_meta, y_meta = self._prepare_meta_training_data(training_data)
            
            if len(X_meta) == 0:
                return {"error": "No valid training data after preparation"}
            
            # Split data
            split_idx = int(0.8 * len(X_meta))
            X_train, X_val = X_meta[:split_idx], X_meta[split_idx:]
            y_train, y_val = y_meta[:split_idx], y_meta[split_idx:]
            
            # Train each meta-learner
            meta_results = {}
            
            for name, model in self.meta_learner_models.items():
                try:
                    # Train model
                    model.fit(X_train, y_train)
                    
                    # Validate
                    y_pred = model.predict(X_val)
                    mse = mean_squared_error(y_val, y_pred)
                    mae = mean_absolute_error(y_val, y_pred)
                    
                    # Cross-validation
                    cv_scores = cross_val_score(model, X_meta, y_meta, cv=5, scoring='neg_mean_squared_error')
                    cv_mean = -cv_scores.mean()
                    cv_std = cv_scores.std()
                    
                    meta_results[name] = {
                        'model': model,
                        'mse': mse,
                        'mae': mae,
                        'cv_mean': cv_mean,
                        'cv_std': cv_std,
                        'score': 1.0 / (1.0 + mse)  # Higher score for lower MSE
                    }
                    
                    logger.info(f"Trained {name} meta-learner: MSE={mse:.6f}, CV={cv_mean:.6f}±{cv_std:.6f}")
                    
                except Exception as e:
                    logger.error(f"Error training {name} meta-learner: {e}")
                    continue
            
            # Select best meta-learner
            if meta_results:
                best_meta = max(meta_results.items(), key=lambda x: x[1]['score'])
                self.meta_models['best'] = best_meta[1]['model']
                self.meta_models['all'] = {name: result['model'] for name, result in meta_results.items()}
                
                # Save meta-learner
                joblib.dump(self.meta_models, os.path.join(self.models_dir, 'meta_learner.pkl'))
                
                return {
                    "status": "success",
                    "best_meta_learner": best_meta[0],
                    "meta_results": {name: {k: v for k, v in result.items() if k != 'model'} 
                                   for name, result in meta_results.items()},
                    "n_training_samples": len(X_meta)
                }
            else:
                return {"error": "No meta-learners trained successfully"}
                
        except Exception as e:
            logger.error(f"Error training meta-learner: {e}")
            return {"error": str(e)}
    
    def _prepare_meta_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare meta-learning training data"""
        try:
            X_meta = []
            y_meta = []
            
            for data_point in training_data:
                # Extract base model predictions
                base_predictions = []
                for model_name in self.base_models.keys():
                    if model_name in data_point.get('predictions', {}):
                        base_predictions.append(data_point['predictions'][model_name])
                    else:
                        base_predictions.append(0.0)  # Default value for missing predictions
                
                # Extract market features
                market_features = data_point.get('market_features', [])
                
                # Extract technical features
                technical_features = data_point.get('technical_features', [])
                
                # Extract sentiment features
                sentiment_features = data_point.get('sentiment_features', [])
                
                # Extract regime features
                regime_features = data_point.get('regime_features', [])
                
                # Combine all features
                combined_features = base_predictions + market_features + technical_features + sentiment_features + regime_features
                
                X_meta.append(combined_features)
                
                # Target (actual return or price change)
                target = data_point.get('target', 0.0)
                y_meta.append(target)
            
            return np.array(X_meta), np.array(y_meta)
            
        except Exception as e:
            logger.error(f"Error preparing meta training data: {e}")
            return np.array([]), np.array([])
    
    def predict_ensemble(self, current_data: Dict) -> Dict:
        """Make ensemble prediction using meta-learner"""
        try:
            # Get base model predictions
            base_predictions = self._get_base_predictions(current_data)
            
            if not base_predictions:
                return {"error": "No base model predictions available"}
            
            # Prepare meta-features
            meta_features = self._prepare_meta_features(current_data, base_predictions)
            
            if len(meta_features) == 0:
                return {"error": "No meta-features available"}
            
            # Get meta-learner prediction
            if 'best' in self.meta_models:
                ensemble_prediction = self.meta_models['best'].predict([meta_features])[0]
            else:
                # Fallback to weighted average
                ensemble_prediction = self._weighted_average_prediction(base_predictions)
            
            # Calculate prediction confidence
            confidence = self._calculate_prediction_confidence(base_predictions, meta_features)
            
            # Get individual model weights
            model_weights = self._get_current_model_weights(base_predictions)
            
            return {
                "ensemble_prediction": float(ensemble_prediction),
                "base_predictions": base_predictions,
                "model_weights": model_weights,
                "confidence": float(confidence),
                "meta_features_used": len(meta_features),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error making ensemble prediction: {e}")
            return {"error": str(e)}
    
    def _get_base_predictions(self, current_data: Dict) -> Dict:
        """Get predictions from all base models"""
        try:
            predictions = {}
            
            for model_name, model in self.base_models.items():
                if model is None:
                    continue
                
                try:
                    # Get prediction based on model type
                    if 'temporal' in model_name:
                        pred = self._get_temporal_prediction(model, current_data)
                    elif 'technical' in model_name:
                        pred = self._get_technical_prediction(model, current_data)
                    elif 'alternative' in model_name:
                        pred = self._get_alternative_prediction(model, current_data)
                    elif 'bayesian' in model_name:
                        pred = self._get_bayesian_prediction(model, current_data)
                    else:
                        pred = 0.0
                    
                    predictions[model_name] = pred
                    
                except Exception as e:
                    logger.error(f"Error getting prediction from {model_name}: {e}")
                    predictions[model_name] = 0.0
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting base predictions: {e}")
            return {}
    
    def _get_temporal_prediction(self, model, current_data: Dict) -> float:
        """Get prediction from temporal model"""
        try:
            # This would interface with the temporal models
            # For now, return a mock prediction
            return np.random.normal(0, 0.01)
        except:
            return 0.0
    
    def _get_technical_prediction(self, model, current_data: Dict) -> float:
        """Get prediction from technical model"""
        try:
            # This would interface with the gradient boosting models
            # For now, return a mock prediction
            return np.random.normal(0, 0.01)
        except:
            return 0.0
    
    def _get_alternative_prediction(self, model, current_data: Dict) -> float:
        """Get prediction from alternative data model"""
        try:
            # This would interface with the alternative data models
            # For now, return a mock prediction
            return np.random.normal(0, 0.01)
        except:
            return 0.0
    
    def _get_bayesian_prediction(self, model, current_data: Dict) -> float:
        """Get prediction from Bayesian model"""
        try:
            # This would interface with the Bayesian models
            # For now, return a mock prediction
            return np.random.normal(0, 0.01)
        except:
            return 0.0
    
    def _prepare_meta_features(self, current_data: Dict, base_predictions: Dict) -> List[float]:
        """Prepare meta-features for ensemble prediction"""
        try:
            features = []
            
            # Base model predictions
            for model_name in self.base_models.keys():
                features.append(base_predictions.get(model_name, 0.0))
            
            # Market features
            market_features = current_data.get('market_features', [])
            features.extend(market_features)
            
            # Technical features
            technical_features = current_data.get('technical_features', [])
            features.extend(technical_features)
            
            # Sentiment features
            sentiment_features = current_data.get('sentiment_features', [])
            features.extend(sentiment_features)
            
            # Regime features
            regime_features = current_data.get('regime_features', [])
            features.extend(regime_features)
            
            # Prediction diversity
            if base_predictions:
                pred_values = list(base_predictions.values())
                features.append(np.std(pred_values))  # Prediction standard deviation
                features.append(np.mean(pred_values))  # Prediction mean
                features.append(np.max(pred_values) - np.min(pred_values))  # Prediction range
            else:
                features.extend([0.0, 0.0, 0.0])
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing meta-features: {e}")
            return []
    
    def _weighted_average_prediction(self, base_predictions: Dict) -> float:
        """Fallback weighted average prediction"""
        try:
            if not base_predictions:
                return 0.0
            
            weighted_sum = 0.0
            total_weight = 0.0
            
            for model_name, prediction in base_predictions.items():
                weight = self.model_weights.get(model_name, 0.0)
                weighted_sum += prediction * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating weighted average: {e}")
            return 0.0
    
    def _calculate_prediction_confidence(self, base_predictions: Dict, meta_features: List[float]) -> float:
        """Calculate prediction confidence"""
        try:
            if not base_predictions:
                return 0.0
            
            # Base confidence from prediction agreement
            pred_values = list(base_predictions.values())
            pred_std = np.std(pred_values)
            pred_mean = np.mean(pred_values)
            
            # Agreement score (inverse of standard deviation)
            agreement_score = 1.0 / (1.0 + pred_std) if pred_std > 0 else 1.0
            
            # Model weight confidence
            active_models = len([p for p in pred_values if p != 0.0])
            weight_confidence = min(active_models / len(self.base_models), 1.0)
            
            # Feature completeness
            feature_confidence = len(meta_features) / (len(self.base_models) + 20)  # Expected feature count
            
            # Combined confidence
            confidence = (agreement_score * 0.4 + weight_confidence * 0.3 + feature_confidence * 0.3)
            
            return min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return 0.0
    
    def _get_current_model_weights(self, base_predictions: Dict) -> Dict:
        """Get current model weights"""
        try:
            if not self.adaptive_weights:
                return self.model_weights.copy()
            
            # Adaptive weighting based on recent performance
            adaptive_weights = {}
            
            for model_name, prediction in base_predictions.items():
                base_weight = self.model_weights.get(model_name, 0.0)
                
                # Adjust weight based on performance history
                if model_name in self.performance_history:
                    recent_performance = self.performance_history[model_name][-10:]  # Last 10 predictions
                    performance_score = np.mean(recent_performance) if recent_performance else 0.5
                    
                    # Adjust weight based on performance
                    performance_factor = 0.5 + performance_score  # Range: 0.5 to 1.5
                    adaptive_weights[model_name] = base_weight * performance_factor
                else:
                    adaptive_weights[model_name] = base_weight
            
            # Normalize weights
            total_weight = sum(adaptive_weights.values())
            if total_weight > 0:
                adaptive_weights = {k: v / total_weight for k, v in adaptive_weights.items()}
            
            return adaptive_weights
            
        except Exception as e:
            logger.error(f"Error getting current model weights: {e}")
            return self.model_weights.copy()
    
    def update_model_performance(self, model_name: str, actual_value: float, predicted_value: float):
        """Update model performance history"""
        try:
            if model_name not in self.performance_history:
                self.performance_history[model_name] = []
            
            # Calculate performance metric (inverse of absolute error)
            error = abs(actual_value - predicted_value)
            performance = 1.0 / (1.0 + error) if error > 0 else 1.0
            
            self.performance_history[model_name].append(performance)
            
            # Keep only recent performance history
            if len(self.performance_history[model_name]) > self.performance_window:
                self.performance_history[model_name] = self.performance_history[model_name][-self.performance_window:]
            
            # Update model weights if adaptive weighting is enabled
            if self.adaptive_weights:
                self._update_adaptive_weights()
                
        except Exception as e:
            logger.error(f"Error updating model performance: {e}")
    
    def _update_adaptive_weights(self):
        """Update model weights based on performance"""
        try:
            if not self.performance_history:
                return
            
            # Calculate performance scores
            performance_scores = {}
            for model_name, history in self.performance_history.items():
                if len(history) >= self.min_performance_samples:
                    performance_scores[model_name] = np.mean(history)
                else:
                    performance_scores[model_name] = 0.5  # Default score
            
            # Update weights using performance scores
            total_score = sum(performance_scores.values())
            if total_score > 0:
                for model_name in self.model_weights.keys():
                    if model_name in performance_scores:
                        # Smooth weight update
                        old_weight = self.model_weights[model_name]
                        new_weight = performance_scores[model_name] / total_score
                        
                        # Apply learning rate and momentum
                        updated_weight = old_weight + self.learning_rate * (new_weight - old_weight)
                        self.model_weights[model_name] = max(0.0, min(1.0, updated_weight))
            
            # Normalize weights
            total_weight = sum(self.model_weights.values())
            if total_weight > 0:
                self.model_weights = {k: v / total_weight for k, v in self.model_weights.items()}
                
        except Exception as e:
            logger.error(f"Error updating adaptive weights: {e}")
    
    def get_ensemble_analysis(self) -> Dict:
        """Get comprehensive ensemble analysis"""
        try:
            analysis = {
                "model_weights": self.model_weights,
                "active_models": len([m for m in self.base_models.values() if m is not None]),
                "total_models": len(self.base_models),
                "adaptive_weighting": self.adaptive_weights,
                "performance_history": {
                    model: {
                        "recent_performance": history[-10:] if len(history) >= 10 else history,
                        "average_performance": np.mean(history) if history else 0.0,
                        "performance_trend": np.polyfit(range(len(history)), history, 1)[0] if len(history) > 1 else 0.0
                    }
                    for model, history in self.performance_history.items()
                },
                "meta_learner_status": "trained" if 'best' in self.meta_models else "not_trained",
                "last_updated": datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting ensemble analysis: {e}")
            return {"error": str(e)}
    
    def save_models(self):
        """Save meta-learner models and weights"""
        try:
            # Save meta-learner
            if self.meta_models:
                joblib.dump(self.meta_models, os.path.join(self.models_dir, 'meta_learner.pkl'))
            
            # Save model weights and performance history
            model_data = {
                'model_weights': self.model_weights,
                'performance_history': self.performance_history,
                'adaptive_weights': self.adaptive_weights,
                'learning_rate': self.learning_rate,
                'momentum': self.momentum
            }
            
            joblib.dump(model_data, os.path.join(self.models_dir, 'model_weights.pkl'))
            
            logger.info("Meta-learner models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load meta-learner models and weights"""
        try:
            # Load meta-learner
            meta_path = os.path.join(self.models_dir, 'meta_learner.pkl')
            if os.path.exists(meta_path):
                self.meta_models = joblib.load(meta_path)
                logger.info("Meta-learner loaded")
            
            # Load model weights and performance history
            weights_path = os.path.join(self.models_dir, 'model_weights.pkl')
            if os.path.exists(weights_path):
                model_data = joblib.load(weights_path)
                self.model_weights = model_data.get('model_weights', {})
                self.performance_history = model_data.get('performance_history', {})
                self.adaptive_weights = model_data.get('adaptive_weights', True)
                self.learning_rate = model_data.get('learning_rate', 0.01)
                self.momentum = model_data.get('momentum', 0.9)
                logger.info("Model weights and performance history loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def reset_weights(self):
        """Reset model weights to equal distribution"""
        try:
            active_models = [name for name, model in self.base_models.items() if model is not None]
            if active_models:
                equal_weight = 1.0 / len(active_models)
                self.model_weights = {model: equal_weight for model in active_models}
                logger.info("Model weights reset to equal distribution")
            
        except Exception as e:
            logger.error(f"Error resetting weights: {e}")
    
    def set_adaptive_weighting(self, enabled: bool):
        """Enable or disable adaptive weighting"""
        try:
            self.adaptive_weights = enabled
            logger.info(f"Adaptive weighting {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            logger.error(f"Error setting adaptive weighting: {e}")
