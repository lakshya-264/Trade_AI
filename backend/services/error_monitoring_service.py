"""
Real-time Error Monitoring Service
Provides real-time error tracking, alerting, and notification system
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from fastapi import WebSocket, WebSocketDisconnect

from models.ml_models import TrainingJob
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class ErrorMonitoringService:
    """Service for real-time error monitoring and alerting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.error_thresholds = {
            'error_rate': 0.2,  # 20% error rate threshold
            'consecutive_failures': 3,  # Alert after 3 consecutive failures
            'critical_errors': ['memory', 'infrastructure']  # Critical error categories
        }
        self.error_history: List[Dict] = []
        self.alert_cooldown = 300  # 5 minutes cooldown between alerts
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection for real-time updates"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial error summary
        await self.send_error_summary(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_error_summary(self, websocket: WebSocket):
        """Send current error summary to WebSocket client"""
        try:
            db = SessionLocal()
            error_summary = self.get_error_summary(db, days=1)
            await websocket.send_json({
                'type': 'error_summary',
                'data': error_summary,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send error summary: {e}")
        finally:
            db.close()
    
    async def broadcast_error_alert(self, error_data: Dict):
        """Broadcast error alert to all connected clients"""
        if not self.active_connections:
            return
        
        message = {
            'type': 'error_alert',
            'data': error_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_error_update(self, update_type: str, data: Dict):
        """Broadcast general error updates to all clients"""
        if not self.active_connections:
            return
        
        message = {
            'type': update_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_error_summary(self, db: Session, days: int = 7) -> Dict:
        """Get comprehensive error summary"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get failed jobs
            failed_jobs = db.query(TrainingJob).filter(
                TrainingJob.status == 'failed',
                TrainingJob.started_at >= start_date
            ).order_by(desc(TrainingJob.started_at)).all()
            
            # Categorize errors
            error_categories = {
                'resource': 0,
                'data': 0,
                'hyperparameter': 0,
                'infrastructure': 0,
                'unknown': 0
            }
            
            recent_errors = []
            error_trends = []
            
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
                    "failed_at": job.started_at.isoformat()
                })
            
            # Calculate error trends (hourly)
            for hours_ago in range(24, 0, -1):
                hour_start = end_date - timedelta(hours=hours_ago)
                hour_end = end_date - timedelta(hours=hours_ago-1)
                
                hour_errors = db.query(TrainingJob).filter(
                    TrainingJob.status == 'failed',
                    TrainingJob.started_at >= hour_start,
                    TrainingJob.started_at < hour_end
                ).count()
                
                hour_total = db.query(TrainingJob).filter(
                    TrainingJob.started_at >= hour_start,
                    TrainingJob.started_at < hour_end
                ).count()
                
                error_rate = hour_errors / hour_total if hour_total > 0 else 0
                
                error_trends.append({
                    "hour": hour_start.strftime('%H:00'),
                    "errors": hour_errors,
                    "total": hour_total,
                    "error_rate": error_rate
                })
            
            return {
                "total_errors": len(failed_jobs),
                "error_categories": error_categories,
                "recent_errors": recent_errors[:20],
                "error_trends": error_trends,
                "period_days": days,
                "error_rate": len(failed_jobs) / max(1, db.query(TrainingJob).filter(
                    TrainingJob.started_at >= start_date
                ).count())
            }
            
        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return {
                "total_errors": 0,
                "error_categories": {},
                "recent_errors": [],
                "error_trends": [],
                "period_days": days,
                "error_rate": 0
            }
    
    async def monitor_errors(self):
        """Background task to monitor errors and send alerts"""
        while True:
            try:
                db = SessionLocal()
                
                # Get recent errors
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=5)
                
                recent_errors = db.query(TrainingJob).filter(
                    TrainingJob.status == 'failed',
                    TrainingJob.started_at >= start_time
                ).all()
                
                # Check for alert conditions
                if recent_errors:
                    await self.check_error_alerts(recent_errors, db)
                
                # Broadcast error summary update
                error_summary = self.get_error_summary(db, days=1)
                await self.broadcast_error_update('error_summary_update', error_summary)
                
            except Exception as e:
                logger.error(f"Error monitoring failed: {e}")
            finally:
                db.close()
            
            # Check every minute
            await asyncio.sleep(60)
    
    async def check_error_alerts(self, recent_errors: List[TrainingJob], db: Session):
        """Check if error conditions trigger alerts"""
        for error in recent_errors:
            # Check if it's a critical error category
            error_category = self.categorize_error(error.error_message)
            
            if error_category in self.error_thresholds['critical_errors']:
                await self.broadcast_error_alert({
                    'level': 'critical',
                    'category': error_category,
                    'job_id': error.job_id,
                    'model_id': error.model_id,
                    'error_message': error.error_message,
                    'suggested_actions': self.get_suggested_actions(error_category)
                })
            
            # Check for consecutive failures
            consecutive_failures = self.check_consecutive_failures(error.model_id, db)
            if consecutive_failures >= self.error_thresholds['consecutive_failures']:
                await self.broadcast_error_alert({
                    'level': 'warning',
                    'category': 'consecutive_failures',
                    'model_id': error.model_id,
                    'consecutive_count': consecutive_failures,
                    'suggested_actions': ['Review model configuration', 'Check data quality', 'Consider hyperparameter tuning']
                })
    
    def categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content"""
        if not error_message:
            return "unknown"
        
        error_msg = error_message.lower()
        if "memory" in error_msg:
            return "resource"
        elif "nan" in error_msg or "validation" in error_msg:
            return "data"
        elif "convergence" in error_msg or "learning rate" in error_msg:
            return "hyperparameter"
        elif "checkpoint" in error_msg or "disk" in error_msg:
            return "infrastructure"
        else:
            return "unknown"
    
    def get_suggested_actions(self, error_category: str) -> List[str]:
        """Get suggested actions for error category"""
        actions = {
            'resource': [
                'Reduce batch size',
                'Use gradient accumulation',
                'Increase available RAM/GPU memory',
                'Use data streaming instead of loading all data'
            ],
            'data': [
                'Check data quality',
                'Implement data imputation',
                'Remove corrupted samples',
                'Add data validation checks'
            ],
            'hyperparameter': [
                'Lower learning rate',
                'Try different optimizer',
                'Adjust model architecture',
                'Implement learning rate scheduling'
            ],
            'infrastructure': [
                'Free up disk space',
                'Check file permissions',
                'Use different checkpoint location',
                'Implement checkpoint compression'
            ]
        }
        return actions.get(error_category, ['Contact ML engineering team'])
    
    def check_consecutive_failures(self, model_id: str, db: Session) -> int:
        """Check number of consecutive failures for a model"""
        recent_jobs = db.query(TrainingJob).filter(
            TrainingJob.model_id == model_id
        ).order_by(desc(TrainingJob.started_at)).limit(10).all()
        
        consecutive = 0
        for job in recent_jobs:
            if job.status == 'failed':
                consecutive += 1
            else:
                break
        
        return consecutive

# Global instance
error_monitoring_service = ErrorMonitoringService()
