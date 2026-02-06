"""
Intrinsic Value Service
Multiple models for calculating intrinsic value and margin of safety
"""

from typing import Dict, List, Any, Optional, Tuple
import math
from datetime import datetime, timedelta
import json

class IntrinsicValueService:
    """Service for calculating intrinsic value using multiple models"""
    
    def __init__(self):
        self.models = {
            'graham': self._graham_formula,
            'dcf_lite': self._dcf_lite,
            'earnings_yield': self._earnings_yield_model,
            'pe_mean_reversion': self._pe_mean_reversion,
            'pb_roe': self._pb_roe_model
        }
    
    def calculate_intrinsic_value(self, 
                                symbol: str,
                                current_price: float,
                                eps: float,
                                growth_rate: float,
                                bond_yield: float,
                                pe_ratio: float,
                                pb_ratio: float,
                                roe: float,
                                dividend_yield: float = 0.0,
                                book_value_per_share: float = 0.0,
                                historical_pe: List[float] = None) -> Dict[str, Any]:
        """
        Calculate intrinsic value using multiple models
        """
        try:
            results = {}
            confidence_scores = {}
            
            # Graham Formula
            graham_result = self._graham_formula(eps, growth_rate, bond_yield)
            results['graham'] = graham_result
            confidence_scores['graham'] = self._calculate_confidence('graham', eps, growth_rate, bond_yield)
            
            # DCF Lite
            dcf_result = self._dcf_lite(eps, growth_rate, bond_yield, dividend_yield)
            results['dcf_lite'] = dcf_result
            confidence_scores['dcf_lite'] = self._calculate_confidence('dcf_lite', eps, growth_rate, bond_yield)
            
            # Earnings Yield Model
            ey_result = self._earnings_yield_model(eps, bond_yield, current_price)
            results['earnings_yield'] = ey_result
            confidence_scores['earnings_yield'] = self._calculate_confidence('earnings_yield', eps, bond_yield, current_price)
            
            # P/E Mean Reversion
            if historical_pe and len(historical_pe) > 0:
                pe_result = self._pe_mean_reversion(eps, historical_pe, current_price)
                results['pe_mean_reversion'] = pe_result
                confidence_scores['pe_mean_reversion'] = self._calculate_confidence('pe_mean_reversion', eps, historical_pe)
            
            # P/B vs ROE Model
            if book_value_per_share > 0 and roe > 0:
                pb_roe_result = self._pb_roe_model(book_value_per_share, roe, current_price)
                results['pb_roe'] = pb_roe_result
                confidence_scores['pb_roe'] = self._calculate_confidence('pb_roe', book_value_per_share, roe)
            
            # Calculate weighted average intrinsic value
            weighted_iv = self._calculate_weighted_average(results, confidence_scores)
            
            # Calculate margin of safety
            margin_of_safety = self._calculate_margin_of_safety(weighted_iv, current_price)
            
            # Risk assessment
            risk_assessment = self._assess_valuation_risk(results, current_price, margin_of_safety)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'intrinsic_value': weighted_iv,
                'margin_of_safety': margin_of_safety,
                'models': results,
                'confidence_scores': confidence_scores,
                'risk_assessment': risk_assessment,
                'recommendation': self._generate_recommendation(margin_of_safety, risk_assessment),
                'calculation_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f"Error calculating intrinsic value: {str(e)}",
                'symbol': symbol,
                'current_price': current_price
            }
    
    def _graham_formula(self, eps: float, growth_rate: float, bond_yield: float) -> Dict[str, Any]:
        """Graham Formula: V = EPS × (8.5 + 2g) × (4.4/Y)"""
        try:
            if bond_yield <= 0:
                return {'error': 'Bond yield must be positive'}
            
            intrinsic_value = eps * (8.5 + 2 * growth_rate) * (4.4 / bond_yield)
            
            return {
                'model': 'Graham Formula',
                'formula': 'V = EPS × (8.5 + 2g) × (4.4/Y)',
                'calculation': f'{eps} × (8.5 + 2×{growth_rate}) × (4.4/{bond_yield})',
                'intrinsic_value': round(intrinsic_value, 2),
                'assumptions': {
                    'eps': eps,
                    'growth_rate': growth_rate,
                    'bond_yield': bond_yield,
                    'base_multiple': 8.5,
                    'growth_multiplier': 2
                }
            }
        except Exception as e:
            return {'error': f"Graham formula error: {str(e)}"}
    
    def _dcf_lite(self, eps: float, growth_rate: float, bond_yield: float, dividend_yield: float) -> Dict[str, Any]:
        """Simplified DCF model"""
        try:
            # Terminal growth rate (conservative)
            terminal_growth = min(growth_rate * 0.5, 0.03)  # Max 3%
            
            # Discount rate (bond yield + risk premium)
            discount_rate = bond_yield + 0.05  # 5% risk premium
            
            # Project earnings for 5 years
            projected_earnings = []
            current_eps = eps
            
            for year in range(1, 6):
                current_eps *= (1 + growth_rate)
                projected_earnings.append(current_eps)
            
            # Terminal value
            terminal_value = (projected_earnings[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            
            # Present value calculation
            pv_earnings = sum(eps / (1 + discount_rate) ** year for year, eps in enumerate(projected_earnings, 1))
            pv_terminal = terminal_value / (1 + discount_rate) ** 5
            
            intrinsic_value = pv_earnings + pv_terminal
            
            return {
                'model': 'DCF Lite',
                'formula': 'PV of 5-year earnings + Terminal value',
                'intrinsic_value': round(intrinsic_value, 2),
                'assumptions': {
                    'growth_rate': growth_rate,
                    'terminal_growth': terminal_growth,
                    'discount_rate': discount_rate,
                    'projection_years': 5
                }
            }
        except Exception as e:
            return {'error': f"DCF Lite error: {str(e)}"}
    
    def _earnings_yield_model(self, eps: float, bond_yield: float, current_price: float) -> Dict[str, Any]:
        """Earnings Yield vs Bond Yield model"""
        try:
            earnings_yield = eps / current_price
            
            # If earnings yield > bond yield, stock is attractive
            # Intrinsic value = EPS / Bond yield
            intrinsic_value = eps / bond_yield
            
            return {
                'model': 'Earnings Yield Model',
                'formula': 'V = EPS / Bond Yield',
                'intrinsic_value': round(intrinsic_value, 2),
                'earnings_yield': round(earnings_yield * 100, 2),
                'bond_yield': round(bond_yield * 100, 2),
                'yield_spread': round((earnings_yield - bond_yield) * 100, 2),
                'assumptions': {
                    'eps': eps,
                    'bond_yield': bond_yield,
                    'current_price': current_price
                }
            }
        except Exception as e:
            return {'error': f"Earnings yield model error: {str(e)}"}
    
    def _pe_mean_reversion(self, eps: float, historical_pe: List[float], current_price: float) -> Dict[str, Any]:
        """P/E Mean Reversion model"""
        try:
            if not historical_pe or len(historical_pe) < 2:
                return {'error': 'Insufficient historical P/E data'}
            
            # Calculate mean and median P/E
            mean_pe = sum(historical_pe) / len(historical_pe)
            median_pe = sorted(historical_pe)[len(historical_pe) // 2]
            
            # Use median for more conservative estimate
            fair_pe = median_pe
            
            intrinsic_value = eps * fair_pe
            
            return {
                'model': 'P/E Mean Reversion',
                'formula': 'V = EPS × Fair P/E',
                'intrinsic_value': round(intrinsic_value, 2),
                'fair_pe': round(fair_pe, 2),
                'current_pe': round(current_price / eps, 2),
                'mean_pe': round(mean_pe, 2),
                'median_pe': round(median_pe, 2),
                'assumptions': {
                    'eps': eps,
                    'historical_pe_count': len(historical_pe),
                    'fair_pe': fair_pe
                }
            }
        except Exception as e:
            return {'error': f"P/E mean reversion error: {str(e)}"}
    
    def _pb_roe_model(self, book_value_per_share: float, roe: float, current_price: float) -> Dict[str, Any]:
        """P/B vs ROE model"""
        try:
            # Fair P/B based on ROE
            # Higher ROE should command higher P/B
            fair_pb = 1 + (roe - 0.1) * 2  # Base P/B of 1, ROE above 10% gets premium
            fair_pb = max(fair_pb, 0.5)  # Minimum P/B of 0.5
            
            intrinsic_value = book_value_per_share * fair_pb
            
            return {
                'model': 'P/B vs ROE',
                'formula': 'V = Book Value × Fair P/B',
                'intrinsic_value': round(intrinsic_value, 2),
                'fair_pb': round(fair_pb, 2),
                'current_pb': round(current_price / book_value_per_share, 2),
                'roe': round(roe * 100, 2),
                'assumptions': {
                    'book_value_per_share': book_value_per_share,
                    'roe': roe,
                    'fair_pb': fair_pb
                }
            }
        except Exception as e:
            return {'error': f"P/B vs ROE model error: {str(e)}"}
    
    def _calculate_weighted_average(self, results: Dict[str, Any], confidence_scores: Dict[str, float]) -> float:
        """Calculate weighted average intrinsic value based on confidence scores"""
        try:
            total_weight = 0
            weighted_sum = 0
            
            for model, result in results.items():
                if 'intrinsic_value' in result and not 'error' in result:
                    weight = confidence_scores.get(model, 0.5)
                    weighted_sum += result['intrinsic_value'] * weight
                    total_weight += weight
            
            if total_weight == 0:
                return 0
            
            return round(weighted_sum / total_weight, 2)
        except Exception as e:
            return 0
    
    def _calculate_confidence(self, model: str, *args) -> float:
        """Calculate confidence score for each model"""
        try:
            confidence_map = {
                'graham': 0.8,  # High confidence, proven formula
                'dcf_lite': 0.7,  # Good confidence, simplified model
                'earnings_yield': 0.6,  # Moderate confidence
                'pe_mean_reversion': 0.7,  # Good confidence if historical data available
                'pb_roe': 0.6   # Moderate confidence
            }
            
            base_confidence = confidence_map.get(model, 0.5)
            
            # Adjust based on data quality
            if model == 'pe_mean_reversion' and len(args) > 0:
                historical_pe = args[0]
                if len(historical_pe) >= 5:
                    base_confidence += 0.1
                elif len(historical_pe) < 3:
                    base_confidence -= 0.2
            
            return min(max(base_confidence, 0.1), 1.0)
        except Exception as e:
            return 0.5
    
    def _calculate_margin_of_safety(self, intrinsic_value: float, current_price: float) -> Dict[str, Any]:
        """Calculate margin of safety"""
        try:
            if intrinsic_value <= 0:
                return {'error': 'Invalid intrinsic value'}
            
            mos_percentage = ((intrinsic_value - current_price) / intrinsic_value) * 100
            
            # Determine safety level
            if mos_percentage >= 30:
                safety_level = 'Very High'
                recommendation = 'Strong Buy'
            elif mos_percentage >= 20:
                safety_level = 'High'
                recommendation = 'Buy'
            elif mos_percentage >= 10:
                safety_level = 'Medium'
                recommendation = 'Consider'
            elif mos_percentage >= 0:
                safety_level = 'Low'
                recommendation = 'Hold'
            else:
                safety_level = 'Negative'
                recommendation = 'Avoid'
            
            return {
                'percentage': round(mos_percentage, 2),
                'absolute_value': round(intrinsic_value - current_price, 2),
                'safety_level': safety_level,
                'recommendation': recommendation,
                'intrinsic_value': intrinsic_value,
                'current_price': current_price
            }
        except Exception as e:
            return {'error': f"Margin of safety calculation error: {str(e)}"}
    
    def _assess_valuation_risk(self, results: Dict[str, Any], current_price: float, margin_of_safety: Dict[str, Any]) -> Dict[str, Any]:
        """Assess valuation risk based on model consistency"""
        try:
            valid_models = [r for r in results.values() if 'intrinsic_value' in r and not 'error' in r]
            
            if len(valid_models) < 2:
                return {'risk_level': 'High', 'reason': 'Insufficient model data'}
            
            # Calculate variance in intrinsic values
            intrinsic_values = [r['intrinsic_value'] for r in valid_models]
            mean_iv = sum(intrinsic_values) / len(intrinsic_values)
            variance = sum((iv - mean_iv) ** 2 for iv in intrinsic_values) / len(intrinsic_values)
            std_dev = math.sqrt(variance)
            coefficient_of_variation = std_dev / mean_iv if mean_iv > 0 else 1
            
            # Risk assessment
            if coefficient_of_variation < 0.1:
                risk_level = 'Low'
                risk_reason = 'High model consistency'
            elif coefficient_of_variation < 0.2:
                risk_level = 'Medium'
                risk_reason = 'Moderate model consistency'
            else:
                risk_level = 'High'
                risk_reason = 'Low model consistency'
            
            # Adjust based on margin of safety
            mos_percentage = margin_of_safety.get('percentage', 0)
            if mos_percentage < 0:
                risk_level = 'Very High'
                risk_reason += ' - Negative margin of safety'
            
            return {
                'risk_level': risk_level,
                'reason': risk_reason,
                'model_count': len(valid_models),
                'coefficient_of_variation': round(coefficient_of_variation, 3),
                'mean_intrinsic_value': round(mean_iv, 2),
                'std_deviation': round(std_dev, 2)
            }
        except Exception as e:
            return {'risk_level': 'High', 'reason': f'Risk assessment error: {str(e)}'}
    
    def _generate_recommendation(self, margin_of_safety: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate investment recommendation"""
        try:
            mos_percentage = margin_of_safety.get('percentage', 0)
            risk_level = risk_assessment.get('risk_level', 'High')
            
            # Base recommendation on margin of safety
            if mos_percentage >= 25 and risk_level in ['Low', 'Medium']:
                action = 'Strong Buy'
                confidence = 'High'
            elif mos_percentage >= 15 and risk_level in ['Low', 'Medium']:
                action = 'Buy'
                confidence = 'Medium'
            elif mos_percentage >= 5:
                action = 'Consider'
                confidence = 'Medium'
            elif mos_percentage >= 0:
                action = 'Hold'
                confidence = 'Low'
            else:
                action = 'Avoid'
                confidence = 'High'
            
            # Adjust for risk
            if risk_level == 'High':
                confidence = 'Low'
            elif risk_level == 'Very High':
                action = 'Avoid'
                confidence = 'High'
            
            return {
                'action': action,
                'confidence': confidence,
                'reasoning': f"Margin of safety: {mos_percentage}%, Risk: {risk_level}",
                'key_factors': [
                    f"Margin of Safety: {mos_percentage}%",
                    f"Risk Level: {risk_level}",
                    f"Model Consistency: {risk_assessment.get('reason', 'Unknown')}"
                ]
            }
        except Exception as e:
            return {
                'action': 'Hold',
                'confidence': 'Low',
                'reasoning': f'Recommendation error: {str(e)}'
            }

# Create service instance
intrinsic_value_service = IntrinsicValueService()
