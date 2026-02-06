"""
Technical Indicators API
Provides advanced technical indicators for trading analysis
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from services.technical_indicators import TechnicalIndicatorsService
from api.routes.comprehensive_trading import fetch_historical_data, normalize_symbol_for_yahoo

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the technical indicators service
technical_service = TechnicalIndicatorsService()

@router.get("/technical-indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    timeframe: str = Query(default="5m", description="Timeframe (1m, 5m, 15m, 1h, 1d)"),
    period: int = Query(default=100, description="Number of periods to analyze")
):
    """
    Get comprehensive technical indicators for a symbol
    """
    try:
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        
        # Fetch historical data
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=period)
        
        if not candles or len(candles) == 0:
            # Generate sample data if no real data available
            logger.warning(f"No historical data for {symbol}, generating sample indicators")
            sample_data = generate_sample_technical_data(symbol, period)
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": sample_data,
                "timestamp": datetime.now().isoformat(),
                "source": "sample_data"
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        
        # Calculate all advanced indicators
        indicators = technical_service.calculate_all_advanced_indicators(data)
        
        # Generate historical indicator data for charting
        historical_data = generate_historical_indicators(data, indicators)
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "current_indicators": indicators,
            "historical_data": historical_data,
            "timestamp": datetime.now().isoformat(),
            "source": "calculated"
        }
        
    except Exception as e:
        logger.error(f"Error getting technical indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating technical indicators: {str(e)}")

@router.get("/technical-indicators/{symbol}/real-time")
async def get_real_time_indicators(
    symbol: str,
    timeframe: str = Query(default="5m", description="Timeframe")
):
    """
    Get real-time technical indicators for a symbol
    """
    try:
        # Get current indicators (faster calculation for real-time)
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=50)
        
        if not candles or len(candles) == 0:
            # Return sample data
            current_price = np.random.uniform(1000, 5000)
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "indicators": {
                    "rsi": np.random.uniform(20, 80),
                    "macd": np.random.uniform(-2, 2),
                    "bollinger_upper": current_price * 1.02,
                    "bollinger_lower": current_price * 0.98,
                    "sma_20": current_price * np.random.uniform(0.98, 1.02),
                    "ema_12": current_price * np.random.uniform(0.99, 1.01),
                    "atr": current_price * np.random.uniform(0.01, 0.03),
                    "volume_sma": np.random.uniform(5000, 50000)
                },
                "timestamp": datetime.now().isoformat(),
                "source": "sample_data"
            }
        
        data = pd.DataFrame(candles)
        indicators = technical_service.calculate_all_advanced_indicators(data)
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "indicators": indicators,
            "timestamp": datetime.now().isoformat(),
            "source": "calculated"
        }
        
    except Exception as e:
        logger.error(f"Error getting real-time indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating real-time indicators: {str(e)}")

@router.get("/technical-indicators/batch")
async def get_batch_technical_indicators(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    timeframe: str = Query(default="5m", description="Timeframe")
):
    """
    Get technical indicators for multiple symbols
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        results = {}
        
        for symbol in symbol_list:
            try:
                # Get real-time indicators for each symbol
                normalized_symbol = normalize_symbol_for_yahoo(symbol)
                candles = await fetch_historical_data(normalized_symbol, timeframe, days=50)
                
                if not candles or len(candles) == 0:
                    # Generate sample data
                    current_price = np.random.uniform(1000, 5000)
                    results[symbol] = {
                        "rsi": np.random.uniform(20, 80),
                        "macd": np.random.uniform(-2, 2),
                        "bollinger_upper": current_price * 1.02,
                        "bollinger_lower": current_price * 0.98,
                        "sma_20": current_price * np.random.uniform(0.98, 1.02),
                        "ema_12": current_price * np.random.uniform(0.99, 1.01),
                        "atr": current_price * np.random.uniform(0.01, 0.03),
                        "volume_sma": np.random.uniform(5000, 50000),
                        "source": "sample_data"
                    }
                else:
                    data = pd.DataFrame(candles)
                    indicators = technical_service.calculate_all_advanced_indicators(data)
                    indicators["source"] = "calculated"
                    results[symbol] = indicators
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                # Add error entry
                results[symbol] = {
                    "error": str(e),
                    "source": "error"
                }
        
        return {
            "success": True,
            "symbols": symbol_list,
            "timeframe": timeframe,
            "indicators": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting batch technical indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating batch indicators: {str(e)}")

def generate_sample_technical_data(symbol: str, period: int) -> List[Dict]:
    """Generate sample technical indicator data for charting"""
    try:
        # Generate sample price data
        dates = pd.date_range(end=datetime.now(), periods=period, freq='5min')
        base_price = np.random.uniform(1000, 5000)
        
        # Generate realistic price movements
        prices = [base_price]
        for i in range(1, period):
            change = np.random.normal(0, 0.002)  # 0.2% volatility
            prices.append(prices[-1] * (1 + change))
        
        # Generate sample indicators
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # Calculate RSI-like oscillator
            rsi_value = 50 + 30 * np.sin(i * 0.1) + np.random.normal(0, 5)
            rsi_value = max(0, min(100, rsi_value))
            
            # Calculate MACD-like oscillator
            macd_value = 0.5 * np.sin(i * 0.05) + np.random.normal(0, 0.1)
            
            # Calculate Bollinger Bands
            bb_upper = price * 1.02
            bb_lower = price * 0.98
            
            # Calculate moving averages
            sma_20 = price * (1 + np.random.normal(0, 0.005))
            ema_12 = price * (1 + np.random.normal(0, 0.003))
            
            # Calculate ATR
            atr = price * np.random.uniform(0.01, 0.03)
            
            # Calculate Volume SMA
            volume_sma = np.random.uniform(5000, 50000)
            
            data.append({
                "timestamp": date.isoformat(),
                "price": price,
                "rsi": rsi_value,
                "macd": macd_value,
                "bollinger_upper": bb_upper,
                "bollinger_lower": bb_lower,
                "sma_20": sma_20,
                "ema_12": ema_12,
                "atr": atr,
                "volume_sma": volume_sma
            })
        
        return data
        
    except Exception as e:
        logger.error(f"Error generating sample technical data: {e}")
        return []

def generate_historical_indicators(data: pd.DataFrame, current_indicators: Dict) -> List[Dict]:
    """Generate historical indicator data for charting"""
    try:
        historical_data = []
        
        # Calculate indicators for each data point
        for i in range(len(data)):
            if i < 20:  # Need minimum data for some indicators
                continue
            
            # Get subset of data up to current point
            subset = data.iloc[:i+1]
            
            # Calculate indicators for this point
            indicators = technical_service.calculate_all_advanced_indicators(subset)
            
            historical_data.append({
                "timestamp": data.index[i].isoformat(),
                "price": float(data.iloc[i]['close']),
                "rsi": indicators['rsi'],
                "macd": indicators['macd'],
                "bollinger_upper": indicators['bollinger_upper'],
                "bollinger_lower": indicators['bollinger_lower'],
                "sma_20": indicators['sma_20'],
                "ema_12": indicators['ema_12'],
                "atr": indicators['atr'],
                "volume_sma": indicators['volume_sma']
            })
        
        return historical_data[-100:]  # Return last 100 points
        
    except Exception as e:
        logger.error(f"Error generating historical indicators: {e}")
        return []
