"""
User Learning Service
Learns from user feedback and behavior to improve recommendations
Integrated with Advanced Learning Services for automatic model improvement
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from core.database_unified import UserFeedback, UserBehaviorTracking, User

# Import advanced learning services
from services.automatic_model_retraining import automatic_model_retraining
from services.dynamic_feature_selection import dynamic_feature_selection
from services.adaptive_algorithm_selection import adaptive_algorithm_selection
from services.realtime_parameter_tuning import realtime_parameter_tuning

logger = logging.getLogger(__name__)

class UserLearningService:
    """Service for learning from user feedback and behavior"""
    
    def __init__(self):
        self.logger = logger
    
    def submit_feedback(
        self,
        db: Session,
        user_id: int,
        entity_type: str,
        entity_id: str,
        feedback_type: str,
        symbol: Optional[str] = None,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Submit user feedback"""
        try:
            feedback = UserFeedback(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                symbol=symbol,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                meta_data=metadata or {},
                created_at=datetime.utcnow()
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            # Trigger learning from feedback
            self._learn_from_feedback(db, user_id, feedback)
            
            self.logger.info(f"Feedback submitted: user_id={user_id}, entity_type={entity_type}, feedback_type={feedback_type}")
            
            return {
                "success": True,
                "feedback_id": feedback.id,
                "message": "Feedback submitted successfully"
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error submitting feedback: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def track_behavior(
        self,
        db: Session,
        user_id: int,
        action_type: str,
        entity_type: str,
        entity_id: str,
        symbol: Optional[str] = None,
        metadata: Optional[Dict] = None,
        session_id: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track user behavior"""
        try:
            behavior = UserBehaviorTracking(
                user_id=user_id,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                symbol=symbol,
                meta_data=metadata or {},
                session_id=session_id,
                referrer=referrer,
                created_at=datetime.utcnow()
            )
            
            db.add(behavior)
            db.commit()
            db.refresh(behavior)
            
            self.logger.info(f"Behavior tracked: user_id={user_id}, action_type={action_type}, entity_type={entity_type}")
            
            return {
                "success": True,
                "behavior_id": behavior.id,
                "message": "Behavior tracked successfully"
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error tracking behavior: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _learn_from_feedback(self, db: Session, user_id: int, feedback: UserFeedback):
        """Learn from user feedback and update preferences"""
        try:
            # Analyze feedback patterns
            feedback_stats = self._analyze_feedback_patterns(db, user_id)
            
            # Update user preferences based on feedback
            if feedback_stats:
                self._update_preferences_from_feedback(db, user_id, feedback_stats)
            
            # Trigger advanced learning services based on feedback
            self._trigger_advanced_learning(db, user_id, feedback, feedback_stats)
            
            self.logger.info(f"Learning from feedback completed for user_id={user_id}")
            
        except Exception as e:
            self.logger.error(f"Error learning from feedback: {e}")
    
    def _trigger_advanced_learning(
        self,
        db: Session,
        user_id: int,
        feedback: UserFeedback,
        feedback_stats: Dict[str, Any]
    ):
        """Trigger advanced learning services based on feedback"""
        try:
            # Determine model name from symbol or entity
            model_name = f"ml_model_{feedback.symbol}" if feedback.symbol else "ml_model_general"
            
            # 1. Check if model needs retraining based on negative feedback
            if feedback.feedback_type in ['not_helpful', 'inaccurate', 'not_useful']:
                satisfaction_rate = feedback_stats.get('satisfaction_rate', 1.0)
                
                # If satisfaction rate drops below threshold, trigger retraining check
                if satisfaction_rate < 0.7:
                    performance_metrics = {
                        'accuracy': satisfaction_rate,
                        'mse': 1.0 - satisfaction_rate,
                        'mae': 1.0 - satisfaction_rate
                    }
                    
                    # Update performance history
                    automatic_model_retraining.update_performance_history(
                        model_name,
                        performance_metrics
                    )
                    
                    self.logger.info(f"Triggered retraining check for {model_name} due to low satisfaction: {satisfaction_rate}")
            
            # 2. Adjust feature importance based on feedback
            if feedback.symbol:
                # Negative feedback suggests features may not be optimal
                if feedback.feedback_type in ['not_helpful', 'inaccurate']:
                    # Adjust feature importance (reduce importance of current features)
                    performance_feedback = {
                        'prediction_accuracy': -0.1  # Negative impact
                    }
                    
                    dynamic_feature_selection.adjust_feature_importance(
                        model_name,
                        performance_feedback
                    )
                    
                    self.logger.info(f"Adjusted feature importance for {model_name} based on negative feedback")
            
            # 3. Update algorithm selection based on feedback
            if feedback.symbol:
                # Track which algorithms perform better for this user
                algorithm_performances = {}
                
                # If positive feedback, current algorithm is good
                if feedback.feedback_type in ['helpful', 'accurate', 'useful']:
                    # This would be tracked per algorithm - placeholder for now
                    pass
                
                # Select best algorithm for symbol
                adaptive_algorithm_selection.select_best_algorithm(
                    symbol=feedback.symbol,
                    algorithm_performances=algorithm_performances
                )
            
            # 4. Adjust parameters based on user preferences
            if feedback.rating is not None:
                # Lower ratings suggest parameters need tuning
                if feedback.rating < 3:
                    current_performance = {
                        'accuracy': feedback.rating / 5.0,
                        'user_satisfaction': feedback.rating / 5.0
                    }
                    
                    realtime_parameter_tuning.optimize_parameters(
                        model_name=model_name,
                        current_performance=current_performance,
                        optimization_target='accuracy'
                    )
                    
                    self.logger.info(f"Triggered parameter optimization for {model_name} due to low rating: {feedback.rating}")
            
        except Exception as e:
            self.logger.error(f"Error triggering advanced learning: {e}")
    
    def _analyze_feedback_patterns(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze user feedback patterns"""
        try:
            # Get recent feedback (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            feedbacks = db.query(UserFeedback).filter(
                and_(
                    UserFeedback.user_id == user_id,
                    UserFeedback.created_at >= cutoff_date
                )
            ).all()
            
            if not feedbacks:
                return {}
            
            # Analyze patterns
            total_feedback = len(feedbacks)
            positive_feedback = sum(1 for f in feedbacks if f.feedback_type in ['helpful', 'accurate', 'useful'])
            negative_feedback = sum(1 for f in feedbacks if f.feedback_type in ['not_helpful', 'inaccurate', 'not_useful'])
            
            # Average rating
            ratings = [f.rating for f in feedbacks if f.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            
            # Symbol preferences (which symbols get positive feedback)
            symbol_feedback = {}
            for f in feedbacks:
                if f.symbol:
                    if f.symbol not in symbol_feedback:
                        symbol_feedback[f.symbol] = {'positive': 0, 'negative': 0}
                    if f.feedback_type in ['helpful', 'accurate', 'useful']:
                        symbol_feedback[f.symbol]['positive'] += 1
                    else:
                        symbol_feedback[f.symbol]['negative'] += 1
            
            # Entity type preferences
            entity_type_feedback = {}
            for f in feedbacks:
                if f.entity_type not in entity_type_feedback:
                    entity_type_feedback[f.entity_type] = {'positive': 0, 'negative': 0}
                if f.feedback_type in ['helpful', 'accurate', 'useful']:
                    entity_type_feedback[f.entity_type]['positive'] += 1
                else:
                    entity_type_feedback[f.entity_type]['negative'] += 1
            
            return {
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'satisfaction_rate': positive_feedback / total_feedback if total_feedback > 0 else 0,
                'average_rating': avg_rating,
                'symbol_preferences': symbol_feedback,
                'entity_type_preferences': entity_type_feedback
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing feedback patterns: {e}")
            return {}
    
    def _update_preferences_from_feedback(self, db: Session, user_id: int, feedback_stats: Dict[str, Any]):
        """Update user preferences based on feedback analysis"""
        try:
            # This would update user preferences in a user_preferences table
            # For now, we'll just log the insights
            self.logger.info(f"Feedback insights for user_id={user_id}: {feedback_stats}")
            
            # Update parameter tuning based on inferred preferences
            inferred_threshold = self._infer_confidence_threshold(feedback_stats)
            
            # Adjust confidence threshold parameter
            if inferred_threshold:
                performance_feedback = {
                    'accuracy': feedback_stats.get('satisfaction_rate', 0.7),
                    'false_positive_rate': 1.0 - feedback_stats.get('satisfaction_rate', 0.7)
                }
                
                realtime_parameter_tuning.adjust_threshold(
                    threshold_name='confidence_threshold',
                    current_value=0.7,  # Default
                    performance_feedback=performance_feedback,
                    adjustment_rate=0.1
                )
            
            # In the future, this could update:
            # - Preferred symbols (based on positive feedback)
            # - Preferred analysis types (predictions vs recommendations)
            # - Confidence thresholds (based on rating patterns)
            
        except Exception as e:
            self.logger.error(f"Error updating preferences from feedback: {e}")
    
    def get_user_feedback_stats(self, db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user feedback statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            feedbacks = db.query(UserFeedback).filter(
                and_(
                    UserFeedback.user_id == user_id,
                    UserFeedback.created_at >= cutoff_date
                )
            ).all()
            
            if not feedbacks:
                return {
                    "total_feedback": 0,
                    "satisfaction_rate": 0,
                    "average_rating": None
                }
            
            positive = sum(1 for f in feedbacks if f.feedback_type in ['helpful', 'accurate', 'useful'])
            ratings = [f.rating for f in feedbacks if f.rating is not None]
            
            return {
                "total_feedback": len(feedbacks),
                "positive_feedback": positive,
                "negative_feedback": len(feedbacks) - positive,
                "satisfaction_rate": positive / len(feedbacks) if feedbacks else 0,
                "average_rating": sum(ratings) / len(ratings) if ratings else None,
                "feedback_by_type": {
                    f.feedback_type: sum(1 for fb in feedbacks if fb.feedback_type == f.feedback_type)
                    for f in feedbacks
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting feedback stats: {e}")
            return {"error": str(e)}
    
    def get_user_behavior_insights(self, db: Session, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get insights from user behavior"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            behaviors = db.query(UserBehaviorTracking).filter(
                and_(
                    UserBehaviorTracking.user_id == user_id,
                    UserBehaviorTracking.created_at >= cutoff_date
                )
            ).all()
            
            if not behaviors:
                return {
                    "total_actions": 0,
                    "action_breakdown": {}
                }
            
            # Analyze behavior patterns
            action_counts = {}
            entity_type_counts = {}
            symbol_counts = {}
            
            for b in behaviors:
                # Count actions
                action_counts[b.action_type] = action_counts.get(b.action_type, 0) + 1
                
                # Count entity types
                entity_type_counts[b.entity_type] = entity_type_counts.get(b.entity_type, 0) + 1
                
                # Count symbols
                if b.symbol:
                    symbol_counts[b.symbol] = symbol_counts.get(b.symbol, 0) + 1
            
            # Calculate recommendation acceptance rate
            recommendations_viewed = sum(1 for b in behaviors if b.action_type == 'viewed_recommendation')
            recommendations_followed = sum(1 for b in behaviors if b.action_type == 'followed_recommendation')
            acceptance_rate = recommendations_followed / recommendations_viewed if recommendations_viewed > 0 else 0
            
            return {
                "total_actions": len(behaviors),
                "action_breakdown": action_counts,
                "entity_type_breakdown": entity_type_counts,
                "top_symbols": dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "recommendation_acceptance_rate": acceptance_rate,
                "most_active_day": self._get_most_active_day(behaviors)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting behavior insights: {e}")
            return {"error": str(e)}
    
    def _get_most_active_day(self, behaviors: List[UserBehaviorTracking]) -> Optional[str]:
        """Get the day with most activity"""
        try:
            day_counts = {}
            for b in behaviors:
                day = b.created_at.strftime('%A')
                day_counts[day] = day_counts.get(day, 0) + 1
            
            if day_counts:
                return max(day_counts.items(), key=lambda x: x[1])[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting most active day: {e}")
            return None
    
    def infer_user_preferences(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Infer user preferences from feedback and behavior"""
        try:
            feedback_stats = self.get_user_feedback_stats(db, user_id)
            behavior_insights = self.get_user_behavior_insights(db, user_id)
            
            # Infer preferences
            preferences = {
                "inferred_risk_tolerance": self._infer_risk_tolerance(db, user_id),
                "preferred_symbols": behavior_insights.get("top_symbols", {}),
                "preferred_analysis_types": self._infer_preferred_analysis_types(feedback_stats, behavior_insights),
                "confidence_threshold": self._infer_confidence_threshold(feedback_stats),
                "trading_frequency": self._infer_trading_frequency(behavior_insights)
            }
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error inferring preferences: {e}")
            return {"error": str(e)}
    
    def _infer_risk_tolerance(self, db: Session, user_id: int) -> str:
        """Infer risk tolerance from trading behavior"""
        try:
            # Analyze order patterns
            orders = db.query(UserBehaviorTracking).filter(
                and_(
                    UserBehaviorTracking.user_id == user_id,
                    UserBehaviorTracking.action_type == 'placed_order'
                )
            ).all()
            
            # Simple heuristic: analyze order sizes and types
            # This is a placeholder - would need actual order data
            return "medium"  # Default
            
        except Exception as e:
            self.logger.error(f"Error inferring risk tolerance: {e}")
            return "medium"
    
    def _infer_preferred_analysis_types(self, feedback_stats: Dict, behavior_insights: Dict) -> List[str]:
        """Infer which analysis types user prefers"""
        try:
            preferred = []
            
            # Check entity type preferences from feedback
            entity_prefs = feedback_stats.get("entity_type_preferences", {})
            for entity_type, stats in entity_prefs.items():
                if stats.get("positive", 0) > stats.get("negative", 0):
                    preferred.append(entity_type)
            
            return preferred if preferred else ["prediction", "recommendation"]
            
        except Exception as e:
            self.logger.error(f"Error inferring preferred analysis types: {e}")
            return ["prediction", "recommendation"]
    
    def _infer_confidence_threshold(self, feedback_stats: Dict) -> float:
        """Infer confidence threshold from feedback ratings"""
        try:
            avg_rating = feedback_stats.get("average_rating")
            if avg_rating:
                # Map rating (1-5) to confidence threshold (0-1)
                # Higher rating = higher confidence threshold
                return min(0.95, max(0.5, (avg_rating / 5.0) * 0.9 + 0.5))
            return 0.7  # Default
            
        except Exception as e:
            self.logger.error(f"Error inferring confidence threshold: {e}")
            return 0.7
    
    def _infer_trading_frequency(self, behavior_insights: Dict) -> str:
        """Infer trading frequency from behavior"""
        try:
            total_actions = behavior_insights.get("total_actions", 0)
            order_actions = sum(
                count for action, count in behavior_insights.get("action_breakdown", {}).items()
                if "order" in action.lower()
            )
            
            if order_actions > 20:
                return "high"
            elif order_actions > 5:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"Error inferring trading frequency: {e}")
            return "medium"

# Global instance
user_learning_service = UserLearningService()

