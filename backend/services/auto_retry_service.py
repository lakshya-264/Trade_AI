"""
Auto-Retry Service with Parameter Optimization
Implements intelligent job retry with adaptive parameter tuning
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models.ml_models import TrainingJob
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class AutoRetryService:
    """Service for intelligent job retry with parameter optimization"""
    
    def __init__(self):
        self.retry_strategies = {
            'memory': {
                'priority': 1,
                'adjustments': [
                    {'batch_size': 0.5},  # Reduce batch size by 50%
                    {'learning_rate': 0.8},  # Reduce learning rate by 20%
                    {'gradient_accumulation_steps': 2}  # Add gradient accumulation
                ]
            },
            'convergence': {
                'priority': 2,
                'adjustments': [
                    {'learning_rate': 0.5},  # Reduce learning rate by 50%
                    {'epochs': 1.5},  # Increase epochs by 50%
                    {'optimizer': 'adam'},  # Try different optimizer
                    {'weight_decay': 0.01}  # Add weight decay
                ]
            },
            'data': {
                'priority': 3,
                'adjustments': [
                    {'data_validation': True},  # Enable data validation
                    {'data_imputation': 'mean'},  # Add data imputation
                    {'batch_size': 0.8},  # Reduce batch size slightly
                    {'dropout': 0.2}  # Add dropout for robustness
                ]
            },
            'infrastructure': {
                'priority': 4,
                'adjustments': [
                    {'checkpoint_frequency': 0.5},  # Checkpoint more frequently
                    {'save_best_only': True},  # Only save best model
                    {'compression': True}  # Enable checkpoint compression
                ]
            },
            'unknown': {
                'priority': 5,
                'adjustments': [
                    {'learning_rate': 0.7},  # Conservative learning rate reduction
                    {'batch_size': 0.8},  # Reduce batch size
                    {'epochs': 1.2}  # Increase epochs slightly
                ]
            }
        }
        
        self.retry_limits = {
            'max_retries': 3,
            'retry_cooldown': 300,  # 5 minutes between retries
            'backoff_multiplier': 2.0
        }
        
        self.performance_history: Dict[str, List[Dict]] = {}
    
    async def analyze_failure(self, job_id: str, db: Session) -> Optional[Dict]:
        """Analyze failed job and determine retry strategy"""
        try:
            failed_job = db.query(TrainingJob).filter(
                TrainingJob.job_id == job_id,
                TrainingJob.status == 'failed'
            ).first()
            
            if not failed_job:
                return None
            
            # Categorize error
            error_category = self._categorize_error(failed_job.error_message)
            
            # Get retry history
            retry_history = self._get_retry_history(failed_job.model_id, db)
            
            # Check if retry is appropriate
            if not self._should_retry(failed_job, retry_history):
                return None
            
            # Determine optimal parameters
            optimized_params = await self._optimize_parameters(
                failed_job, error_category, retry_history
            )
            
            return {
                'original_job_id': job_id,
                'model_id': failed_job.model_id,
                'error_category': error_category,
                'retry_count': len(retry_history) + 1,
                'optimized_parameters': optimized_params,
                'estimated_success_rate': self._estimate_success_rate(
                    error_category, retry_history
                ),
                'reasoning': self._generate_reasoning(
                    error_category, failed_job.error_message, optimized_params
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze failure for job {job_id}: {e}")
            return None
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content"""
        if not error_message:
            return "unknown"
        
        error_msg = error_message.lower()
        if "memory" in error_msg or "cuda" in error_msg:
            return "memory"
        elif "convergence" in error_msg or "learning rate" in error_msg:
            return "convergence"
        elif "nan" in error_msg or "validation" in error_msg:
            return "data"
        elif "checkpoint" in error_msg or "disk" in error_msg:
            return "infrastructure"
        else:
            return "unknown"
    
    def _get_retry_history(self, model_id: str, db: Session) -> List[TrainingJob]:
        """Get retry history for a model"""
        return db.query(TrainingJob).filter(
            TrainingJob.model_id == model_id,
            TrainingJob.status == 'failed'
        ).order_by(desc(TrainingJob.started_at)).limit(10).all()
    
    def _should_retry(self, job: TrainingJob, retry_history: List[TrainingJob]) -> bool:
        """Determine if job should be retried"""
        # Check retry limit
        if len(retry_history) >= self.retry_limits['max_retries']:
            return False
        
        # Check cooldown period
        last_retry = retry_history[0] if retry_history else None
        if last_retry:
            time_since_last = datetime.utcnow() - last_retry.started_at
            if time_since_last.total_seconds() < self.retry_limits['retry_cooldown']:
                return False
        
        # Check if error is retryable
        non_retryable_errors = [
            'permission denied',
            'authentication failed',
            'invalid api key',
            'quota exceeded'
        ]
        
        if job.error_message:
            error_msg = job.error_message.lower()
            if any(err in error_msg for err in non_retryable_errors):
                return False
        
        return True
    
    async def _optimize_parameters(
        self, 
        job: TrainingJob, 
        error_category: str, 
        retry_history: List[TrainingJob]
    ) -> Dict[str, Any]:
        """Optimize parameters based on error category and history"""
        base_params = job.hyperparameters or {}
        
        # Get strategy for error category
        strategy = self.retry_strategies.get(error_category, self.retry_strategies['unknown'])
        
        # Apply adjustments based on retry count
        retry_count = len(retry_history)
        adjustments = strategy['adjustments']
        
        # Select adjustment based on retry count (cycle through options)
        adjustment_index = min(retry_count, len(adjustments) - 1)
        adjustment = adjustments[adjustment_index]
        
        # Apply adjustment to base parameters
        optimized_params = base_params.copy()
        
        for param, value in adjustment.items():
            if param in optimized_params:
                if isinstance(optimized_params[param], (int, float)) and isinstance(value, float):
                    # Scale numeric parameters
                    optimized_params[param] = int(optimized_params[param] * value) if isinstance(optimized_params[param], int) else optimized_params[param] * value
                else:
                    # Set or override parameter
                    optimized_params[param] = value
            else:
                optimized_params[param] = value
        
        # Add retry-specific metadata
        optimized_params['_retry_metadata'] = {
            'retry_count': retry_count + 1,
            'original_error': error_category,
            'optimization_strategy': adjustment,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return optimized_params
    
    def _estimate_success_rate(
        self, 
        error_category: str, 
        retry_history: List[TrainingJob]
    ) -> float:
        """Estimate success rate for retry"""
        # Base success rates by error category
        base_rates = {
            'memory': 0.7,
            'convergence': 0.6,
            'data': 0.8,
            'infrastructure': 0.9,
            'unknown': 0.4
        }
        
        base_rate = base_rates.get(error_category, 0.4)
        
        # Adjust based on retry count
        retry_count = len(retry_history)
        if retry_count == 0:
            return base_rate
        elif retry_count == 1:
            return base_rate * 0.8
        elif retry_count == 2:
            return base_rate * 0.6
        else:
            return base_rate * 0.4
    
    def _generate_reasoning(
        self, 
        error_category: str, 
        error_message: str, 
        optimized_params: Dict[str, Any]
    ) -> str:
        """Generate reasoning for parameter optimization"""
        reasoning = f"Error categorized as '{error_category}'. "
        
        if error_category == 'memory':
            reasoning += "Reducing batch size and learning rate to lower memory usage. "
        elif error_category == 'convergence':
            reasoning += "Adjusting learning rate and increasing epochs for better convergence. "
        elif error_category == 'data':
            reasoning += "Enabling data validation and adjusting batch size for data robustness. "
        elif error_category == 'infrastructure':
            reasoning += "Optimizing checkpoint strategy to reduce disk I/O. "
        else:
            reasoning += "Applying conservative parameter adjustments. "
        
        reasoning += f"Parameters optimized: {', '.join(optimized_params.keys())}"
        
        return reasoning
    
    async def execute_retry(self, retry_plan: Dict, db: Session) -> Optional[str]:
        """Execute optimized retry"""
        try:
            # Create new retry job
            new_job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_auto_retry"
            
            retry_job = TrainingJob(
                job_id=new_job_id,
                model_id=retry_plan['model_id'],
                model_version="1.0.0",  # Could be dynamic
                job_type="training",
                status="running",
                started_at=datetime.utcnow(),
                hyperparameters=retry_plan['optimized_parameters'],
                progress=0.0
            )
            
            db.add(retry_job)
            db.commit()
            
            # Log retry execution
            logger.info(f"Auto-retry executed: {new_job_id} for {retry_plan['model_id']}")
            logger.info(f"Optimization reasoning: {retry_plan['reasoning']}")
            
            return new_job_id
            
        except Exception as e:
            logger.error(f"Failed to execute retry: {e}")
            db.rollback()
            return None
    
    async def monitor_retry_jobs(self):
        """Monitor retry jobs and learn from outcomes"""
        while True:
            try:
                db = SessionLocal()
                
                # Find recently completed retry jobs
                cutoff_time = datetime.utcnow() - timedelta(minutes=10)
                retry_jobs = db.query(TrainingJob).filter(
                    and_(
                        TrainingJob.job_id.like('%_auto_retry'),
                        TrainingJob.started_at >= cutoff_time,
                        TrainingJob.status.in_(['completed', 'failed'])
                    )
                ).all()
                
                # Learn from outcomes
                for job in retry_jobs:
                    await self._learn_from_retry(job, db)
                
            except Exception as e:
                logger.error(f"Retry monitoring failed: {e}")
            finally:
                db.close()
            
            # Check every 5 minutes
            await asyncio.sleep(300)
    
    async def _learn_from_retry(self, job: TrainingJob, db: Session):
        """Learn from retry outcomes to improve future strategies"""
        try:
            retry_metadata = job.hyperparameters.get('_retry_metadata', {})
            if not retry_metadata:
                return
            
            model_id = job.model_id
            error_category = retry_metadata.get('original_error')
            optimization_strategy = retry_metadata.get('optimization_strategy', {})
            
            # Record outcome
            outcome = {
                'job_id': job.job_id,
                'status': job.status,
                'error_category': error_category,
                'strategy': optimization_strategy,
                'timestamp': job.completed_at or datetime.utcnow(),
                'success': job.status == 'completed'
            }
            
            # Update performance history
            if model_id not in self.performance_history:
                self.performance_history[model_id] = []
            
            self.performance_history[model_id].append(outcome)
            
            # Keep only last 20 outcomes per model
            if len(self.performance_history[model_id]) > 20:
                self.performance_history[model_id] = self.performance_history[model_id][-20:]
            
            # Log learning
            if job.status == 'completed':
                logger.info(f"Successful retry learned: {job.job_id} using strategy {optimization_strategy}")
            else:
                logger.info(f"Failed retry learned: {job.job_id} using strategy {optimization_strategy}")
            
        except Exception as e:
            logger.error(f"Failed to learn from retry {job.job_id}: {e}")

# Global instance
auto_retry_service = AutoRetryService()
