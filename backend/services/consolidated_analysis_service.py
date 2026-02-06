"""
Consolidated Analysis Service
Combines all analysis features into a single comprehensive response:
- Price Action (Support/Resistance, Pivot Points)
- Levels (HH/HL/LH/LL)
- Gap Filling Detection & Signals
- Trendline Retesting Signals
- News Integration
- Chart Data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

from services.swing_point_analysis import SwingPointAnalysisService
from services.trendline_detection import TrendlineDetectionService
from services.enhanced_chart_service import EnhancedChartService
from services.intraday_trading_algorithms import IntradayTradingAlgorithms
from core.sentiment_analysis import SentimentAnalysisService

logger = logging.getLogger(__name__)

class ConsolidatedAnalysisService:
    def __init__(self):
        self.swing_service = SwingPointAnalysisService()
        self.trendline_service = TrendlineDetectionService()
        self.chart_service = EnhancedChartService()
        self.intraday_algorithms = IntradayTradingAlgorithms()
        self.sentiment_service = SentimentAnalysisService()
    
    async def get_consolidated_analysis(
        self,
        symbol: str,
        timeframe: str = "1D",
        days: int = 100
    ) -> Dict[str, Any]:
        """
        Get comprehensive consolidated analysis for a symbol
        
        Returns:
            Dictionary containing:
            - chart_data: OHLCV data
            - price_action: Support/Resistance, Pivot Points
            - levels: HH/HL/LH/LL classification
            - gaps: Gap detection and filling status
            - trendlines: Trendline analysis with retest signals
            - news: News feed with sentiment
            - signals: All trading signals
        """
        try:
            # Fetch historical data
            from services.data_fetcher import fetch_historical_data
            candles = await fetch_historical_data(symbol=symbol, timeframe=timeframe, days=days)
            
            if not candles or len(candles) < 10:
                return {
                    "success": False,
                    "error": "Insufficient data for analysis"
                }
            
            df = pd.DataFrame(candles)
            df = df.sort_values('time' if 'time' in df.columns else 'timestamp').reset_index(drop=True)
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    if col == 'volume' and 'vol' in df.columns:
                        df['volume'] = df['vol']
                    else:
                        return {
                            "success": False,
                            "error": f"Missing required column: {col}"
                        }
            
            # Get current price
            current_price = float(df.iloc[-1]['close'])
            
            # 1. Price Action Analysis
            price_action = self._analyze_price_action(df, current_price)
            
            # 2. Levels (HH/HL/LH/LL)
            levels = self._analyze_levels(df)
            
            # 3. Gap Analysis
            gaps = self._analyze_gaps(df)
            
            # 4. Trendline Analysis with Retests
            trendlines = self._analyze_trendlines(df)
            
            # 5. Generate Signals
            signals = self._generate_signals(df, gaps, trendlines, current_price)
            
            # 6. News (will be fetched separately by frontend)
            news_summary = {
                "total_news": 0,
                "sentiment": "NEUTRAL",
                "impact": "LOW"
            }
            
            result = {
                "success": True,
                "data": {
                    "chart_data": candles[-100:],  # Last 100 candles
                    "current_price": current_price,
                    "price_action": price_action,
                    "levels": levels,
                    "gaps": gaps,
                    "trendlines": trendlines,
                    "news": news_summary,
                    "signals": signals,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in consolidated analysis for {symbol}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_price_action(self, df: pd.DataFrame, current_price: float) -> Dict[str, Any]:
        """Analyze price action: Support/Resistance, Pivot Points"""
        try:
            # Get support/resistance from chart service
            s_r_data = self.chart_service._calculate_support_resistance(df)
            
            support_levels = s_r_data.get('support_levels', [])
            resistance_levels = s_r_data.get('resistance_levels', [])
            
            # Calculate pivot points
            last_row = df.iloc[-1]
            high = float(last_row['high'])
            low = float(last_row['low'])
            close = float(last_row['close'])
            
            pivot_point = (high + low + close) / 3
            resistance_1 = 2 * pivot_point - low
            support_1 = 2 * pivot_point - high
            resistance_2 = pivot_point + (high - low)
            support_2 = pivot_point - (high - low)
            
            # Determine trend
            sma_20 = df['close'].tail(20).mean()
            sma_50 = df['close'].tail(50).mean() if len(df) >= 50 else sma_20
            
            if current_price > sma_20 > sma_50:
                trend = "UPTREND"
            elif current_price < sma_20 < sma_50:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
            
            return {
                "support_levels": sorted(support_levels, reverse=True)[:5],
                "resistance_levels": sorted(resistance_levels)[:5],
                "pivot_point": round(pivot_point, 2),
                "resistance_1": round(resistance_1, 2),
                "resistance_2": round(resistance_2, 2),
                "support_1": round(support_1, 2),
                "support_2": round(support_2, 2),
                "trend": trend,
                "current_price": round(current_price, 2)
            }
        except Exception as e:
            logger.error(f"Error in price action analysis: {str(e)}")
            return {
                "support_levels": [],
                "resistance_levels": [],
                "pivot_point": 0,
                "trend": "UNKNOWN",
                "current_price": current_price
            }
    
    def _analyze_levels(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze swing points and classify as HH/HL/LH/LL"""
        try:
            # Convert DataFrame to list format for swing service
            data_list = df.to_dict('records')
            
            # Get swing point analysis
            swing_result = self.swing_service.analyze_swing_points(data_list, strength=5)
            
            if not swing_result.get("success"):
                return {
                    "hh": [],
                    "hl": [],
                    "lh": [],
                    "ll": [],
                    "trend_structure": "UNKNOWN"
                }
            
            swing_data = swing_result.get("data", {})
            labeled_highs = swing_data.get("swing_highs", [])
            labeled_lows = swing_data.get("swing_lows", [])
            trend_analysis = swing_data.get("trend_analysis", {})
            
            # Extract HH, HL, LH, LL
            hh = [p for p in labeled_highs if p.get("label") == "HH"]
            hl = [p for p in labeled_lows if p.get("label") == "HL"]
            lh = [p for p in labeled_highs if p.get("label") == "LH"]
            ll = [p for p in labeled_lows if p.get("label") == "LL"]
            
            trend_structure = trend_analysis.get("trend_direction", "UNKNOWN")
            
            return {
                "hh": hh[:10],  # Top 10
                "hl": hl[:10],
                "lh": lh[:10],
                "ll": ll[:10],
                "trend_structure": trend_structure,
                "total_hh": len(hh),
                "total_hl": len(hl),
                "total_lh": len(lh),
                "total_ll": len(ll)
            }
        except Exception as e:
            logger.error(f"Error in levels analysis: {str(e)}")
            return {
                "hh": [],
                "hl": [],
                "lh": [],
                "ll": [],
                "trend_structure": "UNKNOWN"
            }
    
    def _analyze_gaps(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect gaps and check if they're filled"""
        try:
            gaps = []
            
            # Look for gaps in the data
            for i in range(1, len(df)):
                prev_close = float(df.iloc[i-1]['close'])
                curr_open = float(df.iloc[i]['open'])
                curr_high = float(df.iloc[i]['high'])
                curr_low = float(df.iloc[i]['low'])
                curr_close = float(df.iloc[i]['close'])
                
                # Calculate gap
                gap = curr_open - prev_close
                gap_pct = (gap / prev_close) * 100 if prev_close > 0 else 0
                
                # Only consider significant gaps (>0.5%)
                if abs(gap_pct) > 0.5:
                    gap_type = "UPWARD" if gap > 0 else "DOWNWARD"
                    gap_start = prev_close
                    gap_end = curr_open
                    
                    # Check if gap is filled
                    is_filled = False
                    filled_at = None
                    
                    if gap_type == "UPWARD":
                        # Gap up: check if price went below gap start
                        for j in range(i, min(i + 20, len(df))):  # Check next 20 candles
                            if float(df.iloc[j]['low']) <= gap_start:
                                is_filled = True
                                filled_at = df.iloc[j].get('time') or df.iloc[j].get('timestamp')
                                break
                    else:
                        # Gap down: check if price went above gap start
                        for j in range(i, min(i + 20, len(df))):
                            if float(df.iloc[j]['high']) >= gap_start:
                                is_filled = True
                                filled_at = df.iloc[j].get('time') or df.iloc[j].get('timestamp')
                                break
                    
                    gaps.append({
                        "type": gap_type,
                        "start": round(gap_start, 2),
                        "end": round(gap_end, 2),
                        "size": round(abs(gap), 2),
                        "size_pct": round(abs(gap_pct), 2),
                        "is_filled": is_filled,
                        "filled_at": filled_at,
                        "date": df.iloc[i].get('time') or df.iloc[i].get('timestamp'),
                        "current_price": round(curr_close, 2)
                    })
            
            # Return gaps sorted by date (newest first)
            return sorted(gaps, key=lambda x: x.get('date', ''), reverse=True)[:20]
            
        except Exception as e:
            logger.error(f"Error in gap analysis: {str(e)}")
            return []
    
    def _analyze_trendlines(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze trendlines and detect retests"""
        try:
            # Convert DataFrame to list format
            data_list = df.to_dict('records')
            
            # Get trendline analysis
            trendline_result = self.trendline_service.detect_trendlines(data_list)
            
            if not trendline_result.get("success"):
                return []
            
            trendlines_data = trendline_result.get("data", {}).get("trendlines", [])
            
            # Enhance with retest information
            enhanced_trendlines = []
            for tl in trendlines_data[:10]:  # Top 10 trendlines
                if tl.get("is_broken"):
                    break_info = tl.get("break_info", {})
                    if break_info:
                        break_index = break_info.get("break_index")
                        if break_index is not None:
                            # Check for retest
                            retest_info = self.trendline_service._check_retest(
                                df,
                                break_index,
                                tl.get("slope", 0),
                                tl.get("intercept", 0),
                                tl.get("is_uptrend", True),
                                lookback_bars=10
                            )
                            
                            tl["retest_info"] = retest_info
                            
                            # Add signal if retested
                            if retest_info.get("retested"):
                                tl["retest_signal"] = {
                                    "type": "TRENDLINE_RETEST",
                                    "message": f"Trendline retested at {retest_info.get('retest_price', 0):.2f}",
                                    "strength": "HIGH" if tl.get("strength") == "STRONG" else "MEDIUM",
                                    "timestamp": df.iloc[retest_info.get("retest_index", len(df)-1)].get('time') or 
                                                df.iloc[retest_info.get("retest_index", len(df)-1)].get('timestamp')
                                }
                
                enhanced_trendlines.append(tl)
            
            return enhanced_trendlines
            
        except Exception as e:
            logger.error(f"Error in trendline analysis: {str(e)}")
            return []
    
    def _generate_signals(self, df: pd.DataFrame, gaps: List[Dict], trendlines: List[Dict], current_price: float) -> List[Dict[str, Any]]:
        """Generate all trading signals"""
        signals = []
        
        try:
            # 1. Gap filling signals
            for gap in gaps:
                if gap.get("is_filled"):
                    signals.append({
                        "type": "GAP_FILL",
                        "message": f"{gap.get('type')} gap filled at {gap.get('start', 0):.2f}",
                        "timestamp": gap.get("filled_at"),
                        "strength": "MODERATE",
                        "price": gap.get("start"),
                        "gap_type": gap.get("type")
                    })
            
            # 2. Trendline retest signals
            for tl in trendlines:
                retest_signal = tl.get("retest_signal")
                if retest_signal:
                    signals.append(retest_signal)
            
            # 3. Gap approaching signals (gaps not yet filled, price approaching)
            for gap in gaps:
                if not gap.get("is_filled"):
                    gap_start = gap.get("start", 0)
                    distance = abs(current_price - gap_start)
                    distance_pct = (distance / current_price) * 100 if current_price > 0 else 100
                    
                    if distance_pct < 2:  # Within 2% of gap
                        signals.append({
                            "type": "GAP_APPROACHING",
                            "message": f"Price approaching {gap.get('type')} gap at {gap_start:.2f}",
                            "timestamp": datetime.now().isoformat(),
                            "strength": "LOW",
                            "price": gap_start,
                            "distance_pct": round(distance_pct, 2)
                        })
            
            # Sort by timestamp (newest first)
            signals.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return signals[:20]  # Top 20 signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return []
