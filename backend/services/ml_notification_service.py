"""
ML Notification Service
Automated notifications for drift detection, performance issues, and training events
"""

import smtplib
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from sqlalchemy.orm import Session
from jinja2 import Template

from core.ml_config import get_ml_config
from models.ml_models import ModelDriftHistory, TrainingJob, ModelPerformanceMetrics, ABTestExperiment

logger = logging.getLogger(__name__)

class MLNotificationService:
    """Service for sending ML-related notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_ml_config()
        self.notification_config = self.config.notifications
        
    def send_drift_alert(self, drift_record: ModelDriftHistory) -> bool:
        """Send drift detection alert"""
        try:
            # Get model information
            from models.ml_models import ModelRegistry
            model = self.db.query(ModelRegistry).filter(
                ModelRegistry.model_id == drift_record.model_id
            ).first()
            
            # Prepare alert data
            alert_data = {
                "alert_type": "drift_detected",
                "model_id": drift_record.model_id,
                "model_name": model.model_name if model else drift_record.model_id,
                "model_version": drift_record.model_version,
                "drift_score": drift_record.drift_score,
                "drift_type": drift_record.drift_type,
                "detected_at": drift_record.detected_at,
                "severity": self._get_drift_severity(drift_record.drift_score),
                "metrics": drift_record.drift_metrics or {}
            }
            
            # Send through enabled channels
            success = True
            channels = self.notification_config.get("alerts", {}).get("drift_detected", {}).get("channels", [])
            
            for channel in channels:
                if channel == "email" and self.notification_config.get("channels", {}).get("email", {}).get("enabled"):
                    success &= self._send_email_alert(alert_data, "drift_alert")
                elif channel == "webhook" and self.notification_config.get("channels", {}).get("webhook", {}).get("enabled"):
                    success &= self._send_webhook_alert(alert_data)
                elif channel == "slack" and self.notification_config.get("channels", {}).get("slack", {}).get("enabled"):
                    success &= self._send_slack_alert(alert_data)
            
            if success:
                logger.info(f"Sent drift alert for model {drift_record.model_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send drift alert: {str(e)}")
            return False
    
    def send_training_failure_alert(self, training_job: TrainingJob) -> bool:
        """Send training failure alert"""
        try:
            # Prepare alert data
            alert_data = {
                "alert_type": "training_failure",
                "job_id": training_job.job_id,
                "model_id": training_job.model_id,
                "model_version": training_job.model_version,
                "job_type": training_job.job_type,
                "started_at": training_job.started_at,
                "failed_at": training_job.completed_at,
                "error_message": training_job.error_message,
                "duration_seconds": training_job.training_duration_seconds
            }
            
            # Send through enabled channels
            success = True
            channels = self.notification_config.get("alerts", {}).get("training_failure", {}).get("channels", [])
            
            for channel in channels:
                if channel == "email" and self.notification_config.get("channels", {}).get("email", {}).get("enabled"):
                    success &= self._send_email_alert(alert_data, "training_failure")
                elif channel == "webhook" and self.notification_config.get("channels", {}).get("webhook", {}).get("enabled"):
                    success &= self._send_webhook_alert(alert_data)
            
            if success:
                logger.info(f"Sent training failure alert for job {training_job.job_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send training failure alert: {str(e)}")
            return False
    
    def send_performance_degradation_alert(self, metrics: ModelPerformanceMetrics, baseline: float) -> bool:
        """Send performance degradation alert"""
        try:
            # Get model information
            from models.ml_models import ModelRegistry
            model = self.db.query(ModelRegistry).filter(
                ModelRegistry.model_id == metrics.model_id
            ).first()
            
            # Calculate degradation percentage
            current_performance = metrics.total_return or 0
            degradation_percentage = ((baseline - current_performance) / baseline * 100) if baseline > 0 else 0
            
            # Prepare alert data
            alert_data = {
                "alert_type": "performance_degradation",
                "model_id": metrics.model_id,
                "model_name": model.model_name if model else metrics.model_id,
                "model_version": metrics.model_version,
                "evaluated_at": metrics.evaluated_at,
                "current_performance": current_performance,
                "baseline_performance": baseline,
                "degradation_percentage": degradation_percentage,
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown": metrics.max_drawdown,
                "win_rate": metrics.win_rate
            }
            
            # Send through enabled channels
            success = True
            channels = self.notification_config.get("alerts", {}).get("performance_degradation", {}).get("channels", [])
            
            for channel in channels:
                if channel == "email" and self.notification_config.get("channels", {}).get("email", {}).get("enabled"):
                    success &= self._send_email_alert(alert_data, "performance_degradation")
                elif channel == "webhook" and self.notification_config.get("channels", {}).get("webhook", {}).get("enabled"):
                    success &= self._send_webhook_alert(alert_data)
            
            if success:
                logger.info(f"Sent performance degradation alert for model {metrics.model_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send performance degradation alert: {str(e)}")
            return False
    
    def send_ab_test_completion_alert(self, experiment: ABTestExperiment) -> bool:
        """Send A/B test completion alert"""
        try:
            # Prepare alert data
            alert_data = {
                "alert_type": "ab_test_completed",
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.name,
                "control_model_id": experiment.control_model_id,
                "treatment_model_id": experiment.treatment_model_id,
                "primary_metric": experiment.primary_metric,
                "winner": experiment.winner,
                "statistical_significance": experiment.statistical_significance,
                "effect_size": experiment.effect_size,
                "p_value": experiment.p_value,
                "confidence_interval": experiment.confidence_interval,
                "decision_reason": experiment.decision_reason,
                "duration_days": experiment.duration_days,
                "control_metrics": experiment.control_metrics,
                "treatment_metrics": experiment.treatment_metrics
            }
            
            # Send through enabled channels
            success = True
            channels = self.notification_config.get("alerts", {}).get("ab_test_completed", {}).get("channels", [])
            
            for channel in channels:
                if channel == "email" and self.notification_config.get("channels", {}).get("email", {}).get("enabled"):
                    success &= self._send_email_alert(alert_data, "ab_test_completed")
                elif channel == "webhook" and self.notification_config.get("channels", {}).get("webhook", {}).get("enabled"):
                    success &= self._send_webhook_alert(alert_data)
            
            if success:
                logger.info(f"Sent A/B test completion alert for experiment {experiment.experiment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send A/B test completion alert: {str(e)}")
            return False
    
    def _send_email_alert(self, alert_data: Dict[str, Any], template_name: str) -> bool:
        """Send email alert"""
        try:
            email_config = self.notification_config.get("channels", {}).get("email", {})
            
            if not email_config.get("enabled"):
                return True  # Not an error, just disabled
            
            # Get email template
            template = self._get_email_template(template_name)
            if not template:
                logger.error(f"Email template not found: {template_name}")
                return False
            
            # Render email content
            subject = template.render(alert_data, type="subject")
            body = template.render(alert_data, type="body")
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = email_config.get("from_email", "noreply@traderai.com")
            msg['To'] = email_config.get("to_email", "admin@traderai.com")
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(email_config.get("smtp_server"), email_config.get("smtp_port", 587)) as server:
                server.starttls()
                if email_config.get("username") and email_config.get("password"):
                    server.login(email_config.get("username"), email_config.get("password"))
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False
    
    def _send_webhook_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send webhook alert"""
        try:
            webhook_config = self.notification_config.get("channels", {}).get("webhook", {})
            
            if not webhook_config.get("enabled"):
                return True  # Not an error, just disabled
            
            webhook_url = webhook_config.get("url")
            if not webhook_url:
                logger.error("Webhook URL not configured")
                return False
            
            # Prepare webhook payload
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "alert": alert_data,
                "source": "traderai-ml"
            }
            
            # Send webhook
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")
            return False
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send Slack alert"""
        try:
            slack_config = self.notification_config.get("channels", {}).get("slack", {})
            
            if not slack_config.get("enabled"):
                return True  # Not an error, just disabled
            
            webhook_url = slack_config.get("webhook_url")
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return False
            
            # Prepare Slack message
            message = self._format_slack_message(alert_data)
            
            # Send to Slack
            response = requests.post(
                webhook_url,
                json=message,
                timeout=30
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {str(e)}")
            return False
    
    def _get_email_template(self, template_name: str) -> Optional[Template]:
        """Get email template"""
        templates = {
            "drift_alert": Template("""
                {% if type == 'subject' %}🚨 ML Drift Alert: {{ model_name }}{% else %}
                <h2>🚨 ML Model Drift Detected</h2>
                <p><strong>Model:</strong> {{ model_name }} ({{ model_id }})</p>
                <p><strong>Version:</strong> {{ model_version }}</p>
                <p><strong>Drift Type:</strong> {{ drift_type }}</p>
                <p><strong>Drift Score:</strong> {{ "%.3f"|format(drift_score) }}</p>
                <p><strong>Severity:</strong> {{ severity.upper() }}</p>
                <p><strong>Detected At:</strong> {{ detected_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                
                {% if metrics %}
                <h3>Drift Metrics:</h3>
                <ul>
                {% for key, value in metrics.items() %}
                    <li><strong>{{ key }}:</strong> {{ value }}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                <p>Please investigate this drift and consider retraining the model if necessary.</p>
                <p>View details in the <a href="#">ML Dashboard</a>.</p>
                {% endif %}
            """),
            
            "training_failure": Template("""
                {% if type == 'subject' %}❌ Training Job Failed: {{ job_id }}{% else %}
                <h2>❌ ML Training Job Failed</h2>
                <p><strong>Job ID:</strong> {{ job_id }}</p>
                <p><strong>Model:</strong> {{ model_id }}</p>
                <p><strong>Version:</strong> {{ model_version }}</p>
                <p><strong>Job Type:</strong> {{ job_type }}</p>
                <p><strong>Started At:</strong> {{ started_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                <p><strong>Failed At:</strong> {{ failed_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                
                {% if duration_seconds %}
                <p><strong>Duration:</strong> {{ "%.1f"|format(duration_seconds / 60) }} minutes</p>
                {% endif %}
                
                {% if error_message %}
                <h3>Error Message:</h3>
                <pre>{{ error_message }}</pre>
                {% endif %}
                
                <p>Please check the training logs and investigate the failure.</p>
                <p>View details in the <a href="#">ML Dashboard</a>.</p>
                {% endif %}
            """),
            
            "performance_degradation": Template("""
                {% if type == 'subject' %}📉 Performance Degradation: {{ model_name }}{% else %}
                <h2>📉 Model Performance Degradation Detected</h2>
                <p><strong>Model:</strong> {{ model_name }} ({{ model_id }})</p>
                <p><strong>Version:</strong> {{ model_version }}</p>
                <p><strong>Evaluated At:</strong> {{ evaluated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                
                <h3>Performance Metrics:</h3>
                <ul>
                    <li><strong>Current Return:</strong> {{ "%.2f"|format(current_performance * 100) }}%</li>
                    <li><strong>Baseline Return:</strong> {{ "%.2f"|format(baseline_performance * 100) }}%</li>
                    <li><strong>Degradation:</strong> {{ "%.1f"|format(degradation_percentage) }}%</li>
                    <li><strong>Sharpe Ratio:</strong> {{ "%.2f"|format(sharpe_ratio or 0) }}</li>
                    <li><strong>Max Drawdown:</strong> {{ "%.2f"|format(max_drawdown or 0) }}</li>
                    <li><strong>Win Rate:</strong> {{ "%.2f"|format(win_rate or 0) }}</li>
                </ul>
                
                <p>The model performance has degraded significantly. Please consider retraining or investigation.</p>
                <p>View details in the <a href="#">ML Dashboard</a>.</p>
                {% endif %}
            """),
            
            "ab_test_completed": Template("""
                {% if type == 'subject' %}✅ A/B Test Completed: {{ experiment_name }}{% else %}
                <h2>✅ A/B Test Experiment Completed</h2>
                <p><strong>Experiment:</strong> {{ experiment_name }} ({{ experiment_id }})</p>
                <p><strong>Duration:</strong> {{ duration_days }} days</p>
                <p><strong>Primary Metric:</strong> {{ primary_metric }}</p>
                
                <h3>Results:</h3>
                <ul>
                    <li><strong>Winner:</strong> {{ winner.upper() }}</li>
                    <li><strong>Statistical Significance:</strong> {{ "Yes" if statistical_significance else "No" }}</li>
                    <li><strong>Effect Size:</strong> {{ "%.3f"|format(effect_size or 0) }}</li>
                    <li><strong>P-Value:</strong> {{ "%.3f"|format(p_value or 0) }}</li>
                </ul>
                
                {% if decision_reason %}
                <p><strong>Decision Reason:</strong> {{ decision_reason }}</p>
                {% endif %}
                
                <h3>Models:</h3>
                <ul>
                    <li><strong>Control:</strong> {{ control_model_id }}</li>
                    <li><strong>Treatment:</strong> {{ treatment_model_id }}</li>
                </ul>
                
                <p>View detailed results in the <a href="#">ML Dashboard</a>.</p>
                {% endif %}
            """)
        }
        
        return templates.get(template_name)
    
    def _format_slack_message(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format alert data for Slack"""
        alert_type = alert_data.get("alert_type")
        
        if alert_type == "drift_detected":
            return {
                "text": f"🚨 ML Drift Alert: {alert_data['model_name']}",
                "attachments": [{
                    "color": "danger" if alert_data['severity'] == 'high' else "warning",
                    "fields": [
                        {"title": "Model", "value": f"{alert_data['model_name']} ({alert_data['model_id']})", "short": True},
                        {"title": "Version", "value": alert_data['model_version'], "short": True},
                        {"title": "Drift Type", "value": alert_data['drift_type'], "short": True},
                        {"title": "Drift Score", "value": f"{alert_data['drift_score']:.3f}", "short": True},
                        {"title": "Severity", "value": alert_data['severity'].upper(), "short": True},
                        {"title": "Detected At", "value": alert_data['detected_at'].strftime('%Y-%m-%d %H:%M:%S'), "short": True}
                    ],
                    "actions": [{
                        "type": "button",
                        "text": "View in Dashboard",
                        "url": "https://your-dashboard-url.com/ml"
                    }]
                }]
            }
        
        elif alert_type == "training_failure":
            return {
                "text": f"❌ Training Job Failed: {alert_data['job_id']}",
                "attachments": [{
                    "color": "danger",
                    "fields": [
                        {"title": "Job ID", "value": alert_data['job_id'], "short": True},
                        {"title": "Model", "value": f"{alert_data['model_id']} v{alert_data['model_version']}", "short": True},
                        {"title": "Job Type", "value": alert_data['job_type'], "short": True},
                        {"title": "Failed At", "value": alert_data['failed_at'].strftime('%Y-%m-%d %H:%M:%S'), "short": True}
                    ],
                    "text": f"Error: {alert_data.get('error_message', 'Unknown error')}"
                }]
            }
        
        elif alert_type == "performance_degradation":
            return {
                "text": f"📉 Performance Degradation: {alert_data['model_name']}",
                "attachments": [{
                    "color": "warning",
                    "fields": [
                        {"title": "Model", "value": f"{alert_data['model_name']} ({alert_data['model_id']})", "short": True},
                        {"title": "Version", "value": alert_data['model_version'], "short": True},
                        {"title": "Degradation", "value": f"{alert_data['degradation_percentage']:.1f}%", "short": True},
                        {"title": "Current Return", "value": f"{alert_data['current_performance']:.2%}", "short": True},
                        {"title": "Baseline Return", "value": f"{alert_data['baseline_performance']:.2%}", "short": True},
                        {"title": "Sharpe Ratio", "value": f"{alert_data.get('sharpe_ratio', 0):.2f}", "short": True}
                    ]
                }]
            }
        
        elif alert_type == "ab_test_completed":
            return {
                "text": f"✅ A/B Test Completed: {alert_data['experiment_name']}",
                "attachments": [{
                    "color": "good",
                    "fields": [
                        {"title": "Experiment", "value": f"{alert_data['experiment_name']} ({alert_data['experiment_id']})", "short": True},
                        {"title": "Winner", "value": alert_data['winner'].upper(), "short": True},
                        {"title": "Statistical Significance", "value": "Yes" if alert_data['statistical_significance'] else "No", "short": True},
                        {"title": "Effect Size", "value": f"{alert_data.get('effect_size', 0):.3f}", "short": True},
                        {"title": "Duration", "value": f"{alert_data['duration_days']} days", "short": True},
                        {"title": "Primary Metric", "value": alert_data['primary_metric'], "short": True}
                    ],
                    "text": alert_data.get('decision_reason', '')
                }]
            }
        
        return {"text": f"ML Alert: {alert_type}"}
    
    def _get_drift_severity(self, drift_score: float) -> str:
        """Determine drift severity based on score"""
        if drift_score >= 0.8:
            return "high"
        elif drift_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def check_and_send_alerts(self) -> int:
        """Check for conditions that should trigger alerts and send them"""
        alerts_sent = 0
        
        try:
            # Check for recent drift alerts that haven't been notified
            recent_drifts = self.db.query(ModelDriftHistory).filter(
                ModelDriftHistory.detected_at >= datetime.utcnow() - timedelta(hours=1),
                ModelDriftHistory.status == "detected"
            ).all()
            
            for drift in recent_drifts:
                if self.send_drift_alert(drift):
                    alerts_sent += 1
            
            # Check for recent training failures
            recent_failures = self.db.query(TrainingJob).filter(
                TrainingJob.completed_at >= datetime.utcnow() - timedelta(hours=1),
                TrainingJob.status == "failed"
            ).all()
            
            for job in recent_failures:
                if self.send_training_failure_alert(job):
                    alerts_sent += 1
            
            # Check for performance degradation
            threshold = self.config.performance_monitoring.alerts.get("performance_degradation_threshold", 0.15)
            recent_metrics = self.db.query(ModelPerformanceMetrics).filter(
                ModelPerformanceMetrics.evaluated_at >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            for metrics in recent_metrics:
                # Get baseline performance (simplified - in practice would use historical baseline)
                baseline = 0.10  # 10% baseline return
                if metrics.total_return and baseline > 0:
                    degradation = (baseline - metrics.total_return) / baseline
                    if degradation >= threshold:
                        if self.send_performance_degradation_alert(metrics, baseline):
                            alerts_sent += 1
            
            # Check for completed A/B tests
            recent_ab_tests = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.ended_at >= datetime.utcnow() - timedelta(hours=1),
                ABTestExperiment.status == "completed"
            ).all()
            
            for experiment in recent_ab_tests:
                if self.send_ab_test_completion_alert(experiment):
                    alerts_sent += 1
            
            logger.info(f"Sent {alerts_sent} alerts")
            
        except Exception as e:
            logger.error(f"Error checking and sending alerts: {str(e)}")
        
        return alerts_sent
