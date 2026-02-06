"""
Enhanced Sentiment Analysis API Routes
Integration with the existing backend API system
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio

from ..core.enhanced_sentiment_manager import create_enhanced_sentiment_manager
from ..core.sentiment_config import get_sentiment_config, is_sentiment_enabled, print_sentiment_config
from ..core.sentiment_storage import SentimentDataStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sentiment", tags=["enhanced-sentiment"])

# Global manager instance
sentiment_manager = None

async def get_sentiment_manager():
    """Get or create the sentiment manager instance"""
    global sentiment_manager
    
    if sentiment_manager is None:
        if not is_sentiment_enabled():
            raise HTTPException(
                status_code=503, 
                detail="Enhanced sentiment analysis is disabled. Configure API keys in .env file."
            )
        
        try:
            config = get_sentiment_config()
            sentiment_manager = await create_enhanced_sentiment_manager(config)
        except Exception as e:
            logger.error(f"Failed to initialize sentiment manager: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize sentiment analysis: {str(e)}"
            )
    
    return sentiment_manager

@router.get("/status")
async def get_sentiment_status():
    """Get the status of the enhanced sentiment analysis system"""
    try:
        config = get_sentiment_config()
        
        status = {
            "enabled": is_sentiment_enabled(),
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": {
                "database_path": config.get('database', {}).get('path'),
                "models_path": config.get('models', {}).get('path'),
                "ml_enabled": config.get('ml', {}).get('enabled', False),
                "scheduling": config.get('scheduling', {}),
                "data_retention": config.get('retention', {})
            },
            "api_status": {}
        }
        
        # Check API keys status
        if 'api_keys' in config:
            api_keys = config['api_keys']
            status["api_status"] = {
                "twitter": bool(api_keys.get('twitter', {}).get('bearer_token')),
                "reddit": bool(
                    api_keys.get('reddit', {}).get('client_id') and 
                    api_keys.get('reddit', {}).get('client_secret')
                ),
                "newsapi": bool(api_keys.get('news', {}).get('newsapi_key')),
                "gnews": bool(api_keys.get('news', {}).get('gnews_api_key')),
                "alpha_vantage": bool(api_keys.get('news', {}).get('alpha_vantage_key')),
                "world_bank": bool(api_keys.get('economic', {}).get('world_bank_api_key'))
            }
        
        # Get system status if manager is initialized
        if sentiment_manager and sentiment_manager.initialized:
            system_status = await sentiment_manager.get_system_status()
            status["system"] = system_status
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting sentiment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def run_comprehensive_analysis(
    symbols: List[str] = ["NIFTY", "SENSEX"],
    background_tasks: BackgroundTasks = None
):
    """Run comprehensive sentiment analysis for specified symbols"""
    try:
        manager = await get_sentiment_manager()
        
        # Run analysis
        analysis = await manager.run_comprehensive_analysis(symbols)
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols": symbols,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/real-time/{symbol}")
async def get_real_time_sentiment(symbol: str):
    """Get real-time sentiment for a specific symbol"""
    try:
        manager = await get_sentiment_manager()
        
        real_time_data = await manager.get_real_time_sentiment(symbol)
        
        return {
            "success": True,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "data": real_time_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{symbol}")
async def get_historical_analysis(
    symbol: str,
    days: int = 30
):
    """Get historical sentiment analysis for a symbol"""
    try:
        if days > 365:
            raise HTTPException(status_code=400, detail="Maximum 365 days allowed")
        
        manager = await get_sentiment_manager()
        
        historical_data = await manager.get_historical_analysis(symbol, days)
        
        return {
            "success": True,
            "symbol": symbol,
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
            "data": historical_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-models")
async def train_ml_models(
    training_period_days: int = 90,
    background_tasks: BackgroundTasks = None
):
    """Train ML models with historical data"""
    try:
        if training_period_days > 365:
            raise HTTPException(status_code=400, detail="Maximum 365 days allowed")
        
        manager = await get_sentiment_manager()
        
        # Train models (this might take a while)
        if background_tasks:
            background_tasks.add_task(
                manager.train_models, 
                training_period_days
            )
            return {
                "success": True,
                "message": "Model training started in background",
                "training_period_days": training_period_days
            }
        else:
            # Run synchronously (not recommended for production)
            results = await manager.train_models(training_period_days)
            return {
                "success": True,
                "message": "Model training completed",
                "results": results
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-system")
async def start_sentiment_system():
    """Start the automated sentiment analysis system"""
    try:
        manager = await get_sentiment_manager()
        
        if manager.running:
            return {
                "success": True,
                "message": "Sentiment analysis system is already running"
            }
        
        success = await manager.start_system()
        
        if success:
            return {
                "success": True,
                "message": "Sentiment analysis system started successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to start sentiment analysis system"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sentiment system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-system")
async def stop_sentiment_system():
    """Stop the automated sentiment analysis system"""
    try:
        manager = await get_sentiment_manager()
        
        if not manager.running:
            return {
                "success": True,
                "message": "Sentiment analysis system is not running"
            }
        
        await manager.stop_system()
        
        return {
            "success": True,
            "message": "Sentiment analysis system stopped successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping sentiment system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_sentiment_configuration():
    """Get current sentiment analysis configuration"""
    try:
        config = get_sentiment_config()
        
        # Remove sensitive API keys from response
        safe_config = config.copy()
        if 'api_keys' in safe_config:
            safe_keys = {}
            for service, keys in safe_config['api_keys'].items():
                safe_keys[service] = {
                    key: "configured" if value else "not_configured"
                    for key, value in keys.items()
                }
            safe_config['api_keys'] = safe_keys
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": safe_config
        }
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/{symbol}")
async def get_latest_predictions(
    symbol: str,
    limit: int = 10
):
    """Get latest predictions for a symbol"""
    try:
        if limit > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 predictions allowed")
        
        manager = await get_sentiment_manager()
        
        if not manager.storage:
            raise HTTPException(
                status_code=503,
                detail="Storage not available"
            )
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)  # Last 7 days
        
        predictions = await manager.storage.get_predictions(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "period": "last 7 days",
            "count": len(predictions),
            "predictions": predictions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-stats")
async def get_data_statistics():
    """Get statistics about stored sentiment data"""
    try:
        manager = await get_sentiment_manager()
        
        if not manager.storage:
            raise HTTPException(
                status_code=503,
                detail="Storage not available"
            )
        
        stats = await manager.storage.get_storage_stats()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_old_data(retention_days: int = 90):
    """Clean up old sentiment data"""
    try:
        if retention_days < 30:
            raise HTTPException(status_code=400, detail="Minimum retention period is 30 days")
        
        manager = await get_sentiment_manager()
        
        if not manager.storage:
            raise HTTPException(
                status_code=503,
                detail="Storage not available"
            )
        
        success = await manager.storage.cleanup_old_data(retention_days)
        
        return {
            "success": success,
            "message": f"Cleanup completed for data older than {retention_days} days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def sentiment_health_check():
    """Health check for sentiment analysis system"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check if system is enabled
        health_status["checks"]["enabled"] = is_sentiment_enabled()
        
        # Check configuration
        try:
            config = get_sentiment_config()
            health_status["checks"]["config_loaded"] = True
        except:
            health_status["checks"]["config_loaded"] = False
        
        # Check manager initialization
        if sentiment_manager:
            health_status["checks"]["manager_initialized"] = sentiment_manager.initialized
            health_status["checks"]["system_running"] = sentiment_manager.running
        else:
            health_status["checks"]["manager_initialized"] = False
            health_status["checks"]["system_running"] = False
        
        # Overall status
        all_healthy = all(health_status["checks"].values())
        health_status["status"] = "healthy" if all_healthy else "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Utility function to initialize the sentiment system on startup
async def initialize_sentiment_system():
    """Initialize the sentiment system on application startup"""
    try:
        if is_sentiment_enabled():
            logger.info("Initializing enhanced sentiment analysis system...")
            manager = await get_sentiment_manager()
            logger.info("Enhanced sentiment analysis system initialized successfully")
        else:
            logger.info("Enhanced sentiment analysis is disabled")
    except Exception as e:
        logger.error(f"Failed to initialize sentiment system: {e}")

# Utility function to cleanup on shutdown
async def cleanup_sentiment_system():
    """Cleanup the sentiment system on application shutdown"""
    global sentiment_manager
    
    try:
        if sentiment_manager and sentiment_manager.running:
            await sentiment_manager.stop_system()
            logger.info("Enhanced sentiment analysis system stopped")
    except Exception as e:
        logger.error(f"Error during sentiment system cleanup: {e}")
    finally:
        sentiment_manager = None
