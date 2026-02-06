"""
Enhanced Chart Service for Professional Trading Platform
Provides advanced charting data, technical indicators, and pattern recognition
"""

import pandas as pd
import numpy as np
import ta
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json

logger = logging.getLogger(__name__)

class EnhancedChartService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def get_candlestick_data(self, symbol: str, timeframe: str = "1D", period: int = 100) -> Dict:
        """Get candlestick data with technical indicators"""
        try:
            cache_key = f"candlestick_{symbol}_{timeframe}_{period}"
            
            # Check cache first
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Generate or fetch data
            data = await self._generate_candlestick_data(symbol, timeframe, period)
            
            # Add technical indicators
            data_with_indicators = await self._add_technical_indicators(data)
            
            # Cache the result
            self.cache[cache_key] = (data_with_indicators, datetime.now().timestamp())
            
            return data_with_indicators
            
        except Exception as e:
            logger.error(f"Error getting candlestick data for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_technical_indicators(self, symbol: str, indicators: List[str] = None) -> Dict:
        """Get comprehensive technical indicators"""
        try:
            if indicators is None:
                indicators = [
                    "sma_20", "sma_50", "sma_200",
                    "ema_12", "ema_26", "ema_50",
                    "rsi", "macd", "bollinger_bands",
                    "stochastic", "williams_r", "atr",
                    "adx", "cci", "roc", "obv"
                ]
            
            # Get base data
            data = await self.get_candlestick_data(symbol, "1D", 200)
            if "error" in data:
                return data
            
            df = pd.DataFrame(data["candlesticks"])
            indicators_data = {}
            
            for indicator in indicators:
                try:
                    indicator_data = await self._calculate_indicator(df, indicator)
                    indicators_data[indicator] = indicator_data
                except Exception as e:
                    logger.warning(f"Error calculating {indicator}: {e}")
                    indicators_data[indicator] = None
            
            return {
                "symbol": symbol,
                "indicators": indicators_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_volume_profile(self, symbol: str, timeframe: str = "1D", period: int = 30) -> Dict:
        """Get volume profile analysis"""
        try:
            data = await self.get_candlestick_data(symbol, timeframe, period)
            if "error" in data:
                return data
            
            df = pd.DataFrame(data["candlesticks"])
            
            # Calculate volume profile
            volume_profile = self._calculate_volume_profile(df)
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "volume_profile": volume_profile,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting volume profile for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_support_resistance(self, symbol: str, lookback: int = 50) -> Dict:
        """Calculate support and resistance levels"""
        try:
            data = await self.get_candlestick_data(symbol, "1D", lookback)
            if "error" in data:
                return data
            
            df = pd.DataFrame(data["candlesticks"])
            
            # Calculate support and resistance
            levels = self._calculate_support_resistance(df)
            
            return {
                "symbol": symbol,
                "support_levels": levels["support"],
                "resistance_levels": levels["resistance"],
                "current_price": df["close"].iloc[-1],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting support/resistance for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_pattern_recognition(self, symbol: str, patterns: List[str] = None) -> Dict:
        """Detect chart patterns"""
        try:
            if patterns is None:
                patterns = [
                    "head_and_shoulders", "double_top", "double_bottom",
                    "triangle_ascending", "triangle_descending", "triangle_symmetrical",
                    "flag_bullish", "flag_bearish", "pennant",
                    "cup_and_handle", "wedge_rising", "wedge_falling"
                ]
            
            data = await self.get_candlestick_data(symbol, "1D", 100)
            if "error" in data:
                return data
            
            df = pd.DataFrame(data["candlesticks"])
            
            detected_patterns = {}
            for pattern in patterns:
                try:
                    pattern_data = await self._detect_pattern(df, pattern)
                    if pattern_data:
                        detected_patterns[pattern] = pattern_data
                except Exception as e:
                    logger.warning(f"Error detecting {pattern}: {e}")
            
            return {
                "symbol": symbol,
                "patterns": detected_patterns,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting pattern recognition for {symbol}: {e}")
            return {"error": str(e)}
    
    async def _generate_candlestick_data(self, symbol: str, timeframe: str, period: int) -> Dict:
        """Generate or fetch candlestick data from real market data"""
        try:
            # Import symbol normalizer and data fetcher
            from utils.symbol_normalizer import normalize_symbol_for_yahoo
            from services.data_fetcher import fetch_historical_data
            
            # Normalize symbol for data fetching
            normalized_symbol = normalize_symbol_for_yahoo(symbol)
            logger.info(f"Enhanced Chart Service: Fetching data for {symbol} -> {normalized_symbol}")
            
            # Map timeframe to days for historical data
            timeframe_to_days = {
                "1m": 1, "5m": 1, "15m": 1, "30m": 1,
                "1h": 5, "4h": 10, "1H": 5, "4H": 10,
                "1d": 180, "1D": 180, "1w": 365, "1W": 365,
                "1mo": 730, "1M": 730
            }
            days = timeframe_to_days.get(timeframe, 180)
            
            # Fetch real historical data
            candles = await fetch_historical_data(normalized_symbol, timeframe.lower(), days=days)
            
            if candles and len(candles) > 0:
                # Limit to requested period
                candles = candles[-period:] if len(candles) > period else candles
                
                # Convert to required format
                candlesticks = []
                for candle in candles:
                    candlesticks.append({
                        "time": candle.get("time", 0),
                        "open": float(candle.get("open", 0)),
                        "high": float(candle.get("high", 0)),
                        "low": float(candle.get("low", 0)),
                        "close": float(candle.get("close", 0)),
                        "volume": int(candle.get("volume", 0))
                    })
                
                logger.info(f"✅ Fetched {len(candlesticks)} real candles for {symbol} ({normalized_symbol})")
                
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "candlesticks": candlesticks,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Fallback to mock data only if real data fetch fails
            logger.warning(f"⚠️ Could not fetch real data for {symbol}, using fallback mock data")
            # Use realistic base prices for common symbols
            symbol_upper = symbol.upper()
            if "NIFTY" in symbol_upper:
                base_price = 24000  # Realistic NIFTY 50 price
            elif "BANKNIFTY" in symbol_upper or "NIFTYBANK" in symbol_upper:
                base_price = 50000  # Realistic BANKNIFTY price
            elif symbol_upper == "RELIANCE":
                base_price = 2450
            elif symbol_upper == "TCS":
                base_price = 3000
            else:
                base_price = 1500  # Default for unknown symbols
            current_price = base_price
            candlesticks = []
            
            for i in range(period):
                date = datetime.now() - timedelta(days=period-i-1)
                
                # Generate realistic OHLC data
                open_price = current_price
                volatility = 0.02  # 2% daily volatility
                
                # Random walk with trend
                trend = np.random.normal(0, volatility)
                close_price = open_price * (1 + trend)
                
                # High and low based on open/close
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, volatility/2)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, volatility/2)))
                
                # Volume
                volume = np.random.randint(100000, 2000000)
                
                candlesticks.append({
                    "timestamp": date.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume
                })
                
                current_price = close_price
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "candlesticks": candlesticks,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating candlestick data: {e}")
            return {"error": str(e)}
    
    async def _add_technical_indicators(self, data: Dict) -> Dict:
        """Add technical indicators to candlestick data"""
        try:
            df = pd.DataFrame(data["candlesticks"])
            
            # Calculate basic indicators
            df["sma_20"] = ta.trend.sma_indicator(df["close"], window=20)
            df["sma_50"] = ta.trend.sma_indicator(df["close"], window=50)
            df["ema_12"] = ta.trend.ema_indicator(df["close"], window=12)
            df["ema_26"] = ta.trend.ema_indicator(df["close"], window=26)
            df["rsi"] = ta.momentum.rsi(df["close"], window=14)
            
            # MACD
            macd = ta.trend.macd(df["close"])
            df["macd"] = macd
            df["macd_signal"] = ta.trend.macd_signal(df["close"])
            df["macd_histogram"] = ta.trend.macd_diff(df["close"])
            
            # Bollinger Bands
            bb = ta.volatility.bollinger_hband(df["close"])
            df["bb_upper"] = bb
            df["bb_middle"] = ta.trend.sma_indicator(df["close"], window=20)
            df["bb_lower"] = ta.volatility.bollinger_lband(df["close"])
            
            # Volume indicators
            # Use rolling mean for volume SMA (ta.volume.volume_sma doesn't exist)
            df["volume_sma"] = df["volume"].rolling(window=20).mean()
            df["obv"] = ta.volume.on_balance_volume(df["close"], df["volume"])
            
            # Convert back to list format
            candlesticks_with_indicators = df.to_dict("records")
            
            # Clean up NaN values
            for candle in candlesticks_with_indicators:
                for key, value in candle.items():
                    if pd.isna(value):
                        candle[key] = None
            
            data["candlesticks"] = candlesticks_with_indicators
            return data
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            return data
    
    async def _calculate_indicator(self, df: pd.DataFrame, indicator: str) -> Dict:
        """Calculate a specific technical indicator"""
        try:
            if indicator == "sma_20":
                values = ta.trend.sma_indicator(df["close"], window=20).tolist()
            elif indicator == "sma_50":
                values = ta.trend.sma_indicator(df["close"], window=50).tolist()
            elif indicator == "sma_200":
                values = ta.trend.sma_indicator(df["close"], window=200).tolist()
            elif indicator == "ema_12":
                values = ta.trend.ema_indicator(df["close"], window=12).tolist()
            elif indicator == "ema_26":
                values = ta.trend.ema_indicator(df["close"], window=26).tolist()
            elif indicator == "rsi":
                values = ta.momentum.rsi(df["close"], window=14).tolist()
            elif indicator == "macd":
                values = ta.trend.macd(df["close"]).tolist()
            elif indicator == "bollinger_bands":
                upper = ta.volatility.bollinger_hband(df["close"]).tolist()
                middle = ta.trend.sma_indicator(df["close"], window=20).tolist()
                lower = ta.volatility.bollinger_lband(df["close"]).tolist()
                values = {"upper": upper, "middle": middle, "lower": lower}
            elif indicator == "stochastic":
                values = ta.momentum.stoch(df["high"], df["low"], df["close"]).tolist()
            elif indicator == "williams_r":
                values = ta.momentum.williams_r(df["high"], df["low"], df["close"]).tolist()
            elif indicator == "atr":
                values = ta.volatility.average_true_range(df["high"], df["low"], df["close"]).tolist()
            elif indicator == "adx":
                values = ta.trend.adx(df["high"], df["low"], df["close"]).tolist()
            elif indicator == "cci":
                values = ta.momentum.cci(df["high"], df["low"], df["close"]).tolist()
            elif indicator == "roc":
                values = ta.momentum.roc(df["close"], window=10).tolist()
            elif indicator == "obv":
                values = ta.volume.on_balance_volume(df["close"], df["volume"]).tolist()
            else:
                return None
            
            # Clean NaN values
            if isinstance(values, list):
                values = [v if not pd.isna(v) else None for v in values]
            elif isinstance(values, dict):
                for key in values:
                    values[key] = [v if not pd.isna(v) else None for v in values[key]]
            
            return {
                "name": indicator,
                "values": values,
                "current_value": values[-1] if isinstance(values, list) and values else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating {indicator}: {e}")
            return None
    
    def _calculate_volume_profile(self, df: pd.DataFrame) -> Dict:
        """Calculate volume profile"""
        try:
            # Price levels
            price_min = df["low"].min()
            price_max = df["high"].max()
            price_levels = np.linspace(price_min, price_max, 20)
            
            # Volume at each price level
            volume_profile = {}
            for level in price_levels:
                level_volume = 0
                for _, row in df.iterrows():
                    if row["low"] <= level <= row["high"]:
                        # Proportional volume based on price range
                        level_volume += row["volume"] * (1 / (row["high"] - row["low"] + 1))
                
                volume_profile[round(level, 2)] = level_volume
            
            # Find POC (Point of Control) - highest volume
            poc_price = max(volume_profile, key=volume_profile.get)
            
            return {
                "price_levels": list(volume_profile.keys()),
                "volumes": list(volume_profile.values()),
                "poc_price": poc_price,
                "poc_volume": volume_profile[poc_price]
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {}
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Calculate support and resistance levels"""
        try:
            highs = df["high"].values
            lows = df["low"].values
            
            # Find local maxima and minima
            from scipy.signal import argrelextrema
            
            # Local maxima (resistance)
            resistance_indices = argrelextrema(highs, np.greater, order=5)[0]
            resistance_levels = [highs[i] for i in resistance_indices]
            
            # Local minima (support)
            support_indices = argrelextrema(lows, np.less, order=5)[0]
            support_levels = [lows[i] for i in support_indices]
            
            # Sort and get strongest levels
            resistance_levels = sorted(set(resistance_levels), reverse=True)[:5]
            support_levels = sorted(set(support_levels))[:5]
            
            return {
                "support": support_levels,
                "resistance": resistance_levels
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {"support": [], "resistance": []}
    
    async def _detect_pattern(self, df: pd.DataFrame, pattern: str) -> Optional[Dict]:
        """Detect a specific chart pattern"""
        try:
            if pattern == "head_and_shoulders":
                return self._detect_head_and_shoulders(df)
            elif pattern == "double_top":
                return self._detect_double_top(df)
            elif pattern == "double_bottom":
                return self._detect_double_bottom(df)
            elif pattern == "triangle_ascending":
                return self._detect_triangle_ascending(df)
            elif pattern == "triangle_descending":
                return self._detect_triangle_descending(df)
            elif pattern == "triangle_symmetrical":
                return self._detect_triangle_symmetrical(df)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error detecting {pattern}: {e}")
            return None
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Head and Shoulders pattern"""
        try:
            highs = df["high"].values
            if len(highs) < 20:
                return None
            
            # Simple pattern detection logic
            # Look for three peaks with middle peak higher
            for i in range(10, len(highs) - 10):
                left_peak = max(highs[i-10:i])
                middle_peak = max(highs[i:i+5])
                right_peak = max(highs[i+5:i+15])
                
                if (middle_peak > left_peak and 
                    middle_peak > right_peak and
                    abs(left_peak - right_peak) / middle_peak < 0.05):  # 5% tolerance
                    
                    return {
                        "pattern": "head_and_shoulders",
                        "confidence": 0.7,
                        "start_index": i - 10,
                        "end_index": i + 15,
                        "neckline": (left_peak + right_peak) / 2,
                        "target": (left_peak + right_peak) / 2 - (middle_peak - (left_peak + right_peak) / 2)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting head and shoulders: {e}")
            return None
    
    def _detect_double_top(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Double Top pattern"""
        try:
            highs = df["high"].values
            if len(highs) < 20:
                return None
            
            # Look for two similar peaks
            for i in range(10, len(highs) - 10):
                first_peak = max(highs[i-5:i])
                second_peak = max(highs[i:i+10])
                
                if abs(first_peak - second_peak) / first_peak < 0.03:  # 3% tolerance
                    return {
                        "pattern": "double_top",
                        "confidence": 0.6,
                        "start_index": i - 5,
                        "end_index": i + 10,
                        "resistance_level": (first_peak + second_peak) / 2,
                        "target": (first_peak + second_peak) / 2 - (first_peak - df["low"].iloc[i-5:i+10].min())
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting double top: {e}")
            return None
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Double Bottom pattern"""
        try:
            lows = df["low"].values
            if len(lows) < 20:
                return None
            
            # Look for two similar troughs
            for i in range(10, len(lows) - 10):
                first_trough = min(lows[i-5:i])
                second_trough = min(lows[i:i+10])
                
                if abs(first_trough - second_trough) / first_trough < 0.03:  # 3% tolerance
                    return {
                        "pattern": "double_bottom",
                        "confidence": 0.6,
                        "start_index": i - 5,
                        "end_index": i + 10,
                        "support_level": (first_trough + second_trough) / 2,
                        "target": (first_trough + second_trough) / 2 + (df["high"].iloc[i-5:i+10].max() - first_trough)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting double bottom: {e}")
            return None
    
    def _detect_triangle_ascending(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Ascending Triangle pattern"""
        try:
            highs = df["high"].values
            lows = df["low"].values
            
            if len(highs) < 20:
                return None
            
            # Look for horizontal resistance and rising support
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            # Check if highs are relatively flat
            high_std = np.std(recent_highs)
            high_mean = np.mean(recent_highs)
            
            # Check if lows are rising
            low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
            
            if high_std / high_mean < 0.02 and low_trend > 0:  # 2% tolerance for flat highs
                return {
                    "pattern": "triangle_ascending",
                    "confidence": 0.5,
                    "start_index": len(highs) - 10,
                    "end_index": len(highs),
                    "resistance_level": high_mean,
                    "support_trend": low_trend
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting ascending triangle: {e}")
            return None
    
    def _detect_triangle_descending(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Descending Triangle pattern"""
        try:
            highs = df["high"].values
            lows = df["low"].values
            
            if len(highs) < 20:
                return None
            
            # Look for horizontal support and falling resistance
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            # Check if lows are relatively flat
            low_std = np.std(recent_lows)
            low_mean = np.mean(recent_lows)
            
            # Check if highs are falling
            high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
            
            if low_std / low_mean < 0.02 and high_trend < 0:  # 2% tolerance for flat lows
                return {
                    "pattern": "triangle_descending",
                    "confidence": 0.5,
                    "start_index": len(highs) - 10,
                    "end_index": len(highs),
                    "support_level": low_mean,
                    "resistance_trend": high_trend
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting descending triangle: {e}")
            return None
    
    def _detect_triangle_symmetrical(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Symmetrical Triangle pattern"""
        try:
            highs = df["high"].values
            lows = df["low"].values
            
            if len(highs) < 20:
                return None
            
            # Look for converging highs and lows
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            # Check if highs are falling
            high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[0]
            
            # Check if lows are rising
            low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
            
            if high_trend < 0 and low_trend > 0:
                return {
                    "pattern": "triangle_symmetrical",
                    "confidence": 0.5,
                    "start_index": len(highs) - 10,
                    "end_index": len(highs),
                    "resistance_trend": high_trend,
                    "support_trend": low_trend
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting symmetrical triangle: {e}")
            return None

# Global instance
enhanced_chart_service = EnhancedChartService()
