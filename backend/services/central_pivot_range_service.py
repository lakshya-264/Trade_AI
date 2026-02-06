"""
Central Pivot Range (CPR) Service
CPR is a popular intraday trading tool that identifies key support/resistance levels
Based on previous day's high, low, and close
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class CentralPivotRangeService:
    """Service for Central Pivot Range calculation and analysis"""
    
    def __init__(self):
        self.cpr_education = self._initialize_cpr_education()
    
    def _initialize_cpr_education(self) -> Dict[str, Any]:
        """Initialize CPR education content"""
        return {
            "what_is_cpr": {
                "title": "What is Central Pivot Range?",
                "content": "CPR is an intraday trading tool that identifies three key price levels based on the previous day's trading data. It helps traders identify potential support and resistance levels for the current trading day.",
                "key_concept": "CPR uses yesterday's High, Low, and Close to predict today's key levels",
                "components": {
                    "pivot_point": {
                        "name": "Pivot Point (PP)",
                        "description": "The central price level, calculated as the average of High, Low, and Close",
                        "formula": "PP = (High + Low + Close) / 3",
                        "significance": "Acts as a key support/resistance level"
                    },
                    "top_cpr": {
                        "name": "Top Central Pivot Range (TC)",
                        "description": "The upper boundary of the CPR",
                        "formula": "TC = (High + Low) / 2",
                        "significance": "Acts as resistance level"
                    },
                    "bottom_cpr": {
                        "name": "Bottom Central Pivot Range (BC)",
                        "description": "The lower boundary of the CPR",
                        "formula": "BC = (PP + TC) / 2",
                        "significance": "Acts as support level"
                    }
                }
            },
            "how_to_use": {
                "title": "How to Use CPR for Trading",
                "strategies": [
                    {
                        "strategy": "CPR Width Analysis",
                        "description": "The width between TC and BC indicates market volatility",
                        "narrow_cpr": {
                            "width": "< 0.5% of price",
                            "interpretation": "Low volatility day expected, range-bound trading",
                            "action": "Trade within CPR range, buy near BC, sell near TC"
                        },
                        "wide_cpr": {
                            "width": "> 1% of price",
                            "interpretation": "High volatility day expected, trending moves",
                            "action": "Look for breakouts above TC or below BC"
                        }
                    },
                    {
                        "strategy": "Price Position Relative to CPR",
                        "scenarios": {
                            "above_tc": {
                                "interpretation": "Bullish - Price is above top CPR",
                                "action": "Look for buying opportunities, TC acts as support"
                            },
                            "between_tc_bc": {
                                "interpretation": "Neutral - Price is within CPR range",
                                "action": "Range trading, buy near BC, sell near TC"
                            },
                            "below_bc": {
                                "interpretation": "Bearish - Price is below bottom CPR",
                                "action": "Look for selling opportunities, BC acts as resistance"
                            }
                        }
                    },
                    {
                        "strategy": "CPR Breakout Trading",
                        "description": "When price breaks above TC or below BC",
                        "bullish_breakout": {
                            "condition": "Price breaks above TC with volume",
                            "action": "Buy with stop loss at TC, target next resistance"
                        },
                        "bearish_breakout": {
                            "condition": "Price breaks below BC with volume",
                            "action": "Sell with stop loss at BC, target next support"
                        }
                    }
                ]
            },
            "cpr_types": {
                "title": "Types of CPR",
                "types": [
                    {
                        "type": "Normal CPR",
                        "description": "TC is above PP, BC is below PP",
                        "interpretation": "Standard CPR, balanced market",
                        "width": "Moderate"
                    },
                    {
                        "type": "Narrow CPR",
                        "description": "Small difference between TC and BC (< 0.5%)",
                        "interpretation": "Low volatility, consolidation expected",
                        "trading_style": "Range trading"
                    },
                    {
                        "type": "Wide CPR",
                        "description": "Large difference between TC and BC (> 1%)",
                        "interpretation": "High volatility, trending day expected",
                        "trading_style": "Breakout trading"
                    },
                    {
                        "type": "Reversed CPR",
                        "description": "BC is above TC (rare)",
                        "interpretation": "Unusual market condition, high volatility expected",
                        "caution": "Trade with extra caution"
                    }
                ]
            }
        }
    
    def calculate_cpr(self, high: float, low: float, close: float) -> Dict[str, Any]:
        """
        Calculate Central Pivot Range
        
        Args:
            high: Previous day's high
            low: Previous day's low
            close: Previous day's close
        
        Returns:
            CPR levels and analysis
        """
        try:
            # Calculate Pivot Point
            pivot_point = (high + low + close) / 3
            
            # Calculate Top CPR
            top_cpr = (high + low) / 2
            
            # Calculate Bottom CPR
            bottom_cpr = (pivot_point + top_cpr) / 2
            
            # Calculate CPR width
            cpr_width = top_cpr - bottom_cpr
            cpr_width_percent = (cpr_width / pivot_point * 100) if pivot_point else 0
            
            # Determine CPR type
            cpr_type = self._determine_cpr_type(cpr_width_percent, top_cpr, bottom_cpr)
            
            # Calculate additional levels (optional)
            resistance_1 = 2 * pivot_point - low
            resistance_2 = pivot_point + (high - low)
            support_1 = 2 * pivot_point - high
            support_2 = pivot_point - (high - low)
            
            return {
                "success": True,
                "cpr_levels": {
                    "pivot_point": round(pivot_point, 2),
                    "top_cpr": round(top_cpr, 2),
                    "bottom_cpr": round(bottom_cpr, 2),
                    "cpr_width": round(cpr_width, 2),
                    "cpr_width_percent": round(cpr_width_percent, 2)
                },
                "additional_levels": {
                    "resistance_1": round(resistance_1, 2),
                    "resistance_2": round(resistance_2, 2),
                    "support_1": round(support_1, 2),
                    "support_2": round(support_2, 2)
                },
                "cpr_type": cpr_type,
                "interpretation": self._interpret_cpr(cpr_width_percent, cpr_type),
                "trading_suggestions": self._get_trading_suggestions(cpr_type, cpr_width_percent)
            }
        except Exception as e:
            logger.error(f"Error calculating CPR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_cpr_from_ohlc(self, ohlc_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate CPR from OHLC data (multiple days)
        
        Args:
            ohlc_data: List of OHLC dictionaries with 'high', 'low', 'close', 'time'
        
        Returns:
            CPR levels for each day and analysis
        """
        try:
            if not ohlc_data or len(ohlc_data) < 2:
                return {
                    "success": False,
                    "error": "Need at least 2 days of data"
                }
            
            # Sort by time (oldest first)
            sorted_data = sorted(ohlc_data, key=lambda x: x.get('time', 0))
            
            cpr_results = []
            for i in range(1, len(sorted_data)):
                prev_day = sorted_data[i-1]
                current_day = sorted_data[i]
                
                high = prev_day.get('high', 0)
                low = prev_day.get('low', 0)
                close = prev_day.get('close', 0)
                
                cpr = self.calculate_cpr(high, low, close)
                
                # Analyze how price reacted to CPR
                current_price = current_day.get('close', 0)
                price_position = self._analyze_price_position(
                    current_price,
                    cpr['cpr_levels']['top_cpr'],
                    cpr['cpr_levels']['bottom_cpr'],
                    cpr['cpr_levels']['pivot_point']
                )
                
                cpr_results.append({
                    "date": current_day.get('time', ''),
                    "cpr": cpr,
                    "price_position": price_position,
                    "current_price": current_price
                })
            
            return {
                "success": True,
                "cpr_history": cpr_results,
                "summary": self._summarize_cpr_history(cpr_results)
            }
        except Exception as e:
            logger.error(f"Error calculating CPR from OHLC: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _determine_cpr_type(self, width_percent: float, top_cpr: float, bottom_cpr: float) -> str:
        """Determine CPR type based on width and structure"""
        if bottom_cpr > top_cpr:
            return "Reversed CPR"
        elif width_percent < 0.5:
            return "Narrow CPR"
        elif width_percent > 1.0:
            return "Wide CPR"
        else:
            return "Normal CPR"
    
    def _interpret_cpr(self, width_percent: float, cpr_type: str) -> Dict[str, Any]:
        """Interpret CPR based on width and type"""
        interpretations = {
            "Narrow CPR": {
                "volatility": "Low",
                "expected_movement": "Range-bound trading",
                "trading_style": "Range trading within CPR levels"
            },
            "Wide CPR": {
                "volatility": "High",
                "expected_movement": "Trending moves, breakouts",
                "trading_style": "Breakout trading, momentum"
            },
            "Normal CPR": {
                "volatility": "Moderate",
                "expected_movement": "Balanced market conditions",
                "trading_style": "Both range and breakout trading"
            },
            "Reversed CPR": {
                "volatility": "Very High",
                "expected_movement": "Unusual market conditions",
                "trading_style": "Caution advised"
            }
        }
        
        return interpretations.get(cpr_type, {
            "volatility": "Unknown",
            "expected_movement": "Cannot determine",
            "trading_style": "General trading"
        })
    
    def _get_trading_suggestions(self, cpr_type: str, width_percent: float) -> List[str]:
        """Get trading suggestions based on CPR type"""
        suggestions = []
        
        if cpr_type == "Narrow CPR":
            suggestions.extend([
                "Expect range-bound trading",
                "Buy near Bottom CPR (BC), sell near Top CPR (TC)",
                "Use tight stop losses",
                "Look for mean reversion trades"
            ])
        elif cpr_type == "Wide CPR":
            suggestions.extend([
                "Expect high volatility and trending moves",
                "Look for breakouts above TC or below BC",
                "Use wider stop losses",
                "Follow momentum in breakout direction"
            ])
        elif cpr_type == "Normal CPR":
            suggestions.extend([
                "Market in balanced state",
                "Trade both range and breakout strategies",
                "Monitor price position relative to CPR",
                "Use Pivot Point as key reference"
            ])
        else:  # Reversed CPR
            suggestions.extend([
                "Unusual market condition - trade with caution",
                "Expect high volatility",
                "Use wider stop losses",
                "Consider staying on sidelines"
            ])
        
        return suggestions
    
    def _analyze_price_position(self, current_price: float, top_cpr: float, bottom_cpr: float, pivot: float) -> Dict[str, Any]:
        """Analyze current price position relative to CPR"""
        if current_price > top_cpr:
            position = "Above Top CPR"
            sentiment = "Bullish"
            key_level = top_cpr
            action = "TC acts as support, look for buying opportunities"
        elif current_price < bottom_cpr:
            position = "Below Bottom CPR"
            sentiment = "Bearish"
            key_level = bottom_cpr
            action = "BC acts as resistance, look for selling opportunities"
        elif current_price > pivot:
            position = "Between Pivot and Top CPR"
            sentiment = "Mildly Bullish"
            key_level = pivot
            action = "Pivot acts as support, TC as resistance"
        else:
            position = "Between Bottom CPR and Pivot"
            sentiment = "Mildly Bearish"
            key_level = pivot
            action = "Pivot acts as resistance, BC as support"
        
        distance_from_pivot = abs(current_price - pivot)
        distance_percent = (distance_from_pivot / pivot * 100) if pivot else 0
        
        return {
            "position": position,
            "sentiment": sentiment,
            "key_level": round(key_level, 2),
            "action": action,
            "distance_from_pivot": round(distance_from_pivot, 2),
            "distance_percent": round(distance_percent, 2)
        }
    
    def _summarize_cpr_history(self, cpr_results: List[Dict]) -> Dict[str, Any]:
        """Summarize CPR history"""
        if not cpr_results:
            return {}
        
        cpr_types = [r['cpr']['cpr_type'] for r in cpr_results]
        most_common_type = max(set(cpr_types), key=cpr_types.count)
        
        avg_width = np.mean([r['cpr']['cpr_levels']['cpr_width_percent'] for r in cpr_results])
        
        price_positions = [r['price_position']['sentiment'] for r in cpr_results]
        most_common_sentiment = max(set(price_positions), key=price_positions.count)
        
        return {
            "total_days": len(cpr_results),
            "most_common_cpr_type": most_common_type,
            "average_cpr_width_percent": round(avg_width, 2),
            "most_common_sentiment": most_common_sentiment
        }
    
    def get_cpr_education(self) -> Dict[str, Any]:
        """Get CPR education content"""
        return {
            "success": True,
            "education": self.cpr_education
        }

