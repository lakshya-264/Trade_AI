"""
Drawing Tools Service
Comprehensive drawing and annotation tools for TradingView-style charting
Supports trend lines, Fibonacci tools, shapes, text, and custom drawings
"""

from typing import Dict, List, Optional, Any
import json
import logging
import os
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import asyncio

logger = logging.getLogger(__name__)

class DrawingToolsService:
    def __init__(self):
        # Templates storage
        self.templates: Dict[str, Dict] = {}  # template_id -> template_data
        self.templates_dir = "data/chart_templates"
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Layouts storage
        self.layouts: Dict[str, Dict] = {}  # layout_id -> layout_data
        self.layouts_dir = "data/chart_layouts"
        os.makedirs(self.layouts_dir, exist_ok=True)
        
        self.supported_drawing_types = {
            # Trend Tools
            "trendline": {
                "name": "Trend Line",
                "category": "trend",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw trend lines between two points"
            },
            "horizontal_line": {
                "name": "Horizontal Line",
                "category": "trend",
                "min_points": 1,
                "max_points": 1,
                "description": "Draw horizontal support/resistance lines"
            },
            "vertical_line": {
                "name": "Vertical Line",
                "category": "trend",
                "min_points": 1,
                "max_points": 1,
                "description": "Draw vertical time markers"
            },
            "ray": {
                "name": "Ray",
                "category": "trend",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw infinite ray from a point"
            },
            "extended_line": {
                "name": "Extended Line",
                "category": "trend",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw extended line beyond points"
            },
            "parallel_channel": {
                "name": "Parallel Channel",
                "category": "trend",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw parallel price channels"
            },
            "disjoint_channel": {
                "name": "Disjoint Channel",
                "category": "trend",
                "min_points": 3,
                "max_points": 3,
                "description": "Draw disjointed price channels"
            },
            "regression_trend": {
                "name": "Regression Trend",
                "category": "trend",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw regression trend line"
            },
            
            # Fibonacci Tools
            "fibonacci_retracement": {
                "name": "Fibonacci Retracement",
                "category": "fibonacci",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw Fibonacci retracement levels"
            },
            "fibonacci_extension": {
                "name": "Fibonacci Extension",
                "category": "fibonacci",
                "min_points": 3,
                "max_points": 3,
                "description": "Draw Fibonacci extension levels"
            },
            "fibonacci_time_zones": {
                "name": "Fibonacci Time Zones",
                "category": "fibonacci",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw Fibonacci time zones"
            },
            "fibonacci_spiral": {
                "name": "Fibonacci Spiral",
                "category": "fibonacci",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw Fibonacci spiral"
            },
            "fibonacci_speed_resistance_fan": {
                "name": "Fibonacci Speed Resistance Fan",
                "category": "fibonacci",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw Fibonacci speed resistance fan"
            },
            
            # Pitchfork & Channel Tools
            "pitchfork": {
                "name": "Pitchfork",
                "category": "pitchfork",
                "min_points": 3,
                "max_points": 3,
                "description": "Draw Andrews Pitchfork"
            },
            "andrews_pitchfork": {
                "name": "Andrew's Pitchfork",
                "category": "pitchfork",
                "min_points": 3,
                "max_points": 3,
                "description": "Draw Andrews Pitchfork variant"
            },
            "trend_angle": {
                "name": "Trend Angle",
                "category": "pitchfork",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw trend angle lines"
            },
            "gann_fan": {
                "name": "Gann Fan",
                "category": "pitchfork",
                "min_points": 1,
                "max_points": 1,
                "description": "Draw Gann Fan lines"
            },
            "gann_box": {
                "name": "Gann Box",
                "category": "pitchfork",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw Gann Box"
            },
            "gann_square": {
                "name": "Gann Square",
                "category": "pitchfork",
                "min_points": 1,
                "max_points": 1,
                "description": "Draw Gann Square"
            },
            
            # Geometry & Shape Tools
            "rectangle": {
                "name": "Rectangle",
                "category": "geometry",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw rectangle shapes"
            },
            "ellipse": {
                "name": "Ellipse",
                "category": "geometry",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw ellipse shapes"
            },
            "triangle": {
                "name": "Triangle",
                "category": "geometry",
                "min_points": 3,
                "max_points": 3,
                "description": "Draw triangle shapes"
            },
            "curve": {
                "name": "Curve",
                "category": "geometry",
                "min_points": 3,
                "max_points": 10,
                "description": "Draw curved lines"
            },
            "path": {
                "name": "Path",
                "category": "geometry",
                "min_points": 2,
                "max_points": 20,
                "description": "Draw multi-point paths"
            },
            "arrow": {
                "name": "Arrow",
                "category": "geometry",
                "min_points": 2,
                "max_points": 2,
                "description": "Draw arrow markers"
            },
            "measure": {
                "name": "Measure Tool",
                "category": "geometry",
                "min_points": 2,
                "max_points": 2,
                "description": "Measure price and time distance"
            },
            "polyline": {
                "name": "Polyline",
                "category": "geometry",
                "min_points": 2,
                "max_points": 20,
                "description": "Draw connected line segments"
            },
            "freehand": {
                "name": "Freehand",
                "category": "geometry",
                "min_points": 5,
                "max_points": 100,
                "description": "Draw freehand sketches"
            },
            
            # Text & Label Tools
            "text": {
                "name": "Text",
                "category": "text",
                "min_points": 1,
                "max_points": 1,
                "description": "Add text annotations"
            },
            "note": {
                "name": "Note",
                "category": "text",
                "min_points": 1,
                "max_points": 1,
                "description": "Add note annotations"
            },
            "callout": {
                "name": "Callout",
                "category": "text",
                "min_points": 1,
                "max_points": 1,
                "description": "Add callout annotations"
            },
            "price_label": {
                "name": "Price Label",
                "category": "text",
                "min_points": 1,
                "max_points": 1,
                "description": "Add price level labels"
            },
            "date_price_range": {
                "name": "Date/Price Range Label",
                "category": "text",
                "min_points": 2,
                "max_points": 2,
                "description": "Add date and price range labels"
            },
            "anchored_note": {
                "name": "Anchored Note",
                "category": "text",
                "min_points": 1,
                "max_points": 1,
                "description": "Add anchored note annotations"
            },
            "marker": {
                "name": "Marker",
                "category": "text",
                "min_points": 1,
                "max_points": 1,
                "description": "Add marker annotations"
            },
            
            # Risk Management Tools
            "long_position": {
                "name": "Long Position Tool",
                "category": "risk",
                "min_points": 2,
                "max_points": 2,
                "description": "Mark long position entry and exit"
            },
            "short_position": {
                "name": "Short Position Tool",
                "category": "risk",
                "min_points": 2,
                "max_points": 2,
                "description": "Mark short position entry and exit"
            },
            "risk_reward_ratio": {
                "name": "Risk/Reward Ratio Display",
                "category": "risk",
                "min_points": 2,
                "max_points": 2,
                "description": "Display risk/reward ratio"
            }
        }
        
        # Drawing storage (in production, this would be database)
        self.drawings_storage = {}
        self.drawing_groups = {}
    
    def get_supported_drawing_types(self) -> Dict[str, Any]:
        """Get list of supported drawing types"""
        return self.supported_drawing_types
    
    def get_drawing_types_by_category(self, category: str) -> Dict[str, Any]:
        """Get drawing types filtered by category"""
        return {
            name: info for name, info in self.supported_drawing_types.items()
            if info["category"] == category
        }
    
    async def save_drawing(
        self, 
        user_id: int, 
        chart_id: str, 
        drawing_type: str,
        points: List[Dict[str, Any]], 
        style: Dict[str, Any],
        name: Optional[str] = None
    ) -> str:
        """Save drawing to storage"""
        try:
            # Validate drawing type
            if drawing_type not in self.supported_drawing_types:
                raise ValueError(f"Unsupported drawing type: {drawing_type}")
            
            # Validate points
            drawing_info = self.supported_drawing_types[drawing_type]
            if len(points) < drawing_info["min_points"]:
                raise ValueError(f"Not enough points for {drawing_type}. Minimum: {drawing_info['min_points']}")
            
            if len(points) > drawing_info["max_points"]:
                raise ValueError(f"Too many points for {drawing_type}. Maximum: {drawing_info['max_points']}")
            
            # Generate unique drawing ID
            drawing_id = f"drawing_{user_id}_{chart_id}_{uuid.uuid4().hex[:8]}"
            
            # Create drawing data
            drawing_data = {
                "id": drawing_id,
                "user_id": user_id,
                "chart_id": chart_id,
                "drawing_type": drawing_type,
                "name": name or f"{drawing_info['name']} {len(self.drawings_storage) + 1}",
                "points": points,
                "style": self._validate_and_set_default_style(style, drawing_type),
                "is_visible": True,
                "is_locked": False,
                "group_id": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "metadata": {
                    "version": "1.0",
                    "tool_version": "charting_system_v1"
                }
            }
            
            # Store drawing
            self.drawings_storage[drawing_id] = drawing_data
            
            # Add to user's drawings index
            user_key = f"user_{user_id}"
            if user_key not in self.drawings_storage:
                self.drawings_storage[user_key] = []
            
            self.drawings_storage[user_key].append(drawing_id)
            
            logger.info(f"Drawing {drawing_id} saved for user {user_id}")
            return drawing_id
            
        except Exception as e:
            logger.error(f"Error saving drawing: {e}")
            raise
    
    async def get_drawings(self, user_id: int, chart_id: str) -> List[Dict[str, Any]]:
        """Get all drawings for a chart"""
        try:
            user_key = f"user_{user_id}"
            user_drawings = self.drawings_storage.get(user_key, [])
            
            drawings = []
            for drawing_id in user_drawings:
                if drawing_id in self.drawings_storage:
                    drawing = self.drawings_storage[drawing_id]
                    if drawing["chart_id"] == chart_id:
                        drawings.append(drawing)
            
            # Sort by creation time
            drawings.sort(key=lambda x: x["created_at"])
            
            logger.info(f"Retrieved {len(drawings)} drawings for chart {chart_id}")
            return drawings
            
        except Exception as e:
            logger.error(f"Error getting drawings for chart {chart_id}: {e}")
            return []
    
    async def get_drawing(self, drawing_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific drawing by ID"""
        try:
            if drawing_id not in self.drawings_storage:
                return None
            
            drawing = self.drawings_storage[drawing_id]
            if drawing["user_id"] != user_id:
                return None
            
            return drawing
            
        except Exception as e:
            logger.error(f"Error getting drawing {drawing_id}: {e}")
            return None
    
    async def update_drawing(
        self, 
        drawing_id: str, 
        user_id: int, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update drawing"""
        try:
            if drawing_id not in self.drawings_storage:
                return False
            
            drawing = self.drawings_storage[drawing_id]
            if drawing["user_id"] != user_id:
                return False
            
            # Update allowed fields
            allowed_fields = ["name", "points", "style", "is_visible", "is_locked", "group_id"]
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "style":
                        drawing[field] = self._validate_and_set_default_style(value, drawing["drawing_type"])
                    else:
                        drawing[field] = value
            
            drawing["updated_at"] = datetime.now()
            
            logger.info(f"Drawing {drawing_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating drawing {drawing_id}: {e}")
            return False
    
    async def delete_drawing(self, drawing_id: str, user_id: int) -> bool:
        """Delete drawing"""
        try:
            if drawing_id not in self.drawings_storage:
                return False
            
            drawing = self.drawings_storage[drawing_id]
            if drawing["user_id"] != user_id:
                return False
            
            # Remove from storage
            del self.drawings_storage[drawing_id]
            
            # Remove from user index
            user_key = f"user_{user_id}"
            if user_key in self.drawings_storage:
                user_drawings = self.drawings_storage[user_key]
                if drawing_id in user_drawings:
                    user_drawings.remove(drawing_id)
            
            logger.info(f"Drawing {drawing_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting drawing {drawing_id}: {e}")
            return False
    
    async def duplicate_drawing(self, drawing_id: str, user_id: int, new_chart_id: Optional[str] = None) -> Optional[str]:
        """Duplicate drawing"""
        try:
            original_drawing = await self.get_drawing(drawing_id, user_id)
            if not original_drawing:
                return None
            
            # Create new drawing with modified data
            new_drawing_data = original_drawing.copy()
            new_drawing_data["id"] = f"drawing_{user_id}_{new_chart_id or original_drawing['chart_id']}_{uuid.uuid4().hex[:8]}"
            new_drawing_data["name"] = f"{original_drawing['name']} (Copy)"
            new_drawing_data["chart_id"] = new_chart_id or original_drawing["chart_id"]
            new_drawing_data["created_at"] = datetime.now()
            new_drawing_data["updated_at"] = datetime.now()
            
            # Save new drawing
            new_drawing_id = await self.save_drawing(
                user_id=user_id,
                chart_id=new_drawing_data["chart_id"],
                drawing_type=new_drawing_data["drawing_type"],
                points=new_drawing_data["points"],
                style=new_drawing_data["style"],
                name=new_drawing_data["name"]
            )
            
            return new_drawing_id
            
        except Exception as e:
            logger.error(f"Error duplicating drawing {drawing_id}: {e}")
            return None
    
    async def group_drawings(self, drawing_ids: List[str], user_id: int, group_name: str) -> bool:
        """Group multiple drawings together"""
        try:
            group_id = f"group_{user_id}_{uuid.uuid4().hex[:8]}"
            
            for drawing_id in drawing_ids:
                if drawing_id in self.drawings_storage:
                    drawing = self.drawings_storage[drawing_id]
                    if drawing["user_id"] == user_id:
                        drawing["group_id"] = group_id
            
            # Store group metadata
            self.drawing_groups[group_id] = {
                "id": group_id,
                "name": group_name,
                "drawing_ids": drawing_ids,
                "user_id": user_id,
                "created_at": datetime.now()
            }
            
            logger.info(f"Grouped {len(drawing_ids)} drawings into group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error grouping drawings: {e}")
            return False
    
    async def ungroup_drawings(self, group_id: str, user_id: int) -> bool:
        """Ungroup drawings"""
        try:
            if group_id not in self.drawing_groups:
                return False
            
            group = self.drawing_groups[group_id]
            if group["user_id"] != user_id:
                return False
            
            # Remove group_id from drawings
            for drawing_id in group["drawing_ids"]:
                if drawing_id in self.drawings_storage:
                    self.drawings_storage[drawing_id]["group_id"] = None
            
            # Remove group
            del self.drawing_groups[group_id]
            
            logger.info(f"Ungrouped drawings from group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ungrouping drawings: {e}")
            return False
    
    async def get_drawing_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all drawing groups for user"""
        try:
            user_groups = []
            for group_id, group_data in self.drawing_groups.items():
                if group_data["user_id"] == user_id:
                    user_groups.append(group_data)
            
            return user_groups
            
        except Exception as e:
            logger.error(f"Error getting drawing groups: {e}")
            return []
    
    async def export_drawings(self, user_id: int, chart_id: Optional[str] = None) -> Dict[str, Any]:
        """Export drawings to JSON format"""
        try:
            drawings = []
            if chart_id:
                drawings = await self.get_drawings(user_id, chart_id)
            else:
                # Get all drawings for user
                user_key = f"user_{user_id}"
                user_drawing_ids = self.drawings_storage.get(user_key, [])
                for drawing_id in user_drawing_ids:
                    if drawing_id in self.drawings_storage:
                        drawings.append(self.drawings_storage[drawing_id])
            
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "user_id": user_id,
                "chart_id": chart_id,
                "drawings": drawings,
                "groups": await self.get_drawing_groups(user_id)
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting drawings: {e}")
            return {}
    
    async def import_drawings(self, user_id: int, import_data: Dict[str, Any]) -> bool:
        """Import drawings from JSON format"""
        try:
            if "drawings" not in import_data:
                return False
            
            imported_count = 0
            for drawing_data in import_data["drawings"]:
                try:
                    # Create new drawing with current user_id
                    new_drawing_id = await self.save_drawing(
                        user_id=user_id,
                        chart_id=drawing_data["chart_id"],
                        drawing_type=drawing_data["drawing_type"],
                        points=drawing_data["points"],
                        style=drawing_data["style"],
                        name=drawing_data.get("name")
                    )
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import drawing: {e}")
                    continue
            
            logger.info(f"Imported {imported_count} drawings for user {user_id}")
            return imported_count > 0
            
        except Exception as e:
            logger.error(f"Error importing drawings: {e}")
            return False
    
    def _validate_and_set_default_style(self, style: Dict[str, Any], drawing_type: str) -> Dict[str, Any]:
        """Validate and set default style for drawing type"""
        default_styles = {
            "trendline": {
                "color": "#ff6b6b",
                "lineWidth": 2,
                "lineStyle": "solid",
                "opacity": 1.0
            },
            "horizontal_line": {
                "color": "#4ecdc4",
                "lineWidth": 1,
                "lineStyle": "dashed",
                "opacity": 0.8
            },
            "vertical_line": {
                "color": "#45b7d1",
                "lineWidth": 1,
                "lineStyle": "solid",
                "opacity": 0.8
            },
            "fibonacci_retracement": {
                "color": "#96ceb4",
                "lineWidth": 1,
                "lineStyle": "solid",
                "opacity": 0.7,
                "levels": [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
            },
            "rectangle": {
                "color": "#feca57",
                "lineWidth": 2,
                "lineStyle": "solid",
                "fillColor": "#feca57",
                "fillOpacity": 0.2,
                "opacity": 1.0
            },
            "text": {
                "color": "#000000",
                "fontSize": 12,
                "fontFamily": "Arial",
                "fontWeight": "normal",
                "backgroundColor": "#ffffff",
                "borderColor": "#cccccc",
                "borderWidth": 1
            }
        }
        
        # Get default style for drawing type
        default_style = default_styles.get(drawing_type, {
            "color": "#666666",
            "lineWidth": 1,
            "lineStyle": "solid",
            "opacity": 1.0
        })
        
        # Merge with provided style
        merged_style = default_style.copy()
        merged_style.update(style)
        
        return merged_style
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            # Test basic functionality
            test_drawing = {
                "id": "test",
                "user_id": 1,
                "chart_id": "test",
                "drawing_type": "trendline",
                "points": [{"time": "2024-01-01", "price": 100}, {"time": "2024-01-02", "price": 110}],
                "style": {"color": "#ff0000"},
                "created_at": datetime.now()
            }
            
            self._validate_and_set_default_style(test_drawing["style"], test_drawing["drawing_type"])
            return True
        except Exception:
            return False
    
    def clear_storage(self):
        """Clear all drawings storage (for testing)"""
        self.drawings_storage.clear()
        self.drawing_groups.clear()
        logger.info("Drawing storage cleared")
