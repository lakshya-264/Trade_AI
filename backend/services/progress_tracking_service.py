"""
Progress Tracking Service
Manages user learning progress, certificates, sessions, bookmarks, and notes
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models.market_education_models import (
    UserProgress, UserCertificate, LearningSession, 
    UserBookmark, UserNote
)

logger = logging.getLogger(__name__)

class ProgressTrackingService:
    """Service for tracking user learning progress"""
    
    def __init__(self):
        pass
    
    def update_progress(
        self,
        db: Session,
        user_id: int,
        lesson_id: str,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update or create user progress"""
        try:
            # Check if progress exists
            progress = db.query(UserProgress).filter(
                and_(
                    UserProgress.user_id == user_id,
                    UserProgress.lesson_id == lesson_id
                )
            ).first()
            
            if progress:
                # Update existing
                progress.completion_percentage = progress_data.get("completion_percentage", progress.completion_percentage)
                progress.time_spent_minutes = progress_data.get("time_spent_minutes", progress.time_spent_minutes)
                progress.completed = progress_data.get("completed", progress.completed)
                progress.quiz_score = progress_data.get("quiz_score", progress.quiz_score)
                progress.last_accessed = datetime.utcnow()
                
                if progress_data.get("completed") and not progress.completed_at:
                    progress.completed_at = datetime.utcnow()
                
                if progress_data.get("quiz_score"):
                    progress.quiz_attempts += 1
                    if not progress.best_quiz_score or progress_data["quiz_score"] > progress.best_quiz_score:
                        progress.best_quiz_score = progress_data["quiz_score"]
            else:
                # Create new
                progress = UserProgress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    module_id=progress_data.get("module_id"),
                    learning_path_id=progress_data.get("learning_path_id"),
                    completion_percentage=progress_data.get("completion_percentage", 0.0),
                    time_spent_minutes=progress_data.get("time_spent_minutes", 0),
                    completed=progress_data.get("completed", False),
                    quiz_score=progress_data.get("quiz_score"),
                    started_at=datetime.utcnow(),
                    last_accessed=datetime.utcnow()
                )
                db.add(progress)
            
            db.commit()
            db.refresh(progress)
            
            return {
                "success": True,
                "progress": {
                    "lesson_id": progress.lesson_id,
                    "completion_percentage": progress.completion_percentage,
                    "completed": progress.completed,
                    "time_spent_minutes": progress.time_spent_minutes
                }
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating progress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_progress(
        self,
        db: Session,
        user_id: int,
        learning_path_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's overall progress"""
        try:
            query = db.query(UserProgress).filter(UserProgress.user_id == user_id)
            
            if learning_path_id:
                query = query.filter(UserProgress.learning_path_id == learning_path_id)
            
            all_progress = query.all()
            
            # Calculate statistics
            total_lessons = len(all_progress)
            completed_lessons = sum(1 for p in all_progress if p.completed)
            total_time = sum(p.time_spent_minutes for p in all_progress)
            avg_completion = sum(p.completion_percentage for p in all_progress) / total_lessons if total_lessons > 0 else 0
            
            # Get current streak
            current_streak = self._calculate_streak(db, user_id)
            
            return {
                "success": True,
                "statistics": {
                    "total_lessons": total_lessons,
                    "completed_lessons": completed_lessons,
                    "completion_percentage": avg_completion,
                    "total_time_minutes": total_time,
                    "current_streak": current_streak
                },
                "progress": [
                    {
                        "lesson_id": p.lesson_id,
                        "module_id": p.module_id,
                        "learning_path_id": p.learning_path_id,
                        "completed": p.completed,
                        "completion_percentage": p.completion_percentage,
                        "time_spent_minutes": p.time_spent_minutes,
                        "quiz_score": p.quiz_score,
                        "last_accessed": p.last_accessed.isoformat() if p.last_accessed else None
                    }
                    for p in all_progress
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_certificate(
        self,
        db: Session,
        user_id: int,
        certificate_name: str,
        learning_path_id: str,
        final_score: float,
        validity_months: int = 12
    ) -> Dict[str, Any]:
        """Create a certificate for user"""
        try:
            # Generate verification code
            verification_code = f"TRD-{certificate_name.upper().replace(' ', '-')}-{datetime.now().strftime('%Y')}-{user_id:04d}"
            
            certificate = UserCertificate(
                user_id=user_id,
                certificate_name=certificate_name,
                learning_path_id=learning_path_id,
                verification_code=verification_code,
                final_score=final_score,
                earned_date=datetime.utcnow(),
                expiry_date=datetime.utcnow() + timedelta(days=validity_months * 30),
                validity_months=validity_months,
                is_active=True
            )
            
            db.add(certificate)
            db.commit()
            db.refresh(certificate)
            
            return {
                "success": True,
                "certificate": {
                    "id": certificate.id,
                    "name": certificate.certificate_name,
                    "verification_code": certificate.verification_code,
                    "earned_date": certificate.earned_date.isoformat(),
                    "expiry_date": certificate.expiry_date.isoformat() if certificate.expiry_date else None
                }
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating certificate: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_certificates(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Get all user certificates"""
        try:
            certificates = db.query(UserCertificate).filter(
                and_(
                    UserCertificate.user_id == user_id,
                    UserCertificate.is_active == True
                )
            ).all()
            
            return {
                "success": True,
                "certificates": [
                    {
                        "id": c.id,
                        "name": c.certificate_name,
                        "verification_code": c.verification_code,
                        "final_score": c.final_score,
                        "earned_date": c.earned_date.isoformat(),
                        "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                        "is_active": c.is_active
                    }
                    for c in certificates
                ],
                "count": len(certificates)
            }
        except Exception as e:
            logger.error(f"Error getting certificates: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def start_learning_session(
        self,
        db: Session,
        user_id: int,
        lesson_id: Optional[str] = None,
        module_id: Optional[str] = None,
        learning_path_id: Optional[str] = None,
        device_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a learning session"""
        try:
            session = LearningSession(
                user_id=user_id,
                lesson_id=lesson_id,
                module_id=module_id,
                learning_path_id=learning_path_id,
                session_start=datetime.utcnow(),
                device_type=device_type
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return {
                "success": True,
                "session_id": session.id,
                "started_at": session.session_start.isoformat()
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error starting session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def end_learning_session(
        self,
        db: Session,
        session_id: int,
        duration_minutes: Optional[int] = None,
        pages_viewed: Optional[int] = None
    ) -> Dict[str, Any]:
        """End a learning session"""
        try:
            session = db.query(LearningSession).filter(LearningSession.id == session_id).first()
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            session.session_end = datetime.utcnow()
            
            if duration_minutes:
                session.duration_minutes = duration_minutes
            else:
                # Calculate duration
                delta = session.session_end - session.session_start
                session.duration_minutes = int(delta.total_seconds() / 60)
            
            if pages_viewed:
                session.pages_viewed = pages_viewed
            
            db.commit()
            
            return {
                "success": True,
                "session": {
                    "id": session.id,
                    "duration_minutes": session.duration_minutes
                }
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error ending session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_bookmark(
        self,
        db: Session,
        user_id: int,
        content_type: str,
        content_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a bookmark"""
        try:
            # Check if already bookmarked
            existing = db.query(UserBookmark).filter(
                and_(
                    UserBookmark.user_id == user_id,
                    UserBookmark.content_type == content_type,
                    UserBookmark.content_id == content_id
                )
            ).first()
            
            if existing:
                return {
                    "success": True,
                    "message": "Already bookmarked",
                    "bookmark_id": existing.id
                }
            
            bookmark = UserBookmark(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id,
                title=title,
                created_at=datetime.utcnow()
            )
            
            db.add(bookmark)
            db.commit()
            db.refresh(bookmark)
            
            return {
                "success": True,
                "bookmark": {
                    "id": bookmark.id,
                    "content_type": bookmark.content_type,
                    "content_id": bookmark.content_id
                }
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding bookmark: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_note(
        self,
        db: Session,
        user_id: int,
        content_type: str,
        content_id: str,
        note_text: str
    ) -> Dict[str, Any]:
        """Add or update a note"""
        try:
            # Check if note exists
            note = db.query(UserNote).filter(
                and_(
                    UserNote.user_id == user_id,
                    UserNote.content_type == content_type,
                    UserNote.content_id == content_id
                )
            ).first()
            
            if note:
                # Update existing
                note.note_text = note_text
                note.updated_at = datetime.utcnow()
            else:
                # Create new
                note = UserNote(
                    user_id=user_id,
                    content_type=content_type,
                    content_id=content_id,
                    note_text=note_text,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(note)
            
            db.commit()
            db.refresh(note)
            
            return {
                "success": True,
                "note": {
                    "id": note.id,
                    "content_type": note.content_type,
                    "content_id": note.content_id,
                    "note_text": note.note_text
                }
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding note: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_streak(self, db: Session, user_id: int) -> int:
        """Calculate current learning streak (days)"""
        try:
            # Get all completed lessons
            completed = db.query(UserProgress).filter(
                and_(
                    UserProgress.user_id == user_id,
                    UserProgress.completed == True
                )
            ).order_by(UserProgress.completed_at.desc()).all()
            
            if not completed:
                return 0
            
            # Calculate streak
            streak = 0
            current_date = datetime.utcnow().date()
            
            for progress in completed:
                if progress.completed_at:
                    completed_date = progress.completed_at.date()
                    days_diff = (current_date - completed_date).days
                    
                    if days_diff == streak:
                        streak += 1
                    elif days_diff > streak:
                        break
            
            return streak
        except Exception as e:
            logger.error(f"Error calculating streak: {e}")
            return 0

# Global instance
progress_tracking_service = ProgressTrackingService()

