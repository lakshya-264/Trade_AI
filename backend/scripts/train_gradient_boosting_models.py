"""
Training Script for Gradient Boosting Models (XGBoost/LightGBM) for 1-Month Predictions
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database_unified import get_db
from services.gradient_boosting_models import GradientBoostingModels
from services.data_fetcher import fetch_historical_data
from core.prediction_tracking_models import ModelTrainingLog
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Training symbols (top liquid stocks)
TRAINING_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "BHARTIARTL", "SBIN", "BAJFINANCE", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
    "NESTLEIND", "ULTRACEMCO", "WIPRO", "SUNPHARMA", "TATAMOTORS"
]

async def prepare_training_data(symbols: list, days: int = 500) -> pd.DataFrame:
    """Prepare training data from multiple symbols"""
    all_data = []
    
    for symbol in symbols:
        try:
            logger.info(f"Fetching data for {symbol}...")
            candles = await fetch_historical_data(symbol, "1d", days=days)
            
            if not candles or len(candles) < 100:
                logger.warning(f"Insufficient data for {symbol}")
                continue
            
            df = pd.DataFrame(candles)
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
                df.set_index('time', inplace=True, drop=False)
            
            # Ensure required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    if col == 'volume':
                        df[col] = 0
                    else:
                        df[col] = df.get('close', 0)
            
            df['symbol'] = symbol
            all_data.append(df)
            logger.info(f"✓ Collected {len(df)} candles for {symbol}")
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No training data collected")
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Total training data: {len(combined_df)} candles from {len(all_data)} symbols")
    
    return combined_df

async def train_gradient_boosting_models(
    db: Session,
    symbols: list = None,
    days: int = 500,
    model_types: list = None
):
    """Train gradient boosting models (XGBoost and/or LightGBM)"""
    
    if symbols is None:
        symbols = TRAINING_SYMBOLS
    
    if model_types is None:
        model_types = ['xgb', 'lgb']
    
    logger.info(f"Starting gradient boosting model training for {len(symbols)} symbols")
    logger.info(f"Models to train: {model_types}")
    
    # Create training log
    training_log = ModelTrainingLog(
        model_type="gradient_boosting_ensemble",
        model_category="gradient_boosting",
        timeframe="1M",
        training_started_at=datetime.utcnow(),
        status="running",
        symbols_used=symbols,
        training_config={
            "days": days,
            "model_types": model_types,
            "symbols_count": len(symbols)
        }
    )
    db.add(training_log)
    db.commit()
    
    try:
        # Prepare training data
        logger.info("Preparing training data...")
        training_data = await prepare_training_data(symbols, days=days)
        
        training_log.data_points_count = len(training_data)
        training_log.training_period_start = training_data.index.min().date() if hasattr(training_data.index, 'min') else None
        training_log.training_period_end = training_data.index.max().date() if hasattr(training_data.index, 'max') else None
        db.commit()
        
        # Initialize gradient boosting models service
        gb_models = GradientBoostingModels()
        
        results = {}
        
        # Train XGBoost
        if 'xgb' in model_types:
            logger.info("Training XGBoost model...")
            try:
                xgb_result = gb_models.train_xgboost_model(training_data, target_col='close')
                results['xgb'] = xgb_result
                logger.info(f"✓ XGBoost training completed: {xgb_result}")
            except Exception as e:
                logger.error(f"XGBoost training failed: {e}")
                import traceback
                results['xgb'] = {"error": str(e), "traceback": traceback.format_exc()}
        
        # Train LightGBM
        if 'lgb' in model_types:
            logger.info("Training LightGBM model...")
            try:
                lgb_result = gb_models.train_lightgbm_model(training_data, target_col='close')
                results['lgb'] = lgb_result
                logger.info(f"✓ LightGBM training completed: {lgb_result}")
            except Exception as e:
                logger.error(f"LightGBM training failed: {e}")
                import traceback
                results['lgb'] = {"error": str(e), "traceback": traceback.format_exc()}
        
        # Train Random Forest (optional)
        if 'rf' in model_types:
            logger.info("Training Random Forest model...")
            try:
                rf_result = gb_models.train_random_forest_model(training_data, target_col='close')
                results['rf'] = rf_result
                logger.info(f"✓ Random Forest training completed: {rf_result}")
            except Exception as e:
                logger.error(f"Random Forest training failed: {e}")
                results['rf'] = {"error": str(e)}
        
        # Train Gradient Boosting (optional)
        if 'gb' in model_types:
            logger.info("Training Gradient Boosting model...")
            try:
                gb_result = gb_models.train_gradient_boosting_model(training_data, target_col='close')
                results['gb'] = gb_result
                logger.info(f"✓ Gradient Boosting training completed: {gb_result}")
            except Exception as e:
                logger.error(f"Gradient Boosting training failed: {e}")
                results['gb'] = {"error": str(e)}
        
        # Update training log
        training_log.status = "completed"
        training_log.training_completed_at = datetime.utcnow()
        training_log.training_metrics = results
        
        # Calculate average metrics
        if 'xgb' in results and 'rmse' in results['xgb']:
            training_log.test_loss = results['xgb'].get('rmse')
        
        db.commit()
        
        logger.info("✅ Gradient boosting model training completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        training_log.status = "failed"
        training_log.training_completed_at = datetime.utcnow()
        training_log.error_message = str(e)
        training_log.error_traceback = traceback.format_exc()
        db.commit()
        raise

async def main():
    """Main training function"""
    db = next(get_db())
    
    try:
        # Train XGBoost and LightGBM
        results = await train_gradient_boosting_models(
            db=db,
            symbols=TRAINING_SYMBOLS,
            days=500,
            model_types=['xgb', 'lgb']
        )
        
        print("\n" + "="*60)
        print("TRAINING SUMMARY")
        print("="*60)
        for model_type, result in results.items():
            print(f"\n{model_type.upper()}:")
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  ✓ Status: {result.get('status', 'unknown')}")
                if 'rmse' in result:
                    print(f"  ✓ RMSE: {result['rmse']:.4f}")
                if 'mae' in result:
                    print(f"  ✓ MAE: {result['mae']:.4f}")
                if 'n_features' in result:
                    print(f"  ✓ Features: {result['n_features']}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"Training script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
