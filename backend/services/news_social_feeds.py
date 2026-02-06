"""
Real-Time News and Social Media Feeds Service
Handles news, social media, and alternative data ingestion
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import aiohttp
import json
import re
from collections import deque
import feedparser
import tweepy
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class NewsSocialFeedsIngestion:
    def __init__(self):
        self.news_data = {}
        self.social_data = {}
        self.sentiment_scores = {}
        
        # Data sources
        self.news_sources = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://feeds.reuters.com/news/wealth",
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.moneycontrol.com/rss/business.xml",
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
        ]
        
        self.social_platforms = ["twitter", "reddit", "telegram", "discord"]
        
        # Data storage
        self.data_buffer_size = 5000
        self.update_interval = 60  # 1 minute
        
        # Sentiment analysis
        self.sia = SentimentIntensityAnalyzer()
        
        # Keywords for filtering
        self.market_keywords = [
            "stock", "market", "trading", "investment", "finance", "economy",
            "nse", "bse", "sensex", "nifty", "bull", "bear", "rally", "crash",
            "earnings", "revenue", "profit", "loss", "dividend", "ipo", "merger"
        ]
        
        # Initialize NLTK data
        try:
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
        except:
            pass
    
    async def start_feeds_monitoring(self):
        """Start monitoring news and social media feeds"""
        try:
            while True:
                await self._collect_all_feeds()
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"Error in feeds monitoring: {e}")
    
    async def _collect_all_feeds(self):
        """Collect data from all feeds"""
        try:
            # Collect news
            news_task = asyncio.create_task(self._collect_news_feeds())
            
            # Collect social media
            social_task = asyncio.create_task(self._collect_social_feeds())
            
            # Wait for both to complete
            await asyncio.gather(news_task, social_task)
            
        except Exception as e:
            logger.error(f"Error collecting feeds: {e}")
    
    async def _collect_news_feeds(self):
        """Collect news from RSS feeds"""
        try:
            for source in self.news_sources:
                try:
                    news_items = await self._parse_rss_feed(source)
                    for item in news_items:
                        await self._process_news_item(item)
                except Exception as e:
                    logger.error(f"Error collecting from {source}: {e}")
                    
        except Exception as e:
            logger.error(f"Error collecting news feeds: {e}")
    
    async def _collect_social_feeds(self):
        """Collect social media data"""
        try:
            # Twitter data
            twitter_data = await self._collect_twitter_data()
            for item in twitter_data:
                await self._process_social_item(item, "twitter")
            
            # Reddit data
            reddit_data = await self._collect_reddit_data()
            for item in reddit_data:
                await self._process_social_item(item, "reddit")
            
            # Mock other platforms
            telegram_data = await self._collect_telegram_data()
            for item in telegram_data:
                await self._process_social_item(item, "telegram")
                
        except Exception as e:
            logger.error(f"Error collecting social feeds: {e}")
    
    async def _parse_rss_feed(self, url: str) -> List[Dict]:
        """Parse RSS feed and extract news items"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        news_items = []
                        for entry in feed.entries[:20]:  # Limit to 20 items
                            item = {
                                "title": entry.get("title", ""),
                                "summary": entry.get("summary", ""),
                                "link": entry.get("link", ""),
                                "published": entry.get("published", ""),
                                "source": url,
                                "timestamp": datetime.now()
                            }
                            news_items.append(item)
                        
                        return news_items
                        
        except Exception as e:
            logger.error(f"Error parsing RSS feed {url}: {e}")
        
        return []
    
    async def _collect_twitter_data(self) -> List[Dict]:
        """Collect Twitter data (mock implementation)"""
        try:
            # Mock Twitter data - in production, use actual Twitter API
            mock_tweets = []
            for i in range(10):
                tweet = {
                    "id": f"tweet_{i}",
                    "text": f"Mock tweet about market trends {i}",
                    "author": f"trader_{i}",
                    "created_at": datetime.now(),
                    "retweet_count": np.random.randint(0, 100),
                    "favorite_count": np.random.randint(0, 500),
                    "hashtags": ["#trading", "#stocks", "#nse"],
                    "platform": "twitter"
                }
                mock_tweets.append(tweet)
            
            return mock_tweets
            
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
            return []
    
    async def _collect_reddit_data(self) -> List[Dict]:
        """Collect Reddit data (mock implementation)"""
        try:
            # Mock Reddit data - in production, use Reddit API
            mock_posts = []
            for i in range(10):
                post = {
                    "id": f"reddit_{i}",
                    "title": f"Market discussion {i}",
                    "text": f"Mock Reddit post about trading strategies {i}",
                    "author": f"redditor_{i}",
                    "subreddit": "investing",
                    "score": np.random.randint(0, 1000),
                    "num_comments": np.random.randint(0, 100),
                    "created_at": datetime.now(),
                    "platform": "reddit"
                }
                mock_posts.append(post)
            
            return mock_posts
            
        except Exception as e:
            logger.error(f"Error collecting Reddit data: {e}")
            return []
    
    async def _collect_telegram_data(self) -> List[Dict]:
        """Collect Telegram data (mock implementation)"""
        try:
            # Mock Telegram data - in production, use Telegram API
            mock_messages = []
            for i in range(10):
                message = {
                    "id": f"telegram_{i}",
                    "text": f"Telegram message about market analysis {i}",
                    "channel": f"trading_channel_{i}",
                    "author": f"telegram_user_{i}",
                    "created_at": datetime.now(),
                    "platform": "telegram"
                }
                mock_messages.append(message)
            
            return mock_messages
            
        except Exception as e:
            logger.error(f"Error collecting Telegram data: {e}")
            return []
    
    async def _process_news_item(self, item: Dict):
        """Process and store news item"""
        try:
            # Extract symbols mentioned
            symbols = self._extract_symbols(item["title"] + " " + item["summary"])
            
            # Calculate sentiment
            sentiment = self._calculate_sentiment(item["title"] + " " + item["summary"])
            
            # Add processed data
            processed_item = {
                **item,
                "symbols": symbols,
                "sentiment": sentiment,
                "relevance_score": self._calculate_relevance(item["title"] + " " + item["summary"])
            }
            
            # Store by symbol
            for symbol in symbols:
                if symbol not in self.news_data:
                    self.news_data[symbol] = deque(maxlen=self.data_buffer_size)
                
                self.news_data[symbol].append(processed_item)
            
            # Store general news
            if "GENERAL" not in self.news_data:
                self.news_data["GENERAL"] = deque(maxlen=self.data_buffer_size)
            
            self.news_data["GENERAL"].append(processed_item)
            
        except Exception as e:
            logger.error(f"Error processing news item: {e}")
    
    async def _process_social_item(self, item: Dict, platform: str):
        """Process and store social media item"""
        try:
            # Extract symbols mentioned
            symbols = self._extract_symbols(item.get("text", "") + " " + item.get("title", ""))
            
            # Calculate sentiment
            text = item.get("text", "") + " " + item.get("title", "")
            sentiment = self._calculate_sentiment(text)
            
            # Add processed data
            processed_item = {
                **item,
                "symbols": symbols,
                "sentiment": sentiment,
                "relevance_score": self._calculate_relevance(text),
                "platform": platform
            }
            
            # Store by symbol
            for symbol in symbols:
                if symbol not in self.social_data:
                    self.social_data[symbol] = deque(maxlen=self.data_buffer_size)
                
                self.social_data[symbol].append(processed_item)
            
            # Store general social data
            if "GENERAL" not in self.social_data:
                self.social_data["GENERAL"] = deque(maxlen=self.data_buffer_size)
            
            self.social_data["GENERAL"].append(processed_item)
            
        except Exception as e:
            logger.error(f"Error processing social item: {e}")
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        try:
            symbols = []
            text_upper = text.upper()
            
            # Common Indian stock symbols
            indian_symbols = [
                "RELIANCE", "TCS", "HDFC", "INFY", "HINDUNILVR", "ITC", "KOTAKBANK",
                "BHARTIARTL", "LT", "SBIN", "ASIANPAINT", "MARUTI", "AXISBANK",
                "NESTLEIND", "ULTRACEMCO", "TITAN", "WIPRO", "ONGC", "POWERGRID",
                "NTPC", "TECHM", "TATAMOTORS", "SUNPHARMA", "BAJFINANCE", "HCLTECH"
            ]
            
            for symbol in indian_symbols:
                if symbol in text_upper:
                    symbols.append(symbol)
            
            # Extract NSE symbols (pattern: 3-20 characters, all caps)
            nse_pattern = r'\b[A-Z]{3,20}\b'
            potential_symbols = re.findall(nse_pattern, text_upper)
            
            for symbol in potential_symbols:
                if len(symbol) >= 3 and symbol not in symbols:
                    symbols.append(symbol)
            
            return symbols[:5]  # Limit to 5 symbols per item
            
        except Exception as e:
            logger.error(f"Error extracting symbols: {e}")
            return []
    
    def _calculate_sentiment(self, text: str) -> Dict:
        """Calculate sentiment score for text"""
        try:
            # TextBlob sentiment
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # VADER sentiment
            vader_scores = self.sia.polarity_scores(text)
            
            # Combined sentiment score
            combined_score = (polarity + vader_scores['compound']) / 2
            
            # Classify sentiment
            if combined_score > 0.1:
                sentiment_class = "POSITIVE"
            elif combined_score < -0.1:
                sentiment_class = "NEGATIVE"
            else:
                sentiment_class = "NEUTRAL"
            
            return {
                "score": combined_score,
                "class": sentiment_class,
                "polarity": polarity,
                "subjectivity": subjectivity,
                "vader_positive": vader_scores['pos'],
                "vader_negative": vader_scores['neg'],
                "vader_neutral": vader_scores['neu'],
                "vader_compound": vader_scores['compound']
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")
            return {"score": 0, "class": "NEUTRAL"}
    
    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score based on market keywords"""
        try:
            text_lower = text.lower()
            keyword_matches = sum(1 for keyword in self.market_keywords if keyword in text_lower)
            relevance_score = min(keyword_matches / len(self.market_keywords), 1.0)
            return relevance_score
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.0
    
    def get_news_sentiment(self, symbol: str, hours: int = 24) -> Dict:
        """Get news sentiment for a symbol over specified hours"""
        try:
            if symbol not in self.news_data:
                return {"sentiment": 0, "count": 0, "confidence": 0}
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_news = [
                item for item in self.news_data[symbol]
                if item["timestamp"] >= cutoff_time
            ]
            
            if not recent_news:
                return {"sentiment": 0, "count": 0, "confidence": 0}
            
            # Calculate weighted sentiment
            total_sentiment = 0
            total_weight = 0
            
            for item in recent_news:
                sentiment_score = item["sentiment"]["score"]
                relevance_weight = item["relevance_score"]
                total_sentiment += sentiment_score * relevance_weight
                total_weight += relevance_weight
            
            avg_sentiment = total_sentiment / total_weight if total_weight > 0 else 0
            confidence = min(len(recent_news) / 10, 1.0)  # Confidence based on data volume
            
            return {
                "sentiment": avg_sentiment,
                "count": len(recent_news),
                "confidence": confidence,
                "positive_count": sum(1 for item in recent_news if item["sentiment"]["class"] == "POSITIVE"),
                "negative_count": sum(1 for item in recent_news if item["sentiment"]["class"] == "NEGATIVE"),
                "neutral_count": sum(1 for item in recent_news if item["sentiment"]["class"] == "NEUTRAL")
            }
            
        except Exception as e:
            logger.error(f"Error getting news sentiment for {symbol}: {e}")
            return {"sentiment": 0, "count": 0, "confidence": 0}
    
    def get_social_sentiment(self, symbol: str, hours: int = 24) -> Dict:
        """Get social media sentiment for a symbol over specified hours"""
        try:
            if symbol not in self.social_data:
                return {"sentiment": 0, "count": 0, "confidence": 0}
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_social = [
                item for item in self.social_data[symbol]
                if item["timestamp"] >= cutoff_time
            ]
            
            if not recent_social:
                return {"sentiment": 0, "count": 0, "confidence": 0}
            
            # Calculate weighted sentiment by platform
            platform_weights = {"twitter": 1.0, "reddit": 0.8, "telegram": 0.6, "discord": 0.7}
            
            total_sentiment = 0
            total_weight = 0
            
            for item in recent_social:
                sentiment_score = item["sentiment"]["score"]
                relevance_weight = item["relevance_score"]
                platform_weight = platform_weights.get(item.get("platform", "twitter"), 1.0)
                
                weight = relevance_weight * platform_weight
                total_sentiment += sentiment_score * weight
                total_weight += weight
            
            avg_sentiment = total_sentiment / total_weight if total_weight > 0 else 0
            confidence = min(len(recent_social) / 20, 1.0)  # Confidence based on data volume
            
            return {
                "sentiment": avg_sentiment,
                "count": len(recent_social),
                "confidence": confidence,
                "platform_breakdown": self._get_platform_breakdown(recent_social)
            }
            
        except Exception as e:
            logger.error(f"Error getting social sentiment for {symbol}: {e}")
            return {"sentiment": 0, "count": 0, "confidence": 0}
    
    def _get_platform_breakdown(self, social_items: List[Dict]) -> Dict:
        """Get sentiment breakdown by platform"""
        try:
            platform_data = {}
            
            for item in social_items:
                platform = item.get("platform", "unknown")
                if platform not in platform_data:
                    platform_data[platform] = {
                        "count": 0,
                        "total_sentiment": 0,
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0
                    }
                
                platform_data[platform]["count"] += 1
                platform_data[platform]["total_sentiment"] += item["sentiment"]["score"]
                
                sentiment_class = item["sentiment"]["class"]
                if sentiment_class == "POSITIVE":
                    platform_data[platform]["positive"] += 1
                elif sentiment_class == "NEGATIVE":
                    platform_data[platform]["negative"] += 1
                else:
                    platform_data[platform]["neutral"] += 1
            
            # Calculate averages
            for platform in platform_data:
                count = platform_data[platform]["count"]
                if count > 0:
                    platform_data[platform]["avg_sentiment"] = platform_data[platform]["total_sentiment"] / count
                else:
                    platform_data[platform]["avg_sentiment"] = 0
            
            return platform_data
            
        except Exception as e:
            logger.error(f"Error getting platform breakdown: {e}")
            return {}
    
    def get_combined_sentiment(self, symbol: str, hours: int = 24) -> Dict:
        """Get combined news and social sentiment"""
        try:
            news_sentiment = self.get_news_sentiment(symbol, hours)
            social_sentiment = self.get_social_sentiment(symbol, hours)
            
            # Weighted combination (news: 60%, social: 40%)
            news_weight = 0.6
            social_weight = 0.4
            
            combined_sentiment = (
                news_sentiment["sentiment"] * news_weight * news_sentiment["confidence"] +
                social_sentiment["sentiment"] * social_weight * social_sentiment["confidence"]
            ) / (news_weight * news_sentiment["confidence"] + social_weight * social_sentiment["confidence"] + 1e-8)
            
            combined_confidence = (
                news_sentiment["confidence"] * news_weight +
                social_sentiment["confidence"] * social_weight
            )
            
            return {
                "combined_sentiment": combined_sentiment,
                "combined_confidence": combined_confidence,
                "news_sentiment": news_sentiment,
                "social_sentiment": social_sentiment,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting combined sentiment: {e}")
            return {"combined_sentiment": 0, "combined_confidence": 0}
    
    def get_trending_topics(self, hours: int = 24) -> List[Dict]:
        """Get trending topics from news and social media"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Collect all recent items
            all_items = []
            
            for symbol_data in self.news_data.values():
                all_items.extend([
                    item for item in symbol_data
                    if item["timestamp"] >= cutoff_time
                ])
            
            for symbol_data in self.social_data.values():
                all_items.extend([
                    item for item in symbol_data
                    if item["timestamp"] >= cutoff_time
                ])
            
            # Count symbol mentions
            symbol_counts = {}
            for item in all_items:
                for symbol in item.get("symbols", []):
                    if symbol not in symbol_counts:
                        symbol_counts[symbol] = 0
                    symbol_counts[symbol] += 1
            
            # Sort by count and return top topics
            trending = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {"symbol": symbol, "mention_count": count, "trend_score": count / len(all_items)}
                for symbol, count in trending[:20]
            ]
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []
