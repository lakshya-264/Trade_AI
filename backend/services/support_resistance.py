"""
Support & Resistance Level Detection Service
Identifies key horizontal price levels where price tends to react
Essential for entry/exit planning and risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from scipy.signal import find_peaks
from collections import Counter

logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    elif pd.isna(obj):
        return None
    return obj

class SupportResistanceService:
    def __init__(self):
        self.min_touches = 2  # Minimum touches to confirm a level
        self.price_tolerance = 0.03  # 3% price tolerance for level clustering
        self.tolerance_percent = 0.5  # 0.5% tolerance for level matching
        
    def analyze_support_resistance(
        self,
        data: List[Dict[str, Any]],
        min_touches: int = 2,
        tolerance_percent: float = 0.5,
        lookback_period: int = 100,
        check_double_top: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze and identify support and resistance levels
        
        Args:
            data: OHLCV price data
            min_touches: Minimum number of touches to confirm a level
            tolerance_percent: Price tolerance for level grouping (%)
            lookback_period: How many candles to look back
            
        Returns:
            Dictionary containing support levels, resistance levels, and current price position
        """
        try:
            df = pd.DataFrame(data)
            
            if len(df) < 20:
                return {
                    "success": False,
                    "error": "Insufficient data for S&R analysis"
                }
            
            # Limit lookback
            df = df.tail(lookback_period)
            
            # Ensure we still have data after limiting lookback
            if len(df) == 0:
                return {
                    "success": False,
                    "error": "No data available after applying lookback period"
                }
            
            # Get current price before processing
            current_price = float(df.iloc[-1]['close'])
            
            # Find all potential levels (peaks and troughs)
            potential_levels = self._find_potential_levels(df)
            
            if not potential_levels:
                logger.warning("No potential S&R levels found")
                # Return empty but successful response
                return {
                    "success": True,
                    "data": {
                        "support_levels": [],
                        "resistance_levels": [],
                        "nearest_support": None,
                        "nearest_resistance": None,
                        "trading_zones": [],
                        "current_price": current_price,
                        "statistics": {
                            "total_levels": 0,
                            "support_count": 0,
                            "resistance_count": 0,
                            "nearest_support_distance": None,
                            "nearest_resistance_distance": None
                        }
                    }
                }
            
            # Cluster nearby levels
            clustered_levels = self._cluster_levels(potential_levels, tolerance_percent)
            
            # Validate levels by counting touches
            validated_levels = self._validate_levels(
                df,
                clustered_levels,
                min_touches,
                tolerance_percent
            )
            
            # Classify as support or resistance
            support_levels, resistance_levels = self._classify_levels(
                validated_levels,
                current_price
            )
            
            # Calculate level strength
            support_levels = self._calculate_strength(support_levels, df)
            resistance_levels = self._calculate_strength(resistance_levels, df)
            
            # Check for double top patterns in resistance levels
            double_top_resistance = None
            if check_double_top and len(resistance_levels) > 0:
                double_top_resistance = self._check_double_top_resistance(
                    df, resistance_levels, tolerance_percent
                )
            
            # Mark resistance levels that are double tops
            if double_top_resistance:
                for level in resistance_levels:
                    if abs(level['price'] - double_top_resistance['resistance_level']) < (level['price'] * tolerance_percent / 100):
                        level['is_double_top'] = True
                        level['double_top_info'] = {
                            'first_peak': double_top_resistance['first_peak'],
                            'second_peak': double_top_resistance['second_peak'],
                            'confidence': double_top_resistance['confidence']
                        }
                        level['strength_label'] = 'strong'  # Double top = stronger resistance
                        level['strength'] = min(100, level.get('strength', 0) + 20)  # Boost strength
            
            # Find nearest levels
            nearest = self._find_nearest_levels(
                support_levels,
                resistance_levels,
                current_price
            )
            
            # Generate trading zones
            zones = self._generate_trading_zones(
                support_levels,
                resistance_levels,
                current_price
            )
            
            # Get statistics
            stats = self._calculate_statistics(
                support_levels,
                resistance_levels,
                current_price
            )
            
            result = {
                "success": True,
                "data": {
                    "support_levels": support_levels,
                    "resistance_levels": resistance_levels,
                    "nearest_support": nearest['support'],
                    "nearest_resistance": nearest['resistance'],
                    "trading_zones": zones,
                    "current_price": current_price,
                    "statistics": stats,
                    "double_top_resistance": double_top_resistance
                }
            }
            # Convert numpy types to Python types for JSON serialization
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"Error in S&R analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_potential_levels(self, df: pd.DataFrame) -> List[float]:
        """Find all potential S&R levels using swing highs/lows"""
        levels = []
        
        if len(df) < 10:
            logger.warning(f"DataFrame too small ({len(df)} rows) for peak detection")
            return []
        
        try:
            # Adaptive distance based on data length (more data = can use larger distance)
            # Minimum distance of 3, scales with data size
            adaptive_distance = max(3, min(10, len(df) // 20))
            
            # Find swing highs (resistance candidates)
            highs = df['high'].values if 'high' in df.columns else df['close'].values
            high_peaks, high_properties = find_peaks(
                highs, 
                distance=adaptive_distance,
                prominence=np.std(highs) * 0.5  # Minimum prominence to filter noise
            )
            levels.extend([float(highs[i]) for i in high_peaks if i < len(highs)])
            
            # Find swing lows (support candidates)
            lows = df['low'].values if 'low' in df.columns else df['close'].values
            low_peaks, low_properties = find_peaks(
                -lows, 
                distance=adaptive_distance,
                prominence=np.std(lows) * 0.5  # Minimum prominence to filter noise
            )
            levels.extend([float(lows[i]) for i in low_peaks if i < len(lows)])
            
            # Include high volume nodes (price levels with high volume = important S/R)
            if 'volume' in df.columns and len(df) > 0:
                volume_values = df['volume'].values
                volume_mean = volume_values.mean()
                volume_std = volume_values.std()
                if volume_mean > 0 and volume_std > 0:
                    # Find volume peaks (high volume nodes)
                    volume_peaks, _ = find_peaks(
                        volume_values, 
                        prominence=volume_mean * 0.5  # At least 50% above mean
                    )
                    for idx in volume_peaks:
                        if 0 <= idx < len(df):
                            # Use the price where high volume occurred
                            vol_price = float(df.iloc[idx]['close'])
                            levels.append(vol_price)
            
            # Add psychological levels (round numbers) near price range
            if len(df) > 0:
                price_range = df['close'].max() - df['close'].min()
                current_price = float(df.iloc[-1]['close'])
                
                # Add round number levels within reasonable range
                # For prices > 1000, round to nearest 50
                # For prices > 100, round to nearest 10
                # For prices < 100, round to nearest 5
                if current_price > 1000:
                    round_base = 50
                elif current_price > 100:
                    round_base = 10
                else:
                    round_base = 5
                
                # Add round numbers within 20% of price range
                min_price = df['close'].min()
                max_price = df['close'].max()
                range_span = max_price - min_price
                
                # Generate round numbers in the range
                start_round = int(min_price // round_base) * round_base
                end_round = int(max_price // round_base) * round_base + round_base
                
                for round_level in range(int(start_round), int(end_round) + round_base, round_base):
                    if min_price <= round_level <= max_price:
                        levels.append(float(round_level))
            
        except Exception as e:
            logger.error(f"Error finding potential levels: {e}")
            return []
        
        return levels
    
    def _cluster_levels(
        self,
        levels: List[float],
        tolerance_percent: float
    ) -> List[Dict[str, Any]]:
        """Group nearby levels together"""
        if not levels:
            return []
        
        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            # Check if within tolerance of current cluster
            cluster_avg = np.mean(current_cluster)
            tolerance = cluster_avg * (tolerance_percent / 100)
            
            if abs(level - cluster_avg) <= tolerance:
                current_cluster.append(level)
            else:
                # Save current cluster and start new one
                clusters.append({
                    'price': np.mean(current_cluster),
                    'count': len(current_cluster),
                    'min': min(current_cluster),
                    'max': max(current_cluster)
                })
                current_cluster = [level]
        
        # Don't forget last cluster
        if current_cluster:
            clusters.append({
                'price': np.mean(current_cluster),
                'count': len(current_cluster),
                'min': min(current_cluster),
                'max': max(current_cluster)
            })
        
        return clusters
    
    def _validate_levels(
        self,
        df: pd.DataFrame,
        clusters: List[Dict[str, Any]],
        min_touches: int,
        tolerance_percent: float
    ) -> List[Dict[str, Any]]:
        """Validate levels by counting actual touches"""
        validated = []
        
        for cluster in clusters:
            level_price = cluster['price']
            tolerance = level_price * (tolerance_percent / 100)
            
            # Count touches
            touches = 0
            touch_indices = []
            
            for idx, row in df.iterrows():
                high = float(row.get('high', row.get('close', 0)))
                low = float(row.get('low', row.get('close', 0)))
                
                # Skip invalid data
                if high <= 0 or low <= 0 or high < low:
                    continue
                
                # Check if candle touched the level (more accurate touch detection)
                # A touch occurs when the level is within the candle's high-low range
                # OR when the candle's wick/extreme touches the level
                level_touched = False
                
                # Method 1: Level is within candle body/wicks
                if low - tolerance <= level_price <= high + tolerance:
                    level_touched = True
                # Method 2: Level is very close to high or low (wick touch)
                elif abs(high - level_price) <= tolerance or abs(low - level_price) <= tolerance:
                    level_touched = True
                
                if level_touched:
                    touches += 1
                    touch_indices.append(idx)
            
            if touches >= min_touches:
                # Safely get first and last touch times with bounds checking
                first_touch = None
                last_touch = None
                if touch_indices:
                    first_idx = touch_indices[0]
                    last_idx = touch_indices[-1]
                    if 0 <= first_idx < len(df):
                        first_touch = df.iloc[first_idx].get('time', first_idx)
                    if 0 <= last_idx < len(df):
                        last_touch = df.iloc[last_idx].get('time', last_idx)
                
                validated.append({
                    'price': level_price,
                    'touches': touches,
                    'touch_indices': touch_indices,
                    'first_touch': first_touch,
                    'last_touch': last_touch,
                    'cluster_size': cluster['count']
                })
        
        return validated
    
    def _classify_levels(
        self,
        levels: List[Dict[str, Any]],
        current_price: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Classify levels as support or resistance based on current price"""
        support = []
        resistance = []
        
        # Tolerance for "too close" levels (within 0.1% of current price)
        close_tolerance = current_price * 0.001
        
        for level in levels:
            level_price = level.get('price', 0)
            if level_price <= 0:
                continue  # Skip invalid prices
            
            price_diff = abs(level_price - current_price)
            
            # Skip levels too close to current price (within 0.1%)
            if price_diff < close_tolerance:
                continue
            
            # Support: price levels BELOW current price
            if level_price < current_price:
                level['type'] = 'support'
                support.append(level)
            # Resistance: price levels ABOVE current price
            elif level_price > current_price:
                level['type'] = 'resistance'
                resistance.append(level)
        
        # Sort support descending (highest support = nearest to current price)
        support.sort(key=lambda x: x['price'], reverse=True)
        
        # Sort resistance ascending (lowest resistance = nearest to current price)
        resistance.sort(key=lambda x: x['price'])
        
        return support, resistance
    
    def _calculate_strength(
        self,
        levels: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Calculate strength of each level"""
        for level in levels:
            # Strength factors:
            # 1. Number of touches (more = stronger)
            # 2. Cluster size (more nearby levels = stronger)
            # 3. Age (older = stronger if still valid)
            
            touch_score = min(level['touches'] / 10, 1.0)  # Normalize to 0-1
            cluster_score = min(level['cluster_size'] / 5, 1.0)
            
            # Calculate age score
            if level['touch_indices']:
                age = len(df) - level['touch_indices'][0]
                age_score = min(age / len(df), 0.5)  # Max 0.5 from age
            else:
                age_score = 0
            
            # Combined strength (0-100)
            strength = (touch_score * 50 + cluster_score * 30 + age_score * 20)
            
            level['strength'] = round(strength, 2)
            level['strength_label'] = 'strong' if strength > 70 else 'medium' if strength > 40 else 'weak'
        
        return levels
    
    def _find_nearest_levels(
        self,
        support_levels: List[Dict[str, Any]],
        resistance_levels: List[Dict[str, Any]],
        current_price: float
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Find nearest support and resistance to current price"""
        # Filter and find actual nearest levels
        # Support must be BELOW current price (find maximum support below current)
        valid_supports = [s for s in support_levels if s['price'] < current_price]
        nearest_support = max(valid_supports, key=lambda x: x['price']) if valid_supports else None
        
        # Resistance must be ABOVE current price (find minimum resistance above current)
        valid_resistances = [r for r in resistance_levels if r['price'] > current_price]
        nearest_resistance = min(valid_resistances, key=lambda x: x['price']) if valid_resistances else None
        
        result = {
            'support': nearest_support,
            'resistance': nearest_resistance
        }
        
        if nearest_support:
            distance = current_price - nearest_support['price']
            distance_percent = (distance / current_price) * 100
            result['support']['distance'] = distance
            result['support']['distance_percent'] = distance_percent
        
        if nearest_resistance:
            distance = nearest_resistance['price'] - current_price
            distance_percent = (distance / current_price) * 100
            result['resistance']['distance'] = distance
            result['resistance']['distance_percent'] = distance_percent
        
        return result
    
    def _generate_trading_zones(
        self,
        support_levels: List[Dict[str, Any]],
        resistance_levels: List[Dict[str, Any]],
        current_price: float
    ) -> Dict[str, Any]:
        """Generate trading zones based on S&R levels"""
        
        nearest_support = support_levels[0] if support_levels else None
        nearest_resistance = resistance_levels[0] if resistance_levels else None
        
        if not nearest_support or not nearest_resistance:
            return {
                "status": "insufficient_levels",
                "message": "Need both support and resistance for zones"
            }
        
        # Calculate range
        range_size = nearest_resistance['price'] - nearest_support['price']
        range_percent = (range_size / current_price) * 100
        
        # Determine zone
        mid_point = (nearest_support['price'] + nearest_resistance['price']) / 2
        
        if current_price < mid_point - (range_size * 0.2):
            zone = "lower"
            message = "Price near support - Watch for bounce"
        elif current_price > mid_point + (range_size * 0.2):
            zone = "upper"
            message = "Price near resistance - Watch for rejection"
        else:
            zone = "middle"
            message = "Price in middle of range"
        
        return {
            "status": "active",
            "zone": zone,
            "message": message,
            "support": nearest_support['price'],
            "resistance": nearest_resistance['price'],
            "range_size": round(range_size, 2),
            "range_percent": round(range_percent, 2),
            "mid_point": round(mid_point, 2)
        }
    
    def _check_double_top_resistance(
        self,
        df: pd.DataFrame,
        resistance_levels: List[Dict[str, Any]],
        tolerance_percent: float
    ) -> Optional[Dict[str, Any]]:
        """Check if any resistance level is a double top pattern"""
        try:
            if len(df) < 30:
                logger.debug("Insufficient data for double top detection (< 30 candles)")
                return None
            
            highs = df["high"].values
            lows = df["low"].values
            
            # Find swing highs with adaptive distance
            from scipy.signal import find_peaks
            adaptive_distance = max(3, min(10, len(df) // 20))
            swing_highs = find_peaks(highs, distance=adaptive_distance)[0]
            
            logger.debug(f"Found {len(swing_highs)} swing highs for double top detection")
            
            if len(swing_highs) < 2:
                logger.debug("Not enough swing highs for double top detection")
                return None
            
            # Check for double top pattern
            best_match = None
            best_confidence = 0
            
            for i in range(len(swing_highs) - 1):
                first_idx = swing_highs[i]
                second_idx = swing_highs[i + 1]
                
                if second_idx - first_idx < 5:
                    continue
                
                first_peak = highs[first_idx]
                second_peak = highs[second_idx]
                
                # Check if peaks are similar (within 2%)
                peak_diff_pct = abs(first_peak - second_peak) / first_peak
                if peak_diff_pct > 0.02:
                    continue
                
                # Find neckline
                neckline = lows[first_idx:second_idx+1].min()
                valley_depth = (first_peak - neckline) / first_peak
                
                if valley_depth < 0.03:
                    continue
                
                resistance_level = (first_peak + second_peak) / 2
                
                # Check if this matches any detected resistance level
                # Use a more lenient matching (up to 1% difference)
                for level in resistance_levels:
                    level_price = level.get('price', 0)
                    # Use 1% tolerance for matching (more lenient than 0.5%)
                    match_tolerance = level_price * 0.01  # 1% tolerance
                    
                    if abs(level_price - resistance_level) <= match_tolerance:
                        # Found matching resistance level - it's a double top!
                        confidence = 0.65
                        if peak_diff_pct < 0.01:
                            confidence = 0.80
                        elif peak_diff_pct < 0.015:
                            confidence = 0.70
                        
                        # Prefer higher confidence matches
                        if confidence > best_confidence:
                            best_match = {
                                "resistance_level": float(resistance_level),
                                "matched_level_price": float(level_price),
                                "first_peak": float(first_peak),
                                "second_peak": float(second_peak),
                                "neckline": float(neckline),
                                "confidence": round(confidence, 2),
                                "pattern_height": float(first_peak - neckline),
                                "valley_depth_pct": round(valley_depth * 100, 2),
                                "peak_similarity_pct": round(peak_diff_pct * 100, 2),
                                "first_peak_idx": int(first_idx),
                                "second_peak_idx": int(second_idx)
                            }
                            best_confidence = confidence
                            logger.info(f"Double top detected at resistance level ₹{resistance_level:.2f} "
                                      f"(matched with level ₹{level_price:.2f}), "
                                      f"peaks: ₹{first_peak:.2f} / ₹{second_peak:.2f}, "
                                      f"confidence: {confidence:.2f}")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error checking double top resistance: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_statistics(
        self,
        support_levels: List[Dict[str, Any]],
        resistance_levels: List[Dict[str, Any]],
        current_price: float
    ) -> Dict[str, Any]:
        """Calculate statistics about S&R levels"""
        
        total_levels = len(support_levels) + len(resistance_levels)
        
        strong_support = sum(1 for l in support_levels if l['strength_label'] == 'strong')
        strong_resistance = sum(1 for l in resistance_levels if l['strength_label'] == 'strong')
        
        # Count double top resistance levels
        double_top_count = sum(1 for l in resistance_levels if l.get('is_double_top', False))
        
        avg_support_strength = np.mean([l['strength'] for l in support_levels]) if support_levels else 0
        avg_resistance_strength = np.mean([l['strength'] for l in resistance_levels]) if resistance_levels else 0
        
        return {
            "total_levels": total_levels,
            "support_count": len(support_levels),
            "resistance_count": len(resistance_levels),
            "strong_support_count": strong_support,
            "strong_resistance_count": strong_resistance,
            "double_top_resistance_count": double_top_count,
            "avg_support_strength": round(avg_support_strength, 2),
            "avg_resistance_strength": round(avg_resistance_strength, 2)
        }

