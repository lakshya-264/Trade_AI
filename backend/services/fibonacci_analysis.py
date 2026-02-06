"""
Fibonacci Analysis Service
Provides comprehensive Fibonacci tools for technical analysis:
- Fibonacci Retracement
- Fibonacci Extension
- Fibonacci Fan
- Fibonacci Arcs
- Fibonacci Time Zones
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class FibonacciType(str, Enum):
    RETRACEMENT = "retracement"
    EXTENSION = "extension"
    FAN = "fan"
    ARC = "arc"
    TIME_ZONE = "time_zone"

class TrendDirection(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"

class FibonacciAnalysisService:
    def __init__(self):
        # Standard Fibonacci ratios
        self.retracement_levels = {
            "0.0": 0.000,
            "0.236": 0.236,
            "0.382": 0.382,
            "0.500": 0.500,
            "0.618": 0.618,
            "0.786": 0.786,
            "1.0": 1.000
        }
        
        self.extension_levels = {
            "1.0": 1.000,
            "1.272": 1.272,
            "1.414": 1.414,
            "1.618": 1.618,
            "2.0": 2.000,
            "2.618": 2.618,
            "3.618": 3.618,
            "4.236": 4.236
        }
        
        # Cache for analysis results
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def calculate_fibonacci_retracement(
        self,
        high: float,
        low: float,
        trend_direction: str = "uptrend",
        custom_levels: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate Fibonacci retracement levels
        
        Args:
            high: Swing high price
            low: Swing low price
            trend_direction: "uptrend" or "downtrend"
            custom_levels: Optional custom Fibonacci ratios
        
        Returns:
            Dictionary with retracement levels and analysis
        """
        try:
            # Use custom levels if provided
            if custom_levels:
                levels = {f"{level:.3f}": level for level in custom_levels}
            else:
                levels = self.retracement_levels
            
            # Calculate price difference
            price_diff = high - low
            
            # Calculate retracement levels
            retracement_prices = {}
            
            if trend_direction.lower() == "uptrend":
                # For uptrend, retracements are calculated from high
                for name, ratio in levels.items():
                    retracement_prices[name] = high - (price_diff * ratio)
            else:
                # For downtrend, retracements are calculated from low
                for name, ratio in levels.items():
                    retracement_prices[name] = low + (price_diff * ratio)
            
            # Identify key levels
            key_levels = self._identify_key_retracement_levels(retracement_prices)
            
            result = {
                "type": "fibonacci_retracement",
                "trend_direction": trend_direction,
                "swing_high": high,
                "swing_low": low,
                "price_range": price_diff,
                "levels": retracement_prices,
                "key_levels": key_levels,
                "trading_implications": self._get_retracement_implications(
                    trend_direction, key_levels
                ),
                "calculated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Calculated Fibonacci retracement: {high} to {low}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci retracement: {e}")
            return {}
    
    def calculate_fibonacci_extension(
        self,
        point_a: float,
        point_b: float,
        point_c: float,
        custom_levels: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate Fibonacci extension levels (for profit targets)
        
        Args:
            point_a: First swing point
            point_b: Second swing point (retracement)
            point_c: Third swing point (continuation)
            custom_levels: Optional custom extension ratios
        
        Returns:
            Dictionary with extension levels and targets
        """
        try:
            # Use custom levels if provided
            if custom_levels:
                levels = {f"{level:.3f}": level for level in custom_levels}
            else:
                levels = self.extension_levels
            
            # Calculate moves
            ab_move = point_b - point_a
            bc_move = point_c - point_b
            
            # Determine trend direction
            trend_direction = "uptrend" if ab_move > 0 else "downtrend"
            
            # Calculate extension levels
            extension_prices = {}
            
            if trend_direction == "uptrend":
                # Extensions project from point C upward
                for name, ratio in levels.items():
                    extension_prices[name] = point_c + (abs(ab_move) * ratio)
            else:
                # Extensions project from point C downward
                for name, ratio in levels.items():
                    extension_prices[name] = point_c - (abs(ab_move) * ratio)
            
            result = {
                "type": "fibonacci_extension",
                "trend_direction": trend_direction,
                "point_a": point_a,
                "point_b": point_b,
                "point_c": point_c,
                "ab_move": ab_move,
                "bc_move": bc_move,
                "levels": extension_prices,
                "profit_targets": self._identify_profit_targets(extension_prices),
                "trading_implications": self._get_extension_implications(
                    extension_prices, trend_direction
                ),
                "calculated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Calculated Fibonacci extension: A={point_a}, B={point_b}, C={point_c}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci extension: {e}")
            return {}
    
    def auto_detect_fibonacci_levels(
        self,
        data: List[Dict[str, Any]],
        lookback_period: int = 50,
        min_swing_strength: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Automatically detect significant swing points and calculate Fibonacci levels
        
        Args:
            data: OHLCV data
            lookback_period: Number of candles to analyze
            min_swing_strength: Minimum bars on each side for swing detection
        
        Returns:
            List of detected Fibonacci setups
        """
        try:
            if len(data) < lookback_period:
                return []
            
            df = pd.DataFrame(data[-lookback_period:])
            
            # Detect swing highs and lows
            swing_highs = self._detect_swing_highs(df, min_swing_strength)
            swing_lows = self._detect_swing_lows(df, min_swing_strength)
            
            fibonacci_setups = []
            
            # Find recent significant swings
            recent_swings = self._find_recent_swings(swing_highs, swing_lows, df)
            
            for swing in recent_swings:
                fib_levels = self.calculate_fibonacci_retracement(
                    high=swing['high'],
                    low=swing['low'],
                    trend_direction=swing['direction']
                )
                
                # Add swing metadata
                fib_levels['swing_high_index'] = swing['high_index']
                fib_levels['swing_low_index'] = swing['low_index']
                fib_levels['strength'] = swing['strength']
                fib_levels['current_price'] = float(df.iloc[-1]['close'])
                
                # Determine current level
                current_level = self._determine_current_level(
                    fib_levels['current_price'],
                    fib_levels['levels']
                )
                fib_levels['current_level'] = current_level
                
                fibonacci_setups.append(fib_levels)
            
            logger.info(f"Auto-detected {len(fibonacci_setups)} Fibonacci setups")
            return fibonacci_setups
            
        except Exception as e:
            logger.error(f"Error auto-detecting Fibonacci levels: {e}")
            return []
    
    def analyze_price_at_fib_level(
        self,
        current_price: float,
        fib_levels: Dict[str, float],
        tolerance: float = 0.005  # 0.5% tolerance
    ) -> Dict[str, Any]:
        """
        Analyze if current price is at or near a Fibonacci level
        
        Args:
            current_price: Current stock price
            fib_levels: Fibonacci levels dictionary
            tolerance: Price tolerance as percentage
        
        Returns:
            Analysis of price position relative to Fibonacci levels
        """
        try:
            nearby_levels = []
            
            for level_name, level_price in fib_levels.items():
                price_diff = abs(current_price - level_price)
                price_diff_pct = (price_diff / current_price) * 100
                
                if price_diff_pct <= (tolerance * 100):
                    nearby_levels.append({
                        "level": level_name,
                        "price": level_price,
                        "distance": price_diff,
                        "distance_pct": price_diff_pct,
                        "significance": self._get_level_significance(level_name)
                    })
            
            # Sort by distance
            nearby_levels.sort(key=lambda x: x['distance'])
            
            # Determine next support and resistance
            support_levels = [l for l in fib_levels.items() if l[1] < current_price]
            resistance_levels = [l for l in fib_levels.items() if l[1] > current_price]
            
            next_support = max(support_levels, key=lambda x: x[1]) if support_levels else None
            next_resistance = min(resistance_levels, key=lambda x: x[1]) if resistance_levels else None
            
            result = {
                "current_price": current_price,
                "at_fibonacci_level": len(nearby_levels) > 0,
                "nearby_levels": nearby_levels,
                "next_support": {
                    "level": next_support[0],
                    "price": next_support[1]
                } if next_support else None,
                "next_resistance": {
                    "level": next_resistance[0],
                    "price": next_resistance[1]
                } if next_resistance else None,
                "trading_signal": self._generate_fib_trading_signal(
                    current_price, nearby_levels, next_support, next_resistance
                )
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing price at Fibonacci level: {e}")
            return {}
    
    def calculate_fibonacci_clusters(
        self,
        multiple_fib_setups: List[Dict[str, Any]],
        cluster_tolerance: float = 0.01  # 1% tolerance
    ) -> List[Dict[str, Any]]:
        """
        Identify price levels where multiple Fibonacci levels cluster together
        (these are often strong support/resistance zones)
        
        Args:
            multiple_fib_setups: List of different Fibonacci calculations
            cluster_tolerance: Price tolerance for clustering
        
        Returns:
            List of identified Fibonacci clusters
        """
        try:
            all_levels = []
            
            # Collect all Fibonacci levels from all setups
            for setup in multiple_fib_setups:
                for level_name, level_price in setup.get('levels', {}).items():
                    all_levels.append({
                        "level": level_name,
                        "price": level_price,
                        "setup_id": setup.get('swing_high_index', 0)
                    })
            
            # Find clusters
            clusters = []
            processed = set()
            
            for i, level1 in enumerate(all_levels):
                if i in processed:
                    continue
                
                cluster_levels = [level1]
                cluster_prices = [level1['price']]
                
                for j, level2 in enumerate(all_levels[i+1:], start=i+1):
                    if j in processed:
                        continue
                    
                    price_diff_pct = abs(level1['price'] - level2['price']) / level1['price']
                    
                    if price_diff_pct <= cluster_tolerance:
                        cluster_levels.append(level2)
                        cluster_prices.append(level2['price'])
                        processed.add(j)
                
                if len(cluster_levels) >= 2:  # At least 2 levels must cluster
                    clusters.append({
                        "cluster_price": np.mean(cluster_prices),
                        "cluster_size": len(cluster_levels),
                        "levels": cluster_levels,
                        "strength": self._calculate_cluster_strength(cluster_levels),
                        "significance": "high" if len(cluster_levels) >= 3 else "medium"
                    })
                
                processed.add(i)
            
            # Sort by cluster strength
            clusters.sort(key=lambda x: x['strength'], reverse=True)
            
            logger.info(f"Identified {len(clusters)} Fibonacci clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci clusters: {e}")
            return []
    
    # Helper methods
    
    def _identify_key_retracement_levels(
        self,
        levels: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Identify most significant retracement levels"""
        key_ratios = ['0.382', '0.500', '0.618']
        key_levels = []
        
        for ratio in key_ratios:
            if ratio in levels:
                key_levels.append({
                    "level": ratio,
                    "price": levels[ratio],
                    "significance": self._get_level_significance(ratio)
                })
        
        return key_levels
    
    def _get_level_significance(self, level: str) -> str:
        """Determine significance of a Fibonacci level"""
        high_significance = ['0.382', '0.618', '1.618']
        medium_significance = ['0.500', '0.786', '1.272']
        
        if level in high_significance:
            return "high"
        elif level in medium_significance:
            return "medium"
        else:
            return "low"
    
    def _get_retracement_implications(
        self,
        trend_direction: str,
        key_levels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trading implications for retracement levels"""
        return {
            "trend_direction": trend_direction,
            "optimal_entry_zones": [
                f"{level['level']} level at ₹{level['price']:.2f}"
                for level in key_levels
            ],
            "stop_loss_suggestion": "Place stop loss below 0.786 retracement for uptrend, above for downtrend",
            "confidence": "High when price reacts at 0.618 level",
            "invalidation": "Trend invalidated if price breaks 1.0 level"
        }
    
    def _identify_profit_targets(
        self,
        extension_prices: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Identify optimal profit targets from extensions"""
        targets = []
        priority_levels = ['1.272', '1.618', '2.0', '2.618']
        
        for level in priority_levels:
            if level in extension_prices:
                targets.append({
                    "level": level,
                    "price": extension_prices[level],
                    "priority": "high" if level in ['1.618', '2.618'] else "medium"
                })
        
        return targets
    
    def _get_extension_implications(
        self,
        extension_prices: Dict[str, float],
        trend_direction: str
    ) -> Dict[str, Any]:
        """Generate trading implications for extension levels"""
        return {
            "primary_target": "1.618 extension",
            "extended_target": "2.618 extension",
            "profit_booking": "Book partial profits at each extension level",
            "trend_continuation": f"Strong {trend_direction} if 1.272 is breached"
        }
    
    def _detect_swing_highs(
        self,
        df: pd.DataFrame,
        strength: int = 5
    ) -> List[Tuple[int, float]]:
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
                swing_highs.append((i, current_high))
        
        return swing_highs
    
    def _detect_swing_lows(
        self,
        df: pd.DataFrame,
        strength: int = 5
    ) -> List[Tuple[int, float]]:
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
                swing_lows.append((i, current_low))
        
        return swing_lows
    
    def _find_recent_swings(
        self,
        swing_highs: List[Tuple[int, float]],
        swing_lows: List[Tuple[int, float]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Find most recent significant swings"""
        swings = []
        
        if not swing_highs or not swing_lows:
            return swings
        
        # Get most recent swing high and low
        recent_high = max(swing_highs, key=lambda x: x[0])
        recent_low = max(swing_lows, key=lambda x: x[0])
        
        # Determine if we're in uptrend or downtrend
        if recent_high[0] > recent_low[0]:
            # Uptrend - high came after low
            direction = "downtrend"  # Retracement from high
            high_val = recent_high[1]
            low_val = recent_low[1]
            high_idx = recent_high[0]
            low_idx = recent_low[0]
        else:
            # Downtrend or continuation
            direction = "uptrend"  # Retracement from low
            high_val = recent_high[1]
            low_val = recent_low[1]
            high_idx = recent_high[0]
            low_idx = recent_low[0]
        
        swings.append({
            "high": high_val,
            "low": low_val,
            "high_index": high_idx,
            "low_index": low_idx,
            "direction": direction,
            "strength": abs(high_val - low_val) / low_val * 100  # Percentage move
        })
        
        return swings
    
    def _determine_current_level(
        self,
        current_price: float,
        fib_levels: Dict[str, float]
    ) -> Optional[str]:
        """Determine which Fibonacci level current price is near"""
        tolerance = 0.005  # 0.5%
        
        for level_name, level_price in fib_levels.items():
            price_diff_pct = abs(current_price - level_price) / current_price
            if price_diff_pct <= tolerance:
                return level_name
        
        return None
    
    def _generate_fib_trading_signal(
        self,
        current_price: float,
        nearby_levels: List[Dict],
        next_support: Optional[Tuple],
        next_resistance: Optional[Tuple]
    ) -> Dict[str, Any]:
        """Generate trading signal based on Fibonacci analysis"""
        
        if not nearby_levels:
            return {
                "signal": "NEUTRAL",
                "confidence": 0,
                "reason": "Price not near any Fibonacci level"
            }
        
        # Price is at a Fibonacci level
        strongest_level = nearby_levels[0]
        level_significance = strongest_level['significance']
        
        signal = {
            "signal": "WATCH",
            "confidence": 70 if level_significance == "high" else 50,
            "reason": f"Price at {strongest_level['level']} Fibonacci level",
            "action": "Wait for confirmation before entering"
        }
        
        # Add specific recommendations
        if next_support:
            signal['support'] = f"{next_support[0]} at ₹{next_support[1]:.2f}"
        if next_resistance:
            signal['resistance'] = f"{next_resistance[0]} at ₹{next_resistance[1]:.2f}"
        
        return signal
    
    def _calculate_cluster_strength(
        self,
        cluster_levels: List[Dict]
    ) -> float:
        """Calculate strength of a Fibonacci cluster"""
        # More levels = stronger cluster
        size_score = len(cluster_levels) * 20
        
        # Check for significant ratios
        significant_count = sum(
            1 for level in cluster_levels
            if self._get_level_significance(level['level']) == "high"
        )
        significance_score = significant_count * 30
        
        return min(100, size_score + significance_score)

