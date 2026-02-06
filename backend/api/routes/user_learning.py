"""
User Learning API Routes
Endpoints for user feedback and behavior tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from core.database_unified import get_db, User
from core.auth_dependencies import get_current_active_user
from services.user_learning_service import user_learning_service

router = APIRouter()

# Request/Response Models
class FeedbackRequest(BaseModel):
    entity_type: str  # 'prediction', 'recommendation', 'analysis'
    entity_id: str
    feedback_type: str  # 'helpful', 'not_helpful', 'accurate', 'inaccurate', 'useful', 'not_useful'
    symbol: Optional[str] = None
    rating: Optional[int] = None  # 1-5
    comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BehaviorTrackingRequest(BaseModel):
    action_type: str  # 'viewed_prediction', 'followed_recommendation', 'ignored_recommendation', 'placed_order', 'viewed_analysis'
    entity_type: str  # 'prediction', 'recommendation', 'analysis', 'order'
    entity_id: str
    symbol: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    referrer: Optional[str] = None

@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit user feedback on predictions/recommendations"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        
        result = user_learning_service.submit_feedback(
            db=db,
            user_id=user_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            feedback_type=request.feedback_type,
            symbol=request.symbol,
            rating=request.rating,
            comment=request.comment,
            metadata=request.metadata
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to submit feedback"))
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.post("/behavior")
async def track_behavior(
    request: BehaviorTrackingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Track user behavior"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        
        result = user_learning_service.track_behavior(
            db=db,
            user_id=user_id,
            action_type=request.action_type,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            symbol=request.symbol,
            metadata=request.metadata,
            session_id=request.session_id,
            referrer=request.referrer
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to track behavior"))
        
        return {
            "success": True,
            "message": "Behavior tracked successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking behavior: {str(e)}")

@router.get("/feedback/stats")
async def get_feedback_stats(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user feedback statistics"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        
        stats = user_learning_service.get_user_feedback_stats(db, user_id, days)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feedback stats: {str(e)}")

@router.get("/behavior/insights")
async def get_behavior_insights(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user behavior insights"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        
        insights = user_learning_service.get_user_behavior_insights(db, user_id, days)
        
        return {
            "success": True,
            "data": insights
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting behavior insights: {str(e)}")

@router.get("/preferences/inferred")
async def get_inferred_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get inferred user preferences from feedback and behavior"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user")
        
        preferences = user_learning_service.infer_user_preferences(db, user_id)
        
        return {
            "success": True,
            "data": preferences
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inferring preferences: {str(e)}")

