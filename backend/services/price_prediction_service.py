"""
Price Prediction Service
Generates price predictions for 1 month, 3 months, and 6 months
based on comprehensive analysis of all available features:
- Technical indicators
- Market factors (FII/DII, news, orderbook)
- Chart patterns
- Market structure
- Support/Resistance levels
- Sentiment analysis
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# Import specialized predictors
try:
    from services.short_term_predictor import short_term_predictor
    SHORT_TERM_AVAILABLE = True
except ImportError:
    SHORT_TERM_AVAILABLE = False
    logger.warning("ShortTermPricePredictor not available - 1W predictions will use factor-based method")

try:
    from services.medium_term_predictor import medium_term_predictor
    MEDIUM_TERM_AVAILABLE = True
except ImportError:
    MEDIUM_TERM_AVAILABLE = False
    logger.warning("MediumTermPricePredictor not available - 1M predictions will use factor-based method only")

class PricePredictionService:
    """Service to generate price predictions based on comprehensive analysis"""
    
    def __init__(self):
        self.prediction_horizons = {
            "1W": 5,    # 5 trading days = 1 week
            "1M": 21,   # ~21 trading days in 1 month
            "2M": 42,   # ~42 trading days in 2 months
            "3M": 63,   # ~63 trading days in 3 months
            "6M": 126,  # ~126 trading days in 6 months
            "1Y": 252,  # ~252 trading days in 1 year
            "2Y": 504,  # ~504 trading days in 2 years
        }
    
    async def generate_price_predictions(
        self,
        symbol: str,
        current_price: float,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate price predictions for 1W, 1M, 2M, 3M, 6M, 1Y, and 2Y based on all analysis features

        Args:
            symbol: Stock symbol
            current_price: Current stock price
            analysis_data: Comprehensive analysis data including:
                - technical_indicators
                - market_factors
                - chart_patterns
                - market_structure
                - support_resistance
                - sentiment
                - trendline_analysis
                - swing_points
                - supply_demand
        
        Returns:
            Dictionary with predictions for each timeframe
        """
        try:
            logger.info(f"📈 Generating price predictions for {symbol} at ₹{current_price:.2f}")
            
            predictions = {
                "symbol": symbol,
                "current_price": current_price,
                "prediction_date": datetime.now().isoformat(),
                "timeframes": {}
            }
            
            # Calculate base factors
            base_factors = self._calculate_base_factors(current_price, analysis_data)
            
            # Get historical data for specialized predictors (if needed)
            historical_data = None
            if SHORT_TERM_AVAILABLE or MEDIUM_TERM_AVAILABLE:
                try:
                    from services.data_fetcher import fetch_historical_data
                    candles = await fetch_historical_data(symbol, "1d", days=90)
                    if candles and len(candles) > 0:
                        historical_data = pd.DataFrame(candles)
                        if 'time' in historical_data.columns:
                            historical_data['time'] = pd.to_datetime(historical_data['time'], unit='s', errors='coerce')
                except Exception as e:
                    logger.debug(f"Could not fetch historical data for specialized predictors: {e}")
            
            # Track predictions for accuracy monitoring (optional, requires DB)
            try:
                from services.prediction_tracking_service import prediction_tracking_service
                from core.database_unified import get_db
                TRACKING_AVAILABLE = True
            except ImportError:
                TRACKING_AVAILABLE = False
            
            # Generate predictions for each timeframe
            for timeframe, days in self.prediction_horizons.items():
                # Use specialized predictors for 1W and 1M
                if timeframe == "1W" and SHORT_TERM_AVAILABLE:
                    try:
                        prediction = await short_term_predictor.predict_1week(
                            symbol=symbol,
                            historical_data=historical_data,
                            current_price=current_price
                        )
                        predictions["timeframes"][timeframe] = prediction
                        continue
                    except Exception as e:
                        logger.warning(f"Short-term predictor failed for {symbol}, falling back to factor-based: {e}")
                        # Fall through to factor-based prediction
                
                elif timeframe == "1M" and MEDIUM_TERM_AVAILABLE:
                    try:
                        prediction = await medium_term_predictor.predict_1month(
                            symbol=symbol,
                            historical_data=historical_data,
                            current_price=current_price,
                            technical_indicators=analysis_data.get("technical_indicators"),
                            market_factors=analysis_data.get("market_factors")
                        )
                        predictions["timeframes"][timeframe] = prediction
                        continue
                    except Exception as e:
                        logger.warning(f"Medium-term predictor failed for {symbol}, falling back to factor-based: {e}")
                        # Fall through to factor-based prediction
                
                # Default factor-based prediction for other timeframes or fallback
                prediction = self._predict_for_timeframe(
                    timeframe=timeframe,
                    days=days,
                    current_price=current_price,
                    base_factors=base_factors,
                    analysis_data=analysis_data
                )
                predictions["timeframes"][timeframe] = prediction
            
            # Integrate chart image analysis if available
            chart_images = analysis_data.get("chart_images_analysis", {})
            if chart_images and chart_images.get("has_data"):
                predictions = self._integrate_chart_image_insights(predictions, chart_images, current_price)
            
            # Calculate overall confidence
            predictions["overall_confidence"] = self._calculate_overall_confidence(predictions)
            
            # Generate summary
            predictions["summary"] = self._generate_prediction_summary(predictions)
            
            # Record predictions for tracking (if available and enabled)
            if TRACKING_AVAILABLE and predictions.get("timeframes"):
                db = None
                try:
                    db = next(get_db())
                    for timeframe, pred_data in predictions["timeframes"].items():
                        if isinstance(pred_data, dict) and "predicted_price" in pred_data:
                            await prediction_tracking_service.record_prediction(
                                db=db,
                                symbol=symbol,
                                timeframe=timeframe,
                                predicted_price=pred_data.get("predicted_price", current_price),
                                current_price=current_price,
                                predicted_change_percent=pred_data.get("potential_change_percent", 0),
                                confidence=pred_data.get("confidence", 0),
                                price_range=pred_data.get("price_range", {}),
                                model_type=pred_data.get("model_type", "factor_based"),
                                model_contributions=pred_data.get("model_contributions")
                            )
                except Exception as e:
                    logger.debug(f"Could not record prediction for tracking: {e}")
                finally:
                    if db is not None:
                        try:
                            db.close()
                        except Exception:
                            pass  # Ignore errors during cleanup

            # Log a compact summary for all available horizons (defensive: logging must not break main flow)
            try:
                tf_summaries = []
                for tf_key, tf_data in predictions.get("timeframes", {}).items():
                    price_val = tf_data.get("predicted_price")
                    if isinstance(price_val, (int, float)):
                        tf_summaries.append(f"{tf_key}={price_val:.2f}")
                if tf_summaries:
                    logger.info(f"✅ Generated predictions for {symbol}: " + ", ".join(tf_summaries))
            except Exception:
                pass
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating price predictions for {symbol}: {e}")
            return {
                "symbol": symbol,
                "current_price": current_price,
                "error": str(e),
                "timeframes": {}
            }
    
    def _calculate_base_factors(
        self,
        current_price: float,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate base factors from all analysis data"""
        factors = {
            "momentum_score": 0.0,
            "trend_strength": 0.0,
            "market_sentiment": 0.0,
            "institutional_flow": 0.0,
            "pattern_target": 0.0,
            "support_resistance_bias": 0.0,
            "volatility": 0.0
        }
        
        # 1. Technical Indicators Momentum
        technical = analysis_data.get("technical_indicators", {})
        if technical:
            rsi = technical.get("rsi", 50)
            macd_signal = technical.get("macd_signal", "neutral")
            momentum_score = 0.0
            
            # RSI contribution (-50 to +50, normalized to -1 to +1)
            if rsi > 70:
                momentum_score -= 0.3  # Overbought
            elif rsi < 30:
                momentum_score += 0.3  # Oversold
            else:
                momentum_score += (rsi - 50) / 50 * 0.5
            
            # MACD contribution
            if macd_signal == "bullish":
                momentum_score += 0.2
            elif macd_signal == "bearish":
                momentum_score -= 0.2
            
            factors["momentum_score"] = np.clip(momentum_score, -1, 1)
        
        # 2. Trend Strength
        trendline = analysis_data.get("trendline_analysis", {})
        market_structure = analysis_data.get("market_structure_analysis", {})
        
        trend_strength = 0.0
        if trendline.get("current_trend") == "uptrend":
            trend_strength += 0.3
        elif trendline.get("current_trend") == "downtrend":
            trend_strength -= 0.3
        
        if market_structure.get("current_phase") == "bullish":
            trend_strength += 0.2
        elif market_structure.get("current_phase") == "bearish":
            trend_strength -= 0.2
        
        factors["trend_strength"] = np.clip(trend_strength, -1, 1)
        
        # 3. Market Sentiment
        market_factors = analysis_data.get("market_factors", {})
        sentiment = analysis_data.get("market_sentiment", {})
        
        sentiment_score = 0.0
        
        # News sentiment
        if market_factors:
            news = market_factors.get("news", {})
            if news.get("sentiment") == "positive":
                sentiment_score += 0.2
            elif news.get("sentiment") == "negative":
                sentiment_score -= 0.2
        
        # Overall market sentiment
        if sentiment:
            overall_sentiment = sentiment.get("overall_sentiment", "neutral")
            if overall_sentiment == "bullish":
                sentiment_score += 0.3
            elif overall_sentiment == "bearish":
                sentiment_score -= 0.3
        
        factors["market_sentiment"] = np.clip(sentiment_score, -1, 1)
        
        # 4. Institutional Flow
        if market_factors:
            fii_dii = market_factors.get("fii_dii_flows", {})
            impact_analysis = market_factors.get("impact_analysis", {})
            
            institutional_score = 0.0
            
            # FII/DII impact
            fii_net = fii_dii.get("fii_net_investment", 0)
            dii_net = fii_dii.get("dii_net_investment", 0)
            
            # Normalize FII/DII flows (assuming max ±5000 Cr)
            if abs(fii_net) > 0:
                institutional_score += np.clip(fii_net / 5000, -0.5, 0.5)
            if abs(dii_net) > 0:
                institutional_score += np.clip(dii_net / 5000, -0.3, 0.3)
            
            # Impact analysis contribution
            impact_score = impact_analysis.get("impact_score", 0)
            institutional_score += np.clip(impact_score / 10, -0.2, 0.2)
            
            factors["institutional_flow"] = np.clip(institutional_score, -1, 1)
        
        # 5. Pattern Target
        chart_patterns = analysis_data.get("chart_patterns", {})
        pattern_target = 0.0
        
        if chart_patterns and chart_patterns.get("has_patterns"):
            primary = chart_patterns.get("primary_pattern", {})
            if primary:
                target_price = primary.get("target_price", 0)
                if target_price > 0:
                    # Calculate expected return from pattern
                    expected_return = (target_price - current_price) / current_price
                    pattern_target = np.clip(expected_return, -0.5, 0.5)  # Max ±50%
        
        factors["pattern_target"] = pattern_target
        
        # 6. Support/Resistance Bias
        support_resistance = analysis_data.get("support_resistance_analysis", {})
        supply_demand = analysis_data.get("supply_demand_analysis", {})
        
        sr_bias = 0.0
        
        if support_resistance:
            nearest_support = support_resistance.get("nearest_support", {})
            nearest_resistance = support_resistance.get("nearest_resistance", {})
            
            if nearest_support and nearest_resistance:
                support_price = nearest_support.get("price", current_price)
                resistance_price = nearest_resistance.get("price", current_price)
                
                # Distance to support vs resistance
                dist_to_support = (current_price - support_price) / current_price
                dist_to_resistance = (resistance_price - current_price) / current_price
                
                if dist_to_resistance < dist_to_support:
                    sr_bias += 0.2  # Closer to resistance, bearish
                else:
                    sr_bias -= 0.2  # Closer to support, bullish
        
        factors["support_resistance_bias"] = np.clip(sr_bias, -1, 1)
        
        # 7. Volatility (for risk assessment)
        technical = analysis_data.get("technical_indicators", {})
        volatility = technical.get("atr_percent", 2.0) if technical else 2.0
        factors["volatility"] = volatility / 100  # Convert to decimal
        
        return factors
    
    def _predict_for_timeframe(
        self,
        timeframe: str,
        days: int,
        current_price: float,
        base_factors: Dict[str, float],
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate prediction for a specific timeframe"""
        
        # Calculate weighted expected return
        # Weights for different factors (sum to 1.0)
        weights = {
            "momentum_score": 0.15,
            "trend_strength": 0.20,
            "market_sentiment": 0.15,
            "institutional_flow": 0.25,  # Highest weight
            "pattern_target": 0.15,
            "support_resistance_bias": 0.10
        }
        
        # Calculate composite score
        composite_score = sum(
            base_factors[factor] * weight
            for factor, weight in weights.items()
        )
        
        # Adjust for timeframe (longer timeframes have more uncertainty)
        timeframe_multiplier = {
            "1W": 1.0,  # Full multiplier for short-term
            "1M": 1.0,
            "2M": 0.9,
            "3M": 0.8,  # Slightly less aggressive for longer term
            "6M": 0.6   # More conservative for longer term
        }
        
        adjusted_score = composite_score * timeframe_multiplier.get(timeframe, 1.0)
        
        # Calculate expected return
        # Base return from composite score (max ±15% for 1W, ±30% for 1M, ±50% for 6M)
        max_return = {
            "1W": 0.15,  # Max ±15% for 1 week (more conservative for short-term)
            "1M": 0.30,
            "2M": 0.35,
            "3M": 0.45,
            "6M": 0.60
        }
        
        expected_return = adjusted_score * max_return.get(timeframe, 0.30)
        
        # Add volatility component (random walk component)
        volatility = base_factors["volatility"]
        volatility_component = volatility * np.sqrt(days / 21) * np.random.normal(0, 0.3)
        
        # Final expected return
        total_expected_return = expected_return + volatility_component
        
        # Calculate predicted price
        predicted_price = current_price * (1 + total_expected_return)
        
        # Calculate confidence based on factor agreement
        confidence = self._calculate_confidence(base_factors, adjusted_score)
        
        # Calculate price range (confidence intervals)
        price_range = self._calculate_price_range(
            predicted_price=predicted_price,
            current_price=current_price,
            volatility=volatility,
            days=days,
            confidence=confidence
        )
        
        # Calculate potential upside/downside
        potential_change = predicted_price - current_price
        potential_change_percent = (potential_change / current_price) * 100
        
        return {
            "timeframe": timeframe,
            "days": days,
            "predicted_price": round(predicted_price, 2),
            "current_price": round(current_price, 2),
            "expected_return": round(total_expected_return * 100, 2),
            "potential_change": round(potential_change, 2),
            "potential_change_percent": round(potential_change_percent, 2),
            "confidence": round(confidence, 2),
            "price_range": price_range,
            "factors_contributing": self._get_factors_contributing(base_factors, weights),
            "risk_level": self._assess_risk_level(volatility, abs(composite_score))
        }
    
    def _calculate_confidence(
        self,
        base_factors: Dict[str, float],
        composite_score: float
    ) -> float:
        """Calculate prediction confidence (0-100%)"""
        
        # Base confidence from factor agreement
        factor_values = [
            base_factors["momentum_score"],
            base_factors["trend_strength"],
            base_factors["market_sentiment"],
            base_factors["institutional_flow"]
        ]
        
        # Check if factors agree (same direction)
        positive_count = sum(1 for v in factor_values if v > 0.1)
        negative_count = sum(1 for v in factor_values if v < -0.1)
        
        if positive_count >= 3 or negative_count >= 3:
            agreement = 0.8  # High agreement
        elif positive_count >= 2 or negative_count >= 2:
            agreement = 0.6  # Moderate agreement
        else:
            agreement = 0.4  # Low agreement
        
        # Confidence based on composite score magnitude
        score_magnitude = abs(composite_score)
        magnitude_confidence = min(score_magnitude * 100, 80)  # Max 80% from magnitude
        
        # Combined confidence
        confidence = (agreement * 50) + (magnitude_confidence * 0.5)
        
        # Adjust for timeframe (longer = less confident)
        return min(confidence, 85)  # Cap at 85%
    
    def _calculate_price_range(
        self,
        predicted_price: float,
        current_price: float,
        volatility: float,
        days: int,
        confidence: float
    ) -> Dict[str, float]:
        """Calculate price range with confidence intervals"""
        
        # Calculate standard deviation based on volatility and time
        std_dev = current_price * volatility * np.sqrt(days / 21)
        
        # Confidence intervals (68%, 95%)
        z_68 = 1.0  # 1 standard deviation
        z_95 = 1.96  # 2 standard deviations
        
        return {
            "low_68": round(predicted_price - (std_dev * z_68), 2),
            "high_68": round(predicted_price + (std_dev * z_68), 2),
            "low_95": round(predicted_price - (std_dev * z_95), 2),
            "high_95": round(predicted_price + (std_dev * z_95), 2),
            "volatility": round(volatility * 100, 2)
        }
    
    def _get_factors_contributing(
        self,
        base_factors: Dict[str, float],
        weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Get list of contributing factors"""
        contributing = []
        
        for factor, value in base_factors.items():
            if factor in weights and abs(value) > 0.1:
                contribution = value * weights[factor]
                contributing.append({
                    "factor": factor.replace("_", " ").title(),
                    "value": round(value, 3),
                    "weight": weights[factor],
                    "contribution": round(contribution, 3),
                    "direction": "positive" if value > 0 else "negative"
                })
        
        return sorted(contributing, key=lambda x: abs(x["contribution"]), reverse=True)
    
    def _assess_risk_level(
        self,
        volatility: float,
        composite_magnitude: float
    ) -> str:
        """Assess risk level of prediction"""
        
        if volatility > 0.05 and composite_magnitude < 0.3:
            return "High"
        elif volatility > 0.03 or composite_magnitude < 0.5:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_overall_confidence(
        self,
        predictions: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence across all timeframes"""
        timeframes = predictions.get("timeframes", {})
        if not timeframes:
            return 0.0
        
        confidences = [
            tf.get("confidence", 0)
            for tf in timeframes.values()
        ]
        
        return round(sum(confidences) / len(confidences), 2)
    
    def _integrate_chart_image_insights(
        self,
        predictions: Dict[str, Any],
        chart_images: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Integrate chart image analysis insights into price predictions"""
        try:
            # Get support/resistance from chart images
            nearest_support = chart_images.get("nearest_support")
            nearest_resistance = chart_images.get("nearest_resistance")
            overall_trend = chart_images.get("overall_trend", "neutral")
            
            # Adjust predictions based on image analysis
            if nearest_support and nearest_resistance:
                support_price = nearest_support.get("estimated_price")
                resistance_price = nearest_resistance.get("estimated_price")
                
                if support_price and resistance_price:
                    # Calculate price range from images
                    price_range = resistance_price - support_price
                    
                    # Adjust predictions to respect image-based support/resistance
                    for tf_name, tf_data in predictions.get("timeframes", {}).items():
                        predicted_price = tf_data.get("predicted_price", current_price)
                        
                        # Ensure predictions respect image-based levels
                        if predicted_price < support_price:
                            # Prediction below support - adjust upward
                            predicted_price = support_price * 1.02  # 2% above support
                        elif predicted_price > resistance_price:
                            # Prediction above resistance - adjust downward
                            predicted_price = resistance_price * 0.98  # 2% below resistance
                        
                        # Recalculate metrics
                        potential_change = predicted_price - current_price
                        potential_change_percent = (potential_change / current_price) * 100
                        
                        tf_data["predicted_price"] = round(predicted_price, 2)
                        tf_data["potential_change"] = round(potential_change, 2)
                        tf_data["potential_change_percent"] = round(potential_change_percent, 2)
                        
                        # Add image-based context
                        tf_data["image_based_adjustment"] = True
                        tf_data["image_support"] = support_price
                        tf_data["image_resistance"] = resistance_price
            
            # Adjust confidence based on trend agreement
            if overall_trend != "neutral":
                for tf_name, tf_data in predictions.get("timeframes", {}).items():
                    predicted_change = tf_data.get("potential_change_percent", 0)
                    trend_agreement = (
                        (overall_trend == "uptrend" and predicted_change > 0) or
                        (overall_trend == "downtrend" and predicted_change < 0)
                    )
                    
                    if trend_agreement:
                        # Increase confidence if prediction aligns with image trend
                        current_confidence = tf_data.get("confidence", 0)
                        tf_data["confidence"] = min(current_confidence + 5, 90)  # Boost by 5%, max 90%
                        tf_data["trend_alignment"] = "aligned"
                    else:
                        tf_data["trend_alignment"] = "diverged"
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error integrating chart image insights: {e}")
            return predictions
    
    def _generate_prediction_summary(
        self,
        predictions: Dict[str, Any]
    ) -> str:
        """Generate human-readable summary of predictions"""
        timeframes = predictions.get("timeframes", {})
        current_price = predictions.get("current_price", 0)
        
        if not timeframes:
            return "Price predictions not available."
        
        summary_parts = []
        
        for tf_name in ["1W", "1M", "2M", "3M", "6M"]:
            tf_data = timeframes.get(tf_name, {})
            if tf_data:
                predicted_price = tf_data.get("predicted_price", current_price)
                change_percent = tf_data.get("potential_change_percent", 0)
                confidence = tf_data.get("confidence", 0)
                
                direction = "up" if change_percent > 0 else "down"
                summary_parts.append(
                    f"{tf_name}: ₹{predicted_price:.2f} ({abs(change_percent):.1f}% {direction}, "
                    f"{confidence:.0f}% confidence)"
                )
        
        return " | ".join(summary_parts) if summary_parts else "Predictions not available."

# Create singleton instance
price_prediction_service = PricePredictionService()

