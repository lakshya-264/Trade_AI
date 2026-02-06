"""
TraderGenAI API Routes
Advanced AI-powered trading assistant endpoints
"""

from fastapi import HTTPException, APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from core.trader_gen_ai import trader_gen_ai, AnalysisResult
from core.auth_dependencies import get_current_user
from core.database_unified import User

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    session_id: Optional[str] = None

class AnalysisRequest(BaseModel):
    symbol: str
    query: Optional[str] = None

class AnalysisResponse(BaseModel):
    symbol: str
    recommendation: str
    confidence: float
    reasoning: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    signal_analysis: Dict[str, Any]
    timestamp: str

class InsightRequest(BaseModel):
    symbols: List[str]
    analysis_type: str = "comprehensive"  # comprehensive, technical, sentiment, signals

class InsightResponse(BaseModel):
    insights: List[Dict[str, Any]]
    market_summary: Dict[str, Any]
    timestamp: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat with TraderGenAI assistant"""
    try:
        result = await trader_gen_ai.chat(request.message, request.session_id)
        
        return ChatResponse(
            response=result["response"],
            timestamp=result["timestamp"],
            session_id=result.get("session_id")
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Comprehensive stock analysis with AI reasoning"""
    try:
        result = await trader_gen_ai.analyze_stock(request.symbol, request.query)
        
        if result.recommendation == "ERROR":
            raise HTTPException(status_code=400, detail=result.reasoning)
        
        return AnalysisResponse(
            symbol=result.symbol,
            recommendation=result.recommendation,
            confidence=result.confidence,
            reasoning=result.reasoning,
            price_target=result.price_target,
            stop_loss=result.stop_loss,
            technical_analysis=result.technical_analysis,
            sentiment_analysis=result.sentiment_analysis,
            signal_analysis=result.signal_analysis,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/insights", response_model=InsightResponse)
async def get_market_insights(
    request: InsightRequest,
    current_user: User = Depends(get_current_user)
):
    """Get automated trading insights for multiple symbols"""
    try:
        insights = []
        
        for symbol in request.symbols:
            try:
                if request.analysis_type == "comprehensive":
                    result = await trader_gen_ai.analyze_stock(symbol)
                    insight = {
                        "symbol": symbol,
                        "recommendation": result.recommendation,
                        "confidence": result.confidence,
                        "reasoning": result.reasoning,
                        "price_target": result.price_target,
                        "stop_loss": result.stop_loss
                    }
                else:
                    # Simplified analysis for specific types
                    insight = await _get_simplified_insight(symbol, request.analysis_type)
                
                insights.append(insight)
                
            except Exception as e:
                logger.error(f"Insight error for {symbol}: {e}")
                insights.append({
                    "symbol": symbol,
                    "error": str(e),
                    "recommendation": "ERROR"
                })
        
        # Generate market summary
        market_summary = _generate_market_summary(insights)
        
        return InsightResponse(
            insights=insights,
            market_summary=market_summary,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Insights error: {e}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")

@router.get("/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get conversation history for a session"""
    try:
        from core.database_unified import SessionLocal, ChatMessage
        
        session = SessionLocal()
        try:
            messages = session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp).all()
            
            conversation = []
            for msg in messages:
                conversation.append({
                    "type": msg.message_type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "is_ai_generated": msg.is_ai_generated
                })
            
            return {
                "session_id": session_id,
                "conversation": conversation,
                "message_count": len(conversation)
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Conversation history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")

@router.get("/predictions")
async def get_prediction_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get recent prediction history"""
    try:
        from core.database_unified import SessionLocal, PredictionHistory
        
        session = SessionLocal()
        try:
            predictions = session.query(PredictionHistory).filter(
                PredictionHistory.user_id == current_user.id
            ).order_by(PredictionHistory.created_at.desc()).limit(limit).all()
            
            history = []
            for pred in predictions:
                history.append({
                    "id": pred.id,
                    "symbol": pred.symbol,
                    "prediction_type": pred.prediction_type,
                    "confidence_score": pred.confidence_score,
                    "created_at": pred.created_at.isoformat(),
                    "prediction_data": pred.prediction_data
                })
            
            return {
                "predictions": history,
                "total_count": len(history)
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Prediction history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions: {str(e)}")

@router.get("/status")
async def get_ai_status():
    """Get TraderGenAI status and capabilities"""
    try:
        status = {
            "ai_available": trader_gen_ai.llm is not None,
            "memory_enabled": trader_gen_ai.memory is not None,
            "conversation_chain_available": trader_gen_ai.conversation_chain is not None,
            "analysis_tools_count": len(trader_gen_ai.analysis_tools),
            "capabilities": [
                "Stock analysis and recommendations",
                "Technical analysis (RSI, MACD, SMA, Bollinger Bands)",
                "Sentiment analysis",
                "Trading signal generation",
                "Natural language chat",
                "Conversation memory",
                "Multi-symbol insights",
                "Risk assessment"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"AI status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI status: {str(e)}")

# Helper functions
async def _get_simplified_insight(symbol: str, analysis_type: str) -> Dict[str, Any]:
    """Get simplified insight for specific analysis type"""
    try:
        if analysis_type == "technical":
            from core.technical_analysis import TechnicalAnalysisService
            from core.data_service import data_service
            
            ta_service = TechnicalAnalysisService()
            historical_data = await data_service.get_historical_data(symbol, "NSE", days=30)
            
            if not historical_data:
                return {"symbol": symbol, "error": "No historical data", "recommendation": "ERROR"}
            
            rsi = ta_service.calculate_rsi(historical_data)
            macd = ta_service.calculate_macd(historical_data)
            
            return {
                "symbol": symbol,
                "analysis_type": "technical",
                "rsi": rsi,
                "macd": macd,
                "recommendation": "BUY" if rsi < 30 else "SELL" if rsi > 70 else "HOLD"
            }
            
        elif analysis_type == "sentiment":
            from core.sentiment_analysis import SentimentAnalysisService
            
            sentiment_service = SentimentAnalysisService()
            # Mock sentiment data for now
            sentiment = {
                "overall_sentiment": "positive",
                "confidence": 0.75
            }
            
            return {
                "symbol": symbol,
                "analysis_type": "sentiment",
                "sentiment": sentiment,
                "recommendation": "BUY" if sentiment["overall_sentiment"] == "positive" else "HOLD"
            }
            
        else:  # signals
            from core.signal_generator import SignalGeneratorService
            from core.data_service import data_service
            
            signal_service = SignalGeneratorService()
            quote = await data_service.get_quote(symbol, "NSE")
            
            if not quote:
                return {"symbol": symbol, "error": "No quote data", "recommendation": "ERROR"}
            
            # Simple signal generation
            current_price = quote.get("lastPrice", 0)
            signal = "BUY" if current_price > 0 else "HOLD"
            
            return {
                "symbol": symbol,
                "analysis_type": "signals",
                "signal": signal,
                "current_price": current_price,
                "recommendation": signal
            }
            
    except Exception as e:
        logger.error(f"Simplified insight error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e), "recommendation": "ERROR"}

def _generate_market_summary(insights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate market summary from insights"""
    try:
        total_symbols = len(insights)
        buy_signals = sum(1 for i in insights if i.get("recommendation") == "BUY")
        sell_signals = sum(1 for i in insights if i.get("recommendation") == "SELL")
        hold_signals = sum(1 for i in insights if i.get("recommendation") == "HOLD")
        error_signals = sum(1 for i in insights if i.get("recommendation") == "ERROR")
        
        # Calculate average confidence
        confidences = [i.get("confidence", 0) for i in insights if "confidence" in i]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Determine overall market sentiment
        if buy_signals > sell_signals and buy_signals > hold_signals:
            market_sentiment = "BULLISH"
        elif sell_signals > buy_signals and sell_signals > hold_signals:
            market_sentiment = "BEARISH"
        else:
            market_sentiment = "NEUTRAL"
        
        return {
            "total_symbols": total_symbols,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals,
            "error_signals": error_signals,
            "average_confidence": round(avg_confidence, 3),
            "market_sentiment": market_sentiment,
            "success_rate": round((total_symbols - error_signals) / total_symbols * 100, 1) if total_symbols > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Market summary generation error: {e}")
        return {
            "total_symbols": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "error_signals": 0,
            "average_confidence": 0,
            "market_sentiment": "UNKNOWN",
            "success_rate": 0
        }
