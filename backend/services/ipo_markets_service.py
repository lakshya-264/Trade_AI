"""
IPO Markets Education & Analysis Service
Comprehensive IPO education with practical analysis tools
Covers: IPO process, jargons, analysis, application process, post-IPO tracking
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class IPOMarketsService:
    """Service for IPO education and analysis"""
    
    def __init__(self):
        self.ipo_lessons = self._initialize_ipo_lessons()
        self.ipo_jargons = self._initialize_ipo_jargons()
        self.analysis_tools = self._initialize_analysis_tools()
    
    def _initialize_ipo_lessons(self) -> Dict[str, Any]:
        """Initialize comprehensive IPO lessons"""
        return {
            "ipo_fundamentals": {
                "title": "Understanding IPO Markets",
                "level": "beginner",
                "duration": "45 minutes",
                "sections": [
                    {
                        "title": "What is an IPO?",
                        "content": "An Initial Public Offering (IPO) is the process by which a private company becomes publicly traded by offering its shares to the public for the first time.",
                        "key_points": [
                            "IPO allows companies to raise capital from public investors",
                            "Company transitions from private to public ownership",
                            "Shares are listed on stock exchanges (NSE/BSE)",
                            "Investors can buy shares through IPO application"
                        ],
                        "real_example": {
                            "company": "Zomato IPO (2021)",
                            "details": "Raised ₹9,375 crores at ₹76 per share. Listed at ₹115, giving 51% listing gains to investors."
                        }
                    },
                    {
                        "title": "Why Companies Go Public",
                        "content": "Companies choose IPO for various strategic reasons:",
                        "reasons": {
                            "capital_raising": {
                                "title": "Raise Capital",
                                "description": "Fund business expansion, R&D, debt repayment, or acquisitions",
                                "example": "Paytm IPO raised ₹18,300 crores for expansion"
                            },
                            "liquidity": {
                                "title": "Provide Liquidity",
                                "description": "Early investors and founders can exit their positions",
                                "example": "Founders can sell partial stake while retaining control"
                            },
                            "brand_value": {
                                "title": "Brand Recognition",
                                "description": "Public listing increases company visibility and credibility",
                                "example": "Media coverage and investor attention"
                            },
                            "acquisition_currency": {
                                "title": "Acquisition Currency",
                                "description": "Publicly traded shares can be used for acquisitions",
                                "example": "Stock swaps for mergers and acquisitions"
                            }
                        }
                    },
                    {
                        "title": "Funding Stages Before IPO",
                        "content": "Companies go through multiple funding rounds before IPO:",
                        "stages": [
                            {
                                "stage": "Seed Funding",
                                "description": "Initial capital from founders, friends, family",
                                "amount": "₹10L - ₹1Cr",
                                "purpose": "Proof of concept, MVP development"
                            },
                            {
                                "stage": "Angel/Series A",
                                "description": "Early-stage investors, venture capitalists",
                                "amount": "₹1Cr - ₹50Cr",
                                "purpose": "Product development, market validation"
                            },
                            {
                                "stage": "Series B/C/D",
                                "description": "Growth capital from VCs and PE firms",
                                "amount": "₹50Cr - ₹500Cr",
                                "purpose": "Scaling operations, market expansion"
                            },
                            {
                                "stage": "Pre-IPO",
                                "description": "Final round before going public",
                                "amount": "₹500Cr+",
                                "purpose": "Valuation setting, IPO preparation"
                            },
                            {
                                "stage": "IPO",
                                "description": "Public offering to retail and institutional investors",
                                "amount": "Varies (₹100Cr - ₹20,000Cr+)",
                                "purpose": "Public listing, capital raising"
                            }
                        ]
                    }
                ]
            },
            "ipo_process": {
                "title": "IPO Process Step-by-Step",
                "level": "intermediate",
                "duration": "60 minutes",
                "sections": [
                    {
                        "title": "Pre-IPO Phase (6-12 months)",
                        "steps": [
                            {
                                "step": 1,
                                "title": "Appoint Investment Bankers",
                                "description": "Select merchant bankers (lead managers) for IPO",
                                "key_players": ["Merchant Bankers", "Legal Advisors", "Auditors"],
                                "duration": "1-2 months"
                            },
                            {
                                "step": 2,
                                "title": "Due Diligence",
                                "description": "Comprehensive review of company financials, operations, legal compliance",
                                "checks": ["Financial statements", "Legal compliance", "Regulatory approvals"],
                                "duration": "2-3 months"
                            },
                            {
                                "step": 3,
                                "title": "Draft Red Herring Prospectus (DRHP)",
                                "description": "Detailed document filed with SEBI containing company information",
                                "contents": [
                                    "Company background and business model",
                                    "Financial statements (3-5 years)",
                                    "Risk factors",
                                    "Use of IPO proceeds",
                                    "Management details",
                                    "IPO details (price band, size, dates)"
                                ],
                                "duration": "1-2 months"
                            },
                            {
                                "step": 4,
                                "title": "SEBI Approval",
                                "description": "SEBI reviews DRHP and provides observations",
                                "process": "SEBI may ask for clarifications, company responds, final approval",
                                "duration": "1-2 months"
                            }
                        ]
                    },
                    {
                        "title": "IPO Launch Phase",
                        "steps": [
                            {
                                "step": 5,
                                "title": "Price Band Announcement",
                                "description": "Company announces price range (e.g., ₹900-950 per share)",
                                "components": {
                                    "floor_price": "Minimum price investors can bid",
                                    "cap_price": "Maximum price investors can bid",
                                    "cut_off_price": "Price at which shares are finally issued"
                                }
                            },
                            {
                                "step": 6,
                                "title": "IPO Opening",
                                "description": "IPO opens for subscription (typically 3-5 days)",
                                "categories": {
                                    "qib": "Qualified Institutional Buyers (50% reserved)",
                                    "hni": "High Net Worth Individuals (15% reserved)",
                                    "retail": "Retail Investors (35% reserved)"
                                },
                                "application_methods": [
                                    "ASBA (Application Supported by Blocked Amount)",
                                    "Net Banking",
                                    "UPI",
                                    "Through broker"
                                ]
                            },
                            {
                                "step": 7,
                                "title": "IPO Closing & Allotment",
                                "description": "After IPO closes, shares are allotted based on demand",
                                "allotment_process": {
                                    "oversubscription": "If demand > supply, lottery system for retail",
                                    "full_allotment": "If demand < supply, all applicants get shares",
                                    "proportional": "For QIB and HNI, proportional allotment"
                                },
                                "duration": "5-7 days after IPO closes"
                            },
                            {
                                "step": 8,
                                "title": "Listing",
                                "description": "Shares are listed on stock exchanges (NSE/BSE)",
                                "listing_date": "Typically 6-7 days after IPO closes",
                                "listing_price": "Determined by market demand on listing day",
                                "listing_gain": "Difference between listing price and IPO price"
                            }
                        ]
                    }
                ]
            },
            "ipo_analysis": {
                "title": "How to Analyze an IPO",
                "level": "intermediate",
                "duration": "50 minutes",
                "sections": [
                    {
                        "title": "Financial Analysis",
                        "metrics": {
                            "revenue_growth": {
                                "description": "Year-over-year revenue growth rate",
                                "good_indicator": ">20% consistent growth",
                                "calculation": "(Current Revenue - Previous Revenue) / Previous Revenue * 100"
                            },
                            "profitability": {
                                "description": "Net profit margins and PAT growth",
                                "good_indicator": "Positive and growing profits",
                                "red_flags": "Consistent losses, declining margins"
                            },
                            "debt_levels": {
                                "description": "Debt-to-equity ratio, interest coverage",
                                "good_indicator": "Low debt, high interest coverage",
                                "calculation": "Debt-to-Equity = Total Debt / Shareholders' Equity"
                            },
                            "cash_flow": {
                                "description": "Operating cash flow, free cash flow",
                                "good_indicator": "Positive and growing cash flows",
                                "importance": "Shows company's ability to generate cash"
                            }
                        }
                    },
                    {
                        "title": "Valuation Analysis",
                        "metrics": {
                            "pe_ratio": {
                                "description": "Price-to-Earnings ratio (if profitable)",
                                "calculation": "Market Price / Earnings per Share",
                                "comparison": "Compare with industry peers",
                                "interpretation": "Lower PE may indicate undervaluation (but check why)"
                            },
                            "price_to_sales": {
                                "description": "Price-to-Sales ratio (for loss-making companies)",
                                "calculation": "Market Cap / Total Revenue",
                                "use_case": "Useful for growth companies without profits",
                                "benchmark": "Compare with similar companies"
                            },
                            "ev_ebitda": {
                                "description": "Enterprise Value to EBITDA",
                                "calculation": "EV / EBITDA",
                                "advantage": "Accounts for debt, useful for capital-intensive businesses"
                            },
                            "peg_ratio": {
                                "description": "Price/Earnings to Growth ratio",
                                "calculation": "PE Ratio / Earnings Growth Rate",
                                "interpretation": "PEG < 1 may indicate undervaluation"
                            }
                        }
                    },
                    {
                        "title": "Business Model Analysis",
                        "factors": [
                            {
                                "factor": "Market Size",
                                "questions": [
                                    "What is the total addressable market (TAM)?",
                                    "What is the serviceable market (SAM)?",
                                    "Is the market growing?"
                                ]
                            },
                            {
                                "factor": "Competitive Advantage",
                                "questions": [
                                    "What is the moat? (Brand, technology, network effects)",
                                    "How difficult is it for competitors to enter?",
                                    "What is the market share?"
                                ]
                            },
                            {
                                "factor": "Management Quality",
                                "questions": [
                                    "Track record of promoters?",
                                    "Management experience in the industry?",
                                    "Corporate governance practices?"
                                ]
                            },
                            {
                                "factor": "Use of Proceeds",
                                "questions": [
                                    "How will IPO money be used?",
                                    "Is it for growth or debt repayment?",
                                    "Is the plan realistic?"
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Red Flags to Watch",
                        "warnings": [
                            {
                                "flag": "Excessive Promoter Selling",
                                "description": "If promoters are selling too much, they may not believe in future growth",
                                "check": "Look at offer-for-sale (OFS) component in IPO"
                            },
                            {
                                "flag": "High Valuations",
                                "description": "IPO priced at very high PE ratios compared to peers",
                                "risk": "Limited upside potential, high downside risk"
                            },
                            {
                                "flag": "Weak Financials",
                                "description": "Consistent losses, declining revenue, high debt",
                                "risk": "May struggle post-listing"
                            },
                            {
                                "flag": "Regulatory Issues",
                                "description": "Pending legal cases, regulatory non-compliance",
                                "risk": "Can impact business operations"
                            },
                            {
                                "flag": "Oversubscription Hype",
                                "description": "Extremely high oversubscription may indicate FOMO, not fundamentals",
                                "caution": "Don't invest just because others are"
                            }
                        ]
                    }
                ]
            }
        }
    
    def _initialize_ipo_jargons(self) -> Dict[str, Any]:
        """Initialize IPO jargons dictionary"""
        return {
            "DRHP": {
                "term": "Draft Red Herring Prospectus",
                "definition": "Preliminary document filed with SEBI containing company details, financials, and IPO information",
                "importance": "Must read document before investing in IPO",
                "where_to_find": "SEBI website, company website, merchant banker website"
            },
            "RHP": {
                "term": "Red Herring Prospectus",
                "definition": "Final prospectus after SEBI approval, with IPO dates and price band",
                "difference_from_drhp": "RHP has final IPO details, DRHP is preliminary"
            },
            "Price Band": {
                "term": "Price Band",
                "definition": "Range of prices at which investors can bid (e.g., ₹900-950)",
                "components": {
                    "floor_price": "Minimum bid price",
                    "cap_price": "Maximum bid price"
                },
                "cut_off_price": "Final price at which shares are issued (within price band)"
            },
            "ASBA": {
                "term": "Application Supported by Blocked Amount",
                "definition": "IPO application method where money is blocked (not debited) until allotment",
                "benefits": [
                    "Money remains in your account until allotment",
                    "Interest earned on blocked amount",
                    "Automatic refund if not allotted"
                ],
                "how_to_apply": "Through net banking, UPI, or broker"
            },
            "Grey Market Premium": {
                "term": "Grey Market Premium (GMP)",
                "definition": "Unofficial premium at which IPO shares trade before listing",
                "interpretation": {
                    "positive_gmp": "Market expects listing above IPO price",
                    "negative_gmp": "Market expects listing below IPO price",
                    "caution": "GMP is unofficial and can change"
                }
            },
            "Oversubscription": {
                "term": "Oversubscription",
                "definition": "When IPO demand exceeds shares available",
                "types": {
                    "retail": "Retail category oversubscribed X times",
                    "qib": "QIB category oversubscribed X times",
                    "hni": "HNI category oversubscribed X times"
                },
                "impact": "Higher oversubscription = lower chance of full allotment (lottery system)"
            },
            "Lot Size": {
                "term": "Lot Size",
                "definition": "Minimum number of shares you must apply for",
                "example": "If lot size is 15 shares, you can apply for 15, 30, 45, etc. (multiples)",
                "calculation": "Lot Size = Minimum Application Amount / Price per Share"
            },
            "Allotment": {
                "term": "Allotment",
                "definition": "Process of distributing IPO shares to applicants",
                "methods": {
                    "lottery": "For retail oversubscribed IPOs (random selection)",
                    "proportional": "For QIB/HNI (proportional to application size)",
                    "full": "If not oversubscribed, all applicants get shares"
                }
            },
            "Listing Gain": {
                "term": "Listing Gain",
                "definition": "Profit made on listing day if listing price > IPO price",
                "calculation": "(Listing Price - IPO Price) / IPO Price * 100",
                "example": "IPO at ₹100, listed at ₹120 = 20% listing gain"
            },
            "OFS": {
                "term": "Offer for Sale",
                "definition": "When existing shareholders sell their shares in IPO (not company raising money)",
                "difference_from_fresh_issue": "OFS = shareholders exit, Fresh Issue = company raises money",
                "interpretation": "High OFS may indicate promoters/investors cashing out"
            },
            "Anchor Investors": {
                "term": "Anchor Investors",
                "definition": "Institutional investors who commit to buy shares before IPO opens",
                "benefits": {
                    "for_company": "Ensures subscription, sets benchmark price",
                    "for_investors": "Shows institutional confidence"
                },
                "lock_in": "Anchor investors have 30-day lock-in period"
            },
            "Basis of Allotment": {
                "term": "Basis of Allotment",
                "definition": "Final document showing how shares were allotted",
                "contains": [
                    "Number of applications received",
                    "Oversubscription ratio",
                    "Allotment method",
                    "Refund details"
                ]
            }
        }
    
    def _initialize_analysis_tools(self) -> Dict[str, Any]:
        """Initialize IPO analysis tools"""
        return {
            "ipo_valuation_calculator": {
                "name": "IPO Valuation Calculator",
                "description": "Calculate and compare IPO valuation metrics",
                "inputs": {
                    "ipo_price": "IPO price per share",
                    "total_shares": "Total shares outstanding post-IPO",
                    "revenue": "Annual revenue",
                    "net_profit": "Annual net profit",
                    "ebitda": "Annual EBITDA",
                    "debt": "Total debt",
                    "cash": "Cash and equivalents"
                },
                "outputs": {
                    "market_cap": "Market Capitalization",
                    "enterprise_value": "Enterprise Value",
                    "pe_ratio": "Price-to-Earnings Ratio",
                    "ps_ratio": "Price-to-Sales Ratio",
                    "ev_ebitda": "EV/EBITDA Ratio"
                }
            },
            "listing_gain_calculator": {
                "name": "Listing Gain Calculator",
                "description": "Calculate potential listing gains",
                "inputs": {
                    "ipo_price": "Price at which you got IPO shares",
                    "listing_price": "Expected or actual listing price",
                    "shares_allotted": "Number of shares allotted"
                },
                "outputs": {
                    "gain_per_share": "Profit per share",
                    "total_gain": "Total profit",
                    "gain_percentage": "Percentage gain"
                }
            },
            "ipo_application_calculator": {
                "name": "IPO Application Calculator",
                "description": "Calculate application amount and lot size",
                "inputs": {
                    "price_band": "Price range (floor to cap)",
                    "lot_size": "Minimum lot size",
                    "application_type": "Retail, HNI, or QIB"
                },
                "outputs": {
                    "min_application_amount": "Minimum amount to apply",
                    "max_application_amount": "Maximum amount allowed",
                    "shares_per_lot": "Number of shares in one lot"
                }
            }
        }
    
    def analyze_ipo(self, ipo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an IPO based on provided data
        
        Args:
            ipo_data: Dictionary containing IPO information
                - price_band: {"floor": 900, "cap": 950}
                - financials: {"revenue": 1000, "profit": 100, "debt": 500}
                - market_cap: 10000
                - etc.
        
        Returns:
            Comprehensive IPO analysis
        """
        try:
            analysis = {
                "valuation_analysis": self._analyze_valuation(ipo_data),
                "financial_health": self._analyze_financials(ipo_data),
                "risk_assessment": self._assess_risks(ipo_data),
                "investment_recommendation": self._generate_recommendation(ipo_data),
                "comparison_with_peers": self._compare_with_peers(ipo_data)
            }
            
            return {
                "success": True,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing IPO: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_valuation(self, data: Dict) -> Dict:
        """Analyze IPO valuation"""
        price = data.get("ipo_price", data.get("price_band", {}).get("cap", 0))
        shares = data.get("total_shares", 0)
        revenue = data.get("financials", {}).get("revenue", 0)
        profit = data.get("financials", {}).get("profit", 0)
        
        market_cap = price * shares if price and shares else 0
        pe_ratio = (price / (profit / shares)) if profit and shares else None
        ps_ratio = (market_cap / revenue) if revenue else None
        
        return {
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "ps_ratio": ps_ratio,
            "valuation_assessment": self._assess_valuation_level(pe_ratio, ps_ratio)
        }
    
    def _analyze_financials(self, data: Dict) -> Dict:
        """Analyze financial health"""
        financials = data.get("financials", {})
        revenue = financials.get("revenue", 0)
        profit = financials.get("profit", 0)
        debt = financials.get("debt", 0)
        equity = financials.get("equity", 0)
        
        profit_margin = (profit / revenue * 100) if revenue else 0
        debt_to_equity = (debt / equity) if equity else 0
        
        return {
            "profit_margin": profit_margin,
            "debt_to_equity": debt_to_equity,
            "financial_health_score": self._calculate_health_score(profit_margin, debt_to_equity)
        }
    
    def _assess_risks(self, data: Dict) -> Dict:
        """Assess IPO risks"""
        risks = []
        
        # Valuation risk
        if data.get("pe_ratio", 0) > 50:
            risks.append({
                "type": "High Valuation",
                "severity": "Medium",
                "description": "IPO priced at high PE ratio, limited upside potential"
            })
        
        # Financial risk
        financials = data.get("financials", {})
        if financials.get("profit", 0) < 0:
            risks.append({
                "type": "Loss Making",
                "severity": "High",
                "description": "Company is not profitable, high risk"
            })
        
        # Debt risk
        if financials.get("debt", 0) > financials.get("equity", 1):
            risks.append({
                "type": "High Debt",
                "severity": "Medium",
                "description": "High debt-to-equity ratio, financial stress risk"
            })
        
        return {
            "total_risks": len(risks),
            "risks": risks,
            "overall_risk_level": "High" if len(risks) >= 2 else "Medium" if len(risks) == 1 else "Low"
        }
    
    def _generate_recommendation(self, data: Dict) -> Dict:
        """Generate investment recommendation"""
        # Simple recommendation logic (can be enhanced)
        risks = self._assess_risks(data)
        financials = self._analyze_financials(data)
        
        if risks["overall_risk_level"] == "Low" and financials["financial_health_score"] > 70:
            recommendation = "STRONG BUY"
        elif risks["overall_risk_level"] == "Medium":
            recommendation = "MODERATE BUY"
        else:
            recommendation = "CAUTIOUS / AVOID"
        
        return {
            "recommendation": recommendation,
            "confidence": 0.75,
            "reasoning": "Based on financial health and risk assessment"
        }
    
    def _compare_with_peers(self, data: Dict) -> Dict:
        """Compare IPO with industry peers"""
        # Placeholder - would need peer data
        return {
            "peer_comparison": "Available with peer data",
            "industry_average_pe": None,
            "valuation_vs_peers": "Fair / Expensive / Cheap"
        }
    
    def _assess_valuation_level(self, pe_ratio: Optional[float], ps_ratio: Optional[float]) -> str:
        """Assess if valuation is fair, expensive, or cheap"""
        if pe_ratio:
            if pe_ratio < 15:
                return "Potentially Undervalued"
            elif pe_ratio > 30:
                return "Potentially Overvalued"
            else:
                return "Fairly Valued"
        return "Cannot Assess (No PE Ratio)"
    
    def _calculate_health_score(self, profit_margin: float, debt_to_equity: float) -> float:
        """Calculate financial health score (0-100)"""
        score = 50  # Base score
        
        # Profit margin contribution
        if profit_margin > 20:
            score += 30
        elif profit_margin > 10:
            score += 20
        elif profit_margin > 0:
            score += 10
        
        # Debt contribution
        if debt_to_equity < 0.5:
            score += 20
        elif debt_to_equity < 1.0:
            score += 10
        
        return min(100, max(0, score))
    
    def calculate_ipo_metrics(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate IPO valuation metrics"""
        try:
            ipo_price = inputs.get("ipo_price", 0)
            total_shares = inputs.get("total_shares", 0)
            revenue = inputs.get("revenue", 0)
            net_profit = inputs.get("net_profit", 0)
            ebitda = inputs.get("ebitda", 0)
            debt = inputs.get("debt", 0)
            cash = inputs.get("cash", 0)
            
            market_cap = ipo_price * total_shares
            enterprise_value = market_cap + debt - cash
            
            pe_ratio = (ipo_price / (net_profit / total_shares)) if net_profit and total_shares else None
            ps_ratio = (market_cap / revenue) if revenue else None
            ev_ebitda = (enterprise_value / ebitda) if ebitda else None
            
            return {
                "success": True,
                "metrics": {
                    "market_cap": market_cap,
                    "enterprise_value": enterprise_value,
                    "pe_ratio": pe_ratio,
                    "ps_ratio": ps_ratio,
                    "ev_ebitda": ev_ebitda
                }
            }
        except Exception as e:
            logger.error(f"Error calculating IPO metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_listing_gain(self, ipo_price: float, listing_price: float, shares: int) -> Dict[str, Any]:
        """Calculate listing gain"""
        try:
            gain_per_share = listing_price - ipo_price
            total_gain = gain_per_share * shares
            gain_percentage = (gain_per_share / ipo_price * 100) if ipo_price else 0
            
            return {
                "success": True,
                "results": {
                    "ipo_price": ipo_price,
                    "listing_price": listing_price,
                    "shares_allotted": shares,
                    "gain_per_share": gain_per_share,
                    "total_gain": total_gain,
                    "gain_percentage": round(gain_percentage, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error calculating listing gain: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_ipo_jargons(self) -> Dict[str, Any]:
        """Get all IPO jargons"""
        return {
            "success": True,
            "jargons": self.ipo_jargons,
            "count": len(self.ipo_jargons)
        }
    
    def get_ipo_lessons(self) -> Dict[str, Any]:
        """Get all IPO lessons"""
        return {
            "success": True,
            "lessons": self.ipo_lessons
        }

