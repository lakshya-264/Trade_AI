"""
Social Trading Service
Trading ideas sharing, following traders, comments, and copy trading
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import uuid

logger = logging.getLogger(__name__)

class SocialTradingService:
    """Social trading features"""
    
    def __init__(self):
        self.cache = {}  # Cache for performance
        self.cache_ttl = 300  # 5 minutes
    
    async def share_trading_idea(
        self,
        user_id: int,
        symbol: str,
        analysis: str,
        chart_snapshot: Optional[str] = None,
        tags: Optional[List[str]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Share a trading idea with the community"""
        try:
            from core.database_unified import TradingIdea
            
            idea_id = str(uuid.uuid4())
            idea = TradingIdea(
                id=idea_id,
                user_id=user_id,
                symbol=symbol,
                analysis=analysis,
                chart_snapshot=chart_snapshot,
                tags=",".join(tags) if tags else "",
                likes=0,
                views=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(idea)
            db.commit()
            db.refresh(idea)
            
            logger.info(f"Trading idea shared: {idea_id} by user {user_id}")
            
            return {
                "success": True,
                "idea_id": idea_id,
                "idea": self._format_idea(idea)
            }
            
        except Exception as e:
            logger.error(f"Error sharing trading idea: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    async def follow_trader(
        self,
        follower_id: int,
        trader_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Follow a trader"""
        try:
            from core.database_unified import TraderFollow
            
            # Check if already following
            existing = db.query(TraderFollow).filter(
                TraderFollow.follower_id == follower_id,
                TraderFollow.trader_id == trader_id
            ).first()
            
            if existing:
                return {"success": False, "error": "Already following this trader"}
            
            follow = TraderFollow(
                follower_id=follower_id,
                trader_id=trader_id,
                created_at=datetime.now()
            )
            
            db.add(follow)
            db.commit()
            
            logger.info(f"User {follower_id} followed trader {trader_id}")
            
            return {"success": True, "message": "Successfully followed trader"}
            
        except Exception as e:
            logger.error(f"Error following trader: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    async def add_comment(
        self,
        user_id: int,
        idea_id: str,
        comment: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Add comment to trading idea"""
        try:
            from core.database_unified import IdeaComment
            
            comment_id = str(uuid.uuid4())
            idea_comment = IdeaComment(
                id=comment_id,
                idea_id=idea_id,
                user_id=user_id,
                comment=comment,
                likes=0,
                created_at=datetime.now()
            )
            
            db.add(idea_comment)
            db.commit()
            
            logger.info(f"Comment added: {comment_id} to idea {idea_id}")
            
            return {
                "success": True,
                "comment_id": comment_id,
                "comment": self._format_comment(idea_comment)
            }
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    async def copy_trading_strategy(
        self,
        user_id: int,
        trader_id: int,
        strategy_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Copy a trader's strategy"""
        try:
            from core.database_unified import CopiedStrategy
            
            copy_id = str(uuid.uuid4())
            copied = CopiedStrategy(
                id=copy_id,
                user_id=user_id,
                trader_id=trader_id,
                strategy_id=strategy_id,
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add(copied)
            db.commit()
            
            logger.info(f"Strategy copied: {copy_id} by user {user_id}")
            
            return {
                "success": True,
                "copy_id": copy_id,
                "message": "Strategy copied successfully"
            }
            
        except Exception as e:
            logger.error(f"Error copying strategy: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def _format_idea(self, idea) -> Dict:
        """Format trading idea for response"""
        return {
            "id": idea.id,
            "user_id": idea.user_id,
            "symbol": idea.symbol,
            "analysis": idea.analysis,
            "chart_snapshot": idea.chart_snapshot,
            "tags": idea.tags.split(",") if idea.tags else [],
            "likes": idea.likes,
            "views": idea.views,
            "created_at": idea.created_at.isoformat() if idea.created_at else None
        }
    
    def _format_comment(self, comment) -> Dict:
        """Format comment for response"""
        return {
            "id": comment.id,
            "idea_id": comment.idea_id,
            "user_id": comment.user_id,
            "comment": comment.comment,
            "likes": comment.likes,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        }

# Create singleton instance
social_trading_service = SocialTradingService()

