"""
Duration Analysis Service - Track and analyze holding periods
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import logging

from core.database import get_db
from models.trading_performance_models import TradingExecution
from core.database_unified import User, PortfolioMetadata

logger = logging.getLogger(__name__)

class DurationAnalysisService:
    """Service for analyzing trade durations and holding periods"""
    
    def __init__(self):
        self.duration_categories = {
            'SCALP': {'min_hours': 0, 'max_hours': 1},
            'INTRADAY': {'min_hours': 1, 'max_hours': 6},
            'SWING': {'min_hours': 6, 'max_hours': 72},
            'POSITIONAL': {'min_hours': 72, 'max_hours': 168},
            'LONG_TERM': {'min_hours': 168, 'max_hours': float('inf')}
        }
        
        self.performance_benchmarks = {
            'SCALP': {'target_win_rate': 0.6, 'target_return': 0.5},
            'INTRADAY': {'target_win_rate': 0.55, 'target_return': 1.0},
            'SWING': {'target_win_rate': 0.5, 'target_return': 2.0},
            'POSITIONAL': {'target_win_rate': 0.45, 'target_return': 3.0},
            'LONG_TERM': {'target_win_rate': 0.4, 'target_return': 5.0}
        }
    
    async def analyze_trade_durations(
        self,
        user_id: int,
        days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """Comprehensive duration analysis for user's trades"""
        try:
            logger.info(f"Analyzing trade durations for user {user_id} over {days} days")
            
            # Get user's closed trades
            closed_trades = await self._get_closed_trades(user_id, days, db)
            
            if not closed_trades:
                return {
                    'success': True,
                    'message': 'No closed trades found for analysis',
                    'data': {
                        'total_trades': 0,
                        'duration_analysis': {},
                        'performance_by_duration': {},
                        'recommendations': []
                    }
                }
            
            # Categorize trades by duration
            categorized_trades = self._categorize_trades_by_duration(closed_trades)
            
            # Analyze performance by duration category
            performance_by_duration = await self._analyze_performance_by_duration(
                categorized_trades
            )
            
            # Calculate duration metrics
            duration_metrics = self._calculate_duration_metrics(closed_trades)
            
            # Generate duration insights
            duration_insights = await self._generate_duration_insights(
                categorized_trades, performance_by_duration, duration_metrics
            )
            
            # Optimal duration analysis
            optimal_duration = self._find_optimal_duration(performance_by_duration)
            
            # Holding pattern analysis
            holding_patterns = self._analyze_holding_patterns(closed_trades)
            
            return {
                'success': True,
                'data': {
                    'total_trades': len(closed_trades),
                    'duration_metrics': duration_metrics,
                    'categorized_trades': categorized_trades,
                    'performance_by_duration': performance_by_duration,
                    'duration_insights': duration_insights,
                    'optimal_duration': optimal_duration,
                    'holding_patterns': holding_patterns,
                    'analysis_period': days,
                    'generated_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in duration analysis: {e}")
            raise
    
    async def _get_closed_trades(
        self,
        user_id: int,
        days: int,
        db: Session
    ) -> List[TradingExecution]:
        """Get user's closed trades within the period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            trades = db.query(TradingExecution).filter(
                and_(
                    # TradingExecution.user_id == user_id,
                    TradingExecution.status == 'CLOSED',
                    TradingExecution.created_at >= cutoff_date,
                    TradingExecution.exit_time.isnot(None)
                )
            ).all()
            
            # Calculate holding periods for each trade
            for trade in trades:
                if trade.entry_time and trade.exit_time:
                    trade.holding_period_hours = (
                        trade.exit_time - trade.entry_time
                    ).total_seconds() / 3600
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting closed trades: {e}")
            return []
    
    def _categorize_trades_by_duration(
        self,
        trades: List[TradingExecution]
    ) -> Dict[str, List[TradingExecution]]:
        """Categorize trades by holding duration"""
        try:
            categorized = {
                'SCALP': [],
                'INTRADAY': [],
                'SWING': [],
                'POSITIONAL': [],
                'LONG_TERM': []
            }
            
            for trade in trades:
                holding_hours = getattr(trade, 'holding_period_hours', 0)
                
                for category, limits in self.duration_categories.items():
                    if limits['min_hours'] <= holding_hours < limits['max_hours']:
                        categorized[category].append(trade)
                        break
            
            return categorized
            
        except Exception as e:
            logger.error(f"Error categorizing trades: {e}")
            return {}
    
    async def _analyze_performance_by_duration(
        self,
        categorized_trades: Dict[str, List[TradingExecution]]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze performance metrics for each duration category"""
        try:
            performance_by_duration = {}
            
            for category, trades in categorized_trades.items():
                if not trades:
                    performance_by_duration[category] = {
                        'trade_count': 0,
                        'win_rate': 0,
                        'avg_return': 0,
                        'total_return': 0,
                        'avg_holding_period': 0,
                        'sharpe_ratio': 0,
                        'max_profit': 0,
                        'max_loss': 0,
                        'performance_score': 0,
                        'benchmark_comparison': {}
                    }
                    continue
                
                # Calculate basic metrics
                profitable_trades = [t for t in trades if t.pnl_percent and t.pnl_percent > 0]
                win_rate = len(profitable_trades) / len(trades)
                
                returns = [t.pnl_percent or 0 for t in trades]
                total_return = sum(returns)
                avg_return = total_return / len(trades)
                
                max_profit = max(returns)
                max_loss = min(returns)
                
                # Calculate average holding period
                holding_periods = [getattr(t, 'holding_period_hours', 0) for t in trades]
                avg_holding_period = sum(holding_periods) / len(holding_periods)
                
                # Calculate Sharpe ratio
                if len(returns) > 1:
                    avg_ret = sum(returns) / len(returns)
                    variance = sum((r - avg_ret) ** 2 for r in returns) / len(returns)
                    volatility = variance ** 0.5
                    sharpe_ratio = avg_ret / volatility if volatility > 0 else 0
                else:
                    sharpe_ratio = 0
                
                # Calculate performance score against benchmarks
                benchmark = self.performance_benchmarks.get(category, {})
                performance_score = self._calculate_duration_performance_score(
                    win_rate, avg_return, sharpe_ratio, benchmark
                )
                
                # Benchmark comparison
                benchmark_comparison = {
                    'win_rate_vs_target': win_rate - benchmark.get('target_win_rate', 0.5),
                    'return_vs_target': avg_return - benchmark.get('target_return', 1.0),
                    'meets_win_rate_target': win_rate >= benchmark.get('target_win_rate', 0.5),
                    'meets_return_target': avg_return >= benchmark.get('target_return', 1.0)
                }
                
                performance_by_duration[category] = {
                    'trade_count': len(trades),
                    'win_rate': win_rate,
                    'avg_return': avg_return,
                    'total_return': total_return,
                    'avg_holding_period': avg_holding_period,
                    'sharpe_ratio': sharpe_ratio,
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'performance_score': performance_score,
                    'benchmark_comparison': benchmark_comparison
                }
            
            return performance_by_duration
            
        except Exception as e:
            logger.error(f"Error analyzing performance by duration: {e}")
            return {}
    
    def _calculate_duration_performance_score(
        self,
        win_rate: float,
        avg_return: float,
        sharpe_ratio: float,
        benchmark: Dict[str, float]
    ) -> float:
        """Calculate performance score for duration category"""
        try:
            # Win rate component (40 points)
            target_win_rate = benchmark.get('target_win_rate', 0.5)
            win_rate_score = min(40, (win_rate / target_win_rate) * 40) if target_win_rate > 0 else 0
            
            # Return component (40 points)
            target_return = benchmark.get('target_return', 1.0)
            return_score = min(40, (avg_return / target_return) * 40) if target_return > 0 else 0
            
            # Sharpe ratio component (20 points)
            sharpe_score = min(20, max(0, sharpe_ratio * 10))
            
            total_score = win_rate_score + return_score + sharpe_score
            return round(total_score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0
    
    def _calculate_duration_metrics(
        self,
        trades: List[TradingExecution]
    ) -> Dict[str, Any]:
        """Calculate overall duration metrics"""
        try:
            if not trades:
                return {}
            
            holding_periods = [getattr(t, 'holding_period_hours', 0) for t in trades]
            
            # Basic statistics
            avg_holding_period = sum(holding_periods) / len(holding_periods)
            min_holding_period = min(holding_periods)
            max_holding_period = max(holding_periods)
            
            # Median holding period
            sorted_periods = sorted(holding_periods)
            median_holding_period = sorted_periods[len(sorted_periods) // 2]
            
            # Holding period distribution
            distribution = {
                'under_1_hour': len([p for p in holding_periods if p < 1]),
                '1_to_6_hours': len([p for p in holding_periods if 1 <= p < 6]),
                '6_to_24_hours': len([p for p in holding_periods if 6 <= p < 24]),
                '1_to_3_days': len([p for p in holding_periods if 24 <= p < 72]),
                '3_to_7_days': len([p for p in holding_periods if 72 <= p < 168]),
                'over_7_days': len([p for p in holding_periods if p >= 168])
            }
            
            # Time-based performance
            time_performance = {}
            for period_start, period_end, period_name in [
                (0, 1, 'Scalp'),
                (1, 6, 'Intraday'),
                (6, 24, 'Swing Short'),
                (24, 72, 'Swing Long'),
                (72, 168, 'Positional'),
                (168, float('inf'), 'Long Term')
            ]:
                period_trades = [
                    t for t in trades 
                    if period_start <= getattr(t, 'holding_period_hours', 0) < period_end
                ]
                
                if period_trades:
                    period_returns = [t.pnl_percent or 0 for t in period_trades]
                    period_win_rate = len([r for r in period_returns if r > 0]) / len(period_returns)
                    period_avg_return = sum(period_returns) / len(period_returns)
                    
                    time_performance[period_name] = {
                        'trade_count': len(period_trades),
                        'win_rate': period_win_rate,
                        'avg_return': period_avg_return,
                        'total_return': sum(period_returns)
                    }
            
            return {
                'avg_holding_period': avg_holding_period,
                'median_holding_period': median_holding_period,
                'min_holding_period': min_holding_period,
                'max_holding_period': max_holding_period,
                'distribution': distribution,
                'time_performance': time_performance,
                'total_trades_analyzed': len(trades)
            }
            
        except Exception as e:
            logger.error(f"Error calculating duration metrics: {e}")
            return {}
    
    async def _generate_duration_insights(
        self,
        categorized_trades: Dict[str, List[TradingExecution]],
        performance_by_duration: Dict[str, Dict[str, Any]],
        duration_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights about trading durations"""
        try:
            insights = {
                'optimal_durations': [],
                'suboptimal_durations': [],
                'recommendations': [],
                'patterns': [],
                'risk_assessment': ''
            }
            
            # Find best and worst performing durations
            duration_scores = {
                category: data.get('performance_score', 0)
                for category, data in performance_by_duration.items()
                if data.get('trade_count', 0) > 0
            }
            
            if duration_scores:
                # Best performing durations
                sorted_scores = sorted(duration_scores.items(), key=lambda x: x[1], reverse=True)
                insights['optimal_durations'] = [
                    {
                        'duration': category,
                        'score': score,
                        'win_rate': performance_by_duration[category].get('win_rate', 0),
                        'avg_return': performance_by_duration[category].get('avg_return', 0),
                        'trade_count': performance_by_duration[category].get('trade_count', 0)
                    }
                    for category, score in sorted_scores[:3]
                ]
                
                # Worst performing durations
                insights['suboptimal_durations'] = [
                    {
                        'duration': category,
                        'score': score,
                        'win_rate': performance_by_duration[category].get('win_rate', 0),
                        'avg_return': performance_by_duration[category].get('avg_return', 0),
                        'trade_count': performance_by_duration[category].get('trade_count', 0)
                    }
                    for category, score in sorted_scores[-2:] if score < 50
                ]
            
            # Generate recommendations
            insights['recommendations'] = self._generate_duration_recommendations(
                performance_by_duration, duration_metrics
            )
            
            # Identify patterns
            insights['patterns'] = self._identify_duration_patterns(
                categorized_trades, duration_metrics
            )
            
            # Risk assessment
            insights['risk_assessment'] = self._assess_duration_risk(
                duration_metrics, performance_by_duration
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating duration insights: {e}")
            return {}
    
    def _generate_duration_recommendations(
        self,
        performance_by_duration: Dict[str, Dict[str, Any]],
        duration_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on duration analysis"""
        try:
            recommendations = []
            
            # Analyze average holding period
            avg_period = duration_metrics.get('avg_holding_period', 0)
            
            if avg_period < 2:
                recommendations.append("Very short holding periods detected - consider longer timeframes for better risk management")
            elif avg_period > 72:
                recommendations.append("Very long holding periods detected - ensure proper position sizing and risk management")
            
            # Analyze performance by duration
            for category, metrics in performance_by_duration.items():
                if metrics.get('trade_count', 0) > 5:  # Only consider categories with sufficient data
                    win_rate = metrics.get('win_rate', 0)
                    avg_return = metrics.get('avg_return', 0)
                    
                    if win_rate < 0.4:
                        recommendations.append(f"Low win rate in {category} trades ({win_rate:.1%}) - review entry criteria")
                    
                    if avg_return < 0:
                        recommendations.append(f"Negative average return in {category} trades ({avg_return:.2f}%) - consider strategy adjustment")
            
            # Distribution recommendations
            distribution = duration_metrics.get('distribution', {})
            total_trades = sum(distribution.values())
            
            if total_trades > 0:
                scalp_percentage = (distribution.get('under_1_hour', 0) / total_trades) * 100
                long_term_percentage = (distribution.get('over_7_days', 0) / total_trades) * 100
                
                if scalp_percentage > 40:
                    recommendations.append("High proportion of scalp trades - ensure proper risk management and quick decision making")
                
                if long_term_percentage > 30:
                    recommendations.append("Significant long-term positions - ensure adequate capital and patience")
            
            # General recommendations
            recommendations.extend([
                "Track holding periods consistently to identify optimal timeframes",
                "Consider market conditions when determining holding periods",
                "Use stop-loss orders appropriate for your intended holding period"
            ])
            
            return recommendations[:8]  # Limit to top 8 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _identify_duration_patterns(
        self,
        categorized_trades: Dict[str, List[TradingExecution]],
        duration_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify patterns in trading durations"""
        try:
            patterns = []
            
            # Most common duration
            distribution = duration_metrics.get('distribution', {})
            if distribution:
                max_category = max(distribution, key=distribution.get)
                patterns.append(f"Most common holding period: {max_category}")
            
            # Performance patterns
            performance_by_duration = {}
            for category, trades in categorized_trades.items():
                if trades:
                    returns = [t.pnl_percent or 0 for t in trades]
                    avg_return = sum(returns) / len(returns)
                    performance_by_duration[category] = avg_return
            
            if performance_by_duration:
                best_category = max(performance_by_duration, key=performance_by_duration.get)
                patterns.append(f"Best performing duration: {best_category}")
            
            # Time-based patterns
            time_performance = duration_metrics.get('time_performance', {})
            if time_performance:
                best_time_performance = max(
                    time_performance.items(), 
                    key=lambda x: x[1].get('avg_return', 0)
                )
                patterns.append(f"Best time-based performance: {best_time_performance[0]}")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            return []
    
    def _assess_duration_risk(
        self,
        duration_metrics: Dict[str, Any],
        performance_by_duration: Dict[str, Dict[str, Any]]
    ) -> str:
        """Assess overall risk based on duration analysis"""
        try:
            risk_factors = []
            
            # Check for very short holding periods
            avg_period = duration_metrics.get('avg_holding_period', 0)
            if avg_period < 1:
                risk_factors.append("very short holding periods")
            
            # Check for inconsistent performance
            scores = [
                data.get('performance_score', 0)
                for data in performance_by_duration.values()
                if data.get('trade_count', 0) > 0
            ]
            
            if scores and max(scores) - min(scores) > 40:
                risk_factors.append("inconsistent performance across durations")
            
            # Check for high volatility in short-term trades
            scalp_trades = performance_by_duration.get('SCALP', {})
            if scalp_trades.get('trade_count', 0) > 0:
                max_loss = scalp_trades.get('max_loss', 0)
                if max_loss < -2:
                    risk_factors.append("high losses in short-term trades")
            
            if not risk_factors:
                return "Low risk - duration strategy appears well-balanced"
            elif len(risk_factors) == 1:
                return f"Moderate risk - {risk_factors[0]}"
            else:
                return f"High risk - {', '.join(risk_factors)}"
                
        except Exception as e:
            logger.error(f"Error assessing duration risk: {e}")
            return "Unable to assess risk"
    
    def _find_optimal_duration(
        self,
        performance_by_duration: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Find the optimal duration category based on performance"""
        try:
            best_duration = None
            best_score = 0
            
            for category, metrics in performance_by_duration.items():
                if metrics.get('trade_count', 0) >= 3:  # Minimum trades for reliability
                    score = metrics.get('performance_score', 0)
                    if score > best_score:
                        best_score = score
                        best_duration = category
            
            if best_duration:
                best_metrics = performance_by_duration[best_duration]
                return {
                    'duration': best_duration,
                    'score': best_score,
                    'win_rate': best_metrics.get('win_rate', 0),
                    'avg_return': best_metrics.get('avg_return', 0),
                    'trade_count': best_metrics.get('trade_count', 0),
                    'recommendation': f"Focus on {best_duration} trades for optimal performance"
                }
            else:
                return {
                    'duration': None,
                    'score': 0,
                    'recommendation': "Insufficient data to determine optimal duration"
                }
                
        except Exception as e:
            logger.error(f"Error finding optimal duration: {e}")
            return {}
    
    def _analyze_holding_patterns(
        self,
        trades: List[TradingExecution]
    ) -> Dict[str, Any]:
        """Analyze holding patterns and behaviors"""
        try:
            if not trades:
                return {}
            
            # Time of day patterns
            entry_hours = [t.entry_time.hour for t in trades]
            exit_hours = [t.exit_time.hour for t in trades if t.exit_time]
            
            # Day of week patterns
            entry_days = [t.entry_time.weekday() for t in trades]
            exit_days = [t.exit_time.weekday() for t in trades if t.exit_time]
            
            # Holding period vs return correlation
            holding_returns = [
                (getattr(t, 'holding_period_hours', 0), t.pnl_percent or 0)
                for t in trades
            ]
            
            # Simple correlation calculation
            if len(holding_returns) > 1:
                avg_holding = sum(h for h, r in holding_returns) / len(holding_returns)
                avg_return = sum(r for h, r in holding_returns) / len(holding_returns)
                
                numerator = sum((h - avg_holding) * (r - avg_return) for h, r in holding_returns)
                holding_variance = sum((h - avg_holding) ** 2 for h, r in holding_returns)
                return_variance = sum((r - avg_return) ** 2 for h, r in holding_returns)
                
                correlation = numerator / ((holding_variance * return_variance) ** 0.5) if holding_variance * return_variance > 0 else 0
            else:
                correlation = 0
            
            return {
                'entry_hour_distribution': {str(hour): entry_hours.count(hour) for hour in set(entry_hours)},
                'exit_hour_distribution': {str(hour): exit_hours.count(hour) for hour in set(exit_hours)},
                'entry_day_distribution': {str(day): entry_days.count(day) for day in set(entry_days)},
                'exit_day_distribution': {str(day): exit_days.count(day) for day in set(exit_days)},
                'holding_return_correlation': correlation,
                'correlation_interpretation': self._interpret_correlation(correlation)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing holding patterns: {e}")
            return {}
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient"""
        if correlation > 0.7:
            return "Strong positive correlation - longer holding periods tend to have better returns"
        elif correlation > 0.3:
            return "Moderate positive correlation - longer holding periods generally help"
        elif correlation > -0.3:
            return "Weak correlation - holding period doesn't significantly affect returns"
        elif correlation > -0.7:
            return "Moderate negative correlation - shorter holding periods tend to be better"
        else:
            return "Strong negative correlation - shorter holding periods are clearly better"

# Create global instance
duration_analysis_service = DurationAnalysisService()
