"""
Social Trading API Routes
Trading ideas, following, comments, copy trading
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import logging

from core.database import get_db
from core.auth_dependencies import get_current_user
from services.social_trading import social_trading_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/social-trading", tags=["Social Trading"])

class TradingIdeaRequest(BaseModel):
    symbol: str
    analysis: str
    chart_snapshot: Optional[str] = None
    tags: Optional[List[str]] = None

class CommentRequest(BaseModel):
    idea_id: str
    comment: str

class CopyStrategyRequest(BaseModel):
    trader_id: int
    strategy_id: str

@router.post("/ideas/share")
async def share_trading_idea(
    idea: TradingIdeaRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a trading idea"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        result = await social_trading_service.share_trading_idea(
            user_id=user_id,
            symbol=idea.symbol,
            analysis=idea.analysis,
            chart_snapshot=idea.chart_snapshot,
            tags=idea.tags,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error sharing trading idea: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/follow/{trader_id}")
async def follow_trader(
    trader_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow a trader"""
    try:
        follower_id = current_user.get("id") or current_user.get("user_id")
        result = await social_trading_service.follow_trader(
            follower_id=follower_id,
            trader_id=trader_id,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error following trader: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ideas/comment")
async def add_comment(
    comment: CommentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add comment to trading idea"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        result = await social_trading_service.add_comment(
            user_id=user_id,
            idea_id=comment.idea_id,
            comment=comment.comment,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copy-strategy")
async def copy_strategy(
    request: CopyStrategyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Copy a trader's strategy"""
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
        result = await social_trading_service.copy_trading_strategy(
            user_id=user_id,
            trader_id=request.trader_id,
            strategy_id=request.strategy_id,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error copying strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

