"""
Enhanced Sentiment Analysis Integration Script
Startup and initialization for the enhanced sentiment analysis system
"""

import asyncio
import logging
from typing import Dict, Any

from .sentiment_config import get_sentiment_config, is_sentiment_enabled, print_sentiment_config
from .enhanced_sentiment_manager import create_enhanced_sentiment_manager

logger = logging.getLogger(__name__)

class SentimentAnalysisIntegration:
    """Integration class for enhanced sentiment analysis"""
    
    def __init__(self):
        self.manager = None
        self.initialized = False
        self.running = False
    
    async def initialize(self) -> bool:
        """Initialize the enhanced sentiment analysis system"""
        try:
            if not is_sentiment_enabled():
                logger.info("Enhanced sentiment analysis is disabled in configuration")
                return False
            
            logger.info("Initializing Enhanced Sentiment Analysis Integration...")
            
            # Print configuration summary
            print_sentiment_config()
            
            # Create manager
            config = get_sentiment_config()
            self.manager = await create_enhanced_sentiment_manager(config)
            
            # Initialize the system
            success = await self.manager.initialize()
            
            if success:
                self.initialized = True
                logger.info("✅ Enhanced Sentiment Analysis Integration initialized successfully")
                
                # Optionally start the automated system
                auto_start = config.get('system', {}).get('auto_start', False)
                if auto_start:
                    await self.start_automated_system()
                
                return True
            else:
                logger.error("❌ Failed to initialize Enhanced Sentiment Analysis")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing sentiment analysis integration: {e}")
            return False
    
    async def start_automated_system(self) -> bool:
        """Start the automated sentiment analysis system"""
        try:
            if not self.initialized or not self.manager:
                logger.error("Sentiment manager not initialized")
                return False
            
            logger.info("Starting automated sentiment analysis system...")
            
            success = await self.manager.start_system()
            
            if success:
                self.running = True
                logger.info("✅ Automated sentiment analysis system started")
                return True
            else:
                logger.error("❌ Failed to start automated sentiment analysis system")
                return False
                
        except Exception as e:
            logger.error(f"Error starting automated system: {e}")
            return False
    
    async def stop_automated_system(self):
        """Stop the automated sentiment analysis system"""
        try:
            if self.manager and self.running:
                logger.info("Stopping automated sentiment analysis system...")
                await self.manager.stop_system()
                self.running = False
                logger.info("✅ Automated sentiment analysis system stopped")
                
        except Exception as e:
            logger.error(f"Error stopping automated system: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.stop_automated_system()
            
            if self.manager:
                # Additional cleanup if needed
                self.manager = None
            
            self.initialized = False
            logger.info("✅ Enhanced Sentiment Analysis Integration cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_manager(self):
        """Get the sentiment manager instance"""
        return self.manager
    
    def is_initialized(self) -> bool:
        """Check if the system is initialized"""
        return self.initialized
    
    def is_running(self) -> bool:
        """Check if the automated system is running"""
        return self.running

# Global integration instance
sentiment_integration = SentimentAnalysisIntegration()

async def initialize_sentiment_analysis() -> bool:
    """Initialize the enhanced sentiment analysis system"""
    return await sentiment_integration.initialize()

async def start_sentiment_system() -> bool:
    """Start the automated sentiment analysis system"""
    return await sentiment_integration.start_automated_system()

async def stop_sentiment_system():
    """Stop the automated sentiment analysis system"""
    await sentiment_integration.stop_automated_system()

async def cleanup_sentiment_analysis():
    """Cleanup the enhanced sentiment analysis system"""
    await sentiment_integration.cleanup()

def get_sentiment_manager():
    """Get the sentiment manager instance"""
    return sentiment_integration.get_manager()

def is_sentiment_system_ready() -> bool:
    """Check if the sentiment system is ready"""
    return sentiment_integration.is_initialized()

# Application startup functions
async def on_application_startup():
    """Called when the application starts"""
    try:
        logger.info("Starting enhanced sentiment analysis integration...")
        success = await initialize_sentiment_analysis()
        
        if success:
            logger.info("🚀 Enhanced sentiment analysis integration ready")
        else:
            logger.info("⚠️ Enhanced sentiment analysis integration not available")
            
    except Exception as e:
        logger.error(f"Error in application startup: {e}")

async def on_application_shutdown():
    """Called when the application shuts down"""
    try:
        logger.info("Shutting down enhanced sentiment analysis integration...")
        await cleanup_sentiment_analysis()
        logger.info("✅ Enhanced sentiment analysis integration shutdown complete")
        
    except Exception as e:
        logger.error(f"Error in application shutdown: {e}")

# Configuration validation
def validate_sentiment_configuration() -> Dict[str, Any]:
    """Validate the sentiment analysis configuration"""
    try:
        config = get_sentiment_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "configured_apis": []
        }
        
        # Check if system is enabled
        if not is_sentiment_enabled():
            validation_result["warnings"].append("Enhanced sentiment analysis is disabled")
            return validation_result
        
        # Validate API keys
        api_keys = config.get('api_keys', {})
        
        # Twitter API
        twitter_config = api_keys.get('twitter', {})
        if twitter_config.get('bearer_token'):
            validation_result["configured_apis"].append("Twitter")
        else:
            validation_result["warnings"].append("Twitter API not configured")
        
        # Reddit API
        reddit_config = api_keys.get('reddit', {})
        if reddit_config.get('client_id') and reddit_config.get('client_secret'):
            validation_result["configured_apis"].append("Reddit")
        else:
            validation_result["warnings"].append("Reddit API not configured")
        
        # News APIs
        news_config = api_keys.get('news', {})
        if news_config.get('newsapi_key'):
            validation_result["configured_apis"].append("NewsAPI")
        else:
            validation_result["warnings"].append("NewsAPI not configured")
        
        if news_config.get('gnews_api_key'):
            validation_result["configured_apis"].append("GNews")
        
        if news_config.get('alpha_vantage_key'):
            validation_result["configured_apis"].append("Alpha Vantage")
        
        # Economic APIs
        economic_config = api_keys.get('economic', {})
        if economic_config.get('world_bank_api_key'):
            validation_result["configured_apis"].append("World Bank")
        else:
            validation_result["warnings"].append("World Bank API not configured")
        
        # Validate paths
        db_path = config.get('database', {}).get('path')
        if not db_path:
            validation_result["errors"].append("Database path not configured")
        
        models_path = config.get('models', {}).get('path')
        if not models_path:
            validation_result["warnings"].append("Models path not configured, using default")
        
        # Validate scheduling
        scheduling = config.get('scheduling', {})
        if not scheduling:
            validation_result["warnings"].append("Scheduling not configured, using defaults")
        
        # Overall validation
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Configuration validation failed: {str(e)}"],
            "warnings": [],
            "configured_apis": []
        }

# Quick status check
def get_quick_status() -> Dict[str, Any]:
    """Get a quick status of the sentiment analysis system"""
    try:
        return {
            "enabled": is_sentiment_enabled(),
            "initialized": sentiment_integration.is_initialized(),
            "running": sentiment_integration.is_running(),
            "manager_available": sentiment_integration.get_manager() is not None
        }
    except Exception as e:
        return {
            "enabled": False,
            "initialized": False,
            "running": False,
            "manager_available": False,
            "error": str(e)
        }
