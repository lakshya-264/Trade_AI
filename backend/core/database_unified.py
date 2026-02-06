"""
Unified Database Configuration and Models
All models in one file to avoid circular imports
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Text, Numeric, BigInteger, UniqueConstraint, Date, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool, QueuePool
from datetime import datetime, date
import os

# Database URL - Read from .env file in project root
# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

DATABASE_URL = os.getenv("DATABASE_URL_PRIMARY") or os.getenv("DATABASE_URL") or "sqlite:///./trader_ai.db"

# Create engine with driver-specific args
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Configure connection pool to handle concurrent requests
# For SQLite: Use NullPool to avoid connection sharing issues, create new connection per request
# For PostgreSQL: Use standard pool settings with increased size
if is_sqlite:
    # SQLite: Use NullPool to avoid connection sharing issues
    # Each request gets a fresh connection, avoiding "closed database" errors
    from sqlalchemy.pool import NullPool
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={
            "check_same_thread": False,
            "timeout": 20.0  # Increase timeout for concurrent access
        },
        poolclass=NullPool,  # No connection pooling - fresh connection per request
        pool_pre_ping=False,  # Not needed for NullPool
    )
else:
    # PostgreSQL: Standard pool configuration with increased limits
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args=connect_args,
        pool_size=20,  # Increased from 10
        max_overflow=30,  # Increased from 20
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
    )

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

# ============================================================
# PHASE 3: Historical Accuracy Tracking for NIFTY Opening Predictions
# ============================================================
class NiftyOpeningPrediction(Base):
    """Store predictions and actual openings for accuracy tracking and model improvement"""
    __tablename__ = "nifty_opening_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(Date, nullable=False, index=True)  # Date of prediction (day before opening)
    actual_opening_date = Column(Date, nullable=False, index=True)  # Date when market opened
    
    # Predicted values
    predicted_opening = Column(Float, nullable=False)
    predicted_lower_bound = Column(Float, nullable=False)
    predicted_upper_bound = Column(Float, nullable=False)
    predicted_direction = Column(String(20))  # BULLISH, BEARISH, NEUTRAL
    predicted_confidence = Column(Float)  # 0.0 to 1.0
    
    # Actual values
    actual_opening = Column(Float, nullable=True)  # NULL until market opens
    actual_direction = Column(String(20), nullable=True)
    
    # Factor contributions (stored as JSON)
    factor_contributions = Column(JSON, nullable=True)  # Store all factor weights and impacts
    
    # Accuracy metrics (calculated after actual opening)
    error_points = Column(Float, nullable=True)  # Absolute error in points
    error_percentage = Column(Float, nullable=True)  # Percentage error
    direction_correct = Column(Boolean, nullable=True)  # Was direction prediction correct?
    within_range = Column(Boolean, nullable=True)  # Did actual fall within predicted range?
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index for fast lookups
    __table_args__ = (
        Index('idx_prediction_date', 'prediction_date'),
        Index('idx_actual_date', 'actual_opening_date'),
        UniqueConstraint('prediction_date', 'actual_opening_date', name='uq_prediction_actual_date'),
    )

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile_number = Column(String(30), unique=True, index=True, nullable=True)
    # Align with existing Postgres schema column name
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(30), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    # Demo/Paper Trading balance
    demo_cash_balance = Column(Float, default=1000000.0, nullable=True)  # Default 10L for demo trading
    real_cash_balance = Column(Float, default=0.0, nullable=True)  # For future real trading
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    portfolio_items = relationship("Portfolio", back_populates="user")
    orders = relationship("Order", back_populates="user")
    performance_metrics = relationship("PerformanceMetrics", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    alert_triggers = relationship("AlertTrigger", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")
    learning_progress = relationship("UserProgress", back_populates="user")
    certificates = relationship("UserCertificate", back_populates="user")
    learning_sessions = relationship("LearningSession", back_populates="user")
    bookmarks = relationship("UserBookmark", back_populates="user")
    notes = relationship("UserNote", back_populates="user")
    feedback = relationship("UserFeedback", back_populates="user")
    behavior_tracking = relationship("UserBehaviorTracking", back_populates="user")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="user", cascade="all, delete-orphan")

# UserSession model - Tracks active user sessions
class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)  # JWT jti (JWT ID)
    device_info = Column(String(255), nullable=True)  # Browser/device name
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")

# Market data model
class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True)
    exchange = Column(String(10), default="NSE", index=True)
    last_price = Column(Float, default=0.0)
    change = Column(Float, default=0.0)
    change_percent = Column(Float, default=0.0)
    volume = Column(Integer, default=0)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_market_data_symbol_exchange_timestamp', 'symbol', 'exchange', 'timestamp'),
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
    )

# Portfolio Metadata model - Stores portfolio information (name, description, allocation)
class PortfolioMetadata(Base):
    __tablename__ = "portfolio_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_value = Column(Float, default=0.0)  # Initial cash allocation
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Portfolio model - Stores individual stock holdings
class Portfolio(Base):
    __tablename__ = "portfolios"  # Changed from "portfolio" to "portfolios" for consistency
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    symbol = Column(String(50), index=True)
    quantity = Column(Integer, default=0)
    average_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolio_items")
    
    # Composite index for common query pattern
    __table_args__ = (
        Index('idx_portfolio_user_symbol', 'user_id', 'symbol'),
    )

# Order model
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    symbol = Column(String(50), index=True)
    order_type = Column(String(20))
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    order_status = Column(String(20), default="PENDING", index=True)
    order_time = Column(DateTime, default=datetime.utcnow, index=True)
    filled_time = Column(DateTime)
    filled_price = Column(Float)
    commission = Column(Float, default=0.0)
    notes = Column(Text)
    is_demo = Column(Boolean, default=True)  # Default to demo/paper trading mode
    
    # Relationships
    user = relationship("User", back_populates="orders")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_order_user_status_time', 'user_id', 'order_status', 'order_time'),
        Index('idx_order_user_symbol_time', 'user_id', 'symbol', 'order_time'),
    )

# Position model - Tracks open positions (equity and options) similar to Sensibull
class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Position identification
    symbol = Column(String(50), nullable=False, index=True)  # Underlying symbol (e.g., NIFTY, RELIANCE)
    instrument_type = Column(String(10), nullable=False, default="EQUITY")  # EQUITY, CE, PE, FUT
    strike_price = Column(Float, nullable=True)  # For options
    expiry_date = Column(DateTime, nullable=True)  # For options/futures
    option_type = Column(String(2), nullable=True)  # CE or PE for options
    
    # Position details
    quantity = Column(Integer, nullable=False, default=0)  # Positive for long, negative for short
    average_price = Column(Numeric(10, 2), nullable=False)  # Average entry price
    current_price = Column(Numeric(10, 2), nullable=False, default=0.0)  # Current market price
    lot_size = Column(Integer, default=1)  # Lot size (50 for NIFTY, 1 for equity)
    
    # Financial metrics
    invested_value = Column(Numeric(15, 2), nullable=False, default=0.0)  # Total invested
    current_value = Column(Numeric(15, 2), nullable=False, default=0.0)  # Current market value
    unrealized_pnl = Column(Numeric(15, 2), nullable=False, default=0.0)  # Unrealized P&L
    unrealized_pnl_percent = Column(Numeric(10, 4), nullable=False, default=0.0)  # P&L percentage
    
    # Options Greeks (for options positions)
    delta = Column(Numeric(10, 4), nullable=True)
    gamma = Column(Numeric(10, 6), nullable=True)
    theta = Column(Numeric(10, 4), nullable=True)
    vega = Column(Numeric(10, 4), nullable=True)
    
    # Strategy information
    strategy_id = Column(String(100), nullable=True, index=True)  # If part of a strategy
    strategy_name = Column(String(255), nullable=True)  # Strategy name
    leg_id = Column(String(50), nullable=True)  # Leg ID if part of multi-leg strategy
    
    # Status
    is_active = Column(Boolean, default=True, index=True)  # Active position
    is_demo = Column(Boolean, default=True, index=True)  # Demo or real trading
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False)  # When position was opened
    
    # Relationships
    user = relationship("User", back_populates="positions")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_position_user_symbol', 'user_id', 'symbol', 'is_active'),
        Index('idx_position_user_strategy', 'user_id', 'strategy_id', 'is_active'),
        Index('idx_position_user_active', 'user_id', 'is_active', 'updated_at'),
    )
    
    def get_position_key(self) -> str:
        """Get unique key for position (for grouping similar positions)"""
        if self.instrument_type in ['CE', 'PE']:
            return f"{self.symbol}_{self.instrument_type}_{self.strike_price}_{self.expiry_date}"
        return f"{self.symbol}_{self.instrument_type}"

# Trading signals model
class TradingSignal(Base):
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True)
    signal_type = Column(String(20))
    confidence = Column(Float, default=0.0)
    technical_analysis = Column(Text)
    fundamental_analysis = Column(Text)
    sentiment_analysis = Column(Text)
    price_target = Column(Float)
    stop_loss = Column(Float)
    risk_reward_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# AI Analysis model
class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True)
    analysis_type = Column(String(50))
    signal = Column(String(20))
    confidence = Column(Float, default=0.0)
    reasoning = Column(Text)
    technical_indicators = Column(JSON)
    fundamental_metrics = Column(JSON)
    sentiment_data = Column(JSON)
    price_target = Column(Float)
    stop_loss = Column(Float)
    risk_level = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# Risk metrics model
class RiskMetrics(Base):
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True)
    volatility = Column(Float, default=0.0)
    beta = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    var_95 = Column(Float, default=0.0)
    expected_return = Column(Float, default=0.0)
    standard_deviation = Column(Float, default=0.0)
    correlation_nifty = Column(Float, default=0.0)
    correlation_sensex = Column(Float, default=0.0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

# Performance metrics model
class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_return = Column(Float, default=0.0)
    annualized_return = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    beta = Column(Float, default=0.0)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="performance_metrics")

# Chat Session model
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(255), unique=True, index=True)
    session_name = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

# Chat Message model
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message_type = Column(String(50))  # 'user', 'assistant', 'system', 'prediction'
    content = Column(Text)
    metadata_json = Column(JSON)  # For storing prediction data, context, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_ai_generated = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User")

# Prediction History model
class PredictionHistory(Base):
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String(50), index=True)
    prediction_type = Column(String(50))  # 'price', 'volatility', 'signal', 'sentiment'
    prediction_data = Column(JSON)
    confidence_score = Column(Float)
    actual_result = Column(JSON)  # Store actual results for accuracy tracking
    accuracy_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")

# Market News model
class MarketNews(Base):
    __tablename__ = "market_news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    content = Column(Text)
    source = Column(String(100))
    url = Column(String(500))
    sentiment_score = Column(Float)
    sentiment_label = Column(String(50))  # 'positive', 'negative', 'neutral'
    symbols_mentioned = Column(JSON)  # List of symbols mentioned
    published_at = Column(DateTime)
    embedding = Column(Text)  # Vector embedding for RAG
    category = Column(String(100))  # 'market', 'sector', 'policy', 'earnings'
    importance_score = Column(Float, default=0.0)

# Trading Knowledge model
class TradingKnowledge(Base):
    __tablename__ = "trading_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100))  # 'technical_analysis', 'fundamental', 'risk_management', 'trading_strategies'
    title = Column(String(500))
    content = Column(Text)
    tags = Column(JSON)  # List of tags for better search
    embedding = Column(Text)  # Vector embedding
    difficulty_level = Column(String(50))  # 'beginner', 'intermediate', 'advanced'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# Chat Context model
class ChatContext(Base):
    __tablename__ = "chat_context"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id"))
    context_type = Column(String(100))  # 'portfolio', 'watchlist', 'recent_trades', 'market_state'
    context_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession")

# OTP verification model - Extended for forgot password support
class OTPVerification(Base):
    __tablename__ = "otp_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional for forgot password
    mobile_number = Column(String(20), nullable=True)  # Legacy field, kept for backward compatibility
    otp_code = Column(String(10), nullable=True)  # Legacy field, kept for backward compatibility
    
    # New fields for unified OTP service
    phone_or_email = Column(String(255), index=True, nullable=True)  # Unified identifier (phone or email)
    otp = Column(String(6), nullable=True)  # OTP code (use this instead of otp_code)
    purpose = Column(String(50), nullable=True, default="password_reset")  # Purpose: password_reset, verification, etc.
    is_email = Column(Boolean, default=False)  # Whether identifier is email
    attempts = Column(Integer, default=0)  # Verification attempt counter
    
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<OTPVerification(id={self.id}, phone_or_email='{self.phone_or_email}', otp='{self.otp}', purpose='{self.purpose}')>"

# Alert model
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String(50), index=True)
    name = Column(String(255))
    condition_type = Column(String(50))  # price, indicator, volume, pattern, custom, smart_money_volume
    operator = Column(String(50))  # above, below, crosses_above, crosses_below, equals, etc.
    value = Column(Float)
    custom_conditions = Column(JSON)  # For multi-condition alerts
    notifications = Column(JSON)  # {"in_app": true, "email": false, "sms": false}
    cooldown_minutes = Column(Integer, default=30)
    status = Column(String(20), default="active")  # active, paused, triggered, expired, disabled
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    alert_metadata = Column(JSON)  # Additional metadata
    
    # Relationships
    user = relationship("User")
    triggers = relationship("AlertTrigger", back_populates="alert", cascade="all, delete-orphan")

# Alert Trigger model
class AlertTrigger(Base):
    __tablename__ = "alert_triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String(50), index=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    condition_data = Column(JSON)  # Store the condition data that triggered
    message = Column(Text)
    severity = Column(String(20), default="medium")  # low, medium, high
    
    # Relationships
    alert = relationship("Alert", back_populates="triggers")
    user = relationship("User")

# Smart Money Volume Activity model
class SmartMoneyVolumeActivity(Base):
    __tablename__ = "smart_money_volume_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True)
    timeframe = Column(String(10))  # 1D, 1H, etc.
    lower_timeframe = Column(String(10))  # 5m, 15m, etc.
    z_len = Column(Integer)  # Window length for Z-score calculation
    threshold_abs = Column(Float)  # Absolute Z-score threshold
    who_filter = Column(String(20))  # Both, Retail, Smart Money
    levels_data = Column(JSON)  # Array of level objects
    bubble_data = Column(JSON)  # Bubble object with strongest event
    pl_table = Column(JSON)  # P/L volume totals
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for efficient querying
    __table_args__ = (
        {'extend_existing': True}
    )

# Watchlist model
class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255))
    symbols = Column(JSON)  # Array of symbols
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Backtest Results model
class BacktestResult(Base):
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symbol = Column(String(50), index=True, nullable=False)
    strategy_type = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    parameters = Column(JSON)  # Entry threshold, stop loss, take profit
    metrics = Column(JSON)      # Win rate, profit factor, etc.
    trades = Column(JSON)       # Array of trade objects
    equity_curve = Column(JSON) # Equity curve data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")

# Pattern Outcome Tracking model - for historical pattern success rates
class PatternOutcome(Base):
    __tablename__ = "pattern_outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True, nullable=False)
    pattern_name = Column(String(100), index=True, nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1D, 4H, 1H, etc.
    detected_at = Column(DateTime, nullable=False, index=True)
    pattern_confidence = Column(Float)  # Confidence when detected
    predicted_direction = Column(String(10))  # BULLISH, BEARISH, NEUTRAL
    actual_direction = Column(String(10))  # BULLISH, BEARISH, NEUTRAL (filled after outcome)
    price_at_detection = Column(Float, nullable=False)
    price_after_1d = Column(Float)  # Price 1 day after detection
    price_after_3d = Column(Float)  # Price 3 days after detection
    price_after_5d = Column(Float)  # Price 5 days after detection
    outcome_success = Column(Boolean)  # True if prediction was correct
    outcome_verified = Column(Boolean, default=False)  # True when outcome is confirmed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index for faster queries
    __table_args__ = (
        Index('idx_pattern_symbol_timeframe', 'symbol', 'pattern_name', 'timeframe'),
    )

# Backtest Configurations model
class BacktestConfig(Base):
    __tablename__ = "backtest_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    strategy_name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Stock Master List model
class StockMaster(Base):
    __tablename__ = "stock_master"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    isin = Column(String(20))
    exchange = Column(String(10), nullable=False, index=True)
    sector = Column(String(100))
    sub_sector = Column(String(100))
    industry = Column(String(100))
    face_value = Column(Numeric(10, 2))
    listing_date = Column(Date)
    market_cap = Column(Numeric(20, 2))
    company_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Financial Data model (Quarterly/Annual)
class FinancialData(Base):
    __tablename__ = "financial_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # 'QUARTERLY' or 'ANNUAL'
    period_end = Column(Date, nullable=False)
    revenue = Column(Numeric(20, 2))
    net_profit = Column(Numeric(20, 2))
    net_worth = Column(Numeric(20, 2))
    total_assets = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    current_assets = Column(Numeric(20, 2))
    current_liabilities = Column(Numeric(20, 2))
    eps = Column(Numeric(10, 2))
    book_value = Column(Numeric(10, 2))
    ebit = Column(Numeric(20, 2))
    capital_employed = Column(Numeric(20, 2))
    free_cash_flow = Column(Numeric(20, 2))
    filing_date = Column(Date)
    source_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'period_type', 'period_end', name='uq_financial_data'),
    )

# Financial Ratios model (Calculated)
class FinancialRatios(Base):
    __tablename__ = "financial_ratios"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    current_price = Column(Numeric(10, 2))
    pe_ratio = Column(Numeric(10, 2))
    pb_ratio = Column(Numeric(10, 2))
    roe = Column(Numeric(10, 2))
    roce = Column(Numeric(10, 2))
    debt_to_equity = Column(Numeric(10, 2))
    current_ratio = Column(Numeric(10, 2))
    operating_margin = Column(Numeric(10, 2))
    profit_growth_5y = Column(Numeric(10, 2))
    revenue_growth_5y = Column(Numeric(10, 2))
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'period_end', name='uq_financial_ratios'),
    )

# Screener Growth Metrics model
class ScreenerGrowthMetrics(Base):
    __tablename__ = "screener_growth_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    # Compounded Sales Growth
    sales_growth_10y = Column(Numeric(10, 2))
    sales_growth_5y = Column(Numeric(10, 2))
    sales_growth_3y = Column(Numeric(10, 2))
    sales_growth_ttm = Column(Numeric(10, 2))
    # Compounded Profit Growth
    profit_growth_10y = Column(Numeric(10, 2))
    profit_growth_5y = Column(Numeric(10, 2))
    profit_growth_3y = Column(Numeric(10, 2))
    profit_growth_ttm = Column(Numeric(10, 2))
    # Stock Price CAGR
    price_cagr_10y = Column(Numeric(10, 2))
    price_cagr_5y = Column(Numeric(10, 2))
    price_cagr_3y = Column(Numeric(10, 2))
    price_cagr_1y = Column(Numeric(10, 2))
    # Return on Equity
    roe_10y = Column(Numeric(10, 2))
    roe_5y = Column(Numeric(10, 2))
    roe_3y = Column(Numeric(10, 2))
    roe_last_year = Column(Numeric(10, 2))
    fetched_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', name='uq_screener_growth_metrics'),
    )

# Screener Balance Sheet model
class ScreenerBalanceSheet(Base):
    __tablename__ = "screener_balance_sheet"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    equity_capital = Column(Numeric(20, 2))
    reserves = Column(Numeric(20, 2))
    borrowings = Column(Numeric(20, 2))
    total_equity = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    total_assets = Column(Numeric(20, 2))
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'period_end', name='uq_screener_balance_sheet'),
    )

# Screener Cash Flow model
class ScreenerCashFlow(Base):
    __tablename__ = "screener_cash_flow"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    operating_cash_flow = Column(Numeric(20, 2))
    investing_cash_flow = Column(Numeric(20, 2))
    financing_cash_flow = Column(Numeric(20, 2))
    net_cash_flow = Column(Numeric(20, 2))
    free_cash_flow = Column(Numeric(20, 2))
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'period_end', name='uq_screener_cash_flow'),
    )

# Screener Shareholding Pattern model
class ScreenerShareholding(Base):
    __tablename__ = "screener_shareholding"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    period_end = Column(Date, nullable=False)
    promoters = Column(Numeric(10, 2))
    fiis = Column(Numeric(10, 2))
    diis = Column(Numeric(10, 2))
    government = Column(Numeric(10, 2))
    public = Column(Numeric(10, 2))
    no_of_shareholders = Column(BigInteger)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'period_end', name='uq_screener_shareholding'),
    )

# Daily Market Data model (Enhanced)
class DailyMarketData(Base):
    __tablename__ = "daily_market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    close_price = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    delivery_percent = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_daily_market_data'),
    )

# Screener Results model
class ScreenerResult(Base):
    __tablename__ = "screener_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filter_config = Column(JSON, nullable=False)
    results = Column(JSON, nullable=False)
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")

# Saved Screener Filters model
class ScreenerFilter(Base):
    __tablename__ = "screener_filters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    filter_config = Column(JSON, nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Paper Trading Account model
class PaperAccount(Base):
    __tablename__ = "paper_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    initial_capital = Column(Numeric(15, 2), nullable=False, default=100000.0)
    available_capital = Column(Numeric(15, 2), nullable=False, default=100000.0)
    invested_capital = Column(Numeric(15, 2), nullable=False, default=0.0)
    current_value = Column(Numeric(15, 2), nullable=False, default=100000.0)
    total_pnl = Column(Numeric(15, 2), nullable=False, default=0.0)
    total_pnl_percent = Column(Numeric(10, 4), nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User")
    orders = relationship("PaperOrder", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("PaperPosition", back_populates="account", cascade="all, delete-orphan")

# Paper Trading Order model
class PaperOrder(Base):
    __tablename__ = "paper_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(255), unique=True, index=True, nullable=False)
    account_id = Column(String(255), ForeignKey("paper_accounts.account_id"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, SL, SL_LIMIT
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    stop_loss = Column(Numeric(10, 2), nullable=True)
    target = Column(Numeric(10, 2), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, EXECUTED, CANCELLED, REJECTED
    executed_price = Column(Numeric(10, 2), nullable=True)
    executed_quantity = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    account = relationship("PaperAccount", back_populates="orders")

# Paper Trading Position model
class PaperPosition(Base):
    __tablename__ = "paper_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(255), ForeignKey("paper_accounts.account_id"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    average_price = Column(Numeric(10, 2), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    invested_value = Column(Numeric(15, 2), nullable=False)
    current_value = Column(Numeric(15, 2), nullable=False)
    unrealized_pnl = Column(Numeric(15, 2), nullable=False, default=0.0)
    unrealized_pnl_percent = Column(Numeric(10, 4), nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("PaperAccount", back_populates="positions")
    
    __table_args__ = (
        UniqueConstraint('account_id', 'symbol', name='uq_paper_position'),
    )

# User Feedback model for self-learning system
class UserFeedback(Base):
    """Track user feedback on predictions and recommendations"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # What the feedback is about
    entity_type = Column(String(50), nullable=False, index=True)  # 'prediction', 'recommendation', 'analysis'
    entity_id = Column(String(255), nullable=False, index=True)  # ID of the prediction/recommendation
    symbol = Column(String(50), index=True)  # Stock symbol if applicable
    
    # Feedback data
    feedback_type = Column(String(50), nullable=False)  # 'helpful', 'not_helpful', 'accurate', 'inaccurate', 'useful', 'not_useful'
    rating = Column(Integer)  # 1-5 rating
    comment = Column(Text, nullable=True)
    
    # Additional metadata
    meta_data = Column(JSON, nullable=True)  # Store additional context
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    
    def __repr__(self):
        return f"<UserFeedback(user_id={self.user_id}, entity_type={self.entity_type}, feedback_type={self.feedback_type})>"

