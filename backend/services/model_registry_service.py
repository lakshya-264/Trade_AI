"""
Model Registry Service
Centralized model storage, versioning, and deployment management
"""

import os
import json
import shutil
import hashlib
import pickle
import joblib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from sqlalchemy.orm import Session

from models.ml_models import ModelRegistry, TrainingJob
from core.ml_config import get_ml_config
from schemas.ml_schemas import ModelRegistryCreate, ModelRegistryResponse

logger = logging.getLogger(__name__)

class ModelRegistryService:
    """Service for managing model registry, storage, and versioning"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_ml_config()
        self.base_storage_path = Path(self.config.model_registry.storage.get("base_path", "./models"))
        self.max_versions = self.config.model_registry.storage.get("max_versions_per_model", 10)
        
        # Ensure base storage directory exists
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.models_path = self.base_storage_path / "models"
        self.versions_path = self.base_storage_path / "versions"
        self.metadata_path = self.base_storage_path / "metadata"
        self.backups_path = self.base_storage_path / "backups"
        
        for path in [self.models_path, self.versions_path, self.metadata_path, self.backups_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def register_model(self, model_data: ModelRegistryCreate) -> ModelRegistry:
        """Register a new model in the registry"""
        try:
            # Check if model already exists
            existing_model = self.db.query(ModelRegistry).filter(
                ModelRegistry.model_id == model_data.model_id
            ).first()
            
            if existing_model:
                # Update existing model
                existing_model.model_name = model_data.model_name
                existing_model.model_type = model_data.model_type.value
                existing_model.current_version = model_data.current_version
                existing_model.description = model_data.description
                existing_model.input_features = model_data.input_features
                existing_model.output_features = model_data.output_features
                existing_model.updated_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(existing_model)
                logger.info(f"Updated model registry entry: {model_data.model_id}")
                return existing_model
            else:
                # Create new model registry entry
                model_registry = ModelRegistry(
                    model_id=model_data.model_id,
                    model_name=model_data.model_name,
                    model_type=model_data.model_type.value,
                    current_version=model_data.current_version,
                    description=model_data.description,
                    input_features=model_data.input_features,
                    output_features=model_data.output_features,
                    created_by=model_data.created_by,
                    version_history=[{
                        "version": model_data.current_version,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": model_data.created_by
                    }]
                )
                
                self.db.add(model_registry)
                self.db.commit()
                self.db.refresh(model_registry)
                
                # Create model directory structure
                self._create_model_directories(model_data.model_id)
                
                logger.info(f"Registered new model: {model_data.model_id}")
                return model_registry
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to register model {model_data.model_id}: {str(e)}")
            raise
    
    def save_model(self, model_id: str, version: str, model_object: Any, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save a model object to storage"""
        try:
            # Get model registry entry
            model_registry = self.get_model(model_id)
            if not model_registry:
                raise ValueError(f"Model {model_id} not found in registry")
            
            # Create version directory
            version_dir = self.models_path / model_id / version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            # Save model using joblib (supports sklearn, xgboost, etc.)
            model_file = version_dir / "model.joblib"
            joblib.dump(model_object, model_file)
            
            # Calculate file hash
            model_hash = self._calculate_file_hash(model_file)
            
            # Save metadata
            model_metadata = {
                "model_id": model_id,
                "version": version,
                "saved_at": datetime.utcnow().isoformat(),
                "file_hash": model_hash,
                "file_size_bytes": model_file.stat().st_size,
                "file_size_mb": model_file.stat().st_size / (1024 * 1024),
                "model_type": type(model_object).__name__,
                **(metadata or {})
            }
            
            metadata_file = version_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(model_metadata, f, indent=2)
            
            # Update model registry
            model_registry.model_artifact_path = str(model_file)
            model_registry.model_config_path = str(metadata_file)
            
            # Update version history
            version_entry = {
                "version": version,
                "created_at": datetime.utcnow().isoformat(),
                "file_hash": model_hash,
                "file_size_mb": model_metadata["file_size_mb"],
                "metadata": metadata or {}
            }
            
            if model_registry.version_history:
                # Check if version already exists
                existing_versions = [v["version"] for v in model_registry.version_history]
                if version in existing_versions:
                    # Update existing version
                    idx = existing_versions.index(version)
                    model_registry.version_history[idx] = version_entry
                else:
                    # Add new version
                    model_registry.version_history.append(version_entry)
                    # Limit history size
                    if len(model_registry.version_history) > self.max_versions:
                        model_registry.version_history = model_registry.version_history[-self.max_versions:]
            else:
                model_registry.version_history = [version_entry]
            
            self.db.commit()
            
            logger.info(f"Saved model {model_id} version {version} to registry")
            return str(model_file)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save model {model_id} version {version}: {str(e)}")
            raise
    
    def load_model(self, model_id: str, version: Optional[str] = None) -> Any:
        """Load a model from storage"""
        try:
            # Get model registry entry
            model_registry = self.get_model(model_id)
            if not model_registry:
                raise ValueError(f"Model {model_id} not found in registry")
            
            # Determine version to load
            target_version = version or model_registry.current_version
            
            # Construct model file path
            model_file = self.models_path / model_id / target_version / "model.joblib"
            
            if not model_file.exists():
                raise ValueError(f"Model file not found: {model_file}")
            
            # Load model
            model_object = joblib.load(model_file)
            
            logger.info(f"Loaded model {model_id} version {target_version}")
            return model_object
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id} version {version}: {str(e)}")
            raise
    
    def get_model_metadata(self, model_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Get model metadata"""
        try:
            # Get model registry entry
            model_registry = self.get_model(model_id)
            if not model_registry:
                raise ValueError(f"Model {model_id} not found in registry")
            
            # Determine version
            target_version = version or model_registry.current_version
            
            # Load metadata file
            metadata_file = self.models_path / model_id / target_version / "metadata.json"
            
            if not metadata_file.exists():
                return {}
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get metadata for model {model_id} version {version}: {str(e)}")
            return {}
    
    def list_model_versions(self, model_id: str) -> List[str]:
        """List all available versions for a model"""
        try:
            model_dir = self.models_path / model_id
            if not model_dir.exists():
                return []
            
            versions = []
            for item in model_dir.iterdir():
                if item.is_dir():
                    versions.append(item.name)
            
            return sorted(versions, reverse=True)  # Most recent first
            
        except Exception as e:
            logger.error(f"Failed to list versions for model {model_id}: {str(e)}")
            return []
    
    def delete_model_version(self, model_id: str, version: str) -> bool:
        """Delete a specific model version"""
        try:
            # Get model registry entry
            model_registry = self.get_model(model_id)
            if not model_registry:
                raise ValueError(f"Model {model_id} not found in registry")
            
            # Cannot delete current version
            if version == model_registry.current_version:
                raise ValueError("Cannot delete current model version")
            
            # Delete version directory
            version_dir = self.models_path / model_id / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
            
            # Update version history
            if model_registry.version_history:
                model_registry.version_history = [
                    v for v in model_registry.version_history 
                    if v["version"] != version
                ]
            
            self.db.commit()
            
            logger.info(f"Deleted model {model_id} version {version}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete model {model_id} version {version}: {str(e)}")
            return False
    
    def deploy_model(self, model_id: str, environment: str) -> bool:
        """Deploy a model to specified environment"""
        try:
            # Get model registry entry
            model_registry = self.get_model(model_id)
            if not model_registry:
                raise ValueError(f"Model {model_id} not found in registry")
            
            # Validate environment
            valid_environments = self.config.model_registry.deployment.get("environments", [])
            if environment not in valid_environments:
                raise ValueError(f"Invalid environment: {environment}")
            
            # Check deployment criteria
            if not self._check_deployment_criteria(model_registry):
                raise ValueError("Model does not meet deployment criteria")
            
            # Create deployment directory
            deploy_dir = self.base_storage_path / "deployments" / environment / model_id
            deploy_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy current model to deployment directory
            current_version = model_registry.current_version
            source_dir = self.models_path / model_id / current_version
            
            if source_dir.exists():
                # Remove existing deployment
                if deploy_dir.exists():
                    shutil.rmtree(deploy_dir)
                
                # Copy model files
                shutil.copytree(source_dir, deploy_dir)
                
                # Update deployment info
                model_registry.is_deployed = True
                model_registry.deployment_environment = environment
                model_registry.deployment_endpoint = f"/models/{environment}/{model_id}"
                model_registry.deployed_at = datetime.utcnow()
                
                self.db.commit()
                
                logger.info(f"Deployed model {model_id} to {environment}")
                return True
            else:
                raise ValueError(f"Model version {current_version} not found")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deploy model {model_id} to {environment}: {str(e)}")
            return False
    
    def rollback_model(self, model_id: str, target_version: str) -> bool:
        """Rollback model to a previous version"""
        try:
            # Get model registry entry
            model_registry = self.get_model(model_id)
            if not model_registry:
                raise ValueError(f"Model {model_id} not found in registry")
            
            # Check if target version exists
            available_versions = self.list_model_versions(model_id)
            if target_version not in available_versions:
                raise ValueError(f"Version {target_version} not found")
            
            # Backup current version
            current_version = model_registry.current_version
            backup_dir = self.backups_path / f"{model_id}_{current_version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            current_dir = self.models_path / model_id / current_version
            
            if current_dir.exists():
                shutil.copytree(current_dir, backup_dir)
            
            # Update current version
            model_registry.current_version = target_version
            model_registry.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Rolled back model {model_id} to version {target_version}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to rollback model {model_id} to {target_version}: {str(e)}")
            return False
    
    def get_model(self, model_id: str) -> Optional[ModelRegistry]:
        """Get model from registry"""
        return self.db.query(ModelRegistry).filter(ModelRegistry.model_id == model_id).first()
    
    def list_models(self, model_type: Optional[str] = None, 
                   is_deployed: Optional[bool] = None,
                   limit: int = 50, offset: int = 0) -> List[ModelRegistry]:
        """List models in registry with optional filtering"""
        query = self.db.query(ModelRegistry)
        
        if model_type:
            query = query.filter(ModelRegistry.model_type == model_type)
        
        if is_deployed is not None:
            query = query.filter(ModelRegistry.is_deployed == is_deployed)
        
        return query.offset(offset).limit(limit).all()
    
    def _create_model_directories(self, model_id: str):
        """Create directory structure for a model"""
        model_dir = self.models_path / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial version directory
        initial_version = "v1.0.0"
        version_dir = model_dir / initial_version
        version_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _check_deployment_criteria(self, model_registry: ModelRegistry) -> bool:
        """Check if model meets deployment criteria"""
        criteria = self.config.model_registry.deployment.get("promotion_criteria", {})
        
        # Check minimum performance score
        min_performance = criteria.get("min_performance_score", 0.0)
        if model_registry.best_test_metric and model_registry.best_test_metric < min_performance:
            return False
        
        # Check maximum drift score
        max_drift = criteria.get("max_drift_score", 1.0)
        if model_registry.latest_drift_score and model_registry.latest_drift_score > max_drift:
            return False
        
        # Check minimum backtest days (would need to be tracked elsewhere)
        # This is a placeholder - actual implementation would check training job dates
        
        return True
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get overall model registry statistics"""
        try:
            total_models = self.db.query(ModelRegistry).count()
            deployed_models = self.db.query(ModelRegistry).filter(ModelRegistry.is_deployed == True).count()
            
            # Count by model type
            model_types = self.db.query(ModelRegistry.model_type, 
                                       self.db.func.count(ModelRegistry.id)).group_by(ModelRegistry.model_type).all()
            
            # Count by environment
            environments = self.db.query(ModelRegistry.deployment_environment,
                                       self.db.func.count(ModelRegistry.id)).filter(
                ModelRegistry.is_deployed == True).group_by(ModelRegistry.deployment_environment).all()
            
            return {
                "total_models": total_models,
                "deployed_models": deployed_models,
                "model_types": dict(model_types),
                "deployment_environments": dict(environments),
                "storage_usage_mb": self._calculate_storage_usage()
            }
            
        except Exception as e:
            logger.error(f"Failed to get model statistics: {str(e)}")
            return {}
    
    def _calculate_storage_usage(self) -> float:
        """Calculate total storage usage in MB"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(self.base_storage_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Failed to calculate storage usage: {str(e)}")
            return 0.0
