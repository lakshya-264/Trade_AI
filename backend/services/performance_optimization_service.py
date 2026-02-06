"""
Performance Optimization Service
Provides intelligent recommendations for ML performance improvements
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from models.ml_models import TrainingJob, MLModelPerformanceMetrics
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class PerformanceOptimizationService:
    """Service for ML performance optimization recommendations"""
    
    def __init__(self):
        self.optimization_strategies = {
            'training_speed': {
                'batch_size_optimization': {
                    'description': 'Optimize batch size for faster training',
                    'conditions': ['high_gpu_memory_usage', 'low_gpu_utilization'],
                    'recommendations': [
                        'Increase batch size to maximize GPU utilization',
                        'Use gradient accumulation for effective larger batches',
                        'Consider mixed precision training'
                    ]
                },
                'data_loading': {
                    'description': 'Optimize data loading pipeline',
                    'conditions': ['high_cpu_waiting', 'low_gpu_utilization'],
                    'recommendations': [
                        'Increase number of data loader workers',
                        'Use data prefetching and pin_memory',
                        'Implement data caching and preprocessing'
                    ]
                },
                'model_architecture': {
                    'description': 'Optimize model architecture',
                    'conditions': ['slow_convergence', 'high_memory_usage'],
                    'recommendations': [
                        'Consider model pruning or distillation',
                        'Use depthwise separable convolutions',
                        'Implement efficient attention mechanisms'
                    ]
                }
            },
            'memory_efficiency': {
                'gradient_checkpointing': {
                    'description': 'Use gradient checkpointing to reduce memory',
                    'conditions': ['gpu_memory_out_of_memory', 'high_model_memory'],
                    'recommendations': [
                        'Enable gradient checkpointing',
                        'Reduce batch size with gradient accumulation',
                        'Use model parallelism for large models'
                    ]
                },
                'mixed_precision': {
                    'description': 'Use mixed precision training',
                    'conditions': ['high_memory_usage', 'gpu_supports_fp16'],
                    'recommendations': [
                        'Enable automatic mixed precision (AMP)',
                        'Use FP16 for forward pass, FP32 for gradients',
                        'Consider bfloat16 if supported'
                    ]
                }
            },
            'model_accuracy': {
                'hyperparameter_tuning': {
                    'description': 'Optimize hyperparameters for better accuracy',
                    'conditions': ['low_accuracy', 'poor_convergence'],
                    'recommendations': [
                        'Use learning rate scheduling',
                        'Implement warmup and cosine annealing',
                        'Try different optimizers (AdamW, RAdam)'
                    ]
                },
                'regularization': {
                    'description': 'Add regularization techniques',
                    'conditions': ['overfitting', 'high_validation_loss'],
                    'recommendations': [
                        'Add dropout layers',
                        'Use weight decay and L2 regularization',
                        'Implement data augmentation'
                    ]
                }
            },
            'resource_utilization': {
                'distributed_training': {
                    'description': 'Use distributed training for scalability',
                    'conditions': ['multiple_gpus_available', 'long_training_time'],
                    'recommendations': [
                        'Implement Data Parallel or Distributed Data Parallel',
                        'Use gradient synchronization optimization',
                        'Consider model parallelism for very large models'
                    ]
                },
                'cpu_gpu_balance': {
                    'description': 'Balance CPU and GPU utilization',
                    'conditions': ['cpu_bottleneck', 'gpu_underutilized'],
                    'recommendations': [
                        'Optimize data preprocessing pipeline',
                        'Use asynchronous data loading',
                        'Implement CPU-GPU parallel processing'
                    ]
                }
            }
        }
        
        self.performance_history: Dict[str, List[Dict]] = {}
        self.optimization_cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
    
    async def analyze_performance(self, model_id: str, db: Session) -> Dict[str, Any]:
        """Analyze model performance and generate optimization recommendations"""
        try:
            # Get performance metrics
            performance_data = await self._collect_performance_data(model_id, db)
            
            # Identify performance issues
            issues = await self._identify_performance_issues(performance_data)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(issues, performance_data)
            
            # Calculate optimization potential
            optimization_potential = await self._calculate_optimization_potential(
                performance_data, recommendations
            )
            
            result = {
                'model_id': model_id,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'performance_data': performance_data,
                'identified_issues': issues,
                'recommendations': recommendations,
                'optimization_potential': optimization_potential,
                'priority_actions': self._get_priority_actions(recommendations)
            }
            
            # Cache results
            self.optimization_cache[model_id] = {
                'result': result,
                'timestamp': datetime.utcnow()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze performance for model {model_id}: {e}")
            return {
                'model_id': model_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _collect_performance_data(self, model_id: str, db: Session) -> Dict[str, Any]:
        """Collect performance data for analysis"""
        # Get recent training jobs
        recent_jobs = db.query(TrainingJob).filter(
            TrainingJob.model_id == model_id,
            TrainingJob.started_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(desc(TrainingJob.started_at)).limit(10).all()
        
        # Get performance metrics
        performance_metrics = db.query(MLModelPerformanceMetrics).filter(
            MLModelPerformanceMetrics.model_id == model_id,
            MLModelPerformanceMetrics.evaluated_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(desc(MLModelPerformanceMetrics.evaluated_at)).limit(20).all()
        
        # Analyze training patterns
        training_patterns = self._analyze_training_patterns(recent_jobs)
        
        # Analyze performance trends
        performance_trends = self._analyze_performance_trends(performance_metrics)
        
        # Resource usage analysis
        resource_usage = await self._analyze_resource_usage(model_id)
        
        return {
            'training_jobs': len(recent_jobs),
            'performance_metrics': len(performance_metrics),
            'training_patterns': training_patterns,
            'performance_trends': performance_trends,
            'resource_usage': resource_usage,
            'recent_errors': self._get_recent_errors(recent_jobs)
        }
    
    def _analyze_training_patterns(self, jobs: List[TrainingJob]) -> Dict[str, Any]:
        """Analyze training job patterns"""
        if not jobs:
            return {}
        
        completed_jobs = [j for j in jobs if j.status == 'completed']
        failed_jobs = [j for j in jobs if j.status == 'failed']
        
        # Calculate average training duration
        durations = [j.training_duration_seconds for j in completed_jobs if j.training_duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Analyze hyperparameters
        hyperparams = {}
        for job in completed_jobs:
            if job.hyperparameters:
                for key, value in job.hyperparameters.items():
                    if key not in hyperparams:
                        hyperparams[key] = []
                    hyperparams[key].append(value)
        
        # Calculate average hyperparameters
        avg_hyperparams = {}
        for key, values in hyperparams.items():
            if isinstance(values[0], (int, float)):
                avg_hyperparams[key] = sum(values) / len(values)
        
        return {
            'total_jobs': len(jobs),
            'completed_jobs': len(completed_jobs),
            'failed_jobs': len(failed_jobs),
            'success_rate': len(completed_jobs) / len(jobs) if jobs else 0,
            'average_duration': avg_duration,
            'common_hyperparameters': avg_hyperparams,
            'failure_patterns': self._analyze_failure_patterns(failed_jobs)
        }
    
    def _analyze_performance_trends(self, metrics: List[MLModelPerformanceMetrics]) -> Dict[str, Any]:
        """Analyze performance metric trends"""
        if not metrics:
            return {}
        
        # Sort by date
        sorted_metrics = sorted(metrics, key=lambda x: x.evaluated_at)
        
        # Extract metric values
        accuracy_trend = [m.accuracy for m in sorted_metrics if m.accuracy]
        loss_trend = [m.loss for m in sorted_metrics if m.loss]
        f1_trend = [m.f1_score for m in sorted_metrics if m.f1_score]
        
        # Calculate trends
        trends = {}
        
        if len(accuracy_trend) > 1:
            accuracy_change = accuracy_trend[-1] - accuracy_trend[0]
            trends['accuracy'] = {
                'change': accuracy_change,
                'trend': 'improving' if accuracy_change > 0 else 'declining',
                'volatility': self._calculate_volatility(accuracy_trend)
            }
        
        if len(loss_trend) > 1:
            loss_change = loss_trend[-1] - loss_trend[0]
            trends['loss'] = {
                'change': loss_change,
                'trend': 'improving' if loss_change < 0 else 'declining',
                'volatility': self._calculate_volatility(loss_trend)
            }
        
        return trends
    
    async def _analyze_resource_usage(self, model_id: str) -> Dict[str, Any]:
        """Analyze resource usage patterns"""
        try:
            # Import here to avoid circular imports
            from services.resource_monitoring_service import resource_monitoring_service
            
            # Get resource summary for recent jobs
            recent_jobs = [job_id for job_id in resource_monitoring_service.resource_history.keys()]
            
            resource_summary = {}
            for job_id in recent_jobs:
                if model_id in job_id:  # Simple matching - could be improved
                    summary = resource_monitoring_service.get_job_resource_summary(job_id)
                    if 'cpu' in summary:
                        resource_summary[job_id] = summary
            
            return resource_summary
            
        except Exception as e:
            logger.error(f"Failed to analyze resource usage: {e}")
            return {}
    
    def _get_recent_errors(self, jobs: List[TrainingJob]) -> List[Dict[str, Any]]:
        """Get recent error patterns"""
        errors = []
        for job in jobs:
            if job.status == 'failed' and job.error_message:
                errors.append({
                    'job_id': job.job_id,
                    'error_message': job.error_message,
                    'error_category': self._categorize_error(job.error_message),
                    'failed_at': job.started_at.isoformat()
                })
        
        return errors[-5:]  # Last 5 errors
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error for analysis"""
        if not error_message:
            return "unknown"
        
        error_msg = error_message.lower()
        if "memory" in error_msg:
            return "memory"
        elif "convergence" in error_msg:
            return "convergence"
        elif "data" in error_msg:
            return "data"
        elif "gpu" in error_msg:
            return "gpu"
        else:
            return "unknown"
    
    def _analyze_failure_patterns(self, failed_jobs: List[TrainingJob]) -> Dict[str, Any]:
        """Analyze failure patterns"""
        if not failed_jobs:
            return {}
        
        error_categories = {}
        for job in failed_jobs:
            category = self._categorize_error(job.error_message)
            error_categories[category] = error_categories.get(category, 0) + 1
        
        return {
            'total_failures': len(failed_jobs),
            'error_categories': error_categories,
            'most_common_error': max(error_categories, key=error_categories.get) if error_categories else None
        }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation) of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    async def _identify_performance_issues(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance issues from data"""
        issues = []
        
        # Check training patterns
        patterns = performance_data.get('training_patterns', {})
        
        if patterns.get('success_rate', 1.0) < 0.8:
            issues.append({
                'type': 'low_success_rate',
                'severity': 'high',
                'description': f"Low training success rate: {patterns.get('success_rate', 0):.1%}",
                'impact': 'high'
            })
        
        if patterns.get('average_duration', 0) > 7200:  # > 2 hours
            issues.append({
                'type': 'slow_training',
                'severity': 'medium',
                'description': f"Slow training duration: {patterns.get('average_duration', 0):.0f} seconds",
                'impact': 'medium'
            })
        
        # Check performance trends
        trends = performance_data.get('performance_trends', {})
        
        for metric, trend_data in trends.items():
            if trend_data.get('trend') == 'declining':
                issues.append({
                    'type': f'declining_{metric}',
                    'severity': 'high' if abs(trend_data.get('change', 0)) > 0.1 else 'medium',
                    'description': f"Declining {metric} trend: {trend_data.get('change', 0):.3f}",
                    'impact': 'high'
                })
        
        # Check recent errors
        errors = performance_data.get('recent_errors', [])
        if len(errors) > 3:
            issues.append({
                'type': 'frequent_errors',
                'severity': 'high',
                'description': f"Frequent errors: {len(errors)} recent failures",
                'impact': 'high'
            })
        
        return issues
    
    async def _generate_recommendations(self, issues: List[Dict], performance_data: Dict) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []
        
        for issue in issues:
            issue_type = issue['type']
            
            # Map issues to optimization strategies
            if issue_type in ['low_success_rate', 'frequent_errors']:
                recommendations.extend(self._get_error_handling_recommendations(performance_data))
            
            elif issue_type == 'slow_training':
                recommendations.extend(self._get_speed_optimization_recommendations(performance_data))
            
            elif 'declining_' in issue_type:
                recommendations.extend(self._get_accuracy_improvement_recommendations(performance_data))
            
            elif 'memory' in issue_type:
                recommendations.extend(self._get_memory_optimization_recommendations(performance_data))
        
        # Add general recommendations based on patterns
        recommendations.extend(self._get_general_recommendations(performance_data))
        
        # Remove duplicates and prioritize
        unique_recommendations = []
        seen = set()
        
        for rec in recommendations:
            rec_key = f"{rec['category']}_{rec['strategy']}"
            if rec_key not in seen:
                seen.add(rec_key)
                unique_recommendations.append(rec)
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        unique_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return unique_recommendations[:10]  # Top 10 recommendations
    
    def _get_error_handling_recommendations(self, performance_data: Dict) -> List[Dict]:
        """Get recommendations for error handling"""
        recommendations = []
        
        errors = performance_data.get('recent_errors', [])
        error_categories = {}
        
        for error in errors:
            category = error.get('error_category', 'unknown')
            error_categories[category] = error_categories.get(category, 0) + 1
        
        # Memory errors
        if error_categories.get('memory', 0) > 0:
            recommendations.append({
                'category': 'memory_efficiency',
                'strategy': 'gradient_checkpointing',
                'priority': 'high',
                'expected_improvement': '50-70% memory reduction',
                'implementation_effort': 'medium',
                'recommendations': self.optimization_strategies['memory_efficiency']['gradient_checkpointing']['recommendations']
            })
        
        # Convergence errors
        if error_categories.get('convergence', 0) > 0:
            recommendations.append({
                'category': 'model_accuracy',
                'strategy': 'hyperparameter_tuning',
                'priority': 'high',
                'expected_improvement': '20-40% better convergence',
                'implementation_effort': 'medium',
                'recommendations': self.optimization_strategies['model_accuracy']['hyperparameter_tuning']['recommendations']
            })
        
        return recommendations
    
    def _get_speed_optimization_recommendations(self, performance_data: Dict) -> List[Dict]:
        """Get recommendations for training speed optimization"""
        recommendations = []
        
        resource_usage = performance_data.get('resource_usage', {})
        
        # Check GPU utilization
        low_gpu = any(
            summary.get('gpu', {}).get('average_utilization', 0) < 50
            for summary in resource_usage.values()
        )
        
        if low_gpu:
            recommendations.append({
                'category': 'training_speed',
                'strategy': 'batch_size_optimization',
                'priority': 'high',
                'expected_improvement': '30-50% faster training',
                'implementation_effort': 'low',
                'recommendations': self.optimization_strategies['training_speed']['batch_size_optimization']['recommendations']
            })
        
        # Check data loading bottlenecks
        recommendations.append({
            'category': 'training_speed',
            'strategy': 'data_loading',
            'priority': 'medium',
            'expected_improvement': '20-30% faster training',
            'implementation_effort': 'medium',
            'recommendations': self.optimization_strategies['training_speed']['data_loading']['recommendations']
        })
        
        return recommendations
    
    def _get_accuracy_improvement_recommendations(self, performance_data: Dict) -> List[Dict]:
        """Get recommendations for accuracy improvement"""
        recommendations = []
        
        # Check for overfitting
        trends = performance_data.get('performance_trends', {})
        
        recommendations.append({
            'category': 'model_accuracy',
            'strategy': 'hyperparameter_tuning',
            'priority': 'high',
            'expected_improvement': '10-25% accuracy improvement',
            'implementation_effort': 'medium',
            'recommendations': self.optimization_strategies['model_accuracy']['hyperparameter_tuning']['recommendations']
        })
        
        # Add regularization if needed
        recommendations.append({
            'category': 'model_accuracy',
            'strategy': 'regularization',
            'priority': 'medium',
            'expected_improvement': '5-15% generalization improvement',
            'implementation_effort': 'low',
            'recommendations': self.optimization_strategies['model_accuracy']['regularization']['recommendations']
        })
        
        return recommendations
    
    def _get_memory_optimization_recommendations(self, performance_data: Dict) -> List[Dict]:
        """Get recommendations for memory optimization"""
        recommendations = []
        
        recommendations.append({
            'category': 'memory_efficiency',
            'strategy': 'mixed_precision',
            'priority': 'high',
            'expected_improvement': '40-60% memory reduction',
            'implementation_effort': 'low',
            'recommendations': self.optimization_strategies['memory_efficiency']['mixed_precision']['recommendations']
        })
        
        recommendations.append({
            'category': 'memory_efficiency',
            'strategy': 'gradient_checkpointing',
            'priority': 'medium',
            'expected_improvement': '50-70% memory reduction',
            'implementation_effort': 'medium',
            'recommendations': self.optimization_strategies['memory_efficiency']['gradient_checkpointing']['recommendations']
        })
        
        return recommendations
    
    def _get_general_recommendations(self, performance_data: Dict) -> List[Dict]:
        """Get general optimization recommendations"""
        recommendations = []
        
        # Check if distributed training could help
        patterns = performance_data.get('training_patterns', {})
        if patterns.get('average_duration', 0) > 3600:  # > 1 hour
            recommendations.append({
                'category': 'resource_utilization',
                'strategy': 'distributed_training',
                'priority': 'low',
                'expected_improvement': '2-4x speedup with multiple GPUs',
                'implementation_effort': 'high',
                'recommendations': self.optimization_strategies['resource_utilization']['distributed_training']['recommendations']
            })
        
        return recommendations
    
    async def _calculate_optimization_potential(
        self, 
        performance_data: Dict, 
        recommendations: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate potential improvements from optimizations"""
        potential = {
            'speed_improvement': 0,
            'memory_reduction': 0,
            'accuracy_improvement': 0,
            'overall_score': 0
        }
        
        for rec in recommendations:
            improvement_text = rec.get('expected_improvement', '0%')
            
            # Parse improvement percentages
            if 'faster' in improvement_text.lower():
                speed_match = improvement_text.split('%')[0].split('-')[-1]
                try:
                    potential['speed_improvement'] = max(potential['speed_improvement'], float(speed_match))
                except:
                    pass
            
            if 'reduction' in improvement_text.lower():
                memory_match = improvement_text.split('%')[0].split('-')[-1]
                try:
                    potential['memory_reduction'] = max(potential['memory_reduction'], float(memory_match))
                except:
                    pass
            
            if 'improvement' in improvement_text.lower():
                accuracy_match = improvement_text.split('%')[0].split('-')[-1]
                try:
                    potential['accuracy_improvement'] = max(potential['accuracy_improvement'], float(accuracy_match))
                except:
                    pass
        
        # Calculate overall optimization score
        potential['overall_score'] = (
            potential['speed_improvement'] * 0.4 +
            potential['memory_reduction'] * 0.3 +
            potential['accuracy_improvement'] * 0.3
        )
        
        return potential
    
    def _get_priority_actions(self, recommendations: List[Dict]) -> List[Dict]:
        """Get top priority actions"""
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
        
        return (high_priority + medium_priority)[:3]  # Top 3 priority actions

# Global instance
performance_optimization_service = PerformanceOptimizationService()