# User Behavior Tracking model
class UserBehaviorTracking(Base):
    """Track user actions for learning preferences and behavior"""
    __tablename__ = "user_behavior_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Action details
    action_type = Column(String(100), nullable=False, index=True)  # 'viewed_prediction', 'followed_recommendation', 'ignored_recommendation', 'placed_order', 'viewed_analysis'
    entity_type = Column(String(50), nullable=False)  # 'prediction', 'recommendation', 'analysis', 'order'
    entity_id = Column(String(255), nullable=False, index=True)  # ID of the entity
    symbol = Column(String(50), index=True)  # Stock symbol if applicable
    
    # Action metadata
    meta_data = Column(JSON, nullable=True)  # Store action-specific data (e.g., order details, time spent)
    
    # Context
    session_id = Column(String(255), nullable=True, index=True)  # Track user sessions
    referrer = Column(String(255), nullable=True)  # Where did the action come from
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="behavior_tracking")
    
    def __repr__(self):
        return f"<UserBehaviorTracking(user_id={self.user_id}, action_type={self.action_type}, entity_type={self.entity_type})>"

# Import extended market education models so SQLAlchemy registers them
try:
    from models.market_education_models import (
        UserProgress,
        UserCertificate,
        LearningSession,
        UserBookmark,
        UserNote,
    )
except Exception as import_error:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import market education models: {import_error}")

# Import Strategy and PaperTrade models so SQLAlchemy registers them
try:
    from models.strategy import Strategy, PaperTrade
except Exception as import_error:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import strategy models: {import_error}")

# Utility to initialize tables
def init_db():
    """Initialize all database tables"""
    Base.metadata.create_all(bind=engine)

# Database dependency for FastAPI
def get_db():
    """Get database session dependency for FastAPI with proper error handling"""
    db = None
    try:
        db = SessionLocal()
        # Test connection is alive (for SQLite)
        if is_sqlite:
            try:
                db.execute(text("SELECT 1"))
            except Exception:
                # Connection is bad, create new session
                try:
                    db.close()
                except Exception:
                    pass
                db = SessionLocal()
        yield db
    except Exception as e:
        # Rollback on any error
        if db:
            try:
                db.rollback()
            except Exception:
                pass
        raise
    finally:
        # Always close session safely
        if db:
            try:
                db.close()
            except Exception:
                pass

# Create tables on import
if __name__ != "__main__":
    init_db()
