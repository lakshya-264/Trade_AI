"""
Technical analysis service
"""
from typing import Dict, Any, List
import numpy as np

class TechnicalAnalyzer:
    def __init__(self):
        pass
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD"""
        if len(prices) < 26:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)
        macd = ema12 - ema26
        
        return {
            "macd": macd,
            "signal": macd,  # Simplified
            "histogram": macd
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def analyze_trend(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze trend"""
        if len(prices) < 2:
            return {"trend": "neutral", "strength": 0.0}
        
        recent_prices = prices[-10:] if len(prices) >= 10 else prices
        trend_slope = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        
        if trend_slope > 0.1:
            trend = "bullish"
        elif trend_slope < -0.1:
            trend = "bearish"
        else:
            trend = "neutral"
        
        return {
            "trend": trend,
            "strength": abs(trend_slope),
            "slope": trend_slope
        }
