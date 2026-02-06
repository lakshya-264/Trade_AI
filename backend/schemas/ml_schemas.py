"""
Pydantic schemas for ML-related endpoints
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    INITIAL_TRAINING = "initial_training"
    RETRAINING = "retraining"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DriftType(str, Enum):
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    PERFORMANCE_DRIFT = "performance_drift"

class DriftStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"

class EvaluationType(str, Enum):
    BACKTEST = "backtest"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"

class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    REINFORCEMENT_LEARNING = "reinforcement_learning"

class ExperimentStatus(str, Enum):
    SETUP = "setup"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

# Training Job Schemas

class TrainingJobCreate(BaseModel):
    model_id: str = Field(..., description="Unique identifier for the model")
    model_version: str = Field(..., description="Version of the model")
    job_type: JobType = Field(..., description="Type of training job")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Training hyperparameters")
    validation_split: float = Field(0.2, ge=0.0, le=1.0, description="Validation data split ratio")
    created_by: Optional[str] = Field(None, description="User who created the job")

class TrainingJobResponse(BaseModel):
    id: int
    job_id: str
    model_id: str
    model_version: str
    job_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    hyperparameters: Optional[Dict[str, Any]]
    training_metrics: Optional[Dict[str, Any]]
    validation_metrics: Optional[Dict[str, Any]]
    test_metrics: Optional[Dict[str, Any]]
    model_path: Optional[str]
    model_size_mb: Optional[float]
    training_duration_seconds: Optional[int]
    error_message: Optional[str]
    created_by: Optional[str]
    environment: str
    tags: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)

# Drift Detection Schemas

class DriftDetectionResponse(BaseModel):
    id: int
    model_id: str
    model_version: str
    drift_score: float
    drift_type: str
    drift_metrics: Optional[Dict[str, Any]]
    detected_at: datetime
    resolved_at: Optional[datetime]
    status: str
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class DriftMetrics(BaseModel):
    feature_drift_scores: Dict[str, float]
    overall_drift_score: float
    statistical_tests: Dict[str, Any]
    data_distribution_changes: Dict[str, Any]

# Performance Metrics Schemas

class PerformanceMetricsResponse(BaseModel):
    id: int
    model_id: str
    model_version: str
    evaluated_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Trading performance
    total_return: Optional[float]
    annualized_return: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]
    profit_factor: Optional[float]
    avg_trade_return: Optional[float]
    volatility: Optional[float]
    
    # Model prediction metrics
    prediction_accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    roc_auc: Optional[float]
    
    # Data quality
    data_quality_score: Optional[float]
    missing_data_percentage: Optional[float]
    outlier_percentage: Optional[float]
    
    # Market conditions
    market_regime: Optional[str]
    volatility_regime: Optional[str]
    
    # Trading statistics
    total_trades: Optional[int]
    winning_trades: Optional[int]
    losing_trades: Optional[int]
    avg_holding_period_days: Optional[float]
    
    # Risk metrics
    var_95: Optional[float]
    cvar_95: Optional[float]
    beta: Optional[float]
    alpha: Optional[float]
    
    # Metadata
    evaluation_type: str
    benchmark: Optional[str]
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class PerformanceSummary(BaseModel):
    model_id: str
    model_version: str
    latest_metrics: PerformanceMetricsResponse
    trend_analysis: Dict[str, str]  # "improving", "declining", "stable"
    performance_vs_baseline: Dict[str, float]
    recommendations: List[str]

# Model Registry Schemas

class ModelRegistryCreate(BaseModel):
    model_id: str = Field(..., description="Unique identifier for the model")
    model_name: str = Field(..., description="Human-readable model name")
    model_type: ModelType = Field(..., description="Type of model")
    current_version: str = Field(..., description="Current version of the model")
    description: Optional[str] = Field(None, description="Model description")
    input_features: List[str] = Field(..., description="List of input features")
    output_features: List[str] = Field(..., description="List of output features")
    created_by: Optional[str] = Field(None, description="User who registered the model")

class ModelRegistryResponse(BaseModel):
    id: int
    model_id: str
    model_name: str
    model_type: str
    current_version: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    input_features: List[str]
    output_features: List[str]
    is_deployed: bool
    deployment_environment: Optional[str]
    deployment_endpoint: Optional[str]
    deployed_at: Optional[datetime]
    best_validation_metric: Optional[float]
    best_test_metric: Optional[float]
    latest_drift_score: Optional[float]
    tags: Optional[List[str]]
    labels: Optional[Dict[str, str]]

    model_config = ConfigDict(from_attributes=True)

class ModelDeploymentRequest(BaseModel):
    environment: str = Field(..., pattern="^(development|staging|production)$")
    deployment_endpoint: Optional[str] = Field(None, description="Custom deployment endpoint")
    rollback_version: Optional[str] = Field(None, description="Version to rollback to if needed")

# A/B Testing Schemas

class ABTestExperimentCreate(BaseModel):
    name: str = Field(..., description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    control_model_id: str = Field(..., description="Control model ID")
    control_model_version: str = Field(..., description="Control model version")
    treatment_model_id: str = Field(..., description="Treatment model ID")
    treatment_model_version: str = Field(..., description="Treatment model version")
    primary_metric: str = Field(..., description="Primary success metric")
    significance_level: float = Field(0.05, ge=0.01, le=0.1, description="Statistical significance level")
    minimum_detectable_effect: Optional[float] = Field(None, description="Minimum effect size to detect")
    traffic_split_control: float = Field(0.5, ge=0.0, le=1.0, description="Traffic split for control")
    created_by: Optional[str] = Field(None, description="User who created the experiment")

    @field_validator('traffic_split_control')
    @classmethod
    def validate_traffic_split(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Traffic split must be between 0 and 1')
        return v

class ABTestExperimentResponse(BaseModel):
    id: int
    experiment_id: str
    name: str
    description: Optional[str]
    control_model_id: str
    control_model_version: str
    treatment_model_id: str
    treatment_model_version: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_days: Optional[int]
    status: str
    traffic_split_control: float
    traffic_split_treatment: float
    primary_metric: str
    significance_level: float
    minimum_detectable_effect: Optional[float]
    control_metrics: Optional[Dict[str, Any]]
    treatment_metrics: Optional[Dict[str, Any]]
    statistical_significance: Optional[bool]
    confidence_interval: Optional[List[float]]
    effect_size: Optional[float]
    p_value: Optional[float]
    winner: Optional[str]
    decision_reason: Optional[str]
    decided_at: Optional[datetime]
    created_by: Optional[str]
    tags: Optional[List[str]]
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class ABTestResults(BaseModel):
    experiment_id: str
    winner: str
    statistical_significance: bool
    confidence_interval: List[float]
    effect_size: float
    p_value: float
    control_performance: Dict[str, float]
    treatment_performance: Dict[str, float]
    recommendation: str
    decision_reason: str

# Configuration Schemas

class MLConfig(BaseModel):
    training: Dict[str, Any] = Field(default_factory=dict)
    drift_detection: Dict[str, Any] = Field(default_factory=dict)
    performance_monitoring: Dict[str, Any] = Field(default_factory=dict)
    model_registry: Dict[str, Any] = Field(default_factory=dict)
    ab_testing: Dict[str, Any] = Field(default_factory=dict)

class HyperparameterConfig(BaseModel):
    optimization_method: str = Field("optuna", description="Optimization method: optuna, hyperopt, grid_search")
    n_trials: int = Field(100, ge=1, description="Number of optimization trials")
    timeout_seconds: Optional[int] = Field(None, ge=1, description="Timeout for optimization")
    parameters: Dict[str, Any] = Field(..., description="Parameter search space")
    objective_metric: str = Field(..., description="Metric to optimize")
    direction: str = Field("maximize", pattern="^(maximize|minimize)$", description="Optimization direction")

# Monitoring Schemas

class MonitoringAlert(BaseModel):
    alert_id: str
    model_id: str
    alert_type: str  # drift, performance_degradation, training_failure
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

class DashboardMetrics(BaseModel):
    total_models: int
    active_training_jobs: int
    recent_drift_alerts: int
    deployed_models: int
    avg_model_performance: float
    system_health: str  # healthy, warning, critical
