"""
ML Training API Endpoints
Allows training ML models via API for scheduled retraining
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime

from core.database_unified import get_db
from core.auth_dependencies import get_current_active_user, User
from sqlalchemy.orm import Session
from schemas.responses import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml-training", tags=["ML Training"])

# Import training script components
import sys
import os
# Get project root (go up from backend/api/routes to project root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from scripts.train_ml_models import MLModelTrainer, TRAINING_SYMBOLS
except ImportError as e:
    # If ML training module is not available, create a stub
    logger = logging.getLogger(__name__)
    logger.warning(f"ML training module not available: {e}. ML training endpoints will be disabled.")
    MLModelTrainer = None
    TRAINING_SYMBOLS = []

# Global training status
training_status = {
    "is_training": False,
    "last_training": None,
    "training_results": None,
    "error": None
}

@router.get("/status", response_model=APIResponse[Dict[str, Any]])
async def get_training_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get current training status"""
    try:
        return APIResponse(
            success=True,
            message="Training status retrieved",
            data=training_status
        )
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/all", response_model=APIResponse[Dict[str, Any]])
async def train_all_models(
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Train all ML models"""
    try:
        if MLModelTrainer is None:
            raise HTTPException(
                status_code=503,
                detail="ML training module is not available. Please ensure scripts/train_ml_models.py exists."
            )
        
        if training_status["is_training"]:
            raise HTTPException(
                status_code=400,
                detail="Training is already in progress"
            )
        
        # Use provided symbols or default
        training_symbols = symbols or TRAINING_SYMBOLS
        
        # Start training in background
        training_status["is_training"] = True
        training_status["error"] = None
        
        def training_task():
            try:
                trainer = MLModelTrainer()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(trainer.train_all_models(training_symbols))
                loop.close()
                
                training_status["is_training"] = False
                training_status["last_training"] = datetime.now().isoformat()
                training_status["training_results"] = results
                training_status["error"] = None
            except Exception as e:
                logger.error(f"Training error: {e}")
                training_status["is_training"] = False
                training_status["error"] = str(e)
        
        background_tasks.add_task(training_task)
        
        return APIResponse(
            success=True,
            message="Training started in background",
            data={
                "status": "started",
                "symbols": training_symbols,
                "estimated_time_minutes": 30
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        training_status["is_training"] = False
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/{model_type}", response_model=APIResponse[Dict[str, Any]])
async def train_specific_model(
    model_type: str,
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Train a specific model type"""
    try:
        if MLModelTrainer is None:
            raise HTTPException(
                status_code=503,
                detail="ML training module is not available. Please ensure scripts/train_ml_models.py exists."
            )
        
        if training_status["is_training"]:
            raise HTTPException(
                status_code=400,
                detail="Training is already in progress"
            )
        
        valid_types = ["ai_engine", "gradient_boosting", "temporal", "meta_learner"]
        if model_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type. Valid types: {', '.join(valid_types)}"
            )
        
        training_symbols = symbols or TRAINING_SYMBOLS
        
        training_status["is_training"] = True
        training_status["error"] = None
        
        def training_task():
            try:
                trainer = MLModelTrainer()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                if model_type == "ai_engine":
                    results = loop.run_until_complete(trainer.train_ai_engine(training_symbols))
                elif model_type == "gradient_boosting":
                    results = loop.run_until_complete(trainer.train_gradient_boosting(training_symbols))
                elif model_type == "temporal":
                    results = loop.run_until_complete(trainer.train_temporal_models(training_symbols))
                elif model_type == "meta_learner":
                    results = loop.run_until_complete(trainer.train_meta_learner(training_symbols))
                
                loop.close()
                
                training_status["is_training"] = False
                training_status["last_training"] = datetime.now().isoformat()
                training_status["training_results"] = {model_type: results}
                training_status["error"] = None
            except Exception as e:
                logger.error(f"Training error: {e}")
                training_status["is_training"] = False
                training_status["error"] = str(e)
        
        background_tasks.add_task(training_task)
        
        return APIResponse(
            success=True,
            message=f"Training {model_type} started in background",
            data={
                "status": "started",
                "model_type": model_type,
                "symbols": training_symbols
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        training_status["is_training"] = False
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/performance", response_model=APIResponse[Dict[str, Any]])
async def get_models_performance(
    model_name: Optional[str] = None,
    days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get performance metrics for all trained models"""
    try:
        from services.model_monitoring import model_monitoring
        
        if model_name:
            # Get performance for specific model
            evaluation = model_monitoring.evaluate_predictions(model_name, days=days)
            degradation = model_monitoring.check_model_degradation(model_name)
            
            return APIResponse(
                success=True,
                message=f"Performance metrics for {model_name}",
                data={
                    "model_name": model_name,
                    "evaluation": evaluation,
                    "degradation_check": degradation
                }
            )
        else:
            # Get performance report for all models
            report = model_monitoring.generate_performance_report()
            
            return APIResponse(
                success=True,
                message="Performance report generated",
                data=report
            )
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

