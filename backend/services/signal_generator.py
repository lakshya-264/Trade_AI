"""
Advanced Signal Generator Service
Generates buy/sell signals based on multiple analysis methods
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import asyncio

from .technical_analysis import TechnicalAnalyzer
from .sentiment_analysis import SentimentAnalyzer
from .volume_analyzer import VolumeAnalyzer
from .candlestick_patterns import CandlestickPatternService
from .ai_engine import AIEngine

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.pattern_analyzer = CandlestickPatternService()
        self.ai_engine = AIEngine()
        
        # Signal weights
        self.weights = {
            'technical': 0.3,
            'sentiment': 0.2,
            'volume': 0.2,
            'patterns': 0.2,
            'ai': 0.1
        }
        
        # Signal thresholds
        self.thresholds = {
            'buy': 0.7,
            'sell': 0.7,
            'hold': 0.3
        }
    
    async def generate_comprehensive_signal(self, symbol: str, df: pd.DataFrame, 
                                          exchange: str = "NSE") -> Dict:
        """Generate comprehensive trading signal using all analysis methods"""
        try:
            if len(df) < 20:
                return {"error": "Insufficient data for analysis"}
            
            # Run all analyses in parallel
            analyses = await self._run_all_analyses(symbol, df, exchange)
            
            # Generate individual signals
            signals = self._generate_individual_signals(analyses)
            
            # Combine signals using weighted approach
            combined_signal = self._combine_signals(signals)
            
            # Add pattern analysis
            pattern_analysis = self.pattern_analyzer.analyze_patterns(df)
            
            # Generate final recommendation
            recommendation = self._generate_recommendation(
                combined_signal, pattern_analysis, df
            )
            
            return {
                "symbol": symbol,
                "exchange": exchange,
                "timestamp": datetime.now().isoformat(),
                "recommendation": recommendation,
                "individual_signals": signals,
                "pattern_analysis": pattern_analysis,
                "confidence": combined_signal['confidence'],
                "reasoning": self._generate_reasoning(signals, pattern_analysis),
                "risk_level": self._calculate_risk_level(df, combined_signal),
                "price_targets": self._calculate_price_targets(df, combined_signal),
                "stop_loss": self._calculate_stop_loss(df, combined_signal)
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive signal: {e}")
            return {"error": str(e)}
    
    async def _run_all_analyses(self, symbol: str, df: pd.DataFrame, exchange: str) -> Dict:
        """Run all analysis methods in parallel"""
        try:
            # Technical analysis
            technical_analysis = self.technical_analyzer.analyze(df)
            
            # Sentiment analysis
            sentiment_analysis = await self.sentiment_analyzer.analyze_stock_sentiment(symbol)
            
            # Volume analysis
            volume_analysis = self.volume_analyzer.analyze_volume_patterns(df)
            
            # AI analysis
            ai_analysis = self.ai_engine.generate_signals(df, {
                'technical': technical_analysis,
                'sentiment': sentiment_analysis,
                'volume': volume_analysis
            })
            
            return {
                'technical': technical_analysis,
                'sentiment': sentiment_analysis,
                'volume': volume_analysis,
                'ai': ai_analysis
            }
            
        except Exception as e:
            logger.error(f"Error running analyses: {e}")
            return {}
    
    def _generate_individual_signals(self, analyses: Dict) -> Dict:
        """Generate individual signals from each analysis method"""
        signals = {}
        
        # Technical signal
        if 'technical' in analyses and 'signals' in analyses['technical']:
            tech_signals = analyses['technical']['signals']
            signals['technical'] = {
                'signal': tech_signals.get('overall_signal', 'HOLD'),
                'confidence': tech_signals.get('strength', 0.5),
                'details': tech_signals.get('signals', [])
            }
        else:
            signals['technical'] = {'signal': 'HOLD', 'confidence': 0.0, 'details': []}
        
        # Sentiment signal
        if 'sentiment' in analyses:
            sentiment = analyses['sentiment']
            sentiment_label = sentiment.get('sentiment_label', 'NEUTRAL')
            if sentiment_label == 'POSITIVE':
                signals['sentiment'] = {'signal': 'BUY', 'confidence': sentiment.get('confidence', 0.5), 'details': []}
            elif sentiment_label == 'NEGATIVE':
                signals['sentiment'] = {'signal': 'SELL', 'confidence': sentiment.get('confidence', 0.5), 'details': []}
            else:
                signals['sentiment'] = {'signal': 'HOLD', 'confidence': 0.5, 'details': []}
        else:
            signals['sentiment'] = {'signal': 'HOLD', 'confidence': 0.0, 'details': []}
        
        # Volume signal
        if 'volume' in analyses and 'volume_signals' in analyses['volume']:
            vol_signals = analyses['volume']['volume_signals']
            signals['volume'] = {
                'signal': vol_signals.get('overall_signal', 'HOLD'),
                'confidence': vol_signals.get('strength', 0.5),
                'details': vol_signals.get('signals', [])
            }
        else:
            signals['volume'] = {'signal': 'HOLD', 'confidence': 0.0, 'details': []}
        
        # AI signal
        if 'ai' in analyses:
            ai = analyses['ai']
            signals['ai'] = {
                'signal': ai.get('signal', 'HOLD'),
                'confidence': ai.get('confidence', 0.5),
                'details': []
            }
        else:
            signals['ai'] = {'signal': 'HOLD', 'confidence': 0.0, 'details': []}
        
        return signals

    def _combine_signals(self, signals: Dict) -> Dict:
        """Combine individual signals using weighted approach"""
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        for method, signal_data in signals.items():
            if method in self.weights:
                weight = self.weights[method]
                confidence = signal_data['confidence']
                signal = signal_data['signal']
                
                if signal == 'BUY':
                    buy_score += weight * confidence
                elif signal == 'SELL':
                    sell_score += weight * confidence
                
                total_weight += weight
        
        # Normalize scores
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        # Determine overall signal
        if buy_score > sell_score and buy_score > self.thresholds['buy']:
            overall_signal = 'BUY'
            confidence = buy_score
        elif sell_score > buy_score and sell_score > self.thresholds['sell']:
            overall_signal = 'SELL'
            confidence = sell_score
        else:
            overall_signal = 'HOLD'
            confidence = max(buy_score, sell_score)
        
        return {
            'signal': overall_signal,
            'confidence': confidence,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'individual_signals': signals
        }
    
    def _generate_recommendation(self, combined_signal: Dict, pattern_analysis: Dict, df: pd.DataFrame) -> Dict:
        """Generate final trading recommendation"""
        current_price = df['close'].iloc[-1]
        
        # Get pattern signals
        pattern_signals = pattern_analysis.get('current_signals', {})
        pattern_signal = pattern_signals.get('signal', 'HOLD')
        pattern_confidence = pattern_signals.get('confidence', 0.5)
        
        # Combine with pattern analysis
        final_signal = combined_signal['signal']
        final_confidence = combined_signal['confidence']
        
        # Adjust for pattern confirmation
        if pattern_signal == combined_signal['signal']:
            final_confidence = min(final_confidence + 0.1, 1.0)
        elif pattern_signal != 'HOLD' and pattern_signal != combined_signal['signal']:
            final_confidence = max(final_confidence - 0.1, 0.0)
        
        # Generate action recommendation
        if final_signal == 'BUY' and final_confidence >= 0.7:
            action = 'STRONG_BUY'
        elif final_signal == 'BUY' and final_confidence >= 0.5:
            action = 'BUY'
        elif final_signal == 'SELL' and final_confidence >= 0.7:
            action = 'STRONG_SELL'
        elif final_signal == 'SELL' and final_confidence >= 0.5:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        return {
            'action': action,
            'signal': final_signal,
            'confidence': final_confidence,
            'current_price': current_price,
            'pattern_confirmation': pattern_signal == final_signal,
            'urgency': self._calculate_urgency(final_confidence, pattern_analysis),
            'timeframe': self._suggest_timeframe(final_signal, final_confidence)
        }
    
    def _generate_reasoning(self, signals: Dict, pattern_analysis: Dict) -> str:
        """Generate human-readable reasoning for the signal"""
        reasoning_parts = []
        
        # Technical reasoning
        if signals['technical']['signal'] != 'HOLD':
            reasoning_parts.append(f"Technical analysis suggests {signals['technical']['signal']} "
                                 f"(confidence: {signals['technical']['confidence']:.1%})")
        
        # Sentiment reasoning
        if signals['sentiment']['signal'] != 'HOLD':
            reasoning_parts.append(f"Market sentiment indicates {signals['sentiment']['signal']} "
                                 f"(confidence: {signals['sentiment']['confidence']:.1%})")
        
        # Volume reasoning
        if signals['volume']['signal'] != 'HOLD':
            reasoning_parts.append(f"Volume analysis supports {signals['volume']['signal']} "
                                 f"(confidence: {signals['volume']['confidence']:.1%})")
        
        # Pattern reasoning
        recent_patterns = pattern_analysis.get('current_signals', {}).get('recent_patterns', [])
        if recent_patterns:
            pattern_names = [p['pattern'] for p in recent_patterns[-2:]]
            reasoning_parts.append(f"Recent patterns detected: {', '.join(pattern_names)}")
        
        if not reasoning_parts:
            return "No strong signals detected. Market conditions are neutral."
        
        return ". ".join(reasoning_parts) + "."
    
    def _calculate_risk_level(self, df: pd.DataFrame, combined_signal: Dict) -> str:
        """Calculate risk level for the signal"""
        # Calculate volatility
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        
        # Calculate signal strength
        signal_strength = combined_signal['confidence']
        
        # Determine risk level
        if volatility > 0.3 and signal_strength < 0.6:
            return 'HIGH'
        elif volatility > 0.2 or signal_strength < 0.7:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_price_targets(self, df: pd.DataFrame, combined_signal: Dict) -> Dict:
        """Calculate price targets based on signal"""
        current_price = df['close'].iloc[-1]
        
        # Calculate volatility-based targets
        returns = df['close'].pct_change().dropna()
        volatility = returns.std()
        
        if combined_signal['signal'] == 'BUY':
            target_1 = current_price * (1 + volatility * 1.5)
            target_2 = current_price * (1 + volatility * 2.5)
            target_3 = current_price * (1 + volatility * 4.0)
        elif combined_signal['signal'] == 'SELL':
            target_1 = current_price * (1 - volatility * 1.5)
            target_2 = current_price * (1 - volatility * 2.5)
            target_3 = current_price * (1 - volatility * 4.0)
        else:
            target_1 = target_2 = target_3 = current_price
        
        return {
            'short_term': round(target_1, 2),
            'medium_term': round(target_2, 2),
            'long_term': round(target_3, 2),
            'current': current_price
        }
    
    def _calculate_stop_loss(self, df: pd.DataFrame, combined_signal: Dict) -> Dict:
        """Calculate stop loss levels"""
        current_price = df['close'].iloc[-1]
        
        # Calculate ATR-based stop loss
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        if combined_signal['signal'] == 'BUY':
            stop_loss = current_price - (atr * 2)
            trailing_stop = current_price - (atr * 1.5)
        elif combined_signal['signal'] == 'SELL':
            stop_loss = current_price + (atr * 2)
            trailing_stop = current_price + (atr * 1.5)
        else:
            stop_loss = trailing_stop = current_price
        
        return {
            'stop_loss': round(stop_loss, 2),
            'trailing_stop': round(trailing_stop, 2),
            'atr': round(atr, 2)
        }
    
    def _calculate_urgency(self, confidence: float, pattern_analysis: Dict) -> str:
        """Calculate urgency level for the signal"""
        pattern_strength = pattern_analysis.get('pattern_strength', 0.5)
        
        if confidence >= 0.8 and pattern_strength >= 0.7:
            return 'HIGH'
        elif confidence >= 0.6 or pattern_strength >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _suggest_timeframe(self, signal: str, confidence: float) -> str:
        """Suggest optimal timeframe for the signal"""
        if signal == 'HOLD':
            return 'N/A'
        
        if confidence >= 0.8:
            return 'IMMEDIATE'
        elif confidence >= 0.6:
            return 'WITHIN_1_DAY'
        else:
            return 'WITHIN_3_DAYS'
    
    async def generate_alert_signal(self, symbol: str, df: pd.DataFrame, 
                                  exchange: str = "NSE") -> Optional[Dict]:
        """Generate alert signal for popup notifications"""
        try:
            signal_data = await self.generate_comprehensive_signal(symbol, df, exchange)
            
            if 'error' in signal_data:
                return None
            
            recommendation = signal_data['recommendation']
            
            # Only generate alerts for strong signals
            if recommendation['action'] in ['STRONG_BUY', 'STRONG_SELL', 'BUY', 'SELL']:
                return {
                    'symbol': symbol,
                    'action': recommendation['action'],
                    'signal': recommendation['signal'],
                    'confidence': recommendation['confidence'],
                    'current_price': recommendation['current_price'],
                    'reasoning': signal_data['reasoning'],
                    'urgency': recommendation['urgency'],
                    'price_targets': signal_data['price_targets'],
                    'stop_loss': signal_data['stop_loss'],
                    'risk_level': signal_data['risk_level'],
                    'timestamp': signal_data['timestamp']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating alert signal: {e}")
            return None