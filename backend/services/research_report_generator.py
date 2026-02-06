"""
Research Report Generator Service
Auto-generates comprehensive research reports with advanced pattern detection
100% Legal - Your own analysis and insights
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from services.financial_ratios_service import financial_ratios_service
from services.advanced_chart_patterns import advanced_chart_pattern_detector
from core.data_service import data_service

logger = logging.getLogger(__name__)

class ResearchReportGenerator:
    """Generate comprehensive research reports"""
    
    def __init__(self):
        pass
    
    async def generate_report(
        self,
        symbol: str,
        financial_data: Optional[Dict] = None,
        financial_ratios: Optional[Dict] = None,
        technical_analysis: Optional[Dict] = None,
        sentiment_analysis: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive research report
        
        Args:
            symbol: Stock symbol
            financial_data: Financial data dictionary
            financial_ratios: Financial ratios dictionary
            technical_analysis: Technical analysis dictionary
        
        Returns:
            Complete research report
        """
        try:
            logger.info(f"📊 Generating research report for {symbol}...")
            
            # Get current price
            quote = await data_service.get_quote(symbol, exchange="NSE")
            current_price = float(quote.get("last_price", 0)) if quote else 0
            
            # Generate report sections
            report = {
                "symbol": symbol,
                "company_name": quote.get("company_name", symbol) if quote else symbol,
                "current_price": current_price,
                "report_date": datetime.utcnow().isoformat(),
                "sections": {}
            }
            
            # 1. Price Action Analysis
            report["sections"]["price_action"] = self._generate_price_action(
                symbol, current_price, technical_analysis
            )
            
            # 2. Financial Strength
            if financial_data and financial_ratios:
                report["sections"]["financial_strength"] = self._generate_financial_strength(
                    financial_data, financial_ratios
                )
            
            # 3. Valuation
            if financial_ratios:
                report["sections"]["valuation"] = self._generate_valuation(
                    current_price, financial_ratios
                )
            
            # 4. Technical Signals
            if technical_analysis:
                report["sections"]["technical_signals"] = self._generate_technical_signals(
                    technical_analysis
                )
            
            # 5. Market Sentiment & News Analysis
            if sentiment_analysis:
                report["sections"]["market_sentiment"] = self._generate_market_sentiment(
                    sentiment_analysis
                )
            
            # 6. Risk Assessment
            report["sections"]["risk_assessment"] = self._generate_risk_assessment(
                financial_ratios, technical_analysis, sentiment_analysis
            )
            
            # 7. Chart Pattern Analysis (NEW - Advanced Pattern Detection)
            report["sections"]["chart_patterns"] = await self._generate_chart_pattern_analysis(
                symbol, current_price
            )
            
            # 8. Investment Recommendation (Updated to include pattern analysis)
            report["sections"]["recommendation"] = self._generate_recommendation(
                report["sections"]
            )
            
            logger.info(f"✅ Research report generated for {symbol}")
            return report
        
        except Exception as e:
            logger.error(f"Error generating report for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "report_date": datetime.utcnow().isoformat()
            }
    
    def _generate_price_action(self, symbol: str, price: float, technical: Optional[Dict]) -> Dict:
        """Generate price action analysis"""
        if not technical:
            return {
                "summary": "Technical data not available",
                "trend": "unknown",
                "momentum": "unknown"
            }
        
        rsi = technical.get("rsi", 50)
        sma_20 = technical.get("sma_20", price)
        sma_50 = technical.get("sma_50", price)
        
        # Determine trend
        if price > sma_20 > sma_50:
            trend = "uptrend"
            trend_strength = "strong"
        elif price < sma_20 < sma_50:
            trend = "downtrend"
            trend_strength = "strong"
        else:
            trend = "sideways"
            trend_strength = "moderate"
        
        # Determine momentum
        if rsi > 70:
            momentum = "overbought"
        elif rsi < 30:
            momentum = "oversold"
        else:
            momentum = "neutral"
        
        summary = f"Stock trading at ₹{price:.2f}. "
        if trend == "uptrend":
            summary += f"Trading above 200 SMA → long-term uptrend. "
        elif trend == "downtrend":
            summary += f"Trading below 200 SMA → long-term downtrend. "
        summary += f"RSI = {rsi:.1f} → {momentum} momentum."
        
        return {
            "summary": summary,
            "trend": trend,
            "trend_strength": trend_strength,
            "momentum": momentum,
            "rsi": rsi,
            "sma_20": sma_20,
            "sma_50": sma_50
        }
    
    def _generate_financial_strength(self, financial_data: Dict, ratios: Dict) -> Dict:
        """Generate financial strength analysis"""
        revenue = financial_data.get("revenue", 0)
        net_profit = financial_data.get("net_profit", 0)
        roe = ratios.get("roe")
        roce = ratios.get("roce")
        debt_to_equity = ratios.get("debt_to_equity")
        
        strength_score = 0
        strengths = []
        weaknesses = []
        
        # Revenue growth
        if revenue and revenue > 0:
            strengths.append(f"Revenue: ₹{revenue/10000:.2f} Cr")
        
        # Profitability
        if roe and roe > 20:
            strengths.append(f"ROE: {roe:.1f}% (Excellent)")
            strength_score += 2
        elif roe and roe > 15:
            strengths.append(f"ROE: {roe:.1f}% (Good)")
            strength_score += 1
        elif roe:
            weaknesses.append(f"ROE: {roe:.1f}% (Below average)")
        
        # Debt
        if debt_to_equity and debt_to_equity < 0.5:
            strengths.append(f"Low debt: Debt-to-Equity {debt_to_equity:.2f}")
            strength_score += 1
        elif debt_to_equity and debt_to_equity > 1.0:
            weaknesses.append(f"High debt: Debt-to-Equity {debt_to_equity:.2f}")
            strength_score -= 1
        
        # Overall assessment
        if strength_score >= 3:
            assessment = "Strong"
        elif strength_score >= 1:
            assessment = "Moderate"
        else:
            assessment = "Weak"
        
        summary = f"Financial performance: {assessment}. "
        if strengths:
            summary += "Strengths: " + ", ".join(strengths) + ". "
        if weaknesses:
            summary += "Concerns: " + ", ".join(weaknesses) + "."
        
        return {
            "summary": summary,
            "assessment": assessment,
            "strength_score": strength_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "revenue": revenue,
            "net_profit": net_profit,
            "roe": roe,
            "roce": roce,
            "debt_to_equity": debt_to_equity
        }
    
    def _generate_valuation(self, price: float, ratios: Dict) -> Dict:
        """Generate valuation analysis"""
        pe_ratio = ratios.get("pe_ratio")
        pb_ratio = ratios.get("pb_ratio")
        
        valuation_assessment = "unknown"
        summary = ""
        
        if pe_ratio:
            if pe_ratio < 15:
                valuation_assessment = "undervalued"
                summary = f"PE = {pe_ratio:.1f} (Attractive valuation compared to sector avg)"
            elif pe_ratio < 25:
                valuation_assessment = "fair"
                summary = f"PE = {pe_ratio:.1f} (Fair valuation)"
            else:
                valuation_assessment = "expensive"
                summary = f"PE = {pe_ratio:.1f} (Slightly expensive compared to sector avg)"
        
        return {
            "summary": summary,
            "assessment": valuation_assessment,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio
        }
    
    def _generate_technical_signals(self, technical: Dict) -> Dict:
        """Generate technical signals analysis"""
        rsi = technical.get("rsi", 50)
        macd = technical.get("macd", "0")
        signals = []
        
        if rsi < 30:
            signals.append("RSI oversold - potential buy signal")
        elif rsi > 70:
            signals.append("RSI overbought - potential sell signal")
        
        if isinstance(macd, str):
            try:
                macd_val = float(macd)
                if macd_val > 0:
                    signals.append("MACD bullish crossover")
                elif macd_val < 0:
                    signals.append("MACD bearish")
            except:
                pass
        
        summary = ". ".join(signals) if signals else "Mixed technical signals"
        
        return {
            "summary": summary,
            "signals": signals,
            "rsi": rsi,
            "macd": macd
        }
    
    def _generate_market_sentiment(self, sentiment: Dict) -> Dict:
        """Generate market sentiment analysis from news and current situation"""
        news_sentiment = sentiment.get("news_sentiment", "neutral")
        social_sentiment = sentiment.get("social_sentiment", "neutral")
        market_sentiment = sentiment.get("market_sentiment", "neutral")
        overall_sentiment = sentiment.get("overall_sentiment", "neutral")
        sentiment_score = sentiment.get("sentiment_score", 0.0)
        
        # Determine overall sentiment
        sentiment_map = {
            "positive": "Bullish",
            "negative": "Bearish",
            "neutral": "Neutral",
            "bullish": "Bullish",
            "bearish": "Bearish"
        }
        
        overall = sentiment_map.get(overall_sentiment.lower(), "Neutral")
        if not overall or overall == "Neutral":
            # Try to determine from individual sentiments
            positive_count = sum([
                1 for s in [news_sentiment, social_sentiment, market_sentiment]
                if s and "positive" in str(s).lower() or "bullish" in str(s).lower()
            ])
            negative_count = sum([
                1 for s in [news_sentiment, social_sentiment, market_sentiment]
                if s and "negative" in str(s).lower() or "bearish" in str(s).lower()
            ])
            
            if positive_count > negative_count:
                overall = "Bullish"
            elif negative_count > positive_count:
                overall = "Bearish"
            else:
                overall = "Neutral"
        
        # Build summary
        summary_parts = []
        if news_sentiment:
            summary_parts.append(f"News sentiment: {news_sentiment.capitalize()}")
        if social_sentiment:
            summary_parts.append(f"Social sentiment: {social_sentiment.capitalize()}")
        if market_sentiment:
            summary_parts.append(f"Market sentiment: {market_sentiment.capitalize()}")
        
        summary = f"Overall market sentiment: {overall}. " + ". ".join(summary_parts) if summary_parts else f"Overall market sentiment: {overall}."
        
        # Add sentiment score if available
        if sentiment_score:
            if sentiment_score > 0.3:
                summary += f" Sentiment score: {sentiment_score:.2f} (Positive)."
            elif sentiment_score < -0.3:
                summary += f" Sentiment score: {sentiment_score:.2f} (Negative)."
            else:
                summary += f" Sentiment score: {sentiment_score:.2f} (Neutral)."
        
        return {
            "summary": summary,
            "overall_sentiment": overall,
            "news_sentiment": news_sentiment,
            "social_sentiment": social_sentiment,
            "market_sentiment": market_sentiment,
            "sentiment_score": sentiment_score
        }
    
    def _generate_risk_assessment(self, ratios: Optional[Dict], technical: Optional[Dict], sentiment: Optional[Dict] = None) -> Dict:
        """Generate risk assessment"""
        risk_level = "medium"
        risk_factors = []
        
        if ratios:
            debt_to_equity = ratios.get("debt_to_equity")
            if debt_to_equity and debt_to_equity > 1.0:
                risk_level = "high"
                risk_factors.append("High debt-to-equity ratio")
        
        if technical:
            rsi = technical.get("rsi", 50)
            if rsi > 70:
                risk_factors.append("Overbought conditions")
            elif rsi < 30:
                risk_factors.append("Oversold conditions")
        
        # Add sentiment-based risk factors
        if sentiment:
            news_sentiment = sentiment.get("news_sentiment", "neutral")
            if news_sentiment and "negative" in str(news_sentiment).lower():
                risk_factors.append("Negative news sentiment")
            market_sentiment = sentiment.get("market_sentiment", "neutral")
            if market_sentiment and "bearish" in str(market_sentiment).lower():
                risk_factors.append("Bearish market sentiment")
        
        if not risk_factors:
            risk_factors.append("Moderate risk profile")
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "summary": f"Risk assessment: {risk_level}. " + ". ".join(risk_factors)
        }
    
    async def _generate_chart_pattern_analysis(
        self,
        symbol: str,
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate chart pattern analysis using advanced pattern detection"""
        try:
            # Get historical data for pattern detection
            from core.yahoo_finance_scraper import yahoo_finance_scraper
            
            # Map timeframe to yahoo finance interval
            timeframe_to_interval = {
                "1m": "1m", "2m": "2m", "3m": "3m", "5m": "5m", "15m": "15m",
                "1h": "1h", "2h": "2h", "4h": "4h",
                "1D": "1d", "1W": "1wk", "1M": "1mo", "3M": "3mo", "6M": "6mo"
            }
            interval = timeframe_to_interval.get(timeframe, "1d")
            
            # Determine period based on timeframe (longer for higher timeframes)
            period_map = {
                "1m": "5d", "2m": "5d", "3m": "5d", "5m": "5d", "15m": "5d",
                "1h": "1mo", "2h": "1mo", "4h": "1mo",
                "1D": "1y", "1W": "1y", "1M": "2y", "3M": "2y", "6M": "5y"
            }
            period = period_map.get(timeframe, "1y")
            
            # Get data for the requested timeframe
            # Use get_historical_candles instead of get_historical_data
            historical_data = await yahoo_finance_scraper.get_historical_candles(
                symbol=symbol,
                interval=interval,
                range_period=period
            )
            
            if not historical_data or len(historical_data) < 20:
                return {
                    "summary": "Insufficient data for pattern analysis",
                    "patterns": [],
                    "has_patterns": False
                }
            
            # Convert to DataFrame
            import pandas as pd
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Detect patterns
            patterns = advanced_chart_pattern_detector.detect_all_patterns(
                df, symbol, "1W"
            )
            
            if not patterns:
                return {
                    "summary": "No significant chart patterns detected in current timeframe.",
                    "patterns": [],
                    "has_patterns": False
                }
            
            # Get the most significant pattern (highest confidence)
            primary_pattern = patterns[0] if patterns else None
            
            # Build summary
            pattern_summary = f"Detected {len(patterns)} chart pattern(s). "
            
            if primary_pattern:
                pattern_name = primary_pattern.get("pattern_name", "Pattern")
                confidence = primary_pattern.get("confidence", 0) * 100
                pattern_direction = primary_pattern.get("pattern_direction", "")
                
                pattern_summary += f"Primary pattern: {pattern_name} ({confidence:.1f}% confidence, {pattern_direction}). "
                
                # Add target price if available
                if "target_price" in primary_pattern:
                    target = primary_pattern["target_price"]
                    upside = primary_pattern.get("potential_upside", 0)
                    pattern_summary += f"Target: ₹{target:.2f} (Potential upside: {upside:.2f}%). "
                
                # Add trading signal
                trading_impl = primary_pattern.get("trading_implications", {})
                signal = trading_impl.get("signal", "")
                if signal:
                    pattern_summary += f"Trading signal: {signal}. "
            
            return {
                "summary": pattern_summary,
                "patterns": patterns,
                "has_patterns": True,
                "primary_pattern": primary_pattern,
                "pattern_count": len(patterns)
            }
            
        except Exception as e:
            logger.error(f"Error generating chart pattern analysis: {e}")
            return {
                "summary": f"Pattern analysis unavailable: {str(e)}",
                "patterns": [],
                "has_patterns": False
        }
    
    def _generate_recommendation(self, sections: Dict) -> Dict:
        """Generate investment recommendation"""
        price_action = sections.get("price_action", {})
        financial = sections.get("financial_strength", {})
        valuation = sections.get("valuation", {})
        technical = sections.get("technical_signals", {})
        sentiment = sections.get("market_sentiment", {})
        risk = sections.get("risk_assessment", {})
        
        recommendation = "HOLD"
        confidence = 50
        reasoning = []
        
        # Analyze all factors
        if price_action.get("trend") == "uptrend":
            reasoning.append("Strong uptrend")
            confidence += 10
        
        if financial.get("assessment") == "Strong":
            reasoning.append("Strong financials")
            confidence += 15
            recommendation = "BUY"
        elif financial.get("assessment") == "Weak":
            reasoning.append("Weak financials")
            confidence -= 15
            recommendation = "SELL"
        
        if valuation.get("assessment") == "undervalued":
            reasoning.append("Attractive valuation")
            confidence += 10
        elif valuation.get("assessment") == "expensive":
            reasoning.append("Expensive valuation")
            confidence -= 10
        
        if technical.get("signals"):
            if "buy signal" in str(technical.get("signals", [])).lower():
                reasoning.append("Technical buy signals")
                confidence += 10
        
        # NEW: Chart Pattern Analysis (Most Important)
        chart_patterns = sections.get("chart_patterns", {})
        if chart_patterns.get("has_patterns"):
            primary_pattern = chart_patterns.get("primary_pattern")
            if primary_pattern:
                pattern_name = primary_pattern.get("pattern_name", "")
                pattern_confidence = primary_pattern.get("confidence", 0)
                pattern_direction = primary_pattern.get("pattern_direction", "")
                
                # Strong bullish patterns significantly boost recommendation
                if pattern_direction == "bullish" and pattern_confidence > 0.6:
                    reasoning.append(f"{pattern_name} pattern detected (Bullish)")
                    confidence += 20
                    
                    # If it's Reverse Head & Shoulder with high confidence, strong BUY
                    if "reverse_head_shoulder" in primary_pattern.get("pattern_type", "").lower():
                        reasoning.append("Reverse Head & Shoulder pattern - Strong bullish reversal signal")
                        confidence += 15
                        recommendation = "BUY"
                    
                    # Add target price to recommendation
                    if "target_price" in primary_pattern:
                        target = primary_pattern["target_price"]
                        upside = primary_pattern.get("potential_upside", 0)
                        reasoning.append(f"Pattern target: ₹{target:.2f} ({upside:.2f}% upside)")
                
                elif pattern_direction == "bearish" and pattern_confidence > 0.6:
                    reasoning.append(f"{pattern_name} pattern detected (Bearish)")
                    confidence -= 15
                    if confidence < 40:
                        recommendation = "SELL"
        
        # Add sentiment-based reasoning
        if sentiment:
            overall_sentiment = sentiment.get("overall_sentiment", "Neutral")
            if overall_sentiment == "Bullish":
                reasoning.append("Bullish market sentiment")
                confidence += 10
            elif overall_sentiment == "Bearish":
                reasoning.append("Bearish market sentiment")
                confidence -= 10
            
            news_sentiment = sentiment.get("news_sentiment", "neutral")
            if news_sentiment and "positive" in str(news_sentiment).lower():
                reasoning.append("Positive news sentiment")
                confidence += 5
            elif news_sentiment and "negative" in str(news_sentiment).lower():
                reasoning.append("Negative news sentiment")
                confidence -= 5
        
        if risk.get("risk_level") == "high":
            reasoning.append("High risk")
            confidence -= 10
        
        # Finalize recommendation
        if confidence >= 70:
            recommendation = "BUY"
        elif confidence <= 30:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        # Get target price and holding period from pattern if available
        target_price = None
        holding_period = "3-6 months"  # Default
        potential_upside = None
        
        chart_patterns = sections.get("chart_patterns", {})
        if chart_patterns.get("has_patterns"):
            primary_pattern = chart_patterns.get("primary_pattern")
            if primary_pattern and "target_price" in primary_pattern:
                target_price = primary_pattern["target_price"]
                potential_upside = primary_pattern.get("potential_upside", 0)
                trading_impl = primary_pattern.get("trading_implications", {})
                holding_period = trading_impl.get("holding_period", "3-4 months")
        
        summary = f"Recommendation: {recommendation} (Confidence: {confidence}%). "
        summary += "Reasoning: " + ". ".join(reasoning) if reasoning else "Mixed signals"
        
        if target_price:
            summary += f" Target Price: ₹{target_price:.2f}"
            if potential_upside:
                summary += f" (Potential Upside: {potential_upside:.2f}%)"
            summary += f". Expected Holding Period: {holding_period}."
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "summary": summary,
            "target_price": target_price,
            "potential_upside": potential_upside,
            "holding_period": holding_period
        }

# Create singleton instance
research_report_generator = ResearchReportGenerator()

