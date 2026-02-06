"""
Enhanced Sentiment Analysis Service
Comprehensive sentiment analysis with multiple data sources:
- Twitter (X) API
- Reddit API  
- News APIs (NewsAPI, GNews, Alpha Vantage)
- Economic Indicators (RBI, Inflation, GDP)
- ML Model Integration (FinBERT, VADER, XGBoost, LSTM)
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import aiohttp
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# ML and NLP imports
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    import tweepy
    import praw
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using fallback implementations")

logger = logging.getLogger(__name__)

class SentimentSource(Enum):
    REDDIT = "reddit"
    NEWS = "news"
    FORUM = "forum"
    RBI = "rbi"
    INFLATION = "inflation"
    GDP = "gdp"

@dataclass
class SentimentData:
    """Data structure for sentiment analysis results"""
    source: SentimentSource
    timestamp: datetime
    sentiment_score: float  # -1 to 1
    confidence: float  # 0 to 1
    volume: int  # engagement/volume metric
    text: str  # original text (sample)
    metadata: Dict[str, Any]

class EnhancedSentimentAnalyzer:
    """Enhanced sentiment analysis with multiple data sources and ML models"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.ml_available = ML_AVAILABLE
        
        # Initialize ML models
        self._init_ml_models()
        
        # API clients (initialized lazily)
        self._twitter_client = None
        self._reddit_client = None
        self._news_session = None
        
        # Data storage
        self.sentiment_cache = {}
        self.feature_store = pd.DataFrame()
        
        # Economic indicators cache
        self.economic_cache = {}
        
        logger.info("Enhanced Sentiment Analyzer initialized")

    def _init_ml_models(self):
        """Initialize ML models for sentiment analysis"""
        try:
            if self.ml_available:
                # FinBERT for financial sentiment
                self.finbert_pipeline = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert",
                    tokenizer="ProsusAI/finbert"
                )
                
                # VADER for fast sentiment analysis
                self.vader_analyzer = SentimentIntensityAnalyzer()
                
                # XGBoost model placeholder (would be trained separately)
                self.xgb_model = None
                self.scaler = StandardScaler()
                
                logger.info("ML models initialized successfully")
            else:
                logger.warning("Using fallback sentiment analysis")
                self.finbert_pipeline = None
                self.vader_analyzer = None
                self.xgb_model = None
                self.scaler = None
                
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            self.ml_available = False

    async def collect_twitter_sentiment(self, symbols: List[str], keywords: List[str] = None) -> List[SentimentData]:
        """Collect and analyze Twitter (X) sentiment"""
        try:
            if not self._init_twitter_client():
                return []
            
            keywords = keywords or []
            search_query = self._build_twitter_query(symbols, keywords)
            
            tweets = await self._fetch_tweets(search_query, max_tweets=100)
            sentiment_data = []
            
            for tweet in tweets:
                # Clean text
                cleaned_text = self._clean_text(tweet.get('text', ''))
                
                # Analyze sentiment
                sentiment_result = await self._analyze_text_sentiment(cleaned_text)
                
                # Calculate engagement weight
                engagement = tweet.get('likes', 0) + tweet.get('retweets', 0) + tweet.get('comments', 0)
                
                sentiment_data.append(SentimentData(
                    source=SentimentSource.NEWS,  # Changed from TWITTER to NEWS
                    timestamp=datetime.fromisoformat(tweet.get('created_at', datetime.utcnow().isoformat())),
                    sentiment_score=sentiment_result['score'],
                    confidence=sentiment_result['confidence'],
                    volume=engagement,
                    text=cleaned_text[:200],  # Store sample
                    metadata={
                        'tweet_id': tweet.get('id'),
                        'user': tweet.get('user', {}).get('screen_name'),
                        'likes': tweet.get('likes', 0),
                        'retweets': tweet.get('retweets', 0),
                        'comments': tweet.get('comments', 0)
                    }
                ))
            
            logger.info(f"Collected {len(sentiment_data)} Twitter sentiment data points")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error collecting Twitter sentiment: {e}")
            return []

    async def collect_reddit_sentiment(self, subreddits: List[str] = None) -> List[SentimentData]:
        """Collect and analyze Reddit sentiment from Indian stock market subreddits"""
        try:
            if not self._init_reddit_client():
                return []
            
            subreddits = subreddits or ['IndianStockMarket', 'investing', 'stocks', 'SecurityAnalysis']
            sentiment_data = []
            
            for subreddit_name in subreddits:
                posts = await self._fetch_reddit_posts(subreddit_name, limit=50)
                
                for post in posts:
                    # Analyze post title and comments
                    title_text = self._clean_text(post.get('title', ''))
                    title_sentiment = await self._analyze_text_sentiment(title_text)
                    
                    # Get top comments
                    comments = post.get('comments', [])
                    comment_sentiments = []
                    
                    for comment in comments[:5]:  # Top 5 comments
                        comment_text = self._clean_text(comment.get('body', ''))
                        comment_sentiment = await self._analyze_text_sentiment(comment_text)
                        comment_sentiments.append(comment_sentiment)
                    
                    # Combine title and comment sentiments
                    if comment_sentiments:
                        avg_comment_score = np.mean([s['score'] for s in comment_sentiments])
                        combined_score = (title_sentiment['score'] + avg_comment_score) / 2
                        combined_confidence = (title_sentiment['confidence'] + 
                                            np.mean([s['confidence'] for s in comment_sentiments])) / 2
                    else:
                        combined_score = title_sentiment['score']
                        combined_confidence = title_sentiment['confidence']
                    
                    # Calculate engagement weight
                    upvotes = post.get('ups', 0)
                    comments_count = len(comments)
                    engagement = upvotes + comments_count
                    
                    sentiment_data.append(SentimentData(
                        source=SentimentSource.REDDIT,
                        timestamp=datetime.fromtimestamp(post.get('created_utc', 0)),
                        sentiment_score=combined_score,
                        confidence=combined_confidence,
                        volume=engagement,
                        text=title_text[:200],
                        metadata={
                            'post_id': post.get('id'),
                            'subreddit': subreddit_name,
                            'upvotes': upvotes,
                            'comments_count': comments_count,
                            'title_sentiment': title_sentiment['score']
                        }
                    ))
            
            logger.info(f"Collected {len(sentiment_data)} Reddit sentiment data points")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error collecting Reddit sentiment: {e}")
            return []

    async def collect_news_sentiment(self, symbols: List[str] = None) -> List[SentimentData]:
        """Collect and analyze news sentiment from multiple sources"""
        try:
            symbols = symbols or []
            sentiment_data = []
            
            # Collect from multiple news sources
            news_sources = [
                self._fetch_newsapi_news,
                self._fetch_gnews,
                self._fetch_alpha_vantage_news
            ]
            
            all_articles = []
            for source_func in news_sources:
                try:
                    articles = await source_func(symbols)
                    all_articles.extend(articles)
                except Exception as e:
                    logger.warning(f"Error fetching from {source_func.__name__}: {e}")
            
            # Analyze each article
            for article in all_articles:
                title = self._clean_text(article.get('title', ''))
                content = self._clean_text(article.get('content', ''))
                combined_text = f"{title} {content}"
                
                sentiment_result = await self._analyze_text_sentiment(combined_text)
                
                # Calculate relevance score based on symbol mentions
                relevance_score = self._calculate_relevance(combined_text, symbols)
                
                sentiment_data.append(SentimentData(
                    source=SentimentSource.NEWS,
                    timestamp=datetime.fromisoformat(article.get('publishedAt', datetime.utcnow().isoformat())),
                    sentiment_score=sentiment_result['score'],
                    confidence=sentiment_result['confidence'],
                    volume=article.get('popularity', 1),  # Could be based on source authority
                    text=title[:200],
                    metadata={
                        'source': article.get('source', {}).get('name'),
                        'url': article.get('url'),
                        'relevance_score': relevance_score,
                        'title_length': len(title),
                        'content_length': len(content)
                    }
                ))
            
            logger.info(f"Collected {len(sentiment_data)} news sentiment data points")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error collecting news sentiment: {e}")
            return []

    async def collect_economic_indicators(self) -> Dict[str, SentimentData]:
        """Collect and analyze economic indicators"""
        try:
            economic_data = {}
            
            # RBI Policy Data
            rbi_data = await self._fetch_rbi_policy_data()
            if rbi_data:
                rbi_sentiment = self._analyze_rbi_sentiment(rbi_data)
                economic_data['rbi'] = SentimentData(
                    source=SentimentSource.RBI,
                    timestamp=datetime.utcnow(),
                    sentiment_score=rbi_sentiment['score'],
                    confidence=rbi_sentiment['confidence'],
                    volume=1,  # Policy announcements have high impact
                    text=rbi_sentiment['summary'],
                    metadata=rbi_data
                )
            
            # Inflation Data
            inflation_data = await self._fetch_inflation_data()
            if inflation_data:
                inflation_sentiment = self._analyze_inflation_sentiment(inflation_data)
                economic_data['inflation'] = SentimentData(
                    source=SentimentSource.INFLATION,
                    timestamp=datetime.utcnow(),
                    sentiment_score=inflation_sentiment['score'],
                    confidence=inflation_sentiment['confidence'],
                    volume=1,
                    text=inflation_sentiment['summary'],
                    metadata=inflation_data
                )
            
            # GDP Data
            gdp_data = await self._fetch_gdp_data()
            if gdp_data:
                gdp_sentiment = self._analyze_gdp_sentiment(gdp_data)
                economic_data['gdp'] = SentimentData(
                    source=SentimentSource.GDP,
                    timestamp=datetime.utcnow(),
                    sentiment_score=gdp_sentiment['score'],
                    confidence=gdp_sentiment['confidence'],
                    volume=1,
                    text=gdp_sentiment['summary'],
                    metadata=gdp_data
                )
            
            logger.info(f"Collected {len(economic_data)} economic indicators")
            return economic_data
            
        except Exception as e:
            logger.error(f"Error collecting economic indicators: {e}")
            return {}

    async def _analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using available ML models"""
        try:
            if not text.strip():
                return {'score': 0.0, 'confidence': 0.0}
            
            # Use FinBERT if available
            if self.ml_available and self.finbert_pipeline:
                result = self.finbert_pipeline(text[:512])  # FinBERT has 512 token limit
                label = result[0]['label']
                score = result[0]['score']
                
                # Convert to -1 to 1 scale
                if label == 'positive':
                    sentiment_score = score
                elif label == 'negative':
                    sentiment_score = -score
                else:
                    sentiment_score = 0.0
                
                confidence = score
                
            # Fallback to VADER
            elif self.ml_available and self.vader_analyzer:
                vader_result = self.vader_analyzer.polarity_scores(text)
                sentiment_score = vader_result['compound']
                confidence = abs(vader_result['compound'])
                
            # Simple keyword-based fallback
            else:
                sentiment_score = self._keyword_sentiment(text)
                confidence = min(1.0, abs(sentiment_score))
            
            return {
                'score': np.clip(sentiment_score, -1.0, 1.0),
                'confidence': np.clip(confidence, 0.0, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {e}")
            return {'score': 0.0, 'confidence': 0.0}

    def _keyword_sentiment(self, text: str) -> float:
        """Fallback keyword-based sentiment analysis"""
        positive_words = [
            'bullish', 'growth', 'profit', 'gain', 'rise', 'increase', 'positive',
            'strong', 'excellent', 'outperform', 'beat', 'surge', 'rally', 'boom'
        ]
        negative_words = [
            'bearish', 'decline', 'loss', 'fall', 'decrease', 'negative', 'weak',
            'poor', 'underperform', 'miss', 'drop', 'crash', 'recession', 'crisis'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words

    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove mentions and hashtags (keep the text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _build_twitter_query(self, symbols: List[str], keywords: List[str]) -> str:
        """Build Twitter search query"""
        query_parts = []
        
        # Add symbols
        for symbol in symbols:
            query_parts.append(f"${symbol}")
            query_parts.append(symbol)
        
        # Add keywords
        query_parts.extend(keywords)
        
        # Add market-specific keywords
        market_keywords = ['stocks', 'trading', 'investment', 'market', 'NIFTY', 'SENSEX']
        query_parts.extend(market_keywords)
        
        return ' OR '.join(query_parts)

    def _calculate_relevance(self, text: str, symbols: List[str]) -> float:
        """Calculate relevance score based on symbol mentions"""
        if not symbols:
            return 0.5  # Default relevance
        
        text_lower = text.lower()
        symbol_count = sum(1 for symbol in symbols if symbol.lower() in text_lower)
        
        return min(1.0, symbol_count / len(symbols))

    # Twitter API methods (placeholder implementations)
    def _init_twitter_client(self) -> bool:
        """Initialize Twitter API client"""
        try:
            # Would need actual Twitter API credentials
            # self._twitter_client = tweepy.Client(...)
            return False  # Placeholder
        except Exception:
            return False

    async def _fetch_tweets(self, query: str, max_tweets: int = 100) -> List[Dict]:
        """Fetch tweets from Twitter API"""
        # Placeholder implementation
        return []

    # Reddit API methods (placeholder implementations)
    def _init_reddit_client(self) -> bool:
        """Initialize Reddit API client"""
        try:
            # Would need actual Reddit API credentials
            # self._reddit_client = praw.Reddit(...)
            return False  # Placeholder
        except Exception:
            return False

    async def _fetch_reddit_posts(self, subreddit: str, limit: int = 50) -> List[Dict]:
        """Fetch posts from Reddit"""
        # Placeholder implementation
        return []

    # News API methods (placeholder implementations)
    async def _fetch_newsapi_news(self, symbols: List[str]) -> List[Dict]:
        """Fetch news from NewsAPI"""
        # Placeholder implementation
        return []

    async def _fetch_gnews(self, symbols: List[str]) -> List[Dict]:
        """Fetch news from GNews"""
        # Placeholder implementation
        return []

    async def _fetch_alpha_vantage_news(self, symbols: List[str]) -> List[Dict]:
        """Fetch news from Alpha Vantage"""
        # Placeholder implementation
        return []

    # Economic indicators methods (placeholder implementations)
    async def _fetch_rbi_policy_data(self) -> Dict[str, Any]:
        """Fetch RBI policy data"""
        # Placeholder implementation
        return {}

    async def _fetch_inflation_data(self) -> Dict[str, Any]:
        """Fetch inflation data"""
        # Placeholder implementation
        return {}

    async def _fetch_gdp_data(self) -> Dict[str, Any]:
        """Fetch GDP data"""
        # Placeholder implementation
        return {}

    def _analyze_rbi_sentiment(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze RBI policy sentiment"""
        # Placeholder implementation
        return {'score': 0.0, 'confidence': 0.0, 'summary': ''}

    def _analyze_inflation_sentiment(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze inflation sentiment"""
        # Placeholder implementation
        return {'score': 0.0, 'confidence': 0.0, 'summary': ''}

    def _analyze_gdp_sentiment(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze GDP sentiment"""
        # Placeholder implementation
        return {'score': 0.0, 'confidence': 0.0, 'summary': ''}

class SentimentFeatureEngineer:
    """Feature engineering for sentiment analysis data"""
    
    def __init__(self):
        self.feature_columns = [
            'twitter_sentiment', 'twitter_volume',
            'reddit_sentiment', 'reddit_volume', 
            'news_sentiment', 'news_relevance',
            'rbi_sentiment', 'inflation_sentiment', 'gdp_sentiment',
            'overall_sentiment', 'sentiment_volatility'
        ]
    
    def engineer_features(self, sentiment_data: List[SentimentData], 
                         economic_data: Dict[str, SentimentData]) -> pd.DataFrame:
        """Engineer features from sentiment data"""
        try:
            # Group by source and aggregate
            source_data = {}
            for data in sentiment_data:
                source = data.source.value
                if source not in source_data:
                    source_data[source] = []
                source_data[source].append(data)
            
            # Create feature row
            features = {}
            
            # Twitter features
            if 'twitter' in source_data:
                twitter_data = source_data['twitter']
                features['twitter_sentiment'] = np.mean([d.sentiment_score for d in twitter_data])
                features['twitter_volume'] = np.sum([d.volume for d in twitter_data])
            else:
                features['twitter_sentiment'] = 0.0
                features['twitter_volume'] = 0
            
            # Reddit features
            if 'reddit' in source_data:
                reddit_data = source_data['reddit']
                features['reddit_sentiment'] = np.mean([d.sentiment_score for d in reddit_data])
                features['reddit_volume'] = np.sum([d.volume for d in reddit_data])
            else:
                features['reddit_sentiment'] = 0.0
                features['reddit_volume'] = 0
            
            # News features
            if 'news' in source_data:
                news_data = source_data['news']
                features['news_sentiment'] = np.mean([d.sentiment_score for d in news_data])
                features['news_relevance'] = np.mean([d.metadata.get('relevance_score', 0.5) for d in news_data])
            else:
                features['news_sentiment'] = 0.0
                features['news_relevance'] = 0.5
            
            # Economic features
            features['rbi_sentiment'] = economic_data.get('rbi', SentimentData(None, None, 0, 0, 0, '', {})).sentiment_score
            features['inflation_sentiment'] = economic_data.get('inflation', SentimentData(None, None, 0, 0, 0, '', {})).sentiment_score
            features['gdp_sentiment'] = economic_data.get('gdp', SentimentData(None, None, 0, 0, 0, '', {})).sentiment_score
            
            # Overall sentiment
            sentiment_scores = [
                features['twitter_sentiment'],
                features['reddit_sentiment'], 
                features['news_sentiment']
            ]
            features['overall_sentiment'] = np.mean(sentiment_scores)
            features['sentiment_volatility'] = np.std(sentiment_scores)
            
            # Create DataFrame
            df = pd.DataFrame([features])
            df['timestamp'] = datetime.utcnow()
            
            return df
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return pd.DataFrame()

class SentimentMLPredictor:
    """ML models for trading signal prediction"""
    
    def __init__(self):
        self.xgb_model = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train_models(self, features: pd.DataFrame, targets: pd.DataFrame):
        """Train ML models on historical data"""
        try:
            # Prepare data
            X = features.drop('timestamp', axis=1, errors='ignore')
            y = targets
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train XGBoost for direction prediction
            self.xgb_model = xgb.XGBClassifier(
                objective='binary:logistic',
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1
            )
            self.xgb_model.fit(X_scaled, y['direction'])
            
            # LSTM model would be trained separately for trend prediction
            # self.lstm_model = ...
            
            self.is_trained = True
            logger.info("ML models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training ML models: {e}")
    
    def predict_direction(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Predict market direction using XGBoost"""
        try:
            if not self.is_trained or self.xgb_model is None:
                return {'direction': 'NEUTRAL', 'probability': 0.5, 'confidence': 0.0}
            
            X = features.drop('timestamp', axis=1, errors='ignore')
            X_scaled = self.scaler.transform(X)
            
            prediction = self.xgb_model.predict(X_scaled)[0]
            probability = self.xgb_model.predict_proba(X_scaled)[0]
            
            direction_map = {0: 'DOWN', 1: 'UP', 2: 'NEUTRAL'}
            direction = direction_map.get(prediction, 'NEUTRAL')
            confidence = max(probability)
            
            return {
                'direction': direction,
                'probability': float(confidence),
                'confidence': float(confidence)
            }
            
        except Exception as e:
            logger.error(f"Error predicting direction: {e}")
            return {'direction': 'NEUTRAL', 'probability': 0.5, 'confidence': 0.0}

# Main service class
class EnhancedSentimentAnalysisService:
    """Main service for enhanced sentiment analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = EnhancedSentimentAnalyzer(config)
        self.feature_engineer = SentimentFeatureEngineer()
        self.predictor = SentimentMLPredictor()
        
        # Scheduling
        self.scheduled_tasks = {}
        
    async def run_comprehensive_analysis(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Run complete sentiment analysis pipeline"""
        try:
            symbols = symbols or ['NIFTY', 'SENSEX']
            
            # Collect data from all sources
            twitter_data = await self.analyzer.collect_twitter_sentiment(symbols)
            reddit_data = await self.analyzer.collect_reddit_sentiment()
            news_data = await self.analyzer.collect_news_sentiment(symbols)
            economic_data = await self.analyzer.collect_economic_indicators()
            
            # Combine all sentiment data
            all_sentiment_data = twitter_data + reddit_data + news_data
            
            # Engineer features
            features_df = self.feature_engineer.engineer_features(all_sentiment_data, economic_data)
            
            # Make predictions if models are trained
            predictions = {}
            if self.predictor.is_trained:
                predictions = self.predictor.predict_direction(features_df)
            
            # Generate summary
            summary = self._generate_summary(all_sentiment_data, economic_data, predictions)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'symbols': symbols,
                'data_summary': {
                    'twitter_count': len(twitter_data),
                    'reddit_count': len(reddit_data),
                    'news_count': len(news_data),
                    'economic_indicators': list(economic_data.keys())
                },
                'features': features_df.to_dict('records')[0] if not features_df.empty else {},
                'predictions': predictions,
                'summary': summary,
                'raw_data': {
                    'twitter': [self._serialize_sentiment_data(d) for d in twitter_data[:10]],
                    'reddit': [self._serialize_sentiment_data(d) for d in reddit_data[:10]],
                    'news': [self._serialize_sentiment_data(d) for d in news_data[:10]],
                    'economic': {k: self._serialize_sentiment_data(v) for k, v in economic_data.items()}
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    def _serialize_sentiment_data(self, data: SentimentData) -> Dict[str, Any]:
        """Serialize SentimentData to dictionary"""
        return {
            'source': data.source.value if data.source else None,
            'timestamp': data.timestamp.isoformat() if data.timestamp else None,
            'sentiment_score': data.sentiment_score,
            'confidence': data.confidence,
            'volume': data.volume,
            'text': data.text,
            'metadata': data.metadata
        }
    
    def _generate_summary(self, sentiment_data: List[SentimentData], 
                         economic_data: Dict[str, SentimentData], 
                         predictions: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        try:
            # Calculate overall sentiment
            if sentiment_data:
                avg_sentiment = np.mean([d.sentiment_score for d in sentiment_data])
                avg_confidence = np.mean([d.confidence for d in sentiment_data])
            else:
                avg_sentiment = 0.0
                avg_confidence = 0.0
            
            # Determine sentiment direction
            if avg_sentiment > 0.1:
                sentiment_desc = "positive"
            elif avg_sentiment < -0.1:
                sentiment_desc = "negative"
            else:
                sentiment_desc = "neutral"
            
            # Build summary
            summary_parts = [
                f"Overall market sentiment is {sentiment_desc}",
                f"with {avg_confidence:.1%} confidence"
            ]
            
            # Add economic context
            if economic_data:
                rbi_sentiment = economic_data.get('rbi')
                if rbi_sentiment:
                    if rbi_sentiment.sentiment_score > 0.1:
                        summary_parts.append("RBI policy appears accommodative")
                    elif rbi_sentiment.sentiment_score < -0.1:
                        summary_parts.append("RBI policy appears tightening")
            
            # Add predictions
            if predictions:
                direction = predictions.get('direction', 'NEUTRAL')
                confidence = predictions.get('confidence', 0.0)
                if confidence > 0.6:
                    summary_parts.append(f"ML models predict {direction} movement with {confidence:.1%} confidence")
            
            return ". ".join(summary_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Unable to generate summary"

# Factory function for backward compatibility
def create_sentiment_service(config: Dict[str, Any] = None) -> EnhancedSentimentAnalysisService:
    """Create enhanced sentiment analysis service"""
    return EnhancedSentimentAnalysisService(config)
