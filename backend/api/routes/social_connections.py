"""
Social Connections API Routes
Handles user connections, friend requests, and social networking features
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime
import logging

from core.database_unified import get_db
from core.database_unified import User, UserConnection
from core.auth_dependencies import get_current_user
from schemas.social_connections import (
    ConnectionRequest,
    ConnectionResponse,
    ConnectionStatus,
    UserProfileResponse,
    ConnectionListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/social", tags=["social"])


@router.post("/connections/request", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def send_connection_request(
    request: ConnectionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a connection request to another user"""
    try:
        requester_id = current_user.get("id") or current_user.get("user_id")
        if not requester_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        receiver_id = request.user_id
        
        # Check if user exists
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Can't send request to yourself
        if requester_id == receiver_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send connection request to yourself")
        
        # Check if connection already exists
        existing = db.query(UserConnection).filter(
            or_(
                and_(UserConnection.requester_id == requester_id, UserConnection.receiver_id == receiver_id),
                and_(UserConnection.requester_id == receiver_id, UserConnection.receiver_id == requester_id)
            )
        ).first()
        
        if existing:
            if existing.status == "accepted":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already connected")
            elif existing.status == "pending":
                if existing.requester_id == requester_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connection request already sent")
                else:
                    # Auto-accept if the other user already sent a request
                    existing.status = "accepted"
                    existing.updated_at = datetime.utcnow()
                    db.commit()
                    db.refresh(existing)
                    return ConnectionResponse(
                        id=existing.id,
                        requester_id=existing.requester_id,
                        receiver_id=existing.receiver_id,
                        status=existing.status,
                        created_at=existing.created_at,
                        updated_at=existing.updated_at
                    )
            elif existing.status == "rejected":
                # Allow resending after rejection
                existing.status = "pending"
                existing.requester_id = requester_id
                existing.receiver_id = receiver_id
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                return ConnectionResponse(
                    id=existing.id,
                    requester_id=existing.requester_id,
                    receiver_id=existing.receiver_id,
                    status=existing.status,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at
                )
        
        # Create new connection request
        connection = UserConnection(
            requester_id=requester_id,
            receiver_id=receiver_id,
            status="pending"
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        return ConnectionResponse(
            id=connection.id,
            requester_id=connection.requester_id,
            receiver_id=connection.receiver_id,
            status=connection.status,
            created_at=connection.created_at,
            updated_at=connection.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending connection request: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/connections/{connection_id}/accept", response_model=ConnectionResponse)
async def accept_connection_request(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a connection request"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found")
        
        # Only receiver can accept
        if connection.receiver_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the receiver can accept the request")
        
        if connection.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Connection request is already {connection.status}")
        
        connection.status = "accepted"
        connection.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(connection)
        
        return ConnectionResponse(
            id=connection.id,
            requester_id=connection.requester_id,
            receiver_id=connection.receiver_id,
            status=connection.status,
            created_at=connection.created_at,
            updated_at=connection.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting connection request: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/connections/{connection_id}/reject", response_model=ConnectionResponse)
async def reject_connection_request(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a connection request"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found")
        
        # Only receiver can reject
        if connection.receiver_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the receiver can reject the request")
        
        if connection.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Connection request is already {connection.status}")
        
        connection.status = "rejected"
        connection.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(connection)
        
        return ConnectionResponse(
            id=connection.id,
            requester_id=connection.requester_id,
            receiver_id=connection.receiver_id,
            status=connection.status,
            created_at=connection.created_at,
            updated_at=connection.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting connection request: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connection(
    connection_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a connection (unfriend)"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
        
        # Either user can remove the connection
        if connection.requester_id != user_id and connection.receiver_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to remove this connection")
        
        db.delete(connection)
        db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing connection: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/connections", response_model=ConnectionListResponse)
async def get_connections(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all connections for the current user"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        query = db.query(UserConnection).filter(
            or_(
                UserConnection.requester_id == user_id,
                UserConnection.receiver_id == user_id
            )
        )
        
        if status_filter:
            query = query.filter(UserConnection.status == status_filter)
        
        connections = query.all()
        
        # Get user details for each connection
        connection_list = []
        for conn in connections:
            other_user_id = conn.receiver_id if conn.requester_id == user_id else conn.requester_id
            other_user = db.query(User).filter(User.id == other_user_id).first()
            
            if other_user:
                connection_list.append({
                    "id": conn.id,
                    "user": {
                        "id": other_user.id,
                        "username": other_user.username,
                        "email": other_user.email,
                        "created_at": other_user.created_at.isoformat() if other_user.created_at else None
                    },
                    "status": conn.status,
                    "is_requester": conn.requester_id == user_id,
                    "created_at": conn.created_at.isoformat() if conn.created_at else None,
                    "updated_at": conn.updated_at.isoformat() if conn.updated_at else None
                })
        
        return ConnectionListResponse(
            connections=connection_list,
            total=len(connection_list)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/users/search", response_model=List[UserProfileResponse])
async def search_users(
    q: str = Query(..., min_length=1, description="Search query (username or email)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for users by username or email"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        search_term = f"%{q}%"
        users = db.query(User).filter(
            and_(
                User.id != user_id,
                User.is_active == True,
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        ).limit(50).all()
        
        # Get connection status for each user
        user_list = []
        for user in users:
            # Check connection status
            connection = db.query(UserConnection).filter(
                or_(
                    and_(UserConnection.requester_id == user_id, UserConnection.receiver_id == user.id),
                    and_(UserConnection.requester_id == user.id, UserConnection.receiver_id == user_id)
                )
            ).first()
            
            connection_status = None
            if connection:
                connection_status = connection.status
            
            user_list.append(UserProfileResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at,
                connection_status=connection_status
            ))
        
        return user_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile by ID"""
    try:
        current_user_id = current_user.get("id") or current_user.get("user_id")
        if not current_user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get connection status
        connection = db.query(UserConnection).filter(
            or_(
                and_(UserConnection.requester_id == current_user_id, UserConnection.receiver_id == user_id),
                and_(UserConnection.requester_id == user_id, UserConnection.receiver_id == current_user_id)
            )
        ).first()
        
        connection_status = None
        if connection:
            connection_status = connection.status
        
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            connection_status=connection_status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

