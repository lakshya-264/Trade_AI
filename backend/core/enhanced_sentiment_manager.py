"""
Enhanced Sentiment Analysis Integration Module
Main integration point for all sentiment analysis components
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

# Import all sentiment analysis components
from .enhanced_sentiment_analysis import EnhancedSentimentAnalysisService
from .reddit_sentiment import RedditSentimentCollector
from .news_sentiment import NewsSentimentCollector
from .economic_indicators import EconomicIndicatorsCollector
from .feature_engineering import SentimentFeatureEngineer
from .sentiment_scheduler import SentimentScheduler
from .sentiment_storage import SentimentDataStorage
from .trading_predictor import TradingSignalPredictor
from .sentiment_config import get_sentiment_config, is_sentiment_enabled
from .forum_sentiment import ForumSentimentCollector

logger = logging.getLogger(__name__)

class EnhancedSentimentAnalysisManager:
    """
    Main manager class for enhanced sentiment analysis system
    Integrates all components: data collection, processing, storage, ML, and scheduling
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the enhanced sentiment analysis manager
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        # Load configuration from environment variables if not provided
        if config is None:
            config = get_sentiment_config()
        
        self.config = config or {}
        
        # Component initialization
        self.storage = None
        self.scheduler = None
        self.predictor = None
        self.feature_engineer = None
        
        # Data collectors
        self.reddit_collector = None
        self.news_collector = None
        self.economic_collector = None
        self.forum_collector = None
        
        # Main service
        self.sentiment_service = None
        
        # System status
        self.initialized = False
        self.running = False
        
        # Configuration paths
        self.db_path = self.config.get('database', {}).get('path', 'enhanced_sentiment.db')
        self.models_dir = Path(self.config.get('models', {}).get('path', 'trained_models'))
        
        logger.info("Enhanced Sentiment Analysis Manager initialized")
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Check if enhanced sentiment is enabled
            if not is_sentiment_enabled():
                logger.warning("Enhanced sentiment analysis is disabled in configuration")
                return False
            
            logger.info("Initializing Enhanced Sentiment Analysis System...")
            
            # 1. Initialize storage
            db_config = self.config.get('database', {})
            self.storage = SentimentDataStorage(db_config.get('path', 'enhanced_sentiment.db'))
            await self.storage.initialize_database()
            logger.info("✓ Storage initialized")
            
            # 2. Initialize feature engineer
            self.feature_engineer = SentimentFeatureEngineer(self.config)
            logger.info("✓ Feature engineer initialized")
            
            # 3. Initialize data collectors
            await self._initialize_collectors()
            logger.info("✓ Data collectors initialized")
            
            # 4. Initialize main sentiment service
            self.sentiment_service = EnhancedSentimentAnalysisService(self.config)
            logger.info("✓ Sentiment service initialized")
            
            # 5. Initialize trading predictor
            self.predictor = TradingSignalPredictor(self.config)
            await self.predictor.initialize(self.storage)
            logger.info("✓ Trading predictor initialized")
            
            # 6. Initialize scheduler
            self.scheduler = SentimentScheduler(self.config)
            await self.scheduler.initialize()
            logger.info("✓ Scheduler initialized")
            
            self.initialized = True
            logger.info("🚀 Enhanced Sentiment Analysis System fully initialized!")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def start_system(self) -> bool:
        """Start the automated sentiment analysis system"""
        try:
            if not self.initialized:
                logger.error("System not initialized")
                return False
            
            logger.info("Starting Enhanced Sentiment Analysis System...")
            
            # Start scheduler
            await self.scheduler.start_scheduler()
            self.running = True
            
            logger.info("🔄 Enhanced Sentiment Analysis System is now running!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            return False
    
    async def stop_system(self):
        """Stop the sentiment analysis system"""
        try:
            if not self.running:
                logger.warning("System is not running")
                return
            
            logger.info("Stopping Enhanced Sentiment Analysis System...")
            
            # Stop scheduler
            if self.scheduler:
                await self.scheduler.stop_scheduler()
            
            # Cleanup collectors
            if self.twitter_collector:
                await self.twitter_collector.cleanup()
            if self.news_collector:
                await self.news_collector.cleanup()
            if self.economic_collector:
                await self.economic_collector.cleanup()
            
            self.running = False
            logger.info("⏹️ Enhanced Sentiment Analysis System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    async def run_comprehensive_analysis(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive sentiment analysis
        
        Args:
            symbols: List of stock symbols to analyze
        
        Returns:
            Complete analysis results
        """
        try:
            if not self.initialized:
                return {'error': 'System not initialized'}
            
            symbols = symbols or ['NIFTY', 'SENSEX']
            logger.info(f"Running comprehensive analysis for symbols: {symbols}")
            
            # 1. Collect data from all sources
            collection_results = await self._collect_all_data(symbols)
            
            # 2. Engineer features
            features_df = await self._engineer_features(collection_results)
            
            # 3. Generate predictions
            predictions = await self._generate_predictions(features_df, symbols)
            
            # 4. Store results
            await self._store_analysis_results(collection_results, features_df, predictions)
            
            # 5. Generate comprehensive report
            report = self._generate_comprehensive_report(
                collection_results, features_df, predictions, symbols
            )
            
            logger.info("Comprehensive analysis completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e)}
    
    async def get_real_time_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time sentiment for a specific symbol
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Real-time sentiment data
        """
        try:
            if not self.initialized:
                return {'error': 'System not initialized'}
            
            # Get recent sentiment data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            sentiment_data = await self.storage.get_sentiment_data(
                start_time=start_time,
                end_time=end_time,
                symbol=symbol,
                limit=100
            )
            
            # Get latest predictions
            predictions = await self.storage.get_predictions(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                limit=10
            )
            
            # Calculate real-time metrics
            real_time_metrics = self._calculate_real_time_metrics(sentiment_data, predictions)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'real_time_metrics': real_time_metrics,
                'recent_sentiment': sentiment_data[:10],  # Last 10 records
                'latest_predictions': predictions[:5],    # Last 5 predictions
                'data_points': len(sentiment_data),
                'prediction_count': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time sentiment: {e}")
            return {'error': str(e)}
    
    async def get_historical_analysis(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Get historical sentiment analysis
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
        
        Returns:
            Historical analysis results
        """
        try:
            if not self.initialized:
                return {'error': 'System not initialized'}
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Get historical sentiment data
            sentiment_data = await self.storage.get_sentiment_data(
                start_time=start_time,
                end_time=end_time,
                symbol=symbol,
                limit=5000
            )
            
            # Get aggregated sentiment
            aggregated_data = await self.storage.get_aggregated_sentiment(
                period='day',
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )
            
            # Get historical predictions
            predictions = await self.storage.get_predictions(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            # Calculate historical metrics
            historical_metrics = self._calculate_historical_metrics(
                sentiment_data, aggregated_data, predictions
            )
            
            return {
                'symbol': symbol,
                'period': f"{days} days",
                'start_date': start_time.isoformat(),
                'end_date': end_time.isoformat(),
                'historical_metrics': historical_metrics,
                'aggregated_sentiment': aggregated_data,
                'data_summary': {
                    'sentiment_points': len(sentiment_data),
                    'aggregated_days': len(aggregated_data),
                    'predictions': len(predictions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting historical analysis: {e}")
            return {'error': str(e)}
    
    async def train_models(self, training_period_days: int = 90) -> Dict[str, Any]:
        """
        Train ML models with historical data
        
        Args:
            training_period_days: Number of days of training data
        
        Returns:
            Training results
        """
        try:
            if not self.initialized:
                return {'error': 'System not initialized'}
            
            logger.info(f"Training models with {training_period_days} days of data...")
            
            # Get training data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=training_period_days)
            
            training_data = await self.storage.get_feature_data(
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            if training_data.empty:
                return {'error': 'No training data available'}
            
            # Train models
            training_results = await self.predictor.train_models(training_data)
            
            logger.info("Model training completed")
            return training_results
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return {'error': str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                'system_initialized': self.initialized,
                'system_running': self.running,
                'timestamp': datetime.utcnow().isoformat(),
                'components': {}
            }
            
            # Storage status
            if self.storage:
                storage_stats = await self.storage.get_storage_stats()
                status['components']['storage'] = {
                    'status': 'active',
                    'stats': storage_stats
                }
            
            # Scheduler status
            if self.scheduler:
                task_status = self.scheduler.get_all_tasks_status()
                status['components']['scheduler'] = {
                    'status': 'active' if self.scheduler.scheduler_running else 'inactive',
                    'tasks': task_status
                }
            
            # Collectors status
            status['components']['collectors'] = {
                'reddit': 'active' if self.reddit_collector else 'inactive',
                'news': 'active' if self.news_collector else 'inactive',
                'economic': 'active' if self.economic_collector else 'inactive',
                'forum': 'active' if self.forum_collector else 'inactive'
            }
            
            # Models status
            if self.predictor:
                model_performance = self.predictor.get_model_performance()
                status['components']['models'] = {
                    'status': 'active',
                    'trained_models': list(self.predictor.models.keys()),
                    'performance': model_performance
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    async def _initialize_collectors(self):
        """Initialize all data collectors"""
        api_config = self.config.get('api_keys', {})
        
        # Reddit collector
        reddit_config = api_config.get('reddit', {})
        if reddit_config.get('client_id') and reddit_config.get('client_secret'):
            self.reddit_collector = RedditSentimentCollector(reddit_config)
            await self.reddit_collector.initialize()
            logger.info("✓ Reddit collector initialized")
        else:
            logger.warning("Reddit API keys not configured, Reddit collector disabled")
        
        # News collector
        news_config = api_config.get('news', {})
        if news_config.get('newsapi_key'):
            self.news_collector = NewsSentimentCollector(news_config)
            await self.news_collector.initialize()
            logger.info("✓ News collector initialized")
        else:
            logger.warning("News API keys not configured, News collector disabled")
        
        # Economic collector (always available as it has fallbacks)
        self.economic_collector = EconomicIndicatorsCollector(api_config.get('economic', {}))
        await self.economic_collector.initialize()
        logger.info("✓ Economic collector initialized")
        
        # Forum collector (always available with web scraping)
        self.forum_collector = ForumSentimentCollector(api_config.get('forum', {}))
        await self.forum_collector.initialize()
        logger.info("✓ Forum collector initialized")
    
    async def _collect_all_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Collect data from all sources"""
        collection_results = {}
        
        # Reddit data
        if self.reddit_collector:
            reddit_data = await self.reddit_collector.collect_posts(limit=50)
            collection_results['reddit'] = reddit_data
        
        # News data
        if self.news_collector:
            news_data = await self.news_collector.collect_all_news(symbols, hours_back=24)
            collection_results['news'] = news_data
        
        # Economic data
        if self.economic_collector:
            economic_data = await self.economic_collector.collect_all_indicators()
            collection_results['economic'] = economic_data
        
        # Forum data
        if self.forum_collector:
            forum_data = await self.forum_collector.collect_all_forum_posts(symbols, max_posts_per_source=50)
            collection_results['forum'] = forum_data
        
        return collection_results
    
    async def _engineer_features(self, collection_results: Dict[str, Any]) -> Any:
        """Engineer features from collected data"""
        try:
            # Combine all sentiment data
            all_sentiment_data = []
            for source, data in collection_results.items():
                if source != 'economic' and data:
                    all_sentiment_data.extend(data)
            
            economic_data = collection_results.get('economic', {})
            
            # Engineer features
            features_df = self.feature_engineer.engineer_features(
                all_sentiment_data, economic_data
            )
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return None
    
    async def _generate_predictions(self, features_df, symbols: List[str]) -> Dict[str, Any]:
        """Generate predictions using ML models"""
        try:
            if features_df is None or features_df.empty:
                return {}
            
            predictions = {}
            
            for symbol in symbols:
                prediction_result = await self.predictor.predict_signals(features_df, symbol)
                predictions[symbol] = prediction_result
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {}
    
    async def _store_analysis_results(self, collection_results: Dict[str, Any], 
                                   features_df, predictions: Dict[str, Any]):
        """Store analysis results in database"""
        try:
            # Store sentiment data
            for source, data in collection_results.items():
                if source != 'economic' and data:
                    await self.storage.store_sentiment_data(data)
            
            # Store economic indicators
            if 'economic' in collection_results:
                await self.storage.store_economic_indicators(collection_results['economic'])
            
            # Store feature data
            if features_df is not None and not features_df.empty:
                for symbol in predictions.keys():
                    await self.storage.store_feature_data(features_df, symbol)
            
            logger.info("Analysis results stored successfully")
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
    
    def _generate_comprehensive_report(self, collection_results: Dict[str, Any], 
                                     features_df, predictions: Dict[str, Any],
                                     symbols: List[str]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbols': symbols,
                'data_collection_summary': {
                    'twitter_count': len(collection_results.get('twitter', [])),
                    'reddit_count': len(collection_results.get('reddit', [])),
                    'news_count': len(collection_results.get('news', [])),
                    'economic_indicators': list(collection_results.get('economic', {}).keys())
                },
                'predictions': predictions,
                'feature_summary': {},
                'overall_sentiment': self._calculate_overall_sentiment(collection_results),
                'recommendations': self._generate_recommendations(predictions)
            }
            
            # Add feature summary if available
            if features_df is not None and not features_df.empty:
                report['feature_summary'] = {
                    'total_features': len(features_df.columns),
                    'feature_names': list(features_df.columns)[:10],  # First 10 features
                    'data_points': len(features_df)
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_sentiment(self, collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall sentiment metrics"""
        try:
            all_sentiments = []
            
            for source, data in collection_results.items():
                if source != 'economic' and data:
                    for item in data:
                        if hasattr(item, 'sentiment_score'):
                            all_sentiments.append(item.sentiment_score)
            
            if not all_sentiments:
                return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}
            
            avg_sentiment = sum(all_sentiments) / len(all_sentiments)
            
            if avg_sentiment > 0.1:
                sentiment = 'positive'
            elif avg_sentiment < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': round(avg_sentiment, 3),
                'confidence': min(1.0, len(all_sentiments) / 100),  # Confidence based on data volume
                'data_points': len(all_sentiments)
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall sentiment: {e}")
            return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}
    
    def _generate_recommendations(self, predictions: Dict[str, Any]) -> List[str]:
        """Generate trading recommendations based on predictions"""
        try:
            recommendations = []
            
            for symbol, pred in predictions.items():
                if isinstance(pred, dict) and 'recommendation' in pred:
                    rec = pred['recommendation']
                    action = rec.get('action', 'HOLD')
                    confidence = rec.get('confidence', 0.0)
                    reason = rec.get('reason', '')
                    
                    if confidence > 0.6:  # Only include high-confidence recommendations
                        recommendations.append(
                            f"{symbol}: {action} (Confidence: {confidence:.1%}) - {reason}"
                        )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _calculate_real_time_metrics(self, sentiment_data: List[Dict], 
                                   predictions: List[Dict]) -> Dict[str, Any]:
        """Calculate real-time sentiment metrics"""
        try:
            metrics = {}
            
            # Sentiment metrics
            if sentiment_data:
                sentiments = [item.get('sentiment_score', 0) for item in sentiment_data]
                metrics['current_sentiment'] = {
                    'average': sum(sentiments) / len(sentiments),
                    'trend': 'improving' if len(sentiments) > 1 and sentiments[-1] > sentiments[0] else 'declining',
                    'volatility': max(sentiments) - min(sentiments) if sentiments else 0
                }
            
            # Prediction metrics
            if predictions:
                latest_pred = predictions[0]  # Most recent prediction
                metrics['latest_prediction'] = {
                    'action': latest_pred.get('prediction', 'NEUTRAL'),
                    'confidence': latest_pred.get('confidence', 0.0),
                    'model_type': latest_pred.get('model_type', 'unknown')
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating real-time metrics: {e}")
            return {}
    
    def _calculate_historical_metrics(self, sentiment_data: List[Dict], 
                                   aggregated_data: List[Dict],
                                   predictions: List[Dict]) -> Dict[str, Any]:
        """Calculate historical sentiment metrics"""
        try:
            metrics = {}
            
            # Sentiment trends
            if aggregated_data:
                daily_sentiments = [item.get('sentiment_mean', 0) for item in aggregated_data]
                metrics['sentiment_trend'] = {
                    'average': sum(daily_sentiments) / len(daily_sentiments),
                    'volatility': np.std(daily_sentiments) if daily_sentiments else 0,
                    'trend_direction': 'upward' if len(daily_sentiments) > 1 and daily_sentiments[-1] > daily_sentiments[0] else 'downward'
                }
            
            # Prediction accuracy
            if predictions:
                # This would calculate actual vs predicted accuracy if actual results were available
                metrics['prediction_summary'] = {
                    'total_predictions': len(predictions),
                    'avg_confidence': sum(p.get('confidence', 0) for p in predictions) / len(predictions) if predictions else 0
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating historical metrics: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cleanup collectors
            if self.reddit_collector:
                await self.reddit_collector.cleanup()
            if self.news_collector:
                await self.news_collector.cleanup()
            if self.economic_collector:
                await self.economic_collector.cleanup()
            if self.forum_collector:
                await self.forum_collector.cleanup()
            
            # Cleanup other components
            if self.scheduler:
                await self.scheduler.shutdown()
            
            logger.info("Enhanced sentiment analysis manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Factory function for easy initialization
async def create_enhanced_sentiment_manager(config: Dict[str, Any] = None) -> EnhancedSentimentAnalysisManager:
    """
    Create and initialize enhanced sentiment analysis manager
    
    Args:
        config: Configuration dictionary with API keys and settings
    
    Returns:
        Initialized manager instance
    """
    manager = EnhancedSentimentAnalysisManager(config)
    await manager.initialize()
    return manager

# Example configuration structure
EXAMPLE_CONFIG = {
    'database': {
        'path': 'enhanced_sentiment.db'
    },
    'models': {
        'path': 'trained_models'
    },
    'api_keys': {
        'twitter': {
            'bearer_token': 'your_twitter_bearer_token',
            'consumer_key': 'your_consumer_key',
            'consumer_secret': 'your_consumer_secret',
            'access_token': 'your_access_token',
            'access_token_secret': 'your_access_token_secret'
        },
        'reddit': {
            'client_id': 'your_reddit_client_id',
            'client_secret': 'your_reddit_client_secret',
            'user_agent': 'TraderAI_Sentiment/1.0'
        },
        'news': {
            'newsapi_key': 'your_newsapi_key',
            'gnews_api_key': 'your_gnews_api_key',
            'alpha_vantage_key': 'your_alpha_vantage_key'
        },
        'economic': {
            'world_bank_api_key': 'your_world_bank_api_key'
        }
    },
    'scheduling': {
        'twitter_interval': 15,  # minutes
        'reddit_interval': 60,   # minutes
        'news_interval': 30,     # minutes
        'economic_interval': 240 # minutes
    }
}
