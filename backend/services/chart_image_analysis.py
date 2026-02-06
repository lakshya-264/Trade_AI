"""
Chart Image Analysis Service
Analyzes uploaded chart screenshots to detect patterns, trends, and key levels
"""

import logging
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from io import BytesIO
try:
    from PIL import Image
    import numpy as np
    HAS_IMAGE_LIBS = True
except ImportError:
    HAS_IMAGE_LIBS = False
    logging.warning("PIL/Pillow not installed. Image analysis will be limited.")

logger = logging.getLogger(__name__)

class ChartImageAnalysisService:
    """Analyze chart images to extract trading insights"""
    
    def __init__(self):
        self.supported_formats = ['png', 'jpg', 'jpeg', 'gif', 'webp']
    
    async def analyze_chart_images(
        self,
        images: List[Dict[str, Any]],
        symbol: str,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple chart images and extract insights
        
        Args:
            images: List of image data (base64 or file paths)
            symbol: Stock symbol
            current_price: Current stock price for reference
            
        Returns:
            Analysis results with detected patterns, levels, and insights
        """
        try:
            if not HAS_IMAGE_LIBS:
                return {
                    "success": False,
                    "error": "Image processing libraries not available. Install Pillow: pip install Pillow"
                }
            
            logger.info(f"📸 Analyzing {len(images)} chart images for {symbol}...")
            
            analysis_results = []
            all_patterns = []
            all_levels = []
            all_trends = []
            
            for idx, image_data in enumerate(images):
                try:
                    # Process each image
                    image_analysis = await self._analyze_single_image(
                        image_data, 
                        symbol, 
                        idx + 1,
                        current_price
                    )
                    
                    if image_analysis.get("success"):
                        analysis_results.append(image_analysis)
                        
                        # Collect patterns, levels, and trends
                        if image_analysis.get("patterns"):
                            all_patterns.extend(image_analysis["patterns"])
                        if image_analysis.get("key_levels"):
                            all_levels.extend(image_analysis["key_levels"])
                        if image_analysis.get("trend"):
                            all_trends.append(image_analysis["trend"])
                
                except Exception as e:
                    logger.error(f"Error analyzing image {idx + 1}: {e}")
                    analysis_results.append({
                        "image_index": idx + 1,
                        "success": False,
                        "error": str(e)
                    })
            
            # Generate summary analysis
            summary = self._generate_summary_analysis(
                analysis_results,
                all_patterns,
                all_levels,
                all_trends,
                symbol,
                current_price
            )
            
            # Consolidate levels with price information
            consolidated_levels = self._consolidate_levels(all_levels, current_price)
            
            # Extract support and resistance prices
            support_levels = [l for l in consolidated_levels if l.get("is_support") or l.get("price_type") == "support"]
            resistance_levels = [l for l in consolidated_levels if l.get("is_resistance") or l.get("price_type") == "resistance"]
            
            # Find nearest support and resistance
            nearest_support = None
            nearest_resistance = None
            
            if support_levels and current_price:
                # Filter to only levels below current price
                valid_supports = [l for l in support_levels if l.get("estimated_price") and l.get("estimated_price") < current_price]
                if valid_supports:
                    # Find highest support (closest to current price from below)
                    nearest_support = max(valid_supports, key=lambda x: x.get("estimated_price", 0))
                    # Ensure all required fields are present
                    if nearest_support and not nearest_support.get("distance_percent") and current_price:
                        estimated_price = nearest_support.get("estimated_price")
                        if estimated_price:
                            nearest_support["distance_percent"] = round(((current_price - estimated_price) / current_price * 100), 2)
                    if nearest_support and not nearest_support.get("frequency"):
                        nearest_support["frequency"] = 1
            
            if resistance_levels and current_price:
                # Filter to only levels above current price
                valid_resistances = [l for l in resistance_levels if l.get("estimated_price") and l.get("estimated_price") > current_price]
                if valid_resistances:
                    # Find lowest resistance (closest to current price from above)
                    nearest_resistance = min(valid_resistances, key=lambda x: x.get("estimated_price", float('inf')))
                    # Ensure all required fields are present
                    if nearest_resistance and not nearest_resistance.get("distance_percent") and current_price:
                        estimated_price = nearest_resistance.get("estimated_price")
                        if estimated_price:
                            nearest_resistance["distance_percent"] = round(((estimated_price - current_price) / current_price * 100), 2)
                    if nearest_resistance and not nearest_resistance.get("frequency"):
                        nearest_resistance["frequency"] = 1
            
            return {
                "success": True,
                "symbol": symbol,
                "images_analyzed": len(images),
                "successful_analyses": len([r for r in analysis_results if r.get("success")]),
                "individual_analyses": analysis_results,
                "summary": summary,
                "detected_patterns": self._consolidate_patterns(all_patterns),
                "key_levels": consolidated_levels,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "overall_trend": self._determine_overall_trend(all_trends),
                "current_price": current_price,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chart image analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_single_image(
        self,
        image_data: Dict[str, Any],
        symbol: str,
        image_index: int,
        current_price: Optional[float]
    ) -> Dict[str, Any]:
        """Analyze a single chart image"""
        try:
            # Decode image if base64
            image = None
            if image_data.get("base64"):
                image_bytes = base64.b64decode(image_data["base64"])
                image = Image.open(BytesIO(image_bytes))
            elif image_data.get("file_path"):
                image = Image.open(image_data["file_path"])
            elif image_data.get("bytes"):
                image = Image.open(BytesIO(image_data["bytes"]))
            else:
                return {
                    "image_index": image_index,
                    "success": False,
                    "error": "No valid image data provided"
                }
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get image dimensions
            width, height = image.size
            
            # Convert to numpy array for analysis
            img_array = np.array(image)
            
            # Basic image analysis
            analysis = {
                "image_index": image_index,
                "success": True,
                "image_size": {"width": width, "height": height},
                "image_format": image.format or "unknown",
                "patterns": [],
                "key_levels": [],
                "trend": "unknown",
                "observations": []
            }
            
            # Detect patterns (simplified - can be enhanced with ML)
            patterns = self._detect_patterns_in_image(img_array, width, height)
            analysis["patterns"] = patterns
            
            # Detect key price levels (horizontal lines, support/resistance)
            levels = self._detect_price_levels(img_array, width, height, current_price)
            analysis["key_levels"] = levels
            
            # Determine trend
            trend = self._detect_trend(img_array, width, height)
            analysis["trend"] = trend
            
            # Generate observations
            observations = self._generate_observations(patterns, levels, trend, current_price)
            analysis["observations"] = observations
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing single image: {e}")
            return {
                "image_index": image_index,
                "success": False,
                "error": str(e)
            }
    
    def _detect_patterns_in_image(
        self,
        img_array: np.ndarray,
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """Detect chart patterns in image (simplified detection)"""
        patterns = []
        
        try:
            # Convert to grayscale for analysis
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2).astype(np.uint8)
            else:
                gray = img_array
            
            # Detect potential patterns based on image characteristics
            # This is a simplified approach - real implementation would use ML/computer vision
            
            # Check for potential head and shoulders (three peaks)
            # Check for potential double top/bottom (two similar peaks/troughs)
            # Check for potential triangles (converging lines)
            # Check for potential flags/pennants (rectangular patterns)
            
            # For now, return basic pattern detection
            # In production, this would use trained models or advanced CV techniques
            
            # Sample pattern detection logic
            mid_y = height // 2
            left_region = gray[:, :width//3]
            middle_region = gray[:, width//3:2*width//3]
            right_region = gray[:, 2*width//3:]
            
            # Detect potential patterns based on region analysis
            left_intensity = np.mean(left_region)
            middle_intensity = np.mean(middle_region)
            right_intensity = np.mean(right_region)
            
            # Simple pattern detection based on intensity variations
            if abs(middle_intensity - left_intensity) > 20 and abs(middle_intensity - right_intensity) > 20:
                patterns.append({
                    "pattern_name": "Potential Reversal Pattern",
                    "confidence": 0.6,
                    "description": "Detected significant price movement pattern",
                    "location": "middle region"
                })
            
            # Check for horizontal patterns (support/resistance)
            horizontal_lines = self._detect_horizontal_lines(gray, width, height)
            if len(horizontal_lines) > 0:
                patterns.append({
                    "pattern_name": "Horizontal Support/Resistance",
                    "confidence": 0.7,
                    "description": f"Detected {len(horizontal_lines)} horizontal price levels",
                    "levels": horizontal_lines
                })
            
            # Check for trend patterns
            trend_direction = self._detect_trend_direction(gray, width, height)
            if trend_direction != "neutral":
                patterns.append({
                    "pattern_name": f"{trend_direction.capitalize()} Trend",
                    "confidence": 0.65,
                    "description": f"Detected {trend_direction} price trend",
                    "direction": trend_direction
                })
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def _detect_horizontal_lines(
        self,
        gray: np.ndarray,
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """Detect horizontal lines (potential support/resistance levels)"""
        lines = []
        
        try:
            # Simple horizontal line detection
            # Look for rows with consistent intensity (potential price levels)
            threshold = 10  # Intensity variation threshold
            
            for y in range(0, height, height // 20):  # Sample every 5%
                row = gray[y, :]
                if np.std(row) < threshold:  # Low variation = potential level
                    avg_intensity = np.mean(row)
                    lines.append({
                        "y_position": y,
                        "percentage": (y / height) * 100,
                        "intensity": float(avg_intensity)
                    })
            
        except Exception as e:
            logger.error(f"Error detecting horizontal lines: {e}")
        
        return lines[:5]  # Return top 5 levels
    
    def _detect_trend_direction(
        self,
        gray: np.ndarray,
        width: int,
        height: int
    ) -> str:
        """Detect overall trend direction"""
        try:
            # Analyze left vs right side intensity
            left_half = gray[:, :width//2]
            right_half = gray[:, width//2:]
            
            left_avg = np.mean(left_half)
            right_avg = np.mean(right_half)
            
            diff = right_avg - left_avg
            
            if diff > 15:
                return "uptrend"
            elif diff < -15:
                return "downtrend"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error detecting trend: {e}")
            return "unknown"
    
    def _detect_price_levels(
        self,
        img_array: np.ndarray,
        width: int,
        height: int,
        current_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Detect key price levels from image and estimate actual prices"""
        levels = []
        
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2).astype(np.uint8)
            else:
                gray = img_array
            
            # Detect horizontal levels
            horizontal_lines = self._detect_horizontal_lines(gray, width, height)
            
            # Estimate price range from image (if current_price provided)
            # Chart typically shows price range from bottom (low) to top (high)
            # We'll estimate based on percentage position
            for line in horizontal_lines:
                percentage = line["percentage"]
                
                # Estimate price based on position (0% = bottom/low, 100% = top/high)
                # This is an approximation - actual prices would need OCR or user input
                estimated_price = None
                price_type = "unknown"
                
                if current_price:
                    # Estimate price range (±20% from current price as default range)
                    # Top of chart (0%) = current_price * 1.20 (20% above)
                    # Bottom of chart (100%) = current_price * 0.80 (20% below)
                    price_range_high = current_price * 1.20
                    price_range_low = current_price * 0.80
                    
                    # Convert percentage to price (inverted: 0% = high, 100% = low)
                    estimated_price = price_range_high - ((percentage / 100) * (price_range_high - price_range_low))
                    
                    # Classify as support or resistance
                    if estimated_price < current_price:
                        price_type = "support"
                    elif estimated_price > current_price:
                        price_type = "resistance"
                    else:
                        price_type = "current"
                
                level_data = {
                    "type": "horizontal",
                    "position": line["y_position"],
                    "percentage": percentage,
                    "description": f"Potential {price_type} level at {percentage:.1f}% of chart height"
                }
                
                if estimated_price:
                    level_data["estimated_price"] = round(estimated_price, 2)
                    level_data["price_type"] = price_type
                    level_data["distance_from_current"] = round(abs(estimated_price - current_price), 2) if current_price else None
                    level_data["distance_percent"] = round((abs(estimated_price - current_price) / current_price * 100), 2) if current_price else None
                
                levels.append(level_data)
            
        except Exception as e:
            logger.error(f"Error detecting price levels: {e}")
        
        return levels
    
    def _detect_trend(
        self,
        img_array: np.ndarray,
        width: int,
        height: int
    ) -> str:
        """Detect overall trend from image"""
        try:
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2).astype(np.uint8)
            else:
                gray = img_array
            
            return self._detect_trend_direction(gray, width, height)
            
        except Exception as e:
            logger.error(f"Error detecting trend: {e}")
            return "unknown"
    
    def _generate_observations(
        self,
        patterns: List[Dict],
        levels: List[Dict],
        trend: str,
        current_price: Optional[float]
    ) -> List[str]:
        """Generate human-readable observations"""
        observations = []
        
        if patterns:
            pattern_names = [p.get("pattern_name", "Pattern") for p in patterns]
            observations.append(f"Detected patterns: {', '.join(pattern_names)}")
        
        if levels:
            observations.append(f"Identified {len(levels)} key price level(s)")
        
        if trend != "unknown":
            observations.append(f"Overall trend appears to be {trend}")
        
        if current_price:
            observations.append(f"Analysis relative to current price: ₹{current_price:.2f}")
        
        return observations
    
    def _consolidate_patterns(self, all_patterns: List[Dict]) -> List[Dict]:
        """Consolidate patterns from all images"""
        pattern_counts = {}
        
        for pattern in all_patterns:
            name = pattern.get("pattern_name", "Unknown")
            if name not in pattern_counts:
                pattern_counts[name] = {
                    "pattern_name": name,
                    "count": 0,
                    "total_confidence": 0,
                    "descriptions": []
                }
            
            pattern_counts[name]["count"] += 1
            pattern_counts[name]["total_confidence"] += pattern.get("confidence", 0)
            if pattern.get("description"):
                pattern_counts[name]["descriptions"].append(pattern["description"])
        
        # Calculate average confidence
        consolidated = []
        for name, data in pattern_counts.items():
            consolidated.append({
                "pattern_name": name,
                "frequency": data["count"],
                "average_confidence": data["total_confidence"] / data["count"] if data["count"] > 0 else 0,
                "description": data["descriptions"][0] if data["descriptions"] else ""
            })
        
        return sorted(consolidated, key=lambda x: x["frequency"], reverse=True)
    
    def _consolidate_levels(self, all_levels: List[Dict], current_price: Optional[float] = None) -> List[Dict]:
        """Consolidate price levels from all images with actual price estimates"""
        # Group similar levels by estimated price (if available) or percentage
        level_groups = {}
        
        for level in all_levels:
            estimated_price = level.get("estimated_price")
            percentage = level.get("percentage", 0)
            
            if estimated_price and current_price:
                # Group by price (within 2% of price)
                group_key = round(estimated_price / (current_price * 0.02)) * (current_price * 0.02)
            else:
                # Group by percentage (within 5%)
                group_key = int(percentage / 5) * 5
            
            if group_key not in level_groups:
                level_groups[group_key] = []
            
            level_groups[group_key].append(level)
        
        # Return most common levels with price information
        consolidated = []
        for group_key, levels in sorted(level_groups.items(), key=lambda x: len(x[1]), reverse=True):
            if levels:
                # Get average estimated price if available
                prices = [l.get("estimated_price") for l in levels if l.get("estimated_price")]
                avg_price = sum(prices) / len(prices) if prices else None
                
                # Determine most common price type
                price_types = [l.get("price_type", "unknown") for l in levels]
                most_common_type = max(set(price_types), key=price_types.count) if price_types else "unknown"
                
                consolidated_data = {
                    "frequency": len(levels),
                    "description": levels[0].get("description", "Key price level"),
                    "price_type": most_common_type
                }
                
                if avg_price:
                    consolidated_data["estimated_price"] = round(avg_price, 2)
                    if current_price:
                        consolidated_data["distance_from_current"] = round(abs(avg_price - current_price), 2)
                        consolidated_data["distance_percent"] = round((abs(avg_price - current_price) / current_price * 100), 2)
                        consolidated_data["is_support"] = avg_price < current_price
                        consolidated_data["is_resistance"] = avg_price > current_price
                else:
                    consolidated_data["percentage_range"] = f"{group_key}-{group_key+5}%"
                
                consolidated.append(consolidated_data)
        
        return consolidated[:10]  # Top 10 most common levels
    
    def _determine_overall_trend(self, all_trends: List[str]) -> str:
        """Determine overall trend from all images"""
        if not all_trends:
            return "unknown"
        
        trend_counts = {}
        for trend in all_trends:
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        # Return most common trend
        return max(trend_counts.items(), key=lambda x: x[1])[0]
    
    def _generate_summary_analysis(
        self,
        analysis_results: List[Dict],
        all_patterns: List[Dict],
        all_levels: List[Dict],
        all_trends: List[str],
        symbol: str,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate summary analysis from all images with detailed insights"""
        successful = [r for r in analysis_results if r.get("success")]
        
        summary_parts = []
        summary_parts.append(f"Analyzed {len(successful)} chart image(s) for {symbol}")
        
        if all_patterns:
            unique_patterns = len(set(p.get("pattern_name", "") for p in all_patterns))
            summary_parts.append(f"Detected {unique_patterns} unique pattern type(s) across images")
        
        # Count support and resistance levels
        support_count = len([l for l in all_levels if l.get("price_type") == "support" or (l.get("estimated_price") and current_price and l.get("estimated_price") < current_price)])
        resistance_count = len([l for l in all_levels if l.get("price_type") == "resistance" or (l.get("estimated_price") and current_price and l.get("estimated_price") > current_price)])
        
        if support_count > 0 or resistance_count > 0:
            summary_parts.append(f"Identified {support_count} support level(s) and {resistance_count} resistance level(s)")
        elif all_levels:
            summary_parts.append(f"Identified {len(all_levels)} key price level(s)")
        
        if all_trends:
            overall_trend = self._determine_overall_trend(all_trends)
            trend_count = all_trends.count(overall_trend)
            summary_parts.append(f"Overall trend: {overall_trend.upper()} (detected in {trend_count}/{len(all_trends)} images)")
        
        # Add price level details if available
        if current_price:
            support_prices = [l.get("estimated_price") for l in all_levels if l.get("estimated_price") and l.get("estimated_price") < current_price]
            resistance_prices = [l.get("estimated_price") for l in all_levels if l.get("estimated_price") and l.get("estimated_price") > current_price]
            
            if support_prices:
                nearest_support = max(support_prices)
                summary_parts.append(f"Nearest support from images: ₹{nearest_support:.2f}")
            
            if resistance_prices:
                nearest_resistance = min(resistance_prices)
                summary_parts.append(f"Nearest resistance from images: ₹{nearest_resistance:.2f}")
        
        return {
            "summary_text": ". ".join(summary_parts) if summary_parts else "Chart image analysis complete.",
            "images_analyzed": len(successful),
            "patterns_detected": len(all_patterns),
            "levels_identified": len(all_levels),
            "support_levels_count": support_count,
            "resistance_levels_count": resistance_count,
            "overall_trend": self._determine_overall_trend(all_trends)
        }

# Create singleton instance
chart_image_analysis_service = ChartImageAnalysisService()


