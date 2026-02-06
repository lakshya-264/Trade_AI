"""
A/B Testing Service
Framework for comparing old vs new training approaches
"""

import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from dataclasses import dataclass
import logging

from models.ml_models import ABTestExperiment, ModelPerformanceMetrics, ModelRegistry
from core.ml_config import get_ml_config
from services.model_registry_service import ModelRegistryService

logger = logging.getLogger(__name__)

@dataclass
class ExperimentResult:
    """Results of an A/B test experiment"""
    control_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    statistical_significance: bool
    confidence_interval: List[float]
    effect_size: float
    p_value: float
    winner: str
    recommendation: str
    decision_reason: str

class ABTestingService:
    """Service for managing A/B testing experiments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_ml_config()
        self.model_registry = ModelRegistryService(db)
    
    def create_experiment(self, experiment_data: Dict[str, Any]) -> ABTestExperiment:
        """Create a new A/B test experiment"""
        try:
            # Validate models exist
            control_model = self.model_registry.get_model(experiment_data['control_model_id'])
            treatment_model = self.model_registry.get_model(experiment_data['treatment_model_id'])
            
            if not control_model or not treatment_model:
                raise ValueError("One or both models not found in registry")
            
            # Validate traffic split
            traffic_split = experiment_data.get('traffic_split_control', 0.5)
            if not (0 <= traffic_split <= 1):
                raise ValueError("Traffic split must be between 0 and 1")
            
            experiment = ABTestExperiment(
                experiment_id=experiment_data['experiment_id'],
                name=experiment_data['name'],
                description=experiment_data.get('description'),
                control_model_id=experiment_data['control_model_id'],
                control_model_version=experiment_data['control_model_version'],
                treatment_model_id=experiment_data['treatment_model_id'],
                treatment_model_version=experiment_data['treatment_model_version'],
                primary_metric=experiment_data['primary_metric'],
                traffic_split_control=traffic_split,
                traffic_split_treatment=1.0 - traffic_split,
                significance_level=experiment_data.get('significance_level', 0.05),
                minimum_detectable_effect=experiment_data.get('minimum_detectable_effect'),
                created_by=experiment_data.get('created_by')
            )
            
            self.db.add(experiment)
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Created A/B test experiment: {experiment.experiment_id}")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create A/B test experiment: {str(e)}")
            raise
    
    def start_experiment(self, experiment_id: str, duration_days: int) -> bool:
        """Start an A/B test experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.experiment_id == experiment_id
            ).first()
            
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            if experiment.status != "setup":
                raise ValueError(f"Experiment {experiment_id} is not in setup status")
            
            # Validate duration
            max_duration = self.config.ab_testing.experiments.get('default_duration_days', 14)
            if duration_days > max_duration * 2:  # Allow up to 2x default
                raise ValueError(f"Duration too long (max: {max_duration * 2} days)")
            
            # Check if we have enough concurrent experiments
            max_concurrent = self.config.ab_testing.experiments.get('max_concurrent_experiments', 5)
            running_count = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "running"
            ).count()
            
            if running_count >= max_concurrent:
                raise ValueError(f"Maximum concurrent experiments ({max_concurrent}) reached")
            
            # Update experiment
            experiment.status = "running"
            experiment.started_at = datetime.utcnow()
            experiment.duration_days = duration_days
            experiment.ended_at = experiment.started_at + timedelta(days=duration_days)
            
            self.db.commit()
            
            logger.info(f"Started A/B test experiment: {experiment_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start A/B test experiment {experiment_id}: {str(e)}")
            return False
    
    def stop_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Stop an A/B test experiment and analyze results"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.experiment_id == experiment_id
            ).first()
            
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            if experiment.status != "running":
                raise ValueError(f"Experiment {experiment_id} is not running")
            
            # Collect performance data for both models
            control_data = self._collect_model_performance(
                experiment.control_model_id,
                experiment.control_model_version,
                experiment.started_at,
                experiment.ended_at
            )
            
            treatment_data = self._collect_model_performance(
                experiment.treatment_model_id,
                experiment.treatment_model_version,
                experiment.started_at,
                experiment.ended_at
            )
            
            # Analyze results
            results = self._analyze_experiment_results(
                experiment, control_data, treatment_data
            )
            
            # Update experiment with results
            experiment.status = "completed"
            experiment.ended_at = datetime.utcnow()
            experiment.control_metrics = results.control_metrics
            experiment.treatment_metrics = results.treatment_metrics
            experiment.statistical_significance = results.statistical_significance
            experiment.confidence_interval = results.confidence_interval
            experiment.effect_size = results.effect_size
            experiment.p_value = results.p_value
            experiment.winner = results.winner
            experiment.decision_reason = results.decision_reason
            experiment.decided_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Completed A/B test experiment: {experiment_id}")
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to stop A/B test experiment {experiment_id}: {str(e)}")
            return None
    
    def _collect_model_performance(self, model_id: str, model_version: str,
                                 start_date: datetime, end_date: datetime) -> List[ModelPerformanceMetrics]:
        """Collect performance metrics for a model during experiment period"""
        try:
            metrics = self.db.query(ModelPerformanceMetrics).filter(
                ModelPerformanceMetrics.model_id == model_id,
                ModelPerformanceMetrics.model_version == model_version,
                ModelPerformanceMetrics.evaluated_at >= start_date,
                ModelPerformanceMetrics.evaluated_at <= end_date,
                ModelPerformanceMetrics.evaluation_type == "live_trading"
            ).all()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect performance data for {model_id}: {str(e)}")
            return []
    
    def _analyze_experiment_results(self, experiment: ABTestExperiment,
                                   control_data: List[ModelPerformanceMetrics],
                                   treatment_data: List[ModelPerformanceMetrics]) -> ExperimentResult:
        """Analyze A/B test results using statistical methods"""
        
        # Aggregate metrics
        control_metrics = self._aggregate_metrics(control_data)
        treatment_metrics = self._aggregate_metrics(treatment_data)
        
        # Get primary metric values
        primary_metric = experiment.primary_metric
        control_values = [getattr(m, primary_metric, 0) for m in control_data if getattr(m, primary_metric, None) is not None]
        treatment_values = [getattr(m, primary_metric, 0) for m in treatment_data if getattr(m, primary_metric, None) is not None]
        
        if not control_values or not treatment_values:
            # Fallback to aggregated metrics if no time series data
            control_val = control_metrics.get(primary_metric, 0)
            treatment_val = treatment_metrics.get(primary_metric, 0)
            control_values = [control_val]
            treatment_values = [treatment_val]
        
        # Perform statistical test
        if len(control_values) > 1 and len(treatment_values) > 1:
            # Use t-test for multiple samples
            t_stat, p_value = stats.ttest_ind(treatment_values, control_values)
        else:
            # Use simple comparison for single values
            t_stat = treatment_values[0] - control_values[0]
            p_value = 0.05  # Default p-value for single comparison
        
        # Calculate effect size (Cohen's d)
        if len(control_values) > 1 and len(treatment_values) > 1:
            pooled_std = np.sqrt(((len(control_values) - 1) * np.var(control_values, ddof=1) + 
                                 (len(treatment_values) - 1) * np.var(treatment_values, ddof=1)) / 
                                (len(control_values) + len(treatment_values) - 2))
            effect_size = (np.mean(treatment_values) - np.mean(control_values)) / pooled_std if pooled_std > 0 else 0
        else:
            baseline = np.mean(control_values) if control_values else 1
            effect_size = (np.mean(treatment_values) - baseline) / baseline if baseline > 0 else 0
        
        # Calculate confidence interval
        mean_diff = np.mean(treatment_values) - np.mean(control_values)
        if len(control_values) > 1 and len(treatment_values) > 1:
            se = np.sqrt(np.var(control_values, ddof=1) / len(control_values) + 
                        np.var(treatment_values, ddof=1) / len(treatment_values))
            ci_lower = mean_diff - 1.96 * se
            ci_upper = mean_diff + 1.96 * se
        else:
            ci_lower = mean_diff * 0.9
            ci_upper = mean_diff * 1.1
        
        # Determine winner
        significance_level = experiment.significance_level
        is_significant = p_value < significance_level
        
        if is_significant:
            if mean_diff > 0:
                winner = "treatment"
                recommendation = "Deploy the treatment model"
                decision_reason = f"Treatment model shows statistically significant improvement in {primary_metric}"
            else:
                winner = "control"
                recommendation = "Keep the control model"
                decision_reason = f"Control model outperforms treatment in {primary_metric}"
        else:
            winner = "inconclusive"
            recommendation = "Continue with control model or run longer experiment"
            decision_reason = f"No statistically significant difference between models"
        
        return ExperimentResult(
            control_metrics=control_metrics,
            treatment_metrics=treatment_metrics,
            statistical_significance=is_significant,
            confidence_interval=[ci_lower, ci_upper],
            effect_size=effect_size,
            p_value=p_value,
            winner=winner,
            recommendation=recommendation,
            decision_reason=decision_reason
        )
    
    def _aggregate_metrics(self, metrics_data: List[ModelPerformanceMetrics]) -> Dict[str, float]:
        """Aggregate performance metrics"""
        if not metrics_data:
            return {}
        
        aggregated = {}
        
        # Get all metric attributes
        metric_fields = [
            'total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown',
            'win_rate', 'profit_factor', 'avg_trade_return', 'volatility',
            'prediction_accuracy', 'precision', 'recall', 'f1_score', 'roc_auc',
            'var_95', 'cvar_95', 'beta', 'alpha'
        ]
        
        for field in metric_fields:
            values = [getattr(m, field, None) for m in metrics_data if getattr(m, field, None) is not None]
            if values:
                # Use mean for aggregation
                aggregated[field] = np.mean(values)
        
        # Add count
        aggregated['sample_size'] = len(metrics_data)
        
        return aggregated
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of an experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.experiment_id == experiment_id
            ).first()
            
            if not experiment:
                return None
            
            # Calculate progress if running
            progress = None
            if experiment.status == "running" and experiment.started_at and experiment.ended_at:
                total_time = experiment.ended_at - experiment.started_at
                elapsed = datetime.utcnow() - experiment.started_at
                progress = min(100, (elapsed.total_seconds() / total_time.total_seconds()) * 100)
            
            return {
                'experiment_id': experiment.experiment_id,
                'name': experiment.name,
                'status': experiment.status,
                'progress': progress,
                'started_at': experiment.started_at,
                'ended_at': experiment.ended_at,
                'duration_days': experiment.duration_days,
                'control_model_id': experiment.control_model_id,
                'treatment_model_id': experiment.treatment_model_id,
                'primary_metric': experiment.primary_metric,
                'winner': experiment.winner,
                'statistical_significance': experiment.statistical_significance,
                'effect_size': experiment.effect_size,
                'p_value': experiment.p_value,
                'decision_reason': experiment.decision_reason
            }
            
        except Exception as e:
            logger.error(f"Failed to get experiment summary for {experiment_id}: {str(e)}")
            return None
    
    def list_experiments(self, status: Optional[str] = None,
                        limit: int = 50, offset: int = 0) -> List[ABTestExperiment]:
        """List A/B test experiments"""
        query = self.db.query(ABTestExperiment)
        
        if status:
            query = query.filter(ABTestExperiment.status == status)
        
        return query.order_by(ABTestExperiment.started_at.desc()).offset(offset).limit(limit).all()
    
    def get_running_experiments(self) -> List[ABTestExperiment]:
        """Get all currently running experiments"""
        return self.db.query(ABTestExperiment).filter(
            ABTestExperiment.status == "running"
        ).all()
    
    def check_experiment_completion(self) -> List[str]:
        """Check if any running experiments should be completed"""
        completed_experiments = []
        
        try:
            running_experiments = self.get_running_experiments()
            
            for experiment in running_experiments:
                if experiment.ended_at and datetime.utcnow() >= experiment.ended_at:
                    # Auto-complete experiment
                    result = self.stop_experiment(experiment.experiment_id)
                    if result:
                        completed_experiments.append(experiment.experiment_id)
                        logger.info(f"Auto-completed experiment: {experiment.experiment_id}")
            
        except Exception as e:
            logger.error(f"Error checking experiment completion: {str(e)}")
        
        return completed_experiments
    
    def get_experiment_statistics(self) -> Dict[str, Any]:
        """Get overall A/B testing statistics"""
        try:
            total_experiments = self.db.query(ABTestExperiment).count()
            running_experiments = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "running"
            ).count()
            completed_experiments = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "completed"
            ).count()
            
            # Success rate (treatment wins)
            treatment_wins = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "completed",
                ABTestExperiment.winner == "treatment"
            ).count()
            
            success_rate = (treatment_wins / completed_experiments * 100) if completed_experiments > 0 else 0
            
            # Average effect size
            completed_with_effect = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "completed",
                ABTestExperiment.effect_size.isnot(None)
            ).all()
            
            avg_effect_size = np.mean([exp.effect_size for exp in completed_with_effect]) if completed_with_effect else 0
            
            return {
                'total_experiments': total_experiments,
                'running_experiments': running_experiments,
                'completed_experiments': completed_experiments,
                'success_rate': success_rate,
                'average_effect_size': avg_effect_size,
                'treatment_wins': treatment_wins
            }
            
        except Exception as e:
            logger.error(f"Failed to get experiment statistics: {str(e)}")
            return {}
    
    def validate_experiment_setup(self, experiment_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate experiment setup before creation"""
        errors = []
        
        # Check required fields
        required_fields = ['experiment_id', 'name', 'control_model_id', 
                          'treatment_model_id', 'primary_metric']
        
        for field in required_fields:
            if field not in experiment_data or not experiment_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check models exist
        if 'control_model_id' in experiment_data:
            control_model = self.model_registry.get_model(experiment_data['control_model_id'])
            if not control_model:
                errors.append(f"Control model not found: {experiment_data['control_model_id']}")
        
        if 'treatment_model_id' in experiment_data:
            treatment_model = self.model_registry.get_model(experiment_data['treatment_model_id'])
            if not treatment_model:
                errors.append(f"Treatment model not found: {experiment_data['treatment_model_id']}")
        
        # Validate traffic split
        if 'traffic_split_control' in experiment_data:
            split = experiment_data['traffic_split_control']
            if not isinstance(split, (int, float)) or not (0 <= split <= 1):
                errors.append("Traffic split must be a number between 0 and 1")
        
        # Validate significance level
        if 'significance_level' in experiment_data:
            sig_level = experiment_data['significance_level']
            if not isinstance(sig_level, (int, float)) or not (0 < sig_level < 1):
                errors.append("Significance level must be between 0 and 1")
        
        return len(errors) == 0, errors
