"""
Swing Point Analysis Service
Detects and labels swing points as Higher High (HH), Higher Low (HL), Lower High (LH), Lower Low (LL)
Essential for market structure analysis and trend identification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from enum import Enum
from scipy.signal import argrelextrema

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

class SwingPointType(str, Enum):
    HIGHER_HIGH = "HH"  # Higher High - Bullish
    HIGHER_LOW = "HL"   # Higher Low - Bullish
    LOWER_HIGH = "LH"   # Lower High - Bearish
    LOWER_LOW = "LL"    # Lower Low - Bearish

class TrendDirection(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"

class SwingPointAnalysisService:
    def __init__(self):
        # Configuration
        self.default_strength = 5  # Number of bars on each side for swing detection
        self.min_swing_distance = 3  # Minimum bars between swings
        
    def analyze_swing_points(
        self,
        data: List[Dict[str, Any]],
        strength: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze price data and identify swing points with HH/HL/LH/LL labels
        
        Args:
            data: OHLCV price data
            strength: Number of bars on each side to confirm a swing point
            
        Returns:
            Dictionary containing swing highs, swing lows, labeled points, and trend analysis
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if len(df) < strength * 2 + 1:
                return {
                    "success": False,
                    "error": "Insufficient data for swing point analysis"
                }
            
            # Detect swing highs and lows
            swing_highs = self._detect_swing_highs(df, strength)
            swing_lows = self._detect_swing_lows(df, strength)
            
            # Label swing points (HH/HL/LH/LL)
            labeled_highs = self._label_swing_highs(swing_highs)
            labeled_lows = self._label_swing_lows(swing_lows)
            
            # Combine all labeled points
            all_labeled_points = self._combine_and_sort_points(labeled_highs, labeled_lows)
            
            # Determine overall trend from swing structure
            trend_analysis = self._analyze_trend_structure(labeled_highs, labeled_lows, df)
            
            # Get statistics
            stats = self._calculate_statistics(labeled_highs, labeled_lows, all_labeled_points)
            
            result = {
                "success": True,
                "data": {
                    "swing_highs": labeled_highs,
                    "swing_lows": labeled_lows,
                    "all_points": all_labeled_points,
                    "trend_analysis": trend_analysis,
                    "statistics": stats,
                    "current_structure": self._get_current_structure(all_labeled_points),
                    "recent_points": all_labeled_points[-10:] if len(all_labeled_points) > 10 else all_labeled_points
                }
            }
            # Convert numpy types to Python types for JSON serialization
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"Error in swing point analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_swing_highs(
        self,
        df: pd.DataFrame,
        strength: int
    ) -> List[Dict[str, Any]]:
        """Detect swing high points (local maxima)"""
        highs = df['high'].values if 'high' in df.columns else df['close'].values
        
        # Find local maxima
        swing_indices = argrelextrema(highs, np.greater, order=strength)[0]
        
        swing_highs = []
        for idx in swing_indices:
            if idx < len(df):
                swing_highs.append({
                    "index": int(idx),
                    "price": float(highs[idx]),
                    "time": df.iloc[idx].get('time', idx),
                    "type": "swing_high"
                })
        
        return swing_highs
    
    def _detect_swing_lows(
        self,
        df: pd.DataFrame,
        strength: int
    ) -> List[Dict[str, Any]]:
        """Detect swing low points (local minima)"""
        lows = df['low'].values if 'low' in df.columns else df['close'].values
        
        # Find local minima
        swing_indices = argrelextrema(lows, np.less, order=strength)[0]
        
        swing_lows = []
        for idx in swing_indices:
            if idx < len(df):
                swing_lows.append({
                    "index": int(idx),
                    "price": float(lows[idx]),
                    "time": df.iloc[idx].get('time', idx),
                    "type": "swing_low"
                })
        
        return swing_lows
    
    def _label_swing_highs(
        self,
        swing_highs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Label swing highs as HH (Higher High) or LH (Lower High)"""
        if len(swing_highs) < 2:
            return swing_highs
        
        labeled = []
        for i, point in enumerate(swing_highs):
            if i == 0:
                # First point has no label
                labeled.append({
                    **point,
                    "label": None,
                    "pattern": "initial"
                })
            else:
                prev_price = swing_highs[i-1]['price']
                current_price = point['price']
                
                if current_price > prev_price:
                    label = SwingPointType.HIGHER_HIGH.value
                    pattern = "bullish"
                else:
                    label = SwingPointType.LOWER_HIGH.value
                    pattern = "bearish"
                
                labeled.append({
                    **point,
                    "label": label,
                    "pattern": pattern,
                    "previous_price": prev_price,
                    "price_change": current_price - prev_price,
                    "price_change_percent": ((current_price - prev_price) / prev_price) * 100
                })
        
        return labeled
    
    def _label_swing_lows(
        self,
        swing_lows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Label swing lows as HL (Higher Low) or LL (Lower Low)"""
        if len(swing_lows) < 2:
            return swing_lows
        
        labeled = []
        for i, point in enumerate(swing_lows):
            if i == 0:
                # First point has no label
                labeled.append({
                    **point,
                    "label": None,
                    "pattern": "initial"
                })
            else:
                prev_price = swing_lows[i-1]['price']
                current_price = point['price']
                
                if current_price > prev_price:
                    label = SwingPointType.HIGHER_LOW.value
                    pattern = "bullish"
                else:
                    label = SwingPointType.LOWER_LOW.value
                    pattern = "bearish"
                
                labeled.append({
                    **point,
                    "label": label,
                    "pattern": pattern,
                    "previous_price": prev_price,
                    "price_change": current_price - prev_price,
                    "price_change_percent": ((current_price - prev_price) / prev_price) * 100
                })
        
        return labeled
    
    def _combine_and_sort_points(
        self,
        highs: List[Dict[str, Any]],
        lows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and sort all swing points chronologically"""
        all_points = highs + lows
        all_points.sort(key=lambda x: x['index'])
        return all_points
    
    def _analyze_trend_structure(
        self,
        labeled_highs: List[Dict[str, Any]],
        labeled_lows: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Analyze the overall trend based on swing structure"""
        
        # Count recent HH/HL vs LH/LL (last 5 of each)
        recent_highs = labeled_highs[-5:] if len(labeled_highs) >= 5 else labeled_highs
        recent_lows = labeled_lows[-5:] if len(labeled_lows) >= 5 else labeled_lows
        
        hh_count = sum(1 for p in recent_highs if p.get('label') == 'HH')
        lh_count = sum(1 for p in recent_highs if p.get('label') == 'LH')
        hl_count = sum(1 for p in recent_lows if p.get('label') == 'HL')
        ll_count = sum(1 for p in recent_lows if p.get('label') == 'LL')
        
        bullish_signals = hh_count + hl_count
        bearish_signals = lh_count + ll_count
        
        # Determine trend
        if bullish_signals > bearish_signals + 1:
            trend = TrendDirection.UPTREND.value
            confidence = "high" if bullish_signals >= bearish_signals * 2 else "medium"
            description = "Making Higher Highs and Higher Lows"
        elif bearish_signals > bullish_signals + 1:
            trend = TrendDirection.DOWNTREND.value
            confidence = "high" if bearish_signals >= bullish_signals * 2 else "medium"
            description = "Making Lower Highs and Lower Lows"
        else:
            trend = TrendDirection.SIDEWAYS.value
            confidence = "medium"
            description = "Mixed swing structure, no clear trend"
        
        # Get current price position
        current_price = float(df.iloc[-1]['close']) if 'close' in df.columns else None
        
        return {
            "trend": trend,
            "confidence": confidence,
            "description": description,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "recent_pattern": {
                "higher_highs": hh_count,
                "lower_highs": lh_count,
                "higher_lows": hl_count,
                "lower_lows": ll_count
            },
            "current_price": current_price
        }
    
    def _calculate_statistics(
        self,
        labeled_highs: List[Dict[str, Any]],
        labeled_lows: List[Dict[str, Any]],
        all_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics about swing points"""
        
        total_highs = len(labeled_highs)
        total_lows = len(labeled_lows)
        
        # Count each type
        hh_count = sum(1 for p in labeled_highs if p.get('label') == 'HH')
        lh_count = sum(1 for p in labeled_highs if p.get('label') == 'LH')
        hl_count = sum(1 for p in labeled_lows if p.get('label') == 'HL')
        ll_count = sum(1 for p in labeled_lows if p.get('label') == 'LL')
        
        return {
            "total_swing_points": len(all_points),
            "total_swing_highs": total_highs,
            "total_swing_lows": total_lows,
            "higher_highs": hh_count,
            "lower_highs": lh_count,
            "higher_lows": hl_count,
            "lower_lows": ll_count,
            "bullish_structure_percent": round(((hh_count + hl_count) / max(total_highs + total_lows - 2, 1)) * 100, 2) if total_highs + total_lows > 2 else 0,
            "bearish_structure_percent": round(((lh_count + ll_count) / max(total_highs + total_lows - 2, 1)) * 100, 2) if total_highs + total_lows > 2 else 0
        }
    
    def _get_current_structure(
        self,
        all_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get the most recent swing structure"""
        if len(all_points) < 2:
            return {
                "status": "insufficient_data",
                "message": "Not enough swing points to determine structure"
            }
        
        # Get last 4 points for structure analysis
        recent_points = all_points[-4:] if len(all_points) >= 4 else all_points
        
        labels = [p.get('label') for p in recent_points if p.get('label')]
        
        if not labels:
            return {
                "status": "no_labels",
                "message": "No labeled points available"
            }
        
        # Determine if we have a clear pattern
        latest_label = labels[-1] if labels else None
        
        if latest_label in ['HH', 'HL']:
            structure = "bullish"
            message = f"Latest swing is {latest_label}, indicating bullish momentum"
        elif latest_label in ['LH', 'LL']:
            structure = "bearish"
            message = f"Latest swing is {latest_label}, indicating bearish momentum"
        else:
            structure = "neutral"
            message = "No clear directional structure"
        
        return {
            "status": "active",
            "structure": structure,
            "latest_label": latest_label,
            "message": message,
            "recent_sequence": " → ".join(labels[-4:])
        }
    
    def get_swing_analysis_summary(
        self,
        data: List[Dict[str, Any]],
        strength: int = 5
    ) -> Dict[str, Any]:
        """Get a summary of swing point analysis for quick display"""
        analysis = self.analyze_swing_points(data, strength)
        
        if not analysis.get("success"):
            return analysis
        
        data_obj = analysis["data"]
        trend = data_obj["trend_analysis"]
        stats = data_obj["statistics"]
        structure = data_obj["current_structure"]
        
        return {
            "success": True,
            "summary": {
                "trend": trend["trend"],
                "confidence": trend["confidence"],
                "description": trend["description"],
                "total_points": stats["total_swing_points"],
                "structure": structure["structure"],
                "latest_signal": structure.get("latest_label", "N/A"),
                "recent_pattern": structure.get("recent_sequence", "N/A")
            }
        }

