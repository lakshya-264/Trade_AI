"""
Economic Indicators Tracking System
Collects and analyzes RBI policy, inflation (CPI), and GDP data for sentiment analysis
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import aiohttp
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import json
from .enhanced_sentiment_analysis import SentimentData, SentimentSource

logger = logging.getLogger(__name__)

class EconomicIndicatorsCollector:
    """Economic indicators data collection and sentiment analysis"""
    
    def __init__(self, api_config: Dict[str, str] = None):
        """
        Initialize economic indicators collector
        
        Optional config:
        - world_bank_api_key: World Bank API key
        - alpha_vantage_key: Alpha Vantage API key
        """
        self.api_config = api_config or {}
        self.session = None
        
        # RBI URLs and endpoints
        self.rbi_urls = {
            'policy_rates': 'https://rbi.org.in/scripts/BS_ViewBS.aspx?Id=1125',
            'monetary_policy': 'https://rbi.org.in/scripts/BS_ViewBS.aspx?Id=1124',
            'press_releases': 'https://rbi.org.in/scripts/BS_ViewBS.aspx?Id=976',
            'notifications': 'https://rbi.org.in/scripts/BS_ViewBS.aspx?Id=977'
        }
        
        # MOSPI (Ministry of Statistics and Programme Implementation) URLs
        self.mospi_urls = {
            'cpi': 'https://mospi.gov.in/web/cpi-and-inflation',
            'ipi': 'https://mospi.gov.in/web/industrial-production-index',
            'gdp': 'https://mospi.gov.in/web/gdp'
        }
        
        # World Bank API endpoints
        self.world_bank_endpoints = {
            'inflation': 'https://api.worldbank.org/v2/country/IND/indicator/FP.CPI.TOTL.ZG',
            'gdp_growth': 'https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.MKTP.KD.ZG',
            'interest_rate': 'https://api.worldbank.org/v2/country/IND/indicator/FR.INR.LEND'
        }
        
        # Economic sentiment keywords
        self.policy_keywords = {
            'accommodative': ['accommodative', 'supportive', 'dovish', 'stimulus', 'growth', 'expansion'],
            'tightening': ['tightening', 'hawkish', 'restrictive', 'inflation', 'curb', 'contain'],
            'neutral': ['neutral', 'balanced', 'steady', 'maintain', 'unchanged'],
            'positive': ['growth', 'recovery', 'expansion', 'strength', 'robust', 'momentum'],
            'negative': ['slowdown', 'contraction', 'weakness', 'concern', 'risk', 'volatility']
        }
    
    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'TraderAI-EconomicIndicators/1.0'}
            )
            logger.info("Economic indicators collector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize economic collector: {e}")
            return False
    
    async def collect_all_indicators(self) -> Dict[str, SentimentData]:
        """
        Collect all economic indicators
        
        Returns:
            Dictionary with SentimentData for each indicator type
        """
        try:
            indicators = {}
            
            # Collect RBI policy data
            rbi_data = await self.collect_rbi_policy_data()
            if rbi_data:
                indicators['rbi'] = rbi_data
            
            # Collect inflation data
            inflation_data = await self.collect_inflation_data()
            if inflation_data:
                indicators['inflation'] = inflation_data
            
            # Collect GDP data
            gdp_data = await self.collect_gdp_data()
            if gdp_data:
                indicators['gdp'] = gdp_data
            
            # Collect additional macro indicators
            interest_data = await self.collect_interest_rate_data()
            if interest_data:
                indicators['interest_rate'] = interest_data
            
            logger.info(f"Collected {len(indicators)} economic indicators")
            return indicators
            
        except Exception as e:
            logger.error(f"Error collecting economic indicators: {e}")
            return {}
    
    async def collect_rbi_policy_data(self) -> Optional[SentimentData]:
        """Collect RBI monetary policy data and analyze sentiment"""
        try:
            # Get current policy rates
            policy_rates = await self._fetch_rbi_policy_rates()
            
            # Get latest monetary policy statement
            policy_statement = await self._fetch_rbi_policy_statement()
            
            # Analyze sentiment
            sentiment_analysis = self._analyze_rbi_sentiment(policy_rates, policy_statement)
            
            return SentimentData(
                source=SentimentSource.RBI,
                timestamp=datetime.utcnow(),
                sentiment_score=sentiment_analysis['score'],
                confidence=sentiment_analysis['confidence'],
                volume=1,  # Policy announcements have high impact
                text=sentiment_analysis['summary'],
                metadata={
                    'repo_rate': policy_rates.get('repo_rate'),
                    'reverse_repo_rate': policy_rates.get('reverse_repo_rate'),
                    'msf_rate': policy_rates.get('msf_rate'),
                    'bank_rate': policy_rates.get('bank_rate'),
                    'crr': policy_rates.get('crr'),
                    'policy_stance': sentiment_analysis['stance'],
                    'policy_statement': policy_statement[:500] if policy_statement else '',
                    'last_meeting_date': policy_rates.get('last_meeting_date'),
                    'next_meeting_date': policy_rates.get('next_meeting_date')
                }
            )
            
        except Exception as e:
            logger.error(f"Error collecting RBI policy data: {e}")
            return None
    
    async def collect_inflation_data(self) -> Optional[SentimentData]:
        """Collect CPI inflation data and analyze sentiment"""
        try:
            # Get latest CPI data from MOSPI
            cpi_data = await self._fetch_cpi_data()
            
            # Get historical inflation trend
            inflation_trend = await self._fetch_inflation_trend()
            
            # Analyze inflation sentiment
            sentiment_analysis = self._analyze_inflation_sentiment(cpi_data, inflation_trend)
            
            return SentimentData(
                source=SentimentSource.INFLATION,
                timestamp=datetime.utcnow(),
                sentiment_score=sentiment_analysis['score'],
                confidence=sentiment_analysis['confidence'],
                volume=1,
                text=sentiment_analysis['summary'],
                metadata={
                    'cpi_headline': cpi_data.get('headline_inflation'),
                    'cpi_core': cpi_data.get('core_inflation'),
                    'cpi_food': cpi_data.get('food_inflation'),
                    'cpi_fuel': cpi_data.get('fuel_inflation'),
                    'inflation_trend': sentiment_analysis['trend'],
                    'month_over_month': cpi_data.get('mom_change'),
                    'year_over_year': cpi_data.get('yoy_change'),
                    'target_range': cpi_data.get('target_range', '2-6%'),
                    'data_period': cpi_data.get('period'),
                    'historical_avg': inflation_trend.get('average', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error collecting inflation data: {e}")
            return None
    
    async def collect_gdp_data(self) -> Optional[SentimentData]:
        """Collect GDP data and analyze sentiment"""
        try:
            # Get latest GDP data
            gdp_data = await self._fetch_gdp_data()
            
            # Get GDP growth trend
            gdp_trend = await self._fetch_gdp_trend()
            
            # Analyze GDP sentiment
            sentiment_analysis = self._analyze_gdp_sentiment(gdp_data, gdp_trend)
            
            return SentimentData(
                source=SentimentSource.GDP,
                timestamp=datetime.utcnow(),
                sentiment_score=sentiment_analysis['score'],
                confidence=sentiment_analysis['confidence'],
                volume=1,
                text=sentiment_analysis['summary'],
                metadata={
                    'gdp_growth_qoq': gdp_data.get('qoq_growth'),
                    'gdp_growth_yoy': gdp_data.get('yoy_growth'),
                    'gdp_constant_prices': gdp_data.get('gdp_constant'),
                    'gdp_current_prices': gdp_data.get('gdp_current'),
                    'sector_contributions': gdp_data.get('sector_contributions', {}),
                    'gdp_trend': sentiment_analysis['trend'],
                    'quarter': gdp_data.get('quarter'),
                    'fiscal_year': gdp_data.get('fiscal_year'),
                    'historical_avg': gdp_trend.get('average', 0),
                    'projection': gdp_data.get('projection')
                }
            )
            
        except Exception as e:
            logger.error(f"Error collecting GDP data: {e}")
            return None
    
    async def collect_interest_rate_data(self) -> Optional[SentimentData]:
        """Collect interest rate data"""
        try:
            # Get interest rate data from World Bank
            interest_data = await self._fetch_world_bank_data('interest_rate')
            
            if not interest_data:
                return None
            
            # Analyze interest rate sentiment
            latest_rate = interest_data.get('latest_value', 0)
            trend = interest_data.get('trend', 'stable')
            
            # Determine sentiment based on rate level and trend
            if latest_rate > 8:  # High interest rates
                sentiment_score = -0.3
                stance = 'restrictive'
            elif latest_rate < 4:  # Low interest rates
                sentiment_score = 0.3
                stance = 'accommodative'
            else:
                sentiment_score = 0.0
                stance = 'neutral'
            
            # Adjust for trend
            if trend == 'rising':
                sentiment_score -= 0.2
            elif trend == 'falling':
                sentiment_score += 0.2
            
            return SentimentData(
                source=SentimentSource.RBI,  # Group with RBI data
                timestamp=datetime.utcnow(),
                sentiment_score=np.clip(sentiment_score, -1, 1),
                confidence=0.7,
                volume=1,
                text=f"Interest rates at {latest_rate:.2f}% with {trend} trend",
                metadata={
                    'interest_rate': latest_rate,
                    'trend': trend,
                    'stance': stance,
                    'historical_data': interest_data.get('historical_values', [])[:10]
                }
            )
            
        except Exception as e:
            logger.error(f"Error collecting interest rate data: {e}")
            return None
    
    async def _fetch_rbi_policy_rates(self) -> Dict[str, Any]:
        """Fetch current RBI policy rates"""
        try:
            # This would typically scrape RBI website or use RBI API
            # For now, return mock data with recent RBI rates
            return {
                'repo_rate': 6.50,
                'reverse_repo_rate': 3.35,
                'msf_rate': 6.75,
                'bank_rate': 6.75,
                'crr': 4.50,
                'last_meeting_date': '2024-01-05',
                'next_meeting_date': '2024-02-08',
                'status': 'unchanged'
            }
            
        except Exception as e:
            logger.error(f"Error fetching RBI policy rates: {e}")
            return {}
    
    async def _fetch_rbi_policy_statement(self) -> str:
        """Fetch latest RBI monetary policy statement"""
        try:
            # This would scrape RBI website for latest policy statement
            # For now, return a mock statement
            return """
            The Monetary Policy Committee (MPC) decided to keep the policy repo rate unchanged at 6.50%. 
            The stance of monetary policy remains "withdrawal of accommodation". 
            The MPC remains focused on ensuring price stability while supporting growth.
            Inflation is expected to moderate in the coming quarters due to favorable base effects.
            """
            
        except Exception as e:
            logger.error(f"Error fetching RBI policy statement: {e}")
            return ""
    
    async def _fetch_cpi_data(self) -> Dict[str, Any]:
        """Fetch CPI inflation data"""
        try:
            # This would fetch from MOSPI website or API
            # For now, return mock data
            return {
                'headline_inflation': 5.69,
                'core_inflation': 4.12,
                'food_inflation': 8.70,
                'fuel_inflation': 1.34,
                'mom_change': 0.45,
                'yoy_change': 5.69,
                'target_range': '2-6%',
                'period': 'December 2023',
                'data_date': '2024-01-12'
            }
            
        except Exception as e:
            logger.error(f"Error fetching CPI data: {e}")
            return {}
    
    async def _fetch_inflation_trend(self) -> Dict[str, Any]:
        """Fetch historical inflation trend"""
        try:
            # This would fetch historical data
            # For now, return mock trend data
            return {
                'average': 4.8,
                'trend': 'moderating',
                'volatility': 0.3,
                'historical_values': [5.7, 5.4, 5.1, 4.8, 4.6, 4.9, 5.2, 5.6, 5.9, 5.7]
            }
            
        except Exception as e:
            logger.error(f"Error fetching inflation trend: {e}")
            return {}
    
    async def _fetch_gdp_data(self) -> Dict[str, Any]:
        """Fetch GDP data"""
        try:
            # This would fetch from MOSPI or World Bank
            # For now, return mock data
            return {
                'qoq_growth': 1.6,
                'yoy_growth': 8.4,
                'gdp_constant': 43.73,  # lakh crore
                'gdp_current': 71.72,   # lakh crore
                'sector_contributions': {
                    'agriculture': 18.4,
                    'industry': 25.3,
                    'services': 56.3
                },
                'quarter': 'Q2',
                'fiscal_year': '2023-24',
                'projection': 6.5
            }
            
        except Exception as e:
            logger.error(f"Error fetching GDP data: {e}")
            return {}
    
    async def _fetch_gdp_trend(self) -> Dict[str, Any]:
        """Fetch historical GDP trend"""
        try:
            return {
                'average': 6.2,
                'trend': 'recovering',
                'volatility': 0.8,
                'historical_values': [7.2, 6.8, 6.1, 5.2, 4.5, 6.1, 7.6, 8.2, 8.4, 7.8]
            }
            
        except Exception as e:
            logger.error(f"Error fetching GDP trend: {e}")
            return {}
    
    async def _fetch_world_bank_data(self, indicator: str) -> Dict[str, Any]:
        """Fetch data from World Bank API"""
        try:
            api_key = self.api_config.get('world_bank_api_key')
            url = self.world_bank_endpoints.get(indicator)
            
            if not url:
                return {}
            
            params = {
                'format': 'json',
                'per_page': 20,  # Get last 20 data points
                'date': '2020:2024'
            }
            
            if api_key:
                params['format'] = 'json'
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if len(data) > 1 and data[1]:
                        values = data[1]
                        latest_value = values[0]['value'] if values and values[0]['value'] else 0
                        
                        # Calculate trend
                        if len(values) >= 3:
                            recent_values = [v['value'] for v in values[:3] if v['value']]
                            if len(recent_values) >= 2:
                                if recent_values[0] > recent_values[1]:
                                    trend = 'rising'
                                elif recent_values[0] < recent_values[1]:
                                    trend = 'falling'
                                else:
                                    trend = 'stable'
                            else:
                                trend = 'stable'
                        else:
                            trend = 'stable'
                        
                        return {
                            'latest_value': latest_value,
                            'trend': trend,
                            'historical_values': values[:10]
                        }
                
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching World Bank data for {indicator}: {e}")
            return {}
    
    def _analyze_rbi_sentiment(self, policy_rates: Dict[str, Any], 
                             policy_statement: str) -> Dict[str, Any]:
        """Analyze RBI policy sentiment"""
        try:
            sentiment_score = 0.0
            confidence = 0.7
            stance = 'neutral'
            
            # Analyze policy statement for keywords
            statement_lower = policy_statement.lower()
            
            # Check for policy stance keywords
            accommodative_count = sum(1 for word in self.policy_keywords['accommodative'] 
                                    if word in statement_lower)
            tightening_count = sum(1 for word in self.policy_keywords['tightening'] 
                                  if word in statement_lower)
            neutral_count = sum(1 for word in self.policy_keywords['neutral'] 
                               if word in statement_lower)
            
            # Determine stance
            if accommodative_count > tightening_count and accommodative_count > neutral_count:
                stance = 'accommodative'
                sentiment_score = 0.3
            elif tightening_count > accommodative_count and tightening_count > neutral_count:
                stance = 'tightening'
                sentiment_score = -0.3
            else:
                stance = 'neutral'
                sentiment_score = 0.0
            
            # Adjust based on repo rate level
            repo_rate = policy_rates.get('repo_rate', 6.5)
            if repo_rate > 7.0:
                sentiment_score -= 0.2  # High rates are restrictive
            elif repo_rate < 5.0:
                sentiment_score += 0.2  # Low rates are accommodative
            
            # Check for positive/negative economic terms
            positive_count = sum(1 for word in self.policy_keywords['positive'] 
                               if word in statement_lower)
            negative_count = sum(1 for word in self.policy_keywords['negative'] 
                               if word in statement_lower)
            
            if positive_count > negative_count:
                sentiment_score += 0.1
            elif negative_count > positive_count:
                sentiment_score -= 0.1
            
            # Generate summary
            summary = f"RBI maintains repo rate at {repo_rate}%. Policy stance is {stance}."
            
            return {
                'score': np.clip(sentiment_score, -1, 1),
                'confidence': confidence,
                'stance': stance,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing RBI sentiment: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'stance': 'neutral', 'summary': ''}
    
    def _analyze_inflation_sentiment(self, cpi_data: Dict[str, Any], 
                                   inflation_trend: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inflation sentiment"""
        try:
            headline_inflation = cpi_data.get('headline_inflation', 0)
            target_range = cpi_data.get('target_range', '2-6%')
            trend = inflation_trend.get('trend', 'stable')
            
            sentiment_score = 0.0
            confidence = 0.8
            
            # Check if inflation is within target range
            if 2 <= headline_inflation <= 6:
                sentiment_score += 0.2  # Within target is positive
            elif headline_inflation > 8:
                sentiment_score -= 0.4  # High inflation is negative
            elif headline_inflation < 2:
                sentiment_score -= 0.2  # Very low inflation can be concerning
            
            # Adjust for trend
            if trend == 'moderating' or trend == 'falling':
                sentiment_score += 0.2
            elif trend == 'accelerating' or trend == 'rising':
                sentiment_score -= 0.2
            
            # Check core inflation
            core_inflation = cpi_data.get('core_inflation', 0)
            if core_inflation > 5:
                sentiment_score -= 0.1
            
            # Generate summary
            summary = f"CPI at {headline_inflation}%, {trend} trend. Target range: {target_range}."
            
            return {
                'score': np.clip(sentiment_score, -1, 1),
                'confidence': confidence,
                'trend': trend,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing inflation sentiment: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'trend': 'stable', 'summary': ''}
    
    def _analyze_gdp_sentiment(self, gdp_data: Dict[str, Any], 
                             gdp_trend: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GDP sentiment"""
        try:
            yoy_growth = gdp_data.get('yoy_growth', 0)
            qoq_growth = gdp_data.get('qoq_growth', 0)
            trend = gdp_trend.get('trend', 'stable')
            historical_avg = gdp_trend.get('average', 6.0)
            
            sentiment_score = 0.0
            confidence = 0.8
            
            # Compare YoY growth with historical average
            if yoy_growth > historical_avg + 1:
                sentiment_score += 0.3  # Above average growth
            elif yoy_growth > historical_avg:
                sentiment_score += 0.1  # Slightly above average
            elif yoy_growth < historical_avg - 2:
                sentiment_score -= 0.3  # Below average growth
            elif yoy_growth < historical_avg:
                sentiment_score -= 0.1  # Slightly below average
            
            # Check for recession (negative growth)
            if yoy_growth < 0:
                sentiment_score -= 0.5  # Recession is very negative
            elif yoy_growth < 3:
                sentiment_score -= 0.2  # Slow growth
            
            # Adjust for trend
            if trend == 'recovering' or trend == 'accelerating':
                sentiment_score += 0.1
            elif trend == 'slowing' or trend == 'contracting':
                sentiment_score -= 0.1
            
            # Check quarterly momentum
            if qoq_growth > 2:
                sentiment_score += 0.1
            elif qoq_growth < 0:
                sentiment_score -= 0.1
            
            # Generate summary
            summary = f"GDP growth {yoy_growth}% YoY, {qoq_growth}% QoQ. Trend: {trend}."
            
            return {
                'score': np.clip(sentiment_score, -1, 1),
                'confidence': confidence,
                'trend': trend,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing GDP sentiment: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'trend': 'stable', 'summary': ''}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def create_economic_collector(api_config: Dict[str, str] = None) -> EconomicIndicatorsCollector:
    """Create and initialize economic indicators collector"""
    collector = EconomicIndicatorsCollector(api_config)
    await collector.initialize()
    return collector
