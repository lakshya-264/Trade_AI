"""
ML Service
Main service for ML operations including training, drift detection, and A/B testing
"""

import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.ml_models import (
    TrainingJob, ModelDriftHistory, MLModelPerformanceMetrics, 
    ModelRegistry, ABTestExperiment
)
from services.model_registry_service import ModelRegistryService
from services.drift_detection_service import DriftDetectionService
from services.performance_monitoring_service import PerformanceMonitoringService
from core.ml_config import get_ml_config
from schemas.ml_schemas import TrainingJobCreate, ABTestExperimentCreate

logger = logging.getLogger(__name__)

class MLService:
    """Main ML service orchestrating all ML operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_ml_config()
        self.model_registry = ModelRegistryService(db)
        self.drift_service = DriftDetectionService(db)
        self.performance_service = PerformanceMonitoringService(db)
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard overview metrics"""
        try:
            # Count training jobs by status
            total_jobs = self.db.query(TrainingJob).count()
            running_jobs = self.db.query(TrainingJob).filter(TrainingJob.status == "running").count()
            completed_jobs = self.db.query(TrainingJob).filter(TrainingJob.status == "completed").count()
            failed_jobs = self.db.query(TrainingJob).filter(TrainingJob.status == "failed").count()
            
            # Count models
            total_models = self.db.query(ModelRegistry).count()
            deployed_models = self.db.query(ModelRegistry).filter(ModelRegistry.is_deployed == True).count()
            
            # Count drift alerts
            recent_drift_alerts = self.db.query(ModelDriftHistory).filter(
                ModelDriftHistory.detected_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Count A/B tests
            running_experiments = self.db.query(ABTestExperiment).filter(ABTestExperiment.status == "running").count()
            
            return {
                "training_jobs": {
                    "total": total_jobs,
                    "running": running_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs
                },
                "models": {
                    "total_models": total_models,
                    "deployed_models": deployed_models,
                    "model_types": {},
                    "deployment_environments": {},
                    "storage_usage_mb": 0
                },
                "drift_detection": {
                    "recent_alerts": recent_drift_alerts
                },
                "ab_testing": {
                    "running_experiments": running_experiments
                },
                "system_health": "healthy"
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            return {}
    
    def list_training_jobs(self, status: Optional[str] = None, limit: int = 10) -> List[TrainingJob]:
        """List training jobs with optional status filter"""
        try:
            query = self.db.query(TrainingJob)
            if status:
                query = query.filter(TrainingJob.status == status)
            return query.order_by(desc(TrainingJob.started_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to list training jobs: {str(e)}")
            return []
    
    def list_ab_test_experiments(self, status: Optional[str] = None, limit: int = 20) -> List[ABTestExperiment]:
        """List A/B test experiments with optional status filter"""
        try:
            query = self.db.query(ABTestExperiment)
            if status:
                query = query.filter(ABTestExperiment.status == status)
            return query.order_by(desc(ABTestExperiment.started_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to list A/B test experiments: {str(e)}")
            return []
    
    def create_training_job(self, job_id: str, model_id: str, model_version: str,
                           job_type: str, hyperparameters: Optional[Dict[str, Any]] = None,
                           validation_split: float = 0.2, created_by: Optional[str] = None) -> TrainingJob:
        """Create a new training job"""
        try:
            training_job = TrainingJob(
                job_id=job_id,
                model_id=model_id,
                model_version=model_version,
                job_type=job_type,
                hyperparameters=hyperparameters or {},
                validation_split=validation_split,
                created_by=created_by,
                status="pending"
            )
            
            self.db.add(training_job)
            self.db.commit()
            self.db.refresh(training_job)
            
            logger.info(f"Created training job: {job_id}")
            return training_job
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create training job {job_id}: {str(e)}")
            raise
    
    async def run_training_job(self, job_id: str) -> bool:
        """Execute a training job"""
        try:
            # Get training job
            job = self.get_training_job(job_id)
            if not job:
                raise ValueError(f"Training job {job_id} not found")
            
            # Update status to running
            job.status = "running"
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Starting training job: {job_id}")
            
            # Simulate training process (replace with actual training logic)
            success = await self._execute_training(job)
            
            if success:
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                
                # Save training metrics
                job.training_metrics = {
                    "final_loss": 0.15,
                    "accuracy": 0.85,
                    "epochs_trained": 50
                }
                job.validation_metrics = {
                    "val_loss": 0.18,
                    "val_accuracy": 0.82
                }
                
                # Calculate training duration
                if job.started_at:
                    duration = job.completed_at - job.started_at
                    job.training_duration_seconds = int(duration.total_seconds())
                
                logger.info(f"Training job {job_id} completed successfully")
                
            else:
                job.status = "failed"
                job.error_message = "Training failed due to convergence issues"
                logger.error(f"Training job {job_id} failed")
            
            self.db.commit()
            return success
            
        except Exception as e:
            # Update job status to failed
            job = self.get_training_job(job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                self.db.commit()
            
            logger.error(f"Training job {job_id} failed: {str(e)}")
            return False
    
    async def _execute_training(self, job: TrainingJob) -> bool:
        """Execute the actual training process"""
        try:
            # Simulate training with different logic based on job type
            if job.job_type == "initial_training":
                return await self._initial_training(job)
            elif job.job_type == "retraining":
                return await self._retraining(job)
            elif job.job_type == "hyperparameter_tuning":
                return await self._hyperparameter_tuning(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
                
        except Exception as e:
            logger.error(f"Training execution failed: {str(e)}")
            return False
    
    async def _initial_training(self, job: TrainingJob) -> bool:
        """Perform initial model training"""
        logger.info(f"Performing initial training for model {job.model_id}")
        
        # Simulate training time
        await asyncio.sleep(2)
        
        # In real implementation, this would:
        # 1. Load training data
        # 2. Preprocess features
        # 3. Initialize model
        # 4. Train with specified hyperparameters
        # 5. Validate and save model
        
        return True
    
    async def _retraining(self, job: TrainingJob) -> bool:
        """Perform model retraining"""
        logger.info(f"Performing retraining for model {job.model_id}")
        
        # Simulate training time
        await asyncio.sleep(1.5)
        
        # In real implementation, this would:
        # 1. Load existing model
        # 2. Get new training data
        # 3. Retrain with new data
        # 4. Compare performance with old model
        # 5. Save if improved
        
        return True
    
    async def _hyperparameter_tuning(self, job: TrainingJob) -> bool:
        """Perform hyperparameter optimization"""
        logger.info(f"Performing hyperparameter tuning for model {job.model_id}")
        
        # Get optimization config
        opt_config = self.config.training.hyperparameter_optimization
        n_trials = opt_config.get("n_trials", 50)
        
        # Simulate optimization trials
        for trial in range(min(n_trials, 5)):  # Limit for demo
            await asyncio.sleep(0.5)
            logger.info(f"Hyperparameter trial {trial + 1}/{min(n_trials, 5)}")
        
        # In real implementation, this would use Optuna/Hyperopt:
        # 1. Define search space
        # 2. Run optimization trials
        # 3. Select best hyperparameters
        # 4. Train final model with best params
        
        return True
    
    def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job by ID"""
        return self.db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    
    def list_training_jobs(self, model_id: Optional[str] = None,
                          status: Optional[str] = None,
                          limit: int = 50, offset: int = 0) -> List[TrainingJob]:
        """List training jobs with optional filtering"""
        query = self.db.query(TrainingJob)
        
        if model_id:
            query = query.filter(TrainingJob.model_id == model_id)
        
        if status:
            query = query.filter(TrainingJob.status == status)
        
        return query.order_by(TrainingJob.started_at.desc()).offset(offset).limit(limit).all()
    
    def cancel_training_job(self, job_id: str) -> bool:
        """Cancel a training job"""
        try:
            job = self.get_training_job(job_id)
            if not job:
                return False
            
            if job.status not in ["pending", "running"]:
                return False
            
            job.status = "cancelled"
            job.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Cancelled training job: {job_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cancel training job {job_id}: {str(e)}")
            return False
    
    # Model Registry Operations
    
    def register_model(self, model_id: str, model_name: str, model_type: str,
                      current_version: str, description: Optional[str] = None,
                      input_features: Optional[List[str]] = None,
                      output_features: Optional[List[str]] = None,
                      created_by: Optional[str] = None) -> ModelRegistry:
        """Register a model in the registry"""
        from schemas.ml_schemas import ModelRegistryCreate, ModelType
        
        model_data = ModelRegistryCreate(
            model_id=model_id,
            model_name=model_name,
            model_type=ModelType(model_type),
            current_version=current_version,
            description=description,
            input_features=input_features or [],
            output_features=output_features or [],
            created_by=created_by
        )
        
        return self.model_registry.register_model(model_data)
    
    def list_models(self, model_type: Optional[str] = None,
                   is_deployed: Optional[bool] = None,
                   limit: int = 50, offset: int = 0) -> List[ModelRegistry]:
        """List models in registry"""
        return self.model_registry.list_models(model_type, is_deployed, limit, offset)
    
    def get_model(self, model_id: str) -> Optional[ModelRegistry]:
        """Get model from registry"""
        return self.model_registry.get_model(model_id)
    
    def deploy_model(self, model_id: str, environment: str) -> bool:
        """Deploy a model to specified environment"""
        return self.model_registry.deploy_model(model_id, environment)
    
    # A/B Testing Operations
    
    def create_ab_test_experiment(self, experiment_id: str, name: str,
                                 description: Optional[str],
                                 control_model_id: str, control_model_version: str,
                                 treatment_model_id: str, treatment_model_version: str,
                                 primary_metric: str, traffic_split_control: float = 0.5,
                                 created_by: Optional[str] = None) -> ABTestExperiment:
        """Create an A/B test experiment"""
        try:
            experiment = ABTestExperiment(
                experiment_id=experiment_id,
                name=name,
                description=description,
                control_model_id=control_model_id,
                control_model_version=control_model_version,
                treatment_model_id=treatment_model_id,
                treatment_model_version=treatment_model_version,
                primary_metric=primary_metric,
                traffic_split_control=traffic_split_control,
                traffic_split_treatment=1.0 - traffic_split_control,
                status="setup",
                created_by=created_by
            )
            
            self.db.add(experiment)
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"Created A/B test experiment: {experiment_id}")
            return experiment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create A/B test experiment {experiment_id}: {str(e)}")
            raise
    
    def start_ab_test_experiment(self, experiment_id: str, duration_days: int) -> bool:
        """Start an A/B test experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.experiment_id == experiment_id
            ).first()
            
            if not experiment:
                return False
            
            if experiment.status != "setup":
                return False
            
            experiment.status = "running"
            experiment.started_at = datetime.utcnow()
            experiment.duration_days = duration_days
            
            # Schedule end time
            experiment.ended_at = experiment.started_at + timedelta(days=duration_days)
            
            self.db.commit()
            
            logger.info(f"Started A/B test experiment: {experiment_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to start A/B test experiment {experiment_id}: {str(e)}")
            return False
    
    def stop_ab_test_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Stop an A/B test experiment and analyze results"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.experiment_id == experiment_id
            ).first()
            
            if not experiment:
                return None
            
            if experiment.status != "running":
                return None
            
            # Simulate experiment results (replace with actual analysis)
            results = self._analyze_ab_test_results(experiment)
            
            # Update experiment with results
            experiment.status = "completed"
            experiment.ended_at = datetime.utcnow()
            experiment.control_metrics = results["control_metrics"]
            experiment.treatment_metrics = results["treatment_metrics"]
            experiment.statistical_significance = results["statistical_significance"]
            experiment.confidence_interval = results["confidence_interval"]
            experiment.effect_size = results["effect_size"]
            experiment.p_value = results["p_value"]
            experiment.winner = results["winner"]
            experiment.decision_reason = results["decision_reason"]
            experiment.decided_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Completed A/B test experiment: {experiment_id}")
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to stop A/B test experiment {experiment_id}: {str(e)}")
            return None
    
    def _analyze_ab_test_results(self, experiment: ABTestExperiment) -> Dict[str, Any]:
        """Analyze A/B test results (simulated)"""
        # Simulate results - in real implementation, this would:
        # 1. Collect performance data for both models
        # 2. Perform statistical tests
        # 3. Calculate confidence intervals
        # 4. Determine winner
        
        import random
        
        # Simulate metrics
        control_return = random.uniform(0.05, 0.15)
        treatment_return = control_return + random.uniform(-0.05, 0.08)
        
        control_metrics = {
            "total_return": control_return,
            "sharpe_ratio": random.uniform(0.8, 1.5),
            "max_drawdown": random.uniform(0.05, 0.15),
            "win_rate": random.uniform(0.45, 0.65)
        }
        
        treatment_metrics = {
            "total_return": treatment_return,
            "sharpe_ratio": control_metrics["sharpe_ratio"] + random.uniform(-0.2, 0.3),
            "max_drawdown": random.uniform(0.05, 0.15),
            "win_rate": random.uniform(0.45, 0.65)
        }
        
        # Determine winner
        if treatment_return > control_return * 1.05:  # 5% improvement threshold
            winner = "treatment"
            decision_reason = f"Treatment model showed {((treatment_return/control_return - 1) * 100):.1f}% improvement in {experiment.primary_metric}"
        elif control_return > treatment_return * 1.05:
            winner = "control"
            decision_reason = f"Control model outperformed treatment by {((control_return/treatment_return - 1) * 100):.1f}%"
        else:
            winner = "inconclusive"
            decision_reason = "No statistically significant difference between models"
        
        return {
            "control_metrics": control_metrics,
            "treatment_metrics": treatment_metrics,
            "statistical_significance": winner != "inconclusive",
            "confidence_interval": [min(control_return, treatment_return) - 0.02, 
                                  max(control_return, treatment_return) + 0.02],
            "effect_size": abs(treatment_return - control_return),
            "p_value": random.uniform(0.01, 0.15),
            "winner": winner,
            "decision_reason": decision_reason
        }
    
    def list_ab_test_experiments(self, status: Optional[str] = None,
                                limit: int = 50, offset: int = 0) -> List[ABTestExperiment]:
        """List A/B test experiments"""
        query = self.db.query(ABTestExperiment)
        
        if status:
            query = query.filter(ABTestExperiment.status == status)
        
        return query.order_by(ABTestExperiment.started_at.desc()).offset(offset).limit(limit).all()
    
    # Dashboard Statistics
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for ML dashboard"""
        try:
            # Training job statistics
            total_jobs = self.db.query(TrainingJob).count()
            running_jobs = self.db.query(TrainingJob).filter(TrainingJob.status == "running").count()
            completed_jobs = self.db.query(TrainingJob).filter(TrainingJob.status == "completed").count()
            failed_jobs = self.db.query(TrainingJob).filter(TrainingJob.status == "failed").count()
            
            # Model statistics
            model_stats = self.model_registry.get_model_statistics()
            
            # Drift detection statistics
            recent_drifts = self.db.query(ModelDriftHistory).filter(
                ModelDriftHistory.detected_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # A/B test statistics
            running_experiments = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "running"
            ).count()
            
            return {
                "training_jobs": {
                    "total": total_jobs,
                    "running": running_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs
                },
                "models": model_stats,
                "drift_detection": {
                    "recent_alerts": recent_drifts
                },
                "ab_testing": {
                    "running_experiments": running_experiments
                },
                "system_health": "healthy" if failed_jobs < total_jobs * 0.1 else "warning"
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            return {}
