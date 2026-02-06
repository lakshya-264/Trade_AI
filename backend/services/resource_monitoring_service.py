"""
Resource Monitoring Service
Tracks CPU, GPU, and memory usage during ML training
"""

import logging
import asyncio
import psutil
import platform
import subprocess
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models.ml_models import TrainingJob
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class ResourceMonitoringService:
    """Service for monitoring system resources during ML training"""
    
    def __init__(self):
        self.resource_history: Dict[str, List[Dict]] = {}
        self.active_monitors: Dict[str, bool] = {}
        self.monitoring_interval = 10  # seconds
        self.history_retention = 3600  # 1 hour of history
        
        # Resource thresholds
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'gpu_warning': 85.0,
            'gpu_critical': 95.0
        }
    
    async def start_monitoring(self, job_id: str):
        """Start monitoring resources for a training job"""
        self.active_monitors[job_id] = True
        self.resource_history[job_id] = []
        
        logger.info(f"Started resource monitoring for job {job_id}")
        
        # Start monitoring loop
        asyncio.create_task(self._monitor_job_resources(job_id))
    
    async def stop_monitoring(self, job_id: str):
        """Stop monitoring resources for a training job"""
        if job_id in self.active_monitors:
            self.active_monitors[job_id] = False
            logger.info(f"Stopped resource monitoring for job {job_id}")
    
    async def _monitor_job_resources(self, job_id: str):
        """Monitor resources for a specific job"""
        while self.active_monitors.get(job_id, False):
            try:
                # Collect resource metrics
                metrics = await self._collect_resource_metrics()
                
                # Add timestamp
                metrics['timestamp'] = datetime.utcnow().isoformat()
                metrics['job_id'] = job_id
                
                # Store in history
                if job_id not in self.resource_history:
                    self.resource_history[job_id] = []
                
                self.resource_history[job_id].append(metrics)
                
                # Clean old history
                await self._cleanup_old_history(job_id)
                
                # Check thresholds and send alerts
                await self._check_thresholds(job_id, metrics)
                
            except Exception as e:
                logger.error(f"Resource monitoring error for job {job_id}: {e}")
            
            # Wait before next collection
            await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_resource_metrics(self) -> Dict[str, Any]:
        """Collect current system resource metrics"""
        metrics = {}
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        metrics['cpu'] = {
            'percent': cpu_percent,
            'count': cpu_count,
            'frequency': cpu_freq.current if cpu_freq else None,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        metrics['memory'] = {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
        
        # GPU metrics (if available)
        gpu_metrics = await self._get_gpu_metrics()
        if gpu_metrics:
            metrics['gpu'] = gpu_metrics
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics['disk'] = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': (disk.used / disk.total) * 100
        }
        
        # Network metrics
        network = psutil.net_io_counters()
        metrics['network'] = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }
        
        return metrics
    
    async def _get_gpu_metrics(self) -> Optional[Dict[str, Any]]:
        """Get GPU metrics if NVIDIA GPU is available"""
        try:
            # Try to get NVIDIA GPU metrics
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                
                for i, line in enumerate(lines):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 6:
                        gpus.append({
                            'id': i,
                            'name': parts[0],
                            'memory_total': int(parts[1]) * 1024 * 1024,  # Convert MB to bytes
                            'memory_used': int(parts[2]) * 1024 * 1024,
                            'memory_free': int(parts[3]) * 1024 * 1024,
                            'utilization': float(parts[4]),
                            'temperature': float(parts[5])
                        })
                
                if gpus:
                    return {
                        'gpus': gpus,
                        'total_memory': sum(gpu['memory_total'] for gpu in gpus),
                        'used_memory': sum(gpu['memory_used'] for gpu in gpus),
                        'average_utilization': sum(gpu['utilization'] for gpu in gpus) / len(gpus),
                        'max_temperature': max(gpu['temperature'] for gpu in gpus)
                    }
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # nvidia-smi not available or failed
            pass
        
        return None
    
    async def _cleanup_old_history(self, job_id: str):
        """Clean old resource history data"""
        if job_id in self.resource_history:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.history_retention)
            
            # Filter old entries
            self.resource_history[job_id] = [
                entry for entry in self.resource_history[job_id]
                if datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
    
    async def _check_thresholds(self, job_id: str, metrics: Dict[str, Any]):
        """Check resource thresholds and send alerts"""
        alerts = []
        
        # Check CPU
        cpu_percent = metrics['cpu']['percent']
        if cpu_percent >= self.thresholds['cpu_critical']:
            alerts.append({
                'type': 'critical',
                'resource': 'cpu',
                'value': cpu_percent,
                'threshold': self.thresholds['cpu_critical'],
                'message': f'CPU usage critically high: {cpu_percent:.1f}%'
            })
        elif cpu_percent >= self.thresholds['cpu_warning']:
            alerts.append({
                'type': 'warning',
                'resource': 'cpu',
                'value': cpu_percent,
                'threshold': self.thresholds['cpu_warning'],
                'message': f'CPU usage high: {cpu_percent:.1f}%'
            })
        
        # Check Memory
        memory_percent = metrics['memory']['percent']
        if memory_percent >= self.thresholds['memory_critical']:
            alerts.append({
                'type': 'critical',
                'resource': 'memory',
                'value': memory_percent,
                'threshold': self.thresholds['memory_critical'],
                'message': f'Memory usage critically high: {memory_percent:.1f}%'
            })
        elif memory_percent >= self.thresholds['memory_warning']:
            alerts.append({
                'type': 'warning',
                'resource': 'memory',
                'value': memory_percent,
                'threshold': self.thresholds['memory_warning'],
                'message': f'Memory usage high: {memory_percent:.1f}%'
            })
        
        # Check GPU
        if 'gpu' in metrics:
            gpu_utilization = metrics['gpu']['average_utilization']
            if gpu_utilization >= self.thresholds['gpu_critical']:
                alerts.append({
                    'type': 'critical',
                    'resource': 'gpu',
                    'value': gpu_utilization,
                    'threshold': self.thresholds['gpu_critical'],
                    'message': f'GPU utilization critically high: {gpu_utilization:.1f}%'
                })
            elif gpu_utilization >= self.thresholds['gpu_warning']:
                alerts.append({
                    'type': 'warning',
                    'resource': 'gpu',
                    'value': gpu_utilization,
                    'threshold': self.thresholds['gpu_warning'],
                    'message': f'GPU utilization high: {gpu_utilization:.1f}%'
                })
        
        # Send alerts if any
        if alerts:
            await self._send_resource_alerts(job_id, alerts)
    
    async def _send_resource_alerts(self, job_id: str, alerts: List[Dict]):
        """Send resource alerts to monitoring system"""
        try:
            # Import here to avoid circular imports
            from services.error_monitoring_service import error_monitoring_service
            
            for alert in alerts:
                await error_monitoring_service.broadcast_error_alert({
                    'level': alert['type'],
                    'category': 'resource',
                    'job_id': job_id,
                    'resource_type': alert['resource'],
                    'value': alert['value'],
                    'threshold': alert['threshold'],
                    'message': alert['message'],
                    'suggested_actions': self._get_resource_suggestions(alert['resource'], alert['type'])
                })
        
        except Exception as e:
            logger.error(f"Failed to send resource alerts: {e}")
    
    def _get_resource_suggestions(self, resource: str, alert_type: str) -> List[str]:
        """Get suggestions for resource alerts"""
        suggestions = {
            'cpu': {
                'warning': [
                    'Monitor CPU usage closely',
                    'Consider reducing batch size',
                    'Check for background processes'
                ],
                'critical': [
                    'Reduce batch size immediately',
                    'Kill unnecessary processes',
                    'Consider scaling horizontally'
                ]
            },
            'memory': {
                'warning': [
                    'Monitor memory usage',
                    'Consider reducing batch size',
                    'Enable gradient accumulation'
                ],
                'critical': [
                    'Reduce batch size significantly',
                    'Use data streaming',
                    'Kill unnecessary processes'
                ]
            },
            'gpu': {
                'warning': [
                    'Monitor GPU temperature',
                    'Consider reducing batch size',
                    'Check GPU memory usage'
                ],
                'critical': [
                    'Reduce batch size immediately',
                    'Check GPU cooling',
                    'Consider using mixed precision'
                ]
            }
        }
        
        return suggestions.get(resource, {}).get(alert_type, ['Contact system administrator'])
    
    def get_job_resource_summary(self, job_id: str) -> Dict[str, Any]:
        """Get resource usage summary for a job"""
        if job_id not in self.resource_history:
            return {
                'job_id': job_id,
                'status': 'no_data',
                'message': 'No resource data available'
            }
        
        history = self.resource_history[job_id]
        if not history:
            return {
                'job_id': job_id,
                'status': 'no_data',
                'message': 'No resource data available'
            }
        
        # Calculate statistics
        cpu_values = [entry['cpu']['percent'] for entry in history]
        memory_values = [entry['memory']['percent'] for entry in history]
        
        summary = {
            'job_id': job_id,
            'status': 'active' if self.active_monitors.get(job_id, False) else 'completed',
            'monitoring_duration': len(history) * self.monitoring_interval,
            'data_points': len(history),
            'cpu': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            }
        }
        
        # Add GPU summary if available
        gpu_values = []
        for entry in history:
            if 'gpu' in entry:
                gpu_values.append(entry['gpu']['average_utilization'])
        
        if gpu_values:
            summary['gpu'] = {
                'average': sum(gpu_values) / len(gpu_values),
                'max': max(gpu_values),
                'min': min(gpu_values)
            }
        
        return summary
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource status"""
        try:
            # Get current metrics
            current_metrics = asyncio.run(self._collect_resource_metrics())
            
            # Add system info
            system_info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            }
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system_info': system_info,
                'current_metrics': current_metrics,
                'active_monitors': len(self.active_monitors),
                'monitoring_jobs': list(self.active_monitors.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global instance
resource_monitoring_service = ResourceMonitoringService()
