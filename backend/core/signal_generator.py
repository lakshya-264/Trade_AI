"""
Signal Generator Service
Generates trading signals based on technical analysis and market conditions
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SignalGeneratorService:
    """Generates trading signals based on multiple indicators"""
    
    def __init__(self):
        self.signal_weights = {
            'rsi': 0.2,
            'macd': 0.25,
            'sma': 0.15,
            'bollinger': 0.15,
            'volume': 0.1,
            'momentum': 0.15
        }
    
    def generate_signal(self, symbol: str, technical_data: Dict, price_data: Dict, 
                       sentiment_data: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive trading signal"""
        try:
            # Calculate individual signal scores
            rsi_signal = self._analyze_rsi_signal(technical_data.get('rsi', 50))
            macd_signal = self._analyze_macd_signal(technical_data.get('macd', {}))
            sma_signal = self._analyze_sma_signal(technical_data.get('sma_20', 0), 
                                                technical_data.get('sma_50', 0), 
                                                price_data.get('current', 0))
            bollinger_signal = self._analyze_bollinger_signal(technical_data.get('bollinger_bands', {}), 
                                                            price_data.get('current', 0))
            volume_signal = self._analyze_volume_signal(technical_data.get('volume_trend', {}))
            momentum_signal = self._analyze_momentum_signal(technical_data.get('momentum', 0))
            
            # Calculate weighted signal score
            signal_score = (
                rsi_signal['score'] * self.signal_weights['rsi'] +
                macd_signal['score'] * self.signal_weights['macd'] +
                sma_signal['score'] * self.signal_weights['sma'] +
                bollinger_signal['score'] * self.signal_weights['bollinger'] +
                volume_signal['score'] * self.signal_weights['volume'] +
                momentum_signal['score'] * self.signal_weights['momentum']
            )
            
            # Determine signal strength and direction
            if signal_score > 0.3:
                signal = "BUY"
                strength = "STRONG" if signal_score > 0.6 else "MODERATE"
            elif signal_score < -0.3:
                signal = "SELL"
                strength = "STRONG" if signal_score < -0.6 else "MODERATE"
            else:
                signal = "HOLD"
                strength = "NEUTRAL"
            
            # Calculate confidence based on signal consistency
            confidence = self._calculate_confidence([
                rsi_signal, macd_signal, sma_signal, bollinger_signal, 
                volume_signal, momentum_signal
            ])
            
            # Generate price targets and stop loss
            current_price = price_data.get('current', 0)
            price_targets = self._calculate_price_targets(signal, current_price, signal_score)
            
            # Risk assessment
            risk_level = self._assess_risk(signal_score, confidence, technical_data)
            
            # Timeframe recommendation
            timeframe = self._recommend_timeframe(signal, signal_score, technical_data)
            
            return {
                "symbol": symbol,
                "signal": signal,
                "strength": strength,
                "score": round(signal_score, 3),
                "confidence": round(confidence, 3),
                "price_targets": price_targets,
                "risk_level": risk_level,
                "timeframe": timeframe,
                "reasoning": self._generate_reasoning({
                    'rsi': rsi_signal,
                    'macd': macd_signal,
                    'sma': sma_signal,
                    'bollinger': bollinger_signal,
                    'volume': volume_signal,
                    'momentum': momentum_signal
                }, signal, signal_score),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Signal generation error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "signal": "ERROR",
                "strength": "UNKNOWN",
                "score": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_rsi_signal(self, rsi: float) -> Dict[str, Any]:
        """Analyze RSI signal"""
        if rsi < 30:
            return {"signal": "BUY", "score": 0.8, "reasoning": "Oversold condition"}
        elif rsi > 70:
            return {"signal": "SELL", "score": 0.8, "reasoning": "Overbought condition"}
        elif 30 <= rsi <= 40:
            return {"signal": "BUY", "score": 0.4, "reasoning": "Approaching oversold"}
        elif 60 <= rsi <= 70:
            return {"signal": "SELL", "score": 0.4, "reasoning": "Approaching overbought"}
        else:
            return {"signal": "HOLD", "score": 0.0, "reasoning": "Neutral RSI"}
    
    def _analyze_macd_signal(self, macd_data: Dict) -> Dict[str, Any]:
        """Analyze MACD signal"""
        try:
            macd = macd_data.get('macd', 0)
            signal = macd_data.get('signal', 0)
            histogram = macd_data.get('histogram', 0)
            
            if macd > signal and histogram > 0:
                return {"signal": "BUY", "score": 0.7, "reasoning": "MACD bullish crossover"}
            elif macd < signal and histogram < 0:
                return {"signal": "SELL", "score": 0.7, "reasoning": "MACD bearish crossover"}
            elif macd > signal:
                return {"signal": "BUY", "score": 0.3, "reasoning": "MACD above signal line"}
            elif macd < signal:
                return {"signal": "SELL", "score": 0.3, "reasoning": "MACD below signal line"}
            else:
                return {"signal": "HOLD", "score": 0.0, "reasoning": "MACD neutral"}
        except:
            return {"signal": "HOLD", "score": 0.0, "reasoning": "MACD data unavailable"}
    
    def _analyze_sma_signal(self, sma_20: float, sma_50: float, current_price: float) -> Dict[str, Any]:
        """Analyze SMA signal"""
        try:
            if current_price == 0:
                return {"signal": "HOLD", "score": 0.0, "reasoning": "No price data"}
            
            if current_price > sma_20 > sma_50:
                return {"signal": "BUY", "score": 0.6, "reasoning": "Price above both SMAs (bullish trend)"}
            elif current_price < sma_20 < sma_50:
                return {"signal": "SELL", "score": 0.6, "reasoning": "Price below both SMAs (bearish trend)"}
            elif current_price > sma_20:
                return {"signal": "BUY", "score": 0.3, "reasoning": "Price above 20-day SMA"}
            elif current_price < sma_20:
                return {"signal": "SELL", "score": 0.3, "reasoning": "Price below 20-day SMA"}
            else:
                return {"signal": "HOLD", "score": 0.0, "reasoning": "Price near SMA"}
        except:
            return {"signal": "HOLD", "score": 0.0, "reasoning": "SMA data unavailable"}
    
    def _analyze_bollinger_signal(self, bollinger_data: Dict, current_price: float) -> Dict[str, Any]:
        """Analyze Bollinger Bands signal"""
        try:
            upper = bollinger_data.get('upper', 0)
            middle = bollinger_data.get('middle', 0)
            lower = bollinger_data.get('lower', 0)
            
            if current_price == 0 or upper == 0:
                return {"signal": "HOLD", "score": 0.0, "reasoning": "No Bollinger data"}
            
            if current_price <= lower:
                return {"signal": "BUY", "score": 0.7, "reasoning": "Price at lower Bollinger Band (oversold)"}
            elif current_price >= upper:
                return {"signal": "SELL", "score": 0.7, "reasoning": "Price at upper Bollinger Band (overbought)"}
            elif current_price < middle:
                return {"signal": "BUY", "score": 0.3, "reasoning": "Price below middle band"}
            elif current_price > middle:
                return {"signal": "SELL", "score": 0.3, "reasoning": "Price above middle band"}
            else:
                return {"signal": "HOLD", "score": 0.0, "reasoning": "Price near middle band"}
        except:
            return {"signal": "HOLD", "score": 0.0, "reasoning": "Bollinger data unavailable"}
    
    def _analyze_volume_signal(self, volume_data: Dict) -> Dict[str, Any]:
        """Analyze volume signal"""
        try:
            trend = volume_data.get('trend', 'neutral')
            ratio = volume_data.get('ratio', 1.0)
            
            if trend == "increasing" and ratio > 1.5:
                return {"signal": "BUY", "score": 0.5, "reasoning": "High volume increase (bullish)"}
            elif trend == "decreasing" and ratio < 0.7:
                return {"signal": "SELL", "score": 0.5, "reasoning": "Low volume (bearish)"}
            elif trend == "increasing":
                return {"signal": "BUY", "score": 0.2, "reasoning": "Volume increasing"}
            elif trend == "decreasing":
                return {"signal": "SELL", "score": 0.2, "reasoning": "Volume decreasing"}
            else:
                return {"signal": "HOLD", "score": 0.0, "reasoning": "Volume stable"}
        except:
            return {"signal": "HOLD", "score": 0.0, "reasoning": "Volume data unavailable"}
    
    def _analyze_momentum_signal(self, momentum: float) -> Dict[str, Any]:
        """Analyze momentum signal"""
        if momentum > 5:
            return {"signal": "BUY", "score": 0.6, "reasoning": f"Strong positive momentum ({momentum:.1f}%)"}
        elif momentum < -5:
            return {"signal": "SELL", "score": 0.6, "reasoning": f"Strong negative momentum ({momentum:.1f}%)"}
        elif momentum > 2:
            return {"signal": "BUY", "score": 0.3, "reasoning": f"Positive momentum ({momentum:.1f}%)"}
        elif momentum < -2:
            return {"signal": "SELL", "score": 0.3, "reasoning": f"Negative momentum ({momentum:.1f}%)"}
        else:
            return {"signal": "HOLD", "score": 0.0, "reasoning": f"Neutral momentum ({momentum:.1f}%)"}
    
    def _calculate_confidence(self, signals: List[Dict]) -> float:
        """Calculate overall confidence based on signal consistency"""
        try:
            buy_signals = sum(1 for s in signals if s['signal'] == 'BUY')
            sell_signals = sum(1 for s in signals if s['signal'] == 'SELL')
            hold_signals = sum(1 for s in signals if s['signal'] == 'HOLD')
            
            total_signals = len(signals)
            if total_signals == 0:
                return 0.0
            
            # Calculate consistency
            max_consistency = max(buy_signals, sell_signals, hold_signals)
            consistency_ratio = max_consistency / total_signals
            
            # Calculate average score magnitude
            avg_score = sum(abs(s['score']) for s in signals) / total_signals
            
            # Combine consistency and score magnitude
            confidence = (consistency_ratio * 0.6) + (avg_score * 0.4)
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.5
    
    def _calculate_price_targets(self, signal: str, current_price: float, signal_score: float) -> Dict[str, float]:
        """Calculate price targets and stop loss"""
        try:
            if current_price == 0:
                return {"entry": 0, "target": 0, "stop_loss": 0}
            
            # Calculate target and stop loss based on signal strength
            strength_multiplier = abs(signal_score) * 2  # 0 to 2x multiplier
            
            if signal == "BUY":
                target = current_price * (1 + 0.05 * strength_multiplier)  # 0-10% upside
                stop_loss = current_price * (1 - 0.03 * strength_multiplier)  # 0-6% downside
            elif signal == "SELL":
                target = current_price * (1 - 0.05 * strength_multiplier)  # 0-10% downside
                stop_loss = current_price * (1 + 0.03 * strength_multiplier)  # 0-6% upside
            else:
                target = current_price
                stop_loss = current_price
            
            return {
                "entry": round(current_price, 2),
                "target": round(target, 2),
                "stop_loss": round(stop_loss, 2)
            }
            
        except Exception as e:
            logger.error(f"Price target calculation error: {e}")
            return {"entry": current_price, "target": current_price, "stop_loss": current_price}
    
    def _assess_risk(self, signal_score: float, confidence: float, technical_data: Dict) -> str:
        """Assess risk level"""
        try:
            # Base risk on signal strength and confidence
            risk_score = abs(signal_score) * (1 - confidence)  # Higher score + lower confidence = higher risk
            
            if risk_score < 0.2:
                return "LOW"
            elif risk_score < 0.4:
                return "MEDIUM"
            else:
                return "HIGH"
                
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return "MEDIUM"
    
    def _recommend_timeframe(self, signal: str, signal_score: float, technical_data: Dict) -> str:
        """Recommend trading timeframe"""
        try:
            # Analyze volatility and trend strength
            rsi = technical_data.get('rsi', 50)
            momentum = technical_data.get('momentum', 0)
            
            # Determine timeframe based on signal strength and volatility
            if abs(signal_score) > 0.6 and abs(momentum) > 5:
                return "1-3 days"  # Short-term for strong signals
            elif abs(signal_score) > 0.4:
                return "1-2 weeks"  # Medium-term for moderate signals
            else:
                return "2-4 weeks"  # Long-term for weak signals
                
        except Exception as e:
            logger.error(f"Timeframe recommendation error: {e}")
            return "1-2 weeks"
    
    def _generate_reasoning(self, signals: Dict, overall_signal: str, signal_score: float) -> str:
        """Generate human-readable reasoning"""
        try:
            reasoning_parts = []
            
            # Add reasoning for each indicator
            for indicator, data in signals.items():
                if data['score'] != 0:
                    reasoning_parts.append(f"{indicator.upper()}: {data['reasoning']}")
            
            # Add overall assessment
            if overall_signal == "BUY":
                reasoning_parts.append(f"Overall: Bullish signals with {signal_score:.1%} strength")
            elif overall_signal == "SELL":
                reasoning_parts.append(f"Overall: Bearish signals with {signal_score:.1%} strength")
            else:
                reasoning_parts.append("Overall: Mixed signals, maintaining neutral position")
            
            return " | ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Reasoning generation error: {e}")
            return "Signal analysis completed"
