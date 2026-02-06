"""
AI Engine Service
Combines technical analysis, sentiment analysis, and machine learning
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = "models/ai_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        
        # Load or initialize model
        self._load_or_initialize_model()
    
    def generate_signals(self, df: pd.DataFrame, analysis_data: Dict) -> Dict:
        """Generate AI-powered trading signals"""
        try:
            # Extract features
            features = self._extract_features(df, analysis_data)
            
            # Generate predictions
            predictions = self._predict_signals(features)
            
            # Calculate confidence and price targets
            confidence = self._calculate_confidence(features, analysis_data)
            price_target = self._calculate_price_target(df, predictions)
            stop_loss = self._calculate_stop_loss(df, predictions)
            
            # Determine final signal
            signal = self._determine_signal(predictions, confidence)
            
            return {
                "signal": signal,
                "confidence": confidence,
                "price_target": price_target,
                "stop_loss": stop_loss,
                "features": features,
                "predictions": predictions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating AI signals: {e}")
            return {
                "signal": "HOLD",
                "confidence": 0.0,
                "price_target": 0.0,
                "stop_loss": 0.0,
                "features": {},
                "predictions": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_features(self, df: pd.DataFrame, analysis_data: Dict) -> Dict:
        """Extract features for ML model"""
        try:
            features = {}
            
            # Price features
            current_price = df["close"].iloc[-1]
            features["price_change_1d"] = (current_price - df["close"].iloc[-2]) / df["close"].iloc[-2] if len(df) > 1 else 0
            features["price_change_5d"] = (current_price - df["close"].iloc[-6]) / df["close"].iloc[-6] if len(df) > 5 else 0
            features["price_change_20d"] = (current_price - df["close"].iloc[-21]) / df["close"].iloc[-21] if len(df) > 20 else 0
            
            # Volume features
            if "volume" in df.columns:
                avg_volume = df["volume"].tail(20).mean()
                current_volume = df["volume"].iloc[-1]
                features["volume_ratio"] = current_volume / avg_volume if avg_volume > 0 else 1
            else:
                features["volume_ratio"] = 1
            
            # Volatility features
            features["volatility_20d"] = df["close"].tail(20).std() / df["close"].tail(20).mean() if len(df) > 20 else 0
            
            # Technical analysis features
            if "technical" in analysis_data and "indicators" in analysis_data["technical"]:
                indicators = analysis_data["technical"]["indicators"]
                
                # RSI
                if "rsi" in indicators and not pd.isna(indicators["rsi"].iloc[-1]):
                    features["rsi"] = indicators["rsi"].iloc[-1] / 100  # Normalize to 0-1
                else:
                    features["rsi"] = 0.5
                
                # MACD
                if "macd" in indicators and "macd_signal" in indicators:
                    macd = indicators["macd"].iloc[-1]
                    macd_signal = indicators["macd_signal"].iloc[-1]
                    if not pd.isna(macd) and not pd.isna(macd_signal):
                        features["macd_diff"] = (macd - macd_signal) / current_price
                    else:
                        features["macd_diff"] = 0
                else:
                    features["macd_diff"] = 0
                
                # Moving averages
                if "sma_20" in indicators and not pd.isna(indicators["sma_20"].iloc[-1]):
                    features["sma_20_ratio"] = current_price / indicators["sma_20"].iloc[-1]
                else:
                    features["sma_20_ratio"] = 1
                
                if "sma_50" in indicators and not pd.isna(indicators["sma_50"].iloc[-1]):
                    features["sma_50_ratio"] = current_price / indicators["sma_50"].iloc[-1]
                else:
                    features["sma_50_ratio"] = 1
                
                # Bollinger Bands
                if "bb_upper" in indicators and "bb_lower" in indicators:
                    bb_upper = indicators["bb_upper"].iloc[-1]
                    bb_lower = indicators["bb_lower"].iloc[-1]
                    if not pd.isna(bb_upper) and not pd.isna(bb_lower):
                        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                        features["bb_position"] = bb_position
                    else:
                        features["bb_position"] = 0.5
                else:
                    features["bb_position"] = 0.5
            
            # Sentiment features
            if "sentiment" in analysis_data:
                sentiment = analysis_data["sentiment"]
                features["sentiment_score"] = sentiment.get("sentiment_score", 0)
                features["sentiment_confidence"] = sentiment.get("confidence", 0)
            else:
                features["sentiment_score"] = 0
                features["sentiment_confidence"] = 0
            
            # Market condition features
            features["is_weekend"] = 1 if datetime.now().weekday() >= 5 else 0
            features["hour_of_day"] = datetime.now().hour / 24
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    def _predict_signals(self, features: Dict) -> Dict:
        """Predict trading signals using ML model"""
        try:
            if self.model is None:
                return {"buy_probability": 0.5, "sell_probability": 0.5, "hold_probability": 0.5}
            
            # Convert features to array
            feature_array = np.array(list(features.values())).reshape(1, -1)
            
            # Scale features
            feature_array_scaled = self.scaler.transform(feature_array)
            
            # Get predictions
            probabilities = self.model.predict_proba(feature_array_scaled)[0]
            
            # Map to signal probabilities
            if len(probabilities) == 3:  # Buy, Hold, Sell
                return {
                    "buy_probability": probabilities[0],
                    "hold_probability": probabilities[1],
                    "sell_probability": probabilities[2]
                }
            else:
                return {
                    "buy_probability": 0.5,
                    "sell_probability": 0.5,
                    "hold_probability": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error predicting signals: {e}")
            return {"buy_probability": 0.5, "sell_probability": 0.5, "hold_probability": 0.5}
    
    def _calculate_confidence(self, features: Dict, analysis_data: Dict) -> float:
        """Calculate confidence score for the prediction"""
        try:
            confidence_factors = []
            
            # Technical analysis confidence
            if "technical" in analysis_data and "signals" in analysis_data["technical"]:
                tech_signals = analysis_data["technical"]["signals"]
                if "strength" in tech_signals:
                    confidence_factors.append(tech_signals["strength"])
            
            # Sentiment confidence
            if "sentiment" in analysis_data:
                sentiment_conf = analysis_data["sentiment"].get("confidence", 0)
                confidence_factors.append(sentiment_conf)
            
            # Volume confidence
            if "volume_ratio" in features:
                volume_conf = min(features["volume_ratio"] / 2, 1.0)  # Higher volume = higher confidence
                confidence_factors.append(volume_conf)
            
            # Data quality confidence
            data_quality = min(len(features) / 10, 1.0)  # More features = higher confidence
            confidence_factors.append(data_quality)
            
            # Calculate weighted average
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _calculate_price_target(self, df: pd.DataFrame, predictions: Dict) -> float:
        """Calculate price target based on predictions"""
        try:
            current_price = df["close"].iloc[-1]
            
            # Calculate expected return based on predictions
            buy_prob = predictions.get("buy_probability", 0.5)
            sell_prob = predictions.get("sell_probability", 0.5)
            
            # Weighted expected return
            expected_return = (buy_prob - sell_prob) * 0.1  # Max 10% expected return
            
            # Calculate price target
            price_target = current_price * (1 + expected_return)
            
            return round(price_target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating price target: {e}")
            return df["close"].iloc[-1]
    
    def _calculate_stop_loss(self, df: pd.DataFrame, predictions: Dict) -> float:
        """Calculate stop loss based on predictions and volatility"""
        try:
            current_price = df["close"].iloc[-1]
            
            # Calculate volatility-based stop loss
            volatility = df["close"].tail(20).std() / df["close"].tail(20).mean() if len(df) > 20 else 0.02
            
            # Base stop loss percentage
            base_stop_loss = 0.05  # 5%
            
            # Adjust based on volatility
            stop_loss_pct = base_stop_loss + (volatility * 0.5)
            stop_loss_pct = min(stop_loss_pct, 0.15)  # Max 15%
            
            # Calculate stop loss price
            stop_loss = current_price * (1 - stop_loss_pct)
            
            return round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return df["close"].iloc[-1] * 0.95  # Default 5% stop loss
    
    def _determine_signal(self, predictions: Dict, confidence: float) -> str:
        """Determine final trading signal"""
        try:
            buy_prob = predictions.get("buy_probability", 0.5)
            sell_prob = predictions.get("sell_probability", 0.5)
            hold_prob = predictions.get("hold_probability", 0.5)
            
            # Apply confidence threshold
            min_confidence = 0.6
            
            if confidence < min_confidence:
                return "HOLD"
            
            # Determine signal based on probabilities
            if buy_prob > sell_prob and buy_prob > hold_prob:
                return "BUY"
            elif sell_prob > buy_prob and sell_prob > hold_prob:
                return "SELL"
            else:
                return "HOLD"
                
        except Exception as e:
            logger.error(f"Error determining signal: {e}")
            return "HOLD"
    
    def _load_or_initialize_model(self):
        """Load existing model or initialize new one"""
        try:
            # Create models directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            
            # Try to load existing model
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded existing AI model")
            else:
                # Initialize new model
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10,
                    min_samples_split=5
                )
                logger.info("Initialized new AI model")
                
        except Exception as e:
            logger.error(f"Error loading/initializing model: {e}")
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    def train_model(self, training_data: List[Dict]):
        """Train the AI model with historical data"""
        try:
            if not training_data:
                logger.warning("No training data provided")
                return
            
            # Prepare training data
            X = []
            y = []
            
            for data_point in training_data:
                features = data_point.get("features", {})
                signal = data_point.get("signal", "HOLD")
                
                if features:
                    X.append(list(features.values()))
                    
                    # Convert signal to numeric
                    if signal == "BUY":
                        y.append(0)
                    elif signal == "HOLD":
                        y.append(1)
                    elif signal == "SELL":
                        y.append(2)
                    else:
                        y.append(1)  # Default to HOLD
            
            if not X or not y:
                logger.warning("No valid training data")
                return
            
            # Convert to numpy arrays
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            logger.info(f"Model trained with {len(X)} samples")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        try:
            if self.model is None:
                return {"status": "No model loaded"}
            
            return {
                "model_type": type(self.model).__name__,
                "n_estimators": getattr(self.model, 'n_estimators', 'Unknown'),
                "max_depth": getattr(self.model, 'max_depth', 'Unknown'),
                "feature_count": len(self.scaler.feature_names_in_) if hasattr(self.scaler, 'feature_names_in_') else 'Unknown',
                "model_path": self.model_path,
                "scaler_path": self.scaler_path
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"status": "Error getting model info"}
