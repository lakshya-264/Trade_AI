"""
Advanced Options Trading AI System
Real-time options analysis with AI-powered recommendations
Features: Greeks analysis, Options strategies, Risk management, AI predictions
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
import logging
from datetime import datetime, timedelta
import json
import uuid
import numpy as np
import pandas as pd
from enum import Enum
import math

logger = logging.getLogger(__name__)

class OptionsType(str, Enum):
    CALL = "call"
    PUT = "put"

class OptionsStrategy(str, Enum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    BUTTERFLY = "butterfly"
    IRON_CONDOR = "iron_condor"
    CALENDAR_SPREAD = "calendar_spread"
    DIAGONAL_SPREAD = "diagonal_spread"

class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class OptionsTradingAI:
    def __init__(self):
        # Options data cache
        self.options_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Active options strategies
        self.active_strategies = {}
        
        # AI models for options analysis
        self.ai_models = {
            "price_prediction": None,
            "volatility_prediction": None,
            "strategy_optimizer": None
        }
        
        # Options strategies database
        self.strategies_database = self._initialize_strategies_database()
        
        # Risk management parameters
        self.risk_parameters = {
            "max_portfolio_risk": 0.05,  # 5% max portfolio risk
            "max_single_trade_risk": 0.02,  # 2% max single trade risk
            "max_delta_exposure": 0.1,  # Max delta exposure
            "max_theta_decay": 0.01,  # Max theta decay per day
            "max_vega_exposure": 0.05  # Max vega exposure
        }
        
        # Performance tracking
        self.performance_tracking = {
            "total_trades": 0,
            "profitable_trades": 0,
            "total_pnl": 0.0,
            "strategy_performance": {}
        }
    
    def _initialize_strategies_database(self) -> Dict[str, Any]:
        """Initialize comprehensive options strategies database"""
        return {
            OptionsStrategy.LONG_CALL: {
                "name": "Long Call",
                "description": "Buy call options for bullish outlook",
                "risk_level": RiskLevel.MEDIUM,
                "max_loss": "Premium paid",
                "max_profit": "Unlimited",
                "breakeven": "Strike + Premium",
                "time_decay": "Negative",
                "volatility_impact": "Positive",
                "market_outlook": "Bullish",
                "suitable_for": ["Bullish trend", "Earnings play", "Volatility expansion"],
                "greek_profile": {
                    "delta": "Positive (0 to 1)",
                    "gamma": "Positive",
                    "theta": "Negative",
                    "vega": "Positive"
                }
            },
            OptionsStrategy.LONG_PUT: {
                "name": "Long Put",
                "description": "Buy put options for bearish outlook",
                "risk_level": RiskLevel.MEDIUM,
                "max_loss": "Premium paid",
                "max_profit": "Strike - Premium",
                "breakeven": "Strike - Premium",
                "time_decay": "Negative",
                "volatility_impact": "Positive",
                "market_outlook": "Bearish",
                "suitable_for": ["Bearish trend", "Protection", "Volatility expansion"],
                "greek_profile": {
                    "delta": "Negative (-1 to 0)",
                    "gamma": "Positive",
                    "theta": "Negative",
                    "vega": "Positive"
                }
            },
            OptionsStrategy.COVERED_CALL: {
                "name": "Covered Call",
                "description": "Sell call against long stock position",
                "risk_level": RiskLevel.LOW,
                "max_loss": "Stock price - Premium",
                "max_profit": "Strike - Stock price + Premium",
                "breakeven": "Stock price - Premium",
                "time_decay": "Positive",
                "volatility_impact": "Negative",
                "market_outlook": "Neutral to Bullish",
                "suitable_for": ["Income generation", "Neutral outlook", "High volatility"],
                "greek_profile": {
                    "delta": "Positive (reduced)",
                    "gamma": "Negative",
                    "theta": "Positive",
                    "vega": "Negative"
                }
            },
            OptionsStrategy.PROTECTIVE_PUT: {
                "name": "Protective Put",
                "description": "Buy put to protect long stock position",
                "risk_level": RiskLevel.LOW,
                "max_loss": "Premium paid",
                "max_profit": "Unlimited",
                "breakeven": "Stock price + Premium",
                "time_decay": "Negative",
                "volatility_impact": "Positive",
                "market_outlook": "Bullish with protection",
                "suitable_for": ["Portfolio protection", "Risk management", "Volatile markets"],
                "greek_profile": {
                    "delta": "Positive (reduced)",
                    "gamma": "Positive",
                    "theta": "Negative",
                    "vega": "Positive"
                }
            },
            OptionsStrategy.STRADDLE: {
                "name": "Long Straddle",
                "description": "Buy call and put at same strike",
                "risk_level": RiskLevel.HIGH,
                "max_loss": "Total premium paid",
                "max_profit": "Unlimited",
                "breakeven": "Strike ± Total premium",
                "time_decay": "Negative",
                "volatility_impact": "Very Positive",
                "market_outlook": "High volatility",
                "suitable_for": ["Earnings", "Volatility expansion", "Uncertain direction"],
                "greek_profile": {
                    "delta": "Neutral",
                    "gamma": "Very Positive",
                    "theta": "Very Negative",
                    "vega": "Very Positive"
                }
            },
            OptionsStrategy.STRANGLE: {
                "name": "Long Strangle",
                "description": "Buy call and put at different strikes",
                "risk_level": RiskLevel.MEDIUM,
                "max_loss": "Total premium paid",
                "max_profit": "Unlimited",
                "breakeven": "Call strike + Premium, Put strike - Premium",
                "time_decay": "Negative",
                "volatility_impact": "Positive",
                "market_outlook": "High volatility",
                "suitable_for": ["Volatility expansion", "Lower cost than straddle"],
                "greek_profile": {
                    "delta": "Neutral",
                    "gamma": "Positive",
                    "theta": "Negative",
                    "vega": "Positive"
                }
            },
            OptionsStrategy.BUTTERFLY: {
                "name": "Butterfly Spread",
                "description": "Limited risk/reward spread strategy",
                "risk_level": RiskLevel.LOW,
                "max_loss": "Net premium paid",
                "max_profit": "Limited",
                "breakeven": "Multiple breakeven points",
                "time_decay": "Positive",
                "volatility_impact": "Negative",
                "market_outlook": "Neutral",
                "suitable_for": ["Range-bound markets", "Income generation", "Low volatility"],
                "greek_profile": {
                    "delta": "Neutral",
                    "gamma": "Negative",
                    "theta": "Positive",
                    "vega": "Negative"
                }
            },
            OptionsStrategy.IRON_CONDOR: {
                "name": "Iron Condor",
                "description": "Four-leg spread for income",
                "risk_level": RiskLevel.LOW,
                "max_loss": "Limited",
                "max_profit": "Limited",
                "breakeven": "Multiple breakeven points",
                "time_decay": "Positive",
                "volatility_impact": "Negative",
                "market_outlook": "Neutral",
                "suitable_for": ["Range-bound markets", "Income generation", "Low volatility"],
                "greek_profile": {
                    "delta": "Neutral",
                    "gamma": "Negative",
                    "theta": "Positive",
                    "vega": "Negative"
                }
            }
        }
    
    async def analyze_options_chain(
        self,
        symbol: str,
        underlying_price: float,
        days_to_expiry: int,
        risk_free_rate: float = 0.05,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """Comprehensive options chain analysis"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{underlying_price}_{days_to_expiry}"
            if cache_key in self.options_cache:
                cached_data, timestamp = self.options_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Generate options chain
            options_chain = await self._generate_options_chain(
                symbol, underlying_price, days_to_expiry, risk_free_rate, volatility
            )
            
            # Analyze each option
            analyzed_options = []
            for option in options_chain:
                analysis = await self._analyze_single_option(option, underlying_price, days_to_expiry, risk_free_rate)
                analyzed_options.append({**option, **analysis})
            
            # Find best options
            best_options = await self._find_best_options(analyzed_options)
            
            # Generate strategy recommendations
            strategy_recommendations = await self._generate_strategy_recommendations(
                analyzed_options, underlying_price, days_to_expiry
            )
            
            # Risk analysis
            risk_analysis = await self._analyze_options_risk(analyzed_options)
            
            analysis_result = {
                "symbol": symbol,
                "underlying_price": underlying_price,
                "days_to_expiry": days_to_expiry,
                "analysis_timestamp": datetime.now(),
                "options_chain": analyzed_options,
                "best_options": best_options,
                "strategy_recommendations": strategy_recommendations,
                "risk_analysis": risk_analysis,
                "market_conditions": await self._analyze_market_conditions(symbol, underlying_price)
            }
            
            # Cache results
            self.options_cache[cache_key] = (analysis_result, datetime.now().timestamp())
            
            logger.info(f"Options analysis completed for {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing options chain: {e}")
            return {"error": str(e)}
    
    async def _generate_options_chain(
        self,
        symbol: str,
        underlying_price: float,
        days_to_expiry: int,
        risk_free_rate: float,
        volatility: Optional[float]
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive options chain"""
        try:
            options_chain = []
            
            # Calculate implied volatility if not provided
            if volatility is None:
                volatility = await self._calculate_implied_volatility(symbol, underlying_price, days_to_expiry)
            
            # Generate strikes around current price
            strike_range = 0.2  # 20% range
            min_strike = underlying_price * (1 - strike_range)
            max_strike = underlying_price * (1 + strike_range)
            
            # Generate strikes (every 5% for demonstration)
            strikes = []
            current_strike = min_strike
            while current_strike <= max_strike:
                strikes.append(round(current_strike, 2))
                current_strike *= 1.05
            
            # Generate call and put options
            for strike in strikes:
                # Call option
                call_option = await self._calculate_option_greeks(
                    OptionsType.CALL, underlying_price, strike, days_to_expiry, risk_free_rate, volatility
                )
                call_option.update({
                    "symbol": symbol,
                    "option_type": OptionsType.CALL,
                    "strike": strike,
                    "expiry_days": days_to_expiry
                })
                options_chain.append(call_option)
                
                # Put option
                put_option = await self._calculate_option_greeks(
                    OptionsType.PUT, underlying_price, strike, days_to_expiry, risk_free_rate, volatility
                )
                put_option.update({
                    "symbol": symbol,
                    "option_type": OptionsType.PUT,
                    "strike": strike,
                    "expiry_days": days_to_expiry
                })
                options_chain.append(put_option)
            
            return options_chain
            
        except Exception as e:
            logger.error(f"Error generating options chain: {e}")
            return []
    
    async def _calculate_option_greeks(
        self,
        option_type: OptionsType,
        underlying_price: float,
        strike: float,
        days_to_expiry: int,
        risk_free_rate: float,
        volatility: float
    ) -> Dict[str, Any]:
        """Calculate Black-Scholes option pricing and Greeks"""
        try:
            # Convert days to years
            time_to_expiry = days_to_expiry / 365.0
            
            # Black-Scholes calculation
            d1 = (math.log(underlying_price / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
            d2 = d1 - volatility * math.sqrt(time_to_expiry)
            
            # Calculate option price
            if option_type == OptionsType.CALL:
                option_price = underlying_price * self._normal_cdf(d1) - strike * math.exp(-risk_free_rate * time_to_expiry) * self._normal_cdf(d2)
                delta = self._normal_cdf(d1)
            else:  # PUT
                option_price = strike * math.exp(-risk_free_rate * time_to_expiry) * self._normal_cdf(-d2) - underlying_price * self._normal_cdf(-d1)
                delta = self._normal_cdf(d1) - 1
            
            # Calculate Greeks
            gamma = self._normal_pdf(d1) / (underlying_price * volatility * math.sqrt(time_to_expiry))
            
            theta = (-underlying_price * self._normal_pdf(d1) * volatility / (2 * math.sqrt(time_to_expiry)) -
                    risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * self._normal_cdf(d2 if option_type == OptionsType.CALL else -d2))
            
            vega = underlying_price * self._normal_pdf(d1) * math.sqrt(time_to_expiry)
            
            # Convert theta to daily
            theta_daily = theta / 365.0
            
            return {
                "premium": round(option_price, 2),
                "delta": round(delta, 4),
                "gamma": round(gamma, 4),
                "theta": round(theta_daily, 4),
                "vega": round(vega, 4),
                "implied_volatility": round(volatility, 4),
                "intrinsic_value": max(0, underlying_price - strike) if option_type == OptionsType.CALL else max(0, strike - underlying_price),
                "time_value": round(option_price - max(0, underlying_price - strike if option_type == OptionsType.CALL else strike - underlying_price), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating option Greeks: {e}")
            return {}
    
    def _normal_cdf(self, x: float) -> float:
        """Cumulative distribution function of standard normal distribution"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _normal_pdf(self, x: float) -> float:
        """Probability density function of standard normal distribution"""
        return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)
    
    async def _analyze_single_option(
        self,
        option: Dict[str, Any],
        underlying_price: float,
        days_to_expiry: int,
        risk_free_rate: float
    ) -> Dict[str, Any]:
        """Analyze individual option for trading opportunities"""
        try:
            analysis = {
                "analysis_score": 0.0,
                "recommendation": "hold",
                "confidence": 0.0,
                "risk_level": RiskLevel.MEDIUM,
                "trading_signals": [],
                "key_insights": []
            }
            
            option_type = option["option_type"]
            strike = option["strike"]
            premium = option["premium"]
            delta = option["delta"]
            gamma = option["gamma"]
            theta = option["theta"]
            vega = option["vega"]
            
            # Analyze moneyness
            if option_type == OptionsType.CALL:
                moneyness = underlying_price / strike
                intrinsic_value = max(0, underlying_price - strike)
            else:
                moneyness = strike / underlying_price
                intrinsic_value = max(0, strike - underlying_price)
            
            # Determine moneyness category
            if moneyness > 1.05:
                moneyness_category = "deep_itm"
            elif moneyness > 1.02:
                moneyness_category = "itm"
            elif moneyness > 0.98:
                moneyness_category = "atm"
            elif moneyness > 0.95:
                moneyness_category = "otm"
            else:
                moneyness_category = "deep_otm"
            
            # Analyze time decay
            time_decay_analysis = self._analyze_time_decay(theta, days_to_expiry, premium)
            
            # Analyze volatility sensitivity
            volatility_analysis = self._analyze_volatility_sensitivity(vega, premium)
            
            # Generate trading signals
            trading_signals = []
            
            # Delta-based signals
            if abs(delta) > 0.7:
                trading_signals.append("High delta - acts like stock")
            elif abs(delta) < 0.3:
                trading_signals.append("Low delta - lottery ticket")
            
            # Gamma-based signals
            if gamma > 0.01:
                trading_signals.append("High gamma - rapid delta changes")
            
            # Theta-based signals
            if theta < -0.05:
                trading_signals.append("High time decay - avoid holding")
            elif theta > 0.01:
                trading_signals.append("Positive theta - time decay benefit")
            
            # Vega-based signals
            if vega > 0.1:
                trading_signals.append("High volatility sensitivity")
            
            # Generate recommendation
            recommendation_score = 0.0
            
            # Score based on moneyness
            if moneyness_category == "atm":
                recommendation_score += 0.3  # ATM options are often good for strategies
            elif moneyness_category in ["itm", "otm"]:
                recommendation_score += 0.2
            
            # Score based on Greeks
            if abs(delta) > 0.5:
                recommendation_score += 0.2  # Good directional exposure
            
            if gamma > 0.005:
                recommendation_score += 0.1  # Good gamma
            
            if theta > 0:
                recommendation_score += 0.2  # Positive theta
            
            if vega > 0.05:
                recommendation_score += 0.1  # Good volatility exposure
            
            # Determine recommendation
            if recommendation_score > 0.6:
                analysis["recommendation"] = "strong_buy"
                analysis["confidence"] = min(1.0, recommendation_score)
            elif recommendation_score > 0.4:
                analysis["recommendation"] = "buy"
                analysis["confidence"] = recommendation_score
            elif recommendation_score > 0.2:
                analysis["recommendation"] = "hold"
                analysis["confidence"] = recommendation_score
            else:
                analysis["recommendation"] = "avoid"
                analysis["confidence"] = 0.1
            
            # Determine risk level
            if abs(delta) > 0.8 or theta < -0.1:
                analysis["risk_level"] = RiskLevel.HIGH
            elif abs(delta) > 0.6 or theta < -0.05:
                analysis["risk_level"] = RiskLevel.MEDIUM
            else:
                analysis["risk_level"] = RiskLevel.LOW
            
            analysis.update({
                "moneyness": moneyness,
                "moneyness_category": moneyness_category,
                "intrinsic_value": intrinsic_value,
                "time_decay_analysis": time_decay_analysis,
                "volatility_analysis": volatility_analysis,
                "trading_signals": trading_signals,
                "analysis_score": recommendation_score
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing single option: {e}")
            return {}
    
    def _analyze_time_decay(self, theta: float, days_to_expiry: int, premium: float) -> Dict[str, Any]:
        """Analyze time decay characteristics"""
        try:
            daily_decay = abs(theta)
            total_decay = daily_decay * days_to_expiry
            
            decay_percentage = (total_decay / premium) * 100 if premium > 0 else 0
            
            if decay_percentage > 50:
                decay_level = "very_high"
            elif decay_percentage > 30:
                decay_level = "high"
            elif decay_percentage > 15:
                decay_level = "moderate"
            else:
                decay_level = "low"
            
            return {
                "daily_decay": daily_decay,
                "total_decay": total_decay,
                "decay_percentage": decay_percentage,
                "decay_level": decay_level,
                "days_to_significant_decay": int(premium / (2 * daily_decay)) if daily_decay > 0 else days_to_expiry
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time decay: {e}")
            return {}
    
    def _analyze_volatility_sensitivity(self, vega: float, premium: float) -> Dict[str, Any]:
        """Analyze volatility sensitivity"""
        try:
            vega_percentage = (vega / premium) * 100 if premium > 0 else 0
            
            if vega_percentage > 20:
                sensitivity_level = "very_high"
            elif vega_percentage > 10:
                sensitivity_level = "high"
            elif vega_percentage > 5:
                sensitivity_level = "moderate"
            else:
                sensitivity_level = "low"
            
            return {
                "vega_percentage": vega_percentage,
                "sensitivity_level": sensitivity_level,
                "volatility_impact": f"{vega_percentage:.1f}% per 1% vol change"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volatility sensitivity: {e}")
            return {}
    
    async def _find_best_options(self, analyzed_options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find best options for different strategies"""
        try:
            best_options = {
                "best_call": None,
                "best_put": None,
                "best_atm_call": None,
                "best_atm_put": None,
                "best_otm_call": None,
                "best_otm_put": None,
                "highest_delta": None,
                "highest_gamma": None,
                "best_theta": None,
                "highest_vega": None
            }
            
            calls = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.CALL]
            puts = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.PUT]
            
            if calls:
                # Best call overall
                best_options["best_call"] = max(calls, key=lambda x: x["analysis_score"])
                
                # Best ATM call
                atm_calls = [opt for opt in calls if opt["moneyness_category"] == "atm"]
                if atm_calls:
                    best_options["best_atm_call"] = max(atm_calls, key=lambda x: x["analysis_score"])
                
                # Best OTM call
                otm_calls = [opt for opt in calls if opt["moneyness_category"] in ["otm", "deep_otm"]]
                if otm_calls:
                    best_options["best_otm_call"] = max(otm_calls, key=lambda x: x["analysis_score"])
            
            if puts:
                # Best put overall
                best_options["best_put"] = max(puts, key=lambda x: x["analysis_score"])
                
                # Best ATM put
                atm_puts = [opt for opt in puts if opt["moneyness_category"] == "atm"]
                if atm_puts:
                    best_options["best_atm_put"] = max(atm_puts, key=lambda x: x["analysis_score"])
                
                # Best OTM put
                otm_puts = [opt for opt in puts if opt["moneyness_category"] in ["otm", "deep_otm"]]
                if otm_puts:
                    best_options["best_otm_put"] = max(otm_puts, key=lambda x: x["analysis_score"])
            
            # Find options with extreme Greek values
            all_options = analyzed_options
            
            if all_options:
                best_options["highest_delta"] = max(all_options, key=lambda x: abs(x["delta"]))
                best_options["highest_gamma"] = max(all_options, key=lambda x: x["gamma"])
                best_options["best_theta"] = max(all_options, key=lambda x: x["theta"])
                best_options["highest_vega"] = max(all_options, key=lambda x: x["vega"])
            
            return best_options
            
        except Exception as e:
            logger.error(f"Error finding best options: {e}")
            return {}
    
    async def _generate_strategy_recommendations(
        self,
        analyzed_options: List[Dict[str, Any]],
        underlying_price: float,
        days_to_expiry: int
    ) -> List[Dict[str, Any]]:
        """Generate options strategy recommendations"""
        try:
            recommendations = []
            
            # Analyze market conditions
            market_conditions = await self._analyze_market_conditions("", underlying_price)
            
            # Generate recommendations based on market conditions
            if market_conditions["volatility_regime"] == "high":
                # High volatility strategies
                recommendations.extend([
                    await self._recommend_straddle_strategy(analyzed_options),
                    await self._recommend_strangle_strategy(analyzed_options)
                ])
            
            if market_conditions["trend_strength"] == "strong":
                # Trend-following strategies
                if market_conditions["trend_direction"] == "bullish":
                    recommendations.extend([
                        await self._recommend_long_call_strategy(analyzed_options),
                        await self._recommend_covered_call_strategy(analyzed_options)
                    ])
                else:
                    recommendations.extend([
                        await self._recommend_long_put_strategy(analyzed_options),
                        await self._recommend_protective_put_strategy(analyzed_options)
                    ])
            
            if market_conditions["volatility_regime"] == "low":
                # Low volatility strategies
                recommendations.extend([
                    await self._recommend_butterfly_strategy(analyzed_options),
                    await self._recommend_iron_condor_strategy(analyzed_options)
                ])
            
            # Filter out None recommendations
            recommendations = [rec for rec in recommendations if rec is not None]
            
            # Sort by recommendation score
            recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating strategy recommendations: {e}")
            return []
    
    async def _recommend_straddle_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend straddle strategy"""
        try:
            # Find ATM call and put
            atm_calls = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.CALL and opt["moneyness_category"] == "atm"]
            atm_puts = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.PUT and opt["moneyness_category"] == "atm"]
            
            if not atm_calls or not atm_puts:
                return None
            
            call_option = atm_calls[0]
            put_option = atm_puts[0]
            
            total_premium = call_option["premium"] + put_option["premium"]
            max_loss = total_premium
            max_profit = "Unlimited"
            
            # Calculate breakeven points
            breakeven_up = call_option["strike"] + total_premium
            breakeven_down = put_option["strike"] - total_premium
            
            recommendation_score = 0.0
            
            # Score based on volatility
            if call_option["vega"] > 0.1 and put_option["vega"] > 0.1:
                recommendation_score += 0.3
            
            # Score based on time decay
            if call_option["theta"] < -0.05 and put_option["theta"] < -0.05:
                recommendation_score += 0.2
            
            # Score based on gamma
            if call_option["gamma"] > 0.01 and put_option["gamma"] > 0.01:
                recommendation_score += 0.2
            
            return {
                "strategy": OptionsStrategy.STRADDLE,
                "strategy_name": "Long Straddle",
                "description": "Buy ATM call and put for volatility play",
                "legs": [
                    {"type": "long_call", "strike": call_option["strike"], "premium": call_option["premium"]},
                    {"type": "long_put", "strike": put_option["strike"], "premium": put_option["premium"]}
                ],
                "total_premium": total_premium,
                "max_loss": max_loss,
                "max_profit": max_profit,
                "breakeven_points": [breakeven_up, breakeven_down],
                "recommendation_score": recommendation_score,
                "risk_level": RiskLevel.HIGH,
                "suitable_for": ["High volatility", "Earnings", "Uncertain direction"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending straddle strategy: {e}")
            return None
    
    async def _recommend_long_call_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend long call strategy"""
        try:
            # Find best call option
            calls = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.CALL]
            if not calls:
                return None
            
            best_call = max(calls, key=lambda x: x["analysis_score"])
            
            recommendation_score = best_call["analysis_score"]
            
            return {
                "strategy": OptionsStrategy.LONG_CALL,
                "strategy_name": "Long Call",
                "description": f"Buy call option for bullish outlook",
                "legs": [
                    {"type": "long_call", "strike": best_call["strike"], "premium": best_call["premium"]}
                ],
                "total_premium": best_call["premium"],
                "max_loss": best_call["premium"],
                "max_profit": "Unlimited",
                "breakeven": best_call["strike"] + best_call["premium"],
                "recommendation_score": recommendation_score,
                "risk_level": RiskLevel.MEDIUM,
                "suitable_for": ["Bullish outlook", "Trend following", "Volatility expansion"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending long call strategy: {e}")
            return None
    
    async def _recommend_long_put_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend long put strategy"""
        try:
            # Find best put option
            puts = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.PUT]
            if not puts:
                return None
            
            best_put = max(puts, key=lambda x: x["analysis_score"])
            
            recommendation_score = best_put["analysis_score"]
            
            return {
                "strategy": OptionsStrategy.LONG_PUT,
                "strategy_name": "Long Put",
                "description": f"Buy put option for bearish outlook",
                "legs": [
                    {"type": "long_put", "strike": best_put["strike"], "premium": best_put["premium"]}
                ],
                "total_premium": best_put["premium"],
                "max_loss": best_put["premium"],
                "max_profit": best_put["strike"] - best_put["premium"],
                "breakeven": best_put["strike"] - best_put["premium"],
                "recommendation_score": recommendation_score,
                "risk_level": RiskLevel.MEDIUM,
                "suitable_for": ["Bearish outlook", "Protection", "Volatility expansion"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending long put strategy: {e}")
            return None
    
    async def _recommend_covered_call_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend covered call strategy"""
        try:
            # Find OTM call for covered call
            otm_calls = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.CALL and opt["moneyness_category"] in ["otm", "deep_otm"]]
            if not otm_calls:
                return None
            
            best_call = max(otm_calls, key=lambda x: x["premium"])  # Highest premium
            
            return {
                "strategy": OptionsStrategy.COVERED_CALL,
                "strategy_name": "Covered Call",
                "description": "Sell call against long stock for income",
                "legs": [
                    {"type": "long_stock", "quantity": 100, "price": "current_price"},
                    {"type": "short_call", "strike": best_call["strike"], "premium": best_call["premium"]}
                ],
                "total_premium": best_call["premium"],
                "max_loss": "Stock price - Premium",
                "max_profit": best_call["strike"] - "stock_price" + best_call["premium"],
                "breakeven": "stock_price - Premium",
                "recommendation_score": 0.7,
                "risk_level": RiskLevel.LOW,
                "suitable_for": ["Income generation", "Neutral outlook", "High volatility"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending covered call strategy: {e}")
            return None
    
    async def _recommend_protective_put_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend protective put strategy"""
        try:
            # Find ATM or ITM put for protection
            protective_puts = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.PUT and opt["moneyness_category"] in ["atm", "itm"]]
            if not protective_puts:
                return None
            
            best_put = min(protective_puts, key=lambda x: x["premium"])  # Lowest premium
            
            return {
                "strategy": OptionsStrategy.PROTECTIVE_PUT,
                "strategy_name": "Protective Put",
                "description": "Buy put to protect long stock position",
                "legs": [
                    {"type": "long_stock", "quantity": 100, "price": "current_price"},
                    {"type": "long_put", "strike": best_put["strike"], "premium": best_put["premium"]}
                ],
                "total_premium": best_put["premium"],
                "max_loss": best_put["premium"],
                "max_profit": "Unlimited",
                "breakeven": "stock_price + Premium",
                "recommendation_score": 0.6,
                "risk_level": RiskLevel.LOW,
                "suitable_for": ["Portfolio protection", "Risk management", "Volatile markets"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending protective put strategy: {e}")
            return None
    
    async def _recommend_butterfly_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend butterfly spread strategy"""
        try:
            # Find options for butterfly spread
            calls = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.CALL]
            if len(calls) < 3:
                return None
            
            # Sort by strike
            calls.sort(key=lambda x: x["strike"])
            
            # Find ATM call
            atm_calls = [opt for opt in calls if opt["moneyness_category"] == "atm"]
            if not atm_calls:
                return None
            
            atm_call = atm_calls[0]
            atm_strike = atm_call["strike"]
            
            # Find wings
            wing_calls = [opt for opt in calls if abs(opt["strike"] - atm_strike) > 5]
            if len(wing_calls) < 2:
                return None
            
            wing_calls.sort(key=lambda x: abs(x["strike"] - atm_strike))
            lower_wing = wing_calls[0]
            upper_wing = wing_calls[1]
            
            # Calculate net premium
            net_premium = lower_wing["premium"] + upper_wing["premium"] - 2 * atm_call["premium"]
            
            return {
                "strategy": OptionsStrategy.BUTTERFLY,
                "strategy_name": "Butterfly Spread",
                "description": "Limited risk/reward spread strategy",
                "legs": [
                    {"type": "long_call", "strike": lower_wing["strike"], "premium": lower_wing["premium"]},
                    {"type": "short_call", "strike": atm_call["strike"], "premium": atm_call["premium"], "quantity": 2},
                    {"type": "long_call", "strike": upper_wing["strike"], "premium": upper_wing["premium"]}
                ],
                "net_premium": net_premium,
                "max_loss": abs(net_premium),
                "max_profit": "Limited",
                "recommendation_score": 0.5,
                "risk_level": RiskLevel.LOW,
                "suitable_for": ["Range-bound markets", "Income generation", "Low volatility"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending butterfly strategy: {e}")
            return None
    
    async def _recommend_iron_condor_strategy(self, analyzed_options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Recommend iron condor strategy"""
        try:
            # This is a simplified version - in practice, you'd want more sophisticated selection
            calls = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.CALL]
            puts = [opt for opt in analyzed_options if opt["option_type"] == OptionsType.PUT]
            
            if len(calls) < 2 or len(puts) < 2:
                return None
            
            # Sort by strike
            calls.sort(key=lambda x: x["strike"])
            puts.sort(key=lambda x: x["strike"])
            
            # Select strikes for iron condor
            put_short = puts[len(puts)//2]
            put_long = puts[0]
            call_short = calls[len(calls)//2]
            call_long = calls[-1]
            
            net_premium = put_short["premium"] + call_short["premium"] - put_long["premium"] - call_long["premium"]
            
            return {
                "strategy": OptionsStrategy.IRON_CONDOR,
                "strategy_name": "Iron Condor",
                "description": "Four-leg spread for income",
                "legs": [
                    {"type": "long_put", "strike": put_long["strike"], "premium": put_long["premium"]},
                    {"type": "short_put", "strike": put_short["strike"], "premium": put_short["premium"]},
                    {"type": "short_call", "strike": call_short["strike"], "premium": call_short["premium"]},
                    {"type": "long_call", "strike": call_long["strike"], "premium": call_long["premium"]}
                ],
                "net_premium": net_premium,
                "max_loss": "Limited",
                "max_profit": "Limited",
                "recommendation_score": 0.4,
                "risk_level": RiskLevel.LOW,
                "suitable_for": ["Range-bound markets", "Income generation", "Low volatility"]
            }
            
        except Exception as e:
            logger.error(f"Error recommending iron condor strategy: {e}")
            return None
    
    async def _analyze_market_conditions(self, symbol: str, underlying_price: float) -> Dict[str, Any]:
        """Analyze market conditions for options trading"""
        try:
            # This would integrate with your market analysis services
            # For now, return mock data
            
            return {
                "volatility_regime": "normal",  # low, normal, high
                "trend_strength": "moderate",  # weak, moderate, strong
                "trend_direction": "bullish",  # bullish, bearish, sideways
                "market_sentiment": "neutral",  # bullish, bearish, neutral
                "volume_profile": "normal",  # low, normal, high
                "support_resistance": "balanced"  # support, resistance, balanced
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {}
    
    async def _analyze_options_risk(self, analyzed_options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall risk of options positions"""
        try:
            risk_analysis = {
                "total_delta": 0.0,
                "total_gamma": 0.0,
                "total_theta": 0.0,
                "total_vega": 0.0,
                "portfolio_risk": RiskLevel.MEDIUM,
                "risk_warnings": [],
                "risk_metrics": {}
            }
            
            # Calculate portfolio Greeks
            for option in analyzed_options:
                # This would be weighted by position size
                risk_analysis["total_delta"] += option["delta"]
                risk_analysis["total_gamma"] += option["gamma"]
                risk_analysis["total_theta"] += option["theta"]
                risk_analysis["total_vega"] += option["vega"]
            
            # Assess portfolio risk
            if abs(risk_analysis["total_delta"]) > 0.5:
                risk_analysis["risk_warnings"].append("High delta exposure")
            
            if risk_analysis["total_theta"] < -0.1:
                risk_analysis["risk_warnings"].append("High time decay")
            
            if risk_analysis["total_vega"] > 0.2:
                risk_analysis["risk_warnings"].append("High volatility exposure")
            
            # Determine overall risk level
            if len(risk_analysis["risk_warnings"]) > 2:
                risk_analysis["portfolio_risk"] = RiskLevel.HIGH
            elif len(risk_analysis["risk_warnings"]) > 0:
                risk_analysis["portfolio_risk"] = RiskLevel.MEDIUM
            else:
                risk_analysis["portfolio_risk"] = RiskLevel.LOW
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing options risk: {e}")
            return {}
    
    async def _calculate_implied_volatility(self, symbol: str, underlying_price: float, days_to_expiry: int) -> float:
        """Calculate implied volatility for the symbol"""
        try:
            # This would integrate with your volatility calculation service
            # For now, return a mock value
            base_volatility = 0.25  # 25% base volatility
            
            # Adjust based on days to expiry
            if days_to_expiry < 7:
                volatility_multiplier = 1.2  # Higher vol for short-term
            elif days_to_expiry < 30:
                volatility_multiplier = 1.0  # Normal vol
            else:
                volatility_multiplier = 0.8  # Lower vol for long-term
            
            return base_volatility * volatility_multiplier
            
        except Exception as e:
            logger.error(f"Error calculating implied volatility: {e}")
            return 0.25
    
    async def get_strategy_performance(self, strategy: OptionsStrategy) -> Dict[str, Any]:
        """Get performance statistics for a specific strategy"""
        try:
            if strategy not in self.performance_tracking["strategy_performance"]:
                return {
                    "strategy": strategy,
                    "total_trades": 0,
                    "profitable_trades": 0,
                    "win_rate": 0.0,
                    "average_pnl": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0
                }
            
            perf = self.performance_tracking["strategy_performance"][strategy]
            
            return {
                "strategy": strategy,
                "total_trades": perf["total_trades"],
                "profitable_trades": perf["profitable_trades"],
                "win_rate": perf["profitable_trades"] / perf["total_trades"] if perf["total_trades"] > 0 else 0,
                "average_pnl": perf["total_pnl"] / perf["total_trades"] if perf["total_trades"] > 0 else 0,
                "max_drawdown": perf["max_drawdown"],
                "sharpe_ratio": perf["sharpe_ratio"]
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if options trading AI is available"""
        try:
            return len(self.strategies_database) > 0
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear options analysis cache"""
        self.options_cache.clear()
        logger.info("Options trading AI cache cleared")
