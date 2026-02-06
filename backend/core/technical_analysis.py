"""
Technical Analysis Service
Provides RSI, MACD, SMA, Bollinger Bands, and other technical indicators
"""

import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    """Technical analysis calculations for trading signals"""
    
    def calculate_rsi(self, data: List[Dict], period: int = 14) -> float:
        """Calculate Relative Strength Index (RSI)"""
        try:
            if len(data) < period + 1:
                return 50.0  # Neutral RSI if insufficient data
            
            closes = [float(d.get('close', 0)) for d in data[-period-1:]]
            if len(closes) < 2:
                return 50.0
            
            # Calculate price changes
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            
            # Separate gains and losses
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            # Calculate average gains and losses
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(losses)
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception as e:
            logger.error(f"RSI calculation error: {e}")
            return 50.0
    
    def calculate_macd(self, data: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(data) < slow + signal:
                return {"macd": 0, "signal": 0, "histogram": 0}
            
            closes = [float(d.get('close', 0)) for d in data]
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(closes, fast)
            ema_slow = self._calculate_ema(closes, slow)
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line (EMA of MACD)
            macd_values = [macd_line]  # Simplified - would need full MACD history
            signal_line = self._calculate_ema(macd_values, signal)
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                "macd": round(macd_line, 4),
                "signal": round(signal_line, 4),
                "histogram": round(histogram, 4)
            }
            
        except Exception as e:
            logger.error(f"MACD calculation error: {e}")
            return {"macd": 0, "signal": 0, "histogram": 0}
    
    def calculate_sma(self, data: List[Dict], period: int) -> float:
        """Calculate Simple Moving Average (SMA)"""
        try:
            if len(data) < period:
                return float(data[-1].get('close', 0)) if data else 0.0
            
            closes = [float(d.get('close', 0)) for d in data[-period:]]
            return round(sum(closes) / len(closes), 2)
            
        except Exception as e:
            logger.error(f"SMA calculation error: {e}")
            return 0.0
    
    def calculate_bollinger_bands(self, data: List[Dict], period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        try:
            if len(data) < period:
                current_price = float(data[-1].get('close', 0)) if data else 0.0
                return {"upper": current_price, "middle": current_price, "lower": current_price}
            
            closes = [float(d.get('close', 0)) for d in data[-period:]]
            sma = sum(closes) / len(closes)
            
            # Calculate standard deviation
            variance = sum((x - sma) ** 2 for x in closes) / len(closes)
            std = np.sqrt(variance)
            
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            
            return {
                "upper": round(upper_band, 2),
                "middle": round(sma, 2),
                "lower": round(lower_band, 2)
            }
            
        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {e}")
            return {"upper": 0, "middle": 0, "lower": 0}
    
    def analyze_volume_trend(self, data: List[Dict], period: int = 10) -> Dict[str, Any]:
        """Analyze volume trends"""
        try:
            if len(data) < period:
                return {"trend": "neutral", "ratio": 1.0}
            
            volumes = [float(d.get('volume', 0)) for d in data[-period:]]
            recent_avg = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else volumes[-1]
            older_avg = sum(volumes[:-5]) / (len(volumes) - 5) if len(volumes) > 5 else recent_avg
            
            ratio = recent_avg / older_avg if older_avg > 0 else 1.0
            
            if ratio > 1.2:
                trend = "increasing"
            elif ratio < 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "ratio": round(ratio, 2),
                "recent_avg": round(recent_avg, 0),
                "older_avg": round(older_avg, 0)
            }
            
        except Exception as e:
            logger.error(f"Volume trend analysis error: {e}")
            return {"trend": "neutral", "ratio": 1.0}
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average (EMA)"""
        try:
            if not prices:
                return 0.0
            
            multiplier = 2 / (period + 1)
            ema = prices[0]  # Start with first price
            
            for price in prices[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
            
        except Exception as e:
            logger.error(f"EMA calculation error: {e}")
            return prices[-1] if prices else 0.0
    
    def get_support_resistance(self, data: List[Dict], lookback: int = 20) -> Dict[str, float]:
        """Identify support and resistance levels"""
        try:
            if len(data) < lookback:
                current_price = float(data[-1].get('close', 0)) if data else 0.0
                return {"support": current_price * 0.95, "resistance": current_price * 1.05}
            
            recent_data = data[-lookback:]
            highs = [float(d.get('high', 0)) for d in recent_data]
            lows = [float(d.get('low', 0)) for d in recent_data]
            
            # Simple support/resistance calculation
            resistance = max(highs)
            support = min(lows)
            
            return {
                "support": round(support, 2),
                "resistance": round(resistance, 2)
            }
            
        except Exception as e:
            logger.error(f"Support/Resistance calculation error: {e}")
            return {"support": 0, "resistance": 0}
    
    def calculate_momentum(self, data: List[Dict], period: int = 10) -> float:
        """Calculate price momentum"""
        try:
            if len(data) < period + 1:
                return 0.0
            
            current_price = float(data[-1].get('close', 0))
            past_price = float(data[-period-1].get('close', 0))
            
            momentum = ((current_price - past_price) / past_price) * 100
            return round(momentum, 2)
            
        except Exception as e:
            logger.error(f"Momentum calculation error: {e}")
            return 0.0
