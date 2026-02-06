"""
ML Configuration Manager
Handles loading and managing ML configuration from YAML files and environment variables
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    default_hyperparameters: Dict[str, Any] = field(default_factory=dict)
    hyperparameter_optimization: Dict[str, Any] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DriftDetectionConfig:
    methods: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    data_quality: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMonitoringConfig:
    metrics: Dict[str, Any] = field(default_factory=dict)
    evaluation: Dict[str, Any] = field(default_factory=dict)
    benchmarks: Dict[str, Any] = field(default_factory=dict)
    alerts: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelRegistryConfig:
    storage: Dict[str, Any] = field(default_factory=dict)
    deployment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ABTestingConfig:
    experiments: Dict[str, Any] = field(default_factory=dict)
    traffic_allocation: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    decision_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MLConfig:
    training: TrainingConfig = field(default_factory=TrainingConfig)
    drift_detection: DriftDetectionConfig = field(default_factory=DriftDetectionConfig)
    performance_monitoring: PerformanceMonitoringConfig = field(default_factory=PerformanceMonitoringConfig)
    model_registry: ModelRegistryConfig = field(default_factory=ModelRegistryConfig)
    ab_testing: ABTestingConfig = field(default_factory=ABTestingConfig)
    environments: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    notifications: Dict[str, Any] = field(default_factory=dict)
    caching: Dict[str, Any] = field(default_factory=dict)

class MLConfigManager:
    """Manages ML configuration loading and access"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[MLConfig] = None
        load_dotenv()  # Load environment variables
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Try multiple locations
        possible_paths = [
            "config/ml_config.yaml",
            "config/ml_config.yml", 
            "../config/ml_config.yaml",
            "../../config/ml_config.yaml",
            os.path.join(os.path.dirname(__file__), "../config/ml_config.yaml")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Fallback to current directory
        return "config/ml_config.yaml"
    
    def load_config(self) -> MLConfig:
        """Load configuration from YAML file and environment variables"""
        if self._config is not None:
            return self._config
            
        try:
            # Load YAML configuration
            config_data = self._load_yaml_config()
            
            # Override with environment variables
            config_data = self._override_with_env_vars(config_data)
            
            # Create configuration objects
            self._config = self._create_config_objects(config_data)
            
            logger.info(f"ML configuration loaded from {self.config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load ML configuration: {str(e)}")
            # Return default configuration
            self._config = MLConfig()
            return self._config
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found: {self.config_path}")
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
            return {}
    
    def _override_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration values with environment variables"""
        
        # Environment variable mappings
        env_mappings = {
            # Training
            "ML_TRAINING_BATCH_SIZE": ("training", "default_hyperparameters", "batch_size"),
            "ML_TRAINING_LEARNING_RATE": ("training", "default_hyperparameters", "learning_rate"),
            "ML_TRAINING_EPOCHS": ("training", "default_hyperparameters", "epochs"),
            "ML_TRAINING_MAX_CPU_CORES": ("training", "resource_limits", "max_cpu_cores"),
            "ML_TRAINING_MAX_MEMORY_GB": ("training", "resource_limits", "max_memory_gb"),
            
            # Hyperparameter optimization
            "ML_OPTUNA_N_TRIALS": ("training", "hyperparameter_optimization", "n_trials"),
            "ML_OPTUNA_TIMEOUT_SECONDS": ("training", "hyperparameter_optimization", "timeout_seconds"),
            "ML_OPTUNA_OBJECTIVE_METRIC": ("training", "hyperparameter_optimization", "objective_metric"),
            
            # Drift detection
            "ML_DRIFT_CHECK_INTERVAL_HOURS": ("drift_detection", "monitoring", "check_interval_hours"),
            "ML_DRIFT_ALERT_THRESHOLD": ("drift_detection", "monitoring", "alert_threshold"),
            "ML_DRIFT_SIGNIFICANCE_THRESHOLD": ("drift_detection", "methods", "statistical_tests", "significance_threshold"),
            
            # Performance monitoring
            "ML_PERFORMANCE_BACKTEST_PERIOD_DAYS": ("performance_monitoring", "evaluation", "backtest_period_days"),
            "ML_PERFORMANCE_DEGRADATION_THRESHOLD": ("performance_monitoring", "alerts", "performance_degradation_threshold"),
            
            # Model registry
            "ML_REGISTRY_BASE_PATH": ("model_registry", "storage", "base_path"),
            "ML_REGISTRY_MAX_VERSIONS": ("model_registry", "storage", "max_versions_per_model"),
            
            # A/B testing
            "ML_ABTEST_MAX_CONCURRENT": ("ab_testing", "experiments", "max_concurrent_experiments"),
            "ML_ABTEST_DEFAULT_DURATION": ("ab_testing", "experiments", "default_duration_days"),
            "ML_ABTEST_SIGNIFICANCE_LEVEL": ("ab_testing", "statistics", "significance_level"),
            
            # Database
            "ML_DATABASE_URL": ("environments", os.getenv("ENVIRONMENT", "development"), "database_url"),
            
            # Logging
            "ML_LOG_LEVEL": ("logging", "level"),
            "ML_LOG_FILE_PATH": ("logging", "file_path"),
            
            # Security
            "ML_RATE_LIMIT_TRAINING": ("security", "rate_limiting", "training_requests_per_hour"),
            "ML_RATE_LIMIT_DRIFT": ("security", "rate_limiting", "drift_detection_requests_per_hour"),
            
            # Notifications
            "ML_EMAIL_ENABLED": ("notifications", "channels", "email", "enabled"),
            "ML_SMTP_SERVER": ("notifications", "channels", "email", "smtp_server"),
            "ML_SMTP_PORT": ("notifications", "channels", "email", "smtp_port"),
            
            # Caching
            "ML_REDIS_ENABLED": ("caching", "redis", "enabled"),
            "ML_REDIS_HOST": ("caching", "redis", "host"),
            "ML_REDIS_PORT": ("caching", "redis", "port"),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string to appropriate type
                converted_value = self._convert_env_value(value)
                
                # Set nested configuration value
                self._set_nested_value(config, config_path, converted_value)
        
        return config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Try to convert to boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: tuple, value: Any):
        """Set nested configuration value"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _create_config_objects(self, config_data: Dict[str, Any]) -> MLConfig:
        """Create configuration objects from loaded data"""
        
        # Extract configuration sections with defaults
        training_data = config_data.get('training', {})
        drift_data = config_data.get('drift_detection', {})
        perf_data = config_data.get('performance_monitoring', {})
        registry_data = config_data.get('model_registry', {})
        abtest_data = config_data.get('ab_testing', {})
        
        return MLConfig(
            training=TrainingConfig(
                default_hyperparameters=training_data.get('default_hyperparameters', {}),
                hyperparameter_optimization=training_data.get('hyperparameter_optimization', {}),
                resource_limits=training_data.get('resource_limits', {}),
                data=training_data.get('data', {}),
                models=training_data.get('models', {})
            ),
            drift_detection=DriftDetectionConfig(
                methods=drift_data.get('methods', {}),
                monitoring=drift_data.get('monitoring', {}),
                data_quality=drift_data.get('data_quality', {})
            ),
            performance_monitoring=PerformanceMonitoringConfig(
                metrics=perf_data.get('metrics', {}),
                evaluation=perf_data.get('evaluation', {}),
                benchmarks=perf_data.get('benchmarks', {}),
                alerts=perf_data.get('alerts', {})
            ),
            model_registry=ModelRegistryConfig(
                storage=registry_data.get('storage', {}),
                deployment=registry_data.get('deployment', {}),
                metadata=registry_data.get('metadata', {})
            ),
            ab_testing=ABTestingConfig(
                experiments=abtest_data.get('experiments', {}),
                traffic_allocation=abtest_data.get('traffic_allocation', {}),
                statistics=abtest_data.get('statistics', {}),
                success_metrics=abtest_data.get('success_metrics', {}),
                decision_rules=abtest_data.get('decision_rules', {})
            ),
            environments=config_data.get('environments', {}),
            logging=config_data.get('logging', {}),
            security=config_data.get('security', {}),
            notifications=config_data.get('notifications', {}),
            caching=config_data.get('caching', {})
        )
    
    def get_config(self) -> MLConfig:
        """Get loaded configuration"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> MLConfig:
        """Reload configuration from file"""
        self._config = None
        return self.load_config()
    
    def get_environment_config(self, environment: str = None) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        config = self.get_config()
        environment = environment or os.getenv('ENVIRONMENT', 'development')
        return config.environments.get(environment, {})
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'

# Global configuration manager instance
ml_config_manager = MLConfigManager()

def get_ml_config() -> MLConfig:
    """Get ML configuration (singleton)"""
    return ml_config_manager.get_config()

def reload_ml_config() -> MLConfig:
    """Reload ML configuration"""
    return ml_config_manager.reload_config()
