"""
Advanced Chart Pattern Detection Service
Detects complex chart patterns like Reverse Head & Shoulder, Cup & Handle, etc.
Similar to professional research reports
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# NumPy compatibility: np.bool8 was removed in NumPy 2.0, use np.bool_ instead.
NP_BOOL8 = getattr(np, "bool8", np.bool_)

def _to_python_type(value):
    """Convert numpy/pandas types to native Python types for JSON serialization"""
    import numpy as np
    import pandas as pd
    
    # Check type name as well for edge cases
    type_name = str(type(value))
    type_module = type(value).__module__ if hasattr(type(value), '__module__') else ''
    
    # Check if it's a numpy type by module name first (most reliable)
    if 'numpy' in type_module or 'numpy' in type_name:
        # Try item() method first (works for most numpy scalars)
        if hasattr(value, 'item'):
            try:
                return value.item()
            except:
                pass
        
        # Type-specific conversion
        if 'bool' in type_name.lower():
            return bool(value)
        elif 'int' in type_name.lower():
            return int(value)
        elif 'float' in type_name.lower():
            return float(value)
        else:
            # Last resort: try direct conversion
            try:
                return bool(value) if isinstance(value, (bool, np.bool_, NP_BOOL8)) else \
                       int(value) if isinstance(value, (int, np.integer)) else \
                       float(value) if isinstance(value, (float, np.floating)) else \
                       str(value)
            except:
                return str(value)
    
    # Handle pandas types
    elif isinstance(value, pd.Series):
        return value.tolist()
    elif isinstance(value, pd.DataFrame):
        return value.to_dict('records')
    
    # Handle standard numpy types (NumPy 2.0 compatible - removed np.float_, np.int_)
    elif isinstance(value, (np.integer, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
        return int(value)
    elif isinstance(value, (np.floating, np.float16, np.float32, np.float64)):
        return float(value)
    elif isinstance(value, (np.bool_, NP_BOOL8)):
        return bool(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    
    # Try item() for any numpy scalar
    elif hasattr(value, 'item'):
        try:
            return value.item()
        except:
            return str(value)
    
    # Not a numpy/pandas type, return as-is
    else:
        return value

class AdvancedChartPatternDetector:
    """Advanced chart pattern detection with professional-grade analysis"""
    
    def __init__(self):
        self.min_pattern_length = 20  # Minimum candles for pattern
        self.max_pattern_length = 200  # Maximum candles for pattern
        
    def detect_all_patterns(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1W"
    ) -> List[Dict[str, Any]]:
        """
        Detect all advanced chart patterns in the data
        
        Returns list of detected patterns with analysis
        """
        try:
            if len(df) < self.min_pattern_length:
                return []
            
            patterns = []
            
            # Detect Reverse Head & Shoulder (most important for bullish reversal)
            reverse_hs = self.detect_reverse_head_shoulder(df, symbol, timeframe)
            if reverse_hs:
                patterns.append(reverse_hs)
            
            # Detect Head & Shoulder (bearish reversal)
            head_shoulder = self.detect_head_shoulder(df, symbol, timeframe)
            if head_shoulder:
                patterns.append(head_shoulder)
            
            # Detect Cup & Handle
            cup_handle = self.detect_cup_handle(df, symbol, timeframe)
            if cup_handle:
                patterns.append(cup_handle)
            
            # Detect Double Top/Bottom
            double_top = self.detect_double_top(df, symbol, timeframe)
            if double_top:
                patterns.append(double_top)
            
            double_bottom = self.detect_double_bottom(df, symbol, timeframe)
            if double_bottom:
                patterns.append(double_bottom)
            
            # Detect Triangles
            ascending_triangle = self.detect_ascending_triangle(df, symbol, timeframe)
            if ascending_triangle:
                patterns.append(ascending_triangle)
            
            descending_triangle = self.detect_descending_triangle(df, symbol, timeframe)
            if descending_triangle:
                patterns.append(descending_triangle)
            
            symmetrical_triangle = self.detect_symmetrical_triangle(df, symbol, timeframe)
            if symmetrical_triangle:
                patterns.append(symmetrical_triangle)
            
            # Detect Wedges
            rising_wedge = self.detect_rising_wedge(df, symbol, timeframe)
            if rising_wedge:
                patterns.append(rising_wedge)
            
            falling_wedge = self.detect_falling_wedge(df, symbol, timeframe)
            if falling_wedge:
                patterns.append(falling_wedge)
            
            # Detect Flags & Pennants
            bullish_flag = self.detect_bullish_flag(df, symbol, timeframe)
            if bullish_flag:
                patterns.append(bullish_flag)
            
            bearish_flag = self.detect_bearish_flag(df, symbol, timeframe)
            if bearish_flag:
                patterns.append(bearish_flag)
            
            bullish_pennant = self.detect_bullish_pennant(df, symbol, timeframe)
            if bullish_pennant:
                patterns.append(bullish_pennant)
            
            bearish_pennant = self.detect_bearish_pennant(df, symbol, timeframe)
            if bearish_pennant:
                patterns.append(bearish_pennant)
            
            # Detect Rectangular Range
            rectangular_range = self.detect_rectangular_range(df, symbol, timeframe)
            if rectangular_range:
                patterns.append(rectangular_range)
            
            # Detect Rounding Patterns
            rounding_top = self.detect_rounding_top(df, symbol, timeframe)
            if rounding_top:
                patterns.append(rounding_top)
            
            rounding_bottom = self.detect_rounding_bottom(df, symbol, timeframe)
            if rounding_bottom:
                patterns.append(rounding_bottom)
            
            # Detect Diamond Pattern
            diamond = self.detect_diamond_pattern(df, symbol, timeframe)
            if diamond:
                patterns.append(diamond)
            
            # Detect Island Reversal
            island_reversal = self.detect_island_reversal(df, symbol, timeframe)
            if island_reversal:
                patterns.append(island_reversal)
            
            # Detect Gaps
            gaps = self.detect_gaps(df, symbol, timeframe)
            patterns.extend(gaps)
            
            # Detect Harmonic Patterns
            harmonic_patterns = self.detect_harmonic_patterns(df, symbol, timeframe)
            patterns.extend(harmonic_patterns)
            
            # Detect Three Drives (if we have enough points)
            if len(df) >= 50:
                swing_highs = self._find_swing_highs(df["high"].values, window=3)
                swing_lows = self._find_swing_lows(df["low"].values, window=3)
                all_points = sorted(set(swing_highs + swing_lows))
                if len(all_points) >= 5:
                    # Try to detect three drives
                    for i in range(len(all_points) - 4):
                        if i + 5 < len(all_points):
                            x_idx = all_points[i]
                            a_idx = all_points[i + 1]
                            b_idx = all_points[i + 2]
                            c_idx = all_points[i + 3]
                            d_idx = all_points[i + 4]
                            e_idx = all_points[i + 5]
                            
                            x_price = df["high"].iloc[x_idx] if x_idx in swing_highs else df["low"].iloc[x_idx]
                            a_price = df["high"].iloc[a_idx] if a_idx in swing_highs else df["low"].iloc[a_idx]
                            b_price = df["high"].iloc[b_idx] if b_idx in swing_highs else df["low"].iloc[b_idx]
                            c_price = df["high"].iloc[c_idx] if c_idx in swing_highs else df["low"].iloc[c_idx]
                            d_price = df["high"].iloc[d_idx] if d_idx in swing_highs else df["low"].iloc[d_idx]
                            e_price = df["high"].iloc[e_idx] if e_idx in swing_highs else df["low"].iloc[e_idx]
                            
                            three_drives = self._check_three_drives_pattern(x_price, a_price, b_price, c_price, d_price, e_price)
                            if three_drives:
                                three_drives.update({
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "detected_at": datetime.now().isoformat()
                                })
                                patterns.append(three_drives)
                                break  # Only add first valid pattern
            
            # Detect Price Channels
            price_channel = self.detect_price_channels(df, symbol, timeframe)
            if price_channel:
                patterns.append(price_channel)
            
            # Detect Measured Move
            measured_move = self.detect_measured_move(df, symbol, timeframe)
            if measured_move:
                patterns.append(measured_move)
            
            # Detect Elliott Waves
            elliott_wave = self.detect_elliott_waves(df, symbol, timeframe)
            if elliott_wave:
                patterns.append(elliott_wave)
            
            # Sort by confidence
            patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            # Convert all numpy types to Python types before returning
            def clean_pattern(pattern):
                """Recursively clean pattern dict of numpy types"""
                if isinstance(pattern, dict):
                    return {k: clean_pattern(v) for k, v in pattern.items()}
                elif isinstance(pattern, (list, tuple)):
                    return [clean_pattern(item) for item in pattern]
                else:
                    return _to_python_type(pattern)
            
            return [clean_pattern(p) for p in patterns]
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    def detect_reverse_head_shoulder(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect Reverse Head & Shoulder pattern (Bullish Reversal)
        This is the key pattern shown in the Reliance report
        """
        try:
            if len(df) < 30:
                return None
            
            # Get price data
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            dates = df.index if hasattr(df.index, 'tolist') else range(len(df))
            
            # Find swing lows (troughs)
            swing_lows = self._find_swing_lows(lows, window=5)
            
            if len(swing_lows) < 3:
                return None
            
            # Look for three distinct troughs where middle is lowest
            best_pattern = None
            best_confidence = 0
            
            for i in range(len(swing_lows) - 2):
                left_shoulder_idx = swing_lows[i]
                head_idx = swing_lows[i + 1]
                right_shoulder_idx = swing_lows[i + 2]
                
                # Get the actual low prices
                left_shoulder_low = lows[left_shoulder_idx]
                head_low = lows[head_idx]
                right_shoulder_low = lows[right_shoulder_idx]
                
                # Pattern criteria:
                # 1. Head should be lower than both shoulders
                # 2. Shoulders should be roughly equal height
                # 3. Should have a neckline (resistance) above
                
                if (head_low < left_shoulder_low and 
                    head_low < right_shoulder_low):
                    
                    # Check shoulder symmetry (within 5% tolerance)
                    shoulder_diff = abs(left_shoulder_low - right_shoulder_low) / max(left_shoulder_low, right_shoulder_low)
                    
                    if shoulder_diff < 0.05:  # 5% tolerance
                        # Find neckline (resistance level connecting the peaks between shoulders)
                        neckline = self._find_neckline(
                            df, left_shoulder_idx, head_idx, right_shoulder_idx
                        )
                        
                        if neckline:
                            # Calculate pattern metrics
                            pattern_height = neckline - head_low
                            
                            # Calculate confidence based on:
                            # 1. Pattern perfection (shoulder symmetry, head depth)
                            # 2. Volume confirmation (if available)
                            # 3. Neckline clarity
                            
                            confidence = self._calculate_reverse_hs_confidence(
                                df, left_shoulder_idx, head_idx, right_shoulder_idx,
                                left_shoulder_low, head_low, right_shoulder_low,
                                neckline, pattern_height
                            )
                            
                            if confidence > best_confidence:
                                # Calculate target price (neckline + pattern height)
                                target_price = neckline + pattern_height
                                
                                # Get current price
                                current_price = closes[-1]
                                
                                # Calculate potential upside
                                if current_price > 0:
                                    potential_upside = ((target_price - current_price) / current_price) * 100
                                else:
                                    potential_upside = 0
                                
                                # Get time coordinates
                                left_shoulder_time = self._get_time_from_index(df, left_shoulder_idx)
                                head_time = self._get_time_from_index(df, head_idx)
                                right_shoulder_time = self._get_time_from_index(df, right_shoulder_idx)
                                
                                best_pattern = {
                                    "pattern_type": "reverse_head_shoulder",
                                    "pattern_name": "Reverse Head & Shoulder",
                                    "pattern_category": "reversal",
                                    "pattern_direction": "bullish",
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "detected_at": datetime.now().isoformat(),
                                    
                                    # Pattern points
                                    "left_shoulder": {
                                        "index": int(left_shoulder_idx),
                                        "price": float(left_shoulder_low),
                                        "date": str(dates[left_shoulder_idx]) if hasattr(dates[left_shoulder_idx], '__str__') else str(left_shoulder_idx),
                                        "time": left_shoulder_time
                                    },
                                    "head": {
                                        "index": int(head_idx),
                                        "price": float(head_low),
                                        "date": str(dates[head_idx]) if hasattr(dates[head_idx], '__str__') else str(head_idx),
                                        "time": head_time
                                    },
                                    "right_shoulder": {
                                        "index": int(right_shoulder_idx),
                                        "price": float(right_shoulder_low),
                                        "date": str(dates[right_shoulder_idx]) if hasattr(dates[right_shoulder_idx], '__str__') else str(right_shoulder_idx),
                                        "time": right_shoulder_time
                                    },
                                    
                                    # Key levels
                                    "neckline": float(neckline),
                                    "current_price": float(current_price),
                                    "target_price": float(target_price),
                                    "pattern_height": float(pattern_height),
                                    
                                    # Time/Price coordinates for frontend
                                    "start_time": left_shoulder_time,
                                    "end_time": right_shoulder_time,
                                    "start_price": float(left_shoulder_low),
                                    "end_price": float(current_price),
                                    "key_points": {
                                        "left_shoulder": {"time": left_shoulder_time, "price": float(left_shoulder_low)},
                                        "head": {"time": head_time, "price": float(head_low)},
                                        "right_shoulder": {"time": right_shoulder_time, "price": float(right_shoulder_low)},
                                        "neckline": {"time": right_shoulder_time, "price": float(neckline)}
                                    },
                                    
                                    # Analysis
                                    "confidence": float(confidence),
                                    "potential_upside": float(potential_upside),
                                    "pattern_completion": "forming" if _to_python_type(current_price) < _to_python_type(neckline) else "completed",
                                    
                                    # Trading implications
                                    "trading_implications": {
                                        "signal": "BUY" if confidence > 0.6 else "WATCH",
                                        "entry_price": float(current_price),
                                        "stop_loss": float(head_low * 0.98),  # 2% below head
                                        "target_price": float(target_price),
                                        "risk_reward_ratio": float((target_price - current_price) / (current_price - head_low * 0.98)) if (current_price - head_low * 0.98) > 0 else 0,
                                        "holding_period": "3-4 months" if timeframe in ["1W", "1M"] else "1-2 months"
                                    },
                                    
                                    # Pattern description
                                    "description": (
                                        f"Reverse Head & Shoulder pattern detected. "
                                        f"Current price: ₹{current_price:.2f}, "
                                        f"Target: ₹{target_price:.2f} "
                                        f"(Potential upside: {potential_upside:.2f}%). "
                                        f"Pattern forming with {confidence*100:.1f}% confidence."
                                    ),
                                    
                                    # Technical analysis
                                    "technical_analysis": {
                                        "pattern_strength": "strong" if confidence > 0.7 else "moderate",
                                        "neckline_breakout_required": bool(current_price < neckline),  # Convert to Python bool
                                        "volume_confirmation": bool(self._check_volume_confirmation(df, right_shoulder_idx)),  # Convert to Python bool
                                        "trend_alignment": "bullish_reversal"
                                    }
                                }
                                
                                best_confidence = confidence
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Error detecting reverse head & shoulder: {e}")
            return None
    
    def detect_head_shoulder(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Head & Shoulder pattern (Bearish Reversal)"""
        try:
            if len(df) < 30:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            dates = df.index if hasattr(df.index, 'tolist') else range(len(df))
            
            # Find swing highs (peaks)
            swing_highs = self._find_swing_highs(highs, window=5)
            
            if len(swing_highs) < 3:
                return None
            
            best_pattern = None
            best_confidence = 0
            
            for i in range(len(swing_highs) - 2):
                left_shoulder_idx = swing_highs[i]
                head_idx = swing_highs[i + 1]
                right_shoulder_idx = swing_highs[i + 2]
                
                left_shoulder_high = highs[left_shoulder_idx]
                head_high = highs[head_idx]
                right_shoulder_high = highs[right_shoulder_idx]
                
                if (head_high > left_shoulder_high and 
                    head_high > right_shoulder_high):
                    
                    shoulder_diff = abs(left_shoulder_high - right_shoulder_high) / max(left_shoulder_high, right_shoulder_high)
                    
                    if shoulder_diff < 0.05:
                        neckline = self._find_neckline(
                            df, left_shoulder_idx, head_idx, right_shoulder_idx, is_reverse=False
                        )
                        
                        if neckline:
                            pattern_height = head_high - neckline
                            confidence = self._calculate_hs_confidence(
                                df, left_shoulder_idx, head_idx, right_shoulder_idx,
                                left_shoulder_high, head_high, right_shoulder_high,
                                neckline, pattern_height
                            )
                            
                            if confidence > best_confidence:
                                target_price = neckline - pattern_height
                                current_price = closes[-1]
                                potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                                
                                # Get time coordinates
                                left_shoulder_time = self._get_time_from_index(df, left_shoulder_idx)
                                head_time = self._get_time_from_index(df, head_idx)
                                right_shoulder_time = self._get_time_from_index(df, right_shoulder_idx)
                                
                                best_pattern = {
                                    "pattern_type": "head_shoulder",
                                    "pattern_name": "Head & Shoulder",
                                    "pattern_category": "reversal",
                                    "pattern_direction": "bearish",
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "detected_at": datetime.now().isoformat(),
                                    "left_shoulder": {"index": int(left_shoulder_idx), "price": float(left_shoulder_high), "time": left_shoulder_time},
                                    "head": {"index": int(head_idx), "price": float(head_high), "time": head_time},
                                    "right_shoulder": {"index": int(right_shoulder_idx), "price": float(right_shoulder_high), "time": right_shoulder_time},
                                    "neckline": float(neckline),
                                    "current_price": float(current_price),
                                    "target_price": float(target_price),
                                    "confidence": float(confidence),
                                    "potential_downside": float(potential_downside),
                                    "start_time": left_shoulder_time,
                                    "end_time": right_shoulder_time,
                                    "start_price": float(left_shoulder_high),
                                    "end_price": float(current_price),
                                    "key_points": {
                                        "left_shoulder": {"time": left_shoulder_time, "price": float(left_shoulder_high)},
                                        "head": {"time": head_time, "price": float(head_high)},
                                        "right_shoulder": {"time": right_shoulder_time, "price": float(right_shoulder_high)},
                                        "neckline": {"time": right_shoulder_time, "price": float(neckline)}
                                    },
                                    "trading_implications": {
                                        "signal": "SELL" if confidence > 0.6 else "WATCH",
                                        "target_price": float(target_price)
                                    }
                                }
                                best_confidence = confidence
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Error detecting head & shoulder: {e}")
            return None
    
    def detect_cup_handle(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Cup & Handle pattern (Bullish Continuation)"""
        try:
            if len(df) < 40:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Look for U-shaped cup formation
            # Cup should be 20-40% of total data
            cup_length = len(df) // 3
            
            best_pattern = None
            best_confidence = 0
            
            for start_idx in range(10, len(df) - cup_length - 10):
                cup_data = df.iloc[start_idx:start_idx + cup_length]
                cup_highs = cup_data["high"].values
                cup_lows = cup_data["low"].values
                
                # Check for U-shape (rounded bottom)
                left_side = cup_lows[:len(cup_lows)//2]
                right_side = cup_lows[len(cup_lows)//2:]
                
                # Cup should have rounded bottom
                middle_low = min(cup_lows)
                left_low = min(left_side)
                right_low = min(right_side)
                
                # Check if it forms a U (middle is lowest)
                if middle_low < left_low * 0.98 and middle_low < right_low * 0.98:
                    # Find handle (small pullback after cup)
                    handle_start = start_idx + cup_length
                    handle_end = min(handle_start + cup_length // 3, len(df))
                    
                    if handle_end < len(df):
                        handle_data = df.iloc[handle_start:handle_end]
                        handle_high = handle_data["high"].max()
                        cup_rim = cup_data["high"].max()
                        
                        # Handle should be below cup rim
                        if handle_high < cup_rim * 0.98:
                            confidence = 0.65  # Base confidence for cup & handle
                            
                            if confidence > best_confidence:
                                target_price = cup_rim + (cup_rim - middle_low) * 0.5
                                current_price = closes[-1]
                                potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                                
                                # Get time indices for pattern visualization
                                cup_start_idx = start_idx
                                cup_end_idx = start_idx + cup_length
                                handle_end_idx = handle_end
                                
                                # Convert indices to time if available
                                start_time = df.index[cup_start_idx] if hasattr(df.index[cup_start_idx], '__int__') else cup_start_idx
                                end_time = df.index[handle_end_idx - 1] if handle_end_idx > 0 and hasattr(df.index[handle_end_idx - 1], '__int__') else handle_end_idx - 1
                                
                                best_pattern = {
                                    "pattern_type": "cup_handle",
                                    "pattern_name": "Cup & Handle",
                                    "pattern_category": "continuation",
                                    "pattern_direction": "bullish",
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "detected_at": datetime.now().isoformat(),
                                    "cup_bottom": float(middle_low),
                                    "cup_rim": float(cup_rim),
                                    "current_price": float(current_price),
                                    "target_price": float(target_price),
                                    "confidence": float(confidence),
                                    "potential_upside": float(potential_upside),
                                    "start_time": int(start_time) if isinstance(start_time, (int, float)) else None,
                                    "end_time": int(end_time) if isinstance(end_time, (int, float)) else None,
                                    "start_price": float(cup_data["low"].iloc[0]),
                                    "end_price": float(handle_data["close"].iloc[-1]) if len(handle_data) > 0 else float(current_price),
                                    "key_points": {
                                        "cup_start": {"time": int(start_time) if isinstance(start_time, (int, float)) else None, "price": float(cup_data["high"].iloc[0])},
                                        "cup_bottom": {"time": int(df.index[cup_data["low"].idxmin()]) if hasattr(df.index[cup_data["low"].idxmin()], '__int__') else None, "price": float(middle_low)},
                                        "cup_rim": {"time": int(df.index[cup_data["high"].idxmax()]) if hasattr(df.index[cup_data["high"].idxmax()], '__int__') else None, "price": float(cup_rim)},
                                        "handle_end": {"time": int(end_time) if isinstance(end_time, (int, float)) else None, "price": float(handle_data["close"].iloc[-1]) if len(handle_data) > 0 else float(current_price)}
                                    },
                                    "trading_implications": {
                                        "signal": "BUY",
                                        "target_price": float(target_price)
                                    }
                                }
                                best_confidence = confidence
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Error detecting cup & handle: {e}")
            return None
    
    def detect_double_top(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Double Top pattern (Bearish Reversal) - Enhanced Algorithm"""
        try:
            if len(df) < 30:  # Need more data for reliable detection
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Find swing highs with better parameters
            swing_highs = self._find_swing_highs(highs, window=5)
            
            if len(swing_highs) < 2:
                return None
            
            # Look for double top pattern
            best_pattern = None
            highest_confidence = 0
            
            for i in range(len(swing_highs) - 1):
                first_idx = swing_highs[i]
                second_idx = swing_highs[i + 1]
                
                # Ensure peaks are separated by at least 5 candles
                if second_idx - first_idx < 5:
                    continue
                
                first_peak = highs[first_idx]
                second_peak = highs[second_idx]
                
                # Check if peaks are similar (within 2% tolerance - tighter than before)
                peak_diff_pct = abs(first_peak - second_peak) / first_peak
                if peak_diff_pct > 0.02:  # 2% tolerance for double top
                    continue
                
                # Find neckline (lowest point between the two peaks)
                neckline = lows[first_idx:second_idx+1].min()
                
                # Ensure there's a proper valley between peaks
                valley_idx = first_idx + lows[first_idx:second_idx+1].argmin()
                valley_depth = (first_peak - neckline) / first_peak
                
                # Valley should be at least 3% below peaks for valid double top
                if valley_depth < 0.03:
                    continue
                
                # Calculate pattern metrics
                resistance_level = (first_peak + second_peak) / 2
                pattern_height = first_peak - neckline
                target_price = neckline - pattern_height  # Bearish target
                current_price = closes[-1]
                
                # Calculate confidence based on multiple factors
                confidence = 0.5  # Base confidence
                
                # Higher confidence if peaks are very similar
                if peak_diff_pct < 0.01:  # Within 1%
                    confidence += 0.15
                elif peak_diff_pct < 0.015:  # Within 1.5%
                    confidence += 0.10
                
                # Higher confidence if valley is deep enough
                if valley_depth > 0.05:  # 5%+ valley
                    confidence += 0.10
                elif valley_depth > 0.04:  # 4%+ valley
                    confidence += 0.05
                
                # Higher confidence if pattern is recent (within last 30% of data)
                pattern_age = (len(df) - second_idx) / len(df)
                if pattern_age < 0.3:  # Pattern in last 30% of data
                    confidence += 0.10
                elif pattern_age < 0.5:  # Pattern in last 50% of data
                    confidence += 0.05
                
                # Higher confidence if price is currently near or below neckline
                if current_price <= neckline * 1.02:  # Within 2% of neckline or below
                    confidence += 0.10
                elif current_price <= resistance_level:  # Below resistance
                    confidence += 0.05
                
                # Cap confidence at 0.95
                confidence = min(0.95, confidence)
                
                # Only consider patterns with reasonable confidence
                if confidence >= 0.60 and confidence > highest_confidence:
                    best_pattern = {
                        "pattern_type": "double_top",
                        "pattern_name": "Double Top",
                        "pattern_category": "reversal",
                        "pattern_direction": "bearish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "first_peak": float(first_peak),
                        "second_peak": float(second_peak),
                        "first_peak_time": df.index[first_idx] if hasattr(df.index[first_idx], 'timestamp') else first_idx,
                        "second_peak_time": df.index[second_idx] if hasattr(df.index[second_idx], 'timestamp') else second_idx,
                        "neckline": float(neckline),
                        "resistance_level": float(resistance_level),  # Key resistance level
                        "valley_depth_pct": float(valley_depth * 100),
                        "peak_similarity_pct": float(peak_diff_pct * 100),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "pattern_height": float(pattern_height),
                        "confidence": round(confidence, 2),
                        "description": f"Double Top resistance at ₹{resistance_level:.2f}. Bearish reversal pattern with {confidence*100:.0f}% confidence.",
                        "trading_implications": {
                            "signal": "SELL",
                            "target_price": float(target_price),
                            "stop_loss": float(resistance_level * 1.02),  # 2% above resistance
                            "entry_price": float(current_price),
                            "risk_reward_ratio": round((resistance_level - target_price) / (resistance_level - current_price), 2) if current_price < resistance_level else 0
                        }
                    }
                    highest_confidence = confidence
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Error detecting double top: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def detect_double_bottom(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Double Bottom pattern (Bullish Reversal)"""
        try:
            if len(df) < 20:
                return None
            
            lows = df["low"].values
            swing_lows = self._find_swing_lows(lows, window=5)
            
            if len(swing_lows) < 2:
                return None
            
            for i in range(len(swing_lows) - 1):
                first_trough = lows[swing_lows[i]]
                second_trough = lows[swing_lows[i + 1]]
                
                if abs(first_trough - second_trough) / first_trough < 0.03:
                    # Get the slice for calculating neckline
                    start_idx = int(swing_lows[i])
                    end_idx = int(swing_lows[i + 1])
                    
                    # Ensure valid indices
                    if start_idx >= len(df) or end_idx >= len(df) or start_idx < 0 or end_idx < 0:
                        continue
                    
                    neckline = df.iloc[start_idx:end_idx+1]["high"].max()
                    target_price = neckline + (neckline - first_trough)
                    current_price = df["close"].iloc[-1]
                    potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                    
                    # Get time indices - use integer positions
                    first_trough_idx = int(swing_lows[i])
                    second_trough_idx = int(swing_lows[i + 1])
                    
                    # Find neckline position using integer index
                    neckline_slice = df.iloc[start_idx:end_idx+1]
                    neckline_pos = neckline_slice["high"].idxmax()
                    
                    # Convert neckline_pos to integer position if it's a label
                    if isinstance(neckline_pos, (int, np.integer)):
                        neckline_idx = int(neckline_pos)
                    else:
                        # If it's a label (like datetime), find its position
                        try:
                            neckline_idx = df.index.get_loc(neckline_pos)
                            if isinstance(neckline_idx, slice):
                                neckline_idx = neckline_idx.start if neckline_idx.start is not None else start_idx
                            elif isinstance(neckline_idx, np.ndarray):
                                neckline_idx = int(neckline_idx[0]) if len(neckline_idx) > 0 else start_idx
                            else:
                                neckline_idx = int(neckline_idx) if isinstance(neckline_idx, (int, np.integer)) else start_idx
                        except (KeyError, TypeError, AttributeError):
                            neckline_idx = start_idx
                    
                    # Get time values safely
                    try:
                        start_time = df.index[first_trough_idx]
                        end_time = df.index[second_trough_idx]
                        neckline_time = df.index[neckline_idx] if neckline_idx < len(df.index) else df.index[start_idx]
                    except (IndexError, KeyError, TypeError):
                        start_time = None
                        end_time = None
                        neckline_time = None
                    
                    # Convert times to integers if they're timestamps
                    def safe_time_to_int(time_val):
                        if time_val is None:
                            return None
                        if isinstance(time_val, (int, np.integer)):
                            return int(time_val)
                        elif isinstance(time_val, (float, np.floating)):
                            return int(time_val)
                        elif hasattr(time_val, 'timestamp'):
                            return int(time_val.timestamp())
                        elif hasattr(time_val, '__int__'):
                            return int(time_val)
                        else:
                            return None
                    
                    return {
                        "pattern_type": "double_bottom",
                        "pattern_name": "Double Bottom",
                        "pattern_category": "reversal",
                        "pattern_direction": "bullish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "first_trough": float(first_trough),
                        "second_trough": float(second_trough),
                        "neckline": float(neckline),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": 0.65,
                        "potential_upside": float(potential_upside),
                        "start_time": safe_time_to_int(start_time),
                        "end_time": safe_time_to_int(end_time),
                        "start_price": float(first_trough),
                        "end_price": float(second_trough),
                        "key_points": {
                            "first_trough": {"time": safe_time_to_int(start_time), "price": float(first_trough)},
                            "second_trough": {"time": safe_time_to_int(end_time), "price": float(second_trough)},
                            "neckline": {"time": safe_time_to_int(neckline_time), "price": float(neckline)}
                        },
                        "trading_implications": {
                            "signal": "BUY",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting double bottom: {e}")
            return None
    
    # ==================== TRIANGLE PATTERNS ====================
    
    def detect_ascending_triangle(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Ascending Triangle pattern (Bullish Continuation)"""
        try:
            if len(df) < 20:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Find resistance level (horizontal line at top)
            recent_highs = highs[-20:]
            resistance = np.max(recent_highs)
            
            # Find ascending support line (rising lows)
            recent_lows = lows[-20:]
            low_indices = np.arange(len(recent_lows))
            
            # Fit a line to the lows
            if len(low_indices) > 2:
                coeffs = np.polyfit(low_indices, recent_lows, 1)
                slope = coeffs[0]
                
                # Check if support is rising (positive slope)
                if slope > 0:
                    # Check if highs are relatively flat (within 2% of resistance)
                    high_variance = np.std(recent_highs) / np.mean(recent_highs)
                    
                    if high_variance < 0.02:  # Low variance = flat resistance
                        # Calculate pattern metrics
                        support_start = recent_lows[0]
                        support_end = recent_lows[-1]
                        pattern_height = resistance - support_end
                        
                        confidence = 0.7 if high_variance < 0.015 else 0.6
                        
                        target_price = resistance + pattern_height
                        current_price = closes[-1]
                        potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                        
                        # Get time indices
                        pattern_start_idx = len(df) - 20
                        pattern_end_idx = len(df) - 1
                        start_time = self._get_time_from_index(df, pattern_start_idx)
                        end_time = self._get_time_from_index(df, pattern_end_idx)
                        
                        return {
                            "pattern_type": "ascending_triangle",
                            "pattern_name": "Ascending Triangle",
                            "pattern_category": "continuation",
                            "pattern_direction": "bullish",
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "detected_at": datetime.now().isoformat(),
                            "resistance": float(resistance),
                            "support_slope": float(slope),
                            "current_price": float(current_price),
                            "target_price": float(target_price),
                            "confidence": float(confidence),
                            "potential_upside": float(potential_upside),
                            "start_time": start_time,
                            "end_time": end_time,
                            "start_price": float(support_start),
                            "end_price": float(current_price),
                            "key_points": {
                                "resistance": {"time": end_time, "price": float(resistance)},
                                "support_start": {"time": start_time, "price": float(support_start)},
                                "support_end": {"time": end_time, "price": float(support_end)}
                            },
                            "trading_implications": {
                                "signal": "BUY",
                                "entry_price": float(current_price),
                                "stop_loss": float(support_end * 0.98),
                                "target_price": float(target_price)
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting ascending triangle: {e}")
            return None
    
    def detect_descending_triangle(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Descending Triangle pattern (Bearish Continuation)"""
        try:
            if len(df) < 20:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Find support level (horizontal line at bottom)
            recent_lows = lows[-20:]
            support = np.min(recent_lows)
            
            # Find descending resistance line (falling highs)
            recent_highs = highs[-20:]
            high_indices = np.arange(len(recent_highs))
            
            if len(high_indices) > 2:
                coeffs = np.polyfit(high_indices, recent_highs, 1)
                slope = coeffs[0]
                
                # Check if resistance is falling (negative slope)
                if slope < 0:
                    # Check if lows are relatively flat
                    low_variance = np.std(recent_lows) / np.mean(recent_lows)
                    
                    if low_variance < 0.02:
                        pattern_height = np.mean(recent_highs) - support
                        confidence = 0.7 if low_variance < 0.015 else 0.6
                        
                        target_price = support - pattern_height
                        current_price = closes[-1]
                        potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                        
                        return {
                            "pattern_type": "descending_triangle",
                            "pattern_name": "Descending Triangle",
                            "pattern_category": "continuation",
                            "pattern_direction": "bearish",
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "detected_at": datetime.now().isoformat(),
                            "support": float(support),
                            "resistance_slope": float(slope),
                            "current_price": float(current_price),
                            "target_price": float(target_price),
                            "confidence": float(confidence),
                            "potential_downside": float(potential_downside),
                            "trading_implications": {
                                "signal": "SELL",
                                "target_price": float(target_price)
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting descending triangle: {e}")
            return None
    
    def detect_symmetrical_triangle(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Symmetrical Triangle pattern (Continuation/Reversal)"""
        try:
            if len(df) < 20:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            recent_highs = highs[-20:]
            recent_lows = lows[-20:]
            indices = np.arange(len(recent_highs))
            
            if len(indices) > 2:
                # Fit lines to both highs and lows
                high_coeffs = np.polyfit(indices, recent_highs, 1)
                low_coeffs = np.polyfit(indices, recent_lows, 1)
                
                high_slope = high_coeffs[0]
                low_slope = low_coeffs[0]
                
                # Both should converge (highs falling, lows rising)
                if high_slope < 0 and low_slope > 0:
                    # Calculate convergence point
                    apex = (low_coeffs[1] - high_coeffs[1]) / (high_slope - low_slope)
                    
                    # Check if pattern is forming (not yet at apex)
                    if apex > len(recent_highs):
                        pattern_height = np.mean(recent_highs) - np.mean(recent_lows)
                        confidence = 0.65
                        
                        # Direction depends on breakout
                        current_price = closes[-1]
                        midpoint = (np.mean(recent_highs) + np.mean(recent_lows)) / 2
                        
                        direction = "bullish" if current_price > midpoint else "bearish"
                        target_price = current_price + pattern_height if direction == "bullish" else current_price - pattern_height
                        
                        return {
                            "pattern_type": "symmetrical_triangle",
                            "pattern_name": "Symmetrical Triangle",
                            "pattern_category": "continuation",
                            "pattern_direction": direction,
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "detected_at": datetime.now().isoformat(),
                            "apex_price": float(high_coeffs[1] + high_slope * apex),
                            "current_price": float(current_price),
                            "target_price": float(target_price),
                            "confidence": float(confidence),
                            "trading_implications": {
                                "signal": "WATCH",
                                "breakout_direction": direction,
                                "target_price": float(target_price)
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting symmetrical triangle: {e}")
            return None
    
    # ==================== WEDGE PATTERNS ====================
    
    def detect_rising_wedge(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Rising Wedge pattern (Bearish Reversal)"""
        try:
            if len(df) < 20:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            recent_highs = highs[-20:]
            recent_lows = lows[-20:]
            indices = np.arange(len(recent_highs))
            
            if len(indices) > 2:
                high_coeffs = np.polyfit(indices, recent_highs, 1)
                low_coeffs = np.polyfit(indices, recent_lows, 1)
                
                high_slope = high_coeffs[0]
                low_slope = low_coeffs[0]
                
                # Both rising but converging (high slope < low slope)
                if high_slope > 0 and low_slope > 0 and high_slope < low_slope:
                    confidence = 0.65
                    pattern_height = np.mean(recent_highs) - np.mean(recent_lows)
                    target_price = np.mean(recent_lows) - pattern_height
                    current_price = closes[-1]
                    potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                    
                    return {
                        "pattern_type": "rising_wedge",
                        "pattern_name": "Rising Wedge",
                        "pattern_category": "reversal",
                        "pattern_direction": "bearish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": float(confidence),
                        "potential_downside": float(potential_downside),
                        "trading_implications": {
                            "signal": "SELL",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting rising wedge: {e}")
            return None
    
    def detect_falling_wedge(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Falling Wedge pattern (Bullish Reversal)"""
        try:
            if len(df) < 20:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            recent_highs = highs[-20:]
            recent_lows = lows[-20:]
            indices = np.arange(len(recent_highs))
            
            if len(indices) > 2:
                high_coeffs = np.polyfit(indices, recent_highs, 1)
                low_coeffs = np.polyfit(indices, recent_lows, 1)
                
                high_slope = high_coeffs[0]
                low_slope = low_coeffs[0]
                
                # Both falling but converging (high slope > low slope)
                if high_slope < 0 and low_slope < 0 and high_slope > low_slope:
                    confidence = 0.65
                    pattern_height = np.mean(recent_highs) - np.mean(recent_lows)
                    target_price = np.mean(recent_highs) + pattern_height
                    current_price = closes[-1]
                    potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                    
                    # Get time indices
                    pattern_start_idx = len(df) - 20
                    pattern_end_idx = len(df) - 1
                    start_time = self._get_time_from_index(df, pattern_start_idx)
                    end_time = self._get_time_from_index(df, pattern_end_idx)
                    
                    return {
                        "pattern_type": "falling_wedge",
                        "pattern_name": "Falling Wedge",
                        "pattern_category": "reversal",
                        "pattern_direction": "bullish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": float(confidence),
                        "potential_upside": float(potential_upside),
                        "start_time": start_time,
                        "end_time": end_time,
                        "start_price": float(recent_highs[0]),
                        "end_price": float(current_price),
                        "key_points": {
                            "upper_start": {"time": start_time, "price": float(recent_highs[0])},
                            "upper_end": {"time": end_time, "price": float(recent_highs[-1])},
                            "lower_start": {"time": start_time, "price": float(recent_lows[0])},
                            "lower_end": {"time": end_time, "price": float(recent_lows[-1])}
                        },
                        "trading_implications": {
                            "signal": "BUY",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting falling wedge: {e}")
            return None
    
    # ==================== FLAG & PENNANT PATTERNS ====================
    
    def detect_bullish_flag(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Bullish Flag pattern (Continuation)"""
        try:
            if len(df) < 15:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Look for strong upward move followed by consolidation
            # First 40% should be strong up move
            pole_length = len(df) // 2
            flag_length = len(df) - pole_length
            
            if flag_length < 5:
                return None
            
            pole_data = df.iloc[:pole_length]
            flag_data = df.iloc[pole_length:]
            
            pole_high = pole_data["high"].max()
            pole_low = pole_data["low"].min()
            pole_range = pole_high - pole_low
            
            flag_high = flag_data["high"].max()
            flag_low = flag_data["low"].min()
            flag_range = flag_high - flag_low
            
            # Flag should be small consolidation (20-40% of pole)
            if 0.2 <= flag_range / pole_range <= 0.4:
                # Flag should be slightly downward or horizontal
                flag_slope = (flag_data["close"].iloc[-1] - flag_data["close"].iloc[0]) / len(flag_data)
                
                if flag_slope < pole_range * 0.1:  # Relatively flat or slightly down
                    confidence = 0.7
                    target_price = pole_high + pole_range
                    current_price = closes[-1]
                    potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                    
                    return {
                        "pattern_type": "bullish_flag",
                        "pattern_name": "Bullish Flag",
                        "pattern_category": "continuation",
                        "pattern_direction": "bullish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "pole_height": float(pole_range),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": float(confidence),
                        "potential_upside": float(potential_upside),
                        "trading_implications": {
                            "signal": "BUY",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting bullish flag: {e}")
            return None
    
    def detect_bearish_flag(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Bearish Flag pattern (Continuation)"""
        try:
            if len(df) < 15:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            pole_length = len(df) // 2
            flag_length = len(df) - pole_length
            
            if flag_length < 5:
                return None
            
            pole_data = df.iloc[:pole_length]
            flag_data = df.iloc[pole_length:]
            
            pole_high = pole_data["high"].max()
            pole_low = pole_data["low"].min()
            pole_range = pole_high - pole_low
            
            flag_high = flag_data["high"].max()
            flag_low = flag_data["low"].min()
            flag_range = flag_high - flag_low
            
            if 0.2 <= flag_range / pole_range <= 0.4:
                flag_slope = (flag_data["close"].iloc[-1] - flag_data["close"].iloc[0]) / len(flag_data)
                
                if flag_slope > -pole_range * 0.1:  # Relatively flat or slightly up
                    confidence = 0.7
                    target_price = pole_low - pole_range
                    current_price = closes[-1]
                    potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                    
                    return {
                        "pattern_type": "bearish_flag",
                        "pattern_name": "Bearish Flag",
                        "pattern_category": "continuation",
                        "pattern_direction": "bearish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "pole_height": float(pole_range),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": float(confidence),
                        "potential_downside": float(potential_downside),
                        "trading_implications": {
                            "signal": "SELL",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting bearish flag: {e}")
            return None
    
    def detect_bullish_pennant(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Bullish Pennant pattern (Continuation)"""
        try:
            if len(df) < 15:
                return None
            
            # Similar to flag but with converging trendlines
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            pole_length = len(df) // 2
            pennant_length = len(df) - pole_length
            
            if pennant_length < 5:
                return None
            
            pole_data = df.iloc[:pole_length]
            pennant_data = df.iloc[pole_length:]
            
            pole_high = pole_data["high"].max()
            pole_low = pole_data["low"].min()
            pole_range = pole_high - pole_low
            
            pennant_highs = pennant_data["high"].values
            pennant_lows = pennant_data["low"].values
            indices = np.arange(len(pennant_highs))
            
            if len(indices) > 2:
                high_coeffs = np.polyfit(indices, pennant_highs, 1)
                low_coeffs = np.polyfit(indices, pennant_lows, 1)
                
                # Converging lines (triangle shape)
                if abs(high_coeffs[0] - low_coeffs[0]) > 0:
                    pennant_range = np.mean(pennant_highs) - np.mean(pennant_lows)
                    
                    if 0.15 <= pennant_range / pole_range <= 0.35:
                        confidence = 0.7
                        target_price = pole_high + pole_range
                        current_price = closes[-1]
                        potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                        
                        # Get time indices
                        pole_start_idx = 0
                        pole_end_idx = pole_length
                        pennant_start_idx = pole_length
                        pennant_end_idx = len(df) - 1
                        start_time = self._get_time_from_index(df, pole_start_idx)
                        end_time = self._get_time_from_index(df, pennant_end_idx)
                        
                        return {
                            "pattern_type": "bullish_pennant",
                            "pattern_name": "Bullish Pennant",
                            "pattern_category": "continuation",
                            "pattern_direction": "bullish",
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "detected_at": datetime.now().isoformat(),
                            "pole_height": float(pole_range),
                            "current_price": float(current_price),
                            "target_price": float(target_price),
                            "confidence": float(confidence),
                            "potential_upside": float(potential_upside),
                            "start_time": start_time,
                            "end_time": end_time,
                            "start_price": float(pole_low),
                            "end_price": float(current_price),
                            "key_points": {
                                "pole_start": {"time": start_time, "price": float(pole_low)},
                                "pole_end": {"time": self._get_time_from_index(df, pole_end_idx), "price": float(pole_high)},
                                "pennant_start": {"time": self._get_time_from_index(df, pennant_start_idx), "price": float(pennant_data["close"].iloc[0]) if len(pennant_data) > 0 else float(current_price)},
                                "pennant_end": {"time": end_time, "price": float(current_price)}
                            },
                            "trading_implications": {
                                "signal": "BUY",
                                "target_price": float(target_price)
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting bullish pennant: {e}")
            return None
    
    def detect_bearish_pennant(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Bearish Pennant pattern (Continuation)"""
        try:
            if len(df) < 15:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            pole_length = len(df) // 2
            pennant_length = len(df) - pole_length
            
            if pennant_length < 5:
                return None
            
            pole_data = df.iloc[:pole_length]
            pennant_data = df.iloc[pole_length:]
            
            pole_high = pole_data["high"].max()
            pole_low = pole_data["low"].min()
            pole_range = pole_high - pole_low
            
            pennant_highs = pennant_data["high"].values
            pennant_lows = pennant_data["low"].values
            indices = np.arange(len(pennant_highs))
            
            if len(indices) > 2:
                high_coeffs = np.polyfit(indices, pennant_highs, 1)
                low_coeffs = np.polyfit(indices, pennant_lows, 1)
                
                if abs(high_coeffs[0] - low_coeffs[0]) > 0:
                    pennant_range = np.mean(pennant_highs) - np.mean(pennant_lows)
                    
                    if 0.15 <= pennant_range / pole_range <= 0.35:
                        confidence = 0.7
                        target_price = pole_low - pole_range
                        current_price = closes[-1]
                        potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                        
                        return {
                            "pattern_type": "bearish_pennant",
                            "pattern_name": "Bearish Pennant",
                            "pattern_category": "continuation",
                            "pattern_direction": "bearish",
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "detected_at": datetime.now().isoformat(),
                            "pole_height": float(pole_range),
                            "current_price": float(current_price),
                            "target_price": float(target_price),
                            "confidence": float(confidence),
                            "potential_downside": float(potential_downside),
                            "trading_implications": {
                                "signal": "SELL",
                                "target_price": float(target_price)
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting bearish pennant: {e}")
            return None
    
    # ==================== OTHER PATTERNS ====================
    
    def detect_rectangular_range(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Rectangular Range pattern (Consolidation)"""
        try:
            if len(df) < 20:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Check for horizontal support and resistance
            recent_highs = highs[-20:]
            recent_lows = lows[-20:]
            
            high_mean = np.mean(recent_highs)
            low_mean = np.mean(recent_lows)
            high_std = np.std(recent_highs)
            low_std = np.std(recent_lows)
            
            # Low variance indicates horizontal lines
            if high_std / high_mean < 0.02 and low_std / low_mean < 0.02:
                resistance = np.max(recent_highs)
                support = np.min(recent_lows)
                range_height = resistance - support
                
                confidence = 0.6
                current_price = closes[-1]
                
                # Breakout direction depends on which side price is closer to
                if current_price > (resistance + support) / 2:
                    target_price = resistance + range_height
                    direction = "bullish"
                else:
                    target_price = support - range_height
                    direction = "bearish"
                
                return {
                    "pattern_type": "rectangular_range",
                    "pattern_name": "Rectangular Range",
                    "pattern_category": "consolidation",
                    "pattern_direction": direction,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "detected_at": datetime.now().isoformat(),
                    "resistance": float(resistance),
                    "support": float(support),
                    "current_price": float(current_price),
                    "target_price": float(target_price),
                    "confidence": float(confidence),
                    "trading_implications": {
                        "signal": "WATCH",
                        "breakout_direction": direction,
                        "target_price": float(target_price)
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting rectangular range: {e}")
            return None
    
    def detect_rounding_top(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Rounding Top pattern (Bearish Reversal)"""
        try:
            if len(df) < 30:
                return None
            
            highs = df["high"].values
            closes = df["close"].values
            
            # Look for U-shaped (inverted) pattern in highs
            mid_point = len(highs) // 2
            left_highs = highs[:mid_point]
            right_highs = highs[mid_point:]
            
            # Check if pattern forms inverted U
            left_trend = np.polyfit(np.arange(len(left_highs)), left_highs, 1)[0]
            right_trend = np.polyfit(np.arange(len(right_highs)), right_highs, 1)[0]
            
            # Left should be rising, right should be falling
            if left_trend > 0 and right_trend < 0:
                peak = np.max(highs)
                current_price = closes[-1]
                
                # Calculate target (mirror the rise)
                rise = peak - highs[0]
                target_price = peak - rise
                potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                
                return {
                    "pattern_type": "rounding_top",
                    "pattern_name": "Rounding Top",
                    "pattern_category": "reversal",
                    "pattern_direction": "bearish",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "detected_at": datetime.now().isoformat(),
                    "peak_price": float(peak),
                    "current_price": float(current_price),
                    "target_price": float(target_price),
                    "confidence": 0.65,
                    "potential_downside": float(potential_downside),
                    "trading_implications": {
                        "signal": "SELL",
                        "target_price": float(target_price)
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting rounding top: {e}")
            return None
    
    def detect_rounding_bottom(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Rounding Bottom pattern (Bullish Reversal)"""
        try:
            if len(df) < 30:
                return None
            
            lows = df["low"].values
            closes = df["close"].values
            
            mid_point = len(lows) // 2
            left_lows = lows[:mid_point]
            right_lows = lows[mid_point:]
            
            left_trend = np.polyfit(np.arange(len(left_lows)), left_lows, 1)[0]
            right_trend = np.polyfit(np.arange(len(right_lows)), right_lows, 1)[0]
            
            # Left should be falling, right should be rising
            if left_trend < 0 and right_trend > 0:
                trough = np.min(lows)
                current_price = closes[-1]
                
                fall = lows[0] - trough
                target_price = trough + fall
                potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                
                return {
                    "pattern_type": "rounding_bottom",
                    "pattern_name": "Rounding Bottom",
                    "pattern_category": "reversal",
                    "pattern_direction": "bullish",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "detected_at": datetime.now().isoformat(),
                    "trough_price": float(trough),
                    "current_price": float(current_price),
                    "target_price": float(target_price),
                    "confidence": 0.65,
                    "potential_upside": float(potential_upside),
                    "trading_implications": {
                        "signal": "BUY",
                        "target_price": float(target_price)
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting rounding bottom: {e}")
            return None
    
    def detect_diamond_pattern(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Diamond Pattern (Reversal)"""
        try:
            if len(df) < 30:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Diamond: expanding then contracting
            mid_point = len(df) // 2
            first_half = df.iloc[:mid_point]
            second_half = df.iloc[mid_point:]
            
            first_range = first_half["high"].max() - first_half["low"].min()
            second_range = second_half["high"].max() - second_half["low"].min()
            
            # First half should expand, second half should contract
            if first_range < second_range * 0.8:
                # Check for expanding then contracting volatility
                first_volatility = first_half["close"].std()
                second_volatility = second_half["close"].std()
                
                if first_volatility < second_volatility * 0.7:
                    peak = highs.max()
                    trough = lows.min()
                    current_price = closes[-1]
                    
                    # Target is typically the height of the pattern
                    pattern_height = peak - trough
                    target_price = trough - pattern_height if current_price < (peak + trough) / 2 else peak + pattern_height
                    
                    direction = "bearish" if current_price < (peak + trough) / 2 else "bullish"
                    
                    return {
                        "pattern_type": "diamond",
                        "pattern_name": "Diamond Pattern",
                        "pattern_category": "reversal",
                        "pattern_direction": direction,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "peak_price": float(peak),
                        "trough_price": float(trough),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": 0.6,
                        "trading_implications": {
                            "signal": "SELL" if direction == "bearish" else "BUY",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting diamond pattern: {e}")
            return None
    
    def detect_island_reversal(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Island Reversal pattern"""
        try:
            if len(df) < 10:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            opens = df["open"].values if "open" in df.columns else closes
            
            # Look for gap up, then gap down (or vice versa)
            for i in range(1, len(df) - 1):
                prev_high = highs[i-1]
                curr_low = lows[i]
                next_low = lows[i+1]
                curr_high = highs[i]
                prev_low = lows[i-1]
                
                # Gap up then gap down (bearish island)
                if curr_low > prev_high * 1.01 and next_low > curr_high * 1.01:
                    # Island formed
                    island_high = highs[i]
                    island_low = lows[i]
                    current_price = closes[-1]
                    target_price = prev_low
                    potential_downside = ((current_price - target_price) / current_price) * 100 if current_price > 0 else 0
                    
                    return {
                        "pattern_type": "island_reversal_bearish",
                        "pattern_name": "Island Reversal (Bearish)",
                        "pattern_category": "reversal",
                        "pattern_direction": "bearish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "island_high": float(island_high),
                        "island_low": float(island_low),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": 0.7,
                        "potential_downside": float(potential_downside),
                        "trading_implications": {
                            "signal": "SELL",
                            "target_price": float(target_price)
                        }
                    }
                
                # Gap down then gap up (bullish island)
                elif curr_high < prev_low * 0.99 and i < len(df) - 1 and highs[i + 1] < curr_low * 0.99:
                    island_high = highs[i]
                    island_low = lows[i]
                    current_price = closes[-1]
                    target_price = prev_high
                    potential_upside = ((target_price - current_price) / current_price) * 100 if current_price > 0 else 0
                    
                    return {
                        "pattern_type": "island_reversal_bullish",
                        "pattern_name": "Island Reversal (Bullish)",
                        "pattern_category": "reversal",
                        "pattern_direction": "bullish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "island_high": float(island_high),
                        "island_low": float(island_low),
                        "current_price": float(current_price),
                        "target_price": float(target_price),
                        "confidence": 0.7,
                        "potential_upside": float(potential_upside),
                        "trading_implications": {
                            "signal": "BUY",
                            "target_price": float(target_price)
                        }
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting island reversal: {e}")
            return None
    
    def detect_gaps(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Detect various gap patterns"""
        gaps = []
        
        try:
            if len(df) < 2:
                return gaps
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            opens = df["open"].values if "open" in df.columns else closes
            
            for i in range(1, len(df)):
                prev_high = highs[i-1]
                prev_low = lows[i-1]
                curr_low = lows[i]
                curr_high = highs[i]
                prev_close = closes[i-1]
                curr_open = opens[i]
                
                # Gap up
                if curr_low > prev_high:
                    gap_size = curr_low - prev_high
                    gap_percent = (gap_size / prev_high) * 100
                    
                    # Classify gap type
                    if i == 1 or (i > 1 and lows[i-2] > prev_high):
                        gap_type = "breakaway"
                    elif i < len(df) - 1 and lows[i+1] < curr_low:
                        gap_type = "exhaustion"
                    elif i < len(df) - 1:
                        gap_type = "runaway"
                    else:
                        gap_type = "common"
                    
                    gaps.append({
                        "pattern_type": f"gap_{gap_type}_up",
                        "pattern_name": f"{gap_type.capitalize()} Gap Up",
                        "pattern_category": "gap",
                        "pattern_direction": "bullish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "gap_size": float(gap_size),
                        "gap_percent": float(gap_percent),
                        "gap_start": float(prev_high),
                        "gap_end": float(curr_low),
                        "confidence": 0.8 if gap_type != "common" else 0.5,
                        "trading_implications": {
                            "signal": "BUY" if gap_type == "breakaway" else "WATCH",
                            "gap_type": gap_type
                        }
                    })
                
                # Gap down
                elif curr_high < prev_low:
                    gap_size = prev_low - curr_high
                    gap_percent = (gap_size / prev_low) * 100
                    
                    if i == 1 or (i > 1 and highs[i-2] < prev_low):
                        gap_type = "breakaway"
                    elif i < len(df) - 1 and highs[i+1] > curr_high:
                        gap_type = "exhaustion"
                    elif i < len(df) - 1:
                        gap_type = "runaway"
                    else:
                        gap_type = "common"
                    
                    gaps.append({
                        "pattern_type": f"gap_{gap_type}_down",
                        "pattern_name": f"{gap_type.capitalize()} Gap Down",
                        "pattern_category": "gap",
                        "pattern_direction": "bearish",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "gap_size": float(gap_size),
                        "gap_percent": float(gap_percent),
                        "gap_start": float(prev_low),
                        "gap_end": float(curr_high),
                        "confidence": 0.8 if gap_type != "common" else 0.5,
                        "trading_implications": {
                            "signal": "SELL" if gap_type == "breakaway" else "WATCH",
                            "gap_type": gap_type
                        }
                    })
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error detecting gaps: {e}")
            return gaps
    
    # ==================== HARMONIC PATTERNS ====================
    
    def detect_harmonic_patterns(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Detect all harmonic patterns (Gartley, Butterfly, Bat, Crab, Shark, Cypher, etc.)"""
        patterns = []
        
        try:
            if len(df) < 20:
                return patterns
            
            # Ensure we have required columns
            required_cols = ['high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing required columns for harmonic pattern detection: {df.columns.tolist()}")
                return patterns
            
            # Find swing points
            try:
                highs = df["high"].values
                lows = df["low"].values
            except KeyError as e:
                logger.warning(f"Missing price columns for harmonic detection: {e}")
                return patterns
            
            swing_highs = self._find_swing_highs(highs, window=3)
            swing_lows = self._find_swing_lows(lows, window=3)
            
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return patterns
            
            # Try to detect XABCD patterns
            all_points = sorted(set(swing_highs + swing_lows))
            
            if len(all_points) >= 5:
                # Look for XABCD pattern
                for i in range(len(all_points) - 4):
                    x_idx = all_points[i]
                    a_idx = all_points[i + 1]
                    b_idx = all_points[i + 2]
                    c_idx = all_points[i + 3]
                    d_idx = all_points[i + 4]
                    
                    # Get prices
                    if x_idx in swing_highs:
                        x_price = highs[x_idx]
                    else:
                        x_price = lows[x_idx]
                    
                    if a_idx in swing_highs:
                        a_price = highs[a_idx]
                    else:
                        a_price = lows[a_idx]
                    
                    if b_idx in swing_highs:
                        b_price = highs[b_idx]
                    else:
                        b_price = lows[b_idx]
                    
                    if c_idx in swing_highs:
                        c_price = highs[c_idx]
                    else:
                        c_price = lows[c_idx]
                    
                    if d_idx in swing_highs:
                        d_price = highs[d_idx]
                    else:
                        d_price = lows[d_idx]
                    
                    # Check for Gartley pattern
                    try:
                        gartley = self._check_gartley_pattern(x_price, a_price, b_price, c_price, d_price)
                        if gartley:
                            gartley.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(gartley)
                            continue
                    except Exception as e:
                        logger.debug(f"Error checking Gartley pattern: {e}")
                    
                    # Check for Butterfly pattern
                    try:
                        butterfly = self._check_butterfly_pattern(x_price, a_price, b_price, c_price, d_price)
                        if butterfly:
                            butterfly.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(butterfly)
                            continue
                    except Exception as e:
                        logger.debug(f"Error checking Butterfly pattern: {e}")
                    
                    # Check for Bat pattern
                    try:
                        bat = self._check_bat_pattern(x_price, a_price, b_price, c_price, d_price)
                        if bat:
                            bat.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(bat)
                            continue
                    except Exception as e:
                        logger.debug(f"Error checking Bat pattern: {e}")
                    
                    # Check for Crab pattern
                    try:
                        crab = self._check_crab_pattern(x_price, a_price, b_price, c_price, d_price)
                        if crab:
                            crab.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(crab)
                            continue
                    except Exception as e:
                        logger.debug(f"Error checking Crab pattern: {e}")
                    
                    # Check for Shark pattern
                    try:
                        shark = self._check_shark_pattern(x_price, a_price, b_price, c_price, d_price)
                        if shark:
                            shark.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(shark)
                            continue
                    except Exception as e:
                        logger.debug(f"Error checking Shark pattern: {e}")
                    
                    # Check for Cypher pattern
                    try:
                        cypher = self._check_cypher_pattern(x_price, a_price, b_price, c_price, d_price)
                        if cypher:
                            cypher.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(cypher)
                            continue
                    except Exception as e:
                        logger.debug(f"Error checking Cypher pattern: {e}")
                    
                    # Check for AB=CD pattern
                    try:
                        abcd = self._check_abcd_pattern(x_price, a_price, b_price, c_price, d_price)
                        if abcd:
                            abcd.update({
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat()
                            })
                            patterns.append(abcd)
                    except Exception as e:
                        logger.debug(f"Error checking AB=CD pattern: {e}")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting harmonic patterns: {e}")
            return patterns
    
    def _check_gartley_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for Gartley pattern (XABCD)"""
        try:
            # AB should be 61.8% of XA
            ab_ratio = abs(b - a) / abs(a - x) if abs(a - x) > 0 else 0
            # BC should be 38.2% or 88.6% of AB
            bc_ratio = abs(c - b) / abs(b - a) if abs(b - a) > 0 else 0
            # CD should be 78.6% of XA
            cd_ratio = abs(d - c) / abs(a - x) if abs(a - x) > 0 else 0
            
            # Check if ratios match Gartley (with tolerance)
            if (0.55 <= ab_ratio <= 0.65 and 
                (0.35 <= bc_ratio <= 0.42 or 0.82 <= bc_ratio <= 0.92) and
                0.72 <= cd_ratio <= 0.82):
                return {
                    "pattern_type": "gartley",
                    "pattern_name": "Gartley Pattern",
                    "pattern_category": "harmonic",
                    "pattern_direction": "bullish" if d < c else "bearish",
                    "confidence": 0.7,
                    "prz_price": float(d),
                    "trading_implications": {
                        "signal": "BUY" if d < c else "SELL",
                        "entry_price": float(d),
                        "target_price": float(c + (c - d) * 1.618) if d < c else float(c - (d - c) * 1.618)
                    }
                }
            return None
        except:
            return None
    
    def _check_butterfly_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for Butterfly pattern"""
        try:
            ab_ratio = abs(b - a) / abs(a - x) if abs(a - x) > 0 else 0
            bc_ratio = abs(c - b) / abs(b - a) if abs(b - a) > 0 else 0
            cd_ratio = abs(d - c) / abs(a - x) if abs(a - x) > 0 else 0
            
            # Butterfly: CD should be 127.2% or 161.8% of XA
            if (0.55 <= ab_ratio <= 0.65 and
                0.35 <= bc_ratio <= 0.42 and
                (1.20 <= cd_ratio <= 1.35 or 1.55 <= cd_ratio <= 1.68)):
                return {
                    "pattern_type": "butterfly",
                    "pattern_name": "Butterfly Pattern",
                    "pattern_category": "harmonic",
                    "pattern_direction": "bullish" if d < c else "bearish",
                    "confidence": 0.7,
                    "prz_price": float(d),
                    "trading_implications": {
                        "signal": "BUY" if d < c else "SELL",
                        "entry_price": float(d)
                    }
                }
            return None
        except:
            return None
    
    def _check_bat_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for Bat pattern"""
        try:
            ab_ratio = abs(b - a) / abs(a - x) if abs(a - x) > 0 else 0
            bc_ratio = abs(c - b) / abs(b - a) if abs(b - a) > 0 else 0
            cd_ratio = abs(d - c) / abs(a - x) if abs(a - x) > 0 else 0
            
            # Bat: CD should be 88.6% of XA
            if (0.35 <= ab_ratio <= 0.50 and
                0.35 <= bc_ratio <= 0.42 and
                0.82 <= cd_ratio <= 0.92):
                return {
                    "pattern_type": "bat",
                    "pattern_name": "Bat Pattern",
                    "pattern_category": "harmonic",
                    "pattern_direction": "bullish" if d < c else "bearish",
                    "confidence": 0.75,
                    "prz_price": float(d),
                    "trading_implications": {
                        "signal": "BUY" if d < c else "SELL",
                        "entry_price": float(d)
                    }
                }
            return None
        except:
            return None
    
    def _check_crab_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for Crab pattern"""
        try:
            ab_ratio = abs(b - a) / abs(a - x) if abs(a - x) > 0 else 0
            bc_ratio = abs(c - b) / abs(b - a) if abs(b - a) > 0 else 0
            cd_ratio = abs(d - c) / abs(a - x) if abs(a - x) > 0 else 0
            
            # Crab: CD should be 161.8% of XA
            if (0.35 <= ab_ratio <= 0.50 and
                0.35 <= bc_ratio <= 0.42 and
                1.55 <= cd_ratio <= 1.68):
                return {
                    "pattern_type": "crab",
                    "pattern_name": "Crab Pattern",
                    "pattern_category": "harmonic",
                    "pattern_direction": "bullish" if d < c else "bearish",
                    "confidence": 0.75,
                    "prz_price": float(d),
                    "trading_implications": {
                        "signal": "BUY" if d < c else "SELL",
                        "entry_price": float(d)
                    }
                }
            return None
        except:
            return None
    
    def _check_shark_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for Shark pattern"""
        try:
            ab_ratio = abs(b - a) / abs(a - x) if abs(a - x) > 0 else 0
            bc_ratio = abs(c - b) / abs(b - a) if abs(b - a) > 0 else 0
            cd_ratio = abs(d - c) / abs(a - x) if abs(a - x) > 0 else 0
            
            # Shark: CD should be 50% or 88.6% of XA
            if (0.35 <= ab_ratio <= 0.50 and
                0.35 <= bc_ratio <= 0.42 and
                (0.45 <= cd_ratio <= 0.55 or 0.82 <= cd_ratio <= 0.92)):
                return {
                    "pattern_type": "shark",
                    "pattern_name": "Shark Pattern",
                    "pattern_category": "harmonic",
                    "pattern_direction": "bullish" if d < c else "bearish",
                    "confidence": 0.7,
                    "prz_price": float(d),
                    "trading_implications": {
                        "signal": "BUY" if d < c else "SELL",
                        "entry_price": float(d)
                    }
                }
            return None
        except:
            return None
    
    def _check_cypher_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for Cypher pattern"""
        try:
            ab_ratio = abs(b - a) / abs(a - x) if abs(a - x) > 0 else 0
            bc_ratio = abs(c - b) / abs(b - a) if abs(b - a) > 0 else 0
            cd_ratio = abs(d - c) / abs(a - x) if abs(a - x) > 0 else 0
            
            # Cypher: BC should be 113% or 141.4% of AB, CD should be 78.6% of XA
            if (0.35 <= ab_ratio <= 0.50 and
                (1.08 <= bc_ratio <= 1.18 or 1.36 <= bc_ratio <= 1.46) and
                0.72 <= cd_ratio <= 0.82):
                return {
                    "pattern_type": "cypher",
                    "pattern_name": "Cypher Pattern",
                    "pattern_category": "harmonic",
                    "pattern_direction": "bullish" if d < c else "bearish",
                    "confidence": 0.7,
                    "prz_price": float(d),
                    "trading_implications": {
                        "signal": "BUY" if d < c else "SELL",
                        "entry_price": float(d)
                    }
                }
            return None
        except:
            return None
    
    def _check_abcd_pattern(self, x, a, b, c, d) -> Optional[Dict[str, Any]]:
        """Check for AB=CD pattern"""
        try:
            ab_length = abs(b - a)
            cd_length = abs(d - c)
            bc_ratio = abs(c - b) / ab_length if ab_length > 0 else 0
            
            # AB should equal CD (within 5% tolerance)
            if abs(ab_length - cd_length) / max(ab_length, cd_length) < 0.05:
                # BC should be 38.2%, 50%, or 61.8% of AB
                if 0.35 <= bc_ratio <= 0.42 or 0.47 <= bc_ratio <= 0.53 or 0.58 <= bc_ratio <= 0.65:
                    return {
                        "pattern_type": "abcd",
                        "pattern_name": "AB=CD Pattern",
                        "pattern_category": "harmonic",
                        "pattern_direction": "bullish" if d < c else "bearish",
                        "confidence": 0.75,
                        "prz_price": float(d),
                        "trading_implications": {
                            "signal": "BUY" if d < c else "SELL",
                            "entry_price": float(d),
                            "target_price": float(c + (c - d) * 1.618) if d < c else float(c - (d - c) * 1.618)
                        }
                    }
            return None
        except:
            return None
    
    def _check_three_drives_pattern(self, x, a, b, c, d, e) -> Optional[Dict[str, Any]]:
        """Check for Three Drives pattern (5-point pattern)"""
        try:
            # Three Drives: Three equal moves with specific Fibonacci ratios
            ab_length = abs(b - a)
            cd_length = abs(d - c)
            ef_length = abs(e - d) if e else 0
            
            # All three drives should be approximately equal (within 10% tolerance)
            if ef_length > 0:
                avg_length = (ab_length + cd_length + ef_length) / 3
                if (abs(ab_length - avg_length) / avg_length < 0.1 and
                    abs(cd_length - avg_length) / avg_length < 0.1 and
                    abs(ef_length - avg_length) / avg_length < 0.1):
                    return {
                        "pattern_type": "three_drives",
                        "pattern_name": "Three Drives Pattern",
                        "pattern_category": "harmonic",
                        "pattern_direction": "bullish" if e < d else "bearish",
                        "confidence": 0.75,
                        "prz_price": float(e) if e else None,
                        "trading_implications": {
                            "signal": "BUY" if e < d else "SELL",
                            "entry_price": float(e) if e else None
                        }
                    }
            return None
        except:
            return None
    
    def detect_price_channels(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Price Channel pattern (parallel support and resistance)"""
        try:
            if len(df) < 30:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            
            # Find swing highs and lows
            swing_highs = self._find_swing_highs(highs, window=5)
            swing_lows = self._find_swing_lows(lows, window=5)
            
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return None
            
            # Try to find parallel trendlines
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                # Calculate trendline slopes
                high_slope = (highs[swing_highs[-1]] - highs[swing_highs[0]]) / (swing_highs[-1] - swing_highs[0]) if swing_highs[-1] != swing_highs[0] else 0
                low_slope = (lows[swing_lows[-1]] - lows[swing_lows[0]]) / (swing_lows[-1] - swing_lows[0]) if swing_lows[-1] != swing_lows[0] else 0
                
                # Check if slopes are similar (parallel channels)
                slope_diff = abs(high_slope - low_slope) / max(abs(high_slope), abs(low_slope), 0.001)
                
                if slope_diff < 0.3:  # Parallel within 30%
                    channel_width = abs(highs[swing_highs[-1]] - lows[swing_lows[-1]])
                    current_price = df["close"].iloc[-1]
                    
                    # Determine direction
                    if high_slope > 0:
                        direction = "bullish"
                        signal = "BUY"
                    elif high_slope < 0:
                        direction = "bearish"
                        signal = "SELL"
                    else:
                        direction = "neutral"
                        signal = "HOLD"
                    
                    return {
                        "pattern_type": "price_channel",
                        "pattern_name": "Price Channel",
                        "pattern_category": "classic",
                        "pattern_direction": direction,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "detected_at": datetime.now().isoformat(),
                        "confidence": 0.7,
                        "channel_width": _to_python_type(channel_width),
                        "upper_bound": _to_python_type(highs[swing_highs[-1]]),
                        "lower_bound": _to_python_type(lows[swing_lows[-1]]),
                        "current_price": _to_python_type(current_price),
                        "trading_implications": {
                            "signal": signal,
                            "entry_price": _to_python_type(current_price),
                            "target_price": _to_python_type(highs[swing_highs[-1]] if direction == "bullish" else lows[swing_lows[-1]]),
                            "stop_loss": _to_python_type(lows[swing_lows[-1]] if direction == "bullish" else highs[swing_highs[-1]])
                        }
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error detecting price channels: {e}")
            return None
    
    def detect_measured_move(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Measured Move pattern (ABC pattern with equal moves)"""
        try:
            if len(df) < 40:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            
            # Find swing points
            swing_highs = self._find_swing_highs(highs, window=5)
            swing_lows = self._find_swing_lows(lows, window=5)
            
            if len(swing_highs) < 3 or len(swing_lows) < 3:
                return None
            
            # Look for ABC pattern where BC = AB
            all_points = sorted(set(swing_highs + swing_lows))
            
            if len(all_points) >= 3:
                for i in range(len(all_points) - 2):
                    a_idx = all_points[i]
                    b_idx = all_points[i + 1]
                    c_idx = all_points[i + 2]
                    
                    # Get prices
                    a_price = highs[a_idx] if a_idx in swing_highs else lows[a_idx]
                    b_price = highs[b_idx] if b_idx in swing_highs else lows[b_idx]
                    c_price = highs[c_idx] if c_idx in swing_highs else lows[c_idx]
                    
                    ab_length = abs(b_price - a_price)
                    bc_length = abs(c_price - b_price)
                    
                    # Check if BC ≈ AB (within 10% tolerance)
                    if ab_length > 0:
                        ratio = bc_length / ab_length
                        if 0.9 <= ratio <= 1.1:
                            # Project D = C + (C - B) for measured move target
                            d_price = c_price + (c_price - b_price)
                            
                            return {
                                "pattern_type": "measured_move",
                                "pattern_name": "Measured Move",
                                "pattern_category": "classic",
                                "pattern_direction": "bullish" if c_price > b_price else "bearish",
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat(),
                                "confidence": 0.75,
                                "a_price": _to_python_type(a_price),
                                "b_price": _to_python_type(b_price),
                                "c_price": _to_python_type(c_price),
                                "projected_d_price": _to_python_type(d_price),
                                "trading_implications": {
                                    "signal": "BUY" if c_price > b_price else "SELL",
                                    "entry_price": _to_python_type(c_price),
                                    "target_price": _to_python_type(d_price),
                                    "stop_loss": _to_python_type(b_price)
                                }
                            }
            
            return None
        except Exception as e:
            logger.error(f"Error detecting measured move: {e}")
            return None
    
    def detect_elliott_waves(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Detect Elliott Wave patterns (5-wave impulse and 3-wave correction)"""
        try:
            if len(df) < 50:
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            closes = df["close"].values
            
            # Find swing points
            swing_highs = self._find_swing_highs(highs, window=3)
            swing_lows = self._find_swing_lows(lows, window=3)
            
            if len(swing_highs) < 3 or len(swing_lows) < 3:
                return None
            
            # Try to identify 5-wave impulse pattern
            all_points = sorted(set(swing_highs + swing_lows))
            
            if len(all_points) >= 5:
                # Look for 5-wave pattern (1-2-3-4-5)
                for i in range(len(all_points) - 4):
                    wave1_idx = all_points[i]
                    wave2_idx = all_points[i + 1]
                    wave3_idx = all_points[i + 2]
                    wave4_idx = all_points[i + 3]
                    wave5_idx = all_points[i + 4]
                    
                    # Get wave prices
                    wave1_price = highs[wave1_idx] if wave1_idx in swing_highs else lows[wave1_idx]
                    wave2_price = highs[wave2_idx] if wave2_idx in swing_highs else lows[wave2_idx]
                    wave3_price = highs[wave3_idx] if wave3_idx in swing_highs else lows[wave3_idx]
                    wave4_price = highs[wave4_idx] if wave4_idx in swing_highs else lows[wave4_idx]
                    wave5_price = highs[wave5_idx] if wave5_idx in swing_highs else lows[wave5_idx]
                    
                    # Check Elliott Wave rules:
                    # Wave 2 should not retrace more than 100% of Wave 1
                    # Wave 3 should not be the shortest
                    # Wave 4 should not overlap Wave 1
                    # Wave 5 should be shorter than Wave 3 in most cases
                    
                    wave1_length = abs(wave2_price - wave1_price)
                    wave2_length = abs(wave3_price - wave2_price)
                    wave3_length = abs(wave4_price - wave3_price)
                    wave4_length = abs(wave5_price - wave4_price)
                    
                    # Basic validation
                    if wave1_length > 0 and wave2_length > 0:
                        wave2_retrace = wave2_length / wave1_length
                        
                        # Wave 2 should retrace 38.2% to 78.6% of Wave 1
                        if 0.3 <= wave2_retrace <= 0.8:
                            # Determine wave degree (simplified)
                            total_move = abs(wave5_price - wave1_price)
                            degree = "Minor" if total_move < df["close"].iloc[-1] * 0.1 else "Intermediate"
                            
                            return {
                                "pattern_type": "elliott_wave",
                                "pattern_name": "Elliott Wave Pattern",
                                "pattern_category": "elliott",
                                "pattern_direction": "bullish" if wave5_price > wave1_price else "bearish",
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "detected_at": datetime.now().isoformat(),
                                "confidence": 0.7,
                                "wave_count": 5,
                                "wave_degree": degree,
                                "wave1_price": _to_python_type(wave1_price),
                                "wave2_price": _to_python_type(wave2_price),
                                "wave3_price": _to_python_type(wave3_price),
                                "wave4_price": _to_python_type(wave4_price),
                                "wave5_price": _to_python_type(wave5_price),
                                "trading_implications": {
                                    "signal": "SELL" if wave5_price > wave1_price else "BUY",  # End of impulse = reversal
                                    "entry_price": _to_python_type(wave5_price),
                                    "target_price": _to_python_type(wave4_price - (wave5_price - wave4_price) * 0.618),
                                    "wave_analysis": {
                                        "wave1_length": _to_python_type(wave1_length),
                                        "wave2_length": _to_python_type(wave2_length),
                                        "wave3_length": _to_python_type(wave3_length),
                                        "wave4_length": _to_python_type(wave4_length),
                                        "wave2_retrace_pct": _to_python_type(wave2_retrace * 100)
                                    }
                                }
                            }
            
            return None
        except Exception as e:
            logger.error(f"Error detecting Elliott waves: {e}")
            return None
    
    # Helper methods
    
    def _get_time_from_index(self, df: pd.DataFrame, index: int) -> Optional[int]:
        """Helper method to extract time from DataFrame index"""
        try:
            if hasattr(df.index, 'tolist'):
                if index < len(df.index):
                    time_val = df.index[index]
                    # Convert to timestamp if it's a datetime
                    if hasattr(time_val, 'timestamp'):
                        return int(time_val.timestamp())
                    elif isinstance(time_val, (int, float)):
                        return int(time_val)
                    # Try to get from 'time' column if available
                    elif 'time' in df.columns and index < len(df):
                        time_val = df.iloc[index]['time']
                        if isinstance(time_val, (int, float)):
                            return int(time_val)
            return None
        except:
            return None
    
    def _get_price_at_index(self, df: pd.DataFrame, index: int, price_type: str = 'close') -> Optional[float]:
        """Helper method to extract price from DataFrame at given index"""
        try:
            if index < len(df) and price_type in df.columns:
                return float(df.iloc[index][price_type])
            return None
        except:
            return None
    
    def _find_swing_lows(self, lows: np.ndarray, window: int = 5) -> List[int]:
        """Find swing low points"""
        swing_lows = []
        for i in range(window, len(lows) - window):
            if lows[i] == min(lows[i-window:i+window+1]):
                swing_lows.append(i)
        return swing_lows
    
    def _find_swing_highs(self, highs: np.ndarray, window: int = 5) -> List[int]:
        """Find swing high points"""
        swing_highs = []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                swing_highs.append(i)
        return swing_highs
    
    def _find_neckline(
        self,
        df: pd.DataFrame,
        left_idx: int,
        head_idx: int,
        right_idx: int,
        is_reverse: bool = True
    ) -> Optional[float]:
        """Find neckline (support/resistance) level"""
        try:
            if is_reverse:
                # For reverse H&S, neckline is resistance (highs between shoulders)
                between_left_head = df.iloc[left_idx:head_idx]["high"].max()
                between_head_right = df.iloc[head_idx:right_idx]["high"].max()
                neckline = (between_left_head + between_head_right) / 2
            else:
                # For H&S, neckline is support (lows between shoulders)
                between_left_head = df.iloc[left_idx:head_idx]["low"].min()
                between_head_right = df.iloc[head_idx:right_idx]["low"].min()
                neckline = (between_left_head + between_head_right) / 2
            
            return float(neckline)
        except:
            return None
    
    def _calculate_reverse_hs_confidence(
        self,
        df: pd.DataFrame,
        left_idx: int,
        head_idx: int,
        right_idx: int,
        left_low: float,
        head_low: float,
        right_low: float,
        neckline: float,
        pattern_height: float
    ) -> float:
        """Calculate confidence for reverse head & shoulder pattern"""
        confidence = 0.5  # Base confidence
        
        # Shoulder symmetry (max 0.2 points)
        shoulder_diff = abs(left_low - right_low) / max(left_low, right_low)
        if shoulder_diff < 0.02:
            confidence += 0.2
        elif shoulder_diff < 0.05:
            confidence += 0.1
        
        # Head depth (max 0.2 points)
        head_depth = (max(left_low, right_low) - head_low) / max(left_low, right_low)
        if head_depth > 0.05:
            confidence += 0.2
        elif head_depth > 0.03:
            confidence += 0.1
        
        # Volume confirmation (max 0.2 points)
        if 'volume' in df.columns:
            volume_conf = self._check_volume_confirmation(df, right_idx)
            if volume_conf:
                confidence += 0.2
        
        # Pattern completion (max 0.1 points)
        current_price = df["close"].iloc[-1]
        if current_price > neckline * 0.95:  # Near or above neckline
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_hs_confidence(
        self,
        df: pd.DataFrame,
        left_idx: int,
        head_idx: int,
        right_idx: int,
        left_high: float,
        head_high: float,
        right_high: float,
        neckline: float,
        pattern_height: float
    ) -> float:
        """Calculate confidence for head & shoulder pattern"""
        confidence = 0.5
        
        shoulder_diff = abs(left_high - right_high) / max(left_high, right_high)
        if shoulder_diff < 0.02:
            confidence += 0.2
        elif shoulder_diff < 0.05:
            confidence += 0.1
        
        head_height = (head_high - max(left_high, right_high)) / max(left_high, right_high)
        if head_height > 0.05:
            confidence += 0.2
        elif head_height > 0.03:
            confidence += 0.1
        
        if 'volume' in df.columns:
            volume_conf = self._check_volume_confirmation(df, right_idx)
            if volume_conf:
                confidence += 0.2
        
        return min(1.0, confidence)
    
    def _check_volume_confirmation(self, df: pd.DataFrame, pattern_end_idx: int) -> bool:
        """Check if volume confirms the pattern"""
        try:
            if 'volume' not in df.columns:
                return False
            
            if pattern_end_idx < 10:
                return False
            
            recent_volume = df.iloc[pattern_end_idx-5:pattern_end_idx]["volume"].mean()
            avg_volume = df.iloc[pattern_end_idx-20:pattern_end_idx]["volume"].mean()
            
            # Volume should be higher than average for pattern confirmation
            # Convert to Python bool to avoid numpy.bool_ issues
            result = recent_volume > avg_volume * 1.2
            return bool(result) if hasattr(result, 'item') else bool(result)
            
        except:
            return False

# Create singleton instance
advanced_chart_pattern_detector = AdvancedChartPatternDetector()

