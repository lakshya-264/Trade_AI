"""
Otp Debug API routes
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint for otp debug"""
    return {"message": "Otp Debug API is working"}

@router.get("/health")
async def health():
    """Health check for otp debug"""
    return {"status": "healthy", "service": "otp debug"}
