"""
Educational Service for Stock Market Learning
Comprehensive teaching system with AI-powered explanations
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import asyncio

logger = logging.getLogger(__name__)

class EducationalService:
    def __init__(self):
        self.learning_paths = self._initialize_learning_paths()
        self.concepts = self._initialize_concepts()
        self.strategies = self._initialize_strategies()
        
    def _initialize_learning_paths(self) -> Dict:
        """Initialize structured learning paths"""
        return {
            "beginner": {
                "name": "Stock Market Basics",
                "duration": "2-3 weeks",
                "modules": [
                    {
                        "id": "market_fundamentals",
                        "title": "Market Fundamentals",
                        "lessons": [
                            "What is Stock Market?",
                            "How Stocks Work",
                            "Market Participants",
                            "Market Hours & Sessions"
                        ]
                    },
                    {
                        "id": "basic_concepts",
                        "title": "Basic Concepts",
                        "lessons": [
                            "Stock Price & Volume",
                            "Market Capitalization",
                            "Dividends & Splits",
                            "Bull vs Bear Market"
                        ]
                    },
                    {
                        "id": "order_types",
                        "title": "Order Types",
                        "lessons": [
                            "Market Orders",
                            "Limit Orders",
                            "Stop Loss Orders",
                            "Good Till Triggered (GTT)"
                        ]
                    }
                ]
            },
            "intermediate": {
                "name": "Technical Analysis",
                "duration": "3-4 weeks",
                "modules": [
                    {
                        "id": "chart_patterns",
                        "title": "Chart Patterns",
                        "lessons": [
                            "Support & Resistance",
                            "Trend Lines",
                            "Chart Patterns",
                            "Volume Analysis"
                        ]
                    },
                    {
                        "id": "technical_indicators",
                        "title": "Technical Indicators",
                        "lessons": [
                            "Moving Averages",
                            "RSI (Relative Strength Index)",
                            "MACD",
                            "Bollinger Bands"
                        ]
                    },
                    {
                        "id": "trading_strategies",
                        "title": "Trading Strategies",
                        "lessons": [
                            "Intraday Trading",
                            "Swing Trading",
                            "Position Trading",
                            "Risk Management"
                        ]
                    }
                ]
            },
            "advanced": {
                "name": "Advanced Trading",
                "duration": "4-6 weeks",
                "modules": [
                    {
                        "id": "advanced_analysis",
                        "title": "Advanced Analysis",
                        "lessons": [
                            "Multi-timeframe Analysis",
                            "Fibonacci Retracements",
                            "Elliott Wave Theory",
                            "Market Psychology"
                        ]
                    },
                    {
                        "id": "options_trading",
                        "title": "Options Trading",
                        "lessons": [
                            "Options Basics",
                            "Call & Put Options",
                            "Options Strategies",
                            "Greeks & Risk"
                        ]
                    },
                    {
                        "id": "portfolio_management",
                        "title": "Portfolio Management",
                        "lessons": [
                            "Asset Allocation",
                            "Diversification",
                            "Risk-Return Analysis",
                            "Portfolio Optimization"
                        ]
                    }
                ]
            }
        }
    
    def _initialize_concepts(self) -> Dict:
        """Initialize educational concepts with detailed explanations"""
        return {
            "technical_analysis": {
                "title": "Technical Analysis",
                "description": "Analysis of price movements and volume to predict future price direction",
                "key_points": [
                    "Based on historical price and volume data",
                    "Uses charts and technical indicators",
                    "Assumes market prices reflect all available information",
                    "Helps identify entry and exit points"
                ],
                "examples": [
                    "RSI above 70 indicates overbought condition",
                    "MACD crossover signals trend change",
                    "Support levels act as price floors"
                ]
            },
            "fundamental_analysis": {
                "title": "Fundamental Analysis",
                "description": "Analysis of company financials, industry, and economic factors",
                "key_points": [
                    "Evaluates company's intrinsic value",
                    "Considers financial statements, management, industry",
                    "Long-term investment approach",
                    "Helps identify undervalued stocks"
                ],
                "examples": [
                    "P/E ratio below industry average",
                    "Strong revenue growth",
                    "Low debt-to-equity ratio"
                ]
            },
            "risk_management": {
                "title": "Risk Management",
                "description": "Strategies to protect capital and limit losses",
                "key_points": [
                    "Never risk more than 1-2% per trade",
                    "Use stop-loss orders",
                    "Diversify your portfolio",
                    "Position sizing based on risk"
                ],
                "examples": [
                    "Set stop-loss at 2% below entry",
                    "Don't put all money in one stock",
                    "Use position sizing calculator"
                ]
            }
        }
    
    def _initialize_strategies(self) -> Dict:
        """Initialize trading strategies with detailed explanations"""
        return {
            "intraday": {
                "name": "Intraday Trading",
                "description": "Buying and selling stocks within the same trading day",
                "time_horizon": "Same day (9:15 AM - 3:30 PM)",
                "risk_level": "High",
                "capital_required": "Minimum ₹25,000",
                "strategy_details": {
                    "entry_criteria": [
                        "Strong momentum in first 30 minutes",
                        "Volume above average",
                        "Breakout from resistance",
                        "Positive market sentiment"
                    ],
                    "exit_criteria": [
                        "Target achieved (1:2 risk-reward)",
                        "Stop-loss triggered",
                        "Market closes",
                        "Momentum fades"
                    ],
                    "risk_management": [
                        "Maximum 1% risk per trade",
                        "Stop-loss at 0.5-1% below entry",
                        "Take profit at 1-2% above entry",
                        "Never hold overnight"
                    ],
                    "best_practices": [
                        "Trade only liquid stocks",
                        "Avoid first and last 30 minutes",
                        "Use technical indicators",
                        "Keep emotions in check"
                    ]
                },
                "example_scenario": {
                    "stock": "RELIANCE",
                    "entry_price": 2450,
                    "stop_loss": 2430,
                    "target": 2490,
                    "quantity": 10,
                    "risk": "₹200 (0.8%)",
                    "potential_profit": "₹400 (1.6%)",
                    "reasoning": "Breakout above resistance with high volume"
                }
            },
            "btst": {
                "name": "Buy Today Sell Tomorrow (BTST)",
                "description": "Buying stocks today and selling tomorrow",
                "time_horizon": "1-2 days",
                "risk_level": "Medium-High",
                "capital_required": "Minimum ₹25,000",
                "strategy_details": {
                    "entry_criteria": [
                        "Strong closing momentum",
                        "Positive news or events",
                        "Technical breakout",
                        "Low volatility"
                    ],
                    "exit_criteria": [
                        "Target achieved next day",
                        "Stop-loss triggered",
                        "Negative news",
                        "Technical breakdown"
                    ],
                    "risk_management": [
                        "Maximum 2% risk per trade",
                        "Stop-loss at 1-1.5% below entry",
                        "Take profit at 2-3% above entry",
                        "Monitor overnight news"
                    ],
                    "best_practices": [
                        "Avoid earnings announcements",
                        "Check for corporate actions",
                        "Monitor global markets",
                        "Use limit orders"
                    ]
                },
                "example_scenario": {
                    "stock": "TCS",
                    "entry_price": 3000,
                    "stop_loss": 2970,
                    "target": 3060,
                    "quantity": 8,
                    "risk": "₹240 (1%)",
                    "potential_profit": "₹480 (2%)",
                    "reasoning": "Strong closing with positive sector news"
                }
            },
            "swing_trading": {
                "name": "Swing Trading",
                "description": "Holding stocks for several days to weeks",
                "time_horizon": "3-30 days",
                "risk_level": "Medium",
                "capital_required": "Minimum ₹50,000",
                "strategy_details": {
                    "entry_criteria": [
                        "Trend continuation",
                        "Pullback to support",
                        "Breakout from consolidation",
                        "Positive fundamentals"
                    ],
                    "exit_criteria": [
                        "Target achieved",
                        "Stop-loss triggered",
                        "Trend reversal",
                        "Fundamental change"
                    ],
                    "risk_management": [
                        "Maximum 3% risk per trade",
                        "Stop-loss at 2-3% below entry",
                        "Take profit at 6-9% above entry",
                        "Trail stop-loss"
                    ],
                    "best_practices": [
                        "Focus on trending stocks",
                        "Use multiple timeframes",
                        "Monitor earnings calendar",
                        "Keep trading journal"
                    ]
                },
                "example_scenario": {
                    "stock": "HDFC",
                    "entry_price": 1500,
                    "stop_loss": 1470,
                    "target": 1620,
                    "quantity": 20,
                    "risk": "₹600 (2%)",
                    "potential_profit": "₹2400 (8%)",
                    "reasoning": "Breakout from 3-week consolidation"
                }
            },
            "position_trading": {
                "name": "Position Trading",
                "description": "Long-term holding based on fundamental analysis",
                "time_horizon": "3-12 months",
                "risk_level": "Low-Medium",
                "capital_required": "Minimum ₹1,00,000",
                "strategy_details": {
                    "entry_criteria": [
                        "Undervalued fundamentals",
                        "Strong growth prospects",
                        "Industry leadership",
                        "Dividend yield"
                    ],
                    "exit_criteria": [
                        "Target achieved",
                        "Fundamental deterioration",
                        "Better opportunity",
                        "Portfolio rebalancing"
                    ],
                    "risk_management": [
                        "Maximum 5% risk per trade",
                        "Stop-loss at 10-15% below entry",
                        "Take profit at 30-50% above entry",
                        "Regular review"
                    ],
                    "best_practices": [
                        "Thorough research",
                        "Diversify across sectors",
                        "Monitor quarterly results",
                        "Long-term perspective"
                    ]
                },
                "example_scenario": {
                    "stock": "INFOSYS",
                    "entry_price": 1200,
                    "stop_loss": 1080,
                    "target": 1560,
                    "quantity": 50,
                    "risk": "₹6000 (5%)",
                    "potential_profit": "₹18000 (30%)",
                    "reasoning": "Strong fundamentals with digital transformation theme"
                }
            }
        }
    
    async def get_learning_path(self, level: str = "beginner") -> Dict:
        """Get structured learning path for user level"""
        try:
            if level not in self.learning_paths:
                level = "beginner"
            
            path = self.learning_paths[level]
            
            return {
                "level": level,
                "path": path,
                "progress": await self._get_user_progress(level),
                "recommended_next": await self._get_next_recommendation(level),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting learning path: {e}")
            return {"error": str(e)}
    
    async def get_concept_explanation(self, concept: str) -> Dict:
        """Get detailed explanation of a trading concept"""
        try:
            if concept not in self.concepts:
                return {"error": f"Concept '{concept}' not found"}
            
            concept_data = self.concepts[concept]
            
            return {
                "concept": concept,
                "data": concept_data,
                "related_concepts": await self._get_related_concepts(concept),
                "practical_examples": await self._get_practical_examples(concept),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting concept explanation: {e}")
            return {"error": str(e)}
    
    async def get_strategy_analysis(self, strategy: str, symbol: str = None) -> Dict:
        """Get detailed strategy analysis with examples"""
        try:
            if strategy not in self.strategies:
                return {"error": f"Strategy '{strategy}' not found"}
            
            strategy_data = self.strategies[strategy]
            
            # Add symbol-specific analysis if provided
            if symbol:
                symbol_analysis = await self._analyze_symbol_for_strategy(symbol, strategy)
                strategy_data["symbol_analysis"] = symbol_analysis
            
            return {
                "strategy": strategy,
                "data": strategy_data,
                "risk_assessment": await self._assess_strategy_risk(strategy),
                "success_factors": await self._get_success_factors(strategy),
                "common_mistakes": await self._get_common_mistakes(strategy),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy analysis: {e}")
            return {"error": str(e)}
    
    async def explain_trading_decision(self, symbol: str, action: str, 
                                     technical_data: Dict, fundamental_data: Dict = None) -> Dict:
        """Explain why to buy/sell/hold with detailed technical analysis"""
        try:
            explanation = {
                "symbol": symbol,
                "action": action,
                "confidence": 0.0,
                "reasoning": [],
                "technical_analysis": {},
                "risk_assessment": {},
                "time_horizon": "",
                "entry_exit_strategy": {},
                "educational_content": {}
            }
            
            # Technical Analysis Explanation
            if technical_data:
                explanation["technical_analysis"] = await self._explain_technical_signals(
                    symbol, technical_data
                )
            
            # Fundamental Analysis Explanation
            if fundamental_data:
                explanation["fundamental_analysis"] = await self._explain_fundamental_signals(
                    symbol, fundamental_data
                )
            
            # Risk Assessment
            explanation["risk_assessment"] = await self._assess_trade_risk(
                symbol, action, technical_data
            )
            
            # Time Horizon Recommendation
            explanation["time_horizon"] = await self._recommend_time_horizon(
                symbol, action, technical_data
            )
            
            # Entry/Exit Strategy
            explanation["entry_exit_strategy"] = await self._create_entry_exit_strategy(
                symbol, action, technical_data
            )
            
            # Educational Content
            explanation["educational_content"] = await self._generate_educational_content(
                symbol, action, technical_data
            )
            
            # Overall Confidence
            explanation["confidence"] = await self._calculate_decision_confidence(
                explanation
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining trading decision: {e}")
            return {"error": str(e)}
    
    async def _explain_technical_signals(self, symbol: str, technical_data: Dict) -> Dict:
        """Explain technical analysis signals in detail"""
        try:
            explanations = {}
            
            # RSI Analysis
            if "rsi" in technical_data:
                rsi_value = technical_data["rsi"]
                if rsi_value > 70:
                    explanations["rsi"] = {
                        "value": rsi_value,
                        "signal": "Overbought",
                        "explanation": f"RSI at {rsi_value:.1f} indicates the stock is overbought. This suggests selling pressure may increase soon.",
                        "action": "Consider selling or waiting for pullback",
                        "confidence": 0.7
                    }
                elif rsi_value < 30:
                    explanations["rsi"] = {
                        "value": rsi_value,
                        "signal": "Oversold",
                        "explanation": f"RSI at {rsi_value:.1f} indicates the stock is oversold. This suggests buying opportunity.",
                        "action": "Consider buying or waiting for bounce",
                        "confidence": 0.7
                    }
                else:
                    explanations["rsi"] = {
                        "value": rsi_value,
                        "signal": "Neutral",
                        "explanation": f"RSI at {rsi_value:.1f} is in neutral zone. Look for other signals.",
                        "action": "Wait for clearer signals",
                        "confidence": 0.3
                    }
            
            # MACD Analysis
            if "macd" in technical_data and "macd_signal" in technical_data:
                macd = technical_data["macd"]
                signal = technical_data["macd_signal"]
                
                if macd > signal:
                    explanations["macd"] = {
                        "macd": macd,
                        "signal_line": signal,
                        "signal": "Bullish",
                        "explanation": "MACD line is above signal line, indicating bullish momentum.",
                        "action": "Consider buying",
                        "confidence": 0.6
                    }
                else:
                    explanations["macd"] = {
                        "macd": macd,
                        "signal_line": signal,
                        "signal": "Bearish",
                        "explanation": "MACD line is below signal line, indicating bearish momentum.",
                        "action": "Consider selling",
                        "confidence": 0.6
                    }
            
            # Moving Average Analysis
            if "sma_20" in technical_data and "sma_50" in technical_data:
                sma20 = technical_data["sma_20"]
                sma50 = technical_data["sma_50"]
                current_price = technical_data.get("current_price", 0)
                
                if current_price > sma20 > sma50:
                    explanations["moving_averages"] = {
                        "sma_20": sma20,
                        "sma_50": sma50,
                        "current_price": current_price,
                        "signal": "Strong Uptrend",
                        "explanation": "Price is above both moving averages in ascending order, indicating strong uptrend.",
                        "action": "Consider buying on pullbacks",
                        "confidence": 0.8
                    }
                elif current_price < sma20 < sma50:
                    explanations["moving_averages"] = {
                        "sma_20": sma20,
                        "sma_50": sma50,
                        "current_price": current_price,
                        "signal": "Strong Downtrend",
                        "explanation": "Price is below both moving averages in descending order, indicating strong downtrend.",
                        "action": "Consider selling on rallies",
                        "confidence": 0.8
                    }
            
            # Bollinger Bands Analysis
            if "bb_upper" in technical_data and "bb_lower" in technical_data:
                upper = technical_data["bb_upper"]
                lower = technical_data["bb_lower"]
                current_price = technical_data.get("current_price", 0)
                
                if current_price >= upper:
                    explanations["bollinger_bands"] = {
                        "upper": upper,
                        "lower": lower,
                        "current_price": current_price,
                        "signal": "Overbought",
                        "explanation": "Price is touching upper Bollinger Band, indicating overbought condition.",
                        "action": "Consider selling",
                        "confidence": 0.6
                    }
                elif current_price <= lower:
                    explanations["bollinger_bands"] = {
                        "upper": upper,
                        "lower": lower,
                        "current_price": current_price,
                        "signal": "Oversold",
                        "explanation": "Price is touching lower Bollinger Band, indicating oversold condition.",
                        "action": "Consider buying",
                        "confidence": 0.6
                    }
            
            return explanations
            
        except Exception as e:
            logger.error(f"Error explaining technical signals: {e}")
            return {}
    
    async def _assess_trade_risk(self, symbol: str, action: str, technical_data: Dict) -> Dict:
        """Assess risk for the trading decision"""
        try:
            risk_factors = []
            risk_score = 0.0
            
            # Volatility Risk
            if "atr" in technical_data:
                atr = technical_data["atr"]
                current_price = technical_data.get("current_price", 0)
                volatility_percent = (atr / current_price) * 100
                
                if volatility_percent > 5:
                    risk_factors.append("High volatility - price can move significantly")
                    risk_score += 0.3
                elif volatility_percent > 3:
                    risk_factors.append("Medium volatility - moderate price movements expected")
                    risk_score += 0.2
                else:
                    risk_factors.append("Low volatility - stable price movements")
                    risk_score += 0.1
            
            # Trend Risk
            if "sma_20" in technical_data and "sma_50" in technical_data:
                sma20 = technical_data["sma_20"]
                sma50 = technical_data["sma_50"]
                
                if abs(sma20 - sma50) / sma50 > 0.05:  # 5% difference
                    risk_factors.append("Strong trend - momentum may continue")
                    risk_score += 0.2
                else:
                    risk_factors.append("Weak trend - sideways movement possible")
                    risk_score += 0.3
            
            # Volume Risk
            if "volume" in technical_data:
                volume = technical_data["volume"]
                avg_volume = technical_data.get("avg_volume", volume)
                
                if volume < avg_volume * 0.5:
                    risk_factors.append("Low volume - weak conviction")
                    risk_score += 0.2
                elif volume > avg_volume * 2:
                    risk_factors.append("High volume - strong conviction")
                    risk_score += 0.1
            
            # Overall Risk Assessment
            if risk_score < 0.3:
                risk_level = "Low"
                risk_color = "green"
            elif risk_score < 0.6:
                risk_level = "Medium"
                risk_color = "yellow"
            else:
                risk_level = "High"
                risk_color = "red"
            
            return {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_color": risk_color,
                "risk_factors": risk_factors,
                "recommendations": await self._get_risk_recommendations(risk_level)
            }
            
        except Exception as e:
            logger.error(f"Error assessing trade risk: {e}")
            return {"risk_level": "Unknown", "risk_score": 0.5}
    
    async def _recommend_time_horizon(self, symbol: str, action: str, technical_data: Dict) -> Dict:
        """Recommend appropriate time horizon for the trade"""
        try:
            # Analyze technical indicators to determine time horizon
            time_horizon = "Medium-term (1-4 weeks)"
            reasoning = []
            
            # Check for intraday signals
            if "rsi" in technical_data:
                rsi = technical_data["rsi"]
                if rsi > 70 or rsi < 30:
                    time_horizon = "Short-term (1-3 days)"
                    reasoning.append("RSI extreme levels suggest quick reversal")
            
            # Check for trend strength
            if "sma_20" in technical_data and "sma_50" in technical_data:
                sma20 = technical_data["sma_20"]
                sma50 = technical_data["sma_50"]
                trend_strength = abs(sma20 - sma50) / sma50
                
                if trend_strength > 0.1:  # 10% difference
                    time_horizon = "Long-term (1-3 months)"
                    reasoning.append("Strong trend suggests longer holding period")
                elif trend_strength < 0.02:  # 2% difference
                    time_horizon = "Short-term (1-7 days)"
                    reasoning.append("Weak trend suggests shorter holding period")
            
            # Check volume
            if "volume" in technical_data:
                volume = technical_data["volume"]
                avg_volume = technical_data.get("avg_volume", volume)
                
                if volume > avg_volume * 1.5:
                    reasoning.append("High volume confirms strong move")
                else:
                    reasoning.append("Low volume suggests weak conviction")
            
            return {
                "time_horizon": time_horizon,
                "reasoning": reasoning,
                "recommended_strategies": await self._get_recommended_strategies(time_horizon)
            }
            
        except Exception as e:
            logger.error(f"Error recommending time horizon: {e}")
            return {"time_horizon": "Medium-term (1-4 weeks)", "reasoning": ["Default recommendation"]}
    
    async def _create_entry_exit_strategy(self, symbol: str, action: str, technical_data: Dict) -> Dict:
        """Create detailed entry and exit strategy"""
        try:
            current_price = technical_data.get("current_price", 0)
            
            if action.lower() == "buy":
                # Entry Strategy
                entry_price = current_price
                stop_loss = current_price * 0.97  # 3% below entry
                target = current_price * 1.06     # 6% above entry
                
                strategy = {
                    "action": "BUY",
                    "entry_price": round(entry_price, 2),
                    "stop_loss": round(stop_loss, 2),
                    "target": round(target, 2),
                    "risk_reward_ratio": "1:2",
                    "position_sizing": await self._calculate_position_size(current_price, stop_loss),
                    "entry_reasoning": "Technical indicators suggest bullish momentum",
                    "exit_reasoning": "Take profit at target or stop-loss if trend reverses"
                }
            
            elif action.lower() == "sell":
                # Entry Strategy
                entry_price = current_price
                stop_loss = current_price * 1.03  # 3% above entry
                target = current_price * 0.94     # 6% below entry
                
                strategy = {
                    "action": "SELL",
                    "entry_price": round(entry_price, 2),
                    "stop_loss": round(stop_loss, 2),
                    "target": round(target, 2),
                    "risk_reward_ratio": "1:2",
                    "position_sizing": await self._calculate_position_size(current_price, stop_loss),
                    "entry_reasoning": "Technical indicators suggest bearish momentum",
                    "exit_reasoning": "Take profit at target or stop-loss if trend reverses"
                }
            
            else:  # Hold
                strategy = {
                    "action": "HOLD",
                    "current_price": round(current_price, 2),
                    "reasoning": "Technical indicators are mixed, wait for clearer signals",
                    "next_review": "Monitor for breakout or breakdown",
                    "key_levels": await self._identify_key_levels(technical_data)
                }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error creating entry exit strategy: {e}")
            return {"error": str(e)}
    
    async def _generate_educational_content(self, symbol: str, action: str, technical_data: Dict) -> Dict:
        """Generate educational content related to the trading decision"""
        try:
            educational_content = {
                "key_concepts": [],
                "learning_resources": [],
                "practical_tips": [],
                "common_mistakes": []
            }
            
            # Key Concepts
            if "rsi" in technical_data:
                educational_content["key_concepts"].append({
                    "concept": "RSI (Relative Strength Index)",
                    "explanation": "RSI measures momentum and identifies overbought/oversold conditions",
                    "learning_url": "/learn/technical-analysis/rsi"
                })
            
            if "macd" in technical_data:
                educational_content["key_concepts"].append({
                    "concept": "MACD (Moving Average Convergence Divergence)",
                    "explanation": "MACD shows relationship between two moving averages and momentum",
                    "learning_url": "/learn/technical-analysis/macd"
                })
            
            # Learning Resources
            educational_content["learning_resources"] = [
                {
                    "title": "Technical Analysis Basics",
                    "type": "Video Tutorial",
                    "duration": "15 minutes",
                    "url": "/learn/technical-analysis/basics"
                },
                {
                    "title": "Risk Management Strategies",
                    "type": "Interactive Guide",
                    "duration": "20 minutes",
                    "url": "/learn/risk-management/strategies"
                },
                {
                    "title": "Position Sizing Calculator",
                    "type": "Tool",
                    "url": "/tools/position-sizing"
                }
            ]
            
            # Practical Tips
            educational_content["practical_tips"] = [
                "Always use stop-loss orders to limit risk",
                "Never risk more than 1-2% of your capital per trade",
                "Keep a trading journal to track your decisions",
                "Practice with paper trading before using real money",
                "Stay updated with market news and events"
            ]
            
            # Common Mistakes
            educational_content["common_mistakes"] = [
                "Not using stop-loss orders",
                "Risking too much capital on single trade",
                "Trading based on emotions rather than analysis",
                "Not having a clear exit strategy",
                "Ignoring risk management principles"
            ]
            
            return educational_content
            
        except Exception as e:
            logger.error(f"Error generating educational content: {e}")
            return {}
    
    async def _calculate_position_size(self, entry_price: float, stop_loss: float) -> Dict:
        """Calculate appropriate position size based on risk"""
        try:
            # Assume 1% risk per trade
            risk_per_trade = 0.01
            account_size = 100000  # Default account size
            
            risk_amount = account_size * risk_per_trade
            price_risk = abs(entry_price - stop_loss)
            
            if price_risk > 0:
                position_size = int(risk_amount / price_risk)
                position_value = position_size * entry_price
                
                return {
                    "quantity": position_size,
                    "position_value": round(position_value, 2),
                    "risk_amount": round(risk_amount, 2),
                    "risk_percentage": round((risk_amount / account_size) * 100, 2)
                }
            else:
                return {"error": "Invalid price data"}
                
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"error": str(e)}
    
    async def _get_user_progress(self, level: str) -> Dict:
        """Get user's learning progress"""
        # This would integrate with user database
        return {
            "completed_modules": 0,
            "total_modules": len(self.learning_paths[level]["modules"]),
            "completed_lessons": 0,
            "total_lessons": sum(len(module["lessons"]) for module in self.learning_paths[level]["modules"]),
            "progress_percentage": 0
        }
    
    async def _get_next_recommendation(self, level: str) -> str:
        """Get next recommended learning topic"""
        return f"Complete {self.learning_paths[level]['modules'][0]['title']} module"
    
    async def _get_related_concepts(self, concept: str) -> List[str]:
        """Get related concepts for learning"""
        related_map = {
            "technical_analysis": ["chart_patterns", "technical_indicators", "volume_analysis"],
            "fundamental_analysis": ["financial_statements", "valuation", "industry_analysis"],
            "risk_management": ["position_sizing", "stop_loss", "portfolio_diversification"]
        }
        return related_map.get(concept, [])
    
    async def _get_practical_examples(self, concept: str) -> List[Dict]:
        """Get practical examples for the concept"""
        examples = {
            "technical_analysis": [
                {"title": "RELIANCE Breakout", "description": "How to identify and trade breakouts"},
                {"title": "TCS Support Level", "description": "Using support levels for entry"}
            ],
            "risk_management": [
                {"title": "Position Sizing", "description": "How to calculate position size"},
                {"title": "Stop Loss Placement", "description": "Where to place stop-loss orders"}
            ]
        }
        return examples.get(concept, [])
    
    async def _analyze_symbol_for_strategy(self, symbol: str, strategy: str) -> Dict:
        """Analyze specific symbol for the given strategy"""
        # This would integrate with market data
        return {
            "symbol": symbol,
            "strategy": strategy,
            "suitability": "Good",
            "reasoning": f"{symbol} shows characteristics suitable for {strategy}",
            "risk_level": "Medium"
        }
    
    async def _assess_strategy_risk(self, strategy: str) -> Dict:
        """Assess risk level of the strategy"""
        risk_levels = {
            "intraday": "High",
            "btst": "Medium-High", 
            "swing_trading": "Medium",
            "position_trading": "Low-Medium"
        }
        return {"risk_level": risk_levels.get(strategy, "Medium")}
    
    async def _get_success_factors(self, strategy: str) -> List[str]:
        """Get success factors for the strategy"""
        factors = {
            "intraday": ["Quick decision making", "Risk management", "Market timing"],
            "btst": ["News analysis", "Technical skills", "Risk control"],
            "swing_trading": ["Patience", "Technical analysis", "Trend following"],
            "position_trading": ["Fundamental analysis", "Long-term view", "Diversification"]
        }
        return factors.get(strategy, [])
    
    async def _get_common_mistakes(self, strategy: str) -> List[str]:
        """Get common mistakes for the strategy"""
        mistakes = {
            "intraday": ["Overtrading", "Not using stop-loss", "Emotional decisions"],
            "btst": ["Ignoring overnight news", "Poor risk management", "FOMO trading"],
            "swing_trading": ["Impatience", "Not following trends", "Poor entry timing"],
            "position_trading": ["Lack of research", "Poor diversification", "Ignoring fundamentals"]
        }
        return mistakes.get(strategy, [])
    
    async def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get risk management recommendations"""
        recommendations = {
            "Low": ["Standard position sizing", "Basic stop-loss"],
            "Medium": ["Reduced position size", "Tighter stop-loss", "Monitor closely"],
            "High": ["Minimal position size", "Very tight stop-loss", "Avoid if uncertain"]
        }
        return recommendations.get(risk_level, [])
    
    async def _get_recommended_strategies(self, time_horizon: str) -> List[str]:
        """Get recommended strategies for time horizon"""
        strategies = {
            "Short-term (1-3 days)": ["Intraday Trading", "BTST"],
            "Medium-term (1-4 weeks)": ["Swing Trading"],
            "Long-term (1-3 months)": ["Position Trading", "Swing Trading"]
        }
        return strategies.get(time_horizon, [])
    
    async def _identify_key_levels(self, technical_data: Dict) -> Dict:
        """Identify key support and resistance levels"""
        return {
            "support": technical_data.get("support_levels", []),
            "resistance": technical_data.get("resistance_levels", []),
            "current_price": technical_data.get("current_price", 0)
        }
    
    async def _calculate_decision_confidence(self, explanation: Dict) -> float:
        """Calculate overall confidence in the trading decision"""
        try:
            confidence_factors = []
            
            # Technical analysis confidence
            if "technical_analysis" in explanation:
                tech_signals = explanation["technical_analysis"]
                if tech_signals:
                    avg_confidence = sum(signal.get("confidence", 0.5) for signal in tech_signals.values()) / len(tech_signals)
                    confidence_factors.append(avg_confidence)
            
            # Risk assessment confidence
            if "risk_assessment" in explanation:
                risk_score = explanation["risk_assessment"].get("risk_score", 0.5)
                # Lower risk = higher confidence
                confidence_factors.append(1 - risk_score)
            
            # Overall confidence
            if confidence_factors:
                return round(sum(confidence_factors) / len(confidence_factors), 2)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating decision confidence: {e}")
            return 0.5

# Global instance
educational_service = EducationalService()
