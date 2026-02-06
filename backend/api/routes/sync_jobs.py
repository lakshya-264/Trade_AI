"""
Sync Jobs API Routes
Trigger and manage daily/quarterly sync jobs
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import logging

from core.database import get_db
from core.auth_dependencies import get_current_user_optional
from services.daily_sync_job import daily_sync_job
from services.stock_master_service import stock_master_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/daily-market-data")
async def trigger_daily_market_sync(
    background_tasks: BackgroundTasks,
    symbols: list = None,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Trigger daily market data sync"""
    try:
        # Run in background
        background_tasks.add_task(daily_sync_job.sync_daily_market_data, symbols)
        
        return {
            "success": True,
            "message": "Daily market data sync started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering daily sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/financial-ratios")
async def trigger_financial_ratios_sync(
    background_tasks: BackgroundTasks,
    symbols: list = None,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Trigger financial ratios sync"""
    try:
        # Run in background
        background_tasks.add_task(daily_sync_job.sync_financial_ratios, symbols)
        
        return {
            "success": True,
            "message": "Financial ratios sync started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering ratios sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stock-master")
async def trigger_stock_master_sync(
    background_tasks: BackgroundTasks,
    exchange: str = "NSE",
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Trigger stock master sync"""
    try:
        # Run in background
        background_tasks.add_task(stock_master_service.sync_stock_master, exchange)
        
        return {
            "success": True,
            "message": f"Stock master sync started for {exchange}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering stock master sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

