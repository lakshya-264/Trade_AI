"""
Intraday Trading Algorithms
Comprehensive algorithms for day trading including:
- VWAP Trading
- Momentum Trading
- Breakout Trading
- Mean Reversion
- Scalping
- Gap Trading
- Closing Range
- Volume Profile
- News Trading
- ML-enhanced Confidence Calculation
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum

# Import pandas_ta for technical indicators
try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    logger.warning("pandas_ta (ta) not available - MACD and Bollinger Bands signals disabled")

logger = logging.getLogger(__name__)

# Import SupportResistanceService for double top detection
try:
    from services.support_resistance import SupportResistanceService
    SUPPORT_RESISTANCE_AVAILABLE = True
except ImportError:
    logger.warning("SupportResistanceService not available - double top detection disabled")
    SUPPORT_RESISTANCE_AVAILABLE = False

def to_python_type(value):
    """Convert numpy/pandas types to Python native types for JSON serialization"""
    # Check for NaN/None first
    if pd.isna(value) or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    # Handle numpy.bool_ first (it has item() but isinstance check is more explicit)
    if isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        # Check for NaN/Inf before converting
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    elif hasattr(value, 'item'):
        # numpy scalar - use item() to extract Python native type
        try:
            result = value.item()
            # Check for NaN/Inf after extraction
            if isinstance(result, float) and (np.isnan(result) or np.isinf(result)):
                return None
            return result
        except (AttributeError, ValueError):
            # Fallback if item() doesn't work
            if isinstance(value, bool):
                return bool(value)
            elif isinstance(value, (int, float)):
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    return None
                return type(value)(value)
            else:
                return value
    elif pd.isna(value):
        return None
    else:
        return value

def clean_nan_values(data: Any) -> Any:
    """Recursively clean NaN, Inf, and None values from dictionaries and lists for JSON serialization"""
    if isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            cleaned_val = clean_nan_values(v)
            # Only include None values for specific keys that are allowed to be None
            if cleaned_val is not None or k in ['entry_price', 'stop_loss', 'target_price', 'target', 'entry']:
                cleaned_dict[k] = cleaned_val
        return cleaned_dict
    elif isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, (float, np.floating)):
        if pd.isna(data) or np.isnan(data) or np.isinf(data):
            return None
        try:
            val = float(data)
            # Double-check after conversion
            if np.isnan(val) or np.isinf(val):
                return None
            return val
        except (ValueError, TypeError, OverflowError):
            return None
    elif isinstance(data, (int, np.integer)):
        try:
            return int(data)
        except (ValueError, TypeError, OverflowError):
            return None
    elif pd.isna(data):
        return None
    elif hasattr(data, 'item'):  # numpy scalar
        try:
            val = data.item()
            if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                return None
            if isinstance(val, (float, np.floating)):
                val = float(val)
                if np.isnan(val) or np.isinf(val):
                    return None
            return val
        except (AttributeError, ValueError, TypeError):
            return None
    elif isinstance(data, str):
        return data  # Strings are fine
    else:
        # For any other type, try to convert to a safe type
        try:
            if isinstance(data, bool):
                return bool(data)
            # If it's a number-like object, try to convert
            if hasattr(data, '__float__'):
                val = float(data)
                if np.isnan(val) or np.isinf(val):
                    return None
                return val
            return data
        except (ValueError, TypeError, AttributeError):
            return None

class IntradayStrategy(str, Enum):
    """Intraday Trading Strategies"""
    SCALPING = "scalping"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    VWAP_TRADING = "vwap_trading"
    GAP_TRADING = "gap_trading"
    OPENING_RANGE = "opening_range"
    CLOSING_RANGE = "closing_range"
    NEWS_TRADING = "news_trading"
    VOLUME_PROFILE = "volume_profile"

class TradingSession(str, Enum):
    """Trading Session Types"""
    PRE_MARKET = "pre_market"  # 9:00 - 9:15
    OPENING = "opening"  # 9:15 - 10:00
    MID_MORNING = "mid_morning"  # 10:00 - 11:30
    MID_DAY = "mid_day"  # 11:30 - 14:00
    AFTERNOON = "afternoon"  # 14:00 - 15:00
    CLOSING = "closing"  # 15:00 - 15:30

class IntradayTradingAlgorithms:
    """Intraday Trading Algorithms"""
    
    def __init__(self):
        self.vwap_cache = {}
        self.session_highs = {}
        self.session_lows = {}
        # Initialize SupportResistanceService for double top detection
        if SUPPORT_RESISTANCE_AVAILABLE:
            self.sr_service = SupportResistanceService()
        else:
            self.sr_service = None
        
    def get_trading_session(self, current_time: datetime) -> TradingSession:
        """Determine current trading session"""
        hour = current_time.hour
        minute = current_time.minute
        
        if hour == 9 and minute < 15:
            return TradingSession.PRE_MARKET
        elif hour == 9 or (hour == 10 and minute == 0):
            return TradingSession.OPENING
        elif hour < 11 or (hour == 11 and minute < 30):
            return TradingSession.MID_MORNING
        elif hour < 14:
            return TradingSession.MID_DAY
        elif hour < 15:
            return TradingSession.AFTERNOON
        else:
            return TradingSession.CLOSING
    
    def calculate_vwap(
        self,
        data: pd.DataFrame,
        period: Optional[int] = None
    ) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP)
        Essential for intraday trading
        """
        if data.empty or 'volume' not in data.columns:
            return pd.Series()
        
        if period:
            data = data.tail(period)
        
        # Ensure required columns exist and have valid data
        required_cols = ['high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            return pd.Series()
        
        # Fill NaN values in volume with 0 to avoid division issues
        volume = data['volume'].fillna(0)
        
        # Calculate typical price
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # Calculate VWAP, handling zero volume cases
        volume_cumsum = volume.cumsum()
        # Avoid division by zero - use a small epsilon for zero volumes
        volume_cumsum = volume_cumsum.replace(0, np.nan)
        vwap = (typical_price * volume).cumsum() / volume_cumsum
        
        # Fill any remaining NaN values with the last valid value (forward fill)
        vwap = vwap.ffill().bfill()
        
        # If still NaN, fill with close price as fallback
        if vwap.isna().any():
            vwap = vwap.fillna(data['close'])
        
        return vwap
    
    def vwap_trading_signal(
        self,
        current_price: float,
        vwap: float,
        price_history: pd.DataFrame,
        volume_history: pd.Series
    ) -> Dict[str, Any]:
        """
        Generate VWAP-based trading signals
        Price above VWAP = Bullish
        Price below VWAP = Bearish
        """
        # Check for NaN/Invalid values
        if pd.isna(vwap) or vwap == 0 or np.isnan(vwap) or np.isinf(vwap):
            return {"error": "Invalid VWAP"}
        
        if pd.isna(current_price) or np.isnan(current_price) or np.isinf(current_price):
            return {"error": "Invalid current price"}
        
        # Calculate price vs VWAP percentage
        price_vs_vwap = ((current_price - vwap) / vwap) * 100 if vwap != 0 else 0.0
        
        # Calculate distance bands with NaN handling
        volatility = 0.0
        if not price_history.empty and 'close' in price_history.columns:
            std_val = price_history['close'].std()
            if not pd.isna(std_val) and not np.isnan(std_val) and not np.isinf(std_val):
                volatility = float(std_val)
        
        upper_band = vwap + (2 * volatility)
        lower_band = vwap - (2 * volatility)
        
        # Ensure bands are valid numbers
        if pd.isna(upper_band) or np.isnan(upper_band) or np.isinf(upper_band):
            upper_band = vwap * 1.02  # Default 2% above VWAP
        if pd.isna(lower_band) or np.isnan(lower_band) or np.isinf(lower_band):
            lower_band = vwap * 0.98  # Default 2% below VWAP
        
        # Generate signal
        if current_price > upper_band:
            signal = "SELL"
            strength = "STRONG"
            reason = "Price significantly above VWAP - Overbought"
        elif current_price > vwap * 1.01:
            signal = "BUY"
            strength = "MODERATE"
            reason = "Price above VWAP - Bullish momentum"
        elif current_price < lower_band:
            signal = "BUY"
            strength = "STRONG"
            reason = "Price significantly below VWAP - Oversold"
        elif current_price < vwap * 0.99:
            signal = "SELL"
            strength = "MODERATE"
            reason = "Price below VWAP - Bearish momentum"
        else:
            signal = "HOLD"
            strength = "WEAK"
            reason = "Price near VWAP - Neutral"
        
        # Convert numpy types to Python native types for JSON serialization, handling NaN
        # Ensure all values are valid before adding to result
        def safe_to_python(val):
            """Safely convert to Python type, ensuring no NaN/Inf"""
            converted = to_python_type(val)
            if converted is None:
                return None
            if isinstance(converted, float):
                if np.isnan(converted) or np.isinf(converted):
                    return None
            return converted
        
        result = {
            "signal": signal,
            "strength": strength,
            "current_price": safe_to_python(current_price),
            "vwap": safe_to_python(vwap),
            "price_vs_vwap_pct": safe_to_python(price_vs_vwap),
            "upper_band": safe_to_python(upper_band),
            "lower_band": safe_to_python(lower_band),
            "reason": reason,
            "entry_price": safe_to_python(vwap) if signal != "HOLD" else None,
            "stop_loss": safe_to_python(lower_band) if signal == "BUY" else safe_to_python(upper_band) if signal == "SELL" else None,
            "target": safe_to_python(upper_band) if signal == "BUY" else safe_to_python(lower_band) if signal == "SELL" else None
        }
        
        # Clean any remaining NaN values (double pass for safety)
        cleaned = clean_nan_values(result)
        # Final pass to ensure no NaN values remain
        return clean_nan_values(cleaned)
    
    def momentum_trading_signal(
        self,
        data: pd.DataFrame,
        period: int = 14,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Momentum-based intraday trading
        Uses RSI and Price Rate of Change
        """
        if len(data) < period:
            return {"error": "Insufficient data"}
        
        # Calculate RSI with NaN handling
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        # Avoid division by zero
        loss = loss.replace(0, np.nan)
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Handle NaN RSI values
        if pd.isna(current_rsi) or np.isnan(current_rsi) or np.isinf(current_rsi):
            current_rsi = 50.0  # Default neutral RSI
        
        # Calculate ROC with NaN handling
        if data['close'].iloc[-period] > 0:
            roc = ((data['close'].iloc[-1] - data['close'].iloc[-period]) / data['close'].iloc[-period]) * 100
        else:
            roc = 0.0
        
        # Handle NaN ROC
        if pd.isna(roc) or np.isnan(roc) or np.isinf(roc):
            roc = 0.0
        
        # Calculate momentum
        momentum = data['close'].iloc[-1] - data['close'].iloc[-period]
        momentum_pct = (momentum / data['close'].iloc[-period]) * 100 if data['close'].iloc[-period] > 0 else 0.0
        
        # Handle NaN momentum
        if pd.isna(momentum) or np.isnan(momentum) or np.isinf(momentum):
            momentum = 0.0
        if pd.isna(momentum_pct) or np.isnan(momentum_pct) or np.isinf(momentum_pct):
            momentum_pct = 0.0
        
        # Generate signal
        if current_rsi > 70 and roc > threshold:
            signal = "SELL"
            strength = "STRONG"
            reason = "Overbought with strong momentum - Reversal likely"
        elif current_rsi > 60 and roc > threshold:
            signal = "SELL"
            strength = "MODERATE"
            reason = "Overbought with positive momentum"
        elif current_rsi < 30 and roc < -threshold:
            signal = "BUY"
            strength = "STRONG"
            reason = "Oversold with strong negative momentum - Reversal likely"
        elif current_rsi < 40 and roc < -threshold:
            signal = "BUY"
            strength = "MODERATE"
            reason = "Oversold with negative momentum"
        elif roc > threshold:
            signal = "BUY"
            strength = "MODERATE"
            reason = "Strong positive momentum"
        elif roc < -threshold:
            signal = "SELL"
            strength = "MODERATE"
            reason = "Strong negative momentum"
        else:
            signal = "HOLD"
            strength = "WEAK"
            reason = "Weak momentum - Wait for confirmation"
        
        # Convert numpy types to Python native types for JSON serialization, handling NaN
        result = {
            "signal": signal,
            "strength": strength,
            "rsi": to_python_type(current_rsi),
            "roc": to_python_type(roc),
            "momentum": to_python_type(momentum),
            "momentum_pct": to_python_type(momentum_pct),
            "reason": reason,
            "current_price": to_python_type(data['close'].iloc[-1])
        }
        
        # Clean any remaining NaN values
        return clean_nan_values(result)
    
    def breakout_trading_signal(
        self,
        data: pd.DataFrame,
        lookback_period: int = 20,
        volume_threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        Breakout trading strategy
        Identifies breakouts from consolidation with volume confirmation
        Now includes double top resistance detection for stronger signals
        """
        if len(data) < lookback_period:
            return {"error": "Insufficient data"}
        
        # Convert numpy types to Python native types immediately using helper function
        current_price = to_python_type(data['close'].iloc[-1])
        current_volume = to_python_type(data['volume'].iloc[-1]) if 'volume' in data.columns else 0.0
        
        # Calculate resistance and support
        recent_high = to_python_type(data['high'].tail(lookback_period).max())
        recent_low = to_python_type(data['low'].tail(lookback_period).min())
        avg_volume = to_python_type(data['volume'].tail(lookback_period).mean()) if 'volume' in data.columns else 0.0
        
        # Get support/resistance levels with double top detection
        double_top_resistance = None
        nearest_resistance = None
        resistance_levels = []
        
        if self.sr_service and len(data) >= 50:  # Need enough data for S&R analysis
            try:
                # Convert DataFrame to list of dicts for S&R service
                data_list = data.tail(100).to_dict('records')
                sr_result = self.sr_service.analyze_support_resistance(
                    data=data_list,
                    min_touches=2,
                    tolerance_percent=0.5,
                    lookback_period=100,
                    check_double_top=True
                )
                
                if sr_result.get('success') and sr_result.get('data'):
                    sr_data = sr_result['data']
                    resistance_levels = sr_data.get('resistance_levels', [])
                    nearest_resistance = sr_data.get('nearest_resistance')
                    double_top_resistance = sr_data.get('double_top_resistance')
                    
                    # Find double top resistance levels
                    for level in resistance_levels:
                        if level.get('is_double_top'):
                            double_top_resistance = {
                                'price': level['price'],
                                'strength': level.get('strength', 0),
                                'double_top_info': level.get('double_top_info', {})
                            }
                            break
            except Exception as e:
                logger.warning(f"Error fetching S&R levels for breakout: {e}")
        
        # Check for breakout
        breakout_threshold = float((recent_high - recent_low) * 0.02)  # 2% of range
        
        # Check if price is near double top resistance (within 1%)
        near_double_top = False
        double_top_price = None
        if double_top_resistance:
            double_top_price = double_top_resistance.get('price')
            if double_top_price:
                price_distance_pct = abs((current_price - double_top_price) / double_top_price) * 100
                if price_distance_pct <= 1.0:  # Within 1% of double top
                    near_double_top = True
        
        # Use double top resistance as stronger resistance if available
        effective_resistance = recent_high
        if double_top_price and double_top_price > recent_high:
            effective_resistance = double_top_price
            logger.info(f"Using double top resistance {double_top_price:.2f} instead of recent high {recent_high:.2f}")
        
        # Bullish breakout
        if current_price > effective_resistance + breakout_threshold:
            if current_volume > avg_volume * volume_threshold:
                if double_top_price and current_price > double_top_price:
                    signal = "BUY"
                    strength = "STRONG"
                    reason = f"Strong bullish breakout above DOUBLE TOP resistance {double_top_price:.2f} with volume confirmation"
                else:
                    signal = "BUY"
                    strength = "STRONG"
                    reason = f"Bullish breakout above {effective_resistance:.2f} with volume confirmation"
                entry = float(effective_resistance + breakout_threshold)
                stop_loss = float(effective_resistance - breakout_threshold)
                target = float(entry + (entry - stop_loss) * 2)  # 1:2 risk-reward
            else:
                signal = "WEAK_BUY"
                strength = "WEAK"
                if double_top_price:
                    reason = f"Breakout above {effective_resistance:.2f} (near double top {double_top_price:.2f}) but low volume"
                else:
                    reason = f"Bullish breakout above {effective_resistance:.2f} but low volume"
                entry = None
                stop_loss = None
                target = None
        
        # Bearish breakdown or rejection at double top
        elif current_price < recent_low - breakout_threshold:
            if current_volume > avg_volume * float(volume_threshold):
                signal = "SELL"
                strength = "STRONG"
                reason = f"Bearish breakdown below {recent_low:.2f} with volume confirmation"
                entry = float(recent_low - breakout_threshold)
                stop_loss = float(recent_low + breakout_threshold)
                target = float(entry - (stop_loss - entry) * 2)  # 1:2 risk-reward
            else:
                signal = "WEAK_SELL"
                strength = "WEAK"
                reason = f"Bearish breakdown below {recent_low:.2f} but low volume"
                entry = None
                stop_loss = None
                target = None
        
        # Price near double top resistance - potential rejection
        elif near_double_top and double_top_price:
            if current_price < double_top_price:
                signal = "SELL"
                strength = "MODERATE"
                reason = f"Price near DOUBLE TOP resistance {double_top_price:.2f} - Potential rejection. Current: {current_price:.2f}"
                entry = float(current_price)
                stop_loss = float(double_top_price + breakout_threshold)
                target = float(entry - (stop_loss - entry) * 1.5)  # 1:1.5 risk-reward
            else:
                signal = "HOLD"
                strength = "MODERATE"
                reason = f"Price at DOUBLE TOP resistance {double_top_price:.2f} - Wait for breakout confirmation"
                entry = None
                stop_loss = None
                target = None
        
        else:
            signal = "HOLD"
            strength = "WEAK"
            if double_top_price:
                reason = f"Price in range {recent_low:.2f} - {effective_resistance:.2f} (Double Top: {double_top_price:.2f}) - Wait for breakout"
            else:
                reason = f"Price in range {recent_low:.2f} - {recent_high:.2f} - Wait for breakout"
            entry = None
            stop_loss = None
            target = None
        
        # Convert numpy types to Python native types for JSON serialization
        # Ensure volume_confirmed is a Python bool, not numpy.bool_
        if avg_volume > 0:
            comparison_result = current_volume > (avg_volume * to_python_type(volume_threshold))
            # Use helper function to ensure Python native type
            volume_confirmed = to_python_type(comparison_result)
        else:
            volume_confirmed = False

        rvol = None
        if avg_volume and avg_volume > 0:
            rvol = to_python_type(current_volume / avg_volume)

        volume_quality = "CONFIRMED" if volume_confirmed else "LOW"
        fakeout_risk = False
        if str(signal) not in ["HOLD", "WAIT"] and not volume_confirmed:
            fakeout_risk = True
        
        # Ensure ALL values are Python native types - convert everything explicitly
        result_dict = {
            "signal": str(signal),
            "strength": str(strength),
            "current_price": to_python_type(current_price),
            "resistance": to_python_type(effective_resistance),
            "support": to_python_type(recent_low),
            "entry": to_python_type(entry) if entry is not None else None,
            "stop_loss": to_python_type(stop_loss) if stop_loss is not None else None,
            "target": to_python_type(target) if target is not None else None,
            "reason": str(reason),
            "volume_confirmed": to_python_type(volume_confirmed),
            "rvol": rvol,
            "volume_quality": volume_quality,
            "fakeout_risk": to_python_type(fakeout_risk),
            "double_top_resistance": to_python_type(double_top_price) if double_top_price else None,
            "near_double_top": near_double_top
        }
        return result_dict
    
    def mean_reversion_signal(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        Mean reversion trading strategy
        Buy when price is below mean, sell when above
        """
        if len(data) < period:
            return {"error": "Insufficient data"}
        
        current_price = data['close'].iloc[-1]
        sma = data['close'].tail(period).mean()
        std = data['close'].tail(period).std()
        
        upper_band = sma + (std * std_multiplier)
        lower_band = sma - (std * std_multiplier)
        
        distance_from_mean = ((current_price - sma) / sma) * 100 if sma > 0 else 0
        
        # Generate signal
        if current_price < lower_band:
            signal = "BUY"
            strength = "STRONG"
            reason = f"Price {distance_from_mean:.2f}% below mean - Oversold, expect reversion"
            entry = current_price
            stop_loss = lower_band - std
            target = sma
        elif current_price > upper_band:
            signal = "SELL"
            strength = "STRONG"
            reason = f"Price {distance_from_mean:.2f}% above mean - Overbought, expect reversion"
            entry = current_price
            stop_loss = upper_band + std
            target = sma
        else:
            signal = "HOLD"
            strength = "WEAK"
            reason = f"Price near mean ({distance_from_mean:.2f}%) - No reversion signal"
            entry = None
            stop_loss = None
            target = None
        
        # Convert numpy types to Python native types for JSON serialization
        return {
            "signal": signal,
            "strength": strength,
            "current_price": float(current_price),
            "sma": float(sma),
            "upper_band": float(upper_band),
            "lower_band": float(lower_band),
            "distance_from_mean_pct": float(distance_from_mean),
            "entry": float(entry) if entry is not None else None,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "target": float(target) if target is not None else None,
            "reason": reason
        }
    
    def scalping_signal(
        self,
        data: pd.DataFrame,
        tick_size: float = 0.05,
        min_profit_target: float = 0.3
    ) -> Dict[str, Any]:
        """
        Scalping strategy for quick intraday profits
        Very short-term trades (seconds to minutes)
        """
        if len(data) < 5:
            return {"error": "Insufficient data for scalping"}
        
        current_price = data['close'].iloc[-1]
        prev_price = data['close'].iloc[-2]
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100 if prev_price > 0 else 0
        
        # Calculate micro-trend
        recent_prices = data['close'].tail(5)
        micro_trend = "UP" if recent_prices.iloc[-1] > recent_prices.iloc[0] else "DOWN"
        
        # Volume check
        current_volume = data['volume'].iloc[-1] if 'volume' in data.columns else 0
        avg_volume = data['volume'].tail(5).mean() if 'volume' in data.columns else 0
        
        # Generate scalping signal
        if abs(price_change_pct) > min_profit_target:
            if price_change > 0 and micro_trend == "UP" and current_volume > avg_volume * 0.8:
                signal = "BUY"
                strength = "MODERATE"
                reason = f"Micro uptrend with {price_change_pct:.2f}% move - Quick scalp opportunity"
                entry = current_price
                stop_loss = current_price - (tick_size * 2)
                target = current_price + (tick_size * 3)
            elif price_change < 0 and micro_trend == "DOWN" and current_volume > avg_volume * 0.8:
                signal = "SELL"
                strength = "MODERATE"
                reason = f"Micro downtrend with {abs(price_change_pct):.2f}% move - Quick scalp opportunity"
                entry = current_price
                stop_loss = current_price + (tick_size * 2)
                target = current_price - (tick_size * 3)
            else:
                signal = "HOLD"
                strength = "WEAK"
                reason = "Insufficient momentum for scalping"
                entry = None
                stop_loss = None
                target = None
        else:
            signal = "HOLD"
            strength = "WEAK"
            reason = f"Price movement ({abs(price_change_pct):.2f}%) below minimum threshold"
            entry = None
            stop_loss = None
            target = None
        
        # Convert numpy types to Python native types for JSON serialization
        risk_reward = None
        if entry and stop_loss and target:
            risk_reward = float(abs(target - entry) / abs(stop_loss - entry))
        
        return {
            "signal": signal,
            "strength": strength,
            "current_price": float(current_price),
            "price_change": float(price_change),
            "price_change_pct": float(price_change_pct),
            "micro_trend": micro_trend,
            "entry": float(entry) if entry is not None else None,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "target": float(target) if target is not None else None,
            "reason": reason,
            "risk_reward": risk_reward
        }
    
    def gap_trading_signal(
        self,
        data: pd.DataFrame,
        previous_close: Optional[float] = None,
        gap_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Gap Trading Strategy
        Identifies and trades price gaps at market open
        """
        # Need at least 2 days of data: one for today's open and one for previous close
        if len(data) < 2:
            return {"error": "Insufficient data for gap analysis. Need at least 2 days of data."}
        
        # Data is sorted by time (oldest first), so:
        # - Last row is the most recent (today)
        # - Second-to-last row is previous day (if available)
        # Get today's open (most recent day)
        today_open = data['open'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # Get previous day's close
        if previous_close is None:
            # Extract from data (we already validated len(data) >= 2)
            # Previous day is the second-to-last row
            previous_close = data['close'].iloc[-2]
        
        if previous_close is None or previous_close <= 0:
            return {"error": "Invalid previous close price for gap analysis"}
        
        gap = today_open - previous_close
        gap_pct = (gap / previous_close) * 100 if previous_close > 0 else 0
        
        # Calculate gap size
        gap_size = abs(gap_pct)
        
        # Determine gap type
        if gap > 0:
            gap_type = "UPWARD_GAP"
        elif gap < 0:
            gap_type = "DOWNWARD_GAP"
        else:
            gap_type = "NO_GAP"
        
        # Generate signal based on gap and price action
        if gap_size > gap_threshold:
            if gap_type == "UPWARD_GAP":
                # Bullish gap - check if price holds above gap
                if current_price > today_open:
                    signal = "BUY"
                    strength = "STRONG"
                    reason = f"Bullish gap up {gap_pct:.2f}% - Price holding above gap, continuation likely"
                    entry = current_price
                    stop_loss = today_open - (gap * 0.5)  # Below gap
                    target = today_open + (gap * 1.5)  # Gap extension
                elif current_price < previous_close:
                    signal = "SELL"
                    strength = "MODERATE"
                    reason = f"Bullish gap up {gap_pct:.2f}% - Gap filling, reversal likely"
                    entry = current_price
                    stop_loss = today_open + (gap * 0.3)
                    target = previous_close  # Fill gap
                else:
                    signal = "HOLD"
                    strength = "WEAK"
                    reason = f"Bullish gap up {gap_pct:.2f}% - Price consolidating, wait for direction"
                    entry = None
                    stop_loss = None
                    target = None
            else:  # DOWNWARD_GAP
                # Bearish gap - check if price holds below gap
                if current_price < today_open:
                    signal = "SELL"
                    strength = "STRONG"
                    reason = f"Bearish gap down {abs(gap_pct):.2f}% - Price holding below gap, continuation likely"
                    entry = current_price
                    stop_loss = today_open + (abs(gap) * 0.5)  # Above gap
                    target = today_open - (abs(gap) * 1.5)  # Gap extension
                elif current_price > previous_close:
                    signal = "BUY"
                    strength = "MODERATE"
                    reason = f"Bearish gap down {abs(gap_pct):.2f}% - Gap filling, reversal likely"
                    entry = current_price
                    stop_loss = today_open - (abs(gap) * 0.3)
                    target = previous_close  # Fill gap
                else:
                    signal = "HOLD"
                    strength = "WEAK"
                    reason = f"Bearish gap down {abs(gap_pct):.2f}% - Price consolidating, wait for direction"
                    entry = None
                    stop_loss = None
                    target = None
        else:
            signal = "HOLD"
            strength = "WEAK"
            reason = f"Gap size {gap_pct:.2f}% below threshold {gap_threshold}% - No significant gap"
            entry = None
            stop_loss = None
            target = None
        
        return {
            "signal": signal,
            "strength": strength,
            "gap_type": gap_type,
            "gap_pct": float(gap_pct),
            "gap_size": float(gap_size),
            "today_open": float(today_open),
            "previous_close": float(previous_close),
            "current_price": float(current_price),
            "entry": float(entry) if entry is not None else None,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "target": float(target) if target is not None else None,
            "reason": reason
        }
    
    def closing_range_breakout(
        self,
        data: pd.DataFrame,
        closing_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Closing Range Breakout Strategy
        Last 30 minutes define the range, trade breakouts for next day
        """
        if len(data) < closing_minutes:
            return {"error": "Insufficient closing data"}
        
        # Get closing range (last 30 minutes)
        closing_data = data.tail(closing_minutes)
        closing_high = closing_data['high'].max()
        closing_low = closing_data['low'].min()
        closing_range = closing_high - closing_low
        closing_mid = (closing_high + closing_low) / 2
        
        current_price = data['close'].iloc[-1]
        current_time = datetime.now()
        
        # Check if we're in closing period
        if current_time.hour < 15 or (current_time.hour == 15 and current_time.minute < 30):
            # Still in trading hours - analyze current position
            breakout_threshold = closing_range * 0.1  # 10% of range
            
            if current_price > closing_high + breakout_threshold:
                signal = "BUY"
                strength = "STRONG"
                reason = f"Price breaking above closing range high {closing_high:.2f} - Strong momentum"
                entry = current_price
                stop_loss = closing_high
                target = closing_high + (closing_range * 1.5)
            elif current_price < closing_low - breakout_threshold:
                signal = "SELL"
                strength = "STRONG"
                reason = f"Price breaking below closing range low {closing_low:.2f} - Weak momentum"
                entry = current_price
                stop_loss = closing_low
                target = closing_low - (closing_range * 1.5)
            elif current_price > closing_mid:
                signal = "BUY"
                strength = "MODERATE"
                reason = f"Price in upper half of closing range - Slight bullish bias"
                entry = current_price
                stop_loss = closing_mid
                target = closing_high
            elif current_price < closing_mid:
                signal = "SELL"
                strength = "MODERATE"
                reason = f"Price in lower half of closing range - Slight bearish bias"
                entry = current_price
                stop_loss = closing_mid
                target = closing_low
            else:
                signal = "HOLD"
                strength = "WEAK"
                reason = f"Price at closing range midpoint - Neutral"
                entry = None
                stop_loss = None
                target = None
        else:
            # Market closed - provide next day guidance
            signal = "HOLD"
            strength = "WEAK"
            reason = f"Market closed. Closing range: {closing_low:.2f} - {closing_high:.2f}. Monitor next day opening."
            entry = None
            stop_loss = None
            target = None
        
        return {
            "signal": signal,
            "strength": strength,
            "closing_high": float(closing_high),
            "closing_low": float(closing_low),
            "closing_range": float(closing_range),
            "closing_mid": float(closing_mid),
            "current_price": float(current_price),
            "entry": float(entry) if entry is not None else None,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "target": float(target) if target is not None else None,
            "reason": reason
        }
    
    def volume_profile_signal(
        self,
        data: pd.DataFrame,
        bins: int = 20
    ) -> Dict[str, Any]:
        """
        Volume Profile Analysis
        Identifies high-volume price levels (support/resistance)
        """
        if len(data) < 10:
            return {"error": "Insufficient data for volume profile"}
        
        if 'volume' not in data.columns:
            return {"error": "Volume data required for volume profile"}
        
        current_price = data['close'].iloc[-1]
        
        # Create price bins
        price_min = data['low'].min()
        price_max = data['high'].max()
        price_range = price_max - price_min
        bin_size = price_range / bins
        
        # Calculate volume at each price level
        volume_profile = {}
        for i in range(len(data)):
            price = data['close'].iloc[i]
            volume = data['volume'].iloc[i]
            
            # Assign to bin
            bin_index = int((price - price_min) / bin_size)
            bin_index = min(bin_index, bins - 1)
            bin_price = price_min + (bin_index * bin_size)
            
            if bin_price not in volume_profile:
                volume_profile[bin_price] = 0
            volume_profile[bin_price] += volume
        
        # Find Point of Control (POC) - price level with highest volume
        if not volume_profile:
            return {"error": "Could not calculate volume profile"}
        
        poc_price = max(volume_profile, key=volume_profile.get)
        poc_volume = volume_profile[poc_price]
        total_volume = sum(volume_profile.values())
        
        # Find value area (70% of volume)
        sorted_levels = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
        cumulative_volume = 0
        value_area_high = poc_price
        value_area_low = poc_price
        
        for price, volume in sorted_levels:
            cumulative_volume += volume
            if cumulative_volume <= total_volume * 0.7:
                value_area_high = max(value_area_high, price)
                value_area_low = min(value_area_low, price)
        
        # Generate signal based on price position relative to POC and value area
        price_vs_poc = ((current_price - poc_price) / poc_price) * 100 if poc_price > 0 else 0
        
        if current_price > value_area_high:
            signal = "SELL"
            strength = "MODERATE"
            reason = f"Price above value area - Overvalued, expect pullback to POC {poc_price:.2f}"
            entry = current_price
            # For SELL: Stop loss must be ABOVE entry price (to limit upside risk)
            stop_loss_above_entry = current_price * 1.02  # 2% above entry
            stop_loss_above_val = value_area_high + (price_range * 0.03)  # 3% above value area high
            stop_loss = max(stop_loss_above_entry, stop_loss_above_val, current_price * 1.01)  # Ensure it's always above entry
            target = poc_price
        elif current_price < value_area_low:
            signal = "BUY"
            strength = "MODERATE"
            reason = f"Price below value area - Undervalued, expect bounce to POC {poc_price:.2f}"
            entry = current_price
            # For BUY: Stop loss must be BELOW entry price (to limit downside)
            # Use 2% below entry or value_area_low - 3% buffer, whichever is lower
            stop_loss_below_entry = current_price * 0.98  # 2% below entry
            stop_loss_below_val = value_area_low - (price_range * 0.03)  # 3% below value area low
            stop_loss = min(stop_loss_below_entry, stop_loss_below_val, current_price * 0.97)  # Ensure it's always below entry
            target = poc_price
        elif abs(price_vs_poc) < 1.0:  # Within 1% of POC
            signal = "HOLD"
            strength = "WEAK"
            reason = f"Price near POC {poc_price:.2f} - High liquidity zone, wait for breakout"
            entry = None
            stop_loss = None
            target = None
        elif current_price > poc_price:
            signal = "SELL"
            strength = "WEAK"
            reason = f"Price above POC {poc_price:.2f} - Consider taking profits"
            entry = current_price
            # For SELL: Stop loss must be ABOVE entry price (to limit upside risk)
            stop_loss_above_entry = current_price * 1.02  # 2% above entry
            stop_loss_above_poc = poc_price + (price_range * 0.02)  # 2% above POC
            stop_loss = max(stop_loss_above_entry, stop_loss_above_poc, current_price * 1.01)  # Ensure it's always above entry
            target = value_area_low
        else:
            signal = "BUY"
            strength = "WEAK"
            reason = f"Price below POC {poc_price:.2f} - Consider buying opportunity"
            entry = current_price
            # For BUY: Stop loss must be BELOW entry price
            stop_loss_below_entry = current_price * 0.98  # 2% below entry
            stop_loss_below_poc = poc_price - (price_range * 0.02)  # 2% below POC
            stop_loss = min(stop_loss_below_entry, stop_loss_below_poc, current_price * 0.97)  # Ensure it's always below entry
            target = value_area_high
        
        return {
            "signal": signal,
            "strength": strength,
            "poc_price": float(poc_price),
            "poc_volume": float(poc_volume),
            "value_area_high": float(value_area_high),
            "value_area_low": float(value_area_low),
            "current_price": float(current_price),
            "price_vs_poc_pct": float(price_vs_poc),
            "entry": float(entry) if entry is not None else None,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "target": float(target) if target is not None else None,
            "reason": reason
        }
    
    def opening_range_breakout(
        self,
        data: pd.DataFrame,
        opening_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Opening Range Breakout Strategy
        First 15 minutes define the range, trade breakouts
        """
        if len(data) < opening_minutes:
            return {"error": "Insufficient opening data"}
        
        opening_data = data.head(opening_minutes)
        opening_high = opening_data['high'].max()
        opening_low = opening_data['low'].min()
        opening_range = opening_high - opening_low
        
        current_price = data['close'].iloc[-1]
        current_time = datetime.now()
        
        # Check if we're past opening period
        if current_time.hour == 9 and current_time.minute < 15:
            # Convert numpy types to Python native types for JSON serialization
            return {
                "signal": "WAIT",
                "reason": "Still in opening range period - Wait for breakout",
                "opening_high": float(opening_high),
                "opening_low": float(opening_low),
                "current_price": float(current_price)
            }
        
        # Check for breakout
        breakout_threshold = opening_range * 0.1  # 10% of range
        
        if current_price > opening_high + breakout_threshold:
            signal = "BUY"
            strength = "STRONG"
            reason = f"Bullish breakout above opening high {opening_high:.2f}"
            entry = opening_high + breakout_threshold
            stop_loss = opening_high
            target = opening_high + (opening_range * 1.5)
        elif current_price < opening_low - breakout_threshold:
            signal = "SELL"
            strength = "STRONG"
            reason = f"Bearish breakdown below opening low {opening_low:.2f}"
            entry = opening_low - breakout_threshold
            stop_loss = opening_low
            target = opening_low - (opening_range * 1.5)
        else:
            signal = "HOLD"
            strength = "WEAK"
            reason = f"Price within opening range {opening_low:.2f} - {opening_high:.2f}"
            entry = None
            stop_loss = None
            target = None
        
        # Convert numpy types to Python native types for JSON serialization
        return {
            "signal": signal,
            "strength": strength,
            "opening_high": float(opening_high),
            "opening_low": float(opening_low),
            "opening_range": float(opening_range),
            "current_price": float(current_price),
            "entry": float(entry) if entry is not None else None,
            "stop_loss": float(stop_loss) if stop_loss is not None else None,
            "target": float(target) if target is not None else None,
            "reason": reason
        }
    
    def generate_intraday_signal(
        self,
        data: pd.DataFrame,
        strategy: IntradayStrategy = IntradayStrategy.VWAP_TRADING,
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive intraday trading signal
        Combines multiple strategies based on market conditions
        """
        if data.empty:
            return {"error": "No data provided"}
        
        if current_time is None:
            current_time = datetime.now()
        
        session = self.get_trading_session(current_time)
        signals = []
        confidence_scores = []
        
        # VWAP Signal (always included)
        vwap = self.calculate_vwap(data)
        if not vwap.empty:
            vwap_signal = self.vwap_trading_signal(
                data['close'].iloc[-1],
                vwap.iloc[-1],
                data,
                data['volume'] if 'volume' in data.columns else pd.Series()
            )
            if 'signal' in vwap_signal:
                signals.append(vwap_signal['signal'])
                confidence_scores.append(0.7 if vwap_signal.get('strength') == 'STRONG' else 0.5)
        
        # Strategy-specific signals
        if strategy == IntradayStrategy.MOMENTUM:
            momentum_signal = self.momentum_trading_signal(data)
            if 'signal' in momentum_signal:
                signals.append(momentum_signal['signal'])
                confidence_scores.append(0.6)
        
        elif strategy == IntradayStrategy.BREAKOUT:
            breakout_signal = self.breakout_trading_signal(data)
            if 'signal' in breakout_signal:
                signals.append(breakout_signal['signal'])
                confidence_scores.append(0.7 if breakout_signal.get('strength') == 'STRONG' else 0.5)
        
        elif strategy == IntradayStrategy.MEAN_REVERSION:
            mean_reversion_signal = self.mean_reversion_signal(data)
            if 'signal' in mean_reversion_signal:
                signals.append(mean_reversion_signal['signal'])
                confidence_scores.append(0.6)
        
        elif strategy == IntradayStrategy.SCALPING:
            scalping_signal = self.scalping_signal(data)
            if 'signal' in scalping_signal:
                signals.append(scalping_signal['signal'])
                confidence_scores.append(0.5)
        
        elif strategy == IntradayStrategy.GAP_TRADING:
            # Need previous day's close for gap analysis
            previous_close = None
            if len(data) > 20:
                previous_close = data['close'].iloc[-20] if len(data) >= 20 else None
            if previous_close:
                gap_signal = self.gap_trading_signal(data, previous_close=previous_close)
                if 'signal' in gap_signal:
                    signals.append(gap_signal['signal'])
                    confidence_scores.append(0.7 if gap_signal.get('strength') == 'STRONG' else 0.5)
        
        elif strategy == IntradayStrategy.CLOSING_RANGE:
            closing_signal = self.closing_range_breakout(data)
            if 'signal' in closing_signal:
                signals.append(closing_signal['signal'])
                confidence_scores.append(0.7 if closing_signal.get('strength') == 'STRONG' else 0.5)
        
        elif strategy == IntradayStrategy.VOLUME_PROFILE:
            volume_profile_signal = self.volume_profile_signal(data)
            if 'signal' in volume_profile_signal:
                signals.append(volume_profile_signal['signal'])
                confidence_scores.append(0.6)
        
        # Session-based adjustments
        if session == TradingSession.OPENING:
            opening_signal = self.opening_range_breakout(data)
            if 'signal' in opening_signal and opening_signal['signal'] != 'WAIT':
                signals.append(opening_signal['signal'])
                confidence_scores.append(0.8)
        
        if session == TradingSession.CLOSING:
            closing_signal = self.closing_range_breakout(data)
            if 'signal' in closing_signal:
                signals.append(closing_signal['signal'])
                confidence_scores.append(0.7)
        
        # Aggregate signal
        buy_count = signals.count("BUY") + signals.count("STRONG_BUY")
        sell_count = signals.count("SELL") + signals.count("STRONG_SELL")
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        
        # Enhanced ML-based confidence calculation
        # Factors: signal consistency, volume confirmation, volatility, trend strength
        ml_confidence = self._calculate_ml_confidence(
            signals, confidence_scores, data, buy_count, sell_count
        )
        
        # Use ML confidence if available, otherwise use average
        final_confidence = ml_confidence if ml_confidence > 0 else avg_confidence
        
        if buy_count > sell_count:
            final_signal = "BUY"
            strength = "STRONG" if avg_confidence > 0.7 else "MODERATE"
        elif sell_count > buy_count:
            final_signal = "SELL"
            strength = "STRONG" if avg_confidence > 0.7 else "MODERATE"
        else:
            final_signal = "HOLD"
            strength = "WEAK"
        
        # Convert numpy types to Python native types for JSON serialization
        # Confidence is returned as decimal (0.0-1.0), frontend will convert to percentage
        confidence_decimal = to_python_type(avg_confidence)
        
        return {
            "signal": final_signal,
            "strength": strength,
            "confidence": to_python_type(final_confidence),  # ML-enhanced confidence
            "base_confidence": to_python_type(avg_confidence),  # Original average
            "ml_confidence": to_python_type(ml_confidence),  # ML-enhanced value
            "strategy": strategy.value,
            "session": session.value,
            "current_price": to_python_type(data['close'].iloc[-1]),
            "signals": signals,
            "recommendation": self._get_intraday_recommendation(final_signal, strength, session, strategy),
            "message": self._get_intraday_recommendation(final_signal, strength, session, strategy)  # Add message field for frontend compatibility
        }
    
    def _calculate_ml_confidence(
        self,
        signals: List[str],
        confidence_scores: List[float],
        data: pd.DataFrame,
        buy_count: int,
        sell_count: int
    ) -> float:
        """
        ML-based confidence calculation
        Uses multiple factors to enhance confidence score
        """
        try:
            if not signals or not confidence_scores or data.empty:
                return 0.5
            
            base_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
            
            # Factor 1: Signal consistency (higher if all signals agree)
            signal_consistency = 1.0 - (abs(buy_count - sell_count) / max(len(signals), 1))
            
            # Factor 2: Volume confirmation (if volume data available)
            volume_factor = 1.0
            if 'volume' in data.columns and len(data) > 5:
                current_volume = data['volume'].iloc[-1]
                avg_volume = data['volume'].tail(20).mean() if len(data) >= 20 else data['volume'].mean()
                if avg_volume > 0:
                    volume_ratio = current_volume / avg_volume
                    # Higher volume = higher confidence (capped at 1.2x)
                    volume_factor = min(1.0 + (volume_ratio - 1.0) * 0.2, 1.2)
            
            # Factor 3: Volatility (lower volatility = higher confidence in mean reversion, higher volatility = higher confidence in momentum)
            volatility_factor = 1.0
            if len(data) > 10:
                returns = data['close'].pct_change().dropna()
                volatility = returns.std()
                # Normalize volatility (assume 0.01-0.05 range is normal)
                normalized_vol = min(max(volatility, 0.01), 0.05) / 0.05
                volatility_factor = 0.9 + (normalized_vol * 0.1)  # Slight boost for moderate volatility
            
            # Factor 4: Trend strength (stronger trends = higher confidence)
            trend_factor = 1.0
            if len(data) > 20:
                short_ma = data['close'].tail(5).mean()
                long_ma = data['close'].tail(20).mean()
                if long_ma > 0:
                    trend_strength = abs((short_ma - long_ma) / long_ma)
                    trend_factor = 1.0 + min(trend_strength * 2, 0.2)  # Up to 20% boost
            
            # Combine factors
            ml_confidence = base_confidence * signal_consistency * volume_factor * volatility_factor * trend_factor
            
            # Normalize to 0.0-1.0 range
            ml_confidence = max(0.0, min(1.0, ml_confidence))
            
            return float(ml_confidence)
        except Exception as e:
            logger.warning(f"Error calculating ML confidence: {e}")
            return 0.5  # Fallback to base confidence
    
    async def news_based_signal(
        self,
        symbol: str,
        news_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        News-based Trading Signal
        Analyzes news sentiment to generate trading signals
        """
        try:
            # If news_data not provided, try to fetch
            if news_data is None:
                try:
                    from services.intelligent_stock_selector import IntelligentStockSelector
                    selector = IntelligentStockSelector()
                    # Try to get news for symbol
                    news_data = await selector._fetch_yahoo_finance_news(symbol)
                except Exception as e:
                    logger.warning(f"Could not fetch news for {symbol}: {e}")
                    news_data = []
            
            if not news_data or len(news_data) == 0:
                return {
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "No recent news available for analysis",
                    "sentiment_score": 0.0,
                    "news_count": 0
                }
            
            # Calculate sentiment from news
            sentiment_scores = []
            high_impact_count = 0
            
            for news_item in news_data[:10]:  # Analyze top 10 news items
                # Extract sentiment
                sentiment = news_item.get('sentiment_score', 0.0)
                if isinstance(sentiment, (int, float)):
                    sentiment_scores.append(float(sentiment))
                
                # Check for high-impact keywords
                title = news_item.get('title', '').lower()
                description = news_item.get('description', '').lower()
                text = title + ' ' + description
                
                high_impact_keywords = ['earnings', 'ipo', 'merger', 'acquisition', 'regulatory', 'fda approval', 'breakthrough']
                if any(keyword in text for keyword in high_impact_keywords):
                    high_impact_count += 1
            
            if not sentiment_scores:
                return {
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "News available but sentiment could not be calculated",
                    "sentiment_score": 0.0,
                    "news_count": len(news_data)
                }
            
            avg_sentiment = np.mean(sentiment_scores)
            
            # Generate signal based on sentiment
            if avg_sentiment > 0.3 and high_impact_count > 0:
                signal = "BUY"
                strength = "STRONG"
                reason = f"Strong positive news sentiment ({avg_sentiment:.2f}) with {high_impact_count} high-impact news items"
            elif avg_sentiment > 0.1:
                signal = "BUY"
                strength = "MODERATE"
                reason = f"Positive news sentiment ({avg_sentiment:.2f})"
            elif avg_sentiment < -0.3 and high_impact_count > 0:
                signal = "SELL"
                strength = "STRONG"
                reason = f"Strong negative news sentiment ({avg_sentiment:.2f}) with {high_impact_count} high-impact news items"
            elif avg_sentiment < -0.1:
                signal = "SELL"
                strength = "MODERATE"
                reason = f"Negative news sentiment ({avg_sentiment:.2f})"
            else:
                signal = "HOLD"
                strength = "WEAK"
                reason = f"Neutral news sentiment ({avg_sentiment:.2f})"
            
            return {
                "signal": signal,
                "strength": strength,
                "sentiment_score": float(avg_sentiment),
                "news_count": len(news_data),
                "high_impact_count": high_impact_count,
                "reason": reason
            }
        except Exception as e:
            logger.error(f"Error generating news-based signal: {e}")
            return {
                "signal": "HOLD",
                "strength": "WEAK",
                "reason": f"Error analyzing news: {str(e)}",
                "sentiment_score": 0.0,
                "news_count": 0
            }
    
    def sma_trading_signal(
        self,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        SMA Trading Signal
        Analyzes price position relative to SMA20, SMA50, SMA200
        Detects Golden Cross, Death Cross, and Multi-MA alignment
        """
        try:
            if len(data) < 20:
                return {
                    "error": "Insufficient data for SMA analysis",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "Need at least 20 candles for SMA20 calculation"
                }
            
            current_price = to_python_type(data['close'].iloc[-1])
            closes = data['close'].tolist()
            
            # Calculate SMAs
            sma20 = to_python_type(data['close'].tail(20).mean()) if len(data) >= 20 else None
            sma50 = to_python_type(data['close'].tail(50).mean()) if len(data) >= 50 else None
            sma200 = to_python_type(data['close'].tail(200).mean()) if len(data) >= 200 else (
                to_python_type(data['close'].mean()) if len(data) >= 100 else None
            )
            
            # Calculate price vs SMA percentages
            price_vs_sma20 = ((current_price - sma20) / sma20) * 100 if sma20 else None
            price_vs_sma50 = ((current_price - sma50) / sma50) * 100 if sma50 else None
            price_vs_sma200 = ((current_price - sma200) / sma200) * 100 if sma200 else None
            
            # Detect Golden Cross / Death Cross
            golden_cross = False
            death_cross = False
            
            if sma50 is not None and sma200 is not None:
                # Calculate previous period SMAs for crossover detection
                if len(data) >= 51:
                    previous_sma50 = to_python_type(data['close'].tail(51).head(50).mean())
                else:
                    previous_sma50 = sma50
                
                if len(data) >= 201:
                    previous_sma200 = to_python_type(data['close'].tail(201).head(200).mean())
                else:
                    previous_sma200 = sma200
                
                # Golden Cross: SMA50 crosses above SMA200
                golden_cross = sma50 > sma200 and previous_sma50 <= previous_sma200
                # Death Cross: SMA50 crosses below SMA200
                death_cross = sma50 < sma200 and previous_sma50 >= previous_sma200
            
            # Detect Multi-MA Alignment
            alignment_type = 'none'
            multi_ma_alignment = ''
            
            if sma20 is not None and sma50 is not None and sma200 is not None:
                if current_price > sma20 and sma20 > sma50 and sma50 > sma200:
                    alignment_type = 'perfect_bullish'
                    multi_ma_alignment = 'Perfect Bullish: Price > SMA20 > SMA50 > SMA200'
                elif current_price < sma20 and sma20 < sma50 and sma50 < sma200:
                    alignment_type = 'perfect_bearish'
                    multi_ma_alignment = 'Perfect Bearish: Price < SMA20 < SMA50 < SMA200'
                elif current_price > sma20 and sma20 > sma50:
                    alignment_type = 'partial_bullish'
                    multi_ma_alignment = 'Bullish: Price > SMA20 > SMA50'
                elif current_price < sma20 and sma20 < sma50:
                    alignment_type = 'partial_bearish'
                    multi_ma_alignment = 'Bearish: Price < SMA20 < SMA50'
            
            # Determine overall signal
            signal = 'HOLD'
            strength = 'WEAK'
            confidence = 50
            reason = 'Price near moving averages - Wait for clearer trend'
            
            if golden_cross:
                signal = 'BUY'
                strength = 'STRONG'
                confidence = 85
                reason = 'Golden Cross detected! SMA50 crossed above SMA200 - Strong bullish signal'
            elif death_cross:
                signal = 'SELL'
                strength = 'STRONG'
                confidence = 85
                reason = 'Death Cross detected! SMA50 crossed below SMA200 - Strong bearish signal'
            elif alignment_type == 'perfect_bullish':
                signal = 'BUY'
                strength = 'STRONG'
                confidence = 90
                reason = 'Perfect bullish alignment: Price > SMA20 > SMA50 > SMA200 - Very strong buy signal'
            elif alignment_type == 'perfect_bearish':
                signal = 'SELL'
                strength = 'STRONG'
                confidence = 90
                reason = 'Perfect bearish alignment: Price < SMA20 < SMA50 < SMA200 - Very strong sell signal'
            elif alignment_type == 'partial_bullish':
                signal = 'BUY'
                strength = 'MODERATE'
                confidence = 75
                reason = 'Bullish alignment: Price > SMA20 > SMA50 - Strong buy signal'
            elif alignment_type == 'partial_bearish':
                signal = 'SELL'
                strength = 'MODERATE'
                confidence = 75
                reason = 'Bearish alignment: Price < SMA20 < SMA50 - Strong sell signal'
            elif sma200 is not None:
                if current_price > sma200 * 1.05:
                    signal = 'BUY'
                    strength = 'STRONG'
                    confidence = 75
                    reason = f'Price significantly above SMA200 (+{price_vs_sma200:.2f}%) - Strong long-term uptrend'
                elif current_price > sma200:
                    signal = 'BUY'
                    strength = 'MODERATE'
                    confidence = 70
                    reason = f'Price above SMA200 (+{price_vs_sma200:.2f}%) - Long-term uptrend'
                elif current_price < sma200 * 0.95:
                    signal = 'SELL'
                    strength = 'STRONG'
                    confidence = 75
                    reason = f'Price significantly below SMA200 ({price_vs_sma200:.2f}%) - Strong long-term downtrend'
                elif current_price < sma200 * 0.98:
                    # Neutral zone: price between 95% and 98% of SMA200 - weak bearish but not strong enough for SELL
                    signal = 'HOLD'
                    strength = 'WEAK'
                    confidence = 55
                    reason = f'Price near SMA200 ({price_vs_sma200:.2f}%) - Wait for clearer direction'
                else:
                    # Price between 98% and 100% of SMA200 - very close, should be HOLD
                    signal = 'HOLD'
                    strength = 'WEAK'
                    confidence = 50
                    reason = f'Price very close to SMA200 ({price_vs_sma200:.2f}%) - Neutral zone, wait for breakout'
            elif sma50 is not None:
                if current_price > sma50 * 1.03:
                    signal = 'BUY'
                    strength = 'MODERATE'
                    confidence = 65
                    reason = f'Price significantly above SMA50 (+{price_vs_sma50:.2f}%) - Medium-term uptrend'
                elif current_price > sma50:
                    signal = 'BUY'
                    strength = 'WEAK'
                    confidence = 60
                    reason = f'Price above SMA50 (+{price_vs_sma50:.2f}%) - Medium-term uptrend'
                elif current_price < sma50 * 0.97:
                    signal = 'SELL'
                    strength = 'MODERATE'
                    confidence = 65
                    reason = f'Price significantly below SMA50 ({price_vs_sma50:.2f}%) - Medium-term downtrend'
                elif current_price < sma50 * 0.99:
                    # Neutral zone: price between 97% and 99% of SMA50 - weak bearish but not strong enough for SELL
                    signal = 'HOLD'
                    strength = 'WEAK'
                    confidence = 55
                    reason = f'Price near SMA50 ({price_vs_sma50:.2f}%) - Wait for clearer direction'
                else:
                    # Price between 99% and 100% of SMA50 - very close, should be HOLD
                    signal = 'HOLD'
                    strength = 'WEAK'
                    confidence = 50
                    reason = f'Price very close to SMA50 ({price_vs_sma50:.2f}%) - Neutral zone, wait for breakout'
            elif sma20 is not None:
                if current_price > sma20 * 1.02:
                    signal = 'BUY'
                    strength = 'WEAK'
                    confidence = 60
                    reason = f'Price above SMA20 (+{price_vs_sma20:.2f}%) - Short-term bullish'
                elif current_price < sma20 * 0.98:
                    signal = 'SELL'
                    strength = 'WEAK'
                    confidence = 60
                    reason = f'Price below SMA20 ({price_vs_sma20:.2f}%) - Short-term bearish'
            
            return {
                "signal": signal,
                "strength": strength,
                "current_price": to_python_type(current_price),
                "sma20": to_python_type(sma20) if sma20 else None,
                "sma50": to_python_type(sma50) if sma50 else None,
                "sma200": to_python_type(sma200) if sma200 else None,
                "price_vs_sma20": to_python_type(price_vs_sma20) if price_vs_sma20 is not None else None,
                "price_vs_sma50": to_python_type(price_vs_sma50) if price_vs_sma50 is not None else None,
                "price_vs_sma200": to_python_type(price_vs_sma200) if price_vs_sma200 is not None else None,
                "golden_cross": golden_cross,
                "death_cross": death_cross,
                "multi_ma_alignment": multi_ma_alignment if multi_ma_alignment else None,
                "alignment_type": alignment_type,
                "reason": reason,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating SMA trading signal: {e}")
            return {
                "error": str(e),
                "signal": "HOLD",
                "strength": "WEAK",
                "reason": f"Error calculating SMA signal: {str(e)}"
            }
    
    def macd_trading_signal(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, Any]:
        """
        MACD Trading Signal
        Uses MACD line, signal line, and histogram for trading signals
        """
        try:
            if not TA_AVAILABLE:
                return {
                    "error": "pandas_ta library not available",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "MACD calculation requires pandas_ta library"
                }
            
            if len(data) < slow_period + signal_period:
                return {
                    "error": "Insufficient data for MACD analysis",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": f"Need at least {slow_period + signal_period} candles for MACD calculation"
                }
            
            current_price = to_python_type(data['close'].iloc[-1])
            
            # Calculate MACD using pandas_ta
            macd_line = ta.trend.macd(data['close'], window_slow=slow_period, window_fast=fast_period)
            macd_signal = ta.trend.macd_signal(data['close'], window_slow=slow_period, window_fast=fast_period, window_sign=signal_period)
            macd_histogram = ta.trend.macd_diff(data['close'], window_slow=slow_period, window_fast=fast_period, window_sign=signal_period)
            
            # Get current values
            current_macd = to_python_type(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
            current_signal = to_python_type(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else None
            current_histogram = to_python_type(macd_histogram.iloc[-1]) if not pd.isna(macd_histogram.iloc[-1]) else None
            
            # Get previous values for crossover detection
            prev_macd = to_python_type(macd_line.iloc[-2]) if len(macd_line) >= 2 and not pd.isna(macd_line.iloc[-2]) else None
            prev_signal = to_python_type(macd_signal.iloc[-2]) if len(macd_signal) >= 2 and not pd.isna(macd_signal.iloc[-2]) else None
            prev_histogram = to_python_type(macd_histogram.iloc[-2]) if len(macd_histogram) >= 2 and not pd.isna(macd_histogram.iloc[-2]) else None
            
            if current_macd is None or current_signal is None or current_histogram is None:
                return {
                    "error": "MACD calculation failed",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "Unable to calculate MACD values"
                }
            
            # Detect MACD crossovers
            bullish_crossover = False
            bearish_crossover = False
            
            if prev_macd is not None and prev_signal is not None:
                # Bullish crossover: MACD crosses above signal line
                bullish_crossover = current_macd > current_signal and prev_macd <= prev_signal
                # Bearish crossover: MACD crosses below signal line
                bearish_crossover = current_macd < current_signal and prev_macd >= prev_signal
            
            # Determine signal based on MACD analysis
            signal = 'HOLD'
            strength = 'WEAK'
            confidence = 50
            reason = 'MACD neutral - Wait for clearer signal'
            
            if bullish_crossover:
                signal = 'BUY'
                strength = 'STRONG'
                confidence = 80
                reason = 'MACD bullish crossover detected! MACD crossed above signal line - Strong buy signal'
            elif bearish_crossover:
                signal = 'SELL'
                strength = 'STRONG'
                confidence = 80
                reason = 'MACD bearish crossover detected! MACD crossed below signal line - Strong sell signal'
            elif current_histogram > 0 and prev_histogram is not None and prev_histogram < 0:
                # Histogram turning positive
                signal = 'BUY'
                strength = 'MODERATE'
                confidence = 70
                reason = 'MACD histogram turning positive - Momentum building upward'
            elif current_histogram < 0 and prev_histogram is not None and prev_histogram > 0:
                # Histogram turning negative
                signal = 'SELL'
                strength = 'MODERATE'
                confidence = 70
                reason = 'MACD histogram turning negative - Momentum building downward'
            elif current_macd > current_signal and current_histogram > 0:
                # MACD above signal and histogram positive
                signal = 'BUY'
                strength = 'MODERATE'
                confidence = 65
                reason = 'MACD above signal line with positive histogram - Bullish momentum'
            elif current_macd < current_signal and current_histogram < 0:
                # MACD below signal and histogram negative
                signal = 'SELL'
                strength = 'MODERATE'
                confidence = 65
                reason = 'MACD below signal line with negative histogram - Bearish momentum'
            elif current_macd > 0 and current_signal > 0:
                # Both MACD and signal above zero line
                signal = 'BUY'
                strength = 'WEAK'
                confidence = 60
                reason = 'MACD and signal both above zero - Bullish trend'
            elif current_macd < 0 and current_signal < 0:
                # Both MACD and signal below zero line
                signal = 'SELL'
                strength = 'WEAK'
                confidence = 60
                reason = 'MACD and signal both below zero - Bearish trend'
            
            # Calculate entry, stop loss, and target
            entry_price = current_price
            stop_loss = None
            target_price = None
            
            if signal == 'BUY':
                # Stop loss: 1% below entry
                stop_loss = to_python_type(current_price * 0.99)
                # Target: 2% above entry (2:1 risk-reward)
                target_price = to_python_type(current_price * 1.02)
            elif signal == 'SELL':
                # Stop loss: 1% above entry
                stop_loss = to_python_type(current_price * 1.01)
                # Target: 2% below entry (2:1 risk-reward)
                target_price = to_python_type(current_price * 0.98)
            
            return {
                "signal": signal,
                "strength": strength,
                "current_price": to_python_type(current_price),
                "macd_line": to_python_type(current_macd),
                "macd_signal": to_python_type(current_signal),
                "macd_histogram": to_python_type(current_histogram),
                "bullish_crossover": bullish_crossover,
                "bearish_crossover": bearish_crossover,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "target_price": target_price,
                "reason": reason,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD trading signal: {e}")
            return {
                "error": str(e),
                "signal": "HOLD",
                "strength": "WEAK",
                "reason": f"Error calculating MACD signal: {str(e)}"
            }
    
    def bollinger_bands_trading_signal(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, Any]:
        """
        Bollinger Bands Trading Signal
        Uses Bollinger Bands for volatility-based trading signals
        """
        try:
            if not TA_AVAILABLE:
                return {
                    "error": "pandas_ta library not available",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "Bollinger Bands calculation requires pandas_ta library"
                }
            
            if len(data) < period:
                return {
                    "error": "Insufficient data for Bollinger Bands analysis",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": f"Need at least {period} candles for Bollinger Bands calculation"
                }
            
            current_price = to_python_type(data['close'].iloc[-1])
            
            # Calculate Bollinger Bands using pandas_ta
            bb_upper = ta.volatility.bollinger_hband(data['close'], window=period, window_dev=std_dev)
            bb_middle = ta.volatility.bollinger_mavg(data['close'], window=period)
            bb_lower = ta.volatility.bollinger_lband(data['close'], window=period, window_dev=std_dev)
            
            # Get current values
            current_upper = to_python_type(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
            current_middle = to_python_type(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None
            current_lower = to_python_type(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
            
            # Get previous values for comparison
            prev_price = to_python_type(data['close'].iloc[-2]) if len(data) >= 2 else None
            prev_upper = to_python_type(bb_upper.iloc[-2]) if len(bb_upper) >= 2 and not pd.isna(bb_upper.iloc[-2]) else None
            prev_lower = to_python_type(bb_lower.iloc[-2]) if len(bb_lower) >= 2 and not pd.isna(bb_lower.iloc[-2]) else None
            
            if current_upper is None or current_middle is None or current_lower is None:
                return {
                    "error": "Bollinger Bands calculation failed",
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "reason": "Unable to calculate Bollinger Bands values"
                }
            
            # Calculate band width (volatility measure)
            band_width = ((current_upper - current_lower) / current_middle) * 100 if current_middle > 0 else 0
            
            # Calculate %B (position within bands)
            percent_b = ((current_price - current_lower) / (current_upper - current_lower)) * 100 if (current_upper - current_lower) > 0 else 50
            
            # Determine signal based on Bollinger Bands analysis
            signal = 'HOLD'
            strength = 'WEAK'
            confidence = 50
            reason = 'Price within Bollinger Bands - Neutral position'
            
            # Check for squeeze (low volatility - potential breakout)
            is_squeeze = band_width < 2.0  # Band width less than 2% indicates squeeze
            
            # Check for expansion (high volatility)
            is_expansion = band_width > 5.0  # Band width greater than 5% indicates expansion
            
            # Price touching or breaking bands
            price_touching_upper = current_price >= current_upper * 0.995  # Within 0.5% of upper band
            price_touching_lower = current_price <= current_lower * 1.005  # Within 0.5% of lower band
            
            # Price breaking above upper band
            if current_price > current_upper:
                signal = 'SELL'  # Mean reversion: price too high, expect pullback
                strength = 'MODERATE'
                confidence = 70
                reason = f'Price broke above upper Bollinger Band (₹{current_upper:.2f}) - Overbought, expect mean reversion'
            # Price breaking below lower band
            elif current_price < current_lower:
                signal = 'BUY'  # Mean reversion: price too low, expect bounce
                strength = 'MODERATE'
                confidence = 70
                reason = f'Price broke below lower Bollinger Band (₹{current_lower:.2f}) - Oversold, expect mean reversion'
            # Price touching upper band
            elif price_touching_upper:
                signal = 'SELL'
                strength = 'WEAK'
                confidence = 60
                reason = f'Price touching upper Bollinger Band (₹{current_upper:.2f}) - Potential resistance'
            # Price touching lower band
            elif price_touching_lower:
                signal = 'BUY'
                strength = 'WEAK'
                confidence = 60
                reason = f'Price touching lower Bollinger Band (₹{current_lower:.2f}) - Potential support'
            # Price above middle band (bullish)
            elif current_price > current_middle:
                signal = 'BUY'
                strength = 'WEAK'
                confidence = 55
                reason = f'Price above middle band (₹{current_middle:.2f}) - Mild bullish bias'
            # Price below middle band (bearish)
            elif current_price < current_middle:
                signal = 'SELL'
                strength = 'WEAK'
                confidence = 55
                reason = f'Price below middle band (₹{current_middle:.2f}) - Mild bearish bias'
            
            # Adjust for squeeze (potential breakout)
            if is_squeeze and signal == 'HOLD':
                reason += ' - Bollinger Squeeze detected (low volatility), watch for breakout'
                confidence = 50
            
            # Calculate entry, stop loss, and target
            entry_price = current_price
            stop_loss = None
            target_price = None
            
            if signal == 'BUY':
                # Stop loss: just below lower band or 1.5% below entry
                stop_loss = to_python_type(min(current_lower * 0.99, current_price * 0.985))
                # Target: middle band or 2% above entry
                target_price = to_python_type(max(current_middle, current_price * 1.02))
            elif signal == 'SELL':
                # Stop loss: just above upper band or 1.5% above entry
                stop_loss = to_python_type(max(current_upper * 1.01, current_price * 1.015))
                # Target: middle band or 2% below entry
                target_price = to_python_type(min(current_middle, current_price * 0.98))
            
            return {
                "signal": signal,
                "strength": strength,
                "current_price": to_python_type(current_price),
                "bb_upper": to_python_type(current_upper),
                "bb_middle": to_python_type(current_middle),
                "bb_lower": to_python_type(current_lower),
                "band_width": to_python_type(band_width),
                "percent_b": to_python_type(percent_b),
                "is_squeeze": is_squeeze,
                "is_expansion": is_expansion,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "target_price": target_price,
                "reason": reason,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands trading signal: {e}")
            return {
                "error": str(e),
                "signal": "HOLD",
                "strength": "WEAK",
                "reason": f"Error calculating Bollinger Bands signal: {str(e)}"
            }
    
    def _get_intraday_recommendation(
        self,
        signal: str,
        strength: str,
        session: TradingSession,
        strategy: IntradayStrategy
    ) -> str:
        """Get human-readable intraday recommendation"""
        session_name = session.value.replace("_", " ").title()
        strategy_name = strategy.value.replace("_", " ").title()
        
        if signal == "BUY" and strength == "STRONG":
            return f"Strong {strategy_name} buy signal in {session_name} session. Consider entering long position with tight stop-loss."
        elif signal == "BUY":
            return f"Moderate {strategy_name} buy signal in {session_name} session. Enter with caution and proper risk management."
        elif signal == "SELL" and strength == "STRONG":
            return f"Strong {strategy_name} sell signal in {session_name} session. Consider entering short position with tight stop-loss."
        elif signal == "SELL":
            return f"Moderate {strategy_name} sell signal in {session_name} session. Enter with caution and proper risk management."
        else:
            return f"Neutral signal in {session_name} session. Wait for clearer direction or consider exiting existing positions."

