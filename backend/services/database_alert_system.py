"""
Database-backed Alert System Service
Persistent storage for alerts and triggers using SQLAlchemy models
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.database import get_db, Alert, AlertTrigger, User
from core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

class AlertConditionType(Enum):
    PRICE = "price"
    INDICATOR = "indicator"
    VOLUME = "volume"
    PATTERN = "pattern"
    CUSTOM = "custom"
    SMART_MONEY_VOLUME = "smart_money_volume"

class AlertOperator(Enum):
    ABOVE = "above"
    BELOW = "below"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"

class AlertStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    DISABLED = "disabled"

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    IN_APP = "in_app"

class DatabaseAlertSystemService:
    def __init__(self):
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        self.monitoring_interval = 5  # seconds
        
        # Notification handlers
        self.notification_handlers = {
            NotificationType.EMAIL: self._send_email_notification,
            NotificationType.SMS: self._send_sms_notification,
            NotificationType.WEBHOOK: self._send_webhook_notification,
            NotificationType.PUSH: self._send_push_notification,
            NotificationType.IN_APP: self._send_in_app_notification
        }
        
        # Price data cache for monitoring
        self.price_cache = {}
        self.cache_ttl = 60  # seconds
        
        # WebSocket connections for real-time notifications
        self.websocket_connections = {}
        
        # Alert templates
        self.alert_templates = {
            "price_breakout": {
                "name": "Price Breakout",
                "description": "Alert when price breaks above/below a level",
                "default_condition": {
                    "type": "price",
                    "operator": "crosses_above",
                    "value": 0
                }
            },
            "rsi_overbought": {
                "name": "RSI Overbought",
                "description": "Alert when RSI goes above 70",
                "default_condition": {
                    "type": "indicator",
                    "indicator": "rsi",
                    "operator": "above",
                    "value": 70
                }
            },
            "rsi_oversold": {
                "name": "RSI Oversold",
                "description": "Alert when RSI goes below 30",
                "default_condition": {
                    "type": "indicator",
                    "indicator": "rsi",
                    "operator": "below",
                    "value": 30
                }
            },
            "volume_spike": {
                "name": "Volume Spike",
                "description": "Alert when volume exceeds average by 200%",
                "default_condition": {
                    "type": "volume",
                    "operator": "greater_than",
                    "value": 0
                }
            },
            "macd_crossover": {
                "name": "MACD Crossover",
                "description": "Alert when MACD line crosses signal line",
                "default_condition": {
                    "type": "indicator",
                    "indicator": "macd",
                    "operator": "crosses_above",
                    "value": 0
                }
            },
            "smart_money_bullish": {
                "name": "Smart Money Bullish Activity",
                "description": "Alert when Smart Money shows bullish volume activity",
                "default_condition": {
                    "type": "smart_money_volume",
                    "operator": "equals",
                    "value": "smart_money_bullish"
                }
            },
            "smart_money_bearish": {
                "name": "Smart Money Bearish Activity",
                "description": "Alert when Smart Money shows bearish volume activity",
                "default_condition": {
                    "type": "smart_money_volume",
                    "operator": "equals",
                    "value": "smart_money_bearish"
                }
            },
            "retail_bullish": {
                "name": "Retail Bullish Activity",
                "description": "Alert when Retail shows bullish volume activity",
                "default_condition": {
                    "type": "smart_money_volume",
                    "operator": "equals",
                    "value": "retail_bullish"
                }
            },
            "retail_bearish": {
                "name": "Retail Bearish Activity",
                "description": "Alert when Retail shows bearish volume activity",
                "default_condition": {
                    "type": "smart_money_volume",
                    "operator": "equals",
                    "value": "retail_bearish"
                }
            }
        }
    
    async def create_alert(
        self,
        user_id: int,
        symbol: str,
        condition_type: str,
        operator: str,
        value: float,
        notifications: Dict[str, bool],
        cooldown_minutes: int = 30,
        name: Optional[str] = None,
        custom_conditions: Optional[List[Dict]] = None,
        expiry_date: Optional[datetime] = None,
        db: Session = None
    ) -> str:
        """Create new alert in database"""
        try:
            # Validate inputs
            if condition_type not in [e.value for e in AlertConditionType]:
                raise ValueError(f"Invalid condition type: {condition_type}")
            
            if operator not in [e.value for e in AlertOperator]:
                raise ValueError(f"Invalid operator: {operator}")
            
            # Generate unique alert ID
            alert_id = f"alert_{user_id}_{symbol}_{uuid.uuid4().hex[:8]}"
            
            # Create alert data
            alert_data = {
                "id": alert_id,
                "user_id": user_id,
                "symbol": symbol,
                "name": name or f"Alert for {symbol}",
                "condition_type": condition_type,
                "operator": operator,
                "value": value,
                "custom_conditions": json.dumps(custom_conditions or []),
                "notifications": json.dumps(notifications),
                "cooldown_minutes": cooldown_minutes,
                "status": AlertStatus.ACTIVE.value,
                "trigger_count": 0,
                "last_triggered": None,
                "expiry_date": expiry_date,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "alert_metadata": json.dumps({
                    "version": "1.0",
                    "created_by": "charting_system"
                })
            }
            
            # Store in database
            if db:
                db_alert = Alert(**alert_data)
                db.add(db_alert)
                db.commit()
                db.refresh(db_alert)
            
            # Start monitoring if not already running
            if not self.is_monitoring:
                await self.start_monitoring()
            
            logger.info(f"Alert {alert_id} created for user {user_id}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    async def get_user_alerts(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get all alerts for user from database"""
        try:
            alerts = db.query(Alert).filter(Alert.user_id == user_id).order_by(Alert.created_at.desc()).all()
            
            result = []
            for alert in alerts:
                alert_dict = {
                    "id": alert.id,
                    "user_id": alert.user_id,
                    "symbol": alert.symbol,
                    "name": alert.name,
                    "condition_type": alert.condition_type,
                    "operator": alert.operator,
                    "value": alert.value,
                    "custom_conditions": json.loads(alert.custom_conditions or "[]"),
                    "notifications": json.loads(alert.notifications or "{}"),
                    "cooldown_minutes": alert.cooldown_minutes,
                    "status": alert.status,
                    "trigger_count": alert.trigger_count,
                    "last_triggered": alert.last_triggered,
                    "expiry_date": alert.expiry_date,
                    "created_at": alert.created_at,
                    "updated_at": alert.updated_at,
                    "metadata": json.loads(alert.alert_metadata or "{}")
                }
                result.append(alert_dict)
            
            logger.info(f"Retrieved {len(result)} alerts for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting user alerts: {e}")
            return []
    
    async def get_alert(self, alert_id: str, user_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Get specific alert by ID from database"""
        try:
            alert = db.query(Alert).filter(
                and_(Alert.id == alert_id, Alert.user_id == user_id)
            ).first()
            
            if not alert:
                return None
            
            return {
                "id": alert.id,
                "user_id": alert.user_id,
                "symbol": alert.symbol,
                "name": alert.name,
                "condition_type": alert.condition_type,
                "operator": alert.operator,
                "value": alert.value,
                "custom_conditions": json.loads(alert.custom_conditions or "[]"),
                "notifications": json.loads(alert.notifications or "{}"),
                "cooldown_minutes": alert.cooldown_minutes,
                "status": alert.status,
                "trigger_count": alert.trigger_count,
                "last_triggered": alert.last_triggered,
                "expiry_date": alert.expiry_date,
                "created_at": alert.created_at,
                "updated_at": alert.updated_at,
                "metadata": json.loads(alert.alert_metadata or "{}")
            }
            
        except Exception as e:
            logger.error(f"Error getting alert {alert_id}: {e}")
            return None
    
    async def update_alert(
        self, 
        alert_id: str, 
        user_id: int, 
        updates: Dict[str, Any],
        db: Session
    ) -> bool:
        """Update alert in database"""
        try:
            alert = db.query(Alert).filter(
                and_(Alert.id == alert_id, Alert.user_id == user_id)
            ).first()
            
            if not alert:
                return False
            
            # Update allowed fields
            allowed_fields = [
                "name", "condition_type", "operator", "value", 
                "notifications", "cooldown_minutes", "custom_conditions",
                "expiry_date", "status"
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field in ["notifications", "custom_conditions"]:
                        setattr(alert, field, json.dumps(value))
                    else:
                        setattr(alert, field, value)
            
            alert.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Alert {alert_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {e}")
            return False
    
    async def delete_alert(self, alert_id: str, user_id: int, db: Session) -> bool:
        """Delete alert from database"""
        try:
            alert = db.query(Alert).filter(
                and_(Alert.id == alert_id, Alert.user_id == user_id)
            ).first()
            
            if not alert:
                return False
            
            db.delete(alert)
            db.commit()
            
            logger.info(f"Alert {alert_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting alert {alert_id}: {e}")
            return False
    
    async def create_smv_alert(
        self,
        user_id: int,
        symbol: str,
        activity_type: str,
        notifications: Dict[str, bool] = None,
        cooldown_minutes: int = 30,
        db: Session = None
    ) -> str:
        """Create Smart Money Volume alert"""
        try:
            if notifications is None:
                notifications = {"in_app": True, "email": False}
            
            return await self.create_alert(
                user_id=user_id,
                symbol=symbol,
                condition_type="smart_money_volume",
                operator="equals",
                value=activity_type,
                notifications=notifications,
                cooldown_minutes=cooldown_minutes,
                name=f"SMV {activity_type.replace('_', ' ').title()} Alert for {symbol}",
                db=db
            )
            
        except Exception as e:
            logger.error(f"Error creating SMV alert: {e}")
            raise
    
    async def send_smv_realtime_alert(
        self,
        user_id: int,
        symbol: str,
        smv_data: Dict[str, Any]
    ):
        """Send real-time SMV alert via WebSocket"""
        try:
            bubble = smv_data.get("bubble", {})
            levels = smv_data.get("levels", [])
            
            if not bubble:
                return
            
            # Create alert message
            class_type = bubble.get("class", "")
            direction = bubble.get("dir", 0)
            z_score = bubble.get("max_abs_z", 0)
            price = bubble.get("price", 0)
            
            direction_text = "Bullish" if direction == 1 else "Bearish"
            
            alert_message = {
                "type": "smart_money_volume_alert",
                "symbol": symbol,
                "class": class_type,
                "direction": direction_text,
                "z_score": z_score,
                "price": price,
                "levels_count": len(levels),
                "message": f"🚨 SMV Alert: {symbol} - {class_type} {direction_text} activity detected (Z-score: {z_score:.2f})",
                "timestamp": datetime.now().isoformat(),
                "severity": "high" if z_score > 3.0 else "medium"
            }
            
            # Send via WebSocket
            await self._send_smv_websocket_alert(user_id, alert_message)
            
            logger.info(f"SMV real-time alert sent for {symbol}: {class_type} {direction_text}")
            
        except Exception as e:
            logger.error(f"Error sending SMV real-time alert: {e}")
    
    async def _send_smv_websocket_alert(self, user_id: int, alert_message: Dict[str, Any]):
        """Send SMV alert via WebSocket"""
        try:
            # Import WebSocket manager
            from core.websocket_manager import websocket_manager
            
            # Send SMV alert via WebSocket
            await websocket_manager.send_alert(str(user_id), alert_message)
            
            logger.info(f"SMV WebSocket alert sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending SMV WebSocket alert: {e}")
    
    async def add_websocket_connection(self, user_id: int, websocket):
        """Add WebSocket connection for real-time notifications"""
        try:
            user_key = f"user_{user_id}"
            self.websocket_connections[user_key] = websocket
            logger.info(f"WebSocket connection added for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding WebSocket connection: {e}")
    
    async def remove_websocket_connection(self, user_id: int):
        """Remove WebSocket connection"""
        try:
            user_key = f"user_{user_id}"
            if user_key in self.websocket_connections:
                del self.websocket_connections[user_key]
                logger.info(f"WebSocket connection removed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error removing WebSocket connection: {e}")
    
    async def start_monitoring(self):
        """Start monitoring alerts"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitor_alerts())
        logger.info("Alert monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring alerts"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Alert monitoring stopped")
    
    async def _monitor_alerts(self):
        """Monitor alerts in background"""
        while self.is_monitoring:
            try:
                # Get all active alerts from database
                db = next(get_db())
                try:
                    active_alerts = db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE.value).all()
                    
                    # Check each alert
                    for alert in active_alerts:
                        await self._check_alert_condition(alert, db)
                    
                finally:
                    db.close()
                
                # Wait before next check
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _check_alert_condition(self, alert: Alert, db: Session):
        """Check if alert condition is met"""
        try:
            symbol = alert.symbol
            condition_type = alert.condition_type
            operator = alert.operator
            value = alert.value
            
            # Get current value for symbol
            current_value = await self._get_current_value(symbol, condition_type)
            
            if current_value is None:
                return
            
            # Check condition
            condition_met = self._evaluate_condition(
                current_value,
                operator,
                value,
                json.loads(alert.custom_conditions or "[]")
            )
            
            if condition_met and self._can_trigger_alert(alert):
                await self._trigger_alert(alert, current_value, db)
                
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {e}")
    
    def _evaluate_condition(
        self, 
        current_value: float, 
        operator: str, 
        target_value: float,
        custom_conditions: List[Dict] = None
    ) -> bool:
        """Evaluate alert condition"""
        try:
            # Handle multi-condition alerts
            if custom_conditions:
                return self._evaluate_multi_condition(current_value, custom_conditions)
            
            # Single condition evaluation
            if operator == AlertOperator.ABOVE.value:
                return current_value > target_value
            elif operator == AlertOperator.BELOW.value:
                return current_value < target_value
            elif operator == AlertOperator.CROSSES_ABOVE.value:
                # Would need previous value to detect crossing
                return False  # Simplified for now
            elif operator == AlertOperator.CROSSES_BELOW.value:
                # Would need previous value to detect crossing
                return False  # Simplified for now
            elif operator == AlertOperator.EQUALS.value:
                return abs(current_value - target_value) < 0.01
            elif operator == AlertOperator.NOT_EQUALS.value:
                return abs(current_value - target_value) >= 0.01
            elif operator == AlertOperator.GREATER_THAN.value:
                return current_value > target_value
            elif operator == AlertOperator.LESS_THAN.value:
                return current_value < target_value
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _evaluate_multi_condition(self, current_value: float, conditions: List[Dict]) -> bool:
        """Evaluate multi-condition alert"""
        try:
            # Simple AND logic for now
            for condition in conditions:
                if not self._evaluate_condition(
                    current_value,
                    condition.get("operator", "above"),
                    condition.get("value", 0)
                ):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating multi-condition: {e}")
            return False
    
    def _can_trigger_alert(self, alert: Alert) -> bool:
        """Check if alert can be triggered (cooldown)"""
        try:
            if not alert.last_triggered:
                return True
            
            last_triggered = alert.last_triggered
            cooldown_end = last_triggered + timedelta(minutes=alert.cooldown_minutes)
            
            return datetime.now() > cooldown_end
            
        except Exception as e:
            logger.error(f"Error checking alert cooldown: {e}")
            return True
    
    async def _trigger_alert(self, alert: Alert, current_value: float, db: Session):
        """Trigger alert and send notifications"""
        try:
            # Update alert
            alert.trigger_count += 1
            alert.last_triggered = datetime.now()
            db.commit()
            
            # Create trigger record
            trigger_id = f"trigger_{alert.id}_{uuid.uuid4().hex[:8]}"
            trigger_data = {
                "id": trigger_id,
                "alert_id": alert.id,
                "user_id": alert.user_id,
                "symbol": alert.symbol,
                "triggered_at": datetime.now(),
                "condition_data": json.dumps({
                    "condition_type": alert.condition_type,
                    "operator": alert.operator,
                    "target_value": alert.value,
                    "current_value": current_value
                }),
                "message": self._generate_alert_message(alert, current_value),
                "severity": "medium"
            }
            
            db_trigger = AlertTrigger(**trigger_data)
            db.add(db_trigger)
            db.commit()
            
            # Send notifications
            await self._send_notifications(alert, trigger_data)
            
            # Send real-time notification via WebSocket
            await self._send_realtime_notification(alert.user_id, trigger_data)
            
            logger.info(f"Alert {alert.id} triggered: {alert.symbol} {alert.operator} {alert.value}")
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    def _generate_alert_message(self, alert: Alert, current_value: float) -> str:
        """Generate alert message"""
        try:
            symbol = alert.symbol
            operator = alert.operator
            target_value = alert.value
            current_value = round(current_value, 2)
            target_value = round(target_value, 2)
            
            if operator == "above":
                message = f"🚨 ALERT: {symbol} is now {current_value}, above target {target_value}"
            elif operator == "below":
                message = f"🚨 ALERT: {symbol} is now {current_value}, below target {target_value}"
            elif operator == "crosses_above":
                message = f"🚨 ALERT: {symbol} crossed above {target_value} (current: {current_value})"
            elif operator == "crosses_below":
                message = f"🚨 ALERT: {symbol} crossed below {target_value} (current: {current_value})"
            else:
                message = f"🚨 ALERT: {symbol} condition met (current: {current_value}, target: {target_value})"
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating alert message: {e}")
            return f"Alert triggered for {alert.symbol}"
    
    async def _send_notifications(self, alert: Alert, trigger_data: Dict[str, Any]):
        """Send notifications based on alert settings"""
        try:
            notifications = json.loads(alert.notifications or "{}")
            message = trigger_data["message"]
            
            for notification_type, enabled in notifications.items():
                if enabled and notification_type in self.notification_handlers:
                    try:
                        await self.notification_handlers[notification_type](
                            alert.user_id, 
                            message, 
                            trigger_data
                        )
                    except Exception as e:
                        logger.error(f"Error sending {notification_type} notification: {e}")
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    async def _send_email_notification(self, user_id: int, message: str, trigger_data: Dict[str, Any]):
        """Send email notification"""
        try:
            # This would integrate with your email service
            # For now, just log
            logger.info(f"Email notification sent to user {user_id}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_sms_notification(self, user_id: int, message: str, trigger_data: Dict[str, Any]):
        """Send SMS notification"""
        try:
            # This would integrate with your SMS service
            # For now, just log
            logger.info(f"SMS notification sent to user {user_id}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
    
    async def _send_webhook_notification(self, user_id: int, message: str, trigger_data: Dict[str, Any]):
        """Send webhook notification"""
        try:
            # This would send to configured webhook URL
            # For now, just log
            logger.info(f"Webhook notification sent for user {user_id}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    async def _send_push_notification(self, user_id: int, message: str, trigger_data: Dict[str, Any]):
        """Send push notification"""
        try:
            # This would integrate with push notification service
            # For now, just log
            logger.info(f"Push notification sent to user {user_id}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
    
    async def _send_in_app_notification(self, user_id: int, message: str, trigger_data: Dict[str, Any]):
        """Send in-app notification"""
        try:
            # This would send to user's active WebSocket connection
            await self._send_realtime_notification(user_id, trigger_data)
            
        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
    
    async def _send_realtime_notification(self, user_id: int, trigger_data: Dict[str, Any]):
        """Send real-time notification via WebSocket"""
        try:
            # Import WebSocket manager
            from core.websocket_manager import websocket_manager
            
            # Send alert via WebSocket
            await websocket_manager.send_alert(str(user_id), {
                "alert_id": trigger_data.get("alert_id"),
                "symbol": trigger_data.get("symbol"),
                "condition": trigger_data.get("condition"),
                "current_value": trigger_data.get("current_value"),
                "trigger_value": trigger_data.get("trigger_value"),
                "message": trigger_data.get("message"),
                "severity": trigger_data.get("severity", "medium"),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Real-time alert sent to user {user_id} via WebSocket")
            
        except Exception as e:
            logger.error(f"Error sending real-time notification: {e}")
    
    async def _get_current_value(self, symbol: str, condition_type: str) -> Optional[float]:
        """Get current value for symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{condition_type}"
            if cache_key in self.price_cache:
                cached_data, timestamp = self.price_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Handle SMV-specific conditions
            if condition_type == "smart_money_volume":
                return await self._get_smv_activity_value(symbol)
            
            # Get current value (this would integrate with your data service)
            current_value = await self._fetch_current_value(symbol, condition_type)
            
            # Cache the result
            self.price_cache[cache_key] = (current_value, datetime.now().timestamp())
            
            return current_value
            
        except Exception as e:
            logger.error(f"Error getting current value for {symbol}: {e}")
            return None
    
    async def _get_smv_activity_value(self, symbol: str) -> Optional[str]:
        """Get current Smart Money Volume activity for symbol"""
        try:
            # Import Smart Money Volume service
            from services.smart_money_volume import SmartMoneyVolumeService
            
            smv_service = SmartMoneyVolumeService()
            
            # Get SMV analysis
            smv_data = await smv_service.analyze_volume_activity(
                symbol=symbol,
                timeframe="1D",
                lower_timeframe="5m",
                z_len=50,
                threshold_abs=2.0,
                who="Both"
            )
            
            if "error" in smv_data:
                return None
            
            # Determine activity type based on bubble data
            bubble = smv_data.get("bubble", {})
            if not bubble:
                return None
            
            class_type = bubble.get("class", "")
            direction = bubble.get("dir", 0)
            
            # Map to alert values
            if class_type == "Smart Money" and direction == 1:
                return "smart_money_bullish"
            elif class_type == "Smart Money" and direction == -1:
                return "smart_money_bearish"
            elif class_type == "Retail" and direction == 1:
                return "retail_bullish"
            elif class_type == "Retail" and direction == -1:
                return "retail_bearish"
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting SMV activity for {symbol}: {e}")
            return None
    
    async def _fetch_current_value(self, symbol: str, condition_type: str) -> Optional[float]:
        """Fetch current value from enhanced data service"""
        try:
            # Import enhanced data service
            from core.data_service import data_service
            
            # Get live quote
            quote = await data_service.get_quote(symbol, exchange="NSE")
            
            if quote and "error" not in quote:
                # Return appropriate value based on condition type
                if condition_type in ["price_above", "price_below", "price_equals"]:
                    return quote.get("last_price")
                elif condition_type in ["volume_above", "volume_below"]:
                    return quote.get("volume")
                elif condition_type in ["change_percent_above", "change_percent_below"]:
                    return quote.get("change_percent")
                else:
                    return quote.get("last_price")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current value for {symbol}: {e}")
            return None
    
    def get_alert_templates(self) -> Dict[str, Any]:
        """Get available alert templates"""
        return self.alert_templates
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            # Test basic functionality
            self._evaluate_condition(105, "above", 100)
            return True
        except Exception:
            return False

# Create global instance
database_alert_system = DatabaseAlertSystemService()
