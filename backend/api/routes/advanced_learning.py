"""
Advanced Learning API Routes
Endpoints for automatic model retraining, feature selection, algorithm selection, and parameter tuning
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from core.database_unified import get_db, User
from core.auth_dependencies import get_current_active_user
from services.automatic_model_retraining import automatic_model_retraining
from services.dynamic_feature_selection import dynamic_feature_selection
from services.adaptive_algorithm_selection import adaptive_algorithm_selection
from services.realtime_parameter_tuning import realtime_parameter_tuning
from services.advanced_learning_coordinator import advanced_learning_coordinator

router = APIRouter()

# Request Models
class ModelRetrainingRequest(BaseModel):
    model_name: str
    performance_metrics: Dict[str, float]
    new_data_available: bool = False

class FeatureSelectionRequest(BaseModel):
    model_name: str
    method: Optional[str] = 'auto'  # 'auto', 'univariate', 'mutual_info', 'rfe', 'importance'
    n_features: Optional[int] = None
    task_type: str = 'regression'  # 'regression' or 'classification'

class AlgorithmSelectionRequest(BaseModel):
    symbol: str
    algorithm_performances: Optional[Dict[str, Dict[str, float]]] = None

class ParameterTuningRequest(BaseModel):
    model_name: str
    current_performance: Dict[str, float]
    optimization_target: str = 'accuracy'  # 'accuracy', 'mse', 'sharpe'
    parameter_bounds: Optional[Dict[str, tuple]] = None

class ThresholdAdjustmentRequest(BaseModel):
    threshold_name: str  # 'confidence_threshold', 'stop_loss_percent', 'take_profit_percent'
    current_value: float
    performance_feedback: Dict[str, float]
    adjustment_rate: float = 0.1

# Automatic Model Retraining Endpoints
@router.post("/model-retraining/check")
async def check_model_retraining(
    request: ModelRetrainingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if model needs retraining"""
    try:
        # Update performance history
        automatic_model_retraining.update_performance_history(
            request.model_name,
            request.performance_metrics
        )
        
        # Get retraining status
        status = automatic_model_retraining.get_retraining_status(request.model_name)
        
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/model-retraining/retrain")
async def retrain_model(
    request: ModelRetrainingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrain model if needed"""
    try:
        # Note: In practice, you'd load the actual model and new data here
        # This is a simplified version
        
        result = automatic_model_retraining.check_and_retrain(
            model_name=request.model_name,
            model_instance=None,  # Would be loaded from storage
            performance_metrics=request.performance_metrics,
            new_data=None  # Would be loaded from database
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dynamic Feature Selection Endpoints
@router.post("/feature-selection/select")
async def select_features(
    request: FeatureSelectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Select best features for a model"""
    try:
        # Note: In practice, you'd load X and y from database
        # This is a placeholder - actual implementation would fetch data
        
        result = {
            "success": False,
            "message": "Feature selection requires data. Use with actual data in production."
        }
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feature-selection/features/{model_name}")
async def get_selected_features(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get currently selected features for a model"""
    try:
        features = dynamic_feature_selection.get_selected_features(model_name)
        importance = dynamic_feature_selection.get_feature_importance(model_name)
        
        return {
            "success": True,
            "data": {
                "model_name": model_name,
                "selected_features": features,
                "feature_importance": importance
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Adaptive Algorithm Selection Endpoints
@router.post("/algorithm-selection/select")
async def select_algorithm(
    request: AlgorithmSelectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Select best algorithm for a symbol"""
    try:
        result = adaptive_algorithm_selection.select_best_algorithm(
            symbol=request.symbol,
            algorithm_performances=request.algorithm_performances
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/algorithm-selection/recommendations/{symbol}")
async def get_algorithm_recommendations(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get algorithm recommendations for a symbol"""
    try:
        recommendations = adaptive_algorithm_selection.get_algorithm_recommendations(symbol)
        
        return {
            "success": True,
            "data": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Parameter Tuning Endpoints
@router.post("/parameter-tuning/optimize")
async def optimize_parameters(
    request: ParameterTuningRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimize model parameters"""
    try:
        result = realtime_parameter_tuning.optimize_parameters(
            model_name=request.model_name,
            current_performance=request.current_performance,
            parameter_bounds=request.parameter_bounds,
            optimization_target=request.optimization_target
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameter-tuning/adjust-threshold")
async def adjust_threshold(
    request: ThresholdAdjustmentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Adjust a threshold based on performance"""
    try:
        result = realtime_parameter_tuning.adjust_threshold(
            threshold_name=request.threshold_name,
            current_value=request.current_value,
            performance_feedback=request.performance_feedback,
            adjustment_rate=request.adjustment_rate
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parameter-tuning/parameters/{model_name}")
async def get_current_parameters(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current parameters for a model"""
    try:
        parameters = realtime_parameter_tuning.get_current_parameters(model_name)
        history = realtime_parameter_tuning.get_parameter_history(model_name, days=7)
        
        return {
            "success": True,
            "data": {
                "model_name": model_name,
                "current_parameters": parameters,
                "recent_history": history
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unified Status Endpoint
@router.get("/status")
async def get_advanced_learning_status(
    symbol: Optional[str] = None,
    model_name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive status of all advanced learning features"""
    try:
        result = advanced_learning_coordinator.get_comprehensive_status(
            symbol=symbol,
            model_name=model_name
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning-cycle")
async def process_learning_cycle(
    symbol: str = Body(...),
    model_name: str = Body(...),
    performance_metrics: Dict[str, float] = Body(...),
    context: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process a complete learning cycle"""
    try:
        result = advanced_learning_coordinator.process_learning_cycle(
            symbol=symbol,
            model_name=model_name,
            performance_metrics=performance_metrics,
            context=context
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

