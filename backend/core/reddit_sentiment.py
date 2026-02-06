"""
Reddit API Integration for Sentiment Analysis
Handles Reddit data collection from Indian stock market and investing subreddits
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import praw
from praw.exceptions import RedditAPIException, PRAWException
import aiohttp
import json
from .enhanced_sentiment_analysis import SentimentData, SentimentSource

logger = logging.getLogger(__name__)

class RedditSentimentCollector:
    """Reddit API integration for sentiment analysis"""
    
    def __init__(self, api_config: Dict[str, str]):
        """
        Initialize Reddit collector with API credentials
        
        Required config:
        - client_id: Reddit API client ID
        - client_secret: Reddit API client secret
        - user_agent: Reddit API user agent
        - username: Reddit username (optional)
        - password: Reddit password (optional)
        """
        self.api_config = api_config
        self.reddit = None
        self.rate_limit_info = {}
        
        # Indian stock market and investing subreddits
        self.default_subreddits = [
            'IndianStockMarket', 'investing', 'stocks', 'SecurityAnalysis',
            'ValueInvesting', 'FinanceIndia', 'CA_CFA_India', 'eupersonalfinance',
            'BSE', 'NSE', 'Trading', 'Daytrading', 'StockMarket'
        ]
    
    async def initialize(self) -> bool:
        """Initialize Reddit API client"""
        try:
            client_id = self.api_config.get('client_id')
            client_secret = self.api_config.get('client_secret')
            user_agent = self.api_config.get('user_agent', 'TraderAI_Sentiment_Analysis/1.0')
            
            if not client_id or not client_secret:
                logger.error("Reddit API credentials not provided")
                return False
            
            # Initialize Reddit instance (read-only mode)
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                read_only=True
            )
            
            # Test authentication
            try:
                # Try to access subreddit to test connection
                test_subreddit = self.reddit.subreddit('test')
                logger.info("Reddit API authentication successful")
                return True
                
            except Exception as e:
                logger.error(f"Reddit API authentication failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Reddit API initialization failed: {e}")
            return False
    
    async def collect_posts(self, subreddits: List[str] = None, 
                          time_filter: str = 'day', limit: int = 100) -> List[SentimentData]:
        """
        Collect posts from specified subreddits
        
        Args:
            subreddits: List of subreddit names (default: Indian stock market subreddits)
            time_filter: Time period ('hour', 'day', 'week', 'month', 'year', 'all')
            limit: Maximum number of posts per subreddit
        
        Returns:
            List of SentimentData objects
        """
        try:
            if not self.reddit:
                logger.error("Reddit client not initialized")
                return []
            
            subreddits = subreddits or self.default_subreddits
            all_posts = []
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get hot posts from the specified time period
                    posts = list(subreddit.hot(time_filter=time_filter, limit=limit))
                    
                    # Get comments for each post
                    for post in posts:
                        post_data = await self._process_post(post)
                        if post_data:
                            all_posts.append(post_data)
                    
                    logger.info(f"Collected {len(posts)} posts from r/{subreddit_name}")
                    
                except Exception as e:
                    logger.warning(f"Error collecting from r/{subreddit_name}: {e}")
                    continue
            
            logger.info(f"Total posts collected: {len(all_posts)}")
            return all_posts
            
        except Exception as e:
            logger.error(f"Error collecting Reddit posts: {e}")
            return []
    
    async def collect_search_results(self, query: str, subreddit: str = None, 
                                   time_filter: str = 'week', limit: int = 50) -> List[SentimentData]:
        """
        Collect posts based on search query
        
        Args:
            query: Search query string
            subreddit: Specific subreddit to search (optional)
            time_filter: Time period for search
            limit: Maximum number of results
        
        Returns:
            List of SentimentData objects
        """
        try:
            if not self.reddit:
                logger.error("Reddit client not initialized")
                return []
            
            # Build search parameters
            search_params = {
                'query': query,
                'sort': 'relevance',
                'syntax': 'lucene',
                'time_filter': time_filter,
                'limit': limit
            }
            
            # Search in specific subreddit or all subreddits
            if subreddit:
                search_subreddit = self.reddit.subreddit(subreddit)
                results = list(search_subreddit.search(**search_params))
            else:
                results = list(self.reddit.subreddit('all').search(**search_params))
            
            # Process search results
            all_posts = []
            for post in results:
                post_data = await self._process_post(post, max_comments=3)  # Fewer comments for search results
                if post_data:
                    all_posts.append(post_data)
            
            logger.info(f"Found {len(all_posts)} posts for query: {query}")
            return all_posts
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            return []
    
    async def collect_stock_specific_posts(self, symbols: List[str], 
                                         time_filter: str = 'day', limit: int = 25) -> List[SentimentData]:
        """
        Collect posts mentioning specific stock symbols
        
        Args:
            symbols: List of stock symbols to search for
            time_filter: Time period
            limit: Maximum posts per symbol
        
        Returns:
            List of SentimentData objects
        """
        try:
            all_posts = []
            
            for symbol in symbols:
                # Search for symbol mentions
                query = f'"{symbol}" OR "{symbol.upper()}" OR "{symbol.lower()}"'
                posts = await self.collect_search_results(
                    query=query,
                    subreddit='IndianStockMarket',
                    time_filter=time_filter,
                    limit=limit
                )
                
                # Add symbol metadata
                for post in posts:
                    post.metadata['stock_symbol'] = symbol.upper()
                
                all_posts.extend(posts)
            
            logger.info(f"Collected {len(all_posts)} stock-specific posts for symbols: {symbols}")
            return all_posts
            
        except Exception as e:
            logger.error(f"Error collecting stock-specific posts: {e}")
            return []
    
    async def _process_post(self, post, max_comments: int = 5) -> Optional[SentimentData]:
        """Process a single Reddit post and its comments"""
        try:
            # Get top comments
            comments = []
            try:
                post.comments.replace_more(limit=0)  # Remove "load more comments"
                for comment in post.comments.list()[:max_comments]:
                    if hasattr(comment, 'body') and comment.body:
                        comments.append({
                            'body': comment.body,
                            'score': comment.score,
                            'created_utc': comment.created_utc
                        })
            except Exception as e:
                logger.debug(f"Error getting comments for post {post.id}: {e}")
            
            # Clean post title and content
            title = self._clean_reddit_text(post.title)
            selftext = self._clean_reddit_text(getattr(post, 'selftext', ''))
            
            # Combine title and selftext for analysis
            combined_text = f"{title} {selftext}".strip()
            
            # Calculate engagement metrics
            upvotes = post.score
            comments_count = len(comments)
            total_engagement = upvotes + comments_count
            
            return SentimentData(
                source=SentimentSource.REDDIT,
                timestamp=datetime.fromtimestamp(post.created_utc),
                sentiment_score=0.0,  # Will be calculated by sentiment analyzer
                confidence=0.0,  # Will be calculated by sentiment analyzer
                volume=total_engagement,
                text=title[:200],  # Store title as sample text
                metadata={
                    'post_id': post.id,
                    'subreddit': post.subreddit.display_name,
                    'author': str(post.author) if post.author else '[deleted]',
                    'upvotes': upvotes,
                    'comments_count': comments_count,
                    'upvote_ratio': getattr(post, 'upvote_ratio', 0.0),
                    'title': title,
                    'selftext': selftext[:500],  # Store first 500 chars of content
                    'url': post.url,
                    'permalink': post.permalink,
                    'flair': getattr(post, 'link_flair_text', None),
                    'comments': comments[:3],  # Store top 3 comments
                    'total_awards_received': getattr(post, 'total_awards_received', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing Reddit post: {e}")
            return None
    
    def _clean_reddit_text(self, text: str) -> str:
        """Clean Reddit text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove Reddit markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        text = re.sub(r'^(>|\s>)\s*', '', text, flags=re.MULTILINE)  # Quotes
        
        # Remove subreddit references and user mentions
        text = re.sub(r'r/\w+', '', text)
        text = re.sub(r'u/\w+', '', text)
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def get_subreddit_stats(self, subreddit_name: str) -> Dict[str, Any]:
        """Get statistics for a specific subreddit"""
        try:
            if not self.reddit:
                return {}
            
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get subreddit information
            return {
                'name': subreddit.display_name,
                'subscribers': subreddit.subscribers,
                'active_users': subreddit.active_user_count,
                'created_utc': subreddit.created_utc,
                'description': subreddit.public_description,
                'over18': subreddit.over18,
                'quarantine': subreddit.quarantine
            }
            
        except Exception as e:
            logger.error(f"Error getting subreddit stats for {subreddit_name}: {e}")
            return {}

