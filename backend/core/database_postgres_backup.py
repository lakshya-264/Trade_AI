"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trader:secret@172.31.37.244:5432/trader_ai")

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    mobile_number = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")

# Market data model
class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

# AI Analysis model
class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    analysis_type = Column(String)  # TECHNICAL, FUNDAMENTAL, SENTIMENT
    signal = Column(String)  # BUY, SELL, HOLD
    confidence = Column(Float)
    reasoning = Column(Text)
    technical_indicators = Column(JSON)
    fundamental_metrics = Column(JSON)
    sentiment_data = Column(JSON)
    price_target = Column(Float)
    stop_loss = Column(Float)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# Portfolio model
class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    quantity = Column(Integer)
    average_price = Column(Float)
    current_price = Column(Float)
    pnl = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Order model
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    order_type = Column(String)  # BUY, SELL
    quantity = Column(Integer)
    price = Column(Float)
    order_status = Column(String)  # PENDING, FILLED, CANCELLED, REJECTED
    order_time = Column(DateTime, default=datetime.utcnow)
    filled_time = Column(DateTime)
    filled_price = Column(Float)
    commission = Column(Float, default=0.0)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User")

# Trading signals model
class TradingSignal(Base):
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    signal_type = Column(String)  # BUY, SELL, HOLD
    confidence = Column(Float)
    technical_analysis = Column(Text)
    fundamental_analysis = Column(Text)
    sentiment_analysis = Column(Text)
    price_target = Column(Float)
    stop_loss = Column(Float)
    risk_reward_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# Risk metrics model
class RiskMetrics(Base):
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    volatility = Column(Float)
    beta = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    var_95 = Column(Float)  # Value at Risk 95%
    expected_return = Column(Float)
    standard_deviation = Column(Float)
    correlation_nifty = Column(Float)
    correlation_sensex = Column(Float)
    calculated_at = Column(DateTime, default=datetime.utcnow)

# Performance metrics model
class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_return = Column(Float)
    annualized_return = Column(Float)
    volatility = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    beta = Column(Float)
    calculated_at = Column(DateTime, default=datetime.utcnow)

# Import chat models
# Chat models imported separately to avoid circular imports

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
