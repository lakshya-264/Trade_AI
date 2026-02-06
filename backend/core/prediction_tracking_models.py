"""
Database Models for Price Prediction Tracking and Accuracy Monitoring
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text, Index, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database_unified import Base

class PricePredictionRecord(Base):
    """Store individual price predictions for accuracy tracking"""
    __tablename__ = "price_prediction_records"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # 1W, 1M, 2M, 3M, 6M, 1Y, 2Y
    prediction_date = Column(DateTime, nullable=False, index=True)
    target_date = Column(Date, nullable=False, index=True)  # Date when prediction should be evaluated
    
    # Prediction data
    predicted_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    predicted_change_percent = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    price_range_low_68 = Column(Float)
    price_range_high_68 = Column(Float)
    price_range_low_95 = Column(Float)
    price_range_high_95 = Column(Float)
    
    # Model information
    model_type = Column(String(50), nullable=False)  # 'temporal_ensemble', 'temporal_single', 'ensemble', 'factor_only', 'momentum_fallback', 'fallback'
    model_contributions = Column(JSON)  # Store model-specific contributions
    
    # Actual results (filled after target_date)
    actual_price = Column(Float, nullable=True)
    actual_change_percent = Column(Float, nullable=True)
    evaluated = Column(Boolean, default=False, index=True)
    evaluated_at = Column(DateTime, nullable=True)
    
    # Accuracy metrics (calculated after evaluation)
    price_error = Column(Float, nullable=True)  # Absolute error
    price_error_percent = Column(Float, nullable=True)  # Percentage error
    direction_correct = Column(Boolean, nullable=True)  # Was direction prediction correct?
    within_range_68 = Column(Boolean, nullable=True)  # Did actual fall within 68% range?
    within_range_95 = Column(Boolean, nullable=True)  # Did actual fall within 95% range?
    
    # Additional metadata
    analysis_data_hash = Column(String(64))  # Hash of analysis data used for prediction
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_symbol_timeframe_date', 'symbol', 'timeframe', 'prediction_date'),
        Index('idx_evaluated_timeframe', 'evaluated', 'timeframe', 'target_date'),
    )

class ModelPerformanceMetrics(Base):
    """Aggregated performance metrics for each model type and timeframe"""
    __tablename__ = "model_performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    evaluation_period_start = Column(Date, nullable=False, index=True)
    evaluation_period_end = Column(Date, nullable=False, index=True)
    
    # Metrics
    total_predictions = Column(Integer, default=0)
    evaluated_predictions = Column(Integer, default=0)
    
    # Accuracy metrics
    mean_absolute_error = Column(Float, nullable=True)
    mean_absolute_percentage_error = Column(Float, nullable=True)
    root_mean_squared_error = Column(Float, nullable=True)
    direction_accuracy = Column(Float, nullable=True)  # Percentage of correct direction predictions
    range_68_accuracy = Column(Float, nullable=True)  # Percentage within 68% range
    range_95_accuracy = Column(Float, nullable=True)  # Percentage within 95% range
    
    # Confidence vs accuracy correlation
    avg_confidence = Column(Float, nullable=True)
    high_confidence_accuracy = Column(Float, nullable=True)  # Accuracy for predictions with >70% confidence
    
    # Error distribution
    error_percentiles = Column(JSON)  # {p10, p25, p50, p75, p90, p95, p99}
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        Index('idx_model_timeframe_period', 'model_type', 'timeframe', 'evaluation_period_start', unique=True),
    )

class ModelTrainingLog(Base):
    """Log of model training sessions"""
    __tablename__ = "model_training_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False, index=True)  # 'lstm', 'transformer', 'xgb', 'lgb', etc.
    model_category = Column(String(50), nullable=False)  # 'temporal', 'gradient_boosting'
    timeframe = Column(String(10), nullable=True)  # 1W, 1M, etc.
    
    # Training details
    training_started_at = Column(DateTime, nullable=False, index=True)
    training_completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # 'running', 'completed', 'failed', 'cancelled'
    
    # Training data
    symbols_used = Column(JSON)  # List of symbols used for training
    data_points_count = Column(Integer, nullable=True)
    training_period_start = Column(Date, nullable=True)
    training_period_end = Column(Date, nullable=True)
    
    # Training metrics
    train_loss = Column(Float, nullable=True)
    validation_loss = Column(Float, nullable=True)
    test_loss = Column(Float, nullable=True)
    training_metrics = Column(JSON)  # Additional metrics (accuracy, R², etc.)
    
    # Model file info
    model_file_path = Column(String(500), nullable=True)
    model_version = Column(String(50), nullable=True)
    model_size_mb = Column(Float, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Metadata
    training_config = Column(JSON)  # Store training configuration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_model_status_date', 'model_type', 'status', 'training_started_at'),
    )

class ModelRetrainingSchedule(Base):
    """Schedule for automatic model retraining"""
    __tablename__ = "model_retraining_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False, index=True)
    model_category = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=True)
    
    # Schedule configuration
    schedule_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'on_demand', 'on_accuracy_drop'
    schedule_config = Column(JSON)  # Cron expression or trigger conditions
    
    # Retraining conditions
    retrain_on_accuracy_drop = Column(Boolean, default=False)
    accuracy_drop_threshold = Column(Float, nullable=True)  # Retrain if accuracy drops by this %
    min_days_between_retraining = Column(Integer, default=7)  # Minimum days between retraining
    
    # Status
    enabled = Column(Boolean, default=True, index=True)
    last_retrained_at = Column(DateTime, nullable=True)
    next_retraining_at = Column(DateTime, nullable=True, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        Index('idx_model_schedule_unique', 'model_type', 'timeframe', unique=True),
    )
