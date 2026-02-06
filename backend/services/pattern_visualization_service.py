"""
Pattern Visualization Service
Draws pattern lines and annotations on charts
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class PatternVisualizationService:
    """Service to visualize detected patterns on charts"""
    
    def __init__(self):
        pass
    
    def generate_pattern_annotations(
        self,
        pattern_data: Dict[str, Any],
        chart_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate visualization data for patterns to be drawn on charts
        
        Returns:
            Dictionary with lines, annotations, and target levels
        """
        try:
            pattern_type = pattern_data.get("pattern_type", "")
            annotations = {
                "pattern_type": pattern_type,
                "lines": [],
                "annotations": [],
                "target_levels": [],
                "support_resistance": []
            }
            
            if "reverse_head_shoulder" in pattern_type.lower():
                annotations = self._visualize_reverse_head_shoulder(pattern_data, chart_data)
            elif "head_shoulder" in pattern_type.lower():
                annotations = self._visualize_head_shoulder(pattern_data, chart_data)
            elif "cup_handle" in pattern_type.lower():
                annotations = self._visualize_cup_handle(pattern_data, chart_data)
            elif "double_top" in pattern_type.lower():
                annotations = self._visualize_double_top(pattern_data, chart_data)
            elif "double_bottom" in pattern_type.lower():
                annotations = self._visualize_double_bottom(pattern_data, chart_data)
            elif "triangle" in pattern_type.lower():
                annotations = self._visualize_triangle(pattern_data, chart_data)
            elif "wedge" in pattern_type.lower():
                annotations = self._visualize_wedge(pattern_data, chart_data)
            elif "flag" in pattern_type.lower() or "pennant" in pattern_type.lower():
                annotations = self._visualize_flag_pennant(pattern_data, chart_data)
            
            return annotations
            
        except Exception as e:
            logger.error(f"Error generating pattern annotations: {e}")
            return {}
    
    def _visualize_reverse_head_shoulder(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Reverse Head & Shoulder pattern"""
        try:
            left_shoulder = pattern_data.get("left_shoulder", {})
            head = pattern_data.get("head", {})
            right_shoulder = pattern_data.get("right_shoulder", {})
            neckline = pattern_data.get("neckline", 0)
            target_price = pattern_data.get("target_price", 0)
            
            lines = []
            annotations = []
            
            # Draw neckline (horizontal line)
            if neckline:
                lines.append({
                    "type": "horizontal",
                    "price": neckline,
                    "color": "#3B82F6",  # Blue
                    "style": "solid",
                    "width": 2,
                    "label": f"Neckline: ₹{neckline:.2f}",
                    "start_index": left_shoulder.get("index", 0),
                    "end_index": len(chart_data) - 1
                })
            
            # Draw left shoulder to head line
            if left_shoulder.get("index") and head.get("index"):
                lines.append({
                    "type": "trendline",
                    "points": [
                        {"index": left_shoulder["index"], "price": left_shoulder["price"]},
                        {"index": head["index"], "price": head["price"]}
                    ],
                    "color": "#10B981",  # Green
                    "style": "solid",
                    "width": 2
                })
            
            # Draw head to right shoulder line
            if head.get("index") and right_shoulder.get("index"):
                lines.append({
                    "type": "trendline",
                    "points": [
                        {"index": head["index"], "price": head["price"]},
                        {"index": right_shoulder["index"], "price": right_shoulder["price"]}
                    ],
                    "color": "#10B981",  # Green
                    "style": "solid",
                    "width": 2
                })
            
            # Draw target level
            if target_price:
                lines.append({
                    "type": "horizontal",
                    "price": target_price,
                    "color": "#F59E0B",  # Orange
                    "style": "dashed",
                    "width": 2,
                    "label": f"Target: ₹{target_price:.2f}",
                    "start_index": right_shoulder.get("index", 0),
                    "end_index": len(chart_data) - 1
                })
            
            # Add annotations
            if left_shoulder.get("price"):
                annotations.append({
                    "type": "label",
                    "index": left_shoulder.get("index", 0),
                    "price": left_shoulder["price"],
                    "text": "Left Shoulder",
                    "color": "#10B981"
                })
            
            if head.get("price"):
                annotations.append({
                    "type": "label",
                    "index": head.get("index", 0),
                    "price": head["price"],
                    "text": "Head",
                    "color": "#EF4444"
                })
            
            if right_shoulder.get("price"):
                annotations.append({
                    "type": "label",
                    "index": right_shoulder.get("index", 0),
                    "price": right_shoulder["price"],
                    "text": "Right Shoulder",
                    "color": "#10B981"
                })
            
            return {
                "pattern_type": "reverse_head_shoulder",
                "lines": lines,
                "annotations": annotations,
                "target_levels": [target_price] if target_price else [],
                "support_resistance": [neckline] if neckline else []
            }
            
        except Exception as e:
            logger.error(f"Error visualizing reverse head & shoulder: {e}")
            return {}
    
    def _visualize_head_shoulder(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Head & Shoulder pattern"""
        # Similar to reverse but inverted
        return self._visualize_reverse_head_shoulder(pattern_data, chart_data)
    
    def _visualize_cup_handle(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Cup & Handle pattern"""
        try:
            cup_bottom = pattern_data.get("cup_bottom", 0)
            cup_rim = pattern_data.get("cup_rim", 0)
            target_price = pattern_data.get("target_price", 0)
            
            lines = []
            
            # Draw cup rim (resistance)
            if cup_rim:
                lines.append({
                    "type": "horizontal",
                    "price": cup_rim,
                    "color": "#3B82F6",
                    "style": "solid",
                    "width": 2,
                    "label": f"Cup Rim: ₹{cup_rim:.2f}"
                })
            
            # Draw target
            if target_price:
                lines.append({
                    "type": "horizontal",
                    "price": target_price,
                    "color": "#F59E0B",
                    "style": "dashed",
                    "width": 2,
                    "label": f"Target: ₹{target_price:.2f}"
                })
            
            return {
                "pattern_type": "cup_handle",
                "lines": lines,
                "annotations": [],
                "target_levels": [target_price] if target_price else [],
                "support_resistance": [cup_rim] if cup_rim else []
            }
            
        except Exception as e:
            logger.error(f"Error visualizing cup & handle: {e}")
            return {}
    
    def _visualize_double_top(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Double Top pattern"""
        try:
            first_peak = pattern_data.get("first_peak", 0)
            second_peak = pattern_data.get("second_peak", 0)
            neckline = pattern_data.get("neckline", 0)
            target_price = pattern_data.get("target_price", 0)
            
            lines = []
            
            # Draw resistance line connecting peaks
            if first_peak and second_peak:
                lines.append({
                    "type": "horizontal",
                    "price": (first_peak + second_peak) / 2,
                    "color": "#EF4444",
                    "style": "solid",
                    "width": 2,
                    "label": "Double Top Resistance"
                })
            
            # Draw neckline
            if neckline:
                lines.append({
                    "type": "horizontal",
                    "price": neckline,
                    "color": "#3B82F6",
                    "style": "solid",
                    "width": 2,
                    "label": f"Neckline: ₹{neckline:.2f}"
                })
            
            # Draw target
            if target_price:
                lines.append({
                    "type": "horizontal",
                    "price": target_price,
                    "color": "#F59E0B",
                    "style": "dashed",
                    "width": 2,
                    "label": f"Target: ₹{target_price:.2f}"
                })
            
            return {
                "pattern_type": "double_top",
                "lines": lines,
                "annotations": [],
                "target_levels": [target_price] if target_price else [],
                "support_resistance": [neckline] if neckline else []
            }
            
        except Exception as e:
            logger.error(f"Error visualizing double top: {e}")
            return {}
    
    def _visualize_double_bottom(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Double Bottom pattern"""
        # Similar to double top but inverted
        return self._visualize_double_top(pattern_data, chart_data)
    
    def _visualize_triangle(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Triangle patterns"""
        try:
            # Triangle patterns have converging trendlines
            lines = []
            
            # Get triangle boundaries from pattern data
            upper_line = pattern_data.get("upper_line", {})
            lower_line = pattern_data.get("lower_line", {})
            breakout_level = pattern_data.get("breakout_level", 0)
            
            if upper_line and lower_line:
                lines.append({
                    "type": "trendline",
                    "points": upper_line.get("points", []),
                    "color": "#EF4444",
                    "style": "solid",
                    "width": 2,
                    "label": "Upper Trendline"
                })
                
                lines.append({
                    "type": "trendline",
                    "points": lower_line.get("points", []),
                    "color": "#10B981",
                    "style": "solid",
                    "width": 2,
                    "label": "Lower Trendline"
                })
            
            if breakout_level:
                lines.append({
                    "type": "horizontal",
                    "price": breakout_level,
                    "color": "#F59E0B",
                    "style": "dashed",
                    "width": 2,
                    "label": f"Breakout: ₹{breakout_level:.2f}"
                })
            
            return {
                "pattern_type": pattern_data.get("pattern_type", "triangle"),
                "lines": lines,
                "annotations": [],
                "target_levels": [breakout_level] if breakout_level else [],
                "support_resistance": []
            }
            
        except Exception as e:
            logger.error(f"Error visualizing triangle: {e}")
            return {}
    
    def _visualize_wedge(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Wedge patterns"""
        # Similar to triangle but with different interpretation
        return self._visualize_triangle(pattern_data, chart_data)
    
    def _visualize_flag_pennant(
        self,
        pattern_data: Dict,
        chart_data: List[Dict]
    ) -> Dict:
        """Generate visualization for Flag & Pennant patterns"""
        try:
            lines = []
            
            # Flag has parallel lines
            upper_boundary = pattern_data.get("upper_boundary", 0)
            lower_boundary = pattern_data.get("lower_boundary", 0)
            target_price = pattern_data.get("target_price", 0)
            
            if upper_boundary:
                lines.append({
                    "type": "horizontal",
                    "price": upper_boundary,
                    "color": "#EF4444",
                    "style": "solid",
                    "width": 2,
                    "label": "Upper Boundary"
                })
            
            if lower_boundary:
                lines.append({
                    "type": "horizontal",
                    "price": lower_boundary,
                    "color": "#10B981",
                    "style": "solid",
                    "width": 2,
                    "label": "Lower Boundary"
                })
            
            if target_price:
                lines.append({
                    "type": "horizontal",
                    "price": target_price,
                    "color": "#F59E0B",
                    "style": "dashed",
                    "width": 2,
                    "label": f"Target: ₹{target_price:.2f}"
                })
            
            return {
                "pattern_type": pattern_data.get("pattern_type", "flag"),
                "lines": lines,
                "annotations": [],
                "target_levels": [target_price] if target_price else [],
                "support_resistance": []
            }
            
        except Exception as e:
            logger.error(f"Error visualizing flag/pennant: {e}")
            return {}

# Create singleton instance
pattern_visualization_service = PatternVisualizationService()

