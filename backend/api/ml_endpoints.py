"""
ML endpoints for model training, drift detection, performance monitoring, and A/B testing
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json

from core.database import get_db

# Optional ML models - make imports optional to prevent startup errors
try:
    from models.ml_models import (
        ModelDriftHistory, TrainingJob, ModelPerformanceMetrics, 
        ModelRegistry, ABTestExperiment
    )
    ML_MODELS_AVAILABLE = True
except ImportError:
    ML_MODELS_AVAILABLE = False
    ModelDriftHistory = TrainingJob = ModelPerformanceMetrics = None
    ModelRegistry = ABTestExperiment = None

try:
    from schemas.ml_schemas import (
        TrainingJobCreate, TrainingJobResponse, DriftDetectionResponse,
        PerformanceMetricsResponse, ModelRegistryCreate, ModelRegistryResponse,
        ABTestExperimentCreate, ABTestExperimentResponse
    )
    ML_SCHEMAS_AVAILABLE = True
except ImportError:
    ML_SCHEMAS_AVAILABLE = False
    TrainingJobCreate = TrainingJobResponse = DriftDetectionResponse = None
    PerformanceMetricsResponse = ModelRegistryCreate = ModelRegistryResponse = None
    ABTestExperimentCreate = ABTestExperimentResponse = None

# Optional ML services - make imports optional
try:
    from services.ml_service import MLService
    from services.drift_detection_service import DriftDetectionService
    from services.performance_monitoring_service import PerformanceMonitoringService
    ML_SERVICES_AVAILABLE = True
except ImportError:
    ML_SERVICES_AVAILABLE = False
    MLService = DriftDetectionService = PerformanceMonitoringService = None

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

# Training Management Endpoints

@router.post("/training/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    job_data: TrainingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and start a new training job"""
    if not ML_SERVICES_AVAILABLE or not ML_SCHEMAS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    try:
        ml_service = MLService(db)
        
        # Generate unique job ID
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # Create training job record
        training_job = ml_service.create_training_job(
            job_id=job_id,
            model_id=job_data.model_id,
            model_version=job_data.model_version,
            job_type=job_data.job_type,
            hyperparameters=job_data.hyperparameters,
            validation_split=job_data.validation_split,
            created_by=job_data.created_by
        )
        
        # Start training in background
        background_tasks.add_task(
            ml_service.run_training_job,
            job_id=job_id
        )
        
        return TrainingJobResponse.from_orm(training_job)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create training job: {str(e)}")

