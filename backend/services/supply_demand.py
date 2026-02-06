"""
Supply & Demand Zone Detection Service
Identifies institutional order blocks and zones where large orders were placed
Essential for Smart Money Concepts and institutional trading style
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ZoneType(str, Enum):
    DEMAND = "demand"  # Buying zone (support)
    SUPPLY = "supply"  # Selling zone (resistance)

class ZoneStatus(str, Enum):
    FRESH = "fresh"      # Never tested
    TESTED = "tested"    # Touched but not broken
    BROKEN = "broken"    # Price moved through

class SupplyDemandService:
    def __init__(self):
        self.min_base_candles = 1  # Minimum candles for zone base (very relaxed for backtesting)
        self.zone_strength_threshold = 0.2  # Minimum strength to qualify (very relaxed for backtesting)
        
    def analyze_supply_demand(
        self,
        data: List[Dict[str, Any]],
        lookback_period: int = 100,
        min_zone_strength: float = 0.3  # Relaxed from 0.5
    ) -> Dict[str, Any]:
        """
        Analyze and identify supply and demand zones
        
        Args:
            data: OHLCV price data
            lookback_period: How many candles to look back
            min_zone_strength: Minimum strength score (0-1)
            
        Returns:
            Dictionary containing supply zones, demand zones, and trading signals
        """
        try:
            df = pd.DataFrame(data)
            
            if len(df) < 20:
                return {
                    "success": False,
                    "error": "Insufficient data for supply/demand analysis"
                }
            
            # Limit lookback
            df = df.tail(lookback_period)
            df = df.reset_index(drop=True)
            
            # Detect demand zones (buy zones)
            demand_zones = self._detect_demand_zones(df)
            
            # Detect supply zones (sell zones)
            supply_zones = self._detect_supply_zones(df)
            
            # Calculate zone strength
            demand_zones = self._calculate_zone_strength(demand_zones, df)
            supply_zones = self._calculate_zone_strength(supply_zones, df)
            
            # Filter by minimum strength
            demand_zones = [z for z in demand_zones if z['strength'] >= min_zone_strength]
            supply_zones = [z for z in supply_zones if z['strength'] >= min_zone_strength]
            
            # Update zone status (fresh, tested, broken)
            demand_zones = self._update_zone_status(demand_zones, df, 'demand')
            supply_zones = self._update_zone_status(supply_zones, df, 'supply')
            
            # Find active zones (fresh or tested but not broken)
            active_demand = [z for z in demand_zones if z['status'] != ZoneStatus.BROKEN.value]
            active_supply = [z for z in supply_zones if z['status'] != ZoneStatus.BROKEN.value]
            
            # Generate trading signals
            signals = self._generate_trading_signals(
                active_demand,
                active_supply,
                df
            )
            
            # Get statistics
            stats = self._calculate_statistics(
                demand_zones,
                supply_zones,
                active_demand,
                active_supply
            )
            
            # Find nearest zones
            current_price = float(df.iloc[-1]['close'])
            nearest = self._find_nearest_zones(
                active_demand,
                active_supply,
                current_price
            )
            
            return {
                "success": True,
                "data": {
                    "demand_zones": demand_zones,
                    "supply_zones": supply_zones,
                    "active_demand_zones": active_demand,
                    "active_supply_zones": active_supply,
                    "nearest_demand": nearest['demand'],
                    "nearest_supply": nearest['supply'],
                    "trading_signals": signals,
                    "statistics": stats,
                    "current_price": current_price
                }
            }
            
        except Exception as e:
            logger.error(f"Error in supply/demand analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_demand_zones(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect demand zones (order blocks before strong bullish moves)"""
        zones = []
        
        for i in range(self.min_base_candles, len(df) - 5):
            # Look for strong bullish move (explosive candle)
            current = df.iloc[i]
            body_size = abs(current['close'] - current['open'])
            avg_body = df['close'].iloc[max(0, i-20):i].sub(df['open'].iloc[max(0, i-20):i]).abs().mean()
            
            # Check if it's a strong bullish candle
            if (current['close'] > current['open'] and 
                body_size > avg_body * 1.5):  # 50% larger than average
                
                # Find the base (consolidation before move)
                base_start = max(0, i - 10)
                base_candles = df.iloc[base_start:i]
                
                if len(base_candles) >= self.min_base_candles:
                    # The last bearish candle before the move is the demand zone
                    for j in range(len(base_candles) - 1, -1, -1):
                        candle = base_candles.iloc[j]
                        if candle['close'] < candle['open']:  # Bearish candle
                            zone_top = float(candle['open'])
                            zone_bottom = float(candle['close'])
                            zone_index = base_start + j
                            
                            zones.append({
                                'type': ZoneType.DEMAND.value,
                                'index': int(zone_index),
                                'top': zone_top,
                                'bottom': zone_bottom,
                                'mid': (zone_top + zone_bottom) / 2,
                                'size': zone_top - zone_bottom,
                                'formed_at': df.iloc[zone_index].get('time', zone_index),
                                'explosion_index': int(i),
                                'explosion_candle': {
                                    'open': float(current['open']),
                                    'close': float(current['close']),
                                    'move_percent': ((current['close'] - current['open']) / current['open']) * 100
                                }
                            })
                            break
        
        return zones
    
    def _detect_supply_zones(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect supply zones (order blocks before strong bearish moves)"""
        zones = []
        
        for i in range(self.min_base_candles, len(df) - 5):
            # Look for strong bearish move (explosive candle)
            current = df.iloc[i]
            body_size = abs(current['close'] - current['open'])
            avg_body = df['close'].iloc[max(0, i-20):i].sub(df['open'].iloc[max(0, i-20):i]).abs().mean()
            
            # Check if it's a strong bearish candle
            if (current['close'] < current['open'] and 
                body_size > avg_body * 1.5):  # 50% larger than average
                
                # Find the base (consolidation before move)
                base_start = max(0, i - 10)
                base_candles = df.iloc[base_start:i]
                
                if len(base_candles) >= self.min_base_candles:
                    # The last bullish candle before the move is the supply zone
                    for j in range(len(base_candles) - 1, -1, -1):
                        candle = base_candles.iloc[j]
                        if candle['close'] > candle['open']:  # Bullish candle
                            zone_bottom = float(candle['open'])
                            zone_top = float(candle['close'])
                            zone_index = base_start + j
                            
                            zones.append({
                                'type': ZoneType.SUPPLY.value,
                                'index': int(zone_index),
                                'top': zone_top,
                                'bottom': zone_bottom,
                                'mid': (zone_top + zone_bottom) / 2,
                                'size': zone_top - zone_bottom,
                                'formed_at': df.iloc[zone_index].get('time', zone_index),
                                'explosion_index': int(i),
                                'explosion_candle': {
                                    'open': float(current['open']),
                                    'close': float(current['close']),
                                    'move_percent': ((current['open'] - current['close']) / current['open']) * 100
                                }
                            })
                            break
        
        return zones
    
    def _calculate_zone_strength(
        self,
        zones: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Calculate strength of each zone based on multiple factors"""
        
        for zone in zones:
            # Factors:
            # 1. Size of explosive move (larger = stronger)
            # 2. Volume on explosion (higher = stronger)
            # 3. Zone freshness (fresher = stronger)
            # 4. Time since formation (not too old)
            
            explosion_move = zone['explosion_candle']['move_percent']
            move_score = min(explosion_move / 5, 1.0)  # Normalize to 0-1
            
            # Volume score
            explosion_idx = zone['explosion_index']
            if explosion_idx < len(df) and 'volume' in df.columns:
                explosion_volume = df.iloc[explosion_idx]['volume']
                avg_volume = df['volume'].iloc[max(0, explosion_idx-20):explosion_idx].mean()
                volume_ratio = explosion_volume / avg_volume if avg_volume > 0 else 1
                volume_score = min(volume_ratio / 2, 1.0)
            else:
                volume_score = 0.5
            
            # Freshness score (will be updated in _update_zone_status)
            freshness_score = 1.0  # Default to fresh
            
            # Age score (prefer not too old)
            age = len(df) - zone['index']
            age_score = max(0, 1 - (age / len(df)))
            
            # Combined strength (0-1)
            strength = (
                move_score * 0.4 +
                volume_score * 0.3 +
                freshness_score * 0.2 +
                age_score * 0.1
            )
            
            zone['strength'] = round(strength, 2)
            zone['strength_label'] = 'strong' if strength > 0.7 else 'medium' if strength > 0.4 else 'weak'
        
        return zones
    
    def _update_zone_status(
        self,
        zones: List[Dict[str, Any]],
        df: pd.DataFrame,
        zone_type: str
    ) -> List[Dict[str, Any]]:
        """Update zone status based on price action after formation"""
        
        for zone in zones:
            zone_index = zone['index']
            zone_top = zone['top']
            zone_bottom = zone['bottom']
            
            # Check all candles after zone formation
            touched = False
            broken = False
            touch_count = 0
            
            for i in range(zone_index + 1, len(df)):
                candle = df.iloc[i]
                candle_high = candle.get('high', candle['close'])
                candle_low = candle.get('low', candle['close'])
                
                # Check if price entered the zone
                if candle_low <= zone_top and candle_high >= zone_bottom:
                    touched = True
                    touch_count += 1
                    
                    # Check if zone was broken (price closed through it)
                    if zone_type == 'demand':
                        if candle['close'] < zone_bottom:
                            broken = True
                            break
                    else:  # supply
                        if candle['close'] > zone_top:
                            broken = True
                            break
            
            # Set status
            if broken:
                zone['status'] = ZoneStatus.BROKEN.value
                zone['status_label'] = 'Broken (Invalid)'
            elif touched:
                zone['status'] = ZoneStatus.TESTED.value
                zone['status_label'] = f'Tested ({touch_count}x)'
            else:
                zone['status'] = ZoneStatus.FRESH.value
                zone['status_label'] = 'Fresh (Untested)'
            
            zone['touch_count'] = touch_count
            
            # Update strength based on status
            if zone['status'] == ZoneStatus.FRESH.value:
                zone['strength'] = min(zone['strength'] * 1.2, 1.0)  # Boost fresh zones
            elif zone['status'] == ZoneStatus.BROKEN.value:
                zone['strength'] = zone['strength'] * 0.3  # Penalize broken zones
        
        return zones
    
    def _generate_trading_signals(
        self,
        demand_zones: List[Dict[str, Any]],
        supply_zones: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate trading signals based on zones"""
        
        if not demand_zones and not supply_zones:
            return {
                "signal": "neutral",
                "confidence": "low",
                "message": "No active zones detected"
            }
        
        current_price = float(df.iloc[-1]['close'])
        
        # Check if price is in or near a zone
        in_demand_zone = None
        in_supply_zone = None
        
        for zone in demand_zones:
            if zone['bottom'] <= current_price <= zone['top']:
                in_demand_zone = zone
                break
            elif abs(current_price - zone['top']) / current_price < 0.01:  # Within 1%
                in_demand_zone = zone
        
        for zone in supply_zones:
            if zone['bottom'] <= current_price <= zone['top']:
                in_supply_zone = zone
                break
            elif abs(zone['bottom'] - current_price) / current_price < 0.01:  # Within 1%
                in_supply_zone = zone
        
        # Generate signal
        if in_demand_zone:
            return {
                "signal": "buy",
                "confidence": "high" if in_demand_zone['status'] == 'fresh' else "medium",
                "message": f"Price in {in_demand_zone['status']} demand zone",
                "zone": in_demand_zone,
                "entry_suggestion": f"Buy near {in_demand_zone['bottom']:.2f}",
                "stop_loss": f"Below {in_demand_zone['bottom']:.2f}",
                "target": "Next supply zone"
            }
        
        elif in_supply_zone:
            return {
                "signal": "sell",
                "confidence": "high" if in_supply_zone['status'] == 'fresh' else "medium",
                "message": f"Price in {in_supply_zone['status']} supply zone",
                "zone": in_supply_zone,
                "entry_suggestion": f"Sell near {in_supply_zone['top']:.2f}",
                "stop_loss": f"Above {in_supply_zone['top']:.2f}",
                "target": "Next demand zone"
            }
        
        else:
            # Price between zones
            return {
                "signal": "neutral",
                "confidence": "medium",
                "message": "Wait for price to reach a zone",
                "nearest_demand": demand_zones[0]['mid'] if demand_zones else None,
                "nearest_supply": supply_zones[0]['mid'] if supply_zones else None
            }
    
    def _find_nearest_zones(
        self,
        demand_zones: List[Dict[str, Any]],
        supply_zones: List[Dict[str, Any]],
        current_price: float
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Find nearest demand and supply zones to current price"""
        
        # Find nearest demand zone below current price
        nearest_demand = None
        min_distance = float('inf')
        
        for zone in demand_zones:
            if zone['mid'] < current_price:
                distance = current_price - zone['mid']
                if distance < min_distance:
                    min_distance = distance
                    nearest_demand = zone
        
        # Find nearest supply zone above current price
        nearest_supply = None
        min_distance = float('inf')
        
        for zone in supply_zones:
            if zone['mid'] > current_price:
                distance = zone['mid'] - current_price
                if distance < min_distance:
                    min_distance = distance
                    nearest_supply = zone
        
        return {
            'demand': nearest_demand,
            'supply': nearest_supply
        }
    
    def _calculate_statistics(
        self,
        all_demand: List[Dict[str, Any]],
        all_supply: List[Dict[str, Any]],
        active_demand: List[Dict[str, Any]],
        active_supply: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics about zones"""
        
        fresh_demand = sum(1 for z in active_demand if z['status'] == 'fresh')
        fresh_supply = sum(1 for z in active_supply if z['status'] == 'fresh')
        
        tested_demand = sum(1 for z in active_demand if z['status'] == 'tested')
        tested_supply = sum(1 for z in active_supply if z['status'] == 'tested')
        
        broken_demand = sum(1 for z in all_demand if z['status'] == 'broken')
        broken_supply = sum(1 for z in all_supply if z['status'] == 'broken')
        
        strong_demand = sum(1 for z in active_demand if z['strength_label'] == 'strong')
        strong_supply = sum(1 for z in active_supply if z['strength_label'] == 'strong')
        
        return {
            "total_demand_zones": len(all_demand),
            "total_supply_zones": len(all_supply),
            "active_demand_zones": len(active_demand),
            "active_supply_zones": len(active_supply),
            "fresh_demand": fresh_demand,
            "fresh_supply": fresh_supply,
            "tested_demand": tested_demand,
            "tested_supply": tested_supply,
            "broken_demand": broken_demand,
            "broken_supply": broken_supply,
            "strong_demand": strong_demand,
            "strong_supply": strong_supply
        }

