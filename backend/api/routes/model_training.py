"""
API Routes for Model Training and Performance Monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging

from core.database_unified import get_db
from core.auth_dependencies import get_current_active_user
from services.prediction_tracking_service import prediction_tracking_service
from core.prediction_tracking_models import (
    PricePredictionRecord,
    ModelPerformanceMetrics,
    ModelTrainingLog,
    ModelRetrainingSchedule
)
from sqlalchemy import desc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model-training", tags=["Model Training"])

@router.post("/train/temporal")
async def train_temporal_models(
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = None,
    days: int = 365,
    model_types: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Trigger training of temporal models (LSTM/Transformer) for 1-week predictions
    Runs in background
    """
    try:
        from scripts.train_temporal_models import train_temporal_models
        
        # Default symbols if not provided
        if symbols is None:
            symbols = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                "HINDUNILVR", "BHARTIARTL", "SBIN", "BAJFINANCE", "KOTAKBANK"
            ]
        
        if model_types is None:
            model_types = ['lstm', 'transformer']
        
        # Run training in background
        background_tasks.add_task(train_temporal_models, db, symbols, days, model_types)
        
        return {
            "success": True,
            "message": "Temporal model training started in background",
            "symbols": symbols,
            "model_types": model_types
        }
        
    except Exception as e:
        logger.error(f"Error starting temporal model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/gradient-boosting")
async def train_gradient_boosting_models(
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = None,
    days: int = 500,
    model_types: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Trigger training of gradient boosting models (XGBoost/LightGBM) for 1-month predictions
    Runs in background
    """
    try:
        from scripts.train_gradient_boosting_models import train_gradient_boosting_models
        
        # Default symbols if not provided
        if symbols is None:
            symbols = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                "HINDUNILVR", "BHARTIARTL", "SBIN", "BAJFINANCE", "KOTAKBANK"
            ]
        
        if model_types is None:
            model_types = ['xgb', 'lgb']
        
        # Run training in background
        background_tasks.add_task(train_gradient_boosting_models, db, symbols, days, model_types)
        
        return {
            "success": True,
            "message": "Gradient boosting model training started in background",
            "symbols": symbols,
            "model_types": model_types
        }
        
    except Exception as e:
        logger.error(f"Error starting gradient boosting model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate-predictions")
async def evaluate_predictions(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    days_overdue: int = 0,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Evaluate predictions that have reached their target date"""
    try:
        evaluated = await prediction_tracking_service.evaluate_predictions(
            db=db,
            symbol=symbol,
            timeframe=timeframe,
            days_overdue=days_overdue
        )
        
        return {
            "success": True,
            "evaluated_count": len(evaluated),
            "evaluated_predictions": [
                {
                    "id": p.id,
                    "symbol": p.symbol,
                    "timeframe": p.timeframe,
                    "predicted_price": p.predicted_price,
                    "actual_price": p.actual_price,
                    "price_error_percent": p.price_error_percent,
                    "direction_correct": p.direction_correct
                }
                for p in evaluated
            ]
        }
        
    except Exception as e:
        logger.error(f"Error evaluating predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-metrics")
async def calculate_performance_metrics(
    model_type: str,
    timeframe: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate performance metrics for a model type and timeframe"""
    try:
        metrics = await prediction_tracking_service.calculate_performance_metrics(
            db=db,
            model_type=model_type,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found")
        
        return {
            "success": True,
            "metrics": {
                "model_type": metrics.model_type,
                "timeframe": metrics.timeframe,
                "total_predictions": metrics.total_predictions,
                "evaluated_predictions": metrics.evaluated_predictions,
                "mean_absolute_error": metrics.mean_absolute_error,
                "mean_absolute_percentage_error": metrics.mean_absolute_percentage_error,
                "root_mean_squared_error": metrics.root_mean_squared_error,
                "direction_accuracy": metrics.direction_accuracy,
                "range_68_accuracy": metrics.range_68_accuracy,
                "range_95_accuracy": metrics.range_95_accuracy,
                "avg_confidence": metrics.avg_confidence,
                "high_confidence_accuracy": metrics.high_confidence_accuracy,
                "error_percentiles": metrics.error_percentiles
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-summary")
async def get_performance_summary(
    model_type: Optional[str] = None,
    timeframe: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance summary for models"""
    try:
        metrics_list = prediction_tracking_service.get_model_performance_summary(
            db=db,
            model_type=model_type,
            timeframe=timeframe
        )
        
        return {
            "success": True,
            "metrics": [
                {
                    "model_type": m.model_type,
                    "timeframe": m.timeframe,
                    "evaluation_period": {
                        "start": m.evaluation_period_start.isoformat() if m.evaluation_period_start else None,
                        "end": m.evaluation_period_end.isoformat() if m.evaluation_period_end else None
                    },
                    "total_predictions": m.total_predictions,
                    "evaluated_predictions": m.evaluated_predictions,
                    "mean_absolute_percentage_error": m.mean_absolute_percentage_error,
                    "direction_accuracy": m.direction_accuracy,
                    "range_68_accuracy": m.range_68_accuracy,
                    "range_95_accuracy": m.range_95_accuracy,
                    "avg_confidence": m.avg_confidence
                }
                for m in metrics_list
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-logs")
async def get_training_logs(
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get training logs"""
    try:
        query = db.query(ModelTrainingLog)
        
        if model_type:
            query = query.filter(ModelTrainingLog.model_type == model_type)
        if status:
            query = query.filter(ModelTrainingLog.status == status)
        
        logs = query.order_by(desc(ModelTrainingLog.training_started_at)).limit(limit).all()
        
        return {
            "success": True,
            "logs": [
                {
                    "id": log.id,
                    "model_type": log.model_type,
                    "model_category": log.model_category,
                    "timeframe": log.timeframe,
                    "status": log.status,
                    "training_started_at": log.training_started_at.isoformat() if log.training_started_at else None,
                    "training_completed_at": log.training_completed_at.isoformat() if log.training_completed_at else None,
                    "data_points_count": log.data_points_count,
                    "train_loss": log.train_loss,
                    "validation_loss": log.validation_loss,
                    "test_loss": log.test_loss,
                    "error_message": log.error_message
                }
                for log in logs
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting training logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-predictions")
async def get_recent_predictions(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent predictions"""
    try:
        predictions = prediction_tracking_service.get_recent_predictions(
            db=db,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )
        
        return {
            "success": True,
            "predictions": [
                {
                    "id": p.id,
                    "symbol": p.symbol,
                    "timeframe": p.timeframe,
                    "prediction_date": p.prediction_date.isoformat() if p.prediction_date else None,
                    "target_date": p.target_date.isoformat() if p.target_date else None,
                    "predicted_price": p.predicted_price,
                    "current_price": p.current_price,
                    "actual_price": p.actual_price,
                    "confidence": p.confidence,
                    "evaluated": p.evaluated,
                    "price_error_percent": p.price_error_percent,
                    "direction_correct": p.direction_correct
                }
                for p in predictions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting recent predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
