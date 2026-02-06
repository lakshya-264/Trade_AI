"""
Social Connections Schemas
Pydantic models for social connections API
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class ConnectionRequest(BaseModel):
    """Request to send a connection request"""
    user_id: int


class ConnectionResponse(BaseModel):
    """Response for connection request"""
    id: int
    requester_id: int
    receiver_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConnectionStatus(str):
    """Connection status enum"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: int
    username: str
    email: str
    created_at: datetime
    connection_status: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConnectionItem(BaseModel):
    """Single connection item in list"""
    id: int
    user: UserProfileResponse
    status: str
    is_requester: bool
    created_at: datetime
    updated_at: datetime


class ConnectionListResponse(BaseModel):
    """List of connections"""
    connections: List[ConnectionItem]
    total: int

