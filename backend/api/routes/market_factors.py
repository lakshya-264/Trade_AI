"""
Market Factors API Routes
Handles FII/DII data and other market factors
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from services.market_factors_service import market_factors_service
from core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# ==================== PYDANTIC MODELS ====================

class ManualFIIDIIRequest(BaseModel):
    """Request model for manual FII/DII data input"""
    fii_net_investment: float
    dii_net_investment: float
    date: Optional[str] = None  # Format: YYYY-MM-DD, defaults to today

# ==================== API ENDPOINTS ====================

@router.post("/fii-dii/manual")
async def set_manual_fii_dii(
    request: ManualFIIDIIRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """
    Set manual FII/DII data when automatic scraping fails
    
    Args:
        request: FII/DII data (in Crores)
        current_user: Authenticated user
        
    Returns:
        Success message with stored data
    """
    try:
        result = market_factors_service.set_manual_fii_dii_data(
            fii_net_investment=request.fii_net_investment,
            dii_net_investment=request.dii_net_investment,
            date=request.date
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "message": "Manual FII/DII data set successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error setting manual FII/DII data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fii-dii/manual")
async def get_manual_fii_dii(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """
    Get manual FII/DII data for a specific date
    
    Args:
        date: Date string (YYYY-MM-DD), defaults to today
        current_user: Authenticated user
        
    Returns:
        Manual FII/DII data if available
    """
    try:
        data = market_factors_service.get_manual_fii_dii_data(date=date)
        
        if data:
            return {
                "success": True,
                "data": data
            }
        else:
            return {
                "success": False,
                "message": "No manual FII/DII data found for the specified date",
                "data": None
            }
            
    except Exception as e:
        logger.error(f"Error getting manual FII/DII data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fii-dii/status")
async def get_fii_dii_status(
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """
    Get status of FII/DII data (manual vs automatic)
    
    Returns:
        Status information about FII/DII data availability
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        manual_data = market_factors_service.get_manual_fii_dii_data(today)
        
        return {
            "success": True,
            "has_manual_data": manual_data is not None,
            "manual_data": manual_data,
            "date": today,
            "note": "Manual data takes priority over automatic scraping"
        }
        
    except Exception as e:
        logger.error(f"Error getting FII/DII status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

