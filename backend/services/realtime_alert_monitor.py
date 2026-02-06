"""
Real-time Alert Monitoring Service
Continuously monitors market conditions and triggers alerts
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class RealTimeAlertMonitor:
    def __init__(self):
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        
    async def start_monitoring(self):
        """Start the real-time alert monitoring system"""
        if self.is_running:
            logger.warning("Alert monitoring is already running")
            return
        
        self.is_running = True
        logger.info("Starting real-time alert monitoring system")
        
        # Start main monitoring loop
        self.monitoring_tasks["main_loop"] = asyncio.create_task(
            self.main_monitoring_loop()
        )
        
        # Start alert cleanup task
        self.monitoring_tasks["cleanup_loop"] = asyncio.create_task(
            self.cleanup_expired_alerts()
        )
    
    async def stop_monitoring(self):
        """Stop the real-time alert monitoring system"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping real-time alert monitoring system")
        
        # Cancel all monitoring tasks
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled monitoring task: {task_name}")
        
        self.monitoring_tasks.clear()
    
    async def main_monitoring_loop(self):
        """Main monitoring loop that checks all active alerts"""
        try:
            while self.is_running:
                # Get all active alerts
                active_alerts = await self.get_active_alerts()
                
                if active_alerts:
                    # Process alerts in parallel
                    tasks = []
                    for alert_id, alert_data in active_alerts.items():
                        task = asyncio.create_task(
                            self.check_alert_condition(alert_id, alert_data)
                        )
                        tasks.append(task)
                    
                    # Wait for all alert checks to complete
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next check (every 10 seconds)
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            logger.info("Main monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in main monitoring loop: {e}")
    
    async def get_active_alerts(self) -> Dict[str, Dict[str, Any]]:
        """Get all active alerts from the alert system"""
        try:
            from services.alert_system import alert_system
            
            # Get all alerts from the alert system
            all_alerts = alert_system.get_all_alerts()
            
            # Filter active alerts
            active_alerts = {}
            for alert_id, alert_data in all_alerts.items():
                if alert_data.get("is_active", False):
                    active_alerts[alert_id] = alert_data
            
            return active_alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return {}
    
    async def check_alert_condition(self, alert_id: str, alert_data: Dict[str, Any]):
        """Check if an alert condition is met"""
        try:
            from services.alert_system import alert_system
            
            # Check if alert condition is met
            is_triggered = await alert_system.check_alert_condition(alert_id)
            
            if is_triggered:
                logger.info(f"Alert {alert_id} condition met - triggering alert")
                
                # Trigger the alert
                await alert_system.trigger_alert(alert_id)
                
                # Update alert status
                alert_data["last_triggered"] = datetime.now().isoformat()
                alert_data["trigger_count"] = alert_data.get("trigger_count", 0) + 1
                
        except Exception as e:
            logger.error(f"Error checking alert {alert_id}: {e}")
    
    async def cleanup_expired_alerts(self):
        """Clean up expired alerts"""
        try:
            while self.is_running:
                # Clean up alerts that are no longer active
                expired_alerts = []
                
                for alert_id, alert_data in self.active_alerts.items():
                    # Check if alert has expired
                    if self.is_alert_expired(alert_data):
                        expired_alerts.append(alert_id)
                
                # Remove expired alerts
                for alert_id in expired_alerts:
                    del self.active_alerts[alert_id]
                    logger.info(f"Removed expired alert: {alert_id}")
                
                # Wait before next cleanup (every 5 minutes)
                await asyncio.sleep(300)
                
        except asyncio.CancelledError:
            logger.info("Alert cleanup loop cancelled")
        except Exception as e:
            logger.error(f"Error in alert cleanup loop: {e}")
    
    def is_alert_expired(self, alert_data: Dict[str, Any]) -> bool:
        """Check if an alert has expired"""
        try:
            # Check if alert has an expiration date
            if "expires_at" in alert_data:
                expires_at = datetime.fromisoformat(alert_data["expires_at"])
                if datetime.now() > expires_at:
                    return True
            
            # Check if alert has reached max trigger count
            max_triggers = alert_data.get("max_triggers", 0)
            trigger_count = alert_data.get("trigger_count", 0)
            if max_triggers > 0 and trigger_count >= max_triggers:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert expiration: {e}")
            return False
    
    async def add_alert(self, alert_data: Dict[str, Any]) -> str:
        """Add a new alert to monitoring"""
        try:
            alert_id = alert_data.get("id", f"alert_{datetime.now().timestamp()}")
            
            # Validate alert data
            if not self.validate_alert_data(alert_data):
                raise ValueError("Invalid alert data")
            
            # Add to active alerts
            self.active_alerts[alert_id] = alert_data
            
            logger.info(f"Added alert {alert_id} to monitoring")
            return alert_id
            
        except Exception as e:
            logger.error(f"Error adding alert: {e}")
            raise
    
    async def remove_alert(self, alert_id: str):
        """Remove an alert from monitoring"""
        try:
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
                logger.info(f"Removed alert {alert_id} from monitoring")
            else:
                logger.warning(f"Alert {alert_id} not found in active alerts")
                
        except Exception as e:
            logger.error(f"Error removing alert {alert_id}: {e}")
    
    def validate_alert_data(self, alert_data: Dict[str, Any]) -> bool:
        """Validate alert data structure"""
        required_fields = ["symbol", "condition", "trigger_value", "user_id"]
        
        for field in required_fields:
            if field not in alert_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate condition type
        valid_conditions = [
            "price_above", "price_below", "price_equals",
            "volume_above", "volume_below",
            "change_percent_above", "change_percent_below"
        ]
        
        if alert_data["condition"] not in valid_conditions:
            logger.error(f"Invalid condition: {alert_data['condition']}")
            return False
        
        return True
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "is_running": self.is_running,
            "active_alerts_count": len(self.active_alerts),
            "monitoring_tasks": list(self.monitoring_tasks.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def force_check_all_alerts(self):
        """Force check all active alerts immediately"""
        try:
            active_alerts = await self.get_active_alerts()
            
            if active_alerts:
                tasks = []
                for alert_id, alert_data in active_alerts.items():
                    task = asyncio.create_task(
                        self.check_alert_condition(alert_id, alert_data)
                    )
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"Force checked {len(active_alerts)} alerts")
            else:
                logger.info("No active alerts to check")
                
        except Exception as e:
            logger.error(f"Error force checking alerts: {e}")

# Global alert monitor instance
alert_monitor = RealTimeAlertMonitor()
