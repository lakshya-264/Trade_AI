"""
Feature Engineering for Sentiment Analysis and ML Models
Converts sentiment data into numerical features for machine learning
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from .enhanced_sentiment_analysis import SentimentData, SentimentSource

logger = logging.getLogger(__name__)

class SentimentFeatureEngineer:
    """Advanced feature engineering for sentiment analysis data"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize feature engineer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Feature scaling
        self.scaler = StandardScaler()
        self.min_max_scaler = MinMaxScaler()
        self.scaler_fitted = False
        
        # Feature names
        self.feature_columns = [
            # Twitter features
            'twitter_sentiment_mean', 'twitter_sentiment_std', 'twitter_volume',
            'twitter_engagement_mean', 'twitter_engagement_std', 'twitter_tweet_count',
            
            # Reddit features
            'reddit_sentiment_mean', 'reddit_sentiment_std', 'reddit_volume',
            'reddit_upvotes_mean', 'reddit_upvotes_std', 'reddit_post_count',
            'reddit_comment_sentiment_mean',
            
            # News features
            'news_sentiment_mean', 'news_sentiment_std', 'news_count',
            'news_relevance_mean', 'news_source_diversity', 'news_sentiment_weighted',
            
            # Economic indicators
            'rbi_sentiment', 'rbi_repo_rate', 'rbi_policy_stance',
            'inflation_sentiment', 'inflation_cpi', 'inflation_trend',
            'gdp_sentiment', 'gdp_growth', 'gdp_trend',
            'interest_rate', 'interest_rate_trend',
            
            # Combined features
            'overall_sentiment', 'sentiment_volatility', 'sentiment_skewness',
            'volume_weighted_sentiment', 'confidence_weighted_sentiment',
            'source_balance', 'engagement_correlation',
            
            # Technical features (would be added from price data)
            'price_momentum_1d', 'price_momentum_5d', 'volatility_5d',
            'rsi_14', 'macd_signal', 'volume_ratio',
            
            # Time-based features
            'hour_of_day', 'day_of_week', 'is_trading_hours',
            'is_market_open', 'time_since_market_open'
        ]
        
        # Feature importance weights (for weighted features)
        self.source_weights = {
            SentimentSource.REDDIT: 0.25,
            SentimentSource.NEWS: 0.40,
            SentimentSource.RBI: 0.15,
            SentimentSource.INFLATION: 0.10,
            SentimentSource.GDP: 0.10,
            SentimentSource.FORUM: 0.20
        }
    
    def engineer_features(self, sentiment_data: List[SentimentData], 
                         economic_data: Dict[str, SentimentData],
                         price_data: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Engineer comprehensive features from sentiment and economic data
        
        Args:
            sentiment_data: List of sentiment data points
            economic_data: Economic indicators data
            price_data: Market price data (optional)
        
        Returns:
            DataFrame with engineered features
        """
        try:
            # Group sentiment data by source
            source_data = self._group_by_source(sentiment_data)
            
            # Initialize feature dictionary
            features = {}
            
            # Extract features from each source
            features.update(self._extract_twitter_features(source_data.get('twitter', [])))
            features.update(self._extract_reddit_features(source_data.get('reddit', [])))
            features.update(self._extract_news_features(source_data.get('news', [])))
            features.update(self._extract_economic_features(economic_data))
            
            # Extract combined features
            features.update(self._extract_combined_features(sentiment_data, source_data))
            
            # Add technical features if price data available
            if price_data:
                features.update(self._extract_technical_features(price_data))
            
            # Add time-based features
            features.update(self._extract_time_features())
            
            # Create DataFrame
            df = pd.DataFrame([features])
            df['timestamp'] = datetime.utcnow()
            
            # Ensure all expected columns exist
            for col in self.feature_columns:
                if col not in df.columns:
                    df[col] = 0.0
            
            # Reorder columns
            df = df[self.feature_columns + ['timestamp']]
            
            logger.info(f"Engineered {len(self.feature_columns)} features")
            return df
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=self.feature_columns + ['timestamp'])
    
    def _group_by_source(self, sentiment_data: List[SentimentData]) -> Dict[str, List[SentimentData]]:
        """Group sentiment data by source"""
        source_groups = {}
        
        for data in sentiment_data:
            source_name = data.source.value if data.source else 'unknown'
            if source_name not in source_groups:
                source_groups[source_name] = []
            source_groups[source_name].append(data)
        
        return source_groups
    
    def _extract_twitter_features(self, twitter_data: List[SentimentData]) -> Dict[str, float]:
        """Extract features from Twitter data"""
        features = {}
        
        if not twitter_data:
            # Default values if no data
            features.update({
                'twitter_sentiment_mean': 0.0,
                'twitter_sentiment_std': 0.0,
                'twitter_volume': 0.0,
                'twitter_engagement_mean': 0.0,
                'twitter_engagement_std': 0.0,
                'twitter_tweet_count': 0.0
            })
            return features
        
        # Sentiment statistics
        sentiments = [d.sentiment_score for d in twitter_data]
        features['twitter_sentiment_mean'] = np.mean(sentiments)
        features['twitter_sentiment_std'] = np.std(sentiments)
        
        # Volume and engagement
        volumes = [d.volume for d in twitter_data]
        features['twitter_volume'] = np.sum(volumes)
        features['twitter_engagement_mean'] = np.mean(volumes)
        features['twitter_engagement_std'] = np.std(volumes)
        features['twitter_tweet_count'] = len(twitter_data)
        
        # Additional Twitter-specific features
        # Calculate engagement-weighted sentiment
        if volumes and sum(volumes) > 0:
            weighted_sentiment = sum(s * v for s, v in zip(sentiments, volumes)) / sum(volumes)
            features['twitter_weighted_sentiment'] = weighted_sentiment
        else:
            features['twitter_weighted_sentiment'] = features['twitter_sentiment_mean']
        
        return features
    
    def _extract_reddit_features(self, reddit_data: List[SentimentData]) -> Dict[str, float]:
        """Extract features from Reddit data"""
        features = {}
        
        if not reddit_data:
            features.update({
                'reddit_sentiment_mean': 0.0,
                'reddit_sentiment_std': 0.0,
                'reddit_volume': 0.0,
                'reddit_upvotes_mean': 0.0,
                'reddit_upvotes_std': 0.0,
                'reddit_post_count': 0.0,
                'reddit_comment_sentiment_mean': 0.0
            })
            return features
        
        # Sentiment statistics
        sentiments = [d.sentiment_score for d in reddit_data]
        features['reddit_sentiment_mean'] = np.mean(sentiments)
        features['reddit_sentiment_std'] = np.std(sentiments)
        
        # Volume and upvotes
        volumes = [d.volume for d in reddit_data]
        features['reddit_volume'] = np.sum(volumes)
        features['reddit_upvotes_mean'] = np.mean(volumes)
        features['reddit_upvotes_std'] = np.std(volumes)
        features['reddit_post_count'] = len(reddit_data)
        
        # Extract comment sentiments from metadata
        comment_sentiments = []
        for data in reddit_data:
            comments = data.metadata.get('comments', [])
            for comment in comments:
                if isinstance(comment, dict) and 'sentiment' in comment:
                    comment_sentiments.append(comment['sentiment'])
        
        if comment_sentiments:
            features['reddit_comment_sentiment_mean'] = np.mean(comment_sentiments)
        else:
            features['reddit_comment_sentiment_mean'] = features['reddit_sentiment_mean']
        
        return features
    
    def _extract_news_features(self, news_data: List[SentimentData]) -> Dict[str, float]:
        """Extract features from news data"""
        features = {}
        
        if not news_data:
            features.update({
                'news_sentiment_mean': 0.0,
                'news_sentiment_std': 0.0,
                'news_count': 0.0,
                'news_relevance_mean': 0.0,
                'news_source_diversity': 0.0,
                'news_sentiment_weighted': 0.0
            })
            return features
        
        # Sentiment statistics
        sentiments = [d.sentiment_score for d in news_data]
        features['news_sentiment_mean'] = np.mean(sentiments)
        features['news_sentiment_std'] = np.std(sentiments)
        features['news_count'] = len(news_data)
        
        # Relevance scores
        relevance_scores = [d.metadata.get('relevance_score', 0.5) for d in news_data]
        features['news_relevance_mean'] = np.mean(relevance_scores)
        
        # Source diversity (number of unique sources)
        sources = set()
        for data in news_data:
            source = data.metadata.get('source_name', 'Unknown')
            sources.add(source)
        features['news_source_diversity'] = len(sources) / max(len(news_data), 1)
        
        # Relevance-weighted sentiment
        if relevance_scores and sum(relevance_scores) > 0:
            weighted_sentiment = sum(s * r for s, r in zip(sentiments, relevance_scores)) / sum(relevance_scores)
            features['news_sentiment_weighted'] = weighted_sentiment
        else:
            features['news_sentiment_weighted'] = features['news_sentiment_mean']
        
        return features
    
    def _extract_economic_features(self, economic_data: Dict[str, SentimentData]) -> Dict[str, float]:
        """Extract features from economic indicators"""
        features = {}
        
        # RBI features
        rbi_data = economic_data.get('rbi')
        if rbi_data:
            features['rbi_sentiment'] = rbi_data.sentiment_score
            features['rbi_repo_rate'] = rbi_data.metadata.get('repo_rate', 6.5)
            features['rbi_policy_stance'] = self._encode_policy_stance(
                rbi_data.metadata.get('policy_stance', 'neutral')
            )
        else:
            features.update({
                'rbi_sentiment': 0.0,
                'rbi_repo_rate': 6.5,
                'rbi_policy_stance': 0.0
            })
        
        # Inflation features
        inflation_data = economic_data.get('inflation')
        if inflation_data:
            features['inflation_sentiment'] = inflation_data.sentiment_score
            features['inflation_cpi'] = inflation_data.metadata.get('cpi_headline', 5.0)
            features['inflation_trend'] = self._encode_trend(
                inflation_data.metadata.get('inflation_trend', 'stable')
            )
        else:
            features.update({
                'inflation_sentiment': 0.0,
                'inflation_cpi': 5.0,
                'inflation_trend': 0.0
            })
        
        # GDP features
        gdp_data = economic_data.get('gdp')
        if gdp_data:
            features['gdp_sentiment'] = gdp_data.sentiment_score
            features['gdp_growth'] = gdp_data.metadata.get('gdp_growth_yoy', 6.0)
            features['gdp_trend'] = self._encode_trend(
                gdp_data.metadata.get('gdp_trend', 'stable')
            )
        else:
            features.update({
                'gdp_sentiment': 0.0,
                'gdp_growth': 6.0,
                'gdp_trend': 0.0
            })
        
        # Interest rate features
        interest_data = economic_data.get('interest_rate')
        if interest_data:
            features['interest_rate'] = interest_data.metadata.get('interest_rate', 6.5)
            features['interest_rate_trend'] = self._encode_trend(
                interest_data.metadata.get('trend', 'stable')
            )
        else:
            features.update({
                'interest_rate': 6.5,
                'interest_rate_trend': 0.0
            })
        
        return features
    
    def _extract_combined_features(self, sentiment_data: List[SentimentData], 
                                  source_data: Dict[str, List[SentimentData]]) -> Dict[str, float]:
        """Extract combined features across all sources"""
        features = {}
        
        if not sentiment_data:
            features.update({
                'overall_sentiment': 0.0,
                'sentiment_volatility': 0.0,
                'sentiment_skewness': 0.0,
                'volume_weighted_sentiment': 0.0,
                'confidence_weighted_sentiment': 0.0,
                'source_balance': 0.0,
                'engagement_correlation': 0.0
            })
            return features
        
        # Overall sentiment statistics
        all_sentiments = [d.sentiment_score for d in sentiment_data]
        features['overall_sentiment'] = np.mean(all_sentiments)
        features['sentiment_volatility'] = np.std(all_sentiments)
        features['sentiment_skewness'] = self._calculate_skewness(all_sentiments)
        
        # Volume-weighted sentiment
        volumes = [d.volume for d in sentiment_data]
        if volumes and sum(volumes) > 0:
            weighted_sentiment = sum(s * v for s, v in zip(all_sentiments, volumes)) / sum(volumes)
            features['volume_weighted_sentiment'] = weighted_sentiment
        else:
            features['volume_weighted_sentiment'] = features['overall_sentiment']
        
        # Confidence-weighted sentiment
        confidences = [d.confidence for d in sentiment_data]
        if confidences and sum(confidences) > 0:
            conf_weighted_sentiment = sum(s * c for s, c in zip(all_sentiments, confidences)) / sum(confidences)
            features['confidence_weighted_sentiment'] = conf_weighted_sentiment
        else:
            features['confidence_weighted_sentiment'] = features['overall_sentiment']
        
        # Source balance (how evenly distributed data is across sources)
        source_counts = {source: len(data) for source, data in source_data.items()}
        total_count = sum(source_counts.values())
        if total_count > 0:
            source_balance = 1.0 - (np.std(list(source_counts.values())) / np.mean(list(source_counts.values())))
            features['source_balance'] = max(0.0, source_balance)
        else:
            features['source_balance'] = 0.0
        
        # Engagement-sentiment correlation
        if len(all_sentiments) > 1 and len(volumes) > 1:
            correlation = np.corrcoef(all_sentiments, volumes)[0, 1]
            features['engagement_correlation'] = correlation if not np.isnan(correlation) else 0.0
        else:
            features['engagement_correlation'] = 0.0
        
        return features
    
    def _extract_technical_features(self, price_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract technical features from price data"""
        features = {}
        
        try:
            # Price momentum features
            current_price = price_data.get('current', 0)
            historical_prices = price_data.get('historical', [])
            
            if len(historical_prices) >= 5:
                # 1-day momentum
                price_1d_ago = historical_prices[-1] if len(historical_prices) > 0 else current_price
                features['price_momentum_1d'] = (current_price - price_1d_ago) / price_1d_ago
                
                # 5-day momentum
                price_5d_ago = historical_prices[-5] if len(historical_prices) >= 5 else current_price
                features['price_momentum_5d'] = (current_price - price_5d_ago) / price_5d_ago
                
                # Volatility (5-day)
                returns = [historical_prices[i] / historical_prices[i-1] - 1 
                          for i in range(1, min(6, len(historical_prices)))]
                features['volatility_5d'] = np.std(returns) if returns else 0.0
                
                # RSI (simplified)
                if len(historical_prices) >= 14:
                    gains = []
                    losses = []
                    for i in range(1, 15):
                        change = historical_prices[-i] - historical_prices[-i-1]
                        if change > 0:
                            gains.append(change)
                            losses.append(0)
                        else:
                            gains.append(0)
                            losses.append(abs(change))
                    
                    avg_gain = np.mean(gains) if gains else 0
                    avg_loss = np.mean(losses) if losses else 1
                    rs = avg_gain / avg_loss if avg_loss > 0 else 0
                    features['rsi_14'] = 100 - (100 / (1 + rs))
                else:
                    features['rsi_14'] = 50.0
                
                # MACD (simplified)
                if len(historical_prices) >= 26:
                    ema_12 = np.mean(historical_prices[-12:])
                    ema_26 = np.mean(historical_prices[-26:])
                    features['macd_signal'] = ema_12 - ema_26
                else:
                    features['macd_signal'] = 0.0
                
                # Volume ratio
                current_volume = price_data.get('volume', 0)
                avg_volume = np.mean(price_data.get('historical_volume', [current_volume]))
                features['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
                
            else:
                # Default values if insufficient data
                features.update({
                    'price_momentum_1d': 0.0,
                    'price_momentum_5d': 0.0,
                    'volatility_5d': 0.0,
                    'rsi_14': 50.0,
                    'macd_signal': 0.0,
                    'volume_ratio': 1.0
                })
                
        except Exception as e:
            logger.error(f"Error extracting technical features: {e}")
            # Default values on error
            features.update({
                'price_momentum_1d': 0.0,
                'price_momentum_5d': 0.0,
                'volatility_5d': 0.0,
                'rsi_14': 50.0,
                'macd_signal': 0.0,
                'volume_ratio': 1.0
            })
        
        return features
    
    def _extract_time_features(self) -> Dict[str, float]:
        """Extract time-based features"""
        features = {}
        now = datetime.utcnow()
        
        # Convert to IST (UTC+5:30)
        ist_time = now + timedelta(hours=5, minutes=30)
        
        features['hour_of_day'] = ist_time.hour / 24.0  # Normalized to 0-1
        features['day_of_week'] = ist_time.weekday() / 6.0  # Normalized to 0-1
        
        # Trading hours (9:15 AM to 3:30 PM IST)
        is_trading_hours = 9 <= ist_time.hour <= 15 and ist_time.weekday() < 5
        features['is_trading_hours'] = 1.0 if is_trading_hours else 0.0
        
        # Market open check (simplified - assumes market is open on weekdays)
        features['is_market_open'] = 1.0 if ist_time.weekday() < 5 else 0.0
        
        # Time since market open (in hours, normalized)
        if is_trading_hours:
            market_open = ist_time.replace(hour=9, minute=15, second=0, microsecond=0)
            time_since_open = (ist_time - market_open).total_seconds() / 3600
            features['time_since_market_open'] = time_since_open / 6.25  # 6.25 hours trading day
        else:
            features['time_since_market_open'] = 0.0
        
        return features
    
    def _encode_policy_stance(self, stance: str) -> float:
        """Encode policy stance as numeric value"""
        stance_map = {
            'accommodative': 1.0,
            'supportive': 0.5,
            'neutral': 0.0,
            'tightening': -0.5,
            'restrictive': -1.0
        }
        return stance_map.get(stance.lower(), 0.0)
    
    def _encode_trend(self, trend: str) -> float:
        """Encode trend as numeric value"""
        trend_map = {
            'accelerating': 1.0,
            'rising': 0.5,
            'recovering': 0.25,
            'stable': 0.0,
            'moderating': -0.25,
            'falling': -0.5,
            'slowing': -0.75,
            'contracting': -1.0
        }
        return trend_map.get(trend.lower(), 0.0)
    
    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate skewness of data"""
        try:
            if len(data) < 3:
                return 0.0
            
            data_array = np.array(data)
            mean = np.mean(data_array)
            std = np.std(data_array)
            
            if std == 0:
                return 0.0
            
            skewness = np.mean(((data_array - mean) / std) ** 3)
            return skewness
            
        except Exception:
            return 0.0
    
    def fit_scaler(self, feature_data: pd.DataFrame):
        """Fit the feature scaler on training data"""
        try:
            # Remove timestamp column for scaling
            features_df = feature_data.drop('timestamp', axis=1, errors='ignore')
            
            if not features_df.empty:
                self.scaler.fit(features_df)
                self.scaler_fitted = True
                logger.info("Feature scaler fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting scaler: {e}")
    
    def transform_features(self, feature_data: pd.DataFrame) -> pd.DataFrame:
        """Transform features using fitted scaler"""
        try:
            if not self.scaler_fitted:
                logger.warning("Scaler not fitted, returning original features")
                return feature_data
            
            # Remove timestamp column for scaling
            features_df = feature_data.drop('timestamp', axis=1, errors='ignore')
            
            if not features_df.empty:
                scaled_features = self.scaler.transform(features_df)
                scaled_df = pd.DataFrame(scaled_features, columns=features_df.columns)
                
                # Add timestamp back
                if 'timestamp' in feature_data.columns:
                    scaled_df['timestamp'] = feature_data['timestamp']
                
                return scaled_df
            
            return feature_data
            
        except Exception as e:
            logger.error(f"Error transforming features: {e}")
            return feature_data
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance weights"""
        return self.source_weights.copy()
    
    def create_lag_features(self, feature_data: pd.DataFrame, 
                          lag_periods: List[int] = [1, 3, 5]) -> pd.DataFrame:
        """Create lagged features for time series analysis"""
        try:
            lagged_data = feature_data.copy()
            
            for lag in lag_periods:
                for col in self.feature_columns:
                    if col in feature_data.columns:
                        lagged_data[f'{col}_lag_{lag}'] = feature_data[col].shift(lag)
            
            return lagged_data
            
        except Exception as e:
            logger.error(f"Error creating lag features: {e}")
            return feature_data
    
    def create_rolling_features(self, feature_data: pd.DataFrame, 
                              windows: List[int] = [3, 5, 10]) -> pd.DataFrame:
        """Create rolling window features"""
        try:
            rolling_data = feature_data.copy()
            
            for window in windows:
                for col in self.feature_columns:
                    if col in feature_data.columns:
                        rolling_data[f'{col}_rolling_mean_{window}'] = feature_data[col].rolling(window).mean()
                        rolling_data[f'{col}_rolling_std_{window}'] = feature_data[col].rolling(window).std()
            
            return rolling_data
            
        except Exception as e:
            logger.error(f"Error creating rolling features: {e}")
            return feature_data

class FeatureSelector:
    """Feature selection for sentiment analysis models"""
    
    def __init__(self, method: str = 'correlation'):
        """
        Initialize feature selector
        
        Args:
            method: Selection method ('correlation', 'variance', 'mutual_info')
        """
        self.method = method
        self.selected_features = []
    
    def select_features(self, X: pd.DataFrame, y: pd.Series, 
                      top_k: int = 20) -> List[str]:
        """Select top features based on specified method"""
        try:
            if self.method == 'correlation':
                return self._correlation_selection(X, y, top_k)
            elif self.method == 'variance':
                return self._variance_selection(X, top_k)
            elif self.method == 'mutual_info':
                return self._mutual_info_selection(X, y, top_k)
            else:
                return list(X.columns)[:top_k]
                
        except Exception as e:
            logger.error(f"Error in feature selection: {e}")
            return list(X.columns)[:top_k]
    
    def _correlation_selection(self, X: pd.DataFrame, y: pd.Series, 
                             top_k: int) -> List[str]:
        """Select features based on correlation with target"""
        correlations = X.corrwith(y).abs().sort_values(ascending=False)
        return correlations.head(top_k).index.tolist()
    
    def _variance_selection(self, X: pd.DataFrame, top_k: int) -> List[str]:
        """Select features based on variance"""
        variances = X.var().sort_values(ascending=False)
        return variances.head(top_k).index.tolist()
    
    def _mutual_info_selection(self, X: pd.DataFrame, y: pd.Series, 
                              top_k: int) -> List[str]:
        """Select features based on mutual information"""
        try:
            from sklearn.feature_selection import mutual_info_regression
            
            mi_scores = mutual_info_regression(X, y)
            mi_series = pd.Series(mi_scores, index=X.columns).sort_values(ascending=False)
            return mi_series.head(top_k).index.tolist()
            
        except ImportError:
            logger.warning("sklearn not available, falling back to correlation")
            return self._correlation_selection(X, y, top_k)
