"""
Market Structure Analysis Service
Detects Break of Structure (BOS) and Change of Character (CHoCH)
Essential for Smart Money Concepts and trend reversal identification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from enum import Enum

# Import swing point service to leverage existing logic
from services.swing_point_analysis import SwingPointAnalysisService, SwingPointType

logger = logging.getLogger(__name__)

class StructureBreakType(str, Enum):
    BOS_BULLISH = "BOS_Bullish"      # Break of Structure in uptrend
    BOS_BEARISH = "BOS_Bearish"      # Break of Structure in downtrend
    CHOCH_BULLISH = "CHoCH_Bullish"  # Change of Character to bullish
    CHOCH_BEARISH = "CHoCH_Bearish"  # Change of Character to bearish

class MarketStructureService:
    def __init__(self):
        # Use swing point service for structure detection
        self.swing_service = SwingPointAnalysisService()
        
    def analyze_market_structure(
        self,
        data: List[Dict[str, Any]],
        strength: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze market structure and detect BOS/CHoCH
        
        Args:
            data: OHLCV price data
            strength: Swing detection strength
            
        Returns:
            Dictionary containing structure breaks, current structure, and trading signals
        """
        try:
            # Validate input data
            if not data or len(data) < strength * 4:
                return {
                    "success": False,
                    "error": f"Insufficient data. Need at least {strength * 4} candles, got {len(data) if data else 0}"
                }
            
            # First, get swing points
            swing_analysis = self.swing_service.analyze_swing_points(data, strength)
            
            if not swing_analysis.get("success"):
                return {
                    "success": False,
                    "error": swing_analysis.get("error", "Failed to analyze swing points")
                }
            
            swing_data = swing_analysis["data"]
            
            # Validate swing data
            if not swing_data or "swing_highs" not in swing_data or "swing_lows" not in swing_data:
                return {
                    "success": False,
                    "error": "Invalid swing analysis data structure"
                }
            
            try:
                df = pd.DataFrame(data)
                if df.empty:
                    return {
                        "success": False,
                        "error": "DataFrame is empty after conversion"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create DataFrame: {str(e)}"
                }
            
            # Detect BOS and CHoCH
            try:
                bos_events = self._detect_break_of_structure(
                    swing_data["swing_highs"],
                    swing_data["swing_lows"],
                    df
                )
                
                choch_events = self._detect_change_of_character(
                    swing_data["swing_highs"],
                    swing_data["swing_lows"],
                    df
                )
            except Exception as e:
                logger.error(f"Error detecting structure breaks: {e}")
                return {
                    "success": False,
                    "error": f"Error detecting structure breaks: {str(e)}"
                }
            
            # Combine all structure breaks
            all_breaks = self._combine_structure_breaks(bos_events, choch_events)
            
            # Determine current market structure
            current_structure = self._get_current_structure(
                all_breaks,
                swing_data["trend_analysis"],
                df
            )
            
            # Generate trading signals
            signals = self._generate_trading_signals(
                all_breaks,
                current_structure,
                df
            )
            
            # Get statistics
            stats = self._calculate_statistics(bos_events, choch_events, all_breaks)
            
            return {
                "success": True,
                "data": {
                    "bos_events": bos_events,
                    "choch_events": choch_events,
                    "all_structure_breaks": all_breaks,
                    "current_structure": current_structure,
                    "trading_signals": signals,
                    "statistics": stats,
                    "swing_analysis": swing_data["trend_analysis"]
                }
            }
            
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Error in market structure analysis: {error_msg}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def _detect_break_of_structure(
        self,
        swing_highs: List[Dict[str, Any]],
        swing_lows: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Detect Break of Structure (BOS) - continuation pattern"""
        bos_events = []
        
        # BOS Bullish: Price breaks above previous swing high in uptrend
        for i in range(1, len(swing_highs)):
            prev_high = swing_highs[i-1]
            current_high = swing_highs[i]
            
            if current_high.get('label') == 'HH':
                # Find where price broke above previous high
                break_index = self._find_break_point(
                    df,
                    prev_high['index'],
                    current_high['index'],
                    prev_high['price'],
                    'above'
                )
                
                if break_index is not None:
                    bos_events.append({
                        "type": StructureBreakType.BOS_BULLISH.value,
                        "break_index": int(break_index),
                        "break_price": float(df.iloc[break_index]['close']),
                        "previous_level": float(prev_high['price']),
                        "broken_at": df.iloc[break_index].get('time', break_index),
                        "confidence": "high" if current_high.get('price_change_percent', 0) > 2 else "medium",
                        "description": f"Bullish BOS - Broke above {prev_high['price']:.2f}"
                    })
        
        # BOS Bearish: Price breaks below previous swing low in downtrend
        for i in range(1, len(swing_lows)):
            prev_low = swing_lows[i-1]
            current_low = swing_lows[i]
            
            if current_low.get('label') == 'LL':
                # Find where price broke below previous low
                break_index = self._find_break_point(
                    df,
                    prev_low['index'],
                    current_low['index'],
                    prev_low['price'],
                    'below'
                )
                
                if break_index is not None:
                    bos_events.append({
                        "type": StructureBreakType.BOS_BEARISH.value,
                        "break_index": int(break_index),
                        "break_price": float(df.iloc[break_index]['close']),
                        "previous_level": float(prev_low['price']),
                        "broken_at": df.iloc[break_index].get('time', break_index),
                        "confidence": "high" if abs(current_low.get('price_change_percent', 0)) > 2 else "medium",
                        "description": f"Bearish BOS - Broke below {prev_low['price']:.2f}"
                    })
        
        return bos_events
    
    def _detect_change_of_character(
        self,
        swing_highs: List[Dict[str, Any]],
        swing_lows: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Detect Change of Character (CHoCH) - reversal pattern"""
        choch_events = []
        
        # CHoCH Bullish: Price in downtrend breaks above previous swing high (reversal)
        for i in range(1, len(swing_highs)):
            prev_high = swing_highs[i-1]
            
            # Look for LH followed by break above previous high
            if prev_high.get('label') == 'LH':
                # Check if price breaks above this LH
                start_idx = prev_high['index']
                end_idx = min(start_idx + 50, len(df))
                
                break_index = self._find_break_point(
                    df,
                    start_idx,
                    end_idx,
                    prev_high['price'],
                    'above'
                )
                
                if break_index is not None:
                    choch_events.append({
                        "type": StructureBreakType.CHOCH_BULLISH.value,
                        "break_index": int(break_index),
                        "break_price": float(df.iloc[break_index]['close']),
                        "previous_level": float(prev_high['price']),
                        "broken_at": df.iloc[break_index].get('time', break_index),
                        "confidence": "high",
                        "description": f"Bullish CHoCH - Reversal signal at {prev_high['price']:.2f}"
                    })
        
        # CHoCH Bearish: Price in uptrend breaks below previous swing low (reversal)
        for i in range(1, len(swing_lows)):
            prev_low = swing_lows[i-1]
            
            # Look for HL followed by break below previous low
            if prev_low.get('label') == 'HL':
                # Check if price breaks below this HL
                start_idx = prev_low['index']
                end_idx = min(start_idx + 50, len(df))
                
                break_index = self._find_break_point(
                    df,
                    start_idx,
                    end_idx,
                    prev_low['price'],
                    'below'
                )
                
                if break_index is not None:
                    choch_events.append({
                        "type": StructureBreakType.CHOCH_BEARISH.value,
                        "break_index": int(break_index),
                        "break_price": float(df.iloc[break_index]['close']),
                        "previous_level": float(prev_low['price']),
                        "broken_at": df.iloc[break_index].get('time', break_index),
                        "confidence": "high",
                        "description": f"Bearish CHoCH - Reversal signal at {prev_low['price']:.2f}"
                    })
        
        return choch_events
    
    def _find_break_point(
        self,
        df: pd.DataFrame,
        start_idx: int,
        end_idx: int,
        level: float,
        direction: str
    ) -> Optional[int]:
        """Find the exact candle where price breaks a level"""
        try:
            for i in range(start_idx + 1, min(end_idx, len(df))):
                if direction == 'above':
                    if df.iloc[i]['close'] > level:
                        return i
                elif direction == 'below':
                    if df.iloc[i]['close'] < level:
                        return i
            return None
        except Exception:
            return None
    
    def _combine_structure_breaks(
        self,
        bos_events: List[Dict[str, Any]],
        choch_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and sort all structure breaks chronologically"""
        all_breaks = bos_events + choch_events
        all_breaks.sort(key=lambda x: x['break_index'])
        return all_breaks
    
    def _get_current_structure(
        self,
        all_breaks: List[Dict[str, Any]],
        trend_analysis: Dict[str, Any],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Determine current market structure"""
        
        if not all_breaks:
            return {
                "status": "no_breaks",
                "message": "No structure breaks detected yet",
                "trend": trend_analysis.get("trend", "unknown")
            }
        
        # Get most recent break
        latest_break = all_breaks[-1]
        
        # Determine structure based on latest break and trend
        if latest_break['type'] in [StructureBreakType.BOS_BULLISH.value, StructureBreakType.CHOCH_BULLISH.value]:
            structure = "bullish"
            message = f"Latest: {latest_break['type']} - Expect continuation/reversal upward"
        else:
            structure = "bearish"
            message = f"Latest: {latest_break['type']} - Expect continuation/reversal downward"
        
        return {
            "status": "active",
            "structure": structure,
            "latest_break": latest_break,
            "message": message,
            "current_trend": trend_analysis.get("trend", "unknown"),
            "current_price": float(df.iloc[-1]['close']) if 'close' in df.columns else None
        }
    
    def _generate_trading_signals(
        self,
        all_breaks: List[Dict[str, Any]],
        current_structure: Dict[str, Any],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate trading signals based on structure breaks"""
        
        if not all_breaks or current_structure['status'] == 'no_breaks':
            return {
                "signal": "neutral",
                "confidence": "low",
                "message": "Wait for structure break to form"
            }
        
        latest_break = all_breaks[-1]
        current_price = float(df.iloc[-1]['close']) if 'close' in df.columns else 0
        
        # Generate signal based on latest break type
        if latest_break['type'] == StructureBreakType.BOS_BULLISH.value:
            return {
                "signal": "buy",
                "confidence": latest_break['confidence'],
                "message": "Bullish BOS - Consider long positions",
                "entry_suggestion": "Wait for pullback to broken level",
                "stop_loss": f"Below {latest_break['previous_level']:.2f}"
            }
        
        elif latest_break['type'] == StructureBreakType.BOS_BEARISH.value:
            return {
                "signal": "sell",
                "confidence": latest_break['confidence'],
                "message": "Bearish BOS - Consider short positions",
                "entry_suggestion": "Wait for retest of broken level",
                "stop_loss": f"Above {latest_break['previous_level']:.2f}"
            }
        
        elif latest_break['type'] == StructureBreakType.CHOCH_BULLISH.value:
            return {
                "signal": "buy",
                "confidence": "high",
                "message": "Bullish CHoCH - Potential trend reversal to upside",
                "entry_suggestion": "Enter on confirmation candle close",
                "stop_loss": f"Below recent low"
            }
        
        elif latest_break['type'] == StructureBreakType.CHOCH_BEARISH.value:
            return {
                "signal": "sell",
                "confidence": "high",
                "message": "Bearish CHoCH - Potential trend reversal to downside",
                "entry_suggestion": "Enter on confirmation candle close",
                "stop_loss": f"Above recent high"
            }
        
        return {
            "signal": "neutral",
            "confidence": "low",
            "message": "No clear signal"
        }
    
    def _calculate_statistics(
        self,
        bos_events: List[Dict[str, Any]],
        choch_events: List[Dict[str, Any]],
        all_breaks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics about structure breaks"""
        
        bos_bullish = sum(1 for e in bos_events if e['type'] == StructureBreakType.BOS_BULLISH.value)
        bos_bearish = sum(1 for e in bos_events if e['type'] == StructureBreakType.BOS_BEARISH.value)
        choch_bullish = sum(1 for e in choch_events if e['type'] == StructureBreakType.CHOCH_BULLISH.value)
        choch_bearish = sum(1 for e in choch_events if e['type'] == StructureBreakType.CHOCH_BEARISH.value)
        
        return {
            "total_breaks": len(all_breaks),
            "bos_count": len(bos_events),
            "choch_count": len(choch_events),
            "bos_bullish": bos_bullish,
            "bos_bearish": bos_bearish,
            "choch_bullish": choch_bullish,
            "choch_bearish": choch_bearish,
            "bullish_breaks": bos_bullish + choch_bullish,
            "bearish_breaks": bos_bearish + choch_bearish
        }

