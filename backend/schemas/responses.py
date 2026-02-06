"""
Standardized API Response Schemas
Provides consistent response format across all API endpoints
"""

from typing import TypeVar, Generic, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Generic type for response data
T = TypeVar('T')

class ResponseStatus(str, Enum):
    """Standard response status values"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response format
    Used across all endpoints for consistency
    """
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    data: Optional[T] = Field(None, description="Response data payload")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response format for list endpoints
    """
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: List[T] = Field(..., description="List of items")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """
    Standardized error response format
    """
    success: bool = Field(False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Trading-specific response models
class TradingSignal(BaseModel):
    """Trading signal response"""
    symbol: str = Field(..., description="Stock symbol")
    signal: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., ge=0, le=100, description="Confidence percentage")
    price_target: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    reasoning: str = Field(..., description="AI reasoning for the signal")
    timestamp: datetime = Field(default_factory=datetime.now, description="Signal timestamp")

class MarketData(BaseModel):
    """Market data response"""
    symbol: str = Field(..., description="Stock symbol")
    price: float = Field(..., description="Current price")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Percentage change")
    volume: int = Field(..., description="Trading volume")
    high: float = Field(..., description="Day's high")
    low: float = Field(..., description="Day's low")
    open: float = Field(..., description="Opening price")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")

class PortfolioSummary(BaseModel):
    """Portfolio summary response"""
    total_value: float = Field(..., description="Total portfolio value")
    total_invested: float = Field(..., description="Total amount invested")
    total_pnl: float = Field(..., description="Total profit/loss")
    total_pnl_percent: float = Field(..., description="Total P&L percentage")
    positions_count: int = Field(..., description="Number of positions")
    timestamp: datetime = Field(default_factory=datetime.now, description="Summary timestamp")

# AI Analysis response models
class TechnicalAnalysis(BaseModel):
    """Technical analysis response"""
    symbol: str = Field(..., description="Stock symbol")
    rsi: Optional[float] = Field(None, description="RSI value")
    macd: Optional[Dict[str, float]] = Field(None, description="MACD values")
    sma_50: Optional[float] = Field(None, description="50-day SMA")
    sma_200: Optional[float] = Field(None, description="200-day SMA")
    bollinger_bands: Optional[Dict[str, float]] = Field(None, description="Bollinger Bands")
    support_levels: List[float] = Field(default_factory=list, description="Support levels")
    resistance_levels: List[float] = Field(default_factory=list, description="Resistance levels")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

class SentimentAnalysis(BaseModel):
    """Sentiment analysis response"""
    symbol: str = Field(..., description="Stock symbol")
    overall_sentiment: str = Field(..., description="Overall sentiment: POSITIVE, NEGATIVE, NEUTRAL")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to 1)")
    news_sentiment: Optional[Dict[str, Any]] = Field(None, description="News sentiment data")
    social_sentiment: Optional[Dict[str, Any]] = Field(None, description="Social media sentiment")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

class UnifiedAnalysisResult(BaseModel):
    """Unified AI analysis result"""
    symbol: str = Field(..., description="Stock symbol")
    recommendation: str = Field(..., description="Final recommendation")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score")
    ai_reasoning: str = Field(..., description="AI reasoning explanation")
    natural_language_summary: str = Field(..., description="Natural language summary")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    price_target: Optional[float] = Field(None, description="Price target")
    stop_loss: Optional[float] = Field(None, description="Stop loss")
    risk_level: str = Field("MEDIUM", description="Risk level: LOW, MEDIUM, HIGH")
    technical_analysis: Optional[TechnicalAnalysis] = Field(None, description="Technical analysis")
    sentiment_analysis: Optional[SentimentAnalysis] = Field(None, description="Sentiment analysis")

# Chat response models
class ChatMessage(BaseModel):
    """Chat message response"""
    message_id: str = Field(..., description="Unique message ID")
    message: str = Field(..., description="Message content")
    message_type: str = Field(..., description="user or assistant")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")

class ChatSession(BaseModel):
    """Chat session response"""
    session_id: str = Field(..., description="Unique session ID")
    messages: List[ChatMessage] = Field(..., description="Session messages")
    context_symbol: Optional[str] = Field(None, description="Context stock symbol")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

# Education response models
class EducationContent(BaseModel):
    """Education content response"""
    content_id: str = Field(..., description="Unique content ID")
    title: str = Field(..., description="Content title")
    content_type: str = Field(..., description="Content type")
    difficulty_level: str = Field(..., description="Difficulty level")
    content: str = Field(..., description="Content body")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

# Health check models
class HealthStatus(BaseModel):
    """Health status response"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency statuses")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")

# Utility functions for creating standardized responses
def create_success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    request_id: Optional[str] = None
) -> APIResponse:
    """Create a standardized success response"""
    return APIResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id
    )

def create_error_response(
    message: str,
    error_code: str = "GENERIC_ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        details=details,
        request_id=request_id
    )

def create_paginated_response(
    data: List[Any],
    total_count: int,
    page: int,
    page_size: int,
    message: str = "Data retrieved successfully"
) -> PaginatedResponse:
    """Create a standardized paginated response"""
    total_pages = (total_count + page_size - 1) // page_size
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        pagination={
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    )
