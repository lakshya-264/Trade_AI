"""
Defensive Stock Screener Service
Comprehensive screening based on Graham's defensive criteria
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class DefensiveScreenerService:
    """Service for defensive stock screening"""
    
    def __init__(self):
        self.defensive_criteria = self._initialize_defensive_criteria()
        self.enterprising_criteria = self._initialize_enterprising_criteria()
    
    def _initialize_defensive_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Initialize defensive investor criteria"""
        return {
            'company_size': {
                'name': 'Company Size',
                'description': 'Large, established company',
                'criteria': {
                    'market_cap_min': 10000,  # ₹10,000 crores
                    'market_cap_currency': 'INR',
                    'years_public': 5
                },
                'weight': 0.15
            },
            'financial_strength': {
                'name': 'Financial Strength',
                'description': 'Strong balance sheet',
                'criteria': {
                    'current_ratio_min': 2.0,
                    'debt_to_equity_max': 0.5,
                    'interest_coverage_min': 5.0,
                    'quick_ratio_min': 1.0
                },
                'weight': 0.25
            },
            'earnings_stability': {
                'name': 'Earnings Stability',
                'description': 'Consistent profitability',
                'criteria': {
                    'positive_earnings_years': 10,
                    'earnings_growth_consistency': 0.7,  # 70% of years positive
                    'revenue_growth_min': 0.05  # 5% minimum
                },
                'weight': 0.20
            },
            'dividend_record': {
                'name': 'Dividend Record',
                'description': 'Regular dividend payments',
                'criteria': {
                    'dividend_years_min': 10,
                    'dividend_growth_years': 5,
                    'dividend_yield_min': 0.02,  # 2% minimum
                    'payout_ratio_max': 0.6  # 60% maximum
                },
                'weight': 0.15
            },
            'moderate_valuation': {
                'name': 'Moderate Valuation',
                'description': 'Not overpriced',
                'criteria': {
                    'pe_ratio_max': 15,
                    'pb_ratio_max': 1.5,
                    'pe_pb_product_max': 22.5,
                    'price_to_sales_max': 3.0
                },
                'weight': 0.25
            }
        }
    
    def _initialize_enterprising_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Initialize enterprising investor criteria"""
        return {
            'net_current_asset_value': {
                'name': 'Net Current Asset Value',
                'description': 'NCAV/Net-Net stocks',
                'criteria': {
                    'ncav_discount_min': 0.33,  # 33% discount to NCAV
                    'current_assets_min': 1.5,  # 1.5x total liabilities
                    'no_debt': True
                },
                'weight': 0.30
            },
            'turnaround_potential': {
                'name': 'Turnaround Potential',
                'description': 'Distressed but recoverable',
                'criteria': {
                    'recent_loss_years_max': 2,
                    'revenue_stability': 0.8,
                    'management_change': True,
                    'industry_outlook': 'positive'
                },
                'weight': 0.25
            },
            'asset_backed_value': {
                'name': 'Asset-Backed Value',
                'description': 'Strong asset backing',
                'criteria': {
                    'book_value_discount_min': 0.5,  # 50% discount to book
                    'asset_quality': 'high',
                    'liquidation_value_min': 0.8
                },
                'weight': 0.25
            },
            'growth_at_reasonable_price': {
                'name': 'Growth at Reasonable Price',
                'description': 'Growth with reasonable valuation',
                'criteria': {
                    'peg_ratio_max': 1.0,
                    'earnings_growth_min': 0.15,  # 15% minimum
                    'revenue_growth_min': 0.10,  # 10% minimum
                    'pe_ratio_max': 20
                },
                'weight': 0.20
            }
        }
    
    def screen_defensive_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen stock against defensive criteria"""
        try:
            symbol = stock_data.get('symbol', 'UNKNOWN')
            results = {}
            total_score = 0
            total_weight = 0
            
            for criterion_id, criterion in self.defensive_criteria.items():
                result = self._evaluate_criterion(criterion_id, criterion, stock_data)
                results[criterion_id] = result
                
                if result['passed']:
                    total_score += criterion['weight']
                total_weight += criterion['weight']
            
            defensive_score = (total_score / total_weight) * 100 if total_weight > 0 else 0
            
            # Generate recommendation
            recommendation = self._generate_defensive_recommendation(defensive_score, results)
            
            return {
                'symbol': symbol,
                'screening_type': 'Defensive',
                'defensive_score': round(defensive_score, 1),
                'criteria_results': results,
                'recommendation': recommendation,
                'screening_date': datetime.utcnow().isoformat(),
                'passed_criteria': sum(1 for r in results.values() if r['passed']),
                'total_criteria': len(results)
            }
            
        except Exception as e:
            return {
                'error': f"Defensive screening error: {str(e)}",
                'symbol': stock_data.get('symbol', 'UNKNOWN')
            }
    
    def screen_enterprising_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screen stock against enterprising criteria"""
        try:
            symbol = stock_data.get('symbol', 'UNKNOWN')
            results = {}
            total_score = 0
            total_weight = 0
            
            for criterion_id, criterion in self.enterprising_criteria.items():
                result = self._evaluate_enterprising_criterion(criterion_id, criterion, stock_data)
                results[criterion_id] = result
                
                if result['passed']:
                    total_score += criterion['weight']
                total_weight += criterion['weight']
            
            enterprising_score = (total_score / total_weight) * 100 if total_weight > 0 else 0
            
            # Generate recommendation
            recommendation = self._generate_enterprising_recommendation(enterprising_score, results)
            
            return {
                'symbol': symbol,
                'screening_type': 'Enterprising',
                'enterprising_score': round(enterprising_score, 1),
                'criteria_results': results,
                'recommendation': recommendation,
                'screening_date': datetime.utcnow().isoformat(),
                'passed_criteria': sum(1 for r in results.values() if r['passed']),
                'total_criteria': len(results)
            }
            
        except Exception as e:
            return {
                'error': f"Enterprising screening error: {str(e)}",
                'symbol': stock_data.get('symbol', 'UNKNOWN')
            }
    
    def _evaluate_criterion(self, criterion_id: str, criterion: Dict[str, Any], stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single defensive criterion"""
        try:
            criteria = criterion['criteria']
            passed = True
            details = {}
            
            if criterion_id == 'company_size':
                market_cap = stock_data.get('market_cap', 0)
                years_public = stock_data.get('years_public', 0)
                
                passed = market_cap >= criteria['market_cap_min'] and years_public >= criteria['years_public']
                details = {
                    'market_cap': market_cap,
                    'years_public': years_public,
                    'required_market_cap': criteria['market_cap_min'],
                    'required_years': criteria['years_public']
                }
            
            elif criterion_id == 'financial_strength':
                current_ratio = stock_data.get('current_ratio', 0)
                debt_to_equity = stock_data.get('debt_to_equity', 1)
                interest_coverage = stock_data.get('interest_coverage', 0)
                quick_ratio = stock_data.get('quick_ratio', 0)
                
                passed = (
                    current_ratio >= criteria['current_ratio_min'] and
                    debt_to_equity <= criteria['debt_to_equity_max'] and
                    interest_coverage >= criteria['interest_coverage_min'] and
                    quick_ratio >= criteria['quick_ratio_min']
                )
                details = {
                    'current_ratio': current_ratio,
                    'debt_to_equity': debt_to_equity,
                    'interest_coverage': interest_coverage,
                    'quick_ratio': quick_ratio
                }
            
            elif criterion_id == 'earnings_stability':
                positive_earnings_years = stock_data.get('positive_earnings_years', 0)
                earnings_growth_consistency = stock_data.get('earnings_growth_consistency', 0)
                revenue_growth = stock_data.get('revenue_growth', 0)
                
                passed = (
                    positive_earnings_years >= criteria['positive_earnings_years'] and
                    earnings_growth_consistency >= criteria['earnings_growth_consistency'] and
                    revenue_growth >= criteria['revenue_growth_min']
                )
                details = {
                    'positive_earnings_years': positive_earnings_years,
                    'earnings_growth_consistency': earnings_growth_consistency,
                    'revenue_growth': revenue_growth
                }
            
            elif criterion_id == 'dividend_record':
                dividend_years = stock_data.get('dividend_years', 0)
                dividend_growth_years = stock_data.get('dividend_growth_years', 0)
                dividend_yield = stock_data.get('dividend_yield', 0)
                payout_ratio = stock_data.get('payout_ratio', 1)
                
                passed = (
                    dividend_years >= criteria['dividend_years_min'] and
                    dividend_growth_years >= criteria['dividend_growth_years'] and
                    dividend_yield >= criteria['dividend_yield_min'] and
                    payout_ratio <= criteria['payout_ratio_max']
                )
                details = {
                    'dividend_years': dividend_years,
                    'dividend_growth_years': dividend_growth_years,
                    'dividend_yield': dividend_yield,
                    'payout_ratio': payout_ratio
                }
            
            elif criterion_id == 'moderate_valuation':
                pe_ratio = stock_data.get('pe_ratio', 999)
                pb_ratio = stock_data.get('pb_ratio', 999)
                price_to_sales = stock_data.get('price_to_sales', 999)
                pe_pb_product = pe_ratio * pb_ratio
                
                passed = (
                    pe_ratio <= criteria['pe_ratio_max'] and
                    pb_ratio <= criteria['pb_ratio_max'] and
                    pe_pb_product <= criteria['pe_pb_product_max'] and
                    price_to_sales <= criteria['price_to_sales_max']
                )
                details = {
                    'pe_ratio': pe_ratio,
                    'pb_ratio': pb_ratio,
                    'pe_pb_product': pe_pb_product,
                    'price_to_sales': price_to_sales
                }
            
            return {
                'criterion_name': criterion['name'],
                'description': criterion['description'],
                'passed': passed,
                'weight': criterion['weight'],
                'details': details,
                'requirements': criteria
            }
            
        except Exception as e:
            return {
                'criterion_name': criterion['name'],
                'description': criterion['description'],
                'passed': False,
                'weight': criterion['weight'],
                'error': f"Evaluation error: {str(e)}"
            }
    
    def _evaluate_enterprising_criterion(self, criterion_id: str, criterion: Dict[str, Any], stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single enterprising criterion"""
        try:
            criteria = criterion['criteria']
            passed = True
            details = {}
            
            if criterion_id == 'net_current_asset_value':
                ncav = stock_data.get('net_current_asset_value', 0)
                current_price = stock_data.get('current_price', 1)
                current_assets = stock_data.get('current_assets', 0)
                total_liabilities = stock_data.get('total_liabilities', 1)
                debt = stock_data.get('debt', 0)
                
                ncav_discount = (ncav - current_price) / ncav if ncav > 0 else 0
                
                passed = (
                    ncav_discount >= criteria['ncav_discount_min'] and
                    current_assets >= criteria['current_assets_min'] * total_liabilities and
                    (not criteria['no_debt'] or debt == 0)
                )
                details = {
                    'ncav': ncav,
                    'ncav_discount': ncav_discount,
                    'current_assets': current_assets,
                    'total_liabilities': total_liabilities,
                    'debt': debt
                }
            
            elif criterion_id == 'turnaround_potential':
                recent_loss_years = stock_data.get('recent_loss_years', 0)
                revenue_stability = stock_data.get('revenue_stability', 0)
                management_change = stock_data.get('management_change', False)
                industry_outlook = stock_data.get('industry_outlook', 'neutral')
                
                passed = (
                    recent_loss_years <= criteria['recent_loss_years_max'] and
                    revenue_stability >= criteria['revenue_stability'] and
                    management_change == criteria['management_change'] and
                    industry_outlook == criteria['industry_outlook']
                )
                details = {
                    'recent_loss_years': recent_loss_years,
                    'revenue_stability': revenue_stability,
                    'management_change': management_change,
                    'industry_outlook': industry_outlook
                }
            
            elif criterion_id == 'asset_backed_value':
                book_value = stock_data.get('book_value_per_share', 0)
                current_price = stock_data.get('current_price', 1)
                asset_quality = stock_data.get('asset_quality', 'medium')
                liquidation_value = stock_data.get('liquidation_value', 0)
                
                book_discount = (book_value - current_price) / book_value if book_value > 0 else 0
                
                passed = (
                    book_discount >= criteria['book_value_discount_min'] and
                    asset_quality == criteria['asset_quality'] and
                    liquidation_value >= criteria['liquidation_value_min']
                )
                details = {
                    'book_value': book_value,
                    'book_discount': book_discount,
                    'asset_quality': asset_quality,
                    'liquidation_value': liquidation_value
                }
            
            elif criterion_id == 'growth_at_reasonable_price':
                peg_ratio = stock_data.get('peg_ratio', 999)
                earnings_growth = stock_data.get('earnings_growth', 0)
                revenue_growth = stock_data.get('revenue_growth', 0)
                pe_ratio = stock_data.get('pe_ratio', 999)
                
                passed = (
                    peg_ratio <= criteria['peg_ratio_max'] and
                    earnings_growth >= criteria['earnings_growth_min'] and
                    revenue_growth >= criteria['revenue_growth_min'] and
                    pe_ratio <= criteria['pe_ratio_max']
                )
                details = {
                    'peg_ratio': peg_ratio,
                    'earnings_growth': earnings_growth,
                    'revenue_growth': revenue_growth,
                    'pe_ratio': pe_ratio
                }
            
            return {
                'criterion_name': criterion['name'],
                'description': criterion['description'],
                'passed': passed,
                'weight': criterion['weight'],
                'details': details,
                'requirements': criteria
            }
            
        except Exception as e:
            return {
                'criterion_name': criterion['name'],
                'description': criterion['description'],
                'passed': False,
                'weight': criterion['weight'],
                'error': f"Evaluation error: {str(e)}"
            }
    
    def _generate_defensive_recommendation(self, score: float, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate defensive investment recommendation"""
        try:
            if score >= 80:
                action = 'Strong Buy'
                confidence = 'High'
                reasoning = 'Excellent defensive characteristics'
            elif score >= 60:
                action = 'Buy'
                confidence = 'Medium'
                reasoning = 'Good defensive characteristics'
            elif score >= 40:
                action = 'Consider'
                confidence = 'Medium'
                reasoning = 'Moderate defensive characteristics'
            elif score >= 20:
                action = 'Hold'
                confidence = 'Low'
                reasoning = 'Weak defensive characteristics'
            else:
                action = 'Avoid'
                confidence = 'High'
                reasoning = 'Poor defensive characteristics'
            
            # Identify key strengths and weaknesses
            strengths = [name for name, result in results.items() if result['passed']]
            weaknesses = [name for name, result in results.items() if not result['passed']]
            
            return {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'key_factors': [
                    f"Defensive Score: {score}%",
                    f"Passed Criteria: {len(strengths)}/{len(results)}",
                    f"Primary Strengths: {', '.join(strengths[:3])}" if strengths else "None",
                    f"Primary Weaknesses: {', '.join(weaknesses[:3])}" if weaknesses else "None"
                ]
            }
            
        except Exception as e:
            return {
                'action': 'Hold',
                'confidence': 'Low',
                'reasoning': f'Recommendation error: {str(e)}'
            }
    
    def _generate_enterprising_recommendation(self, score: float, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enterprising investment recommendation"""
        try:
            if score >= 75:
                action = 'Strong Buy'
                confidence = 'High'
                reasoning = 'Excellent enterprising opportunity'
            elif score >= 50:
                action = 'Buy'
                confidence = 'Medium'
                reasoning = 'Good enterprising opportunity'
            elif score >= 25:
                action = 'Consider'
                confidence = 'Medium'
                reasoning = 'Moderate enterprising potential'
            elif score >= 10:
                action = 'Hold'
                confidence = 'Low'
                reasoning = 'Limited enterprising potential'
            else:
                action = 'Avoid'
                confidence = 'High'
                reasoning = 'Poor enterprising characteristics'
            
            # Identify key strengths and weaknesses
            strengths = [name for name, result in results.items() if result['passed']]
            weaknesses = [name for name, result in results.items() if not result['passed']]
            
            return {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'key_factors': [
                    f"Enterprising Score: {score}%",
                    f"Passed Criteria: {len(strengths)}/{len(results)}",
                    f"Primary Strengths: {', '.join(strengths[:3])}" if strengths else "None",
                    f"Primary Weaknesses: {', '.join(weaknesses[:3])}" if weaknesses else "None"
                ]
            }
            
        except Exception as e:
            return {
                'action': 'Hold',
                'confidence': 'Low',
                'reasoning': f'Recommendation error: {str(e)}'
            }

# Create service instance
defensive_screener_service = DefensiveScreenerService()
