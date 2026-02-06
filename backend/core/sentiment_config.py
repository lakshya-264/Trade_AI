"""
Configuration Loader for Enhanced Sentiment Analysis
Loads configuration from environment variables and provides it to the sentiment system
"""

import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SentimentConfigLoader:
    """Load and manage configuration for enhanced sentiment analysis"""
    
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        try:
            # Database configuration
            self.config['database'] = {
                'path': os.getenv('SENTIMENT_DB_PATH', 'enhanced_sentiment.db')
            }
            
            # Models configuration
            self.config['models'] = {
                'path': os.getenv('SENTIMENT_MODELS_PATH', 'trained_models')
            }
            
            # API Keys
            self.config['api_keys'] = {
                'reddit': {
                    'client_id': os.getenv('REDDIT_CLIENT_ID'),
                    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                    'user_agent': os.getenv('REDDIT_USER_AGENT', 'TraderAI_Sentiment/1.0')
                },
                'news': {
                    'newsapi_key': os.getenv('NEWS_API_KEY'),
                    'gnews_api_key': os.getenv('GNEWS_API_KEY'),
                    'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_API_KEY')
                },
                'economic': {
                    'world_bank_api_key': os.getenv('WORLD_BANK_API_KEY')
                }
            }
            
            # Scheduling configuration
            self.config['scheduling'] = {
                'reddit_interval': int(os.getenv('REDDIT_SENTIMENT_INTERVAL', 60)),
                'news_interval': int(os.getenv('NEWS_SENTIMENT_INTERVAL', 30)),
                'economic_interval': int(os.getenv('ECONOMIC_INDICATORS_INTERVAL', 240)),
                'comprehensive_interval': int(os.getenv('COMPREHENSIVE_ANALYSIS_INTERVAL', 60))
            }
            
            # ML Model configuration
            self.config['ml'] = {
                'enabled': os.getenv('ENABLE_ML_PREDICTIONS', 'True').lower() == 'true',
                'confidence_threshold': float(os.getenv('MODEL_CONFIDENCE_THRESHOLD', 0.6)),
                'ensemble_voting_weighted': os.getenv('ENSEMBLE_VOTING_WEIGHTED', 'True').lower() == 'true'
            }
            
            # Data retention configuration
            self.config['retention'] = {
                'sentiment_data_days': int(os.getenv('SENTIMENT_DATA_RETENTION_DAYS', 90)),
                'aggregated_data_days': int(os.getenv('AGGREGATED_DATA_RETENTION_DAYS', 365)),
                'prediction_data_days': int(os.getenv('PREDICTION_DATA_RETENTION_DAYS', 180))
            }
            
            # System configuration
            self.config['system'] = {
                'enabled': os.getenv('ENABLE_ENHANCED_SENTIMENT', 'True').lower() == 'true',
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true'
            }
            
            # Validate configuration
            self.validate_config()
            
            logger.info("Enhanced sentiment analysis configuration loaded successfully")
            return self.config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self.config
    
    def validate_config(self):
        """Validate the loaded configuration"""
        try:
            # Check if enhanced sentiment is enabled
            if not self.config.get('system', {}).get('enabled', False):
                logger.warning("Enhanced sentiment analysis is disabled")
                return
            
            # Validate required API keys
            missing_keys = []
            
            # Reddit API validation
            reddit_config = self.config.get('api_keys', {}).get('reddit', {})
            if not reddit_config.get('client_id'):
                missing_keys.append('REDDIT_CLIENT_ID')
            if not reddit_config.get('client_secret'):
                missing_keys.append('REDDIT_CLIENT_SECRET')
            
            # News API validation
            news_config = self.config.get('api_keys', {}).get('news', {})
            if not news_config.get('newsapi_key'):
                missing_keys.append('NEWS_API_KEY')
            
            # Log warnings for missing keys
            if missing_keys:
                logger.warning(f"Missing API keys for enhanced sentiment: {missing_keys}")
                logger.info("System will operate in limited mode without these APIs")
            
            # Create directories if they don't exist
            models_path = Path(self.config.get('models', {}).get('path', 'trained_models'))
            models_path.mkdir(exist_ok=True)
            
            db_path = Path(self.config.get('database', {}).get('path', 'enhanced_sentiment.db'))
            db_path.parent.mkdir(exist_ok=True)
            
            logger.info("Configuration validation completed")
            
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
    
    def get_twitter_config(self) -> Dict[str, str]:
        """Get Twitter API configuration"""
        return self.config.get('api_keys', {}).get('twitter', {})
    
    def get_reddit_config(self) -> Dict[str, str]:
        """Get Reddit API configuration"""
        return self.config.get('api_keys', {}).get('reddit', {})
    
    def get_news_config(self) -> Dict[str, str]:
        """Get News API configuration"""
        return self.config.get('api_keys', {}).get('news', {})
    
    def get_economic_config(self) -> Dict[str, str]:
        """Get Economic API configuration"""
        return self.config.get('api_keys', {}).get('economic', {})
    
    def get_scheduling_config(self) -> Dict[str, int]:
        """Get scheduling configuration"""
        return self.config.get('scheduling', {})
    
    def get_ml_config(self) -> Dict[str, Any]:
        """Get ML model configuration"""
        return self.config.get('ml', {})
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return self.config.get('database', {})
    
    def is_enabled(self) -> bool:
        """Check if enhanced sentiment analysis is enabled"""
        return self.config.get('system', {}).get('enabled', False)
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get the complete configuration"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration with new values"""
        try:
            self.config.update(new_config)
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
    
    def get_api_status(self) -> Dict[str, bool]:
        """Get status of API configurations"""
        status = {}
        
        # Twitter API status
        twitter_config = self.get_twitter_config()
        status['twitter'] = bool(twitter_config.get('bearer_token'))
        
        # Reddit API status
        reddit_config = self.get_reddit_config()
        status['reddit'] = bool(reddit_config.get('client_id') and reddit_config.get('client_secret'))
        
        # News API status
        news_config = self.get_news_config()
        status['newsapi'] = bool(news_config.get('newsapi_key'))
        status['gnews'] = bool(news_config.get('gnews_api_key'))
        status['alpha_vantage'] = bool(news_config.get('alpha_vantage_key'))
        
        # Economic API status
        economic_config = self.get_economic_config()
        status['world_bank'] = bool(economic_config.get('world_bank_api_key'))
        
        return status
    
    def print_config_summary(self):
        """Print a summary of the current configuration"""
        try:
            print("\n" + "="*60)
            print("ENHANCED SENTIMENT ANALYSIS CONFIGURATION")
            print("="*60)
            
            # System status
            print(f"System Enabled: {self.is_enabled()}")
            print(f"Debug Mode: {self.config.get('system', {}).get('debug', False)}")
            print(f"Log Level: {self.config.get('system', {}).get('log_level', 'INFO')}")
            
            # Database
            db_config = self.get_database_config()
            print(f"Database Path: {db_config.get('path', 'enhanced_sentiment.db')}")
            
            # Models
            models_config = self.config.get('models', {})
            print(f"Models Path: {models_config.get('path', 'trained_models')}")
            
            # API Status
            print("\nAPI Status:")
            api_status = self.get_api_status()
            for api, status in api_status.items():
                status_icon = "✅" if status else "❌"
                print(f"  {api.replace('_', ' ').title()}: {status_icon}")
            
            # Scheduling
            scheduling = self.get_scheduling_config()
            print(f"\nScheduling Intervals (minutes):")
            for service, interval in scheduling.items():
                print(f"  {service.replace('_', ' ').title()}: {interval}")
            
            # ML Configuration
            ml_config = self.get_ml_config()
            print(f"\nML Configuration:")
            print(f"  Enabled: {ml_config.get('enabled', False)}")
            print(f"  Confidence Threshold: {ml_config.get('confidence_threshold', 0.6)}")
            print(f"  Ensemble Voting: {ml_config.get('ensemble_voting_weighted', False)}")
            
            # Data Retention
            retention = self.config.get('retention', {})
            print(f"\nData Retention (days):")
            for data_type, days in retention.items():
                print(f"  {data_type.replace('_', ' ').title()}: {days}")
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error printing configuration summary: {e}")

# Global configuration instance
config_loader = SentimentConfigLoader()

def get_sentiment_config() -> Dict[str, Any]:
    """Get the enhanced sentiment analysis configuration"""
    return config_loader.get_full_config()

def is_sentiment_enabled() -> bool:
    """Check if enhanced sentiment analysis is enabled"""
    return config_loader.is_enabled()

def get_api_keys() -> Dict[str, Any]:
    """Get all API keys configuration"""
    return config_loader.config.get('api_keys', {})

def print_sentiment_config():
    """Print the sentiment analysis configuration summary"""
    config_loader.print_config_summary()
