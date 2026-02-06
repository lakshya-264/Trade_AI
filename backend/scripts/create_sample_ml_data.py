"""
Create Sample ML Data
Script to populate ML dashboard with sample data for demonstration
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.ml_models import TrainingJob, ModelRegistry, MLModelPerformanceMetrics, ModelDriftHistory, ABTestExperiment

def create_sample_data():
    """Create sample ML data for dashboard demonstration"""
    db = SessionLocal()
    
    try:
        # Create sample models
        models = [
            {
                "model_id": "stock_classifier_v1",
                "model_name": "Stock Movement Classifier",
                "model_type": "classification",
                "model_version": "1.0.0",
                "framework": "sklearn",
                "is_deployed": True,
                "deployment_environment": "production",
                "model_metadata": {"description": "Classifies stock movements", "features": ["price", "volume", "indicators"]}
            },
            {
                "model_id": "price_predictor_v2",
                "model_name": "Price Prediction Model",
                "model_type": "regression",
                "model_version": "2.1.0",
                "framework": "tensorflow",
                "is_deployed": True,
                "deployment_environment": "staging"
            },
            {
                "model_id": "trading_agent_v1",
                "model_name": "Reinforcement Trading Agent",
                "model_type": "reinforcement_learning",
                "model_version": "1.0.0",
                "framework": "pytorch",
                "is_deployed": False,
                "deployment_environment": None
            }
        ]
        
        for model_data in models:
            # Check if model already exists
            existing = db.query(ModelRegistry).filter(ModelRegistry.model_id == model_data["model_id"]).first()
            if not existing:
                model = ModelRegistry(**model_data)
                db.add(model)
        
        # Create sample training jobs
        job_statuses = ["running", "completed", "failed", "completed", "running"]
        for i, status in enumerate(job_statuses):
            job_id = f"job_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}"
            
            # Check if job already exists
            existing = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
            if not existing:
                job = TrainingJob(
                    job_id=job_id,
                    model_id=random.choice([m["model_id"] for m in models]),
                    model_version="1.0.0",
                    job_type="training",
                    status=status,
                    started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                    progress=100 if status == "completed" else random.randint(10, 90) if status == "running" else 0,
                    training_duration_seconds=random.randint(1800, 7200) if status == "completed" else None,
                    hyperparameters={"learning_rate": 0.001, "batch_size": 32, "epochs": 100},
                    metrics={"accuracy": random.uniform(0.7, 0.95), "loss": random.uniform(0.1, 0.5)} if status == "completed" else None,
                )
                
                # Add error details for failed jobs
                if status == "failed":
                    job.error_message = random.choice([
                        "Out of memory error - dataset too large for available RAM",
                        "Data validation failed - found NaN values in training data",
                        "Hyperparameter convergence failed - learning rate too high",
                        "Model checkpoint corruption - unable to save intermediate state",
                        "GPU memory overflow - batch size exceeds GPU capacity"
                    ])
                    
                    # Add detailed error traceback based on error type
                    if "memory" in job.error_message.lower():
                        job.error_traceback = """Traceback (most recent call last):
  File "training_pipeline.py", line 156, in train_model
    model.fit(X_train, y_train)
  File "tensorflow/keras/engine/training.py", line 1234, in fit
    raise MemoryError("Unable to allocate 8.2 GiB for training batch")
MemoryError: CUDA out of memory. Tried to allocate 8.20 GiB for tensor with shape [1024, 1024, 512]
  GPU: NVIDIA RTX 3080 (10.0 GiB total capacity)
"""
                    elif "validation" in job.error_message.lower():
                        job.error_traceback = """Traceback (most recent call last):
  File "data_preprocessing.py", line 89, in validate_data
    assert not np.any(np.isnan(X_train)), "NaN values found in training data"
AssertionError: NaN values found in training data
  Found 1,247 NaN values in features: ['volume', 'rsi', 'macd']
  Suggestion: Use data imputation or remove affected samples
"""
                    elif "convergence" in job.error_message.lower():
                        job.error_traceback = """Traceback (most recent call last):
  File "model_training.py", line 234, in train_with_validation
    history = model.fit(X_train, y_train, validation_split=0.2)
  File "tensorflow/keras/engine/training.py", line 1456, in fit
    raise ConvergenceError("Model failed to converge after 100 epochs")
ConvergenceError: Training loss oscillating, no improvement for 50 consecutive epochs
  Current loss: 0.8234, Best loss: 0.8156
  Consider: Lower learning rate, different optimizer, or model architecture
