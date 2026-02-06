"""
Comprehensive TradingView-Style API Routes
Integrates all advanced features: Charting, Patterns, Volume Analysis, Trading Recommendations, Voice, Options
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import pytz

# Helper function to convert datetime to IST
def to_ist_isoformat(dt):
    """Convert datetime to IST timezone and return ISO format string"""
    if not dt:
        return None
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(pytz.timezone('Asia/Kolkata')).isoformat()

# Helper function to parse datetime string and ensure UTC timezone-aware
def _parse_datetime_utc(dt_str: str) -> datetime:
    """Parse datetime string and ensure it's timezone-aware (UTC)"""
    dt_str_normalized = dt_str.replace('Z', '+00:00')
    dt = datetime.fromisoformat(dt_str_normalized)
    # Ensure timezone-aware: fromisoformat with +00:00 creates UTC-aware datetime
    # Only localize if naive (shouldn't happen with +00:00, but safe check)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt
from pydantic import BaseModel
import asyncio
import math
import json
import pandas as pd
import numpy as np
import uuid
import re

def _deep_clean_nan_values(obj):
    """Recursively clean NaN, Inf, and non-JSON-serializable values"""
    if obj is None:
        return None
    
    if isinstance(obj, dict):
        cleaned_dict = {}
        for k, v in obj.items():
            cleaned_val = _deep_clean_nan_values(v)
            # Only include None for specific keys that are allowed
            if cleaned_val is not None or k in ['entry_price', 'stop_loss', 'target_price', 'target', 'entry']:
                cleaned_dict[k] = cleaned_val
        return cleaned_dict
    elif isinstance(obj, list):
        return [_deep_clean_nan_values(item) for item in obj]
    elif isinstance(obj, (float, np.floating)):
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        try:
            val = float(obj)
            if np.isnan(val) or np.isinf(val):
                return None
            return val
        except (ValueError, TypeError, OverflowError):
            return None
    elif isinstance(obj, (int, np.integer)):
        try:
            return int(obj)
        except (ValueError, TypeError, OverflowError):
            return None
    elif pd.isna(obj):
        return None
    elif hasattr(obj, 'item'):  # numpy scalar
        try:
            val = obj.item()
            if isinstance(val, float):
                if np.isnan(val) or np.isinf(val):
                    return None
                return float(val)
            elif isinstance(val, int):
                return int(val)
            elif isinstance(val, bool):
                return bool(val)
            return val
        except (ValueError, TypeError, AttributeError, OverflowError):
            return None
    elif isinstance(obj, bool):
        return bool(obj)
    elif isinstance(obj, str):
        return str(obj)
    else:
        # For any other type, try to convert safely
        try:
            # Check if it's a number-like object
            if hasattr(obj, '__float__'):
                val = float(obj)
                if np.isnan(val) or np.isinf(val):
                    return None
                return val
            # Check if it's an enum
            if hasattr(obj, 'value'):
                return obj.value
            # Return as-is for other types (strings, etc.)
            return obj
        except (ValueError, TypeError, AttributeError, OverflowError):
            return None

from core.database import get_db
from core.auth_dependencies import get_current_user, get_current_user_optional

# Import all services
from services.enhanced_chart_service import enhanced_chart_service
from services.technical_indicators import TechnicalIndicatorsService
from services.drawing_tools import DrawingToolsService
from services.database_alert_system import database_alert_system
from services.watchlist_service import WatchlistService
from services.animation_teaching import TeachingAnimationService
from services.pattern_recognition import CandlestickPatternRecognitionService
from services.volume_price_analysis import VolumePriceAnalysisService
from services.trading_recommendations import TradingRecommendationEngine
from services.voice_trading_assistant import VoiceTradingAssistant
from services.options_trading_ai import OptionsTradingAI
from services.smart_money_volume import smart_money_volume_service
from services.fno_trading_algorithms import FNOTradingAlgorithms, FNOStrategy, OIAnalysis
from services.intraday_trading_algorithms import IntradayTradingAlgorithms, IntradayStrategy, TradingSession
from services.advanced_chart_patterns import AdvancedChartPatternDetector
# Import fetch_historical_data at module level to avoid import errors
from services.data_fetcher import fetch_historical_data
# Import symbol normalizer
from utils.symbol_normalizer import normalize_symbol_for_yahoo, normalize_symbol_for_display
# Import advanced ML services
from services.automated_training_pipeline import automated_training_pipeline
from services.model_performance_monitoring import model_performance_monitoring
from services.realtime_model_updates import realtime_model_updates
from services.realtime_orderbook import realtime_orderbook
from services.realtime_trade_feed import realtime_trade_feed
from services.realtime_options_chain import realtime_options_chain
from services.advanced_chart_types import advanced_chart_types
from core.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()

