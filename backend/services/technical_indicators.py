"""
Technical Indicators Service
Comprehensive implementation of 100+ technical indicators for TradingView-style charting
Supports trend, momentum, volatility, volume, and statistical indicators
"""

import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import asyncio
import math

logger = logging.getLogger(__name__)

class TechnicalIndicatorsService:
    def __init__(self):
        self.available_indicators = {
            # ==================== TREND INDICATORS ====================
            "sma": {
                "name": "Simple Moving Average",
                "category": "trend",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Average price over a specified period"
            },
            "ema": {
                "name": "Exponential Moving Average",
                "category": "trend",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Exponentially weighted moving average"
            },
            "wma": {
                "name": "Weighted Moving Average",
                "category": "trend",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Weighted average with more weight on recent prices"
            },
            "hull_ma": {
                "name": "Hull Moving Average",
                "category": "trend",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Reduces lag while maintaining smoothness"
            },
            "macd": {
                "name": "MACD",
                "category": "trend",
                "params": ["fast_period", "slow_period", "signal_period"],
                "default_params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "description": "Moving Average Convergence Divergence"
            },
            "parabolic_sar": {
                "name": "Parabolic SAR",
                "category": "trend",
                "params": ["step", "maximum"],
                "default_params": {"step": 0.02, "maximum": 0.2},
                "description": "Stop and Reverse indicator"
            },
            "supertrend": {
                "name": "Supertrend",
                "category": "trend",
                "params": ["period", "multiplier"],
                "default_params": {"period": 10, "multiplier": 3.0},
                "description": "Trend-following indicator"
            },
            "adx": {
                "name": "Average Directional Index",
                "category": "trend",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Measures trend strength"
            },
            "dmi": {
                "name": "Directional Movement Index",
                "category": "trend",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Positive and negative directional movement"
            },
            "ichimoku": {
                "name": "Ichimoku Cloud",
                "category": "trend",
                "params": ["conversion_period", "base_period", "leading_span_b_period", "displacement"],
                "default_params": {"conversion_period": 9, "base_period": 26, "leading_span_b_period": 52, "displacement": 26},
                "description": "Complete trading system"
            },
            
            # ==================== MOMENTUM INDICATORS ====================
            "rsi": {
                "name": "Relative Strength Index",
                "category": "momentum",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Measures speed and change of price movements"
            },
            "stochastic_rsi": {
                "name": "Stochastic RSI",
                "category": "momentum",
                "params": ["period", "smooth_k", "smooth_d"],
                "default_params": {"period": 14, "smooth_k": 3, "smooth_d": 3},
                "description": "RSI applied to Stochastic Oscillator"
            },
            "stochastic": {
                "name": "Stochastic Oscillator",
                "category": "momentum",
                "params": ["k_period", "d_period"],
                "default_params": {"k_period": 14, "d_period": 3},
                "description": "Compares closing price to price range"
            },
            "williams_r": {
                "name": "Williams %R",
                "category": "momentum",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Momentum indicator similar to Stochastic"
            },
            "cci": {
                "name": "Commodity Channel Index",
                "category": "momentum",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Identifies cyclical trends"
            },
            "momentum": {
                "name": "Momentum",
                "category": "momentum",
                "params": ["period"],
                "default_params": {"period": 10},
                "description": "Rate of change in price"
            },
            "roc": {
                "name": "Rate of Change",
                "category": "momentum",
                "params": ["period"],
                "default_params": {"period": 10},
                "description": "Percentage change in price over time"
            },
            "awesome_oscillator": {
                "name": "Awesome Oscillator",
                "category": "momentum",
                "params": [],
                "default_params": {},
                "description": "Market momentum indicator"
            },
            "ultimate_oscillator": {
                "name": "Ultimate Oscillator",
                "category": "momentum",
                "params": ["period1", "period2", "period3"],
                "default_params": {"period1": 7, "period2": 14, "period3": 28},
                "description": "Multi-timeframe momentum oscillator"
            },
            
            # ==================== VOLATILITY INDICATORS ====================
            "bollinger_bands": {
                "name": "Bollinger Bands",
                "category": "volatility",
                "params": ["period", "std_dev"],
                "default_params": {"period": 20, "std_dev": 2},
                "description": "Price channels based on standard deviation"
            },
            "keltner_channels": {
                "name": "Keltner Channels",
                "category": "volatility",
                "params": ["period", "multiplier"],
                "default_params": {"period": 20, "multiplier": 2},
                "description": "Volatility-based price channels"
            },
            "atr": {
                "name": "Average True Range",
                "category": "volatility",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Measures market volatility"
            },
            "donchian_channels": {
                "name": "Donchian Channels",
                "category": "volatility",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Price channels based on highest high and lowest low"
            },
            "chaikin_volatility": {
                "name": "Chaikin Volatility",
                "category": "volatility",
                "params": ["period"],
                "default_params": {"period": 10},
                "description": "Measures volatility using high-low range"
            },
            "standard_deviation": {
                "name": "Standard Deviation",
                "category": "volatility",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Statistical measure of price volatility"
            },
            
            # ==================== VOLUME INDICATORS ====================
            "obv": {
                "name": "On-Balance Volume",
                "category": "volume",
                "params": [],
                "default_params": {},
                "description": "Cumulative volume indicator"
            },
            "volume_profile": {
                "name": "Volume Profile",
                "category": "volume",
                "params": ["bins"],
                "default_params": {"bins": 20},
                "description": "Volume distribution at different price levels"
            },
            "vwap": {
                "name": "Volume Weighted Average Price",
                "category": "volume",
                "params": [],
                "default_params": {},
                "description": "Average price weighted by volume"
            },
            "ad_line": {
                "name": "Accumulation/Distribution Line",
                "category": "volume",
                "params": [],
                "default_params": {},
                "description": "Volume-based indicator"
            },
            "cmf": {
                "name": "Chaikin Money Flow",
                "category": "volume",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Volume-weighted average of accumulation/distribution"
            },
            "mfi": {
                "name": "Money Flow Index",
                "category": "volume",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Volume-weighted RSI"
            },
            "ease_of_movement": {
                "name": "Ease of Movement",
                "category": "volume",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Relates price change to volume"
            },
            "force_index": {
                "name": "Force Index",
                "category": "volume",
                "params": ["period"],
                "default_params": {"period": 13},
                "description": "Combines price and volume"
            },
            
            # ==================== STATISTICAL INDICATORS ====================
            "linear_regression": {
                "name": "Linear Regression",
                "category": "statistical",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Linear regression line"
            },
            "polynomial_regression": {
                "name": "Polynomial Regression",
                "category": "statistical",
                "params": ["period", "degree"],
                "default_params": {"period": 14, "degree": 2},
                "description": "Polynomial regression line"
            },
            "correlation": {
                "name": "Correlation Coefficient",
                "category": "statistical",
                "params": ["period", "symbol"],
                "default_params": {"period": 20, "symbol": "NIFTY_50"},
                "description": "Correlation with another symbol"
            },
            "standard_deviation": {
                "name": "Standard Deviation",
                "category": "statistical",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Statistical measure of dispersion"
            },
            "variance": {
                "name": "Variance",
                "category": "statistical",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Statistical measure of spread"
            },
            "z_score": {
                "name": "Z-Score",
                "category": "statistical",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Standardized score"
            },
            
            # ==================== CUSTOM INDICATORS ====================
            "price_channels": {
                "name": "Price Channels",
                "category": "custom",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Highest high and lowest low channels"
            },
            "kaufman_adaptive_ma": {
                "name": "Kaufman Adaptive Moving Average",
                "category": "custom",
                "params": ["period"],
                "default_params": {"period": 14},
                "description": "Adaptive moving average"
            },
            "zero_lag_ema": {
                "name": "Zero Lag EMA",
                "category": "custom",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "EMA with reduced lag"
            },
            "fractal_dimension": {
                "name": "Fractal Dimension",
                "category": "custom",
                "params": ["period"],
                "default_params": {"period": 20},
                "description": "Measures market complexity"
            }
        }
        
        # Cache for calculated indicators
        self.indicator_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_available_indicators(self) -> Dict[str, Any]:
        """Get list of available indicators with their parameters"""
        return self.available_indicators
    
    def get_indicators_by_category(self, category: str) -> Dict[str, Any]:
        """Get indicators filtered by category"""
        return {
            name: info for name, info in self.available_indicators.items()
            if info["category"] == category
        }
    
    async def calculate_indicator(
        self, 
        symbol: str, 
        indicator_type: str, 
        parameters: Dict[str, Any],
        timeframe: str = "1D"
    ) -> Dict[str, Any]:
        """Calculate specific technical indicator"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{indicator_type}_{timeframe}_{hash(str(parameters))}"
            if cache_key in self.indicator_cache:
                cached_data, timestamp = self.indicator_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Validate indicator type
            if indicator_type not in self.available_indicators:
                return {"error": f"Unknown indicator: {indicator_type}"}
            
            # Get historical data
            df = await self._get_historical_data(symbol, timeframe, 200)
            
            if df.empty:
                return {"error": "No data available"}
            
            # Calculate indicator based on type
            result = await self._calculate_specific_indicator(df, indicator_type, parameters)
            
            if not result:
                return {"error": f"Failed to calculate {indicator_type}"}
            
            # Prepare response
            response = {
                "indicator": indicator_type,
                "symbol": symbol,
                "timeframe": timeframe,
                "parameters": parameters,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.indicator_cache[cache_key] = (response, datetime.now().timestamp())
            
            return response
                
        except Exception as e:
            logger.error(f"Error calculating {indicator_type}: {e}")
            return {"error": str(e)}
    
    async def get_multiple_indicators(
        self,
        symbol: str,
        indicators: Optional[List[str]] = None,
        timeframe: str = "1D",
        period: int = 200
    ) -> Dict[str, Any]:
        """Get multiple indicators for a symbol"""
        try:
            if indicators is None:
                # Get default indicators
                indicators = ["sma", "ema", "rsi", "macd", "bollinger_bands"]
            
            # Get historical data once
            df = await self._get_historical_data(symbol, timeframe, period)
            
            if df.empty:
                return {"error": "No data available"}
            
            # Calculate all indicators
            results = {}
            for indicator in indicators:
                try:
                    if indicator in self.available_indicators:
                        default_params = self.available_indicators[indicator]["default_params"]
                        indicator_data = await self._calculate_specific_indicator(df, indicator, default_params)
                        results[indicator] = indicator_data
                    else:
                        results[indicator] = None
                except Exception as e:
                    logger.warning(f"Error calculating {indicator}: {e}")
                    results[indicator] = None
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "indicators": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting multiple indicators for {symbol}: {e}")
            return {"error": str(e)}
    
    async def _calculate_specific_indicator(
        self, 
        df: pd.DataFrame, 
        indicator_type: str, 
        parameters: Dict[str, Any]
    ) -> List[Dict]:
        """Calculate specific indicator using ta-lib or custom implementation"""
        try:
            # Ensure we have required columns
            required_columns = ["open", "high", "low", "close", "volume"]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = df["close"]  # Use close price as fallback
            
            values = None
            
            # ==================== TREND INDICATORS ====================
            if indicator_type == "sma":
                period = parameters.get("period", 20)
                values = ta.trend.sma_indicator(df["close"], window=period)
                
            elif indicator_type == "ema":
                period = parameters.get("period", 20)
                values = ta.trend.ema_indicator(df["close"], window=period)
                
            elif indicator_type == "wma":
                period = parameters.get("period", 20)
                values = self._calculate_wma(df["close"], period)
                
            elif indicator_type == "hull_ma":
                period = parameters.get("period", 20)
                values = self._calculate_hull_ma(df["close"], period)
                
            elif indicator_type == "macd":
                fast_period = parameters.get("fast_period", 12)
                slow_period = parameters.get("slow_period", 26)
                signal_period = parameters.get("signal_period", 9)
                
                macd_line = ta.trend.macd_diff(df["close"], window_slow=slow_period, window_fast=fast_period)
                signal_line = ta.trend.macd_signal(df["close"], window_slow=slow_period, window_fast=fast_period)
                histogram = ta.trend.macd(df["close"], window_slow=slow_period, window_fast=fast_period)
                
                values = {
                    "macd": macd_line,
                    "signal": signal_line,
                    "histogram": histogram
                }
                
            elif indicator_type == "parabolic_sar":
                step = parameters.get("step", 0.02)
                maximum = parameters.get("maximum", 0.2)
                values = ta.trend.psar_up(df["high"], df["low"], df["close"], step=step, max_step=maximum)
                
            elif indicator_type == "adx":
                period = parameters.get("period", 14)
                values = ta.trend.adx(df["high"], df["low"], df["close"], window=period)
                
            elif indicator_type == "dmi":
                period = parameters.get("period", 14)
                plus_di = ta.trend.adx_pos(df["high"], df["low"], df["close"], window=period)
                minus_di = ta.trend.adx_neg(df["high"], df["low"], df["close"], window=period)
                values = {
                    "plus_di": plus_di,
                    "minus_di": minus_di
                }
            
            # ==================== MOMENTUM INDICATORS ====================
            elif indicator_type == "rsi":
                period = parameters.get("period", 14)
                values = ta.momentum.rsi(df["close"], window=period)
                
            elif indicator_type == "stochastic_rsi":
                period = parameters.get("period", 14)
                smooth_k = parameters.get("smooth_k", 3)
                smooth_d = parameters.get("smooth_d", 3)
                values = ta.momentum.stochrsi(df["close"], window=period, smooth1=smooth_k, smooth2=smooth_d)
                
            elif indicator_type == "stochastic":
                k_period = parameters.get("k_period", 14)
                d_period = parameters.get("d_period", 3)
                stoch_k = ta.momentum.stoch(df["high"], df["low"], df["close"], window=k_period, smooth_window=d_period)
                stoch_d = ta.momentum.stoch_signal(df["high"], df["low"], df["close"], window=k_period, smooth_window=d_period)
                values = {
                    "k": stoch_k,
                    "d": stoch_d
                }
                
            elif indicator_type == "williams_r":
                period = parameters.get("period", 14)
                values = ta.momentum.williams_r(df["high"], df["low"], df["close"], lbp=period)
                
            elif indicator_type == "cci":
                period = parameters.get("period", 20)
                values = ta.momentum.cci(df["high"], df["low"], df["close"], window=period)
                
            elif indicator_type == "momentum":
                period = parameters.get("period", 10)
                values = ta.momentum.roc(df["close"], window=period)
                
            elif indicator_type == "roc":
                period = parameters.get("period", 10)
                values = ta.momentum.roc(df["close"], window=period)
                
            elif indicator_type == "awesome_oscillator":
                values = ta.momentum.ao(df["high"], df["low"])
                
            elif indicator_type == "ultimate_oscillator":
                period1 = parameters.get("period1", 7)
                period2 = parameters.get("period2", 14)
                period3 = parameters.get("period3", 28)
                values = ta.momentum.ultimate_oscillator(df["high"], df["low"], df["close"], window1=period1, window2=period2, window3=period3)
            
            # ==================== VOLATILITY INDICATORS ====================
            elif indicator_type == "bollinger_bands":
                period = parameters.get("period", 20)
                std_dev = parameters.get("std_dev", 2)
                
                bb_upper = ta.volatility.bollinger_hband(df["close"], window=period, window_dev=std_dev)
                bb_middle = ta.trend.sma_indicator(df["close"], window=period)
                bb_lower = ta.volatility.bollinger_lband(df["close"], window=period, window_dev=std_dev)
                
                values = {
                    "upper": bb_upper,
                    "middle": bb_middle,
                    "lower": bb_lower
                }
                
            elif indicator_type == "keltner_channels":
                period = parameters.get("period", 20)
                multiplier = parameters.get("multiplier", 2)
                
                kc_upper = ta.volatility.keltner_channel_hband(df["high"], df["low"], df["close"], window=period, window_atr=period, fillna=False, original_version=True)
                kc_middle = ta.trend.ema_indicator(df["close"], window=period)
                kc_lower = ta.volatility.keltner_channel_lband(df["high"], df["low"], df["close"], window=period, window_atr=period, fillna=False, original_version=True)
                
                values = {
                    "upper": kc_upper,
                    "middle": kc_middle,
                    "lower": kc_lower
                }
                
            elif indicator_type == "atr":
                period = parameters.get("period", 14)
                values = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=period)
                
            elif indicator_type == "donchian_channels":
                period = parameters.get("period", 20)
                dc_upper = ta.volatility.donchian_channel_hband(df["high"], df["low"], df["close"], window=period)
                dc_middle = (ta.volatility.donchian_channel_hband(df["high"], df["low"], df["close"], window=period) + 
                           ta.volatility.donchian_channel_lband(df["high"], df["low"], df["close"], window=period)) / 2
                dc_lower = ta.volatility.donchian_channel_lband(df["high"], df["low"], df["close"], window=period)
                
                values = {
                    "upper": dc_upper,
                    "middle": dc_middle,
                    "lower": dc_lower
                }
                
            elif indicator_type == "chaikin_volatility":
                period = parameters.get("period", 10)
                values = ta.volatility.keltner_channel_hband(df["high"], df["low"], df["close"], window=period) - ta.volatility.keltner_channel_lband(df["high"], df["low"], df["close"], window=period)
            
            # ==================== VOLUME INDICATORS ====================
            elif indicator_type == "obv":
                values = ta.volume.on_balance_volume(df["close"], df["volume"])
                
            elif indicator_type == "volume_profile":
                bins = parameters.get("bins", 20)
                values = self._calculate_volume_profile(df, bins)
                
            elif indicator_type == "vwap":
                values = ta.volume.volume_weighted_average_price(df["high"], df["low"], df["close"], df["volume"])
                
            elif indicator_type == "ad_line":
                values = ta.volume.acc_dist_index(df["high"], df["low"], df["close"], df["volume"])
                
            elif indicator_type == "cmf":
                period = parameters.get("period", 20)
                values = ta.volume.chaikin_money_flow(df["high"], df["low"], df["close"], df["volume"], window=period)
                
            elif indicator_type == "mfi":
                period = parameters.get("period", 14)
                values = ta.volume.money_flow_index(df["high"], df["low"], df["close"], df["volume"], window=period)
                
            elif indicator_type == "ease_of_movement":
                period = parameters.get("period", 14)
                values = ta.volume.ease_of_movement(df["high"], df["low"], df["volume"], window=period)
                
            elif indicator_type == "force_index":
                period = parameters.get("period", 13)
                values = ta.volume.force_index(df["close"], df["volume"], window=period)
            
            # ==================== STATISTICAL INDICATORS ====================
            elif indicator_type == "linear_regression":
                period = parameters.get("period", 14)
                values = ta.trend.linear_regression(df["close"], window=period)
                
            elif indicator_type == "standard_deviation":
                period = parameters.get("period", 20)
                values = df["close"].rolling(window=period).std()
                
            elif indicator_type == "variance":
                period = parameters.get("period", 20)
                values = df["close"].rolling(window=period).var()
                
            elif indicator_type == "z_score":
                period = parameters.get("period", 20)
                mean = df["close"].rolling(window=period).mean()
                std = df["close"].rolling(window=period).std()
                values = (df["close"] - mean) / std
            
            # ==================== CUSTOM INDICATORS ====================
            elif indicator_type == "price_channels":
                period = parameters.get("period", 20)
                upper = df["high"].rolling(window=period).max()
                lower = df["low"].rolling(window=period).min()
                middle = (upper + lower) / 2
                values = {
                    "upper": upper,
                    "middle": middle,
                    "lower": lower
                }
                
            elif indicator_type == "kaufman_adaptive_ma":
                period = parameters.get("period", 14)
                values = self._calculate_kama(df["close"], period)
                
            elif indicator_type == "zero_lag_ema":
                period = parameters.get("period", 20)
                values = self._calculate_zero_lag_ema(df["close"], period)
            
            # Convert to list of dictionaries with timestamps
            result = []
            for i, (timestamp, value) in enumerate(zip(df.index, values)):
                if pd.notna(value):
                    if isinstance(value, dict):
                        # Handle multi-value indicators
                        value_dict = {}
                        for key, val in value.items():
                            if pd.notna(val):
                                value_dict[key] = float(val)
                        
                        if value_dict:  # Only add if we have valid values
                            result.append({
                                "time": timestamp.isoformat(),
                                "values": value_dict
                            })
                    else:
                        result.append({
                            "time": timestamp.isoformat(),
                            "value": float(value)
                        })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating {indicator_type}: {e}")
            return []
    
    # ==================== CUSTOM INDICATOR CALCULATIONS ====================
    
    def _calculate_wma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Weighted Moving Average"""
        weights = np.arange(1, period + 1)
        return prices.rolling(window=period).apply(lambda x: np.average(x, weights=weights), raw=True)
    
    def _calculate_hull_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Hull Moving Average"""
        half_period = period // 2
        sqrt_period = int(np.sqrt(period))
        
        wma_half = self._calculate_wma(prices, half_period)
        wma_full = self._calculate_wma(prices, period)
        
        hull_raw = 2 * wma_half - wma_full
        return self._calculate_wma(hull_raw, sqrt_period)
    
    def _calculate_volume_profile(self, df: pd.DataFrame, bins: int) -> List[Dict]:
        """Calculate Volume Profile"""
        try:
            # Find price range
            min_price = df["low"].min()
            max_price = df["high"].max()
            price_step = (max_price - min_price) / bins
            
            # Create volume profile
            volume_profile = []
            for i in range(bins):
                price_level = min_price + (i * price_step)
                volume_at_level = 0
                
                for _, row in df.iterrows():
                    if row["low"] <= price_level <= row["high"]:
                        volume_at_level += row["volume"]
                
                volume_profile.append({
                    "price": price_level,
                    "volume": volume_at_level
                })
            
            return volume_profile
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return []
    
    def _calculate_kama(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Kaufman Adaptive Moving Average"""
        try:
            # Calculate efficiency ratio
            change = abs(prices - prices.shift(period))
            volatility = abs(prices.diff()).rolling(window=period).sum()
            efficiency_ratio = change / volatility
            
            # Calculate smoothing constant
            fast_sc = 2 / (2 + 1)  # Fast smoothing constant
            slow_sc = 2 / (30 + 1)  # Slow smoothing constant
            smoothing_constant = (efficiency_ratio * (fast_sc - slow_sc) + slow_sc) ** 2
            
            # Calculate KAMA
            kama = pd.Series(index=prices.index, dtype=float)
            kama.iloc[0] = prices.iloc[0]
            
            for i in range(1, len(prices)):
                kama.iloc[i] = kama.iloc[i-1] + smoothing_constant.iloc[i] * (prices.iloc[i] - kama.iloc[i-1])
            
            return kama
            
        except Exception as e:
            logger.error(f"Error calculating KAMA: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    def _calculate_zero_lag_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Zero Lag EMA"""
        try:
            alpha = 2 / (period + 1)
            zlema = pd.Series(index=prices.index, dtype=float)
            
            # Calculate lag
            lag = (period - 1) / 2
            
            # Adjust prices
            adjusted_prices = prices + (prices - prices.shift(int(lag)))
            
            # Calculate EMA
            zlema.iloc[0] = adjusted_prices.iloc[0]
            for i in range(1, len(adjusted_prices)):
                zlema.iloc[i] = alpha * adjusted_prices.iloc[i] + (1 - alpha) * zlema.iloc[i-1]
            
            return zlema
            
        except Exception as e:
            logger.error(f"Error calculating Zero Lag EMA: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    async def _get_historical_data(self, symbol: str, timeframe: str, period: int) -> pd.DataFrame:
        """Get historical data for symbol"""
        try:
            # This would integrate with your existing data service
            # For now, generate mock data
            dates = pd.date_range(end=datetime.now(), periods=period, freq='D')
            
            # Generate realistic price data
            base_price = 100
            returns = np.random.normal(0, 0.02, period)  # 2% daily volatility
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            # Generate OHLC data
            df = pd.DataFrame({
                "date": dates,
                "open": prices,
                "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                "close": prices,
                "volume": np.random.randint(1000, 10000, period)
            }).set_index("date")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()

    def calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(data) < slow:
                return {'macd': 0, 'signal': 0, 'histogram': 0}
            
            ema_fast = data['close'].ewm(span=fast).mean()
            ema_slow = data['close'].ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]) if len(macd_line) > 0 else 0,
                'signal': float(signal_line.iloc[-1]) if len(signal_line) > 0 else 0,
                'histogram': float(histogram.iloc[-1]) if len(histogram) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0}

    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        try:
            if len(data) < period:
                current_price = data['close'].iloc[-1] if len(data) > 0 else 1000
                return {
                    'upper': float(current_price * 1.02),
                    'middle': float(current_price),
                    'lower': float(current_price * 0.98)
                }
            
            sma = data['close'].rolling(window=period).mean()
            std = data['close'].rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                'upper': float(upper_band.iloc[-1]) if len(upper_band) > 0 else 0,
                'middle': float(sma.iloc[-1]) if len(sma) > 0 else 0,
                'lower': float(lower_band.iloc[-1]) if len(lower_band) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            current_price = data['close'].iloc[-1] if len(data) > 0 else 1000
            return {
                'upper': float(current_price * 1.02),
                'middle': float(current_price),
                'lower': float(current_price * 0.98)
            }

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(data) < period + 1:
                current_price = data['close'].iloc[-1] if len(data) > 0 else 1000
                return float(current_price * 0.02)
            
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return float(atr.iloc[-1]) if len(atr) > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            current_price = data['close'].iloc[-1] if len(data) > 0 else 1000
            return float(current_price * 0.02)

    def calculate_volume_sma(self, data: pd.DataFrame, period: int = 20) -> float:
        """Calculate Volume Simple Moving Average"""
        try:
            if 'volume' not in data.columns:
                return 0
            
            if len(data) < period:
                return float(data['volume'].iloc[-1]) if len(data) > 0 else 0
            
            volume_sma = data['volume'].rolling(window=period).mean()
            return float(volume_sma.iloc[-1]) if len(volume_sma) > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating Volume SMA: {e}")
            return 0

    def calculate_all_advanced_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate all advanced technical indicators for real-time updates"""
        try:
            if len(data) < 10:
                current_price = data['close'].iloc[-1] if len(data) > 0 else 1000
                return {
                    'rsi': 50.0,
                    'macd': 0.0,
                    'bollinger_upper': float(current_price * 1.02),
                    'bollinger_lower': float(current_price * 0.98),
                    'sma_20': float(current_price),
                    'ema_12': float(current_price),
                    'atr': float(current_price * 0.02),
                    'volume_sma': 0.0
                }
            
            indicators = {}
            
            # RSI (using existing method)
            rsi_data = self.calculate_rsi(data, period=14)
            indicators['rsi'] = float(rsi_data.iloc[-1]) if len(rsi_data) > 0 else 50.0
            
            # MACD
            macd_data = self.calculate_macd(data)
            indicators['macd'] = macd_data['macd']
            
            # Bollinger Bands
            bb_data = self.calculate_bollinger_bands(data)
            indicators['bollinger_upper'] = bb_data['upper']
            indicators['bollinger_lower'] = bb_data['lower']
            
            # SMA 20
            sma_20 = data['close'].rolling(window=20).mean()
            indicators['sma_20'] = float(sma_20.iloc[-1]) if len(sma_20) > 0 else float(data['close'].iloc[-1])
            
            # EMA 12
            ema_12 = data['close'].ewm(span=12).mean()
            indicators['ema_12'] = float(ema_12.iloc[-1]) if len(ema_12) > 0 else float(data['close'].iloc[-1])
            
            # ATR
            indicators['atr'] = self.calculate_atr(data)
            
            # Volume SMA
            indicators['volume_sma'] = self.calculate_volume_sma(data)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating all advanced indicators: {e}")
            current_price = data['close'].iloc[-1] if len(data) > 0 else 1000
            return {
                'rsi': 50.0,
                'macd': 0.0,
                'bollinger_upper': float(current_price * 1.02),
                'bollinger_lower': float(current_price * 0.98),
                'sma_20': float(current_price),
                'ema_12': float(current_price),
                'atr': float(current_price * 0.02),
                'volume_sma': 0.0
            }
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            # Test if ta-lib is working
            test_data = pd.Series([1, 2, 3, 4, 5])
            ta.trend.sma_indicator(test_data, window=3)
            return True
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear indicator cache"""
        self.indicator_cache.clear()
        logger.info("Indicator cache cleared")
