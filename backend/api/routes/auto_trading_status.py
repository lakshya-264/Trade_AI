"""
Auto Trading Status API
Provides status information about automated trading execution
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import logging

from core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auto-trading", tags=["Auto Trading"])

# Global variables to track auto-trading status
auto_trading_enabled = True
last_execution_time = None
next_execution_time = None
execution_count = 0
last_execution_result = None
auto_trading_task = None

def get_auto_trading_status() -> Dict[str, Any]:
    """Get current auto-trading status"""
    global auto_trading_enabled, last_execution_time, next_execution_time, execution_count, last_execution_result
    
    now = datetime.now()
    
    status = {
        "enabled": auto_trading_enabled,
        "last_execution": last_execution_time.isoformat() if last_execution_time else None,
        "next_execution": next_execution_time.isoformat() if next_execution_time else None,
        "execution_count": execution_count,
        "last_result": last_execution_result,
        "time_until_next": None,
        "status_message": "Auto-trading is active" if auto_trading_enabled else "Auto-trading is disabled"
    }
    
    # Calculate time until next execution
    if next_execution_time and now < next_execution_time:
        time_until = next_execution_time - now
        status["time_until_next"] = {
            "minutes": int(time_until.total_seconds() // 60),
            "seconds": int(time_until.total_seconds() % 60)
        }
        status["status_message"] = f"Next execution in {status['time_until_next']['minutes']}m {status['time_until_next']['seconds']}s"
    elif next_execution_time and now >= next_execution_time:
        status["status_message"] = "Execution pending..."
    
    return status

def update_auto_trading_status(success: bool, result: Dict[str, Any] = None):
    """Update auto-trading status after execution"""
    global last_execution_time, next_execution_time, execution_count, last_execution_result
    
    now = datetime.now()
    last_execution_time = now
    next_execution_time = now + timedelta(minutes=30)  # Next execution in 30 minutes
    execution_count += 1
    last_execution_result = {
        "success": success,
        "executed_trades": result.get("executed_trades", []) if result else [],
        "portfolio_update": result.get("portfolio_update", {}) if result else {},
        "error": result.get("error") if result else None
    }
    
    logger.info(f"🤖 Auto-trading status updated: {execution_count} executions, last: {'success' if success else 'failed'}")

@router.get("/status")
async def get_auto_trading_status_endpoint(db: Session = Depends(get_db)):
    """Get auto-trading status"""
    try:
        status = get_auto_trading_status()
        
        # Add additional information
        status.update({
            "server_time": datetime.now().isoformat(),
            "execution_interval": "30 minutes",
            "paper_trading": True,
            "max_trades_per_execution": 3,
            "min_confidence_threshold": 0.8,
            "target_symbols": "NIFTY_50"
        })
        
        return {
            "success": True,
            "data": status,
            "message": "Auto-trading status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting auto-trading status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get auto-trading status"
        }

@router.get("/public/status")
async def get_auto_trading_status_public():
    """Get auto-trading status (public endpoint - no authentication)"""
    try:
        status = get_auto_trading_status()
        
        # Add additional information
        status.update({
            "server_time": datetime.now().isoformat(),
            "execution_interval": "30 minutes",
            "paper_trading": True,
            "max_trades_per_execution": 3,
            "min_confidence_threshold": 0.8,
            "target_symbols": "NIFTY_50"
        })
        
        return {
            "success": True,
            "data": status,
            "message": "Auto-trading status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting auto-trading status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get auto-trading status"
        }

@router.post("/toggle")
async def toggle_auto_trading(enable: bool = True, db: Session = Depends(get_db)):
    """Enable or disable auto-trading"""
    global auto_trading_enabled
    
    try:
        auto_trading_enabled = enable
        status = get_auto_trading_status()
        
        logger.info(f"🤖 Auto-trading {'enabled' if enable else 'disabled'}")
        
        return {
            "success": True,
            "data": {
                "enabled": auto_trading_enabled,
                "previous_state": not enable
            },
            "message": f"Auto-trading {'enabled' if enable else 'disabled'} successfully"
        }
    except Exception as e:
        logger.error(f"Error toggling auto-trading: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to toggle auto-trading"
        }

@router.get("/execution-history")
async def get_execution_history(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent auto-trading execution history"""
    try:
        # This would typically query a database table for execution history
        # For now, return the most recent execution result
        status = get_auto_trading_status()
        
        history = []
        if last_execution_result:
            history.append({
                "timestamp": last_execution_time.isoformat() if last_execution_time else None,
                "result": last_execution_result,
                "execution_number": execution_count
            })
        
        return {
            "success": True,
            "data": {
                "history": history[-limit:],
                "total_executions": execution_count
            },
            "message": "Execution history retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get execution history"
        }