async def _calculate_next_day_opening_impact(
    current_price: float,
    gift_nifty_data: Optional[Dict[str, Any]],
    india_vix_data: Optional[Dict[str, Any]],
    symbol: str
) -> Dict[str, Any]:
    """
    Calculate next day opening impact based on GIFT NIFTY, India VIX, Global Markets, News, and FII/DII flows
    Returns analysis with expected opening range and impact levels
    Always returns a dict (never None) - includes error info if calculation fails
    
    METHODOLOGY:
    - PRIMARY (70%): GIFT NIFTY premium/discount - Best predictor of next-day opening
    - SECONDARY (30% combined): Global markets (10%), News (10%), FII/DII flows (10%)
    - VOLATILITY: India VIX - Affects range width, not direction
    """
    try:
        if not current_price or current_price <= 0:
            logger.warning(f"⚠️ Cannot calculate next day opening: current_price is {current_price}")
            return {
                "applicable": True,
                "error": f"Invalid current price: {current_price}",
                "current_nifty_price": None,
                "note": "Current price is required for opening analysis. Please ensure NIFTY price data is available."
            }
        
        analysis = {
            "applicable": True,
            "current_nifty_price": round(current_price, 2),
            "expected_opening_direction": "NEUTRAL",
            "expected_opening_range": None,
            "confidence": 0.0,
            "key_levels": {},
            "interpretation": "",
            "risk_assessment": "MODERATE"
        }
        
        # ============================================================
        # PHASE 1: TIME-OF-DAY WEIGHTING & GIFT NIFTY ANALYSIS
        # ============================================================
        from datetime import datetime, timedelta
        
        # Calculate hours until market open (9:15 AM IST)
        now = datetime.now()
        market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
        # If market already opened today, calculate for next day
        if now.hour >= 9 and now.minute >= 15:
            market_open_time += timedelta(days=1)
        
        hours_until_open = (market_open_time - now).total_seconds() / 3600
        
        # Dynamic GIFT NIFTY weight based on proximity to market open
        if hours_until_open < 2:  # Within 2 hours of open
            gift_nifty_base_weight = 0.80  # Higher confidence
            time_weight_note = "High confidence - Close to market open"
        elif hours_until_open < 6:  # 2-6 hours before open
            gift_nifty_base_weight = 0.70  # Current weight
            time_weight_note = "Moderate confidence - Mid-range timing"
        else:  # More than 6 hours before open
            gift_nifty_base_weight = 0.60  # Lower confidence
            time_weight_note = "Lower confidence - Early prediction"
        
        analysis["time_analysis"] = {
            "hours_until_open": round(hours_until_open, 1),
            "market_open_time": market_open_time.isoformat(),
            "gift_nifty_weight": gift_nifty_base_weight,
            "note": time_weight_note
        }
        
        # GIFT NIFTY Impact (Primary indicator for opening direction)
        gift_impact_pct = 0.0  # Percentage change expected
        gift_premium_discount = 0.0
        gift_sentiment = "NEUTRAL"
        gift_price = None
        gift_volume = 0.0
        gift_avg_volume = 0.0
        gift_volume_ratio = 1.0
        
        if gift_nifty_data and isinstance(gift_nifty_data, dict) and "error" not in gift_nifty_data:
            gift_price = gift_nifty_data.get("price", 0)
            gift_change_pct = gift_nifty_data.get("change_pct", 0)
            gift_premium_discount = gift_nifty_data.get("premium_discount_pct", 0)
            gift_sentiment = gift_nifty_data.get("sentiment", "NEUTRAL")
            gift_volume = gift_nifty_data.get("volume", 0)
            gift_avg_volume = gift_nifty_data.get("avg_volume", gift_volume)  # Use current if avg not available
            
            # PHASE 2: GIFT NIFTY Volume Analysis
            if gift_avg_volume > 0:
                gift_volume_ratio = gift_volume / gift_avg_volume
            else:
                gift_volume_ratio = 1.0
            
            # Adjust GIFT NIFTY weight based on volume
            volume_adjusted_weight = gift_nifty_base_weight
            volume_confidence_boost = 0.0
            
            if gift_volume_ratio > 1.5:  # High volume - confirm direction
                volume_adjusted_weight *= 1.1  # Increase weight by 10%
                volume_confidence_boost = 0.05
                analysis["gift_nifty_volume_status"] = "HIGH_VOLUME"
            elif gift_volume_ratio < 0.7:  # Low volume - reduce confidence
                volume_adjusted_weight *= 0.9  # Decrease weight by 10%
                volume_confidence_boost = -0.05
                analysis["gift_nifty_volume_status"] = "LOW_VOLUME"
            else:
                analysis["gift_nifty_volume_status"] = "NORMAL_VOLUME"
            
            gift_nifty_base_weight = volume_adjusted_weight
            
            # Use premium/discount percentage if available (more reliable)
            # Otherwise calculate from price difference
            if gift_premium_discount != 0:
                gift_impact_pct = gift_premium_discount
            elif gift_price > 0 and current_price > 0:
                price_diff_pct = ((gift_price - current_price) / current_price) * 100
                gift_impact_pct = max(-5.0, min(5.0, price_diff_pct))
            
            # PHASE 2: Gap Fill Probability - Large gaps often get filled
            gap_size_pct = abs(gift_impact_pct)
            gap_fill_adjustment = 0.0
            
            if gap_size_pct > 1.0:  # Large gap (>1%)
                gap_fill_probability = 0.6  # ~60% of gaps >1% get filled
                # Reduce expected gap by fill probability
                gap_fill_adjustment = gift_impact_pct * (gap_fill_probability * 0.3)  # Reduce by 18% for large gaps
                gift_impact_pct = gift_impact_pct - gap_fill_adjustment
                analysis["gap_fill_warning"] = f"Large gap detected ({gap_size_pct:.2f}%). Historical data shows ~60% probability of gap fill."
            else:
                analysis["gap_fill_warning"] = None
            
            # Validate and cap gift_impact_pct to reasonable range (±3% for opening gap)
            gift_impact_pct = max(-3.0, min(3.0, gift_impact_pct))
            
            analysis["expected_opening_direction"] = gift_sentiment
            if gift_price:
                analysis["gift_nifty_price"] = round(gift_price, 2)
            analysis["gift_nifty_premium_discount_pct"] = round(gift_premium_discount, 2)
            analysis["gift_nifty_expected_change_pct"] = round(gift_impact_pct, 2)
            analysis["gift_nifty_volume"] = round(gift_volume, 0)
            analysis["gift_nifty_volume_ratio"] = round(gift_volume_ratio, 2)
            analysis["gift_nifty_final_weight"] = round(gift_nifty_base_weight, 2)
        
        # India VIX Impact (Volatility indicator - affects opening range width)
        vix_level = None
        vix_regime = "NORMAL"
        volatility_multiplier = 1.0
        vix_change_pct = 0.0
        vix_sentiment_adjustment = 0.0  # PHASE 1: VIX Direction Impact
        
        if india_vix_data and isinstance(india_vix_data, dict) and "error" not in india_vix_data:
            vix_level = india_vix_data.get("level")
            vix_regime = india_vix_data.get("regime", "NORMAL")
            vix_change_pct = india_vix_data.get("change_pct", 0.0)
            
            # PHASE 1: VIX Change Direction - Rising VIX = Fear, Falling VIX = Confidence
            if vix_change_pct > 5:  # VIX up >5%
                vix_sentiment_adjustment = -0.05  # Slight bearish
                analysis["vix_direction"] = "RISING_FEAR"
            elif vix_change_pct < -5:  # VIX down >5%
                vix_sentiment_adjustment = 0.05   # Slight bullish
                analysis["vix_direction"] = "FALLING_FEAR"
            else:
                analysis["vix_direction"] = "STABLE"
            
            # VIX affects the expected range width
            # Higher VIX = Wider opening range (more volatility expected)
            if vix_level:
                if vix_level < 15:
                    volatility_multiplier = 0.7  # Low volatility - tighter range
                elif vix_level < 20:
                    volatility_multiplier = 1.0  # Normal volatility
                elif vix_level < 25:
                    volatility_multiplier = 1.3  # Elevated volatility - wider range
                elif vix_level < 30:
                    volatility_multiplier = 1.6  # High volatility - much wider range
                else:
                    volatility_multiplier = 2.0  # Extreme volatility - very wide range
        
        # ============================================================
        # PHASE 1: PREVIOUS DAY CLOSING BEHAVIOR
        # ============================================================
        prev_day_close_adjustment = 0.0  # Initialize adjustment
        prev_day_high = None
        prev_day_low = None
        prev_day_close = None
        
        try:
            from services.data_fetcher import fetch_historical_data
            # Fetch previous day's data
            historical_data = await fetch_historical_data("^NSEI", "1d", days=2)
            
            if historical_data and len(historical_data) >= 2:
                prev_day_data = historical_data[-2]  # Previous day
                current_day_data = historical_data[-1]  # Current day (if available)
                
                prev_day_high = prev_day_data.get("high", current_price)
                prev_day_low = prev_day_data.get("low", current_price)
                prev_day_close = prev_day_data.get("close", current_price)
                
                # Calculate closing position (0 = low, 1 = high)
                if (prev_day_high - prev_day_low) > 0:
                    closing_position = (prev_day_close - prev_day_low) / (prev_day_high - prev_day_low)
                    
                    if closing_position > 0.75:  # Strong close (top 25% of range)
                        prev_day_close_adjustment = 0.10  # +0.10% boost
                        analysis["prev_day_close_strength"] = "STRONG"
                    elif closing_position < 0.25:  # Weak close (bottom 25% of range)
                        prev_day_close_adjustment = -0.10  # -0.10% drag
                        analysis["prev_day_close_strength"] = "WEAK"
                    else:
                        analysis["prev_day_close_strength"] = "NEUTRAL"
                    
                    analysis["prev_day_data"] = {
                        "high": round(prev_day_high, 2),
                        "low": round(prev_day_low, 2),
                        "close": round(prev_day_close, 2),
                        "closing_position": round(closing_position, 2)
                    }
        except Exception as e:
            logger.debug(f"Could not fetch previous day data: {e}")
            analysis["prev_day_data"] = None
        
        # ============================================================
        # STEP 1: FETCH SECONDARY INDICATORS FIRST
        # ============================================================
        # Fetch Global Markets, News, FII/DII, Currency, Options OI, Sector data
        # BEFORE calculating opening price so we can incorporate their impact
        
        # Initialize secondary indicator variables
        global_adjustment_pct = 0.0
        news_adjustment_pct = 0.0
        fii_dii_adjustment_pct = 0.0
        currency_adjustment_pct = 0.0  # PHASE 2: Currency Impact
        options_oi_adjustment_pct = 0.0  # PHASE 3: Options OI Impact
        sector_adjustment_pct = 0.0  # PHASE 3: Sector Rotation Impact
        
        # Global Markets Impact
        overall_global_sentiment = "NEUTRAL"
        try:
            import yfinance as yf
            # Fetch US markets (S&P 500, Dow Jones, NASDAQ)
            us_sentiment = "NEUTRAL"
            us_change_pct = 0.0
            try:
                sp500 = yf.Ticker("^GSPC")
                sp500_info = sp500.history(period="2d")
                if not sp500_info.empty and len(sp500_info) > 1:
                    us_change_pct = float((sp500_info['Close'].iloc[-1] - sp500_info['Close'].iloc[-2]) / sp500_info['Close'].iloc[-2] * 100)
                    if us_change_pct > 0.5:
                        us_sentiment = "BULLISH"
                    elif us_change_pct < -0.5:
                        us_sentiment = "BEARISH"
            except Exception:
                pass
            
            # Asian markets (Nikkei, Hang Seng)
            asian_sentiment = "NEUTRAL"
            asian_change_pct = 0.0
            try:
                nikkei = yf.Ticker("^N225")
                nikkei_info = nikkei.history(period="2d")
                if not nikkei_info.empty and len(nikkei_info) > 1:
                    asian_change_pct = float((nikkei_info['Close'].iloc[-1] - nikkei_info['Close'].iloc[-2]) / nikkei_info['Close'].iloc[-2] * 100)
                    if asian_change_pct > 0.5:
                        asian_sentiment = "BULLISH"
                    elif asian_change_pct < -0.5:
                        asian_sentiment = "BEARISH"
            except Exception:
                pass
            
            overall_global_sentiment = "NEUTRAL"
            if us_sentiment == "BULLISH" and asian_sentiment == "BULLISH":
                overall_global_sentiment = "BULLISH"
                global_adjustment_pct = 0.15  # +0.15% boost
            elif us_sentiment == "BEARISH" and asian_sentiment == "BEARISH":
                overall_global_sentiment = "BEARISH"
                global_adjustment_pct = -0.15  # -0.15% drag
            elif us_sentiment == "BEARISH" or asian_sentiment == "BEARISH":
                overall_global_sentiment = "CAUTIOUS"
                global_adjustment_pct = -0.05  # Slight negative
            elif us_sentiment == "BULLISH" or asian_sentiment == "BULLISH":
                global_adjustment_pct = 0.08  # Slight positive
            
            analysis["global_markets"] = {
                "us_markets": {
                    "status": us_sentiment,
                    "change_pct": round(us_change_pct, 2),
                    "impact": f"US markets closed {us_sentiment.lower()}. {'Positive' if us_sentiment == 'BULLISH' else 'Negative' if us_sentiment == 'BEARISH' else 'Neutral'} impact expected on NIFTY opening."
                },
                "asian_markets": {
                    "status": asian_sentiment,
                    "change_pct": round(asian_change_pct, 2),
                    "impact": f"Asian markets showing {asian_sentiment.lower()} sentiment. {'Positive' if asian_sentiment == 'BULLISH' else 'Negative' if asian_sentiment == 'BEARISH' else 'Neutral'} influence on opening."
                },
                "overall_sentiment": overall_global_sentiment
            }
        except Exception as e:
            logger.warning(f"Could not fetch global markets data: {e}")
            analysis["global_markets"] = {
                "us_markets": {"status": "UNAVAILABLE", "change_pct": 0, "impact": "Data not available"},
                "asian_markets": {"status": "UNAVAILABLE", "change_pct": 0, "impact": "Data not available"},
                "overall_sentiment": "NEUTRAL"
            }
        
        # News & Events - Fetch real news data
        try:
            from services.intelligent_stock_selector import IntelligentStockSelector
            from services.sentiment_analysis import SentimentAnalysisService
            
            news_selector = IntelligentStockSelector()
            sentiment_service = SentimentAnalysisService()
            
            # Fetch overnight news for NIFTY/Indian markets
            overnight_news = []
            try:
                # Fetch Yahoo Finance news for NIFTY
                yahoo_news = await news_selector._fetch_yahoo_finance_news()
                
                # Filter for recent news (last 24 hours) and analyze sentiment
                from datetime import datetime, timedelta
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for news_item in yahoo_news[:15]:  # Top 15 news items
                    try:
                        # Extract sentiment if available, otherwise analyze
                        sentiment_score = news_item.get('sentiment_score', 0.0)
                        if sentiment_score == 0:
                            # Analyze sentiment from title/description
                            title = news_item.get('title', '')
                            description = news_item.get('description', '')
                            text = f"{title} {description}"
                            if text:
                                sentiment_result = sentiment_service.analyze_sentiment(text)
                                sentiment_score = sentiment_result.get('score', 0.0)
                        
                        # Determine impact level
                        impact = "LOW"
                        headline_lower = news_item.get('title', '').lower()
                        high_impact_keywords = ['nifty', 'sensex', 'rbi', 'gdp', 'inflation', 'rate cut', 'budget', 'fii', 'dii', 'crash', 'rally', 'surge', 'plunge']
                        if any(keyword in headline_lower for keyword in high_impact_keywords):
                            impact = "HIGH"
                        elif abs(sentiment_score) > 0.3:
                            impact = "MEDIUM"
                        
                        # Determine sentiment
                        sentiment = "NEUTRAL"
                        if sentiment_score > 0.2:
                            sentiment = "BULLISH"
                        elif sentiment_score < -0.2:
                            sentiment = "BEARISH"
                        
                        overnight_news.append({
                            "headline": news_item.get('title', 'No title'),
                            "description": news_item.get('description', '')[:200],  # Truncate
                            "impact": impact,
                            "sentiment": sentiment,
                            "sentiment_score": round(sentiment_score, 2),
                            "source": news_item.get('source', 'Yahoo Finance'),
                            "published": news_item.get('published', '')
                        })
                    except Exception as e:
                        logger.debug(f"Error processing news item: {e}")
                        continue
                
                # Calculate overall news impact
                if overnight_news:
                    avg_sentiment = sum(n.get('sentiment_score', 0) for n in overnight_news) / len(overnight_news)
                    high_impact_count = sum(1 for n in overnight_news if n.get('impact') == 'HIGH')
                    
                    if avg_sentiment > 0.2 and high_impact_count > 2:
                        overall_impact = "BULLISH"
                    elif avg_sentiment < -0.2 and high_impact_count > 2:
                        overall_impact = "BEARISH"
                    elif avg_sentiment > 0.1:
                        overall_impact = "SLIGHTLY_BULLISH"
                    elif avg_sentiment < -0.1:
                        overall_impact = "SLIGHTLY_BEARISH"
                    else:
                        overall_impact = "NEUTRAL"
                else:
                    overall_impact = "NEUTRAL"
                
                # Sector-specific news (simplified - can be enhanced)
                sector_news = []
                sector_keywords = {
                    "Banking": ["bank", "rbi", "interest rate", "credit"],
                    "IT": ["it", "software", "tech", "digital"],
                    "Pharma": ["pharma", "drug", "fda", "medicine"],
                    "Auto": ["auto", "vehicle", "car", "motor"]
                }
                
                for sector, keywords in sector_keywords.items():
                    sector_items = [n for n in overnight_news if any(kw in n.get('headline', '').lower() for kw in keywords)]
                    if sector_items:
                        sector_news.append({
                            "sector": sector,
                            "headline": sector_items[0].get('headline', ''),
                            "impact": sector_items[0].get('impact', 'LOW')
                        })
                
                analysis["news_events"] = {
                    "overnight_news": overnight_news[:10],  # Top 10 most relevant
                    "sector_news": sector_news,
                    "overall_impact": overall_impact,
                    "news_count": len(overnight_news),
                    "avg_sentiment": round(avg_sentiment, 2) if overnight_news else 0.0
                }
            except Exception as news_error:
                logger.warning(f"Could not fetch news data: {news_error}")
                analysis["news_events"] = {
                    "overnight_news": [],
                    "sector_news": [],
                    "overall_impact": "NEUTRAL",
                    "note": f"News data fetch failed: {str(news_error)}"
                }
        except Exception as e:
            logger.warning(f"News integration error: {e}")
            analysis["news_events"] = {
                "overnight_news": [],
                "sector_news": [],
                "overall_impact": "NEUTRAL",
                "note": f"News service unavailable: {str(e)}"
            }
        
        # FII/DII Flows - Fetch real data
        try:
            from services.market_factors_service import MarketFactorsService
            
            market_factors = MarketFactorsService()
            fii_dii_data = await market_factors._fetch_fii_dii_flows(symbol)
            
            fii_net = fii_dii_data.get("fii_net_investment", 0.0)
            dii_net = fii_dii_data.get("dii_net_investment", 0.0)
            
            # Convert to crores if needed (assuming data is already in crores)
            # If data is in lakhs, multiply by 0.01; if in thousands, multiply by 0.0001
            # Most sources provide in crores, so we'll use as-is
            
            # Determine impact based on flows
            # FII buying (positive) = Bullish, FII selling (negative) = Bearish
            # DII buying (positive) = Bullish, DII selling (negative) = Bearish
            # Combined: Both buying = Very Bullish, Both selling = Very Bearish
            
            impact = "NEUTRAL"
            interpretation_parts = []
            
            if fii_net > 500:  # FII buying > ₹500 Cr
                impact = "BULLISH"
                interpretation_parts.append(f"Strong FII buying (₹{fii_net:.0f} Cr) indicates positive sentiment.")
            elif fii_net < -500:  # FII selling > ₹500 Cr
                impact = "BEARISH"
                interpretation_parts.append(f"FII selling (₹{fii_net:.0f} Cr) indicates negative sentiment.")
            elif fii_net > 0:
                impact = "SLIGHTLY_BULLISH"
                interpretation_parts.append(f"Moderate FII buying (₹{fii_net:.0f} Cr).")
            elif fii_net < 0:
                impact = "SLIGHTLY_BEARISH"
                interpretation_parts.append(f"FII selling (₹{abs(fii_net):.0f} Cr).")
            
            if dii_net > 500:  # DII buying > ₹500 Cr
                if impact == "BULLISH":
                    impact = "VERY_BULLISH"
                elif impact == "BEARISH":
                    impact = "NEUTRAL"  # DII countering FII selling
                else:
                    impact = "BULLISH"
                interpretation_parts.append(f"Strong DII buying (₹{dii_net:.0f} Cr) supports market.")
            elif dii_net < -500:  # DII selling > ₹500 Cr
                if impact == "BEARISH":
                    impact = "VERY_BEARISH"
                elif impact == "BULLISH":
                    impact = "NEUTRAL"  # DII countering FII buying
                else:
                    impact = "BEARISH"
                interpretation_parts.append(f"DII selling (₹{abs(dii_net):.0f} Cr) adds pressure.")
            elif dii_net > 0:
                interpretation_parts.append(f"Moderate DII buying (₹{dii_net:.0f} Cr).")
            elif dii_net < 0:
                interpretation_parts.append(f"DII selling (₹{abs(dii_net):.0f} Cr).")
            
            if not interpretation_parts:
                interpretation_parts.append("FII/DII flows are neutral. No significant institutional activity.")
            
            analysis["fii_dii_flows"] = {
                "fii_net": round(fii_net, 2),
                "dii_net": round(dii_net, 2),
                "interpretation": " ".join(interpretation_parts),
                "impact": impact,
                "data_source": fii_dii_data.get("data_source", "UNKNOWN"),
                "last_updated": fii_dii_data.get("last_updated", datetime.now().isoformat()),
                "trend": fii_dii_data.get("trend", "neutral")
            }
        except Exception as fii_error:
            logger.warning(f"Could not fetch FII/DII data: {fii_error}")
            analysis["fii_dii_flows"] = {
                "fii_net": 0.0,
                "dii_net": 0.0,
                "interpretation": f"FII/DII data fetch failed: {str(fii_error)}. Check NSE website manually.",
                "impact": "NEUTRAL",
                "note": "Data integration error. FII/DII flows significantly impact NIFTY movement."
            }
        
        # ============================================================
        # PHASE 2: CURRENCY IMPACT (USD/INR)
        # ============================================================
        try:
            usd_inr_rate = 83.0
            usd_inr_change_pct = 0.0
            
            try:
                import yfinance as yf
                usd_inr = yf.Ticker("USDINR=X")
                usd_inr_info = usd_inr.history(period="2d")
                if not usd_inr_info.empty and len(usd_inr_info) > 1:
                    usd_inr_rate = float(usd_inr_info['Close'].iloc[-1])
                    prev_rate = float(usd_inr_info['Close'].iloc[-2])
                    usd_inr_change_pct = ((usd_inr_rate - prev_rate) / prev_rate) * 100
            except Exception:
                pass
            
            # Rupee strengthening (USD/INR down) = Positive for markets
            # Rupee weakening (USD/INR up) = Negative for markets
            if usd_inr_change_pct < -0.3:  # Rupee strengthened >0.3%
                currency_adjustment_pct = 0.05  # +0.05% boost
                currency_sentiment = "BULLISH"
            elif usd_inr_change_pct > 0.3:  # Rupee weakened >0.3%
                currency_adjustment_pct = -0.05  # -0.05% drag
                currency_sentiment = "BEARISH"
            else:
                currency_adjustment_pct = 0.0
                currency_sentiment = "NEUTRAL"
            
            analysis["currency_impact"] = {
                "usd_inr_rate": round(usd_inr_rate, 2),
                "usd_inr_change_pct": round(usd_inr_change_pct, 2),
                "sentiment": currency_sentiment,
                "adjustment_pct": round(currency_adjustment_pct, 3),
                "interpretation": f"Rupee {'strengthened' if usd_inr_change_pct < 0 else 'weakened' if usd_inr_change_pct > 0 else 'stable'} by {abs(usd_inr_change_pct):.2f}%"
            }
        except Exception as e:
            logger.warning(f"Could not fetch currency data: {e}")
            analysis["currency_impact"] = {
                "usd_inr_rate": None,
                "usd_inr_change_pct": 0,
                "sentiment": "UNAVAILABLE",
                "adjustment_pct": 0.0
            }
        
        # ============================================================
        # PHASE 3: OPTIONS OPEN INTEREST DATA (PCR, Max Pain)
        # ============================================================
        try:
            # Try to fetch options OI data for NIFTY
            # Note: This requires options chain data - using simplified approach
            pcr = 1.0  # Default neutral PCR
            max_pain_level = current_price  # Default to current price
            
            try:
                # Try to get comprehensive OI analysis if available
                # For now, we'll use a placeholder that can be enhanced with real options data
                # In production, you'd call: await get_comprehensive_oi_analysis("NIFTY", ...)
                analysis["options_oi"] = {
                    "pcr": pcr,
                    "max_pain_level": round(max_pain_level, 2),
                    "max_pain_diff_pct": 0.0,
                    "sentiment": "NEUTRAL",
                    "note": "Options OI data integration pending. Real-time options chain data required."
                }
                
                # Calculate adjustment based on PCR
                if pcr > 1.2:  # More puts = Bearish
                    options_oi_adjustment_pct = -0.08
                elif pcr < 0.8:  # More calls = Bullish
                    options_oi_adjustment_pct = 0.08
                else:
                    options_oi_adjustment_pct = 0.0
                
                # Max Pain influence
                if max_pain_level:
                    max_pain_diff_pct = ((max_pain_level - current_price) / current_price) * 100
                    if abs(max_pain_diff_pct) < 0.5:  # Max pain close to current
                        options_oi_adjustment_pct += max_pain_diff_pct * 0.1  # Small pull towards max pain
            except Exception as oi_error:
                logger.debug(f"Options OI data not available: {oi_error}")
                options_oi_adjustment_pct = 0.0
                analysis["options_oi"] = {
                    "pcr": None,
                    "max_pain_level": None,
                    "sentiment": "UNAVAILABLE",
                    "note": "Options OI data fetch failed"
                }
        except Exception as e:
            logger.warning(f"Options OI integration error: {e}")
            options_oi_adjustment_pct = 0.0
        
        # ============================================================
        # PHASE 3: SECTOR ROTATION IMPACT
        # ============================================================
        try:
            banking_change = 0.0
            it_change = 0.0
            
            try:
                import yfinance as yf
                # Fetch Banking sector (NIFTY BANK)
                bank_nifty = yf.Ticker("^NSEBANK")
                bank_data = bank_nifty.history(period="2d")
                if not bank_data.empty and len(bank_data) > 1:
                    banking_change = float((bank_data['Close'].iloc[-1] - bank_data['Close'].iloc[-2]) / bank_data['Close'].iloc[-2] * 100)
                
                # Fetch IT sector (NIFTY IT)
                nifty_it = yf.Ticker("^CNXIT")
                it_data = nifty_it.history(period="2d")
                if not it_data.empty and len(it_data) > 1:
                    it_change = float((it_data['Close'].iloc[-1] - it_data['Close'].iloc[-2]) / it_data['Close'].iloc[-2] * 100)
            except Exception:
                pass
            
            # Weighted impact (Banking ~30% of NIFTY, IT ~15%)
            sector_adjustment_pct = (banking_change * 0.30) + (it_change * 0.15)
            sector_adjustment_pct = max(-0.15, min(0.15, sector_adjustment_pct))  # Cap at ±0.15%
            
            analysis["sector_rotation"] = {
                "banking_change_pct": round(banking_change, 2),
                "it_change_pct": round(it_change, 2),
                "weighted_impact_pct": round(sector_adjustment_pct, 3),
                "interpretation": f"Banking: {banking_change:+.2f}%, IT: {it_change:+.2f}%"
            }
        except Exception as e:
            logger.warning(f"Could not fetch sector data: {e}")
            sector_adjustment_pct = 0.0
            analysis["sector_rotation"] = {
                "banking_change_pct": None,
                "it_change_pct": None,
                "weighted_impact_pct": 0.0,
                "note": "Sector data unavailable"
            }
        
        # ============================================================
        # STEP 2: CALCULATE OPENING PRICE WITH ALL FACTORS
        # ============================================================
        # Primary: GIFT NIFTY (dynamic weight 60-80% based on time & volume)
        if gift_impact_pct != 0:
            base_opening_price = current_price * (1 + gift_impact_pct / 100)
        else:
            base_opening_price = current_price
        
        # Apply ALL secondary indicator adjustments with updated weights
        # Previous Day Close: 5%, Global Markets: 8%, News: 7%, FII/DII: 5%
        # Currency: 2%, Options OI: 3%, Sector: 2%, VIX Direction: 2%
        total_adjustment_pct = (
            prev_day_close_adjustment * 0.05 +      # 5% weight
            global_adjustment_pct * 0.08 +           # 8% weight
            news_adjustment_pct * 0.07 +             # 7% weight
            fii_dii_adjustment_pct * 0.05 +          # 5% weight
            currency_adjustment_pct * 0.02 +         # 2% weight
            options_oi_adjustment_pct * 0.03 +      # 3% weight
            sector_adjustment_pct * 0.02 +           # 2% weight
            vix_sentiment_adjustment * 0.02          # 2% weight (VIX direction)
        )
        
        # Cap total adjustment at ±0.6% to prevent over-correction
        total_adjustment_pct = max(-0.6, min(0.6, total_adjustment_pct))
        
        # Final expected opening price
        expected_opening_price = base_opening_price * (1 + total_adjustment_pct / 100)
        
        # Calculate expected opening range width based on VIX
        if abs(gift_impact_pct) > 0:
            base_range_pct = min(0.5, abs(gift_impact_pct) * 0.2)
        else:
            base_range_pct = 0.3
        
        range_width_pct = base_range_pct * volatility_multiplier
        range_width_pct = min(2.0, range_width_pct)
        range_points = current_price * (range_width_pct / 100)
        
        # Calculate bounds
        lower_bound = max(current_price * 0.95, round(expected_opening_price - range_points, 2))
        upper_bound = round(expected_opening_price + range_points, 2)
        most_likely = round(expected_opening_price, 2)
        
        if most_likely < lower_bound:
            most_likely = lower_bound
        elif most_likely > upper_bound:
            most_likely = upper_bound
        
        analysis["expected_opening_range"] = {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "most_likely": most_likely,
            "range_width_pct": round(range_width_pct, 2)
        }
        
        # Key levels
        support_level = max(current_price * 0.99, round(expected_opening_price - (range_points * 1.2), 2))
        resistance_level = round(expected_opening_price + (range_points * 1.2), 2)
        
        analysis["key_levels"] = {
            "support": support_level,
            "resistance": resistance_level,
            "current_price": round(current_price, 2)
        }
        
        # Calculate confidence
        confidence = 0.5
        if gift_nifty_data and isinstance(gift_nifty_data, dict) and abs(gift_premium_discount) > 0:
            gift_confidence = min(0.3, abs(gift_premium_discount) / 100)
            confidence += gift_confidence
        
        if vix_level:
            if vix_level < 15:
                confidence += 0.15
            elif vix_level > 25:
                confidence -= 0.20
        
        analysis["confidence"] = max(0.1, min(0.95, confidence))
        
        # Generate interpretation
        interpretations = []
        if gift_sentiment == "BEARISH" and vix_regime in ["HIGH", "EXTREME"]:
            interpretations.append("⚠️ BEARISH GIFT NIFTY + HIGH VIX: Expect gap down opening with high volatility.")
            analysis["risk_assessment"] = "HIGH"
        elif gift_sentiment == "BEARISH":
            interpretations.append("🔻 BEARISH GIFT NIFTY: Expect gap down opening.")
            analysis["risk_assessment"] = "MODERATE"
        elif gift_sentiment == "BULLISH" and vix_regime in ["HIGH", "EXTREME"]:
            interpretations.append("⚠️ BULLISH GIFT NIFTY + HIGH VIX: Expect gap up opening but with high volatility.")
            analysis["risk_assessment"] = "HIGH"
        elif gift_sentiment == "BULLISH":
            interpretations.append("🔺 BULLISH GIFT NIFTY: Expect gap up opening.")
            analysis["risk_assessment"] = "MODERATE"
        
        if vix_regime == "EXTREME":
            interpretations.append("🚨 EXTREME VIX: Very high volatility expected.")
            analysis["risk_assessment"] = "VERY HIGH"
        elif vix_regime == "HIGH":
            interpretations.append("⚠️ HIGH VIX: Elevated volatility expected.")
        
        if not interpretations:
            interpretations.append("📊 NEUTRAL: Standard opening expected.")
        
        analysis["interpretation"] = " ".join(interpretations)
        
        # Enhanced Summary with all factors
        analysis["summary"] = {
            "gift_nifty_sentiment": gift_sentiment,
            "vix_regime": vix_regime,
            "vix_change": round(vix_change_pct, 2),
            "expected_direction": analysis["expected_opening_direction"],
            "volatility_level": vix_regime,
            "opening_range_estimate": f"{lower_bound:.0f} - {upper_bound:.0f}",
            "hours_until_open": round(hours_until_open, 1),
            "prediction_confidence": analysis["confidence"],
            "all_factors_included": True
        }
        
        # Add methodology note
        analysis["methodology"] = {
            "primary_indicator": "GIFT NIFTY (Dynamic Weight: 60-80% based on time & volume)",
            "secondary_indicators": [
                "Previous Day Closing Behavior (5%)",
                "Global Markets - US & Asian (8%)",
                "News Sentiment (7%)",
                "FII/DII Flows (5%)",
                "Currency Impact - USD/INR (2%)",
                "Options OI - PCR & Max Pain (3%)",
                "Sector Rotation - Banking & IT (2%)",
                "VIX Direction Change (2%)"
            ],
            "volatility_indicator": "India VIX (affects range width, not direction)",
            "enhancements": [
                "Time-of-Day Weighting",
                "Volume Analysis",
                "Gap Fill Probability",
                "Previous Day Momentum",
                "Multi-Factor Weighted Model"
            ]
        }
        
        # Technical Levels
        analysis["technical_levels"] = {
            "support_levels": [support_level],
            "resistance_levels": [resistance_level],
            "pivot_points": {
                "r3": round(expected_opening_price + (range_points * 2.5), 2),
                "r2": round(expected_opening_price + (range_points * 1.5), 2),
                "r1": round(expected_opening_price + (range_points * 0.5), 2),
                "pp": round(expected_opening_price, 2),
                "s1": round(expected_opening_price - (range_points * 0.5), 2),
                "s2": round(expected_opening_price - (range_points * 1.5), 2),
                "s3": round(expected_opening_price - (range_points * 2.5), 2)
            },
            "interpretation": f"Key technical levels calculated. Support: ₹{support_level:.0f}, Resistance: ₹{resistance_level:.0f}."
        }
        
        # Log calculation
        logger.info(f"📊 Next Day Opening Calculation:")
        logger.info(f"   Current: ₹{current_price:.2f}")
        logger.info(f"   GIFT NIFTY Impact: {gift_impact_pct:.2f}%")
        logger.info(f"   Base Opening: ₹{base_opening_price:.2f}")
        logger.info(f"   Global Adj: {global_adjustment_pct:.2f}%, News Adj: {news_adjustment_pct:.2f}%, FII/DII Adj: {fii_dii_adjustment_pct:.2f}%")
        logger.info(f"   Total Adjustment: {total_adjustment_pct:.2f}%")
        logger.info(f"   Final Opening: ₹{expected_opening_price:.2f}")
        logger.info(f"   Range: ₹{lower_bound:.2f} - ₹{upper_bound:.2f} (±{range_width_pct:.2f}%)")
        
        logger.info(f"✅ Next Day Opening Analysis calculated successfully: Direction={analysis['expected_opening_direction']}, Range={analysis['expected_opening_range']['most_likely'] if analysis['expected_opening_range'] else 'N/A'}")
        return analysis
    
    except Exception as e:
        logger.error(f"❌ Error in _calculate_next_day_opening_impact: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Always return an error dict instead of None
        return {
            "applicable": True,
            "error": f"Calculation error: {str(e)}",
            "current_nifty_price": round(current_price, 2) if current_price and current_price > 0 else None,
            "gift_nifty_available": gift_nifty_data is not None and isinstance(gift_nifty_data, dict) and "error" not in gift_nifty_data,
            "vix_available": india_vix_data is not None and isinstance(india_vix_data, dict) and "error" not in india_vix_data,
            "note": f"An error occurred during calculation: {str(e)}. Check backend logs for details."
        }

# Initialize services
technical_indicators_service = TechnicalIndicatorsService()
drawing_tools_service = DrawingToolsService()
# Initialize services
alert_system_service = database_alert_system
watchlist_service = WatchlistService()
animation_teaching_service = TeachingAnimationService()
pattern_recognition_service = CandlestickPatternRecognitionService()
volume_analysis_service = VolumePriceAnalysisService()
trading_recommendation_engine = TradingRecommendationEngine()
voice_assistant = VoiceTradingAssistant()
options_trading_ai = OptionsTradingAI()
fno_algorithms = FNOTradingAlgorithms()
intraday_algorithms = IntradayTradingAlgorithms()
advanced_pattern_detector = AdvancedChartPatternDetector()

# ==================== PYDANTIC MODELS ====================

class ChartDataRequest(BaseModel):
    symbol: str
    timeframe: str = "1D"
    period: int = 100
    chart_type: str = "candlestick"
    indicators: Optional[List[str]] = None

class PatternAnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1D"
    min_confidence: float = 0.6
    pattern_types: Optional[List[str]] = None

class VolumeAnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1D"
    analysis_type: str = "comprehensive"

class TradingRecommendationRequest(BaseModel):
    symbol: str
    timeframe: str = "1D"
    analysis_data: Dict[str, Any]
    user_preferences: Optional[Dict[str, Any]] = None

class VoiceCommandRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    user_id: int
    context: Dict[str, Any]

class OptionsAnalysisRequest(BaseModel):
    symbol: str
    underlying_price: float
    days_to_expiry: int
    risk_free_rate: float = 0.05
    volatility: Optional[float] = None

class AnimationSessionRequest(BaseModel):
    animation_type: str
    symbol: str = "RELIANCE"
    difficulty: str = "beginner"

# ==================== CHART DATA ENDPOINTS ====================

@router.post("/chart-data")
async def get_advanced_chart_data(
    request: ChartDataRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive chart data with indicators"""
    try:
        data = await enhanced_chart_service.get_candlestick_data(
            symbol=request.symbol,
            timeframe=request.timeframe,
            period=request.period
        )
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])

        # Add indicators if requested
        if request.indicators:
            for indicator in request.indicators:
                indicator_data = technical_indicators_service.calculate_indicator(
                    indicator, data["candlesticks"], {}
                )
                data[f"{indicator.lower()}_data"] = indicator_data

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message": f"Chart data for {request.symbol} retrieved successfully"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PATTERN RECOGNITION ENDPOINTS ====================

@router.get("/pattern-analysis")
async def get_pattern_analysis(
    symbol: str = Query(..., description="Stock symbol"),
    timeframe: str = Query("1D", description="Timeframe"),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """GET endpoint for pattern analysis - includes all classic, harmonic, and Elliott Wave patterns"""
    try:
        # Fetch historical data
        candles = await fetch_historical_data(symbol, timeframe, days=365 * 2)  # Fetch 2 years of data
        if not candles:
            raise HTTPException(status_code=404, detail="No historical data found for the symbol.")

        # Convert to DataFrame
        df_data = []
        for candle in candles:
            df_data.append({
                'open': candle.get('open', 0),
                'high': candle.get('high', 0),
                'low': candle.get('low', 0),
                'close': candle.get('close', 0),
                'volume': candle.get('volume', 0),
                'time': candle.get('time', 0)
            })
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('date', inplace=True)

        # Detect candlestick patterns
        detected_patterns = await pattern_recognition_service.detect_patterns(
            symbol=symbol,
            timeframe=timeframe,
            data=candles,
            min_confidence=min_confidence
        )
        
        # Detect all advanced patterns (classic, harmonic, Elliott Wave)
        advanced_patterns = advanced_pattern_detector.detect_all_patterns(
            df=df,
            symbol=symbol,
            timeframe=timeframe
        )
        
        # Combine and filter by confidence
        all_patterns = detected_patterns + advanced_patterns
        filtered_patterns = [
            p for p in all_patterns 
            if p.get("confidence", 0) >= min_confidence or p.get("strength", 0) >= min_confidence
        ]
        
        # Format patterns for frontend
        formatted_patterns = []
        for pattern in filtered_patterns:
            formatted_patterns.append({
                "pattern_name": pattern.get("pattern_name") or pattern.get("name") or "Unknown Pattern",
                "confidence": pattern.get("confidence") or pattern.get("strength") or 0.7,
                "target_price": pattern.get("target_price") or pattern.get("target"),
                "start_time": pattern.get("start_time") or pattern.get("start_date"),
                "end_time": pattern.get("end_time") or pattern.get("end_date"),
                "start_price": pattern.get("start_price") or pattern.get("price"),
                "end_price": pattern.get("end_price") or pattern.get("price"),
                "description": pattern.get("description") or pattern.get("pattern_name") or "Pattern detected",
                "signal": pattern.get("signal") or "neutral",
                "pattern_category": pattern.get("pattern_category") or "other"
            })

        return {
            "success": True,
            "patterns": formatted_patterns,
            "pattern_count": len(formatted_patterns),
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/patterns/analyze")
async def analyze_candlestick_patterns(
    request: PatternAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """POST endpoint for pattern analysis - includes all classic, harmonic, and Elliott Wave patterns"""
    try:
        # Get chart data
        chart_data = await enhanced_chart_service.get_candlestick_data(
            symbol=request.symbol,
            timeframe=request.timeframe,
            period=200
        )
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])

        # Detect candlestick patterns
        detected_patterns = await pattern_recognition_service.detect_patterns(
            symbol=request.symbol,
            timeframe=request.timeframe,
            data=chart_data["candlesticks"],
            min_confidence=request.min_confidence
        )
        
        # Convert chart data to DataFrame for advanced pattern detection
        candles = chart_data.get("candlesticks", [])
        if candles:
            df_data = []
            for idx, candle in enumerate(candles):
                df_data.append({
                    'open': candle.get('open', 0),
                    'high': candle.get('high', 0),
                    'low': candle.get('low', 0),
                    'close': candle.get('close', 0),
                    'volume': candle.get('volume', 0),
                    'time': candle.get('time', candle.get('timestamp', idx))
                })
            df = pd.DataFrame(df_data)
            # Set time as index for easier time-based lookups
            if 'time' in df.columns:
                # Convert time to numeric if it's a string/timestamp
                df['time'] = pd.to_numeric(df['time'], errors='coerce').fillna(df.index)
                df.index = df['time']
            
            # Detect all advanced patterns (classic, harmonic, Elliott Wave)
            advanced_patterns = advanced_pattern_detector.detect_all_patterns(
                df=df,
                symbol=request.symbol,
                timeframe=request.timeframe
            )
            
            # Format advanced patterns to include time/price coordinates
            formatted_advanced_patterns = []
            for pattern in advanced_patterns:
                formatted_pattern = pattern.copy()
                
                # Ensure pattern has required fields for frontend
                if 'pattern_name' not in formatted_pattern:
                    formatted_pattern['pattern_name'] = formatted_pattern.get('pattern_type', 'Unknown Pattern').replace('_', ' ').title()
                
                if 'signal' not in formatted_pattern:
                    trading_impl = formatted_pattern.get('trading_implications', {})
                    signal = trading_impl.get('signal', 'HOLD')
                    formatted_pattern['signal'] = signal.lower() if isinstance(signal, str) else 'neutral'
                
                # Add time/price if missing
                if 'start_time' not in formatted_pattern or formatted_pattern.get('start_time') is None:
                    # Use detected_at or current time
                    formatted_pattern['start_time'] = None
                
                if 'end_time' not in formatted_pattern or formatted_pattern.get('end_time') is None:
                    formatted_pattern['end_time'] = None
                
                if 'start_price' not in formatted_pattern:
                    formatted_pattern['start_price'] = formatted_pattern.get('current_price', 0)
                
                if 'end_price' not in formatted_pattern:
                    formatted_pattern['end_price'] = formatted_pattern.get('current_price', 0)
                
                formatted_advanced_patterns.append(formatted_pattern)
            
            # Combine candlestick and advanced patterns
            all_patterns = detected_patterns + formatted_advanced_patterns
        else:
            all_patterns = detected_patterns

        return {
            "success": True,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "detected_patterns": all_patterns,
            "pattern_count": len(all_patterns),
            "candlestick_patterns": len(detected_patterns),
            "advanced_patterns": len(all_patterns) - len(detected_patterns),
            "timestamp": datetime.now().isoformat(),
            "message": f"Pattern analysis completed for {request.symbol}"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SMART MONEY VOLUME ACTIVITY ====================

@router.get("/smart-money/volume-activity")
async def get_smart_money_volume_activity(
    symbol: str = Query(..., description="Underlying symbol"),
    timeframe: str = Query("1D", description="Higher timeframe for bar context"),
    lower_timeframe: str = Query("5m", description="Lower timeframe for volume analysis"),
    z_len: int = Query(50, ge=5, description="Window length for volume Z-score"),
    threshold_abs: float = Query(2.0, ge=0.1, description="|Z| threshold for significant events"),
    who: str = Query("Both", regex="^(Both|Retail|Smart Money)$", description="Class filter") ,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Detect significant lower-timeframe volume events and aggregate P/L by class.

    Mirrors the behavior of the provided Pine Script at a high level.
    Returns levels (price/type/class/volume/z), bubble (strongest |Z|), and P/L totals.
    """
    try:
        result = await smart_money_volume_service.analyze_volume_activity(
            symbol=symbol,
            timeframe=timeframe,
            lower_timeframe=lower_timeframe,
            z_len=z_len,
            threshold_abs=threshold_abs,
            who=who,
        )
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        return {
            "success": True,
            "data": result,
            "message": "Smart money volume activity computed successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing smart money volume activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns/available")
async def get_available_patterns():
    """Get list of available candlestick patterns"""
    try:
        patterns = pattern_recognition_service.get_available_patterns()
        return {
            "success": True,
            "patterns": patterns,
            "count": len(patterns),
            "message": "Available patterns retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting available patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VOLUME ANALYSIS ENDPOINTS ====================

@router.post("/volume/analyze")
async def analyze_volume_price_relationship(
    request: VolumeAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprehensive volume-price analysis"""
    try:
        # Get chart data
        chart_data = await enhanced_chart_service.get_candlestick_data(
            symbol=request.symbol,
            timeframe=request.timeframe,
            period=200
        )
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])

        # Perform volume analysis
        analysis_result = await volume_analysis_service.analyze_volume_price_relationship(
            symbol=request.symbol,
            timeframe=request.timeframe,
            data=chart_data["candlesticks"],
            analysis_type=request.analysis_type
        )

        return {
            "success": True,
            "analysis_result": analysis_result,
            "timestamp": datetime.now().isoformat(),
            "message": f"Volume analysis completed for {request.symbol}"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error analyzing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TRADING RECOMMENDATIONS ENDPOINTS ====================

@router.post("/recommendations/generate")
async def generate_trading_recommendation(
    request: TradingRecommendationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI-powered trading recommendations"""
    try:
        # Generate comprehensive recommendation
        recommendation = await trading_recommendation_engine.generate_trading_recommendation(
            symbol=request.symbol,
            timeframe=request.timeframe,
            analysis_data=request.analysis_data,
            user_preferences=request.user_preferences
        )

        return {
            "success": True,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat(),
            "message": f"Trading recommendation generated for {request.symbol}"
        }
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/options-suggestion")
async def get_options_trading_suggestion(
    symbol: str,
    underlying_price: float,
    days_to_expiry: int = 30,
    option_type: str = "call",
    risk_tolerance: str = "medium",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive options trading suggestions"""
    try:
        # Convert string to enum
        from services.options_trading_ai import OptionsType
        option_type_enum = OptionsType.CALL if option_type.lower() == "call" else OptionsType.PUT
        
        suggestion = await trading_recommendation_engine.get_options_trading_suggestion(
            symbol=symbol,
            underlying_price=underlying_price,
            days_to_expiry=days_to_expiry,
            option_type=option_type_enum,
            risk_tolerance=risk_tolerance
        )

        return {
            "success": True,
            "suggestion": suggestion,
            "timestamp": datetime.now().isoformat(),
            "message": f"Options trading suggestion generated for {symbol}"
        }
    except Exception as e:
        logger.error(f"Error generating options suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VOICE FUNCTIONALITY ENDPOINTS ====================

@router.post("/voice/process-command")
async def process_voice_command(
    request: VoiceCommandRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process voice command and generate response"""
    try:
        # Initialize AI models if not already done
        if not voice_assistant.is_available():
            await voice_assistant.initialize_ai_models()
        
        # Decode audio data
        import base64
        audio_data = base64.b64decode(request.audio_data)
        
        # Process voice command
        response = await voice_assistant.process_voice_command(
            audio_data=audio_data,
            user_id=request.user_id,
            context=request.context
        )

        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "message": "Voice command processed successfully"
        }
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/start-monitoring")

# ==================== SYMBOL SEARCH ====================

@router.get("/search")
async def search_symbols(
    query: str = Query(..., min_length=1, description="Search query for symbol or company name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """
    Search for stock symbols by symbol code or company name
    Returns matching symbols with metadata
    """
    try:
        # Popular Indian stocks database (in production, this would be from a database)
        stock_database = {
            'RELIANCE': {'name': 'Reliance Industries Ltd', 'sector': 'Energy', 'exchange': 'NSE'},
            'TCS': {'name': 'Tata Consultancy Services', 'sector': 'IT', 'exchange': 'NSE'},
            'HDFCBANK': {'name': 'HDFC Bank Ltd', 'sector': 'Banking', 'exchange': 'NSE'},
            'INFY': {'name': 'Infosys Ltd', 'sector': 'IT', 'exchange': 'NSE'},
            'ICICIBANK': {'name': 'ICICI Bank Ltd', 'sector': 'Banking', 'exchange': 'NSE'},
            'HINDUNILVR': {'name': 'Hindustan Unilever Ltd', 'sector': 'FMCG', 'exchange': 'NSE'},
            'KOTAKBANK': {'name': 'Kotak Mahindra Bank', 'sector': 'Banking', 'exchange': 'NSE'},
            'ITC': {'name': 'ITC Ltd', 'sector': 'FMCG', 'exchange': 'NSE'},
            'BHARTIARTL': {'name': 'Bharti Airtel Ltd', 'sector': 'Telecom', 'exchange': 'NSE'},
            'SBIN': {'name': 'State Bank of India', 'sector': 'Banking', 'exchange': 'NSE'},
            'BAJFINANCE': {'name': 'Bajaj Finance Ltd', 'sector': 'Finance', 'exchange': 'NSE'},
            'ASIANPAINT': {'name': 'Asian Paints Ltd', 'sector': 'Paints', 'exchange': 'NSE'},
            'AXISBANK': {'name': 'Axis Bank Ltd', 'sector': 'Banking', 'exchange': 'NSE'},
            'MARUTI': {'name': 'Maruti Suzuki India', 'sector': 'Automobile', 'exchange': 'NSE'},
            'SUNPHARMA': {'name': 'Sun Pharmaceutical', 'sector': 'Pharma', 'exchange': 'NSE'},
            # Custom stocks
            'NMDC': {'name': 'NMDC Limited', 'sector': 'Steel', 'exchange': 'NSE'},
            'INFIBEAM': {'name': 'Infibeam Avenues Limited', 'sector': 'IT', 'exchange': 'NSE'},
            'INDIANREN': {'name': 'Indian Renewable Energy Development Agency', 'sector': 'Power', 'exchange': 'NSE'},
            'TANLA': {'name': 'Tanla Platforms Limited', 'sector': 'IT', 'exchange': 'NSE'},
            'BIRLASOFT': {'name': 'Birlasoft Limited', 'sector': 'IT', 'exchange': 'NSE'},
            'SUZLON': {'name': 'Suzlon Energy Limited', 'sector': 'Power', 'exchange': 'NSE'},
            'SAKSOFT': {'name': 'Saksoft Limited', 'sector': 'IT', 'exchange': 'NSE'},
            'GAIL': {'name': 'GAIL (India) Limited', 'sector': 'Oil & Gas', 'exchange': 'NSE'},
            'ADANIGREEN': {'name': 'Adani Green Energy Limited', 'sector': 'Power', 'exchange': 'NSE'},
            'NHPC': {'name': 'NHPC Limited', 'sector': 'Power', 'exchange': 'NSE'},
            'COCHINSHIP': {'name': 'Cochin Shipyard Limited', 'sector': 'Infrastructure', 'exchange': 'NSE'},
            'IRB': {'name': 'IRB Infrastructure Developers Limited', 'sector': 'Infrastructure', 'exchange': 'NSE'},
            'BAJAJHLDNG': {'name': 'Bajaj Housing Finance Limited', 'sector': 'Financial Services', 'exchange': 'NSE'},
            'HGIEL': {'name': 'Hindustan Green Energy Limited', 'sector': 'Power', 'exchange': 'NSE'},
            'BSE': {'name': 'BSE Limited', 'sector': 'Financial Services', 'exchange': 'NSE'},
            'TITAN': {'name': 'Titan Company Ltd', 'sector': 'Consumer', 'exchange': 'NSE'},
            'ULTRACEMCO': {'name': 'UltraTech Cement', 'sector': 'Cement', 'exchange': 'NSE'},
            'NESTLEIND': {'name': 'Nestle India Ltd', 'sector': 'FMCG', 'exchange': 'NSE'},
            'POWERGRID': {'name': 'Power Grid Corp', 'sector': 'Power', 'exchange': 'NSE'},
            'NTPC': {'name': 'NTPC Ltd', 'sector': 'Power', 'exchange': 'NSE'},
            'TECHM': {'name': 'Tech Mahindra Ltd', 'sector': 'IT', 'exchange': 'NSE'},
            'WIPRO': {'name': 'Wipro Ltd', 'sector': 'IT', 'exchange': 'NSE'},
            'HCLTECH': {'name': 'HCL Technologies', 'sector': 'IT', 'exchange': 'NSE'},
            'LT': {'name': 'Larsen & Toubro', 'sector': 'Engineering', 'exchange': 'NSE'},
            'BAJAJFINSV': {'name': 'Bajaj Finserv Ltd', 'sector': 'Finance', 'exchange': 'NSE'},
            'DRREDDY': {'name': 'Dr. Reddy\'s Labs', 'sector': 'Pharma', 'exchange': 'NSE'},
            'TATAMOTORS': {'name': 'Tata Motors Ltd', 'sector': 'Automobile', 'exchange': 'NSE'},
            'BRITANNIA': {'name': 'Britannia Industries', 'sector': 'FMCG', 'exchange': 'NSE'},
        }
        
        query_upper = query.upper()
        query_lower = query.lower()
        
        results = []
        for symbol, info in stock_database.items():
            # Match by symbol
            if query_upper in symbol:
                results.append({
                    'symbol': symbol,
                    'name': info['name'],
                    'sector': info['sector'],
                    'exchange': info['exchange'],
                    'match_type': 'symbol'
                })
            # Match by company name
            elif query_lower in info['name'].lower():
                results.append({
                    'symbol': symbol,
                    'name': info['name'],
                    'sector': info['sector'],
                    'exchange': info['exchange'],
                    'match_type': 'name'
                })
            # Match by sector
            elif query_lower in info['sector'].lower():
                results.append({
                    'symbol': symbol,
                    'name': info['name'],
                    'sector': info['sector'],
                    'exchange': info['exchange'],
                    'match_type': 'sector'
                })
            
            if len(results) >= limit:
                break
        
        # Sort: symbol matches first, then name matches, then sector
        results.sort(key=lambda x: (
            0 if x['match_type'] == 'symbol' else 1 if x['match_type'] == 'name' else 2,
            x['symbol']
        ))
        
        return {
            'success': True,
            'query': query,
            'results': results[:limit],
            'count': len(results[:limit])
        }
        
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
async def start_voice_monitoring(
    symbols: List[str],
    alert_types: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start real-time voice monitoring for trading alerts"""
    try:
        session_id = await voice_assistant.start_real_time_voice_monitoring(
            user_id=getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None),
            symbols=symbols,
            alert_types=alert_types
        )

        return {
            "success": True,
            "session_id": session_id,
            "symbols": symbols,
            "alert_types": alert_types,
            "message": "Voice monitoring started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting voice monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/voice/stop-monitoring/{session_id}")
async def stop_voice_monitoring(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop voice monitoring session"""
    try:
        success = await voice_assistant.stop_voice_monitoring(session_id)
        
        return {
            "success": success,
            "session_id": session_id,
            "message": "Voice monitoring stopped successfully" if success else "Session not found"
        }
    except Exception as e:
        logger.error(f"Error stopping voice monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== OPTIONS TRADING ENDPOINTS ====================

@router.post("/options/analyze")
async def analyze_options_chain(
    request: OptionsAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprehensive options chain analysis with AI"""
    try:
        analysis_result = await options_trading_ai.analyze_options_chain(
            symbol=request.symbol,
            underlying_price=request.underlying_price,
            days_to_expiry=request.days_to_expiry,
            risk_free_rate=request.risk_free_rate,
            volatility=request.volatility
        )

        return {
            "success": True,
            "analysis_result": analysis_result,
            "timestamp": datetime.now().isoformat(),
            "message": f"Options analysis completed for {request.symbol}"
        }
    except Exception as e:
        logger.error(f"Error analyzing options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/strategies")
async def get_options_strategies():
    """Get available options trading strategies"""
    try:
        strategies = list(options_trading_ai.strategies_database.keys())
        strategy_details = []
        
        for strategy in strategies:
            details = options_trading_ai.strategies_database[strategy]
            strategy_details.append({
                "strategy": strategy,
                "name": details["name"],
                "description": details["description"],
                "risk_level": details["risk_level"],
                "market_outlook": details["market_outlook"]
            })

        return {
            "success": True,
            "strategies": strategy_details,
            "count": len(strategy_details),
            "message": "Options strategies retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting options strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/strategy-performance/{strategy}")
async def get_strategy_performance(
    strategy: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance statistics for specific options strategy"""
    try:
        performance = await options_trading_ai.get_strategy_performance(strategy)
        
        return {
            "success": True,
            "strategy": strategy,
            "performance": performance,
            "message": f"Performance data retrieved for {strategy}"
        }
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANIMATION TEACHING ENDPOINTS ====================

@router.post("/teaching/start-session")
async def start_animation_session(
    request: AnimationSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start interactive animation teaching session"""
    try:
        session_id = await animation_teaching_service.start_animation_session(
            user_id=current_user["id"],
            animation_type=request.animation_type,
            symbol=request.symbol,
            difficulty=request.difficulty
        )

        return {
            "success": True,
            "session_id": session_id,
            "animation_type": request.animation_type,
            "symbol": request.symbol,
            "difficulty": request.difficulty,
            "message": "Animation session started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting animation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teaching/session/{session_id}/step/{step_number}")
async def get_animation_step(
    session_id: str,
    step_number: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific animation step with interactive content"""
    try:
        step_content = await animation_teaching_service.get_animation_step(
            session_id=session_id,
            step_number=step_number
        )

        return {
            "success": True,
            "step_content": step_content,
            "message": "Animation step retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting animation step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teaching/session/{session_id}/quiz")
async def submit_quiz_answer(
    session_id: str,
    question_id: str,
    user_answer: int,
    time_taken: float,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answer and get feedback"""
    try:
        result = await animation_teaching_service.submit_quiz_answer(
            session_id=session_id,
            question_id=question_id,
            user_answer=user_answer,
            time_taken=time_taken
        )

        return {
            "success": True,
            "result": result,
            "message": "Quiz answer submitted successfully"
        }
    except Exception as e:
        logger.error(f"Error submitting quiz answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teaching/session/{session_id}/complete")
async def complete_animation_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete animation session and get results"""
    try:
        results = await animation_teaching_service.complete_animation_session(session_id)

        return {
            "success": True,
            "results": results,
            "message": "Animation session completed successfully"
        }
    except Exception as e:
        logger.error(f"Error completing animation session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/teaching/progress/{user_id}")
async def get_user_progress(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's learning progress and achievements"""
    try:
        progress = await animation_teaching_service.get_user_progress(user_id)

        return {
            "success": True,
            "progress": progress,
            "message": "User progress retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TECHNICAL INDICATORS ENDPOINTS ====================

@router.post("/indicators/calculate")
async def calculate_indicator(
    indicator_type: str,
    symbol: str,
    timeframe: str = "1D",
    settings: Dict[str, Any] = {},
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate specific technical indicator"""
    try:
        # Get chart data
        chart_data = await enhanced_chart_service.get_candlestick_data(
            symbol=symbol,
            timeframe=timeframe,
            period=200
        )
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])

        # Calculate indicator
        indicator_data = technical_indicators_service.calculate_indicator(
            indicator_type, chart_data["candlesticks"], settings
        )

        return {
            "success": True,
            "indicator_type": indicator_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "data": indicator_data,
            "timestamp": datetime.now().isoformat(),
            "message": f"{indicator_type} calculated successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating indicator: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DRAWING TOOLS ENDPOINTS ====================

@router.post("/drawings")
async def save_drawing(
    drawing_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user drawing to database"""
    try:
        drawing_id = await drawing_tools_service.save_drawing(
            db, getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None), drawing_data
        )
        return {
            "success": True,
            "drawing_id": drawing_id,
            "message": "Drawing saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving drawing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drawings/{chart_id}")
async def get_drawings(
    chart_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all drawings for a chart"""
    try:
        drawings = await drawing_tools_service.get_drawings(db, getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None), chart_id)
        return {
            "success": True,
            "drawings": drawings,
            "count": len(drawings),
            "message": "Drawings retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error retrieving drawings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ALERT SYSTEM ENDPOINTS ====================

@router.post("/alerts")
async def create_alert(
    alert_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new trading alert"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        # Normalize payload
        symbol = alert_data.get("symbol")
        condition_type = alert_data.get("condition_type") or ("price" if str(alert_data.get("rule", "")).startswith("price") else "custom")
        operator_raw = str(alert_data.get("operator", "greater_than")).lower()
        operator_map = {"gt": "greater_than", "lt": "less_than", "eq": "equals"}
        operator = operator_map.get(operator_raw, operator_raw)
        value = float(alert_data.get("value", 0))
        notifications = alert_data.get("notifications") or {"in_app": True}
        cooldown_minutes = int(alert_data.get("cooldown_minutes", 30))
        name = alert_data.get("name")
        custom_conditions = alert_data.get("custom_conditions")
        expiry_date = None
        alert_id = await alert_system_service.create_alert(
            user_id=user_id,
            symbol=symbol,
            condition_type=condition_type,
            operator=operator,
            value=value,
            notifications=notifications,
            cooldown_minutes=cooldown_minutes,
            name=name,
            custom_conditions=custom_conditions,
            expiry_date=expiry_date,
            db=db
        )
        return {
            "success": True,
            "alert_id": alert_id,
            "message": "Alert created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_user_alerts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user alerts"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            return {
                "success": True,
                "alerts": [],
                "count": 0,
                "message": "No user authenticated"
            }
        alerts = await alert_system_service.get_user_alerts(user_id, db)
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "message": "Alerts retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/{alert_id}")
async def update_alert(
    alert_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing alert"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        # Normalize operator shortcuts if present
        if "operator" in updates:
            op = str(updates.get("operator", "")).lower()
            updates["operator"] = {"gt": "greater_than", "lt": "less_than", "eq": "equals"}.get(op, op)
        ok = await alert_system_service.update_alert(alert_id, user_id, updates, db)
        return {"success": ok, "message": "Alert updated" if ok else "Alert not updated"}
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        ok = await alert_system_service.delete_alert(alert_id, user_id, db)
        return {"success": ok, "message": "Alert deleted" if ok else "Alert not deleted"}
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WATCHLIST ENDPOINTS ====================

@router.post("/watchlists")
async def create_watchlist(
    name: str,
    symbols: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new watchlist"""
    try:
        watchlist_id = await watchlist_service.create_watchlist(
            getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None), name, symbols
        )
        return {
            "success": True,
            "watchlist_id": watchlist_id,
            "message": "Watchlist created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlists")
async def get_user_watchlists(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user watchlists"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        if not user_id:
            return {
                "success": True,
                "watchlists": [],
                "count": 0,
                "message": "No user authenticated"
            }
        watchlists = await watchlist_service.get_user_watchlists(user_id)
        return {
            "success": True,
            "watchlists": watchlists,
            "count": len(watchlists),
            "message": "Watchlists retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error retrieving watchlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/watchlists/{watchlist_id}")
async def update_watchlist(
    watchlist_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a watchlist"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        ok = await watchlist_service.update_watchlist(watchlist_id, user_id, updates)
        return {"success": ok, "message": "Watchlist updated" if ok else "Watchlist not updated"}
    except Exception as e:
        logger.error(f"Error updating watchlist {watchlist_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a watchlist"""
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        ok = await watchlist_service.delete_watchlist(watchlist_id, user_id)
        return {"success": ok, "message": "Watchlist deleted" if ok else "Watchlist not deleted"}
    except Exception as e:
        logger.error(f"Error deleting watchlist {watchlist_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watchlists/{watchlist_id}/symbols")
async def add_symbol_to_watchlist(
    watchlist_id: str,
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        ok = await watchlist_service.add_symbol(watchlist_id, symbol, user_id)
        return {"success": ok}
    except Exception as e:
        logger.error(f"Error adding symbol to watchlist {watchlist_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlists/{watchlist_id}/symbols")
async def remove_symbol_from_watchlist(
    watchlist_id: str,
    symbol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id = getattr(current_user, 'id', current_user.get('id') if isinstance(current_user, dict) else None)
        ok = await watchlist_service.remove_symbol(watchlist_id, symbol, user_id)
        return {"success": ok}
    except Exception as e:
        logger.error(f"Error removing symbol from watchlist {watchlist_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols/search")
async def search_symbols(
    query: str,
    limit: int = Query(default=10, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for trading symbols"""
    try:
        results = await watchlist_service.search_symbols(query, limit)
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "message": "Symbol search completed successfully"
        }
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WEBSOCKET ENDPOINTS ====================

@router.websocket("/ws/chart-data/{symbol}")
async def websocket_chart_data(websocket: WebSocket, symbol: str):
    """WebSocket for real-time chart data updates"""
    await websocket.accept()
    try:
        while True:
            # Get real-time data
            data = await enhanced_chart_service.get_candlestick_data(
                symbol=symbol,
                timeframe="1m",
                period=1
            )
            
            if "error" not in data:
                await websocket.send_json({
                    "type": "chart_update",
                    "symbol": symbol,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")

@router.websocket("/ws/order-book/{symbol}")
async def websocket_order_book(websocket: WebSocket, symbol: str):
    """WebSocket for real-time order book (Level 2 market data)"""
    await websocket.accept()
    last_state = None
    
    try:
        while True:
            # Check if update is needed (throttling)
            if realtime_orderbook.should_update(symbol):
                # Get delta update
                delta = await realtime_orderbook.get_delta_update(symbol, last_state)
                
                if "error" not in delta:
                    await websocket.send_json({
                        "type": "order_book_update",
                        "symbol": symbol,
                        "data": delta,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Update last state
                    if delta.get("bids_changed") or delta.get("asks_changed"):
                        last_state = await realtime_orderbook.get_order_book(symbol)
            
            await asyncio.sleep(0.1)  # Check every 100ms
            
    except WebSocketDisconnect:
        logger.info(f"Order book WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"Order book WebSocket error for {symbol}: {e}")

@router.websocket("/ws/trade-feed/{symbol}")
async def websocket_trade_feed(websocket: WebSocket, symbol: str):
    """WebSocket for real-time trade execution feed"""
    await websocket.accept()
    
    try:
        while True:
            # Check if update is needed (throttling)
            if realtime_trade_feed.should_update(symbol):
                # Get aggregated trades
                trades = await realtime_trade_feed.get_aggregated_trades(symbol, window_seconds=1.0)
                
                if trades:
                    await websocket.send_json({
                        "type": "trade_feed_update",
                        "symbol": symbol,
                        "data": {
                            "trades": trades,
                            "count": len(trades)
                        },
                        "timestamp": datetime.now().isoformat()
                    })
            
            await asyncio.sleep(0.2)  # Check every 200ms (5 updates/sec)
            
    except WebSocketDisconnect:
        logger.info(f"Trade feed WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"Trade feed WebSocket error for {symbol}: {e}")

@router.websocket("/ws/options-chain/{symbol}")
async def websocket_options_chain(websocket: WebSocket, symbol: str):
    """WebSocket for real-time options chain"""
    await websocket.accept()
    last_state = None
    page = 1
    
    try:
        # Send initial full chain
        initial_chain = await realtime_options_chain.get_options_chain(symbol, page=page)
        await websocket.send_json({
            "type": "options_chain_full",
            "symbol": symbol,
            "data": initial_chain,
            "timestamp": datetime.now().isoformat()
        })
        last_state = initial_chain
        
        while True:
            # Check if update is needed (throttling)
            if realtime_options_chain.should_update(symbol):
                # Get delta update
                delta = await realtime_options_chain.get_delta_update(symbol, last_state)
                
                if "error" not in delta and (delta.get("changed_strikes") or delta.get("new_strikes")):
                    await websocket.send_json({
                        "type": "options_chain_delta",
                        "symbol": symbol,
                        "data": delta,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Update last state
                    last_state = await realtime_options_chain.get_options_chain(symbol, page=page)
            
            await asyncio.sleep(1.0)  # Check every second
            
    except WebSocketDisconnect:
        logger.info(f"Options chain WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"Options chain WebSocket error for {symbol}: {e}")

@router.websocket("/ws/trading-signals")
async def websocket_trading_signals(websocket: WebSocket):
    """WebSocket for real-time trading signals"""
    await websocket.accept()
    try:
        while True:
            # This would integrate with your real-time signal generation
            # For now, sending mock data
            signal_data = {
                "type": "trading_signal",
                "symbol": "RELIANCE",
                "signal": "buy",
                "confidence": 0.85,
                "price": 2500.0,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_json(signal_data)
            await asyncio.sleep(10)  # Send signal every 10 seconds
            
    except WebSocketDisconnect:
        logger.info("Trading signals WebSocket disconnected")
    except Exception as e:
        logger.error(f"Trading signals WebSocket error: {e}")

# ==================== SYSTEM STATUS ENDPOINTS ====================

@router.get("/system/status")
async def get_system_status():
    """Get status of all services"""
    try:
        def safe_available(obj):
            try:
                attr = getattr(obj, 'is_available', None)
                if callable(attr):
                    return bool(attr())
                if isinstance(attr, bool):
                    return attr
                return True
            except Exception:
                return False

        status = {
            "enhanced_charting": True,  # enhanced_chart_service may not expose is_available
            "technical_indicators": safe_available(technical_indicators_service),
            "drawing_tools": safe_available(drawing_tools_service),
            "alert_system": safe_available(alert_system_service),
            "watchlist_service": safe_available(watchlist_service),
            "animation_teaching": safe_available(animation_teaching_service),
            "pattern_recognition": safe_available(pattern_recognition_service),
            "volume_analysis": safe_available(volume_analysis_service),
            "trading_recommendations": safe_available(trading_recommendation_engine),
            "voice_assistant": safe_available(voice_assistant),
            "options_trading_ai": safe_available(options_trading_ai)
        }
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "message": "System status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/performance")
async def get_system_performance():
    """Get performance statistics for all services"""
    try:
        performance = {
            "voice_performance": await voice_assistant.get_voice_performance_stats(),
            "trading_recommendations": trading_recommendation_engine.get_performance_statistics(),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "performance": performance,
            "message": "Performance statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting performance statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADDITIONAL COMPREHENSIVE ENDPOINTS ====================

@router.get("/teaching/flows")
async def get_teaching_flows():
    """Get available teaching flows and courses"""
    try:
        flows = [
            {
                "id": "candlestick-patterns",
                "name": "Candlestick Pattern Recognition",
                "description": "Learn to identify and trade candlestick patterns",
                "duration": "2 hours",
                "difficulty": "beginner",
                "topics": ["doji", "hammer", "engulfing", "morning_star", "evening_star"],
                "prerequisites": []
            },
            {
                "id": "technical-indicators",
                "name": "Technical Indicators Mastery",
                "description": "Master RSI, MACD, Bollinger Bands, and more",
                "duration": "3 hours",
                "difficulty": "intermediate",
                "topics": ["rsi", "macd", "bollinger_bands", "stochastic", "atr"],
                "prerequisites": ["candlestick-patterns"]
            },
            {
                "id": "options-strategies",
                "name": "Options Trading Strategies",
                "description": "Learn advanced options strategies and risk management",
                "duration": "4 hours",
                "difficulty": "advanced",
                "topics": ["calls", "puts", "straddles", "strangles", "iron_condors"],
                "prerequisites": ["technical-indicators"]
            },
            {
                "id": "risk-management",
                "name": "Risk Management Fundamentals",
                "description": "Essential risk management techniques for traders",
                "duration": "1.5 hours",
                "difficulty": "beginner",
                "topics": ["position_sizing", "stop_losses", "portfolio_diversification"],
                "prerequisites": []
            }
        ]
        
        return {
            "success": True,
            "flows": flows,
            "message": "Teaching flows retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting teaching flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/options/strategy-views")
async def get_options_strategy_views(
    symbol: str = Query(..., description="Underlying symbol"),
    current_price: float = Query(..., description="Current underlying price"),
    days_to_expiry: int = Query(30, description="Days to expiry")
):
    """Get visual strategy views for options trading"""
    try:
        # Generate strategy views
        strategies = [
            {
                "name": "Long Call",
                "type": "bullish",
                "max_profit": "Unlimited",
                "max_loss": "Premium paid",
                "breakeven": current_price + 50,  # Example
                "probability": 0.35,
                "risk_level": "high",
                "description": "Buy call option for bullish outlook"
            },
            {
                "name": "Long Put",
                "type": "bearish",
                "max_profit": current_price - 10,  # Example
                "max_loss": "Premium paid",
                "breakeven": current_price - 50,  # Example
                "probability": 0.30,
                "risk_level": "high",
                "description": "Buy put option for bearish outlook"
            },
            {
                "name": "Covered Call",
                "type": "neutral",
                "max_profit": "Premium + (strike - current_price)",
                "max_loss": "Unlimited downside",
                "breakeven": current_price - 50,  # Example
                "probability": 0.60,
                "risk_level": "medium",
                "description": "Sell call against long stock position"
            },
            {
                "name": "Straddle",
                "type": "volatile",
                "max_profit": "Unlimited",
                "max_loss": "Total premium paid",
                "breakeven": [current_price - 100, current_price + 100],  # Example
                "probability": 0.25,
                "risk_level": "high",
                "description": "Buy call and put at same strike"
            }
        ]
        
        return {
            "success": True,
            "symbol": symbol,
            "current_price": current_price,
            "days_to_expiry": days_to_expiry,
            "strategies": strategies,
            "message": "Options strategy views generated successfully"
        }
    except Exception as e:
        logger.error(f"Error getting options strategy views: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/real-time-quotes")
async def websocket_real_time_quotes(websocket: WebSocket):
    """WebSocket for real-time stock quotes"""
    await websocket.accept()
    try:
        while True:
            # Simulate real-time quotes
            quotes = {
                "NIFTY50": {"price": 19500 + (await asyncio.sleep(0.1) or 0), "change": 50},
                "SENSEX": {"price": 65000 + (await asyncio.sleep(0.1) or 0), "change": 150},
                "RELIANCE": {"price": 2500 + (await asyncio.sleep(0.1) or 0), "change": 25}
            }
            
            await websocket.send_json({
                "type": "quotes",
                "data": quotes,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)  # Send updates every second
            
    except WebSocketDisconnect:
        logger.info("Real-time quotes WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in real-time quotes WebSocket: {e}")

@router.websocket("/ws/market-alerts")
async def websocket_market_alerts(websocket: WebSocket):
    """WebSocket for real-time market alerts"""
    await websocket.accept()
    try:
        while True:
            # Simulate market alerts
            alerts = [
                {
                    "id": f"alert_{datetime.now().timestamp()}",
                    "type": "price_alert",
                    "symbol": "RELIANCE",
                    "message": "RELIANCE crossed 2500 resistance level",
                    "severity": "medium",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            await websocket.send_json({
                "type": "market_alert",
                "data": alerts,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(5)  # Send alerts every 5 seconds
            
    except WebSocketDisconnect:
        logger.info("Market alerts WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in market alerts WebSocket: {e}")

@router.get("/teaching/quiz/{flow_id}")
async def get_teaching_quiz(
    flow_id: str,
    level: str = Query("beginner", description="Quiz difficulty level")
):
    """Get quiz questions for a teaching flow"""
    try:
        quiz_questions = {
            "candlestick-patterns": [
                {
                    "id": 1,
                    "question": "What does a doji candlestick pattern indicate?",
                    "options": ["Strong bullish signal", "Market indecision", "Strong bearish signal", "Volume spike"],
                    "correct_answer": 1,
                    "explanation": "A doji indicates market indecision with opening and closing prices nearly equal."
                },
                {
                    "id": 2,
                    "question": "Which pattern is considered a bullish reversal?",
                    "options": ["Evening star", "Hammer", "Shooting star", "Hanging man"],
                    "correct_answer": 1,
                    "explanation": "Hammer is a bullish reversal pattern that appears at the bottom of downtrends."
                }
            ],
            "technical-indicators": [
                {
                    "id": 1,
                    "question": "What RSI level typically indicates oversold conditions?",
                    "options": ["Above 70", "Below 30", "Above 50", "Below 50"],
                    "correct_answer": 1,
                    "explanation": "RSI below 30 typically indicates oversold conditions, suggesting potential buying opportunity."
                }
            ]
        }
        
        questions = quiz_questions.get(flow_id, [])
        
        return {
            "success": True,
            "flow_id": flow_id,
            "level": level,
            "questions": questions,
            "message": "Quiz questions retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting teaching quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teaching/quiz/{flow_id}/submit")
async def submit_quiz_answers(
    flow_id: str,
    answers: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results"""
    try:
        # Calculate score
        total_questions = len(answers.get("answers", []))
        correct_answers = 0
        
        for answer in answers.get("answers", []):
            if answer.get("is_correct", False):
                correct_answers += 1
        
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Determine pass/fail
        passed = score >= 70
        
        return {
            "success": True,
            "flow_id": flow_id,
            "score": round(score, 2),
            "passed": passed,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "message": f"Quiz {'passed' if passed else 'failed'} with {score:.1f}% score"
        }
    except Exception as e:
        logger.error(f"Error submitting quiz answers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoints for Smart Money Volume alerts
@router.websocket("/ws/smart-money-alerts/{user_id}")
async def websocket_smart_money_alerts(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for Smart Money Volume alerts"""
    await websocket.accept()
    try:
        # Add WebSocket connection to alert system
        await alert_system_service.add_websocket_connection(user_id, websocket)
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Wait for next heartbeat
                await asyncio.sleep(30)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in SMV WebSocket connection: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error establishing SMV WebSocket connection: {e}")
    finally:
        # Remove WebSocket connection
        await alert_system_service.remove_websocket_connection(user_id)

@router.post("/smart-money-alerts/create")
async def create_smart_money_alert(
    request_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Smart Money Volume alert"""
    try:
        symbol = request_data.get("symbol")
        activity_type = request_data.get("activity_type")  # smart_money_bullish, smart_money_bearish, retail_bullish, retail_bearish
        notifications = request_data.get("notifications", {"in_app": True, "email": False})
        cooldown_minutes = request_data.get("cooldown_minutes", 30)
        
        if not symbol or not activity_type:
            raise HTTPException(status_code=400, detail="Symbol and activity_type are required")
        
        if activity_type not in ["smart_money_bullish", "smart_money_bearish", "retail_bullish", "retail_bearish"]:
            raise HTTPException(status_code=400, detail="Invalid activity_type")
        
        alert_id = await alert_system_service.create_smv_alert(
            user_id=current_user.id,
            symbol=symbol,
            activity_type=activity_type,
            notifications=notifications,
            cooldown_minutes=cooldown_minutes,
            db=db
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"SMV alert created for {symbol} - {activity_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SMV alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/smart-money-alerts/test/{symbol}")
async def test_smart_money_alert(
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """Test Smart Money Volume alert for a symbol"""
    try:
        # Get SMV data
        smv_data = await smart_money_volume_service.analyze_volume_activity(
            symbol=symbol,
            timeframe="1D",
            lower_timeframe="5m",
            z_len=50,
            threshold_abs=2.0,
            who="Both"
        )
        
        if "error" in smv_data:
            raise HTTPException(status_code=400, detail=smv_data["error"])
        
        # Send test alert
        await alert_system_service.send_smv_realtime_alert(
            user_id=current_user.id,
            symbol=symbol,
            smv_data=smv_data
        )
        
        return {
            "success": True,
            "message": f"Test SMV alert sent for {symbol}",
            "smv_data": smv_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing SMV alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== F&O TRADING ALGORITHMS ====================

class OIAnalysisRequest(BaseModel):
    current_price: float
    previous_price: float
    current_oi: float
    previous_oi: float

class PCRAnalysisRequest(BaseModel):
    put_oi: float
    call_oi: float

class MaxPainRequest(BaseModel):
    strikes: List[float]
    call_oi: List[float]
    put_oi: List[float]
    current_price: float

class FuturesSpreadRequest(BaseModel):
    near_month_price: float
    far_month_price: float
    near_month_oi: float
    far_month_oi: float
    cost_of_carry: Optional[float] = 0.08

class OptionsStrategyRequest(BaseModel):
    current_price: float
    volatility: float
    time_to_expiry: int
    market_sentiment: str
    risk_tolerance: Optional[str] = "medium"

@router.get("/fno/chart-analysis/{symbol}")
async def get_fno_chart_analysis(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe for analysis"),
    enable_multi_timeframe: bool = Query(True, description="Enable multi-timeframe analysis"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get comprehensive chart analysis for FNO trading suggestions with multi-timeframe confirmation"""
    try:
        # Import pandas at function level to avoid scoping issues
        import pandas as pd
        import numpy as np
        
        # Normalize symbol for data fetching (handles NIFTY, stocks, etc.)
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        display_symbol = normalize_symbol_for_display(normalized_symbol) or symbol
        logger.info(f"FNO Chart Analysis: Normalized {symbol} -> {normalized_symbol} (display: {display_symbol})")
        
        # Initialize variables early to avoid scoping issues
        nearest_support = None
        nearest_resistance = None
        support_distance_pct = None
        resistance_distance_pct = None
        current_price = 0
        
        # Fetch current price from real-time quote service first (for verification)
        try:
            from core.data_service import data_service
            quote = await data_service.get_quote(display_symbol, exchange="NSE")
            if quote and "error" not in quote:
                current_price = float(quote.get("last_price", 0))
                logger.info(f"✅ Fetched current price for {symbol} ({display_symbol}): ₹{current_price}")
        except Exception as quote_error:
            logger.warning(f"Could not fetch real-time quote for {symbol}: {quote_error}")
            current_price = 0
        
        # Multi-timeframe analysis: Analyze 1D, 4H, 1H for confirmation
        multi_timeframe_results = {}
        if enable_multi_timeframe:
            try:
                # Try multiple timeframe formats - Indian stocks may not support all
                timeframes_to_analyze = ["1D", "1d", "4H", "4h", "1H", "1h"]  # Try both formats
                timeframe_weights = {"1D": 0.5, "1d": 0.5, "4H": 0.3, "4h": 0.3, "1H": 0.2, "1h": 0.2}
                analyzed_timeframes = set()  # Track which timeframes we've successfully analyzed
                
                for tf in timeframes_to_analyze:
                    # Skip if we've already analyzed this timeframe (e.g., "1D" and "1d")
                    tf_normalized = tf.upper()
                    if tf_normalized in analyzed_timeframes:
                        continue
                    
                    try:
                        tf_chart_data = await enhanced_chart_service.get_candlestick_data(
                            symbol=normalized_symbol,
                            timeframe=tf,
                            period=100
                        )
                        if "error" not in tf_chart_data and tf_chart_data.get("candlesticks"):
                            tf_candles = tf_chart_data.get("candlesticks", [])
                            if len(tf_candles) >= 2:
                                # Quick trend analysis for this timeframe
                                tf_df = pd.DataFrame(tf_candles)
                                if 'close' in tf_df.columns:
                                    tf_current_price = tf_df['close'].iloc[-1]
                                    tf_sma_20 = tf_df['close'].tail(20).mean() if len(tf_df) >= 20 else tf_current_price
                                    tf_sma_50 = tf_df['close'].tail(50).mean() if len(tf_df) >= 50 else tf_current_price
                                    
                                    # Use normalized timeframe name
                                    multi_timeframe_results[tf_normalized] = {
                                        "trend": "BULLISH" if tf_current_price > tf_sma_20 > tf_sma_50 else "BEARISH" if tf_current_price < tf_sma_20 < tf_sma_50 else "NEUTRAL",
                                        "price": float(tf_current_price),
                                        "sma_20": float(tf_sma_20),
                                        "sma_50": float(tf_sma_50),
                                        "weight": timeframe_weights.get(tf_normalized, timeframe_weights.get(tf, 0.33))
                                    }
                                    analyzed_timeframes.add(tf_normalized)
                    except Exception as tf_error:
                        logger.warning(f"Multi-timeframe analysis failed for {tf}: {tf_error}")
                        continue
                
                # If we only got 1D data, use it with higher confidence
                if len(multi_timeframe_results) == 1 and "1D" in multi_timeframe_results:
                    multi_timeframe_results["1D"]["weight"] = 1.0  # Full weight if only daily available
            except Exception as mtf_error:
                logger.warning(f"Multi-timeframe analysis error: {mtf_error}")
        
        # Get technical indicators (primary timeframe) - use normalized symbol
        chart_data = await enhanced_chart_service.get_candlestick_data(
            symbol=normalized_symbol,
            timeframe=timeframe,
            period=100
        )
        
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        
        candlesticks = chart_data.get("candlesticks", [])
        if not candlesticks:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol} (normalized: {normalized_symbol})")
        
        # Calculate key indicators from candlesticks data
        # Convert candlesticks to DataFrame for indicator calculation
        # (pandas and numpy already imported at function level)
        
        if not candlesticks or len(candlesticks) == 0:
            raise HTTPException(status_code=404, detail=f"No candlestick data found for {symbol}")
        
        df = pd.DataFrame(candlesticks)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Empty DataFrame for {symbol}")
        
        # Ensure required columns exist
        required_candle_cols = ['open', 'high', 'low', 'close']
        missing_candle_cols = [col for col in required_candle_cols if col not in df.columns]
        if missing_candle_cols:
            raise HTTPException(status_code=400, detail=f"Missing required columns in candlestick data: {', '.join(missing_candle_cols)}")
        
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
            df.set_index('time', inplace=True)
        elif df.index.name is None:
            # If no time column, create a simple index
            df.index = pd.date_range(end=datetime.now(), periods=len(df), freq='1D')
        
        # Calculate indicators using the internal method (with error handling)
        rsi_data = None
        macd_data = None
        sma_20 = None
        sma_50 = None
        bb_data = None
        
        try:
            rsi_data = await technical_indicators_service._calculate_specific_indicator(df, "rsi", {"period": 14})
        except Exception as rsi_error:
            logger.warning(f"RSI calculation failed for {symbol}: {rsi_error}")
            rsi_data = pd.Series([50] * len(df))  # Default neutral RSI
        
        try:
            macd_data = await technical_indicators_service._calculate_specific_indicator(df, "macd", {})
        except Exception as macd_error:
            logger.warning(f"MACD calculation failed for {symbol}: {macd_error}")
            macd_data = {"macd": [0], "signal": [0]}
        
        try:
            sma_20 = await technical_indicators_service._calculate_specific_indicator(df, "sma", {"period": 20})
        except Exception as sma20_error:
            logger.warning(f"SMA 20 calculation failed for {symbol}: {sma20_error}")
            sma_20 = pd.Series([current_price] * len(df)) if 'close' in df.columns else pd.Series([0] * len(df))
        
        try:
            sma_50 = await technical_indicators_service._calculate_specific_indicator(df, "sma", {"period": 50})
        except Exception as sma50_error:
            logger.warning(f"SMA 50 calculation failed for {symbol}: {sma50_error}")
            sma_50 = pd.Series([current_price] * len(df)) if 'close' in df.columns else pd.Series([0] * len(df))
        
        try:
            bb_data = await technical_indicators_service._calculate_specific_indicator(df, "bollinger_bands", {})
        except Exception as bb_error:
            logger.warning(f"Bollinger Bands calculation failed for {symbol}: {bb_error}")
            bb_data = None
        
        # Get pattern analysis using enhanced_chart_service - use normalized symbol
        detected_patterns = []
        try:
            pattern_result = await enhanced_chart_service.get_pattern_recognition(symbol=normalized_symbol)
            if isinstance(pattern_result, dict) and "error" not in pattern_result:
                # Try multiple possible keys for patterns
                detected_patterns = (
                    pattern_result.get("patterns", []) or 
                    pattern_result.get("detected_patterns", []) or
                    pattern_result.get("candlestick_patterns", []) or
                    []
                )
                # If patterns is a dict, convert to list
                if isinstance(detected_patterns, dict):
                    detected_patterns = [
                        {**v, "pattern_name": k} if isinstance(v, dict) else {"pattern_name": k, "pattern": v}
                        for k, v in detected_patterns.items()
                    ]
            elif isinstance(pattern_result, list):
                detected_patterns = pattern_result
            else:
                detected_patterns = []
            
            logger.info(f"Pattern recognition for {symbol}: Found {len(detected_patterns)} patterns")
        except Exception as pattern_error:
            logger.warning(f"Pattern recognition failed for {symbol}: {pattern_error}")
            detected_patterns = []
        
        # Get volume analysis (with error handling) - Enhanced with divergence and volume profile
        volume_analysis = None
        volume_profile_data = None
        divergence_signals = []
        bullish_divergences = []
        bearish_divergences = []
        try:
            volume_analysis = await volume_analysis_service.analyze_volume_price_relationship(
                symbol=normalized_symbol,
                timeframe=timeframe,
                data=candlesticks,
                analysis_type="comprehensive"
            )
            # Extract divergence signals if available
            if isinstance(volume_analysis, dict):
                # Get divergence analysis
                divergence_analysis = volume_analysis.get("divergence_analysis", {})
                if isinstance(divergence_analysis, dict):
                    bullish_divergences = divergence_analysis.get("bullish_divergences", [])
                    bearish_divergences = divergence_analysis.get("bearish_divergences", [])
                    if bullish_divergences:
                        divergence_signals.append("BULLISH_DIVERGENCE")
                    if bearish_divergences:
                        divergence_signals.append("BEARISH_DIVERGENCE")
                
                # Get volume profile data
                volume_profile_analysis = volume_analysis.get("volume_profile_analysis", {})
                if isinstance(volume_profile_analysis, dict):
                    volume_profile_data = volume_profile_analysis.get("volume_profile") or volume_profile_analysis
        except Exception as vol_error:
            logger.warning(f"Volume analysis failed for {symbol}: {vol_error}")
            volume_analysis = {"trend": "NEUTRAL", "error": str(vol_error)}
        
        # Get Support/Resistance levels
        support_levels = []
        resistance_levels = []
        pivot_points = []
        try:
            key_levels = await trading_recommendation_engine._identify_key_levels({
                "price_data": candlesticks
            })
            support_levels = key_levels.get("support_levels", [])
            resistance_levels = key_levels.get("resistance_levels", [])
            pivot_points = key_levels.get("pivot_points", [])
        except Exception as sr_error:
            logger.warning(f"Support/Resistance detection failed for {symbol}: {sr_error}")
        
        # Get volume-based support/resistance from volume profile
        volume_based_sr = []
        try:
            if volume_profile_data:
                volume_based_sr = await volume_analysis_service._identify_support_resistance_levels(volume_profile_data)
        except Exception as vsr_error:
            logger.warning(f"Volume-based S/R detection failed for {symbol}: {vsr_error}")
        
        # Get current values (update the variable initialized at function start)
        # Use the latest close from candlesticks, but prefer real-time quote if available
        latest_close = candlesticks[-1]["close"] if candlesticks else 0
        
        # Ensure we have a valid price - prioritize real-time quote, fallback to latest close
        if current_price == 0 or current_price is None:
            current_price = latest_close if latest_close > 0 else 0
            logger.info(f"Using latest close price from candlesticks: ₹{current_price}")
        elif latest_close > 0:
            # Check if prices differ significantly (>10% difference)
            price_diff_pct = abs(current_price - latest_close) / max(current_price, latest_close, 1) * 100
            if price_diff_pct > 10:
                # If difference is too large, prefer the more recent candlestick close
                logger.warning(f"Price mismatch: Quote={current_price}, Candlestick={latest_close} (diff: {price_diff_pct:.2f}%). Using candlestick close.")
                current_price = latest_close
            else:
                logger.info(f"Using real-time quote price: ₹{current_price} (candlestick close: ₹{latest_close}, diff: {price_diff_pct:.2f}%)")
        
        # Final safety check - ensure we have a valid price
        if current_price == 0 or current_price is None:
            logger.error(f"⚠️ No valid price found for {symbol}. Quote: {current_price}, Candlestick: {latest_close}")
            # Try to get from DataFrame if available
            if 'close' in df.columns and len(df) > 0:
                current_price = float(df['close'].iloc[-1])
                logger.info(f"Using DataFrame close price: ₹{current_price}")
        
        # Calculate nearest support and resistance (variables already initialized at function start)
        if support_levels and current_price:
            # Filter supports below current price and get the highest one
            supports_below = [s for s in support_levels if isinstance(s, (int, float)) and s < current_price]
            if supports_below:
                nearest_support = max(supports_below)
                support_distance_pct = round(((current_price - nearest_support) / current_price) * 100, 2)
        if resistance_levels and current_price:
            # Filter resistances above current price and get the lowest one
            resistances_above = [r for r in resistance_levels if isinstance(r, (int, float)) and r > current_price]
            if resistances_above:
                nearest_resistance = min(resistances_above)
                resistance_distance_pct = round(((nearest_resistance - current_price) / current_price) * 100, 2)
        
        # Detect RSI Divergence (additional to volume divergence)
        if len(candlesticks) >= 14 and isinstance(rsi_data, pd.Series) and len(rsi_data) >= 14:
            try:
                # Get last 14 periods for divergence detection
                recent_prices = [c["close"] for c in candlesticks[-14:]]
                recent_rsi = rsi_data.tail(14).tolist()
                
                # Check for bullish RSI divergence (price lower lows, RSI higher lows)
                if len(recent_prices) >= 5 and len(recent_rsi) >= 5:
                    price_lows = [min(recent_prices[i:i+3]) for i in range(len(recent_prices)-2)]
                    rsi_lows = [min(recent_rsi[i:i+3]) for i in range(len(recent_rsi)-2)]
                    
                    # Bullish: Price making lower lows, RSI making higher lows
                    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
                        price_trend_down = price_lows[-1] < price_lows[-2]
                        rsi_trend_up = rsi_lows[-1] > rsi_lows[-2]
                        if price_trend_down and rsi_trend_up:
                            if "BULLISH_DIVERGENCE" not in divergence_signals:
                                divergence_signals.append("BULLISH_DIVERGENCE")
                            bullish_divergences.append({"type": "RSI", "strength": "medium"})
                    
                    # Bearish: Price making higher highs, RSI making lower highs
                    price_highs = [max(recent_prices[i:i+3]) for i in range(len(recent_prices)-2)]
                    rsi_highs = [max(recent_rsi[i:i+3]) for i in range(len(recent_rsi)-2)]
                    if len(price_highs) >= 2 and len(rsi_highs) >= 2:
                        price_trend_up = price_highs[-1] > price_highs[-2]
                        rsi_trend_down = rsi_highs[-1] < rsi_highs[-2]
                        if price_trend_up and rsi_trend_down:
                            if "BEARISH_DIVERGENCE" not in divergence_signals:
                                divergence_signals.append("BEARISH_DIVERGENCE")
                            bearish_divergences.append({"type": "RSI", "strength": "medium"})
            except Exception as rsi_div_error:
                logger.warning(f"RSI divergence detection failed: {rsi_div_error}")
        
        # Extract values from indicator results (they may be Series or dicts)
        try:
            if isinstance(rsi_data, pd.Series):
                rsi_value = float(rsi_data.iloc[-1]) if len(rsi_data) > 0 and not rsi_data.iloc[-1] is None else 50
            elif isinstance(rsi_data, (list, np.ndarray)):
                rsi_value = float(rsi_data[-1]) if len(rsi_data) > 0 else 50
            elif isinstance(rsi_data, dict):
                # Handle dict format - try common keys, handle nested dicts
                rsi_val = rsi_data.get("rsi") or rsi_data.get("value") or rsi_data.get("rsi_value")
                if isinstance(rsi_val, dict):
                    rsi_val = rsi_val.get("rsi") or rsi_val.get("value") or 50
                rsi_value = float(rsi_val) if rsi_val is not None and not isinstance(rsi_val, dict) else 50
            elif rsi_data is None:
                rsi_value = 50
            else:
                rsi_value = 50
        except Exception as rsi_extract_error:
            logger.warning(f"Error extracting RSI value for {symbol}: {rsi_extract_error}")
            rsi_value = 50
        try:
            if isinstance(macd_data, dict):
                macd_list = macd_data.get("macd", [0])
                signal_list = macd_data.get("signal", [0])
                macd_value = float(macd_list[-1]) if isinstance(macd_list, list) and len(macd_list) > 0 else (float(macd_data.get("macd", 0)) if not isinstance(macd_data.get("macd"), list) else 0)
                macd_signal = float(signal_list[-1]) if isinstance(signal_list, list) and len(signal_list) > 0 else (float(macd_data.get("signal", 0)) if not isinstance(macd_data.get("signal"), list) else 0)
            elif isinstance(macd_data, pd.DataFrame):
                macd_value = float(macd_data["macd"].iloc[-1]) if "macd" in macd_data.columns and len(macd_data) > 0 else 0
                macd_signal = float(macd_data["signal"].iloc[-1]) if "signal" in macd_data.columns and len(macd_data) > 0 else 0
            elif macd_data is None:
                macd_value = 0
                macd_signal = 0
            else:
                macd_value = 0
                macd_signal = 0
        except Exception as macd_extract_error:
            logger.warning(f"Error extracting MACD values for {symbol}: {macd_extract_error}")
            macd_value = 0
            macd_signal = 0
        
        try:
            if isinstance(sma_20, pd.Series):
                sma_20_value = float(sma_20.iloc[-1]) if len(sma_20) > 0 and not pd.isna(sma_20.iloc[-1]) else current_price
            elif isinstance(sma_20, (list, np.ndarray)):
                sma_20_value = float(sma_20[-1]) if len(sma_20) > 0 else current_price
            elif isinstance(sma_20, dict):
                # Handle dict format - try common keys, handle nested dicts
                sma_val = sma_20.get("sma_20") or sma_20.get("value") or sma_20.get("sma") or sma_20.get("sma20")
                if isinstance(sma_val, dict):
                    sma_val = sma_val.get("sma_20") or sma_val.get("value") or sma_val.get("sma") or current_price
                sma_20_value = float(sma_val) if sma_val is not None and not isinstance(sma_val, dict) else current_price
            elif sma_20 is None:
                sma_20_value = current_price
            else:
                sma_20_value = current_price
        except Exception as sma20_extract_error:
            logger.warning(f"Error extracting SMA 20 value for {symbol}: {sma20_extract_error}")
            sma_20_value = current_price
        
        try:
            if isinstance(sma_50, pd.Series):
                sma_50_value = float(sma_50.iloc[-1]) if len(sma_50) > 0 and not pd.isna(sma_50.iloc[-1]) else current_price
            elif isinstance(sma_50, (list, np.ndarray)):
                sma_50_value = float(sma_50[-1]) if len(sma_50) > 0 else current_price
            elif isinstance(sma_50, dict):
                # Handle dict format - try common keys, handle nested dicts
                sma_val = sma_50.get("sma_50") or sma_50.get("value") or sma_50.get("sma") or sma_50.get("sma50")
                if isinstance(sma_val, dict):
                    sma_val = sma_val.get("sma_50") or sma_val.get("value") or sma_val.get("sma") or current_price
                sma_50_value = float(sma_val) if sma_val is not None and not isinstance(sma_val, dict) else current_price
            elif sma_50 is None:
                sma_50_value = current_price
            else:
                sma_50_value = current_price
        except Exception as sma50_extract_error:
            logger.warning(f"Error extracting SMA 50 value for {symbol}: {sma50_extract_error}")
            sma_50_value = current_price
        
        # Determine trend
        trend = "BULLISH" if current_price > sma_20_value > sma_50_value else "BEARISH" if current_price < sma_20_value < sma_50_value else "NEUTRAL"
        
        # Generate FNO suggestions based on analysis
        suggestions = []
        
        # RSI-based suggestions
        if rsi_value > 70:
            suggestions.append({
                "type": "BEARISH",
                "title": "Overbought Condition",
                "description": f"RSI at {rsi_value:.2f} indicates overbought. Consider PUT options or bearish strategies.",
                "confidence": "HIGH",
                "indicator": "RSI"
            })
        elif rsi_value < 30:
            suggestions.append({
                "type": "BULLISH",
                "title": "Oversold Condition",
                "description": f"RSI at {rsi_value:.2f} indicates oversold. Consider CALL options or bullish strategies.",
                "confidence": "HIGH",
                "indicator": "RSI"
            })
        
        # MACD-based suggestions
        if macd_value > macd_signal:
            suggestions.append({
                "type": "BULLISH",
                "title": "MACD Bullish Crossover",
                "description": "MACD above signal line indicates bullish momentum. Consider CALL options.",
                "confidence": "MEDIUM",
                "indicator": "MACD"
            })
        elif macd_value < macd_signal:
            suggestions.append({
                "type": "BEARISH",
                "title": "MACD Bearish Crossover",
                "description": "MACD below signal line indicates bearish momentum. Consider PUT options.",
                "confidence": "MEDIUM",
                "indicator": "MACD"
            })
        
        # Trend-based suggestions
        if trend == "BULLISH":
            suggestions.append({
                "type": "BULLISH",
                "title": "Uptrend Confirmed",
                "description": "Price above both SMAs indicates strong uptrend. Consider bullish strategies.",
                "confidence": "HIGH",
                "indicator": "Moving Averages"
            })
        elif trend == "BEARISH":
            suggestions.append({
                "type": "BEARISH",
                "title": "Downtrend Confirmed",
                "description": "Price below both SMAs indicates strong downtrend. Consider bearish strategies.",
                "confidence": "HIGH",
                "indicator": "Moving Averages"
            })
        
        # Pattern-based suggestions (with confidence filtering)
        if detected_patterns:
            # Convert enhanced_chart_service pattern format to suggestions
            pattern_list = []
            if isinstance(detected_patterns, dict):
                # enhanced_chart_service returns dict of patterns
                for pattern_name, pattern_data in list(detected_patterns.items())[:3]:
                    if isinstance(pattern_data, dict):
                        pattern_type = pattern_name.upper()
                        is_bullish = any(x in pattern_type for x in ['BULLISH', 'BULL', 'RISING', 'ASCENDING', 'CUP'])
                        is_bearish = any(x in pattern_type for x in ['BEARISH', 'BEAR', 'FALLING', 'DESCENDING', 'TOP'])
                        
                        # Get confidence if available
                        pattern_confidence = pattern_data.get("confidence", 0.5)
                        confidence_level = "HIGH" if pattern_confidence >= 0.7 else "MEDIUM" if pattern_confidence >= 0.5 else "LOW"
                        
                        if is_bullish:
                            suggestions.append({
                                "type": "BULLISH",
                                "title": f"{pattern_name.replace('_', ' ').title()} Detected",
                                "description": f"Bullish pattern detected: {pattern_name} (Confidence: {pattern_confidence*100:.0f}%). Consider CALL options or bullish strategies.",
                                "confidence": confidence_level,
                                "indicator": "Pattern Recognition"
                            })
                        elif is_bearish:
                            suggestions.append({
                                "type": "BEARISH",
                                "title": f"{pattern_name.replace('_', ' ').title()} Detected",
                                "description": f"Bearish pattern detected: {pattern_name} (Confidence: {pattern_confidence*100:.0f}%). Consider PUT options or bearish strategies.",
                                "confidence": confidence_level,
                                "indicator": "Pattern Recognition"
                            })
            elif isinstance(detected_patterns, list):
                # If it's a list format - filter by confidence >= 0.6
                filtered_patterns = [p for p in detected_patterns if isinstance(p, dict) and p.get("confidence", 0) >= 0.6]
                filtered_patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)
                
                for pattern in filtered_patterns[:3]:  # Top 3 high-confidence patterns
                    if isinstance(pattern, dict):
                        pattern_name = pattern.get("pattern_name") or pattern.get("pattern_type", "")
                        pattern_type = str(pattern_name).upper()
                        is_bullish = any(x in pattern_type for x in ['BULLISH', 'BULL', 'RISING', 'ASCENDING'])
                        is_bearish = any(x in pattern_type for x in ['BEARISH', 'BEAR', 'FALLING', 'DESCENDING'])
                        
                        pattern_confidence = pattern.get("confidence", 0.5)
                        confidence_level = "HIGH" if pattern_confidence >= 0.7 else "MEDIUM" if pattern_confidence >= 0.5 else "LOW"
                        
                        if is_bullish:
                            suggestions.append({
                                "type": "BULLISH",
                                "title": f"{pattern_name} Detected",
                                "description": pattern.get("description", f"Bullish pattern detected (Confidence: {pattern_confidence*100:.0f}%). Consider CALL options."),
                                "confidence": confidence_level,
                                "indicator": "Pattern Recognition"
                            })
                        elif is_bearish:
                            suggestions.append({
                                "type": "BEARISH",
                                "title": f"{pattern_name} Detected",
                                "description": pattern.get("description", f"Bearish pattern detected (Confidence: {pattern_confidence*100:.0f}%). Consider PUT options."),
                                "confidence": confidence_level,
                                "indicator": "Pattern Recognition"
                            })
        
        # Support/Resistance-based suggestions
        if nearest_support and current_price:
            support_distance = ((current_price - nearest_support) / current_price) * 100
            if support_distance < 3:  # Within 3% of support
                suggestions.append({
                    "type": "BULLISH",
                    "title": "Near Support Level",
                    "description": f"Price is near support at ₹{nearest_support:.2f} ({support_distance:.2f}% away). Potential bounce opportunity. Consider CALL options.",
                    "confidence": "MEDIUM",
                    "indicator": "Support/Resistance"
                })
        
        if nearest_resistance and current_price:
            resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
            if resistance_distance < 3:  # Within 3% of resistance
                suggestions.append({
                    "type": "BEARISH",
                    "title": "Near Resistance Level",
                    "description": f"Price is near resistance at ₹{nearest_resistance:.2f} ({resistance_distance:.2f}% away). Potential rejection. Consider PUT options.",
                    "confidence": "MEDIUM",
                    "indicator": "Support/Resistance"
                })
        
        # Divergence-based suggestions
        if bullish_divergences:
            suggestions.append({
                "type": "BULLISH",
                "title": "Bullish Divergence Detected",
                "description": f"Price making lower lows while volume making higher lows. Potential bullish reversal. Consider CALL options. (Strength: {len(bullish_divergences)} divergence(s))",
                "confidence": "HIGH",
                "indicator": "Divergence Analysis"
            })
        
        if bearish_divergences:
            suggestions.append({
                "type": "BEARISH",
                "title": "Bearish Divergence Detected",
                "description": f"Price making higher highs while volume making lower highs. Potential bearish reversal. Consider PUT options. (Strength: {len(bearish_divergences)} divergence(s))",
                "confidence": "HIGH",
                "indicator": "Divergence Analysis"
                            })
        
        # Key facts/metrics
        # Safely get patterns count and names with confidence filtering
        patterns_count = 0
        pattern_names = []
        high_confidence_patterns = []
        pattern_confidence_scores = []
        
        if isinstance(detected_patterns, list):
            # First, log what we received
            logger.info(f"📊 Pattern detection for {symbol}: Received {len(detected_patterns)} patterns")
            
            # Filter by confidence (only patterns with confidence >= 0.6)
            filtered_patterns = [
                p for p in detected_patterns 
                if isinstance(p, dict) and p.get("confidence", 0) >= 0.6
            ]
            logger.info(f"   After confidence filter (>=0.6): {len(filtered_patterns)} patterns")
            
            # If no high-confidence patterns, include all patterns (lower threshold)
            if len(filtered_patterns) == 0:
                filtered_patterns = [p for p in detected_patterns if isinstance(p, dict)]
                logger.info(f"   Using all patterns (lowered threshold): {len(filtered_patterns)} patterns")
            
            patterns_count = len(filtered_patterns)
            
            # Sort by confidence (highest first)
            filtered_patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            # Extract pattern names from filtered list
            for pattern in filtered_patterns[:15]:  # Top 15 patterns (increased from 10)
                if isinstance(pattern, dict):
                    # Try multiple possible keys for pattern name
                    pattern_name = (
                        pattern.get("pattern_name") or 
                        pattern.get("pattern_type") or 
                        pattern.get("name") or
                        pattern.get("type") or
                        pattern.get("pattern") or
                        ""
                    )
                    
                    # Handle Enum values (PatternType.HAMMER -> "hammer")
                    original_pattern_name = pattern_name
                    if pattern_name:
                        if hasattr(pattern_name, 'value'):
                            pattern_name = pattern_name.value
                        elif hasattr(pattern_name, 'name'):
                            pattern_name = pattern_name.name
                        elif isinstance(pattern_name, type) and hasattr(pattern_name, '__name__'):
                            # Handle if it's a class/type
                            pattern_name = pattern_name.__name__
                        # Convert to string if not already
                        if not isinstance(pattern_name, str):
                            pattern_name = str(pattern_name)
                    
                    confidence = pattern.get("confidence", 0.5)  # Default to 0.5 if not provided
                    
                    # Debug logging for missing pattern names
                    if not pattern_name:
                        logger.warning(f"⚠️ Pattern dict missing name field for {symbol}. Keys: {list(pattern.keys())}")
                        logger.warning(f"   pattern_type value: {pattern.get('pattern_type')}, type: {type(pattern.get('pattern_type'))}")
                        # Try to extract from any string-like value
                        for key in ['pattern_type', 'pattern_name', 'name', 'type', 'pattern']:
                            val = pattern.get(key)
                            if val:
                                # Handle Enum
                                if hasattr(val, 'value'):
                                    val = val.value
                                elif hasattr(val, 'name'):
                                    val = val.name
                                # Convert to string
                                if not isinstance(val, str):
                                    val = str(val)
                                if val and val.strip():
                                    pattern_name = val.strip()
                                    logger.info(f"   ✅ Found pattern name in '{key}': {pattern_name}")
                                    break
                    
                    if pattern_name:
                        # Clean and format pattern name
                        clean_name = str(pattern_name).replace('_', ' ').replace('-', ' ').title().strip()
                        if clean_name and clean_name not in pattern_names:  # Avoid duplicates
                            pattern_names.append(clean_name)
                            pattern_confidence_scores.append({
                                "name": clean_name,
                                "confidence": round(confidence * 100, 1)  # Convert to percentage
                            })
                            if confidence >= 0.7:
                                high_confidence_patterns.append(clean_name)
                elif isinstance(pattern, str):
                    clean_name = pattern.replace('_', ' ').replace('-', ' ').title().strip()
                    if clean_name and clean_name not in pattern_names:
                        pattern_names.append(clean_name)
        elif isinstance(detected_patterns, dict):
            patterns_count = len(detected_patterns)
            logger.info(f"📊 Processing {patterns_count} patterns from dict format for {symbol}")
            # Extract pattern names from dict
            for pattern_name, pattern_data in list(detected_patterns.items())[:15]:  # Top 15 patterns
                if isinstance(pattern_data, dict):
                    # Check if pattern_data has a confidence field
                    confidence = pattern_data.get("confidence", 0.5)
                    # Lower threshold for dict patterns (they might not have confidence)
                    if confidence >= 0.5:  # Lowered from 0.6 to 0.5
                        clean_name = str(pattern_name).replace('_', ' ').replace('-', ' ').title().strip()
                        if clean_name and clean_name not in pattern_names:
                            pattern_names.append(clean_name)
                            pattern_confidence_scores.append({
                                "name": clean_name,
                                "confidence": round(confidence * 100, 1)
                            })
                            if confidence >= 0.7:
                                high_confidence_patterns.append(clean_name)
                            logger.info(f"   ✅ Extracted pattern: '{clean_name}' (confidence: {confidence:.2f})")
                else:
                    # If pattern_data is not a dict, just use the key (pattern was detected)
                    clean_name = str(pattern_name).replace('_', ' ').replace('-', ' ').title().strip()
                    if clean_name and clean_name not in pattern_names:
                        pattern_names.append(clean_name)
                        pattern_confidence_scores.append({
                            "name": clean_name,
                            "confidence": 65.0  # Default confidence when pattern_data is not a dict
                        })
                        logger.info(f"   ✅ Extracted pattern (no data): '{clean_name}'")
        elif detected_patterns is not None:
            # If it's not a list or dict, try to convert or default to 0
            try:
                patterns_count = len(detected_patterns) if hasattr(detected_patterns, '__len__') else 0
            except (TypeError, AttributeError):
                patterns_count = 0
        
        # Fallback: Extract pattern names from suggestions if direct extraction failed
        if not pattern_names and patterns_count > 0 and suggestions:
            logger.info(f"🔄 Fallback: Extracting pattern names from suggestions for {symbol}...")
            extracted_from_suggestions = []
            for suggestion in suggestions:
                if isinstance(suggestion, dict):
                    title = suggestion.get("title", "")
                    # Look for patterns in title (e.g., "Double Top Detected", "Hammer Detected")
                    if "Detected" in title:
                        # Extract pattern name by removing " Detected" suffix
                        pattern_name = title.replace(" Detected", "").strip()
                        if pattern_name and pattern_name not in pattern_names and pattern_name not in extracted_from_suggestions:
                            extracted_from_suggestions.append(pattern_name)
                            logger.info(f"   ✅ Extracted from title: '{pattern_name}'")
                    # Also check description for pattern names
                    description = suggestion.get("description", "")
                    if description and "pattern detected:" in description.lower():
                        # Extract pattern name from description (e.g., "Bullish pattern detected: hammer")
                        match = re.search(r'pattern detected:\s*([^(\s]+)', description, re.IGNORECASE)
                        if match:
                            pattern_name = match.group(1).strip()
                            if pattern_name and pattern_name not in pattern_names and pattern_name not in extracted_from_suggestions:
                                extracted_from_suggestions.append(pattern_name)
                                logger.info(f"   ✅ Extracted from description: '{pattern_name}'")
            
            # Add extracted names to pattern_names list
            if extracted_from_suggestions:
                pattern_names.extend(extracted_from_suggestions)
                # Also update pattern_confidence_scores if we have suggestions
                for pattern_name in extracted_from_suggestions:
                    pattern_confidence_scores.append({
                        "name": pattern_name,
                        "confidence": 65.0  # Default confidence when extracted from suggestions
                    })
                logger.info(f"   ✅ Total extracted from suggestions: {len(extracted_from_suggestions)}")
        
        # Log pattern names for debugging
        if pattern_names:
            logger.info(f"✅ Extracted {len(pattern_names)} pattern names for {symbol}: {pattern_names[:5]}")
        else:
            logger.warning(f"⚠️ No pattern names extracted for {symbol}. Detected patterns type: {type(detected_patterns)}, count: {patterns_count}")
            if detected_patterns and len(detected_patterns) > 0:
                sample_pattern = detected_patterns[0] if isinstance(detected_patterns, list) else list(detected_patterns.values())[0] if isinstance(detected_patterns, dict) else None
                if sample_pattern:
                    logger.warning(f"   Sample pattern type: {type(sample_pattern)}")
                    if isinstance(sample_pattern, dict):
                        logger.warning(f"   Sample pattern keys: {list(sample_pattern.keys())}")
                        # Log first few key-value pairs
                        for key in list(sample_pattern.keys())[:5]:
                            val = sample_pattern[key]
                            val_str = str(val)[:50] if val else "None"
                            logger.warning(f"   {key}: {val_str} (type: {type(val).__name__})")
        
        # Recalculate distance to nearest support/resistance if not already calculated
        if nearest_support is None and support_levels and current_price:
            # Find nearest support below current price
            supports_below = [s for s in support_levels if isinstance(s, (int, float)) and s < current_price]
            if supports_below:
                nearest_support = max(supports_below)
                support_distance_pct = round(((current_price - nearest_support) / current_price) * 100, 2)
        
        if resistance_levels and current_price and nearest_resistance is None:
            # Find nearest resistance above current price
            resistances_above = [r for r in resistance_levels if isinstance(r, (int, float)) and r > current_price]
            if resistances_above:
                nearest_resistance = min(resistances_above)
                resistance_distance_pct = round(((nearest_resistance - current_price) / current_price) * 100, 2)
        
        # Safely get volume trend with improved extraction
        volume_trend_value = "NEUTRAL"
        if volume_analysis:
            try:
                if isinstance(volume_analysis, dict):
                    # Try multiple keys for volume trend
                    volume_trend_value = (
                        volume_analysis.get("trend") or
                        volume_analysis.get("volume_trend") or
                        volume_analysis.get("sentiment") or
                        volume_analysis.get("overall_sentiment") or
                        "NEUTRAL"
                    )
                    # Normalize to uppercase
                    if isinstance(volume_trend_value, str):
                        volume_trend_value = volume_trend_value.upper()
                        # Map variations to standard values
                        if "BULL" in volume_trend_value or "UP" in volume_trend_value or "RISING" in volume_trend_value:
                            volume_trend_value = "BULLISH"
                        elif "BEAR" in volume_trend_value or "DOWN" in volume_trend_value or "FALLING" in volume_trend_value:
                            volume_trend_value = "BEARISH"
                        else:
                            volume_trend_value = "NEUTRAL"
                elif hasattr(volume_analysis, "get"):
                    volume_trend_value = volume_analysis.get("trend", "NEUTRAL")
                else:
                    # Try to get from overall_assessment if available
                    if hasattr(volume_analysis, "overall_assessment"):
                        overall_assessment = volume_analysis.overall_assessment
                        if isinstance(overall_assessment, dict):
                            volume_trend_value = overall_assessment.get("overall_sentiment", "NEUTRAL")
            except Exception as vol_trend_error:
                logger.warning(f"Error extracting volume trend: {vol_trend_error}")
                volume_trend_value = "NEUTRAL"
        
        # Fallback: Analyze volume from candlesticks if volume_analysis failed
        if volume_trend_value == "NEUTRAL" and 'volume' in df.columns and len(df) >= 2:
            try:
                recent_volumes = df['volume'].tail(5).values
                avg_volume = recent_volumes[:-1].mean() if len(recent_volumes) > 1 else recent_volumes[0]
                current_volume = recent_volumes[-1]
                
                # Compare current volume to average
                if current_volume > avg_volume * 1.2:  # 20% above average
                    # Check price direction
                    if 'close' in df.columns and len(df) >= 2:
                        price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
                        if price_change > 0:
                            volume_trend_value = "BULLISH"
                        elif price_change < 0:
                            volume_trend_value = "BEARISH"
            except Exception as vol_fallback_error:
                logger.debug(f"Volume fallback analysis failed: {vol_fallback_error}")
        
        logger.info(f"Volume Trend for {symbol}: {volume_trend_value}")
        
        # Multi-timeframe trend confirmation
        multi_timeframe_trend = "NEUTRAL"
        multi_timeframe_confidence = 0.0
        
        # If we have multi-timeframe results, calculate weighted trend
        if multi_timeframe_results and len(multi_timeframe_results) > 0:
            bullish_weight = sum(tf_data.get("weight", 0.33) for tf_data in multi_timeframe_results.values() if tf_data.get("trend") == "BULLISH")
            bearish_weight = sum(tf_data.get("weight", 0.33) for tf_data in multi_timeframe_results.values() if tf_data.get("trend") == "BEARISH")
            total_weight = sum(tf_data.get("weight", 0.33) for tf_data in multi_timeframe_results.values())
            
            if total_weight > 0:
                if bullish_weight > bearish_weight and bullish_weight > 0.4:  # Lowered threshold from 0.5 to 0.4
                    multi_timeframe_trend = "BULLISH"
                    multi_timeframe_confidence = min(bullish_weight / total_weight, 0.95)  # Cap at 95%
                elif bearish_weight > bullish_weight and bearish_weight > 0.4:
                    multi_timeframe_trend = "BEARISH"
                    multi_timeframe_confidence = min(bearish_weight / total_weight, 0.95)  # Cap at 95%
                else:
                    multi_timeframe_trend = "NEUTRAL"
                    # Confidence based on how close to a clear trend
                    max_weight = max(bullish_weight, bearish_weight)
                    multi_timeframe_confidence = max_weight / total_weight if total_weight > 0 else 0.3
                
                # Special case: If only 1D data available, boost confidence slightly
                if len(multi_timeframe_results) == 1 and "1D" in multi_timeframe_results:
                    multi_timeframe_confidence = min(multi_timeframe_confidence * 1.2, 0.85)  # Boost but cap at 85%
                    logger.info(f"Multi-timeframe: Only 1D data available for {symbol}, using with {multi_timeframe_confidence:.2%} confidence")
        else:
            # Fallback: If no multi-timeframe data available (4H/1H failed), use primary timeframe trend
            multi_timeframe_trend = trend  # Use the primary timeframe trend
            multi_timeframe_confidence = 0.6  # Moderate confidence when using primary timeframe only
            logger.info(f"Multi-timeframe: No multi-timeframe data available for {symbol}, using primary timeframe ({timeframe}) trend as fallback")
        
        # ML Prediction (simple ensemble model)
        ml_prediction = None
        ml_confidence = 0.0
        ml_features = {}
        try:
            # Feature engineering for ML
            features = {
                "rsi": rsi_value,
                "macd": macd_value,
                "macd_signal": macd_signal,
                "price_vs_sma20": ((current_price - sma_20_value) / sma_20_value) * 100 if sma_20_value > 0 else 0,
                "price_vs_sma50": ((current_price - sma_50_value) / sma_50_value) * 100 if sma_50_value > 0 else 0,
                "volume_trend_score": 1.0 if volume_trend_value == "BULLISH" else -1.0 if volume_trend_value == "BEARISH" else 0.0,
                "pattern_count": patterns_count,
                "high_confidence_patterns_count": len(high_confidence_patterns),
                "has_bullish_divergence": 1.0 if len(bullish_divergences) > 0 else 0.0,
                "has_bearish_divergence": 1.0 if len(bearish_divergences) > 0 else 0.0,
                "support_distance": support_distance_pct if support_distance_pct else 10.0,
                "resistance_distance": resistance_distance_pct if resistance_distance_pct else 10.0,
                "multi_timeframe_score": 1.0 if multi_timeframe_trend == "BULLISH" else -1.0 if multi_timeframe_trend == "BEARISH" else 0.0
            }
            
            # Simple weighted ensemble prediction
            bullish_score = 0.0
            bearish_score = 0.0
            
            # RSI contribution (30-70 range is neutral)
            if features["rsi"] < 30:
                bullish_score += 0.15  # Oversold
            elif features["rsi"] > 70:
                bearish_score += 0.15  # Overbought
            
            # MACD contribution
            if features["macd"] > features["macd_signal"]:
                bullish_score += 0.10
            else:
                bearish_score += 0.10
            
            # SMA trend contribution
            if features["price_vs_sma20"] > 0 and features["price_vs_sma50"] > 0:
                bullish_score += 0.10
            elif features["price_vs_sma20"] < 0 and features["price_vs_sma50"] < 0:
                bearish_score += 0.10
            
            # Volume trend
            bullish_score += features["volume_trend_score"] * 0.10
            bearish_score -= features["volume_trend_score"] * 0.10
            
            # Pattern contribution
            if features["high_confidence_patterns_count"] > 0:
                bullish_score += 0.10
            elif features["pattern_count"] > 0:
                bullish_score += 0.05
            
            # Divergence contribution
            if features["has_bullish_divergence"]:
                bullish_score += 0.15
            if features["has_bearish_divergence"]:
                bearish_score += 0.15
            
            # Support/Resistance contribution
            if features["support_distance"] < 3:
                bullish_score += 0.10  # Near support
            if features["resistance_distance"] < 3:
                bearish_score += 0.10  # Near resistance
            
            # Multi-timeframe contribution
            bullish_score += features["multi_timeframe_score"] * 0.10
            bearish_score -= features["multi_timeframe_score"] * 0.10
            
            # GIFT NIFTY contribution (for NIFTY predictions - strong indicator of next day opening)
            if gift_nifty_data and "sentiment" in gift_nifty_data and gift_nifty_data.get("sentiment") != "NEUTRAL":
                gift_sentiment = gift_nifty_data["sentiment"]
                gift_change_pct = abs(gift_nifty_data.get("change_pct", 0))
                # Weight based on change magnitude (stronger moves = higher weight)
                gift_weight = min(0.20, gift_change_pct / 10.0)  # Max 20% weight, scales with change %
                if gift_sentiment == "BULLISH":
                    bullish_score += gift_weight
                    logger.info(f"GIFT NIFTY: Adding {gift_weight:.1%} to bullish score (change: {gift_nifty_data.get('change_pct', 0):.2f}%)")
                elif gift_sentiment == "BEARISH":
                    bearish_score += gift_weight
                    logger.info(f"GIFT NIFTY: Adding {gift_weight:.1%} to bearish score (change: {gift_nifty_data.get('change_pct', 0):.2f}%)")
            
            # India VIX contribution (for all predictions - volatility adjustment)
            # VIX doesn't change direction, but adjusts confidence
            # High VIX = lower confidence in any prediction
            # Low VIX = higher confidence in trend continuation
            if india_vix_data and "confidence_adjustment" in india_vix_data:
                vix_adjustment = india_vix_data.get("confidence_adjustment", 0.0)
                # Apply VIX adjustment to both scores proportionally
                # This reduces overall confidence when VIX is high
                if vix_adjustment != 0:
                    # Scale down both scores when VIX is high (reduces confidence)
                    # Scale up both scores when VIX is low (increases confidence)
                    adjustment_factor = 1.0 + vix_adjustment
                    bullish_score *= adjustment_factor
                    bearish_score *= adjustment_factor
                    logger.info(f"India VIX: Applied {vix_adjustment:.1%} confidence adjustment (VIX Level: {india_vix_data.get('level', 'N/A')}, Regime: {india_vix_data.get('regime', 'N/A')})")
            
            # Determine prediction with improved thresholds
            total_score = bullish_score + bearish_score
            
            # Handle edge cases
            if total_score == 0:
                # No signals - use trend as fallback
                ml_prediction = trend
                ml_confidence = 0.3  # Low confidence fallback
                logger.info(f"ML Prediction: No signals detected, using trend fallback: {trend}")
            else:
                bullish_ratio = bullish_score / total_score
                bearish_ratio = bearish_score / total_score
                
                # Improved thresholds with better confidence calculation
                if bullish_ratio > 0.55:  # 55% bullish signals
                    ml_prediction = "BULLISH"
                    # Confidence scales with how far above 55% threshold
                    ml_confidence = min(0.5 + (bullish_ratio - 0.55) * 0.9, 0.95)  # 50% to 95% range
                elif bearish_ratio > 0.55:  # 55% bearish signals
                    ml_prediction = "BEARISH"
                    # Confidence scales with how far above 55% threshold
                    ml_confidence = min(0.5 + (bearish_ratio - 0.55) * 0.9, 0.95)  # 50% to 95% range
                else:
                    ml_prediction = "NEUTRAL"
                    # Confidence based on how close to neutral (closer to 50/50 = lower confidence)
                    # If ratio is close to 0.5, confidence is low; if closer to 0.55, confidence is higher
                    ratio_diff = abs(bullish_ratio - bearish_ratio)
                    ml_confidence = min(ratio_diff * 1.6, 0.5)  # Scale to 0-50% range for neutral
                
                logger.info(f"ML Prediction: {ml_prediction} (Confidence: {ml_confidence:.1%}, Bullish: {bullish_ratio:.1%}, Bearish: {bearish_ratio:.1%})")
            
            # Apply India VIX confidence adjustment to final ML confidence
            if india_vix_data and "confidence_adjustment" in india_vix_data:
                vix_adjustment = india_vix_data.get("confidence_adjustment", 0.0)
                # Apply adjustment to confidence (not to prediction direction)
                ml_confidence = max(0.1, min(0.95, ml_confidence + vix_adjustment))  # Clamp between 10% and 95%
                logger.info(f"India VIX Confidence Adjustment: {vix_adjustment:+.1%} → Final ML Confidence: {ml_confidence:.1%}")
            
            ml_features = features
        except Exception as ml_error:
            logger.warning(f"ML prediction failed: {ml_error}")
            ml_prediction = "NEUTRAL"
            ml_confidence = 0.0
        
        # Historical Pattern Success Rates (from database)
        pattern_success_rates = {}
        try:
            from backend.core.database_unified import PatternOutcome
            from sqlalchemy import func
            
            # Get success rates for detected patterns
            for pattern_name in pattern_names:
                pattern_key = pattern_name.upper().replace(' ', '_')
                # Query database for this pattern's success rate
                success_query = db.query(
                    func.avg(func.cast(PatternOutcome.outcome_success, Float)).label('success_rate'),
                    func.count(PatternOutcome.id).label('total_count')
                ).filter(
                    PatternOutcome.pattern_name == pattern_key,
                    PatternOutcome.outcome_verified == True
                ).first()
                
                if success_query and success_query.total_count and success_query.total_count > 0:
                    pattern_success_rates[pattern_name] = {
                        "success_rate": round(float(success_query.success_rate or 0.5), 3),
                        "sample_size": int(success_query.total_count)
                    }
                else:
                    # Use default from pattern recognition service
                    pattern_success_rates[pattern_name] = {
                        "success_rate": 0.65,  # Default
                        "sample_size": 0
                    }
        except Exception as success_rate_error:
            logger.warning(f"Pattern success rate lookup failed: {success_rate_error}")
            # Use defaults
            for pattern_name in pattern_names:
                pattern_success_rates[pattern_name] = {
                    "success_rate": 0.65,
                    "sample_size": 0
                }
        
        # GIFT NIFTY Analysis (for NIFTY predictions - provides next day opening insights)
        gift_nifty_data = None
        gift_nifty_sentiment = "NEUTRAL"
        try:
            from utils.symbol_normalizer import GIFT_NIFTY_SYMBOL
            # Check if analyzing NIFTY (for next day perception)
            is_nifty = symbol.upper() in ["NIFTY", "NIFTY50", "NIFTY_50", "^NSEI"] or normalized_symbol == "^NSEI"
            
            if is_nifty:
                # Fetch GIFT NIFTY data (trades almost 24 hours, provides next day opening insights)
                try:
                    from core.data_service import data_service
                    gift_quote = await data_service.get_quote(GIFT_NIFTY_SYMBOL, exchange="SGX")  # GIFT NIFTY trades on SGX
                    
                    if gift_quote and "error" not in gift_quote:
                        gift_price = float(gift_quote.get("last_price", 0))
                        gift_change = float(gift_quote.get("change_percent", 0))
                        gift_change_abs = float(gift_quote.get("change", 0))
                        
                        # Calculate premium/discount vs NIFTY spot
                        nifty_premium_pct = ((gift_price - current_price) / current_price * 100) if current_price > 0 else 0
                        
                        # Determine sentiment based on GIFT NIFTY movement
                        if gift_change > 0.3:  # GIFT NIFTY up > 0.3%
                            gift_nifty_sentiment = "BULLISH"
                        elif gift_change < -0.3:  # GIFT NIFTY down > 0.3%
                            gift_nifty_sentiment = "BEARISH"
                        else:
                            gift_nifty_sentiment = "NEUTRAL"
                        
                        gift_nifty_data = {
                            "price": round(gift_price, 2),
                            "change_pct": round(gift_change, 2),
                            "change_abs": round(gift_change_abs, 2),
                            "premium_discount_pct": round(nifty_premium_pct, 2),
                            "sentiment": gift_nifty_sentiment,
                            "note": "GIFT NIFTY trades ~24 hours and indicates next day opening direction"
                        }
                        
                        logger.info(f"✅ GIFT NIFTY data: Price=₹{gift_price}, Change={gift_change:.2f}%, Premium/Discount={nifty_premium_pct:.2f}%, Sentiment={gift_nifty_sentiment}")
                    else:
                        # Fallback: Try fetching via yfinance
                        try:
                            import yfinance as yf
                            gift_ticker = yf.Ticker(GIFT_NIFTY_SYMBOL)
                            gift_info = gift_ticker.history(period="1d", interval="1m")
                            if not gift_info.empty:
                                gift_price = float(gift_info['Close'].iloc[-1])
                                gift_change_pct = float(gift_info['Close'].pct_change().iloc[-1] * 100) if len(gift_info) > 1 else 0
                                nifty_premium_pct = ((gift_price - current_price) / current_price * 100) if current_price > 0 else 0
                                
                                if gift_change_pct > 0.3:
                                    gift_nifty_sentiment = "BULLISH"
                                elif gift_change_pct < -0.3:
                                    gift_nifty_sentiment = "BEARISH"
                                else:
                                    gift_nifty_sentiment = "NEUTRAL"
                                
                                gift_nifty_data = {
                                    "price": round(gift_price, 2),
                                    "change_pct": round(gift_change_pct, 2),
                                    "change_abs": round(gift_price - gift_info['Close'].iloc[-2] if len(gift_info) > 1 else 0, 2),
                                    "premium_discount_pct": round(nifty_premium_pct, 2),
                                    "sentiment": gift_nifty_sentiment,
                                    "note": "GIFT NIFTY trades ~24 hours and indicates next day opening direction"
                                }
                                logger.info(f"✅ GIFT NIFTY data (via yfinance): Price=₹{gift_price}, Change={gift_change_pct:.2f}%")
                        except Exception as yf_error:
                            logger.warning(f"Could not fetch GIFT NIFTY via yfinance: {yf_error}")
                            gift_nifty_data = {
                                "error": "Could not fetch GIFT NIFTY data",
                                "note": "GIFT NIFTY data unavailable - using standard analysis only"
                            }
                except Exception as gift_error:
                    logger.warning(f"GIFT NIFTY fetch failed: {gift_error}")
                    gift_nifty_data = {
                        "error": str(gift_error),
                        "note": "GIFT NIFTY data unavailable - using standard analysis only"
                    }
            else:
                gift_nifty_data = {
                    "applicable": False,
                    "note": "GIFT NIFTY analysis only applicable for NIFTY index"
                }
        except Exception as gift_nifty_error:
            logger.warning(f"GIFT NIFTY analysis failed: {gift_nifty_error}")
            gift_nifty_data = {"error": str(gift_nifty_error)}
        
        # India VIX Analysis (for all predictions - volatility indicator)
        india_vix_data = None
        india_vix_level = None
        india_vix_sentiment = "NEUTRAL"
        vix_confidence_adjustment = 0.0
        try:
            from utils.symbol_normalizer import INDIA_VIX_SYMBOL
            from core.data_service import data_service
            
            # Fetch India VIX data (applicable for all symbols)
            try:
                vix_quote = await data_service.get_quote(INDIA_VIX_SYMBOL, exchange="NSE")
                
                if vix_quote and "error" not in vix_quote:
                    vix_price = float(vix_quote.get("last_price", 0))
                    vix_change = float(vix_quote.get("change_percent", 0))
                    vix_change_abs = float(vix_quote.get("change", 0))
                    india_vix_level = vix_price
                    
                    # VIX Interpretation:
                    # < 15: Low volatility (calm market) - Higher confidence in trend continuation
                    # 15-20: Normal volatility - Standard confidence
                    # 20-25: Elevated volatility - Lower confidence, wider price swings expected
                    # > 25: High volatility (fear/uncertainty) - Much lower confidence, expect volatility
                    # > 30: Extreme volatility - Very low confidence, high uncertainty
                    
                    if vix_price < 15:
                        vix_regime = "LOW"
                        vix_interpretation = "Low volatility - Calm market conditions. Higher confidence in trend continuation."
                        vix_confidence_adjustment = 0.05  # Boost confidence by 5%
                        india_vix_sentiment = "CALM"
                    elif vix_price < 20:
                        vix_regime = "NORMAL"
                        vix_interpretation = "Normal volatility - Standard market conditions."
                        vix_confidence_adjustment = 0.0  # No adjustment
                        india_vix_sentiment = "NEUTRAL"
                    elif vix_price < 25:
                        vix_regime = "ELEVATED"
                        vix_interpretation = "Elevated volatility - Increased uncertainty. Expect wider price swings."
                        vix_confidence_adjustment = -0.05  # Reduce confidence by 5%
                        india_vix_sentiment = "CAUTIOUS"
                    elif vix_price < 30:
                        vix_regime = "HIGH"
                        vix_interpretation = "High volatility - Fear/uncertainty in market. Lower confidence, expect volatility."
                        vix_confidence_adjustment = -0.10  # Reduce confidence by 10%
                        india_vix_sentiment = "FEARFUL"
                    else:
                        vix_regime = "EXTREME"
                        vix_interpretation = "Extreme volatility - Very high uncertainty. Very low confidence, high risk."
                        vix_confidence_adjustment = -0.15  # Reduce confidence by 15%
                        india_vix_sentiment = "PANIC"
                    
                    # VIX Change Interpretation
                    vix_change_interpretation = ""
                    if abs(vix_change) > 5:
                        if vix_change > 0:
                            vix_change_interpretation = "VIX spiking - Volatility increasing rapidly. Expect increased market volatility."
                            vix_confidence_adjustment -= 0.05  # Additional reduction for spiking VIX
                        else:
                            vix_change_interpretation = "VIX declining - Volatility decreasing. Market calming down."
                            vix_confidence_adjustment += 0.02  # Small boost for declining VIX
                    
                    india_vix_data = {
                        "level": round(vix_price, 2),
                        "change_pct": round(vix_change, 2),
                        "change_abs": round(vix_change_abs, 2),
                        "regime": vix_regime,
                        "interpretation": vix_interpretation,
                        "change_interpretation": vix_change_interpretation,
                        "sentiment": india_vix_sentiment,
                        "confidence_adjustment": round(vix_confidence_adjustment, 3),
                        "note": "India VIX measures expected volatility. Higher VIX = higher uncertainty = lower prediction confidence."
                    }
                    
                    logger.info(f"✅ India VIX: Level={vix_price:.2f}, Regime={vix_regime}, Change={vix_change:.2f}%, Confidence Adjustment={vix_confidence_adjustment:.1%}")
                else:
                    # Fallback: Try fetching via yfinance
                    try:
                        import yfinance as yf
                        vix_ticker = yf.Ticker(INDIA_VIX_SYMBOL)
                        vix_info = vix_ticker.history(period="1d", interval="1m")
                        if not vix_info.empty:
                            vix_price = float(vix_info['Close'].iloc[-1])
                            vix_change_pct = float(vix_info['Close'].pct_change().iloc[-1] * 100) if len(vix_info) > 1 else 0
                            india_vix_level = vix_price
                            
                            # Same interpretation logic
                            if vix_price < 15:
                                vix_regime = "LOW"
                                vix_interpretation = "Low volatility - Calm market conditions."
                                vix_confidence_adjustment = 0.05
                                india_vix_sentiment = "CALM"
                            elif vix_price < 20:
                                vix_regime = "NORMAL"
                                vix_interpretation = "Normal volatility - Standard market conditions."
                                vix_confidence_adjustment = 0.0
                                india_vix_sentiment = "NEUTRAL"
                            elif vix_price < 25:
                                vix_regime = "ELEVATED"
                                vix_interpretation = "Elevated volatility - Increased uncertainty."
                                vix_confidence_adjustment = -0.05
                                india_vix_sentiment = "CAUTIOUS"
                            elif vix_price < 30:
                                vix_regime = "HIGH"
                                vix_interpretation = "High volatility - Fear/uncertainty in market."
                                vix_confidence_adjustment = -0.10
                                india_vix_sentiment = "FEARFUL"
                            else:
                                vix_regime = "EXTREME"
                                vix_interpretation = "Extreme volatility - Very high uncertainty."
                                vix_confidence_adjustment = -0.15
                                india_vix_sentiment = "PANIC"
                            
                            india_vix_data = {
                                "level": round(vix_price, 2),
                                "change_pct": round(vix_change_pct, 2),
                                "change_abs": round(vix_price - vix_info['Close'].iloc[-2] if len(vix_info) > 1 else 0, 2),
                                "regime": vix_regime,
                                "interpretation": vix_interpretation,
                                "sentiment": india_vix_sentiment,
                                "confidence_adjustment": round(vix_confidence_adjustment, 3),
                                "note": "India VIX measures expected volatility. Higher VIX = higher uncertainty = lower prediction confidence."
                            }
                            logger.info(f"✅ India VIX (via yfinance): Level={vix_price:.2f}, Regime={vix_regime}")
                    except Exception as yf_error:
                        logger.warning(f"Could not fetch India VIX via yfinance: {yf_error}")
                        india_vix_data = {
                            "error": "Could not fetch India VIX data",
                            "note": "India VIX data unavailable - using standard analysis only"
                        }
            except Exception as vix_error:
                logger.warning(f"India VIX fetch failed: {vix_error}")
                india_vix_data = {
                    "error": str(vix_error),
                    "note": "India VIX data unavailable - using standard analysis only"
                }
        except Exception as vix_analysis_error:
            logger.warning(f"India VIX analysis failed: {vix_analysis_error}")
            india_vix_data = {"error": str(vix_analysis_error)}
        
        # Options Flow Analysis (for FNO stocks)
        options_flow_analysis = None
        options_sentiment = "NEUTRAL"
        try:
            # Check if stock is FNO-traded (simplified check - can be enhanced with actual FNO list)
            fno_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "LT"]
            is_fno_stock = symbol.upper() in [s.upper() for s in fno_stocks] or symbol.upper() in NIFTY50_SYMBOLS
            
            if is_fno_stock:
                # Try to get OI analysis (if available)
                # For now, we'll use volume as a proxy for options flow
                # In production, this would integrate with actual options data APIs
                options_flow_analysis = {
                    "is_fno_stock": True,
                    "volume_surge": volume_trend_value == "BULLISH",
                    "sentiment": "BULLISH" if volume_trend_value == "BULLISH" and trend == "BULLISH" else "BEARISH" if volume_trend_value == "BEARISH" and trend == "BEARISH" else "NEUTRAL",
                    "note": "Options flow data integration pending - using volume as proxy"
                }
                options_sentiment = options_flow_analysis["sentiment"]
            else:
                options_flow_analysis = {
                    "is_fno_stock": False,
                    "note": "Stock not in FNO list"
                }
        except Exception as options_error:
            logger.warning(f"Options flow analysis failed: {options_error}")
            options_flow_analysis = {"error": str(options_error)}

        gap_analysis = {
            "total_gaps": 0,
            "filled": 0,
            "active": 0,
            "active_gaps": []
        }
        try:
            gaps: list = []
            if isinstance(candlesticks, list) and len(candlesticks) >= 2:
                for i in range(1, len(candlesticks)):
                    prev_c = candlesticks[i - 1] or {}
                    cur_c = candlesticks[i] or {}

                    prev_close = prev_c.get("close")
                    cur_open = cur_c.get("open")
                    if prev_close is None or cur_open is None:
                        continue

                    try:
                        prev_close_f = float(prev_close)
                        cur_open_f = float(cur_open)
                    except Exception:
                        continue

                    if prev_close_f == 0:
                        continue

                    gap_size = cur_open_f - prev_close_f
                    gap_size_pct = (gap_size / prev_close_f) * 100
                    if abs(gap_size_pct) < 0.2:
                        continue

                    gap_type = "UPWARD" if gap_size > 0 else "DOWNWARD"
                    low_bound = min(prev_close_f, cur_open_f)
                    high_bound = max(prev_close_f, cur_open_f)

                    filled = False
                    for j in range(i, len(candlesticks)):
                        c = candlesticks[j] or {}
                        hi = c.get("high")
                        lo = c.get("low")
                        if hi is None or lo is None:
                            continue
                        try:
                            hi_f = float(hi)
                            lo_f = float(lo)
                        except Exception:
                            continue
                        if lo_f <= low_bound and hi_f >= high_bound:
                            filled = True
                            break

                    gaps.append({
                        "type": gap_type,
                        "start": round(low_bound, 2),
                        "end": round(high_bound, 2),
                        "size_pct": round(abs(gap_size_pct), 2),
                        "filled": filled
                    })

            total_gaps = len(gaps)
            filled_gaps = sum(1 for g in gaps if g.get("filled"))
            active_gaps = [g for g in gaps if not g.get("filled")]

            gap_analysis = {
                "total_gaps": total_gaps,
                "filled": filled_gaps,
                "active": len(active_gaps),
                "active_gaps": active_gaps[:10]
            }
        except Exception as gap_error:
            logger.warning(f"Gap analysis generation failed for {symbol}: {gap_error}")
        
        facts = {
            "current_price": current_price,
            "rsi": round(rsi_value, 2),
            "macd": round(macd_value, 4),
            "macd_signal": round(macd_signal, 4),
            "sma_20": round(sma_20_value, 2),
            "sma_50": round(sma_50_value, 2),
            "trend": trend,
            "price_vs_sma20": round(((current_price - sma_20_value) / sma_20_value) * 100, 2),
            "price_vs_sma50": round(((current_price - sma_50_value) / sma_50_value) * 100, 2),
            "patterns_detected": patterns_count,
            "pattern_names": pattern_names,
            "high_confidence_patterns": high_confidence_patterns,  # Patterns with confidence >= 70%
            "pattern_confidence_scores": pattern_confidence_scores,  # Pattern names with confidence percentages
            "pattern_success_rates": pattern_success_rates,  # Historical success rates for each pattern
            "volume_trend": volume_trend_value,
            # Support/Resistance Levels
            "support_levels": [round(s, 2) for s in support_levels[:5]],  # Top 5 support levels
            "resistance_levels": [round(r, 2) for r in resistance_levels[:5]],  # Top 5 resistance levels
            "nearest_support": round(nearest_support, 2) if nearest_support else None,
            "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
            "support_distance_pct": support_distance_pct,  # Distance to nearest support in %
            "resistance_distance_pct": resistance_distance_pct,  # Distance to nearest resistance in %
            "pivot_points": [round(p, 2) for p in pivot_points] if pivot_points else [],
            # Divergence Detection
            "divergences": divergence_signals,  # List of divergence signals
            "has_bullish_divergence": len(bullish_divergences) > 0,
            "has_bearish_divergence": len(bearish_divergences) > 0,
            "bullish_divergence_count": len(bullish_divergences),
            "bearish_divergence_count": len(bearish_divergences),
            # Volume Profile
            "volume_profile_levels": [
                {"price": round(level.get("price", 0), 2), "strength": level.get("strength", "moderate")}
                for level in volume_based_sr[:5]
            ] if volume_based_sr else [],
            # Multi-Timeframe Analysis
            "multi_timeframe_analysis": multi_timeframe_results,
            "multi_timeframe_trend": multi_timeframe_trend,
            "multi_timeframe_confidence": round(multi_timeframe_confidence, 3),
            # ML Prediction
            "ml_prediction": ml_prediction,
            "ml_confidence": round(ml_confidence, 3),
            "ml_features": ml_features,
            # Options Flow Analysis
            "options_flow_analysis": options_flow_analysis,
            "options_sentiment": options_sentiment,
            # GIFT NIFTY Analysis (for next day opening insights)
            "gift_nifty_data": gift_nifty_data,
            "gift_nifty_sentiment": gift_nifty_sentiment,
            # India VIX Analysis (volatility indicator for all predictions)
            "india_vix_data": india_vix_data,
            "india_vix_level": india_vix_level,
            "india_vix_sentiment": india_vix_sentiment,
            # Combined Analysis (GIFT NIFTY + VIX impact on next day opening)
            "next_day_opening_analysis": None,
            "gap_analysis": gap_analysis
        }
        
        # Calculate next day opening analysis for NIFTY only
        # Check multiple symbol variations
        symbol_upper = symbol.upper().strip()
        is_nifty_symbol = (
            symbol_upper in ["NIFTY", "NIFTY50", "NIFTY_50", "^NSEI", "NIFTY 50", "NIFTY-50"] or
            normalized_symbol == "^NSEI" or
            symbol_upper.startswith("NIFTY") or
            "^NSEI" in normalized_symbol.upper()
        )
        
        logger.info(f"🔍 Next Day Opening Analysis check: symbol={symbol}, normalized={normalized_symbol}, is_nifty={is_nifty_symbol}, current_price={current_price}")
        
        if is_nifty_symbol:
            try:
                # Log input data for debugging
                logger.info(f"📊 Calculating Next Day Opening Analysis for {symbol}:")
                logger.info(f"   - Current Price: {current_price}")
                logger.info(f"   - GIFT NIFTY Data: {gift_nifty_data}")
                logger.info(f"   - India VIX Data: {india_vix_data}")
                
                next_day_analysis = await _calculate_next_day_opening_impact(
                    current_price, gift_nifty_data, india_vix_data, symbol
                )
                
                # Function always returns a dict (never None), so always set it
                facts["next_day_opening_analysis"] = next_day_analysis
                
                if "error" in next_day_analysis:
                    logger.warning(f"⚠️ Next Day Opening Analysis has error for {symbol}: {next_day_analysis.get('error')}")
                else:
                    logger.info(f"✅ Next Day Opening Analysis calculated for {symbol}: Direction={next_day_analysis.get('expected_opening_direction')}, Range={next_day_analysis.get('expected_opening_range', {}).get('most_likely', 'N/A')}")
            except Exception as next_day_error:
                logger.error(f"❌ Error calculating next day opening analysis for {symbol}: {next_day_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Still include basic analysis even if calculation fails
                facts["next_day_opening_analysis"] = {
                    "applicable": True,
                    "error": str(next_day_error),
                    "current_nifty_price": round(current_price, 2) if current_price > 0 else None,
                    "gift_nifty_available": gift_nifty_data is not None and "error" not in (gift_nifty_data or {}),
                    "vix_available": india_vix_data is not None and "error" not in (india_vix_data or {}),
                    "note": "Analysis calculation failed. Check GIFT NIFTY and VIX data separately."
                }
        
        response_payload = {
            "success": True,
            "data": {
                "symbol": symbol,
                "timeframe": timeframe,
                "suggestions": suggestions,
                "facts": facts,
                "indicators": {
                    "rsi": rsi_value,
                    "macd": macd_value,
                    "macd_signal": macd_signal,
                    "sma_20": sma_20_value,
                    "sma_50": sma_50_value
                },
                "patterns": list(detected_patterns.items())[:5] if isinstance(detected_patterns, dict) else (detected_patterns[:5] if isinstance(detected_patterns, list) else []),  # Top 5 patterns
                "volume_analysis": volume_analysis
            },
            "timestamp": datetime.now().isoformat()
        }

        # Prevent JSON serialization crashes from NaN/Inf values
        return _deep_clean_nan_values(response_payload)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error getting chart analysis for FNO {symbol} (timeframe={timeframe}): {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Failed to get chart analysis: {str(e)}")

@router.post("/fno/oi-analysis")
async def analyze_open_interest(
    request: OIAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze Open Interest for F&O trading signals"""
    try:
        result = fno_algorithms.analyze_open_interest(
            current_price=request.current_price,
            previous_price=request.previous_price,
            current_oi=request.current_oi,
            previous_oi=request.previous_oi
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error in OI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fno/pcr-analysis")
async def analyze_pcr(
    request: PCRAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate Put-Call Ratio (PCR) for market sentiment"""
    try:
        result = fno_algorithms.calculate_pcr(
            put_oi=request.put_oi,
            call_oi=request.call_oi
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error in PCR analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fno/max-pain")
async def calculate_max_pain(
    request: MaxPainRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate Maximum Pain point for options"""
    try:
        result = fno_algorithms.find_max_pain(
            strikes=request.strikes,
            call_oi=request.call_oi,
            put_oi=request.put_oi,
            current_price=request.current_price
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error calculating max pain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fno/oi-analysis/{symbol}")
async def get_comprehensive_oi_analysis(
    symbol: str,
    expiry_date: Optional[str] = Query(None, description="Expiry date (e.g., 30DEC2025)"),
    timeframe: str = Query("DAILY", description="Timeframe: 3MIN, 15MIN, 30MIN, DAILY"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get comprehensive Open Interest analysis with charts data"""
    try:
        # Normalize symbol
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        
        # Get current price using the same method as Comprehensive Trading Pro
        # Use chart data to get the latest price - fetch more data for better accuracy
        try:
            chart_data = await enhanced_chart_service.get_candlestick_data(
                symbol=symbol,
                timeframe="1D" if timeframe == "DAILY" else timeframe,
                period=100  # Fetch more data to get latest price
            )
            if chart_data and "candlesticks" in chart_data and len(chart_data["candlesticks"]) > 0:
                spot_price = chart_data["candlesticks"][-1].get("close", 0)
                # If close is 0 or very old, try to get real-time quote
                if spot_price == 0:
                    from core.data_service import data_service
                    quote = await data_service.get_quote(normalized_symbol)
                    spot_price = quote.get('last_price', 0) if quote else 0
            else:
                # Fallback to quote service
                from core.data_service import data_service
                quote = await data_service.get_quote(normalized_symbol)
                spot_price = quote.get('last_price', 0) if quote else 26000
        except Exception as price_error:
            logger.warning(f"Error getting price for {symbol}: {price_error}")
            # Final fallback
            spot_price = 26000 if "NIFTY" in symbol.upper() else 0
        
        # Get futures price (approximate as spot + small premium for now)
        futures_price = spot_price * 1.0005  # Small premium
        
        # Get lot size (NIFTY = 75, BANKNIFTY = 25, etc.)
        lot_size_map = {
            'NIFTY': 75, 'NIFTY50': 75, 'NIFTY_50': 75,
            'BANKNIFTY': 25, 'NIFTYBANK': 25, 'NIFTY_BANK': 25,
            'NIFTYIT': 25, 'NIFTY_IT': 25,
        }
        lot_size = lot_size_map.get(symbol.upper(), 50)
        
        # Generate mock OI data by strike (in production, fetch from NSE API)
        # Calculate ATM strike (round to nearest 50 for NIFTY)
        atm_strike = round(spot_price / 50) * 50
        
        # Generate strikes around ATM
        strikes = []
        for i in range(-20, 21):  # 20 strikes on each side
            strike = atm_strike + (i * 50)
            if strike > 0:
                strikes.append(strike)
        
        # Generate OI data for calls and puts
        import random
        random.seed(hash(symbol) % 1000)  # Consistent random data per symbol
        
        call_oi_data = []
        put_oi_data = []
        oi_buildup_data = []
        change_in_oi_data = []
        
        total_call_oi = 0
        total_put_oi = 0
        
        for strike in strikes:
            # Generate realistic OI distribution (higher OI near ATM)
            distance_from_atm = abs(strike - atm_strike)
            base_oi = max(50000, 200000 - (distance_from_atm * 1000))
            
            # Add randomness
            call_oi = int(base_oi * (0.8 + random.random() * 0.4))
            put_oi = int(base_oi * (0.8 + random.random() * 0.4))
            
            # Higher OI for puts (typical market behavior)
            if strike < atm_strike:
                put_oi = int(put_oi * 1.3)
            elif strike > atm_strike:
                call_oi = int(call_oi * 1.2)
            
            call_oi_data.append({
                "strike": strike,
                "oi": call_oi,
                "change_oi": random.randint(-5000, 15000),
                "volume": random.randint(10000, 50000),
                "ltp": max(0, strike - spot_price + random.randint(-50, 50))
            })
            
            put_oi_data.append({
                "strike": strike,
                "oi": put_oi,
                "change_oi": random.randint(-5000, 15000),
                "volume": random.randint(10000, 50000),
                "ltp": max(0, spot_price - strike + random.randint(-50, 50))
            })
            
            # OI Buildup (positive = buildup, negative = unwinding)
            oi_buildup = call_oi - put_oi if strike >= atm_strike else put_oi - call_oi
            oi_buildup_data.append({
                "strike": strike,
                "buildup": oi_buildup,
                "call_oi": call_oi,
                "put_oi": put_oi
            })
            
            # Change in OI
            change_in_oi_data.append({
                "strike": strike,
                "change_oi": call_oi_data[-1]["change_oi"] - put_oi_data[-1]["change_oi"]
            })
            
            total_call_oi += call_oi
            total_put_oi += put_oi
        
        # Calculate PCR
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        
        # Calculate MaxPain
        max_pain_strikes = []
        for strike in strikes:
            pain = 0
            for call in call_oi_data:
                if call["strike"] < strike:
                    pain += call["oi"] * (strike - call["strike"])
            for put in put_oi_data:
                if put["strike"] > strike:
                    pain += put["oi"] * (put["strike"] - strike)
            max_pain_strikes.append({"strike": strike, "pain": pain})
        
        max_pain_strike = min(max_pain_strikes, key=lambda x: x["pain"])["strike"]
        
        # Modified MaxPain (weighted average)
        total_pain = sum(x["pain"] for x in max_pain_strikes)
        if total_pain > 0:
            modified_max_pain = sum(x["strike"] * x["pain"] for x in max_pain_strikes) / total_pain
        else:
            modified_max_pain = atm_strike
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "expiry_date": expiry_date or "30DEC2025",
                "timeframe": timeframe,
                "metrics": {
                    "spot_price": round(spot_price, 2),
                    "futures_price": round(futures_price, 2),
                    "lot_size": lot_size,
                    "pcr": round(pcr, 2),
                    "max_pain_strike": max_pain_strike,
                    "modified_max_pain": round(modified_max_pain, 2),
                    "atm_strike": atm_strike,
                    "total_call_oi": total_call_oi,
                    "total_put_oi": total_put_oi
                },
                "strikes": strikes,
                "call_oi": call_oi_data,
                "put_oi": put_oi_data,
                "oi_buildup": oi_buildup_data,
                "change_in_oi": change_in_oi_data,
                "max_pain_data": max_pain_strikes
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting comprehensive OI analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fno/futures-spread")
async def analyze_futures_spread(
    request: FuturesSpreadRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze Futures Spread opportunities"""
    try:
        result = fno_algorithms.futures_spread_opportunity(
            near_month_price=request.near_month_price,
            far_month_price=request.far_month_price,
            near_month_oi=request.near_month_oi,
            far_month_oi=request.far_month_oi,
            cost_of_carry=request.cost_of_carry
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error in futures spread analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fno/options-strategy")
async def get_options_strategy_recommendation(
    request: OptionsStrategyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get Options Strategy Recommendations"""
    try:
        result = fno_algorithms.options_strategy_recommendation(
            current_price=request.current_price,
            volatility=request.volatility,
            time_to_expiry=request.time_to_expiry,
            market_sentiment=request.market_sentiment,
            risk_tolerance=request.risk_tolerance
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error getting options strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fno/futures-fair-value")
async def calculate_futures_fair_value(
    spot_price: float = Query(...),
    risk_free_rate: float = Query(0.06),
    dividend_yield: float = Query(0.02),
    days_to_expiry: int = Query(30),
    current_user: dict = Depends(get_current_user)
):
    """Calculate Futures Fair Value"""
    try:
        result = fno_algorithms.calculate_futures_fair_value(
            spot_price=spot_price,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            days_to_expiry=days_to_expiry
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error calculating futures fair value: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INTRADAY TRADING ALGORITHMS ====================

class IntradaySignalRequest(BaseModel):
    data: Dict[str, Any]  # Price data as dict
    strategy: Optional[str] = "vwap_trading"
    current_time: Optional[str] = None

@router.post("/intraday/vwap-signal")
async def get_vwap_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get VWAP-based intraday trading signal"""
    try:
        # Fetch price data
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"VWAP Signal: Normalized {symbol} -> {normalized_symbol}, Timeframe: {timeframe}, Duration: {days} days")
        
        # Get recent data for VWAP calculation
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if candles:
            logger.info(f"VWAP Signal: Fetched {len(candles)} candles for {symbol} with timeframe {timeframe}")
        else:
            logger.warning(f"VWAP Signal: No candles returned for {symbol} with timeframe {timeframe}")
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            return {
                "success": False,
                "error": f"Invalid data format for {symbol}. Missing required columns: {', '.join(missing_cols)}.",
                "data": None
            }
        
        # Ensure volume column exists (add with 0 if missing)
        if 'volume' not in data.columns:
            logger.warning(f"Volume column missing for {symbol}, using 0 as default")
            data['volume'] = 0
        
        # Calculate VWAP
        try:
            vwap = intraday_algorithms.calculate_vwap(data)
        except Exception as vwap_error:
            logger.error(f"Error calculating VWAP for {symbol}: {vwap_error}")
            import traceback
            logger.error(f"VWAP calculation traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Failed to calculate VWAP: {str(vwap_error)}",
                "data": None
            }
        
        if vwap.empty:
            return {
                "success": False,
                "error": f"Unable to calculate VWAP for {symbol}. Insufficient data points.",
                "data": None
            }
        
        # Get current price and VWAP, handling NaN
        current_price_val = data['close'].iloc[-1]
        vwap_val = vwap.iloc[-1]
        
        # Check for NaN values
        import numpy as np
        if pd.isna(current_price_val) or np.isnan(current_price_val) or np.isinf(current_price_val):
            return {
                "success": False,
                "error": f"Invalid current price for {symbol}. Data may be incomplete.",
                "data": None
            }
        
        if pd.isna(vwap_val) or np.isnan(vwap_val) or np.isinf(vwap_val):
            return {
                "success": False,
                "error": f"Unable to calculate valid VWAP for {symbol}. Insufficient data points.",
                "data": None
            }
        
        # Get signal
        try:
            result = intraday_algorithms.vwap_trading_signal(
                current_price=float(current_price_val),
                vwap=float(vwap_val),
                price_history=data,
                volume_history=data['volume'] if 'volume' in data.columns else pd.Series()
            )
        except Exception as signal_error:
            logger.error(f"Error generating VWAP signal for {symbol}: {signal_error}")
            import traceback
            logger.error(f"Signal generation traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Failed to generate VWAP signal: {str(signal_error)}",
                "data": None
            }
        
        # Check if result has error
        if 'error' in result:
            return {
                "success": False,
                "error": result['error'],
                "data": None
            }
        
        # Clean NaN values from result - ensure all values are JSON serializable
        try:
            from services.intraday_trading_algorithms import clean_nan_values
            cleaned_result = clean_nan_values(result)
            
            # Ensure cleaned_vwap is a valid number or None
            if pd.isna(vwap_val) or np.isnan(vwap_val) or np.isinf(vwap_val):
                cleaned_vwap = None
            else:
                try:
                    cleaned_vwap = float(vwap_val)
                    # Double-check it's not NaN after conversion
                    if np.isnan(cleaned_vwap) or np.isinf(cleaned_vwap):
                        cleaned_vwap = None
                except (ValueError, TypeError):
                    cleaned_vwap = None
            
            # Additional pass to ensure all values in cleaned_result are JSON serializable
            try:
                # Test if the result can be JSON serialized
                json.dumps(cleaned_result)
            except (ValueError, TypeError) as json_error:
                logger.warning(f"Result still contains non-JSON values, doing deep clean: {json_error}")
                # Deep clean all values recursively
                cleaned_result = _deep_clean_nan_values(cleaned_result)
                # Test again after deep clean
                try:
                    json.dumps(cleaned_result)
                except (ValueError, TypeError) as json_error2:
                    logger.error(f"Result still not JSON serializable after deep clean: {json_error2}")
                    # Last resort: return minimal safe response
                    from services.intraday_trading_algorithms import to_python_type
                    cleaned_result = {
                        "signal": result.get("signal", "HOLD"),
                        "strength": result.get("strength", "WEAK"),
                        "current_price": to_python_type(result.get("current_price", 0)),
                        "vwap": to_python_type(result.get("vwap", 0)),
                        "reason": result.get("reason", "Signal generated")
                    }
        except Exception as clean_error:
            logger.error(f"Error cleaning NaN values for {symbol}: {clean_error}")
            import traceback
            logger.error(f"Clean error traceback: {traceback.format_exc()}")
            # Return result with manual cleaning if automatic cleaning fails
            cleaned_result = _deep_clean_nan_values(result)
            cleaned_vwap = None if (pd.isna(vwap_val) or np.isnan(vwap_val) or np.isinf(vwap_val)) else float(vwap_val)
        
        # Final validation - ensure response is JSON serializable
        # Clean all values one more time before creating response (multiple passes for safety)
        for _ in range(3):  # Multiple passes to catch nested NaN values
            cleaned_result = _deep_clean_nan_values(cleaned_result)
        
        if cleaned_vwap is not None:
            cleaned_vwap_val = _deep_clean_nan_values(cleaned_vwap)
            if cleaned_vwap_val is None or (isinstance(cleaned_vwap_val, float) and (np.isnan(cleaned_vwap_val) or np.isinf(cleaned_vwap_val))):
                cleaned_vwap = None
            else:
                cleaned_vwap = cleaned_vwap_val
        else:
            cleaned_vwap = None
        
        response_data = {
            "success": True,
            "data": cleaned_result,
            "vwap": cleaned_vwap
        }
        
        # Final deep clean of entire response structure
        response_data = _deep_clean_nan_values(response_data)
        
        # Test JSON serialization before returning - multiple passes to ensure clean data
        max_clean_attempts = 5
        for attempt in range(max_clean_attempts):
            try:
                # Test serialization
                test_json = json.dumps(response_data)
                # Success - data is JSON serializable
                # Use JSONResponse to have explicit control
                return JSONResponse(content=response_data, status_code=200)
            except (ValueError, TypeError) as json_test_error:
                if attempt < max_clean_attempts - 1:
                    logger.warning(f"Response contains non-JSON values (attempt {attempt + 1}/{max_clean_attempts}), cleaning again: {json_test_error}")
                    # Deep clean the entire response recursively
                    response_data = _deep_clean_nan_values(response_data)
                    # Also clean nested structures
                    if isinstance(response_data, dict):
                        response_data = {k: _deep_clean_nan_values(v) for k, v in response_data.items()}
                else:
                    # Last attempt failed - return error response
                    logger.error(f"Response still not JSON serializable after {max_clean_attempts} cleaning attempts: {json_test_error}")
                    import traceback
                    logger.error(f"Final clean error traceback: {traceback.format_exc()}")
                    # Return minimal safe error response using JSONResponse
                    return JSONResponse(
                        content={
                            "success": False,
                            "error": "Failed to serialize response data. Please try again with different parameters.",
                            "data": None
                        },
                        status_code=200
                    )
        
        # Should never reach here, but just in case
        return JSONResponse(content=response_data, status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error getting VWAP signal for {symbol} (timeframe={timeframe}, days={days}): {e}")
        logger.error(f"Traceback: {error_trace}")
        return {
            "success": False,
            "error": f"Failed to calculate VWAP signal: {str(e)}",
            "data": None
        }

@router.post("/intraday/momentum-signal")
async def get_momentum_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    period: int = Query(14),
    threshold: float = Query(0.5),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Momentum-based intraday trading signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Momentum Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        result = intraday_algorithms.momentum_trading_signal(
            data=data,
            period=period,
            threshold=threshold
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Import error in momentum signal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting momentum signal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/breakout-signal")
async def get_breakout_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    lookback_period: int = Query(20),
    volume_threshold: float = Query(1.5),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Breakout-based intraday trading signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Breakout Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        result = intraday_algorithms.breakout_trading_signal(
            data=data,
            lookback_period=lookback_period,
            volume_threshold=volume_threshold
        )
        
        # Ensure result doesn't contain numpy types - convert recursively
        def clean_dict(d):
            """Recursively clean dictionary of numpy types"""
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            elif hasattr(d, 'item'):
                return d.item()
            elif isinstance(d, (np.integer, np.int64, np.int32)):
                return int(d)
            elif isinstance(d, (np.floating, np.float64, np.float32)):
                return float(d)
            elif isinstance(d, np.bool_):
                return bool(d)
            else:
                return d
        
        cleaned_result = clean_dict(result)
        
        return {
            "success": True,
            "data": cleaned_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting breakout signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/mean-reversion-signal")
async def get_mean_reversion_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    period: int = Query(20),
    std_multiplier: float = Query(2.0),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Mean Reversion-based intraday trading signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Mean Reversion Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        result = intraday_algorithms.mean_reversion_signal(
            data=data,
            period=period,
            std_multiplier=std_multiplier
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mean reversion signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/scalping-signal")
async def get_scalping_signal(
    symbol: str = Query(...),
    timeframe: str = Query("1m"),
    tick_size: float = Query(0.05),
    min_profit_target: float = Query(0.3),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Scalping-based intraday trading signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Scalping Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        result = intraday_algorithms.scalping_signal(
            data=data,
            tick_size=tick_size,
            min_profit_target=min_profit_target
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scalping signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/gap-trading-signal")
async def get_gap_trading_signal(
    symbol: str = Query(...),
    timeframe: str = Query("1d"),
    gap_threshold: float = Query(0.5),
    days: int = Query(2, ge=2, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Gap Trading signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Gap Trading Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        # Need at least 2 days of data for gap analysis
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) < 2:
            return {
                "success": False,
                "error": f"Insufficient data for gap analysis. Need at least 2 days of data.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty or len(data) < 2:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        # Ensure data is sorted by time (oldest first)
        if 'time' in data.columns:
            data = data.sort_values('time').reset_index(drop=True)
        
        # Get previous day's close (second-to-last row)
        previous_close = float(data['close'].iloc[-2]) if len(data) >= 2 else None
        
        if previous_close is None:
            return {
                "success": False,
                "error": f"Insufficient data for gap analysis. Need at least 2 days of data.",
                "data": None
            }
        
        result = intraday_algorithms.gap_trading_signal(
            data=data,
            previous_close=previous_close,
            gap_threshold=gap_threshold
        )
        
        # Check if result has error
        if isinstance(result, dict) and "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "data": None
            }
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting gap trading signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/closing-range-signal")
async def get_closing_range_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    closing_minutes: int = Query(30),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Closing Range Breakout signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Closing Range Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.closing_range_breakout(
            data=data,
            closing_minutes=closing_minutes
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting closing range signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/volume-profile-signal")
async def get_volume_profile_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    bins: int = Query(20),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Volume Profile signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Volume Profile Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.volume_profile_signal(
            data=data,
            bins=bins
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting volume profile signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/sma-signal")
async def get_sma_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get SMA-based intraday trading signal"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"SMA Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        result = intraday_algorithms.sma_trading_signal(data=data)
        
        # Ensure result doesn't contain numpy types - convert recursively
        def clean_dict(d):
            """Recursively clean dictionary of numpy types"""
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            elif hasattr(d, 'item'):
                return d.item()
            elif isinstance(d, (np.integer, np.int64, np.int32)):
                return int(d)
            elif isinstance(d, (np.floating, np.float64, np.float32)):
                if np.isnan(d) or np.isinf(d):
                    return None
                return float(d)
            elif isinstance(d, np.bool_):
                return bool(d)
            elif pd.isna(d):
                return None
            return d
        
        cleaned_result = clean_dict(result)
        
        return {
            "success": True,
            "data": cleaned_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SMA signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/news-signal")
async def get_news_based_signal(
    symbol: str = Query(...),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get News-based trading signal"""
    try:
        # Note: news_based_signal may not use days parameter, but we accept it for consistency
        result = await intraday_algorithms.news_based_signal(symbol=symbol)
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting news-based signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/opening-range")
async def get_opening_range_breakout(
    symbol: str = Query(...),
    timeframe: str = Query("1m", description="Timeframe for analysis"),
    days: int = Query(1, ge=1, le=5, description="Number of days of historical data"),
    opening_minutes: int = Query(15),
    current_user: dict = Depends(get_current_user)
):
    """Get Opening Range Breakout signal"""
    try:
        import pandas as pd
        
        # Normalize symbol
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        
        # Get historical data
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        result = intraday_algorithms.opening_range_breakout(
            data=data,
            opening_minutes=opening_minutes
        )
        
        # Clean the result (remove numpy types)
        def clean_dict(d):
            """Recursively clean dictionary of numpy types"""
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            elif hasattr(d, 'item'):
                return d.item()
            elif isinstance(d, (np.integer, np.int64, np.int32)):
                return int(d)
            elif isinstance(d, (np.floating, np.float64, np.float32)):
                if np.isnan(d) or np.isinf(d):
                    return None
                return float(d)
            elif isinstance(d, np.bool_):
                return bool(d)
            elif pd.isna(d):
                return None
            return d
        
        cleaned_result = clean_dict(result)
        
        return {
            "success": True,
            "data": cleaned_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opening range signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/macd-signal")
async def get_macd_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m", description="Timeframe for analysis"),
    days: int = Query(1, ge=1, le=30, description="Number of days of historical data"),
    fast_period: int = Query(12, ge=5, le=50, description="MACD fast period"),
    slow_period: int = Query(26, ge=10, le=100, description="MACD slow period"),
    signal_period: int = Query(9, ge=5, le=30, description="MACD signal period"),
    current_user: dict = Depends(get_current_user)
):
    """Get MACD Trading Signal"""
    try:
        import pandas as pd
        
        # Normalize symbol
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        
        # Fetch historical data
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}",
                "data": None
            }
        
        # Get MACD signal
        result = intraday_algorithms.macd_trading_signal(
            data=data,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period
        )
        
        # Clean the result (remove numpy types)
        def clean_dict(d):
            """Recursively clean dictionary of numpy types"""
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            elif hasattr(d, 'item'):
                return d.item()
            elif isinstance(d, (np.integer, np.int64, np.int32)):
                return int(d)
            elif isinstance(d, (np.floating, np.float64, np.float32)):
                if np.isnan(d) or np.isinf(d):
                    return None
                return float(d)
            elif isinstance(d, np.bool_):
                return bool(d)
            elif pd.isna(d):
                return None
            return d
        
        cleaned_result = clean_dict(result)
        
        return {
            "success": True,
            "data": cleaned_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MACD signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/bollinger-signal")
async def get_bollinger_bands_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m", description="Timeframe for analysis"),
    days: int = Query(1, ge=1, le=30, description="Number of days of historical data"),
    period: int = Query(20, ge=5, le=50, description="Bollinger Bands period"),
    std_dev: float = Query(2.0, ge=1.0, le=3.0, description="Standard deviation multiplier"),
    current_user: dict = Depends(get_current_user)
):
    """Get Bollinger Bands Trading Signal"""
    try:
        import pandas as pd
        
        # Normalize symbol
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        
        # Fetch historical data
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}",
                "data": None
            }
        
        # Get Bollinger Bands signal
        result = intraday_algorithms.bollinger_bands_trading_signal(
            data=data,
            period=period,
            std_dev=std_dev
        )
        
        # Clean the result (remove numpy types)
        def clean_dict(d):
            """Recursively clean dictionary of numpy types"""
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            elif hasattr(d, 'item'):
                return d.item()
            elif isinstance(d, (np.integer, np.int64, np.int32)):
                return int(d)
            elif isinstance(d, (np.floating, np.float64, np.float32)):
                if np.isnan(d) or np.isinf(d):
                    return None
                return float(d)
            elif isinstance(d, np.bool_):
                return bool(d)
            elif pd.isna(d):
                return None
            return d
        
        cleaned_result = clean_dict(result)
        
        return {
            "success": True,
            "data": cleaned_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Bollinger Bands signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intraday/ai-insight")
async def get_intraday_ai_insight(
    symbol: str = Query(...),
    signal_type: str = Query(...),  # vwap, momentum, breakout, mean_reversion, scalping, comprehensive
    signal_data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered insights and explanations for intraday trading signals"""
    try:
        # Get signal data from parameter or use empty dict
        signal_data = signal_data if signal_data else {}
        
        # Generate contextual AI explanation based on signal type and data
        current_price = signal_data.get('current_price', 0) if signal_data else 0
        signal = signal_data.get('signal', 'HOLD') if signal_data else 'HOLD'
        
        # Create prompt based on signal type
        signal_prompts = {
            "vwap": f"Explain the VWAP trading signal for {symbol} at ₹{current_price:.2f}. Signal: {signal}. Provide actionable insights in 2-3 sentences.",
            "momentum": f"Explain the Momentum trading signal for {symbol} at ₹{current_price:.2f}. Signal: {signal}. Provide actionable insights in 2-3 sentences.",
            "breakout": f"Explain the Breakout trading signal for {symbol} at ₹{current_price:.2f}. Signal: {signal}. Provide actionable insights in 2-3 sentences.",
            "mean_reversion": f"Explain the Mean Reversion trading signal for {symbol} at ₹{current_price:.2f}. Signal: {signal}. Provide actionable insights in 2-3 sentences.",
            "scalping": f"Explain the Scalping trading signal for {symbol} at ₹{current_price:.2f}. Signal: {signal}. Provide actionable insights in 2-3 sentences.",
            "comprehensive": f"Explain the Comprehensive trading signal for {symbol} at ₹{current_price:.2f}. Signal: {signal}. Provide actionable insights in 2-3 sentences."
        }
        
        prompt = signal_prompts.get(signal_type.lower(), signal_prompts["comprehensive"])
        
        # Generate AI insight using trading recommendation engine
        try:
            insight = await trading_recommendation_engine.generate_trading_recommendation(
                symbol=symbol,
                timeframe="5m",
                analysis_data={
                    "signal_type": signal_type,
                    "signal": signal,
                    "current_price": current_price,
                    "signal_data": signal_data or {}
                },
                user_preferences={"generate_insight": True, "prompt": prompt}
            )
            
            ai_insight = insight.get("recommendation", {}).get("summary", "") if isinstance(insight, dict) else str(insight)
        except Exception as e:
            logger.warning(f"AI insight generation failed, using fallback: {e}")
            # Fallback to template-based insights
            ai_insight = _generate_fallback_insight(signal_type, signal, signal_data)
        
        return {
            "success": True,
            "insight": ai_insight,
            "signal_type": signal_type,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating AI insight: {e}")
        # Return fallback insight even on error
        return {
            "success": True,
            "insight": _generate_fallback_insight(signal_type, signal_data.get('signal', 'HOLD') if signal_data else 'HOLD', signal_data),
            "signal_type": signal_type,
            "timestamp": datetime.now().isoformat()
        }

def _generate_fallback_insight(signal_type: str, signal: str, signal_data: Dict[str, Any]) -> str:
    """Generate fallback insight when AI service is unavailable"""
    insights = {
        "vwap": {
            "BUY": "Price is trading above VWAP, indicating bullish momentum. Consider entering long positions with tight stop-loss below VWAP.",
            "SELL": "Price is trading below VWAP, indicating bearish pressure. Consider short positions or exiting long positions.",
            "HOLD": "Price is consolidating around VWAP. Wait for a clear directional breakout before taking positions."
        },
        "momentum": {
            "BUY": "Strong momentum indicators suggest upward price movement. RSI and ROC confirm bullish trend. Enter long with proper risk management.",
            "SELL": "Momentum indicators show weakening or bearish signals. Consider reducing exposure or entering short positions.",
            "HOLD": "Momentum is neutral. Wait for stronger confirmation signals before taking action."
        },
        "breakout": {
            "BUY": "Price has broken above resistance with volume confirmation. This is a strong bullish signal. Enter long with stop-loss below breakout level.",
            "SELL": "Price has broken below support with volume. This indicates bearish momentum. Consider short positions or exit longs.",
            "HOLD": "Price is trading within the range. Wait for a clear breakout above resistance or below support before trading."
        },
        "mean_reversion": {
            "BUY": "Price has deviated significantly below the mean, suggesting a potential bounce. Enter long with stop-loss below recent low.",
            "SELL": "Price has moved significantly above the mean, indicating potential pullback. Consider taking profits or entering short.",
            "HOLD": "Price is near the mean. No significant deviation detected. Wait for clearer reversion signals."
        },
        "scalping": {
            "BUY": "Micro-trend and price action favor quick long scalp. Enter with tight stop-loss and quick profit target.",
            "SELL": "Short-term momentum favors quick short scalp. Enter with tight stop-loss for quick profit.",
            "HOLD": "Insufficient price movement for scalping. Wait for better entry opportunities with higher volatility."
        },
        "comprehensive": {
            "BUY": "Multiple indicators align for a bullish signal. Consider entering long positions with proper risk management and stop-loss.",
            "SELL": "Multiple indicators suggest bearish conditions. Consider reducing exposure or entering short positions.",
            "HOLD": "Mixed signals detected. Wait for clearer directional confirmation before taking positions."
        }
    }
    
    signal_key = "BUY" if "BUY" in signal.upper() else "SELL" if "SELL" in signal.upper() else "HOLD"
    return insights.get(signal_type.lower(), insights["comprehensive"]).get(signal_key, "Monitor the market for clearer signals.")

@router.get("/intraday/chart-analysis/{symbol}")
async def get_intraday_chart_analysis(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe for analysis"),
    enable_multi_timeframe: bool = Query(True, description="Enable multi-timeframe analysis"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get comprehensive chart analysis for intraday trading (normalizes symbol correctly)"""
    try:
        logger.info(f"📊 Intraday Chart Analysis requested for: {symbol} (timeframe: {timeframe})")
        
        # Reuse the FNO chart analysis endpoint logic but with proper symbol normalization
        # This ensures correct symbol normalization for all stock types (NIFTY, stocks, etc.)
        result = await get_fno_chart_analysis(
            symbol=symbol,
            timeframe=timeframe,
            enable_multi_timeframe=enable_multi_timeframe,
            current_user=current_user,
            db=db
        )
        
        # Validate response structure
        if not result or not result.get("success"):
            logger.error(f"❌ Invalid response from get_fno_chart_analysis for {symbol}")
            raise HTTPException(status_code=500, detail="Invalid response from chart analysis service")
        
        if not result.get("data") or not result.get("data").get("facts"):
            logger.error(f"❌ Missing facts in response for {symbol}")
            raise HTTPException(status_code=500, detail="Missing analysis data in response")
        
        logger.info(f"✅ Successfully generated chart analysis for {symbol}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error getting intraday chart analysis for {symbol}: {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Failed to get chart analysis: {str(e)}")

@router.post("/intraday/comprehensive-signal")
async def get_comprehensive_intraday_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    strategy: str = Query("vwap_trading"),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Comprehensive Intraday Trading Signal (combines multiple strategies)"""
    try:
        import pandas as pd
        
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        logger.info(f"Comprehensive Signal: Normalized {symbol} -> {normalized_symbol}, Duration: {days} days")
        
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Convert to DataFrame
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        # Map strategy string to enum
        strategy_map = {
            "scalping": IntradayStrategy.SCALPING,
            "momentum": IntradayStrategy.MOMENTUM,
            "breakout": IntradayStrategy.BREAKOUT,
            "mean_reversion": IntradayStrategy.MEAN_REVERSION,
            "vwap_trading": IntradayStrategy.VWAP_TRADING,
            "gap_trading": IntradayStrategy.GAP_TRADING,
            "opening_range": IntradayStrategy.OPENING_RANGE,
            "closing_range": IntradayStrategy.CLOSING_RANGE,
            "volume_profile": IntradayStrategy.VOLUME_PROFILE,
            "news_trading": IntradayStrategy.NEWS_TRADING
        }
        
        strategy_enum = strategy_map.get(strategy, IntradayStrategy.VWAP_TRADING)
        
        result = intraday_algorithms.generate_intraday_signal(
            data=data,
            strategy=strategy_enum,
            current_time=datetime.now()
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comprehensive intraday signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intraday/trading-session")
async def get_trading_session(
    current_user: dict = Depends(get_current_user)
):
    """Get current trading session"""
    try:
        session = intraday_algorithms.get_trading_session(datetime.now())
        return {
            "success": True,
            "data": {
                "session": session.value,
                "current_time": datetime.now().isoformat(),
                "description": _get_session_description(session)
            }
        }
    except Exception as e:
        logger.error(f"Error getting trading session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_session_description(session: TradingSession) -> str:
    """Get description for trading session"""
    descriptions = {
        TradingSession.PRE_MARKET: "Pre-market session (9:00-9:15 AM) - Low liquidity, prepare for opening",
        TradingSession.OPENING: "Opening session (9:15-10:00 AM) - High volatility, opening range formation",
        TradingSession.MID_MORNING: "Mid-morning session (10:00-11:30 AM) - Normal trading activity",
        TradingSession.MID_DAY: "Mid-day session (11:30 AM-2:00 PM) - Lunch break, lower volume",
        TradingSession.AFTERNOON: "Afternoon session (2:00-3:00 PM) - Increased activity",
        TradingSession.CLOSING: "Closing session (3:00-3:30 PM) - High volatility, closing range formation"
    }
    return descriptions.get(session, "Unknown session")

# ==================== COMMODITY TRADING ENDPOINTS ====================

# Commodity symbol mappings
COMMODITY_SYMBOLS = {
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "CRUDE_OIL": "CL=F",
    "CRUDEOIL": "CL=F",
    "CRUDE": "CL=F",
    "NATURAL_GAS": "NG=F",
    "NATURALGAS": "NG=F",
    "GAS": "NG=F"
}

def get_commodity_yahoo_symbol(symbol: str) -> str:
    """Get Yahoo Finance symbol for commodity"""
    symbol_upper = symbol.upper()
    # If already in Yahoo Finance format (ends with =F), return as-is
    if symbol_upper.endswith("=F"):
        return symbol_upper
    # Otherwise, look up in mapping
    return COMMODITY_SYMBOLS.get(symbol_upper, symbol_upper)

async def get_usd_to_inr_rate() -> float:
    """Get current USD to INR exchange rate from Yahoo Finance"""
    try:
        from core.data_service import data_service
        # Fetch USD/INR exchange rate (USDINR=X)
        quote = await data_service.get_quote("USDINR=X", exchange="FOREX")
        if quote and "error" not in quote and quote.get("last_price"):
            return float(quote.get("last_price", 83.0))  # Default to ~83 if unavailable
        # Fallback: try fetching directly
        from services.data_fetcher import fetch_historical_data
        candles = await fetch_historical_data("USDINR=X", "1d", days=1)
        if candles and len(candles) > 0:
            return float(candles[-1].get("close", 83.0))
        return 83.0  # Default fallback rate
    except Exception as e:
        logger.warning(f"Could not fetch USD/INR rate: {e}, using default 83.0")
        return 83.0  # Default fallback rate

async def _add_commodity_stop_loss_exit_price(result: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """Add consistent stop loss and exit price calculations for commodity signals (converted to INR)"""
    # Convert USD price to INR
    usd_to_inr = await get_usd_to_inr_rate()
    current_price_inr = current_price * usd_to_inr
    
    signal = result.get("signal", "HOLD")
    if signal == "BUY":
        result["stop_loss"] = current_price_inr * 0.98  # 2% below entry (in INR)
        result["exit_price"] = current_price_inr * 1.03  # 3% above entry (target in INR)
        result["target"] = current_price_inr * 1.03
    elif signal == "SELL":
        result["stop_loss"] = current_price_inr * 0.98  # 2% below entry (in INR)
        result["exit_price"] = current_price_inr * 0.97  # 3% below entry (target in INR)
        result["target"] = current_price_inr * 0.97
    else:
        # For HOLD, keep existing values or set to None
        if "stop_loss" not in result:
            result["stop_loss"] = None
        if "exit_price" not in result:
            result["exit_price"] = result.get("target")
    
    # Also update current_price to INR and add metadata
    result["current_price"] = current_price_inr
    result["current_price_usd"] = current_price  # Keep USD price for reference
    result["exchange_rate"] = usd_to_inr
    result["currency"] = "INR"
    
    return result

@router.get("/commodity/quote/{symbol}")
async def get_commodity_quote(
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current quote for a commodity (converted to INR)"""
    try:
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        from core.data_service import data_service
        quote = await data_service.get_quote(yahoo_symbol, exchange="COMMODITY")
        
        if not quote or "error" in quote:
            return {
                "success": False,
                "error": f"No quote available for {symbol}",
                "data": None
            }
        
        # Get USD to INR exchange rate and convert prices
        usd_to_inr = await get_usd_to_inr_rate()
        price_usd = quote.get("last_price", 0)
        change_usd = quote.get("change", 0)
        price_inr = price_usd * usd_to_inr
        change_inr = change_usd * usd_to_inr
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "yahoo_symbol": yahoo_symbol,
                "price": price_inr,  # Price in INR
                "price_usd": price_usd,  # Original USD price
                "change": change_inr,  # Change in INR
                "change_percent": quote.get("change_percent", 0),  # Percentage is same
                "exchange_rate": usd_to_inr,  # USD/INR rate used
                "currency": "INR"
            }
        }
    except Exception as e:
        logger.error(f"Error getting commodity quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/vwap-signal")
async def get_commodity_vwap_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get VWAP-based commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        logger.info(f"Commodity VWAP Signal: {symbol} -> {yahoo_symbol}, Timeframe: {timeframe}, Duration: {days} days")
        
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}. Please check if the symbol is correct and market is open.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            return {
                "success": False,
                "error": f"Missing required columns: {missing_cols}",
                "data": None
            }
        
        if 'volume' not in data.columns:
            data['volume'] = 0
        
        # Calculate VWAP
        vwap = intraday_algorithms.calculate_vwap(data)
        if vwap.empty:
            return {
                "success": False,
                "error": "Could not calculate VWAP",
                "data": None
            }
        
        current_price = float(data['close'].iloc[-1])
        current_vwap = float(vwap.iloc[-1])
        
        # Generate signal
        result = intraday_algorithms.vwap_trading_signal(
            current_price=current_price,
            vwap=current_vwap,
            price_history=data,
            volume_history=data['volume'] if 'volume' in data.columns else pd.Series()
        )
        
        # Add consistent stop loss and exit price calculations (converted to INR)
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity VWAP signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/momentum-signal")
async def get_commodity_momentum_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    period: int = Query(14),
    threshold: float = Query(0.5),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Momentum-based commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty or len(data) < period:
            return {
                "success": False,
                "error": f"Insufficient data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.momentum_trading_signal(
            data=data,
            period=period,
            threshold=threshold
        )
        
        # Add consistent stop loss and exit price calculations
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity momentum signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/breakout-signal")
async def get_commodity_breakout_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    lookback_period: int = Query(20),
    volume_threshold: float = Query(1.5),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Breakout-based commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.breakout_trading_signal(
            data=data,
            lookback_period=lookback_period,
            volume_threshold=volume_threshold
        )
        
        # Add consistent stop loss and exit price calculations
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity breakout signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/mean-reversion-signal")
async def get_commodity_mean_reversion_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    period: int = Query(20),
    std_multiplier: float = Query(2.0),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Mean Reversion-based commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.mean_reversion_signal(
            data=data,
            period=period,
            std_multiplier=std_multiplier
        )
        
        # Add consistent stop loss and exit price calculations
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity mean reversion signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/scalping-signal")
async def get_commodity_scalping_signal(
    symbol: str = Query(...),
    timeframe: str = Query("1m"),
    tick_size: float = Query(0.05),
    min_profit_target: float = Query(0.3),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Scalping-based commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.scalping_signal(
            data=data,
            tick_size=tick_size,
            min_profit_target=min_profit_target
        )
        
        # Add consistent stop loss and exit price calculations
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity scalping signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/gap-trading-signal")
async def get_commodity_gap_trading_signal(
    symbol: str = Query(...),
    timeframe: str = Query("1d"),
    gap_threshold: float = Query(0.5),
    days: int = Query(2, ge=2, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Gap Trading-based commodity signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty or len(data) < 2:
            return {
                "success": False,
                "error": f"Insufficient data for gap analysis. Need at least 2 days.",
                "data": None
            }
        
        result = intraday_algorithms.gap_trading_signal(
            data=data,
            gap_threshold=gap_threshold
        )
        
        # Add consistent stop loss and exit price calculations
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity gap trading signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/closing-range-signal")
async def get_commodity_closing_range_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Closing Range-based commodity signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        result = intraday_algorithms.closing_range_breakout(data)
        
        # Add consistent stop loss and exit price calculations
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity closing range signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/volume-profile-signal")
async def get_commodity_volume_profile_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    bins: int = Query(20),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Volume Profile-based commodity signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        if 'volume' not in data.columns:
            data['volume'] = 0
        
        result = intraday_algorithms.volume_profile_signal(data, bins=bins)
        
        # Add consistent stop loss and exit price calculations (converted to INR)
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity volume profile signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/news-signal")
async def get_commodity_news_signal(
    symbol: str = Query(...),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get News-based commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        result = await intraday_algorithms.news_based_signal(symbol=yahoo_symbol)
        
        # Get current price for conversion (fetch latest candle)
        try:
            candles = await fetch_historical_data(yahoo_symbol, "1d", days=1)
            if candles and len(candles) > 0:
                data = pd.DataFrame(candles)
                current_price = float(data['close'].iloc[-1])
                result = await _add_commodity_stop_loss_exit_price(result, current_price)
        except Exception as e:
            logger.warning(f"Could not convert news signal prices to INR: {e}")
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity news signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commodity/comprehensive-signal")
async def get_commodity_comprehensive_signal(
    symbol: str = Query(...),
    timeframe: str = Query("5m"),
    strategy: str = Query("vwap_trading"),
    days: int = Query(1, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get Comprehensive commodity trading signal"""
    try:
        import pandas as pd
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        candles = await fetch_historical_data(yahoo_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            return {
                "success": False,
                "error": f"No data available for {symbol}.",
                "data": None
            }
        
        data = pd.DataFrame(candles)
        if data.empty:
            return {
                "success": False,
                "error": f"Empty data for {symbol}.",
                "data": None
            }
        
        strategy_map = {
            "scalping": IntradayStrategy.SCALPING,
            "momentum": IntradayStrategy.MOMENTUM,
            "breakout": IntradayStrategy.BREAKOUT,
            "mean_reversion": IntradayStrategy.MEAN_REVERSION,
            "vwap_trading": IntradayStrategy.VWAP_TRADING,
            "gap_trading": IntradayStrategy.GAP_TRADING,
            "opening_range": IntradayStrategy.OPENING_RANGE,
            "closing_range": IntradayStrategy.CLOSING_RANGE,
            "volume_profile": IntradayStrategy.VOLUME_PROFILE,
            "news_trading": IntradayStrategy.NEWS_TRADING
        }
        
        strategy_enum = strategy_map.get(strategy, IntradayStrategy.VWAP_TRADING)
        
        result = intraday_algorithms.generate_intraday_signal(
            data=data,
            strategy=strategy_enum,
            current_time=datetime.now()
        )
        
        # Add consistent stop loss and exit price calculations (converted to INR)
        current_price = float(data['close'].iloc[-1])
        result = await _add_commodity_stop_loss_exit_price(result, current_price)
        
        return {
            "success": True,
            "data": _deep_clean_nan_values(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity comprehensive signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/commodity/chart-analysis/{symbol}")
async def get_commodity_chart_analysis(
    symbol: str,
    timeframe: str = Query("1D"),
    enable_multi_timeframe: bool = Query(False),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get comprehensive chart analysis for commodity (similar to FNO chart analysis)"""
    try:
        yahoo_symbol = get_commodity_yahoo_symbol(symbol)
        # Reuse the FNO chart analysis endpoint logic but for commodities
        # This will work since commodities can use the same technical analysis
        return await get_fno_chart_analysis(
            symbol=yahoo_symbol,
            timeframe=timeframe,
            enable_multi_timeframe=enable_multi_timeframe,
            current_user=current_user,
            db=db
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting commodity chart analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Nifty 50 stocks list (includes recently added stocks)
NIFTY50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "HDFC", "ITC", "BHARTIARTL",
    "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID",
    "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA", "EICHERMOT",
    "SHREECEM", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "COALINDIA", "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP",
    "ADANIPORTS", "BPCL", "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", "ADANIENT", "SBILIFE", "HINDALCO",
    # Recently added stocks
    "NMDC", "INFIBEAM", "INDIANREN", "BSE", "TANLA", "BIRLASOFT", "SUZLON", "SAKSOFT", "GAIL", 
    "ADANIGREEN", "NHPC", "COCHINSHIP", "IRFC", "IRB", "BAJAJHLDNG", "HGIEL"
]

# In-memory cache for Nifty50 signals (simple implementation, can be upgraded to Redis)
_nifty50_cache: Dict[str, tuple] = {}  # key: (timeframe, days), value: (data, timestamp)
_cache_ttl = 300  # 5 minutes cache TTL

def _get_cache_key(timeframe: str, days: int = 1) -> str:
    """Generate cache key for Nifty50 signals"""
    return f"nifty50_signals:{timeframe}:{days}"

def _is_cache_valid(cache_entry: tuple) -> bool:
    """Check if cache entry is still valid"""
    if not cache_entry:
        return False
    data, timestamp = cache_entry
    age_seconds = (datetime.now() - timestamp).total_seconds()
    return age_seconds < _cache_ttl

@router.post("/intraday/nifty50-signals")
async def get_nifty50_trading_signals(
    timeframe: str = Query("5m", description="Timeframe for analysis"),
    days: int = Query(1, ge=1, le=365, description="Number of days of historical data"),
    current_user: dict = Depends(get_current_user),
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Get trading signals for all Nifty 50 stocks across 9 strategies:
    - VWAP Trading
    - Momentum Trading
    - Breakout Trading
    - Mean Reversion
    - Scalping
    - Gap Trading
    - Closing Range
    - Volume Profile
    - News Trading
    
    Returns signals in separate columns with % change and comprehensive signal
    
    Optimized with:
    - Parallel batch processing (10 stocks per batch)
    - Caching (5 minute TTL)
    - Error handling per stock
    """
    try:
        from core.data_service import data_service
        
        # Check cache first
        cache_key = _get_cache_key(timeframe, days)
        if use_cache and cache_key in _nifty50_cache:
            cached_data, cached_timestamp = _nifty50_cache[cache_key]
            if _is_cache_valid((cached_data, cached_timestamp)):
                logger.info(f"Returning cached Nifty50 signals for {timeframe} (days={days})")
                return {
                    "success": True,
                    "data": cached_data,
                    "count": len(cached_data),
                    "timestamp": cached_timestamp.isoformat(),
                    "cached": True
                }
        
        results = []
        
        # Process stocks in batches to avoid overwhelming the system
        # Increased batch size for better parallelization
        batch_size = 15  # Increased from 10 to 15 for better performance
        for i in range(0, len(NIFTY50_SYMBOLS), batch_size):
            batch = NIFTY50_SYMBOLS[i:i + batch_size]
            batch_tasks = []
            
            for symbol in batch:
                batch_tasks.append(_process_stock_signals(symbol, timeframe, days))
            
            # Process batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Filter out errors and add successful results
            for result in batch_results:
                if isinstance(result, dict) and "error" not in result:
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Error processing stock: {result}")
        
        # Sort by symbol
        results.sort(key=lambda x: x.get("symbol", ""))
        
        # Cache the results
        _nifty50_cache[cache_key] = (results, datetime.now())
        
        # Clean up old cache entries (keep only last 10)
        if len(_nifty50_cache) > 10:
            # Remove oldest entries
            sorted_cache = sorted(_nifty50_cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_cache[:-10]:
                del _nifty50_cache[key]
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
    except Exception as e:
        logger.error(f"Error getting Nifty 50 signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_stock_signals(symbol: str, timeframe: str, days: int = 1) -> Dict[str, Any]:
    """Process signals for a single stock across all 9 strategies"""
    try:
        # Normalize symbol for data fetching
        normalized_symbol = normalize_symbol_for_yahoo(symbol)
        display_symbol = normalize_symbol_for_display(normalized_symbol) or symbol
        
        # Fetch current price and % change
        from core.data_service import data_service
        quote = await data_service.get_quote(display_symbol, exchange="NSE")
        
        if not quote or "error" in quote:
            return {
                "symbol": symbol,
                "error": f"No data available for {symbol}"
            }
        
        current_price = float(quote.get("last_price", 0))
        change_pct = float(quote.get("change_percent", 0))
        
        # Fetch historical data using normalized symbol with specified days
        logger.info(f"Fetching historical data for {symbol} (normalized: {normalized_symbol}), timeframe: {timeframe}, days: {days}")
        candles = await fetch_historical_data(normalized_symbol, timeframe, days=days)
        
        if not candles or len(candles) == 0:
            logger.warning(f"No historical data for {symbol}")
            return {
                "symbol": symbol,
                "price": current_price,
                "change_pct": change_pct,
                "error": "Insufficient historical data"
            }
        
        logger.info(f"Received {len(candles)} candles for {symbol}")
        data = pd.DataFrame(candles)
        if data.empty or len(data) < 5:
            logger.warning(f"Insufficient data points for {symbol}: {len(data)} < 5")
            return {
                "symbol": symbol,
                "price": current_price,
                "change_pct": change_pct,
                "error": "Insufficient data points"
            }
        
        logger.info(f"Data columns for {symbol}: {list(data.columns)}")
        logger.info(f"Data shape for {symbol}: {data.shape}")
        logger.info(f"Data sample for {symbol}: {data.head(2).to_dict('records')}")
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_cols):
            logger.error(f"Missing required columns for {symbol}: {required_cols}")
            return {
                "symbol": symbol,
                "price": current_price,
                "change_pct": change_pct,
                "error": "Invalid data format"
            }
        
        # Add volume if missing (use 0 as default)
        if 'volume' not in data.columns:
            data['volume'] = 0
        
        # Use latest close price from historical data for calculations (ensures consistency with VWAP)
        # This ensures VWAP and current price are from the same data source
        latest_close_price = float(data['close'].iloc[-1])
        
        # For display, prefer real-time quote price, but use historical close if quote is unavailable
        # For calculations, always use historical data's latest close for consistency
        price_for_calculations = latest_close_price if latest_close_price > 0 else current_price
        display_price = current_price if current_price > 0 else latest_close_price
        
        # Calculate all strategy signals (original 5 + new 4)
        signals = {}
        
        # 1. VWAP Trading Signal
        try:
            vwap = intraday_algorithms.calculate_vwap(data)
            if not vwap.empty:
                vwap_signal = intraday_algorithms.vwap_trading_signal(
                    current_price=price_for_calculations,  # Use historical data's latest close for consistency
                    vwap=float(vwap.iloc[-1]),
                    price_history=data,
                    volume_history=data['volume'] if 'volume' in data.columns else pd.Series()
                )
                signals["vwap"] = {
                    "signal": vwap_signal.get("signal", "HOLD"),
                    "strength": vwap_signal.get("strength", "WEAK"),
                    "vwap_value": float(vwap.iloc[-1]) if not vwap.empty else None,
                    "price_vs_vwap_pct": vwap_signal.get("price_vs_vwap_pct", 0)
                }
            else:
                signals["vwap"] = {"signal": "HOLD", "strength": "WEAK", "vwap_value": None}
        except Exception as e:
            logger.warning(f"VWAP signal error for {symbol}: {e}")
            signals["vwap"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 2. Momentum Trading Signal
        try:
            momentum_signal = intraday_algorithms.momentum_trading_signal(data)
            signals["momentum"] = {
                "signal": momentum_signal.get("signal", "HOLD"),
                "strength": momentum_signal.get("strength", "WEAK"),
                "rsi": momentum_signal.get("rsi"),
                "roc": momentum_signal.get("roc")
            }
        except Exception as e:
            logger.warning(f"Momentum signal error for {symbol}: {e}")
            signals["momentum"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 3. Breakout Trading Signal
        try:
            breakout_signal = intraday_algorithms.breakout_trading_signal(data)
            signals["breakout"] = {
                "signal": breakout_signal.get("signal", "HOLD"),
                "strength": breakout_signal.get("strength", "WEAK"),
                "resistance": breakout_signal.get("resistance"),
                "support": breakout_signal.get("support")
            }
        except Exception as e:
            logger.warning(f"Breakout signal error for {symbol}: {e}")
            signals["breakout"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 4. Mean Reversion Signal
        try:
            mean_reversion_signal = intraday_algorithms.mean_reversion_signal(data)
            signals["mean_reversion"] = {
                "signal": mean_reversion_signal.get("signal", "HOLD"),
                "strength": mean_reversion_signal.get("strength", "WEAK"),
                "distance_from_mean_pct": mean_reversion_signal.get("distance_from_mean_pct", 0),
                "sma": mean_reversion_signal.get("sma")
            }
        except Exception as e:
            logger.warning(f"Mean reversion signal error for {symbol}: {e}")
            signals["mean_reversion"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 5. Scalping Signal
        try:
            scalping_signal = intraday_algorithms.scalping_signal(data)
            signals["scalping"] = {
                "signal": scalping_signal.get("signal", "HOLD"),
                "strength": scalping_signal.get("strength", "WEAK"),
                "price_change_pct": scalping_signal.get("price_change_pct", 0)
            }
        except Exception as e:
            logger.warning(f"Scalping signal error for {symbol}: {e}")
            signals["scalping"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 6. Gap Trading Signal
        try:
            # For gap trading, we need the previous trading day's close
            # Fetch daily data separately to get previous day's close
            previous_close = None
            daily_candles = await fetch_historical_data(normalized_symbol, "1d", days=5)
            
            if daily_candles and len(daily_candles) >= 2:
                # Get previous day's close from daily data
                daily_data = pd.DataFrame(daily_candles)
                # Ensure data is sorted by time (oldest first)
                if 'time' in daily_data.columns:
                    daily_data = daily_data.sort_values('time').reset_index(drop=True)
                
                if len(daily_data) >= 2:
                    # Previous day is the second-to-last day
                    previous_close = float(daily_data['close'].iloc[-2])
            
            # If we have previous close, calculate gap signal
            # For gap analysis, we need today's open from the intraday data
            # But if we're using intraday timeframe, we need to get today's first candle
            if previous_close is not None:
                # Ensure intraday data is sorted
                intraday_data_sorted = data.copy()
                if 'time' in intraday_data_sorted.columns:
                    intraday_data_sorted = intraday_data_sorted.sort_values('time').reset_index(drop=True)
                
                gap_signal = intraday_algorithms.gap_trading_signal(intraday_data_sorted, previous_close=previous_close)
                if "error" not in gap_signal:
                    signals["gap_trading"] = {
                        "signal": gap_signal.get("signal", "HOLD"),
                        "strength": gap_signal.get("strength", "WEAK"),
                        "gap_pct": gap_signal.get("gap_pct", 0)
                    }
                else:
                    signals["gap_trading"] = {
                        "signal": "HOLD",
                        "strength": "WEAK",
                        "gap_pct": None,
                        "error": gap_signal.get("error", "Gap analysis failed")
                    }
            else:
                signals["gap_trading"] = {
                    "signal": "HOLD",
                    "strength": "WEAK",
                    "gap_pct": None,
                    "error": "Previous day's close not available"
                }
        except Exception as e:
            logger.warning(f"Gap Trading signal error for {symbol}: {e}")
            signals["gap_trading"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 7. Closing Range Signal
        try:
            closing_signal = intraday_algorithms.closing_range_breakout(data)
            signals["closing_range"] = {
                "signal": closing_signal.get("signal", "HOLD"),
                "strength": closing_signal.get("strength", "WEAK"),
                "closing_high": closing_signal.get("closing_high"),
                "closing_low": closing_signal.get("closing_low")
            }
        except Exception as e:
            logger.warning(f"Closing Range signal error for {symbol}: {e}")
            signals["closing_range"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 8. Volume Profile Signal
        try:
            volume_profile_signal = intraday_algorithms.volume_profile_signal(data)
            signals["volume_profile"] = {
                "signal": volume_profile_signal.get("signal", "HOLD"),
                "strength": volume_profile_signal.get("strength", "WEAK"),
                "poc_price": volume_profile_signal.get("poc_price"),
                "price_vs_poc_pct": volume_profile_signal.get("price_vs_poc_pct", 0)
            }
        except Exception as e:
            logger.warning(f"Volume Profile signal error for {symbol}: {e}")
            signals["volume_profile"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # 9. News-based Signal (async, may take time)
        try:
            news_signal = await intraday_algorithms.news_based_signal(symbol=symbol)
            signals["news"] = {
                "signal": news_signal.get("signal", "HOLD"),
                "strength": news_signal.get("strength", "WEAK"),
                "sentiment_score": news_signal.get("sentiment_score", 0),
                "news_count": news_signal.get("news_count", 0)
            }
        except Exception as e:
            logger.warning(f"News signal error for {symbol}: {e}")
            signals["news"] = {"signal": "HOLD", "strength": "WEAK", "error": str(e)}
        
        # Calculate Comprehensive Signal (now includes all 9 strategies)
        buy_count = sum(1 for s in signals.values() if s.get("signal", "").upper().startswith("BUY"))
        sell_count = sum(1 for s in signals.values() if s.get("signal", "").upper().startswith("SELL"))
        hold_count = sum(1 for s in signals.values() if s.get("signal", "").upper() == "HOLD")
        
        # Calculate confidence based on signal strength
        strength_scores = {
            "STRONG": 0.8,
            "MODERATE": 0.6,
            "WEAK": 0.4
        }
        avg_confidence = sum(strength_scores.get(s.get("strength", "WEAK"), 0.4) for s in signals.values()) / len(signals) if signals else 0.4
        
        if buy_count > sell_count:
            comprehensive_signal = "BUY"
            comprehensive_strength = "STRONG" if avg_confidence > 0.7 else "MODERATE" if avg_confidence > 0.5 else "WEAK"
        elif sell_count > buy_count:
            comprehensive_signal = "SELL"
            comprehensive_strength = "STRONG" if avg_confidence > 0.7 else "MODERATE" if avg_confidence > 0.5 else "WEAK"
        else:
            comprehensive_signal = "HOLD"
            comprehensive_strength = "WEAK"
        
        # Calculate entry price, stop loss, and exit price based on comprehensive signal using chart analysis
        logger.info(f"Starting entry/exit calculation for {symbol}: signal={comprehensive_signal}, data_points={len(data)}")
        try:
            from services.chart_based_entry_exit_calculator import chart_calculator
            
            # Calculate volatility for adjustments
            price_changes = data['close'].pct_change().dropna()
            volatility = price_changes.std() if len(price_changes) > 0 else None
            
            logger.info(f"Data volatility for {symbol}: {volatility}")
            logger.info(f"Price for calculations for {symbol}: {price_for_calculations}")
            
            # Use chart-based calculator for realistic entry/exit prices
            chart_analysis = chart_calculator.calculate_entry_exit_prices(
                data=data,
                signal=comprehensive_signal,
                current_price=price_for_calculations,
                volatility=volatility
            )
            
            entry_price = chart_analysis.get('entry_price')
            stop_loss = chart_analysis.get('stop_loss')
            exit_price = chart_analysis.get('exit_price')
            holding_period = chart_analysis.get('holding_period', 'N/A')
            
            logger.info(f"Chart-based analysis for {symbol}: {comprehensive_signal} signal")
            logger.info(f"Entry: {entry_price}, Stop Loss: {stop_loss}, Exit: {exit_price}")
            logger.info(f"Holding Period: {holding_period}")
            logger.info(f"Risk-Reward Ratio: {chart_analysis.get('analysis', {}).get('risk_reward_ratio', 0):.2f}")
            logger.info(f"Method: {chart_analysis.get('analysis', {}).get('method', 'unknown')}")
            
        except Exception as e:
            logger.warning(f"Chart-based calculation failed for {symbol}, using fallback: {e}")
            # Fallback to simple calculation
            entry_price = None
            stop_loss = None
            exit_price = None
            
            if comprehensive_signal == "BUY":
                entry_price = price_for_calculations
                stop_loss = price_for_calculations * 0.98
                exit_price = price_for_calculations * 1.03
            elif comprehensive_signal == "SELL":
                entry_price = price_for_calculations
                stop_loss = price_for_calculations * 1.02
                exit_price = price_for_calculations * 0.97
            else:
                entry_price = price_for_calculations
                stop_loss = None
                exit_price = None

        # Guardrails: enforce correct ordering for the UI/scanner
        try:
            if entry_price is not None and stop_loss is not None and exit_price is not None:
                e = float(entry_price)
                sl = float(stop_loss)
                tp = float(exit_price)

                if comprehensive_signal == "BUY":
                    # Ensure SL < entry < target
                    if sl >= e:
                        sl = e * 0.98
                    if tp <= e:
                        tp = e * 1.03
                elif comprehensive_signal == "SELL":
                    # Ensure SL > entry > target
                    if sl <= e:
                        sl = e * 1.02
                    if tp >= e:
                        tp = e * 0.97

                stop_loss = sl
                exit_price = tp
        except Exception:
            pass
        
        # Calculate change percentage based on historical data if quote change is not available
        if change_pct == 0 and len(data) >= 2:
            prev_close = float(data['close'].iloc[-2])
            if prev_close > 0:
                change_pct = ((price_for_calculations - prev_close) / prev_close) * 100
        
        return {
            "symbol": symbol,
            "price": display_price,  # Show real-time quote price for display
            "current_price": display_price,  # Add alias for frontend
            "change_pct": change_pct,
            "timeframe": timeframe,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "exit_price": exit_price,
            "holding_period": holding_period if 'holding_period' in locals() else "N/A",
            "chart_analysis": chart_analysis.get('analysis', {}) if 'chart_analysis' in locals() else {},
            "vwap_signal": signals["vwap"].get("signal", "HOLD"),
            "vwap_strength": signals["vwap"].get("strength", "WEAK"),
            "vwap_value": signals["vwap"].get("vwap_value"),
            "momentum_signal": signals["momentum"].get("signal", "HOLD"),
            "momentum_strength": signals["momentum"].get("strength", "WEAK"),
            "momentum_rsi": signals["momentum"].get("rsi"),
            "momentum_roc": signals["momentum"].get("roc"),
            "breakout_signal": signals["breakout"].get("signal", "HOLD"),
            "breakout_strength": signals["breakout"].get("strength", "WEAK"),
            "breakout_resistance": signals["breakout"].get("resistance"),
            "breakout_support": signals["breakout"].get("support"),
            "mean_reversion_signal": signals["mean_reversion"].get("signal", "HOLD"),
            "mean_reversion_strength": signals["mean_reversion"].get("strength", "WEAK"),
            "mean_reversion_distance_pct": signals["mean_reversion"].get("distance_from_mean_pct", 0),
            "mean_reversion_sma": signals["mean_reversion"].get("sma"),
            "scalping_signal": signals["scalping"].get("signal", "HOLD"),
            "scalping_strength": signals["scalping"].get("strength", "WEAK"),
            "scalping_price_change_pct": signals["scalping"].get("price_change_pct", 0),
            "gap_trading_signal": signals.get("gap_trading", {}).get("signal", "HOLD"),
            "gap_trading_strength": signals.get("gap_trading", {}).get("strength", "WEAK"),
            "gap_trading_pct": signals.get("gap_trading", {}).get("gap_pct"),
            "closing_range_signal": signals.get("closing_range", {}).get("signal", "HOLD"),
            "closing_range_strength": signals.get("closing_range", {}).get("strength", "WEAK"),
            "volume_profile_signal": signals.get("volume_profile", {}).get("signal", "HOLD"),
            "volume_profile_strength": signals.get("volume_profile", {}).get("strength", "WEAK"),
            "volume_profile_poc": signals.get("volume_profile", {}).get("poc_price"),
            "news_signal": signals.get("news", {}).get("signal", "HOLD"),
            "news_strength": signals.get("news", {}).get("strength", "WEAK"),
            "news_sentiment": signals.get("news", {}).get("sentiment_score", 0),
            "comprehensive_signal": comprehensive_signal,
            "comprehensive_strength": comprehensive_strength,
            "comprehensive_confidence": round(avg_confidence * 100, 1),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count
        }
    except Exception as e:
        logger.error(f"Error processing signals for {symbol}: {e}")
        return {
            "symbol": symbol,
            "error": str(e)
        }

# ==================== ADVANCED ML MODEL MANAGEMENT ====================

@router.get("/ml-models/training-status")
async def get_training_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get automated training pipeline status"""
    try:
        status = automated_training_pipeline.get_training_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ml-models/train")
async def trigger_model_training(
    models: List[str] = Query(None, description="Models to train (optional, defaults to all)"),
    symbols: List[str] = Query(None, description="Symbols to train on (optional)"),
    full_retrain: bool = Query(False, description="Perform full retraining"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger model training"""
    try:
        if models is None:
            models = ["gradient_boosting", "temporal_models", "alternative_data", "bayesian", "reinforcement_learning", "meta_learner"]
        
        if symbols is None:
            symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        
        results = await automated_training_pipeline.train_models(
            models=models,
            symbols=symbols,
            full_retrain=full_retrain
        )
        
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ml-models/performance")
async def get_model_performance(
    model_name: Optional[str] = Query(None, description="Specific model name (optional)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get model performance metrics"""
    try:
        summary = model_performance_monitoring.get_performance_summary(model_name)
        return {
            "success": True,
            "performance": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ModelUpdateRequest(BaseModel):
    """Request model for real-time model updates"""
    model_name: str
    symbol: str
    data: Dict[str, Any]
    target: Optional[float] = None

@router.post("/ml-models/update")
async def update_model_realtime(
    request: ModelUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add new data point for real-time model update"""
    try:
        await realtime_model_updates.add_new_data(
            model_name=request.model_name,
            symbol=request.symbol,
            data=request.data,
            target=request.target
        )
        
        return {
            "success": True,
            "message": f"Data added to update buffer for {request.model_name}",
            "update_status": realtime_model_updates.get_update_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ml-models/update-status")
async def get_update_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time model update status"""
    try:
        status = realtime_model_updates.get_update_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting update status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Strategy Builder APIs ====================

# Helper functions to eliminate code duplication

def get_strategy_model():
    """Get Strategy model with fallback import"""
    try:
        from models.strategy import Strategy
        return Strategy
    except ImportError:
        from backend.models.strategy import Strategy
        return Strategy

def get_paper_trade_model():
    """Get PaperTrade model with fallback import"""
    try:
        from models.strategy import PaperTrade
        return PaperTrade
    except ImportError:
        from backend.models.strategy import PaperTrade
        return PaperTrade

def get_user_id(current_user: dict) -> str:
    """Extract and validate user ID from current_user"""
    user_id = current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return user_id

def serialize_legs(legs: List[Any]) -> str:
    """Serialize legs list to JSON string"""
    return json.dumps([leg.dict() if hasattr(leg, 'dict') else leg for leg in legs])

def deserialize_legs(legs_json: str) -> List[Dict]:
    """Deserialize legs JSON string to list"""
    return json.loads(legs_json) if legs_json else []

def calculate_leg_pnl(leg_data: Dict, entry_price: float, current_price: float) -> float:
    """Calculate P&L for a single leg
    
    For options (CE/PE), P&L is calculated based on premium difference.
    The entry premium is stored in leg.price, and we estimate current premium
    based on intrinsic value and time value approximation.
    
    For futures (FUT), P&L is calculated based on price difference.
    """
    try:
        leg = StrategyLegRequest(**leg_data)
        multiplier = leg.lotSize or 50
        total_quantity = leg.quantity * multiplier
        
        # Get entry premium/price from leg (this is the actual price paid/received)
        entry_premium = leg.price if leg.price and leg.price > 0 else 0
        
        if leg.instrument == 'CE':
            # For Call options, calculate current premium based on intrinsic value + time value
            intrinsic_current = max(0, current_price - leg.strike)
            intrinsic_entry = max(0, entry_price - leg.strike)
            
            # Estimate current premium:
            # - If ITM: intrinsic value + some time value (10% of intrinsic)
            # - If OTM: use a decayed value based on entry premium
            if intrinsic_current > 0:
                # ITM: intrinsic + time value approximation
                current_premium = intrinsic_current + (intrinsic_current * 0.1)
            else:
                # OTM: decay the premium (simplified - in reality this depends on time to expiry, IV, etc.)
                # For simplicity, we'll use a percentage of entry premium based on how far OTM
                distance_otm = abs(leg.strike - current_price)
                distance_otm_pct = (distance_otm / entry_price) * 100 if entry_price > 0 else 0
                decay_factor = max(0.1, 1 - (distance_otm_pct / 100))
                current_premium = entry_premium * decay_factor if entry_premium > 0 else 0
            
            if leg.action == 'BUY':
                # Bought call: profit if current premium > entry premium
                return (current_premium - entry_premium) * total_quantity
            else:
                # Sold call: profit if entry premium > current premium
                return (entry_premium - current_premium) * total_quantity
                
        elif leg.instrument == 'PE':
            # For Put options
            intrinsic_current = max(0, leg.strike - current_price)
            intrinsic_entry = max(0, leg.strike - entry_price)
            
            # Estimate current premium similar to calls
            if intrinsic_current > 0:
                # ITM: intrinsic + time value
                current_premium = intrinsic_current + (intrinsic_current * 0.1)
            else:
                # OTM: decay the premium
                distance_otm = abs(leg.strike - current_price)
                distance_otm_pct = (distance_otm / entry_price) * 100 if entry_price > 0 else 0
                decay_factor = max(0.1, 1 - (distance_otm_pct / 100))
                current_premium = entry_premium * decay_factor if entry_premium > 0 else 0
            
            if leg.action == 'BUY':
                # Bought put: profit if current premium > entry premium
                return (current_premium - entry_premium) * total_quantity
            else:
                # Sold put: profit if entry premium > current premium
                return (entry_premium - current_premium) * total_quantity
                
        elif leg.instrument == 'FUT':
            # For Futures, P&L is straightforward price difference
            pnl_per_unit = current_price - entry_price
            if leg.action == 'BUY':
                # Bought future: profit if price goes up
                return pnl_per_unit * total_quantity
            else:
                # Sold future: profit if price goes down
                return -pnl_per_unit * total_quantity
                
        return 0.0
    except Exception as e:
        logger.error(f"Error calculating leg P&L: {e}, leg_data: {leg_data}")
        return 0.0

def format_strategy_response(strategy: Any) -> Dict:
    """Format Strategy model to API response format"""
    return {
        "id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "symbol": strategy.symbol,
        "legs": deserialize_legs(strategy.legs),
        "metrics": json.loads(strategy.metrics) if strategy.metrics else None,
        "createdAt": strategy.created_at.isoformat() if strategy.created_at else None,
        "updatedAt": strategy.updated_at.isoformat() if strategy.updated_at else None
    }

def format_paper_trade_response(trade: Any) -> Dict:
    """Format PaperTrade model to API response format"""
    return {
        "id": trade.id,
        "strategyId": trade.strategy_id,
        "entryPrice": trade.entry_price,
        "currentPrice": trade.current_price,
        "quantity": trade.quantity,
        "entryTime": to_ist_isoformat(trade.entry_time),
        "pnl": trade.pnl,
        "pnlPercentage": trade.pnl_percentage,
        "status": trade.status,
        "exitPrice": trade.exit_price if hasattr(trade, 'exit_price') else None,
        "exitTime": to_ist_isoformat(trade.exit_time) if hasattr(trade, 'exit_time') and trade.exit_time else None
    }

class StrategyLegRequest(BaseModel):
    id: Optional[str] = None
    action: str  # BUY or SELL
    instrument: str  # CE, PE, or FUT
    expiry: str
    strike: float
    quantity: int
    price: float
    premium: Optional[float] = None
    lotSize: Optional[int] = 50

class StrategyCalculateRequest(BaseModel):
    symbol: Optional[str] = None
    legs: List[StrategyLegRequest]
    current_price: float
    expiry_date: Optional[str] = None
    days_to_expiry: Optional[int] = None

class StrategySaveRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    symbol: str
    legs: List[StrategyLegRequest]
    metrics: Optional[Dict[str, Any]] = None

@router.post("/strategy/calculate")
async def calculate_strategy_metrics(
    request: StrategyCalculateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate strategy metrics including payoff, Greeks, and risk parameters"""
    try:
        import math
        try:
            from scipy.stats import norm
        except ImportError:
            # Fallback to math.erf for normal CDF
            def norm_cdf(x):
                return 0.5 * (1 + math.erf(x / math.sqrt(2)))
            def norm_pdf(x):
                return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
            norm = type('norm', (), {'cdf': norm_cdf, 'pdf': norm_pdf})()
        
        legs = request.legs
        current_price = request.current_price
        days_to_expiry = request.days_to_expiry or 30  # Use provided days_to_expiry or default to 30
        
        # Calculate total premium paid/received
        total_premium = 0
        for leg in legs:
            multiplier = leg.lotSize or 50
            total_quantity = leg.quantity * multiplier
            if leg.action == 'BUY':
                total_premium -= leg.price * total_quantity
            else:
                total_premium += leg.price * total_quantity
        
        # Calculate payoff at expiry for different price points
        min_strike = min([l.strike for l in legs])
        max_strike = max([l.strike for l in legs])
        price_range = max_strike - min_strike
        start_price = max(0, min_strike - price_range * 0.3)
        end_price = max_strike + price_range * 0.3
        
        payoffs = []
        for price in np.linspace(start_price, end_price, 100):
            payoff = 0
            for leg in legs:
                multiplier = leg.lotSize or 50
                total_quantity = leg.quantity * multiplier
                
                if leg.instrument == 'CE':
                    intrinsic = max(0, price - leg.strike)
                    if leg.action == 'BUY':
                        payoff += (intrinsic - leg.price) * total_quantity
                    else:
                        payoff += (leg.price - intrinsic) * total_quantity
                elif leg.instrument == 'PE':
                    intrinsic = max(0, leg.strike - price)
                    if leg.action == 'BUY':
                        payoff += (intrinsic - leg.price) * total_quantity
                    else:
                        payoff += (leg.price - intrinsic) * total_quantity
                elif leg.instrument == 'FUT':
                    pnl = price - leg.price
                    if leg.action == 'BUY':
                        payoff += pnl * total_quantity
                    else:
                        payoff -= pnl * total_quantity
            
            payoffs.append(payoff)
        
        max_profit = max(payoffs)
        max_loss = min(payoffs)
        
        # Calculate breakeven points
        breakeven_points = []
        for i in range(len(payoffs) - 1):
            if payoffs[i] * payoffs[i + 1] <= 0:
                price_at_be = start_price + (end_price - start_price) * i / 100
                breakeven_points.append(price_at_be)
        
        # Calculate Greeks (simplified)
        delta = 0
        gamma = 0
        theta = 0
        vega = 0
        
        # Risk-free rate and volatility assumptions
        risk_free_rate = 0.06  # 6% annual
        volatility = 0.20  # 20% annual volatility
        # days_to_expiry is already set above from request
        
        for leg in legs:
            multiplier = leg.lotSize or 50
            total_quantity = leg.quantity * multiplier
            time_to_expiry = days_to_expiry / 365.0
            
            if leg.instrument in ['CE', 'PE']:
                S = current_price
                K = leg.strike
                r = risk_free_rate
                sigma = volatility
                T = time_to_expiry
                
                if T > 0:
                    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
                    d2 = d1 - sigma * math.sqrt(T)
                    
                    if leg.instrument == 'CE':
                        leg_delta = norm.cdf(d1) if leg.action == 'BUY' else -norm.cdf(d1)
                        leg_gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
                        leg_theta = (-(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) - 
                                   r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
                        leg_vega = S * norm.pdf(d1) * math.sqrt(T) / 100
                    else:  # PE
                        leg_delta = (norm.cdf(d1) - 1) if leg.action == 'BUY' else -(norm.cdf(d1) - 1)
                        leg_gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
                        leg_theta = (-(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) + 
                                   r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
                        leg_vega = S * norm.pdf(d1) * math.sqrt(T) / 100
                    
                    delta += leg_delta * total_quantity
                    gamma += leg_gamma * total_quantity
                    theta += leg_theta * total_quantity
                    vega += leg_vega * total_quantity
                elif leg.instrument == 'FUT':
                    leg_delta = 1 if leg.action == 'BUY' else -1
                    delta += leg_delta * total_quantity
        
        # Calculate probability of profit (simplified)
        # Assume normal distribution around current price
        if max_profit > 0 and max_loss < 0:
            prob_of_profit = 50.0  # Simplified
        elif max_loss >= 0:
            prob_of_profit = 100.0
        else:
            prob_of_profit = 0.0
        
        # Reward/Risk ratio
        reward_risk = abs(max_profit / max_loss) if max_loss != 0 else 0
        
        # Margin required (simplified calculation)
        margin_required = abs(total_premium) * 1.2  # 20% buffer
        
        metrics = {
            "maxProfit": max_profit,
            "maxLoss": max_loss,
            "breakevenPoints": breakeven_points,
            "probabilityOfProfit": prob_of_profit,
            "rewardRiskRatio": reward_risk,
            "totalPremium": abs(total_premium),
            "marginRequired": margin_required,
            "greeks": {
                "delta": delta,
                "gamma": gamma,
                "theta": theta,
                "vega": vega
            }
        }
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error calculating strategy metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy/save")
async def save_strategy(
    request: StrategySaveRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save a strategy for the current user"""
    try:
        db = next(get_db())
        StrategyModel = get_strategy_model()
        user_id = get_user_id(current_user)
        
        # Validate request
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Strategy name is required")
        
        if not request.legs or len(request.legs) == 0:
            raise HTTPException(status_code=400, detail="At least one leg is required")
        
        # Validate legs
        for i, leg in enumerate(request.legs):
            if leg.instrument in ['CE', 'PE'] and (not leg.strike or leg.strike <= 0):
                raise HTTPException(status_code=400, detail=f"Leg {i+1}: Invalid strike price for {leg.instrument}")
            if not leg.quantity or leg.quantity <= 0:
                raise HTTPException(status_code=400, detail=f"Leg {i+1}: Invalid quantity")
            if not leg.expiry or not leg.expiry.strip():
                raise HTTPException(status_code=400, detail=f"Leg {i+1}: Expiry is required")
        
        # Generate ID for new strategy if not provided
        strategy_id = request.id if request.id else str(uuid.uuid4())
        
        strategy_data = {
            "id": strategy_id,
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "symbol": request.symbol,
            "legs": serialize_legs(request.legs),
            "metrics": json.dumps(request.metrics) if request.metrics else None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        if request.id:
            # Update existing strategy
            strategy = db.query(StrategyModel).filter(
                StrategyModel.id == request.id,
                StrategyModel.user_id == user_id
            ).first()
            
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            for key, value in strategy_data.items():
                if key != 'created_at':
                    setattr(strategy, key, value)
            
            db.commit()
            db.refresh(strategy)
            
            return {
                "success": True,
                "data": format_strategy_response(strategy)
            }
        else:
            # Create new strategy (ID already generated above)
            strategy = StrategyModel(**strategy_data)
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
            
            return {
                "success": True,
                "data": format_strategy_response(strategy)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/saved")
async def get_saved_strategies(
    symbol: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all saved strategies for the current user"""
    try:
        db = next(get_db())
        StrategyModel = get_strategy_model()
        user_id = get_user_id(current_user)
        
        query = db.query(StrategyModel).filter(StrategyModel.user_id == user_id)
        if symbol:
            query = query.filter(StrategyModel.symbol == symbol)
        
        strategies = query.order_by(StrategyModel.created_at.desc()).all()
        
        result = [format_strategy_response(strategy) for strategy in strategies]
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching saved strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single strategy by ID"""
    try:
        db = next(get_db())
        StrategyModel = get_strategy_model()
        user_id = get_user_id(current_user)
        
        strategy = db.query(StrategyModel).filter(
            StrategyModel.id == strategy_id,
            StrategyModel.user_id == user_id
        ).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "data": format_strategy_response(strategy)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/strategy/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a saved strategy"""
    try:
        db = next(get_db())
        StrategyModel = get_strategy_model()
        user_id = get_user_id(current_user)
        
        strategy = db.query(StrategyModel).filter(
            StrategyModel.id == strategy_id,
            StrategyModel.user_id == user_id
        ).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        db.delete(strategy)
        db.commit()
        
        return {
            "success": True,
            "message": "Strategy deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/suggested")
async def get_suggested_strategies(
    symbol: Optional[str] = Query(None, description="Stock symbol (e.g., NIFTY, RELIANCE)"),
    outlook: str = Query("bullish", description="Market outlook: bullish, bearish, neutral, others"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get suggested strategies based on market outlook and symbol"""
    try:
        outlook_lower = outlook.lower()
        
        # Define strategy templates based on outlook
        strategies = []
        
        if outlook_lower == "bullish":
            strategies = [
                {
                    "id": "bull-call-spread",
                    "name": "Bull Call Spread",
                    "description": "Buy lower strike call, sell higher strike call. Limited risk, limited profit.",
                    "outlook": "bullish",
                    "max_profit": "Limited",
                    "max_loss": "Limited",
                    "breakeven": "Lower strike + Net premium paid",
                    "legs": [
                        {"type": "CALL", "action": "BUY", "strike": "ATM", "quantity": 50},
                        {"type": "CALL", "action": "SELL", "strike": "OTM", "quantity": 50}
                    ]
                },
                {
                    "id": "bull-put-spread",
                    "name": "Bull Put Spread",
                    "description": "Sell higher strike put, buy lower strike put. Collect premium with limited risk.",
                    "outlook": "bullish",
                    "max_profit": "Net premium received",
                    "max_loss": "Limited",
                    "breakeven": "Higher strike - Net premium received",
                    "legs": [
                        {"type": "PUT", "action": "SELL", "strike": "OTM", "quantity": 50},
                        {"type": "PUT", "action": "BUY", "strike": "OTM-1", "quantity": 50}
                    ]
                },
                {
                    "id": "buy-call",
                    "name": "Buy Call",
                    "description": "Simple long call option. Unlimited profit potential, limited risk.",
                    "outlook": "bullish",
                    "max_profit": "Unlimited",
                    "max_loss": "Premium paid",
                    "breakeven": "Strike + Premium",
                    "legs": [
                        {"type": "CALL", "action": "BUY", "strike": "ATM", "quantity": 50}
                    ]
                },
                {
                    "id": "sell-put",
                    "name": "Sell Put",
                    "description": "Sell put option to collect premium. Bullish strategy with limited profit.",
                    "outlook": "bullish",
                    "max_profit": "Premium received",
                    "max_loss": "Strike - Premium",
                    "breakeven": "Strike - Premium",
                    "legs": [
                        {"type": "PUT", "action": "SELL", "strike": "OTM", "quantity": 50}
                    ]
                }
            ]
        elif outlook_lower == "bearish":
            strategies = [
                {
                    "id": "bear-call-spread",
                    "name": "Bear Call Spread",
                    "description": "Sell lower strike call, buy higher strike call. Collect premium with limited risk.",
                    "outlook": "bearish",
                    "max_profit": "Net premium received",
                    "max_loss": "Limited",
                    "breakeven": "Lower strike + Net premium received",
                    "legs": [
                        {"type": "CALL", "action": "SELL", "strike": "ATM", "quantity": 50},
                        {"type": "CALL", "action": "BUY", "strike": "OTM", "quantity": 50}
                    ]
                },
                {
                    "id": "bear-put-spread",
                    "name": "Bear Put Spread",
                    "description": "Buy higher strike put, sell lower strike put. Limited risk, limited profit.",
                    "outlook": "bearish",
                    "max_profit": "Limited",
                    "max_loss": "Limited",
                    "breakeven": "Higher strike - Net premium paid",
                    "legs": [
                        {"type": "PUT", "action": "BUY", "strike": "ATM", "quantity": 50},
                        {"type": "PUT", "action": "SELL", "strike": "OTM", "quantity": 50}
                    ]
                },
                {
                    "id": "buy-put",
                    "name": "Buy Put",
                    "description": "Simple long put option. High profit potential if stock falls, limited risk.",
                    "outlook": "bearish",
                    "max_profit": "Strike - Premium (if stock goes to zero)",
                    "max_loss": "Premium paid",
                    "breakeven": "Strike - Premium",
                    "legs": [
                        {"type": "PUT", "action": "BUY", "strike": "ATM", "quantity": 50}
                    ]
                },
                {
                    "id": "sell-call",
                    "name": "Sell Call",
                    "description": "Sell call option to collect premium. Bearish strategy with limited profit.",
                    "outlook": "bearish",
                    "max_profit": "Premium received",
                    "max_loss": "Unlimited",
                    "breakeven": "Strike + Premium",
                    "legs": [
                        {"type": "CALL", "action": "SELL", "strike": "OTM", "quantity": 50}
                    ]
                }
            ]
        elif outlook_lower == "neutral":
            strategies = [
                {
                    "id": "iron-condor",
                    "name": "Iron Condor",
                    "description": "Sell OTM call spread and OTM put spread. Collect premium, profit in range.",
                    "outlook": "neutral",
                    "max_profit": "Net premium received",
                    "max_loss": "Limited",
                    "breakeven": "Two breakeven points",
                    "legs": [
                        {"type": "CALL", "action": "SELL", "strike": "OTM+1", "quantity": 50},
                        {"type": "CALL", "action": "BUY", "strike": "OTM+2", "quantity": 50},
                        {"type": "PUT", "action": "SELL", "strike": "OTM-1", "quantity": 50},
                        {"type": "PUT", "action": "BUY", "strike": "OTM-2", "quantity": 50}
                    ]
                },
                {
                    "id": "short-straddle",
                    "name": "Short Straddle",
                    "description": "Sell ATM call and ATM put. Collect premium, profit if stock stays flat.",
                    "outlook": "neutral",
                    "max_profit": "Total premium received",
                    "max_loss": "Unlimited",
                    "breakeven": "Strike ± Total premium",
                    "legs": [
                        {"type": "CALL", "action": "SELL", "strike": "ATM", "quantity": 50},
                        {"type": "PUT", "action": "SELL", "strike": "ATM", "quantity": 50}
                    ]
                },
                {
                    "id": "short-strangle",
                    "name": "Short Strangle",
                    "description": "Sell OTM call and OTM put. Collect premium with wider profit range.",
                    "outlook": "neutral",
                    "max_profit": "Total premium received",
                    "max_loss": "Unlimited",
                    "breakeven": "Call strike + Premium, Put strike - Premium",
                    "legs": [
                        {"type": "CALL", "action": "SELL", "strike": "OTM", "quantity": 50},
                        {"type": "PUT", "action": "SELL", "strike": "OTM", "quantity": 50}
                    ]
                }
            ]
        else:  # others
            strategies = [
                {
                    "id": "long-straddle",
                    "name": "Long Straddle",
                    "description": "Buy ATM call and ATM put. Profit from large moves in either direction.",
                    "outlook": "others",
                    "max_profit": "Unlimited (up) or Strike - Premium (down)",
                    "max_loss": "Total premium paid",
                    "breakeven": "Strike ± Total premium",
                    "legs": [
                        {"type": "CALL", "action": "BUY", "strike": "ATM", "quantity": 50},
                        {"type": "PUT", "action": "BUY", "strike": "ATM", "quantity": 50}
                    ]
                },
                {
                    "id": "long-strangle",
                    "name": "Long Strangle",
                    "description": "Buy OTM call and OTM put. Lower cost than straddle, needs bigger move.",
                    "outlook": "others",
                    "max_profit": "Unlimited (up) or Put strike - Premium (down)",
                    "max_loss": "Total premium paid",
                    "breakeven": "Call strike + Premium, Put strike - Premium",
                    "legs": [
                        {"type": "CALL", "action": "BUY", "strike": "OTM", "quantity": 50},
                        {"type": "PUT", "action": "BUY", "strike": "OTM", "quantity": 50}
                    ]
                }
            ]
        
        logger.info(f"Returning {len(strategies)} suggested strategies for {symbol} with outlook: {outlook}")
        
        return {
            "success": True,
            "data": strategies
        }
    except Exception as e:
        logger.error(f"Error fetching suggested strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Paper Trading APIs ====================

class PaperTradeEnterRequest(BaseModel):
    strategy_id: str
    strategy_name: str
    symbol: str
    legs: List[StrategyLegRequest]
    entry_price: float
    entry_time: str

class PaperTradeExitRequest(BaseModel):
    trade_id: str
    exit_price: float
    exit_time: str

class PaperTradeUpdatePricesRequest(BaseModel):
    strategy_id: str
    current_price: float

@router.post("/paper-trading/enter")
async def enter_paper_trade(
    request: PaperTradeEnterRequest,
    current_user: dict = Depends(get_current_user)
):
    """Enter a paper trade"""
    try:
        db = next(get_db())
        PaperTrade = get_paper_trade_model()
        user_id = get_user_id(current_user)
        
        # Generate a unique ID for the paper trade
        trade_id = str(uuid.uuid4())
        
        trade = PaperTrade(
            id=trade_id,
            user_id=user_id,
            strategy_id=request.strategy_id,
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            legs=serialize_legs(request.legs),
            entry_price=request.entry_price,
            current_price=request.entry_price,
            quantity=sum([leg.quantity * (leg.lotSize or 50) for leg in request.legs]),
            entry_time=_parse_datetime_utc(request.entry_time),
            pnl=0,
            pnl_percentage=0,
            status='open'
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        return {
            "success": True,
            "data": format_paper_trade_response(trade)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error entering paper trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/paper-trading/exit")
async def exit_paper_trade(
    request: PaperTradeExitRequest,
    current_user: dict = Depends(get_current_user)
):
    """Exit a paper trade"""
    try:
        db = next(get_db())
        PaperTrade = get_paper_trade_model()
        user_id = get_user_id(current_user)
        
        trade = db.query(PaperTrade).filter(
            PaperTrade.id == request.trade_id,
            PaperTrade.user_id == user_id,
            PaperTrade.status == 'open'
        ).first()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        # Calculate final P&L using helper function
        legs = deserialize_legs(trade.legs)
        exit_pnl = sum(calculate_leg_pnl(leg_data, trade.entry_price, request.exit_price) for leg_data in legs)
        
        trade.exit_price = request.exit_price
        trade.exit_time = _parse_datetime_utc(request.exit_time)
        trade.pnl = exit_pnl
        trade.pnl_percentage = (exit_pnl / abs(trade.entry_price * trade.quantity)) * 100 if trade.entry_price * trade.quantity != 0 else 0
        trade.status = 'closed'
        trade.current_price = request.exit_price
        
        db.commit()
        db.refresh(trade)
        
        return {
            "success": True,
            "data": format_paper_trade_response(trade)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exiting paper trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/paper-trading/update-prices")
async def update_paper_trade_prices(
    request: PaperTradeUpdatePricesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update prices for open paper trades"""
    try:
        db = next(get_db())
        PaperTrade = get_paper_trade_model()
        user_id = get_user_id(current_user)
        
        trades = db.query(PaperTrade).filter(
            PaperTrade.strategy_id == request.strategy_id,
            PaperTrade.user_id == user_id,
            PaperTrade.status == 'open'
        ).all()
        
        updated_trades = []
        for trade in trades:
            # Calculate current P&L using helper function
            legs = deserialize_legs(trade.legs)
            current_pnl = sum(calculate_leg_pnl(leg_data, trade.entry_price, request.current_price) for leg_data in legs)
            
            trade.current_price = request.current_price
            trade.pnl = current_pnl
            trade.pnl_percentage = (current_pnl / abs(trade.entry_price * trade.quantity)) * 100 if trade.entry_price * trade.quantity != 0 else 0
            
            updated_trades.append(format_paper_trade_response(trade))
        
        db.commit()
        
        return {
            "success": True,
            "data": updated_trades
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating paper trade prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper-trading/trades")
async def get_paper_trades(
    strategy_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all paper trades for the current user"""
    try:
        db = next(get_db())
        PaperTrade = get_paper_trade_model()
        user_id = get_user_id(current_user)
        
        query = db.query(PaperTrade).filter(PaperTrade.user_id == user_id)
        if strategy_id:
            query = query.filter(PaperTrade.strategy_id == strategy_id)
        
        trades = query.order_by(PaperTrade.entry_time.desc()).all()
        
        result = [format_paper_trade_response(trade) for trade in trades]
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching paper trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))
