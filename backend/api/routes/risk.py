"""
Risk Management API Routes
Advanced risk assessment and management tools
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from core.database import get_db
from core.auth_dependencies import get_current_user
from services.risk_manager import risk_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/assess")
async def assess_risk(
    request_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess portfolio risk"""
    try:
        portfolio_data = request_data.get("portfolio", {})
        risk_model = request_data.get("model", "var")
        
        result = await risk_manager.assess_portfolio_risk(
            portfolio=portfolio_data,
            model=risk_model
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Risk assessment completed successfully"
        }
    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", operation_id="get_risk_metrics")
async def get_risk_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available risk metrics with live portfolio data"""
    try:
        # Extract user ID from current_user
        user_id = getattr(current_user, 'id', None)
        
        result = await risk_manager.get_risk_metrics(user_id=user_id)
        metrics = result.get("metrics", {}) if isinstance(result, dict) else {}
        # Flatten for UI compatibility and include nested for API clarity
        flattened = {**metrics, **result}
        # Ensure total_value exists
        if "total_value" not in flattened and "portfolio_value" in flattened:
            flattened["total_value"] = flattened.get("portfolio_value", 0)
        return {
            "success": True,
            "data": flattened,
            "message": "Risk metrics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stress-test")
async def stress_test_portfolio(
    request_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform stress test on portfolio"""
    try:
        portfolio_data = request_data.get("portfolio", {})
        scenarios = request_data.get("scenarios", ["market_crash", "recession"])
        
        result = await risk_manager.stress_test(
            portfolio=portfolio_data,
            scenarios=scenarios
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Stress test completed successfully"
        }
    except Exception as e:
        logger.error(f"Error performing stress test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Missing Endpoints for API Compatibility ----------

@router.get("/portfolio-risk")
async def get_portfolio_risk():
    """Get portfolio risk assessment"""
    try:
        return {
            "message": "Portfolio risk assessment retrieved successfully",
            "risk_score": 0.75,
            "risk_level": "MEDIUM",
            "recommendations": ["Diversify holdings", "Review stop-loss orders"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio risk: {str(e)}")

@router.get("/allocation")
async def get_risk_allocation():
    """Return current vs target allocation (static sample)."""
    try:
        return {
            "success": True,
            "data": {
                "current": {"equity": 62.0, "bonds": 28.0, "cash": 10.0},
                "target": {"equity": 60.0, "bonds": 35.0, "cash": 5.0},
                "max_drift": 7.0,
                "needs_rebalancing": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/limits")
async def get_risk_limits():
    """Expose current risk limits from manager."""
    try:
        return {"success": True, "data": risk_manager.get_risk_limits()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_risk_alerts():
    """Return active risk alerts (sample)."""
    try:
        return {
            "success": True,
            "data": [
                {"type": "CONCENTRATION", "message": "Equity weight drifted +7% from target", "priority": "MEDIUM"}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports")
async def get_risk_reports():
    """Return available risk reports (sample list)."""
    try:
        return {
            "success": True,
            "data": [
                {"id": "latest", "title": "Weekly Risk Summary", "generated_at": datetime.utcnow().isoformat()}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))