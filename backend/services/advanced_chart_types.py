"""
Advanced Chart Types Service
Volume Profile, Market Profile, Order Flow, Footprint, Renko, Point & Figure, Heikin Ashi
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedChartTypes:
    """Advanced chart types and analysis"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def calculate_volume_profile(
        self,
        df: pd.DataFrame,
        price_bins: int = 50
    ) -> Dict[str, Any]:
        """Calculate Volume Profile (Price-by-Volume analysis)"""
        try:
            if len(df) == 0:
                return {"error": "No data available"}
            
            # Create price bins
            min_price = df["low"].min()
            max_price = df["high"].max()
            price_range = max_price - min_price
            
            if price_range == 0:
                return {"error": "No price variation"}
            
            bin_size = price_range / price_bins
            bins = np.arange(min_price, max_price + bin_size, bin_size)
            
            # Calculate volume at each price level
            volume_profile = []
            for i in range(len(bins) - 1):
                bin_low = bins[i]
                bin_high = bins[i + 1]
                
                # Filter candles in this price range
                mask = (df["low"] <= bin_high) & (df["high"] >= bin_low)
                volume_in_bin = df.loc[mask, "volume"].sum()
                
                volume_profile.append({
                    "price": (bin_low + bin_high) / 2,
                    "volume": float(volume_in_bin),
                    "price_low": float(bin_low),
                    "price_high": float(bin_high)
                })
            
            # Find POC (Point of Control - highest volume)
            poc = max(volume_profile, key=lambda x: x["volume"])
            
            # Find Value Area (70% of volume)
            sorted_profile = sorted(volume_profile, key=lambda x: x["volume"], reverse=True)
            total_volume = sum(p["volume"] for p in volume_profile)
            value_area_volume = total_volume * 0.70
            
            value_area = []
            cumulative_volume = 0
            for profile_point in sorted_profile:
                value_area.append(profile_point)
                cumulative_volume += profile_point["volume"]
                if cumulative_volume >= value_area_volume:
                    break
            
            value_area_low = min(p["price_low"] for p in value_area)
            value_area_high = max(p["price_high"] for p in value_area)
            
            return {
                "volume_profile": volume_profile,
                "poc": {
                    "price": poc["price"],
                    "volume": poc["volume"]
                },
                "value_area": {
                    "low": value_area_low,
                    "high": value_area_high,
                    "volume_percentage": 70.0
                },
                "total_volume": float(total_volume),
                "price_range": {
                    "min": float(min_price),
                    "max": float(max_price)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {"error": str(e)}
    
    def calculate_market_profile(
        self,
        df: pd.DataFrame,
        time_period: str = "30T"  # 30-minute periods
    ) -> Dict[str, Any]:
        """Calculate Market Profile (Time-Price Opportunity analysis)"""
        try:
            if len(df) == 0:
                return {"error": "No data available"}
            
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df = df.set_index("timestamp")
                else:
                    df.index = pd.date_range(start=datetime.now(), periods=len(df), freq="1H")
            
            # Resample to time periods
            resampled = df.resample(time_period).agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            })
            
            # Calculate TPO (Time Price Opportunity) for each period
            market_profile = []
            for period, row in resampled.iterrows():
                # Create price bins for this period
                price_range = row["high"] - row["low"]
                if price_range > 0:
                    bins = np.linspace(row["low"], row["high"], 20)
                    tpo_count = {}
                    
                    for price in bins:
                        tpo_count[float(price)] = 1
                    
                    market_profile.append({
                        "period": period.isoformat(),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                        "tpo_count": len(tpo_count),
                        "price_range": float(price_range)
                    })
            
            return {
                "market_profile": market_profile,
                "period": time_period,
                "total_periods": len(market_profile)
            }
            
        except Exception as e:
            logger.error(f"Error calculating market profile: {e}")
            return {"error": str(e)}
    
    def calculate_order_flow(
        self,
        df: pd.DataFrame,
        bid_ask_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Calculate Order Flow (Bid/Ask imbalance visualization)"""
        try:
            if len(df) == 0:
                return {"error": "No data available"}
            
            # Calculate buy/sell pressure
            order_flow = []
            for idx, row in df.iterrows():
                # Estimate buy/sell pressure from price action
                body = abs(row["close"] - row["open"])
                upper_shadow = row["high"] - max(row["open"], row["close"])
                lower_shadow = min(row["open"], row["close"]) - row["low"]
                
                # Bullish if close > open
                is_bullish = row["close"] > row["open"]
                
                # Calculate imbalance
                if is_bullish:
                    buy_pressure = body + lower_shadow
                    sell_pressure = upper_shadow
                else:
                    buy_pressure = lower_shadow
                    sell_pressure = body + upper_shadow
                
                total_pressure = buy_pressure + sell_pressure
                imbalance = (buy_pressure - sell_pressure) / total_pressure if total_pressure > 0 else 0
                
                order_flow.append({
                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "price": float(row["close"]),
                    "buy_pressure": float(buy_pressure),
                    "sell_pressure": float(sell_pressure),
                    "imbalance": float(imbalance),
                    "volume": float(row["volume"])
                })
            
            # Calculate cumulative imbalance
            cumulative_imbalance = 0
            for flow in order_flow:
                cumulative_imbalance += flow["imbalance"]
                flow["cumulative_imbalance"] = cumulative_imbalance
            
            return {
                "order_flow": order_flow,
                "average_imbalance": float(np.mean([f["imbalance"] for f in order_flow])),
                "total_imbalance": float(cumulative_imbalance)
            }
            
        except Exception as e:
            logger.error(f"Error calculating order flow: {e}")
            return {"error": str(e)}
    
    def create_footprint_chart(
        self,
        df: pd.DataFrame,
        price_levels: int = 20
    ) -> Dict[str, Any]:
        """Create Footprint Chart (Detailed order flow visualization)"""
        try:
            if len(df) == 0:
                return {"error": "No data available"}
            
            # Create price levels
            min_price = df["low"].min()
            max_price = df["high"].max()
            price_range = max_price - min_price
            level_size = price_range / price_levels
            
            # Build footprint
            footprint = {}
            for idx, row in df.iterrows():
                # Determine price levels touched
                levels_touched = np.arange(
                    np.floor((row["low"] - min_price) / level_size),
                    np.ceil((row["high"] - min_price) / level_size) + 1
                ).astype(int)
                
                for level in levels_touched:
                    price_level = min_price + (level * level_size)
                    price_key = f"{price_level:.2f}"
                    
                    if price_key not in footprint:
                        footprint[price_key] = {
                            "price": float(price_level),
                            "buy_volume": 0,
                            "sell_volume": 0,
                            "total_volume": 0,
                            "touches": 0
                        }
                    
                    # Estimate buy/sell volume
                    if row["close"] >= row["open"]:
                        footprint[price_key]["buy_volume"] += row["volume"] * 0.6
                        footprint[price_key]["sell_volume"] += row["volume"] * 0.4
                    else:
                        footprint[price_key]["buy_volume"] += row["volume"] * 0.4
                        footprint[price_key]["sell_volume"] += row["volume"] * 0.6
                    
                    footprint[price_key]["total_volume"] += row["volume"]
                    footprint[price_key]["touches"] += 1
            
            footprint_list = sorted(footprint.values(), key=lambda x: x["price"])
            
            return {
                "footprint": footprint_list,
                "price_levels": price_levels,
                "price_range": {
                    "min": float(min_price),
                    "max": float(max_price)
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating footprint chart: {e}")
            return {"error": str(e)}
    
    def convert_to_renko(
        self,
        df: pd.DataFrame,
        brick_size: float = None
    ) -> pd.DataFrame:
        """Convert price data to Renko chart"""
        try:
            if len(df) == 0:
                return pd.DataFrame()
            
            # Auto-calculate brick size if not provided (1% of average price)
            if brick_size is None:
                avg_price = df["close"].mean()
                brick_size = avg_price * 0.01
            
            renko_bricks = []
            current_price = df["close"].iloc[0]
            current_direction = None  # 'up' or 'down'
            
            for idx, row in df.iterrows():
                price = row["close"]
                price_change = price - current_price
                
                # Determine number of bricks
                if abs(price_change) >= brick_size:
                    num_bricks = int(abs(price_change) / brick_size)
                    direction = 'up' if price_change > 0 else 'down'
                    
                    for _ in range(num_bricks):
                        if direction == 'up':
                            brick_open = current_price
                            brick_close = current_price + brick_size
                            current_price = brick_close
                        else:
                            brick_open = current_price
                            brick_close = current_price - brick_size
                            current_price = brick_close
                        
                        renko_bricks.append({
                            "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                            "open": float(brick_open),
                            "high": float(max(brick_open, brick_close)),
                            "low": float(min(brick_open, brick_close)),
                            "close": float(brick_close),
                            "volume": float(row["volume"] / num_bricks) if num_bricks > 0 else 0
                        })
            
            return pd.DataFrame(renko_bricks)
            
        except Exception as e:
            logger.error(f"Error converting to Renko: {e}")
            return pd.DataFrame()
    
    def convert_to_point_and_figure(
        self,
        df: pd.DataFrame,
        box_size: float = None,
        reversal: int = 3
    ) -> pd.DataFrame:
        """Convert price data to Point & Figure chart"""
        try:
            if len(df) == 0:
                return pd.DataFrame()
            
            # Auto-calculate box size if not provided
            if box_size is None:
                avg_price = df["close"].mean()
                box_size = avg_price * 0.01
            
            pnf_columns = []
            current_column = []
            current_direction = None  # 'X' (up) or 'O' (down)
            current_box_price = df["close"].iloc[0]
            
            for idx, row in df.iterrows():
                high = row["high"]
                low = row["low"]
                
                if current_direction is None:
                    # First column
                    if high - current_box_price >= box_size:
                        current_direction = 'X'
                        while current_box_price + box_size <= high:
                            current_box_price += box_size
                            current_column.append({
                                "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                                "price": float(current_box_price),
                                "type": "X"
                            })
                    elif current_box_price - low >= box_size:
                        current_direction = 'O'
                        while current_box_price - box_size >= low:
                            current_box_price -= box_size
                            current_column.append({
                                "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                                "price": float(current_box_price),
                                "type": "O"
                            })
                else:
                    # Continue or reverse
                    if current_direction == 'X':
                        # Check for continuation
                        if high - current_box_price >= box_size:
                            while current_box_price + box_size <= high:
                                current_box_price += box_size
                                current_column.append({
                                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                                    "price": float(current_box_price),
                                    "type": "X"
                                })
                        # Check for reversal
                        elif current_box_price - low >= box_size * reversal:
                            pnf_columns.append(current_column)
                            current_column = []
                            current_direction = 'O'
                            while current_box_price - box_size >= low:
                                current_box_price -= box_size
                                current_column.append({
                                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                                    "price": float(current_box_price),
                                    "type": "O"
                                })
                    else:  # 'O'
                        # Check for continuation
                        if current_box_price - low >= box_size:
                            while current_box_price - box_size >= low:
                                current_box_price -= box_size
                                current_column.append({
                                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                                    "price": float(current_box_price),
                                    "type": "O"
                                })
                        # Check for reversal
                        elif high - current_box_price >= box_size * reversal:
                            pnf_columns.append(current_column)
                            current_column = []
                            current_direction = 'X'
                            while current_box_price + box_size <= high:
                                current_box_price += box_size
                                current_column.append({
                                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                                    "price": float(current_box_price),
                                    "type": "X"
                                })
            
            if current_column:
                pnf_columns.append(current_column)
            
            # Flatten columns
            pnf_data = []
            for col in pnf_columns:
                pnf_data.extend(col)
            
            return pd.DataFrame(pnf_data)
            
        except Exception as e:
            logger.error(f"Error converting to Point & Figure: {e}")
            return pd.DataFrame()
    
    def convert_to_heikin_ashi(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """Convert price data to Heikin Ashi chart"""
        try:
            if len(df) == 0:
                return pd.DataFrame()
            
            ha_df = df.copy()
            
            # Calculate Heikin Ashi values
            ha_df["ha_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
            
            ha_df["ha_open"] = 0.0
            ha_df.loc[0, "ha_open"] = (df["open"].iloc[0] + df["close"].iloc[0]) / 2
            
            for i in range(1, len(ha_df)):
                ha_df.iloc[i, ha_df.columns.get_loc("ha_open")] = (
                    ha_df.iloc[i-1]["ha_open"] + ha_df.iloc[i-1]["ha_close"]
                ) / 2
            
            ha_df["ha_high"] = ha_df[["high", "ha_open", "ha_close"]].max(axis=1)
            ha_df["ha_low"] = ha_df[["low", "ha_open", "ha_close"]].min(axis=1)
            
            # Create new dataframe with Heikin Ashi values
            result = pd.DataFrame({
                "timestamp": ha_df.index if isinstance(ha_df.index, pd.DatetimeIndex) else range(len(ha_df)),
                "open": ha_df["ha_open"],
                "high": ha_df["ha_high"],
                "low": ha_df["ha_low"],
                "close": ha_df["ha_close"],
                "volume": ha_df["volume"]
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting to Heikin Ashi: {e}")
            return pd.DataFrame()

# Create singleton instance
advanced_chart_types = AdvancedChartTypes()

