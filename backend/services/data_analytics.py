"""
Data Analytics Service
Historical performance tracking, signal analytics, market regime detection, sector rotation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from collections import defaultdict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DataAnalyticsService:
    """Data analytics and performance tracking"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def track_analysis_accuracy(
        self,
        analysis_id: str,
        symbol: str,
        predicted_price: float,
        predicted_direction: str,
        actual_price: Optional[float] = None,
        actual_direction: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Track analysis accuracy"""
        try:
            from core.database_unified import AnalysisAccuracy
            
            # Calculate accuracy if actual values provided
            accuracy = None
            if actual_price and actual_direction:
                price_error = abs(predicted_price - actual_price) / actual_price * 100
                direction_correct = (predicted_direction == actual_direction)
                accuracy = {
                    "price_error_pct": round(price_error, 2),
                    "direction_correct": direction_correct
                }
            
            record = AnalysisAccuracy(
                analysis_id=analysis_id,
                symbol=symbol,
                predicted_price=predicted_price,
                predicted_direction=predicted_direction,
                actual_price=actual_price,
                actual_direction=actual_direction,
                accuracy=accuracy,
                created_at=datetime.now()
            )
            
            db.add(record)
            db.commit()
            
            return {"success": True, "recorded": True}
            
        except Exception as e:
            logger.error(f"Error tracking analysis accuracy: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    async def analyze_signal_performance(
        self,
        user_id: Optional[int] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Analyze ML signal performance"""
        try:
            from core.database_unified import TradingSignal, AnalysisAccuracy
            
            # Query signals
            query = db.query(TradingSignal)
            
            if user_id:
                query = query.filter(TradingSignal.user_id == user_id)
            if symbol:
                query = query.filter(TradingSignal.symbol == symbol)
            if start_date:
                query = query.filter(TradingSignal.created_at >= start_date)
            if end_date:
                query = query.filter(TradingSignal.created_at <= end_date)
            
            signals = query.all()
            
            if not signals:
                return {"success": False, "error": "No signals found"}
            
            # Analyze performance
            total_signals = len(signals)
            buy_signals = [s for s in signals if s.signal == "BUY"]
            sell_signals = [s for s in signals if s.signal == "SELL"]
            
            # Get accuracy data
            signal_ids = [s.id for s in signals]
            accuracy_records = db.query(AnalysisAccuracy).filter(
                AnalysisAccuracy.analysis_id.in_(signal_ids)
            ).all()
            
            correct_predictions = sum(1 for a in accuracy_records if a.accuracy and a.accuracy.get("direction_correct", False))
            total_with_accuracy = len(accuracy_records)
            
            accuracy_rate = (correct_predictions / total_with_accuracy * 100) if total_with_accuracy > 0 else 0
            
            return {
                "success": True,
                "total_signals": total_signals,
                "buy_signals": len(buy_signals),
                "sell_signals": len(sell_signals),
                "accuracy_rate": round(accuracy_rate, 2),
                "correct_predictions": correct_predictions,
                "total_evaluated": total_with_accuracy
            }
            
        except Exception as e:
            logger.error(f"Error analyzing signal performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_market_regime(
        self,
        symbol: str,
        lookback_days: int = 60
    ) -> Dict[str, Any]:
        """Detect current market regime"""
        try:
            from services.data_fetcher import fetch_historical_data
            
            # Get historical data
            candles = await fetch_historical_data(symbol, timeframe="1d", days=lookback_days)
            
            if not candles or len(candles) < 30:
                return {"success": False, "error": "Insufficient data"}
            
            df = pd.DataFrame(candles)
            df['returns'] = df['close'].pct_change()
            
            # Calculate volatility
            volatility = df['returns'].std() * np.sqrt(252)  # Annualized
            
            # Calculate trend
            sma_20 = df['close'].rolling(20).mean()
            sma_50 = df['close'].rolling(50).mean() if len(df) >= 50 else sma_20
            
            current_price = df['close'].iloc[-1]
            trend = "BULLISH" if current_price > sma_20.iloc[-1] else "BEARISH"
            
            # Determine regime
            if volatility > 0.3:
                regime = "HIGH_VOLATILITY"
            elif volatility < 0.15:
                regime = "LOW_VOLATILITY"
            else:
                regime = "NORMAL"
            
            # Market condition
            if trend == "BULLISH" and regime == "LOW_VOLATILITY":
                condition = "TRENDING_UP"
            elif trend == "BEARISH" and regime == "LOW_VOLATILITY":
                condition = "TRENDING_DOWN"
            elif regime == "HIGH_VOLATILITY":
                condition = "CHOPPY"
            else:
                condition = "SIDEWAYS"
            
            return {
                "success": True,
                "regime": regime,
                "trend": trend,
                "condition": condition,
                "volatility": round(volatility, 4),
                "volatility_pct": round(volatility * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_sector_rotation(
        self,
        sectors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze sector rotation and performance"""
        try:
            # Default sectors
            if not sectors:
                sectors = ["IT", "BANKING", "PHARMA", "AUTO", "FMCG", "ENERGY"]
            
            sector_performance = {}
            
            # Sector symbols mapping (simplified)
            sector_symbols = {
                "IT": ["TCS", "INFY", "WIPRO", "HCLTECH"],
                "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK"],
                "PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "LUPIN"],
                "AUTO": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO"],
                "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA"],
                "ENERGY": ["RELIANCE", "ONGC", "BPCL", "IOC"]
            }
            
            for sector in sectors:
                symbols = sector_symbols.get(sector, [])
                if not symbols:
                    continue
                
                # Get performance for sector stocks
                from services.data_fetcher import fetch_historical_data
                
                sector_returns = []
                for symbol in symbols[:2]:  # Limit to 2 stocks per sector for performance
                    try:
                        candles = await fetch_historical_data(symbol, timeframe="1d", days=30)
                        if candles and len(candles) > 1:
                            return_pct = ((candles[-1]['close'] - candles[0]['close']) / candles[0]['close']) * 100
                            sector_returns.append(return_pct)
                    except:
                        continue
                
                if sector_returns:
                    avg_return = np.mean(sector_returns)
                    sector_performance[sector] = {
                        "avg_return": round(avg_return, 2),
                        "stock_count": len(sector_returns)
                    }
            
            # Rank sectors
            ranked_sectors = sorted(
                sector_performance.items(),
                key=lambda x: x[1]["avg_return"],
                reverse=True
            )
            
            return {
                "success": True,
                "sector_performance": dict(sector_performance),
                "ranked_sectors": [{"sector": s[0], "return": s[1]["avg_return"]} for s in ranked_sectors],
                "top_sector": ranked_sectors[0][0] if ranked_sectors else None,
                "bottom_sector": ranked_sectors[-1][0] if ranked_sectors else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sector rotation: {e}")
            return {"success": False, "error": str(e)}

# Create singleton instance
data_analytics_service = DataAnalyticsService()

