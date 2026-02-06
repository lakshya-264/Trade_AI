"""
Training Script for Temporal Models (LSTM/Transformer) for 1-Week Predictions
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
from services.temporal_models import TemporalModels
from services.data_fetcher import fetch_historical_data
from services.prediction_tracking_service import prediction_tracking_service
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

async def prepare_training_data(symbols: list, days: int = 365) -> pd.DataFrame:
    """Prepare training data from multiple symbols"""
    all_data = []
    
    for symbol in symbols:
        try:
            logger.info(f"Fetching data for {symbol}...")
            candles = await fetch_historical_data(symbol, "1d", days=days)
            
            if not candles or len(candles) < 60:
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

async def train_temporal_models(
    db: Session,
    symbols: list = None,
    days: int = 365,
    model_types: list = None
):
    """Train temporal models (LSTM and/or Transformer)"""
    
    if symbols is None:
        symbols = TRAINING_SYMBOLS
    
    if model_types is None:
        model_types = ['lstm', 'transformer']
    
    logger.info(f"Starting temporal model training for {len(symbols)} symbols")
    logger.info(f"Models to train: {model_types}")
    
    # Create training log
    training_log = ModelTrainingLog(
        model_type="temporal_ensemble",
        model_category="temporal",
        timeframe="1W",
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
        
        # Initialize temporal models service
        temporal_models = TemporalModels()
        
        # Prepare sequences
        logger.info("Preparing sequences...")
        features = ['open', 'high', 'low', 'close', 'volume']
        X, y = temporal_models.prepare_sequences(training_data, features)
        
        if len(X) == 0:
            raise ValueError("No sequences prepared from training data")
        
        logger.info(f"Prepared {len(X)} sequences for training")
        
        results = {}
        
        # Train LSTM
        if 'lstm' in model_types:
            logger.info("Training LSTM model...")
            try:
                lstm_result = temporal_models.train_lstm_model(training_data, features)
                results['lstm'] = lstm_result
                logger.info(f"✓ LSTM training completed: {lstm_result}")
            except Exception as e:
                logger.error(f"LSTM training failed: {e}")
                results['lstm'] = {"error": str(e)}
        
        # Train Transformer
        if 'transformer' in model_types:
            logger.info("Training Transformer model...")
            try:
                transformer_result = temporal_models.train_transformer_model(training_data, features)
                results['transformer'] = transformer_result
                logger.info(f"✓ Transformer training completed: {transformer_result}")
            except Exception as e:
                logger.error(f"Transformer training failed: {e}")
                results['transformer'] = {"error": str(e)}
        
        # Update training log
        training_log.status = "completed"
        training_log.training_completed_at = datetime.utcnow()
        training_log.training_metrics = results
        
        # Calculate average losses
        if 'lstm' in results and 'final_train_loss' in results['lstm']:
            training_log.train_loss = results['lstm'].get('final_train_loss')
            training_log.validation_loss = results['lstm'].get('final_val_loss')
        
        db.commit()
        
        logger.info("✅ Temporal model training completed successfully")
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
        # Train both LSTM and Transformer
        results = await train_temporal_models(
            db=db,
            symbols=TRAINING_SYMBOLS,
            days=365,
            model_types=['lstm', 'transformer']
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
                if 'final_train_loss' in result:
                    print(f"  ✓ Train Loss: {result['final_train_loss']:.6f}")
                if 'final_val_loss' in result:
                    print(f"  ✓ Val Loss: {result['final_val_loss']:.6f}")
        
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
