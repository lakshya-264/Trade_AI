"""
Real-Time Animation Teaching System
Interactive learning system for candlestick patterns, volume analysis, and trading signals
Features step-by-step animations, quizzes, and progress tracking
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
import logging
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class AnimationType(str, Enum):
    PATTERN_RECOGNITION = "pattern_recognition"
    VOLUME_ANALYSIS = "volume_analysis"
    TRADING_SIGNALS = "trading_signals"
    OPTIONS_TRADING = "options_trading"
    MARKET_SENTIMENT = "market_sentiment"
    TECHNICAL_INDICATORS = "technical_indicators"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class TeachingAnimationService:
    def __init__(self):
        # Animation templates and lessons
        self.animation_templates = self._initialize_animation_templates()
        
        # User progress tracking
        self.user_progress = {}
        
        # Real-time animation sessions
        self.active_sessions = {}
        
        # Quiz questions database
        self.quiz_questions = self._initialize_quiz_questions()
        
        # Pattern recognition patterns
        self.candlestick_patterns = self._initialize_candlestick_patterns()
        
        # Volume analysis scenarios
        self.volume_scenarios = self._initialize_volume_scenarios()
        
        # Trading signal examples
        self.trading_signal_examples = self._initialize_trading_signals()
    
    def _initialize_animation_templates(self) -> Dict[str, Any]:
        """Initialize comprehensive animation templates"""
        return {
            AnimationType.PATTERN_RECOGNITION: {
                "title": "Candlestick Pattern Recognition",
                "description": "Learn to identify and interpret candlestick patterns",
                "difficulty_levels": [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED],
                "estimated_duration": 45,  # minutes
                "lessons": [
                    {
                        "id": "basic_patterns",
                        "title": "Basic Reversal Patterns",
                        "patterns": ["hammer", "doji", "engulfing", "harami"],
                        "duration": 15
                    },
                    {
                        "id": "advanced_patterns",
                        "title": "Advanced Reversal Patterns",
                        "patterns": ["morning_star", "evening_star", "three_white_soldiers", "three_black_crows"],
                        "duration": 20
                    },
                    {
                        "id": "continuation_patterns",
                        "title": "Continuation Patterns",
                        "patterns": ["three_methods_rising", "three_methods_falling"],
                        "duration": 10
                    }
                ]
            },
            AnimationType.VOLUME_ANALYSIS: {
                "title": "Volume-Price Analysis",
                "description": "Master volume analysis and price-volume relationships",
                "difficulty_levels": [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED],
                "estimated_duration": 30,
                "lessons": [
                    {
                        "id": "volume_basics",
                        "title": "Volume Basics",
                        "concepts": ["volume_trends", "volume_averages", "volume_spikes"],
                        "duration": 10
                    },
                    {
                        "id": "price_volume_confirmation",
                        "title": "Price-Volume Confirmation",
                        "concepts": ["volume_confirmation", "volume_divergence", "breakout_volume"],
                        "duration": 15
                    },
                    {
                        "id": "volume_profile",
                        "title": "Volume Profile Analysis",
                        "concepts": ["poc", "value_area", "volume_at_price"],
                        "duration": 5
                    }
                ]
            },
            AnimationType.TRADING_SIGNALS: {
                "title": "Trading Signal Analysis",
                "description": "Learn to interpret and act on trading signals",
                "difficulty_levels": [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT],
                "estimated_duration": 60,
                "lessons": [
                    {
                        "id": "signal_types",
                        "title": "Types of Trading Signals",
                        "concepts": ["buy_signals", "sell_signals", "hold_signals", "strong_signals"],
                        "duration": 15
                    },
                    {
                        "id": "signal_confirmation",
                        "title": "Signal Confirmation",
                        "concepts": ["multi_timeframe", "indicator_confirmation", "volume_confirmation"],
                        "duration": 20
                    },
                    {
                        "id": "risk_management",
                        "title": "Risk Management",
                        "concepts": ["stop_loss", "take_profit", "position_sizing", "risk_reward"],
                        "duration": 25
                    }
                ]
            },
            AnimationType.OPTIONS_TRADING: {
                "title": "Options Trading Strategies",
                "description": "Master options trading with real-time analysis",
                "difficulty_levels": [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT],
                "estimated_duration": 90,
                "lessons": [
                    {
                        "id": "options_basics",
                        "title": "Options Fundamentals",
                        "concepts": ["calls_puts", "strike_prices", "expiry", "premium"],
                        "duration": 20
                    },
                    {
                        "id": "greeks_analysis",
                        "title": "Greeks Analysis",
                        "concepts": ["delta", "gamma", "theta", "vega"],
                        "duration": 25
                    },
                    {
                        "id": "options_strategies",
                        "title": "Options Strategies",
                        "concepts": ["covered_calls", "protective_puts", "straddles", "spreads"],
                        "duration": 45
                    }
                ]
            }
        }
    
    def _initialize_candlestick_patterns(self) -> Dict[str, Any]:
        """Initialize candlestick pattern definitions"""
        return {
            "hammer": {
                "name": "Hammer",
                "type": "reversal",
                "bullish_bearish": "bullish",
                "description": "A bullish reversal pattern with a small body and long lower shadow",
                "recognition_criteria": {
                    "body_size": "small",
                    "lower_shadow": "long",
                    "upper_shadow": "short_or_none",
                    "position": "at_low"
                },
                "trading_significance": "Strong bullish reversal signal",
                "success_rate": 0.75,
                "example_scenarios": [
                    {
                        "title": "Hammer at Support",
                        "description": "Hammer pattern forming at a key support level",
                        "chart_data": self._generate_hammer_chart_data(),
                        "analysis_steps": [
                            "Identify the downtrend",
                            "Look for support level",
                            "Confirm hammer formation",
                            "Wait for confirmation candle",
                            "Enter long position"
                        ]
                    }
                ]
            },
            "doji": {
                "name": "Doji",
                "type": "indecision",
                "bullish_bearish": "neutral",
                "description": "Indecision pattern with open and close at same level",
                "recognition_criteria": {
                    "body_size": "very_small",
                    "shadows": "can_be_long",
                    "position": "anywhere"
                },
                "trading_significance": "Market indecision, potential reversal",
                "success_rate": 0.60,
                "example_scenarios": [
                    {
                        "title": "Doji at Resistance",
                        "description": "Doji pattern forming at resistance level",
                        "chart_data": self._generate_doji_chart_data(),
                        "analysis_steps": [
                            "Identify uptrend",
                            "Look for resistance level",
                            "Confirm doji formation",
                            "Wait for next candle direction",
                            "Trade in direction of breakout"
                        ]
                    }
                ]
            },
            "engulfing": {
                "name": "Engulfing",
                "type": "reversal",
                "bullish_bearish": "both",
                "description": "Large candle engulfs previous candle completely",
                "recognition_criteria": {
                    "current_body": "large",
                    "previous_body": "smaller",
                    "engulfment": "complete",
                    "opposite_colors": True
                },
                "trading_significance": "Strong reversal signal",
                "success_rate": 0.80,
                "example_scenarios": [
                    {
                        "title": "Bullish Engulfing",
                        "description": "Green candle engulfs red candle",
                        "chart_data": self._generate_bullish_engulfing_data(),
                        "analysis_steps": [
                            "Identify downtrend",
                            "Look for small red candle",
                            "Confirm large green engulfing",
                            "Check volume confirmation",
                            "Enter long position"
                        ]
                    }
                ]
            }
        }
    
    def _initialize_volume_scenarios(self) -> Dict[str, Any]:
        """Initialize volume analysis scenarios"""
        return {
            "volume_breakout": {
                "title": "Volume Breakout Analysis",
                "description": "Analyzing volume during price breakouts",
                "scenarios": [
                    {
                        "name": "High Volume Breakout",
                        "description": "Price breaks resistance with high volume",
                        "chart_data": self._generate_volume_breakout_data(),
                        "analysis_points": [
                            "Previous resistance level",
                            "Volume spike during breakout",
                            "Price confirmation",
                            "Volume sustainability",
                            "Target calculation"
                        ],
                        "trading_signal": "Strong Buy",
                        "confidence": 85
                    },
                    {
                        "name": "Low Volume Breakout",
                        "description": "Price breaks resistance with low volume",
                        "chart_data": self._generate_low_volume_breakout_data(),
                        "analysis_points": [
                            "Weak volume during breakout",
                            "Potential false breakout",
                            "Wait for volume confirmation",
                            "Risk of reversal",
                            "Conservative approach"
                        ],
                        "trading_signal": "Hold/Wait",
                        "confidence": 45
                    }
                ]
            },
            "volume_divergence": {
                "title": "Volume-Price Divergence",
                "description": "Identifying divergences between price and volume",
                "scenarios": [
                    {
                        "name": "Bullish Divergence",
                        "description": "Price makes lower low, volume makes higher low",
                        "chart_data": self._generate_bullish_divergence_data(),
                        "analysis_points": [
                            "Price trend analysis",
                            "Volume trend analysis",
                            "Divergence confirmation",
                            "Reversal probability",
                            "Entry strategy"
                        ],
                        "trading_signal": "Buy",
                        "confidence": 70
                    }
                ]
            }
        }
    
    def _initialize_trading_signals(self) -> Dict[str, Any]:
        """Initialize trading signal examples"""
        return {
            "strong_buy_signals": {
                "title": "Strong Buy Signals",
                "description": "Multiple confirmations for strong buy signals",
                "examples": [
                    {
                        "name": "Multi-Timeframe Bullish",
                        "description": "Bullish signals across multiple timeframes",
                        "chart_data": self._generate_multi_timeframe_bullish_data(),
                        "confirmations": [
                            "Daily chart: Bullish engulfing",
                            "4H chart: RSI oversold bounce",
                            "1H chart: Volume spike",
                            "15M chart: MACD crossover"
                        ],
                        "risk_management": {
                            "stop_loss": "Below recent low",
                            "take_profit": "Next resistance level",
                            "risk_reward": "1:2"
                        }
                    }
                ]
            },
            "strong_sell_signals": {
                "title": "Strong Sell Signals",
                "description": "Multiple confirmations for strong sell signals",
                "examples": [
                    {
                        "name": "Distribution Pattern",
                        "description": "Institutional selling with volume",
                        "chart_data": self._generate_distribution_pattern_data(),
                        "confirmations": [
                            "High volume on down days",
                            "Lower volume on up days",
                            "Price rejection at resistance",
                            "Bearish divergence"
                        ],
                        "risk_management": {
                            "stop_loss": "Above recent high",
                            "take_profit": "Next support level",
                            "risk_reward": "1:2"
                        }
                    }
                ]
            }
        }
    
    def _initialize_quiz_questions(self) -> Dict[str, List[Dict]]:
        """Initialize quiz questions for each lesson"""
        return {
            "pattern_recognition": [
                {
                    "id": "hammer_identification",
                    "question": "Which of the following best describes a hammer pattern?",
                    "options": [
                        "Small body with long upper shadow",
                        "Small body with long lower shadow",
                        "Large body with equal shadows",
                        "No body, only shadows"
                    ],
                    "correct_answer": 1,
                    "explanation": "A hammer has a small body with a long lower shadow, indicating buying pressure at the lows.",
                    "difficulty": DifficultyLevel.BEGINNER
                },
                {
                    "id": "doji_significance",
                    "question": "What does a doji pattern typically indicate?",
                    "options": [
                        "Strong bullish momentum",
                        "Strong bearish momentum",
                        "Market indecision",
                        "Volume spike"
                    ],
                    "correct_answer": 2,
                    "explanation": "A doji indicates market indecision as buyers and sellers are in equilibrium.",
                    "difficulty": DifficultyLevel.BEGINNER
                }
            ],
            "volume_analysis": [
                {
                    "id": "volume_confirmation",
                    "question": "What does high volume during a price breakout typically indicate?",
                    "options": [
                        "Weak breakout",
                        "Strong institutional interest",
                        "Market manipulation",
                        "Low liquidity"
                    ],
                    "correct_answer": 1,
                    "explanation": "High volume during breakouts indicates strong institutional interest and validates the move.",
                    "difficulty": DifficultyLevel.INTERMEDIATE
                }
            ],
            "trading_signals": [
                {
                    "id": "signal_confirmation",
                    "question": "How many confirmations should you ideally have before entering a trade?",
                    "options": [
                        "One confirmation",
                        "Two confirmations",
                        "Three or more confirmations",
                        "No confirmations needed"
                    ],
                    "correct_answer": 2,
                    "explanation": "Multiple confirmations increase the probability of success and reduce false signals.",
                    "difficulty": DifficultyLevel.INTERMEDIATE
                }
            ]
        }
    
    async def start_animation_session(
        self,
        user_id: int,
        animation_type: AnimationType,
        symbol: str = "RELIANCE",
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    ) -> str:
        """Start a new animation teaching session"""
        try:
            session_id = f"session_{user_id}_{animation_type}_{uuid.uuid4().hex[:8]}"
            
            # Get animation template
            template = self.animation_templates[animation_type]
            
            # Create session data
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "animation_type": animation_type,
                "symbol": symbol,
                "difficulty": difficulty,
                "template": template,
                "current_lesson": 0,
                "current_step": 0,
                "total_steps": self._calculate_total_steps(template),
                "started_at": datetime.now(),
                "progress": 0.0,
                "quiz_scores": [],
                "is_active": True
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Initialize user progress if not exists
            if user_id not in self.user_progress:
                self.user_progress[user_id] = {
                    "total_sessions": 0,
                    "completed_sessions": 0,
                    "average_score": 0.0,
                    "skill_levels": {
                        AnimationType.PATTERN_RECOGNITION: 0.0,
                        AnimationType.VOLUME_ANALYSIS: 0.0,
                        AnimationType.TRADING_SIGNALS: 0.0,
                        AnimationType.OPTIONS_TRADING: 0.0
                    }
                }
            
            logger.info(f"Animation session {session_id} started for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting animation session: {e}")
            raise
    
    async def get_animation_step(
        self,
        session_id: str,
        step_number: int
    ) -> Dict[str, Any]:
        """Get specific animation step with interactive content"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            animation_type = session["animation_type"]
            
            # Generate step content based on animation type
            step_content = await self._generate_step_content(
                animation_type,
                step_number,
                session["symbol"],
                session["difficulty"]
            )
            
            # Update session progress
            session["current_step"] = step_number
            session["progress"] = (step_number / session["total_steps"]) * 100
            
            return {
                "session_id": session_id,
                "step_number": step_number,
                "step_content": step_content,
                "progress": session["progress"],
                "is_completed": step_number >= session["total_steps"]
            }
            
        except Exception as e:
            logger.error(f"Error getting animation step: {e}")
            raise
    
    async def submit_quiz_answer(
        self,
        session_id: str,
        question_id: str,
        user_answer: int,
        time_taken: float
    ) -> Dict[str, Any]:
        """Submit quiz answer and get feedback"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            
            # Find question
            animation_type = session["animation_type"]
            questions = self.quiz_questions.get(animation_type.value, [])
            
            question = None
            for q in questions:
                if q["id"] == question_id:
                    question = q
                    break
            
            if not question:
                raise ValueError("Question not found")
            
            # Check answer
            is_correct = user_answer == question["correct_answer"]
            
            # Calculate score based on correctness and time
            base_score = 100 if is_correct else 0
            time_bonus = max(0, 20 - time_taken)  # Bonus for quick answers
            final_score = min(100, base_score + time_bonus)
            
            # Store quiz result
            quiz_result = {
                "question_id": question_id,
                "user_answer": user_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "time_taken": time_taken,
                "score": final_score,
                "timestamp": datetime.now()
            }
            
            session["quiz_scores"].append(quiz_result)
            
            return {
                "is_correct": is_correct,
                "correct_answer": question["correct_answer"],
                "explanation": question["explanation"],
                "score": final_score,
                "time_taken": time_taken,
                "overall_progress": session["progress"]
            }
            
        except Exception as e:
            logger.error(f"Error submitting quiz answer: {e}")
            raise
    
    async def complete_animation_session(self, session_id: str) -> Dict[str, Any]:
        """Complete animation session and calculate final results"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError("Session not found")
            
            session = self.active_sessions[session_id]
            user_id = session["user_id"]
            
            # Calculate final score
            quiz_scores = session["quiz_scores"]
            if quiz_scores:
                average_score = sum(q["score"] for q in quiz_scores) / len(quiz_scores)
            else:
                average_score = 0.0
            
            # Update user progress
            user_progress = self.user_progress[user_id]
            user_progress["total_sessions"] += 1
            user_progress["completed_sessions"] += 1
            
            # Update skill level for this animation type
            animation_type = session["animation_type"]
            current_skill = user_progress["skill_levels"][animation_type]
            new_skill = min(100, current_skill + (average_score * 0.1))  # Gradual improvement
            user_progress["skill_levels"][animation_type] = new_skill
            
            # Update overall average score
            total_sessions = user_progress["total_sessions"]
            current_avg = user_progress["average_score"]
            user_progress["average_score"] = ((current_avg * (total_sessions - 1)) + average_score) / total_sessions
            
            # Mark session as completed
            session["is_active"] = False
            session["completed_at"] = datetime.now()
            session["final_score"] = average_score
            
            # Generate completion certificate
            certificate = await self._generate_completion_certificate(session, average_score)
            
            logger.info(f"Animation session {session_id} completed with score {average_score}")
            
            return {
                "session_id": session_id,
                "final_score": average_score,
                "certificate": certificate,
                "skill_progression": user_progress["skill_levels"],
                "overall_progress": user_progress
            }
            
        except Exception as e:
            logger.error(f"Error completing animation session: {e}")
            raise
    
    async def get_user_progress(self, user_id: int) -> Dict[str, Any]:
        """Get user's learning progress and achievements"""
        try:
            if user_id not in self.user_progress:
                return {
                    "user_id": user_id,
                    "total_sessions": 0,
                    "completed_sessions": 0,
                    "average_score": 0.0,
                    "skill_levels": {
                        AnimationType.PATTERN_RECOGNITION: 0.0,
                        AnimationType.VOLUME_ANALYSIS: 0.0,
                        AnimationType.TRADING_SIGNALS: 0.0,
                        AnimationType.OPTIONS_TRADING: 0.0
                    },
                    "achievements": [],
                    "recommendations": []
                }
            
            progress = self.user_progress[user_id]
            
            # Generate achievements
            achievements = await self._generate_achievements(user_id, progress)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(progress)
            
            return {
                "user_id": user_id,
                **progress,
                "achievements": achievements,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            raise
    
    async def _generate_step_content(
        self,
        animation_type: AnimationType,
        step_number: int,
        symbol: str,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """Generate interactive step content"""
        try:
            if animation_type == AnimationType.PATTERN_RECOGNITION:
                return await self._generate_pattern_step(step_number, symbol, difficulty)
            elif animation_type == AnimationType.VOLUME_ANALYSIS:
                return await self._generate_volume_step(step_number, symbol, difficulty)
            elif animation_type == AnimationType.TRADING_SIGNALS:
                return await self._generate_trading_step(step_number, symbol, difficulty)
            elif animation_type == AnimationType.OPTIONS_TRADING:
                return await self._generate_options_step(step_number, symbol, difficulty)
            else:
                raise ValueError(f"Unsupported animation type: {animation_type}")
                
        except Exception as e:
            logger.error(f"Error generating step content: {e}")
            raise
    
    async def _generate_pattern_step(
        self,
        step_number: int,
        symbol: str,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """Generate pattern recognition step"""
        patterns = ["hammer", "doji", "engulfing"]
        pattern = patterns[step_number % len(patterns)]
        pattern_data = self.candlestick_patterns[pattern]
        
        return {
            "step_type": "pattern_recognition",
            "title": f"Learning {pattern_data['name']} Pattern",
            "description": pattern_data["description"],
            "chart_data": pattern_data["example_scenarios"][0]["chart_data"],
            "annotations": [
                {
                    "type": "highlight",
                    "element": "candlestick",
                    "index": -1,  # Last candle
                    "color": "#ff6b6b",
                    "message": f"This is a {pattern_data['name']} pattern"
                }
            ],
            "interactive_elements": [
                {
                    "type": "click_annotation",
                    "element": "candlestick",
                    "message": "Click on the pattern to learn more"
                }
            ],
            "explanations": pattern_data["example_scenarios"][0]["analysis_steps"],
            "quiz_question": self._get_random_quiz_question("pattern_recognition", difficulty)
        }
    
    async def _generate_volume_step(
        self,
        step_number: int,
        symbol: str,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """Generate volume analysis step"""
        scenarios = list(self.volume_scenarios.keys())
        scenario_key = scenarios[step_number % len(scenarios)]
        scenario_data = self.volume_scenarios[scenario_key]
        
        return {
            "step_type": "volume_analysis",
            "title": scenario_data["title"],
            "description": scenario_data["description"],
            "chart_data": scenario_data["scenarios"][0]["chart_data"],
            "annotations": [
                {
                    "type": "volume_bar",
                    "element": "volume",
                    "index": -1,
                    "color": "#4ecdc4",
                    "message": "High volume during breakout"
                }
            ],
            "interactive_elements": [
                {
                    "type": "volume_analysis",
                    "element": "volume_chart",
                    "message": "Analyze the volume pattern"
                }
            ],
            "explanations": scenario_data["scenarios"][0]["analysis_points"],
            "trading_signal": scenario_data["scenarios"][0]["trading_signal"],
            "confidence": scenario_data["scenarios"][0]["confidence"]
        }
    
    async def _generate_trading_step(
        self,
        step_number: int,
        symbol: str,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """Generate trading signals step"""
        signal_types = list(self.trading_signal_examples.keys())
        signal_key = signal_types[step_number % len(signal_types)]
        signal_data = self.trading_signal_examples[signal_key]
        
        return {
            "step_type": "trading_signals",
            "title": signal_data["title"],
            "description": signal_data["description"],
            "chart_data": signal_data["examples"][0]["chart_data"],
            "annotations": [
                {
                    "type": "signal_marker",
                    "element": "price",
                    "index": -1,
                    "color": "#96ceb4",
                    "message": "Strong Buy Signal"
                }
            ],
            "interactive_elements": [
                {
                    "type": "signal_confirmation",
                    "element": "multi_timeframe",
                    "message": "Check multiple timeframes for confirmation"
                }
            ],
            "confirmations": signal_data["examples"][0]["confirmations"],
            "risk_management": signal_data["examples"][0]["risk_management"]
        }
    
    async def _generate_options_step(
        self,
        step_number: int,
        symbol: str,
        difficulty: DifficultyLevel
    ) -> Dict[str, Any]:
        """Generate options trading step"""
        return {
            "step_type": "options_trading",
            "title": "Options Greeks Analysis",
            "description": "Understanding Delta, Gamma, Theta, and Vega",
            "chart_data": self._generate_options_chart_data(),
            "annotations": [
                {
                    "type": "greeks_display",
                    "element": "options_panel",
                    "color": "#feca57",
                    "message": "Monitor Greeks for risk management"
                }
            ],
            "interactive_elements": [
                {
                    "type": "greeks_calculator",
                    "element": "options_calculator",
                    "message": "Calculate Greeks for different scenarios"
                }
            ],
            "greeks_explanation": {
                "delta": "Price sensitivity to underlying asset",
                "gamma": "Rate of change of delta",
                "theta": "Time decay",
                "vega": "Volatility sensitivity"
            }
        }
    
    def _calculate_total_steps(self, template: Dict[str, Any]) -> int:
        """Calculate total steps for animation template"""
        total_steps = 0
        for lesson in template["lessons"]:
            total_steps += lesson["duration"]  # Assuming 1 step per minute
        return total_steps
    
    def _get_random_quiz_question(self, category: str, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Get random quiz question for category and difficulty"""
        questions = self.quiz_questions.get(category, [])
        filtered_questions = [q for q in questions if q["difficulty"] == difficulty]
        
        if not filtered_questions:
            filtered_questions = questions  # Fallback to any difficulty
        
        if filtered_questions:
            import random
            return random.choice(filtered_questions)
        else:
            return None
    
    async def _generate_completion_certificate(
        self,
        session: Dict[str, Any],
        score: float
    ) -> Dict[str, Any]:
        """Generate completion certificate"""
        return {
            "certificate_id": f"cert_{session['id']}",
            "user_id": session["user_id"],
            "animation_type": session["animation_type"],
            "symbol": session["symbol"],
            "difficulty": session["difficulty"],
            "final_score": score,
            "completion_date": datetime.now().isoformat(),
            "certificate_text": f"Congratulations! You completed {session['animation_type']} training with {score:.1f}% accuracy.",
            "badge": self._generate_badge(score)
        }
    
    def _generate_badge(self, score: float) -> str:
        """Generate achievement badge based on score"""
        if score >= 90:
            return "expert"
        elif score >= 80:
            return "advanced"
        elif score >= 70:
            return "intermediate"
        else:
            return "beginner"
    
    async def _generate_achievements(self, user_id: int, progress: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate user achievements"""
        achievements = []
        
        # Completion achievements
        if progress["completed_sessions"] >= 1:
            achievements.append({
                "id": "first_completion",
                "name": "First Steps",
                "description": "Completed your first animation session",
                "badge": "bronze"
            })
        
        if progress["completed_sessions"] >= 10:
            achievements.append({
                "id": "dedicated_learner",
                "name": "Dedicated Learner",
                "description": "Completed 10 animation sessions",
                "badge": "silver"
            })
        
        # Skill achievements
        for skill_type, skill_level in progress["skill_levels"].items():
            if skill_level >= 80:
                achievements.append({
                    "id": f"expert_{skill_type}",
                    "name": f"Expert in {skill_type.replace('_', ' ').title()}",
                    "description": f"Mastered {skill_type.replace('_', ' ')}",
                    "badge": "gold"
                })
        
        return achievements
    
    async def _generate_recommendations(self, progress: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate learning recommendations"""
        recommendations = []
        
        # Find lowest skill level
        skill_levels = progress["skill_levels"]
        lowest_skill = min(skill_levels.items(), key=lambda x: x[1])
        
        if lowest_skill[1] < 50:
            recommendations.append({
                "type": "skill_improvement",
                "title": f"Improve {lowest_skill[0].replace('_', ' ').title()}",
                "description": f"Your {lowest_skill[0].replace('_', ' ')} skills need attention",
                "priority": "high"
            })
        
        # Recommend next difficulty level
        if progress["average_score"] >= 80:
            recommendations.append({
                "type": "difficulty_upgrade",
                "title": "Try Advanced Level",
                "description": "You're ready for more challenging content",
                "priority": "medium"
            })
        
        return recommendations
    
    # Mock data generation methods
    def _generate_hammer_chart_data(self) -> List[Dict]:
        """Generate mock hammer pattern chart data"""
        return [
            {"time": "2024-01-01", "open": 100, "high": 102, "low": 95, "close": 101},
            {"time": "2024-01-02", "open": 101, "high": 103, "low": 98, "close": 100},
            {"time": "2024-01-03", "open": 100, "high": 101, "low": 90, "close": 100.5},  # Hammer
            {"time": "2024-01-04", "open": 100.5, "high": 105, "low": 100, "close": 104}
        ]
    
    def _generate_doji_chart_data(self) -> List[Dict]:
        """Generate mock doji pattern chart data"""
        return [
            {"time": "2024-01-01", "open": 100, "high": 105, "low": 98, "close": 103},
            {"time": "2024-01-02", "open": 103, "high": 107, "low": 101, "close": 105},
            {"time": "2024-01-03", "open": 105, "high": 106, "low": 104, "close": 105},  # Doji
            {"time": "2024-01-04", "open": 105, "high": 108, "low": 103, "close": 107}
        ]
    
    def _generate_bullish_engulfing_data(self) -> List[Dict]:
        """Generate mock bullish engulfing pattern data"""
        return [
            {"time": "2024-01-01", "open": 100, "high": 102, "low": 98, "close": 99},
            {"time": "2024-01-02", "open": 99, "high": 101, "low": 97, "close": 98},
            {"time": "2024-01-03", "open": 98, "high": 100, "low": 96, "close": 97},
            {"time": "2024-01-04", "open": 97, "high": 103, "low": 96, "close": 102}  # Engulfing
        ]
    
    def _generate_volume_breakout_data(self) -> List[Dict]:
        """Generate mock volume breakout data"""
        return {
            "price_data": [
                {"time": "2024-01-01", "open": 100, "high": 102, "low": 98, "close": 101},
                {"time": "2024-01-02", "open": 101, "high": 103, "low": 99, "close": 102},
                {"time": "2024-01-03", "open": 102, "high": 105, "low": 101, "close": 104},  # Breakout
                {"time": "2024-01-04", "open": 104, "high": 107, "low": 103, "close": 106}
            ],
            "volume_data": [
                {"time": "2024-01-01", "volume": 1000000},
                {"time": "2024-01-02", "volume": 1200000},
                {"time": "2024-01-03", "volume": 3000000},  # High volume
                {"time": "2024-01-04", "volume": 2500000}
            ]
        }
    
    def _generate_low_volume_breakout_data(self) -> List[Dict]:
        """Generate mock low volume breakout data"""
        return {
            "price_data": [
                {"time": "2024-01-01", "open": 100, "high": 102, "low": 98, "close": 101},
                {"time": "2024-01-02", "open": 101, "high": 103, "low": 99, "close": 102},
                {"time": "2024-01-03", "open": 102, "high": 105, "low": 101, "close": 104},  # Breakout
                {"time": "2024-01-04", "open": 104, "high": 103, "low": 100, "close": 101}  # Reversal
            ],
            "volume_data": [
                {"time": "2024-01-01", "volume": 1000000},
                {"time": "2024-01-02", "volume": 1200000},
                {"time": "2024-01-03", "volume": 800000},  # Low volume
                {"time": "2024-01-04", "volume": 1500000}
            ]
        }
    
    def _generate_bullish_divergence_data(self) -> List[Dict]:
        """Generate mock bullish divergence data"""
        return {
            "price_data": [
                {"time": "2024-01-01", "open": 100, "high": 105, "low": 98, "close": 103},
                {"time": "2024-01-02", "open": 103, "high": 104, "low": 100, "close": 101},
                {"time": "2024-01-03", "open": 101, "high": 102, "low": 98, "close": 99},  # Lower low
                {"time": "2024-01-04", "open": 99, "high": 103, "low": 97, "close": 102}
            ],
            "volume_data": [
                {"time": "2024-01-01", "volume": 2000000},
                {"time": "2024-01-02", "volume": 1800000},
                {"time": "2024-01-03", "volume": 2200000},  # Higher volume on lower low
                {"time": "2024-01-04", "volume": 1900000}
            ]
        }
    
    def _generate_multi_timeframe_bullish_data(self) -> Dict[str, List[Dict]]:
        """Generate mock multi-timeframe bullish data"""
        return {
            "daily": [
                {"time": "2024-01-01", "open": 100, "high": 102, "low": 98, "close": 101},
                {"time": "2024-01-02", "open": 101, "high": 103, "low": 99, "close": 102},
                {"time": "2024-01-03", "open": 102, "high": 105, "low": 101, "close": 104}
            ],
            "4h": [
                {"time": "2024-01-03T00:00", "open": 102, "high": 103, "low": 101, "close": 102.5},
                {"time": "2024-01-03T04:00", "open": 102.5, "high": 104, "low": 102, "close": 103.5},
                {"time": "2024-01-03T08:00", "open": 103.5, "high": 105, "low": 103, "close": 104}
            ],
            "1h": [
                {"time": "2024-01-03T08:00", "open": 103.5, "high": 104, "low": 103, "close": 103.8},
                {"time": "2024-01-03T09:00", "open": 103.8, "high": 104.5, "low": 103.5, "close": 104.2},
                {"time": "2024-01-03T10:00", "open": 104.2, "high": 105, "low": 104, "close": 104}
            ]
        }
    
    def _generate_distribution_pattern_data(self) -> List[Dict]:
        """Generate mock distribution pattern data"""
        return [
            {"time": "2024-01-01", "open": 100, "high": 102, "low": 98, "close": 101, "volume": 1500000},
            {"time": "2024-01-02", "open": 101, "high": 103, "low": 99, "close": 100, "volume": 2000000},  # High vol down
            {"time": "2024-01-03", "open": 100, "high": 102, "low": 98, "close": 101, "volume": 1200000},  # Low vol up
            {"time": "2024-01-04", "open": 101, "high": 100, "low": 97, "close": 98, "volume": 1800000}   # High vol down
        ]
    
    def _generate_options_chart_data(self) -> Dict[str, Any]:
        """Generate mock options chart data"""
        return {
            "underlying_price": 100,
            "options_data": [
                {
                    "strike": 95,
                    "call_premium": 8.5,
                    "put_premium": 2.1,
                    "delta": 0.75,
                    "gamma": 0.02,
                    "theta": -0.05,
                    "vega": 0.15
                },
                {
                    "strike": 100,
                    "call_premium": 5.2,
                    "put_premium": 5.2,
                    "delta": 0.50,
                    "gamma": 0.03,
                    "theta": -0.08,
                    "vega": 0.20
                },
                {
                    "strike": 105,
                    "call_premium": 2.8,
                    "put_premium": 8.9,
                    "delta": 0.25,
                    "gamma": 0.02,
                    "theta": -0.05,
                    "vega": 0.15
                }
            ]
        }
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            # Test basic functionality
            return len(self.animation_templates) > 0
        except Exception:
            return False
    
    def clear_storage(self):
        """Clear all storage (for testing)"""
        self.user_progress.clear()
        self.active_sessions.clear()
        logger.info("Animation teaching storage cleared")
