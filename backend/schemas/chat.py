"""
Chat schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime

class ChatSession(BaseModel):
    id: int
    session_name: str
    created_at: datetime
    message_count: int

class PredictionRequest(BaseModel):
    message: str
    prediction_type: str = "price"

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    reasoning: str
    timestamp: datetime
