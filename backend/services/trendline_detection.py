"""
Trendline Detection Service
Automatically detects and draws trendlines and channels on price charts
Includes uptrend lines, downtrend lines, and channel detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from enum import Enum
from scipy import stats
from itertools import combinations

logger = logging.getLogger(__name__)

class TrendlineType(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    HORIZONTAL = "horizontal"

class TrendlineStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class TrendlineDetectionService:
    def __init__(self):
        # Configuration parameters
        self.min_touches = 2  # Minimum points to form a trendline
        self.touch_tolerance = 0.02  # 2% tolerance for considering a touch
        self.min_length_bars = 10  # Minimum length in bars
        self.max_break_distance = 0.03  # 3% max distance for break detection
        
        # Cache for performance
        self.trendline_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def detect_all_trendlines(
        self,
        data: List[Dict[str, Any]],
        min_touches: int = 2,
        lookback_period: int = 100
    ) -> Dict[str, Any]:
        """
        Detect all significant trendlines in the data
        
        Args:
            data: OHLCV price data
            min_touches: Minimum number of touches required
            lookback_period: Number of candles to analyze
        
        Returns:
            Dictionary with uptrend lines, downtrend lines, and channels
        """
        try:
            if len(data) < 10:
                return {"error": "Insufficient data"}
            
            # Convert to DataFrame
            df = pd.DataFrame(data[-lookback_period:])
            
            # Detect swing points
            swing_highs = self._detect_swing_highs(df)
            swing_lows = self._detect_swing_lows(df)
            
            # Detect uptrend lines (connect swing lows)
            uptrend_lines = self._detect_uptrend_lines(
                df, swing_lows, min_touches
            )
            
            # Detect downtrend lines (connect swing highs)
            downtrend_lines = self._detect_downtrend_lines(
                df, swing_highs, min_touches
            )
            
            # Detect horizontal support/resistance
            horizontal_lines = self._detect_horizontal_lines(
                df, swing_highs, swing_lows
            )
            
            # Detect channels
            channels = self._detect_channels(
                df, uptrend_lines, downtrend_lines
            )
            
            # Find most significant trendlines
            best_uptrend = self._find_best_trendline(uptrend_lines) if uptrend_lines else None
            best_downtrend = self._find_best_trendline(downtrend_lines) if downtrend_lines else None
            
            # Check for trendline breaks
            breaks = self._detect_trendline_breaks(
                df, uptrend_lines + downtrend_lines
            )
            
            result = {
                "uptrend_lines": uptrend_lines,
                "downtrend_lines": downtrend_lines,
                "horizontal_lines": horizontal_lines,
                "channels": channels,
                "best_uptrend": best_uptrend,
                "best_downtrend": best_downtrend,
                "recent_breaks": breaks,
                "swing_highs": swing_highs,
                "swing_lows": swing_lows,
                "current_trend": self._determine_current_trend(
                    best_uptrend, best_downtrend, df
                ),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(
                f"Detected {len(uptrend_lines)} uptrends, "
                f"{len(downtrend_lines)} downtrends, "
                f"{len(channels)} channels"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting trendlines: {e}")
            return {"error": str(e)}
    
    def _detect_swing_highs(
        self,
        df: pd.DataFrame,
        strength: int = 5
    ) -> List[Dict[str, Any]]:
        """Detect swing high points"""
        swing_highs = []
        
        for i in range(strength, len(df) - strength):
            is_swing_high = True
            current_high = df.iloc[i]['high']
            
            # Check left side
            for j in range(i - strength, i):
                if df.iloc[j]['high'] > current_high:
                    is_swing_high = False
                    break
            
            # Check right side
            if is_swing_high:
                for j in range(i + 1, i + strength + 1):
                    if df.iloc[j]['high'] > current_high:
                        is_swing_high = False
                        break
            
            if is_swing_high:
                swing_highs.append({
                    "index": i,
                    "price": current_high,
                    "time": df.iloc[i].get('time', i)
                })
        
        return swing_highs
    
    def _detect_swing_lows(
        self,
        df: pd.DataFrame,
        strength: int = 5
    ) -> List[Dict[str, Any]]:
        """Detect swing low points"""
        swing_lows = []
        
        for i in range(strength, len(df) - strength):
            is_swing_low = True
            current_low = df.iloc[i]['low']
            
            # Check left side
            for j in range(i - strength, i):
                if df.iloc[j]['low'] < current_low:
                    is_swing_low = False
                    break
            
            # Check right side
            if is_swing_low:
                for j in range(i + 1, i + strength + 1):
                    if df.iloc[j]['low'] < current_low:
                        is_swing_low = False
                        break
            
            if is_swing_low:
                swing_lows.append({
                    "index": i,
                    "price": current_low,
                    "time": df.iloc[i].get('time', i)
                })
        
        return swing_lows
    
    def _detect_uptrend_lines(
        self,
        df: pd.DataFrame,
        swing_lows: List[Dict[str, Any]],
        min_touches: int
    ) -> List[Dict[str, Any]]:
        """
        Detect uptrend lines by connecting swing lows
        """
        uptrend_lines = []
        
        if len(swing_lows) < 2:
            return uptrend_lines
        
        # Try all combinations of swing lows
        for combo in combinations(swing_lows, 2):
            point1, point2 = combo
            
            # Skip if points are too close
            if abs(point1['index'] - point2['index']) < self.min_length_bars:
                continue
            
            # Calculate trendline parameters
            x1, y1 = point1['index'], point1['price']
            x2, y2 = point2['index'], point2['price']
            
            # Only uptrend (positive slope)
            if y2 <= y1:
                continue
            
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1
            
            # Check how many points touch this line
            touches = self._count_touches(
                df, swing_lows, slope, intercept, is_uptrend=True
            )
            
            if touches['count'] >= min_touches:
                # Calculate strength with volume confirmation
                strength, volume_info = self._calculate_trendline_strength(
                    touches['count'],
                    touches['avg_distance'],
                    x2 - x1,
                    touches['recent_touches'],
                    df,
                    touches['points']
                )
                
                # Extend line to current point
                current_index = len(df) - 1
                current_value = slope * current_index + intercept
                
                # Check if line is broken
                is_broken = self._check_if_broken(
                    df, slope, intercept, x2, is_uptrend=True
                )
                
                # Get time values from DataFrame if available
                start_time = df.iloc[x1].get('time', None) if x1 < len(df) else None
                end_time = df.iloc[current_index].get('time', None) if current_index < len(df) else None
                
                uptrend_lines.append({
                    "type": TrendlineType.UPTREND,
                    "start_index": x1,
                    "start_price": y1,
                    "end_index": current_index,
                    "end_price": current_value,
                    "start_time": start_time,
                    "end_time": end_time,
                    "slope": slope,
                    "intercept": intercept,
                    "touches": touches['count'],
                    "touch_points": touches['points'],
                    "strength": strength,
                    "volume_info": volume_info,  # NEW: Volume confirmation data
                    "is_broken": is_broken,
                    "avg_distance": touches['avg_distance'],
                    "length_bars": current_index - x1
                })
        
        # Sort by strength and touches
        uptrend_lines.sort(
            key=lambda x: (x['touches'], x['strength'], -x['avg_distance']),
            reverse=True
        )
        
        return uptrend_lines[:10]  # Return top 10
    
    def _detect_downtrend_lines(
        self,
        df: pd.DataFrame,
        swing_highs: List[Dict[str, Any]],
        min_touches: int
    ) -> List[Dict[str, Any]]:
        """
        Detect downtrend lines by connecting swing highs
        """
        downtrend_lines = []
        
        if len(swing_highs) < 2:
            return downtrend_lines
        
        # Try all combinations of swing highs
        for combo in combinations(swing_highs, 2):
            point1, point2 = combo
            
            # Skip if points are too close
            if abs(point1['index'] - point2['index']) < self.min_length_bars:
                continue
            
            # Calculate trendline parameters
            x1, y1 = point1['index'], point1['price']
            x2, y2 = point2['index'], point2['price']
            
            # Only downtrend (negative slope)
            if y2 >= y1:
                continue
            
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1
            
            # Check how many points touch this line
            touches = self._count_touches(
                df, swing_highs, slope, intercept, is_uptrend=False
            )
            
            if touches['count'] >= min_touches:
                # Calculate strength with volume confirmation
                strength, volume_info = self._calculate_trendline_strength(
                    touches['count'],
                    touches['avg_distance'],
                    x2 - x1,
                    touches['recent_touches'],
                    df,
                    touches['points']
                )
                
                # Extend line to current point
                current_index = len(df) - 1
                current_value = slope * current_index + intercept
                
                # Check if line is broken
                is_broken = self._check_if_broken(
                    df, slope, intercept, x2, is_uptrend=False
                )
                
                # Get time values from DataFrame if available
                start_time = df.iloc[x1].get('time', None) if x1 < len(df) else None
                end_time = df.iloc[current_index].get('time', None) if current_index < len(df) else None
                
                downtrend_lines.append({
                    "type": TrendlineType.DOWNTREND,
                    "start_index": x1,
                    "start_price": y1,
                    "end_index": current_index,
                    "end_price": current_value,
                    "start_time": start_time,
                    "end_time": end_time,
                    "slope": slope,
                    "intercept": intercept,
                    "touches": touches['count'],
                    "touch_points": touches['points'],
                    "strength": strength,
                    "volume_info": volume_info,  # NEW: Volume confirmation data
                    "is_broken": is_broken,
                    "avg_distance": touches['avg_distance'],
                    "length_bars": current_index - x1
                })
        
        # Sort by strength and touches
        downtrend_lines.sort(
            key=lambda x: (x['touches'], x['strength'], -x['avg_distance']),
            reverse=True
        )
        
        return downtrend_lines[:10]  # Return top 10
    
    def _count_touches(
        self,
        df: pd.DataFrame,
        swing_points: List[Dict[str, Any]],
        slope: float,
        intercept: float,
        is_uptrend: bool
    ) -> Dict[str, Any]:
        """
        Count how many swing points touch the trendline
        """
        touches = []
        distances = []
        recent_touches = 0
        
        for point in swing_points:
            x = point['index']
            y = point['price']
            
            # Calculate expected y on the line
            expected_y = slope * x + intercept
            
            # Calculate distance (as percentage)
            distance = abs(y - expected_y) / expected_y
            
            # Check if it's a touch
            if distance <= self.touch_tolerance:
                touches.append(point)
                distances.append(distance)
                
                # Check if it's a recent touch (last 20% of data)
                if x > len(df) * 0.8:
                    recent_touches += 1
        
        return {
            "count": len(touches),
            "points": touches,
            "avg_distance": np.mean(distances) if distances else 0,
            "recent_touches": recent_touches
        }
    
    def _calculate_trendline_strength(
        self,
        touches: int,
        avg_distance: float,
        length: int,
        recent_touches: int,
        df: Optional[pd.DataFrame] = None,
        touch_points: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Calculate trendline strength based on multiple factors including volume confirmation
        
        Returns:
            Tuple of (strength_string, volume_info_dict)
        """
        score = 0
        
        # Touch count (0-40 points)
        score += min(touches * 10, 40)
        
        # Distance quality (0-20 points)
        distance_score = (1 - avg_distance / self.touch_tolerance) * 20
        score += max(0, distance_score)
        
        # Length (0-20 points)
        length_score = min(length / 50, 1) * 20
        score += length_score
        
        # Recent touches (0-20 points)
        recent_score = min(recent_touches * 7, 20)
        score += recent_score
        
        # Volume confirmation (0-20 points) - NEW
        volume_score = 0
        volume_quality = "low"
        avg_volume_ratio = 1.0
        volume_confirmed_touches = 0
        volume_info = {
            "volume_quality": "low",
            "avg_volume_ratio": 1.0,
            "volume_confirmed_touches": 0,
            "total_touches": touches,
            "volume_score": 0
        }
        
        if df is not None and touch_points and 'volume' in df.columns and len(df) > 0:
            volume_ratios = []
            volume_confirmed_touches = 0
            
            for touch_point in touch_points:
                touch_index = touch_point.get('index', 0)
                if 0 <= touch_index < len(df):
                    touch_volume = df.iloc[touch_index].get('volume', 0)
                    
                    # Calculate average volume around touch point (20-period window)
                    start_idx = max(0, touch_index - 10)
                    end_idx = min(len(df), touch_index + 10)
                    avg_volume = df.iloc[start_idx:end_idx]['volume'].mean() if end_idx > start_idx else touch_volume
                    
                    if avg_volume > 0:
                        volume_ratio = touch_volume / avg_volume
                        volume_ratios.append(volume_ratio)
                        
                        # Count volume-confirmed touches (>120% of average)
                        if volume_ratio > 1.2:
                            volume_confirmed_touches += 1
            
            if volume_ratios:
                avg_volume_ratio = float(np.mean(volume_ratios))
                
                # Volume score based on:
                # 1. Average volume ratio at touches (0-10 points)
                # 2. Number of volume-confirmed touches (0-10 points)
                volume_ratio_score = min(avg_volume_ratio * 5, 10)  # Max 10 points
                confirmed_touches_score = min((volume_confirmed_touches / touches) * 10, 10) if touches > 0 else 0  # Max 10 points
                
                volume_score = volume_ratio_score + confirmed_touches_score
                
                # Determine volume quality
                if avg_volume_ratio > 1.5 and volume_confirmed_touches >= touches * 0.6:
                    volume_quality = "very_high"
                elif avg_volume_ratio > 1.2 and volume_confirmed_touches >= touches * 0.4:
                    volume_quality = "high"
                elif avg_volume_ratio > 1.0:
                    volume_quality = "moderate"
                else:
                    volume_quality = "low"
                
                volume_info = {
                    "volume_quality": volume_quality,
                    "avg_volume_ratio": avg_volume_ratio,
                    "volume_confirmed_touches": volume_confirmed_touches,
                    "total_touches": touches,
                    "volume_score": float(volume_score)
                }
        
        score += volume_score
        
        # Adjust final score based on volume quality (bonus/penalty)
        if volume_quality == "very_high":
            score = min(score * 1.1, 100)  # 10% bonus, capped at 100
        elif volume_quality == "high":
            score = min(score * 1.05, 100)  # 5% bonus
        elif volume_quality == "low":
            score = score * 0.95  # 5% penalty
        
        # Categorize
        if score >= 75:
            strength = TrendlineStrength.VERY_STRONG
        elif score >= 60:
            strength = TrendlineStrength.STRONG
        elif score >= 40:
            strength = TrendlineStrength.MODERATE
        else:
            strength = TrendlineStrength.WEAK
        
        return strength, volume_info
    
    def _check_if_broken(
        self,
        df: pd.DataFrame,
        slope: float,
        intercept: float,
        start_index: int,
        is_uptrend: bool
    ) -> Dict[str, Any]:
        """
        Enhanced break detection with retest logic and volume confirmation
        """
        breaks = []
        lookback_bars = 5  # Bars to check for retest after break
        
        # Check from start_index to end
        for i in range(start_index, len(df)):
            expected_y = slope * i + intercept
            close = df.iloc[i]['close']
            low = df.iloc[i]['low']
            high = df.iloc[i]['high']
            volume = df.iloc[i].get('volume', 0)
            
            # Calculate average volume for comparison
            avg_volume = df['volume'].rolling(20).mean().iloc[i] if 'volume' in df.columns and i >= 20 else volume
            
            is_break = False
            break_type = None  # 'close' or 'wick'
            
            if is_uptrend:
                # For uptrend, break is when price closes below line
                if close < expected_y * (1 - self.max_break_distance):
                    is_break = True
                    break_type = 'close'
                # Also check for wick break (low touched but didn't close below)
                elif low < expected_y * (1 - self.max_break_distance * 0.5) and close >= expected_y * (1 - self.max_break_distance * 0.5):
                    is_break = True
                    break_type = 'wick'
            else:
                # For downtrend, break is when price closes above line
                if close > expected_y * (1 + self.max_break_distance):
                    is_break = True
                    break_type = 'close'
                # Also check for wick break (high touched but didn't close above)
                elif high > expected_y * (1 + self.max_break_distance * 0.5) and close <= expected_y * (1 + self.max_break_distance * 0.5):
                    is_break = True
                    break_type = 'wick'
            
            if is_break:
                # Check volume confirmation
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                volume_confirmed = volume_ratio > 1.2  # 20% above average
                
                # Check for retest after break
                retest_info = self._check_retest(
                    df, i, slope, intercept, is_uptrend, lookback_bars
                )
                
                # Calculate break strength
                break_strength = self._calculate_break_strength(
                    break_type, volume_confirmed, retest_info, 
                    abs((expected_y - close) / expected_y * 100) if is_uptrend else abs((close - expected_y) / expected_y * 100)
                )
                
                breaks.append({
                    "index": i,
                    "price": close,
                    "expected": expected_y,
                    "break_percentage": (expected_y - close) / expected_y * 100 if is_uptrend else (close - expected_y) / expected_y * 100,
                    "break_type": break_type,
                    "volume_ratio": volume_ratio,
                    "volume_confirmed": volume_confirmed,
                    "retest": retest_info,
                    "break_strength": break_strength
                })
        
        if breaks:
            # Return the most significant break (last one with highest strength)
            latest_break = breaks[-1]
            return {
                "is_broken": True,
                "break_index": latest_break['index'],
                "break_price": latest_break['price'],
                "break_percentage": latest_break['break_percentage'],
                "break_type": latest_break['break_type'],
                "volume_confirmed": latest_break['volume_confirmed'],
                "volume_ratio": latest_break['volume_ratio'],
                "retest": latest_break['retest'],
                "break_strength": latest_break['break_strength'],
                "signal_quality": self._determine_signal_quality(
                    latest_break['break_type'],
                    latest_break['volume_confirmed'],
                    latest_break['retest']
                )
            }
        else:
            return {"is_broken": False}
    
    def _check_retest(
        self,
        df: pd.DataFrame,
        break_index: int,
        slope: float,
        intercept: float,
        is_uptrend: bool,
        lookback_bars: int = 5
    ) -> Dict[str, Any]:
        """
        Check if price retested the broken trendline after break
        """
        retest_found = False
        retest_index = None
        retest_price = None
        retest_type = None  # 'support' or 'resistance'
        
        # Check bars after break
        for i in range(break_index + 1, min(break_index + lookback_bars + 1, len(df))):
            expected_y = slope * i + intercept
            close = df.iloc[i]['close']
            low = df.iloc[i]['low']
            high = df.iloc[i]['high']
            
            # Check if price returned to trendline (within 1% tolerance)
            tolerance = 0.01
            
            if is_uptrend:
                # For broken uptrend, check if price retested from below (now resistance)
                if low <= expected_y * (1 + tolerance) and close >= expected_y * (1 - tolerance):
                    retest_found = True
                    retest_index = i
                    retest_price = close
                    retest_type = 'resistance'
                    break
            else:
                # For broken downtrend, check if price retested from above (now support)
                if high >= expected_y * (1 - tolerance) and close <= expected_y * (1 + tolerance):
                    retest_found = True
                    retest_index = i
                    retest_price = close
                    retest_type = 'support'
                    break
        
        return {
            "retested": retest_found,
            "retest_index": retest_index,
            "retest_price": retest_price,
            "retest_type": retest_type
        }
    
    def _calculate_break_strength(
        self,
        break_type: str,
        volume_confirmed: bool,
        retest_info: Dict[str, Any],
        break_percentage: float
    ) -> str:
        """
        Calculate break strength based on multiple factors
        """
        score = 0
        
        # Break type (close break is stronger than wick break)
        if break_type == 'close':
            score += 40
        else:  # wick
            score += 20
        
        # Volume confirmation
        if volume_confirmed:
            score += 30
        else:
            score += 10
        
        # Retest adds strength (confirms the break)
        if retest_info.get('retested', False):
            score += 20
        else:
            score += 5
        
        # Break percentage (larger breaks are stronger)
        if break_percentage > 5:
            score += 10
        elif break_percentage > 3:
            score += 5
        
        # Categorize
        if score >= 80:
            return "very_strong"
        elif score >= 60:
            return "strong"
        elif score >= 40:
            return "moderate"
        else:
            return "weak"
    
    def _determine_signal_quality(
        self,
        break_type: str,
        volume_confirmed: bool,
        retest_info: Dict[str, Any]
    ) -> str:
        """
        Determine overall signal quality for trading
        """
        if break_type == 'close' and volume_confirmed and retest_info.get('retested', False):
            return "HIGH"
        elif break_type == 'close' and (volume_confirmed or retest_info.get('retested', False)):
            return "MEDIUM"
        elif break_type == 'close':
            return "LOW"
        else:  # wick break
            return "VERY_LOW"
    
    def _detect_horizontal_lines(
        self,
        df: pd.DataFrame,
        swing_highs: List[Dict[str, Any]],
        swing_lows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect horizontal support and resistance levels
        """
        horizontal_lines = []
        
        # Cluster swing points by price
        all_points = swing_highs + swing_lows
        if not all_points:
            return horizontal_lines
        
        # Sort by price
        all_points.sort(key=lambda x: x['price'])
        
        # Group nearby prices
        clusters = []
        current_cluster = [all_points[0]]
        
        for point in all_points[1:]:
            # Check if point is within 1% of cluster average
            cluster_avg = np.mean([p['price'] for p in current_cluster])
            if abs(point['price'] - cluster_avg) / cluster_avg <= 0.01:
                current_cluster.append(point)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [point]
        
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
        
        # Create horizontal lines from clusters
        for cluster in clusters:
            if len(cluster) >= 2:
                price = np.mean([p['price'] for p in cluster])
                min_index = min(p['index'] for p in cluster)
                max_index = max(p['index'] for p in cluster)
                
                horizontal_lines.append({
                    "type": TrendlineType.HORIZONTAL,
                    "price": price,
                    "start_index": min_index,
                    "end_index": len(df) - 1,
                    "touches": len(cluster),
                    "touch_points": cluster,
                    "strength": self._calculate_horizontal_strength(cluster, len(df))
                })
        
        # Sort by touches and strength
        horizontal_lines.sort(key=lambda x: x['touches'], reverse=True)
        
        return horizontal_lines[:5]  # Top 5
    
    def _calculate_horizontal_strength(
        self,
        cluster: List[Dict[str, Any]],
        total_bars: int
    ) -> str:
        """Calculate strength of horizontal level"""
        touches = len(cluster)
        
        # Check if recent touches
        recent = sum(1 for p in cluster if p['index'] > total_bars * 0.7)
        
        if touches >= 4 and recent >= 1:
            return TrendlineStrength.VERY_STRONG
        elif touches >= 3:
            return TrendlineStrength.STRONG
        elif touches >= 2:
            return TrendlineStrength.MODERATE
        else:
            return TrendlineStrength.WEAK
    
    def _detect_channels(
        self,
        df: pd.DataFrame,
        uptrend_lines: List[Dict[str, Any]],
        downtrend_lines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect price channels (parallel trendlines)
        """
        channels = []
        
        # Check for uptrend channels (uptrend line + parallel resistance)
        for uptrend in uptrend_lines[:5]:  # Top 5 uptrends
            # Try to find parallel resistance line
            resistance = self._find_parallel_line(
                df, uptrend, is_uptrend=True
            )
            
            if resistance:
                channels.append({
                    "type": "ascending_channel",
                    "support_line": uptrend,
                    "resistance_line": resistance,
                    "width": resistance['avg_price'] - uptrend['end_price'],
                    "width_percentage": (resistance['avg_price'] - uptrend['end_price']) / uptrend['end_price'] * 100
                })
        
        # Check for downtrend channels (downtrend line + parallel support)
        for downtrend in downtrend_lines[:5]:  # Top 5 downtrends
            # Try to find parallel support line
            support = self._find_parallel_line(
                df, downtrend, is_uptrend=False
            )
            
            if support:
                channels.append({
                    "type": "descending_channel",
                    "resistance_line": downtrend,
                    "support_line": support,
                    "width": downtrend['end_price'] - support['avg_price'],
                    "width_percentage": (downtrend['end_price'] - support['avg_price']) / downtrend['end_price'] * 100
                })
        
        return channels
    
    def _find_parallel_line(
        self,
        df: pd.DataFrame,
        base_line: Dict[str, Any],
        is_uptrend: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Find a parallel line to the base line
        """
        slope = base_line['slope']
        
        # Look for parallel line with same slope
        # For uptrend base, look for parallel resistance (higher)
        # For downtrend base, look for parallel support (lower)
        
        if is_uptrend:
            # Find highs that could form parallel resistance
            highs = df['high'].values
            best_intercept = None
            best_touches = 0
            
            for i in range(len(df)):
                # Calculate intercept if line passes through this high
                intercept = highs[i] - slope * i
                
                # Count touches
                touches = 0
                for j in range(len(df)):
                    expected = slope * j + intercept
                    if abs(highs[j] - expected) / expected <= self.touch_tolerance:
                        touches += 1
                
                if touches > best_touches and touches >= 2:
                    best_touches = touches
                    best_intercept = intercept
            
            if best_intercept and best_touches >= 2:
                current_index = len(df) - 1
                return {
                    "slope": slope,
                    "intercept": best_intercept,
                    "touches": best_touches,
                    "avg_price": slope * current_index + best_intercept
                }
        
        return None
    
    def _find_best_trendline(
        self,
        trendlines: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the most significant trendline
        """
        if not trendlines:
            return None
        
        # Already sorted by strength, return first non-broken
        for line in trendlines:
            if not line.get('is_broken', {}).get('is_broken', False):
                return line
        
        # If all broken, return the strongest
        return trendlines[0]
    
    def _detect_trendline_breaks(
        self,
        df: pd.DataFrame,
        trendlines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect recent trendline breaks with enhanced information
        """
        breaks = []
        
        for line in trendlines:
            break_info = line.get('is_broken', {})
            if break_info.get('is_broken', False):
                # Check if break is recent (last 10 bars)
                if break_info.get('break_index', 0) > len(df) - 10:
                    # Determine break direction
                    if line['type'] == TrendlineType.UPTREND:
                        break_direction = "BEARISH"  # Uptrend broken = bearish
                    else:
                        break_direction = "BULLISH"  # Downtrend broken = bullish
                    
                    breaks.append({
                        "trendline_type": line['type'],
                        "break_index": break_info['break_index'],
                        "break_price": break_info['break_price'],
                        "break_percentage": break_info['break_percentage'],
                        "break_type": break_info.get('break_type', 'close'),
                        "break_direction": break_direction,
                        "break_strength": break_info.get('break_strength', 'weak'),
                        "volume_confirmed": break_info.get('volume_confirmed', False),
                        "volume_ratio": break_info.get('volume_ratio', 1.0),
                        "retest": break_info.get('retest', {}),
                        "signal_quality": break_info.get('signal_quality', 'LOW'),
                        "original_line": {
                            "slope": line['slope'],
                            "touches": line['touches'],
                            "strength": line['strength']
                        }
                    })
        
        return breaks
    
    def _determine_current_trend(
        self,
        best_uptrend: Optional[Dict[str, Any]],
        best_downtrend: Optional[Dict[str, Any]],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Determine current trend based on trendlines
        """
        if not best_uptrend and not best_downtrend:
            return {"trend": "sideways", "confidence": "low"}
        
        current_price = df.iloc[-1]['close']
        
        if best_uptrend and not best_uptrend.get('is_broken', {}).get('is_broken', False):
            # Check if price is above uptrend line
            expected_value = best_uptrend['slope'] * (len(df) - 1) + best_uptrend['intercept']
            if current_price > expected_value * 0.98:
                return {
                    "trend": "uptrend",
                    "confidence": best_uptrend['strength'],
                    "trendline": best_uptrend
                }
        
        if best_downtrend and not best_downtrend.get('is_broken', {}).get('is_broken', False):
            # Check if price is below downtrend line
            expected_value = best_downtrend['slope'] * (len(df) - 1) + best_downtrend['intercept']
            if current_price < expected_value * 1.02:
                return {
                    "trend": "downtrend",
                    "confidence": best_downtrend['strength'],
                    "trendline": best_downtrend
                }
        
        return {"trend": "sideways", "confidence": "moderate"}
    
    def project_trendline(
        self,
        trendline: Dict[str, Any],
        future_bars: int = 20,
        data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Project trendline into future and calculate price targets
        
        Args:
            trendline: Trendline dictionary with slope, intercept, start_index, end_index
            future_bars: Number of bars to project into future
            data: Optional OHLCV data for time calculation
        
        Returns:
            Dictionary with projections, target zones, and future price levels
        """
        try:
            slope = trendline.get('slope', 0)
            intercept = trendline.get('intercept', 0)
            current_index = trendline.get('end_index', 0)
            current_price = trendline.get('end_price', 0)
            
            # Calculate projections for each future bar
            projections = []
            target_prices = []
            
            for i in range(1, future_bars + 1):
                future_index = current_index + i
                projected_price = slope * future_index + intercept
                
                # Calculate time if data provided
                future_time = None
                if data and len(data) > 0:
                    # Estimate time based on average interval
                    last_time = data[-1].get('time', None)
                    if last_time and len(data) > 1:
                        # Calculate average time interval
                        time_intervals = []
                        for j in range(1, min(10, len(data))):
                            if 'time' in data[-j] and 'time' in data[-j-1]:
                                interval = data[-j]['time'] - data[-j-1]['time']
                                if interval > 0:
                                    time_intervals.append(interval)
                        
                        if time_intervals:
                            avg_interval = sum(time_intervals) / len(time_intervals)
                            future_time = last_time + (i * avg_interval)
                
                projections.append({
                    "index": future_index,
                    "price": float(projected_price),
                    "time": future_time,
                    "bars_ahead": i
                })
                target_prices.append(float(projected_price))
            
            # Calculate target zones
            # Upper zone: +2% from projected price
            # Lower zone: -2% from projected price
            if target_prices:
                min_price = min(target_prices)
                max_price = max(target_prices)
                
                target_zone = {
                    "upper": float(max_price * 1.02),
                    "lower": float(min_price * 0.98),
                    "center": float((max_price + min_price) / 2),
                    "width": float(max_price - min_price),
                    "width_percentage": float(((max_price - min_price) / current_price) * 100) if current_price > 0 else 0
                }
            else:
                target_zone = {
                    "upper": current_price * 1.02,
                    "lower": current_price * 0.98,
                    "center": current_price,
                    "width": 0,
                    "width_percentage": 0
                }
            
            # Calculate specific targets at key intervals
            key_targets = {
                "short_term": {
                    "bars": 5,
                    "price": float(projections[4]['price']) if len(projections) > 4 else current_price,
                    "time": projections[4]['time'] if len(projections) > 4 else None
                },
                "medium_term": {
                    "bars": 10,
                    "price": float(projections[9]['price']) if len(projections) > 9 else current_price,
                    "time": projections[9]['time'] if len(projections) > 9 else None
                },
                "long_term": {
                    "bars": 20,
                    "price": float(projections[19]['price']) if len(projections) > 19 else current_price,
                    "time": projections[19]['time'] if len(projections) > 19 else None
                }
            }
            
            return {
                "trendline": {
                    "type": trendline.get('type'),
                    "strength": trendline.get('strength'),
                    "touches": trendline.get('touches'),
                    "current_price": current_price,
                    "current_index": current_index
                },
                "projections": projections,
                "target_zone": target_zone,
                "key_targets": key_targets,
                "future_bars": future_bars,
                "projection_type": "extended" if slope != 0 else "horizontal"
            }
            
        except Exception as e:
            logger.error(f"Error projecting trendline: {e}")
            return {"error": str(e)}
    
    def project_all_trendlines(
        self,
        trendlines: List[Dict[str, Any]],
        future_bars: int = 20,
        data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Project multiple trendlines into future
        
        Args:
            trendlines: List of trendline dictionaries
            future_bars: Number of bars to project
            data: Optional OHLCV data
        
        Returns:
            Dictionary with projections for each trendline
        """
        projections = {}
        
        for i, trendline in enumerate(trendlines):
            projection = self.project_trendline(trendline, future_bars, data)
            if "error" not in projection:
                projections[f"trendline_{i}"] = projection
        
        return {
            "projections": projections,
            "total_trendlines": len(trendlines),
            "future_bars": future_bars
        }

