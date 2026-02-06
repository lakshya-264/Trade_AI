"""
Real-Time Voice Trading Assistant
Advanced AI-powered voice functionality for trading recommendations and options trading
Features: Text-to-Speech, Voice Commands, Real-time Audio Alerts, AI Voice Analysis
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
import logging
from datetime import datetime, timedelta
import json
import uuid
import base64
import io
from enum import Enum
import numpy as np
import pandas as pd

# AI and ML imports
try:
    import openai
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    # Try to import whisper with error handling
    try:
        import whisper
        WHISPER_AVAILABLE = True
    except Exception as e:
        logging.warning(f"Whisper not available: {e}")
        whisper = None
        WHISPER_AVAILABLE = False
    
    from gtts import gTTS
    import pygame
    import speech_recognition as sr
    from pydub import AudioSegment
    from pydub.playback import play
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    WHISPER_AVAILABLE = False
    whisper = None
    logging.warning(f"AI libraries not available: {e}. Install: pip install openai transformers torch whisper gtts pygame SpeechRecognition pydub")

logger = logging.getLogger(__name__)

class VoiceCommandType(str, Enum):
    BUY_SIGNAL = "buy_signal"
    SELL_SIGNAL = "sell_signal"
    OPTIONS_ANALYSIS = "options_analysis"
    MARKET_UPDATE = "market_update"
    PATTERN_ALERT = "pattern_alert"
    VOLUME_ALERT = "volume_alert"
    RISK_WARNING = "risk_warning"
    EDUCATIONAL_TIP = "educational_tip"

class VoiceTone(str, Enum):
    PROFESSIONAL = "professional"
    URGENT = "urgent"
    CALM = "calm"
    EXCITED = "excited"
    WARNING = "warning"

class VoiceTradingAssistant:
    def __init__(self):
        self.is_available = AI_AVAILABLE
        
        if not self.is_available:
            logger.warning("Voice functionality not available - missing AI dependencies")
            return
        
        # Initialize AI models
        self.openai_client = None
        self.whisper_model = None
        self.tts_pipeline = None
        self.sentiment_analyzer = None
        self.voice_recognizer = sr.Recognizer()
        
        # Voice settings
        self.voice_settings = {
            "language": "en",
            "voice_speed": 1.0,
            "voice_volume": 0.8,
            "default_tone": VoiceTone.PROFESSIONAL
        }
        
        # Active voice sessions
        self.active_sessions = {}
        
        # Voice command patterns
        self.command_patterns = self._initialize_command_patterns()
        
        # Real-time monitoring
        self.monitoring_active = False
        self.alert_queue = asyncio.Queue()
        
        # Performance tracking
        self.voice_performance = {
            "total_commands": 0,
            "successful_commands": 0,
            "response_times": []
        }
    
    async def initialize_ai_models(self):
        """Initialize AI models for voice processing"""
        try:
            if not self.is_available:
                return False
            
            # Initialize OpenAI client
            self.openai_client = openai.OpenAI()
            
            # Initialize Whisper for speech recognition (if available)
            if WHISPER_AVAILABLE and whisper:
                try:
                    self.whisper_model = whisper.load_model("base")
                except Exception as e:
                    logger.warning(f"Failed to load Whisper model: {e}")
                    self.whisper_model = None
            else:
                self.whisper_model = None
            
            # Initialize TTS pipeline
            self.tts_pipeline = pipeline("text-to-speech", model="microsoft/speecht5_tts")
            
            # Initialize sentiment analyzer
            self.sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            
            logger.info("AI models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            return False
    
    def _initialize_command_patterns(self) -> Dict[str, Any]:
        """Initialize voice command patterns"""
        return {
            "buy_signals": [
                "buy signal detected",
                "strong buy recommendation",
                "bullish pattern confirmed",
                "volume breakout detected",
                "support level bounce"
            ],
            "sell_signals": [
                "sell signal detected",
                "strong sell recommendation",
                "bearish pattern confirmed",
                "resistance rejection",
                "distribution pattern"
            ],
            "options_trading": [
                "options analysis",
                "call option recommendation",
                "put option recommendation",
                "options strategy",
                "greeks analysis"
            ],
            "market_updates": [
                "market update",
                "price alert",
                "volume spike",
                "trend change",
                "market sentiment"
            ],
            "educational": [
                "explain pattern",
                "teach me",
                "what does this mean",
                "trading tip",
                "risk management"
            ]
        }
    
    async def process_voice_command(
        self,
        audio_data: bytes,
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process voice command and generate response"""
        try:
            if not self.is_available:
                return {"error": "Voice functionality not available"}
            
            # Convert audio to text
            transcript = await self._speech_to_text(audio_data)
            if not transcript:
                return {"error": "Could not transcribe audio"}
            
            # Analyze command intent
            intent = await self._analyze_command_intent(transcript)
            
            # Generate appropriate response
            response = await self._generate_voice_response(intent, context, user_id)
            
            # Convert response to speech
            audio_response = await self._text_to_speech(response["text"], response["tone"])
            
            # Track performance
            self.voice_performance["total_commands"] += 1
            self.voice_performance["successful_commands"] += 1
            
            return {
                "transcript": transcript,
                "intent": intent,
                "response": response,
                "audio_response": audio_response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return {"error": str(e)}
    
    async def _speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text using Whisper"""
        try:
            # Save audio data to temporary file
            temp_file = f"temp_audio_{uuid.uuid4().hex}.wav"
            
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Transcribe using Whisper (if available)
            if self.whisper_model:
                result = self.whisper_model.transcribe(temp_file)
                transcript = result["text"].strip()
            else:
                # Fallback to basic speech recognition
                transcript = "Speech recognition not available"
                logger.warning("Whisper not available - using fallback")
            
            # Clean up temp file
            import os
            os.remove(temp_file)
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return ""
    
    async def _analyze_command_intent(self, transcript: str) -> Dict[str, Any]:
        """Analyze command intent using AI"""
        try:
            # Use OpenAI to analyze intent
            prompt = f"""
            Analyze this trading-related voice command and extract:
            1. Command type (buy_signal, sell_signal, options_analysis, market_update, educational)
            2. Confidence level (0-1)
            3. Key parameters (symbol, timeframe, etc.)
            4. Urgency level (low, medium, high)
            
            Command: "{transcript}"
            
            Respond in JSON format.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            
            # Enhance with sentiment analysis
            sentiment = self.sentiment_analyzer(transcript)[0]
            intent_data["sentiment"] = sentiment["label"]
            intent_data["sentiment_score"] = sentiment["score"]
            
            return intent_data
            
        except Exception as e:
            logger.error(f"Error analyzing command intent: {e}")
            return {
                "command_type": "unknown",
                "confidence": 0.5,
                "parameters": {},
                "urgency": "medium",
                "sentiment": "neutral",
                "sentiment_score": 0.5
            }
    
    async def _generate_voice_response(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Generate intelligent voice response"""
        try:
            command_type = intent.get("command_type", "unknown")
            urgency = intent.get("urgency", "medium")
            
            # Determine response tone based on urgency and sentiment
            if urgency == "high":
                tone = VoiceTone.URGENT
            elif intent.get("sentiment") == "NEGATIVE":
                tone = VoiceTone.WARNING
            elif intent.get("sentiment") == "POSITIVE":
                tone = VoiceTone.EXCITED
            else:
                tone = VoiceTone.PROFESSIONAL
            
            # Generate response based on command type
            if command_type == "buy_signal":
                response_text = await self._generate_buy_signal_response(context, intent)
            elif command_type == "sell_signal":
                response_text = await self._generate_sell_signal_response(context, intent)
            elif command_type == "options_analysis":
                response_text = await self._generate_options_response(context, intent)
            elif command_type == "market_update":
                response_text = await self._generate_market_update_response(context, intent)
            elif command_type == "educational":
                response_text = await self._generate_educational_response(context, intent)
            else:
                response_text = "I understand you're asking about trading. Could you please be more specific about what you'd like to know?"
            
            return {
                "text": response_text,
                "tone": tone,
                "command_type": command_type,
                "confidence": intent.get("confidence", 0.5)
            }
            
        except Exception as e:
            logger.error(f"Error generating voice response: {e}")
            return {
                "text": "I'm sorry, I couldn't process your request. Please try again.",
                "tone": VoiceTone.PROFESSIONAL,
                "command_type": "error",
                "confidence": 0.0
            }
    
    async def _generate_buy_signal_response(self, context: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate buy signal voice response"""
        try:
            symbol = context.get("symbol", "the stock")
            current_price = context.get("current_price", 0)
            confidence = intent.get("confidence", 0.5)
            
            if confidence > 0.8:
                response = f"Strong buy signal detected for {symbol} at {current_price}. Multiple indicators confirm bullish momentum. Consider entering with proper risk management."
            elif confidence > 0.6:
                response = f"Buy signal detected for {symbol} at {current_price}. Technical indicators suggest upward movement. Monitor for confirmation."
            else:
                response = f"Weak buy signal for {symbol} at {current_price}. Wait for stronger confirmation before entering."
            
            # Add risk warning
            response += " Remember to use stop losses and position sizing."
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating buy signal response: {e}")
            return "Buy signal analysis completed. Please check the detailed analysis on your screen."
    
    async def _generate_sell_signal_response(self, context: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate sell signal voice response"""
        try:
            symbol = context.get("symbol", "the stock")
            current_price = context.get("current_price", 0)
            confidence = intent.get("confidence", 0.5)
            
            if confidence > 0.8:
                response = f"Strong sell signal detected for {symbol} at {current_price}. Multiple indicators confirm bearish momentum. Consider exiting or shorting with proper risk management."
            elif confidence > 0.6:
                response = f"Sell signal detected for {symbol} at {current_price}. Technical indicators suggest downward movement. Monitor for confirmation."
            else:
                response = f"Weak sell signal for {symbol} at {current_price}. Wait for stronger confirmation before selling."
            
            # Add risk warning
            response += " Remember to protect your capital with proper risk management."
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating sell signal response: {e}")
            return "Sell signal analysis completed. Please check the detailed analysis on your screen."
    
    async def _generate_options_response(self, context: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate options trading response"""
        try:
            symbol = context.get("symbol", "the underlying")
            options_data = context.get("options_data", {})
            
            if not options_data:
                return f"Options analysis for {symbol} is not currently available. Please ensure options data is loaded."
            
            # Analyze options data
            call_options = options_data.get("call_options", [])
            put_options = options_data.get("put_options", [])
            
            response = f"Options analysis for {symbol}: "
            
            if call_options:
                best_call = max(call_options, key=lambda x: x.get("delta", 0))
                response += f"Best call option has delta {best_call.get('delta', 0):.2f} and premium {best_call.get('premium', 0):.2f}. "
            
            if put_options:
                best_put = max(put_options, key=lambda x: abs(x.get("delta", 0)))
                response += f"Best put option has delta {best_put.get('delta', 0):.2f} and premium {best_put.get('premium', 0):.2f}. "
            
            response += "Consider your risk tolerance and market outlook before trading options."
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating options response: {e}")
            return "Options analysis completed. Please check the detailed options data on your screen."
    
    async def _generate_market_update_response(self, context: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate market update response"""
        try:
            market_data = context.get("market_data", {})
            symbol = context.get("symbol", "the market")
            
            current_price = market_data.get("current_price", 0)
            change = market_data.get("change", 0)
            change_percent = market_data.get("change_percent", 0)
            volume = market_data.get("volume", 0)
            
            response = f"Market update for {symbol}: "
            response += f"Current price is {current_price}. "
            
            if change > 0:
                response += f"Up {change_percent:.2f} percent. "
            elif change < 0:
                response += f"Down {abs(change_percent):.2f} percent. "
            else:
                response += "No change. "
            
            response += f"Volume is {volume:,}. "
            
            # Add market sentiment
            sentiment = market_data.get("sentiment", "neutral")
            if sentiment == "bullish":
                response += "Market sentiment is bullish."
            elif sentiment == "bearish":
                response += "Market sentiment is bearish."
            else:
                response += "Market sentiment is neutral."
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating market update response: {e}")
            return "Market update completed. Please check the latest market data on your screen."
    
    async def _generate_educational_response(self, context: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Generate educational response"""
        try:
            topic = intent.get("parameters", {}).get("topic", "trading")
            
            educational_tips = {
                "pattern": "Candlestick patterns like hammer, doji, and engulfing can indicate potential reversals. Always confirm with volume and other indicators.",
                "volume": "Volume is crucial for confirming price movements. High volume on breakouts increases the likelihood of continuation.",
                "risk": "Never risk more than 2% of your capital on a single trade. Use stop losses and position sizing to protect your account.",
                "options": "Options trading involves Greeks - Delta measures price sensitivity, Theta measures time decay, and Vega measures volatility sensitivity.",
                "general": "Successful trading requires discipline, risk management, and continuous learning. Start with paper trading to practice your strategies."
            }
            
            tip = educational_tips.get(topic, educational_tips["general"])
            return f"Here's a trading tip: {tip}"
            
        except Exception as e:
            logger.error(f"Error generating educational response: {e}")
            return "I'd be happy to help you learn about trading. What specific topic would you like to know more about?"
    
    async def _text_to_speech(self, text: str, tone: VoiceTone = VoiceTone.PROFESSIONAL) -> bytes:
        """Convert text to speech with appropriate tone"""
        try:
            # Adjust text based on tone
            if tone == VoiceTone.URGENT:
                text = f"⚠️ URGENT: {text}"
            elif tone == VoiceTone.WARNING:
                text = f"⚠️ WARNING: {text}"
            elif tone == VoiceTone.EXCITED:
                text = f"🎉 {text}"
            
            # Generate speech using gTTS
            tts = gTTS(text=text, lang=self.voice_settings["language"], slow=False)
            
            # Save to bytes
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return b""
    
    async def start_real_time_voice_monitoring(
        self,
        user_id: int,
        symbols: List[str],
        alert_types: List[VoiceCommandType]
    ) -> str:
        """Start real-time voice monitoring for trading alerts"""
        try:
            session_id = f"voice_monitor_{user_id}_{uuid.uuid4().hex[:8]}"
            
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "symbols": symbols,
                "alert_types": alert_types,
                "started_at": datetime.now(),
                "is_active": True,
                "alerts_sent": 0
            }
            
            self.active_sessions[session_id] = session_data
            
            # Start monitoring task
            asyncio.create_task(self._monitor_trading_signals(session_id))
            
            logger.info(f"Voice monitoring started for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting voice monitoring: {e}")
            return ""
    
    async def _monitor_trading_signals(self, session_id: str):
        """Monitor trading signals and generate voice alerts"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return
            
            while session["is_active"]:
                # Check for trading signals
                for symbol in session["symbols"]:
                    # This would integrate with your trading recommendation engine
                    # For now, we'll simulate signal detection
                    signal_data = await self._check_trading_signals(symbol)
                    
                    if signal_data:
                        await self._generate_voice_alert(session_id, symbol, signal_data)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f"Error in trading signal monitoring: {e}")
    
    async def _check_trading_signals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Check for trading signals (integrate with your recommendation engine)"""
        try:
            # This would integrate with your existing trading recommendation engine
            # For demonstration, we'll return mock data
            
            # Simulate signal detection
            import random
            if random.random() < 0.1:  # 10% chance of signal
                signal_types = ["buy", "sell", "pattern", "volume"]
                signal_type = random.choice(signal_types)
                
                return {
                    "type": signal_type,
                    "symbol": symbol,
                    "confidence": random.uniform(0.6, 0.9),
                    "price": random.uniform(100, 200),
                    "message": f"{signal_type.title()} signal detected for {symbol}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking trading signals: {e}")
            return None
    
    async def _generate_voice_alert(
        self,
        session_id: str,
        symbol: str,
        signal_data: Dict[str, Any]
    ):
        """Generate voice alert for trading signal"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return
            
            signal_type = signal_data["type"]
            confidence = signal_data["confidence"]
            price = signal_data["price"]
            
            # Determine alert tone
            if confidence > 0.8:
                tone = VoiceTone.URGENT
            elif confidence > 0.6:
                tone = VoiceTone.PROFESSIONAL
            else:
                tone = VoiceTone.CALM
            
            # Generate alert message
            if signal_type == "buy":
                message = f"Buy signal for {symbol} at {price:.2f}. Confidence: {confidence:.1%}"
            elif signal_type == "sell":
                message = f"Sell signal for {symbol} at {price:.2f}. Confidence: {confidence:.1%}"
            elif signal_type == "pattern":
                message = f"Pattern detected for {symbol} at {price:.2f}. Check your charts."
            elif signal_type == "volume":
                message = f"Volume spike for {symbol} at {price:.2f}. Monitor for breakout."
            else:
                message = f"Trading alert for {symbol} at {price:.2f}"
            
            # Convert to speech
            audio_alert = await self._text_to_speech(message, tone)
            
            # Send to user (this would integrate with WebSocket)
            alert_data = {
                "session_id": session_id,
                "symbol": symbol,
                "signal_data": signal_data,
                "message": message,
                "audio_alert": base64.b64encode(audio_alert).decode(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to alert queue
            await self.alert_queue.put(alert_data)
            
            # Update session stats
            session["alerts_sent"] += 1
            
            logger.info(f"Voice alert generated for {symbol}: {signal_type}")
            
        except Exception as e:
            logger.error(f"Error generating voice alert: {e}")
    
    async def stop_voice_monitoring(self, session_id: str) -> bool:
        """Stop voice monitoring session"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["is_active"] = False
                del self.active_sessions[session_id]
                logger.info(f"Voice monitoring stopped for session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error stopping voice monitoring: {e}")
            return False
    
    async def get_voice_performance_stats(self) -> Dict[str, Any]:
        """Get voice functionality performance statistics"""
        try:
            total_commands = self.voice_performance["total_commands"]
            successful_commands = self.voice_performance["successful_commands"]
            
            accuracy = successful_commands / total_commands if total_commands > 0 else 0
            
            avg_response_time = np.mean(self.voice_performance["response_times"]) if self.voice_performance["response_times"] else 0
            
            return {
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "accuracy": accuracy,
                "average_response_time": avg_response_time,
                "active_sessions": len(self.active_sessions),
                "ai_models_available": self.is_available
            }
            
        except Exception as e:
            logger.error(f"Error getting voice performance stats: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if voice functionality is available"""
        return self.is_available and AI_AVAILABLE
    
    def clear_cache(self):
        """Clear voice functionality cache"""
        self.active_sessions.clear()
        self.voice_performance = {
            "total_commands": 0,
            "successful_commands": 0,
            "response_times": []
        }
        logger.info("Voice functionality cache cleared")
