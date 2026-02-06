"""
Market Structure & Regulation Education Module
Covers: Regulators, Clearing & Settlement, Market Intermediaries
Logical grouping of related market infrastructure topics
"""
from typing import Dict, List, Any
from datetime import datetime

class MarketStructureEducationService:
    """Comprehensive market structure and regulation education"""
    
    def __init__(self):
        self.lessons = self._initialize_lessons()
    
    def _initialize_lessons(self) -> Dict[str, Any]:
        """Initialize all market structure lessons"""
        return {
            # ========== REGULATORS MODULE ==========
            "regulators_1": {
                "id": "regulators_1",
                "title": "Introduction to Market Regulators",
                "module": "Market Regulation",
                "level": "beginner",
                "duration": "30 minutes",
                "overview": "Understanding who regulates Indian stock markets and why regulation is essential",
                "learning_objectives": [
                    "Identify key regulatory bodies in India",
                    "Understand the role of SEBI",
                    "Recognize the importance of market regulation",
                    "Learn about investor protection mechanisms"
                ],
                "content": {
                    "introduction": {
                        "text": "Stock markets are complex ecosystems with millions of participants. To ensure fairness, transparency, and investor protection, robust regulation is essential. In India, multiple regulatory bodies work together to maintain market integrity.",
                        "key_concept": "Regulation ensures fair play, protects investors, and maintains market confidence."
                    },
                    "main_content": [
                        {
                            "section": "Why Regulate Markets?",
                            "content": "Market regulation serves multiple critical purposes:",
                            "points": [
                                {
                                    "title": "Investor Protection",
                                    "description": "Prevents fraud, manipulation, and ensures fair treatment of all investors",
                                    "example": "SEBI's insider trading regulations protect small investors from unfair practices"
                                },
                                {
                                    "title": "Market Integrity",
                                    "description": "Ensures transparent price discovery and prevents market manipulation",
                                    "example": "Circuit breakers prevent extreme volatility and protect market stability"
                                },
                                {
                                    "title": "Systemic Stability",
                                    "description": "Prevents market failures that could impact the entire economy",
                                    "example": "Capital adequacy requirements for brokers prevent systemic risks"
                                },
                                {
                                    "title": "Fair Competition",
                                    "description": "Ensures all participants operate on a level playing field",
                                    "example": "Disclosure requirements ensure all investors have equal access to information"
                                }
                            ]
                        },
                        {
                            "section": "Key Regulatory Bodies in India",
                            "content": "India has a multi-layered regulatory framework:",
                            "regulators": [
                                {
                                    "name": "SEBI (Securities and Exchange Board of India)",
                                    "role": "Primary regulator for securities market",
                                    "functions": [
                                        "Regulates stock exchanges (NSE, BSE)",
                                        "Regulates brokers, mutual funds, and other intermediaries",
                                        "Protects investor interests",
                                        "Prevents insider trading and market manipulation",
                                        "Regulates IPOs and public issues",
                                        "Oversees corporate governance"
                                    ],
                                    "established": "1992",
                                    "headquarters": "Mumbai",
                                    "website": "www.sebi.gov.in"
                                },
                                {
                                    "name": "RBI (Reserve Bank of India)",
                                    "role": "Central bank and monetary authority",
                                    "functions": [
                                        "Regulates money market and foreign exchange",
                                        "Manages monetary policy",
                                        "Regulates banking sector",
                                        "Manages foreign exchange reserves",
                                        "Oversees payment systems"
                                    ],
                                    "established": "1935",
                                    "headquarters": "Mumbai"
                                },
                                {
                                    "name": "IRDAI (Insurance Regulatory and Development Authority)",
                                    "role": "Regulates insurance sector",
                                    "functions": [
                                        "Regulates insurance companies",
                                        "Protects policyholder interests",
                                        "Promotes insurance sector growth"
                                    ]
                                },
                                {
                                    "name": "PFRDA (Pension Fund Regulatory and Development Authority)",
                                    "role": "Regulates pension funds",
                                    "functions": [
                                        "Regulates NPS (National Pension System)",
                                        "Oversees pension fund managers"
                                    ]
                                }
                            ]
                        },
                        {
                            "section": "SEBI: The Primary Market Regulator",
                            "content": "SEBI is the most important regulator for stock market participants:",
                            "sebi_powers": [
                                {
                                    "power": "Regulatory Powers",
                                    "description": "Can issue regulations, guidelines, and circulars",
                                    "example": "SEBI LODR (Listing Obligations and Disclosure Requirements) regulations"
                                },
                                {
                                    "power": "Investigative Powers",
                                    "description": "Can investigate violations and impose penalties",
                                    "example": "SEBI can ban entities from markets, impose fines up to ₹25 crores"
                                },
                                {
                                    "power": "Adjudicatory Powers",
                                    "description": "Can pass orders and judgments",
                                    "example": "SEBI can order disgorgement of illegal gains"
                                },
                                {
                                    "power": "Rule-Making Powers",
                                    "description": "Can create rules for market participants",
                                    "example": "SEBI regulations on algo trading, margin requirements"
                                }
                            ],
                            "sebi_initiatives": [
                                "Investor Education Programs",
                                "SCORES (SEBI Complaints Redress System)",
                                "KYC (Know Your Customer) requirements",
                                "Investor Protection Fund",
                                "Market surveillance systems"
                            ]
                        },
                        {
                            "section": "Market Participants",
                            "content": "Understanding who participates in markets:",
                            "participants": [
                                {
                                    "type": "Retail Investors",
                                    "description": "Individual investors trading for personal wealth creation",
                                    "characteristics": ["Small ticket sizes", "Long-term focus", "Need protection"]
                                },
                                {
                                    "type": "Institutional Investors",
                                    "description": "Large organizations investing on behalf of others",
                                    "subtypes": [
                                        {"name": "FII (Foreign Institutional Investors)", "example": "Foreign mutual funds, pension funds"},
                                        {"name": "DII (Domestic Institutional Investors)", "example": "Indian mutual funds, insurance companies"},
                                        {"name": "Banks", "example": "SBI, HDFC Bank"},
                                        {"name": "Insurance Companies", "example": "LIC, HDFC Life"}
                                    ]
                                },
                                {
                                    "type": "Market Intermediaries",
                                    "description": "Entities that facilitate trading",
                                    "subtypes": [
                                        {"name": "Stock Brokers", "example": "Zerodha, ICICI Direct"},
                                        {"name": "Depository Participants", "example": "CDSL, NSDL"},
                                        {"name": "Clearing Members", "example": "Clearing corporations"},
                                        {"name": "Registrars", "example": "KFintech, Link Intime"}
                                    ]
                                }
                            ]
                        }
                    ],
                    "key_takeaways": [
                        "SEBI is the primary regulator for Indian stock markets",
                        "Regulation protects investors and ensures market integrity",
                        "Multiple regulatory bodies oversee different aspects of financial markets",
                        "Understanding regulations helps investors make informed decisions",
                        "SEBI has comprehensive powers to investigate and penalize violations"
                    ],
                    "real_world_example": {
                        "scenario": "SEBI's Action Against Insider Trading",
                        "description": "In 2020, SEBI imposed a penalty of ₹25 crores on a company executive for insider trading. This demonstrates SEBI's commitment to protecting small investors and maintaining market integrity.",
                        "lesson": "Regulation ensures that all investors, regardless of size, have equal access to information and fair trading opportunities."
                    }
                },
                "quiz": {
                    "questions": [
                        {
                            "question": "Which is the primary regulator for Indian stock markets?",
                            "options": ["RBI", "SEBI", "IRDAI", "PFRDA"],
                            "correct_answer": 1,
                            "explanation": "SEBI (Securities and Exchange Board of India) is the primary regulator for securities markets in India."
                        },
                        {
                            "question": "When was SEBI established?",
                            "options": ["1980", "1992", "2000", "2010"],
                            "correct_answer": 1,
                            "explanation": "SEBI was established in 1992 as an independent regulatory body."
                        },
                        {
                            "question": "What is the maximum penalty SEBI can impose?",
                            "options": ["₹5 crores", "₹10 crores", "₹25 crores", "₹50 crores"],
                            "correct_answer": 2,
                            "explanation": "SEBI can impose penalties up to ₹25 crores for violations."
                        }
                    ]
                }
            },
            
            "regulators_2": {
                "id": "regulators_2",
                "title": "Market Intermediaries Explained",
                "module": "Market Regulation",
                "level": "beginner",
                "duration": "25 minutes",
                "overview": "Understanding brokers, depositories, and other market intermediaries",
                "content": {
                    "introduction": {
                        "text": "Market intermediaries are essential service providers that make stock trading possible. Understanding their roles helps you navigate the market effectively."
                    },
                    "main_content": [
                        {
                            "section": "Stock Brokers",
                            "content": "Brokers are your gateway to stock markets:",
                            "broker_functions": [
                                "Execute buy/sell orders on exchanges",
                                "Provide trading platforms and tools",
                                "Handle account opening and KYC",
                                "Provide research and advisory services",
                                "Manage margin and collateral",
                                "Settle trades and handle pay-in/pay-out"
                            ],
                            "broker_types": [
                                {"type": "Full-Service Brokers", "example": "ICICI Direct, HDFC Securities", "features": ["Research", "Advisory", "Higher brokerage"]},
                                {"type": "Discount Brokers", "example": "Zerodha, etc.", "features": ["Low brokerage", "Self-service", "Technology-focused"]}
                            ]
                        },
                        {
                            "section": "Depositories (NSDL & CDSL)",
                            "content": "Depositories hold your shares in electronic form:",
                            "depository_functions": [
                                "Dematerialization (convert physical shares to electronic)",
                                "Safekeeping of securities",
                                "Transfer of securities",
                                "Corporate action processing",
                                "Pledge and hypothecation services"
                            ],
                            "depositories": [
                                {"name": "NSDL", "full_form": "National Securities Depository Limited", "established": "1996"},
                                {"name": "CDSL", "full_form": "Central Depository Services Limited", "established": "1999"}
                            ]
                        },
                        {
                            "section": "Clearing Corporations",
                            "content": "Ensure trade settlement happens smoothly:",
                            "functions": [
                                "Act as central counterparty",
                                "Guarantee trade settlement",
                                "Manage risk through margins",
                                "Handle pay-in and pay-out",
                                "Maintain settlement guarantee fund"
                            ]
                        }
                    ]
                }
            },
            
            # ========== CLEARING & SETTLEMENT MODULE ==========
            "clearing_settlement_1": {
                "id": "clearing_settlement_1",
                "title": "Understanding Clearing and Settlement",
                "module": "Clearing & Settlement",
                "level": "beginner",
                "duration": "35 minutes",
                "overview": "Learn how trades are settled, T+1 settlement cycle, and behind-the-scenes operations",
                "learning_objectives": [
                    "Understand the settlement cycle (T+1)",
                    "Learn about clearing process",
                    "Understand pay-in and pay-out",
                    "Recognize importance of settlement"
                ],
                "content": {
                    "introduction": {
                        "text": "When you buy or sell a stock, the transaction doesn't complete immediately. There's a process called 'settlement' that ensures money and shares are exchanged correctly. Understanding this process is crucial for every trader.",
                        "key_concept": "Settlement is the process of transferring securities and money between buyers and sellers after a trade is executed."
                    },
                    "main_content": [
                        {
                            "section": "What is Settlement?",
                            "content": "Settlement is the final step in a trade:",
                            "definition": "The process of transferring securities from seller to buyer and money from buyer to seller",
                            "timeline": {
                                "T Day": "Trade execution day",
                                "T+1 Day": "Settlement day (in India)",
                                "T+2 Day": "Previously used, now upgraded to T+1"
                            }
                        },
                        {
                            "section": "T+1 Settlement Cycle",
                            "content": "India moved to T+1 settlement in 2023:",
                            "t1_details": {
                                "what_it_means": "Trades executed on Day T are settled on Day T+1 (next trading day)",
                                "example": "If you buy a stock on Monday, settlement happens on Tuesday",
                                "benefits": [
                                    "Faster fund availability",
                                    "Reduced counterparty risk",
                                    "Lower margin requirements",
                                    "Better capital efficiency"
                                ],
                                "process": [
                                    "Day T (Trade Day): Order executed, trade confirmed",
                                    "Day T+1 Morning: Pay-in (shares from seller, money from buyer)",
                                    "Day T+1 Afternoon: Pay-out (shares to buyer, money to seller)",
                                    "Day T+1 Evening: Shares and money credited to accounts"
                                ]
                            }
                        },
                        {
                            "section": "Clearing Process",
                            "content": "Clearing happens before settlement:",
                            "clearing_steps": [
                                {
                                    "step": "Trade Matching",
                                    "description": "Exchange matches buy and sell orders",
                                    "details": "Ensures price, quantity, and other terms match"
                                },
                                {
                                    "step": "Trade Confirmation",
                                    "description": "Both parties receive trade confirmation",
                                    "details": "Contract note is generated"
                                },
                                {
                                    "step": "Clearing",
                                    "description": "Clearing corporation becomes counterparty",
                                    "details": "Reduces risk for both parties"
                                },
                                {
                                    "step": "Settlement",
                                    "description": "Actual transfer of securities and funds",
                                    "details": "Happens on T+1 day"
                                }
                            ]
                        },
                        {
                            "section": "Pay-in and Pay-out",
                            "content": "Understanding the settlement flow:",
                            "pay_in": {
                                "definition": "Delivery of securities/money to clearing corporation",
                                "timing": "Morning of T+1 day (before 10:30 AM)",
                                "from_seller": "Shares in demat account",
                                "from_buyer": "Money in trading account"
                            },
                            "pay_out": {
                                "definition": "Delivery of securities/money from clearing corporation",
                                "timing": "Afternoon of T+1 day (after 2:00 PM)",
                                "to_buyer": "Shares credited to demat account",
                                "to_seller": "Money credited to trading account"
                            }
                        },
                        {
                            "section": "Margin Requirements",
                            "content": "Margins ensure settlement:",
                            "margin_types": [
                                {
                                    "type": "SPAN Margin",
                                    "description": "Standard Portfolio Analysis of Risk",
                                    "purpose": "Covers potential losses"
                                },
                                {
                                    "type": "Exposure Margin",
                                    "description": "Additional margin for open positions",
                                    "purpose": "Covers extreme market movements"
                                },
                                {
                                    "type": "VaR Margin",
                                    "description": "Value at Risk margin",
                                    "purpose": "Covers 99% confidence level losses"
                                }
                            ]
                        },
                        {
                            "section": "What Happens if Settlement Fails?",
                            "content": "Settlement failures have consequences:",
                            "failure_scenarios": [
                                {
                                    "scenario": "Buyer doesn't pay",
                                    "consequence": "Shares not delivered, penalty charged",
                                    "action": "Broker may square off position"
                                },
                                {
                                    "scenario": "Seller doesn't deliver shares",
                                    "consequence": "Auction process, penalty charged",
                                    "action": "Buyer gets shares from auction"
                                }
                            ],
                            "penalties": [
                                "Penalty charges (0.05% per day)",
                                "Trading restrictions",
                                "Bad delivery charges",
                                "Impact on credit rating"
                            ]
                        }
                    ],
                    "key_takeaways": [
                        "T+1 settlement means trades settle the next trading day",
                        "Clearing happens before settlement to reduce risk",
                        "Pay-in happens in morning, pay-out in afternoon of T+1",
                        "Margins ensure settlement happens smoothly",
                        "Settlement failures result in penalties and restrictions"
                    ],
                    "real_world_example": {
                        "scenario": "Monday Trade Settlement",
                        "description": "You buy 100 shares of RELIANCE on Monday at ₹2,500. On Tuesday morning, ₹2,50,000 is debited from your account (pay-in). On Tuesday afternoon, 100 shares are credited to your demat account (pay-out).",
                        "lesson": "Understanding settlement helps you plan your trades and manage cash flow effectively."
                    }
                },
                "quiz": {
                    "questions": [
                        {
                            "question": "What does T+1 settlement mean?",
                            "options": [
                                "Trade settles same day",
                                "Trade settles next trading day",
                                "Trade settles after 1 week",
                                "Trade settles after 1 month"
                            ],
                            "correct_answer": 1,
                            "explanation": "T+1 means trade executed on Day T settles on Day T+1 (next trading day)."
                        },
                        {
                            "question": "When does pay-in happen?",
                            "options": [
                                "Same day as trade",
                                "Morning of T+1 day",
                                "Evening of T+1 day",
                                "T+2 day"
                            ],
                            "correct_answer": 1,
                            "explanation": "Pay-in happens in the morning of T+1 day (before 10:30 AM)."
                        }
                    ]
                }
            }
        }
    
    def get_lesson(self, lesson_id: str) -> Dict[str, Any]:
        """Get a specific lesson"""
        return self.lessons.get(lesson_id, {})
    
    def get_module_lessons(self, module: str) -> List[Dict[str, Any]]:
        """Get all lessons in a module"""
        return [lesson for lesson in self.lessons.values() if lesson.get("module") == module]
    
    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Get all lessons"""
        return list(self.lessons.values())

