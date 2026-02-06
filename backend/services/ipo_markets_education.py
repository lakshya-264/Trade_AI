"""
IPO Markets Education Module
Comprehensive coverage of IPO process, funding stages, and investment strategies
"""
from typing import Dict, List, Any
from datetime import datetime

class IPOMarketsEducationService:
    """Comprehensive IPO markets education"""
    
    def __init__(self):
        self.lessons = self._initialize_lessons()
        self.tools = self._initialize_tools()
    
    def _initialize_lessons(self) -> Dict[str, Any]:
        """Initialize IPO education lessons"""
        return {
            "ipo_fundamentals_1": {
                "id": "ipo_fundamentals_1",
                "title": "Business Funding Journey: From Startup to IPO",
                "module": "IPO Markets",
                "level": "beginner",
                "duration": "40 minutes",
                "overview": "Understand how businesses raise capital at different stages and the path to going public",
                "learning_objectives": [
                    "Understand different funding stages",
                    "Learn about venture capital and private equity",
                    "Recognize when companies are ready for IPO",
                    "Understand the IPO process timeline"
                ],
                "content": {
                    "introduction": {
                        "text": "Every successful company starts with an idea and needs money to grow. Understanding how businesses raise capital helps you understand IPOs better.",
                        "key_concept": "Companies go through multiple funding stages before they're ready to go public through an IPO."
                    },
                    "main_content": [
                        {
                            "section": "Funding Stages of a Business",
                            "content": "Companies raise money at different stages:",
                            "stages": [
                                {
                                    "stage": "Seed Stage",
                                    "description": "Initial funding to start the business",
                                    "amount": "₹10 lakhs - ₹1 crore",
                                    "investors": "Founders, friends, family, angel investors",
                                    "purpose": "Product development, market research",
                                    "example": "A tech startup developing an app"
                                },
                                {
                                    "stage": "Series A",
                                    "description": "First significant round of venture capital",
                                    "amount": "₹1-10 crores",
                                    "investors": "Venture Capital firms",
                                    "purpose": "Scaling operations, hiring team",
                                    "example": "Zomato's early funding rounds"
                                },
                                {
                                    "stage": "Series B, C, D...",
                                    "description": "Subsequent funding rounds for growth",
                                    "amount": "₹10-100 crores per round",
                                    "investors": "VCs, Private Equity firms",
                                    "purpose": "Market expansion, acquisitions",
                                    "example": "Ola, Swiggy growth rounds"
                                },
                                {
                                    "stage": "Pre-IPO",
                                    "description": "Final funding before going public",
                                    "amount": "₹100-1000 crores",
                                    "investors": "Private Equity, Strategic investors",
                                    "purpose": "Prepare for IPO, strengthen balance sheet",
                                    "example": "Paytm before IPO"
                                },
                                {
                                    "stage": "IPO",
                                    "description": "Going public, raising money from public",
                                    "amount": "₹500-10,000+ crores",
                                    "investors": "Retail and institutional investors",
                                    "purpose": "Public listing, liquidity for early investors",
                                    "example": "LIC IPO (₹21,000 crores)"
                                }
                            ]
                        },
                        {
                            "section": "Why Companies Go Public?",
                            "content": "Reasons companies choose IPO:",
                            "reasons": [
                                {
                                    "reason": "Raise Capital",
                                    "description": "Access to large amounts of capital from public markets",
                                    "benefit": "Fund expansion, reduce debt, invest in R&D"
                                },
                                {
                                    "reason": "Liquidity for Early Investors",
                                    "description": "Early investors (VCs, founders) can exit",
                                    "benefit": "Realize returns on their investment"
                                },
                                {
                                    "reason": "Brand Visibility",
                                    "description": "Public listing increases brand recognition",
                                    "benefit": "Better customer trust, employee attraction"
                                },
                                {
                                    "reason": "Valuation Discovery",
                                    "description": "Market determines company's true value",
                                    "benefit": "Fair valuation based on market forces"
                                },
                                {
                                    "reason": "Employee Stock Options",
                                    "description": "Employees can monetize their stock options",
                                    "benefit": "Better employee retention and motivation"
                                }
                            ]
                        },
                        {
                            "section": "IPO Eligibility Criteria",
                            "content": "SEBI has strict criteria for IPOs:",
                            "criteria": [
                                {
                                    "requirement": "Track Record",
                                    "details": "Minimum 3 years of profitable operations",
                                    "exception": "Tech companies can list without profits (with conditions)"
                                },
                                {
                                    "requirement": "Net Worth",
                                    "details": "Minimum net worth of ₹1 crore in each of last 3 years",
                                    "exception": "Startups have relaxed criteria"
                                },
                                {
                                    "requirement": "Public Shareholding",
                                    "details": "Minimum 25% public shareholding post-IPO",
                                    "exception": "Large companies can maintain 10% minimum"
                                },
                                {
                                    "requirement": "Promoter Holding",
                                    "details": "Promoters must hold minimum 20% post-IPO",
                                    "purpose": "Ensures promoter commitment"
                                }
                            ]
                        }
                    ],
                    "key_takeaways": [
                        "Companies go through multiple funding stages before IPO",
                        "IPO allows companies to raise large capital from public",
                        "SEBI has strict eligibility criteria for IPOs",
                        "Understanding funding stages helps evaluate IPO companies"
                    ]
                },
                "quiz": {
                    "questions": [
                        {
                            "question": "What is the first funding stage for a startup?",
                            "options": ["Series A", "Seed Stage", "Pre-IPO", "IPO"],
                            "correct_answer": 1,
                            "explanation": "Seed stage is the initial funding stage where founders raise money to start the business."
                        }
                    ]
                }
            },
            
            "ipo_process_1": {
                "id": "ipo_process_1",
                "title": "IPO Process: Step-by-Step Guide",
                "module": "IPO Markets",
                "level": "intermediate",
                "duration": "45 minutes",
                "overview": "Complete guide to IPO process from company perspective and investor perspective",
                "content": {
                    "introduction": {
                        "text": "The IPO process is complex and involves multiple steps. Understanding this process helps you make better IPO investment decisions."
                    },
                    "main_content": [
                        {
                            "section": "IPO Process Timeline",
                            "content": "Typical IPO takes 4-6 months:",
                            "timeline": [
                                {
                                    "phase": "Phase 1: Preparation (Month 1-2)",
                                    "steps": [
                                        "Appoint merchant bankers (lead managers)",
                                        "Appoint other intermediaries (registrars, bankers)",
                                        "Prepare DRHP (Draft Red Herring Prospectus)",
                                        "Due diligence and financial audit",
                                        "Valuation exercise"
                                    ]
                                },
                                {
                                    "phase": "Phase 2: SEBI Approval (Month 2-3)",
                                    "steps": [
                                        "File DRHP with SEBI",
                                        "SEBI reviews and provides observations",
                                        "Company addresses SEBI observations",
                                        "SEBI approval (usually 30-60 days)"
                                    ]
                                },
                                {
                                    "phase": "Phase 3: Marketing & Roadshow (Month 3-4)",
                                    "steps": [
                                        "Roadshow to institutional investors",
                                        "Price discovery through book building",
                                        "Finalize issue price",
                                        "File RHP (Red Herring Prospectus)"
                                    ]
                                },
                                {
                                    "phase": "Phase 4: Public Issue (Month 4)",
                                    "steps": [
                                        "Issue opens for subscription",
                                        "Investors apply (3-5 days)",
                                        "Allotment process",
                                        "Refund to unsuccessful applicants",
                                        "Listing on stock exchange"
                                    ]
                                }
                            ]
                        },
                        {
                            "section": "Key IPO Documents",
                            "content": "Important documents to understand:",
                            "documents": [
                                {
                                    "document": "DRHP (Draft Red Herring Prospectus)",
                                    "description": "Initial document filed with SEBI",
                                    "contains": [
                                        "Company business model",
                                        "Financial statements (3-5 years)",
                                        "Risk factors",
                                        "Use of IPO proceeds",
                                        "Management details"
                                    ],
                                    "importance": "First detailed information about company"
                                },
                                {
                                    "document": "RHP (Red Herring Prospectus)",
                                    "description": "Final prospectus with issue price",
                                    "contains": [
                                        "All DRHP information",
                                        "Issue price band",
                                        "Issue size",
                                        "Subscription dates"
                                    ],
                                    "importance": "Complete information for investors"
                                },
                                {
                                    "document": "Price Band",
                                    "description": "Range of issue price",
                                    "example": "₹900-950 per share",
                                    "importance": "Investors bid within this range"
                                }
                            ]
                        },
                        {
                            "section": "How to Apply for IPO?",
                            "content": "Step-by-step guide for investors:",
                            "steps": [
                                {
                                    "step": "1. Open Demat Account",
                                    "description": "Mandatory for IPO application",
                                    "details": "Demat account with any broker/DP"
                                },
                                {
                                    "step": "2. Check IPO Details",
                                    "description": "Read RHP, understand business",
                                    "details": "Check price band, issue size, dates"
                                },
                                {
                                    "step": "3. Apply Through ASBA",
                                    "description": "ASBA (Applications Supported by Blocked Amount)",
                                    "details": [
                                        "Money blocked in bank account (not debited)",
                                        "Apply through bank or broker",
                                        "Specify number of shares and bid price"
                                    ]
                                },
                                {
                                    "step": "4. Wait for Allotment",
                                    "description": "Allotment happens after issue closes",
                                    "details": [
                                        "Retail investors: Minimum 1 lot guaranteed",
                                        "Allotment based on demand",
                                        "Refund if not allotted"
                                    ]
                                },
                                {
                                    "step": "5. Receive Shares",
                                    "description": "Shares credited to demat account",
                                    "details": "Usually 1 week after issue closes"
                                },
                                {
                                    "step": "6. Listing Day",
                                    "description": "Shares start trading on exchange",
                                    "details": "Can sell immediately or hold"
                                }
                            ]
                        }
                    ]
                }
            },
            
            "ipo_jargons": {
                "id": "ipo_jargons",
                "title": "IPO Jargons Explained",
                "module": "IPO Markets",
                "level": "beginner",
                "duration": "30 minutes",
                "content": {
                    "jargons": [
                        {
                            "term": "Grey Market Premium (GMP)",
                            "definition": "Unofficial premium at which IPO shares trade before listing",
                            "example": "If GMP is ₹50 and issue price is ₹900, expected listing price is ₹950",
                            "note": "Grey market is unofficial, not regulated"
                        },
                        {
                            "term": "Cut-off Price",
                            "definition": "Highest price in price band",
                            "example": "If price band is ₹900-950, cut-off is ₹950",
                            "note": "Applying at cut-off maximizes allotment chances"
                        },
                        {
                            "term": "Lot Size",
                            "definition": "Minimum number of shares you can apply for",
                            "example": "If lot size is 15 shares, you can apply for 15, 30, 45...",
                            "note": "Retail investors can apply for maximum 13 lots"
                        },
                        {
                            "term": "Book Building",
                            "definition": "Process of price discovery through investor bids",
                            "example": "Investors bid at different prices, final price determined by demand",
                            "note": "Most IPOs use book building method"
                        },
                        {
                            "term": "Oversubscription",
                            "definition": "When demand exceeds issue size",
                            "example": "If issue is ₹1000 crores and applications are ₹5000 crores, it's 5x oversubscribed",
                            "note": "Higher oversubscription may mean lower allotment"
                        },
                        {
                            "term": "Anchor Investors",
                            "definition": "Institutional investors who invest before public issue",
                            "example": "Mutual funds, insurance companies invest 30-60% before IPO opens",
                            "note": "Anchor investment shows institutional confidence"
                        },
                        {
                            "term": "Lock-in Period",
                            "definition": "Period during which promoters cannot sell shares",
                            "example": "Promoters typically have 3-year lock-in",
                            "note": "Prevents immediate exit by promoters"
                        }
                    ]
                }
            }
        }
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize IPO-related tools"""
        return {
            "ipo_calculator": {
                "id": "ipo_calculator",
                "name": "IPO Investment Calculator",
                "description": "Calculate potential returns from IPO investment",
                "inputs": {
                    "issue_price": {"type": "number", "label": "Issue Price (₹)", "required": True},
                    "lot_size": {"type": "number", "label": "Lot Size", "required": True},
                    "number_of_lots": {"type": "number", "label": "Number of Lots", "required": True},
                    "expected_listing_price": {"type": "number", "label": "Expected Listing Price (₹)", "required": True}
                },
                "calculate": lambda inputs: {
                    "total_investment": inputs["issue_price"] * inputs["lot_size"] * inputs["number_of_lots"],
                    "expected_value": inputs["expected_listing_price"] * inputs["lot_size"] * inputs["number_of_lots"],
                    "potential_profit": (inputs["expected_listing_price"] - inputs["issue_price"]) * inputs["lot_size"] * inputs["number_of_lots"],
                    "potential_return_percent": ((inputs["expected_listing_price"] - inputs["issue_price"]) / inputs["issue_price"]) * 100
                }
            }
        }
    
    def get_lesson(self, lesson_id: str) -> Dict[str, Any]:
        """Get a specific lesson"""
        return self.lessons.get(lesson_id, {})
    
    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Get all IPO lessons"""
        return list(self.lessons.values())

