"""
Advanced Trading Recommendation Engine
Real-time trading signals with buy/sell/hold recommendations
Multi-factor analysis with confidence scoring and risk management
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
import logging
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from enum import Enum
import uuid

# Import options trading AI for integrated recommendations
from services.options_trading_ai import OptionsTradingAI, OptionsStrategy, OptionsType

logger = logging.getLogger(__name__)

class TradingSignal(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class SignalStrength(str, Enum):
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class TradingRecommendationEngine:
    def __init__(self):
        # Recommendation cache
        self.recommendation_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Active recommendations
        self.active_recommendations = {}
        
        # Initialize options trading AI
        self.options_trading_ai = OptionsTradingAI()
        
        # Signal weights for different analysis types
        self.signal_weights = {
            "technical_analysis": 0.25,
            "volume_analysis": 0.20,
            "pattern_recognition": 0.20,
            "momentum_indicators": 0.15,
            "trend_analysis": 0.10,
            "market_sentiment": 0.10
        }
        
        # Risk management parameters
        self.risk_parameters = {
            "max_position_size": 0.1,  # 10% of portfolio
            "stop_loss_percentage": 0.02,  # 2% stop loss
            "take_profit_ratio": 2.0,  # 1:2 risk-reward ratio
            "max_drawdown": 0.05  # 5% max drawdown
        }
        
        # Recommendation templates
        self.recommendation_templates = self._initialize_recommendation_templates()
        
        # Historical performance tracking
        self.performance_tracking = {}
    
    def _initialize_recommendation_templates(self) -> Dict[str, Any]:
        """Initialize trading recommendation templates"""
        return {
            "strong_buy": {
                "name": "Strong Buy",
                "description": "Multiple confirmations suggest strong bullish momentum",
                "confidence_threshold": 0.8,
                "risk_level": RiskLevel.MEDIUM,
                "position_sizing": "aggressive",
                "time_horizon": "short_to_medium",
                "key_indicators": [
                    "Bullish pattern confirmation",
                    "High volume breakout",
                    "Strong momentum indicators",
                    "Positive market sentiment"
                ]
            },
            "buy": {
                "name": "Buy",
                "description": "Positive signals suggest bullish bias",
                "confidence_threshold": 0.6,
                "risk_level": RiskLevel.MEDIUM,
                "position_sizing": "moderate",
                "time_horizon": "medium",
                "key_indicators": [
                    "Bullish technical setup",
                    "Volume confirmation",
                    "Support level bounce",
                    "Positive momentum"
                ]
            },
            "hold": {
                "name": "Hold",
                "description": "Mixed signals suggest waiting for clarity",
                "confidence_threshold": 0.4,
                "risk_level": RiskLevel.LOW,
                "position_sizing": "conservative",
                "time_horizon": "short",
                "key_indicators": [
                    "Indecision patterns",
                    "Low volume",
                    "Sideways movement",
                    "Mixed signals"
                ]
            },
            "sell": {
                "name": "Sell",
                "description": "Negative signals suggest bearish bias",
                "confidence_threshold": 0.6,
                "risk_level": RiskLevel.MEDIUM,
                "position_sizing": "moderate",
                "time_horizon": "medium",
                "key_indicators": [
                    "Bearish technical setup",
                    "Volume confirmation",
                    "Resistance rejection",
                    "Negative momentum"
                ]
            },
            "strong_sell": {
                "name": "Strong Sell",
                "description": "Multiple confirmations suggest strong bearish momentum",
                "confidence_threshold": 0.8,
                "risk_level": RiskLevel.HIGH,
                "position_sizing": "aggressive",
                "time_horizon": "short_to_medium",
                "key_indicators": [
                    "Bearish pattern confirmation",
                    "High volume breakdown",
                    "Strong negative momentum",
                    "Negative market sentiment"
                ]
            }
        }
    
    async def generate_trading_recommendation(
        self,
        symbol: str,
        timeframe: str,
        analysis_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive trading recommendation"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}_{hash(str(analysis_data))}"
            if cache_key in self.recommendation_cache:
                cached_data, timestamp = self.recommendation_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Generate recommendation ID
            recommendation_id = f"rec_{symbol}_{uuid.uuid4().hex[:8]}"
            
            # Analyze different factors
            technical_score = await self._analyze_technical_factors(analysis_data)
            volume_score = await self._analyze_volume_factors(analysis_data)
            pattern_score = await self._analyze_pattern_factors(analysis_data)
            momentum_score = await self._analyze_momentum_factors(analysis_data)
            trend_score = await self._analyze_trend_factors(analysis_data)
            sentiment_score = await self._analyze_sentiment_factors(analysis_data)
            
            # Calculate weighted composite score
            composite_score = (
                technical_score * self.signal_weights["technical_analysis"] +
                volume_score * self.signal_weights["volume_analysis"] +
                pattern_score * self.signal_weights["pattern_recognition"] +
                momentum_score * self.signal_weights["momentum_indicators"] +
                trend_score * self.signal_weights["trend_analysis"] +
                sentiment_score * self.signal_weights["market_sentiment"]
            )
            
            # Determine trading signal
            trading_signal = await self._determine_trading_signal(composite_score)
            
            # Calculate confidence
            confidence = await self._calculate_confidence(
                technical_score, volume_score, pattern_score, 
                momentum_score, trend_score, sentiment_score
            )
            
            # Generate price targets and risk management
            price_targets = await self._calculate_price_targets(symbol, analysis_data, trading_signal)
            risk_management = await self._calculate_risk_management(symbol, analysis_data, trading_signal)
            
            # Generate reasoning
            reasoning = await self._generate_reasoning(
                technical_score, volume_score, pattern_score,
                momentum_score, trend_score, sentiment_score,
                trading_signal
            )
            
            # Create recommendation
            recommendation = {
                "id": recommendation_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "generated_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=24),
                
                # Core recommendation
                "trading_signal": trading_signal,
                "confidence": confidence,
                "signal_strength": self._classify_signal_strength(confidence),
                
                # Analysis scores
                "analysis_scores": {
                    "technical": technical_score,
                    "volume": volume_score,
                    "pattern": pattern_score,
                    "momentum": momentum_score,
                    "trend": trend_score,
                    "sentiment": sentiment_score,
                    "composite": composite_score
                },
                
                # Price targets and risk management
                "price_targets": price_targets,
                "risk_management": risk_management,
                
                # Reasoning and insights
                "reasoning": reasoning,
                "key_levels": await self._identify_key_levels(analysis_data),
                "market_context": await self._analyze_market_context(analysis_data),
                
                # Additional information
                "time_horizon": await self._determine_time_horizon(trading_signal),
                "risk_level": await self._assess_risk_level(trading_signal, confidence),
                "position_sizing": await self._recommend_position_sizing(trading_signal, confidence),
                
                # Educational content
                "educational_content": await self._generate_educational_content(trading_signal, analysis_data),
                
                # Performance tracking
                "tracking_id": recommendation_id,
                "is_active": True
            }
            
            # Store recommendation
            self.active_recommendations[recommendation_id] = recommendation
            
            # Cache results
            self.recommendation_cache[cache_key] = (recommendation, datetime.now().timestamp())
            
            logger.info(f"Trading recommendation generated for {symbol}: {trading_signal}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating trading recommendation: {e}")
            return {"error": str(e)}
    
    async def _analyze_technical_factors(self, analysis_data: Dict[str, Any]) -> float:
        """Analyze technical indicators and patterns"""
        try:
            technical_score = 0.0
            
            # Get technical indicators data
            technical_indicators = analysis_data.get("technical_indicators", {})
            
            # RSI analysis
            rsi_data = technical_indicators.get("rsi", {})
            if rsi_data:
                rsi_value = rsi_data.get("value", 50)
                if rsi_value < 30:
                    technical_score += 0.3  # Oversold, bullish
                elif rsi_value > 70:
                    technical_score -= 0.3  # Overbought, bearish
                elif 40 <= rsi_value <= 60:
                    technical_score += 0.1  # Neutral, slightly bullish
            
            # MACD analysis
            macd_data = technical_indicators.get("macd", {})
            if macd_data:
                macd_line = macd_data.get("macd", 0)
                signal_line = macd_data.get("signal", 0)
                histogram = macd_data.get("histogram", 0)
                
                if macd_line > signal_line and histogram > 0:
                    technical_score += 0.2  # Bullish MACD
                elif macd_line < signal_line and histogram < 0:
                    technical_score -= 0.2  # Bearish MACD
            
            # Moving averages
            sma_data = technical_indicators.get("sma", {})
            if sma_data:
                sma_20 = sma_data.get("20", 0)
                sma_50 = sma_data.get("50", 0)
                current_price = analysis_data.get("current_price", 0)
                
                if current_price > sma_20 > sma_50:
                    technical_score += 0.2  # Bullish MA alignment
                elif current_price < sma_20 < sma_50:
                    technical_score -= 0.2  # Bearish MA alignment
            
            # Bollinger Bands
            bb_data = technical_indicators.get("bollinger_bands", {})
            if bb_data:
                current_price = analysis_data.get("current_price", 0)
                upper_band = bb_data.get("upper", 0)
                lower_band = bb_data.get("lower", 0)
                
                if current_price <= lower_band:
                    technical_score += 0.2  # Oversold, bullish
                elif current_price >= upper_band:
                    technical_score -= 0.2  # Overbought, bearish
            
            return max(-1.0, min(1.0, technical_score))
            
        except Exception as e:
            logger.error(f"Error analyzing technical factors: {e}")
            return 0.0
    
    async def _analyze_volume_factors(self, analysis_data: Dict[str, Any]) -> float:
        """Analyze volume-based signals"""
        try:
            volume_score = 0.0
            
            # Get volume analysis data
            volume_analysis = analysis_data.get("volume_analysis", {})
            
            # Volume confirmation
            correlation_analysis = volume_analysis.get("correlation_analysis", {})
            overall_correlation = correlation_analysis.get("correlations", {}).get("overall", 0)
            
            if overall_correlation > 0.3:
                volume_score += 0.3  # Strong positive correlation
            elif overall_correlation < -0.3:
                volume_score -= 0.3  # Strong negative correlation
            
            # Volume breakout analysis
            breakout_analysis = volume_analysis.get("breakout_analysis", {})
            recent_breakouts = breakout_analysis.get("recent_breakouts", [])
            
            for breakout in recent_breakouts:
                if breakout.get("volume_confirmation", False):
                    price_change = breakout.get("price_change", 0)
                    if price_change > 0.02:
                        volume_score += 0.2  # Bullish volume breakout
                    elif price_change < -0.02:
                        volume_score -= 0.2  # Bearish volume breakout
            
            # Volume divergence
            divergence_analysis = volume_analysis.get("divergence_analysis", {})
            bullish_divergences = divergence_analysis.get("bullish_divergences", [])
            bearish_divergences = divergence_analysis.get("bearish_divergences", [])
            
            if bullish_divergences:
                volume_score += 0.3  # Bullish divergence
            elif bearish_divergences:
                volume_score -= 0.3  # Bearish divergence
            
            # Institutional flow
            institutional_analysis = volume_analysis.get("institutional_analysis", {})
            institutional_flow = institutional_analysis.get("flow_trend", "neutral")
            
            if institutional_flow == "bullish":
                volume_score += 0.2
            elif institutional_flow == "bearish":
                volume_score -= 0.2
            
            return max(-1.0, min(1.0, volume_score))
            
        except Exception as e:
            logger.error(f"Error analyzing volume factors: {e}")
            return 0.0
    
    async def _analyze_pattern_factors(self, analysis_data: Dict[str, Any]) -> float:
        """Analyze candlestick pattern signals"""
        try:
            pattern_score = 0.0
            
            # Get pattern recognition data
            pattern_data = analysis_data.get("pattern_recognition", {})
            detected_patterns = pattern_data.get("detected_patterns", [])
            
            for pattern in detected_patterns:
                pattern_type = pattern.get("pattern_type", "")
                confidence = pattern.get("confidence", 0)
                bullish_bearish = pattern.get("bullish_bearish", "neutral")
                
                # Weight pattern score by confidence
                pattern_weight = confidence * 0.3
                
                if bullish_bearish == "bullish":
                    pattern_score += pattern_weight
                elif bullish_bearish == "bearish":
                    pattern_score -= pattern_weight
            
            # Pattern success rates
            for pattern in detected_patterns:
                success_rate = pattern.get("success_rate", 0.5)
                pattern_type = pattern.get("pattern_type", "")
                
                # Adjust score based on historical success rate
                if success_rate > 0.7:
                    pattern_score *= 1.2  # Boost high-success patterns
                elif success_rate < 0.5:
                    pattern_score *= 0.8  # Reduce low-success patterns
            
            return max(-1.0, min(1.0, pattern_score))
            
        except Exception as e:
            logger.error(f"Error analyzing pattern factors: {e}")
            return 0.0
    
    async def _analyze_momentum_factors(self, analysis_data: Dict[str, Any]) -> float:
        """Analyze momentum indicators"""
        try:
            momentum_score = 0.0
            
            # Get momentum indicators
            momentum_indicators = analysis_data.get("momentum_indicators", {})
            
            # Stochastic oscillator
            stoch_data = momentum_indicators.get("stochastic", {})
            if stoch_data:
                stoch_k = stoch_data.get("k", 50)
                stoch_d = stoch_data.get("d", 50)
                
                if stoch_k < 20 and stoch_d < 20:
                    momentum_score += 0.2  # Oversold, bullish
                elif stoch_k > 80 and stoch_d > 80:
                    momentum_score -= 0.2  # Overbought, bearish
            
            # Williams %R
            williams_r = momentum_indicators.get("williams_r", 50)
            if williams_r < -80:
                momentum_score += 0.2  # Oversold, bullish
            elif williams_r > -20:
                momentum_score -= 0.2  # Overbought, bearish
            
            # CCI (Commodity Channel Index)
            cci = momentum_indicators.get("cci", 0)
            if cci < -100:
                momentum_score += 0.2  # Oversold, bullish
            elif cci > 100:
                momentum_score -= 0.2  # Overbought, bearish
            
            # Rate of Change
            roc = momentum_indicators.get("roc", 0)
            if roc > 0.05:  # 5% positive change
                momentum_score += 0.2
            elif roc < -0.05:  # 5% negative change
                momentum_score -= 0.2
            
            return max(-1.0, min(1.0, momentum_score))
            
        except Exception as e:
            logger.error(f"Error analyzing momentum factors: {e}")
            return 0.0
    
    async def _analyze_trend_factors(self, analysis_data: Dict[str, Any]) -> float:
        """Analyze trend direction and strength"""
        try:
            trend_score = 0.0
            
            # Get trend analysis data
            trend_data = analysis_data.get("trend_analysis", {})
            
            # Trend direction
            trend_direction = trend_data.get("direction", "sideways")
            trend_strength = trend_data.get("strength", 0.5)
            
            if trend_direction == "uptrend":
                trend_score += trend_strength * 0.4
            elif trend_direction == "downtrend":
                trend_score -= trend_strength * 0.4
            
            # Moving average trends
            ma_trend = trend_data.get("ma_trend", "neutral")
            if ma_trend == "bullish":
                trend_score += 0.3
            elif ma_trend == "bearish":
                trend_score -= 0.3
            
            # Trend line analysis
            trend_lines = trend_data.get("trend_lines", [])
            for line in trend_lines:
                line_type = line.get("type", "")
                line_strength = line.get("strength", 0.5)
                
                if line_type == "support":
                    trend_score += line_strength * 0.2
                elif line_type == "resistance":
                    trend_score -= line_strength * 0.2
            
            return max(-1.0, min(1.0, trend_score))
            
        except Exception as e:
            logger.error(f"Error analyzing trend factors: {e}")
            return 0.0
    
    async def _analyze_sentiment_factors(self, analysis_data: Dict[str, Any]) -> float:
        """Analyze market sentiment"""
        try:
            sentiment_score = 0.0
            
            # Get sentiment analysis data
            sentiment_data = analysis_data.get("market_sentiment", {})
            
            # Overall sentiment
            overall_sentiment = sentiment_data.get("overall_sentiment", "neutral")
            sentiment_strength = sentiment_data.get("sentiment_score", 0)
            
            if overall_sentiment == "bullish":
                sentiment_score += abs(sentiment_strength) * 0.3
            elif overall_sentiment == "bearish":
                sentiment_score -= abs(sentiment_strength) * 0.3
            
            # Fear/Greed index
            fear_greed_index = sentiment_data.get("fear_greed_index", 50)
            if fear_greed_index > 70:
                sentiment_score -= 0.2  # Too greedy, bearish
            elif fear_greed_index < 30:
                sentiment_score += 0.2  # Too fearful, bullish
            
            # Market breadth
            market_breadth = sentiment_data.get("market_breadth", {})
            advance_decline_ratio = market_breadth.get("advance_decline_ratio", 1.0)
            
            if advance_decline_ratio > 1.2:
                sentiment_score += 0.2  # Bullish breadth
            elif advance_decline_ratio < 0.8:
                sentiment_score -= 0.2  # Bearish breadth
            
            return max(-1.0, min(1.0, sentiment_score))
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment factors: {e}")
            return 0.0
    
    async def _determine_trading_signal(self, composite_score: float) -> TradingSignal:
        """Determine trading signal based on composite score"""
        try:
            if composite_score >= 0.6:
                return TradingSignal.STRONG_BUY
            elif composite_score >= 0.2:
                return TradingSignal.BUY
            elif composite_score <= -0.6:
                return TradingSignal.STRONG_SELL
            elif composite_score <= -0.2:
                return TradingSignal.SELL
            else:
                return TradingSignal.HOLD
                
        except Exception as e:
            logger.error(f"Error determining trading signal: {e}")
            return TradingSignal.HOLD
    
    async def _calculate_confidence(
        self,
        technical_score: float,
        volume_score: float,
        pattern_score: float,
        momentum_score: float,
        trend_score: float,
        sentiment_score: float
    ) -> float:
        """Calculate confidence in the recommendation"""
        try:
            # Calculate score consistency
            scores = [technical_score, volume_score, pattern_score, momentum_score, trend_score, sentiment_score]
            
            # Remove zero scores for consistency calculation
            non_zero_scores = [s for s in scores if s != 0]
            
            if len(non_zero_scores) < 3:
                return 0.3  # Low confidence with few signals
            
            # Calculate consistency (how many scores agree in direction)
            positive_scores = sum(1 for s in non_zero_scores if s > 0)
            negative_scores = sum(1 for s in non_zero_scores if s < 0)
            
            consistency = max(positive_scores, negative_scores) / len(non_zero_scores)
            
            # Calculate signal strength
            avg_abs_score = sum(abs(s) for s in non_zero_scores) / len(non_zero_scores)
            
            # Combine consistency and strength
            confidence = (consistency * 0.6) + (avg_abs_score * 0.4)
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    async def _calculate_price_targets(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
        trading_signal: TradingSignal
    ) -> Dict[str, Any]:
        """Calculate price targets and levels"""
        try:
            current_price = analysis_data.get("current_price", 100.0)
            
            price_targets = {
                "current_price": current_price,
                "target_price": current_price,
                "stop_loss": current_price,
                "risk_reward_ratio": 1.0
            }
            
            # Get key levels
            key_levels = await self._identify_key_levels(analysis_data)
            support_levels = key_levels.get("support_levels", [])
            resistance_levels = key_levels.get("resistance_levels", [])
            
            if trading_signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]:
                # Calculate bullish targets
                if resistance_levels:
                    target_price = min(resistance_levels)  # Nearest resistance
                else:
                    target_price = current_price * 1.05  # 5% target
                
                if support_levels:
                    stop_loss = max(support_levels)  # Nearest support
                else:
                    stop_loss = current_price * 0.98  # 2% stop loss
                
                price_targets["target_price"] = target_price
                price_targets["stop_loss"] = stop_loss
                
            elif trading_signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]:
                # Calculate bearish targets
                if support_levels:
                    target_price = max(support_levels)  # Nearest support
                else:
                    target_price = current_price * 0.95  # 5% target
                
                if resistance_levels:
                    stop_loss = min(resistance_levels)  # Nearest resistance
                else:
                    stop_loss = current_price * 1.02  # 2% stop loss
                
                price_targets["target_price"] = target_price
                price_targets["stop_loss"] = stop_loss
            
            # Calculate risk-reward ratio
            if trading_signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]:
                risk = current_price - price_targets["stop_loss"]
                reward = price_targets["target_price"] - current_price
            elif trading_signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]:
                risk = price_targets["stop_loss"] - current_price
                reward = current_price - price_targets["target_price"]
            else:
                risk = reward = 0
            
            if risk > 0:
                price_targets["risk_reward_ratio"] = reward / risk
            
            return price_targets
            
        except Exception as e:
            logger.error(f"Error calculating price targets: {e}")
            return {}
    
    async def _calculate_risk_management(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
        trading_signal: TradingSignal
    ) -> Dict[str, Any]:
        """Calculate risk management parameters"""
        try:
            risk_management = {
                "position_size": 0.05,  # Default 5%
                "stop_loss_percentage": 0.02,  # 2%
                "take_profit_percentage": 0.04,  # 4%
                "max_drawdown": 0.05,  # 5%
                "risk_level": RiskLevel.MEDIUM
            }
            
            # Adjust position size based on signal strength
            if trading_signal in [TradingSignal.STRONG_BUY, TradingSignal.STRONG_SELL]:
                risk_management["position_size"] = 0.08  # 8% for strong signals
                risk_management["risk_level"] = RiskLevel.HIGH
            elif trading_signal in [TradingSignal.BUY, TradingSignal.SELL]:
                risk_management["position_size"] = 0.05  # 5% for regular signals
                risk_management["risk_level"] = RiskLevel.MEDIUM
            else:
                risk_management["position_size"] = 0.02  # 2% for hold
                risk_management["risk_level"] = RiskLevel.LOW
            
            # Adjust stop loss based on volatility
            volatility = analysis_data.get("volatility", 0.02)
            risk_management["stop_loss_percentage"] = max(0.01, volatility * 1.5)
            
            # Calculate take profit based on risk-reward ratio
            risk_reward_ratio = self.risk_parameters["take_profit_ratio"]
            risk_management["take_profit_percentage"] = risk_management["stop_loss_percentage"] * risk_reward_ratio
            
            return risk_management
            
        except Exception as e:
            logger.error(f"Error calculating risk management: {e}")
            return {}
    
    async def _generate_reasoning(
        self,
        technical_score: float,
        volume_score: float,
        pattern_score: float,
        momentum_score: float,
        trend_score: float,
        sentiment_score: float,
        trading_signal: TradingSignal
    ) -> List[str]:
        """Generate reasoning for the recommendation"""
        try:
            reasoning = []
            
            # Technical analysis reasoning
            if abs(technical_score) > 0.3:
                if technical_score > 0:
                    reasoning.append("Technical indicators show bullish momentum")
                else:
                    reasoning.append("Technical indicators show bearish momentum")
            
            # Volume analysis reasoning
            if abs(volume_score) > 0.3:
                if volume_score > 0:
                    reasoning.append("Volume confirms bullish price action")
                else:
                    reasoning.append("Volume confirms bearish price action")
            
            # Pattern recognition reasoning
            if abs(pattern_score) > 0.3:
                if pattern_score > 0:
                    reasoning.append("Bullish candlestick patterns detected")
                else:
                    reasoning.append("Bearish candlestick patterns detected")
            
            # Momentum reasoning
            if abs(momentum_score) > 0.3:
                if momentum_score > 0:
                    reasoning.append("Momentum indicators suggest upward pressure")
                else:
                    reasoning.append("Momentum indicators suggest downward pressure")
            
            # Trend reasoning
            if abs(trend_score) > 0.3:
                if trend_score > 0:
                    reasoning.append("Trend analysis supports bullish outlook")
                else:
                    reasoning.append("Trend analysis supports bearish outlook")
            
            # Sentiment reasoning
            if abs(sentiment_score) > 0.3:
                if sentiment_score > 0:
                    reasoning.append("Market sentiment is bullish")
                else:
                    reasoning.append("Market sentiment is bearish")
            
            # Add general reasoning if no specific factors
            if not reasoning:
                reasoning.append("Mixed signals suggest waiting for clearer direction")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return ["Analysis completed with mixed signals"]
    
    async def _identify_key_levels(self, analysis_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Identify key support and resistance levels"""
        try:
            key_levels = {
                "support_levels": [],
                "resistance_levels": [],
                "pivot_points": []
            }
            
            # Get price data
            price_data = analysis_data.get("price_data", [])
            if not price_data:
                return key_levels
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(price_data)
            
            # Find recent highs and lows
            recent_highs = df['high'].tail(20).tolist()
            recent_lows = df['low'].tail(20).tolist()
            
            # Identify resistance levels (recent highs)
            resistance_levels = []
            for i in range(1, len(recent_highs) - 1):
                if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]:
                    resistance_levels.append(recent_highs[i])
            
            # Identify support levels (recent lows)
            support_levels = []
            for i in range(1, len(recent_lows) - 1):
                if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i+1]:
                    support_levels.append(recent_lows[i])
            
            # Calculate pivot points
            current_price = df.iloc[-1]['close']
            high = df.iloc[-1]['high']
            low = df.iloc[-1]['low']
            
            pivot_point = (high + low + current_price) / 3
            resistance_1 = 2 * pivot_point - low
            support_1 = 2 * pivot_point - high
            resistance_2 = pivot_point + (high - low)
            support_2 = pivot_point - (high - low)
            
            # Debug logging
            logger.info(f"Key Levels Calculation - Current Price: {current_price}, High: {high}, Low: {low}")
            logger.info(f"Pivot Point: {pivot_point}, R1: {resistance_1}, S1: {support_1}")
            logger.info(f"Swing-based resistances found: {len(resistance_levels)}")
            logger.info(f"Swing-based supports found: {len(support_levels)}")
            
            # If no swing-based resistance levels found, use pivot-based calculations
            if not resistance_levels:
                resistance_levels = [resistance_1, resistance_2]
                logger.info("Using pivot-based resistance levels as fallback")
            
            # If no swing-based support levels found, use pivot-based calculations  
            if not support_levels:
                support_levels = [support_1, support_2]
                logger.info("Using pivot-based support levels as fallback")
            
            key_levels["support_levels"] = sorted(support_levels, reverse=True)[:3]  # Top 3
            key_levels["resistance_levels"] = sorted(resistance_levels)[:3]  # Top 3
            key_levels["pivot_points"] = [pivot_point, support_1, support_2, resistance_1, resistance_2]
            
            return key_levels
            
        except Exception as e:
            logger.error(f"Error identifying key levels: {e}")
            return {"support_levels": [], "resistance_levels": [], "pivot_points": []}
    
    async def _analyze_market_context(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze broader market context"""
        try:
            market_context = {
                "market_phase": "unknown",
                "volatility_regime": "normal",
                "trend_strength": "moderate",
                "market_structure": "balanced"
            }
            
            # Analyze volatility
            volatility = analysis_data.get("volatility", 0.02)
            if volatility > 0.03:
                market_context["volatility_regime"] = "high"
            elif volatility < 0.01:
                market_context["volatility_regime"] = "low"
            
            # Analyze trend strength
            trend_data = analysis_data.get("trend_analysis", {})
            trend_strength = trend_data.get("strength", 0.5)
            
            if trend_strength > 0.7:
                market_context["trend_strength"] = "strong"
            elif trend_strength < 0.3:
                market_context["trend_strength"] = "weak"
            
            # Determine market phase
            sentiment_data = analysis_data.get("market_sentiment", {})
            fear_greed_index = sentiment_data.get("fear_greed_index", 50)
            
            if fear_greed_index > 80:
                market_context["market_phase"] = "euphoria"
            elif fear_greed_index < 20:
                market_context["market_phase"] = "panic"
            elif 30 <= fear_greed_index <= 70:
                market_context["market_phase"] = "normal"
            
            return market_context
            
        except Exception as e:
            logger.error(f"Error analyzing market context: {e}")
            return {}
    
    async def _determine_time_horizon(self, trading_signal: TradingSignal) -> str:
        """Determine recommended time horizon"""
        try:
            if trading_signal in [TradingSignal.STRONG_BUY, TradingSignal.STRONG_SELL]:
                return "short_to_medium"  # 1-4 weeks
            elif trading_signal in [TradingSignal.BUY, TradingSignal.SELL]:
                return "medium"  # 2-8 weeks
            else:
                return "short"  # 1-2 weeks
                
        except Exception as e:
            logger.error(f"Error determining time horizon: {e}")
            return "short"
    
    async def _assess_risk_level(self, trading_signal: TradingSignal, confidence: float) -> RiskLevel:
        """Assess risk level for the recommendation"""
        try:
            if trading_signal in [TradingSignal.STRONG_BUY, TradingSignal.STRONG_SELL]:
                if confidence > 0.8:
                    return RiskLevel.MEDIUM
                else:
                    return RiskLevel.HIGH
            elif trading_signal in [TradingSignal.BUY, TradingSignal.SELL]:
                if confidence > 0.7:
                    return RiskLevel.MEDIUM
                else:
                    return RiskLevel.HIGH
            else:
                return RiskLevel.LOW
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return RiskLevel.MEDIUM
    
    async def _recommend_position_sizing(self, trading_signal: TradingSignal, confidence: float) -> str:
        """Recommend position sizing strategy"""
        try:
            if trading_signal in [TradingSignal.STRONG_BUY, TradingSignal.STRONG_SELL]:
                if confidence > 0.8:
                    return "aggressive"
                else:
                    return "moderate"
            elif trading_signal in [TradingSignal.BUY, TradingSignal.SELL]:
                return "moderate"
            else:
                return "conservative"
                
        except Exception as e:
            logger.error(f"Error recommending position sizing: {e}")
            return "conservative"
    
    async def _generate_educational_content(
        self,
        trading_signal: TradingSignal,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate educational content for the recommendation"""
        try:
            template = self.recommendation_templates.get(trading_signal, {})
            
            educational_content = {
                "signal_explanation": template.get("description", ""),
                "key_indicators": template.get("key_indicators", []),
                "trading_tips": [],
                "risk_warnings": [],
                "learning_resources": []
            }
            
            # Add specific trading tips based on signal
            if trading_signal == TradingSignal.STRONG_BUY:
                educational_content["trading_tips"] = [
                    "Consider entering on pullbacks to support levels",
                    "Use trailing stops to protect profits",
                    "Monitor volume for confirmation",
                    "Consider scaling in positions"
                ]
            elif trading_signal == TradingSignal.STRONG_SELL:
                educational_content["trading_tips"] = [
                    "Consider entering on bounces to resistance levels",
                    "Use tight stops due to volatility",
                    "Monitor for reversal patterns",
                    "Consider short-term positions"
                ]
            
            # Add risk warnings
            educational_content["risk_warnings"] = [
                "Past performance does not guarantee future results",
                "Always use proper risk management",
                "Consider your risk tolerance before trading",
                "Monitor market conditions for changes"
            ]
            
            return educational_content
            
        except Exception as e:
            logger.error(f"Error generating educational content: {e}")
            return {}
    
    def _classify_signal_strength(self, confidence: float) -> SignalStrength:
        """Classify signal strength based on confidence"""
        if confidence >= 0.8:
            return SignalStrength.VERY_STRONG
        elif confidence >= 0.6:
            return SignalStrength.STRONG
        elif confidence >= 0.4:
            return SignalStrength.MODERATE
        elif confidence >= 0.2:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK
    
    async def get_recommendation_history(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical recommendations for symbol"""
        try:
            history = []
            
            for rec_id, recommendation in self.active_recommendations.items():
                if recommendation["symbol"] == symbol:
                    history.append(recommendation)
            
            # Sort by generation time
            history.sort(key=lambda x: x["generated_at"], reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recommendation history: {e}")
            return []
    
    async def update_recommendation_performance(self, recommendation_id: str, actual_outcome: str):
        """Update recommendation performance tracking"""
        try:
            if recommendation_id in self.active_recommendations:
                recommendation = self.active_recommendations[recommendation_id]
                
                # Calculate performance
                predicted_signal = recommendation["trading_signal"]
                performance_score = self._calculate_performance_score(predicted_signal, actual_outcome)
                
                # Update tracking
                if recommendation_id not in self.performance_tracking:
                    self.performance_tracking[recommendation_id] = {
                        "total_recommendations": 0,
                        "correct_predictions": 0,
                        "accuracy": 0.0
                    }
                
                tracking = self.performance_tracking[recommendation_id]
                tracking["total_recommendations"] += 1
                if performance_score > 0:
                    tracking["correct_predictions"] += 1
                
                tracking["accuracy"] = tracking["correct_predictions"] / tracking["total_recommendations"]
                
                logger.info(f"Updated performance for {recommendation_id}: {performance_score}")
                
        except Exception as e:
            logger.error(f"Error updating recommendation performance: {e}")
    
    def _calculate_performance_score(self, predicted: TradingSignal, actual: str) -> float:
        """Calculate performance score for recommendation"""
        try:
            # Convert actual outcome to signal
            if actual in ["strong_buy", "buy"]:
                actual_signal = TradingSignal.BUY
            elif actual in ["strong_sell", "sell"]:
                actual_signal = TradingSignal.SELL
            else:
                actual_signal = TradingSignal.HOLD
            
            # Calculate score
            if predicted == actual_signal:
                return 1.0  # Perfect match
            elif (predicted in [TradingSignal.BUY, TradingSignal.STRONG_BUY] and 
                  actual_signal in [TradingSignal.BUY, TradingSignal.STRONG_BUY]):
                return 0.8  # Partial match
            elif (predicted in [TradingSignal.SELL, TradingSignal.STRONG_SELL] and 
                  actual_signal in [TradingSignal.SELL, TradingSignal.STRONG_SELL]):
                return 0.8  # Partial match
            else:
                return 0.0  # No match
                
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        try:
            total_recommendations = sum(t["total_recommendations"] for t in self.performance_tracking.values())
            total_correct = sum(t["correct_predictions"] for t in self.performance_tracking.values())
            
            overall_accuracy = total_correct / total_recommendations if total_recommendations > 0 else 0
            
            return {
                "total_recommendations": total_recommendations,
                "correct_predictions": total_correct,
                "overall_accuracy": overall_accuracy,
                "performance_by_signal": self._get_performance_by_signal()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance statistics: {e}")
            return {}
    
    def _get_performance_by_signal(self) -> Dict[str, Any]:
        """Get performance statistics by signal type"""
        try:
            signal_performance = {}
            
            for signal in TradingSignal:
                signal_performance[signal] = {
                    "total": 0,
                    "correct": 0,
                    "accuracy": 0.0
                }
            
            # This would be populated from actual performance data
            return signal_performance
            
        except Exception as e:
            logger.error(f"Error getting performance by signal: {e}")
            return {}
    
    async def get_options_trading_suggestion(
        self,
        symbol: str,
        underlying_price: float,
        days_to_expiry: int = 30,
        option_type: OptionsType = OptionsType.CALL,
        risk_tolerance: str = "medium"
    ) -> Dict[str, Any]:
        """Generate comprehensive options trading suggestions"""
        try:
            # Get comprehensive options analysis
            options_analysis = await self.options_trading_ai.analyze_options_chain(
                symbol=symbol,
                underlying_price=underlying_price,
                days_to_expiry=days_to_expiry
            )
            
            if "error" in options_analysis:
                return {"error": options_analysis["error"]}
            
            # Get stock recommendation for context
            stock_recommendation = await self.generate_trading_recommendation(
                symbol=symbol,
                timeframe="1D",
                analysis_data={"price": underlying_price}
            )
            
            # Generate options-specific recommendations
            options_suggestions = await self._generate_options_suggestions(
                options_analysis, stock_recommendation, option_type, risk_tolerance
            )
            
            return {
                "symbol": symbol,
                "underlying_price": underlying_price,
                "days_to_expiry": days_to_expiry,
                "option_type": option_type,
                "risk_tolerance": risk_tolerance,
                "stock_recommendation": stock_recommendation,
                "options_analysis": options_analysis,
                "options_suggestions": options_suggestions,
                "timestamp": datetime.now().isoformat(),
                "message": f"Options trading suggestions generated for {symbol}"
            }
            
        except Exception as e:
            logger.error(f"Error generating options trading suggestions: {e}")
            return {"error": str(e)}

    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            return len(self.recommendation_templates) > 0 and self.options_trading_ai.is_available()
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear recommendation cache"""
        self.recommendation_cache.clear()
        logger.info("Trading recommendation cache cleared")
