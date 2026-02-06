"""
Advanced Volume-Price Analysis Service
Real-time volume analysis with price confirmation, divergence detection, and trading signals
Comprehensive volume profile analysis and institutional flow detection
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

logger = logging.getLogger(__name__)

class VolumeSignal(str, Enum):
    BULLISH_CONFIRMATION = "bullish_confirmation"
    BEARISH_CONFIRMATION = "bearish_confirmation"
    BULLISH_DIVERGENCE = "bullish_divergence"
    BEARISH_DIVERGENCE = "bearish_divergence"
    VOLUME_BREAKOUT = "volume_breakout"
    VOLUME_DECLINE = "volume_decline"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    NEUTRAL = "neutral"

class VolumeStrength(str, Enum):
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class VolumePriceAnalysisService:
    def __init__(self):
        # Volume analysis cache
        self.volume_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Volume profile storage
        self.volume_profiles = {}
        
        # Institutional flow tracking
        self.institutional_flows = {}
        
        # Volume indicators calculations
        self.volume_indicators = {}
        
        # Real-time volume monitoring
        self.active_monitoring = {}
        
        # Volume analysis templates
        self.analysis_templates = self._initialize_analysis_templates()
    
    def _initialize_analysis_templates(self) -> Dict[str, Any]:
        """Initialize volume analysis templates"""
        return {
            "volume_breakout": {
                "name": "Volume Breakout Analysis",
                "description": "Analyzing volume during price breakouts",
                "key_metrics": [
                    "volume_ratio",
                    "price_momentum",
                    "breakout_confirmation",
                    "volume_sustainability"
                ],
                "trading_implications": {
                    "high_volume_breakout": "Strong buy/sell signal",
                    "low_volume_breakout": "Weak signal, wait for confirmation",
                    "volume_fade": "Potential reversal signal"
                }
            },
            "volume_divergence": {
                "name": "Volume-Price Divergence",
                "description": "Detecting divergences between price and volume",
                "key_metrics": [
                    "price_trend",
                    "volume_trend",
                    "divergence_strength",
                    "reversal_probability"
                ],
                "trading_implications": {
                    "bullish_divergence": "Potential bullish reversal",
                    "bearish_divergence": "Potential bearish reversal",
                    "no_divergence": "Trend continuation likely"
                }
            },
            "accumulation_distribution": {
                "name": "Accumulation/Distribution Analysis",
                "description": "Identifying institutional accumulation or distribution",
                "key_metrics": [
                    "volume_price_trend",
                    "institutional_flow",
                    "smart_money_activity",
                    "retail_participation"
                ],
                "trading_implications": {
                    "accumulation": "Institutional buying, bullish",
                    "distribution": "Institutional selling, bearish",
                    "neutral": "Balanced activity"
                }
            },
            "volume_profile": {
                "name": "Volume Profile Analysis",
                "description": "Analyzing volume distribution at different price levels",
                "key_metrics": [
                    "point_of_control",
                    "value_area",
                    "volume_at_price",
                    "price_acceptance"
                ],
                "trading_implications": {
                    "high_volume_node": "Strong support/resistance",
                    "low_volume_node": "Weak support/resistance",
                    "value_area_break": "Significant move likely"
                }
            }
        }
    
    async def analyze_volume_price_relationship(
        self,
        symbol: str,
        timeframe: str,
        data: List[Dict[str, Any]],
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Comprehensive volume-price analysis"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}_{analysis_type}_{hash(str(data))}"
            if cache_key in self.volume_cache:
                cached_data, timestamp = self.volume_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            if len(df) < 10:
                return {"error": "Insufficient data for volume analysis"}
            
            # Perform comprehensive analysis
            analysis_results = {
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_timestamp": datetime.now(),
                "data_points": len(df),
                "analysis_type": analysis_type
            }
            
            # Basic volume metrics
            volume_metrics = await self._calculate_volume_metrics(df)
            analysis_results["volume_metrics"] = volume_metrics
            
            # Volume-price correlation
            correlation_analysis = await self._analyze_volume_price_correlation(df)
            analysis_results["correlation_analysis"] = correlation_analysis
            
            # Volume breakout analysis
            breakout_analysis = await self._analyze_volume_breakouts(df)
            analysis_results["breakout_analysis"] = breakout_analysis
            
            # Volume divergence analysis
            divergence_analysis = await self._analyze_volume_divergences(df)
            analysis_results["divergence_analysis"] = divergence_analysis
            
            # Accumulation/Distribution analysis
            accumulation_analysis = await self._analyze_accumulation_distribution(df)
            analysis_results["accumulation_analysis"] = accumulation_analysis
            
            # Volume profile analysis
            profile_analysis = await self._analyze_volume_profile(df)
            analysis_results["profile_analysis"] = profile_analysis
            
            # Institutional flow analysis
            institutional_analysis = await self._analyze_institutional_flows(df)
            analysis_results["institutional_analysis"] = institutional_analysis
            
            # Generate trading signals
            trading_signals = await self._generate_volume_trading_signals(analysis_results)
            analysis_results["trading_signals"] = trading_signals
            
            # Overall assessment
            overall_assessment = await self._generate_overall_assessment(analysis_results)
            analysis_results["overall_assessment"] = overall_assessment
            
            # Cache results
            self.volume_cache[cache_key] = (analysis_results, datetime.now().timestamp())
            
            logger.info(f"Volume analysis completed for {symbol}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing volume-price relationship: {e}")
            return {"error": str(e)}
    
    async def _calculate_volume_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic volume metrics"""
        try:
            if 'volume' not in df.columns:
                return {"error": "Volume data not available"}
            
            current_volume = df.iloc[-1]['volume']
            
            # Calculate various volume averages
            volume_5_avg = df['volume'].tail(5).mean()
            volume_10_avg = df['volume'].tail(10).mean()
            volume_20_avg = df['volume'].tail(20).mean()
            volume_50_avg = df['volume'].tail(50).mean() if len(df) >= 50 else df['volume'].mean()
            
            # Volume ratios
            volume_ratio_5 = current_volume / volume_5_avg if volume_5_avg > 0 else 1
            volume_ratio_10 = current_volume / volume_10_avg if volume_10_avg > 0 else 1
            volume_ratio_20 = current_volume / volume_20_avg if volume_20_avg > 0 else 1
            
            # Volume trend
            volume_trend = await self._calculate_volume_trend(df)
            
            # Volume volatility
            volume_volatility = df['volume'].std() / df['volume'].mean() if df['volume'].mean() > 0 else 0
            
            return {
                "current_volume": current_volume,
                "volume_averages": {
                    "5_period": volume_5_avg,
                    "10_period": volume_10_avg,
                    "20_period": volume_20_avg,
                    "50_period": volume_50_avg
                },
                "volume_ratios": {
                    "5_period": volume_ratio_5,
                    "10_period": volume_ratio_10,
                    "20_period": volume_ratio_20
                },
                "volume_trend": volume_trend,
                "volume_volatility": volume_volatility,
                "volume_strength": self._classify_volume_strength(volume_ratio_20)
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume metrics: {e}")
            return {}
    
    async def _analyze_volume_price_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlation between volume and price"""
        try:
            if 'volume' not in df.columns or 'close' not in df.columns:
                return {"error": "Required data not available"}
            
            # Calculate price changes
            df['price_change'] = df['close'].pct_change()
            df['volume_change'] = df['volume'].pct_change()
            
            # Remove NaN values
            df_clean = df.dropna()
            
            if len(df_clean) < 5:
                return {"error": "Insufficient data for correlation analysis"}
            
            # Calculate correlations
            correlation_5 = df_clean['price_change'].tail(5).corr(df_clean['volume_change'].tail(5))
            correlation_10 = df_clean['price_change'].tail(10).corr(df_clean['volume_change'].tail(10))
            correlation_20 = df_clean['price_change'].tail(20).corr(df_clean['volume_change'].tail(20))
            
            # Overall correlation
            overall_correlation = df_clean['price_change'].corr(df_clean['volume_change'])
            
            # Volume confirmation analysis
            confirmation_analysis = await self._analyze_volume_confirmation(df_clean)
            
            return {
                "correlations": {
                    "5_period": correlation_5,
                    "10_period": correlation_10,
                    "20_period": correlation_20,
                    "overall": overall_correlation
                },
                "confirmation_analysis": confirmation_analysis,
                "correlation_strength": self._classify_correlation_strength(overall_correlation),
                "interpretation": self._interpret_correlation(overall_correlation)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume-price correlation: {e}")
            return {}
    
    async def _analyze_volume_breakouts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume during price breakouts"""
        try:
            if 'volume' not in df.columns or 'close' not in df.columns:
                return {"error": "Required data not available"}
            
            breakout_analysis = {
                "recent_breakouts": [],
                "breakout_patterns": [],
                "volume_confirmation": {}
            }
            
            # Look for recent breakouts (last 10 periods)
            recent_data = df.tail(10)
            volume_20_avg = df['volume'].tail(20).mean()
            
            for i in range(1, len(recent_data)):
                current = recent_data.iloc[i]
                previous = recent_data.iloc[i-1]
                
                # Check for price breakout
                price_change = (current['close'] - previous['close']) / previous['close']
                volume_ratio = current['volume'] / volume_20_avg if volume_20_avg > 0 else 1
                
                # Significant breakout criteria
                if abs(price_change) > 0.02:  # 2% price move
                    breakout = {
                        "timestamp": current.get('time', f"period_{i}"),
                        "price_change": price_change,
                        "volume_ratio": volume_ratio,
                        "volume_confirmation": volume_ratio > 1.5,
                        "breakout_strength": self._calculate_breakout_strength(price_change, volume_ratio)
                    }
                    breakout_analysis["recent_breakouts"].append(breakout)
            
            # Analyze breakout patterns
            breakout_analysis["breakout_patterns"] = await self._identify_breakout_patterns(recent_data)
            
            # Volume confirmation summary
            breakout_analysis["volume_confirmation"] = await self._summarize_volume_confirmation(
                breakout_analysis["recent_breakouts"]
            )
            
            return breakout_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing volume breakouts: {e}")
            return {}
    
    async def _analyze_volume_divergences(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume-price divergences"""
        try:
            if 'volume' not in df.columns or 'close' not in df.columns:
                return {"error": "Required data not available"}
            
            divergence_analysis = {
                "bullish_divergences": [],
                "bearish_divergences": [],
                "divergence_strength": {},
                "reversal_probability": 0.0
            }
            
            # Look for divergences in last 20 periods
            lookback_data = df.tail(20)
            
            # Calculate price and volume trends
            price_trend = await self._calculate_trend(lookback_data['close'])
            volume_trend = await self._calculate_trend(lookback_data['volume'])
            
            # Detect divergences
            if price_trend < 0 and volume_trend > 0:
                # Bullish divergence: price down, volume up
                divergence_strength = abs(price_trend) + volume_trend
                divergence_analysis["bullish_divergences"].append({
                    "strength": divergence_strength,
                    "price_trend": price_trend,
                    "volume_trend": volume_trend,
                    "detected_at": datetime.now()
                })
                divergence_analysis["reversal_probability"] = min(0.8, divergence_strength * 0.1)
            
            elif price_trend > 0 and volume_trend < 0:
                # Bearish divergence: price up, volume down
                divergence_strength = price_trend + abs(volume_trend)
                divergence_analysis["bearish_divergences"].append({
                    "strength": divergence_strength,
                    "price_trend": price_trend,
                    "volume_trend": volume_trend,
                    "detected_at": datetime.now()
                })
                divergence_analysis["reversal_probability"] = min(0.8, divergence_strength * 0.1)
            
            # Classify divergence strength
            divergence_analysis["divergence_strength"] = self._classify_divergence_strength(
                len(divergence_analysis["bullish_divergences"]) + 
                len(divergence_analysis["bearish_divergences"])
            )
            
            return divergence_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing volume divergences: {e}")
            return {}
    
    async def _analyze_accumulation_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze accumulation and distribution patterns"""
        try:
            if 'volume' not in df.columns or 'close' not in df.columns or 'high' not in df.columns or 'low' not in df.columns:
                return {"error": "Required data not available"}
            
            accumulation_analysis = {
                "accumulation_score": 0.0,
                "distribution_score": 0.0,
                "institutional_flow": "neutral",
                "smart_money_activity": "low",
                "retail_participation": "normal"
            }
            
            # Calculate Accumulation/Distribution Line
            ad_line = await self._calculate_ad_line(df)
            
            # Analyze recent AD line trend
            recent_ad_trend = await self._calculate_trend(ad_line.tail(10))
            
            # Analyze volume patterns
            volume_patterns = await self._analyze_volume_patterns(df)
            
            # Determine accumulation vs distribution
            if recent_ad_trend > 0.1:
                accumulation_analysis["accumulation_score"] = min(1.0, recent_ad_trend * 2)
                accumulation_analysis["institutional_flow"] = "accumulation"
            elif recent_ad_trend < -0.1:
                accumulation_analysis["distribution_score"] = min(1.0, abs(recent_ad_trend) * 2)
                accumulation_analysis["institutional_flow"] = "distribution"
            
            # Analyze smart money activity
            accumulation_analysis["smart_money_activity"] = await self._analyze_smart_money_activity(df)
            
            # Analyze retail participation
            accumulation_analysis["retail_participation"] = await self._analyze_retail_participation(df)
            
            return accumulation_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing accumulation/distribution: {e}")
            return {}
    
    async def _analyze_volume_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume profile at different price levels"""
        try:
            if 'volume' not in df.columns or 'high' not in df.columns or 'low' not in df.columns:
                return {"error": "Required data not available"}
            
            profile_analysis = {
                "point_of_control": 0.0,
                "value_area_high": 0.0,
                "value_area_low": 0.0,
                "volume_nodes": [],
                "price_acceptance": {},
                "support_resistance_levels": []
            }
            
            # Create volume profile
            volume_profile = await self._create_volume_profile(df)
            
            if volume_profile:
                # Find Point of Control (POC)
                poc_price = max(volume_profile.keys(), key=lambda k: volume_profile[k])
                profile_analysis["point_of_control"] = poc_price
                
                # Calculate Value Area (70% of volume)
                total_volume = sum(volume_profile.values())
                value_area_volume = total_volume * 0.7
                
                # Sort prices by volume
                sorted_prices = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
                
                cumulative_volume = 0
                value_area_prices = []
                
                for price, volume in sorted_prices:
                    cumulative_volume += volume
                    value_area_prices.append(price)
                    if cumulative_volume >= value_area_volume:
                        break
                
                if value_area_prices:
                    profile_analysis["value_area_high"] = max(value_area_prices)
                    profile_analysis["value_area_low"] = min(value_area_prices)
                
                # Identify volume nodes
                profile_analysis["volume_nodes"] = await self._identify_volume_nodes(volume_profile)
                
                # Analyze price acceptance
                profile_analysis["price_acceptance"] = await self._analyze_price_acceptance(df, volume_profile)
                
                # Identify support/resistance levels
                profile_analysis["support_resistance_levels"] = await self._identify_support_resistance_levels(volume_profile)
            
            return profile_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing volume profile: {e}")
            return {}
    
    async def _analyze_institutional_flows(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze institutional money flows"""
        try:
            institutional_analysis = {
                "institutional_buying": 0.0,
                "institutional_selling": 0.0,
                "net_institutional_flow": 0.0,
                "flow_trend": "neutral",
                "institutional_sentiment": "neutral"
            }
            
            # Analyze large volume trades (proxy for institutional activity)
            large_volume_threshold = df['volume'].quantile(0.8)  # Top 20% of volume
            
            large_volume_data = df[df['volume'] >= large_volume_threshold]
            
            if len(large_volume_data) > 0:
                # Analyze price direction during large volume
                large_volume_up = large_volume_data[large_volume_data['close'] > large_volume_data['open']]
                large_volume_down = large_volume_data[large_volume_data['close'] < large_volume_data['open']]
                
                institutional_buying = len(large_volume_up) / len(large_volume_data)
                institutional_selling = len(large_volume_down) / len(large_volume_data)
                
                institutional_analysis["institutional_buying"] = institutional_buying
                institutional_analysis["institutional_selling"] = institutional_selling
                institutional_analysis["net_institutional_flow"] = institutional_buying - institutional_selling
                
                # Determine flow trend
                if institutional_analysis["net_institutional_flow"] > 0.2:
                    institutional_analysis["flow_trend"] = "bullish"
                    institutional_analysis["institutional_sentiment"] = "bullish"
                elif institutional_analysis["net_institutional_flow"] < -0.2:
                    institutional_analysis["flow_trend"] = "bearish"
                    institutional_analysis["institutional_sentiment"] = "bearish"
            
            return institutional_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing institutional flows: {e}")
            return {}
    
    async def _generate_volume_trading_signals(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on volume analysis"""
        try:
            trading_signals = {
                "primary_signal": VolumeSignal.NEUTRAL,
                "signal_strength": VolumeStrength.MODERATE,
                "confidence": 0.5,
                "reasoning": [],
                "entry_conditions": [],
                "exit_conditions": [],
                "risk_factors": []
            }
            
            # Analyze volume metrics
            volume_metrics = analysis_results.get("volume_metrics", {})
            volume_ratios = volume_metrics.get("volume_ratios", {})
            volume_strength = volume_metrics.get("volume_strength", "moderate")
            
            # Analyze correlation
            correlation_analysis = analysis_results.get("correlation_analysis", {})
            overall_correlation = correlation_analysis.get("correlations", {}).get("overall", 0)
            
            # Analyze breakouts
            breakout_analysis = analysis_results.get("breakout_analysis", {})
            recent_breakouts = breakout_analysis.get("recent_breakouts", [])
            
            # Analyze divergences
            divergence_analysis = analysis_results.get("divergence_analysis", {})
            bullish_divergences = divergence_analysis.get("bullish_divergences", [])
            bearish_divergences = divergence_analysis.get("bearish_divergences", [])
            
            # Analyze accumulation/distribution
            accumulation_analysis = analysis_results.get("accumulation_analysis", {})
            institutional_flow = accumulation_analysis.get("institutional_flow", "neutral")
            
            # Generate signals based on analysis
            signal_score = 0.0
            
            # Volume confirmation signals
            if volume_strength in ["strong", "very_strong"]:
                if overall_correlation > 0.3:
                    signal_score += 0.3
                    trading_signals["reasoning"].append("Strong volume with positive price correlation")
                elif overall_correlation < -0.3:
                    signal_score -= 0.3
                    trading_signals["reasoning"].append("Strong volume with negative price correlation")
            
            # Breakout signals
            for breakout in recent_breakouts:
                if breakout.get("volume_confirmation", False):
                    if breakout.get("price_change", 0) > 0.02:
                        signal_score += 0.2
                        trading_signals["reasoning"].append("Volume-confirmed bullish breakout")
                    elif breakout.get("price_change", 0) < -0.02:
                        signal_score -= 0.2
                        trading_signals["reasoning"].append("Volume-confirmed bearish breakout")
            
            # Divergence signals
            if bullish_divergences:
                signal_score += 0.4
                trading_signals["reasoning"].append("Bullish volume divergence detected")
            elif bearish_divergences:
                signal_score -= 0.4
                trading_signals["reasoning"].append("Bearish volume divergence detected")
            
            # Institutional flow signals
            if institutional_flow == "accumulation":
                signal_score += 0.3
                trading_signals["reasoning"].append("Institutional accumulation detected")
            elif institutional_flow == "distribution":
                signal_score -= 0.3
                trading_signals["reasoning"].append("Institutional distribution detected")
            
            # Determine final signal
            if signal_score > 0.5:
                trading_signals["primary_signal"] = VolumeSignal.BULLISH_CONFIRMATION
                trading_signals["signal_strength"] = VolumeStrength.STRONG if signal_score > 0.8 else VolumeStrength.MODERATE
            elif signal_score < -0.5:
                trading_signals["primary_signal"] = VolumeSignal.BEARISH_CONFIRMATION
                trading_signals["signal_strength"] = VolumeStrength.STRONG if signal_score < -0.8 else VolumeStrength.MODERATE
            else:
                trading_signals["primary_signal"] = VolumeSignal.NEUTRAL
                trading_signals["signal_strength"] = VolumeStrength.MODERATE
            
            trading_signals["confidence"] = min(1.0, abs(signal_score))
            
            # Generate entry/exit conditions
            trading_signals["entry_conditions"] = await self._generate_entry_conditions(trading_signals)
            trading_signals["exit_conditions"] = await self._generate_exit_conditions(trading_signals)
            trading_signals["risk_factors"] = await self._identify_risk_factors(analysis_results)
            
            return trading_signals
            
        except Exception as e:
            logger.error(f"Error generating volume trading signals: {e}")
            return {}
    
    async def _generate_overall_assessment(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment of volume analysis"""
        try:
            assessment = {
                "overall_sentiment": "neutral",
                "volume_health": "moderate",
                "market_structure": "balanced",
                "trading_recommendation": "hold",
                "key_insights": [],
                "risk_level": "medium"
            }
            
            # Aggregate signals
            trading_signals = analysis_results.get("trading_signals", {})
            primary_signal = trading_signals.get("primary_signal", VolumeSignal.NEUTRAL)
            signal_strength = trading_signals.get("signal_strength", VolumeStrength.MODERATE)
            
            # Determine overall sentiment
            if primary_signal in [VolumeSignal.BULLISH_CONFIRMATION, VolumeSignal.BULLISH_DIVERGENCE]:
                assessment["overall_sentiment"] = "bullish"
                assessment["trading_recommendation"] = "buy"
            elif primary_signal in [VolumeSignal.BEARISH_CONFIRMATION, VolumeSignal.BEARISH_DIVERGENCE]:
                assessment["overall_sentiment"] = "bearish"
                assessment["trading_recommendation"] = "sell"
            
            # Assess volume health
            volume_metrics = analysis_results.get("volume_metrics", {})
            volume_strength = volume_metrics.get("volume_strength", "moderate")
            
            if volume_strength in ["strong", "very_strong"]:
                assessment["volume_health"] = "healthy"
            elif volume_strength in ["weak", "very_weak"]:
                assessment["volume_health"] = "unhealthy"
            
            # Assess market structure
            accumulation_analysis = analysis_results.get("accumulation_analysis", {})
            institutional_flow = accumulation_analysis.get("institutional_flow", "neutral")
            
            if institutional_flow == "accumulation":
                assessment["market_structure"] = "accumulation"
            elif institutional_flow == "distribution":
                assessment["market_structure"] = "distribution"
            
            # Generate key insights
            assessment["key_insights"] = await self._generate_key_insights(analysis_results)
            
            # Assess risk level
            assessment["risk_level"] = await self._assess_risk_level(analysis_results)
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error generating overall assessment: {e}")
            return {}
    
    # Helper methods
    async def _calculate_volume_trend(self, df: pd.DataFrame) -> str:
        """Calculate volume trend direction"""
        try:
            if len(df) < 5:
                return "insufficient_data"
            
            recent_volume = df.tail(5)['volume'].mean()
            earlier_volume = df.tail(10).head(5)['volume'].mean()
            
            if recent_volume > earlier_volume * 1.1:
                return "increasing"
            elif recent_volume < earlier_volume * 0.9:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return "unknown"
    
    def _classify_volume_strength(self, volume_ratio: float) -> str:
        """Classify volume strength based on ratio"""
        if volume_ratio >= 2.0:
            return "very_strong"
        elif volume_ratio >= 1.5:
            return "strong"
        elif volume_ratio >= 1.2:
            return "moderate"
        elif volume_ratio >= 0.8:
            return "weak"
        else:
            return "very_weak"
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "very_strong"
        elif abs_corr >= 0.5:
            return "strong"
        elif abs_corr >= 0.3:
            return "moderate"
        elif abs_corr >= 0.1:
            return "weak"
        else:
            return "very_weak"
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation value"""
        if correlation > 0.5:
            return "Strong positive correlation - volume confirms price moves"
        elif correlation > 0.2:
            return "Moderate positive correlation - volume generally supports price"
        elif correlation > -0.2:
            return "Weak correlation - volume and price move independently"
        elif correlation > -0.5:
            return "Moderate negative correlation - volume opposes price moves"
        else:
            return "Strong negative correlation - volume contradicts price moves"
    
    def _calculate_breakout_strength(self, price_change: float, volume_ratio: float) -> str:
        """Calculate breakout strength"""
        strength_score = abs(price_change) * 10 + (volume_ratio - 1) * 0.5
        
        if strength_score >= 0.4:
            return "very_strong"
        elif strength_score >= 0.3:
            return "strong"
        elif strength_score >= 0.2:
            return "moderate"
        else:
            return "weak"
    
    async def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend slope"""
        try:
            if len(series) < 2:
                return 0.0
            
            x = np.arange(len(series))
            y = series.values
            
            # Calculate linear regression slope
            slope = np.polyfit(x, y, 1)[0]
            
            # Normalize by first value
            if series.iloc[0] != 0:
                normalized_slope = slope / series.iloc[0]
            else:
                normalized_slope = slope
            
            return normalized_slope
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return 0.0
    
    async def _calculate_ad_line(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Accumulation/Distribution Line"""
        try:
            ad_line = []
            ad_value = 0
            
            for _, row in df.iterrows():
                clv = ((row['close'] - row['low']) - (row['high'] - row['close'])) / (row['high'] - row['low'])
                if pd.isna(clv):
                    clv = 0
                ad_value += clv * row['volume']
                ad_line.append(ad_value)
            
            return pd.Series(ad_line)
            
        except Exception as e:
            logger.error(f"Error calculating AD line: {e}")
            return pd.Series()
    
    async def _create_volume_profile(self, df: pd.DataFrame) -> Dict[float, float]:
        """Create volume profile"""
        try:
            volume_profile = {}
            
            for _, row in df.iterrows():
                price_range = np.linspace(row['low'], row['high'], 10)
                volume_per_price = row['volume'] / 10
                
                for price in price_range:
                    price_level = round(price, 2)
                    volume_profile[price_level] = volume_profile.get(price_level, 0) + volume_per_price
            
            return volume_profile
            
        except Exception as e:
            logger.error(f"Error creating volume profile: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            return len(self.analysis_templates) > 0
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear volume analysis cache"""
        self.volume_cache.clear()
        logger.info("Volume analysis cache cleared")
    
    # Missing helper methods
    async def _analyze_volume_confirmation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume confirmation of price moves"""
        try:
            if len(df) < 5:
                return {"error": "Insufficient data"}
            
            confirmation_score = 0.0
            confirmations = []
            
            for i in range(1, min(10, len(df))):
                current = df.iloc[i]
                previous = df.iloc[i-1]
                
                price_change = (current['close'] - previous['close']) / previous['close']
                volume_change = (current['volume'] - previous['volume']) / previous['volume'] if previous['volume'] > 0 else 0
                
                # Volume confirms price move if both move in same direction
                if abs(price_change) > 0.01:  # Significant price move
                    if (price_change > 0 and volume_change > 0) or (price_change < 0 and volume_change > 0):
                        confirmation_score += 1
                        confirmations.append({
                            "period": i,
                            "price_change": price_change,
                            "volume_change": volume_change,
                            "confirmed": True
                        })
            
            confirmation_rate = confirmation_score / min(10, len(df) - 1) if len(df) > 1 else 0
            
            return {
                "confirmation_rate": confirmation_rate,
                "confirmations": confirmations,
                "strength": "strong" if confirmation_rate > 0.7 else "moderate" if confirmation_rate > 0.5 else "weak"
            }
        except Exception as e:
            logger.error(f"Error analyzing volume confirmation: {e}")
            return {"confirmation_rate": 0.5, "strength": "moderate"}
    
    async def _identify_breakout_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify volume breakout patterns"""
        try:
            patterns = []
            
            if len(df) < 3:
                return patterns
            
            volume_avg = df['volume'].mean()
            
            for i in range(1, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i-1]
                
                price_change = (current['close'] - previous['close']) / previous['close']
                volume_ratio = current['volume'] / volume_avg if volume_avg > 0 else 1
                
                if abs(price_change) > 0.015 and volume_ratio > 1.5:  # Significant breakout
                    patterns.append({
                        "type": "bullish_breakout" if price_change > 0 else "bearish_breakout",
                        "price_change": price_change,
                        "volume_ratio": volume_ratio,
                        "strength": "strong" if volume_ratio > 2.0 else "moderate"
                    })
            
            return patterns
        except Exception as e:
            logger.error(f"Error identifying breakout patterns: {e}")
            return []
    
    def _classify_divergence_strength(self, divergence_count: int) -> str:
        """Classify divergence strength"""
        if divergence_count >= 3:
            return "very_strong"
        elif divergence_count >= 2:
            return "strong"
        elif divergence_count >= 1:
            return "moderate"
        else:
            return "weak"
    
    async def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns"""
        try:
            if len(df) < 10:
                return {"error": "Insufficient data"}
            
            recent_volume = df.tail(5)['volume'].mean()
            earlier_volume = df.tail(10).head(5)['volume'].mean()
            
            volume_trend = "increasing" if recent_volume > earlier_volume * 1.1 else "decreasing" if recent_volume < earlier_volume * 0.9 else "stable"
            
            # Check for volume spikes
            volume_spikes = []
            volume_std = df['volume'].std()
            volume_mean = df['volume'].mean()
            
            for i, row in df.tail(10).iterrows():
                if row['volume'] > volume_mean + 2 * volume_std:
                    volume_spikes.append({
                        "index": i,
                        "volume": row['volume'],
                        "volume_ratio": row['volume'] / volume_mean if volume_mean > 0 else 1
                    })
            
            return {
                "volume_trend": volume_trend,
                "volume_spikes": volume_spikes,
                "pattern": "accumulation" if volume_trend == "increasing" else "distribution" if volume_trend == "decreasing" else "neutral"
            }
        except Exception as e:
            logger.error(f"Error analyzing volume patterns: {e}")
            return {"volume_trend": "stable", "pattern": "neutral"}
    
    async def _identify_volume_nodes(self, volume_profile: Dict[float, float]) -> List[Dict[str, Any]]:
        """Identify volume nodes (high volume areas)"""
        try:
            if not volume_profile:
                return []
            
            total_volume = sum(volume_profile.values())
            avg_volume = total_volume / len(volume_profile) if volume_profile else 0
            
            nodes = []
            for price, volume in volume_profile.items():
                if volume > avg_volume * 1.5:  # High volume node
                    nodes.append({
                        "price": price,
                        "volume": volume,
                        "strength": "strong" if volume > avg_volume * 2.0 else "moderate"
                    })
            
            # Sort by volume descending
            nodes.sort(key=lambda x: x["volume"], reverse=True)
            
            return nodes[:10]  # Top 10 nodes
        except Exception as e:
            logger.error(f"Error identifying volume nodes: {e}")
            return []
    
    async def _generate_entry_conditions(self, trading_signals: Dict[str, Any]) -> List[str]:
        """Generate entry conditions for trading signals"""
        try:
            conditions = []
            primary_signal = trading_signals.get("primary_signal", VolumeSignal.NEUTRAL)
            
            if primary_signal == VolumeSignal.BULLISH_CONFIRMATION:
                conditions.append("Wait for price to break above recent high with volume confirmation")
                conditions.append("Enter on pullback to support with decreasing volume")
            elif primary_signal == VolumeSignal.BEARISH_CONFIRMATION:
                conditions.append("Wait for price to break below recent low with volume confirmation")
                conditions.append("Enter on bounce to resistance with decreasing volume")
            elif primary_signal == VolumeSignal.BULLISH_DIVERGENCE:
                conditions.append("Enter when price shows reversal pattern with increasing volume")
            elif primary_signal == VolumeSignal.BEARISH_DIVERGENCE:
                conditions.append("Enter when price shows reversal pattern with increasing volume")
            else:
                conditions.append("Wait for clearer volume confirmation")
            
            return conditions
        except Exception as e:
            logger.error(f"Error generating entry conditions: {e}")
            return ["Wait for volume confirmation"]
    
    async def _generate_exit_conditions(self, trading_signals: Dict[str, Any]) -> List[str]:
        """Generate exit conditions for trading signals"""
        try:
            conditions = []
            primary_signal = trading_signals.get("primary_signal", VolumeSignal.NEUTRAL)
            
            if primary_signal in [VolumeSignal.BULLISH_CONFIRMATION, VolumeSignal.BULLISH_DIVERGENCE]:
                conditions.append("Exit on volume decline with price reaching target")
                conditions.append("Exit if volume diverges negatively from price")
            elif primary_signal in [VolumeSignal.BEARISH_CONFIRMATION, VolumeSignal.BEARISH_DIVERGENCE]:
                conditions.append("Exit on volume decline with price reaching target")
                conditions.append("Exit if volume diverges negatively from price")
            else:
                conditions.append("Exit on volume confirmation of reversal")
            
            return conditions
        except Exception as e:
            logger.error(f"Error generating exit conditions: {e}")
            return ["Exit on volume confirmation"]
    
    async def _identify_risk_factors(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Identify risk factors from analysis"""
        try:
            risk_factors = []
            
            volume_metrics = analysis_results.get("volume_metrics", {})
            volume_strength = volume_metrics.get("volume_strength", "moderate")
            
            if volume_strength in ["weak", "very_weak"]:
                risk_factors.append("Low volume - weak price moves may not be sustainable")
            
            correlation_analysis = analysis_results.get("correlation_analysis", {})
            overall_correlation = correlation_analysis.get("correlations", {}).get("overall", 0)
            
            if abs(overall_correlation) < 0.2:
                risk_factors.append("Weak volume-price correlation - price moves may be unreliable")
            
            divergence_analysis = analysis_results.get("divergence_analysis", {})
            if divergence_analysis.get("reversal_probability", 0) > 0.6:
                risk_factors.append("High reversal probability detected")
            
            return risk_factors
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return []
    
    async def _generate_key_insights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate key insights from analysis"""
        try:
            insights = []
            
            volume_metrics = analysis_results.get("volume_metrics", {})
            volume_strength = volume_metrics.get("volume_strength", "moderate")
            volume_trend = volume_metrics.get("volume_trend", "stable")
            
            if volume_strength in ["strong", "very_strong"]:
                insights.append(f"Strong volume activity detected - {volume_trend} trend")
            
            correlation_analysis = analysis_results.get("correlation_analysis", {})
            overall_correlation = correlation_analysis.get("correlations", {}).get("overall", 0)
            
            if abs(overall_correlation) > 0.5:
                insights.append(f"Strong volume-price correlation ({overall_correlation:.2f}) - moves are well-confirmed")
            
            breakout_analysis = analysis_results.get("breakout_analysis", {})
            recent_breakouts = breakout_analysis.get("recent_breakouts", [])
            if recent_breakouts:
                insights.append(f"{len(recent_breakouts)} volume-confirmed breakouts detected recently")
            
            divergence_analysis = analysis_results.get("divergence_analysis", {})
            bullish_divs = divergence_analysis.get("bullish_divergences", [])
            bearish_divs = divergence_analysis.get("bearish_divergences", [])
            
            if bullish_divs:
                insights.append("Bullish volume divergence detected - potential reversal")
            if bearish_divs:
                insights.append("Bearish volume divergence detected - potential reversal")
            
            accumulation_analysis = analysis_results.get("accumulation_analysis", {})
            institutional_flow = accumulation_analysis.get("institutional_flow", "neutral")
            
            if institutional_flow == "accumulation":
                insights.append("Institutional accumulation detected - bullish signal")
            elif institutional_flow == "distribution":
                insights.append("Institutional distribution detected - bearish signal")
            
            if not insights:
                insights.append("Volume analysis shows neutral conditions")
            
            return insights
        except Exception as e:
            logger.error(f"Error generating key insights: {e}")
            return ["Volume analysis completed"]
    
    async def _summarize_volume_confirmation(self, breakouts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize volume confirmation from breakouts"""
        try:
            if not breakouts:
                return {"confirmed": 0, "unconfirmed": 0, "confirmation_rate": 0.0}
            
            confirmed = sum(1 for b in breakouts if b.get("volume_confirmation", False))
            unconfirmed = len(breakouts) - confirmed
            confirmation_rate = confirmed / len(breakouts) if breakouts else 0.0
            
            return {
                "confirmed": confirmed,
                "unconfirmed": unconfirmed,
                "confirmation_rate": confirmation_rate,
                "strength": "strong" if confirmation_rate > 0.7 else "moderate" if confirmation_rate > 0.5 else "weak"
            }
        except Exception as e:
            logger.error(f"Error summarizing volume confirmation: {e}")
            return {"confirmed": 0, "unconfirmed": 0, "confirmation_rate": 0.0}
    
    async def _analyze_price_acceptance(self, df: pd.DataFrame, volume_profile: Dict[float, float]) -> Dict[str, Any]:
        """Analyze price acceptance at different levels"""
        try:
            if not volume_profile:
                return {"error": "No volume profile data"}
            
            current_price = df.iloc[-1]['close']
            
            # Find closest volume node
            closest_node = min(volume_profile.keys(), key=lambda x: abs(x - current_price))
            node_volume = volume_profile[closest_node]
            avg_volume = sum(volume_profile.values()) / len(volume_profile) if volume_profile else 0
            
            acceptance_level = "high" if node_volume > avg_volume * 1.5 else "moderate" if node_volume > avg_volume else "low"
            
            return {
                "current_price": current_price,
                "closest_node": closest_node,
                "node_volume": node_volume,
                "acceptance_level": acceptance_level
            }
        except Exception as e:
            logger.error(f"Error analyzing price acceptance: {e}")
            return {"acceptance_level": "moderate"}
    
    async def _identify_support_resistance_levels(self, volume_profile: Dict[float, float]) -> List[Dict[str, Any]]:
        """Identify support/resistance levels from volume profile"""
        try:
            if not volume_profile:
                return []
            
            # Find high volume nodes (potential support/resistance)
            total_volume = sum(volume_profile.values())
            avg_volume = total_volume / len(volume_profile) if volume_profile else 0
            
            levels = []
            for price, volume in volume_profile.items():
                if volume > avg_volume * 1.5:
                    # Calculate average price for support/resistance determination
                    avg_price = sum(volume_profile.keys()) / len(volume_profile) if volume_profile else price
                    levels.append({
                        "price": price,
                        "volume": volume,
                        "strength": "strong" if volume > avg_volume * 2.0 else "moderate",
                        "type": "support" if price < avg_price else "resistance"
                    })
            
            # Sort by volume descending
            levels.sort(key=lambda x: x["volume"], reverse=True)
            
            return levels[:5]  # Top 5 levels
        except Exception as e:
            logger.error(f"Error identifying support/resistance levels: {e}")
            return []
    
    async def _analyze_smart_money_activity(self, df: pd.DataFrame) -> str:
        """Analyze smart money activity"""
        try:
            if len(df) < 10:
                return "low"
            
            # Large volume trades during price moves indicate smart money
            large_volume_threshold = df['volume'].quantile(0.8)
            large_volume_data = df[df['volume'] >= large_volume_threshold]
            
            if len(large_volume_data) > len(df) * 0.3:
                return "high"
            elif len(large_volume_data) > len(df) * 0.15:
                return "moderate"
            else:
                return "low"
        except Exception as e:
            logger.error(f"Error analyzing smart money activity: {e}")
            return "moderate"
    
    async def _analyze_retail_participation(self, df: pd.DataFrame) -> str:
        """Analyze retail participation"""
        try:
            if len(df) < 10:
                return "normal"
            
            # High volume volatility suggests retail participation
            volume_volatility = df['volume'].std() / df['volume'].mean() if df['volume'].mean() > 0 else 0
            
            if volume_volatility > 0.5:
                return "high"
            elif volume_volatility > 0.3:
                return "moderate"
            else:
                return "normal"
        except Exception as e:
            logger.error(f"Error analyzing retail participation: {e}")
            return "normal"
    
    async def _assess_risk_level(self, analysis_results: Dict[str, Any]) -> str:
        """Assess overall risk level"""
        try:
            risk_score = 0
            
            volume_metrics = analysis_results.get("volume_metrics", {})
            volume_strength = volume_metrics.get("volume_strength", "moderate")
            
            if volume_strength in ["weak", "very_weak"]:
                risk_score += 1
            
            correlation_analysis = analysis_results.get("correlation_analysis", {})
            overall_correlation = correlation_analysis.get("correlations", {}).get("overall", 0)
            
            if abs(overall_correlation) < 0.2:
                risk_score += 1
            
            divergence_analysis = analysis_results.get("divergence_analysis", {})
            if divergence_analysis.get("reversal_probability", 0) > 0.6:
                risk_score += 1
            
            if risk_score >= 2:
                return "high"
            elif risk_score >= 1:
                return "medium"
            else:
                return "low"
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "medium"