# Stock-specific search terms
STOCK_SEARCH_TERMS = {
    'RELIANCE': ['RELIANCE', 'RIL', 'Reliance Industries'],
    'TCS': ['TCS', 'Tata Consultancy Services', 'Tata Consultancy'],
    'INFY': ['INFY', 'Infosys', 'INFOSYS'],
    'HDFC': ['HDFC', 'HDFC Bank', 'HDFC Life'],
    'ICICI': ['ICICI', 'ICICI Bank', 'ICICIBANK'],
    'SBI': ['SBI', 'State Bank of India', 'SBIN'],
    'NIFTY': ['NIFTY', 'Nifty 50', 'Nifty50', 'NIFTY50'],
    'SENSEX': ['SENSEX', 'BSE Sensex', 'Sensex'],
    'BANKNIFTY': ['BANKNIFTY', 'Nifty Bank', 'Bank Nifty']
}

# Market-related search queries
MARKET_SEARCH_QUERIES = [
    'stock market india', 'share market', 'nifty prediction', 'sensex analysis',
    'trading strategy', 'investment advice', 'technical analysis', 'fundamental analysis',
    'inflation impact', 'rbi policy', 'gdp growth', 'market crash', 'bull market', 'bear market'
]

async def create_reddit_collector(api_config: Dict[str, str]) -> RedditSentimentCollector:
    """Create and initialize Reddit collector"""
    collector = RedditSentimentCollector(api_config)
    await collector.initialize()
    return collector
