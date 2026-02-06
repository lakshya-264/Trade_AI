"""
Enhanced News Sentiment Analysis
Multiple news sources integration: NewsAPI, GNews, Alpha Vantage, Google Finance RSS,
Economic Times, Livemint, Moneycontrol, Business Standard, Financial Express,
NDTV Profit, Bloomberg Quint, Reuters India, Yahoo Finance India
"""

import asyncio
import logging
import re
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
from .enhanced_sentiment_analysis import SentimentData, SentimentSource

logger = logging.getLogger(__name__)

class NewsSentimentCollector:
    """Enhanced news sentiment collection from multiple sources"""
    
    def __init__(self, api_config: Dict[str, str]):
        """
        Initialize news collector with API credentials
        
        Required config:
        - newsapi_key: NewsAPI.org API key
        - gnews_api_key: GNews API key (optional)
        - alpha_vantage_key: Alpha Vantage API key (optional)
        """
        self.api_config = api_config
        self.session = None
        
        # Indian financial news RSS feeds
        self.indian_news_feeds = {
            'economic_times': 'https://economictimes.indiatimes.com/rssfeeds/1977065503.cms',
            'livemint': 'https://www.livemint.com/rss/news',
            'moneycontrol': 'https://www.moneycontrol.com/rss/marketreports.xml',
            'business_standard': 'https://www.business-standard.com/rss/home_page_top_stories.rss',
            'financial_express': 'https://www.financialexpress.com/feed/',
            'ndtv_profit': 'https://feeds.feedburner.com/NdtvProfit-IBNLive',
            'bloomberg_quint': 'https://www.bloombergquint.com/feed/',
            'reuters_india': 'https://in.reuters.com/rssFeed/businessNews',
            'yahoo_finance': 'https://finance.yahoo.com/news/rssindex',
            'the_hindu_business': 'https://www.thehindubusinessline.com/rssfeeds/default.xml'
        }
        
        # Additional news sources for web scraping
        self.web_news_sources = {
            'moneycontrol_news': 'https://www.moneycontrol.com/news/business',
            'economic_times_markets': 'https://economictimes.indiatimes.com/markets',
            'livemint_markets': 'https://www.livemint.com/market',
            'valuepickr': 'https://www.valuepickr.com/',
            'safal_niveshak': 'https://safalniveshak.com/'
        }
        
        # Google News RSS endpoints (FREE, No Auth, Real-time!)
        self.google_news_rss = {
            'base_url': 'https://news.google.com/rss/search',
            'indian_markets': {
                'nifty': 'https://news.google.com/rss/search?q=NIFTY+India+stock+market',
                'sensex': 'https://news.google.com/rss/search?q=SENSEX+BSE+India',
                'reliance': 'https://news.google.com/rss/search?q=RELIANCE+India+stock',
                'tcs': 'https://news.google.com/rss/search?q=TCS+Tata+Consultancy+India',
                'infy': 'https://news.google.com/rss/search?q=Infosys+India+technology',
                'hdfc': 'https://news.google.com/rss/search?q=HDFC+Bank+India',
                'icici': 'https://news.google.com/rss/search?q=ICICI+Bank+India',
                'sbi': 'https://news.google.com/rss/search?q=SBI+State+Bank+India',
                'banking': 'https://news.google.com/rss/search?q=banking+India+finance',
                'rbi': 'https://news.google.com/rss/search?q=RBI+Reserve+Bank+India',
                'economy': 'https://news.google.com/rss/search?q=Indian+economy+GDP+inflation',
                'markets': 'https://news.google.com/rss/search?q=Indian+stock+markets+trading'
            }
        }
        
        # Indian financial news sources
        self.indian_news_sources = [
            'the-economic-times',
            'the-hindu',
            'livemint',
            'business-standard',
            'financial-express',
            'ndtv-profit',
            'moneycontrol',
            'zee-business',
            'cnbc-tv18',
            'bloomberg-quint'
        ]
        
        # RSS feeds for Indian financial news
        self.rss_feeds = [
            'https://economictimes.indiatimes.com/rssfeeds/1977021501.cms',
            'https://www.livemint.com/rss/news',
            'https://www.business-standard.com/rss/home_page_top_stories.rss',
            'https://www.financialexpress.com/feed/',
            'https://www.moneycontrol.com/rss/news.xml',
            'https://www.ndtv.com/rss/money.xml',
            'https://www.zeebiz.com/rss/companies.xml',
            'https://www.cnbc.com/id/100003114/device/rss/rss.xml'
        ]
        
        # Company and sector keywords
        self.company_keywords = {
            'RELIANCE': ['reliance industries', 'ril', 'mukesh ambani'],
            'TCS': ['tata consultancy services', 'tcs', 'tata group'],
            'INFY': ['infosys', 'infy', 'narayana murthy'],
            'HDFC': ['hdfc bank', 'hdfc', 'deepak parekh'],
            'ICICI': ['icici bank', 'icici', 'chanda kochhar'],
            'SBI': ['state bank of india', 'sbi', 'public sector banks'],
            'HUL': ['hindustan unilever', 'hul', 'fmcg'],
            'ITC': ['itc limited', 'itc', 'cigarettes', 'fmcg']
        }
        
        # Market and economic keywords
        self.market_keywords = [
            'nifty', 'sensex', 'bse', 'nse', 'stock market', 'share market',
            'inflation', 'gdp', 'rbi', 'repo rate', 'interest rates',
            'bull market', 'bear market', 'volatility', 'crude oil',
            'foreign investment', 'fii', 'dii', 'mutual funds', 'sip'
        ]
    
    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'TraderAI-Sentiment/1.0'}
            )
            logger.info("News collector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize news collector: {e}")
            return False
    
    async def collect_all_news(self, symbols: List[str] = None, 
                             hours_back: int = 24) -> List[SentimentData]:
        """
        Collect news from all available sources
        
        Args:
            symbols: Stock symbols to track
            hours_back: How many hours back to collect news
        
        Returns:
            List of SentimentData objects
        """
        try:
            all_news = []
            
            # Collect from different sources
            tasks = [
                self._collect_newsapi_news(symbols, hours_back),
                self._collect_gnews(symbols, hours_back),
                self._collect_alpha_vantage_news(symbols),
                self._collect_rss_news(hours_back),
                self.collect_indian_rss_news(symbols, hours_back),
                self.collect_web_scraped_news(symbols, hours_back),
                self.collect_google_news_rss(symbols, hours_back)  # 🎯 The gem!
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_news.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"News collection error: {result}")
            
            # Remove duplicates based on title similarity
            unique_news = self._remove_duplicates(all_news)
            
            logger.info(f"Collected {len(unique_news)} unique news articles")
            return unique_news
            
        except Exception as e:
            logger.error(f"Error collecting all news: {e}")
            return []
    
    async def _collect_newsapi_news(self, symbols: List[str] = None, 
                                  hours_back: int = 24) -> List[SentimentData]:
        """Collect news from NewsAPI.org"""
        try:
            api_key = self.api_config.get('newsapi_key')
            if not api_key:
                logger.warning("NewsAPI key not provided")
                return []
            
            # Build search query
            query = self._build_news_query(symbols)
            
            # Calculate date range
            from_date = datetime.utcnow() - timedelta(hours=hours_back)
            from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Make API request
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'domains': 'economictimes.indiatimes.com,livemint.com,business-standard.com',
                'language': 'en',
                'from': from_date_str,
                'sortBy': 'relevancy',
                'pageSize': 100,
                'apiKey': api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get('articles', [])
                    
                    sentiment_data = []
                    for article in articles:
                        sentiment_data.append(self._newsapi_to_sentiment_data(article))
                    
                    logger.info(f"NewsAPI: {len(sentiment_data)} articles")
                    return sentiment_data
                else:
                    logger.warning(f"NewsAPI error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error collecting NewsAPI news: {e}")
            return []
    
    async def _collect_gnews(self, symbols: List[str] = None, 
                           hours_back: int = 24) -> List[SentimentData]:
        """Collect news from GNews API"""
        try:
            api_key = self.api_config.get('gnews_api_key')
            if not api_key:
                logger.warning("GNews API key not provided")
                return []
            
            # Build search query
            query = self._build_news_query(symbols)
            
            # Make API request
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': query,
                'lang': 'en',
                'country': 'in',  # India
                'max': 50,
                'apikey': api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get('articles', [])
                    
                    sentiment_data = []
                    for article in articles:
                        sentiment_data.append(self._gnews_to_sentiment_data(article))
                    
                    logger.info(f"GNews: {len(sentiment_data)} articles")
                    return sentiment_data
                else:
                    logger.warning(f"GNews error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error collecting GNews: {e}")
            return []
    
    async def _collect_alpha_vantage_news(self, symbols: List[str] = None) -> List[SentimentData]:
        """Collect news from Alpha Vantage"""
        try:
            api_key = self.api_config.get('alpha_vantage_key')
            if not api_key:
                logger.warning("Alpha Vantage key not provided")
                return []
            
            sentiment_data = []
            
            # Collect news for each symbol
            for symbol in (symbols or ['RELIANCE.BSE', 'TCS.BSE']):
                url = 'https://www.alphavantage.co/query'
                params = {
                    'function': 'NEWS_SENTIMENT',
                    'tickers': symbol,
                    'apikey': api_key
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('feed', [])
                        
                        for article in articles:
                            sentiment_data.append(self._alphavantage_to_sentiment_data(article, symbol))
                    
                    await asyncio.sleep(12)  # Alpha Vantage rate limit: 5 calls per minute
            
            logger.info(f"Alpha Vantage: {len(sentiment_data)} articles")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error collecting Alpha Vantage news: {e}")
            return []
    
    async def _collect_rss_news(self, hours_back: int = 24) -> List[SentimentData]:
        """Collect news from RSS feeds"""
        try:
            sentiment_data = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            for feed_url in self.rss_feeds:
                try:
                    # Parse RSS feed
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries:
                        # Check if article is within time window
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                            if pub_date < cutoff_time:
                                continue
                        
                        sentiment_data.append(self._rss_to_sentiment_data(entry, feed_url))
                    
                except Exception as e:
                    logger.warning(f"Error parsing RSS feed {feed_url}: {e}")
                    continue
            
            logger.info(f"RSS feeds: {len(sentiment_data)} articles")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error collecting RSS news: {e}")
            return []
    
    def _build_news_query(self, symbols: List[str] = None) -> str:
        """Build news search query"""
        query_parts = []
        
        # Add symbols and company names
        if symbols:
            for symbol in symbols:
                if symbol in self.company_keywords:
                    query_parts.extend(self.company_keywords[symbol])
                query_parts.append(symbol)
        
        # Add market keywords
        query_parts.extend(self.market_keywords[:10])  # Limit keywords
        
        # Add India-specific terms
        query_parts.extend(['India', 'Indian', 'Mumbai', 'Delhi', 'Bangalore'])
        
        return ' OR '.join(query_parts[:20])  # Limit query length
    
    def _newsapi_to_sentiment_data(self, article: Dict) -> SentimentData:
        """Convert NewsAPI article to SentimentData"""
        return SentimentData(
            source=SentimentSource.NEWS,
            timestamp=self._parse_date(article.get('publishedAt')),
            sentiment_score=0.0,  # Will be calculated by sentiment analyzer
            confidence=0.0,  # Will be calculated by sentiment analyzer
            volume=1,  # Default volume
            text=article.get('title', ''),
            metadata={
                'source_name': article.get('source', {}).get('name', ''),
                'author': article.get('author', ''),
                'url': article.get('url', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'url_to_image': article.get('urlToImage', ''),
                'provider': 'NewsAPI'
            }
        )
    
    def _gnews_to_sentiment_data(self, article: Dict) -> SentimentData:
        """Convert GNews article to SentimentData"""
        return SentimentData(
            source=SentimentSource.NEWS,
            timestamp=self._parse_date(article.get('publishedAt')),
            sentiment_score=0.0,
            confidence=0.0,
            volume=1,
            text=article.get('title', ''),
            metadata={
                'source_name': article.get('source', {}).get('name', ''),
                'author': article.get('author', ''),
                'url': article.get('url', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'image': article.get('image', ''),
                'provider': 'GNews'
            }
        )
    
    def _alphavantage_to_sentiment_data(self, article: Dict, symbol: str) -> SentimentData:
        """Convert Alpha Vantage article to SentimentData"""
        # Alpha Vantage provides sentiment scores
        overall_sentiment = article.get('overall_sentiment_score', 0)
        
        return SentimentData(
            source=SentimentSource.NEWS,
            timestamp=self._parse_date(article.get('time_published')),
            sentiment_score=float(overall_sentiment) / 10,  # Convert to -1 to 1 scale
            confidence=abs(float(overall_sentiment)) / 10,
            volume=1,
            text=article.get('title', ''),
            metadata={
                'source_name': article.get('source', ''),
                'url': article.get('url', ''),
                'summary': article.get('summary', ''),
                'topics': article.get('topics', []),
                'ticker_sentiment': article.get('ticker_sentiment', []),
                'provider': 'AlphaVantage',
                'symbol': symbol
            }
        )
    
    def _rss_to_sentiment_data(self, entry: Dict, feed_url: str) -> SentimentData:
        """Convert RSS entry to SentimentData"""
        # Extract content from RSS entry
        content = ''
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if entry.content else ''
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # Clean HTML content
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text()
        
        return SentimentData(
            source=SentimentSource.NEWS,
            timestamp=self._parse_rss_date(entry),
            sentiment_score=0.0,
            confidence=0.0,
            volume=1,
            text=entry.get('title', ''),
            metadata={
                'source_name': entry.get('title', '').split(' - ')[-1] if ' - ' in entry.get('title', '') else 'RSS',
                'author': entry.get('author', ''),
                'url': entry.get('link', ''),
                'description': entry.get('summary', ''),
                'content': content[:500],  # First 500 chars
                'provider': 'RSS',
                'feed_url': feed_url
            }
        )
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                formats = [
                    '%Y-%m-%dT%H:%M:%S%z',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S',
                    '%a, %d %b %Y %H:%M:%S %Z'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                
                # Fallback to current time
                return datetime.utcnow()
                
            except:
                return datetime.utcnow()
    
    def _parse_rss_date(self, entry: Dict) -> datetime:
        """Parse RSS date"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        else:
            return datetime.utcnow()
    
    def _remove_duplicates(self, news_items: List[SentimentData]) -> List[SentimentData]:
        """Remove duplicate news based on title similarity"""
        seen_titles = set()
        unique_items = []
        
        for item in news_items:
            title = item.text.lower().strip()
            
            # Simple similarity check - exact title match
            if title not in seen_titles:
                seen_titles.add(title)
                unique_items.append(item)
        
        return unique_items
    
    async def calculate_news_relevance(self, sentiment_data: SentimentData, 
                                     symbols: List[str]) -> float:
        """Calculate relevance score for news article"""
        try:
            text = f"{sentiment_data.text} {sentiment_data.metadata.get('description', '')}".lower()
            
            relevance_score = 0.0
            
            # Check symbol mentions
            for symbol in symbols:
                if symbol.lower() in text:
                    relevance_score += 0.3
                
                # Check company name mentions
                if symbol in self.company_keywords:
                    for company_name in self.company_keywords[symbol]:
                        if company_name.lower() in text:
                            relevance_score += 0.2
            
            # Check market keywords
            market_mentions = sum(1 for keyword in self.market_keywords if keyword.lower() in text)
            relevance_score += min(market_mentions * 0.1, 0.3)
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.5  # Default relevance
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text
    
    def _is_within_time_window(self, entry, hours_back: int) -> bool:
        """Check if entry is within time window"""
        try:
            published = datetime.utcnow()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (ValueError, TypeError):
                    published = datetime.utcnow()
            elif hasattr(entry, 'published'):
                try:
                    from email.utils import parsedate_to_datetime
                    published = parsedate_to_datetime(entry.published)
                    if published is None:
                        published = datetime.utcnow()
                except:
                    published = datetime.utcnow()
            
            time_diff = datetime.utcnow() - published
            return time_diff <= timedelta(hours=hours_back)
        except:
            return True  # Include if we can't parse date
    
    async def collect_google_news_rss(self, symbols: List[str] = None,
                                     hours_back: int = 24) -> List[SentimentData]:
        """
        Collect news from Google News RSS (FREE, No Auth, Real-time!)
        
        This is the gem - Google News RSS provides:
        - Free access with no authentication
        - Near real-time news updates
        - Very scraper-friendly structure
        - Comprehensive news aggregation
        """
        try:
            all_news = []
            
            # Determine which queries to use
            queries_to_use = []
            
            if symbols:
                # Use symbol-specific queries
                for symbol in symbols:
                    symbol_lower = symbol.lower()
                    if symbol_lower in self.google_news_rss['indian_markets']:
                        queries_to_use.append((symbol_lower, self.google_news_rss['indian_markets'][symbol_lower]))
            
            # Always add general market queries
            general_queries = ['markets', 'economy', 'banking', 'rbi']
            for query_name in general_queries:
                queries_to_use.append((query_name, self.google_news_rss['indian_markets'][query_name]))
            
            logger.info(f"🔍 Collecting Google News RSS for {len(queries_to_use)} queries")
            
            for query_name, rss_url in queries_to_use:
                try:
                    logger.info(f"📰 Fetching Google News RSS for: {query_name}")
                    
                    # Parse RSS feed
                    feed = feedparser.parse(rss_url)
                    
                    if feed.bozo:
                        logger.warning(f"Malformed RSS feed for {query_name}")
                        continue
                    
                    for entry in feed.entries[:30]:  # Get up to 30 articles per query
                        try:
                            # Parse publication date
                            published = datetime.utcnow()
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                try:
                                    published = datetime(*entry.published_parsed[:6])
                                except (ValueError, TypeError):
                                    # Fallback to current time if parsing fails
                                    published = datetime.utcnow()
                            elif hasattr(entry, 'published'):
                                # Try to parse published string
                                try:
                                    from email.utils import parsedate_to_datetime
                                    published = parsedate_to_datetime(entry.published)
                                    if published is None:
                                        published = datetime.utcnow()
                                except:
                                    published = datetime.utcnow()
                            
                            # Check if within time window (more lenient filtering)
                            time_diff = datetime.utcnow() - published
                            if time_diff > timedelta(hours=hours_back):
                                continue
                            
                            # Extract content
                            title = entry.get('title', '')
                            summary = entry.get('summary', '')
                            link = entry.get('link', '')
                            
                            # Google News specific content extraction
                            content = f"{title}. {summary}"
                            
                            # Clean text
                            content = self._clean_text(content)
                            
                            # Skip very short content
                            if len(content) < 50:
                                continue
                            
                            # Calculate relevance (simple version for Google News)
                            relevance = 0.5  # Default relevance
                            
                            # Check symbol mentions
                            text_lower = content.lower()
                            for symbol in (symbols or []):
                                if symbol.lower() in text_lower:
                                    relevance += 0.3
                                
                                # Check company keywords
                                if symbol in self.company_keywords:
                                    for company_name in self.company_keywords[symbol]:
                                        if company_name.lower() in text_lower:
                                            relevance += 0.2
                            
                            # Check market keywords
                            market_mentions = sum(1 for keyword in self.market_keywords if keyword.lower() in text_lower)
                            relevance += min(market_mentions * 0.1, 0.3)
                            
                            relevance = min(relevance, 1.0)
                            
                            if relevance < 0.2:  # Lower threshold for Google News (broader coverage)
                                continue
                            
                            # Extract source from link or title
                            source_name = "Google News"
                            if link:
                                # Extract source name from URL
                                from urllib.parse import urlparse
                                domain = urlparse(link).netloc
                                if domain:
                                    source_name = f"Google News - {domain.replace('www.', '')}"
                            
                            # Create sentiment data
                            sentiment_data = SentimentData(
                                source=SentimentSource.NEWS,
                                timestamp=published,
                                sentiment_score=0.0,  # Will be calculated later
                                confidence=0.8,  # High confidence for Google News
                                volume=1,
                                text=content,
                                metadata={
                                    'source': 'google_news_rss',
                                    'query': query_name,
                                    'title': title,
                                    'url': link,
                                    'relevance_score': relevance,
                                    'google_news': True,
                                    'real_time': True
                                }
                            )
                            
                            all_news.append(sentiment_data)
                            
                        except Exception as e:
                            logger.debug(f"Error processing Google News entry: {e}")
                            continue
                    
                    logger.info(f"✅ Collected {len([e for e in feed.entries[:30] if self._is_within_time_window(e, hours_back)])} recent articles from Google News - {query_name}")
                    
                except Exception as e:
                    logger.error(f"Error collecting Google News RSS for {query_name}: {e}")
                    continue
            
            # Remove duplicates based on title similarity
            unique_news = []
            seen_titles = set()
            
            for news in all_news:
                title = news.metadata.get('title', '').lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_news.append(news)
            
            logger.info(f"🎯 Google News RSS collected {len(unique_news)} unique articles (removed {len(all_news) - len(unique_news)} duplicates)")
            return unique_news
            
        except Exception as e:
            logger.error(f"Error in Google News RSS collection: {e}")
            return []
    
    async def collect_indian_rss_news(self, symbols: List[str] = None, 
                                   hours_back: int = 24) -> List[SentimentData]:
        """Collect news from Indian financial RSS feeds"""
        try:
            all_news = []
            
            for source_name, feed_url in self.indian_news_feeds.items():
                try:
                    logger.info(f"Collecting RSS news from {source_name}")
                    
                    # Parse RSS feed
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:20]:  # Limit to 20 articles per source
                        # Parse publication date
                        published = datetime.utcnow()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published = datetime(*entry.published_parsed[:6])
                        
                        # Check if within time window
                        if datetime.utcnow() - published > timedelta(hours=hours_back):
                            continue
                        
                        # Extract content
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')
                        content = f"{title}. {summary}"
                        
                        # Clean text
                        content = self._clean_text(content)
                        
                        # Calculate relevance
                        relevance = self._calculate_relevance(content, symbols or [])
                        
                        if relevance < 0.3:  # Skip low relevance articles
                            continue
                        
                        # Create sentiment data
                        sentiment_data = SentimentData(
                            source=SentimentSource.NEWS,
                            timestamp=published,
                            sentiment_score=0.0,  # Will be calculated later
                            confidence=0.7,
                            volume=1,
                            text=content,
                            metadata={
                                'source': source_name,
                                'title': title,
                                'url': entry.get('link', ''),
                                'relevance_score': relevance,
                                'author': entry.get('author', ''),
                                'tags': entry.get('tags', [])
                            }
                        )
                        
                        all_news.append(sentiment_data)
                        
                except Exception as e:
                    logger.error(f"Error collecting from {source_name}: {e}")
                    continue
            
            logger.info(f"Collected {len(all_news)} articles from Indian RSS feeds")
            return all_news
            
        except Exception as e:
            logger.error(f"Error in RSS news collection: {e}")
            return []
    
    async def collect_web_scraped_news(self, symbols: List[str] = None,
                                     hours_back: int = 24) -> List[SentimentData]:
        """Collect news from web scraping sources"""
        try:
            all_news = []
            
            for source_name, base_url in self.web_news_sources.items():
                try:
                    logger.info(f"Scraping news from {source_name}")
                    
                    # Fetch the webpage
                    async with self.session.get(base_url) as response:
                        if response.status != 200:
                            continue
                        
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract articles based on common HTML patterns
                        articles = []
                        
                        if 'moneycontrol' in source_name:
                            articles = soup.find_all('article', class_='news_box')[:10]
                        elif 'economictimes' in source_name:
                            articles = soup.find_all('div', class_='eachStory')[:10]
                        elif 'livemint' in source_name:
                            articles = soup.find_all('article', class_='story-card')[:10]
                        else:
                            # Generic approach - find links with news-like patterns
                            articles = soup.find_all('a', href=re.compile(r'/news|/article|/story'))[:10]
                        
                        for article in articles:
                            try:
                                # Extract title and link
                                title_elem = article.find('h2') or article.find('h3') or article.find('a')
                                title = title_elem.get_text(strip=True) if title_elem else ''
                                link = article.find('a')['href'] if article.find('a') else ''
                                
                                # Extract summary
                                summary_elem = article.find('p') or article.find('div', class_='summary')
                                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                                
                                # Combine content
                                content = f"{title}. {summary}"
                                
                                if len(content) < 50:  # Skip very short content
                                    continue
                                
                                # Clean text
                                content = self._clean_text(content)
                                
                                # Calculate relevance
                                relevance = self._calculate_relevance(content, symbols or [])
                                
                                if relevance < 0.3:  # Skip low relevance articles
                                    continue
                                
                                # Create sentiment data
                                sentiment_data = SentimentData(
                                    source=SentimentSource.NEWS,
                                    timestamp=datetime.utcnow(),
                                    sentiment_score=0.0,  # Will be calculated later
                                    confidence=0.6,  # Lower confidence for scraped content
                                    volume=1,
                                    text=content,
                                    metadata={
                                        'source': source_name,
                                        'title': title,
                                        'url': link,
                                        'relevance_score': relevance,
                                        'scraped': True
                                    }
                                )
                                
                                all_news.append(sentiment_data)
                                
                            except Exception as e:
                                logger.debug(f"Error processing article: {e}")
                                continue
                        
                except Exception as e:
                    logger.error(f"Error scraping {source_name}: {e}")
                    continue
            
            logger.info(f"Scraped {len(all_news)} articles from web sources")
            return all_news
            
        except Exception as e:
            logger.error(f"Error in web scraping: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def create_news_collector(api_config: Dict[str, str]) -> NewsSentimentCollector:
    """Create and initialize news collector"""
    collector = NewsSentimentCollector(api_config)
    await collector.initialize()
    return collector
