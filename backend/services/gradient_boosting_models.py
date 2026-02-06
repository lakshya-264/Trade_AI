"""
Gradient Boosting Models Service
XGBoost and LightGBM models for technical indicators and features
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, classification_report
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class GradientBoostingModels:
    """Gradient Boosting models for technical analysis and feature prediction"""
    
    def __init__(self):
        self.xgb_model = None
        self.lgb_model = None
        self.rf_model = None
        self.gb_model = None
        
        # Feature scaler
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Models directory
        self.models_dir = "models/gradient_boosting"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Model parameters
        self.xgb_params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 1000,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.lgb_params = {
            'objective': 'regression',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 1000,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1,
            'verbose': -1
        }
        
        self.rf_params = {
            'n_estimators': 1000,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.gb_params = {
            'n_estimators': 1000,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'random_state': 42
        }
    
    def prepare_features(self, df: pd.DataFrame, target_col: str = 'close') -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare features for gradient boosting models"""
        try:
            # Technical indicators
            features_df = self._calculate_technical_indicators(df)
            
            # Price-based features
            features_df = self._add_price_features(features_df)
            
            # Volume features
            features_df = self._add_volume_features(features_df)
            
            # Volatility features
            features_df = self._add_volatility_features(features_df)
            
            # Momentum features
            features_df = self._add_momentum_features(features_df)
            
            # Market microstructure features
            features_df = self._add_microstructure_features(features_df)
            
            # Time-based features
            features_df = self._add_time_features(features_df)
            
            # Remove rows with NaN values
            features_df = features_df.dropna()
            
            if len(features_df) == 0:
                return np.array([]), np.array([]), []
            
            # Separate features and target
            feature_cols = [col for col in features_df.columns if col != target_col]
            X = features_df[feature_cols].values
            y = features_df[target_col].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            return X_scaled, y, feature_cols
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.array([]), np.array([]), []
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        try:
            features_df = df.copy()
            
            # Moving averages
            for window in [5, 10, 20, 50, 100]:
                features_df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
                features_df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
            
            # RSI
            features_df['rsi_14'] = self._calculate_rsi(df['close'], 14)
            features_df['rsi_21'] = self._calculate_rsi(df['close'], 21)
            
            # MACD
            macd_line, signal_line, histogram = self._calculate_macd(df['close'])
            features_df['macd'] = macd_line
            features_df['macd_signal'] = signal_line
            features_df['macd_histogram'] = histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df['close'])
            features_df['bb_upper'] = bb_upper
            features_df['bb_middle'] = bb_middle
            features_df['bb_lower'] = bb_lower
            features_df['bb_width'] = (bb_upper - bb_lower) / bb_middle
            features_df['bb_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
            
            # Stochastic Oscillator
            stoch_k, stoch_d = self._calculate_stochastic(df)
            features_df['stoch_k'] = stoch_k
            features_df['stoch_d'] = stoch_d
            
            # Williams %R
            features_df['williams_r'] = self._calculate_williams_r(df)
            
            # ATR
            features_df['atr'] = self._calculate_atr(df)
            
            # ADX
            features_df['adx'] = self._calculate_adx(df)
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        try:
            # Price changes
            for period in [1, 5, 10, 20]:
                df[f'price_change_{period}'] = df['close'].pct_change(period)
                df[f'price_change_abs_{period}'] = df['close'].diff(period)
            
            # Price ratios
            df['high_low_ratio'] = df['high'] / df['low']
            df['close_open_ratio'] = df['close'] / df['open']
            
            # Price position within day range
            df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
            
            # Gap features
            df['gap'] = df['open'] - df['close'].shift(1)
            df['gap_percent'] = df['gap'] / df['close'].shift(1)
            
            return df
        except Exception as e:
            logger.error(f"Error adding price features: {e}")
            return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""
        try:
            if 'volume' not in df.columns:
                return df
            
            # Volume moving averages
            for window in [5, 10, 20, 50]:
                df[f'volume_sma_{window}'] = df['volume'].rolling(window=window).mean()
            
            # Volume ratios
            df['volume_ratio_5'] = df['volume'] / df['volume_sma_5']
            df['volume_ratio_20'] = df['volume'] / df['volume_sma_20']
            
            # Volume-price trend
            df['vpt'] = (df['volume'] * df['close'].pct_change()).cumsum()
            
            # On-Balance Volume
            df['obv'] = self._calculate_obv(df)
            
            # Volume-weighted average price
            df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
            
            return df
        except Exception as e:
            logger.error(f"Error adding volume features: {e}")
            return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility features"""
        try:
            # Rolling volatility
            for window in [5, 10, 20, 50]:
                df[f'volatility_{window}'] = df['close'].rolling(window=window).std()
                df[f'volatility_pct_{window}'] = df['close'].pct_change().rolling(window=window).std()
            
            # Parkinson volatility
            df['parkinson_vol'] = np.sqrt(
                1 / (4 * np.log(2)) * np.log(df['high'] / df['low']) ** 2
            )
            
            # Garman-Klass volatility
            df['gk_vol'] = np.sqrt(
                0.5 * np.log(df['high'] / df['low']) ** 2 - 
                (2 * np.log(2) - 1) * np.log(df['close'] / df['open']) ** 2
            )
            
            return df
        except Exception as e:
            logger.error(f"Error adding volatility features: {e}")
            return df
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum features"""
        try:
            # Rate of change
            for period in [5, 10, 20]:
                df[f'roc_{period}'] = df['close'].pct_change(period)
            
            # Momentum
            for period in [5, 10, 20]:
                df[f'momentum_{period}'] = df['close'] - df['close'].shift(period)
            
            # Commodity Channel Index
            df['cci'] = self._calculate_cci(df)
            
            # Money Flow Index
            df['mfi'] = self._calculate_mfi(df)
            
            return df
        except Exception as e:
            logger.error(f"Error adding momentum features: {e}")
            return df
    
    def _add_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market microstructure features"""
        try:
            # Bid-ask spread proxy
            df['spread_proxy'] = (df['high'] - df['low']) / df['close']
            
            # Price impact
            df['price_impact'] = df['close'].pct_change() / df['volume'].pct_change()
            
            # Order flow imbalance proxy
            df['order_flow_proxy'] = (df['close'] - df['open']) / (df['high'] - df['low'])
            
            return df
        except Exception as e:
            logger.error(f"Error adding microstructure features: {e}")
            return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        try:
            if df.index.dtype == 'datetime64[ns]':
                df['hour'] = df.index.hour
                df['day_of_week'] = df.index.dayofweek
                df['day_of_month'] = df.index.day
                df['month'] = df.index.month
                df['quarter'] = df.index.quarter
                
                # Cyclical encoding
                df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
                df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
                df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
                df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            return df
        except Exception as e:
            logger.error(f"Error adding time features: {e}")
            return df
    
    def train_xgboost_model(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """Train XGBoost model"""
        try:
            # Prepare features
            X, y, feature_names = self.prepare_features(df, target_col)
            if len(X) == 0:
                return {"error": "No features available for training"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.xgb_model = xgb.XGBRegressor(**self.xgb_params)
            
            # Try new API first (XGBoost 2.0+), fallback to old API
            try:
                # New API with callbacks
                from xgboost import callback
                callbacks = [callback.EarlyStopping(rounds=50, save_best=True)]
                self.xgb_model.fit(
                    X_train, y_train,
                    eval_set=[(X_test, y_test)],
                    callbacks=callbacks,
                    verbose=False
                )
            except (TypeError, AttributeError, ImportError):
                # Fallback to old API or without early stopping
                try:
                    self.xgb_model.fit(
                        X_train, y_train,
                        eval_set=[(X_test, y_test)],
                        early_stopping_rounds=50,
                        verbose=False
                    )
                except TypeError:
                    # If early_stopping_rounds doesn't work, train without it
                    self.xgb_model.fit(X_train, y_train, verbose=False)
            
            # Make predictions
            y_pred = self.xgb_model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Feature importance
            feature_importance = dict(zip(feature_names, self.xgb_model.feature_importances_))
            
            # Save model
            joblib.dump(self.xgb_model, os.path.join(self.models_dir, 'xgboost_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'xgboost_scaler.pkl'))
            
            return {
                "status": "success",
                "mse": mse,
                "mae": mae,
                "rmse": rmse,
                "feature_importance": feature_importance,
                "n_features": len(feature_names)
            }
            
        except Exception as e:
            logger.error(f"Error training XGBoost model: {e}")
            return {"error": str(e)}
    
    def train_lightgbm_model(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """Train LightGBM model"""
        try:
            # Prepare features
            X, y, feature_names = self.prepare_features(df, target_col)
            if len(X) == 0:
                return {"error": "No features available for training"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.lgb_model = lgb.LGBMRegressor(**self.lgb_params)
            self.lgb_model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
            )
            
            # Make predictions
            y_pred = self.lgb_model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Feature importance
            feature_importance = dict(zip(feature_names, self.lgb_model.feature_importances_))
            
            # Save model
            joblib.dump(self.lgb_model, os.path.join(self.models_dir, 'lightgbm_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'lightgbm_scaler.pkl'))
            
            return {
                "status": "success",
                "mse": mse,
                "mae": mae,
                "rmse": rmse,
                "feature_importance": feature_importance,
                "n_features": len(feature_names)
            }
            
        except Exception as e:
            logger.error(f"Error training LightGBM model: {e}")
            return {"error": str(e)}
    
    def train_random_forest_model(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """Train Random Forest model"""
        try:
            # Prepare features
            X, y, feature_names = self.prepare_features(df, target_col)
            if len(X) == 0:
                return {"error": "No features available for training"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.rf_model = RandomForestRegressor(**self.rf_params)
            self.rf_model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = self.rf_model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Feature importance
            feature_importance = dict(zip(feature_names, self.rf_model.feature_importances_))
            
            # Save model
            joblib.dump(self.rf_model, os.path.join(self.models_dir, 'random_forest_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'random_forest_scaler.pkl'))
            
            return {
                "status": "success",
                "mse": mse,
                "mae": mae,
                "rmse": rmse,
                "feature_importance": feature_importance,
                "n_features": len(feature_names)
            }
            
        except Exception as e:
            logger.error(f"Error training Random Forest model: {e}")
            return {"error": str(e)}
    
    def train_gradient_boosting_model(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """Train Gradient Boosting model"""
        try:
            # Prepare features
            X, y, feature_names = self.prepare_features(df, target_col)
            if len(X) == 0:
                return {"error": "No features available for training"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.gb_model = GradientBoostingRegressor(**self.gb_params)
            self.gb_model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = self.gb_model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Feature importance
            feature_importance = dict(zip(feature_names, self.gb_model.feature_importances_))
            
            # Save model
            joblib.dump(self.gb_model, os.path.join(self.models_dir, 'gradient_boosting_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.models_dir, 'gradient_boosting_scaler.pkl'))
            
            return {
                "status": "success",
                "mse": mse,
                "mae": mae,
                "rmse": rmse,
                "feature_importance": feature_importance,
                "n_features": len(feature_names)
            }
            
        except Exception as e:
            logger.error(f"Error training Gradient Boosting model: {e}")
            return {"error": str(e)}
    
    def train_all_models(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """Train all gradient boosting models"""
        try:
            results = {}
            
            # Train XGBoost
            logger.info("Training XGBoost model...")
            results['xgboost'] = self.train_xgboost_model(df, target_col)
            
            # Train LightGBM
            logger.info("Training LightGBM model...")
            results['lightgbm'] = self.train_lightgbm_model(df, target_col)
            
            # Train Random Forest
            logger.info("Training Random Forest model...")
            results['random_forest'] = self.train_random_forest_model(df, target_col)
            
            # Train Gradient Boosting
            logger.info("Training Gradient Boosting model...")
            results['gradient_boosting'] = self.train_gradient_boosting_model(df, target_col)
            
            return results
            
        except Exception as e:
            logger.error(f"Error training all models: {e}")
            return {"error": str(e)}
    
    def predict_ensemble(self, df: pd.DataFrame, target_col: str = 'close') -> Dict:
        """Make ensemble predictions using all models"""
        try:
            # Prepare features
            X, _, feature_names = self.prepare_features(df, target_col)
            if len(X) == 0:
                return {"error": "No features available for prediction"}
            
            predictions = {}
            
            # XGBoost prediction
            if self.xgb_model:
                xgb_pred = self.xgb_model.predict(X)
                predictions['xgboost'] = xgb_pred.tolist()
            
            # LightGBM prediction
            if self.lgb_model:
                lgb_pred = self.lgb_model.predict(X)
                predictions['lightgbm'] = lgb_pred.tolist()
            
            # Random Forest prediction
            if self.rf_model:
                rf_pred = self.rf_model.predict(X)
                predictions['random_forest'] = rf_pred.tolist()
            
            # Gradient Boosting prediction
            if self.gb_model:
                gb_pred = self.gb_model.predict(X)
                predictions['gradient_boosting'] = gb_pred.tolist()
            
            if not predictions:
                return {"error": "No trained models available"}
            
            # Ensemble prediction (equal weights)
            ensemble_pred = np.mean(list(predictions.values()), axis=0)
            predictions['ensemble'] = ensemble_pred.tolist()
            
            return {
                "predictions": predictions,
                "n_models": len(predictions) - 1,  # Exclude ensemble
                "feature_names": feature_names
            }
            
        except Exception as e:
            logger.error(f"Error making ensemble predictions: {e}")
            return {"error": str(e)}
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            # Load XGBoost
            xgb_path = os.path.join(self.models_dir, 'xgboost_model.pkl')
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                logger.info("XGBoost model loaded")
            
            # Load LightGBM
            lgb_path = os.path.join(self.models_dir, 'lightgbm_model.pkl')
            if os.path.exists(lgb_path):
                self.lgb_model = joblib.load(lgb_path)
                logger.info("LightGBM model loaded")
            
            # Load Random Forest
            rf_path = os.path.join(self.models_dir, 'random_forest_model.pkl')
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
                logger.info("Random Forest model loaded")
            
            # Load Gradient Boosting
            gb_path = os.path.join(self.models_dir, 'gradient_boosting_model.pkl')
            if os.path.exists(gb_path):
                self.gb_model = joblib.load(gb_path)
                logger.info("Gradient Boosting model loaded")
            
            # Load scaler
            scaler_path = os.path.join(self.models_dir, 'xgboost_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("Scaler loaded")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    # Technical indicator calculation methods
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series(index=prices.index, dtype=float)
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            return macd_line, signal_line, histogram
        except:
            return pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float)
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            return upper, sma, lower
        except:
            return pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float), pd.Series(index=prices.index, dtype=float)
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_window: int = 14, d_window: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        try:
            low_min = df['low'].rolling(window=k_window).min()
            high_max = df['high'].rolling(window=k_window).max()
            k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
            d_percent = k_percent.rolling(window=d_window).mean()
            return k_percent, d_percent
        except:
            return pd.Series(index=df.index, dtype=float), pd.Series(index=df.index, dtype=float)
    
    def _calculate_williams_r(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        try:
            high_max = df['high'].rolling(window=window).max()
            low_min = df['low'].rolling(window=window).min()
            williams_r = -100 * ((high_max - df['close']) / (high_max - low_min))
            return williams_r
        except:
            return pd.Series(index=df.index, dtype=float)
    
    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=window).mean()
            return atr
        except:
            return pd.Series(index=df.index, dtype=float)
    
    def _calculate_adx(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate ADX"""
        try:
            high_diff = df['high'].diff()
            low_diff = df['low'].diff()
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
            
            plus_dm = pd.Series(plus_dm, index=df.index).rolling(window=window).mean()
            minus_dm = pd.Series(minus_dm, index=df.index).rolling(window=window).mean()
            
            atr = self._calculate_atr(df, window)
            plus_di = 100 * (plus_dm / atr)
            minus_di = 100 * (minus_dm / atr)
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=window).mean()
            return adx
        except:
            return pd.Series(index=df.index, dtype=float)
    
    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        try:
            obv = np.where(df['close'] > df['close'].shift(1), df['volume'],
                          np.where(df['close'] < df['close'].shift(1), -df['volume'], 0))
            return pd.Series(obv, index=df.index).cumsum()
        except:
            return pd.Series(index=df.index, dtype=float)
    
    def _calculate_cci(self, df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        try:
            tp = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = tp.rolling(window=window).mean()
            mad = tp.rolling(window=window).apply(lambda x: np.mean(np.abs(x - x.mean())))
            cci = (tp - sma_tp) / (0.015 * mad)
            return cci
        except:
            return pd.Series(index=df.index, dtype=float)
    
    def _calculate_mfi(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Money Flow Index"""
        try:
            tp = (df['high'] + df['low'] + df['close']) / 3
            rmf = tp * df['volume']
            
            positive_flow = np.where(tp > tp.shift(1), rmf, 0)
            negative_flow = np.where(tp < tp.shift(1), rmf, 0)
            
            positive_flow = pd.Series(positive_flow, index=df.index).rolling(window=window).sum()
            negative_flow = pd.Series(negative_flow, index=df.index).rolling(window=window).sum()
            
            mfi = 100 - (100 / (1 + positive_flow / negative_flow))
            return mfi
        except:
            return pd.Series(index=df.index, dtype=float)
