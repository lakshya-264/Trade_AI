"""
Session Management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pydantic import BaseModel
import logging

from core.database_unified import get_db, User, UserSession
from core.auth_dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

class SessionResponse(BaseModel):
    id: str
    device_info: str | None
    ip_address: str | None
    user_agent: str | None
    is_active: bool
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True

@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for current user"""
    try:
        user_id = current_user.get("id")
        current_session_id = current_user.get("session_id")
        
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).order_by(UserSession.created_at.desc()).all()
        
        result = []
        for session in sessions:
            session_dict = {
                "id": session.id,
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "is_active": session.is_active,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "expires_at": session.expires_at,
                "is_current": session.session_token == current_session_id if current_session_id else False
            }
            result.append(SessionResponse(**session_dict))
        
        return result
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    try:
        user_id = current_user.get("id")
        
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.is_active = False
        db.commit()
        
        logger.info(f"Session {session_id} revoked by user {user_id}")
        return {"message": "Session revoked successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}"
        )

@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke all sessions for current user (except current session)"""
    try:
        user_id = current_user.get("id")
        current_session_id = current_user.get("session_id")
        
        # Revoke all sessions except current
        query = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        )
        
        if current_session_id:
            query = query.filter(UserSession.session_token != current_session_id)
        
        sessions_revoked = query.update({"is_active": False})
        db.commit()
        
        logger.info(f"All sessions revoked for user {user_id} (except current)")
        return {
            "message": f"Revoked {sessions_revoked} session(s)",
            "sessions_revoked": sessions_revoked,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke sessions: {str(e)}"
        )