@router.get("/training/jobs", response_model=List[TrainingJobResponse])
async def list_training_jobs(
    model_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List training jobs with optional filtering"""
    try:
        ml_service = MLService(db)
        jobs = ml_service.list_training_jobs(
            model_id=model_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [TrainingJobResponse.from_orm(job) for job in jobs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list training jobs: {str(e)}")

@router.get("/training/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific training job"""
    try:
        ml_service = MLService(db)
        job = ml_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")
            
        return TrainingJobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training job: {str(e)}")

@router.post("/training/jobs/{job_id}/cancel")
async def cancel_training_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a running training job"""
    try:
        ml_service = MLService(db)
        success = ml_service.cancel_training_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Training job not found or cannot be cancelled")
            
        return {"message": "Training job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel training job: {str(e)}")

# Drift Detection Endpoints

@router.post("/drift/detect", response_model=DriftDetectionResponse)
async def detect_model_drift(
    model_id: str,
    model_version: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger drift detection for a specific model"""
    try:
        drift_service = DriftDetectionService(db)
        
        # Run drift detection in background
        background_tasks.add_task(
            drift_service.run_drift_detection,
            model_id=model_id,
            model_version=model_version
        )
        
        return {"message": "Drift detection started", "status": "running"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start drift detection: {str(e)}")

@router.get("/drift/history", response_model=List[DriftDetectionResponse])
async def get_drift_history(
    model_id: Optional[str] = Query(None),
    model_version: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get drift detection history"""
    try:
        drift_service = DriftDetectionService(db)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        drift_records = drift_service.get_drift_history(
            model_id=model_id,
            model_version=model_version,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        return [DriftDetectionResponse.from_orm(record) for record in drift_records]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drift history: {str(e)}")

@router.get("/drift/latest/{model_id}")
async def get_latest_drift_score(
    model_id: str,
    model_version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get latest drift score for a model"""
    try:
        drift_service = DriftDetectionService(db)
        latest_drift = drift_service.get_latest_drift(model_id, model_version)
        
        if not latest_drift:
            return {"drift_score": None, "status": "no_data"}
            
        return {
            "drift_score": latest_drift.drift_score,
            "drift_type": latest_drift.drift_type,
            "detected_at": latest_drift.detected_at,
            "status": latest_drift.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest drift: {str(e)}")

# Performance Monitoring Endpoints

@router.get("/performance/metrics", response_model=List[PerformanceMetricsResponse])
async def get_performance_metrics(
    model_id: Optional[str] = Query(None),
    model_version: Optional[str] = Query(None),
    evaluation_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get performance metrics for models"""
    try:
        perf_service = PerformanceMonitoringService(db)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        metrics = perf_service.get_performance_metrics(
            model_id=model_id,
            model_version=model_version,
            evaluation_type=evaluation_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return [PerformanceMetricsResponse.from_orm(metric) for metric in metrics]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/performance/summary/{model_id}")
async def get_performance_summary(
    model_id: str,
    model_version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get performance summary for a model"""
    try:
        perf_service = PerformanceMonitoringService(db)
        summary = perf_service.get_performance_summary(model_id, model_version)
        
        if not summary:
            return {"message": "No performance data found"}
            
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

# Model Registry Endpoints

@router.post("/registry/models", response_model=ModelRegistryResponse)
async def register_model(
    model_data: ModelRegistryCreate,
    db: Session = Depends(get_db)
):
    """Register a new model in the registry"""
    try:
        ml_service = MLService(db)
        model = ml_service.register_model(
            model_id=model_data.model_id,
            model_name=model_data.model_name,
            model_type=model_data.model_type,
            current_version=model_data.current_version,
            description=model_data.description,
            input_features=model_data.input_features,
            output_features=model_data.output_features,
            created_by=model_data.created_by
        )
        
        return ModelRegistryResponse.from_orm(model)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register model: {str(e)}")

@router.get("/registry/models", response_model=List[ModelRegistryResponse])
async def list_models(
    model_type: Optional[str] = Query(None),
    is_deployed: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List models in the registry"""
    try:
        ml_service = MLService(db)
        models = ml_service.list_models(
            model_type=model_type,
            is_deployed=is_deployed,
            limit=limit,
            offset=offset
        )
        
        return [ModelRegistryResponse.from_orm(model) for model in models]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.get("/registry/models/{model_id}", response_model=ModelRegistryResponse)
async def get_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Get model details from registry"""
    try:
        ml_service = MLService(db)
        model = ml_service.get_model(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
            
        return ModelRegistryResponse.from_orm(model)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")

@router.post("/registry/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    environment: str = Query(..., regex="^(development|staging|production)$"),
    db: Session = Depends(get_db)
):
    """Deploy a model to specified environment"""
    try:
        ml_service = MLService(db)
        success = ml_service.deploy_model(model_id, environment)
        
        if not success:
            raise HTTPException(status_code=404, detail="Model not found or deployment failed")
            
        return {"message": f"Model deployed to {environment}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {str(e)}")

# A/B Testing Endpoints

@router.post("/abtest/experiments", response_model=ABTestExperimentResponse)
async def create_ab_test(
    experiment_data: ABTestExperimentCreate,
    db: Session = Depends(get_db)
):
    """Create a new A/B test experiment"""
    try:
        ml_service = MLService(db)
        experiment = ml_service.create_ab_test_experiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            name=experiment_data.name,
            description=experiment_data.description,
            control_model_id=experiment_data.control_model_id,
            control_model_version=experiment_data.control_model_version,
            treatment_model_id=experiment_data.treatment_model_id,
            treatment_model_version=experiment_data.treatment_model_version,
            primary_metric=experiment_data.primary_metric,
            traffic_split_control=experiment_data.traffic_split_control,
            created_by=experiment_data.created_by
        )
        
        return ABTestExperimentResponse.from_orm(experiment)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create A/B test: {str(e)}")

@router.get("/abtest/experiments", response_model=List[ABTestExperimentResponse])
async def list_ab_tests(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List A/B test experiments"""
    try:
        ml_service = MLService(db)
        experiments = ml_service.list_ab_test_experiments(
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [ABTestExperimentResponse.from_orm(exp) for exp in experiments]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list A/B tests: {str(e)}")

@router.post("/abtest/experiments/{experiment_id}/start")
async def start_ab_test(
    experiment_id: str,
    duration_days: int = Query(..., ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Start an A/B test experiment"""
    try:
        ml_service = MLService(db)
        success = ml_service.start_ab_test_experiment(experiment_id, duration_days)
        
        if not success:
            raise HTTPException(status_code=404, detail="Experiment not found or cannot be started")
            
        return {"message": "A/B test started", "duration_days": duration_days}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start A/B test: {str(e)}")

@router.post("/abtest/experiments/{experiment_id}/stop")
async def stop_ab_test(
    experiment_id: str,
    db: Session = Depends(get_db)
):
    """Stop an A/B test experiment and analyze results"""
    try:
        ml_service = MLService(db)
        results = ml_service.stop_ab_test_experiment(experiment_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Experiment not found or cannot be stopped")
            
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop A/B test: {str(e)}")
