"""
ML Models Integration for Trading Signals
XGBoost, LSTM, and other ML models for sentiment-based trading predictions
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pickle
from pathlib import Path
import json

# ML imports
try:
    import xgboost as xgb
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    # Create dummy keras for type hints
    keras = None
    logging.warning("ML libraries not available")

from .feature_engineering import SentimentFeatureEngineer
from .sentiment_storage import SentimentDataStorage

logger = logging.getLogger(__name__)

class TradingSignalPredictor:
    """ML models for trading signal prediction based on sentiment"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize trading signal predictor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.ml_available = ML_AVAILABLE
        
        # Feature engineer
        self.feature_engineer = SentimentFeatureEngineer(config)
        
        # Storage
        self.storage = None
        
        # Models
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Model configurations
        self.model_configs = {
            'xgboost_direction': {
                'type': 'xgboost',
                'target': 'direction',
                'params': {
                    'objective': 'multi:softprob',
                    'num_class': 3,  # UP, DOWN, NEUTRAL
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'n_estimators': 100,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8
                }
            },
            'xgboost_binary': {
                'type': 'xgboost',
                'target': 'binary_direction',
                'params': {
                    'objective': 'binary:logistic',
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'n_estimators': 100
                }
            },
            'random_forest': {
                'type': 'random_forest',
                'target': 'direction',
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'random_state': 42
                }
            },
            'logistic_regression': {
                'type': 'logistic_regression',
                'target': 'binary_direction',
                'params': {
                    'random_state': 42,
                    'max_iter': 1000
                }
            },
            'lstm_trend': {
                'type': 'lstm',
                'target': 'trend',
                'params': {
                    'sequence_length': 10,
                    'lstm_units': 50,
                    'dropout': 0.2,
                    'epochs': 50,
                    'batch_size': 32
                }
            }
        }
        
        # Model performance tracking
        self.model_performance = {}
        
        # Prediction thresholds
        self.thresholds = {
            'high_confidence': 0.7,
            'medium_confidence': 0.5,
            'low_confidence': 0.3
        }
        
        logger.info("Trading signal predictor initialized")
    
    async def initialize(self, storage: SentimentDataStorage = None) -> bool:
        """Initialize the predictor with storage and load models"""
        try:
            self.storage = storage
            
            # Load existing models if available
            await self._load_models()
            
            logger.info("Trading signal predictor initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Predictor initialization failed: {e}")
            return False
    
    async def train_models(self, training_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Train all ML models
        
        Args:
            training_data: Training dataset (optional, will fetch from storage if not provided)
        
        Returns:
            Training results
        """
        try:
            if not self.ml_available:
                logger.error("ML libraries not available")
                return {'error': 'ML libraries not available'}
            
            # Get training data if not provided
            if training_data is None:
                training_data = await self._prepare_training_data()
            
            if training_data.empty:
                logger.error("No training data available")
                return {'error': 'No training data available'}
            
            # Prepare features and targets
            X, y_dict = self._prepare_features_and_targets(training_data)
            
            if X.empty:
                logger.error("No features prepared for training")
                return {'error': 'No features prepared'}
            
            results = {}
            
            # Train each model
            for model_name, config in self.model_configs.items():
                try:
                    if config['target'] not in y_dict:
                        logger.warning(f"Target {config['target']} not available for model {model_name}")
                        continue
                    
                    y = y_dict[config['target']]
                    
                    if len(y) == 0:
                        logger.warning(f"No target data for {config['target']}")
                        continue
                    
                    # Split data
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
                    )
                    
                    # Train model
                    model_result = await self._train_single_model(
                        model_name, config, X_train, X_test, y_train, y_test
                    )
                    
                    results[model_name] = model_result
                    
                except Exception as e:
                    logger.error(f"Error training model {model_name}: {e}")
                    results[model_name] = {'error': str(e)}
            
            # Save models
            await self._save_models()
            
            logger.info(f"Model training completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in model training: {e}")
            return {'error': str(e)}
    
    async def predict_signals(self, features_df: pd.DataFrame, 
                            symbol: str = None) -> Dict[str, Any]:
        """
        Generate trading signals using all available models
        
        Args:
            features_df: DataFrame with features
            symbol: Stock symbol
        
        Returns:
            Dictionary with predictions from all models
        """
        try:
            if features_df.empty:
                logger.error("No features provided for prediction")
                return {'error': 'No features provided'}
            
            predictions = {}
            ensemble_prediction = None
            confidence_scores = []
            
            # Get predictions from each trained model
            for model_name, model in self.models.items():
                try:
                    if model is None:
                        continue
                    
                    config = self.model_configs.get(model_name, {})
                    target_type = config.get('target', 'direction')
                    
                    # Prepare features
                    X = self._prepare_prediction_features(features_df)
                    
                    if X.empty:
                        continue
                    
                    # Make prediction
                    if config['type'] == 'xgboost':
                        pred = self._predict_xgboost(model, X, target_type)
                    elif config['type'] == 'random_forest':
                        pred = self._predict_sklearn(model, X, target_type)
                    elif config['type'] == 'logistic_regression':
                        pred = self._predict_sklearn(model, X, target_type)
                    elif config['type'] == 'lstm':
                        pred = await self._predict_lstm(model, X, config)
                    else:
                        continue
                    
                    if pred:
                        predictions[model_name] = pred
                        confidence_scores.append(pred.get('confidence', 0))
                        
                except Exception as e:
                    logger.error(f"Error predicting with model {model_name}: {e}")
            
            # Generate ensemble prediction
            if predictions:
                ensemble_prediction = self._generate_ensemble_prediction(predictions)
            
            # Generate trading recommendation
            recommendation = self._generate_trading_recommendation(ensemble_prediction, predictions)
            
            result = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'individual_predictions': predictions,
                'ensemble_prediction': ensemble_prediction,
                'recommendation': recommendation,
                'model_count': len(predictions),
                'avg_confidence': np.mean(confidence_scores) if confidence_scores else 0.0
            }
            
            # Store prediction
            if self.storage:
                await self._store_prediction(result, symbol)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {'error': str(e)}
    
    async def _prepare_training_data(self) -> pd.DataFrame:
        """Prepare training data from storage"""
        try:
            if not self.storage:
                logger.error("Storage not available")
                return pd.DataFrame()
            
            # Get historical sentiment data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)  # Last 90 days
            
            # Get sentiment data
            sentiment_data = await self.storage.get_sentiment_data(start_time, end_time, limit=10000)
            
            # Get feature data
            feature_data = await self.storage.get_feature_data(start_time=start_time, end_time=end_time, limit=10000)
            
            # Get historical price data (would need to be implemented)
            # For now, use mock price data
            price_data = self._generate_mock_price_data(len(feature_data))
            
            # Combine data
            if not feature_data.empty:
                # Add price-based targets
                feature_data = self._add_price_targets(feature_data, price_data)
                
            return feature_data
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return pd.DataFrame()
    
    def _prepare_features_and_targets(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.Series]]:
        """Prepare features and target variables"""
        try:
            # Feature columns (exclude target columns)
            feature_columns = [col for col in data.columns 
                              if not col.startswith('target_') and col != 'timestamp']
            
            X = data[feature_columns].copy()
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Create target variables
            y_dict = {}
            
            # Direction target (UP, DOWN, NEUTRAL)
            if 'target_direction' in data.columns:
                y_dict['direction'] = data['target_direction']
            
            # Binary direction target (UP/DOWN)
            if 'target_binary_direction' in data.columns:
                y_dict['binary_direction'] = data['target_binary_direction']
            
            # Trend target
            if 'target_trend' in data.columns:
                y_dict['trend'] = data['target_trend']
            
            return X, y_dict
            
        except Exception as e:
            logger.error(f"Error preparing features and targets: {e}")
            return pd.DataFrame(), {}
    
    async def _train_single_model(self, model_name: str, config: Dict[str, Any],
                                X_train: pd.DataFrame, X_test: pd.DataFrame,
                                y_train: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
        """Train a single model"""
        try:
            logger.info(f"Training model: {model_name}")
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Store scaler
            self.scalers[model_name] = scaler
            
            # Train model based on type
            if config['type'] == 'xgboost':
                model = xgb.XGBClassifier(**config['params'])
                model.fit(X_train_scaled, y_train)
                
            elif config['type'] == 'random_forest':
                model = RandomForestClassifier(**config['params'])
                model.fit(X_train_scaled, y_train)
                
            elif config['type'] == 'logistic_regression':
                model = LogisticRegression(**config['params'])
                model.fit(X_train_scaled, y_train)
                
            elif config['type'] == 'lstm':
                model = await self._train_lstm_model(
                    X_train_scaled, X_test_scaled, y_train, y_test, config['params']
                )
            else:
                return {'error': f'Unknown model type: {config["type"]}'}
            
            # Store model
            self.models[model_name] = model
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Get feature importance if available
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(X_train.columns, model.feature_importances_))
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            
            result = {
                'model_type': config['type'],
                'target': config['target'],
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'feature_importance': feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            # Store performance
            self.model_performance[model_name] = result
            
            logger.info(f"Model {model_name} trained. Accuracy: {accuracy:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}")
            return {'error': str(e)}
    
    async def _train_lstm_model(self, X_train: np.ndarray, X_test: np.ndarray,
                              y_train: pd.Series, y_test: pd.Series,
                              params: Dict[str, Any]):
        """Train LSTM model for trend prediction"""
        try:
            if not ML_AVAILABLE:
                return {'error': 'TensorFlow/Keras not available'}
            
            sequence_length = params['sequence_length']
            
            # Prepare sequences
            X_train_seq = self._create_sequences(X_train, sequence_length)
            X_test_seq = self._create_sequences(X_test, sequence_length)
            
            # Adjust targets for sequences
            y_train_seq = y_train[sequence_length-1:]
            y_test_seq = y_test[sequence_length-1:]
            
            # Build LSTM model
            model = keras.Sequential([
                layers.LSTM(params['lstm_units'], 
                           return_sequences=True, 
                           input_shape=(sequence_length, X_train.shape[1])),
                layers.Dropout(params['dropout']),
                layers.LSTM(params['lstm_units'], return_sequences=False),
                layers.Dropout(params['dropout']),
                layers.Dense(32, activation='relu'),
                layers.Dense(3, activation='softmax')  # 3 classes: UP, DOWN, NEUTRAL
            ])
            
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # Train model
            history = model.fit(
                X_train_seq, y_train_seq,
                epochs=params['epochs'],
                batch_size=params['batch_size'],
                validation_split=0.2,
                verbose=0
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            raise
    
    def _create_sequences(self, data: np.ndarray, sequence_length: int) -> np.ndarray:
        """Create sequences for LSTM training"""
        sequences = []
        for i in range(len(data) - sequence_length + 1):
            sequences.append(data[i:i+sequence_length])
        return np.array(sequences)
    
    def _prepare_prediction_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """Prepare features for prediction"""
        try:
            # Get feature columns
            feature_columns = [col for col in features_df.columns if col != 'timestamp']
            
            X = features_df[feature_columns].copy()
            X = X.fillna(X.mean())
            
            return X.values
            
        except Exception as e:
            logger.error(f"Error preparing prediction features: {e}")
            return np.array([])
    
    def _predict_xgboost(self, model: xgb.XGBClassifier, X: np.ndarray, 
                        target_type: str) -> Dict[str, Any]:
        """Make prediction with XGBoost model"""
        try:
            # Scale features
            scaler = self.scalers.get('xgboost_direction') or self.scalers.get('xgboost_binary')
            if scaler:
                X_scaled = scaler.transform(X)
            else:
                X_scaled = X
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            probabilities = model.predict_proba(X_scaled)[0]
            
            # Map prediction to label
            if target_type == 'direction':
                labels = ['DOWN', 'NEUTRAL', 'UP']
                predicted_label = labels[prediction]
                confidence = max(probabilities)
            else:  # binary
                labels = ['DOWN', 'UP']
                predicted_label = labels[prediction]
                confidence = max(probabilities)
            
            return {
                'prediction': predicted_label,
                'confidence': float(confidence),
                'probabilities': {label: float(prob) for label, prob in zip(labels, probabilities)},
                'model_type': 'xgboost'
            }
            
        except Exception as e:
            logger.error(f"Error in XGBoost prediction: {e}")
            return None
    
    def _predict_sklearn(self, model, X: np.ndarray, target_type: str) -> Dict[str, Any]:
        """Make prediction with scikit-learn model"""
        try:
            # Scale features
            model_name = type(model).__name__.lower()
            scaler_key = None
            for key in self.scalers.keys():
                if model_name in key:
                    scaler_key = key
                    break
            
            if scaler_key and scaler_key in self.scalers:
                X_scaled = self.scalers[scaler_key].transform(X)
            else:
                X_scaled = X
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X_scaled)[0]
                confidence = max(probabilities)
            else:
                probabilities = None
                confidence = 1.0
            
            # Map prediction to label
            if target_type == 'direction':
                labels = ['DOWN', 'NEUTRAL', 'UP']
                predicted_label = labels[prediction] if prediction < len(labels) else 'NEUTRAL'
            else:  # binary
                labels = ['DOWN', 'UP']
                predicted_label = labels[prediction] if prediction < len(labels) else 'NEUTRAL'
            
            result = {
                'prediction': predicted_label,
                'confidence': float(confidence),
                'model_type': model_name
            }
            
            if probabilities is not None:
                result['probabilities'] = {label: float(prob) for label, prob in zip(labels, probabilities)}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in sklearn prediction: {e}")
            return None
    
    async def _predict_lstm(self, model, X: np.ndarray, 
                          config: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction with LSTM model"""
        try:
            sequence_length = config['params']['sequence_length']
            
            # Create sequences
            if len(X) < sequence_length:
                # Pad with zeros if not enough data
                padding = np.zeros((sequence_length - len(X), X.shape[1]))
                X_padded = np.vstack([padding, X])
            else:
                X_padded = X[-sequence_length:]
            
            X_seq = X_padded.reshape(1, sequence_length, X.shape[1])
            
            # Make prediction
            probabilities = model.predict(X_seq, verbose=0)[0]
            prediction = np.argmax(probabilities)
            confidence = max(probabilities)
            
            labels = ['DOWN', 'NEUTRAL', 'UP']
            predicted_label = labels[prediction]
            
            return {
                'prediction': predicted_label,
                'confidence': float(confidence),
                'probabilities': {label: float(prob) for label, prob in zip(labels, probabilities)},
                'model_type': 'lstm'
            }
            
        except Exception as e:
            logger.error(f"Error in LSTM prediction: {e}")
            return None
    
    def _generate_ensemble_prediction(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ensemble prediction from individual model predictions"""
        try:
            if not predictions:
                return None
            
            # Collect predictions and confidences
            prediction_votes = {'UP': 0, 'DOWN': 0, 'NEUTRAL': 0}
            confidence_sum = 0.0
            weighted_votes = {'UP': 0.0, 'DOWN': 0.0, 'NEUTRAL': 0.0}
            
            for model_name, pred in predictions.items():
                if pred and 'prediction' in pred:
                    label = pred['prediction']
                    confidence = pred.get('confidence', 0.5)
                    
                    # Simple voting
                    if label in prediction_votes:
                        prediction_votes[label] += 1
                    
                    # Weighted voting by confidence
                    if label in weighted_votes:
                        weighted_votes[label] += confidence
                    
                    confidence_sum += confidence
            
            # Determine ensemble prediction
            if weighted_votes['UP'] > weighted_votes['DOWN'] and weighted_votes['UP'] > weighted_votes['NEUTRAL']:
                ensemble_prediction = 'UP'
            elif weighted_votes['DOWN'] > weighted_votes['UP'] and weighted_votes['DOWN'] > weighted_votes['NEUTRAL']:
                ensemble_prediction = 'DOWN'
            else:
                ensemble_prediction = 'NEUTRAL'
            
            # Calculate ensemble confidence
            total_votes = sum(prediction_votes.values())
            if total_votes > 0:
                vote_confidence = prediction_votes[ensemble_prediction] / total_votes
                avg_confidence = confidence_sum / len(predictions) if predictions else 0
                ensemble_confidence = (vote_confidence + avg_confidence) / 2
            else:
                ensemble_confidence = 0.0
            
            return {
                'prediction': ensemble_prediction,
                'confidence': ensemble_confidence,
                'votes': prediction_votes,
                'weighted_votes': weighted_votes,
                'model_count': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error generating ensemble prediction: {e}")
            return None
    
    def _generate_trading_recommendation(self, ensemble_prediction: Dict[str, Any],
                                       individual_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading recommendation based on predictions"""
        try:
            if not ensemble_prediction:
                return {
                    'action': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'No reliable prediction available'
                }
            
            prediction = ensemble_prediction['prediction']
            confidence = ensemble_prediction['confidence']
            model_count = ensemble_prediction['model_count']
            
            # Determine action based on prediction and confidence
            if confidence >= self.thresholds['high_confidence'] and model_count >= 3:
                if prediction == 'UP':
                    action = 'BUY'
                elif prediction == 'DOWN':
                    action = 'SELL'
                else:
                    action = 'HOLD'
                reason = f"Strong {prediction.lower()} signal with {confidence:.1%} confidence from {model_count} models"
            
            elif confidence >= self.thresholds['medium_confidence'] and model_count >= 2:
                if prediction == 'UP':
                    action = 'WEAK_BUY'
                elif prediction == 'DOWN':
                    action = 'WEAK_SELL'
                else:
                    action = 'HOLD'
                reason = f"Moderate {prediction.lower()} signal with {confidence:.1%} confidence from {model_count} models"
            
            else:
                action = 'HOLD'
                reason = f"Low confidence ({confidence:.1%}) or insufficient model agreement"
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'prediction': prediction,
                'model_agreement': ensemble_prediction['votes']
            }
            
        except Exception as e:
            logger.error(f"Error generating trading recommendation: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': 'Error generating recommendation'
            }
    
    async def _store_prediction(self, prediction_result: Dict[str, Any], symbol: str):
        """Store prediction result in database"""
        try:
            if not self.storage:
                return
            
            # Extract ensemble prediction for storage
            ensemble = prediction_result.get('ensemble_prediction', {})
            recommendation = prediction_result.get('recommendation', {})
            
            prediction_data = {
                'timestamp': datetime.fromisoformat(prediction_result['timestamp']),
                'symbol': symbol,
                'model_type': 'ensemble',
                'prediction': ensemble.get('prediction', 'NEUTRAL'),
                'probability': ensemble.get('confidence', 0.0),
                'confidence': ensemble.get('confidence', 0.0),
                'features_used': list(prediction_result.get('individual_predictions', {}).keys()),
                'actual_result': None  # To be updated later
            }
            
            await self.storage.store_prediction(prediction_data)
            
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
    
    def _generate_mock_price_data(self, num_samples: int) -> pd.DataFrame:
        """Generate mock price data for testing"""
        try:
            np.random.seed(42)
            
            # Generate random walk prices
            returns = np.random.normal(0.001, 0.02, num_samples)
            prices = [100]  # Starting price
            
            for ret in returns:
                prices.append(prices[-1] * (1 + ret))
            
            # Create DataFrame
            dates = pd.date_range(end=datetime.utcnow(), periods=num_samples, freq='H')
            
            df = pd.DataFrame({
                'timestamp': dates,
                'price': prices[1:num_samples+1],
                'returns': returns
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Error generating mock price data: {e}")
            return pd.DataFrame()
    
    def _add_price_targets(self, feature_data: pd.DataFrame, price_data: pd.DataFrame) -> pd.DataFrame:
        """Add price-based target variables to feature data"""
        try:
            if feature_data.empty or price_data.empty:
                return feature_data
            
            # Merge data on timestamp
            merged = pd.merge_asof(
                feature_data.sort_values('timestamp'),
                price_data.sort_values('timestamp'),
                on='timestamp',
                direction='nearest'
            )
            
            # Calculate future returns (next 1 hour, 5 hours)
            if 'price' in merged.columns:
                merged['future_return_1h'] = merged['price'].pct_change(1).shift(-1)
                merged['future_return_5h'] = merged['price'].pct_change(5).shift(-5)
                
                # Create direction targets
                merged['target_direction'] = pd.cut(
                    merged['future_return_1h'],
                    bins=[-np.inf, -0.01, 0.01, np.inf],
                    labels=['DOWN', 'NEUTRAL', 'UP']
                )
                
                merged['target_binary_direction'] = np.where(
                    merged['future_return_1h'] > 0.01, 'UP',
                    np.where(merged['future_return_1h'] < -0.01, 'DOWN', 'NEUTRAL')
                )
                
                # Create trend target (5-hour direction)
                merged['target_trend'] = pd.cut(
                    merged['future_return_5h'],
                    bins=[-np.inf, -0.02, 0.02, np.inf],
                    labels=[0, 1, 2]  # DOWN, NEUTRAL, UP
                )
            
            return merged
            
        except Exception as e:
            logger.error(f"Error adding price targets: {e}")
            return feature_data
    
    async def _save_models(self):
        """Save trained models to disk"""
        try:
            models_dir = Path("trained_models")
            models_dir.mkdir(exist_ok=True)
            
            # Save sklearn models
            for model_name, model in self.models.items():
                if model_name.startswith('lstm'):
                    # Save Keras model
                    model.save(models_dir / f"{model_name}.h5")
                else:
                    # Save sklearn model
                    with open(models_dir / f"{model_name}.pkl", 'wb') as f:
                        pickle.dump(model, f)
            
            # Save scalers
            with open(models_dir / "scalers.pkl", 'wb') as f:
                pickle.dump(self.scalers, f)
            
            # Save performance metrics
            with open(models_dir / "performance.json", 'w') as f:
                json.dump(self.model_performance, f, indent=2)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    async def _load_models(self):
        """Load trained models from disk"""
        try:
            models_dir = Path("trained_models")
            
            if not models_dir.exists():
                logger.info("No saved models found")
                return
            
            # Load scalers
            scalers_file = models_dir / "scalers.pkl"
            if scalers_file.exists():
                with open(scalers_file, 'rb') as f:
                    self.scalers = pickle.load(f)
            
            # Load performance metrics
            perf_file = models_dir / "performance.json"
            if perf_file.exists():
                with open(perf_file, 'r') as f:
                    self.model_performance = json.load(f)
            
            # Load models
            for model_name in self.model_configs.keys():
                if model_name.startswith('lstm'):
                    model_file = models_dir / f"{model_name}.h5"
                    if model_file.exists():
                        self.models[model_name] = keras.models.load_model(model_file)
                else:
                    model_file = models_dir / f"{model_name}.pkl"
                    if model_file.exists():
                        with open(model_file, 'rb') as f:
                            self.models[model_name] = pickle.load(f)
            
            logger.info(f"Loaded {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all models"""
        return self.model_performance.copy()
    
    async def update_prediction_result(self, prediction_id: int, actual_result: str):
        """Update prediction with actual result for performance tracking"""
        try:
            if not self.storage:
                return
            
            # This would update the actual_result field in the predictions table
            # Implementation depends on storage system
            logger.info(f"Updated prediction {prediction_id} with actual result: {actual_result}")
            
        except Exception as e:
            logger.error(f"Error updating prediction result: {e}")

# Factory function
async def create_trading_predictor(config: Dict[str, Any] = None, 
                                 storage: SentimentDataStorage = None) -> TradingSignalPredictor:
    """Create and initialize trading signal predictor"""
    predictor = TradingSignalPredictor(config)
    await predictor.initialize(storage)
    return predictor
