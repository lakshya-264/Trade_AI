"""
Futures & Options (F&O) Trading Algorithms
Comprehensive algorithms for Futures and Options trading including:
- Open Interest Analysis
- Option Chain Analysis
- Futures Spread Trading
- Options Strategies
- F&O Risk Management
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum

logger = logging.getLogger(__name__)

class FNOStrategy(str, Enum):
    """F&O Trading Strategies"""
    # Futures Strategies
    FUTURES_LONG = "futures_long"
    FUTURES_SHORT = "futures_short"
    FUTURES_SPREAD = "futures_spread"
    FUTURES_ARBITRAGE = "futures_arbitrage"
    CALENDAR_SPREAD = "calendar_spread"
    
    # Options Strategies
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    BUTTERFLY = "butterfly"
    IRON_CONDOR = "iron_condor"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    
    # Advanced Strategies
    DELTA_NEUTRAL = "delta_neutral"
    GAMMA_SCALPING = "gamma_scalping"
    THETA_DECAY = "theta_decay"
    VOLATILITY_ARBITRAGE = "volatility_arbitrage"

class OIAnalysis(str, Enum):
    """Open Interest Analysis Types"""
    LONG_BUILDUP = "long_buildup"  # Price ↑ + OI ↑
    SHORT_BUILDUP = "short_buildup"  # Price ↓ + OI ↑
    LONG_UNWINDING = "long_unwinding"  # Price ↓ + OI ↓
    SHORT_COVERING = "short_covering"  # Price ↑ + OI ↓

class FNOTradingAlgorithms:
    """Futures & Options Trading Algorithms"""
    
    def __init__(self):
        self.oi_cache = {}
        self.option_chain_cache = {}
        self.cache_ttl = 60  # 1 minute for F&O data
        
    def analyze_open_interest(
        self,
        current_price: float,
        previous_price: float,
        current_oi: float,
        previous_oi: float
    ) -> Dict[str, Any]:
        """
        Analyze Open Interest to determine market sentiment
        
        Returns:
        - long_buildup: Price ↑ + OI ↑ (Bullish)
        - short_buildup: Price ↓ + OI ↑ (Bearish)
        - long_unwinding: Price ↓ + OI ↓ (Bearish)
        - short_covering: Price ↑ + OI ↓ (Bullish)
        """
        price_change = current_price - previous_price
        oi_change = current_oi - previous_oi
        price_change_pct = (price_change / previous_price) * 100 if previous_price > 0 else 0
        oi_change_pct = (oi_change / previous_oi) * 100 if previous_oi > 0 else 0
        
        # Determine OI Analysis
        if price_change > 0 and oi_change > 0:
            analysis_type = OIAnalysis.LONG_BUILDUP
            sentiment = "Bullish"
            strength = min(abs(price_change_pct), abs(oi_change_pct)) / 10.0
        elif price_change < 0 and oi_change > 0:
            analysis_type = OIAnalysis.SHORT_BUILDUP
            sentiment = "Bearish"
            strength = min(abs(price_change_pct), abs(oi_change_pct)) / 10.0
        elif price_change < 0 and oi_change < 0:
            analysis_type = OIAnalysis.LONG_UNWINDING
            sentiment = "Bearish"
            strength = min(abs(price_change_pct), abs(oi_change_pct)) / 10.0
        elif price_change > 0 and oi_change < 0:
            analysis_type = OIAnalysis.SHORT_COVERING
            sentiment = "Bullish"
            strength = min(abs(price_change_pct), abs(oi_change_pct)) / 10.0
        else:
            analysis_type = None
            sentiment = "Neutral"
            strength = 0.0
        
        return {
            "analysis_type": analysis_type.value if analysis_type else None,
            "sentiment": sentiment,
            "strength": min(strength, 1.0),
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "oi_change": oi_change,
            "oi_change_pct": oi_change_pct,
            "current_price": current_price,
            "current_oi": current_oi,
            "signal": self._generate_oi_signal(analysis_type, strength)
        }
    
    def _generate_oi_signal(self, analysis_type: Optional[OIAnalysis], strength: float) -> str:
        """Generate trading signal based on OI analysis"""
        if not analysis_type or strength < 0.3:
            return "HOLD"
        
        if analysis_type == OIAnalysis.LONG_BUILDUP:
            return "STRONG_BUY" if strength > 0.7 else "BUY"
        elif analysis_type == OIAnalysis.SHORT_COVERING:
            return "BUY" if strength > 0.5 else "WEAK_BUY"
        elif analysis_type == OIAnalysis.SHORT_BUILDUP:
            return "STRONG_SELL" if strength > 0.7 else "SELL"
        elif analysis_type == OIAnalysis.LONG_UNWINDING:
            return "SELL" if strength > 0.5 else "WEAK_SELL"
        
        return "HOLD"
    
    def calculate_pcr(self, put_oi: float, call_oi: float) -> Dict[str, Any]:
        """
        Calculate Put-Call Ratio (PCR)
        PCR > 1: More puts (Bearish sentiment)
        PCR < 1: More calls (Bullish sentiment)
        """
        if call_oi == 0:
            pcr = float('inf') if put_oi > 0 else 0
        else:
            pcr = put_oi / call_oi
        
        # Interpret PCR
        if pcr > 1.5:
            sentiment = "Very Bearish"
            signal = "STRONG_SELL"
        elif pcr > 1.2:
            sentiment = "Bearish"
            signal = "SELL"
        elif pcr > 0.8:
            sentiment = "Neutral"
            signal = "HOLD"
        elif pcr > 0.6:
            sentiment = "Bullish"
            signal = "BUY"
        else:
            sentiment = "Very Bullish"
            signal = "STRONG_BUY"
        
        return {
            "pcr": pcr,
            "put_oi": put_oi,
            "call_oi": call_oi,
            "sentiment": sentiment,
            "signal": signal,
            "interpretation": self._get_pcr_interpretation(pcr)
        }
    
    def _get_pcr_interpretation(self, pcr: float) -> str:
        """Get interpretation of PCR value"""
        if pcr > 1.5:
            return "Extreme bearish sentiment - Market may be oversold"
        elif pcr > 1.2:
            return "Bearish sentiment - Puts are expensive"
        elif pcr > 0.8:
            return "Neutral sentiment - Balanced market"
        elif pcr > 0.6:
            return "Bullish sentiment - Calls are expensive"
        else:
            return "Extreme bullish sentiment - Market may be overbought"
    
    def find_max_pain(
        self,
        strikes: List[float],
        call_oi: List[float],
        put_oi: List[float],
        current_price: float
    ) -> Dict[str, Any]:
        """
        Calculate Maximum Pain Point
        The strike price where option writers have maximum profit
        """
        if not strikes or len(call_oi) != len(strikes) or len(put_oi) != len(strikes):
            return {"error": "Invalid data"}
        
        max_pain = None
        min_pain_value = float('inf')
        
        for strike in strikes:
            total_pain = 0
            
            # Calculate pain for calls (ITM calls cause pain)
            for i, s in enumerate(strikes):
                if s < strike:  # ITM calls
                    total_pain += call_oi[i] * (strike - s)
            
            # Calculate pain for puts (ITM puts cause pain)
            for i, s in enumerate(strikes):
                if s > strike:  # ITM puts
                    total_pain += put_oi[i] * (s - strike)
            
            if total_pain < min_pain_value:
                min_pain_value = total_pain
                max_pain = strike
        
        distance_from_price = abs(max_pain - current_price) if max_pain else 0
        distance_pct = (distance_from_price / current_price) * 100 if current_price > 0 else 0
        
        return {
            "max_pain": max_pain,
            "current_price": current_price,
            "distance": distance_from_price,
            "distance_pct": distance_pct,
            "signal": "BEARISH" if max_pain < current_price else "BULLISH" if max_pain > current_price else "NEUTRAL",
            "interpretation": self._interpret_max_pain(max_pain, current_price, distance_pct)
        }
    
    def _interpret_max_pain(self, max_pain: float, current_price: float, distance_pct: float) -> str:
        """Interpret max pain analysis"""
        if max_pain is None:
            return "Unable to calculate max pain"
        
        if distance_pct < 1:
            return f"Price is very close to max pain ({max_pain}). Market may consolidate."
        elif max_pain < current_price:
            return f"Max pain ({max_pain}) is below current price. Downward pressure expected."
        else:
            return f"Max pain ({max_pain}) is above current price. Upward pressure expected."
    
    def futures_spread_opportunity(
        self,
        near_month_price: float,
        far_month_price: float,
        near_month_oi: float,
        far_month_oi: float,
        cost_of_carry: float = 0.08  # 8% annual
    ) -> Dict[str, Any]:
        """
        Identify Futures Spread Trading Opportunities
        Calendar spread analysis
        """
        spread = far_month_price - near_month_price
        days_to_expiry = 30  # Approximate
        theoretical_spread = near_month_price * (cost_of_carry / 365) * days_to_expiry
        
        spread_ratio = spread / near_month_price if near_month_price > 0 else 0
        theoretical_ratio = theoretical_spread / near_month_price if near_month_price > 0 else 0
        
        # Determine opportunity
        if spread > theoretical_spread * 1.1:
            opportunity = "SELL_SPREAD"  # Spread is too wide
            signal = "SELL"
            profit_potential = spread - theoretical_spread
        elif spread < theoretical_spread * 0.9:
            opportunity = "BUY_SPREAD"  # Spread is too narrow
            signal = "BUY"
            profit_potential = theoretical_spread - spread
        else:
            opportunity = "NO_OPPORTUNITY"
            signal = "HOLD"
            profit_potential = 0
        
        return {
            "near_month_price": near_month_price,
            "far_month_price": far_month_price,
            "spread": spread,
            "theoretical_spread": theoretical_spread,
            "spread_ratio": spread_ratio,
            "theoretical_ratio": theoretical_ratio,
            "opportunity": opportunity,
            "signal": signal,
            "profit_potential": profit_potential,
            "profit_potential_pct": (profit_potential / near_month_price) * 100 if near_month_price > 0 else 0
        }
    
    def options_strategy_recommendation(
        self,
        current_price: float,
        volatility: float,
        time_to_expiry: int,
        market_sentiment: str,
        risk_tolerance: str = "medium"
    ) -> Dict[str, Any]:
        """
        Recommend Options Strategy based on market conditions
        """
        recommendations = []
        
        # High volatility strategies
        if volatility > 0.3:
            if market_sentiment == "bullish":
                recommendations.append({
                    "strategy": FNOStrategy.LONG_CALL.value,
                    "confidence": 0.7,
                    "reason": "High volatility with bullish sentiment - Long calls benefit from volatility expansion"
                })
            elif market_sentiment == "bearish":
                recommendations.append({
                    "strategy": FNOStrategy.LONG_PUT.value,
                    "confidence": 0.7,
                    "reason": "High volatility with bearish sentiment - Long puts benefit from volatility expansion"
                })
            else:
                recommendations.append({
                    "strategy": FNOStrategy.STRADDLE.value,
                    "confidence": 0.8,
                    "reason": "High volatility with neutral sentiment - Straddle benefits from large moves"
                })
        
        # Low volatility strategies
        elif volatility < 0.15:
            if market_sentiment == "bullish":
                recommendations.append({
                    "strategy": FNOStrategy.BULL_CALL_SPREAD.value,
                    "confidence": 0.75,
                    "reason": "Low volatility with bullish sentiment - Bull call spread reduces cost"
                })
            elif market_sentiment == "bearish":
                recommendations.append({
                    "strategy": FNOStrategy.BEAR_PUT_SPREAD.value,
                    "confidence": 0.75,
                    "reason": "Low volatility with bearish sentiment - Bear put spread reduces cost"
                })
            else:
                recommendations.append({
                    "strategy": FNOStrategy.IRON_CONDOR.value,
                    "confidence": 0.7,
                    "reason": "Low volatility with neutral sentiment - Iron condor benefits from range-bound market"
                })
        
        # Theta decay strategies (close to expiry)
        if time_to_expiry <= 7:
            recommendations.append({
                "strategy": FNOStrategy.THETA_DECAY.value,
                "confidence": 0.8,
                "reason": "Close to expiry - Sell options to benefit from theta decay"
            })
        
        # Risk-based filtering
        if risk_tolerance == "low":
            recommendations = [r for r in recommendations if r["strategy"] not in [
                FNOStrategy.STRADDLE.value,
                FNOStrategy.STRANGLE.value
            ]]
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "recommendations": recommendations[:3],  # Top 3
            "current_price": current_price,
            "volatility": volatility,
            "time_to_expiry": time_to_expiry,
            "market_sentiment": market_sentiment
        }
    
    def calculate_futures_fair_value(
        self,
        spot_price: float,
        risk_free_rate: float = 0.06,
        dividend_yield: float = 0.02,
        days_to_expiry: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate Futures Fair Value
        F = S * e^((r - d) * t)
        """
        time_years = days_to_expiry / 365.0
        fair_value = spot_price * np.exp((risk_free_rate - dividend_yield) * time_years)
        
        return {
            "spot_price": spot_price,
            "fair_value": fair_value,
            "premium": fair_value - spot_price,
            "premium_pct": ((fair_value - spot_price) / spot_price) * 100 if spot_price > 0 else 0,
            "risk_free_rate": risk_free_rate,
            "dividend_yield": dividend_yield,
            "days_to_expiry": days_to_expiry
        }
    
    def generate_fno_signal(
        self,
        price_data: pd.DataFrame,
        oi_data: Optional[pd.DataFrame] = None,
        option_chain: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive F&O trading signal
        Combines price action, OI analysis, and option chain data
        """
        if price_data.empty:
            return {"error": "No price data"}
        
        current_price = price_data['close'].iloc[-1]
        previous_price = price_data['close'].iloc[-2] if len(price_data) > 1 else current_price
        
        signals = []
        confidence_scores = []
        
        # Price momentum signal
        price_change = (current_price - previous_price) / previous_price if previous_price > 0 else 0
        if price_change > 0.02:
            signals.append("BULLISH")
            confidence_scores.append(0.6)
        elif price_change < -0.02:
            signals.append("BEARISH")
            confidence_scores.append(0.6)
        else:
            signals.append("NEUTRAL")
            confidence_scores.append(0.3)
        
        # OI Analysis
        if oi_data is not None and not oi_data.empty:
            oi_analysis = self.analyze_open_interest(
                current_price,
                previous_price,
                oi_data['oi'].iloc[-1] if 'oi' in oi_data.columns else 0,
                oi_data['oi'].iloc[-2] if len(oi_data) > 1 and 'oi' in oi_data.columns else 0
            )
            signals.append(oi_analysis.get("sentiment", "NEUTRAL"))
            confidence_scores.append(oi_analysis.get("strength", 0.5))
        
        # Option Chain Analysis
        if option_chain:
            if 'pcr' in option_chain:
                pcr_analysis = self.calculate_pcr(
                    option_chain.get('put_oi', 0),
                    option_chain.get('call_oi', 0)
                )
                signals.append(pcr_analysis.get("sentiment", "NEUTRAL"))
                confidence_scores.append(0.7)
        
        # Aggregate signal
        bullish_count = signals.count("BULLISH") + signals.count("Bullish")
        bearish_count = signals.count("BEARISH") + signals.count("Bearish")
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.5
        
        if bullish_count > bearish_count:
            final_signal = "BUY"
            strength = "STRONG" if avg_confidence > 0.7 else "MODERATE"
        elif bearish_count > bullish_count:
            final_signal = "SELL"
            strength = "STRONG" if avg_confidence > 0.7 else "MODERATE"
        else:
            final_signal = "HOLD"
            strength = "WEAK"
        
        return {
            "signal": final_signal,
            "strength": strength,
            "confidence": avg_confidence,
            "current_price": current_price,
            "price_change_pct": price_change * 100,
            "signals": signals,
            "recommendation": self._get_fno_recommendation(final_signal, strength, avg_confidence)
        }
    
    def _get_fno_recommendation(self, signal: str, strength: str, confidence: float) -> str:
        """Get human-readable recommendation"""
        if signal == "BUY" and strength == "STRONG":
            return f"Strong buy signal with {confidence:.0%} confidence. Consider long futures or call options."
        elif signal == "BUY":
            return f"Moderate buy signal with {confidence:.0%} confidence. Consider covered calls or bull spreads."
        elif signal == "SELL" and strength == "STRONG":
            return f"Strong sell signal with {confidence:.0%} confidence. Consider short futures or put options."
        elif signal == "SELL":
            return f"Moderate sell signal with {confidence:.0%} confidence. Consider protective puts or bear spreads."
        else:
            return f"Neutral signal. Wait for clearer direction or consider delta-neutral strategies."

