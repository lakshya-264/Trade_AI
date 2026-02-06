"""
Consolidated Market Education Services
Contains: Dow Theory, Clearing & Settlement, Glossary, Level 3 Data, Trading Routine, Rights/OFS/FPO
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DowTheoryService:
    """Enhanced Dow Theory service with pattern detection"""
    
    def __init__(self):
        self.dow_theory_content = self._initialize_dow_theory()
    
    def _initialize_dow_theory(self) -> Dict[str, Any]:
        return {
            "principles": {
                "principle_1": {
                    "title": "The Averages Discount Everything",
                    "description": "Stock prices reflect all available information",
                    "implication": "Technical analysis focuses on price action, not news"
                },
                "principle_2": {
                    "title": "Three Types of Trends",
                    "description": "Primary (major), Secondary (corrections), Minor (daily fluctuations)",
                    "primary_trend": {
                        "duration": "1-3 years",
                        "direction": "Bull market (higher highs) or Bear market (lower lows)",
                        "importance": "Most important for long-term investors"
                    },
                    "secondary_trend": {
                        "duration": "3 weeks to 3 months",
                        "description": "Corrections within primary trend (20-33% retracement)",
                        "importance": "Trading opportunities"
                    },
                    "minor_trend": {
                        "duration": "Days to weeks",
                        "description": "Daily price fluctuations",
                        "importance": "Can be noise, less reliable"
                    }
                },
                "principle_3": {
                    "title": "Trend Phases",
                    "description": "Three phases in both bull and bear markets",
                    "bull_market_phases": [
                        "Accumulation: Smart money buys",
                        "Public Participation: Retail joins, strong uptrend",
                        "Distribution: Smart money sells, retail still buying"
                    ],
                    "bear_market_phases": [
                        "Distribution: Selling begins",
                        "Public Participation: Panic selling",
                        "Accumulation: Smart money buys at lows"
                    ]
                },
                "principle_4": {
                    "title": "Averages Must Confirm",
                    "description": "Industrial and Transportation averages must confirm each other",
                    "confirmation": "Both averages must make new highs/lows together",
                    "non_confirmation": "Warning sign of trend weakness"
                },
                "principle_5": {
                    "title": "Volume Confirms Trend",
                    "description": "Volume should increase in direction of trend",
                    "bull_market": "Volume increases on up days",
                    "bear_market": "Volume increases on down days"
                },
                "principle_6": {
                    "title": "Trend Remains Until Reversal",
                    "description": "Trend continues until clear reversal signals",
                    "reversal_signals": [
                        "Failure to make new high/low",
                        "Break of previous swing point",
                        "Volume confirmation of reversal"
                    ]
                }
            },
            "trading_ranges": {
                "title": "Trading Ranges and Flags",
                "description": "Price consolidation patterns within trends",
                "flag_pattern": {
                    "description": "Brief consolidation after strong move",
                    "characteristics": [
                        "Small rectangular pattern",
                        "Slopes against main trend",
                        "Volume decreases during flag",
                        "Breakout in direction of main trend"
                    ],
                    "trading_strategy": "Buy breakout from flag in uptrend, sell breakdown in downtrend"
                },
                "risk_reward": {
                    "title": "Risk-Reward Ratio",
                    "description": "Measure potential profit vs potential loss",
                    "calculation": "Reward / Risk",
                    "minimum_ratio": "Should be at least 2:1 (risk ₹1 to make ₹2)",
                    "example": {
                        "entry": 100,
                        "stop_loss": 95,
                        "target": 110,
                        "risk": 5,
                        "reward": 10,
                        "ratio": "2:1 (Good)"
                    }
                }
            }
        }
    
    def detect_dow_theory_signals(self, price_data: List[Dict]) -> Dict[str, Any]:
        """Detect Dow Theory signals from price data"""
        try:
            # Simplified Dow Theory analysis
            highs = [d.get('high', 0) for d in price_data]
            lows = [d.get('low', 0) for d in price_data]
            
            # Detect higher highs and higher lows (uptrend)
            higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
            higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
            
            # Detect lower highs and lower lows (downtrend)
            lower_highs = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i-1])
            lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
            
            if higher_highs > lower_highs and higher_lows > lower_lows:
                trend = "Uptrend (Bull Market)"
                signal = "BUY"
            elif lower_highs > higher_highs and lower_lows > higher_lows:
                trend = "Downtrend (Bear Market)"
                signal = "SELL"
            else:
                trend = "Sideways (Consolidation)"
                signal = "HOLD"
            
            return {
                "success": True,
                "trend": trend,
                "signal": signal,
                "higher_highs": higher_highs,
                "higher_lows": higher_lows,
                "lower_highs": lower_highs,
                "lower_lows": lower_lows
            }
        except Exception as e:
            logger.error(f"Error detecting Dow Theory signals: {e}")
            return {"success": False, "error": str(e)}


class ClearingSettlementService:
    """Clearing and Settlement Education Service"""
    
    def __init__(self):
        self.settlement_content = self._initialize_settlement_content()
    
    def _initialize_settlement_content(self) -> Dict[str, Any]:
        return {
            "what_is_settlement": {
                "title": "What is Clearing and Settlement?",
                "description": "Process of transferring securities and money between buyers and sellers",
                "clearing": {
                    "definition": "Process of determining obligations (who owes what to whom)",
                    "steps": [
                        "Trade matching",
                        "Obligation determination",
                        "Risk management",
                        "Settlement instruction"
                    ]
                },
                "settlement": {
                    "definition": "Actual transfer of securities and funds",
                    "steps": [
                        "Securities transfer (delivery)",
                        "Funds transfer (payment)",
                        "Confirmation"
                    ]
                }
            },
            "t_plus_settlement": {
                "title": "T+1 Settlement Cycle",
                "description": "India has T+1 settlement (fastest in the world)",
                "t_plus_meaning": {
                    "t": "Trade date (day of transaction)",
                    "t_plus_1": "Settlement date (1 day after trade)",
                    "example": "Buy on Monday (T) → Settlement on Tuesday (T+1)"
                },
                "timeline": {
                    "t_day": {
                        "time": "9:15 AM - 3:30 PM",
                        "activity": "Trading happens",
                        "end_of_day": "Trades are matched and confirmed"
                    },
                    "t_plus_1": {
                        "time": "By 11:30 AM",
                        "activity": "Securities and funds are transferred",
                        "pay_in": "Sellers must deliver shares",
                        "pay_out": "Buyers receive shares and pay money"
                    }
                },
                "benefits": [
                    "Faster settlement reduces risk",
                    "Lower margin requirements",
                    "Better capital efficiency",
                    "Reduced counterparty risk"
                ]
            },
            "pay_in_pay_out": {
                "title": "Pay-in and Pay-out",
                "pay_in": {
                    "definition": "Delivery of securities/funds to clearing corporation",
                    "for_sellers": "Must deliver shares by T+1",
                    "for_buyers": "Must pay money by T+1",
                    "deadline": "11:30 AM on T+1"
                },
                "pay_out": {
                    "definition": "Receipt of securities/funds from clearing corporation",
                    "for_buyers": "Receive shares by T+1",
                    "for_sellers": "Receive money by T+1",
                    "timing": "Usually by 2:00 PM on T+1"
                }
            },
            "margin_system": {
                "title": "Margin and Risk Management",
                "description": "System to protect against default risk",
                "types": {
                    "var_margin": {
                        "name": "Value at Risk (VaR) Margin",
                        "description": "Covers potential loss from price movement",
                        "calculation": "Based on volatility and position size"
                    },
                    "exposure_margin": {
                        "name": "Exposure Margin",
                        "description": "Additional margin for large positions",
                        "purpose": "Extra protection for high exposure"
                    },
                    "mark_to_market": {
                        "name": "Mark to Market (MTM)",
                        "description": "Daily profit/loss calculation",
                        "process": "Unrealized P&L is settled daily"
                    }
                }
            },
            "clearing_house": {
                "title": "Clearing Corporation",
                "description": "NSCCL (NSE) and ICCL (BSE) handle clearing and settlement",
                "functions": [
                    "Trade confirmation",
                    "Risk management",
                    "Settlement guarantee",
                    "Default management"
                ],
                "guarantee": "Clearing corporation guarantees settlement even if one party defaults"
            }
        }
    
    def calculate_settlement_date(self, trade_date: datetime, settlement_days: int = 1) -> Dict[str, Any]:
        """Calculate settlement date"""
        try:
            settlement_date = trade_date + timedelta(days=settlement_days)
            
            return {
                "success": True,
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "settlement_date": settlement_date.strftime("%Y-%m-%d"),
                "settlement_cycle": f"T+{settlement_days}",
                "days_to_settlement": settlement_days
            }
        except Exception as e:
            logger.error(f"Error calculating settlement date: {e}")
            return {"success": False, "error": str(e)}


class GlossaryService:
    """Comprehensive Stock Market Glossary"""
    
    def __init__(self):
        self.glossary = self._initialize_glossary()
    
    def _initialize_glossary(self) -> Dict[str, Any]:
        return {
            "A": {
                "ASBA": {
                    "term": "Application Supported by Blocked Amount",
                    "definition": "IPO application method where money is blocked until allotment",
                    "category": "IPO"
                },
                "ADR": {
                    "term": "American Depositary Receipt",
                    "definition": "US-listed security representing shares of foreign company",
                    "category": "International"
                }
            },
            "B": {
                "Bear Market": {
                    "term": "Bear Market",
                    "definition": "Market in decline, prices falling",
                    "category": "Market Terms"
                },
                "Bull Market": {
                    "term": "Bull Market",
                    "definition": "Market in rise, prices increasing",
                    "category": "Market Terms"
                },
                "Beta": {
                    "term": "Beta",
                    "definition": "Measure of stock's volatility relative to market",
                    "category": "Technical Analysis"
                },
                "Bid": {
                    "term": "Bid",
                    "definition": "Price at which buyers are willing to buy",
                    "category": "Trading"
                },
                "Broker": {
                    "term": "Broker",
                    "definition": "Intermediary who facilitates stock trading",
                    "category": "Market Participants"
                }
            },
            "C": {
                "Call Option": {
                    "term": "Call Option",
                    "definition": "Right to buy stock at strike price",
                    "category": "Options"
                },
                "Candlestick": {
                    "term": "Candlestick",
                    "definition": "Chart pattern showing OHLC data",
                    "category": "Technical Analysis"
                },
                "Circuit Breaker": {
                    "term": "Circuit Breaker",
                    "definition": "Trading halt when market moves beyond limits",
                    "category": "Market Terms"
                }
            },
            "D": {
                "Dividend": {
                    "term": "Dividend",
                    "definition": "Distribution of company profits to shareholders",
                    "category": "Corporate Actions"
                },
                "Demat Account": {
                    "term": "Demat Account",
                    "definition": "Electronic account for holding securities",
                    "category": "Trading"
                }
            },
            "E": {
                "EPS": {
                    "term": "Earnings Per Share",
                    "definition": "Profit divided by number of shares",
                    "category": "Fundamental Analysis"
                },
                "Ex-Dividend": {
                    "term": "Ex-Dividend",
                    "definition": "Date from which stock trades without dividend",
                    "category": "Corporate Actions"
                }
            },
            "F": {
                "FII": {
                    "term": "Foreign Institutional Investor",
                    "definition": "Foreign entity investing in Indian markets",
                    "category": "Market Participants"
                },
                "Futures": {
                    "term": "Futures",
                    "definition": "Contract to buy/sell at future date",
                    "category": "Derivatives"
                }
            },
            "G": {
                "Gap": {
                    "term": "Gap",
                    "definition": "Price jump with no trading in between",
                    "category": "Technical Analysis"
                },
                "Grey Market": {
                    "term": "Grey Market",
                    "definition": "Unofficial trading before IPO listing",
                    "category": "IPO"
                }
            },
            "H": {
                "Hedge": {
                    "term": "Hedge",
                    "definition": "Strategy to reduce risk",
                    "category": "Risk Management"
                },
                "Holding Period": {
                    "term": "Holding Period",
                    "definition": "Time for which investment is held",
                    "category": "Trading"
                }
            },
            "I": {
                "IPO": {
                    "term": "Initial Public Offering",
                    "definition": "First time company offers shares to public",
                    "category": "IPO"
                },
                "Index": {
                    "term": "Index",
                    "definition": "Benchmark representing market performance",
                    "category": "Market Terms"
                }
            },
            "L": {
                "Limit Order": {
                    "term": "Limit Order",
                    "definition": "Order to buy/sell at specific price",
                    "category": "Trading"
                },
                "Liquidity": {
                    "term": "Liquidity",
                    "definition": "Ease of buying/selling without price impact",
                    "category": "Market Terms"
                }
            },
            "M": {
                "Market Order": {
                    "term": "Market Order",
                    "definition": "Order executed at current market price",
                    "category": "Trading"
                },
                "Margin": {
                    "term": "Margin",
                    "definition": "Borrowed money to buy securities",
                    "category": "Trading"
                }
            },
            "O": {
                "Options": {
                    "term": "Options",
                    "definition": "Right to buy/sell at strike price",
                    "category": "Derivatives"
                },
                "Oversubscription": {
                    "term": "Oversubscription",
                    "definition": "IPO demand exceeds supply",
                    "category": "IPO"
                }
            },
            "P": {
                "PE Ratio": {
                    "term": "Price-to-Earnings Ratio",
                    "definition": "Stock price divided by earnings per share",
                    "category": "Fundamental Analysis"
                },
                "Portfolio": {
                    "term": "Portfolio",
                    "definition": "Collection of investments",
                    "category": "Investment"
                }
            },
            "R": {
                "RSI": {
                    "term": "Relative Strength Index",
                    "definition": "Momentum oscillator (0-100)",
                    "category": "Technical Analysis"
                },
                "Resistance": {
                    "term": "Resistance",
                    "definition": "Price level where selling pressure increases",
                    "category": "Technical Analysis"
                }
            },
            "S": {
                "Support": {
                    "term": "Support",
                    "definition": "Price level where buying interest increases",
                    "category": "Technical Analysis"
                },
                "Stop Loss": {
                    "term": "Stop Loss",
                    "definition": "Order to limit losses",
                    "category": "Risk Management"
                }
            },
            "T": {
                "T+1": {
                    "term": "T+1 Settlement",
                    "definition": "Settlement one day after trade",
                    "category": "Settlement"
                },
                "Technical Analysis": {
                    "term": "Technical Analysis",
                    "definition": "Analysis based on price and volume patterns",
                    "category": "Analysis"
                }
            },
            "V": {
                "Volume": {
                    "term": "Volume",
                    "definition": "Number of shares traded",
                    "category": "Trading"
                },
                "Volatility": {
                    "term": "Volatility",
                    "definition": "Measure of price fluctuations",
                    "category": "Risk Management"
                }
            }
        }
    
    def search_glossary(self, search_term: str) -> Dict[str, Any]:
        """Search glossary by term"""
        results = []
        search_lower = search_term.lower()
        
        for category, terms in self.glossary.items():
            for term_key, term_data in terms.items():
                if search_lower in term_key.lower() or search_lower in term_data.get("definition", "").lower():
                    results.append({
                        "term": term_data.get("term", term_key),
                        "definition": term_data.get("definition", ""),
                        "category": term_data.get("category", "General")
                    })
        
        return {
            "success": True,
            "search_term": search_term,
            "results": results,
            "count": len(results)
        }


class Level3DataService:
    """Level 3 Data (Order Book Depth) Education"""
    
    def __init__(self):
        self.level3_content = self._initialize_level3_content()
    
    def _initialize_level3_content(self) -> Dict[str, Any]:
        return {
            "what_is_level3": {
                "title": "What is Level 3 Data?",
                "description": "Detailed order book showing all buy and sell orders at different price levels",
                "also_known_as": "20 Market Depth, Order Book Depth",
                "levels": {
                    "level_1": "Best bid and ask prices",
                    "level_2": "Top 5 bid and ask prices with quantities",
                    "level_3": "Complete order book (all price levels)"
                }
            },
            "order_book_components": {
                "bid_side": {
                    "description": "Buy orders (demand side)",
                    "shows": "Price and quantity at each level",
                    "interpretation": "Higher bids indicate strong buying interest"
                },
                "ask_side": {
                    "description": "Sell orders (supply side)",
                    "shows": "Price and quantity at each level",
                    "interpretation": "Lower asks indicate strong selling pressure"
                },
                "spread": {
                    "description": "Difference between best bid and best ask",
                    "narrow_spread": "High liquidity, tight market",
                    "wide_spread": "Low liquidity, volatile market"
                }
            },
            "how_to_read": {
                "title": "How to Read Order Book",
                "interpretations": [
                    {
                        "scenario": "Large buy orders at multiple levels",
                        "meaning": "Strong support, bullish signal"
                    },
                    {
                        "scenario": "Large sell orders at multiple levels",
                        "meaning": "Strong resistance, bearish signal"
                    },
                    {
                        "scenario": "Thin order book (small quantities)",
                        "meaning": "Low liquidity, high volatility risk"
                    },
                    {
                        "scenario": "Thick order book (large quantities)",
                        "meaning": "High liquidity, stable prices"
                    }
                ]
            }
        }


class TradingRoutineService:
    """Trading Routine Guide Service"""
    
    def __init__(self):
        self.routines = self._initialize_routines()
    
    def _initialize_routines(self) -> Dict[str, Any]:
        return {
            "daily_routine": {
                "pre_market": {
                    "time": "8:00 AM - 9:15 AM",
                    "activities": [
                        "Review overnight global markets",
                        "Check economic calendar for events",
                        "Review watchlist stocks",
                        "Check for corporate announcements",
                        "Review previous day's trades",
                        "Set trading plan for the day"
                    ]
                },
                "market_hours": {
                    "time": "9:15 AM - 3:30 PM",
                    "activities": [
                        "Monitor open positions",
                        "Execute planned trades",
                        "Watch for breakout opportunities",
                        "Manage risk (stop losses)",
                        "Take notes on market behavior"
                    ]
                },
                "post_market": {
                    "time": "3:30 PM - 6:00 PM",
                    "activities": [
                        "Review day's trades",
                        "Analyze what worked and what didn't",
                        "Update trading journal",
                        "Review charts and patterns",
                        "Plan for next day"
                    ]
                }
            },
            "weekly_routine": {
                "sunday": [
                    "Review week's performance",
                    "Analyze trading statistics",
                    "Identify patterns in wins/losses",
                    "Plan for upcoming week"
                ],
                "monday": [
                    "Weekly market overview",
                    "Sector analysis",
                    "Set weekly goals"
                ]
            },
            "monthly_routine": [
                "Comprehensive performance review",
                "Risk assessment",
                "Strategy evaluation",
                "Adjust trading plan if needed"
            ]
        }


class RightsOFSService:
    """Rights, OFS, FPO Education Service"""
    
    def __init__(self):
        self.content = self._initialize_content()
    
    def _initialize_content(self) -> Dict[str, Any]:
        return {
            "rights_issue": {
                "title": "Rights Issue",
                "description": "Company offers new shares to existing shareholders",
                "key_points": [
                    "Proportional to existing holding",
                    "Discounted price",
                    "Optional (can subscribe, renounce, or let lapse)",
                    "Dilutes shareholding if not subscribed"
                ]
            },
            "ofs": {
                "title": "Offer for Sale (OFS)",
                "description": "Existing shareholders sell their shares to public",
                "key_points": [
                    "Not company raising money",
                    "Shareholders exiting",
                    "Can be part of IPO",
                    "No dilution (just ownership transfer)"
                ]
            },
            "fpo": {
                "title": "Follow-on Public Offer (FPO)",
                "description": "Company raises additional capital after IPO",
                "key_points": [
                    "Company raising more money",
                    "Can be fresh issue or OFS",
                    "Dilutes if fresh issue",
                    "Usually at discount to market price"
                ]
            },
            "comparison": {
                "table": {
                    "feature": ["Rights", "OFS", "FPO"],
                    "who_raises_money": ["Company", "Shareholders", "Company"],
                    "dilution": ["Yes (if fresh)", "No", "Yes (if fresh)"],
                    "discount": ["Usually", "Market price", "Usually"],
                    "eligibility": ["Existing shareholders", "Public", "Public"]
                }
            }
        }

