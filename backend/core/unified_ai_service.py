"""
Unified AI Service - Combines Traditional AI Analysis with Generative AI
Provides seamless integration of both approaches for maximum effectiveness
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# Apply Gemini AFC limit and transport settings BEFORE any google-genai imports
# This raises the max remote calls from 10 to 100 and forces REST transport to reduce throttling
os.environ["GOOGLE_GENAI_USE_LEGACY_REST"] = "1"
os.environ["GOOGLE_GENAI_MAX_REMOTE_CALLS"] = os.getenv("GEMINI_MAX_REMOTE_CALLS", "100")
logger = logging.getLogger(__name__)

# Traditional AI imports
try:
    from .technical_analysis import TechnicalAnalysisService
    from .sentiment_analysis import SentimentAnalysisService
    from ..services.signal_generator import SignalGeneratorService
    from ..services.ai_engine import AIEngine
    from ..services.volume_analyzer import VolumeAnalyzer
    from ..services.candlestick_patterns import CandlestickPatternService
except ImportError:
    # Fallback for missing services
    TechnicalAnalysisService = None
    SentimentAnalysisService = None
    SignalGeneratorService = None
    AIEngine = None
    VolumeAnalyzer = None
    CandlestickPatternService = None

# GenAI imports
try:
    from langchain_openai import ChatOpenAI

    # LangChain moved schemas/messages into langchain_core in newer versions
    try:
        from langchain.schema import HumanMessage, AIMessage, SystemMessage
    except ImportError:
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    from langchain_core.chat_history import InMemoryChatMessageHistory
    from langchain_core.chat_history import BaseChatMessageHistory

    # Prompts also moved into langchain_core in newer versions
    try:
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    except ImportError:
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # ConversationChain was removed/moved in newer LangChain versions; keep optional.
    try:
        from langchain.chains import ConversationChain  # Deprecated - keeping for reference
    except ImportError:
        ConversationChain = None

    # Tools/agents moved around across versions; keep fallbacks
    try:
        from langchain.tools import Tool
    except ImportError:
        from langchain_core.tools import Tool

    try:
        from langchain.agents import initialize_agent, AgentType
    except ImportError:
        initialize_agent = None
        AgentType = None
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create dummy classes when LangChain is not available
    class BaseChatMessageHistory:
        def __init__(self):
            self.messages = []
        def add_message(self, message):
            self.messages.append(message)
        def clear(self):
            self.messages = []
    
    class InMemoryChatMessageHistory(BaseChatMessageHistory):
        pass

# Gemini imports for fallback
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    GEMINI_NEW_API = False

try:
    from .database_unified import SessionLocal, MarketData, ChatSession, ChatMessage, PredictionHistory
    from .data_service import data_service
except ImportError:
    SessionLocal = None
    MarketData = None
    ChatSession = None
    ChatMessage = None
    PredictionHistory = None
    data_service = None

logger = logging.getLogger(__name__)

@dataclass
class UnifiedAnalysisResult:
    """Combined result from both AI approaches"""
    symbol: str
    
    # Traditional AI Results
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    volume_analysis: Dict[str, Any]
    pattern_analysis: Dict[str, Any]
    ml_signals: Dict[str, Any]
    
    # GenAI Results
    ai_reasoning: str
    natural_language_explanation: str
    conversational_response: str
    
    # Combined Results
    final_recommendation: str
    confidence_score: float
    
    # Metadata
    analysis_timestamp: datetime
    analysis_duration_ms: int
    ai_methods_used: List[str]
    
    # Optional fields with defaults
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_level: str = "MEDIUM"

    # Trade plan (optional)
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    holding_period: Optional[str] = None
    holding_days_min: Optional[int] = None
    holding_days_max: Optional[int] = None

class UnifiedAIService:
    """
    Unified AI Service that combines traditional AI analysis with Generative AI
    Provides the best of both worlds for comprehensive trading analysis
    """
    
    def __init__(self):
        # Traditional AI Services
        self.technical_analyzer = TechnicalAnalysisService() if TechnicalAnalysisService else None
        self.sentiment_analyzer = SentimentAnalysisService() if SentimentAnalysisService else None
        self.signal_generator = SignalGeneratorService() if SignalGeneratorService else None
        self.ai_engine = AIEngine() if AIEngine else None
        self.volume_analyzer = VolumeAnalyzer() if VolumeAnalyzer else None
        self.pattern_analyzer = CandlestickPatternService() if CandlestickPatternService else None
        
        # GenAI Services - Use both OpenAI and LangChain
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.langchain_api_key = os.getenv("LANGCHAIN_API_KEY")  # For LangChain-specific features
        self.llm = None
        self.memory = None
        self.conversation_chain = None
        self.analysis_tools = {}

        # Gemini fallback runtime state
        self.gemini_llm = None
        self.use_gemini_fallback = False
        
        # Chat functionality (consolidated from TraderGenAI)
        self.chat_mode = False
        self.chat_memory = None
        self.chat_chain = None

        # In-memory message histories for LangChain 1.2.x
        self._analysis_histories: Dict[str, BaseChatMessageHistory] = {}
        self._chat_histories: Dict[str, BaseChatMessageHistory] = {}
        
        # Initialize GenAI if available (requires OpenAI API key or Gemini API key)
        if LANGCHAIN_AVAILABLE and (self.openai_api_key or self.gemini_api_key):
            self._initialize_genai()
        else:
            # These are informational messages, not errors
            if not self.openai_api_key and not self.gemini_api_key:
                logger.info("GenAI features disabled: Neither OpenAI nor Gemini API key set (optional - system works without it)")
            if not LANGCHAIN_AVAILABLE:
                logger.info("GenAI features disabled: LangChain not available (optional - system works without it)")
            logger.info("Using traditional AI analysis (ML models, technical analysis, sentiment, etc.)")
            self._initialize_traditional_only()

    # -------------------- Analysis caching (module-wide) --------------------
    # Note: UnifiedAIService is created per-request by FastAPI Depends; instance-level
    # cache would be ineffective. Use class-level structures shared across instances.
    _analysis_cache: Dict[str, Any] = {}
    _analysis_cache_expires_at: Dict[str, datetime] = {}
    _analysis_inflight: Dict[str, "asyncio.Task"] = {}
    _analysis_cache_lock: "asyncio.Lock" = asyncio.Lock()

    def _analysis_cache_ttl_seconds(self, analysis_depth: str) -> int:
        depth = (analysis_depth or "").upper().strip()
        if depth == "QUICK":
            return 60
        if depth == "STANDARD":
            return 300
        return 900

    def _make_analysis_cache_key(
        self,
        symbol: str,
        analysis_depth: str,
        user_query: Optional[str],
        include_charts: bool,
        include_news: bool,
    ) -> str:
        sym = (symbol or "").upper().strip()
        depth = (analysis_depth or "").upper().strip()
        uq = (user_query or "").strip().lower()
        return f"unified_ai:{sym}:{depth}:{int(bool(include_charts))}:{int(bool(include_news))}:{uq}"
    
    def _initialize_genai(self):
        """Initialize Generative AI components with OpenAI + LangChain, with model fallbacks."""
        try:
            if self.openai_api_key:
                os.environ["OPENAI_API_KEY"] = self.openai_api_key

            # Build model fallback list: env first, then sensible defaults
            preferred = os.getenv("OPENAI_MODEL")
            fallback_models = [
                preferred.strip() if preferred else None,
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-3.5-turbo",
            ]
            # remove falsy and duplicates keeping order
            seen = set()
            model_candidates = []
            for m in fallback_models:
                if m and m not in seen:
                    seen.add(m)
                    model_candidates.append(m)

            init_errors = []
            chosen_model = None

            if self.openai_api_key:
                # Try models in order until one works
                for model_name in model_candidates:
                    try:
                        candidate_llm = ChatOpenAI(
                            model_name=model_name,
                            temperature=0.3,
                            openai_api_key=self.openai_api_key,
                            max_tokens=2000,
                        )
                        try:
                            resp = candidate_llm.invoke("ping")
                            if not hasattr(resp, "content"):
                                pass
                        except Exception as probe_err:
                            init_errors.append(f"probe {model_name}: {probe_err}")
                            continue

                        self.llm = candidate_llm
                        chosen_model = model_name
                        break
                    except Exception as init_err:
                        init_errors.append(f"init {model_name}: {init_err}")
                        continue
            elif GEMINI_AVAILABLE and self.gemini_api_key:
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash-latest",
                        temperature=0.3,
                        google_api_key=self.gemini_api_key,
                        max_retries=3,
                        timeout=30,
                        max_output_tokens=2048,
                        max_tokens=2048,
                    )
                    chosen_model = "gemini-1.5-flash"
                except Exception as init_err:
                    init_errors.append(f"init gemini: {init_err}")

            if not self.llm:
                logger.warning(
                    "GenAI disabled: could not initialize any OpenAI model from candidates %s. Errors: %s",
                    model_candidates,
                    "; ".join(init_errors)[:500],
                )
                self._initialize_traditional_only()
                return

            # Initialize conversation history (LangChain 1.2.x compatible)
            # RunnableWithMessageHistory expects a BaseChatMessageHistory.
            self.memory = InMemoryChatMessageHistory()
            
            # Setup analysis tools
            self._setup_analysis_tools()
            
            # Create conversation chain
            self._setup_conversation_chain()
            
            # Initialize chat functionality (consolidated from TraderGenAI)
            self._setup_chat_functionality()
            
            logger.info("OK GenAI initialized successfully")
            logger.info(f"🤖 Model: {chosen_model}")
            logger.info(f"🧠 Memory: Enabled (15 messages)")
            logger.info(f"🔧 Tools: {len(self.analysis_tools)} available")
            logger.info(f"💬 Chat: Enabled")
            
        except Exception as e:
            logger.error(f"ERROR Failed to initialize GenAI: {e}")
            self._initialize_traditional_only()
    
    def _initialize_traditional_only(self):
        """Initialize traditional AI only mode"""
        self.llm = None
        self.memory = None
        self.conversation_chain = None
        logger.info("Unified AI Service initialized with Traditional AI only")

    def _get_analysis_history(self, session_id: str) -> BaseChatMessageHistory:
        if not session_id:
            session_id = "default"
        if session_id not in self._analysis_histories:
            self._analysis_histories[session_id] = InMemoryChatMessageHistory()
        return self._analysis_histories[session_id]

    def _get_chat_history_store(self, session_id: str) -> BaseChatMessageHistory:
        if not session_id:
            session_id = "default"
        if session_id not in self._chat_histories:
            self._chat_histories[session_id] = InMemoryChatMessageHistory()
        return self._chat_histories[session_id]
    
    def _setup_analysis_tools(self):
        """Setup analysis tools for GenAI agent"""
        self.analysis_tools = {
            "get_quote": Tool(
                name="get_quote",
                description="Get current stock quote and price data",
                func=self._get_quote_tool
            ),
            "technical_analysis": Tool(
                name="technical_analysis",
                description="Perform comprehensive technical analysis",
                func=self._technical_analysis_tool
            ),
            "sentiment_analysis": Tool(
                name="sentiment_analysis",
                description="Analyze market sentiment and news",
                func=self._sentiment_analysis_tool
            ),
            "volume_analysis": Tool(
                name="volume_analysis",
                description="Analyze volume patterns and trends",
                func=self._volume_analysis_tool
            ),
            "pattern_analysis": Tool(
                name="pattern_analysis",
                description="Detect candlestick patterns",
                func=self._pattern_analysis_tool
            ),
            "ml_signals": Tool(
                name="ml_signals",
                description="Generate machine learning trading signals",
                func=self._ml_signals_tool
            )
        }
    
    def _setup_conversation_chain(self):
        """Setup conversation chain with enhanced system prompt"""
        system_prompt = """You are TraderGenAI Pro, an advanced unified AI trading assistant that combines traditional AI analysis with generative AI reasoning.

