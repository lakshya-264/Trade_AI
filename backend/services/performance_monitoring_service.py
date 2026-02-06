"""
Performance Monitoring Service
Tracks and analyzes model performance metrics over time
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models.ml_models import MLModelPerformanceMetrics, ModelRegistry

logger = logging.getLogger(__name__)

class PerformanceMonitoringService:
    """Service for monitoring model performance"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_performance_metrics(self, model_id: str, model_version: str,
                                 evaluation_type: str, metrics: Dict[str, Any]) -> MLModelPerformanceMetrics:
        """Record performance metrics for a model"""
        try:
            # Create performance record
            perf_record = MLModelPerformanceMetrics(
                model_id=model_id,
                model_version=model_version,
                evaluation_type=evaluation_type,
                evaluated_at=datetime.utcnow(),
                # Standard ML metrics
                accuracy=metrics.get('accuracy'),
                precision=metrics.get('precision'),
                recall=metrics.get('recall'),
                f1_score=metrics.get('f1_score'),
                auc_roc=metrics.get('auc_roc'),
                # Trading-specific metrics
                total_return=metrics.get('total_return'),
                sharpe_ratio=metrics.get('sharpe_ratio'),
                max_drawdown=metrics.get('max_drawdown'),
                win_rate=metrics.get('win_rate'),
                profit_factor=metrics.get('profit_factor'),
                # Store any additional metrics
                custom_metrics={k: v for k, v in metrics.items() 
                              if k not in ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc',
                                       'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'profit_factor']}
            )
            
            self.db.add(perf_record)
            self.db.commit()
            self.db.refresh(perf_record)
            
            logger.info(f"Recorded performance metrics for model {model_id}")
            return perf_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record performance metrics for model {model_id}: {str(e)}")
            raise
    
    def get_performance_metrics(self, model_id: Optional[str] = None,
                               days: int = 30,
                               evaluation_type: Optional[str] = None) -> List[MLModelPerformanceMetrics]:
        """Get performance metrics with optional filters"""
        try:
            query = self.db.query(MLModelPerformanceMetrics)
            
            if model_id:
                query = query.filter(MLModelPerformanceMetrics.model_id == model_id)
            
            if evaluation_type:
                query = query.filter(MLModelPerformanceMetrics.evaluation_type == evaluation_type)
            
            # Filter by date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            query = query.filter(MLModelPerformanceMetrics.evaluated_at >= start_date)
            
            results = query.order_by(desc(MLModelPerformanceMetrics.evaluated_at)).all()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return []
    
    def get_performance_summary(self, model_id: str, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for a model"""
        try:
            metrics = self.get_performance_metrics(model_id, days)
            
            if not metrics:
                return {
                    "model_id": model_id,
                    "total_metrics": 0,
                    "avg_return": 0.0,
                    "avg_sharpe": 0.0,
                    "latest_metrics": None
                }
            
            # Calculate averages
            returns = [m.total_return for m in metrics if m.total_return is not None]
            sharpes = [m.sharpe_ratio for m in metrics if m.sharpe_ratio is not None]
            
            return {
                "model_id": model_id,
                "total_metrics": len(metrics),
                "avg_return": sum(returns) / len(returns) if returns else 0.0,
                "avg_sharpe": sum(sharpes) / len(sharpes) if sharpes else 0.0,
                "latest_metrics": metrics[0] if metrics else None,
                "trend": self._calculate_performance_trend(metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary for {model_id}: {str(e)}")
            return {}
    
    def get_model_performance_comparison(self, model_ids: List[str], days: int = 30) -> Dict[str, Dict]:
        """Compare performance across multiple models"""
        try:
            comparison = {}
            
            for model_id in model_ids:
                summary = self.get_performance_summary(model_id, days)
                comparison[model_id] = summary
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare model performance: {str(e)}")
            return {}
    
    def get_top_performing_models(self, metric: str = 'total_return', days: int = 30, limit: int = 10) -> List[Dict]:
        """Get top performing models by a specific metric"""
        try:
            # Get all metrics for the period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = self.db.query(MLModelPerformanceMetrics).filter(
                MLModelPerformanceMetrics.evaluated_at >= start_date
            )
            
            # Filter by metric
            if metric == 'total_return':
                query = query.filter(MLModelPerformanceMetrics.total_return.isnot(None))
            elif metric == 'sharpe_ratio':
                query = query.filter(MLModelPerformanceMetrics.sharpe_ratio.isnot(None))
            elif metric == 'accuracy':
                query = query.filter(MLModelPerformanceMetrics.accuracy.isnot(None))
            
            metrics = query.order_by(desc(getattr(MLModelPerformanceMetrics, metric))).limit(limit).all()
            
            results = []
            for m in metrics:
                results.append({
                    "model_id": m.model_id,
                    "model_version": m.model_version,
                    "evaluated_at": m.evaluated_at,
                    "evaluation_type": m.evaluation_type,
                    metric: getattr(m, metric)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get top performing models: {str(e)}")
            return []
    
    def detect_performance_degradation(self, model_id: str, threshold: float = 0.1, days: int = 7) -> bool:
        """Detect if a model's performance has degraded beyond threshold"""
        try:
            recent_metrics = self.get_performance_metrics(model_id, days)
            
            if len(recent_metrics) < 2:
                return False
            
            # Compare latest with oldest
            latest = recent_metrics[0]
            oldest = recent_metrics[-1]
            
            # Check total return degradation
            if latest.total_return and oldest.total_return:
                degradation = (oldest.total_return - latest.total_return) / abs(oldest.total_return)
                return degradation > threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to detect performance degradation for {model_id}: {str(e)}")
            return False
    
    def _calculate_performance_trend(self, metrics: List[MLModelPerformanceMetrics]) -> str:
        """Calculate performance trend from metrics"""
        try:
            if len(metrics) < 2:
                return "insufficient_data"
            
            # Simple trend calculation based on total_return
            returns = [m.total_return for m in metrics if m.total_return is not None]
            
            if len(returns) < 2:
                return "insufficient_data"
            
            # Calculate trend
            recent_avg = sum(returns[:len(returns)//2]) / (len(returns)//2)
            older_avg = sum(returns[len(returns)//2:]) / (len(returns) - len(returns)//2)
            
            if recent_avg > older_avg * 1.02:  # 2% improvement
                return "improving"
            elif recent_avg < older_avg * 0.98:  # 2% decline
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Failed to calculate performance trend: {str(e)}")
            return "unknown"
