"""
Central Pivot Range (CPR) Service
Technical analysis tool for intraday trading
Based on Zerodha Varsity Chapter 22
"""
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class CentralPivotRangeService:
    """Calculate and analyze Central Pivot Range for trading"""
    
    def __init__(self):
        self.default_lookback = 20  # Default lookback period
    
    def calculate_cpr(
        self,
        high: float,
        low: float,
        close: float,
        previous_high: Optional[float] = None,
        previous_low: Optional[float] = None,
        previous_close: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate Central Pivot Range (CPR) for a single day
        
        CPR is calculated using:
        - Pivot Point (PP) = (High + Low + Close) / 3
        - Top Central Pivot (TC) = (High + Low) / 2
        - Bottom Central Pivot (BC) = (PP + TC) / 2
        
        Args:
            high: Today's high price
            low: Today's low price
            close: Today's close price
            previous_high: Previous day's high (for trend analysis)
            previous_low: Previous day's low (for trend analysis)
            previous_close: Previous day's close (for trend analysis)
        
        Returns:
            Dictionary with CPR levels and analysis
        """
        try:
            # Calculate Pivot Point
            pivot_point = (high + low + close) / 3
            
            # Calculate Top Central Pivot
            top_cpr = (high + low) / 2
            
            # Calculate Bottom Central Pivot
            bottom_cpr = (pivot_point + top_cpr) / 2
            
            # Calculate CPR width (narrow vs wide)
            cpr_width = top_cpr - bottom_cpr
            cpr_width_percent = (cpr_width / pivot_point) * 100 if pivot_point > 0 else 0
            
            # Determine CPR type
            if cpr_width_percent < 0.5:
                cpr_type = "Narrow CPR"
                cpr_significance = "High - Indicates consolidation, potential breakout"
            elif cpr_width_percent < 1.0:
                cpr_type = "Normal CPR"
                cpr_significance = "Medium - Normal market conditions"
            else:
                cpr_type = "Wide CPR"
                cpr_significance = "Low - High volatility, less reliable"
            
            # Calculate support and resistance levels
            resistance_1 = 2 * pivot_point - low
            resistance_2 = pivot_point + (high - low)
            support_1 = 2 * pivot_point - high
            support_2 = pivot_point - (high - low)
            
            result = {
                "pivot_point": round(pivot_point, 2),
                "top_cpr": round(top_cpr, 2),
                "bottom_cpr": round(bottom_cpr, 2),
                "cpr_width": round(cpr_width, 2),
                "cpr_width_percent": round(cpr_width_percent, 2),
                "cpr_type": cpr_type,
                "cpr_significance": cpr_significance,
                "resistance_levels": {
                    "r2": round(resistance_2, 2),
                    "r1": round(resistance_1, 2),
                    "tc": round(top_cpr, 2)
                },
                "support_levels": {
                    "bc": round(bottom_cpr, 2),
                    "s1": round(support_1, 2),
                    "s2": round(support_2, 2)
                },
                "current_price": round(close, 2),
                "price_position": self._determine_price_position(close, top_cpr, bottom_cpr, pivot_point)
            }
            
            # Add trend analysis if previous day data available
            if previous_high and previous_low and previous_close:
                prev_cpr = self.calculate_cpr(previous_high, previous_low, previous_close)
                result["trend_analysis"] = self._analyze_cpr_trend(
                    result, prev_cpr, close, previous_close
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating CPR: {e}")
            return {"error": str(e)}
    
    def _determine_price_position(
        self,
        price: float,
        top_cpr: float,
        bottom_cpr: float,
        pivot: float
    ) -> Dict[str, Any]:
        """Determine where current price is relative to CPR"""
        if price > top_cpr:
            position = "Above Top CPR"
            bias = "Bullish"
            strength = "Strong"
        elif price > pivot:
            position = "Between Top CPR and Pivot"
            bias = "Bullish"
            strength = "Moderate"
        elif price > bottom_cpr:
            position = "Between Pivot and Bottom CPR"
            bias = "Neutral to Bearish"
            strength = "Moderate"
        else:
            position = "Below Bottom CPR"
            bias = "Bearish"
            strength = "Strong"
        
        return {
            "position": position,
            "bias": bias,
            "strength": strength,
            "distance_from_pivot": round(((price - pivot) / pivot) * 100, 2) if pivot > 0 else 0
        }
    
    def _analyze_cpr_trend(
        self,
        current_cpr: Dict[str, Any],
        previous_cpr: Dict[str, Any],
        current_price: float,
        previous_price: float
    ) -> Dict[str, Any]:
        """Analyze CPR trend and price movement"""
        # CPR trend
        current_pivot = current_cpr["pivot_point"]
        previous_pivot = previous_cpr["pivot_point"]
        
        if current_pivot > previous_pivot:
            cpr_trend = "Rising CPR"
            cpr_bias = "Bullish"
        elif current_pivot < previous_pivot:
            cpr_trend = "Falling CPR"
            cpr_bias = "Bearish"
        else:
            cpr_trend = "Neutral CPR"
            cpr_bias = "Neutral"
        
        # Price trend
        price_change = current_price - previous_price
        price_change_percent = (price_change / previous_price) * 100 if previous_price > 0 else 0
        
        # Alignment
        if cpr_bias == "Bullish" and price_change > 0:
            alignment = "Aligned - Both CPR and price moving up"
            signal_strength = "Strong"
        elif cpr_bias == "Bearish" and price_change < 0:
            alignment = "Aligned - Both CPR and price moving down"
            signal_strength = "Strong"
        else:
            alignment = "Divergence - CPR and price moving in opposite directions"
            signal_strength = "Weak"
        
        return {
            "cpr_trend": cpr_trend,
            "cpr_bias": cpr_bias,
            "price_change": round(price_change, 2),
            "price_change_percent": round(price_change_percent, 2),
            "alignment": alignment,
            "signal_strength": signal_strength
        }
    
    def calculate_cpr_for_dataframe(
        self,
        df: pd.DataFrame,
        high_col: str = "high",
        low_col: str = "low",
        close_col: str = "close"
    ) -> pd.DataFrame:
        """
        Calculate CPR for entire DataFrame
        
        Args:
            df: DataFrame with OHLC data
            high_col: Column name for high prices
            low_col: Column name for low prices
            close_col: Column name for close prices
        
        Returns:
            DataFrame with CPR columns added
        """
        try:
            result_df = df.copy()
            
            # Calculate CPR for each row
            cpr_data = []
            for i in range(len(df)):
                high = df.iloc[i][high_col]
                low = df.iloc[i][low_col]
                close = df.iloc[i][close_col]
                
                # Get previous day data if available
                prev_high = df.iloc[i-1][high_col] if i > 0 else None
                prev_low = df.iloc[i-1][low_col] if i > 0 else None
                prev_close = df.iloc[i-1][close_col] if i > 0 else None
                
                cpr = self.calculate_cpr(high, low, close, prev_high, prev_low, prev_close)
                cpr_data.append(cpr)
            
            # Add CPR columns to DataFrame
            result_df["pivot_point"] = [c["pivot_point"] for c in cpr_data]
            result_df["top_cpr"] = [c["top_cpr"] for c in cpr_data]
            result_df["bottom_cpr"] = [c["bottom_cpr"] for c in cpr_data]
            result_df["cpr_width"] = [c["cpr_width"] for c in cpr_data]
            result_df["cpr_type"] = [c["cpr_type"] for c in cpr_data]
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating CPR for DataFrame: {e}")
            return df
    
    def get_trading_signals(
        self,
        current_price: float,
        cpr_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trading signals based on CPR
        
        Args:
            current_price: Current market price
            cpr_data: CPR calculation result
        
        Returns:
            Trading signals and recommendations
        """
        try:
            top_cpr = cpr_data["top_cpr"]
            bottom_cpr = cpr_data["bottom_cpr"]
            pivot = cpr_data["pivot_point"]
            price_position = cpr_data["price_position"]
            
            signals = []
            recommendations = []
            
            # Price above Top CPR - Bullish
            if current_price > top_cpr:
                signals.append({
                    "signal": "BUY",
                    "strength": "Strong",
                    "reason": "Price above Top CPR indicates bullish momentum",
                    "entry": current_price,
                    "stop_loss": bottom_cpr,
                    "target_1": cpr_data["resistance_levels"]["r1"],
                    "target_2": cpr_data["resistance_levels"]["r2"]
                })
                recommendations.append("Consider buying with stop loss at Bottom CPR")
            
            # Price below Bottom CPR - Bearish
            elif current_price < bottom_cpr:
                signals.append({
                    "signal": "SELL",
                    "strength": "Strong",
                    "reason": "Price below Bottom CPR indicates bearish momentum",
                    "entry": current_price,
                    "stop_loss": top_cpr,
                    "target_1": cpr_data["support_levels"]["s1"],
                    "target_2": cpr_data["support_levels"]["s2"]
                })
                recommendations.append("Consider selling with stop loss at Top CPR")
            
            # Price between Top and Bottom CPR - Wait for breakout
            else:
                signals.append({
                    "signal": "WAIT",
                    "strength": "Neutral",
                    "reason": "Price within CPR range, wait for breakout",
                    "breakout_above": top_cpr,
                    "breakout_below": bottom_cpr
                })
                recommendations.append("Wait for price to break above Top CPR (buy) or below Bottom CPR (sell)")
            
            # Narrow CPR - Potential breakout
            if cpr_data["cpr_type"] == "Narrow CPR":
                recommendations.append("Narrow CPR detected - High probability of breakout soon")
            
            return {
                "signals": signals,
                "recommendations": recommendations,
                "cpr_analysis": cpr_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return {"error": str(e)}

# Create service instance
cpr_service = CentralPivotRangeService()

