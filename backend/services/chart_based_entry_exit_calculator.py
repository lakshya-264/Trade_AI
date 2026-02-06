"""
Enhanced Chart-Based Entry/Exit Price Calculator
Implements real technical analysis for accurate trading signals
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChartBasedEntryExitCalculator:
    """Calculate entry/exit prices based on real technical analysis"""
    
    def __init__(self):
        self.min_profit_target = 0.5  # Minimum 0.5% profit target
        self.max_profit_target = 5.0  # Maximum 5% profit target
        self.risk_reward_ratio = 2.0  # Minimum 1:2 risk-reward ratio
        
    def calculate_entry_exit_prices(
        self, 
        data: pd.DataFrame, 
        signal: str, 
        current_price: float,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate entry, stop loss, and exit prices based on technical analysis
        
        Args:
            data: Historical price data with OHLCV
            signal: BUY, SELL, or HOLD
            current_price: Current market price
            volatility: Optional volatility multiplier for adjustments
            
        Returns:
            Dictionary with entry_price, stop_loss, exit_price and analysis
        """
        try:
            logger.info(f"Chart calculator: data length = {len(data)}, signal = {signal}, current_price = {current_price}")
            
            if len(data) < 10:  # Reduced from 20 to 10
                logger.warning(f"Insufficient data for chart analysis ({len(data)} < 10), using fallback")
                return self._fallback_calculation(signal, current_price)
            
            # Calculate technical indicators
            technical_analysis = self._analyze_technicals(data, current_price)
            logger.info(f"Technical analysis completed: {len(technical_analysis)} indicators")
            
            # Calculate support/resistance levels
            support_resistance = self._calculate_support_resistance(data)
            logger.info(f"Support/Resistance analysis completed: support={support_resistance.get('support')}, resistance={support_resistance.get('resistance')}")
            
            # Determine entry price based on signal and technicals
            entry_price = self._calculate_entry_price(
                signal, current_price, technical_analysis, support_resistance
            )
            
            # Calculate stop loss based on technical levels
            stop_loss = self._calculate_stop_loss(
                signal, entry_price, technical_analysis, support_resistance
            )
            
            # Calculate exit price based on technical targets
            exit_price, holding_period = self._calculate_exit_price(
                signal, entry_price, stop_loss, technical_analysis, support_resistance, volatility
            )
            
            logger.info(f"Calculated prices - Entry: {entry_price}, Stop: {stop_loss}, Exit: {exit_price}")
            logger.info(f"Estimated holding period: {holding_period}")
            
            # Validate risk-reward ratio
            validated_prices = self._validate_risk_reward(
                signal, entry_price, stop_loss, exit_price, current_price
            )
            
            return {
                **validated_prices,
                'holding_period': holding_period,
                'analysis': {
                    'signal': signal,
                    'technical_analysis': technical_analysis,
                    'support_resistance': support_resistance,
                    'risk_reward_ratio': self._calculate_risk_reward_ratio(
                        signal, validated_prices['entry_price'], 
                        validated_prices['stop_loss'], validated_prices['exit_price']
                    ),
                    'confidence': self._calculate_confidence(technical_analysis, support_resistance),
                    'method': 'chart_based_technical_analysis'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chart-based calculation: {e}")
            return self._fallback_calculation(signal, current_price)
    
    def _analyze_technicals(self, data: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Analyze technical indicators"""
        try:
            data_len = len(data)
            logger.info(f"Analyzing technicals with {data_len} data points")
            
            # Calculate moving averages with adaptive periods
            sma_period = min(20, data_len // 2) if data_len >= 4 else 3
            sma_period_long = min(50, data_len) if data_len >= 10 else sma_period
            
            data['sma_20'] = data['close'].rolling(window=sma_period).mean()
            data['sma_50'] = data['close'].rolling(window=sma_period_long).mean()
            data['ema_12'] = data['close'].ewm(span=min(12, data_len // 2)).mean()
            data['ema_26'] = data['close'].ewm(span=min(26, data_len)).mean()
            
            # Calculate RSI with adaptive period
            rsi_period = min(14, data_len // 2) if data_len >= 4 else 3
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            data['rsi'] = rsi
            
            # Calculate MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=min(9, data_len // 3)).mean()
            data['macd_histogram'] = data['macd'] - data['macd_signal']
            
            # Calculate Bollinger Bands with adaptive period
            bb_period = min(20, data_len // 2) if data_len >= 4 else 3
            data['bb_middle'] = data['close'].rolling(window=bb_period).mean()
            bb_std = data['close'].rolling(window=bb_period).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
            
            # Get latest values
            latest = data.iloc[-1]
            
            return {
                'sma_20': latest.get('sma_20'),
                'sma_50': latest.get('sma_50'),
                'ema_12': latest.get('ema_12'),
                'ema_26': latest.get('ema_26'),
                'rsi': latest.get('rsi'),
                'macd': latest.get('macd'),
                'macd_signal': latest.get('macd_signal'),
                'macd_histogram': latest.get('macd_histogram'),
                'bb_upper': latest.get('bb_upper'),
                'bb_middle': latest.get('bb_middle'),
                'bb_lower': latest.get('bb_lower'),
                'price_vs_sma20': ((current_price - latest.get('sma_20', current_price)) / latest.get('sma_20', current_price)) * 100,
                'price_vs_sma50': ((current_price - latest.get('sma_50', current_price)) / latest.get('sma_50', current_price)) * 100,
                'rsi_signal': 'overbought' if latest.get('rsi', 50) > 70 else 'oversold' if latest.get('rsi', 50) < 30 else 'neutral',
                'bb_position': self._get_bollinger_position(current_price, latest.get('bb_lower'), latest.get('bb_upper'))
            }
            
        except Exception as e:
            logger.error(f"Error analyzing technicals: {e}")
            return {}
    
    def _calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate dynamic support and resistance levels"""
        try:
            data_len = len(data)
            logger.info(f"Calculating support/resistance with {data_len} data points")
            
            if data_len < 6:
                logger.warning("Insufficient data for support/resistance analysis")
                return {'support': None, 'resistance': None}
            
            # Use adaptive lookback period
            lookback = min(20, data_len // 2) if data_len >= 10 else data_len - 2
            recent_data = data.tail(lookback)
            
            # Resistance: recent highs
            resistance_levels = []
            for i in range(2, len(recent_data)-2):
                if (recent_data.iloc[i]['high'] > recent_data.iloc[i-1]['high'] and 
                    recent_data.iloc[i]['high'] > recent_data.iloc[i-2]['high'] and
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+1]['high'] and 
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+2]['high']):
                    resistance_levels.append(recent_data.iloc[i]['high'])
            
            # Support: recent lows  
            support_levels = []
            for i in range(2, len(recent_data)-2):
                if (recent_data.iloc[i]['low'] < recent_data.iloc[i-1]['low'] and 
                    recent_data.iloc[i]['low'] < recent_data.iloc[i-2]['low'] and
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+1]['low'] and 
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+2]['low']):
                    support_levels.append(recent_data.iloc[i]['low'])
            
            # If no swing points found, use simple min/max approach
            if not resistance_levels:
                resistance_levels = [recent_data['high'].max()]
            if not support_levels:
                support_levels = [recent_data['low'].min()]
            
            # Get the closest levels
            current_price = data.iloc[-1]['close']
            
            resistance = min(resistance_levels) if resistance_levels else None
            support = max(support_levels) if support_levels else None
            
            # Filter by relevance (within 15% of current price for intraday)
            max_distance = 0.15
            if resistance and (resistance - current_price) / current_price > max_distance:
                resistance = None
            if support and (current_price - support) / current_price > max_distance:
                support = None
            
            return {
                'support': support,
                'resistance': resistance,
                'support_distance': ((current_price - support) / current_price * 100) if support else None,
                'resistance_distance': ((resistance - current_price) / current_price * 100) if resistance else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {'support': None, 'resistance': None}
    
    def _calculate_entry_price(
        self, 
        signal: str, 
        current_price: float, 
        technicals: Dict[str, Any], 
        sr_levels: Dict[str, Any]
    ) -> float:
        """Calculate optimal entry price based on technical analysis"""
        if signal == "HOLD":
            return current_price
        
        entry_price = current_price
        
        # Adjust entry based on technical indicators
        if signal == "BUY":
            # For BUY, look for entry below current price if overbought
            if technicals.get('rsi_signal') == 'overbought':
                entry_price = current_price * 0.99  # Wait for 1% dip
            elif technicals.get('bb_position') == 'upper':
                entry_price = current_price * 0.98  # Wait for pullback to middle
            elif technicals.get('price_vs_sma20', 0) > 2:
                entry_price = current_price * 0.99  # Wait for minor pullback
                
        elif signal == "SELL":
            # For SELL, look for entry above current price if oversold
            if technicals.get('rsi_signal') == 'oversold':
                entry_price = current_price * 1.01  # Wait for 1% bounce
            elif technicals.get('bb_position') == 'lower':
                entry_price = current_price * 1.02  # Wait for bounce to middle
            elif technicals.get('price_vs_sma20', 0) < -2:
                entry_price = current_price * 1.01  # Wait for minor bounce
        
        return entry_price
    
    def _calculate_stop_loss(
        self, 
        signal: str, 
        entry_price: float, 
        technicals: Dict[str, Any], 
        sr_levels: Dict[str, Any]
    ) -> float:
        """Calculate stop loss with better risk management"""
        if signal == "HOLD":
            return None
            
        # Calculate percentage-based stop loss as fallback
        base_stop_pct = 0.025  # 2.5% base stop loss
        
        if signal == "BUY":
            # For BUY, stop loss should be below support or recent low
            support = sr_levels.get('support')
            bb_lower = technicals.get('bb_lower')
            sma_20 = technicals.get('sma_20')
            
            # Multiple stop loss options
            stop_options = []
            
            # Option 1: Support-based with buffer
            if support and support > 0:
                stop_options.append(support * 0.985)  # 1.5% below support
            
            # Option 2: Bollinger Band lower
            if bb_lower and bb_lower > 0:
                stop_options.append(bb_lower * 0.99)  # 1% below BB lower
            
            # Option 3: SMA-based
            if sma_20 and sma_20 > 0:
                stop_options.append(sma_20 * 0.98)  # 2% below SMA
            
            # Option 4: Percentage-based (wider for better risk-reward)
            stop_options.append(entry_price * (1 - base_stop_pct))
            
            # Choose the most reasonable stop loss (not too tight, not too loose)
            valid_stops = [s for s in stop_options if s > 0 and s < entry_price]
            if valid_stops:
                # Prefer stops that give reasonable room (1.5% - 4% risk)
                preferred_stops = []
                for s in valid_stops:
                    risk_pct = (entry_price - s) / entry_price
                    if 0.015 <= risk_pct <= 0.04:  # 1.5% to 4% risk
                        preferred_stops.append(s)
                
                if preferred_stops:
                    stop_loss = max(preferred_stops)  # Highest (closest) preferred stop
                else:
                    stop_loss = max(valid_stops)  # Highest valid stop
            else:
                stop_loss = entry_price * (1 - base_stop_pct)
                    
        else:  # SELL
            # For SELL, stop loss should be above resistance or recent high
            resistance = sr_levels.get('resistance')
            bb_upper = technicals.get('bb_upper')
            sma_20 = technicals.get('sma_20')
            
            # Multiple stop loss options
            stop_options = []
            
            # Option 1: Resistance-based with buffer
            if resistance and resistance > 0:
                stop_options.append(resistance * 1.015)  # 1.5% above resistance
            
            # Option 2: Bollinger Band upper
            if bb_upper and bb_upper > 0:
                stop_options.append(bb_upper * 1.01)  # 1% above BB upper
            
            # Option 3: SMA-based
            if sma_20 and sma_20 > 0:
                stop_options.append(sma_20 * 1.02)  # 2% above SMA
            
            # Option 4: Percentage-based (wider for better risk-reward)
            stop_options.append(entry_price * (1 + base_stop_pct))
            
            # Choose the most reasonable stop loss
            valid_stops = [s for s in stop_options if s > 0 and s > entry_price]
            if valid_stops:
                # Prefer stops that give reasonable room (1.5% - 4% risk)
                preferred_stops = []
                for s in valid_stops:
                    risk_pct = (s - entry_price) / entry_price
                    if 0.015 <= risk_pct <= 0.04:  # 1.5% to 4% risk
                        preferred_stops.append(s)
                
                if preferred_stops:
                    stop_loss = min(preferred_stops)  # Lowest (closest) preferred stop
                else:
                    stop_loss = min(valid_stops)  # Lowest valid stop
            else:
                stop_loss = entry_price * (1 + base_stop_pct)
        
        return stop_loss
    
    def _calculate_exit_price(
        self, 
        signal: str, 
        entry_price: float, 
        stop_loss: float, 
        technicals: Dict[str, Any], 
        sr_levels: Dict[str, Any],
        volatility: Optional[float]
    ) -> Tuple[float, str]:
        """Calculate exit price with better targets and estimate holding period"""
        if signal == "HOLD":
            return None, "N/A"
            
        # Calculate potential profit based on risk
        if signal == "BUY":
            risk = entry_price - stop_loss
            min_target = entry_price + (risk * self.risk_reward_ratio)  # Minimum 2:1
        else:  # SELL
            risk = stop_loss - entry_price
            min_target = entry_price - (risk * self.risk_reward_ratio)  # Minimum 2:1
        
        # Look for better technical targets
        potential_targets = []
        target_sources = []
        
        if signal == "BUY":
            resistance = sr_levels.get('resistance')
            bb_upper = technicals.get('bb_upper')
            
            # Target 1: Resistance level
            if resistance and resistance > entry_price:
                potential_targets.append(resistance)
                target_sources.append("resistance")
            
            # Target 2: Bollinger Band upper
            if bb_upper and bb_upper > entry_price:
                potential_targets.append(bb_upper)
                target_sources.append("bollinger_upper")
            
            # Target 3: Minimum risk-reward target
            potential_targets.append(min_target)
            target_sources.append("risk_reward")
            
            # Target 4: Extended target (3:1 ratio)
            extended_target = entry_price + (risk * 3.0)
            potential_targets.append(extended_target)
            target_sources.append("extended_3:1")
            
            # Choose the best target
            if potential_targets:
                # Prefer targets that give 2:1 to 3:1 risk-reward
                preferred_targets = []
                for i, target in enumerate(potential_targets):
                    reward = target - entry_price
                    rr_ratio = reward / risk if risk > 0 else 0
                    if 2.0 <= rr_ratio <= 3.5:  # Ideal range
                        preferred_targets.append((target, target_sources[i]))
                
                if preferred_targets:
                    # Choose the closest target in preferred range
                    exit_price, source = min(preferred_targets, key=lambda x: x[0])
                else:
                    # Choose the minimum acceptable target (2:1)
                    exit_price = min_target
                    source = "risk_reward"
            else:
                exit_price = min_target
                source = "risk_reward"
                
        else:  # SELL
            support = sr_levels.get('support')
            bb_lower = technicals.get('bb_lower')
            
            # Target 1: Support level
            if support and support < entry_price:
                potential_targets.append(support)
                target_sources.append("support")
            
            # Target 2: Bollinger Band lower
            if bb_lower and bb_lower < entry_price:
                potential_targets.append(bb_lower)
                target_sources.append("bollinger_lower")
            
            # Target 3: Minimum risk-reward target
            potential_targets.append(min_target)
            target_sources.append("risk_reward")
            
            # Target 4: Extended target (3:1 ratio)
            extended_target = entry_price - (risk * 3.0)
            potential_targets.append(extended_target)
            target_sources.append("extended_3:1")
            
            # Choose the best target
            if potential_targets:
                # Prefer targets that give 2:1 to 3:1 risk-reward
                preferred_targets = []
                for i, target in enumerate(potential_targets):
                    reward = entry_price - target
                    rr_ratio = reward / risk if risk > 0 else 0
                    if 2.0 <= rr_ratio <= 3.5:  # Ideal range
                        preferred_targets.append((target, target_sources[i]))
                
                if preferred_targets:
                    # Choose the closest target in preferred range
                    exit_price, source = max(preferred_targets, key=lambda x: x[0])
                else:
                    # Choose the minimum acceptable target (2:1)
                    exit_price = min_target
                    source = "risk_reward"
            else:
                exit_price = min_target
                source = "risk_reward"
        
        # Adjust for volatility if provided
        if volatility:
            if signal == "BUY":
                exit_price = exit_price * (1 + volatility * 0.3)  # Slight adjustment for volatility
            else:
                exit_price = exit_price * (1 - volatility * 0.3)
        
        # Estimate holding period based on target distance and volatility
        holding_period = self._estimate_holding_period(
            entry_price, exit_price, volatility, signal, source
        )
        
        return exit_price, holding_period
    
    def _estimate_holding_period(
        self, 
        entry_price: float, 
        exit_price: float, 
        volatility: Optional[float], 
        signal: str, 
        target_source: str
    ) -> str:
        """Estimate holding period based on target distance and market conditions"""
        
        # Calculate target distance percentage
        if signal == "BUY":
            target_distance_pct = ((exit_price - entry_price) / entry_price) * 100
        else:  # SELL
            target_distance_pct = ((entry_price - exit_price) / entry_price) * 100
        
        # Base holding period calculation
        if volatility:
            # Adjust for volatility - higher volatility = faster moves
            volatility_factor = min(max(volatility * 100, 0.5), 3.0)  # Normalize to 0.5-3.0
        else:
            volatility_factor = 1.5  # Default assumption
        
        # Calculate base days needed
        base_days = (target_distance_pct / volatility_factor) * 2  # 2% per day adjusted for volatility
        
        # Adjust based on target source
        source_adjustments = {
            "resistance": 0.8,      # Resistance targets are usually faster
            "support": 0.8,         # Support targets are usually faster
            "bollinger_upper": 1.2,  # BB targets take longer
            "bollinger_lower": 1.2,  # BB targets take longer
            "risk_reward": 1.0,      # Standard calculation
            "extended_3:1": 1.5      # Extended targets take longer
        }
        
        adjustment = source_adjustments.get(target_source, 1.0)
        estimated_days = base_days * adjustment
        
        # Convert to human-readable format
        if estimated_days < 1:
            return "Intraday"
        elif estimated_days <= 2:
            return "1-2 days"
        elif estimated_days <= 5:
            return "3-5 days"
        elif estimated_days <= 10:
            return "1-2 weeks"
        elif estimated_days <= 20:
            return "2-3 weeks"
        else:
            return "3+ weeks"
    
    def _validate_risk_reward(
        self, 
        signal: str, 
        entry_price: float, 
        stop_loss: float, 
        exit_price: float, 
        current_price: float
    ) -> Dict[str, Any]:
        """Validate and adjust prices for proper risk-reward ratio"""
        if signal == "HOLD":
            return {
                'entry_price': entry_price,
                'stop_loss': None,
                'exit_price': None,
                'validated': True
            }
        
        # Ensure proper ordering
        if signal == "BUY":
            # BUY: stop_loss < entry < exit_price
            if stop_loss >= entry_price:
                stop_loss = entry_price * 0.97
            if exit_price <= entry_price:
                # Ensure minimum risk-reward ratio
                risk = entry_price - stop_loss
                exit_price = entry_price + (risk * self.risk_reward_ratio)
                
        else:  # SELL
            # SELL: exit_price < entry < stop_loss
            if stop_loss <= entry_price:
                stop_loss = entry_price * 1.03
            if exit_price >= entry_price:
                # Ensure minimum risk-reward ratio
                risk = stop_loss - entry_price
                exit_price = entry_price - (risk * self.risk_reward_ratio)
        
        # Ensure prices are realistic (within 10% of current price)
        max_distance = 0.10  # 10%
        
        if abs(entry_price - current_price) / current_price > max_distance:
            entry_price = current_price
            
        if signal == "BUY":
            if (entry_price - stop_loss) / entry_price > 0.05:  # Max 5% risk
                stop_loss = entry_price * 0.95
            if (exit_price - entry_price) / entry_price > 0.08:  # Max 8% target
                exit_price = entry_price * 1.08
        else:
            if (stop_loss - entry_price) / entry_price > 0.05:  # Max 5% risk
                stop_loss = entry_price * 1.05
            if (entry_price - exit_price) / entry_price > 0.08:  # Max 8% target
                exit_price = entry_price * 0.92
        
        return {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'exit_price': exit_price,
            'validated': True
        }
    
    def _calculate_risk_reward_ratio(
        self, 
        signal: str, 
        entry_price: float, 
        stop_loss: float, 
        exit_price: float
    ) -> float:
        """Calculate risk-reward ratio"""
        if signal == "HOLD" or not stop_loss or not exit_price:
            return 0.0
            
        if signal == "BUY":
            risk = entry_price - stop_loss
            reward = exit_price - entry_price
        else:  # SELL
            risk = stop_loss - entry_price
            reward = entry_price - exit_price
        
        return reward / risk if risk > 0 else 0.0
    
    def _calculate_confidence(
        self, 
        technicals: Dict[str, Any], 
        sr_levels: Dict[str, Any]
    ) -> float:
        """Calculate confidence level based on technical analysis strength"""
        confidence = 0.5  # Base confidence
        
        # Add confidence for clear technical signals
        if technicals.get('rsi_signal') in ['overbought', 'oversold']:
            confidence += 0.1
        
        if technicals.get('macd_histogram', 0) != 0:
            confidence += 0.1
        
        if sr_levels.get('support') or sr_levels.get('resistance'):
            confidence += 0.15
        
        if technicals.get('bb_position') in ['upper', 'lower']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_bollinger_position(self, price: float, lower: float, upper: float) -> str:
        """Determine position relative to Bollinger Bands"""
        if not lower or not upper:
            return 'middle'
        
        if price >= upper * 0.98:
            return 'upper'
        elif price <= lower * 1.02:
            return 'lower'
        else:
            return 'middle'
    
    def _fallback_calculation(self, signal: str, current_price: float) -> Dict[str, Any]:
        """Fallback to simple percentage-based calculation"""
        if signal == "BUY":
            return {
                'entry_price': current_price,
                'stop_loss': current_price * 0.97,
                'exit_price': current_price * 1.03,
                'holding_period': "1-2 days",
                'validated': True,
                'analysis': {
                    'method': 'fallback_simple_percentage',
                    'confidence': 0.3,
                    'risk_reward_ratio': 1.0
                }
            }
        elif signal == "SELL":
            return {
                'entry_price': current_price,
                'stop_loss': current_price * 1.03,
                'exit_price': current_price * 0.97,
                'holding_period': "1-2 days",
                'validated': True,
                'analysis': {
                    'method': 'fallback_simple_percentage',
                    'confidence': 0.3,
                    'risk_reward_ratio': 1.0
                }
            }
        else:
            return {
                'entry_price': current_price,
                'stop_loss': None,
                'exit_price': None,
                'holding_period': "N/A",
                'validated': True,
                'analysis': {
                    'method': 'hold_no_action',
                    'confidence': 0.5,
                    'risk_reward_ratio': 0.0
                }
            }

# Global instance
chart_calculator = ChartBasedEntryExitCalculator()
