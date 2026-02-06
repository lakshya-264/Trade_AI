"""
Trading schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class QuoteRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"

class QuoteResponse(BaseModel):
    symbol: str
    last_price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime

class OrderRequest(BaseModel):
    symbol: str
    order_type: str
    quantity: int
    price: float

class OrderResponse(BaseModel):
    id: int
    symbol: str
    order_type: str
    quantity: int
    price: float
    order_status: str
    order_time: datetime

class PortfolioItem(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float

class TradingSignal(BaseModel):
    symbol: str
    signal_type: str
    confidence: float
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    created_at: datetime
