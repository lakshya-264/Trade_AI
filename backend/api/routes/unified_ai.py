"""
Unified AI API Routes
Combines Traditional AI Analysis with Generative AI for comprehensive trading insights
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from core.unified_ai_service import UnifiedAIService, UnifiedAnalysisResult
from core.data_service import data_service
from core.database_unified import get_db
from schemas.responses import APIResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Pydantic models for request/response
class UnifiedAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol to analyze")
    user_query: Optional[str] = Field(None, description="User's specific question or context")
    analysis_depth: str = Field("COMPREHENSIVE", description="Analysis depth: QUICK, STANDARD, COMPREHENSIVE")
    include_charts: bool = Field(True, description="Include chart analysis")
    include_news: bool = Field(True, description="Include news sentiment analysis")

class UnifiedChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    context_symbol: Optional[str] = Field(None, description="Stock symbol for context")

class BatchAnalysisRequest(BaseModel):
    symbols: List[str] = Field(..., description="List of stock symbols to analyze")
    analysis_depth: str = Field("STANDARD", description="Analysis depth")
    user_query: Optional[str] = Field(None, description="Common query for all symbols")

class UnifiedAnalysisResponse(BaseModel):
    symbol: str
    analysis_result: Dict[str, Any]
    confidence_score: float
    recommendation: str
    analysis_timestamp: datetime
    processing_time_ms: int
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_level: str = "MEDIUM"
    current_price: Optional[float] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    holding_period: Optional[str] = None
    holding_days_min: Optional[int] = None
    holding_days_max: Optional[int] = None

# Dependency to get Unified AI service
def get_unified_ai_service() -> UnifiedAIService:
    """Get Unified AI service instance"""
    try:
        return UnifiedAIService()
    except Exception as e:
        logger.error(f"Failed to initialize Unified AI service: {e}")
        raise HTTPException(status_code=503, detail="Unified AI service unavailable")

@router.post("/analyze", response_model=APIResponse[UnifiedAnalysisResponse])
async def analyze_stock_unified(
    request: UnifiedAnalysisRequest,
    background_tasks: BackgroundTasks,
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Perform comprehensive unified AI analysis on a stock symbol
    Combines traditional AI analysis with generative AI insights
    """
    try:
        logger.info(f"Starting unified analysis for {request.symbol}")
        
        # Perform unified analysis
        try:
            result = await unified_ai.analyze_stock_unified(
                symbol=request.symbol,
                user_query=request.user_query,
                analysis_depth=request.analysis_depth,
                include_charts=request.include_charts,
                include_news=request.include_news
            )
        except AttributeError:
            # Fallback if method doesn't exist
            logger.warning("analyze_stock_unified method not available, using fallback")
            result = await unified_ai.analyze_stock_fallback(
                symbol=request.symbol,
                user_query=request.user_query
            )
        
        if not result:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        # Store analysis result in database
        background_tasks.add_task(
            store_analysis_result,
            symbol=request.symbol,
            result=result,
            db=db
        )
        
        # Fetch current quote for the symbol
        try:
            quote = await data_service.get_quote(request.symbol, "NSE")
        except Exception:
            quote = {}

        # Prepare response
        response_data = UnifiedAnalysisResponse(
            symbol=result.symbol,
            analysis_result={
                "technical_analysis": result.technical_analysis,
                "sentiment_analysis": result.sentiment_analysis,
                "volume_analysis": result.volume_analysis,
                "pattern_analysis": result.pattern_analysis,
                "ml_signals": result.ml_signals,
                "ai_reasoning": result.ai_reasoning,
                "natural_language_explanation": result.natural_language_explanation,
                "conversational_response": result.conversational_response,
                "ai_methods_used": result.ai_methods_used,
                "quote": quote
            },
            confidence_score=result.confidence_score,
            recommendation=result.final_recommendation,
            price_target=result.price_target,
            stop_loss=result.stop_loss,
            risk_level=result.risk_level,
            entry_price=result.entry_price,
            exit_price=result.exit_price,
            holding_period=result.holding_period,
            holding_days_min=result.holding_days_min,
            holding_days_max=result.holding_days_max,
            analysis_timestamp=result.analysis_timestamp,
            processing_time_ms=result.analysis_duration_ms,
            current_price=quote.get("last_price")
        )
        
        return APIResponse(
            success=True,
            message=f"Unified analysis completed for {request.symbol}",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Unified analysis failed for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/chat", response_model=APIResponse[Dict[str, Any]])
async def chat_with_unified_ai(
    request: UnifiedChatRequest,
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Chat with Unified AI system
    Provides conversational interface with context-aware responses
    """
    try:
        logger.info(f"Processing chat message: {request.message[:50]}...")
        
        # Process chat message
        response = await unified_ai.chat_with_unified_ai(
            message=request.message,
            session_id=request.session_id,
            context_symbol=request.context_symbol
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="Chat processing failed")
        
        return APIResponse(
            success=True,
            message="Chat response generated successfully",
            data=response
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/batch-analyze", response_model=APIResponse[Dict[str, Any]])
async def batch_analyze_symbols(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Perform batch analysis on multiple symbols
    Efficiently processes multiple stocks with unified AI
    """
    try:
        logger.info(f"Starting batch analysis for {len(request.symbols)} symbols")
        
        # Perform batch analysis
        results = await unified_ai.batch_analyze_symbols(
            symbols=request.symbols,
            analysis_depth=request.analysis_depth,
            user_query=request.user_query
        )
        
        if not results:
            raise HTTPException(status_code=500, detail="Batch analysis failed")
        
        # Store batch results
        background_tasks.add_task(
            store_batch_results,
            results=results,
            db=db
        )
        
        return APIResponse(
            success=True,
            message=f"Batch analysis completed for {len(request.symbols)} symbols",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/status", response_model=APIResponse[Dict[str, Any]])
async def get_unified_ai_status(
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service)
):
    """
    Get Unified AI service status and capabilities
    """
    try:
        status = await unified_ai.get_service_status()
        
        return APIResponse(
            success=True,
            message="Service status retrieved successfully",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/recommendations/{symbol}", response_model=APIResponse[List[Dict[str, Any]]])
async def get_ai_recommendations(
    symbol: str,
    limit: int = 5,
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Get AI-powered trading recommendations for a symbol
    """
    try:
        recommendations = await unified_ai.get_recommendations(
            symbol=symbol,
            limit=limit
        )
        
        return APIResponse(
            success=True,
            message=f"Recommendations retrieved for {symbol}",
            data=recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to get recommendations for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")

@router.get("/insights/{symbol}", response_model=APIResponse[Dict[str, Any]])
async def get_ai_insights(
    symbol: str,
    insight_type: str = "comprehensive",
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Get AI-generated insights for a symbol
    """
    try:
        insights = await unified_ai.get_insights(
            symbol=symbol,
            insight_type=insight_type
        )
        
        return APIResponse(
            success=True,
            message=f"Insights retrieved for {symbol}",
            data=insights
        )
        
    except Exception as e:
        logger.error(f"Failed to get insights for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Insights failed: {str(e)}")

@router.get("/market-overview", response_model=APIResponse[Dict[str, Any]])
async def get_market_overview(
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Get comprehensive market overview with AI analysis
    """
    try:
        market_overview = await unified_ai.get_market_overview()
        
        return APIResponse(
            success=True,
            message="Market overview retrieved successfully",
            data=market_overview
        )
        
    except Exception as e:
        logger.error(f"Failed to get market overview: {e}")
        raise HTTPException(status_code=500, detail=f"Market overview failed: {str(e)}")

@router.post("/test-notification", response_model=APIResponse[Dict[str, Any]])
async def test_notification(
    test_data: Dict[str, Any],
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Test notification system
    """
    try:
        result = await unified_ai.test_notification(test_data)
        
        return APIResponse(
            success=True,
            message="Notification test completed",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Failed to test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Notification test failed: {str(e)}")

@router.get("/notification-preferences", response_model=APIResponse[Dict[str, Any]])
async def get_notification_preferences(
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Get notification preferences
    """
    try:
        preferences = await unified_ai.get_notification_preferences()
        
        return APIResponse(
            success=True,
            message="Notification preferences retrieved",
            data=preferences
        )
        
    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Preferences retrieval failed: {str(e)}")

@router.post("/notification-preferences", response_model=APIResponse[Dict[str, Any]])
async def update_notification_preferences(
    preferences: Dict[str, Any],
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Update notification preferences
    """
    try:
        result = await unified_ai.update_notification_preferences(preferences)
        
        return APIResponse(
            success=True,
            message="Notification preferences updated",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Preferences update failed: {str(e)}")

# Background task functions
async def store_analysis_result(symbol: str, result: UnifiedAnalysisResult, db):
    """Store analysis result in database"""
    try:
        # Implementation for storing analysis results
        logger.info(f"Storing analysis result for {symbol}")
        # Add database storage logic here
    except Exception as e:
        logger.error(f"Failed to store analysis result for {symbol}: {e}")

async def store_batch_results(results: Dict[str, Any], db):
    """Store batch analysis results in database"""
    try:
        logger.info(f"Storing batch results for {len(results)} symbols")
        # Add database storage logic here
    except Exception as e:
        logger.error(f"Failed to store batch results: {e}")

# ==================== CHAT ENDPOINTS (Consolidated from TraderGenAI) ====================

@router.post("/chat/simple", response_model=APIResponse[Dict[str, Any]])
async def chat_with_ai_simple(
    request: UnifiedChatRequest,
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service),
    db = Depends(get_db)
):
    """
    Chat with the AI assistant (simple legacy handler)
    """
    try:
        # Get chat response
        try:
            response = unified_ai.chat(
                message=request.message,
                context=request.context_symbol
            )
        except Exception as chat_error:
            logger.warning(f"Chat failed, using fallback: {chat_error}")
            response = f"I apologize, but I'm currently unable to process your message: '{request.message}'. Please try again later or contact support."
        
        # Prepare response data
        response_data = {
            "message": request.message,
            "response": response,
            "session_id": request.session_id,
            "context_symbol": request.context_symbol,
            "timestamp": datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Chat response generated successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/chat/history", response_model=APIResponse[List[Dict[str, str]]])
async def get_chat_history(
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service)
):
    """
    Get chat conversation history
    """
    try:
        history = unified_ai.get_chat_history()
        
        return APIResponse(
            success=True,
            message="Chat history retrieved successfully",
            data=history
        )
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Chat history failed: {str(e)}")

@router.delete("/chat/history", response_model=APIResponse[Dict[str, str]])
async def clear_chat_history(
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service)
):
    """
    Clear chat conversation history
    """
    try:
        unified_ai.clear_chat_memory()
        
        return APIResponse(
            success=True,
            message="Chat history cleared successfully",
            data={"status": "cleared"}
        )
        
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Clear chat history failed: {str(e)}")

@router.post("/chat/mode", response_model=APIResponse[Dict[str, str]])
async def set_chat_mode(
    enabled: bool,
    unified_ai: UnifiedAIService = Depends(get_unified_ai_service)
):
    """
    Enable or disable chat mode
    """
    try:
        unified_ai.set_chat_mode(enabled)
        
        return APIResponse(
            success=True,
            message=f"Chat mode {'enabled' if enabled else 'disabled'} successfully",
            data={"chat_mode": "enabled" if enabled else "disabled"}
        )
        
    except Exception as e:
        logger.error(f"Failed to set chat mode: {e}")
        raise HTTPException(status_code=500, detail=f"Set chat mode failed: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for Unified AI service"""
    return {
        "success": True,
        "message": "Unified AI service is healthy",
        "data": {
            "service": "unified_ai",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    }
