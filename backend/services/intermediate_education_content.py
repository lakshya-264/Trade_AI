"""
Intermediate Education Content
Technical Analysis modules with detailed explanations
"""

def get_intermediate_lessons():
    """Get intermediate level lessons for technical analysis"""
    return {
        # INTERMEDIATE LEVEL - TECHNICAL ANALYSIS
        "chart_patterns_1": {
            "title": "Support & Resistance",
            "level": "intermediate",
            "module": "Chart Patterns",
            "duration": "35 minutes",
            "difficulty": "intermediate",
            "overview": "Understanding the fundamental concepts of support and resistance in technical analysis",
            "learning_objectives": [
                "Define support and resistance levels",
                "Identify support and resistance on charts",
                "Understand the psychology behind S&R",
                "Learn how to trade S&R breakouts and bounces"
            ],
            "content": {
                "introduction": {
                    "text": "Support and resistance are the foundation of technical analysis. These levels represent areas where price has historically found buying or selling pressure, creating psychological barriers for future price movement.",
                    "key_concept": "Support acts as a price floor (demand), while resistance acts as a price ceiling (supply)."
                },
                "main_content": [
                    {
                        "section": "Understanding Support",
                        "content": "Support is a price level where buying interest is strong enough to overcome selling pressure, causing prices to bounce higher.",
                        "detailed_explanation": {
                            "definition": "Price level where demand exceeds supply",
                            "psychology": "Buyers see value and step in",
                            "characteristics": ["Multiple touches", "Volume confirmation", "Time spent at level"],
                            "strength_factors": ["Number of touches", "Volume at level", "Time spent", "Angle of approach"]
                        }
                    },
                    {
                        "section": "Understanding Resistance",
                        "content": "Resistance is a price level where selling interest is strong enough to overcome buying pressure, causing prices to fall lower.",
                        "detailed_explanation": {
                            "definition": "Price level where supply exceeds demand",
                            "psychology": "Sellers see overvaluation and step in",
                            "characteristics": ["Multiple rejections", "Volume confirmation", "Time spent at level"],
                            "strength_factors": ["Number of rejections", "Volume at level", "Time spent", "Angle of approach"]
                        }
                    },
                    {
                        "section": "Role Reversal",
                        "content": "When support is broken, it often becomes resistance. When resistance is broken, it often becomes support.",
                        "mechanism": {
                            "support_to_resistance": "Broken support becomes resistance due to trapped buyers",
                            "resistance_to_support": "Broken resistance becomes support due to trapped sellers",
                            "psychological_factor": "Previous buyers/sellers remember their pain points",
                            "confirmation": "Volume and time spent confirm role reversal"
                        }
                    },
                    {
                        "section": "Trading Applications",
                        "content": "Support and resistance levels provide excellent trading opportunities:",
                        "trading_strategies": {
                            "bounce_trading": {
                                "description": "Buy at support, sell at resistance",
                                "entry": "Price bounces off support/resistance",
                                "stop_loss": "Below support or above resistance",
                                "target": "Next resistance or support level"
                            },
                            "breakout_trading": {
                                "description": "Trade the breakout of S&R levels",
                                "entry": "Price breaks through with volume",
                                "stop_loss": "Back inside the broken level",
                                "target": "Measured move or next level"
                            },
                            "false_breakout": {
                                "description": "Trade the reversal after false breakout",
                                "entry": "Price returns inside the level",
                                "stop_loss": "Beyond the false breakout",
                                "target": "Opposite S&R level"
                            }
                        }
                    }
                ],
                "key_takeaways": [
                    "Support and resistance are psychological price levels",
                    "Multiple touches make levels stronger",
                    "Volume confirmation is crucial",
                    "Role reversal is a common phenomenon",
                    "S&R levels provide excellent trading opportunities"
                ],
                "real_world_example": {
                    "scenario": "Nifty 50 Support at 17,000",
                    "description": "Nifty found strong support at 17,000 level multiple times in 2023. Each bounce was accompanied by high volume, confirming the level's strength. When finally broken in October 2023, it became resistance.",
                    "lesson": "Strong support levels can provide multiple trading opportunities before eventual breakdown."
                }
            },
            "quiz": {
                "questions": [
                    {
                        "question": "What makes a support level stronger?",
                        "options": ["Higher price", "More volume", "Fewer touches", "Lower volatility"],
                        "correct_answer": 1,
                        "explanation": "Volume confirmation makes support levels stronger as it shows real buying interest."
                    },
                    {
                        "question": "What happens when support is broken?",
                        "options": ["It disappears", "It becomes resistance", "It stays support", "Price goes up"],
                        "correct_answer": 1,
                        "explanation": "Broken support often becomes resistance due to trapped buyers and psychological factors."
                    }
                ]
            }
        },
        
        "chart_patterns_2": {
            "title": "Trend Lines",
            "level": "intermediate",
            "module": "Chart Patterns",
            "duration": "30 minutes",
            "difficulty": "intermediate",
            "overview": "Master the art of drawing and trading trend lines for better market timing",
            "learning_objectives": [
                "Learn to identify and draw trend lines",
                "Understand trend line validation criteria",
                "Master trend line trading strategies",
                "Recognize trend line breakouts and failures"
            ],
            "content": {
                "introduction": {
                    "text": "Trend lines are one of the most powerful tools in technical analysis. They help identify the direction of price movement and provide entry and exit signals.",
                    "key_concept": "Trend lines connect significant price points to show the direction of market sentiment."
                },
                "main_content": [
                    {
                        "section": "Drawing Trend Lines",
                        "content": "A valid trend line connects at least two significant price points:",
                        "detailed_explanation": {
                            "uptrend_line": "Connects two or more higher lows",
                            "downtrend_line": "Connects two or more lower highs",
                            "validation": "Requires at least two touches, preferably three",
                            "angle": "Steepness indicates trend strength",
                            "timeframe": "Longer timeframes provide stronger signals"
                        }
                    },
                    {
                        "section": "Trend Line Strength",
                        "content": "The strength of a trend line depends on several factors:",
                        "strength_factors": {
                            "number_of_touches": "More touches = stronger trend line",
                            "angle": "Moderate angles (30-45 degrees) are most reliable",
                            "timeframe": "Longer timeframes provide stronger signals",
                            "volume": "Volume confirmation at trend line touches",
                            "duration": "Longer-lasting trend lines are more significant"
                        }
                    },
                    {
                        "section": "Trading Trend Lines",
                        "content": "Trend lines provide multiple trading opportunities:",
                        "trading_strategies": {
                            "bounce_trading": {
                                "description": "Buy/sell at trend line bounces",
                                "entry": "Price bounces off trend line",
                                "stop_loss": "Below/above trend line",
                                "target": "Previous swing high/low"
                            },
                            "breakout_trading": {
                                "description": "Trade trend line breakouts",
                                "entry": "Price breaks trend line with volume",
                                "stop_loss": "Back inside trend line",
                                "target": "Measured move or next level"
                            },
                            "pullback_trading": {
                                "description": "Trade pullbacks to broken trend lines",
                                "entry": "Price pulls back to broken trend line",
                                "stop_loss": "Beyond pullback low/high",
                                "target": "Breakout target"
                            }
                        }
                    }
                ],
                "key_takeaways": [
                    "Trend lines require at least two touches for validation",
                    "More touches make trend lines stronger",
                    "Volume confirmation is essential",
                    "Trend line breakouts often lead to significant moves",
                    "Avoid forcing trend lines where they don't fit naturally"
                ],
                "real_world_example": {
                    "scenario": "Reliance Industries Uptrend",
                    "description": "Reliance formed a strong uptrend line from ₹2,000 to ₹2,800 over 6 months in 2023. The trend line was tested 4 times with volume confirmation, providing excellent buying opportunities.",
                    "lesson": "Strong trend lines can provide multiple trading opportunities with high probability setups."
                }
            },
            "quiz": {
                "questions": [
                    {
                        "question": "How many touches are required for a valid trend line?",
                        "options": ["One", "Two", "Three", "Four"],
                        "correct_answer": 1,
                        "explanation": "A valid trend line requires at least two touches, though three or more make it stronger."
                    },
                    {
                        "question": "What indicates a strong trend line?",
                        "options": ["Steep angle", "Multiple touches", "High price", "Low volume"],
                        "correct_answer": 1,
                        "explanation": "Multiple touches indicate a strong trend line as it shows consistent price behavior."
                    }
                ]
            }
        },
        
        "technical_indicators_1": {
            "title": "Moving Averages",
            "level": "intermediate",
            "module": "Technical Indicators",
            "duration": "40 minutes",
            "difficulty": "intermediate",
            "overview": "Master moving averages for trend identification and trading signals",
            "learning_objectives": [
                "Understand different types of moving averages",
                "Learn moving average crossover strategies",
                "Master support/resistance with moving averages",
                "Apply moving averages for trend following"
            ],
            "content": {
                "introduction": {
                    "text": "Moving averages smooth out price data to identify trends and provide trading signals. They are among the most widely used technical indicators.",
                    "key_concept": "Moving averages show the average price over a specific period, smoothing out short-term volatility."
                },
                "main_content": [
                    {
                        "section": "Types of Moving Averages",
                        "content": "There are several types of moving averages, each with unique characteristics:",
                        "types": {
                            "simple_moving_average": {
                                "calculation": "Sum of prices divided by period",
                                "characteristics": ["Equal weight to all prices", "Smooth", "Lagging"],
                                "use_case": "Long-term trend identification"
                            },
                            "exponential_moving_average": {
                                "calculation": "Gives more weight to recent prices",
                                "characteristics": ["More responsive", "Less smooth", "Faster signals"],
                                "use_case": "Short-term trading signals"
                            },
                            "weighted_moving_average": {
                                "calculation": "Linear weighting of recent prices",
                                "characteristics": ["Moderate responsiveness", "Balanced smoothness"],
                                "use_case": "Medium-term analysis"
                            }
                        }
                    },
                    {
                        "section": "Common Periods",
                        "content": "Different moving average periods serve different purposes:",
                        "periods": {
                            "short_term": {
                                "periods": ["5, 10, 20"],
                                "use": "Short-term trading signals",
                                "characteristics": ["Fast", "Noisy", "Many signals"]
                            },
                            "medium_term": {
                                "periods": ["50, 100"],
                                "use": "Medium-term trend identification",
                                "characteristics": ["Balanced", "Moderate signals"]
                            },
                            "long_term": {
                                "periods": ["200, 250"],
                                "use": "Long-term trend identification",
                                "characteristics": ["Slow", "Smooth", "Few signals"]
                            }
                        }
                    },
                    {
                        "section": "Trading Strategies",
                        "content": "Moving averages provide several trading strategies:",
                        "strategies": {
                            "crossover_strategy": {
                                "description": "Buy when fast MA crosses above slow MA",
                                "entry": "Golden cross (bullish crossover)",
                                "exit": "Death cross (bearish crossover)",
                                "example": "50 MA crossing above 200 MA"
                            },
                            "price_crossover": {
                                "description": "Buy when price crosses above MA",
                                "entry": "Price breaks above MA",
                                "exit": "Price breaks below MA",
                                "example": "Price crossing above 20 MA"
                            },
                            "ma_support_resistance": {
                                "description": "Use MA as dynamic support/resistance",
                                "entry": "Price bounces off MA",
                                "exit": "Price breaks MA",
                                "example": "Price bouncing off 50 MA in uptrend"
                            }
                        }
                    }
                ],
                "key_takeaways": [
                    "Moving averages smooth price data to show trends",
                    "Different types serve different purposes",
                    "Crossover strategies provide clear signals",
                    "Multiple timeframes increase signal reliability",
                    "Moving averages work best in trending markets"
                ],
                "real_world_example": {
                    "scenario": "Nifty 50 Golden Cross",
                    "description": "In March 2023, Nifty's 50-day MA crossed above 200-day MA, signaling a major trend change. The index rallied 15% over the next 3 months.",
                    "lesson": "Golden crosses often signal major trend changes and provide excellent long-term trading opportunities."
                }
            },
            "quiz": {
                "questions": [
                    {
                        "question": "Which moving average is most responsive to price changes?",
                        "options": ["SMA", "EMA", "WMA", "All are equal"],
                        "correct_answer": 1,
                        "explanation": "EMA gives more weight to recent prices, making it more responsive than SMA."
                    },
                    {
                        "question": "What is a Golden Cross?",
                        "options": ["Price above MA", "Fast MA above slow MA", "Volume spike", "Support break"],
                        "correct_answer": 1,
                        "explanation": "Golden Cross occurs when a faster moving average crosses above a slower one."
                    }
                ]
            }
        },
        
        "technical_indicators_2": {
            "title": "RSI (Relative Strength Index)",
            "level": "intermediate",
            "module": "Technical Indicators",
            "duration": "35 minutes",
            "difficulty": "intermediate",
            "overview": "Master RSI for identifying overbought and oversold conditions",
            "learning_objectives": [
                "Understand RSI calculation and interpretation",
                "Learn overbought/oversold trading strategies",
                "Master RSI divergence patterns",
                "Apply RSI for trend confirmation"
            ],
            "content": {
                "introduction": {
                    "text": "RSI measures the speed and magnitude of price changes, helping identify overbought and oversold conditions in the market.",
                    "key_concept": "RSI oscillates between 0 and 100, with readings above 70 indicating overbought conditions and below 30 indicating oversold conditions."
                },
                "main_content": [
                    {
                        "section": "RSI Calculation",
                        "content": "RSI is calculated using the following formula:",
                        "calculation": {
                            "step_1": "Calculate average gain and average loss over 14 periods",
                            "step_2": "Calculate relative strength (RS) = Average Gain / Average Loss",
                            "step_3": "RSI = 100 - (100 / (1 + RS))",
                            "default_period": "14 periods (can be adjusted)",
                            "range": "0 to 100"
                        }
                    },
                    {
                        "section": "RSI Interpretation",
                        "content": "RSI readings provide different market insights:",
                        "interpretation": {
                            "overbought": {
                                "level": "Above 70",
                                "meaning": "Price may be too high, potential reversal",
                                "action": "Consider selling or reducing positions"
                            },
                            "oversold": {
                                "level": "Below 30",
                                "meaning": "Price may be too low, potential reversal",
                                "action": "Consider buying or adding positions"
                            },
                            "neutral": {
                                "level": "30-70",
                                "meaning": "Normal market conditions",
                                "action": "Trend following strategies"
                            }
                        }
                    },
                    {
                        "section": "RSI Divergence",
                        "content": "RSI divergence occurs when price and RSI move in opposite directions:",
                        "divergence_types": {
                            "bullish_divergence": {
                                "description": "Price makes lower lows, RSI makes higher lows",
                                "signal": "Potential bullish reversal",
                                "confirmation": "RSI breaks above previous high"
                            },
                            "bearish_divergence": {
                                "description": "Price makes higher highs, RSI makes lower highs",
                                "signal": "Potential bearish reversal",
                                "confirmation": "RSI breaks below previous low"
                            }
                        }
                    },
                    {
                        "section": "Trading Strategies",
                        "content": "RSI provides several trading opportunities:",
                        "strategies": {
                            "overbought_oversold": {
                                "description": "Trade reversals at extreme levels",
                                "entry": "RSI exits overbought/oversold zone",
                                "stop_loss": "Beyond extreme level",
                                "target": "Previous swing high/low"
                            },
                            "divergence_trading": {
                                "description": "Trade divergence patterns",
                                "entry": "Divergence confirmation",
                                "stop_loss": "Beyond divergence low/high",
                                "target": "Measured move"
                            },
                            "trend_confirmation": {
                                "description": "Use RSI to confirm trend direction",
                                "bullish": "RSI above 50 in uptrend",
                                "bearish": "RSI below 50 in downtrend",
                                "use": "Filter trades in trend direction"
                            }
                        }
                    }
                ],
                "key_takeaways": [
                    "RSI measures momentum and identifies extremes",
                    "Overbought/oversold levels provide reversal signals",
                    "Divergence patterns often precede reversals",
                    "RSI works best in ranging markets",
                    "Combine RSI with other indicators for confirmation"
                ],
                "real_world_example": {
                    "scenario": "HDFC Bank RSI Divergence",
                    "description": "In August 2023, HDFC Bank made higher highs while RSI made lower highs, showing bearish divergence. The stock corrected 12% over the next month.",
                    "lesson": "RSI divergence often provides early warning signals of potential trend reversals."
                }
            },
            "quiz": {
                "questions": [
                    {
                        "question": "What RSI level typically indicates overbought conditions?",
                        "options": ["Above 50", "Above 70", "Above 80", "Above 90"],
                        "correct_answer": 1,
                        "explanation": "RSI above 70 typically indicates overbought conditions."
                    },
                    {
                        "question": "What is bullish divergence?",
                        "options": ["Price and RSI both rising", "Price falling, RSI rising", "Price rising, RSI falling", "Both falling"],
                        "correct_answer": 1,
                        "explanation": "Bullish divergence occurs when price makes lower lows while RSI makes higher lows."
                    }
                ]
            }
        },
        
        "trading_strategies_1": {
            "title": "Intraday Trading",
            "level": "intermediate",
            "module": "Trading Strategies",
            "duration": "45 minutes",
            "difficulty": "intermediate",
            "overview": "Master intraday trading strategies for consistent daily profits",
            "learning_objectives": [
                "Understand intraday trading fundamentals",
                "Learn momentum-based strategies",
                "Master scalping techniques",
                "Apply risk management for intraday trading"
            ],
            "content": {
                "introduction": {
                    "text": "Intraday trading involves buying and selling stocks within the same trading day, capitalizing on short-term price movements for quick profits.",
                    "key_concept": "Intraday trading requires discipline, quick decision-making, and strict risk management to be profitable."
                },
                "main_content": [
                    {
                        "section": "Intraday Trading Fundamentals",
                        "content": "Successful intraday trading requires understanding key fundamentals:",
                        "fundamentals": {
                            "market_timing": "Trade during high-volume periods (9:30-11:00 AM, 2:00-3:30 PM)",
                            "volatility": "Choose stocks with adequate volatility (2-5% daily range)",
                            "liquidity": "Focus on liquid stocks for easy entry/exit",
                            "news_awareness": "Stay updated with market-moving news",
                            "risk_management": "Never risk more than 1-2% per trade"
                        }
                    },
                    {
                        "section": "Momentum Strategies",
                        "content": "Momentum strategies capitalize on strong price movements:",
                        "strategies": {
                            "breakout_trading": {
                                "description": "Trade breakouts from consolidation patterns",
                                "entry": "Price breaks resistance with volume",
                                "stop_loss": "Below breakout level",
                                "target": "1:2 or 1:3 risk-reward ratio"
                            },
                            "gap_trading": {
                                "description": "Trade gap openings",
                                "gap_up": "Buy if gap holds above previous close",
                                "gap_down": "Short if gap holds below previous close",
                                "confirmation": "Volume and momentum confirmation"
                            },
                            "news_momentum": {
                                "description": "Trade on news-driven moves",
                                "entry": "Strong reaction to news",
                                "timing": "Enter within first 15-30 minutes",
                                "exit": "Momentum fades or target reached"
                            }
                        }
                    },
                    {
                        "section": "Scalping Techniques",
                        "content": "Scalping involves quick trades for small profits:",
                        "techniques": {
                            "bid_ask_spread": {
                                "description": "Capture bid-ask spread",
                                "method": "Buy at bid, sell at ask",
                                "profit": "Small but consistent",
                                "requirement": "High liquidity stocks"
                            },
                            "level_2_trading": {
                                "description": "Use order book for entries",
                                "method": "Watch large orders at key levels",
                                "entry": "Follow institutional flow",
                                "advantage": "Better entry timing"
                            },
                            "time_based_exits": {
                                "description": "Exit trades based on time",
                                "method": "Set maximum holding time",
                                "reason": "Avoid overnight risk",
                                "discipline": "Stick to time limits"
                            }
                        }
                    },
                    {
                        "section": "Risk Management",
                        "content": "Proper risk management is crucial for intraday trading:",
                        "risk_rules": {
                            "position_sizing": "Risk only 1-2% of capital per trade",
                            "stop_losses": "Always use stop losses",
                            "profit_targets": "Set realistic profit targets",
                            "max_trades": "Limit number of trades per day",
                            "loss_limit": "Stop trading after 3-4 consecutive losses"
                        }
                    }
                ],
                "key_takeaways": [
                    "Intraday trading requires discipline and quick decisions",
                    "Focus on liquid stocks with adequate volatility",
                    "Use momentum strategies for trend following",
                    "Scalping requires precision and quick execution",
                    "Risk management is more important than profit potential"
                ],
                "real_world_example": {
                    "scenario": "Reliance Intraday Breakout",
                    "description": "On earnings day, Reliance broke above ₹2,500 resistance with 3x average volume. Intraday traders entered at ₹2,510, set stop at ₹2,480, and exited at ₹2,580 for 2.8% profit.",
                    "lesson": "Earnings announcements often provide excellent intraday trading opportunities with clear entry and exit levels."
                }
            },
            "quiz": {
                "questions": [
                    {
                        "question": "What is the maximum risk per trade for intraday trading?",
                        "options": ["5%", "3%", "2%", "1%"],
                        "correct_answer": 2,
                        "explanation": "Risk should be limited to 1-2% per trade to preserve capital."
                    },
                    {
                        "question": "What is scalping?",
                        "options": ["Long-term trading", "Quick trades for small profits", "High-risk trading", "Fundamental analysis"],
                        "correct_answer": 1,
                        "explanation": "Scalping involves quick trades to capture small profits frequently."
                    }
                ]
            }
        }
    }
