"""
Drift Detection Service
Monitors model performance and detects concept/data drift
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.ml_models import ModelDriftHistory, ModelRegistry

logger = logging.getLogger(__name__)

class DriftDetectionService:
    """Service for detecting and managing model drift"""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_drift_threshold = 0.7
    
    def detect_drift(self, model_id: str, model_version: str, 
                    current_metrics: Dict[str, Any], 
                    baseline_metrics: Dict[str, Any]) -> ModelDriftHistory:
        """Detect drift between current and baseline metrics"""
        try:
            # Calculate drift score (simplified)
            drift_score = self._calculate_drift_score(current_metrics, baseline_metrics)
            
            # Determine drift type and severity
            drift_type = self._determine_drift_type(current_metrics, baseline_metrics)
            severity = self._determine_severity(drift_score)
            
            # Create drift record
            drift_record = ModelDriftHistory(
                model_id=model_id,
                model_version=model_version,
                drift_type=drift_type,
                drift_score=drift_score,
                drift_threshold=self.default_drift_threshold,
                severity=severity,
                baseline_metrics=baseline_metrics,
                current_metrics=current_metrics,
                status="active",
                recommended_action=self._get_recommended_action(severity, drift_type)
            )
            
            self.db.add(drift_record)
            self.db.commit()
            self.db.refresh(drift_record)
            
            logger.info(f"Drift detected for model {model_id}: score={drift_score:.3f}, type={drift_type}")
            return drift_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to detect drift for model {model_id}: {str(e)}")
            raise
    
    def get_drift_history(self, model_id: Optional[str] = None, 
                          status: Optional[str] = None,
                          days: int = 30) -> List[ModelDriftHistory]:
        """Get drift history with optional filters"""
        try:
            query = self.db.query(ModelDriftHistory)
            
            if model_id:
                query = query.filter(ModelDriftHistory.model_id == model_id)
            
            if status:
                query = query.filter(ModelDriftHistory.status == status)
            
            # Filter by date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            query = query.filter(ModelDriftHistory.detected_at >= start_date)
            
            results = query.order_by(desc(ModelDriftHistory.detected_at)).all()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get drift history: {str(e)}")
            return []
    
    def resolve_drift(self, drift_id: int, resolution_notes: Optional[str] = None) -> bool:
        """Mark a drift alert as resolved"""
        try:
            drift = self.db.query(ModelDriftHistory).filter(ModelDriftHistory.id == drift_id).first()
            if not drift:
                return False
            
            drift.status = "resolved"
            if resolution_notes:
                drift.description = (drift.description or "") + f"\n\nResolution: {resolution_notes}"
            
            self.db.commit()
            logger.info(f"Resolved drift alert {drift_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to resolve drift alert {drift_id}: {str(e)}")
            return False
    
    def get_active_drift_alerts(self, model_id: Optional[str] = None) -> List[ModelDriftHistory]:
        """Get all active drift alerts"""
        return self.get_drift_history(model_id=model_id, status="active")
    
    def _calculate_drift_score(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> float:
        """Calculate drift score between current and baseline metrics"""
        try:
            # Simplified drift calculation
            score = 0.0
            total_comparisons = 0
            
            # Compare common metrics
            for key in ['accuracy', 'precision', 'recall', 'f1_score', 'total_return', 'sharpe_ratio']:
                if key in current and key in baseline:
                    current_val = float(current[key])
                    baseline_val = float(baseline[key])
                    
                    if baseline_val != 0:
                        # Calculate relative change
                        change = abs(current_val - baseline_val) / abs(baseline_val)
                        score += min(change, 1.0)  # Cap at 1.0
                        total_comparisons += 1
            
            return score / max(total_comparisons, 1)
            
        except Exception as e:
            logger.error(f"Failed to calculate drift score: {str(e)}")
            return 0.0
    
    def _determine_drift_type(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
        """Determine the type of drift"""
        # Simplified logic - in real implementation, this would be more sophisticated
        if 'feature_distribution' in current or 'feature_distribution' in baseline:
            return "data_drift"
        elif 'target_distribution' in current or 'target_distribution' in baseline:
            return "concept_drift"
        else:
            return "performance_drift"
    
    def _determine_severity(self, drift_score: float) -> str:
        """Determine severity based on drift score"""
        if drift_score >= 0.8:
            return "high"
        elif drift_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _get_recommended_action(self, severity: str, drift_type: str) -> str:
        """Get recommended action based on severity and drift type"""
        if severity == "high":
            if drift_type == "concept_drift":
                return "Retrain model with recent data"
            elif drift_type == "data_drift":
                return "Update data preprocessing pipeline"
            else:
                return "Investigate model performance degradation"
        elif severity == "medium":
            return "Monitor closely and consider retraining"
        else:
            return "Continue monitoring"
