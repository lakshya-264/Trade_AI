"""
Candlestick Pattern Recognition Service
Advanced pattern detection for professional trading
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class CandlestickPatternService:
    def __init__(self):
        self.patterns = {
            "hammer": self._detect_hammer,
            "doji": self._detect_doji,
            "engulfing": self._detect_engulfing,
            "morning_star": self._detect_morning_star,
            "shooting_star": self._detect_shooting_star,
            "three_white_soldiers": self._detect_three_white_soldiers,
            "evening_star": self._detect_evening_star,
            "hanging_man": self._detect_hanging_man,
            "inverted_hammer": self._detect_inverted_hammer,
            "piercing_line": self._detect_piercing_line,
            "dark_cloud_cover": self._detect_dark_cloud_cover,
            "harami": self._detect_harami,
            "spinning_top": self._detect_spinning_top
        }
    
    def detect_patterns(self, df: pd.DataFrame, patterns: List[str] = None) -> Dict:
        """Detect all specified candlestick patterns"""
        try:
            if patterns is None:
                patterns = list(self.patterns.keys())
            
            detected_patterns = {}
            
            for pattern_name in patterns:
                if pattern_name in self.patterns:
                    try:
                        pattern_data = self.patterns[pattern_name](df)
                        if pattern_data:
                            detected_patterns[pattern_name] = pattern_data
                    except Exception as e:
                        logger.warning(f"Error detecting {pattern_name}: {e}")
            
            return {
                "patterns": detected_patterns,
                "total_patterns": len(detected_patterns),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return {"patterns": {}, "total_patterns": 0, "error": str(e)}
    
    def analyze_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns and return signal information"""
        try:
            # Detect all patterns
            pattern_data = self.detect_patterns(df)
            
            # Analyze recent patterns for signals
            recent_patterns = []
            current_signals = {
                'signal': 'HOLD',
                'confidence': 0.5,
                'recent_patterns': []
            }
            
            # Check last 5 candles for patterns
            if len(df) >= 5:
                recent_df = df.tail(5)
                for pattern_name, pattern_func in self.patterns.items():
                    try:
                        pattern_result = pattern_func(recent_df)
                        if pattern_result:
                            recent_patterns.append({
                                'pattern': pattern_name,
                                'confidence': pattern_result.get('confidence', 0.5),
                                'signal': pattern_result.get('signal', 'NEUTRAL'),
                                'timestamp': pattern_result.get('timestamp', datetime.now().isoformat())
                            })
                    except Exception as e:
                        logger.warning(f"Error analyzing {pattern_name}: {e}")
            
            # Determine overall signal based on recent patterns
            if recent_patterns:
                bullish_patterns = [p for p in recent_patterns if p['signal'] == 'BULLISH']
                bearish_patterns = [p for p in recent_patterns if p['signal'] == 'BEARISH']
                
                if len(bullish_patterns) > len(bearish_patterns):
                    current_signals['signal'] = 'BUY'
                    current_signals['confidence'] = min(0.8, 0.5 + len(bullish_patterns) * 0.1)
                elif len(bearish_patterns) > len(bullish_patterns):
                    current_signals['signal'] = 'SELL'
                    current_signals['confidence'] = min(0.8, 0.5 + len(bearish_patterns) * 0.1)
                
                current_signals['recent_patterns'] = recent_patterns
            
            return {
                'current_signals': current_signals,
                'pattern_strength': len(recent_patterns) / 5.0,  # Normalize to 0-1
                'total_patterns_detected': len(pattern_data.get('patterns', {})),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {
                'current_signals': {'signal': 'HOLD', 'confidence': 0.0, 'recent_patterns': []},
                'pattern_strength': 0.0,
                'total_patterns_detected': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def _detect_hammer(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Hammer pattern - bullish reversal"""
        try:
            if len(df) < 1:
                return None
            
            last_candle = df.iloc[-1]
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            # Hammer criteria
            body_size = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            # Hammer: small body, long lower shadow, small upper shadow
            body_ratio = body_size / total_range
            lower_shadow_ratio = lower_shadow / total_range
            upper_shadow_ratio = upper_shadow / total_range
            
            if (body_ratio < 0.3 and  # Small body
                lower_shadow_ratio > 0.6 and  # Long lower shadow
                upper_shadow_ratio < 0.1):  # Small upper shadow
                
                confidence = min(0.9, 0.5 + (lower_shadow_ratio - 0.6) * 2)
                
                return {
                    "pattern": "Hammer",
                    "type": "Bullish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Potential bullish reversal signal",
                    "target_price": close_price * 1.05,  # 5% target
                    "stop_loss": low_price * 0.98,  # 2% below low
                    "risk_reward": round((close_price * 1.05 - close_price) / (close_price - low_price * 0.98), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting hammer: {e}")
            return None
    
    def _detect_doji(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Doji pattern - indecision"""
        try:
            if len(df) < 1:
                return None
            
            last_candle = df.iloc[-1]
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            # Doji criteria
            body_size = abs(close_price - open_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            
            # Doji: very small body (less than 5% of total range)
            if body_ratio < 0.05:
                confidence = 0.8 if body_ratio < 0.02 else 0.6
                
                return {
                    "pattern": "Doji",
                    "type": "Indecision",
                    "confidence": round(confidence, 2),
                    "description": "Market indecision, potential reversal",
                    "target_price": None,  # No clear direction
                    "stop_loss": None,
                    "risk_reward": None,
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting doji: {e}")
            return None
    
    def _detect_engulfing(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Engulfing pattern - strong reversal"""
        try:
            if len(df) < 2:
                return None
            
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            
            current_open = current_candle['open']
            current_close = current_candle['close']
            previous_open = previous_candle['open']
            previous_close = previous_candle['close']
            
            # Determine if bullish or bearish engulfing
            current_body = current_close - current_open
            previous_body = previous_close - previous_open
            
            # Bullish Engulfing
            if (previous_body < 0 and  # Previous candle bearish
                current_body > 0 and  # Current candle bullish
                current_open < previous_close and  # Current opens below previous close
                current_close > previous_open):  # Current closes above previous open
                
                confidence = min(0.95, 0.6 + abs(current_body) / previous_open * 10)
                
                return {
                    "pattern": "Bullish Engulfing",
                    "type": "Bullish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Strong bullish reversal signal",
                    "target_price": current_close * 1.08,  # 8% target
                    "stop_loss": current_open * 0.97,  # 3% below current open
                    "risk_reward": round((current_close * 1.08 - current_close) / (current_close - current_open * 0.97), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            # Bearish Engulfing
            elif (previous_body > 0 and  # Previous candle bullish
                  current_body < 0 and  # Current candle bearish
                  current_open > previous_close and  # Current opens above previous close
                  current_close < previous_open):  # Current closes below previous open
                
                confidence = min(0.95, 0.6 + abs(current_body) / previous_open * 10)
                
                return {
                    "pattern": "Bearish Engulfing",
                    "type": "Bearish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Strong bearish reversal signal",
                    "target_price": current_close * 0.92,  # 8% target
                    "stop_loss": current_open * 1.03,  # 3% above current open
                    "risk_reward": round((current_close - current_close * 0.92) / (current_open * 1.03 - current_close), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting engulfing: {e}")
            return None
    
    def _detect_morning_star(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Morning Star pattern - bullish reversal"""
        try:
            if len(df) < 3:
                return None
            
            first_candle = df.iloc[-3]
            second_candle = df.iloc[-2]
            third_candle = df.iloc[-1]
            
            first_close = first_candle['close']
            first_open = first_candle['open']
            second_close = second_candle['close']
            second_open = second_candle['open']
            third_close = third_candle['close']
            third_open = third_candle['open']
            
            # Morning Star criteria
            first_body = first_close - first_open
            second_body = second_close - second_open
            third_body = third_close - third_open
            
            # First candle: bearish
            # Second candle: small body (star)
            # Third candle: bullish, closes in first candle's body
            if (first_body < 0 and  # First candle bearish
                abs(second_body) < abs(first_body) * 0.3 and  # Second candle small body
                third_body > 0 and  # Third candle bullish
                third_close > (first_open + first_close) / 2):  # Third closes in first's body
                
                confidence = min(0.9, 0.5 + abs(third_body) / first_open * 5)
                
                return {
                    "pattern": "Morning Star",
                    "type": "Bullish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Strong bullish reversal after downtrend",
                    "target_price": third_close * 1.1,  # 10% target
                    "stop_loss": second_candle['low'] * 0.98,  # Below star's low
                    "risk_reward": round((third_close * 1.1 - third_close) / (third_close - second_candle['low'] * 0.98), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting morning star: {e}")
            return None
    
    def _detect_shooting_star(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Shooting Star pattern - bearish reversal"""
        try:
            if len(df) < 1:
                return None
            
            last_candle = df.iloc[-1]
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            # Shooting Star criteria
            body_size = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            upper_shadow_ratio = upper_shadow / total_range
            lower_shadow_ratio = lower_shadow / total_range
            
            # Shooting Star: small body, long upper shadow, small lower shadow
            if (body_ratio < 0.3 and  # Small body
                upper_shadow_ratio > 0.6 and  # Long upper shadow
                lower_shadow_ratio < 0.1):  # Small lower shadow
                
                confidence = min(0.9, 0.5 + (upper_shadow_ratio - 0.6) * 2)
                
                return {
                    "pattern": "Shooting Star",
                    "type": "Bearish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Potential bearish reversal signal",
                    "target_price": close_price * 0.95,  # 5% target
                    "stop_loss": high_price * 1.02,  # 2% above high
                    "risk_reward": round((close_price - close_price * 0.95) / (high_price * 1.02 - close_price), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting shooting star: {e}")
            return None
    
    def _detect_three_white_soldiers(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Three White Soldiers pattern - bullish continuation"""
        try:
            if len(df) < 3:
                return None
            
            first_candle = df.iloc[-3]
            second_candle = df.iloc[-2]
            third_candle = df.iloc[-1]
            
            first_close = first_candle['close']
            first_open = first_candle['open']
            second_close = second_candle['close']
            second_open = second_candle['open']
            third_close = third_candle['close']
            third_open = third_candle['open']
            
            # Three White Soldiers criteria
            first_body = first_close - first_open
            second_body = second_close - second_open
            third_body = third_close - third_open
            
            # All three candles bullish with increasing closes
            if (first_body > 0 and  # First candle bullish
                second_body > 0 and  # Second candle bullish
                third_body > 0 and  # Third candle bullish
                second_close > first_close and  # Second closes higher than first
                third_close > second_close):  # Third closes higher than second
                
                confidence = min(0.9, 0.6 + (third_close - first_close) / first_close * 2)
                
                return {
                    "pattern": "Three White Soldiers",
                    "type": "Bullish Continuation",
                    "confidence": round(confidence, 2),
                    "description": "Strong bullish momentum continuation",
                    "target_price": third_close * 1.12,  # 12% target
                    "stop_loss": first_open * 0.98,  # Below first candle's open
                    "risk_reward": round((third_close * 1.12 - third_close) / (third_close - first_open * 0.98), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting three white soldiers: {e}")
            return None
    
    def _detect_evening_star(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Evening Star pattern - bearish reversal"""
        try:
            if len(df) < 3:
                return None
            
            first_candle = df.iloc[-3]
            second_candle = df.iloc[-2]
            third_candle = df.iloc[-1]
            
            first_close = first_candle['close']
            first_open = first_candle['open']
            second_close = second_candle['close']
            second_open = second_candle['open']
            third_close = third_candle['close']
            third_open = third_candle['open']
            
            # Evening Star criteria
            first_body = first_close - first_open
            second_body = second_close - second_open
            third_body = third_close - third_open
            
            # First candle: bullish
            # Second candle: small body (star)
            # Third candle: bearish, closes in first candle's body
            if (first_body > 0 and  # First candle bullish
                abs(second_body) < abs(first_body) * 0.3 and  # Second candle small body
                third_body < 0 and  # Third candle bearish
                third_close < (first_open + first_close) / 2):  # Third closes in first's body
                
                confidence = min(0.9, 0.5 + abs(third_body) / first_open * 5)
                
                return {
                    "pattern": "Evening Star",
                    "type": "Bearish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Strong bearish reversal after uptrend",
                    "target_price": third_close * 0.9,  # 10% target
                    "stop_loss": second_candle['high'] * 1.02,  # Above star's high
                    "risk_reward": round((third_close - third_close * 0.9) / (second_candle['high'] * 1.02 - third_close), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting evening star: {e}")
            return None
    
    def _detect_hanging_man(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Hanging Man pattern - bearish reversal"""
        try:
            if len(df) < 1:
                return None
            
            last_candle = df.iloc[-1]
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            # Hanging Man criteria (similar to Hammer but in uptrend)
            body_size = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            lower_shadow_ratio = lower_shadow / total_range
            upper_shadow_ratio = upper_shadow / total_range
            
            # Hanging Man: small body, long lower shadow, small upper shadow
            if (body_ratio < 0.3 and  # Small body
                lower_shadow_ratio > 0.6 and  # Long lower shadow
                upper_shadow_ratio < 0.1):  # Small upper shadow
                
                confidence = min(0.8, 0.4 + (lower_shadow_ratio - 0.6) * 2)
                
                return {
                    "pattern": "Hanging Man",
                    "type": "Bearish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Potential bearish reversal in uptrend",
                    "target_price": close_price * 0.95,  # 5% target
                    "stop_loss": high_price * 1.02,  # 2% above high
                    "risk_reward": round((close_price - close_price * 0.95) / (high_price * 1.02 - close_price), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting hanging man: {e}")
            return None
    
    def _detect_inverted_hammer(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Inverted Hammer pattern - bullish reversal"""
        try:
            if len(df) < 1:
                return None
            
            last_candle = df.iloc[-1]
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            # Inverted Hammer criteria
            body_size = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            upper_shadow_ratio = upper_shadow / total_range
            lower_shadow_ratio = lower_shadow / total_range
            
            # Inverted Hammer: small body, long upper shadow, small lower shadow
            if (body_ratio < 0.3 and  # Small body
                upper_shadow_ratio > 0.6 and  # Long upper shadow
                lower_shadow_ratio < 0.1):  # Small lower shadow
                
                confidence = min(0.8, 0.4 + (upper_shadow_ratio - 0.6) * 2)
                
                return {
                    "pattern": "Inverted Hammer",
                    "type": "Bullish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Potential bullish reversal signal",
                    "target_price": close_price * 1.05,  # 5% target
                    "stop_loss": low_price * 0.98,  # 2% below low
                    "risk_reward": round((close_price * 1.05 - close_price) / (close_price - low_price * 0.98), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting inverted hammer: {e}")
            return None
    
    def _detect_piercing_line(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Piercing Line pattern - bullish reversal"""
        try:
            if len(df) < 2:
                return None
            
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            
            current_open = current_candle['open']
            current_close = current_candle['close']
            previous_open = previous_candle['open']
            previous_close = previous_candle['close']
            
            # Piercing Line criteria
            previous_body = previous_close - previous_open
            current_body = current_close - current_open
            
            # Previous candle bearish, current candle bullish
            # Current opens below previous close, closes in previous body
            if (previous_body < 0 and  # Previous candle bearish
                current_body > 0 and  # Current candle bullish
                current_open < previous_close and  # Current opens below previous close
                current_close > (previous_open + previous_close) / 2 and  # Current closes in previous body
                current_close < previous_open):  # Current doesn't close above previous open
                
                confidence = min(0.85, 0.5 + current_body / previous_open * 5)
                
                return {
                    "pattern": "Piercing Line",
                    "type": "Bullish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Bullish reversal after bearish candle",
                    "target_price": current_close * 1.06,  # 6% target
                    "stop_loss": current_open * 0.97,  # 3% below current open
                    "risk_reward": round((current_close * 1.06 - current_close) / (current_close - current_open * 0.97), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting piercing line: {e}")
            return None
    
    def _detect_dark_cloud_cover(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Dark Cloud Cover pattern - bearish reversal"""
        try:
            if len(df) < 2:
                return None
            
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            
            current_open = current_candle['open']
            current_close = current_candle['close']
            previous_open = previous_candle['open']
            previous_close = previous_candle['close']
            
            # Dark Cloud Cover criteria
            previous_body = previous_close - previous_open
            current_body = current_close - current_open
            
            # Previous candle bullish, current candle bearish
            # Current opens above previous close, closes in previous body
            if (previous_body > 0 and  # Previous candle bullish
                current_body < 0 and  # Current candle bearish
                current_open > previous_close and  # Current opens above previous close
                current_close < (previous_open + previous_close) / 2 and  # Current closes in previous body
                current_close > previous_open):  # Current doesn't close below previous open
                
                confidence = min(0.85, 0.5 + abs(current_body) / previous_open * 5)
                
                return {
                    "pattern": "Dark Cloud Cover",
                    "type": "Bearish Reversal",
                    "confidence": round(confidence, 2),
                    "description": "Bearish reversal after bullish candle",
                    "target_price": current_close * 0.94,  # 6% target
                    "stop_loss": current_open * 1.03,  # 3% above current open
                    "risk_reward": round((current_close - current_close * 0.94) / (current_open * 1.03 - current_close), 2),
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting dark cloud cover: {e}")
            return None
    
    def _detect_harami(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Harami pattern - reversal signal"""
        try:
            if len(df) < 2:
                return None
            
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            
            current_open = current_candle['open']
            current_close = current_candle['close']
            previous_open = previous_candle['open']
            previous_close = previous_candle['close']
            
            # Harami criteria
            previous_body = abs(previous_close - previous_open)
            current_body = abs(current_close - current_open)
            
            # Current candle's body is inside previous candle's body
            if (current_body < previous_body * 0.5 and  # Current body smaller
                min(current_open, current_close) > min(previous_open, previous_close) and  # Current low above previous low
                max(current_open, current_close) < max(previous_open, previous_close)):  # Current high below previous high
                
                # Determine if bullish or bearish harami
                if previous_close > previous_open:  # Previous bullish
                    pattern_type = "Bearish Reversal"
                    confidence = 0.6
                else:  # Previous bearish
                    pattern_type = "Bullish Reversal"
                    confidence = 0.6
                
                return {
                    "pattern": "Harami",
                    "type": pattern_type,
                    "confidence": round(confidence, 2),
                    "description": f"Potential {pattern_type.lower()} signal",
                    "target_price": current_close * (1.05 if pattern_type == "Bullish Reversal" else 0.95),
                    "stop_loss": current_close * (0.98 if pattern_type == "Bullish Reversal" else 1.02),
                    "risk_reward": 2.0,  # Generic risk-reward
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting harami: {e}")
            return None
    
    def _detect_spinning_top(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Spinning Top pattern - indecision"""
        try:
            if len(df) < 1:
                return None
            
            last_candle = df.iloc[-1]
            open_price = last_candle['open']
            high_price = last_candle['high']
            low_price = last_candle['low']
            close_price = last_candle['close']
            
            # Spinning Top criteria
            body_size = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range == 0:
                return None
            
            body_ratio = body_size / total_range
            shadow_ratio = (lower_shadow + upper_shadow) / total_range
            
            # Spinning Top: small body, long shadows on both sides
            if (body_ratio < 0.3 and  # Small body
                shadow_ratio > 0.6):  # Long shadows
                
                confidence = 0.7
                
                return {
                    "pattern": "Spinning Top",
                    "type": "Indecision",
                    "confidence": round(confidence, 2),
                    "description": "Market indecision, potential reversal",
                    "target_price": None,  # No clear direction
                    "stop_loss": None,
                    "risk_reward": None,
                    "candle_index": len(df) - 1,
                    "timestamp": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting spinning top: {e}")
            return None