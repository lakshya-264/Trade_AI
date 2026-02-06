"""
Forum Sentiment Analysis
Scrapes financial forums for market sentiment: Moneycontrol, ValuePickr
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import json
from .enhanced_sentiment_analysis import SentimentData, SentimentSource

logger = logging.getLogger(__name__)

class ForumSentimentCollector:
    """Forum sentiment collection from financial forums"""
    
    def __init__(self, config: Dict[str, str] = None):
        """
        Initialize forum collector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.session = None
        
        # Forum configurations
        self.forum_sources = {
            'moneycontrol_forum': {
                'base_url': 'https://www.moneycontrol.com/stocks/marketstats/marketcap/index.html',
                'discussion_url': 'https://www.moneycontrol.com/messageboard',
                'selectors': {
                    'topics': '.msg_list li',
                    'title': '.msg_title a',
                    'link': '.msg_title a',
                    'author': '.msg_user',
                    'timestamp': '.msg_time',
                    'content': '.msg_body',
                    'replies': '.msg_reply_count',
                    'views': '.msg_view_count'
                }
            },
            'valuepickr_forum': {
                'base_url': 'https://www.valuepickr.com/forum/',
                'discussion_url': 'https://www.valuepickr.com/forum/latest',
                'selectors': {
                    'topics': '.topic-list .topic',
                    'title': '.topic-title a',
                    'link': '.topic-title a',
                    'author': '.topic-author',
                    'timestamp': '.topic-date',
                    'content': '.topic-preview',
                    'replies': '.topic-replies',
                    'views': '.topic-views'
                }
            },
            'tradingview_forum': {
                'base_url': 'https://www.tradingview.com/markets/indices-ideas/',
                'selectors': {
                    'topics': '.tv-chart-widget-list__item',
                    'title': '.tv-chart-widget-list__item-title',
                    'link': 'a',
                    'author': '.tv-chart-widget-list__item-author',
                    'timestamp': '.tv-chart-widget-list__item-time',
                    'content': '.tv-chart-widget-list__item-description'
                }
            }
        }
        
        # Stock symbols and their common forum mentions
        self.stock_keywords = {
            'RELIANCE': ['reliance', 'ril', 'ambani', 'rIL', 'RIL'],
            'TCS': ['tcs', 'tata consultancy', 'tata', 'TCS', 'Tata Consultancy'],
            'INFY': ['infosys', 'infy', 'narayana murthy', 'INFY', 'Infosys'],
            'HDFC': ['hdfc bank', 'hdfc', 'deepak parekh', 'HDFC', 'HDFC Bank'],
            'ICICI': ['icici bank', 'icici', 'chanda kochhar', 'ICICI', 'ICICI Bank'],
            'SBI': ['state bank of india', 'sbi', 'public sector', 'SBI', 'State Bank'],
            'NIFTY': ['nifty', 'nifty 50', 'index', 'NIFTY', 'Nifty 50'],
            'SENSEX': ['sensex', 'bse sensex', 'index', 'SENSEX', 'BSE'],
            'BANKNIFTY': ['bank nifty', 'banknifty', 'banking index', 'BANKNIFTY']
        }
        
        # Sentiment indicators in forum posts
        self.bullish_keywords = [
            'buy', 'bullish', 'up', 'rise', 'gain', 'profit', 'target', 'upside',
            'strong', 'good', 'excellent', 'multibagger', 'breakout', 'rally',
            'momentum', 'growth', 'long', 'accumulate', 'hold', 'positive'
        ]
        
        self.bearish_keywords = [
            'sell', 'bearish', 'down', 'fall', 'loss', 'risk', 'downside',
            'weak', 'bad', 'poor', 'crash', 'correction', 'decline', 'drop',
            'short', 'avoid', 'exit', 'negative', 'concern', 'fear'
        ]
    
    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            logger.info("Forum collector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize forum collector: {e}")
            return False
    
    async def collect_moneycontrol_discussions(self, symbols: List[str] = None,
                                             max_posts: int = 50) -> List[SentimentData]:
        """Collect discussions from Moneycontrol forum"""
        try:
            all_posts = []
            forum_config = self.forum_sources['moneycontrol_forum']
            
            # Fetch latest discussions
            async with self.session.get(forum_config['discussion_url']) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Moneycontrol forum: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract discussion topics
                topics = soup.select('.msg_list li')[:max_posts]
                
                for topic in topics:
                    try:
                        # Extract title and link
                        title_elem = topic.select_one('.msg_title a')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        # Extract metadata
                        author_elem = topic.select_one('.msg_user')
                        author = author_elem.get_text(strip=True) if author_elem else 'Anonymous'
                        
                        time_elem = topic.select_one('.msg_time')
                        timestamp = self._parse_forum_time(time_elem.get_text(strip=True)) if time_elem else datetime.utcnow()
                        
                        # Extract engagement metrics
                        replies_elem = topic.select_one('.msg_reply_count')
                        replies = int(replies_elem.get_text(strip=True)) if replies_elem else 0
                        
                        views_elem = topic.select_one('.msg_view_count')
                        views = int(views_elem.get_text(strip=True)) if views_elem else 0
                        
                        # Calculate relevance based on symbols
                        relevance = self._calculate_forum_relevance(title, symbols)
                        
                        if relevance < 0.3:  # Skip low relevance posts
                            continue
                        
                        # Calculate sentiment based on title
                        sentiment_score = self._calculate_sentiment(title)
                        confidence = min(0.5 + (replies + views) / 100, 0.9)
                        
                        # Create sentiment data
                        data = SentimentData(
                            source=SentimentSource.FORUM,
                            timestamp=timestamp,
                            sentiment_score=sentiment_score,
                            confidence=min(confidence, 1.0),
                            volume=replies + 1,  # Use replies as volume
                            text=title,
                            metadata={
                                'source': 'moneycontrol_forum',
                                'author': author,
                                'title': title,
                                'url': link,
                                'replies': replies,
                                'views': views,
                                'relevance_score': relevance,
                                'forum_type': 'discussion'
                            }
                        )
                        
                        all_posts.append(data)
                        
                    except Exception as e:
                        logger.debug(f"Error processing Moneycontrol topic: {e}")
                        continue
            
            logger.info(f"Collected {len(all_posts)} posts from Moneycontrol forum")
            return all_posts
            
        except Exception as e:
            logger.error(f"Error collecting Moneycontrol discussions: {e}")
            return []
    
    async def collect_valuepickr_discussions(self, symbols: List[str] = None,
                                           max_posts: int = 50) -> List[SentimentData]:
        """Collect discussions from ValuePickr forum"""
        try:
            all_posts = []
            
            # Fetch latest discussions
            forum_config = self.forum_sources['valuepickr_forum']
            
            async with self.session.get(forum_config['discussion_url']) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch ValuePickr forum: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract discussion topics
                topics = soup.select('.topic-list .topic')[:max_posts]
                
                for topic in topics:
                    try:
                        # Extract title and link
                        title_elem = topic.select_one('.topic-title a')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        # Extract metadata
                        author_elem = topic.select_one('.topic-author')
                        author = author_elem.get_text(strip=True) if author_elem else 'Anonymous'
                        
                        time_elem = topic.select_one('.topic-date')
                        timestamp = self._parse_forum_time(time_elem.get_text(strip=True)) if time_elem else datetime.utcnow()
                        
                        # Extract engagement metrics
                        replies_elem = topic.select_one('.topic-replies')
                        replies = int(replies_elem.get_text(strip=True)) if replies_elem else 0
                        
                        views_elem = topic.select_one('.topic-views')
                        views = int(views_elem.get_text(strip=True)) if views_elem else 0
                        
                        # Calculate relevance
                        relevance = self._calculate_forum_relevance(title, symbols)
                        
                        if relevance < 0.3:  # Skip low relevance posts
                            continue
                        
                        # Calculate sentiment
                        sentiment_score = self._calculate_sentiment(title)
                        confidence = min(0.6 + (replies + views) / 200, 0.9)
                        
                        # Create sentiment data
                        sentiment_data = SentimentData(
                            source=SentimentSource.SOCIAL_MEDIA,
                            timestamp=timestamp,
                            sentiment_score=sentiment_score,
                            confidence=confidence,
                            volume=replies + 1,
                            text=title,
                            metadata={
                                'source': 'valuepickr_forum',
                                'author': author,
                                'title': title,
                                'url': link,
                                'replies': replies,
                                'views': views,
                                'relevance_score': relevance,
                                'forum_type': 'discussion'
                            }
                        )
                        
                        all_posts.append(data)
                        
                    except Exception as e:
                        logger.debug(f"Error processing ValuePickr topic: {e}")
                        continue
            
            logger.info(f"Collected {len(all_posts)} posts from ValuePickr forum")
            return all_posts
            
        except Exception as e:
            logger.error(f"Error collecting ValuePickr discussions: {e}")
            return []
    
    async def collect_all_forum_posts(self, symbols: List[str] = None,
                                    max_posts_per_source: int = 50) -> List[SentimentData]:
        """Collect posts from all configured forums"""
        try:
            all_posts = []
            
            # Collect from Moneycontrol
            moneycontrol_posts = await self.collect_moneycontrol_discussions(
                symbols, max_posts_per_source
            )
            all_posts.extend(moneycontrol_posts)
            
            # Collect from ValuePickr
            valuepickr_posts = await self.collect_valuepickr_discussions(
                symbols, max_posts_per_source
            )
            all_posts.extend(valuepickr_posts)
            
            # Sort by timestamp (most recent first)
            all_posts.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"Collected {len(all_posts)} total forum posts")
            return all_posts
            
        except Exception as e:
            logger.error(f"Error collecting forum posts: {e}")
            return []
    
    def _parse_forum_time(self, time_text: str) -> datetime:
        """Parse forum timestamp"""
        try:
            # Handle various time formats
            if 'ago' in time_text.lower():
                # "2 hours ago", "30 mins ago", etc.
                if 'hour' in time_text.lower():
                    hours = int(re.search(r'(\d+)', time_text).group(1))
                    return datetime.utcnow() - timedelta(hours=hours)
                elif 'min' in time_text.lower():
                    minutes = int(re.search(r'(\d+)', time_text).group(1))
                    return datetime.utcnow() - timedelta(minutes=minutes)
                elif 'day' in time_text.lower():
                    days = int(re.search(r'(\d+)', time_text).group(1))
                    return datetime.utcnow() - timedelta(days=days)
            else:
                # Try to parse as regular datetime
                return datetime.fromisoformat(time_text.replace('Last updated:', '').strip())
        except:
            return datetime.utcnow()
    
    def _calculate_forum_relevance(self, text: str, symbols: List[str]) -> float:
        """Calculate relevance score for forum post"""
        try:
            if not symbols:
                return 0.5
            
            text_lower = text.lower()
            relevance_score = 0.0
            
            # Check symbol mentions
            for symbol in symbols:
                if symbol.lower() in text_lower:
                    relevance_score += 0.4
                
                # Check company keywords
                if symbol in self.stock_keywords:
                    for keyword in self.stock_keywords[symbol]:
                        if keyword.lower() in text_lower:
                            relevance_score += 0.2
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating forum relevance: {e}")
            return 0.5
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score from text"""
        try:
            text_lower = text.lower()
            
            # Count bullish and bearish keywords
            bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
            bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
            
            # Calculate sentiment score
            if bullish_count > bearish_count:
                return min(bullish_count / (bullish_count + bearish_count), 0.8)
            elif bearish_count > bullish_count:
                return -min(bearish_count / (bullish_count + bearish_count), 0.8)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")
            return 0.0
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def create_forum_collector(config: Dict[str, str] = None) -> ForumSentimentCollector:
    """Create and initialize forum collector"""
    collector = ForumSentimentCollector(config)
    await collector.initialize()
    return collector
