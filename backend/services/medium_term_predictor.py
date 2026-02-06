"""
Medium-Term Price Predictor Service
Specialized ensemble predictor for 1-month (21 trading days) horizon
Combines Gradient Boosting models (XGBoost, LightGBM) with factor-based model
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.gradient_boosting_models import GradientBoostingModels
from services.data_fetcher import fetch_historical_data

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency
_price_prediction_service = None

def _get_price_prediction_service():
    """Lazy import of PricePredictionService"""
    global _price_prediction_service
    if _price_prediction_service is None:
        from services.price_prediction_service import price_prediction_service
        _price_prediction_service = price_prediction_service
    return _price_prediction_service

class MediumTermPricePredictor:
    """Specialized ensemble predictor for 1-month horizon"""
    
    def __init__(self):
        self.gb_models = GradientBoostingModels()
        
    def _get_adaptive_weights(self, symbol: str) -> Dict[str, float]:
        """
        Get adaptive weights for ensemble based on recent performance
        In production, this would track model performance over time
        """
        # Default weights (can be adjusted based on backtesting results)
        return {
            "xgb": 0.35,
            "lgb": 0.35,
            "factor": 0.30  # Factor-based model gets 30%
        }
    
    async def predict_1month(
        self,
        symbol: str,
        historical_data: Optional[pd.DataFrame] = None,
        current_price: Optional[float] = None,
        technical_indicators: Optional[Dict] = None,
        market_factors: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Predict price 1 month ahead using ensemble (Gradient Boosting + Factor Model)
        
        Args:
            symbol: Stock symbol
            historical_data: DataFrame with OHLCV data (should have at least 60 days)
            current_price: Current stock price
            technical_indicators: Technical indicators data
            market_factors: Market factors data
        
        Returns:
            Dictionary with 1-month prediction details
        """
        try:
            # Fetch data if not provided
            if historical_data is None:
                candles = await fetch_historical_data(symbol, "1d", days=90)
                if not candles or len(candles) < 60:
                    logger.warning(f"Insufficient data for 1-month prediction: {symbol}")
                    if current_price:
                        return self._get_fallback_prediction(current_price)
                    return {"error": "Insufficient historical data"}
                
                historical_data = pd.DataFrame(candles)
                if 'time' in historical_data.columns:
                    historical_data['time'] = pd.to_datetime(historical_data['time'], unit='s', errors='coerce')
                    historical_data.set_index('time', inplace=True, drop=False)
            
            # Ensure required columns
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
            
            # 1. Prepare features for gradient boosting
            X, y, feature_names = self.gb_models.prepare_features(historical_data, target_col='close')
            
            if len(X) == 0:
                # Fallback to factor-based only
                return await self._factor_only_prediction(
                    symbol, current_price, technical_indicators, market_factors
                )
            
            # Shift target by 21 days for 1-month prediction
            if len(X) < 21:
                return await self._factor_only_prediction(
                    symbol, current_price, technical_indicators, market_factors
                )
            
            X_shifted = X[:-21]
            y_shifted = y[21:]  # Target is 21 days ahead
            
            # 2. Gradient boosting predictions
            xgb_prediction = None
            lgb_prediction = None
            
            try:
                # Try XGBoost prediction
                if self.gb_models.xgb_model is not None:
                    last_features = X[-1:]
                    xgb_prediction = float(self.gb_models.xgb_model.predict(last_features)[0])
                else:
                    # Try to load saved model
                    import os
                    import joblib
                    xgb_path = os.path.join(self.gb_models.models_dir, 'xgboost_model.pkl')
                    if os.path.exists(xgb_path):
                        try:
                            self.gb_models.xgb_model = joblib.load(xgb_path)
                            scaler_path = os.path.join(self.gb_models.models_dir, 'xgboost_scaler.pkl')
                            if os.path.exists(scaler_path):
                                self.gb_models.scaler = joblib.load(scaler_path)
                            last_features = X[-1:]
                            xgb_prediction = float(self.gb_models.xgb_model.predict(last_features)[0])
                        except Exception as e:
                            logger.debug(f"Could not load XGBoost model: {e}")
            except Exception as e:
                logger.debug(f"XGBoost prediction not available: {e}")
            
            try:
                # Try LightGBM prediction
                if self.gb_models.lgb_model is not None:
                    last_features = X[-1:]
                    lgb_prediction = float(self.gb_models.lgb_model.predict(last_features)[0])
                else:
                    # Try to load saved model
                    import os
                    import joblib
                    lgb_path = os.path.join(self.gb_models.models_dir, 'lightgbm_model.pkl')
                    if os.path.exists(lgb_path):
                        try:
                            self.gb_models.lgb_model = joblib.load(lgb_path)
                            scaler_path = os.path.join(self.gb_models.models_dir, 'lightgbm_scaler.pkl')
                            if os.path.exists(scaler_path):
                                self.gb_models.scaler = joblib.load(scaler_path)
                            last_features = X[-1:]
                            lgb_prediction = float(self.gb_models.lgb_model.predict(last_features)[0])
                        except Exception as e:
                            logger.debug(f"Could not load LightGBM model: {e}")
            except Exception as e:
                logger.debug(f"LightGBM prediction not available: {e}")
            
            # 3. Factor-based prediction
            analysis_data = {
                "technical_indicators": technical_indicators or {},
                "market_factors": market_factors or {}
            }
            
            price_prediction_service = _get_price_prediction_service()
            
            base_factors = price_prediction_service._calculate_base_factors(
                current_price, analysis_data
            )
            
            # Factor-based prediction (synchronous method)
            factor_prediction = price_prediction_service._predict_for_timeframe(
                timeframe="1M",
                days=21,
                current_price=current_price,
                base_factors=base_factors,
                analysis_data=analysis_data
            )
            
            factor_price = factor_prediction.get("predicted_price", current_price)
            
            # 4. Ensemble with adaptive weights
            weights = self._get_adaptive_weights(symbol)
            predictions = []
            model_weights = []
            
            if xgb_prediction is not None:
                predictions.append(xgb_prediction)
                model_weights.append(weights["xgb"])
            
            if lgb_prediction is not None:
                predictions.append(lgb_prediction)
                model_weights.append(weights["lgb"])
            
            # Always include factor-based prediction
            predictions.append(factor_price)
            model_weights.append(weights["factor"])
            
            if len(predictions) == 0:
                return await self._factor_only_prediction(
                    symbol, current_price, technical_indicators, market_factors
                )
            
            # Normalize weights
            total_weight = sum(model_weights)
            model_weights = [w / total_weight for w in model_weights]
            
            # Weighted average
            final_prediction = sum(p * w for p, w in zip(predictions, model_weights))
            
            # Ensure prediction is reasonable (within ±30% of current price for 1 month)
            final_prediction = np.clip(
                final_prediction,
                current_price * 0.70,
                current_price * 1.30
            )
            
            # Calculate confidence based on model agreement
            if len(predictions) >= 2:
                std_dev = np.std(predictions)
                agreement = 1 - (std_dev / current_price)
                confidence = max(60, min(85, agreement * 100 + 10))  # 60-85% for ensemble
            else:
                confidence = factor_prediction.get("confidence", 65)
            
            # Use factor-based price range (already calculated)
            price_range = factor_prediction.get("price_range", {
                "low_68": round(final_prediction * 0.97, 2),
                "high_68": round(final_prediction * 1.03, 2),
                "low_95": round(final_prediction * 0.94, 2),
                "high_95": round(final_prediction * 1.06, 2),
                "volatility": 2.0
            })
            
            # Calculate metrics
            potential_change = final_prediction - current_price
            potential_change_percent = (potential_change / current_price) * 100
            expected_return = potential_change_percent / 21  # Daily return
            
            # Risk level from factor prediction
            risk_level = factor_prediction.get("risk_level", "Medium")
            
            return {
                "timeframe": "1M",
                "days": 21,
                "predicted_price": round(final_prediction, 2),
                "current_price": round(current_price, 2),
                "expected_return": round(expected_return, 2),
                "potential_change": round(potential_change, 2),
                "potential_change_percent": round(potential_change_percent, 2),
                "confidence": round(confidence, 2),
                "price_range": price_range,
                "model_type": "ensemble",
                "model_contributions": {
                    "xgb": round(xgb_prediction, 2) if xgb_prediction else None,
                    "lgb": round(lgb_prediction, 2) if lgb_prediction else None,
                    "factor": round(factor_price, 2)
                },
                "risk_level": risk_level,
                "factors_contributing": factor_prediction.get("factors_contributing", [])
            }
            
        except Exception as e:
            logger.error(f"Error in 1-month prediction for {symbol}: {e}")
            if current_price:
                return await self._factor_only_prediction(
                    symbol, current_price, technical_indicators, market_factors
                )
            return {"error": str(e)}
    
    async def _factor_only_prediction(
        self,
        symbol: str,
        current_price: float,
        technical_indicators: Optional[Dict] = None,
        market_factors: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Fallback to factor-based prediction only"""
        try:
            analysis_data = {
                "technical_indicators": technical_indicators or {},
                "market_factors": market_factors or {}
            }
            
            price_prediction_service = _get_price_prediction_service()
            
            base_factors = price_prediction_service._calculate_base_factors(
                current_price, analysis_data
            )
            
            prediction = price_prediction_service._predict_for_timeframe(
                timeframe="1M",
                days=21,
                current_price=current_price,
                base_factors=base_factors,
                analysis_data=analysis_data
            )
            
            prediction["model_type"] = "factor_only"
            return prediction
            
        except Exception as e:
            logger.error(f"Error in factor-only prediction: {e}")
            return self._get_fallback_prediction(current_price)
    
    def _get_fallback_prediction(self, current_price: float) -> Dict[str, Any]:
        """Get fallback prediction when models unavailable"""
        return {
            "timeframe": "1M",
            "days": 21,
            "predicted_price": round(current_price, 2),
            "current_price": round(current_price, 2),
            "expected_return": 0.0,
            "potential_change": 0.0,
            "potential_change_percent": 0.0,
            "confidence": 40.0,
            "price_range": {
                "low_68": round(current_price * 0.95, 2),
                "high_68": round(current_price * 1.05, 2),
                "low_95": round(current_price * 0.90, 2),
                "high_95": round(current_price * 1.10, 2),
                "volatility": 2.5
            },
            "model_type": "fallback",
            "risk_level": "High"
        }

# Create singleton instance
medium_term_predictor = MediumTermPricePredictor()
