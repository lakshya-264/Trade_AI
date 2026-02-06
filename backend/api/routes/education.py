"""
Educational API Routes
Provides learning content, tutorials, and educational explanations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from core.database import get_db
from core.auth_dependencies import get_current_user, get_current_user_optional
from services.educational_service import educational_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/learning-paths")
async def get_learning_paths(
    level: str = Query("beginner", description="Learning level: beginner, intermediate, advanced"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get structured learning paths for different levels"""
    try:
        # Use educational_service (it's async)
        result = await educational_service.get_learning_path(level)
        return {
            "success": True,
            "data": result,
            "message": f"Learning path for {level} level retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/concepts/{concept}")
async def get_concept_explanation(
    concept: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed explanation of a trading concept"""
    try:
        result = await educational_service.get_concept_explanation(concept)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": f"Concept explanation for '{concept}' retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting concept explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tutorials")
async def get_tutorials(
    category: str = Query("all", description="Tutorial category"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available tutorials"""
    try:
        result = await educational_service.get_tutorials(category)
        return {
            "success": True,
            "data": result,
            "message": f"Tutorials for category '{category}' retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting tutorials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quizzes")
async def get_quizzes(
    level: str = Query("beginner", description="Quiz level"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quizzes for different levels"""
    try:
        result = await educational_service.get_quizzes(level)
        return {
            "success": True,
            "data": result,
            "message": f"Quizzes for {level} level retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting quizzes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: int,
    answers: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results"""
    try:
        result = await educational_service.submit_quiz(quiz_id, answers)
        return {
            "success": True,
            "data": result,
            "message": "Quiz submitted successfully"
        }
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress")
async def get_learning_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's learning progress"""
    try:
        result = await educational_service.get_user_progress(current_user["id"])
        return {
            "success": True,
            "data": result,
            "message": "Learning progress retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lessons/{lesson_id}")
async def get_lesson(
    lesson_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific lesson by ID"""
    try:
        # Mock data for now - replace with real database query
        lesson = {
            "id": lesson_id,
            "title": f"Lesson {lesson_id}",
            "content": f"This is the detailed content for lesson {lesson_id}",
            "exercises": [
                {"id": 1, "question": f"Question 1 for lesson {lesson_id}", "type": "multiple_choice"},
                {"id": 2, "question": f"Question 2 for lesson {lesson_id}", "type": "true_false"}
            ],
            "duration": "30 minutes",
            "difficulty": "beginner",
            "timestamp": "2025-01-07T00:00:00Z"
        }
        
        return {
            "success": True,
            "data": lesson
        }
    except Exception as e:
        logger.error(f"Error getting lesson {lesson_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Missing Endpoints for API Compatibility ----------

@router.get("/content")
async def get_content():
    """Get educational content"""
    try:
        return {
            "message": "Educational content retrieved successfully",
            "content": [
                {"id": 1, "title": "Introduction to Stock Trading", "type": "article"},
                {"id": 2, "title": "Technical Analysis Basics", "type": "video"},
                {"id": 3, "title": "Risk Management Strategies", "type": "course"}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting content: {str(e)}")

@router.get("/trading-strategies")
async def get_trading_strategies(
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get trading strategies"""
    try:
        strategies = {
            "momentum_trading": {
                "name": "Momentum Trading",
                "description": "Trade stocks that are moving strongly in one direction on high volume",
                "time_horizon": "Intraday to Short-term (1-5 days)",
                "risk_level": "High",
                "capital_required": "₹50,000 - ₹5,00,000",
                "strategy_details": {
                    "entry_criteria": [
                        "Stock breaks above resistance with high volume",
                        "RSI between 50-70 (not overbought)",
                        "MACD shows bullish crossover",
                        "Price above 20-day moving average"
                    ],
                    "exit_criteria": [
                        "Target price reached (2:1 risk-reward ratio)",
                        "Stop loss triggered",
                        "Volume decreases significantly",
                        "RSI crosses above 80 (overbought)"
                    ],
                    "risk_management": [
                        "Never risk more than 2% of capital per trade",
                        "Set stop loss at 2-3% below entry",
                        "Use trailing stop loss after 5% profit",
                        "Diversify across 3-5 positions"
                    ],
                    "best_practices": [
                        "Trade during high volume hours (9:30 AM - 11:30 AM)",
                        "Avoid trading during news events",
                        "Review strategy performance weekly",
                        "Keep a trading journal"
                    ]
                },
                "example_scenario": {
                    "stock": "RELIANCE",
                    "entry_price": 2450,
                    "stop_loss": 2400,
                    "target": 2550,
                    "quantity": 40,
                    "risk": "₹2,000 (2% of ₹1,00,000)",
                    "potential_profit": "₹4,000 (4% return)",
                    "reasoning": "Strong breakout above ₹2450 with 2x average volume, RSI at 65, MACD bullish"
                }
            },
            "swing_trading": {
                "name": "Swing Trading",
                "description": "Hold positions for several days to weeks to capture price swings",
                "time_horizon": "Short to Medium-term (5-30 days)",
                "risk_level": "Medium",
                "capital_required": "₹1,00,000 - ₹10,00,000",
                "strategy_details": {
                    "entry_criteria": [
                        "Stock in uptrend with higher highs and higher lows",
                        "Pullback to support level (20 or 50-day MA)",
                        "Bullish candlestick pattern (hammer, engulfing)",
                        "Volume increases on bounce"
                    ],
                    "exit_criteria": [
                        "Target reached (3:1 risk-reward)",
                        "Trend reversal signals",
                        "Stop loss hit",
                        "Time-based exit (30 days)"
                    ],
                    "risk_management": [
                        "Risk 1-2% per trade",
                        "Stop loss at 5-7% below entry",
                        "Position size based on volatility",
                        "Maximum 5 open positions"
                    ],
                    "best_practices": [
                        "Focus on liquid stocks (volume > 1M)",
                        "Trade with the overall market trend",
                        "Use weekly charts for trend confirmation",
                        "Set alerts for key price levels"
                    ]
                },
                "example_scenario": {
                    "stock": "TCS",
                    "entry_price": 3200,
                    "stop_loss": 3040,
                    "target": 3520,
                    "quantity": 30,
                    "risk": "₹4,800 (1.5% of ₹3,20,000)",
                    "potential_profit": "₹9,600 (3% return)",
                    "reasoning": "Pullback to 50-day MA support, bullish engulfing pattern, RSI oversold bounce"
                }
            },
            "value_investing": {
                "name": "Value Investing",
                "description": "Buy undervalued stocks with strong fundamentals for long-term growth",
                "time_horizon": "Long-term (1-5 years)",
                "risk_level": "Low to Medium",
                "capital_required": "₹5,00,000+",
                "strategy_details": {
                    "entry_criteria": [
                        "P/E ratio below industry average",
                        "P/B ratio < 1.5",
                        "Debt-to-equity < 0.5",
                        "Consistent earnings growth (5+ years)",
                        "Dividend yield > 2%"
                    ],
                    "exit_criteria": [
                        "Stock reaches fair value",
                        "Fundamentals deteriorate",
                        "Better opportunity identified",
                        "Long-term target achieved"
                    ],
                    "risk_management": [
                        "Diversify across sectors (10-15 stocks)",
                        "Regular portfolio review (quarterly)",
                        "Avoid over-concentration (>20% in one stock)",
                        "Rebalance annually"
                    ],
                    "best_practices": [
                        "Focus on quality companies with moats",
                        "Buy during market corrections",
                        "Reinvest dividends",
                        "Hold for long-term wealth creation"
                    ]
                },
                "example_scenario": {
                    "stock": "INFY",
                    "entry_price": 1400,
                    "stop_loss": 1260,
                    "target": 1800,
                    "quantity": 70,
                    "risk": "₹9,800 (1% of ₹9,80,000)",
                    "potential_profit": "₹28,000 (2.8% annual return + dividends)",
                    "reasoning": "P/E 22 (industry avg 28), strong balance sheet, consistent 15%+ ROE, dividend yield 2.5%"
                }
            },
            "scalping": {
                "name": "Scalping",
                "description": "Make many small profits by trading quick price movements",
                "time_horizon": "Intraday (seconds to minutes)",
                "risk_level": "Very High",
                "capital_required": "₹1,00,000 - ₹10,00,000",
                "strategy_details": {
                    "entry_criteria": [
                        "High liquidity stocks (volume > 5M)",
                        "Tight bid-ask spread (<0.1%)",
                        "Price near support/resistance",
                        "Order flow shows buying/selling pressure"
                    ],
                    "exit_criteria": [
                        "Quick profit target (0.5-1%)",
                        "Stop loss (0.3-0.5%)",
                        "Time-based exit (5-10 minutes)",
                        "Volume dries up"
                    ],
                    "risk_management": [
                        "Risk 0.5% per trade maximum",
                        "Tight stop losses essential",
                        "Maximum 10 trades per day",
                        "Stop trading after 3 consecutive losses"
                    ],
                    "best_practices": [
                        "Trade during first 30 minutes and last 30 minutes",
                        "Use Level 2 order book data",
                        "Focus on 1-2 stocks only",
                        "Requires active monitoring"
                    ]
                },
                "example_scenario": {
                    "stock": "NIFTY",
                    "entry_price": 19500,
                    "stop_loss": 19480,
                    "target": 19520,
                    "quantity": 50,
                    "risk": "₹1,000 (0.5% of ₹2,00,000)",
                    "potential_profit": "₹1,000 (0.5% return)",
                    "reasoning": "Quick bounce from support, high volume, tight spread, order flow bullish"
                }
            }
        }
        
        return {
            "success": True,
            "data": {
                "strategies": strategies
            },
            "message": "Trading strategies retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting trading strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))