"""
                    else:
                        job.error_traceback = """Traceback (most recent call last):
  File "checkpoint_manager.py", line 67, in save_checkpoint
    torch.save(model.state_dict(), checkpoint_path)
  File "torch/serialization.py", line 292, in save
    raise IOError("Unable to write checkpoint file")
IOError: Disk space insufficient - need 2.5 GiB, only 1.2 GiB available
"""
                
                if status == "completed":
                    job.completed_at = job.started_at + timedelta(seconds=job.training_duration_seconds)
                db.add(job)
        
        # Create sample performance metrics
        for model in models:
            for days_ago in range(30, 0, -5):
                metrics = MLModelPerformanceMetrics(
                    model_id=model["model_id"],
                    model_version=model["model_version"],
                    evaluated_at=datetime.utcnow() - timedelta(days=days_ago),
                    evaluation_type="validation",
                    accuracy=random.uniform(0.7, 0.95),
                    precision=random.uniform(0.65, 0.92),
                    recall=random.uniform(0.68, 0.94),
                    f1_score=random.uniform(0.72, 0.93),
                    total_return=random.uniform(-0.1, 0.25),
                    sharpe_ratio=random.uniform(0.5, 2.5),
                    max_drawdown=random.uniform(-0.2, -0.05),
                    win_rate=random.uniform(0.45, 0.75),
                    profit_factor=random.uniform(1.1, 2.8)
                )
                db.add(metrics)
        
        # Create sample drift alerts
        drift_severities = ["high", "medium", "low", "medium"]
        for i, severity in enumerate(drift_severities):
            drift = ModelDriftHistory(
                model_id=random.choice([m["model_id"] for m in models]),
                model_version="1.0.0",
                detected_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                drift_type=random.choice(["data_drift", "concept_drift", "performance_drift"]),
                drift_score=random.uniform(0.3, 0.9),
                drift_threshold=0.7,
                status="active",
                severity=severity,
                description=f"Drift detected in model performance metrics",
                recommended_action="Retrain model with recent data" if severity == "high" else "Monitor closely"
            )
            db.add(drift)
        
        # Create sample A/B tests
        experiments = [
            {
                "experiment_id": "exp_classifier_comparison",
                "name": "Classifier Model Comparison",
                "control_model_id": "stock_classifier_v1",
                "treatment_model_id": "stock_classifier_v2",
                "primary_metric": "accuracy",
                "status": "running",
                "duration_days": 14
            },
            {
                "experiment_id": "exp_predictor_enhancement",
                "name": "Price Predictor Enhancement",
                "control_model_id": "price_predictor_v1",
                "treatment_model_id": "price_predictor_v2",
                "primary_metric": "total_return",
                "status": "completed",
                "duration_days": 21,
                "winner": "treatment",
                "statistical_significance": True
            }
        ]
        
        for exp_data in experiments:
            # Check if experiment already exists
            existing = db.query(ABTestExperiment).filter(ABTestExperiment.experiment_id == exp_data["experiment_id"]).first()
            if not existing:
                exp = ABTestExperiment(
                    experiment_id=exp_data["experiment_id"],
                    name=exp_data["name"],
                    control_model_id=exp_data["control_model_id"],
                    treatment_model_id=exp_data["treatment_model_id"],
                    primary_metric=exp_data["primary_metric"],
                    status=exp_data["status"],
                    started_at=datetime.utcnow() - timedelta(days=exp_data.get("duration_days", 14)),
                    traffic_split=0.5,
                    duration_days=exp_data.get("duration_days"),
                    winner=exp_data.get("winner"),
                    statistical_significance=exp_data.get("statistical_significance"),
                    control_performance={"accuracy": 0.82, "total_return": 0.15} if exp_data["experiment_id"] == "exp_classifier_comparison" else {"total_return": 0.12},
                    treatment_performance={"accuracy": 0.85, "total_return": 0.18} if exp_data["experiment_id"] == "exp_classifier_comparison" else {"total_return": 0.19}
                )
                if exp_data["status"] == "completed":
                    exp.ended_at = exp.started_at + timedelta(days=exp_data["duration_days"])
                db.add(exp)
        
        db.commit()
        print("✅ Sample ML data created successfully!")
        
        # Print summary
        print(f"Models: {db.query(ModelRegistry).count()}")
        print(f"Training Jobs: {db.query(TrainingJob).count()}")
        print(f"Performance Metrics: {db.query(MLModelPerformanceMetrics).count()}")
        print(f"Drift Alerts: {db.query(ModelDriftHistory).count()}")
        print(f"A/B Tests: {db.query(ABTestExperiment).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
