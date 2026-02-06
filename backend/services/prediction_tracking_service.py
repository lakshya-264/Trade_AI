"""
Prediction Tracking Service
Tracks price predictions and calculates accuracy metrics
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from core.prediction_tracking_models import (
    PricePredictionRecord,
    ModelPerformanceMetrics,
    ModelTrainingLog
)
from core.data_service import data_service

logger = logging.getLogger(__name__)

class PredictionTrackingService:
    """Service for tracking predictions and calculating accuracy"""
    
    def __init__(self):
        pass
    
    async def record_prediction(
        self,
        db: Session,
        symbol: str,
        timeframe: str,
        predicted_price: float,
        current_price: float,
        predicted_change_percent: float,
        confidence: float,
        price_range: Dict[str, float],
        model_type: str,
        model_contributions: Optional[Dict] = None,
        analysis_data_hash: Optional[str] = None
    ) -> PricePredictionRecord:
        """
        Record a new price prediction
        
        Args:
            db: Database session
            symbol: Stock symbol
            timeframe: Prediction timeframe (1W, 1M, etc.)
            predicted_price: Predicted price
            current_price: Current price at prediction time
            predicted_change_percent: Predicted percentage change
            confidence: Prediction confidence (0-100)
            price_range: Price range dictionary with low_68, high_68, low_95, high_95
            model_type: Type of model used
            model_contributions: Model-specific contributions
            analysis_data_hash: Hash of analysis data used
        
        Returns:
            Created PricePredictionRecord
        """
        try:
            # Calculate target date based on timeframe
            days_map = {
                "1W": 5,
                "1M": 21,
                "2M": 42,
                "3M": 63,
                "6M": 126,
                "1Y": 252,
                "2Y": 504
            }
            days = days_map.get(timeframe, 21)
            target_date = date.today() + timedelta(days=days)
            
            prediction_record = PricePredictionRecord(
                symbol=symbol.upper(),
                timeframe=timeframe,
                prediction_date=datetime.utcnow(),
                target_date=target_date,
                predicted_price=predicted_price,
                current_price=current_price,
                predicted_change_percent=predicted_change_percent,
                confidence=confidence,
                price_range_low_68=price_range.get("low_68"),
                price_range_high_68=price_range.get("high_68"),
                price_range_low_95=price_range.get("low_95"),
                price_range_high_95=price_range.get("high_95"),
                model_type=model_type,
                model_contributions=model_contributions or {},
                analysis_data_hash=analysis_data_hash,
                evaluated=False
            )
            
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)
            
            logger.info(f"Recorded prediction: {symbol} {timeframe} -> {predicted_price:.2f} (target: {target_date})")
            return prediction_record
            
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
            db.rollback()
            raise
    
    async def evaluate_predictions(
        self,
        db: Session,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        days_overdue: int = 0
    ) -> List[PricePredictionRecord]:
        """
        Evaluate predictions that have reached their target date
        
        Args:
            db: Database session
            symbol: Optional symbol filter
            timeframe: Optional timeframe filter
            days_overdue: Evaluate predictions that are at least this many days past target date
        
        Returns:
            List of evaluated prediction records
        """
        try:
            # Find unevaluated predictions that have reached their target date
            cutoff_date = date.today() - timedelta(days=days_overdue)
            
            query = db.query(PricePredictionRecord).filter(
                and_(
                    PricePredictionRecord.evaluated == False,
                    PricePredictionRecord.target_date <= cutoff_date
                )
            )
            
            if symbol:
                query = query.filter(PricePredictionRecord.symbol == symbol.upper())
            if timeframe:
                query = query.filter(PricePredictionRecord.timeframe == timeframe)
            
            predictions = query.all()
            
            evaluated_records = []
            
            for pred in predictions:
                try:
                    # Fetch actual price for the target date
                    # Note: We'll use the closest available price
                    actual_price = await self._get_actual_price(
                        pred.symbol,
                        pred.target_date
                    )
                    
                    if actual_price is None:
                        logger.warning(f"Could not get actual price for {pred.symbol} on {pred.target_date}")
                        continue
                    
                    # Calculate metrics
                    price_error = abs(actual_price - pred.predicted_price)
                    price_error_percent = (price_error / pred.current_price) * 100 if pred.current_price > 0 else 0
                    
                    actual_change_percent = ((actual_price - pred.current_price) / pred.current_price) * 100 if pred.current_price > 0 else 0
                    
                    # Direction correctness
                    predicted_direction = 1 if pred.predicted_change_percent > 0 else -1
                    actual_direction = 1 if actual_change_percent > 0 else -1
                    direction_correct = predicted_direction == actual_direction
                    
                    # Range checks
                    within_range_68 = (
                        pred.price_range_low_68 is not None and
                        pred.price_range_high_68 is not None and
                        pred.price_range_low_68 <= actual_price <= pred.price_range_high_68
                    )
                    within_range_95 = (
                        pred.price_range_low_95 is not None and
                        pred.price_range_high_95 is not None and
                        pred.price_range_low_95 <= actual_price <= pred.price_range_high_95
                    )
                    
                    # Update record
                    pred.actual_price = actual_price
                    pred.actual_change_percent = actual_change_percent
                    pred.evaluated = True
                    pred.evaluated_at = datetime.utcnow()
                    pred.price_error = price_error
                    pred.price_error_percent = price_error_percent
                    pred.direction_correct = direction_correct
                    pred.within_range_68 = within_range_68
                    pred.within_range_95 = within_range_95
                    
                    evaluated_records.append(pred)
                    
                except Exception as e:
                    logger.error(f"Error evaluating prediction {pred.id}: {e}")
                    continue
            
            db.commit()
            
            logger.info(f"Evaluated {len(evaluated_records)} predictions")
            return evaluated_records
            
        except Exception as e:
            logger.error(f"Error evaluating predictions: {e}")
            db.rollback()
            raise
    
    async def _get_actual_price(self, symbol: str, target_date: date) -> Optional[float]:
        """Get actual price for a symbol on a specific date"""
        try:
            # Try to get historical data for the target date
            from services.data_fetcher import fetch_historical_data
            
            # Fetch data around the target date
            candles = await fetch_historical_data(symbol, "1d", days=30)
            if not candles:
                return None
            
            # Find the closest candle to target_date
            target_timestamp = datetime.combine(target_date, datetime.min.time()).timestamp()
            closest_candle = None
            min_diff = float('inf')
            
            for candle in candles:
                candle_time = candle.get('time', 0)
                if isinstance(candle_time, str):
                    try:
                        candle_time = datetime.fromisoformat(candle_time.replace('Z', '+00:00')).timestamp()
                    except:
                        continue
                
                diff = abs(candle_time - target_timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest_candle = candle
            
            if closest_candle and min_diff < 86400 * 2:  # Within 2 days
                return float(closest_candle.get('close', 0))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting actual price for {symbol} on {target_date}: {e}")
            return None
    
    async def calculate_performance_metrics(
        self,
        db: Session,
        model_type: str,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ModelPerformanceMetrics:
        """
        Calculate aggregated performance metrics for a model type and timeframe
        
        Args:
            db: Database session
            model_type: Type of model
            timeframe: Prediction timeframe
            start_date: Start of evaluation period
            end_date: End of evaluation period
        
        Returns:
            ModelPerformanceMetrics object
        """
        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=90)
            if end_date is None:
                end_date = date.today()
            
            # Query evaluated predictions
            predictions = db.query(PricePredictionRecord).filter(
                and_(
                    PricePredictionRecord.model_type == model_type,
                    PricePredictionRecord.timeframe == timeframe,
                    PricePredictionRecord.evaluated == True,
                    PricePredictionRecord.prediction_date >= datetime.combine(start_date, datetime.min.time()),
                    PricePredictionRecord.prediction_date <= datetime.combine(end_date, datetime.max.time())
                )
            ).all()
            
            if not predictions:
                return None
            
            # Calculate metrics
            total_predictions = len(predictions)
            evaluated_predictions = sum(1 for p in predictions if p.evaluated)
            
            if evaluated_predictions == 0:
                return None
            
            # Price errors
            errors = [p.price_error for p in predictions if p.price_error is not None]
            error_percents = [p.price_error_percent for p in predictions if p.price_error_percent is not None]
            
            mae = np.mean(errors) if errors else None
            mape = np.mean(error_percents) if error_percents else None
            rmse = np.sqrt(np.mean([e**2 for e in errors])) if errors else None
            
            # Direction accuracy
            direction_correct = sum(1 for p in predictions if p.direction_correct)
            direction_accuracy = (direction_correct / evaluated_predictions) * 100 if evaluated_predictions > 0 else None
            
            # Range accuracy
            range_68_correct = sum(1 for p in predictions if p.within_range_68)
            range_68_accuracy = (range_68_correct / evaluated_predictions) * 100 if evaluated_predictions > 0 else None
            
            range_95_correct = sum(1 for p in predictions if p.within_range_95)
            range_95_accuracy = (range_95_correct / evaluated_predictions) * 100 if evaluated_predictions > 0 else None
            
            # Confidence metrics
            confidences = [p.confidence for p in predictions if p.confidence is not None]
            avg_confidence = np.mean(confidences) if confidences else None
            
            # High confidence accuracy (confidence > 70%)
            high_conf_predictions = [p for p in predictions if p.confidence and p.confidence > 70]
            high_conf_correct = sum(1 for p in high_conf_predictions if p.direction_correct)
            high_confidence_accuracy = (high_conf_correct / len(high_conf_predictions)) * 100 if high_conf_predictions else None
            
            # Error percentiles
            error_percentiles = None
            if error_percents:
                error_percentiles = {
                    "p10": np.percentile(error_percents, 10),
                    "p25": np.percentile(error_percents, 25),
                    "p50": np.percentile(error_percents, 50),
                    "p75": np.percentile(error_percents, 75),
                    "p90": np.percentile(error_percents, 90),
                    "p95": np.percentile(error_percents, 95),
                    "p99": np.percentile(error_percents, 99)
                }
            
            # Create or update metrics record
            metrics = db.query(ModelPerformanceMetrics).filter(
                and_(
                    ModelPerformanceMetrics.model_type == model_type,
                    ModelPerformanceMetrics.timeframe == timeframe,
                    ModelPerformanceMetrics.evaluation_period_start == start_date,
                    ModelPerformanceMetrics.evaluation_period_end == end_date
                )
            ).first()
            
            if not metrics:
                metrics = ModelPerformanceMetrics(
                    model_type=model_type,
                    timeframe=timeframe,
                    evaluation_period_start=start_date,
                    evaluation_period_end=end_date
                )
                db.add(metrics)
            
            # Update metrics
            metrics.total_predictions = total_predictions
            metrics.evaluated_predictions = evaluated_predictions
            metrics.mean_absolute_error = mae
            metrics.mean_absolute_percentage_error = mape
            metrics.root_mean_squared_error = rmse
            metrics.direction_accuracy = direction_accuracy
            metrics.range_68_accuracy = range_68_accuracy
            metrics.range_95_accuracy = range_95_accuracy
            metrics.avg_confidence = avg_confidence
            metrics.high_confidence_accuracy = high_confidence_accuracy
            metrics.error_percentiles = error_percentiles
            
            db.commit()
            db.refresh(metrics)
            
            logger.info(f"Calculated performance metrics for {model_type} {timeframe}: MAE={mae:.2f}, Direction Accuracy={direction_accuracy:.1f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            db.rollback()
            raise
    
    def get_recent_predictions(
        self,
        db: Session,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 100
    ) -> List[PricePredictionRecord]:
        """Get recent predictions"""
        query = db.query(PricePredictionRecord)
        
        if symbol:
            query = query.filter(PricePredictionRecord.symbol == symbol.upper())
        if timeframe:
            query = query.filter(PricePredictionRecord.timeframe == timeframe)
        
        return query.order_by(desc(PricePredictionRecord.prediction_date)).limit(limit).all()
    
    def get_model_performance_summary(
        self,
        db: Session,
        model_type: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> List[ModelPerformanceMetrics]:
        """Get performance summary for models"""
        query = db.query(ModelPerformanceMetrics)
        
        if model_type:
            query = query.filter(ModelPerformanceMetrics.model_type == model_type)
        if timeframe:
            query = query.filter(ModelPerformanceMetrics.timeframe == timeframe)
        
        return query.order_by(desc(ModelPerformanceMetrics.evaluation_period_end)).limit(10).all()

# Create singleton instance
prediction_tracking_service = PredictionTrackingService()
