"""
Arpit Education API Routes
Endpoints for Value Investing Principles education
"""

from fastapi import HTTPException, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import json

from core.database import get_db
from core.auth_dependencies import get_current_active_user
from core.database import User
from services.arpit_education_service import arpit_education_service

router = APIRouter()

@router.get("///lessons")
async def get_arpit_lessons(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all Arpit lessons"""
    try:
        lessons = arpit_education_service.lessons
        return {
            "success": True,
            "data": {
                "lessons": lessons,
                "total_lessons": len(lessons),
                "user_progress": arpit_education_service.get_progress_tracking(current_user.id)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lessons: {str(e)}")

@router.get("///lessons/{lesson_id}")
async def get_lesson_content(
    lesson_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed lesson content"""
    try:
        content = arpit_education_service.get_lesson_content(lesson_id)
        
        if "error" in content:
            raise HTTPException(status_code=404, detail=content["error"])
        
        return {
            "success": True,
            "data": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lesson content: {str(e)}")

@router.get("///animations/{animation_id}")
async def get_animation_sequence(
    animation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get animation sequence for frontend"""
    try:
        animation = arpit_education_service.get_animation_sequence(animation_id)
        
        if "error" in animation:
            raise HTTPException(status_code=404, detail=animation["error"])
        
        return {
            "success": True,
            "data": animation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching animation: {str(e)}")

@router.get("///examples/{example_id}")
async def get_examples(
    example_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get practical examples"""
    try:
        examples = arpit_education_service.examples
        
        if example_id not in examples:
            raise HTTPException(status_code=404, detail="Example not found")
        
        return {
            "success": True,
            "data": examples[example_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching examples: {str(e)}")

@router.post("///quiz/{lesson_id}/submit")
async def submit_quiz(
    lesson_id: str,
    answers: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers"""
    try:
        quiz = arpit_education_service._generate_quiz(lesson_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Calculate score
        correct_answers = 0
        total_questions = len(quiz)
        
        for i, question in enumerate(quiz):
            user_answer = answers.get(f"question_{i}", -1)
            if user_answer == question["correct"]:
                correct_answers += 1
        
        score = (correct_answers / total_questions) * 100
        
        # Update progress
        arpit_education_service.update_progress(
            current_user.id, 
            lesson_id, 
            {"quiz_score": score, "completed": True}
        )
        
        return {
            "success": True,
            "data": {
                "score": score,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "passed": score >= 70
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting quiz: {str(e)}")

@router.get("///progress")
async def get_user_progress(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's learning progress"""
    try:
        progress = arpit_education_service.get_progress_tracking(current_user.id)
        
        return {
            "success": True,
            "data": progress
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching progress: {str(e)}")

@router.post("///progress/update")
async def update_user_progress(
    progress_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's learning progress"""
    try:
        lesson_id = progress_data.get("lesson_id")
        if not lesson_id:
            raise HTTPException(status_code=400, detail="Lesson ID required")
        
        success = arpit_education_service.update_progress(
            current_user.id, 
            lesson_id, 
            progress_data
        )
        
        return {
            "success": success,
            "message": "Progress updated successfully" if success else "Failed to update progress"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating progress: {str(e)}")

@router.get("///certificates")
async def get_certificates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's earned certificates"""
    try:
        progress = arpit_education_service.get_progress_tracking(current_user.id)
        
        certificates = []
        for lesson_id, lesson_data in arpit_education_service.lessons.items():
            if lesson_id in progress.get("completed_lessons", []):
                certificates.append({
                    "lesson_id": lesson_id,
                    "title": lesson_data["title"],
                    "earned_date": "2024-01-01",  # This would come from database
                    "certificate_id": f"arpit_{lesson_id}_{current_user.id}"
                })
        
        return {
            "success": True,
            "data": {
                "certificates": certificates,
                "total_certificates": len(certificates)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching certificates: {str(e)}")

@router.get("///tools/arpit-formula")
async def arpit_formula_calculator(
    eps: float,
    growth_rate: float,
    bond_yield: float,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate intrinsic value using Arpit formula"""
    try:
        # Arpit Formula: V = EPS × (8.5 + 2g) × (4.4/Y)
        intrinsic_value = eps * (8.5 + 2 * growth_rate) * (4.4 / bond_yield)
        
        return {
            "success": True,
            "data": {
                "eps": eps,
                "growth_rate": growth_rate,
                "bond_yield": bond_yield,
                "intrinsic_value": round(intrinsic_value, 2),
                "formula": "V = EPS × (8.5 + 2g) × (4.4/Y)",
                "calculation": f"V = {eps} × (8.5 + 2×{growth_rate}) × (4.4/{bond_yield}) = {round(intrinsic_value, 2)}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating intrinsic value: {str(e)}")

@router.get("///tools/margin-of-safety")
async def margin_of_safety_calculator(
    intrinsic_value: float,
    market_price: float,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate margin of safety"""
    try:
        if intrinsic_value <= 0:
            raise HTTPException(status_code=400, detail="Intrinsic value must be positive")
        
        margin_of_safety = ((intrinsic_value - market_price) / intrinsic_value) * 100
        
        return {
            "success": True,
            "data": {
                "intrinsic_value": intrinsic_value,
                "market_price": market_price,
                "margin_of_safety": round(margin_of_safety, 2),
                "safety_level": "High" if margin_of_safety > 20 else "Medium" if margin_of_safety > 10 else "Low",
                "recommendation": "Buy" if margin_of_safety > 20 else "Consider" if margin_of_safety > 10 else "Avoid"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating margin of safety: {str(e)}")

@router.get("///tools/defensive-screener")
async def defensive_stock_screener(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Screen stock against Arpit's defensive criteria"""
    try:
        # This would integrate with real stock data
        # For now, returning mock data
        mock_screening = {
            "symbol": symbol,
            "criteria": [
                {
                    "name": "Company Size",
                    "passed": True,
                    "value": "Large Cap",
                    "description": "Market cap > ₹10,000 crores"
                },
                {
                    "name": "Financial Strength",
                    "passed": True,
                    "value": "Strong",
                    "description": "Current ratio > 2.0, Debt/Equity < 0.5"
                },
                {
                    "name": "Earnings Stability",
                    "passed": True,
                    "value": "Stable",
                    "description": "Positive earnings for 10+ years"
                },
                {
                    "name": "Dividend Record",
                    "passed": False,
                    "value": "Inconsistent",
                    "description": "Uninterrupted dividends for 10+ years"
                },
                {
                    "name": "Moderate Valuation",
                    "passed": True,
                    "value": "Fair",
                    "description": "P/E < 15, P/B < 1.5"
                }
            ],
            "total_passed": 4,
            "total_criteria": 5,
            "arpit_score": 80,
            "recommendation": "Good defensive stock"
        }
        
        return {
            "success": True,
            "data": mock_screening
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error screening stock: {str(e)}")
