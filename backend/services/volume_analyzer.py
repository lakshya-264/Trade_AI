"""
Volume Analysis Service
Analyze buy/sell volume patterns and order flow
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class VolumeAnalyzer:
    def __init__(self):
        self.volume_thresholds = {
            "high_volume": 2.0,  # 2x average volume
            "very_high_volume": 3.0,  # 3x average volume
            "low_volume": 0.5,  # 0.5x average volume
        }
        
    def analyze_volume_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns and trends"""
        try:
            if "volume" not in df.columns or len(df) < 20:
                return {"error": "Insufficient volume data"}
            
            # Calculate volume metrics
            volume_metrics = self._calculate_volume_metrics(df)
            
            # Analyze volume trends
            volume_trends = self._analyze_volume_trends(df)
            
            # Detect volume spikes
            volume_spikes = self._detect_volume_spikes(df)
            
            # Analyze price-volume relationship
            price_volume_analysis = self._analyze_price_volume_relationship(df)
            
            # Generate volume signals
            volume_signals = self._generate_volume_signals(df, volume_metrics)
            
            return {
                "volume_metrics": volume_metrics,
                "volume_trends": volume_trends,
                "volume_spikes": volume_spikes,
                "price_volume_analysis": price_volume_analysis,
                "volume_signals": volume_signals,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume patterns: {e}")
            return {"error": str(e)}
    
    def analyze_order_flow(self, order_data: List[Dict]) -> Dict:
        """Analyze order flow patterns"""
        try:
            if not order_data:
                return {"error": "No order data available"}
            
            # Convert to DataFrame
            df = pd.DataFrame(order_data)
            
            # Analyze buy vs sell orders
            buy_sell_analysis = self._analyze_buy_sell_orders(df)
            
            # Analyze order sizes
            order_size_analysis = self._analyze_order_sizes(df)
            
            # Analyze order timing
            timing_analysis = self._analyze_order_timing(df)
            
            # Generate order flow signals
            order_flow_signals = self._generate_order_flow_signals(df)
            
            return {
                "buy_sell_analysis": buy_sell_analysis,
                "order_size_analysis": order_size_analysis,
                "timing_analysis": timing_analysis,
                "order_flow_signals": order_flow_signals,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order flow: {e}")
            return {"error": str(e)}
    
    def _calculate_volume_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate volume-based metrics"""
        try:
            volume = df["volume"]
            
            # Basic volume statistics
            avg_volume = volume.mean()
            median_volume = volume.median()
            std_volume = volume.std()
            max_volume = volume.max()
            min_volume = volume.min()
            
            # Volume ratios
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volume trend
            volume_trend = self._calculate_volume_trend(volume)
            
            # Volume volatility
            volume_volatility = std_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                "average_volume": round(avg_volume, 2),
                "median_volume": round(median_volume, 2),
                "std_volume": round(std_volume, 2),
                "max_volume": round(max_volume, 2),
                "min_volume": round(min_volume, 2),
                "current_volume": round(current_volume, 2),
                "volume_ratio": round(volume_ratio, 2),
                "volume_trend": volume_trend,
                "volume_volatility": round(volume_volatility, 4)
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume metrics: {e}")
            return {}
    
    def _analyze_volume_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze volume trends over time"""
        try:
            volume = df["volume"]
            
            # Short-term trend (5 periods)
            short_trend = self._calculate_volume_trend(volume.tail(5))
            
            # Medium-term trend (20 periods)
            medium_trend = self._calculate_volume_trend(volume.tail(20))
            
            # Long-term trend (50 periods)
            long_trend = self._calculate_volume_trend(volume.tail(50)) if len(volume) >= 50 else "INSUFFICIENT_DATA"
            
            # Volume acceleration
            volume_acceleration = self._calculate_volume_acceleration(volume)
            
            return {
                "short_term_trend": short_trend,
                "medium_term_trend": medium_trend,
                "long_term_trend": long_trend,
                "volume_acceleration": volume_acceleration
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume trends: {e}")
            return {}
    
    def _detect_volume_spikes(self, df: pd.DataFrame) -> List[Dict]:
        """Detect volume spikes and anomalies"""
        try:
            volume = df["volume"]
            avg_volume = volume.mean()
            std_volume = volume.std()
            
            spikes = []
            
            for i, vol in enumerate(volume):
                if vol > avg_volume + (2 * std_volume):  # 2 standard deviations above mean
                    spikes.append({
                        "index": i,
                        "volume": vol,
                        "ratio": vol / avg_volume,
                        "date": df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                        "severity": "HIGH" if vol > avg_volume + (3 * std_volume) else "MEDIUM"
                    })
            
            return spikes[-10:]  # Return last 10 spikes
            
        except Exception as e:
            logger.error(f"Error detecting volume spikes: {e}")
            return []
    
    def _analyze_price_volume_relationship(self, df: pd.DataFrame) -> Dict:
        """Analyze relationship between price and volume"""
        try:
            if "close" not in df.columns or "volume" not in df.columns:
                return {"error": "Price and volume data required"}
            
            price = df["close"]
            volume = df["volume"]
            
            # Calculate correlation
            correlation = price.corr(volume)
            
            # Analyze volume on up days vs down days
            price_change = price.pct_change()
            up_days = price_change > 0
            down_days = price_change < 0
            
            up_volume = volume[up_days].mean() if up_days.any() else 0
            down_volume = volume[down_days].mean() if down_days.any() else 0
            
            # Volume-weighted average price (VWAP)
            vwap = (price * volume).sum() / volume.sum() if volume.sum() > 0 else price.iloc[-1]
            
            # On-Balance Volume (OBV)
            obv = self._calculate_obv(price, volume)
            
            return {
                "price_volume_correlation": round(correlation, 4),
                "up_days_avg_volume": round(up_volume, 2),
                "down_days_avg_volume": round(down_volume, 2),
                "volume_ratio_up_down": round(up_volume / down_volume, 2) if down_volume > 0 else 0,
                "vwap": round(vwap, 2),
                "obv_trend": self._calculate_obv_trend(obv)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing price-volume relationship: {e}")
            return {}
    
    def _generate_volume_signals(self, df: pd.DataFrame, volume_metrics: Dict) -> Dict:
        """Generate trading signals based on volume analysis"""
        try:
            signals = {
                "overall_signal": "NEUTRAL",
                "strength": 0,
                "signals": []
            }
            
            volume_ratio = volume_metrics.get("volume_ratio", 1)
            volume_trend = volume_metrics.get("volume_trend", "NEUTRAL")
            
            # High volume signal
            if volume_ratio > self.volume_thresholds["high_volume"]:
                signals["signals"].append({
                    "type": "HIGH_VOLUME",
                    "signal": "BUY" if volume_trend == "INCREASING" else "SELL",
                    "strength": min(volume_ratio / 2, 1.0),
                    "message": f"Volume is {volume_ratio:.1f}x average"
                })
            
            # Very high volume signal
            if volume_ratio > self.volume_thresholds["very_high_volume"]:
                signals["signals"].append({
                    "type": "VERY_HIGH_VOLUME",
                    "signal": "BUY" if volume_trend == "INCREASING" else "SELL",
                    "strength": 0.9,
                    "message": f"Volume is {volume_ratio:.1f}x average - Very high activity"
                })
            
            # Low volume signal
            if volume_ratio < self.volume_thresholds["low_volume"]:
                signals["signals"].append({
                    "type": "LOW_VOLUME",
                    "signal": "HOLD",
                    "strength": 0.3,
                    "message": f"Volume is {volume_ratio:.1f}x average - Low activity"
                })
            
            # Determine overall signal
            if signals["signals"]:
                buy_signals = [s for s in signals["signals"] if s["signal"] == "BUY"]
                sell_signals = [s for s in signals["signals"] if s["signal"] == "SELL"]
                
                if buy_signals and not sell_signals:
                    signals["overall_signal"] = "BUY"
                    signals["strength"] = max(s["strength"] for s in buy_signals)
                elif sell_signals and not buy_signals:
                    signals["overall_signal"] = "SELL"
                    signals["strength"] = max(s["strength"] for s in sell_signals)
                elif buy_signals and sell_signals:
                    buy_strength = max(s["strength"] for s in buy_signals)
                    sell_strength = max(s["strength"] for s in sell_signals)
                    if buy_strength > sell_strength:
                        signals["overall_signal"] = "BUY"
                        signals["strength"] = buy_strength
                    else:
                        signals["overall_signal"] = "SELL"
                        signals["strength"] = sell_strength
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating volume signals: {e}")
            return {"overall_signal": "NEUTRAL", "strength": 0, "signals": []}
    
    def _analyze_buy_sell_orders(self, df: pd.DataFrame) -> Dict:
        """Analyze buy vs sell order patterns"""
        try:
            if "order_type" not in df.columns:
                return {"error": "Order type data required"}
            
            buy_orders = df[df["order_type"] == "BUY"]
            sell_orders = df[df["order_type"] == "SELL"]
            
            buy_volume = buy_orders["quantity"].sum() if "quantity" in buy_orders.columns else 0
            sell_volume = sell_orders["quantity"].sum() if "quantity" in sell_orders.columns else 0
            
            total_volume = buy_volume + sell_volume
            
            return {
                "buy_orders_count": len(buy_orders),
                "sell_orders_count": len(sell_orders),
                "buy_volume": buy_volume,
                "sell_volume": sell_volume,
                "buy_volume_ratio": buy_volume / total_volume if total_volume > 0 else 0,
                "sell_volume_ratio": sell_volume / total_volume if total_volume > 0 else 0,
                "net_volume": buy_volume - sell_volume,
                "order_imbalance": (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing buy/sell orders: {e}")
            return {}
    
    def _analyze_order_sizes(self, df: pd.DataFrame) -> Dict:
        """Analyze order size patterns"""
        try:
            if "quantity" not in df.columns:
                return {"error": "Quantity data required"}
            
            quantities = df["quantity"]
            
            return {
                "average_order_size": quantities.mean(),
                "median_order_size": quantities.median(),
                "max_order_size": quantities.max(),
                "min_order_size": quantities.min(),
                "std_order_size": quantities.std(),
                "large_orders_count": len(quantities[quantities > quantities.quantile(0.9)]),
                "small_orders_count": len(quantities[quantities < quantities.quantile(0.1)])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order sizes: {e}")
            return {}
    
    def _analyze_order_timing(self, df: pd.DataFrame) -> Dict:
        """Analyze order timing patterns"""
        try:
            if "timestamp" not in df.columns:
                return {"error": "Timestamp data required"}
            
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["hour"] = df["timestamp"].dt.hour
            
            # Analyze by hour
            hourly_counts = df["hour"].value_counts().sort_index()
            
            # Peak hours
            peak_hours = hourly_counts.nlargest(3).index.tolist()
            
            return {
                "total_orders": len(df),
                "peak_hours": peak_hours,
                "hourly_distribution": hourly_counts.to_dict(),
                "most_active_hour": hourly_counts.idxmax(),
                "least_active_hour": hourly_counts.idxmin()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order timing: {e}")
            return {}
    
    def _generate_order_flow_signals(self, df: pd.DataFrame) -> Dict:
        """Generate signals based on order flow analysis"""
        try:
            buy_sell_analysis = self._analyze_buy_sell_orders(df)
            
            signals = {
                "overall_signal": "NEUTRAL",
                "strength": 0,
                "signals": []
            }
            
            order_imbalance = buy_sell_analysis.get("order_imbalance", 0)
            
            if order_imbalance > 0.1:  # 10% more buy orders
                signals["signals"].append({
                    "type": "ORDER_IMBALANCE",
                    "signal": "BUY",
                    "strength": min(abs(order_imbalance), 1.0),
                    "message": f"Buy order imbalance: {order_imbalance:.1%}"
                })
            elif order_imbalance < -0.1:  # 10% more sell orders
                signals["signals"].append({
                    "type": "ORDER_IMBALANCE",
                    "signal": "SELL",
                    "strength": min(abs(order_imbalance), 1.0),
                    "message": f"Sell order imbalance: {order_imbalance:.1%}"
                })
            
            # Determine overall signal
            if signals["signals"]:
                signal = signals["signals"][0]
                signals["overall_signal"] = signal["signal"]
                signals["strength"] = signal["strength"]
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating order flow signals: {e}")
            return {"overall_signal": "NEUTRAL", "strength": 0, "signals": []}
    
    def _calculate_volume_trend(self, volume_series: pd.Series) -> str:
        """Calculate volume trend direction"""
        try:
            if len(volume_series) < 2:
                return "INSUFFICIENT_DATA"
            
            # Simple linear trend
            x = np.arange(len(volume_series))
            y = volume_series.values
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                return "INCREASING"
            elif slope < -0.1:
                return "DECREASING"
            else:
                return "STABLE"
                
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return "UNKNOWN"
    
    def _calculate_volume_acceleration(self, volume_series: pd.Series) -> float:
        """Calculate volume acceleration"""
        try:
            if len(volume_series) < 3:
                return 0
            
            # Calculate second derivative
            first_diff = volume_series.diff()
            second_diff = first_diff.diff()
            
            return second_diff.iloc[-1] if not pd.isna(second_diff.iloc[-1]) else 0
            
        except Exception as e:
            logger.error(f"Error calculating volume acceleration: {e}")
            return 0
    
    def _calculate_obv(self, price: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        try:
            price_change = price.diff()
            obv = np.where(price_change > 0, volume, 
                          np.where(price_change < 0, -volume, 0)).cumsum()
            return pd.Series(obv, index=price.index)
            
        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")
            return pd.Series(0, index=price.index)
    
    def _calculate_obv_trend(self, obv: pd.Series) -> str:
        """Calculate OBV trend"""
        try:
            if len(obv) < 2:
                return "INSUFFICIENT_DATA"
            
            recent_obv = obv.tail(5)
            trend = self._calculate_volume_trend(recent_obv)
            return trend
            
        except Exception as e:
            logger.error(f"Error calculating OBV trend: {e}")
            return "UNKNOWN"
