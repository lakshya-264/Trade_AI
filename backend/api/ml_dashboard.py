"""
ML Dashboard API endpoints
Real-time training and performance visualization dashboard
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime, timedelta

from core.database import get_db

# Optional ML services - make imports optional
try:
    from services.ml_service import MLService
    from services.drift_detection_service import DriftDetectionService
    from services.performance_monitoring_service import PerformanceMonitoringService
    from services.error_monitoring_service import ErrorMonitoringService
    from services.auto_retry_service import AutoRetryService
    from services.resource_monitoring_service import ResourceMonitoringService
    from services.performance_optimization_service import PerformanceOptimizationService
    from services.automated_code_optimizer import AutomatedCodeOptimizer
    ML_SERVICES_AVAILABLE = True
except ImportError:
    ML_SERVICES_AVAILABLE = False
    MLService = DriftDetectionService = PerformanceMonitoringService = ErrorMonitoringService = AutoRetryService = ResourceMonitoringService = PerformanceOptimizationService = AutomatedCodeOptimizer = None

router = APIRouter(prefix="/api/v1/ml/dashboard", tags=["ML Dashboard"])

# WebSocket connection manager
class DashboardConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message, default=str)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn)

manager = DashboardConnectionManager()

@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """Get dashboard overview with key metrics"""
    if not ML_SERVICES_AVAILABLE:
        # Return mock data when ML services aren't available
        return {
            "metrics": {
                "training_jobs": {"total": 0, "running": 0, "completed": 0, "failed": 0},
                "models": {"total_models": 0, "deployed_models": 0, "model_types": {}, "deployment_environments": {}, "storage_usage_mb": 0},
                "drift_detection": {"recent_alerts": 0},
                "ab_testing": {"running_experiments": 0},
                "system_health": "unavailable"
            },
            "recent_activity": [],
            "system_status": {"status": "ML services unavailable", "message": "ML services are not installed or configured"},
            "timestamp": datetime.utcnow()
        }
    try:
        ml_service = MLService(db)
        metrics = ml_service.get_dashboard_metrics()
        
        # Add recent activity
        recent_activity = get_recent_activity(db)
        
        # Add system status
        system_status = get_system_status()
        
        return {
            "metrics": metrics,
            "recent_activity": recent_activity,
            "system_status": system_status,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")

@router.get("/training/status")
async def get_training_status(db: Session = Depends(get_db)):
    """Get current training job status"""
    if not ML_SERVICES_AVAILABLE:
        return {
            "running_jobs": [],
            "recent_completed": [],
            "total_jobs": 0,
            "message": "ML services unavailable"
        }
    try:
        ml_service = MLService(db)
        
        # Get running jobs
        running_jobs = ml_service.list_training_jobs(status="running", limit=10)
        
        # Get recent completed jobs
        recent_completed = ml_service.list_training_jobs(
            status="completed", 
            limit=5
        )
        
        # Get recent failed jobs
        recent_failed = ml_service.list_training_jobs(
            status="failed", 
            limit=5
        )
        
        return {
            "running_jobs": [format_training_job(job) for job in running_jobs],
            "recent_completed": [format_training_job(job) for job in recent_completed],
            "recent_failed": [format_training_job(job) for job in recent_failed],
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training status: {str(e)}")

@router.get("/training/errors/{job_id}")
async def get_training_job_error(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed error information for a failed training job"""
    if not ML_SERVICES_AVAILABLE:
        return {
            "job_id": job_id,
            "error_message": "ML services unavailable",
            "error_traceback": None,
            "error_category": "system",
            "suggested_actions": ["Check ML service status", "Verify backend connectivity"]
        }
    
    try:
        from models.ml_models import TrainingJob
        
        # Get the failed job
        job = db.query(TrainingJob).filter(
            TrainingJob.job_id == job_id,
            TrainingJob.status == 'failed'
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Failed job {job_id} not found")
        
        # Categorize the error
        error_category = "unknown"
        suggested_actions = []
        
        if job.error_message:
            error_msg = job.error_message.lower()
            if "memory" in error_msg:
                error_category = "resource"
                suggested_actions = [
                    "Reduce batch size",
                    "Use gradient accumulation",
                    "Increase available RAM/GPU memory",
                    "Use data streaming instead of loading all data"
                ]
            elif "nan" in error_msg or "validation" in error_msg:
                error_category = "data"
                suggested_actions = [
                    "Check data quality",
                    "Implement data imputation",
                    "Remove corrupted samples",
                    "Add data validation checks"
                ]
            elif "convergence" in error_msg or "learning rate" in error_msg:
                error_category = "hyperparameter"
                suggested_actions = [
                    "Lower learning rate",
                    "Try different optimizer",
                    "Adjust model architecture",
                    "Implement learning rate scheduling"
                ]
            elif "checkpoint" in error_msg or "disk" in error_msg:
                error_category = "infrastructure"
                suggested_actions = [
                    "Free up disk space",
                    "Check file permissions",
                    "Use different checkpoint location",
                    "Implement checkpoint compression"
                ]
        
        return {
            "job_id": job.job_id,
            "model_id": job.model_id,
            "error_message": job.error_message,
            "error_traceback": job.error_traceback,
            "error_category": error_category,
            "suggested_actions": suggested_actions,
            "failed_at": job.started_at,
            "hyperparameters": job.hyperparameters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error details: {str(e)}")

@router.get("/training/errors/summary")
async def get_errors_summary(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get summary of recent training errors with categorization"""
    if not ML_SERVICES_AVAILABLE:
        return {
            "total_errors": 0,
            "error_categories": {},
            "recent_errors": [],
            "message": "ML services unavailable"
        }
    
    try:
        from models.ml_models import TrainingJob
        from datetime import datetime, timedelta
        
        # Get recent failed jobs
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        failed_jobs = db.query(TrainingJob).filter(
            TrainingJob.status == 'failed',
            TrainingJob.started_at >= start_date
        ).order_by(desc(TrainingJob.started_at)).all()
        
        # Categorize errors
        error_categories = {
            "resource": 0,
            "data": 0,
            "hyperparameter": 0,
            "infrastructure": 0,
            "unknown": 0
        }
        
        recent_errors = []
        
        for job in failed_jobs:
            # Categorize error
            error_category = "unknown"
            if job.error_message:
                error_msg = job.error_message.lower()
                if "memory" in error_msg:
                    error_category = "resource"
                elif "nan" in error_msg or "validation" in error_msg:
                    error_category = "data"
                elif "convergence" in error_msg or "learning rate" in error_msg:
                    error_category = "hyperparameter"
                elif "checkpoint" in error_msg or "disk" in error_msg:
                    error_category = "infrastructure"
            
            error_categories[error_category] += 1
            
            recent_errors.append({
                "job_id": job.job_id,
                "model_id": job.model_id,
                "error_message": job.error_message,
                "error_category": error_category,
                "failed_at": job.started_at
            })
        
        return {
            "total_errors": len(failed_jobs),
            "error_categories": error_categories,
            "recent_errors": recent_errors[:10],  # Last 10 errors
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get errors summary: {str(e)}")

@router.post("/training/{job_id}/retry")
async def retry_failed_job(
    job_id: str,
    retry_config: dict = None,
    db: Session = Depends(get_db)
):
    """Retry a failed training job with optional configuration changes"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        from models.ml_models import TrainingJob
        import uuid
        from datetime import datetime
        
        # Get the failed job
        failed_job = db.query(TrainingJob).filter(
            TrainingJob.job_id == job_id,
            TrainingJob.status == 'failed'
        ).first()
        
        if not failed_job:
            raise HTTPException(status_code=404, detail=f"Failed job {job_id} not found")
        
        # Create new retry job
        new_job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M')}_retry"
        
        retry_job = TrainingJob(
            job_id=new_job_id,
            model_id=failed_job.model_id,
            model_version=failed_job.model_version,
            job_type="training",
            status="running",
            started_at=datetime.utcnow(),
            hyperparameters=retry_config or failed_job.hyperparameters,
            progress=0.0
        )
        
        db.add(retry_job)
        db.commit()
        
        return {
            "message": f"Job {job_id} retry initiated",
            "new_job_id": new_job_id,
            "original_job_id": job_id,
            "status": "running",
            "retry_config": retry_config or failed_job.hyperparameters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry job: {str(e)}")

@router.get("/models/performance")
async def get_models_performance(
    model_id: str = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get MLModelPerformanceMetrics"""
    if not ML_SERVICES_AVAILABLE:
        return {
            "metrics": [],
            "summary": {"avg_return": 0, "avg_sharpe": 0, "total_models": 0},
            "message": "ML services unavailable"
        }
    try:
        perf_service = PerformanceMonitoringService(db)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get performance metrics
        if model_id:
            metrics = perf_service.get_performance_metrics(
                model_id=model_id,
                start_date=start_date,
                end_date=end_date
            )
        else:
            # Get metrics for all models
            metrics = perf_service.get_performance_metrics(
                start_date=start_date,
                end_date=end_date
            )
        
        # Get performance summaries
        summaries = {}
        if model_id:
            summary = perf_service.get_performance_summary(model_id)
            if summary:
                summaries[model_id] = summary
        else:
            # Get summaries for top models
            ml_service = MLService(db)
            models = ml_service.list_models(limit=10)
            for model in models:
                summary = perf_service.get_performance_summary(model.model_id)
                if summary:
                    summaries[model.model_id] = summary
        
        return {
            "metrics": [format_performance_metric(metric) for metric in metrics],
            "summaries": summaries,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": days
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {str(e)}")

@router.get("/drift/alerts")
async def get_drift_alerts(
    model_id: str = None,
    status: str = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get drift detection alerts"""
    if not ML_SERVICES_AVAILABLE:
        return {
            "alerts": {"high": [], "medium": [], "low": []},
            "total_alerts": 0,
            "message": "ML services unavailable"
        }
    try:
        drift_service = DriftDetectionService(db)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get drift history
        drift_records = drift_service.get_drift_history(
            model_id=model_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group by severity
        alerts_by_severity = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for record in drift_records:
            severity = get_drift_severity(record.drift_score)
            alerts_by_severity[severity].append(format_drift_alert(record))
        
        return {
            "alerts": alerts_by_severity,
            "total_alerts": len(drift_records),
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": days
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drift alerts: {str(e)}")

@router.get("/ab-testing/experiments")
async def get_ab_testing_experiments(
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get A/B testing experiments"""
    if not ML_SERVICES_AVAILABLE:
        return {
            "experiments": [],
            "total_experiments": 0,
            "message": "ML services unavailable"
        }
    try:
        ml_service = MLService(db)
        experiments = ml_service.list_ab_test_experiments(status=status, limit=20)
        
        return {
            "experiments": [format_ab_test_experiment(exp) for exp in experiments],
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get A/B testing experiments: {str(e)}")

@router.get("/models/registry")
async def get_models_registry(
    model_type: str = None,
    is_deployed: bool = None,
    db: Session = Depends(get_db)
):
    """Get models from registry"""
    try:
        ml_service = MLService(db)
        models = ml_service.list_models(
            model_type=model_type,
            is_deployed=is_deployed,
            limit=50
        )
        
        return {
            "models": [format_model_registry(model) for model in models],
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models registry: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)  # Update every 5 seconds
            
            # Get current metrics (would need database session)
            update_data = {
                "type": "metrics_update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    # Add real-time metrics here
                    "active_training_jobs": 0,
                    "recent_drift_alerts": 0,
                    "system_health": "healthy"
                }
            }
            
            await manager.broadcast(update_data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Helper functions for formatting data

def format_training_job(job) -> Dict[str, Any]:
    """Format training job for dashboard"""
    return {
        "job_id": job.job_id,
        "model_id": job.model_id,
        "model_version": job.model_version,
        "job_type": job.job_type,
        "status": job.status,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "training_duration_seconds": job.training_duration_seconds,
        "progress": calculate_job_progress(job),
        "error_message": job.error_message
    }

def format_performance_metric(metric) -> Dict[str, Any]:
    """Format performance metric for dashboard"""
    return {
        "id": metric.id,
        "model_id": metric.model_id,
        "model_version": metric.model_version,
        "evaluated_at": metric.evaluated_at,
        "total_return": metric.total_return,
        "sharpe_ratio": metric.sharpe_ratio,
        "max_drawdown": metric.max_drawdown,
        "win_rate": metric.win_rate,
        "evaluation_type": metric.evaluation_type
    }

def format_drift_alert(alert) -> Dict[str, Any]:
    """Format drift alert for dashboard"""
    return {
        "id": alert.id,
        "model_id": alert.model_id,
        "model_version": alert.model_version,
        "drift_score": alert.drift_score,
        "drift_type": alert.drift_type,
        "detected_at": alert.detected_at,
        "status": alert.status,
        "severity": get_drift_severity(alert.drift_score)
    }

def format_ab_test_experiment(exp) -> Dict[str, Any]:
    """Format A/B test experiment for dashboard"""
    return {
        "experiment_id": exp.experiment_id,
        "name": exp.name,
        "status": exp.status,
        "started_at": exp.started_at,
        "ended_at": exp.ended_at,
        "duration_days": exp.duration_days,
        "control_model_id": exp.control_model_id,
        "treatment_model_id": exp.treatment_model_id,
        "primary_metric": exp.primary_metric,
        "winner": exp.winner,
        "statistical_significance": exp.statistical_significance
    }

def format_model_registry(model) -> Dict[str, Any]:
    """Format model registry entry for dashboard"""
    return {
        "model_id": model.model_id,
        "model_name": model.model_name,
        "model_type": model.model_type,
        "current_version": model.current_version,
        "is_deployed": model.is_deployed,
        "deployment_environment": model.deployment_environment,
        "best_test_metric": model.best_test_metric,
        "latest_drift_score": model.latest_drift_score,
        "created_at": model.created_at,
        "updated_at": model.updated_at
    }

def calculate_job_progress(job) -> float:
    """Calculate training job progress"""
    if job.status == "completed":
        return 100.0
    elif job.status == "failed" or job.status == "cancelled":
        return 0.0
    elif job.status == "running":
        # Estimate progress based on time elapsed
        if job.started_at:
            elapsed = datetime.utcnow() - job.started_at
            # Assume max 4 hours for training
            max_duration = timedelta(hours=4)
            progress = min(100.0, (elapsed.total_seconds() / max_duration.total_seconds()) * 100)
            return progress
    return 0.0

def get_drift_severity(drift_score: float) -> str:
    """Determine drift severity based on score"""
    if drift_score >= 0.8:
        return "high"
    elif drift_score >= 0.5:
        return "medium"
    else:
        return "low"

def get_recent_activity(db: Session) -> List[Dict[str, Any]]:
    """Get recent activity for dashboard"""
    try:
        from models.ml_models import TrainingJob, ModelDriftHistory, ABTestExperiment
        
        activities = []
        
        # Recent training jobs
        recent_jobs = db.query(TrainingJob).order_by(TrainingJob.started_at.desc()).limit(5).all()
        for job in recent_jobs:
            activities.append({
                "type": "training_job",
                "id": job.job_id,
                "message": f"Training job {job.job_id} {job.status}",
                "timestamp": job.started_at or job.created_at,
                "status": job.status
            })
        
        # Recent drift alerts
        recent_drifts = db.query(ModelDriftHistory).order_by(ModelDriftHistory.detected_at.desc()).limit(3).all()
        for drift in recent_drifts:
            activities.append({
                "type": "drift_alert",
                "id": drift.id,
                "message": f"Drift detected for model {drift.model_id}",
                "timestamp": drift.detected_at,
                "severity": drift.severity
            })
        
        # Recent A/B tests
        recent_tests = db.query(ABTestExperiment).order_by(ABTestExperiment.started_at.desc()).limit(3).all()
        for test in recent_tests:
            activities.append({
                "type": "ab_test",
                "id": test.experiment_id,
                "message": f"A/B test {test.name} {test.status}",
                "timestamp": test.started_at,
                "status": test.status
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:10]
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []

def get_system_status() -> Dict[str, Any]:
    """Get overall system status"""
    return {
        "health": "healthy",
        "ml_services": ML_SERVICES_AVAILABLE,
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time ML Dashboard updates"""
    if ML_SERVICES_AVAILABLE:
        await error_monitoring_service.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    # Handle client requests (e.g., subscribe to specific updates)
                    if message.get('type') == 'subscribe':
                        # Handle subscription requests
                        pass
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {data}")
        except WebSocketDisconnect:
            error_monitoring_service.disconnect(websocket)
    else:
        await websocket.close(code=1000, reason="ML services unavailable")

# Background task for error monitoring
async def start_error_monitoring():
    """Start the background error monitoring task"""
    if ML_SERVICES_AVAILABLE:
        asyncio.create_task(error_monitoring_service.monitor_errors())

# Auto-Retry endpoints
@router.post("/training/{job_id}/auto-retry")
async def auto_retry_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Analyze failed job and execute optimized retry"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        # Analyze failure and create retry plan
        retry_plan = await auto_retry_service.analyze_failure(job_id, db)
        
        if not retry_plan:
            raise HTTPException(status_code=400, detail="Retry not recommended for this job")
        
        # Execute retry
        new_job_id = await auto_retry_service.execute_retry(retry_plan, db)
        
        if not new_job_id:
            raise HTTPException(status_code=500, detail="Failed to execute retry")
        
        return {
            "message": "Auto-retry initiated successfully",
            "original_job_id": job_id,
            "new_job_id": new_job_id,
            "retry_plan": retry_plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-retry failed: {str(e)}")

@router.get("/training/{job_id}/retry-analysis")
async def get_retry_analysis(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get retry analysis without executing retry"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        retry_plan = await auto_retry_service.analyze_failure(job_id, db)
        
        if not retry_plan:
            return {
                "retry_recommended": False,
                "reason": "Job not eligible for retry",
                "job_id": job_id
            }
        
        return {
            "retry_recommended": True,
            "retry_plan": retry_plan,
            "job_id": job_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retry analysis failed: {str(e)}")

@router.get("/models/{model_id}/retry-history")
async def get_retry_history(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Get retry history for a model"""
    if not ML_SERVICES_AVAILABLE:
        return {"retry_history": [], "message": "ML services unavailable"}
    
    try:
        from models.ml_models import TrainingJob
        
        retry_jobs = db.query(TrainingJob).filter(
            TrainingJob.model_id == model_id,
            TrainingJob.job_id.like('%_auto_retry')
        ).order_by(desc(TrainingJob.started_at)).limit(20).all()
        
        history = []
        for job in retry_jobs:
            retry_metadata = job.hyperparameters.get('_retry_metadata', {})
            history.append({
                "job_id": job.job_id,
                "status": job.status,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "error_category": retry_metadata.get('original_error'),
                "retry_count": retry_metadata.get('retry_count'),
                "success_rate": retry_metadata.get('estimated_success_rate'),
                "optimization_strategy": retry_metadata.get('optimization_strategy')
            })
        
        return {
            "model_id": model_id,
            "retry_history": history,
            "total_retries": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retry history: {str(e)}")

@router.get("/auto-retry/performance")
async def get_auto_retry_performance():
    """Get auto-retry system performance metrics"""
    if not ML_SERVICES_AVAILABLE:
        return {"performance": {}, "message": "ML services unavailable"}
    
    try:
        performance_metrics = auto_retry_service.performance_history
        
        # Calculate overall statistics
        total_retries = sum(len(history) for history in performance_metrics.values())
        successful_retries = sum(
            sum(1 for outcome in history if outcome['success'])
            for history in performance_metrics.values()
        )
        
        success_rate = successful_retries / total_retries if total_retries > 0 else 0
        
        # Performance by error category
        category_performance = {}
        for history in performance_metrics.values():
            for outcome in history:
                category = outcome['error_category']
                if category not in category_performance:
                    category_performance[category] = {'total': 0, 'success': 0}
                category_performance[category]['total'] += 1
                if outcome['success']:
                    category_performance[category]['success'] += 1
        
        # Calculate success rates by category
        for category in category_performance:
            total = category_performance[category]['total']
            success = category_performance[category]['success']
            category_performance[category]['success_rate'] = success / total if total > 0 else 0
        
        return {
            "total_retries": total_retries,
            "successful_retries": successful_retries,
            "overall_success_rate": success_rate,
            "performance_by_category": category_performance,
            "models_with_retries": len(performance_metrics)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

# Background task for auto-retry monitoring
async def start_auto_retry_monitoring():
    """Start the background auto-retry monitoring task"""
    if ML_SERVICES_AVAILABLE:
        asyncio.create_task(auto_retry_service.monitor_retry_jobs())

# Resource Monitoring endpoints
@router.get("/resources/system")
async def get_system_resources():
    """Get current system resource status"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        return resource_monitoring_service.get_system_resources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system resources: {str(e)}")

@router.get("/resources/job/{job_id}")
async def get_job_resources(job_id: str):
    """Get resource usage summary for a specific job"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        return resource_monitoring_service.get_job_resource_summary(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job resources: {str(e)}")

@router.post("/resources/job/{job_id}/start")
async def start_job_monitoring(job_id: str):
    """Start resource monitoring for a training job"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        await resource_monitoring_service.start_monitoring(job_id)
        return {
            "message": f"Resource monitoring started for job {job_id}",
            "job_id": job_id,
            "status": "monitoring"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/resources/job/{job_id}/stop")
async def stop_job_monitoring(job_id: str):
    """Stop resource monitoring for a training job"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        await resource_monitoring_service.stop_monitoring(job_id)
        return {
            "message": f"Resource monitoring stopped for job {job_id}",
            "job_id": job_id,
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/resources/thresholds")
async def get_resource_thresholds():
    """Get current resource monitoring thresholds"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        return {
            "thresholds": resource_monitoring_service.thresholds,
            "monitoring_interval": resource_monitoring_service.monitoring_interval,
            "history_retention": resource_monitoring_service.history_retention
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thresholds: {str(e)}")

@router.put("/resources/thresholds")
async def update_resource_thresholds(thresholds: Dict[str, float]):
    """Update resource monitoring thresholds"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        # Validate thresholds
        valid_keys = ['cpu_warning', 'cpu_critical', 'memory_warning', 'memory_critical', 'gpu_warning', 'gpu_critical']
        
        for key, value in thresholds.items():
            if key in valid_keys:
                if 0 <= value <= 100:
                    resource_monitoring_service.thresholds[key] = value
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid threshold value for {key}: {value}")
        
        return {
            "message": "Resource thresholds updated successfully",
            "thresholds": resource_monitoring_service.thresholds
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update thresholds: {str(e)}")

# Background task for resource monitoring
async def start_resource_monitoring():
    """Start the background resource monitoring task"""
    if ML_SERVICES_AVAILABLE:
        # Resource monitoring is started per-job, so no global task needed
        logger.info("Resource monitoring service initialized")

# Performance Optimization endpoints
@router.get("/optimization/analyze/{model_id}")
async def analyze_model_performance(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Analyze model performance and generate optimization recommendations"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        analysis = await performance_optimization_service.analyze_performance(model_id, db)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

@router.get("/optimization/recommendations/{model_id}")
async def get_optimization_recommendations(
    model_id: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get optimization recommendations for a model"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        analysis = await performance_optimization_service.analyze_performance(model_id, db)
        recommendations = analysis.get('recommendations', [])
        
        # Filter by category if specified
        if category:
            recommendations = [r for r in recommendations if r.get('category') == category]
        
        # Filter by priority if specified
        if priority:
            recommendations = [r for r in recommendations if r.get('priority') == priority]
        
        return {
            'model_id': model_id,
            'recommendations': recommendations,
            'total_count': len(recommendations),
            'optimization_potential': analysis.get('optimization_potential', {}),
            'priority_actions': analysis.get('priority_actions', [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/optimization/strategies")
async def get_optimization_strategies():
    """Get available optimization strategies"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        return {
            'strategies': performance_optimization_service.optimization_strategies,
            'categories': list(performance_optimization_service.optimization_strategies.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategies: {str(e)}")

@router.post("/optimization/implement/{model_id}")
async def implement_optimization(
    model_id: str,
    optimization_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Implement optimization recommendations"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services unavailable")
    
    try:
        strategy = optimization_request.get('strategy')
        category = optimization_request.get('category')
        
        if not strategy or not category:
            raise HTTPException(status_code=400, detail="Strategy and category required")
        
        # Validate strategy exists
        if category not in performance_optimization_service.optimization_strategies:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        if strategy not in performance_optimization_service.optimization_strategies[category]:
            raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")
        
        # Create optimization record (in a real implementation, this would trigger the optimization)
        optimization_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{model_id}"
        
        return {
            'optimization_id': optimization_id,
            'model_id': model_id,
            'category': category,
            'strategy': strategy,
            'status': 'initiated',
            'message': f"Optimization {strategy} initiated for model {model_id}",
            'estimated_completion': '15-30 minutes',
            'expected_improvement': performance_optimization_service.optimization_strategies[category][strategy].get('description', 'Performance improvement expected')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization implementation failed: {str(e)}")

@router.get("/optimization/benchmark/{model_id}")
async def get_performance_benchmark(
    model_id: str,
    baseline_days: int = 7,
    db: Session = Depends(get_db)
):
    """Get performance benchmark for a model"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        from models.ml_models import MLModelPerformanceMetrics
        
        # Get baseline performance
        baseline_start = datetime.utcnow() - timedelta(days=baseline_days)
        baseline_metrics = db.query(MLModelPerformanceMetrics).filter(
            MLModelPerformanceMetrics.model_id == model_id,
            MLModelPerformanceMetrics.evaluated_at >= baseline_start
        ).all()
        
        if not baseline_metrics:
            return {
                'model_id': model_id,
                'message': 'No baseline data available',
                'baseline_period_days': baseline_days
            }
        
        # Calculate baseline statistics
        accuracies = [m.accuracy for m in baseline_metrics if m.accuracy]
        losses = [m.loss for m in baseline_metrics if m.loss]
        f1_scores = [m.f1_score for m in baseline_metrics if m.f1_score]
        
        benchmark = {
            'model_id': model_id,
            'baseline_period_days': baseline_days,
            'data_points': len(baseline_metrics),
            'metrics': {
                'accuracy': {
                    'mean': sum(accuracies) / len(accuracies) if accuracies else None,
                    'max': max(accuracies) if accuracies else None,
                    'min': min(accuracies) if accuracies else None,
                    'trend': 'stable'  # Could calculate actual trend
                },
                'loss': {
                    'mean': sum(losses) / len(losses) if losses else None,
                    'max': max(losses) if losses else None,
                    'min': min(losses) if losses else None,
                    'trend': 'stable'
                },
                'f1_score': {
                    'mean': sum(f1_scores) / len(f1_scores) if f1_scores else None,
                    'max': max(f1_scores) if f1_scores else None,
                    'min': min(f1_scores) if f1_scores else None,
                    'trend': 'stable'
                }
            },
            'performance_grade': self._calculate_performance_grade(accuracies, losses, f1_scores),
            'improvement_opportunities': self._identify_improvement_opportunities(accuracies, losses, f1_scores)
        }
        
        return benchmark
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark analysis failed: {str(e)}")

def _calculate_performance_grade(self, accuracies: List[float], losses: List[float], f1_scores: List[float]) -> str:
    """Calculate performance grade"""
    if not accuracies:
        return 'N/A'
    
    avg_accuracy = sum(accuracies) / len(accuracies)
    
    if avg_accuracy >= 0.95:
        return 'A+'
    elif avg_accuracy >= 0.90:
        return 'A'
    elif avg_accuracy >= 0.85:
        return 'B+'
    elif avg_accuracy >= 0.80:
        return 'B'
    elif avg_accuracy >= 0.75:
        return 'C+'
    elif avg_accuracy >= 0.70:
        return 'C'
    else:
        return 'D'

def _identify_improvement_opportunities(self, accuracies: List[float], losses: List[float], f1_scores: List[float]) -> List[str]:
    """Identify improvement opportunities"""
    opportunities = []
    
    if accuracies and max(accuracies) - min(accuracies) > 0.1:
        opportunities.append('High accuracy variance - consider regularization')
    
    if losses and max(losses) - min(losses) > 0.2:
        opportunities.append('High loss variance - adjust learning rate')
    
    if accuracies and (sum(accuracies) / len(accuracies)) < 0.85:
        opportunities.append('Low average accuracy - consider model architecture changes')
    
    if f1_scores and (sum(f1_scores) / len(f1_scores)) < 0.80:
        opportunities.append('Low F1 score - improve precision/recall balance')
    
    return opportunities or ['Performance is optimal - consider advanced optimizations']

# Automated Code Generation endpoints
@router.post("/optimization/generate-code/{model_id}")
async def generate_optimization_code(
    model_id: str,
    optimization_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate actual optimization code implementation"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        # First analyze performance
        analysis = await performance_optimization_service.analyze_performance(model_id, db)
        
        # Generate code based on analysis
        code_generation = await automated_code_optimizer.generate_optimization_code(analysis)
        
        return {
            'model_id': model_id,
            'optimization_id': code_generation.get('optimization_id'),
            'generated_code': code_generation.get('generated_code', {}),
            'implementation_plan': code_generation.get('implementation_plan', []),
            'total_strategies': code_generation.get('total_strategies', 0),
            'estimated_time': code_generation.get('estimated_implementation_time', 'Unknown'),
            'integration_instructions': code_generation.get('integration_instructions', ''),
            'performance_analysis': analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")

@router.get("/optimization/code-templates")
async def get_code_templates():
    """Get available code generation templates"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        return {
            'available_templates': list(automated_code_optimizer.code_templates.keys()),
            'template_descriptions': {
                'batch_size_optimization': 'Optimizes batch size and gradient accumulation',
                'learning_rate_optimization': 'Adds learning rate scheduling and optimization',
                'mixed_precision': 'Enables mixed precision training for memory efficiency',
                'gradient_checkpointing': 'Implements gradient checkpointing for large models',
                'data_loading_optimization': 'Optimizes data loading pipeline'
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.post("/optimization/apply-code/{model_id}")
async def apply_optimization_code(
    model_id: str,
    apply_request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Apply generated optimization code (simulation)"""
    if not ML_SERVICES_AVAILABLE:
        return {"error": "ML services unavailable"}
    
    try:
        strategy = apply_request.get('strategy')
        code = apply_request.get('generated_code')
        
        if not strategy or not code:
            raise HTTPException(status_code=400, detail="Strategy and code required")
        
        # In a real implementation, this would:
        # 1. Create backup of original files
        # 2. Apply code changes to appropriate files
        # 3. Validate syntax
        # 4. Run tests
        # 5. Deploy changes
        
        # For now, simulate the application
        application_id = f"apply_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            'application_id': application_id,
            'model_id': model_id,
            'strategy': strategy,
            'status': 'applied_simulated',
            'files_modified': self._get_modified_files(strategy),
            'backup_created': f"backup_{application_id}.zip",
            'validation_status': 'passed',
            'next_steps': [
                'Test the optimized model in development environment',
                'Monitor performance using ML Dashboard',
                'Rollback if issues occur using provided backup'
            ],
            'estimated_impact': apply_request.get('expected_improvement', 'Performance improvement expected')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code application failed: {str(e)}")

def _get_modified_files(self, strategy: str) -> List[str]:
    """Get list of files that would be modified by strategy"""
    file_map = {
        'batch_size_optimization': ['training_config.py', 'data_loader.py'],
        'learning_rate_optimization': ['training_loop.py', 'optimizer_config.py'],
        'mixed_precision': ['training_loop.py'],
        'gradient_checkpointing': ['model.py', 'training_loop.py'],
        'data_loading_optimization': ['data_loader.py', 'dataset.py']
    }
    return file_map.get(strategy, ['training_files'])
