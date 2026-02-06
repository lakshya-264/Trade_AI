"""
Short-Term Price Predictor Service
Specialized predictor for 1-week (5 trading days) horizon using temporal models
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import torch

from services.temporal_models import TemporalModels
from services.data_fetcher import fetch_historical_data

logger = logging.getLogger(__name__)

class ShortTermPricePredictor:
    """Specialized predictor for 1-week horizon using temporal models"""
    
    def __init__(self):
        self.temporal_models = TemporalModels()
        self.sequence_length = 20  # 20 days lookback for short-term
        self.prediction_days = 5   # 1 week = 5 trading days
        
    def _prepare_sequences_5day(self, historical_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for 5-day ahead prediction"""
        try:
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in historical_data.columns for col in required_cols):
                return np.array([]), np.array([])
            
            # Use last 20 days + need 5 days ahead
            if len(historical_data) < self.sequence_length + self.prediction_days:
                return np.array([]), np.array([])
            
            # Select and scale features
            data = historical_data[required_cols].values
            scaled_data = self.temporal_models.scaler.fit_transform(data)
            
            # Create sequences: 20 days input -> 5 days ahead target
            X, y = [], []
            for i in range(self.sequence_length, len(scaled_data) - self.prediction_days + 1):
                X.append(scaled_data[i-self.sequence_length:i])
                # Target is close price 5 days ahead
                y_value = float(scaled_data[i+self.prediction_days-1, 3])  # Close price column
                y.append(y_value)
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing sequences: {e}")
            return np.array([]), np.array([])
    
    def _momentum_based_prediction(
        self, 
        historical_data: pd.DataFrame, 
        current_price: float
    ) -> Dict[str, Any]:
        """Fallback momentum-based prediction when ML models unavailable"""
        try:
            if len(historical_data) < 5:
                return self._get_fallback_prediction(current_price)
            
            # Calculate short-term momentum
            closes = historical_data['close'].values
            recent_returns = []
            
            for i in range(1, min(6, len(closes))):
                ret = (closes[-1] - closes[-i-1]) / closes[-i-1] if i < len(closes) else 0
                recent_returns.append(ret)
            
            avg_momentum = np.mean(recent_returns) if recent_returns else 0
            
            # Project 5 days ahead with momentum decay
            momentum_factor = avg_momentum * 0.7  # Decay factor for short-term
            predicted_price = current_price * (1 + momentum_factor * 5)
            
            # Ensure reasonable bounds (±10% for 1 week)
            predicted_price = np.clip(
                predicted_price, 
                current_price * 0.9, 
                current_price * 1.1
            )
            
            # Calculate volatility for confidence
            volatility = np.std(recent_returns) if len(recent_returns) > 1 else 0.02
            confidence = max(50, min(70, 100 - (volatility * 1000)))  # 50-70% for momentum-based
            
            return {
                "timeframe": "1W",
                "days": 5,
                "predicted_price": round(predicted_price, 2),
                "current_price": round(current_price, 2),
                "expected_return": round(momentum_factor * 5 * 100, 2),
                "potential_change": round(predicted_price - current_price, 2),
                "potential_change_percent": round(((predicted_price - current_price) / current_price) * 100, 2),
                "confidence": round(confidence, 2),
                "price_range": {
                    "low_68": round(predicted_price * 0.97, 2),
                    "high_68": round(predicted_price * 1.03, 2),
                    "low_95": round(predicted_price * 0.94, 2),
                    "high_95": round(predicted_price * 1.06, 2),
                    "volatility": round(volatility * 100, 2)
                },
                "model_type": "momentum_fallback",
                "risk_level": "Medium"
            }
            
        except Exception as e:
            logger.error(f"Error in momentum-based prediction: {e}")
            return self._get_fallback_prediction(current_price)
    
    def _get_fallback_prediction(self, current_price: float) -> Dict[str, Any]:
        """Get fallback prediction when data is insufficient"""
        return {
            "timeframe": "1W",
            "days": 5,
            "predicted_price": round(current_price, 2),
            "current_price": round(current_price, 2),
            "expected_return": 0.0,
            "potential_change": 0.0,
            "potential_change_percent": 0.0,
            "confidence": 30.0,
            "price_range": {
                "low_68": round(current_price * 0.98, 2),
                "high_68": round(current_price * 1.02, 2),
                "low_95": round(current_price * 0.95, 2),
                "high_95": round(current_price * 1.05, 2),
                "volatility": 2.0
            },
            "model_type": "fallback",
            "risk_level": "High"
        }
    
    async def predict_1week(
        self,
        symbol: str,
        historical_data: Optional[pd.DataFrame] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Predict price 1 week ahead using temporal models (LSTM + Transformer)
        
        Args:
            symbol: Stock symbol
            historical_data: DataFrame with OHLCV data (must have at least 25 days)
            current_price: Current stock price
        
        Returns:
            Dictionary with 1-week prediction details
        """
        try:
            # Fetch data if not provided
            if historical_data is None:
                candles = await fetch_historical_data(symbol, "1d", days=60)
                if not candles or len(candles) < 25:
                    logger.warning(f"Insufficient data for 1-week prediction: {symbol}")
                    if current_price:
                        return self._get_fallback_prediction(current_price)
                    return {"error": "Insufficient historical data"}
                
                historical_data = pd.DataFrame(candles)
                if 'time' in historical_data.columns:
                    historical_data['time'] = pd.to_datetime(historical_data['time'], unit='s', errors='coerce')
                    historical_data.set_index('time', inplace=True, drop=False)
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in historical_data.columns:
                    if col == 'volume':
                        historical_data[col] = 0
                    else:
                        historical_data[col] = historical_data.get('close', current_price or 0)
            
            # Get current price if not provided
            if current_price is None:
                current_price = float(historical_data['close'].iloc[-1])
            
            if len(historical_data) < self.sequence_length + self.prediction_days:
                return self._momentum_based_prediction(historical_data, current_price)
            
            # Prepare sequences for 5-day ahead prediction
            sequences, targets = self._prepare_sequences_5day(historical_data)
            
            if len(sequences) == 0:
                return self._momentum_based_prediction(historical_data, current_price)
            
            # Get last sequence for prediction
            last_sequence = sequences[-1:]
            
            # Predict with LSTM (if model available)
            lstm_prediction = None
            try:
                # Try to load model if not already loaded
                import os
                lstm_path = os.path.join(self.temporal_models.models_dir, 'lstm_best_model.pth')
                if os.path.exists(lstm_path) and self.temporal_models.lstm_model is None:
                    # Initialize and load model
                    input_size = sequences.shape[2]
                    self.temporal_models.lstm_model = self.temporal_models.lstm_model or \
                        self.temporal_models.__class__.__new__(self.temporal_models.__class__).__init__()
                    # For now, skip model loading - use momentum fallback
                    pass
                
                if self.temporal_models.lstm_model is not None:
                    self.temporal_models.lstm_model.eval()
                    with torch.no_grad():
                        sequence_tensor = torch.FloatTensor(last_sequence)
                        lstm_output = self.temporal_models.lstm_model(sequence_tensor)
                        lstm_prediction = float(lstm_output.squeeze().item())
                        
                        # Inverse transform to get actual price
                        close_values = historical_data['close'].values[-self.sequence_length:]
                        min_close = close_values.min()
                        max_close = close_values.max()
                        if max_close > min_close:
                            lstm_prediction = lstm_prediction * (max_close - min_close) + min_close
                        else:
                            lstm_prediction = current_price
            except Exception as e:
                logger.debug(f"LSTM prediction not available: {e}")
            
            # Predict with Transformer (if model available)
            transformer_prediction = None
            try:
                if self.temporal_models.transformer_model is not None:
                    self.temporal_models.transformer_model.eval()
                    with torch.no_grad():
                        sequence_tensor = torch.FloatTensor(last_sequence)
                        transformer_output = self.temporal_models.transformer_model(sequence_tensor)
                        transformer_prediction = float(transformer_output.squeeze().item())
                        
                        # Inverse transform
                        close_values = historical_data['close'].values[-self.sequence_length:]
                        min_close = close_values.min()
                        max_close = close_values.max()
                        if max_close > min_close:
                            transformer_prediction = transformer_prediction * (max_close - min_close) + min_close
                        else:
                            transformer_prediction = current_price
            except Exception as e:
                logger.debug(f"Transformer prediction not available: {e}")
            
            # Ensemble predictions
            predictions = []
            weights = []
            
            if lstm_prediction is not None:
                predictions.append(lstm_prediction)
                weights.append(0.6)  # LSTM gets 60% weight
            
            if transformer_prediction is not None:
                predictions.append(transformer_prediction)
                weights.append(0.4)  # Transformer gets 40% weight
            
            if len(predictions) == 0:
                # Fallback: Use momentum-based prediction
                return self._momentum_based_prediction(historical_data, current_price)
            
            # Normalize weights
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            # Weighted average
            predicted_price = sum(p * w for p, w in zip(predictions, weights))
            
            # Ensure prediction is reasonable (within ±15% of current price for 1 week)
            predicted_price = np.clip(
                predicted_price,
                current_price * 0.85,
                current_price * 1.15
            )
            
            # Calculate confidence based on model agreement
            if len(predictions) == 2:
                agreement = 1 - abs(predictions[0] - predictions[1]) / current_price
                confidence = max(55, min(75, agreement * 100))  # 55-75% for temporal models
            else:
                confidence = 60  # Single model prediction
            
            # Calculate volatility for price range
            recent_returns = historical_data['close'].pct_change().dropna().tail(20)
            volatility = recent_returns.std() if len(recent_returns) > 1 else 0.02
            
            # Calculate price range
            std_dev = current_price * volatility * np.sqrt(5 / 21)
            price_range = {
                "low_68": round(predicted_price - (std_dev * 1.0), 2),
                "high_68": round(predicted_price + (std_dev * 1.0), 2),
                "low_95": round(predicted_price - (std_dev * 1.96), 2),
                "high_95": round(predicted_price + (std_dev * 1.96), 2),
                "volatility": round(volatility * 100, 2)
            }
            
            # Calculate metrics
            potential_change = predicted_price - current_price
            potential_change_percent = (potential_change / current_price) * 100
            expected_return = potential_change_percent / 5  # Daily return
            
            # Assess risk
            risk_level = "High" if volatility > 0.03 else "Medium" if volatility > 0.02 else "Low"
            
            return {
                "timeframe": "1W",
                "days": 5,
                "predicted_price": round(predicted_price, 2),
                "current_price": round(current_price, 2),
                "expected_return": round(expected_return, 2),
                "potential_change": round(potential_change, 2),
                "potential_change_percent": round(potential_change_percent, 2),
                "confidence": round(confidence, 2),
                "price_range": price_range,
                "model_type": "temporal_ensemble" if len(predictions) == 2 else "temporal_single",
                "model_contributions": {
                    "lstm": round(lstm_prediction, 2) if lstm_prediction else None,
                    "transformer": round(transformer_prediction, 2) if transformer_prediction else None
                },
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Error in 1-week prediction for {symbol}: {e}")
            if current_price:
                return self._get_fallback_prediction(current_price)
            return {"error": str(e)}

# Create singleton instance
short_term_predictor = ShortTermPricePredictor()
