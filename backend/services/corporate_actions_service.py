"""
Corporate Actions Service - Enhanced
Comprehensive corporate actions education with impact analysis calculator
Covers: Dividends, splits, bonus, rights, buybacks, and their impact on stock prices
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CorporateActionsService:
    """Enhanced service for corporate actions education and analysis"""
    
    def __init__(self):
        self.corporate_actions = self._initialize_corporate_actions()
        self.impact_calculators = self._initialize_impact_calculators()
    
    def _initialize_corporate_actions(self) -> Dict[str, Any]:
        """Initialize comprehensive corporate actions content"""
        return {
            "dividends": {
                "title": "Dividends",
                "description": "Distribution of company profits to shareholders",
                "types": {
                    "interim_dividend": {
                        "name": "Interim Dividend",
                        "description": "Paid during the financial year, before final accounts",
                        "frequency": "Can be declared multiple times in a year",
                        "example": "Company declares ₹5 per share interim dividend in Q3"
                    },
                    "final_dividend": {
                        "name": "Final Dividend",
                        "description": "Paid after annual results, approved by shareholders",
                        "frequency": "Once a year, at AGM",
                        "example": "Company declares ₹10 per share final dividend at AGM"
                    },
                    "special_dividend": {
                        "name": "Special Dividend",
                        "description": "One-time dividend, usually from exceptional profits or asset sales",
                        "frequency": "Occasional",
                        "example": "Company sells asset and distributes ₹20 per share special dividend"
                    }
                },
                "key_dates": {
                    "declaration_date": "Date when board announces dividend",
                    "record_date": "Date to determine eligible shareholders",
                    "ex_dividend_date": "Date from which stock trades without dividend (usually 1 day before record date)",
                    "payment_date": "Date when dividend is paid to shareholders"
                },
                "impact_on_price": {
                    "ex_dividend_effect": "Stock price typically falls by dividend amount on ex-date",
                    "example": "Stock at ₹100, ₹5 dividend → Price adjusts to ₹95 on ex-date",
                    "reason": "Dividend is cash outflow, reduces company value"
                },
                "taxation": {
                    "for_shareholders": "Dividend income is taxable as per income tax slab",
                    "tds": "Company deducts TDS @ 10% if dividend > ₹5,000",
                    "for_company": "Dividend Distribution Tax (DDT) was abolished in 2020"
                }
            },
            "stock_split": {
                "title": "Stock Split",
                "description": "Dividing existing shares into multiple shares",
                "example": {
                    "before": "1 share of ₹1000 face value",
                    "split": "1:10 split (1 share becomes 10 shares)",
                    "after": "10 shares of ₹100 face value each",
                    "impact": "Total value remains same, but number of shares increases"
                },
                "reasons": [
                    "Make stock more affordable for retail investors",
                    "Increase liquidity",
                    "Improve marketability",
                    "Psychological effect (lower price seems more attractive)"
                ],
                "impact_on_price": {
                    "theoretical": "Price should adjust proportionally (e.g., 1:2 split → price halves)",
                    "practical": "Often sees positive sentiment, price may not fall exactly by split ratio",
                    "example": "Stock at ₹2000, 1:2 split → Price should be ₹1000, but may trade at ₹1050 due to positive sentiment"
                },
                "key_dates": {
                    "announcement_date": "Date when split is announced",
                    "record_date": "Date to determine eligible shareholders",
                    "ex_split_date": "Date from which stock trades on split basis",
                    "credit_date": "Date when new shares are credited to demat account"
                }
            },
            "bonus_issue": {
                "title": "Bonus Issue",
                "description": "Free shares given to existing shareholders from company's reserves",
                "example": {
                    "before": "You own 10 shares",
                    "bonus": "1:1 bonus (1 bonus share for every 1 share held)",
                    "after": "You own 20 shares (10 original + 10 bonus)",
                    "cost": "No cost to shareholder, shares come from reserves"
                },
                "reasons": [
                    "Reward shareholders",
                    "Capitalize reserves",
                    "Improve liquidity",
                    "Signal company confidence"
                ],
                "impact_on_price": {
                    "theoretical": "Price adjusts proportionally (e.g., 1:1 bonus → price halves)",
                    "practical": "Similar to stock split, may see positive sentiment",
                    "example": "Stock at ₹200, 1:1 bonus → Price should be ₹100, but may trade at ₹105"
                },
                "vs_stock_split": {
                    "bonus": "Shares come from reserves, increases paid-up capital",
                    "split": "Just divides existing shares, paid-up capital unchanged",
                    "accounting": "Bonus affects balance sheet, split doesn't"
                }
            },
            "rights_issue": {
                "title": "Rights Issue",
                "description": "Company offers new shares to existing shareholders at discounted price",
                "example": {
                    "scenario": "Company needs capital",
                    "offer": "1:5 rights issue at ₹50 (current price ₹100)",
                    "meaning": "For every 5 shares you own, you can buy 1 new share at ₹50",
                    "choice": "You can subscribe, renounce (sell rights), or let it lapse"
                },
                "key_features": {
                    "discounted_price": "Rights price is usually below market price",
                    "proportional": "Allocation is proportional to existing holding",
                    "optional": "Shareholder can choose to subscribe or not",
                    "transferable": "Rights can be sold to others (renunciation)"
                },
                "impact_on_price": {
                    "announcement": "Usually negative (dilution concern)",
                    "ex_rights_date": "Price adjusts for dilution",
                    "formula": "Theoretical Ex-Rights Price = (Old Price × Old Shares + Rights Price × New Shares) / Total Shares"
                },
                "calculation_example": {
                    "old_price": 100,
                    "old_shares": 5,
                    "rights_price": 50,
                    "new_shares": 1,
                    "theoretical_price": "(100 × 5 + 50 × 1) / 6 = ₹91.67"
                }
            },
            "buyback": {
                "title": "Share Buyback",
                "description": "Company buys back its own shares from market",
                "methods": {
                    "tender_offer": {
                        "name": "Tender Offer",
                        "description": "Company offers to buy at fixed price from shareholders",
                        "process": "Shareholders can tender shares at offer price"
                    },
                    "open_market": {
                        "name": "Open Market",
                        "description": "Company buys shares from open market like any investor",
                        "process": "Gradual buying over time"
                    }
                },
                "reasons": [
                    "Return excess cash to shareholders",
                    "Improve earnings per share (EPS)",
                    "Signal undervaluation",
                    "Prevent hostile takeover"
                ],
                "impact_on_price": {
                    "announcement": "Usually positive (signals confidence, reduces supply)",
                    "during_buyback": "Price support from company buying",
                    "post_buyback": "EPS improves (fewer shares outstanding)"
                }
            }
        }
    
    def _initialize_impact_calculators(self) -> Dict[str, Any]:
        """Initialize impact calculation tools"""
        return {
            "dividend_impact": {
                "name": "Dividend Impact Calculator",
                "description": "Calculate impact of dividend on stock price and returns"
            },
            "split_impact": {
                "name": "Stock Split Impact Calculator",
                "description": "Calculate adjusted price after stock split"
            },
            "bonus_impact": {
                "name": "Bonus Issue Impact Calculator",
                "description": "Calculate adjusted price and holdings after bonus"
            },
            "rights_impact": {
                "name": "Rights Issue Impact Calculator",
                "description": "Calculate theoretical ex-rights price and dilution impact"
            }
        }
    
    def calculate_dividend_impact(self, current_price: float, dividend_per_share: float, shares_held: int) -> Dict[str, Any]:
        """Calculate dividend impact on portfolio"""
        try:
            total_dividend = dividend_per_share * shares_held
            dividend_yield = (dividend_per_share / current_price * 100) if current_price else 0
            ex_dividend_price = current_price - dividend_per_share
            
            return {
                "success": True,
                "current_price": current_price,
                "dividend_per_share": dividend_per_share,
                "shares_held": shares_held,
                "total_dividend": total_dividend,
                "dividend_yield": round(dividend_yield, 2),
                "ex_dividend_price": round(ex_dividend_price, 2),
                "price_adjustment": -dividend_per_share,
                "portfolio_value_before": current_price * shares_held,
                "portfolio_value_after": (ex_dividend_price * shares_held) + total_dividend,
                "net_impact": "No change (value shifts from stock to cash)"
            }
        except Exception as e:
            logger.error(f"Error calculating dividend impact: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_split_impact(self, current_price: float, split_ratio: str, shares_held: int) -> Dict[str, Any]:
        """Calculate stock split impact"""
        try:
            # Parse split ratio (e.g., "1:2" means 1 share becomes 2)
            ratio_parts = split_ratio.split(":")
            if len(ratio_parts) != 2:
                return {"success": False, "error": "Invalid split ratio format. Use format '1:2'"}
            
            old_shares = int(ratio_parts[0])
            new_shares = int(ratio_parts[1])
            split_multiplier = new_shares / old_shares
            
            adjusted_price = current_price / split_multiplier
            new_shares_held = shares_held * split_multiplier
            
            return {
                "success": True,
                "current_price": current_price,
                "split_ratio": split_ratio,
                "shares_held_before": shares_held,
                "adjusted_price": round(adjusted_price, 2),
                "new_shares_held": int(new_shares_held),
                "portfolio_value_before": current_price * shares_held,
                "portfolio_value_after": adjusted_price * new_shares_held,
                "net_impact": "No change in value, only number of shares increases"
            }
        except Exception as e:
            logger.error(f"Error calculating split impact: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_bonus_impact(self, current_price: float, bonus_ratio: str, shares_held: int) -> Dict[str, Any]:
        """Calculate bonus issue impact"""
        try:
            # Parse bonus ratio (e.g., "1:1" means 1 bonus share for every 1 share)
            ratio_parts = bonus_ratio.split(":")
            if len(ratio_parts) != 2:
                return {"success": False, "error": "Invalid bonus ratio format. Use format '1:1'"}
            
            existing_shares = int(ratio_parts[0])
            bonus_shares = int(ratio_parts[1])
            bonus_multiplier = (existing_shares + bonus_shares) / existing_shares
            
            adjusted_price = current_price / bonus_multiplier
            new_shares_held = shares_held * bonus_multiplier
            
            return {
                "success": True,
                "current_price": current_price,
                "bonus_ratio": bonus_ratio,
                "shares_held_before": shares_held,
                "adjusted_price": round(adjusted_price, 2),
                "new_shares_held": int(new_shares_held),
                "bonus_shares_received": int(shares_held * (bonus_shares / existing_shares)),
                "portfolio_value_before": current_price * shares_held,
                "portfolio_value_after": adjusted_price * new_shares_held,
                "net_impact": "No change in value, free shares added"
            }
        except Exception as e:
            logger.error(f"Error calculating bonus impact: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_rights_impact(self, current_price: float, rights_ratio: str, rights_price: float, shares_held: int) -> Dict[str, Any]:
        """Calculate rights issue impact"""
        try:
            # Parse rights ratio (e.g., "1:5" means 1 right share for every 5 existing shares)
            ratio_parts = rights_ratio.split(":")
            if len(ratio_parts) != 2:
                return {"success": False, "error": "Invalid rights ratio format. Use format '1:5'"}
            
            existing_shares = int(ratio_parts[0])
            rights_shares = int(ratio_parts[1])
            
            # Calculate rights entitlement
            rights_entitlement = int((shares_held / existing_shares) * rights_shares)
            
            # Calculate theoretical ex-rights price
            total_old_value = current_price * existing_shares
            total_new_value = rights_price * rights_shares
            total_shares_after = existing_shares + rights_shares
            theoretical_ex_rights_price = (total_old_value + total_new_value) / total_shares_after
            
            # Calculate if you subscribe
            cost_to_subscribe = rights_price * rights_entitlement
            new_total_shares = shares_held + rights_entitlement
            new_portfolio_value = theoretical_ex_rights_price * new_total_shares
            old_portfolio_value = current_price * shares_held
            net_investment_required = cost_to_subscribe
            
            return {
                "success": True,
                "current_price": current_price,
                "rights_ratio": rights_ratio,
                "rights_price": rights_price,
                "shares_held": shares_held,
                "rights_entitlement": rights_entitlement,
                "theoretical_ex_rights_price": round(theoretical_ex_rights_price, 2),
                "cost_to_subscribe": cost_to_subscribe,
                "shares_after_subscription": new_total_shares,
                "portfolio_value_before": old_portfolio_value,
                "portfolio_value_after_subscription": round(new_portfolio_value, 2),
                "dilution_impact": round(current_price - theoretical_ex_rights_price, 2),
                "dilution_percent": round(((current_price - theoretical_ex_rights_price) / current_price * 100), 2)
            }
        except Exception as e:
            logger.error(f"Error calculating rights impact: {e}")
            return {"success": False, "error": str(e)}
    
    def get_corporate_actions_info(self) -> Dict[str, Any]:
        """Get comprehensive corporate actions information"""
        return {
            "success": True,
            "corporate_actions": self.corporate_actions,
            "calculators": self.impact_calculators
        }

