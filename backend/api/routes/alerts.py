"""
Alert System API Routes
Manage price alerts, structure break notifications, and level touch alerts
Now using database for persistence
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
from services.email_service import email_service

from core.database_unified import get_db, Alert as AlertModel, AlertTrigger
from core.database import User  # User model is in database.py
from core.auth_dependencies import get_current_active_user, get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()

class AlertType:
    PRICE_LEVEL = "price_level"
    STRUCTURE_BREAK = "structure_break"
    ZONE_TOUCH = "zone_touch"
    TRENDLINE_BREAK = "trendline_break"

class AlertCondition:
    ABOVE = "above"
    BELOW = "below"
    CROSSES = "crosses"
    TOUCHES = "touches"

class Alert(BaseModel):
    """Alert configuration model (API)"""
    id: Optional[int] = None
    symbol: str = Field(..., description="Stock symbol")
    alert_type: str = Field(..., description="Type of alert")
    condition: str = Field(..., description="Alert condition")
    target_price: Optional[float] = Field(None, description="Target price for price alerts")
    level_id: Optional[str] = Field(None, description="S&R/S&D level ID")
    threshold_percent: float = Field(1.0, description="Distance threshold in %", ge=0.1, le=10)
    enabled: bool = Field(True, description="Whether alert is active")
    notify_browser: bool = Field(True, description="Show browser notification")
    notify_sound: bool = Field(True, description="Play sound")
    notify_email: bool = Field(False, description="Send email")
    name: Optional[str] = Field(None, description="Alert name")
    created_at: Optional[str] = None
    triggered_at: Optional[str] = None
    trigger_count: int = 0

class AlertResponse(BaseModel):
    """Response for alert operations"""
    success: bool
    message: str
    alert: Optional[Dict] = None
    alerts: Optional[List[Dict]] = None

def _alert_to_dict(db_alert: AlertModel) -> Dict:
    """Convert database Alert model to API dict format"""
    return {
        "id": str(db_alert.id),
        "symbol": db_alert.symbol,
        "alert_type": db_alert.condition_type or "price_level",
        "condition": db_alert.operator or "above",
        "target_price": db_alert.value,
        "threshold_percent": 1.0,  # Default, can be stored in metadata
        "enabled": db_alert.status == "active",
        "notify_browser": db_alert.notifications.get("browser", True) if db_alert.notifications else True,
        "notify_sound": db_alert.notifications.get("sound", True) if db_alert.notifications else True,
        "notify_email": db_alert.notifications.get("email", False) if db_alert.notifications else False,
        "name": db_alert.name,
        "created_at": db_alert.created_at.isoformat() if db_alert.created_at else None,
        "triggered_at": db_alert.last_triggered.isoformat() if db_alert.last_triggered else None,
        "trigger_count": db_alert.trigger_count or 0
    }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        active_count = db.query(AlertModel).filter(AlertModel.status == "active").count()
        total_count = db.query(AlertModel).count()
        
        return {
            "success": True,
            "service": "alerts",
            "status": "healthy",
            "active_alerts": active_count,
            "total_alerts": total_count
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "service": "alerts",
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/create")
async def create_alert(
    alert: Alert,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AlertResponse:
    """Create a new alert"""
    try:
        # Map API model to database model
        db_alert = AlertModel(
            user_id=current_user.id if current_user else None,
            symbol=alert.symbol,
            name=alert.name or f"{alert.symbol} {alert.alert_type}",
            condition_type=alert.alert_type,
            operator=alert.condition,
            value=alert.target_price or 0.0,
            custom_conditions={
                "level_id": alert.level_id,
                "threshold_percent": alert.threshold_percent
            } if alert.level_id or alert.threshold_percent != 1.0 else None,
            notifications={
                "browser": alert.notify_browser,
                "sound": alert.notify_sound,
                "email": alert.notify_email
            },
            status="active" if alert.enabled else "paused",
            trigger_count=0,
            alert_metadata={
                "level_id": alert.level_id,
                "threshold_percent": alert.threshold_percent
            }
        )
        
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        logger.info(f"✅ Created alert {db_alert.id} for {alert.symbol}")
        
        return AlertResponse(
            success=True,
            message=f"Alert created for {alert.symbol}",
            alert=_alert_to_dict(db_alert)
        )
        
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_alerts(
    symbol: Optional[str] = None,
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AlertResponse:
    """List all alerts, optionally filtered by symbol"""
    try:
        query = db.query(AlertModel)
        
        # Filter by user if authenticated
        if current_user:
            query = query.filter(AlertModel.user_id == current_user.id)
        
        # Filter by symbol if provided
        if symbol:
            query = query.filter(AlertModel.symbol == symbol)
        
        # Filter by enabled status
        if enabled_only:
            query = query.filter(AlertModel.status == "active")
        
        db_alerts = query.order_by(AlertModel.created_at.desc()).all()
        alerts = [_alert_to_dict(a) for a in db_alerts]
        
        return AlertResponse(
            success=True,
            message=f"Found {len(alerts)} alerts",
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{alert_id}")
async def update_alert(
    alert_id: str,
    enabled: Optional[bool] = Body(None),
    threshold_percent: Optional[float] = Body(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AlertResponse:
    """Update alert settings"""
    try:
        # Convert string ID to integer
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert ID format")
        
        query = db.query(AlertModel).filter(AlertModel.id == alert_id_int)
        
        # If user is authenticated, only allow updating their own alerts
        if current_user:
            query = query.filter(AlertModel.user_id == current_user.id)
        
        db_alert = query.first()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update fields
        if enabled is not None:
            db_alert.status = "active" if enabled else "paused"
        
        if threshold_percent is not None:
            if db_alert.alert_metadata:
                db_alert.alert_metadata["threshold_percent"] = threshold_percent
            else:
                db_alert.alert_metadata = {"threshold_percent": threshold_percent}
        
        db_alert.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_alert)
        
        return AlertResponse(
            success=True,
            message="Alert updated",
            alert=_alert_to_dict(db_alert)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AlertResponse:
    """Delete an alert"""
    try:
        # Convert string ID to integer
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert ID format")
        
        query = db.query(AlertModel).filter(AlertModel.id == alert_id_int)
        
        # If user is authenticated, only allow deleting their own alerts
        if current_user:
            query = query.filter(AlertModel.user_id == current_user.id)
        
        db_alert = query.first()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert_dict = _alert_to_dict(db_alert)
        db.delete(db_alert)
        db.commit()
        
        logger.info(f"🗑️ Deleted alert {alert_id}")
        
        return AlertResponse(
            success=True,
            message="Alert deleted",
            alert=alert_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check")
async def check_alerts(
    symbol: str = Body(...),
    current_price: float = Body(...),
    db: Session = Depends(get_db)
) -> Dict:
    """Check if any alerts should be triggered for current price"""
    try:
        triggered = []
        
        # Get all active alerts for this symbol
        active_alerts = db.query(AlertModel).filter(
            AlertModel.symbol == symbol,
            AlertModel.status == "active"
        ).all()
        
        for db_alert in active_alerts:
            # Check price level alerts
            if db_alert.condition_type == AlertType.PRICE_LEVEL and db_alert.value:
                target = db_alert.value
                threshold_percent = db_alert.alert_metadata.get("threshold_percent", 1.0) if db_alert.alert_metadata else 1.0
                threshold = target * (threshold_percent / 100)
                
                if abs(current_price - target) <= threshold:
                    # Create trigger record
                    trigger = AlertTrigger(
                        alert_id=db_alert.id,
                        user_id=db_alert.user_id,
                        symbol=symbol,
                        triggered_at=datetime.utcnow(),
                        condition_data={
                            "current_price": current_price,
                            "target_price": target,
                            "distance": abs(current_price - target),
                            "distance_percent": abs((current_price - target) / target * 100)
                        },
                        message=f"Price ₹{current_price:.2f} near target ₹{target:.2f}",
                        severity="medium"
                    )
                    db.add(trigger)
                    
                    # Update alert
                    db_alert.trigger_count = (db_alert.trigger_count or 0) + 1
                    db_alert.last_triggered = datetime.utcnow()
                    db.commit()
                    
                    alert_dict = _alert_to_dict(db_alert)
                    alert_info = {
                        'alert_id': str(db_alert.id),
                        'alert': alert_dict,
                        'message': f"Price ₹{current_price:.2f} near target ₹{target:.2f}",
                        'distance': abs(current_price - target),
                        'distance_percent': abs((current_price - target) / target * 100)
                    }
                    triggered.append(alert_info)
                    
                    # Send email notification if enabled
                    if db_alert.notifications and db_alert.notifications.get("email"):
                        if db_alert.user_id:
                            user = db.query(User).filter(User.id == db_alert.user_id).first()
                            if user and user.email:
                                try:
                                    email_service.send_alert_email(
                                        to_email=user.email,
                                        alert_data={
                                            'symbol': symbol,
                                            'current_price': current_price,
                                            'target_price': target,
                                            'condition': db_alert.operator or 'near',
                                            'alert_type': db_alert.condition_type,
                                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        }
                                    )
                                except Exception as email_error:
                                    logger.error(f"Error sending alert email: {email_error}")
        
        return {
            'success': True,
            'symbol': symbol,
            'current_price': current_price,
            'triggered_alerts': triggered,
            'triggered_count': len(triggered)
        }
        
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Dict:
    """Get recent alert trigger history"""
    try:
        query = db.query(AlertTrigger).order_by(AlertTrigger.triggered_at.desc())
        
        # Filter by user if authenticated
        if current_user:
            query = query.filter(AlertTrigger.user_id == current_user.id)
        
        triggers = query.limit(limit).all()
        
        history = [{
            'id': t.id,
            'alert_id': t.alert_id,
            'symbol': t.symbol,
            'triggered_at': t.triggered_at.isoformat() if t.triggered_at else None,
            'message': t.message,
            'severity': t.severity,
            'condition_data': t.condition_data
        } for t in triggers]
        
        return {
            'success': True,
            'history': history,
            'count': len(history)
        }
        
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear-all")
async def clear_all_alerts(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> AlertResponse:
    """Clear all alerts (use with caution!)"""
    try:
        query = db.query(AlertModel)
        
        # If user is authenticated, only clear their alerts
        if current_user:
            query = query.filter(AlertModel.user_id == current_user.id)
        
        count = query.count()
        query.delete(synchronize_session=False)
        db.commit()
        
        return AlertResponse(
            success=True,
            message=f"Cleared {count} alerts"
        )
        
    except Exception as e:
        logger.error(f"Error clearing alerts: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