Your capabilities:
- Traditional AI: Technical analysis, sentiment analysis, volume analysis, pattern detection, ML signals
- Generative AI: Natural language explanations, contextual reasoning, conversational analysis
- Unified Analysis: Combining both approaches for maximum accuracy

Analysis Process:
1. Gather all traditional AI analysis results
2. Synthesize findings using generative AI reasoning
3. Provide clear, actionable recommendations with confidence levels
4. Explain complex concepts in simple terms
5. Suggest risk management strategies

Guidelines:
- Always base recommendations on data-driven analysis
- Provide confidence levels (0-100%)
- Include price targets and stop-loss levels
- Explain your reasoning clearly
- Consider market context and risk factors
- Be conservative with high-risk recommendations
- Remember conversation history for context

Response Format:
- Clear recommendation (BUY/SELL/HOLD)
- Confidence percentage
- Price target and stop-loss
- Risk level (LOW/MEDIUM/HIGH)
- Detailed reasoning
- Natural language explanation

Always be accurate, helpful, and transparent about limitations."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # Use RunnableWithMessageHistory instead of deprecated ConversationChain
        from langchain_core.runnables.history import RunnableWithMessageHistory
        from langchain_core.runnables import RunnablePassthrough
        
        # Create the base chain
        base_chain = prompt | self.llm
        
        # Wrap with message history
        self.conversation_chain = RunnableWithMessageHistory(
            base_chain,
            self._get_analysis_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
    
    async def analyze_stock_unified(
        self, 
        symbol: str, 
        user_query: str = None,
        analysis_depth: str = "COMPREHENSIVE",  # QUICK, STANDARD, COMPREHENSIVE
        include_charts: bool = True,
        include_news: bool = True
    ) -> UnifiedAnalysisResult:
        """
        Perform unified analysis combining traditional AI and GenAI
        
        Args:
            symbol: Stock symbol to analyze
            user_query: Optional user query for context
            analysis_depth: Analysis depth (QUICK, STANDARD, COMPREHENSIVE)
            include_charts: Whether to include chart analysis
            include_news: Whether to include news sentiment analysis
        """
        cache_key = self._make_analysis_cache_key(symbol, analysis_depth, user_query, include_charts, include_news)
        now = datetime.utcnow()

        # Fast path: cache hit / inflight de-dupe
        inflight_to_await: Optional[asyncio.Task] = None
        async with self._analysis_cache_lock:
            expires_at = self._analysis_cache_expires_at.get(cache_key)
            cached = self._analysis_cache.get(cache_key)
            if expires_at and expires_at > now and cached:
                return cached

            inflight = self._analysis_inflight.get(cache_key)
            if inflight:
                inflight_to_await = inflight
            else:

                async def _compute() -> UnifiedAnalysisResult:
                    start_time = datetime.utcnow()
                    try:
                        # Step 1: Gather all traditional AI analysis
                        traditional_results = await self._run_traditional_analysis(symbol, analysis_depth)

                        # Step 2: Generate GenAI reasoning and explanation
                        genai_results = await self._generate_genai_analysis(
                            symbol, traditional_results, user_query
                        )

                        # Step 3: Combine results and generate final recommendation
                        final_recommendation = await self._combine_analysis_results(
                            traditional_results, genai_results
                        )

                        # Step 4: Create unified result
                        analysis_duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                        result = UnifiedAnalysisResult(
                            symbol=symbol,
                            technical_analysis=traditional_results.get("technical", {}),
                            sentiment_analysis=traditional_results.get("sentiment", {}),
                            volume_analysis=traditional_results.get("volume", {}),
                            pattern_analysis=traditional_results.get("patterns", {}),
                            ml_signals=traditional_results.get("ml_signals", {}),
                            ai_reasoning=genai_results.get("reasoning", ""),
                            natural_language_explanation=genai_results.get("explanation", ""),
                            conversational_response=genai_results.get("response", ""),
                            final_recommendation=final_recommendation.get("recommendation", "HOLD"),
                            confidence_score=final_recommendation.get("confidence", 0.0),
                            price_target=final_recommendation.get("price_target"),
                            stop_loss=final_recommendation.get("stop_loss"),
                            risk_level=final_recommendation.get("risk_level", "MEDIUM"),
                            entry_price=final_recommendation.get("entry_price"),
                            exit_price=final_recommendation.get("exit_price"),
                            holding_period=final_recommendation.get("holding_period"),
                            holding_days_min=final_recommendation.get("holding_days_min"),
                            holding_days_max=final_recommendation.get("holding_days_max"),
                            analysis_timestamp=start_time,
                            analysis_duration_ms=int(analysis_duration),
                            ai_methods_used=self._get_used_methods(traditional_results, genai_results)
                        )

                        # Cache successful result
                        ttl_seconds = self._analysis_cache_ttl_seconds(analysis_depth)
                        async with self._analysis_cache_lock:
                            self._analysis_cache[cache_key] = result
                            self._analysis_cache_expires_at[cache_key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)

                        return result
                    except Exception as e:
                        logger.error(f"Unified analysis error for {symbol}: {e}")
                        return self._create_error_result(symbol, str(e))
                    finally:
                        async with self._analysis_cache_lock:
                            self._analysis_inflight.pop(cache_key, None)

                task = asyncio.create_task(_compute())
                self._analysis_inflight[cache_key] = task
                inflight_to_await = task

        return await inflight_to_await
    
    async def _run_traditional_analysis(self, symbol: str, depth: str) -> Dict[str, Any]:
        """Run all traditional AI analysis methods with real ML models"""
        results = {}
        
        try:
            logger.info(f"🔍 Running traditional AI analysis for {symbol} (depth: {depth})")
            
            # Step 1: Get historical data
            historical_data = []
            df = None
            
            # Use real data fetcher service for historical data
            try:
                from services.data_fetcher import fetch_historical_data
                
                # Fetch historical data (last 180 days for comprehensive analysis)
                historical_data = await fetch_historical_data(
                    symbol=symbol,
                    timeframe="1d",  # Daily data
                    days=180  # 6 months of data for comprehensive analysis
                )
                
                if historical_data and len(historical_data) > 0:
                    # Convert to pandas DataFrame
                    import pandas as pd
                    df = pd.DataFrame(historical_data)
                    
                    # Ensure required columns exist and rename if needed
                    column_mapping = {
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    }
                    
                    # Rename columns if needed
                    df = df.rename(columns=column_mapping)
                    
                    # Ensure we have the required columns
                    required_cols = ['open', 'high', 'low', 'close', 'volume']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    
                    if missing_cols:
                        logger.warning(f"Missing columns {missing_cols} for {symbol}, using fallback")
                        df = None
                    else:
                        # Ensure numeric types
                        for col in required_cols:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        # Sort by time (data_fetcher returns 'time' column as Unix timestamp)
                        if 'time' in df.columns:
                            df = df.sort_values(by='time')
                        elif 'timestamp' in df.columns:
                            df = df.sort_values(by='timestamp')
                        elif 'date' in df.columns:
                            df = df.sort_values(by='date')
                        
                        # Remove any rows with NaN values
                        df = df.dropna(subset=required_cols)
                        
                        logger.info(f"✅ Loaded {len(df)} data points for {symbol}")
                else:
                    logger.warning(f"No historical data available for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {e}")
                df = None
            
            # Step 2: Run Technical Analysis
            technical_analysis = {}
            if self.technical_analyzer and df is not None:
                try:
                    technical_analysis = self.technical_analyzer.analyze(df)
                    logger.info(f"✅ Technical analysis completed for {symbol}")
                except Exception as e:
                    logger.error(f"Technical analysis error for {symbol}: {e}")
                    technical_analysis = {"error": str(e), "signal": "HOLD"}
            else:
                logger.warning(f"Technical analyzer not available or no data for {symbol}")
                technical_analysis = {"signal": "HOLD", "rsi": 50.0, "macd": "neutral"}
            
            # Step 3: Run Sentiment Analysis
            sentiment_analysis = {}
            if self.sentiment_analyzer:
                try:
                    sentiment_analysis = await self.sentiment_analyzer.analyze_stock_sentiment(symbol)
                    logger.info(f"✅ Sentiment analysis completed for {symbol}")
                except Exception as e:
                    logger.error(f"Sentiment analysis error for {symbol}: {e}")
                    sentiment_analysis = {"error": str(e), "news_sentiment": "neutral", "social_sentiment": "neutral"}
            else:
                logger.warning(f"Sentiment analyzer not available for {symbol}")
                sentiment_analysis = {"news_sentiment": "neutral", "social_sentiment": "neutral"}
            
            # Step 4: Run Volume Analysis
            volume_analysis = {}
            if self.volume_analyzer and df is not None:
                try:
                    volume_analysis = self.volume_analyzer.analyze_volume_patterns(df)
                    logger.info(f"✅ Volume analysis completed for {symbol}")
                except Exception as e:
                    logger.error(f"Volume analysis error for {symbol}: {e}")
                    volume_analysis = {"error": str(e), "volume_trend": "neutral", "volume_signal": "HOLD"}
            else:
                logger.warning(f"Volume analyzer not available or no data for {symbol}")
                volume_analysis = {"volume_trend": "neutral", "volume_signal": "HOLD"}
            
            # Step 5: Run Pattern Analysis
            pattern_analysis = {}
            if self.pattern_analyzer and df is not None:
                try:
                    pattern_analysis = self.pattern_analyzer.detect_patterns(df)
                    logger.info(f"✅ Pattern analysis completed for {symbol}")
                except Exception as e:
                    logger.error(f"Pattern analysis error for {symbol}: {e}")
                    pattern_analysis = {"error": str(e), "candlestick_patterns": []}
            else:
                logger.warning(f"Pattern analyzer not available or no data for {symbol}")
                pattern_analysis = {"candlestick_patterns": []}
            
            # Step 6: Run AI Engine (ML Signals)
            ml_signals = {}
            if self.ai_engine and df is not None:
                try:
                    # Prepare analysis data for AI Engine
                    analysis_data = {
                        'technical': technical_analysis,
                        'sentiment': sentiment_analysis,
                        'volume': volume_analysis
                    }
                    
                    ml_signals = self.ai_engine.generate_signals(df, analysis_data)
                    logger.info(f"✅ ML signals generated for {symbol}: {ml_signals.get('signal', 'HOLD')}")
                    
                    # Log prediction for monitoring
                    try:
                        from services.model_monitoring import model_monitoring
                        current_price = float(df['close'].iloc[-1]) if len(df) > 0 else 0
                        model_monitoring.log_prediction(
                            model_name="ai_engine",
                            symbol=symbol,
                            prediction=ml_signals.get('price_target', current_price),
                            actual_value=None,  # Will be updated later when actual price is known
                            confidence=ml_signals.get('confidence', 0.0),
                            metadata={
                                'signal': ml_signals.get('signal', 'HOLD'),
                                'stop_loss': ml_signals.get('stop_loss', 0.0)
                            }
                        )
                    except Exception as monitor_error:
                        logger.debug(f"Model monitoring error (non-critical): {monitor_error}")
                except Exception as e:
                    logger.error(f"AI Engine error for {symbol}: {e}")
                    ml_signals = {
                        "signal": "HOLD",
                        "confidence": 0.0,
                        "price_target": 0.0,
                        "stop_loss": 0.0,
                        "error": str(e)
                    }
            else:
                logger.warning(f"AI Engine not available or no data for {symbol}")
                ml_signals = {
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "price_target": 0.0,
                    "stop_loss": 0.0
                }
            
            # Step 7: Try to load and use advanced ML models (optional, if available)
            advanced_ml_predictions = {}
            if depth == "COMPREHENSIVE" and df is not None:
                try:
                    # Try to load and use Alternative Data Models (News Sentiment, Social Media)
                    try:
                        from services.alternative_data_models import AlternativeDataModels
                        alt_data_models = AlternativeDataModels()
                        alt_data_models.load_models()
                        
                        # Prepare text data from sentiment analysis
                        text_data = []
                        if sentiment_analysis.get('news_sentiment'):
                            text_data.append(sentiment_analysis.get('news_sentiment', {}).get('summary', ''))
                        if sentiment_analysis.get('social_sentiment'):
                            text_data.append(sentiment_analysis.get('social_sentiment', {}).get('summary', ''))
                        
                        if text_data and (alt_data_models.text_cnn_model or alt_data_models.multimodal_transformer):
                            text_features, text_meta = alt_data_models.prepare_text_features(text_data)
                            
                            if len(text_features) > 0:
                                # Get predictions from alternative data models
                                alt_prediction = alt_data_models.predict_sentiment(text_features)
                                if alt_prediction and 'error' not in alt_prediction:
                                    advanced_ml_predictions['alternative_data'] = {
                                        'sentiment_score': alt_prediction.get('sentiment_score', 0.0),
                                        'confidence': alt_prediction.get('confidence', 0.0),
                                        'model_type': 'text_cnn' if alt_data_models.text_cnn_model else 'multimodal'
                                    }
                                    logger.info(f"✅ Alternative data model prediction completed for {symbol}")
                    except Exception as e:
                        logger.debug(f"Alternative data models not available for {symbol}: {e}")
                    
                    # Try to load and use Bayesian Models (Market Regime, Probabilistic Predictions)
                    try:
                        from services.bayesian_macro_models import BayesianMacroModels
                        bayesian_models = BayesianMacroModels()
                        bayesian_models.load_models()
                        
                        # Identify market regime
                        regime_result = bayesian_models.identify_market_regimes(df)
                        if regime_result and 'error' not in regime_result:
                            advanced_ml_predictions['bayesian'] = {
                                'current_regime': regime_result.get('current_regime_name', 'Unknown'),
                                'regime_confidence': regime_result.get('current_regime_confidence', 0.0),
                                'regime_statistics': regime_result.get('regime_statistics', {})
                            }
                            logger.info(f"✅ Bayesian market regime analysis completed for {symbol}")
                        
                        # Get correlation analysis
                        correlation_result = bayesian_models.analyze_correlations(df)
                        if correlation_result and 'error' not in correlation_result:
                            if 'bayesian' not in advanced_ml_predictions:
                                advanced_ml_predictions['bayesian'] = {}
                            advanced_ml_predictions['bayesian']['correlations'] = correlation_result
                            logger.info(f"✅ Bayesian correlation analysis completed for {symbol}")
                    except Exception as e:
                        logger.debug(f"Bayesian models not available for {symbol}: {e}")
                    
                    # Try to load and use Reinforcement Learning Agent
                    try:
                        from services.reinforcement_learning_agent import ReinforcementLearningAgent
                        rl_agent = ReinforcementLearningAgent()
                        rl_agent.load_model()
                        
                        if rl_agent.q_network:
                            # Get current state from price data
                            current_state = rl_agent.env.get_state(df)
                            
                            if current_state is not None and len(current_state) > 0:
                                # Get action from RL agent
                                action = rl_agent.act(current_state, training=False)
                                action_names = ['HOLD', 'BUY', 'SELL']
                                
                                # Get Q-values for all actions
                                import torch
                                with torch.no_grad():
                                    state_tensor = torch.FloatTensor(current_state).unsqueeze(0)
                                    q_values = rl_agent.q_network(state_tensor)
                                    q_values_list = q_values.squeeze().tolist()
                                
                                advanced_ml_predictions['reinforcement_learning'] = {
                                    'action': action_names[action] if action < len(action_names) else 'HOLD',
                                    'action_index': int(action),
                                    'q_values': q_values_list,
                                    'confidence': float(max(q_values_list)) if q_values_list else 0.0
                                }
                                logger.info(f"✅ Reinforcement learning prediction completed for {symbol}: {action_names[action] if action < len(action_names) else 'HOLD'}")
                    except Exception as e:
                        logger.debug(f"Reinforcement learning agent not available for {symbol}: {e}")
                    
                    # Try to load and use Meta-Learner Fusion
                    try:
                        from services.meta_learner_fusion import MetaLearnerFusion
                        meta_learner = MetaLearnerFusion()
                        meta_learner.load_models()
                        
                        if meta_learner.meta_models and 'best' in meta_learner.meta_models:
                            # Prepare current data for meta-learner
                            current_data = {
                                'technical': technical_analysis,
                                'sentiment': sentiment_analysis,
                                'volume': volume_analysis
                            }
                            
                            # Add advanced ML predictions to meta-learner input
                            if advanced_ml_predictions:
                                current_data['advanced_ml'] = advanced_ml_predictions
                            
                            ensemble_pred = meta_learner.predict_ensemble(current_data)
                            if ensemble_pred and 'error' not in ensemble_pred:
                                advanced_ml_predictions['meta_learner'] = ensemble_pred
                                logger.info(f"✅ Meta-learner prediction completed for {symbol}")
                    except Exception as e:
                        logger.debug(f"Meta-learner not available for {symbol}: {e}")
                    
                    # Try to load and use Gradient Boosting models
                    try:
                        from services.gradient_boosting_models import GradientBoostingModels
                        gb_models = GradientBoostingModels()
                        gb_models.load_models()
                        
                        if gb_models.xgb_model or gb_models.lgb_model:
                            gb_pred = gb_models.predict_ensemble(df, target_col='close')
                            if gb_pred and 'error' not in gb_pred:
                                advanced_ml_predictions['gradient_boosting'] = gb_pred
                                logger.info(f"✅ Gradient boosting prediction completed for {symbol}")
                    except Exception as e:
                        logger.debug(f"Gradient boosting models not available for {symbol}: {e}")
                    
                    # Try to load and use Temporal Models (LSTM/Transformer)
                    try:
                        from services.temporal_models import TemporalModels
                        temporal_models = TemporalModels()
                        temporal_models.load_models()
                        
                        if temporal_models.lstm_model:
                            lstm_pred = temporal_models.predict_lstm(df)
                            if lstm_pred and 'error' not in lstm_pred:
                                advanced_ml_predictions['lstm'] = lstm_pred
                                logger.info(f"✅ LSTM prediction completed for {symbol}")
                        
                        if temporal_models.transformer_model:
                            transformer_pred = temporal_models.predict_transformer(df)
                            if transformer_pred and 'error' not in transformer_pred:
                                advanced_ml_predictions['transformer'] = transformer_pred
                                logger.info(f"✅ Transformer prediction completed for {symbol}")
                    except Exception as e:
                        logger.debug(f"Temporal models not available for {symbol}: {e}")
                        
                except Exception as e:
                    logger.debug(f"Advanced ML models not available for {symbol}: {e}")
            
            # Step 8: Combine all results and enhance ML signals with advanced models
            combined_ml_signals = ml_signals.copy()
            
            # Enhance ML signals with advanced models if available
            if advanced_ml_predictions:
                # Add alternative data sentiment
                if 'alternative_data' in advanced_ml_predictions:
                    alt_sentiment = advanced_ml_predictions['alternative_data'].get('sentiment_score', 0.0)
                    if alt_sentiment > 0.6:
                        combined_ml_signals['alternative_sentiment'] = 'bullish'
                    elif alt_sentiment < 0.4:
                        combined_ml_signals['alternative_sentiment'] = 'bearish'
                    else:
                        combined_ml_signals['alternative_sentiment'] = 'neutral'
                    combined_ml_signals['alternative_confidence'] = advanced_ml_predictions['alternative_data'].get('confidence', 0.0)
                
                # Add Bayesian regime information
                if 'bayesian' in advanced_ml_predictions:
                    regime = advanced_ml_predictions['bayesian'].get('current_regime_name', 'Unknown')
                    combined_ml_signals['market_regime'] = regime
                    combined_ml_signals['regime_confidence'] = advanced_ml_predictions['bayesian'].get('current_regime_confidence', 0.0)
                
                # Add RL action
                if 'reinforcement_learning' in advanced_ml_predictions:
                    rl_action = advanced_ml_predictions['reinforcement_learning'].get('action', 'HOLD')
                    combined_ml_signals['rl_action'] = rl_action
                    combined_ml_signals['rl_confidence'] = advanced_ml_predictions['reinforcement_learning'].get('confidence', 0.0)
                    
                    # Override signal if RL confidence is high
                    if combined_ml_signals['rl_confidence'] > 0.7:
                        if rl_action == 'BUY' and combined_ml_signals.get('signal') != 'BUY':
                            combined_ml_signals['signal'] = 'BUY'
                            combined_ml_signals['confidence'] = max(combined_ml_signals.get('confidence', 0.0), combined_ml_signals['rl_confidence'])
                        elif rl_action == 'SELL' and combined_ml_signals.get('signal') != 'SELL':
                            combined_ml_signals['signal'] = 'SELL'
                            combined_ml_signals['confidence'] = max(combined_ml_signals.get('confidence', 0.0), combined_ml_signals['rl_confidence'])
            
            results = {
                "technical": technical_analysis,
                "sentiment": sentiment_analysis,
                "volume": volume_analysis,
                "patterns": pattern_analysis,
                "ml_signals": combined_ml_signals
            }
            
            # Add advanced ML predictions if available
            if advanced_ml_predictions:
                results["advanced_ml"] = advanced_ml_predictions
                logger.info(f"✅ Advanced ML predictions included for {symbol}: {list(advanced_ml_predictions.keys())}")
            
            logger.info(f"✅ Traditional analysis completed for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Traditional analysis error for {symbol}: {e}", exc_info=True)
            # Return fallback results instead of empty dict
            return {
                "technical": {"signal": "HOLD", "rsi": 50.0, "macd": "neutral", "error": str(e)},
                "sentiment": {"news_sentiment": "neutral", "social_sentiment": "neutral", "error": str(e)},
                "volume": {"volume_trend": "neutral", "volume_signal": "HOLD", "error": str(e)},
                "patterns": {"candlestick_patterns": [], "error": str(e)},
                "ml_signals": {"signal": "HOLD", "confidence": 0.0, "error": str(e)}
            }
    
    async def _generate_genai_analysis(
        self, 
        symbol: str, 
        traditional_results: Dict[str, Any], 
        user_query: str = None
    ) -> Dict[str, Any]:
        """Generate GenAI analysis and reasoning"""
        
        if not self.conversation_chain:
            return self._get_fallback_genai_analysis(traditional_results)
        
        try:
            # Prepare context for GenAI
            context = self._prepare_genai_context(symbol, traditional_results, user_query)
            
            # Generate AI reasoning
            ai_prompt = f"""
            Analyze the following stock data for {symbol}:
            
            Technical Analysis: {json.dumps(traditional_results.get('technical', {}), indent=2)}
            Sentiment Analysis: {json.dumps(traditional_results.get('sentiment', {}), indent=2)}
            Volume Analysis: {json.dumps(traditional_results.get('volume', {}), indent=2)}
            Pattern Analysis: {json.dumps(traditional_results.get('patterns', {}), indent=2)}
            ML Signals: {json.dumps(traditional_results.get('ml_signals', {}), indent=2)}
            
            User Query: {user_query or "Provide comprehensive analysis"}
            
            Please provide:
            1. Clear recommendation (BUY/SELL/HOLD)
            2. Confidence level (0-100%)
            3. Price target and stop-loss
            4. Risk level (LOW/MEDIUM/HIGH)
            5. Detailed reasoning
            6. Natural language explanation
            """
            
            response = await self.conversation_chain.ainvoke({"input": ai_prompt})
            
            # Parse response
            parsed_response = self._parse_genai_response(response)
            
            return {
                "reasoning": parsed_response.get("reasoning", ""),
                "explanation": parsed_response.get("explanation", ""),
                "response": response
            }
            
        except Exception as e:
            logger.error(f"GenAI analysis error: {e}")
            return self._get_fallback_genai_analysis(traditional_results)
    
    async def _combine_analysis_results(
        self, 
        traditional_results: Dict[str, Any], 
        genai_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine traditional AI and GenAI results for final recommendation"""
        
        # Extract signals from traditional analysis
        technical_signal = traditional_results.get("technical", {}).get("signal", "HOLD")
        sentiment_signal = traditional_results.get("sentiment", {}).get("signal", "NEUTRAL")
        ml_signal = traditional_results.get("ml_signals", {}).get("prediction", "HOLD")
        
        # Weight the signals
        weights = {
            "technical": 0.3,
            "sentiment": 0.2,
            "ml": 0.3,
            "genai": 0.2
        }
        
        # Calculate weighted recommendation
        signal_scores = {
            "BUY": 1,
            "HOLD": 0,
            "SELL": -1
        }
        
        weighted_score = (
            signal_scores.get(technical_signal, 0) * weights["technical"] +
            signal_scores.get(sentiment_signal, 0) * weights["sentiment"] +
            signal_scores.get(ml_signal, 0) * weights["ml"]
        )
        
        # Determine final recommendation
        if weighted_score > 0.3:
            recommendation = "BUY"
            confidence = min(95, abs(weighted_score) * 100)
        elif weighted_score < -0.3:
            recommendation = "SELL"
            confidence = min(95, abs(weighted_score) * 100)
        else:
            recommendation = "HOLD"
            confidence = 60
        
        # Current price proxy (best effort)
        technical = traditional_results.get("technical", {}) or {}
        ml_signals_obj = traditional_results.get("ml_signals", {}) or {}
        current_price = (
            technical.get("current_price")
            or technical.get("last_price")
            or ml_signals_obj.get("current_price")
            or ml_signals_obj.get("last_price")
        )

        # Calculate price targets from technical/ML analysis
        price_target = technical.get("price_target") or ml_signals_obj.get("price_target")
        stop_loss = technical.get("stop_loss") or ml_signals_obj.get("stop_loss")

        # Trade plan defaults (entry/exit/holding period)
        entry_price = float(current_price) if isinstance(current_price, (int, float)) else None
        exit_price: Optional[float] = None

        # If target exists use it as exit for BUY; for SELL use a downside target if present
        if isinstance(price_target, (int, float)):
            exit_price = float(price_target)
        elif entry_price is not None:
            # Simple fallback targets when none are available
            if recommendation == "BUY":
                exit_price = round(entry_price * 1.03, 2)
            elif recommendation == "SELL":
                exit_price = round(entry_price * 0.97, 2)

        # Holding period heuristic by analysis depth
        depth = (genai_results.get("analysis_depth") or "").upper().strip()
        if not depth:
            # best effort: infer from traditional pipeline depth if passed in signals
            depth = (traditional_results.get("analysis_depth") or "").upper().strip()

        holding_period = None
        holding_days_min = None
        holding_days_max = None
        if depth == "QUICK":
            holding_period = "INTRADAY"
            holding_days_min, holding_days_max = 0, 1
        elif depth == "STANDARD":
            holding_period = "SWING"
            holding_days_min, holding_days_max = 3, 20
        else:
            holding_period = "POSITIONAL"
            holding_days_min, holding_days_max = 20, 90
        
        # Determine risk level
        risk_level = "MEDIUM"
        if confidence > 80:
            risk_level = "LOW"
        elif confidence < 50:
            risk_level = "HIGH"
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "price_target": price_target,
            "stop_loss": stop_loss,
            "risk_level": risk_level,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "holding_period": holding_period,
            "holding_days_min": holding_days_min,
            "holding_days_max": holding_days_max,
        }
    
    # Tool functions for GenAI
    def _get_quote_tool(self, symbol: str) -> str:
        """Tool for getting stock quotes"""
        try:
            if data_service:
                quote = asyncio.run(data_service.get_quote(symbol, "NSE"))
                return json.dumps(quote, indent=2)
            else:
                return f"Mock quote data for {symbol}"
        except Exception as e:
            return f"Error getting quote: {str(e)}"
    
    def _technical_analysis_tool(self, symbol: str) -> str:
        """Tool for technical analysis"""
        try:
            if self.technical_analyzer:
                # Mock analysis
                analysis = {"rsi": 65.2, "macd": "bullish", "signal": "BUY"}
                return json.dumps(analysis, indent=2)
            else:
                return f"Mock technical analysis for {symbol}"
        except Exception as e:
            return f"Error in technical analysis: {str(e)}"
    
    def _sentiment_analysis_tool(self, symbol: str) -> str:
        """Tool for sentiment analysis"""
        try:
            if self.sentiment_analyzer:
                sentiment = {"news_sentiment": "positive", "social_sentiment": "neutral"}
                return json.dumps(sentiment, indent=2)
            else:
                return f"Mock sentiment analysis for {symbol}"
        except Exception as e:
            return f"Error in sentiment analysis: {str(e)}"
    
    def _volume_analysis_tool(self, symbol: str) -> str:
        """Tool for volume analysis"""
        try:
            if self.volume_analyzer:
                analysis = {"volume_trend": "increasing", "volume_signal": "BUY"}
                return json.dumps(analysis, indent=2)
            else:
                return f"Mock volume analysis for {symbol}"
        except Exception as e:
            return f"Error in volume analysis: {str(e)}"
    
    def _pattern_analysis_tool(self, symbol: str) -> str:
        """Tool for pattern analysis"""
        try:
            if self.pattern_analyzer:
                patterns = {"candlestick_patterns": ["hammer", "doji"]}
                return json.dumps(patterns, indent=2)
            else:
                return f"Mock pattern analysis for {symbol}"
        except Exception as e:
            return f"Error in pattern analysis: {str(e)}"
    
    def _ml_signals_tool(self, symbol: str) -> str:
        """Tool for ML signals"""
        try:
            if self.ai_engine:
                signals = {"prediction": "BUY", "confidence": 0.85}
                return json.dumps(signals, indent=2)
            else:
                return f"Mock ML signals for {symbol}"
        except Exception as e:
            return f"Error in ML signals: {str(e)}"
    
    # Helper methods
    def _prepare_genai_context(self, symbol: str, results: Dict[str, Any], user_query: str) -> str:
        """Prepare context for GenAI analysis"""
        context = f"Stock: {symbol}\n"
        context += f"User Query: {user_query or 'Comprehensive analysis'}\n"
        context += f"Analysis Results: {json.dumps(results, indent=2)}"
        return context
    
    def _parse_genai_response(self, response: str) -> Dict[str, str]:
        """Parse GenAI response into structured format"""
        # Simple parsing - can be enhanced with more sophisticated parsing
        return {
            "reasoning": response,
            "explanation": response
        }
    
    def _get_fallback_genai_analysis(self, traditional_results: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when GenAI is not available"""
        return {
            "reasoning": "Analysis based on traditional AI methods only",
            "explanation": "GenAI not available. Using traditional analysis results.",
            "response": "Traditional AI analysis completed successfully."
        }
    
    def _get_used_methods(self, traditional_results: Dict[str, Any], genai_results: Dict[str, Any]) -> List[str]:
        """Get list of AI methods used in analysis"""
        methods = []
        
        if traditional_results.get("technical"):
            methods.append("Technical Analysis")
        if traditional_results.get("sentiment"):
            methods.append("Sentiment Analysis")
        if traditional_results.get("volume"):
            methods.append("Volume Analysis")
        if traditional_results.get("patterns"):
            methods.append("Pattern Analysis")
        if traditional_results.get("ml_signals"):
            methods.append("Machine Learning")
        if genai_results.get("reasoning"):
            methods.append("Generative AI")
        
        return methods
    
    def _create_error_result(self, symbol: str, error_message: str) -> UnifiedAnalysisResult:
        """Create error result"""
        return UnifiedAnalysisResult(
            symbol=symbol,
            technical_analysis={},
            sentiment_analysis={},
            volume_analysis={},
            pattern_analysis={},
            ml_signals={},
            ai_reasoning="",
            natural_language_explanation=f"Error: {error_message}",
            conversational_response=f"Analysis failed for {symbol}: {error_message}",
            final_recommendation="ERROR",
            confidence_score=0.0,
            analysis_timestamp=datetime.utcnow(),
            analysis_duration_ms=0,
            ai_methods_used=["Error"]
        )
    
    # ==================== CHAT FUNCTIONALITY (Consolidated from TraderGenAI) ====================
    
    def _setup_chat_functionality(self):
        """Setup chat functionality for conversational AI"""
        try:
            if not self.llm:
                logger.warning("No LLM available for chat functionality")
                return
            
            # Initialize chat history (LangChain 1.2.x compatible)
            self.chat_memory = InMemoryChatMessageHistory()
            
            # Create chat-specific tools
            chat_tools = [
                Tool(
                    name="get_stock_info",
                    description="Get current stock information and price",
                    func=self._get_stock_info_tool
                ),
                Tool(
                    name="analyze_stock",
                    description="Perform comprehensive stock analysis",
                    func=self._analyze_stock_tool
                ),
                Tool(
                    name="get_market_summary",
                    description="Get market summary and trends",
                    func=self._get_market_summary_tool
                )
            ]
            
            # Create chat chain using new LangChain approach
            from langchain_core.runnables.history import RunnableWithMessageHistory
            from langchain_core.prompts import ChatPromptTemplate
            
            chat_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful trading assistant. Provide accurate and helpful responses about stocks, markets, and trading."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            
            base_chat_chain = chat_prompt | self.llm
            self.chat_chain = RunnableWithMessageHistory(
                base_chat_chain,
                self._get_chat_history_store,
                input_messages_key="input",
                history_messages_key="chat_history"
            )
            
            logger.info("OK Chat functionality initialized")
            
        except Exception as e:
            logger.error(f"ERROR Failed to setup chat functionality: {e}")
            self.chat_memory = None
            self.chat_chain = None
    
    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Chat with the AI assistant using LangChain with fallback to Gemini if OpenAI fails.
        Includes simple in-memory cache to reduce repeated calls.
        """
        try:
            # Simple in-memory cache key for chat to reduce repeated calls
            cache_key = f"chat:{hash(message)}:{hash(str(context) if context else '')}"
            if not hasattr(self, "_chat_cache"):
                self._chat_cache = {}
            if cache_key in self._chat_cache:
                logger.info("Returning cached chat response")
                return self._chat_cache[cache_key]

            # Try LangChain conversation first
            if self.conversation_chain:
                try:
                    # LangChain with session_id in config for RunnableWithMessageHistory
                    config = {"configurable": {"session_id": "default"}}
                    response = self.conversation_chain.invoke({"input": message}, config=config)
                    # Handle AIMessage object (LangChain returns AIMessage, not dict)
                    if hasattr(response, "content"):
                        response_text = response.content
                    elif isinstance(response, dict):
                        response_text = response.get("response", "")
                    else:
                        response_text = str(response)
                    if response_text:
                        self._chat_cache[cache_key] = response_text
                        return response_text
                except Exception as openai_err:
                    # Detect OpenAI rate limit (429) and fallback to Gemini
                    err_str = str(openai_err).lower()
                    if "429" in err_str or "rate limit" in err_str or "too many requests" in err_str:
                        logger.warning("OpenAI rate limited (429), falling back to Gemini")
                        if GEMINI_AVAILABLE and self.gemini_api_key:
                            fallback_resp = await self._chat_with_gemini_fallback(message, context)
                            self._chat_cache[cache_key] = fallback_resp
                            return fallback_resp
                        else:
                            return "OpenAI is rate-limited and Gemini is not available. Please try again later."
                    else:
                        # For other errors, still try Gemini as last resort
                        logger.warning(f"LangChain chat failed: {openai_err}")
                        if GEMINI_AVAILABLE and self.gemini_api_key:
                            fallback_resp = await self._chat_with_gemini_fallback(message, context)
                            self._chat_cache[cache_key] = fallback_resp
                            return fallback_resp
                        raise
            else:
                # No LangChain chain, try Gemini directly
                if GEMINI_AVAILABLE and self.gemini_api_key:
                    fallback_resp = await self._chat_with_gemini_fallback(message, context)
                    self._chat_cache[cache_key] = fallback_resp
                    return fallback_resp
                else:
                    return "Chat functionality is not available. Please configure OpenAI or Gemini API key."
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def _chat_with_gemini_fallback(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Fallback to Gemini API when OpenAI rate limits are hit or unavailable.
        
        Args:
            message: User message
            context: Optional context dictionary
            
        Returns:
            AI response from Gemini
        """
        try:
            if not GEMINI_AVAILABLE:
                return "Gemini fallback is not available. Please install langchain-google-genai and google-generativeai packages."
            
            if not self.gemini_api_key:
                return "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
            
            # Initialize Gemini if not already done
            if not self.gemini_llm:
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    self.gemini_llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash-latest",
                        temperature=0.3,
                        google_api_key=self.gemini_api_key,
                        max_retries=3,
                        timeout=30,
                        max_output_tokens=2048,
                        max_tokens=2048,
                    )
                except Exception as e:
                    return f"Failed to initialize Gemini: {str(e)}"
            
            # Use Gemini to generate response
            if hasattr(self.gemini_llm, 'invoke'):
                # LangChain wrapper
                response = self.gemini_llm.invoke(message)
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
            else:
                # Direct Gemini API call (unlikely)
                response = self.gemini_llm.generate_content(message)
                response_text = response.text
            
            return response_text
        except Exception as e:
            logger.error(f"Gemini fallback error: {e}")
            return f"Gemini fallback error: {str(e)}"
    
    def set_chat_mode(self, enabled: bool = True):
        """Enable or disable chat mode"""
        self.chat_mode = enabled
        logger.info(f"Chat mode: {'Enabled' if enabled else 'Disabled'}")
    
    def clear_chat_memory(self):
        """Clear chat conversation history"""
        try:
            self._chat_histories.clear()
            logger.info("Chat memory cleared")
        except Exception:
            # best effort
            self._chat_histories = {}
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get chat conversation history"""
        try:
            store = self._get_chat_history_store("default")
            history = []
            for message in getattr(store, "messages", [])[-50:]:
                if hasattr(message, "content"):
                    history.append({
                        "role": "user" if message.__class__.__name__ == "HumanMessage" else "assistant",
                        "content": message.content,
                    })
            return history
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def chat_with_unified_ai(self, message: str, session_id: str = None, context_symbol: str = None) -> Dict[str, Any]:
        """
        Chat with unified AI system (async version for API)
        
        Args:
            message: User message
            session_id: Optional session ID
            context_symbol: Optional stock symbol context
            
        Returns:
            Chat response dictionary
        """
        try:
            # Use the existing chat method (now async)
            response = await self.chat(message, context_symbol)
            
            return {
                "message": message,
                "response": response,
                "session_id": session_id or f"session_{int(datetime.now().timestamp())}",
                "context_symbol": context_symbol,
                "timestamp": datetime.now().isoformat(),
                "ai_method": "unified"
            }
            
        except Exception as e:
            logger.error(f"Chat with unified AI failed: {e}")
            return {
                "message": message,
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "session_id": session_id or f"session_{int(datetime.now().timestamp())}",
                "context_symbol": context_symbol,
                "timestamp": datetime.now().isoformat(),
                "ai_method": "fallback",
                "error": str(e)
            }
    
    # Chat-specific tools
    def _get_stock_info_tool(self, symbol: str) -> str:
        """Tool for getting stock information"""
        try:
            # This would integrate with your data service
            return f"Stock information for {symbol}: Current price, volume, and basic metrics."
        except Exception as e:
            return f"Error getting stock info for {symbol}: {e}"
    
    async def analyze_stock_fallback(self, symbol: str, user_query: str = None) -> UnifiedAnalysisResult:
        """
        Fallback analysis method when GenAI is not available
        Uses only traditional AI analysis
        """
        try:
            logger.info(f"Performing fallback analysis for {symbol}")
            
            # Use traditional AI analysis only
            traditional_result = self.analyze_stock(symbol, user_query or "Provide a comprehensive analysis")
            
            if not traditional_result:
                # Create a basic result if analysis fails
                return UnifiedAnalysisResult(
                    symbol=symbol,
                    recommendation="HOLD",
                    confidence_score=50.0,
                    ai_reasoning="Traditional AI analysis completed",
                    natural_language_summary=f"Analysis for {symbol} completed using traditional methods. GenAI features are not available.",
                    analysis_result={
                        "technical_analysis": "Basic technical analysis completed",
                        "sentiment_analysis": "Sentiment analysis completed",
                        "volume_analysis": "Volume analysis completed"
                    }
                )
            
            # Convert traditional result to unified format
            return UnifiedAnalysisResult(
                symbol=symbol,
                recommendation=traditional_result.recommendation,
                confidence_score=traditional_result.confidence_score,
                ai_reasoning=traditional_result.ai_reasoning,
                natural_language_summary=traditional_result.natural_language_summary,
                analysis_result=traditional_result.analysis_result
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            # Return a basic result
            return UnifiedAnalysisResult(
                symbol=symbol,
                recommendation="HOLD",
                confidence_score=30.0,
                ai_reasoning="Analysis failed due to technical issues",
                natural_language_summary=f"Unable to complete analysis for {symbol}. Please try again later.",
                analysis_result={"error": str(e)}
            )
    
    def _analyze_stock_tool(self, symbol: str) -> str:
        """Tool for analyzing stock"""
        try:
            # Use the existing analysis functionality
            result = self.analyze_stock(symbol, "Please provide a comprehensive analysis")
            return result.natural_language_explanation
        except Exception as e:
            return f"Error analyzing {symbol}: {e}"
    
    def _get_market_summary_tool(self, query: str = "") -> str:
        """Tool for getting market summary"""
        try:
            return f"Market summary: Current market conditions, trends, and key indicators."
        except Exception as e:
            return f"Error getting market summary: {e}"
    
    async def batch_analyze_symbols(self, symbols: List[str], analysis_depth: str = "STANDARD", user_query: str = None) -> Dict[str, Any]:
        """
        Perform batch analysis on multiple symbols
        
        Args:
            symbols: List of stock symbols to analyze
            analysis_depth: Analysis depth (QUICK, STANDARD, COMPREHENSIVE)
            user_query: Optional common query for all symbols
            
        Returns:
            Dictionary with analysis results for each symbol
        """
        try:
            logger.info(f"Starting batch analysis for {len(symbols)} symbols")
            
            # Process symbols in parallel for efficiency
            tasks = []
            for symbol in symbols:
                task = self.analyze_stock_unified(
                    symbol=symbol,
                    user_query=user_query,
                    analysis_depth=analysis_depth,
                    include_charts=True,
                    include_news=True
                )
                tasks.append(task)
            
            # Wait for all analyses to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            batch_results = {}
            for i, (symbol, result) in enumerate(zip(symbols, results)):
                if isinstance(result, Exception):
                    logger.error(f"Analysis failed for {symbol}: {result}")
                    batch_results[symbol] = {
                        "error": str(result),
                        "status": "failed"
                    }
                else:
                    batch_results[symbol] = {
                        "symbol": result.symbol,
                        "recommendation": result.final_recommendation,
                        "confidence_score": result.confidence_score,
                        "ai_reasoning": result.ai_reasoning,
                        "natural_language_explanation": result.natural_language_explanation,
                        "price_target": result.price_target,
                        "stop_loss": result.stop_loss,
                        "risk_level": result.risk_level,
                        "analysis_timestamp": result.analysis_timestamp.isoformat(),
                        "processing_time_ms": result.analysis_duration_ms,
                        "status": "success"
                    }
            
            return {
                "batch_analysis": batch_results,
                "total_symbols": len(symbols),
                "successful_analyses": len([r for r in batch_results.values() if r.get("status") == "success"]),
                "failed_analyses": len([r for r in batch_results.values() if r.get("status") == "failed"]),
                "analysis_depth": analysis_depth,
                "user_query": user_query,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return {
                "error": str(e),
                "total_symbols": len(symbols),
                "successful_analyses": 0,
                "failed_analyses": len(symbols),
                "status": "failed"
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get Unified AI service status and capabilities
        
        Returns:
            Dictionary with service status information
        """
        try:
            # Check traditional AI services
            traditional_services = {
                "technical_analyzer": self.technical_analyzer is not None,
                "sentiment_analyzer": self.sentiment_analyzer is not None,
                "signal_generator": self.signal_generator is not None,
                "ai_engine": self.ai_engine is not None,
                "volume_analyzer": self.volume_analyzer is not None,
                "pattern_analyzer": self.pattern_analyzer is not None
            }
            
            # Check GenAI services
            genai_services = {
                "llm_available": self.llm is not None,
                "memory_enabled": self.memory is not None,
                "conversation_chain_available": self.conversation_chain is not None,
                "openai_api_key": self.openai_api_key is not None,
                "langchain_available": LANGCHAIN_AVAILABLE
            }
            
            # Count available services
            traditional_count = sum(1 for available in traditional_services.values() if available)
            genai_count = sum(1 for available in genai_services.values() if available)
            
            # Determine overall status
            overall_status = "healthy" if traditional_count > 0 else "degraded"
            if genai_count > 0:
                overall_status = "optimal"
            
            return {
                "service_name": "Unified AI Service",
                "overall_status": overall_status,
                "traditional_ai": {
                    "status": "available" if traditional_count > 0 else "unavailable",
                    "services_count": traditional_count,
                    "total_services": len(traditional_services),
                    "services": traditional_services
                },
                "generative_ai": {
                    "status": "available" if genai_count > 0 else "unavailable",
                    "services_count": genai_count,
                    "total_services": len(genai_services),
                    "services": genai_services
                },
                "capabilities": [
                    "Stock analysis and recommendations",
                    "Technical analysis (RSI, MACD, SMA, Bollinger Bands)",
                    "Sentiment analysis",
                    "Volume pattern analysis",
                    "Candlestick pattern detection",
                    "Machine learning signals",
                    "Natural language explanations",
                    "Conversational chat interface",
                    "Batch analysis processing",
                    "Risk assessment and price targets"
                ],
                "chat_mode": self.chat_mode,
                "data_service_available": data_service is not None,
                "database_available": SessionLocal is not None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {
                "service_name": "Unified AI Service",
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive market overview with AI analysis
        
        Returns:
            Dictionary containing market overview data
        """
        try:
            logger.info("Getting market overview")
            
            # Get market data from data service
            if data_service:
                # Get top indices
                nifty_data = await data_service.get_quote("NIFTY50", "NSE")
                sensex_data = await data_service.get_quote("SENSEX", "BSE")
                
                # Get sector performance (mock data for now)
                sector_performance = {
                    "IT": {"change": 1.2, "change_percent": 0.8},
                    "Banking": {"change": -0.8, "change_percent": -0.5},
                    "Pharma": {"change": 2.1, "change_percent": 1.3},
                    "Auto": {"change": 0.5, "change_percent": 0.3},
                    "Energy": {"change": -1.2, "change_percent": -0.8}
                }
                
                # Generate AI insights about market
                market_sentiment = "bullish" if nifty_data.get("change", 0) > 0 else "bearish"
                
                # Use GenAI for market analysis if available
                if self.llm:
                    try:
                        market_analysis_prompt = f"""
                        Analyze the current market conditions:
                        - NIFTY 50: {nifty_data.get('last_price', 0)} ({nifty_data.get('change_percent', 0):.2f}%)
                        - SENSEX: {sensex_data.get('last_price', 0)} ({sensex_data.get('change_percent', 0):.2f}%)
                        - Sector Performance: {sector_performance}
                        
                        Provide a brief market overview and key insights.
                        """
                        
                        response = await self.llm.ainvoke(market_analysis_prompt)
                        ai_insights = response.content if hasattr(response, 'content') else str(response)
                    except Exception as e:
                        logger.warning(f"GenAI market analysis failed: {e}")
                        ai_insights = "Market analysis based on traditional methods only."
                else:
                    ai_insights = "Market analysis based on traditional methods only."
                
                return {
                    "market_status": "open",
                    "indices": {
                        "nifty50": nifty_data,
                        "sensex": sensex_data
                    },
                    "sector_performance": sector_performance,
                    "market_sentiment": market_sentiment,
                    "ai_insights": ai_insights,
                    "key_levels": {
                        "support": nifty_data.get('last_price', 0) * 0.95,
                        "resistance": nifty_data.get('last_price', 0) * 1.05
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Fallback data
                return {
                    "market_status": "open",
                    "indices": {
                        "nifty50": {"last_price": 27372.82, "change": 32.82, "change_percent": 0.12},
                        "sensex": {"last_price": 23589.23, "change": 132.23, "change_percent": 0.56}
                    },
                    "sector_performance": {
                        "IT": {"change": 1.2, "change_percent": 0.8},
                        "Banking": {"change": -0.8, "change_percent": -0.5},
                        "Pharma": {"change": 2.1, "change_percent": 1.3}
                    },
                    "market_sentiment": "bullish",
                    "ai_insights": "Market showing positive momentum with mixed sector performance.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_notification(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test notification system
        
        Args:
            test_data: Test data for notification
            
        Returns:
            Dictionary containing test results
        """
        try:
            logger.info("Testing notification system")
            
            # Import notification service
            from services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Prepare test signal data
            test_signal = {
                "symbol": test_data.get("symbol", "TEST"),
                "action": test_data.get("action", "BUY"),
                "signal": test_data.get("signal", "STRONG_BUY"),
                "confidence": test_data.get("confidence", 0.85),
                "current_price": test_data.get("current_price", 100.0),
                "reasoning": test_data.get("reasoning", "Test notification"),
                "urgency": test_data.get("urgency", "HIGH"),
                "timestamp": datetime.now().isoformat()
            }
            
            # Test notification
            user_phone = test_data.get("phone", "+1234567890")
            result = await notification_service.send_trading_signal(test_signal, user_phone)
            
            return {
                "test_status": "completed",
                "signal_data": test_signal,
                "notification_result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing notification: {e}")
            return {
                "test_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_notification_preferences(self) -> Dict[str, Any]:
        """
        Get notification preferences
        
        Returns:
            Dictionary containing notification preferences
        """
        try:
            logger.info("Getting notification preferences")
            
            # Import notification service
            from services.notification_service import NotificationService
            notification_service = NotificationService()
            
            return {
                "preferences": notification_service.user_preferences,
                "available_channels": ["whatsapp", "sms", "email"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def update_notification_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update notification preferences
        
        Args:
            preferences: New notification preferences
            
        Returns:
            Dictionary containing update results
        """
        try:
            logger.info("Updating notification preferences")
            
            # Import notification service
            from services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Update preferences
            notification_service.user_preferences.update(preferences)
            
            return {
                "update_status": "success",
                "updated_preferences": notification_service.user_preferences,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return {
                "update_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_recommendations(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get AI-powered trading recommendations for a symbol
        
        Args:
            symbol: Stock symbol to get recommendations for
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            logger.info(f"Getting recommendations for {symbol}")
            
            # Perform analysis to generate recommendations
            analysis_result = await self.analyze_stock_unified(
                symbol=symbol,
                user_query=f"Provide trading recommendations for {symbol}",
                analysis_depth="COMPREHENSIVE",
                include_charts=True,
                include_news=True
            )
            
            # Generate multiple recommendations based on analysis
            recommendations = []
            
            # Primary recommendation based on analysis
            primary_rec = {
                "symbol": symbol,
                "recommendation": analysis_result.final_recommendation,
                "confidence_score": analysis_result.confidence_score,
                "reasoning": analysis_result.ai_reasoning,
                "price_target": analysis_result.price_target,
                "stop_loss": analysis_result.stop_loss,
                "risk_level": analysis_result.risk_level,
                "timeframe": "Short-term",
                "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
                "type": "primary"
            }
            recommendations.append(primary_rec)
            
            # Generate additional recommendations based on technical analysis
            if analysis_result.technical_analysis:
                tech_data = analysis_result.technical_analysis
                
                # RSI-based recommendation
                if tech_data.get("rsi"):
                    rsi = tech_data["rsi"]
                    if rsi > 70:
                        recommendations.append({
                            "symbol": symbol,
                            "recommendation": "SELL",
                            "confidence_score": 75.0,
                            "reasoning": f"RSI indicates overbought condition ({rsi:.1f})",
                            "price_target": analysis_result.price_target * 0.95 if analysis_result.price_target else None,
                            "stop_loss": analysis_result.price_target * 1.05 if analysis_result.price_target else None,
                            "risk_level": "HIGH",
                            "timeframe": "Short-term",
                            "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
                            "type": "technical_rsi"
                        })
                    elif rsi < 30:
                        recommendations.append({
                            "symbol": symbol,
                            "recommendation": "BUY",
                            "confidence_score": 70.0,
                            "reasoning": f"RSI indicates oversold condition ({rsi:.1f})",
                            "price_target": analysis_result.price_target * 1.05 if analysis_result.price_target else None,
                            "stop_loss": analysis_result.price_target * 0.95 if analysis_result.price_target else None,
                            "risk_level": "MEDIUM",
                            "timeframe": "Medium-term",
                            "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
                            "type": "technical_rsi"
                        })
                
                # MACD-based recommendation
                if tech_data.get("macd") == "bullish":
                    recommendations.append({
                        "symbol": symbol,
                        "recommendation": "BUY",
                        "confidence_score": 65.0,
                        "reasoning": "MACD shows bullish momentum",
                        "price_target": analysis_result.price_target,
                        "stop_loss": analysis_result.stop_loss,
                        "risk_level": "MEDIUM",
                        "timeframe": "Medium-term",
                        "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
                        "type": "technical_macd"
                    })
            
            # Sentiment-based recommendation
            if analysis_result.sentiment_analysis:
                sentiment_data = analysis_result.sentiment_analysis
                if sentiment_data.get("news_sentiment") == "positive":
                    recommendations.append({
                        "symbol": symbol,
                        "recommendation": "BUY",
                        "confidence_score": 60.0,
                        "reasoning": "Positive news sentiment detected",
                        "price_target": analysis_result.price_target,
                        "stop_loss": analysis_result.stop_loss,
                        "risk_level": "LOW",
                        "timeframe": "Long-term",
                        "analysis_timestamp": analysis_result.analysis_timestamp.isoformat(),
                        "type": "sentiment"
                    })
            
            # Limit results and sort by confidence
            recommendations = sorted(recommendations, key=lambda x: x["confidence_score"], reverse=True)[:limit]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get recommendations for {symbol}: {e}")
            # Return a basic recommendation as fallback
            return [{
                "symbol": symbol,
                "recommendation": "HOLD",
                "confidence_score": 30.0,
                "reasoning": f"Unable to generate recommendations due to technical issues: {str(e)}",
                "price_target": None,
                "stop_loss": None,
                "risk_level": "HIGH",
                "timeframe": "Unknown",
                "analysis_timestamp": datetime.now().isoformat(),
                "type": "fallback",
                "error": str(e)
            }]
    
    async def get_insights(self, symbol: str, insight_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Get AI-generated insights for a symbol
        
        Args:
            symbol: Stock symbol to get insights for
            insight_type: Type of insights (comprehensive, technical, sentiment, volume)
            
        Returns:
            Dictionary with insights data
        """
        try:
            logger.info(f"Getting {insight_type} insights for {symbol}")
            
            # Perform analysis based on insight type
            analysis_depth = "COMPREHENSIVE" if insight_type == "comprehensive" else "STANDARD"
            
            analysis_result = await self.analyze_stock_unified(
                symbol=symbol,
                user_query=f"Provide {insight_type} insights for {symbol}",
                analysis_depth=analysis_depth,
                include_charts=True,
                include_news=True
            )
            
            # Build insights based on type
            insights = {
                "symbol": symbol,
                "insight_type": insight_type,
                "timestamp": analysis_result.analysis_timestamp.isoformat(),
                "overall_sentiment": "neutral",
                "key_insights": [],
                "risk_assessment": {
                    "level": analysis_result.risk_level,
                    "factors": []
                },
                "recommendations": {
                    "primary": analysis_result.final_recommendation,
                    "confidence": analysis_result.confidence_score,
                    "reasoning": analysis_result.ai_reasoning
                }
            }
            
            # Technical insights
            if insight_type in ["comprehensive", "technical"] and analysis_result.technical_analysis:
                tech_data = analysis_result.technical_analysis
                insights["technical_insights"] = {
                    "rsi": tech_data.get("rsi"),
                    "macd_signal": tech_data.get("macd"),
                    "trend": "bullish" if tech_data.get("signal") == "BUY" else "bearish",
                    "strength": "strong" if analysis_result.confidence_score > 70 else "moderate"
                }
                
                # Add RSI insight
                if tech_data.get("rsi"):
                    rsi = tech_data["rsi"]
                    if rsi > 70:
                        insights["key_insights"].append(f"RSI indicates overbought condition ({rsi:.1f})")
                        insights["risk_assessment"]["factors"].append("Overbought condition")
                    elif rsi < 30:
                        insights["key_insights"].append(f"RSI indicates oversold condition ({rsi:.1f})")
                        insights["risk_assessment"]["factors"].append("Oversold condition")
            
            # Sentiment insights
            if insight_type in ["comprehensive", "sentiment"] and analysis_result.sentiment_analysis:
                sentiment_data = analysis_result.sentiment_analysis
                insights["sentiment_insights"] = {
                    "news_sentiment": sentiment_data.get("news_sentiment"),
                    "social_sentiment": sentiment_data.get("social_sentiment"),
                    "overall_sentiment": sentiment_data.get("news_sentiment", "neutral")
                }
                
                if sentiment_data.get("news_sentiment") == "positive":
                    insights["key_insights"].append("Positive news sentiment detected")
                elif sentiment_data.get("news_sentiment") == "negative":
                    insights["key_insights"].append("Negative news sentiment detected")
            
            # Volume insights
            if insight_type in ["comprehensive", "volume"] and analysis_result.volume_analysis:
                volume_data = analysis_result.volume_analysis
                insights["volume_insights"] = {
                    "trend": volume_data.get("volume_trend"),
                    "signal": volume_data.get("volume_signal"),
                    "strength": "high" if volume_data.get("volume_trend") == "increasing" else "normal"
                }
                
                if volume_data.get("volume_trend") == "increasing":
                    insights["key_insights"].append("Volume is increasing, indicating strong interest")
            
            # Pattern insights
            if insight_type in ["comprehensive", "patterns"] and analysis_result.pattern_analysis:
                pattern_data = analysis_result.pattern_analysis
                insights["pattern_insights"] = {
                    "patterns": pattern_data.get("candlestick_patterns", []),
                    "significance": "high" if len(pattern_data.get("candlestick_patterns", [])) > 0 else "low"
                }
                
                patterns = pattern_data.get("candlestick_patterns", [])
                if patterns:
                    insights["key_insights"].append(f"Detected patterns: {', '.join(patterns)}")
            
            # ML insights
            if insight_type in ["comprehensive", "ml"] and analysis_result.ml_signals:
                ml_data = analysis_result.ml_signals
                insights["ml_insights"] = {
                    "prediction": ml_data.get("prediction"),
                    "confidence": ml_data.get("confidence"),
                    "model_performance": "high" if ml_data.get("confidence", 0) > 0.8 else "moderate"
                }
            
            # Generate summary
            if analysis_result.confidence_score > 70:
                insights["overall_sentiment"] = "bullish" if analysis_result.final_recommendation == "BUY" else "bearish"
            elif analysis_result.confidence_score < 40:
                insights["overall_sentiment"] = "bearish" if analysis_result.final_recommendation == "SELL" else "neutral"
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get insights for {symbol}: {e}")
            return {
                "symbol": symbol,
                "insight_type": insight_type,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "overall_sentiment": "unknown",
                "key_insights": [f"Unable to generate insights due to technical issues: {str(e)}"],
                "risk_assessment": {
                    "level": "HIGH",
                    "factors": ["Technical error"]
                },
                "recommendations": {
                    "primary": "HOLD",
                    "confidence": 0.0,
                    "reasoning": "Unable to analyze due to technical issues"
                }
            }

# Global instance - will be created lazily to ensure .env is loaded first
_unified_ai_service_instance = None

def get_unified_ai_service_instance() -> UnifiedAIService:
    """Get or create the global UnifiedAIService instance (lazy initialization)"""
    global _unified_ai_service_instance
    if _unified_ai_service_instance is None:
        # Ensure .env is loaded (in case it wasn't loaded before module import)
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass
        _unified_ai_service_instance = UnifiedAIService()
    return _unified_ai_service_instance

# For backward compatibility - create instance, not property
unified_ai_service = get_unified_ai_service_instance()
