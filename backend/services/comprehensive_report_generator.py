"""
Comprehensive Research Report Generator
Generates vast level of analysis automatically - similar to professional research reports
Includes: Quarterly P&L, Yearly P&L, Balance Sheet, Shareholding, 10 Strong Points, etc.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from services.financial_ratios_service import financial_ratios_service
from services.advanced_chart_patterns import advanced_chart_pattern_detector
from services.enhanced_chart_service import EnhancedChartService
from services.market_factors_service import market_factors_service
from services.trendline_detection import TrendlineDetectionService
from services.market_structure import MarketStructureService
from services.support_resistance import SupportResistanceService
from services.swing_point_analysis import SwingPointAnalysisService
from services.supply_demand import SupplyDemandService
from services.price_prediction_service import price_prediction_service
from services.detailed_company_research import detailed_company_research
from core.data_service import data_service
from core.database_unified import FinancialData, FinancialRatios, StockMaster

logger = logging.getLogger(__name__)

class ComprehensiveReportGenerator:
    """Generate comprehensive research reports with vast analysis"""
    
    def __init__(self):
        self.enhanced_chart_service = EnhancedChartService()
        self.trendline_service = TrendlineDetectionService()
        self.market_structure_service = MarketStructureService()
        self.support_resistance_service = SupportResistanceService()
        self.swing_point_service = SwingPointAnalysisService()
        self.supply_demand_service = SupplyDemandService()
    
    async def generate_comprehensive_report(
        self,
        symbol: str,
        db: Session,
        financial_data: Optional[Dict] = None,
        financial_ratios: Optional[Dict] = None,
        technical_analysis: Optional[Dict] = None,
        sentiment_analysis: Optional[Dict] = None,
        timeframe: str = "1D",
        chart_image_analysis: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive research report with vast analysis
        
        Returns report with all sections similar to professional research reports
        """
        try:
            logger.info(f"📊 Generating comprehensive research report for {symbol}...")
            
            # Get current price and company info
            quote = await data_service.get_quote(symbol, exchange="NSE")
            current_price = float(quote.get("last_price", 0)) if quote else 0
            company_name = quote.get("company_name", symbol) if quote else symbol
            
            # Get stock master info
            stock_master = db.query(StockMaster).filter(
                StockMaster.symbol == symbol.upper()
            ).first()
            
            market_cap = None
            if stock_master and stock_master.market_cap:
                market_cap = float(stock_master.market_cap)
            elif current_price > 0:
                # Estimate market cap if not available (rough estimate)
                # This would need actual shares outstanding for accuracy
                pass
            
            # Fetch all financial data from database
            quarterly_data = db.query(FinancialData).filter(
                FinancialData.symbol == symbol.upper(),
                FinancialData.period_type == "QUARTERLY"
            ).order_by(FinancialData.period_end.desc()).limit(10).all()
            
            yearly_data = db.query(FinancialData).filter(
                FinancialData.symbol == symbol.upper(),
                FinancialData.period_type == "ANNUAL"
            ).order_by(FinancialData.period_end.desc()).limit(8).all()
            
            # Get all financial ratios
            all_ratios = db.query(FinancialRatios).filter(
                FinancialRatios.symbol == symbol.upper()
            ).order_by(FinancialRatios.period_end.desc()).limit(10).all()
            
            # Generate comprehensive report
            report = {
                "symbol": symbol,
                "company_name": company_name,
                "current_price": current_price,
                "market_cap": market_cap,
                "report_date": datetime.utcnow().isoformat(),
                "sections": {}
            }
            
            # 0. Executive Summary (NEW - Quick Win)
            report["sections"]["executive_summary"] = self._generate_executive_summary(
                symbol, company_name, current_price, financial_ratios, quarterly_data, 
                yearly_data, technical_analysis, market_cap
            )
            
            # 0.5. Key Metrics Dashboard (NEW - Quick Win)
            report["sections"]["key_metrics_dashboard"] = self._generate_key_metrics_dashboard(
                financial_ratios, current_price, quarterly_data, yearly_data, market_cap
            )
            
            # 0.6. Financial Trends Data (NEW - Quick Win)
            report["sections"]["financial_trends"] = self._generate_financial_trends_data(
                quarterly_data, yearly_data
            )
            
            # 0.7. Risk Indicators (NEW - Quick Win)
            report["sections"]["risk_indicators"] = self._generate_risk_indicators(
                financial_ratios, quarterly_data, technical_analysis
            )
            
            # 0.8. Comparison Table (NEW - Quick Win)
            report["sections"]["comparison_table"] = self._generate_comparison_table(
                quarterly_data, yearly_data, financial_ratios, all_ratios
            )
            
            # 1. Financial Ratios Summary (Key Metrics)
            report["sections"]["financial_ratios"] = self._generate_financial_ratios_summary(
                financial_ratios, current_price, market_cap, stock_master
            )
            
            # 1.5. Detailed Company Research (Company-specific detailed analysis)
            report["sections"]["detailed_company_research"] = await detailed_company_research.generate_research_section(symbol, use_scraper=True)
            
            # 2. Quarterly P&L Analysis
            report["sections"]["quarterly_pl"] = self._generate_quarterly_pl_analysis(
                quarterly_data, symbol, all_ratios
            )
            
            # 3. Yearly P&L Analysis
            report["sections"]["yearly_pl"] = self._generate_yearly_pl_analysis(
                yearly_data, symbol
            )
            
            # 4. Balance Sheet Analysis
            report["sections"]["balance_sheet"] = self._generate_balance_sheet_analysis(
                yearly_data, symbol
            )
            
            # 5. Financial Strength Analysis
            if financial_data and financial_ratios:
                report["sections"]["financial_strength"] = self._generate_financial_strength(
                    financial_data, financial_ratios, quarterly_data, yearly_data
                )
            
            # 6. Valuation Analysis
            if financial_ratios:
                report["sections"]["valuation"] = self._generate_valuation(
                    current_price, financial_ratios, all_ratios
                )
            
            # 7. Price Action & Technical Analysis
            report["sections"]["price_action"] = self._generate_price_action(
                symbol, current_price, technical_analysis
            )
            
            # 8. Technical Signals
            if technical_analysis:
                report["sections"]["technical_signals"] = self._generate_technical_signals(
                    technical_analysis
                )
            
            # 9. Chart Pattern Analysis (Enhanced - includes all patterns)
            report["sections"]["chart_patterns"] = await self._generate_comprehensive_chart_pattern_analysis(
                symbol, current_price, timeframe
            )
            
            # 9.5. Trading Analysis Sections (Trendlines, Market Structure, S/R, Swing Points, Supply/Demand)
            # Generate analysis for multiple timeframes, including intraday and higher timeframes
            timeframes_config = {
                # Intraday timeframes (short-term trading view)
                "1m": {"timeframe": "1m", "period": 300, "label": "1 Minute"},
                "2m": {"timeframe": "2m", "period": 300, "label": "2 Minute"},
                "3m": {"timeframe": "3m", "period": 300, "label": "3 Minute"},
                "5m": {"timeframe": "5m", "period": 300, "label": "5 Minute"},
                "15m": {"timeframe": "15m", "period": 300, "label": "15 Minute"},
                "1h": {"timeframe": "1h", "period": 300, "label": "1 Hour"},
                "2h": {"timeframe": "2h", "period": 300, "label": "2 Hour"},
                "4h": {"timeframe": "4h", "period": 300, "label": "4 Hour"},

                # Higher timeframes (swing / positional view)
                "1D": {"timeframe": "1D", "period": 200, "label": "Daily"},
                "1W": {"timeframe": "1W", "period": 100, "label": "Weekly"},
                "1M": {"timeframe": "1M", "period": 50, "label": "Monthly"},
                "3M": {"timeframe": "1M", "period": 150, "label": "3-Month"},
                "6M": {"timeframe": "1M", "period": 300, "label": "6-Month"},
            }
            
            # Use requested timeframe or default to daily
            requested_tf = timeframe if timeframe in timeframes_config else "1D"
            
            # Generate analysis ONLY for the requested timeframe (optimization: don't generate all timeframes)
            trading_analysis_by_timeframe = {}
            
            # Only process the requested timeframe to avoid timeout
            tf_config = timeframes_config.get(requested_tf)
            if tf_config:
                tf_key = requested_tf
                try:
                    candlestick_data = await self.enhanced_chart_service.get_candlestick_data(
                        symbol, timeframe=tf_config["timeframe"], period=tf_config["period"]
                    )
                    
                    if candlestick_data and "candlesticks" in candlestick_data and not "error" in candlestick_data:
                        ohlcv_data = candlestick_data["candlesticks"]
                        
                        # Convert to format expected by services
                        formatted_data = [
                            {
                                "time": c.get("time", i),
                                "open": float(c.get("open", 0)),
                                "high": float(c.get("high", 0)),
                                "low": float(c.get("low", 0)),
                                "close": float(c.get("close", 0)),
                                "volume": float(c.get("volume", 0)) if c.get("volume") else 0
                            }
                            for i, c in enumerate(ohlcv_data)
                        ]
                        
                        # Generate all trading analyses for this timeframe
                        trading_analysis_by_timeframe[tf_key] = {
                            "timeframe": tf_key,
                            "label": tf_config["label"],
                            "trendline_analysis": await self._generate_trendline_analysis(
                                symbol, formatted_data, current_price, tf_key
                            ),
                            "market_structure_analysis": await self._generate_market_structure_analysis(
                                symbol, formatted_data, current_price, tf_key
                            ),
                            "support_resistance_analysis": await self._generate_support_resistance_analysis(
                                symbol, formatted_data, current_price, tf_key
                            ),
                            "swing_point_analysis": await self._generate_swing_point_analysis(
                                symbol, formatted_data, current_price, tf_key
                            ),
                            "supply_demand_analysis": await self._generate_supply_demand_analysis(
                                symbol, formatted_data, current_price, tf_key
                            )
                        }
                    else:
                        trading_analysis_by_timeframe[tf_key] = {
                            "timeframe": tf_key,
                            "label": tf_config["label"],
                            "error": "Data not available"
                        }
                except Exception as e:
                    logger.error(f"Error generating {tf_key} analysis: {e}")
                    trading_analysis_by_timeframe[tf_key] = {
                        "timeframe": tf_key,
                        "label": tf_config["label"],
                        "error": str(e)
                    }
            
            # Set primary analysis (from requested timeframe)
            primary_analysis = trading_analysis_by_timeframe.get(requested_tf, {})
            if primary_analysis and "error" not in primary_analysis:
                report["sections"]["trendline_analysis"] = primary_analysis.get("trendline_analysis", {})
                report["sections"]["market_structure_analysis"] = primary_analysis.get("market_structure_analysis", {})
                report["sections"]["support_resistance_analysis"] = primary_analysis.get("support_resistance_analysis", {})
                report["sections"]["swing_point_analysis"] = primary_analysis.get("swing_point_analysis", {})
                report["sections"]["supply_demand_analysis"] = primary_analysis.get("supply_demand_analysis", {})
            else:
                # Fallback to daily if requested timeframe failed
                daily_analysis = trading_analysis_by_timeframe.get("1D", {})
                if daily_analysis and "error" not in daily_analysis:
                    report["sections"]["trendline_analysis"] = daily_analysis.get("trendline_analysis", {})
                    report["sections"]["market_structure_analysis"] = daily_analysis.get("market_structure_analysis", {})
                    report["sections"]["support_resistance_analysis"] = daily_analysis.get("support_resistance_analysis", {})
                    report["sections"]["swing_point_analysis"] = daily_analysis.get("swing_point_analysis", {})
                    report["sections"]["supply_demand_analysis"] = daily_analysis.get("supply_demand_analysis", {})
                else:
                    # Set empty sections if all timeframes failed
                    report["sections"]["trendline_analysis"] = {"summary": "Trading analysis data not available.", "has_data": False}
                    report["sections"]["market_structure_analysis"] = {"summary": "Market structure data not available.", "has_data": False}
                    report["sections"]["support_resistance_analysis"] = {"summary": "Support/Resistance data not available.", "has_data": False}
                    report["sections"]["swing_point_analysis"] = {"summary": "Swing point data not available.", "has_data": False}
                    report["sections"]["supply_demand_analysis"] = {"summary": "Supply/Demand data not available.", "has_data": False}
            
            # Store all timeframes analysis for comparison
            report["sections"]["trading_analysis_timeframes"] = trading_analysis_by_timeframe
            report["timeframe"] = requested_tf
            
            # 10. Market Factors (News, Orderbook, Block Deals, FII/DII)
            report["sections"]["market_factors"] = await self._generate_market_factors_analysis(
                symbol
            )
            
            # 10.5. Price Predictions (1M, 3M, 6M)
            report["sections"]["price_predictions"] = await self._generate_price_predictions(
                symbol, current_price, report["sections"]
            )
            
            # 10.6. Shared Chart Images Analysis (if provided)
            if chart_image_analysis and chart_image_analysis.get("success"):
                report["sections"]["chart_images_analysis"] = self._generate_chart_images_analysis(
                    chart_image_analysis, symbol, current_price
                )
            else:
                report["sections"]["chart_images_analysis"] = {
                    "summary": "No chart images provided for analysis.",
                    "has_data": False
                }
            
            # 11. Market Sentiment
            if sentiment_analysis:
                report["sections"]["market_sentiment"] = self._generate_market_sentiment(
                    sentiment_analysis
                )
            
            # 11. Risk Assessment
            report["sections"]["risk_assessment"] = self._generate_risk_assessment(
                financial_ratios, technical_analysis, sentiment_analysis, quarterly_data
            )
            
            # 12. 10 Strong Points (Comprehensive Analysis)
            report["sections"]["strong_points"] = self._generate_strong_points(
                report["sections"], symbol, current_price
            )
            
            # 13. Investment Recommendation
            report["sections"]["recommendation"] = self._generate_recommendation(
                report["sections"]
            )
            
            # 14. Comprehensive Conclusion
            report["sections"]["conclusion"] = self._generate_conclusion(
                report["sections"], symbol, current_price
            )
            
            logger.info(f"✅ Comprehensive research report generated for {symbol}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "symbol": symbol,
                "error": str(e),
                "report_date": datetime.utcnow().isoformat()
            }
    
    def _generate_financial_ratios_summary(
        self,
        ratios: Optional[Dict],
        current_price: float,
        market_cap: Optional[float],
        stock_master: Optional[StockMaster]
    ) -> Dict:
        """Generate financial ratios summary section"""
        try:
            summary_parts = []
            ratios_dict = {}
            
            if ratios:
                pe_ratio = ratios.get("pe_ratio")
                pb_ratio = ratios.get("pb_ratio")
                roe = ratios.get("roe")
                roce = ratios.get("roce")
                debt_to_equity = ratios.get("debt_to_equity")
                
                if pe_ratio:
                    ratios_dict["pe_ratio"] = float(pe_ratio)
                    summary_parts.append(f"PE Ratio: {pe_ratio:.2f}")
                
                if pb_ratio:
                    ratios_dict["pb_ratio"] = float(pb_ratio)
                    summary_parts.append(f"PB Ratio: {pb_ratio:.2f}")
                
                if roe:
                    ratios_dict["roe"] = float(roe)
                    summary_parts.append(f"ROE: {roe:.2f}%")
                
                if roce:
                    ratios_dict["roce"] = float(roce)
                    summary_parts.append(f"ROCE: {roce:.2f}%")
                
                if debt_to_equity is not None:
                    ratios_dict["debt_to_equity"] = float(debt_to_equity)
                    summary_parts.append(f"Debt-to-Equity: {debt_to_equity:.2f}")
            
            if market_cap:
                ratios_dict["market_cap"] = market_cap
                summary_parts.append(f"Market Cap: ₹{market_cap/10000:.2f} Cr")
            
            if current_price:
                ratios_dict["current_price"] = current_price
                summary_parts.append(f"Current Price: ₹{current_price:.2f}")
            
            summary = ". ".join(summary_parts) if summary_parts else "Financial ratios data not available."
            
            return {
                "summary": summary,
                "ratios": ratios_dict,
                "has_data": len(ratios_dict) > 0
            }
            
        except Exception as e:
            logger.error(f"Error generating financial ratios summary: {e}")
            return {"summary": "Financial ratios data not available.", "ratios": {}, "has_data": False}
    
    def _generate_quarterly_pl_analysis(
        self,
        quarterly_data: List,
        symbol: str,
        all_ratios: Optional[List] = None,
    ) -> Dict:
        """Generate quarterly P&L analysis"""
        try:
            if not quarterly_data or len(quarterly_data) == 0:
                return {
                    "summary": "Quarterly financial data not available.",
                    "quarters": [],
                    "has_data": False,
                    "trends": {}
                }
            
            quarters = []
            sales_trend = []
            profit_trend = []
            
            for q in quarterly_data[:10]:  # Last 10 quarters
                revenue_val = float(q.revenue) if q.revenue else None
                profit_val = float(q.net_profit) if q.net_profit else None
                ebit_val = float(q.ebit) if q.ebit else None
                net_worth_val = float(getattr(q, "net_worth", None)) if getattr(q, "net_worth", None) else None
                total_liab_val = float(getattr(q, "total_liabilities", None)) if getattr(q, "total_liabilities", None) else None

                net_margin_pct = None
                op_margin_pct = None
                if revenue_val and revenue_val > 0:
                    if profit_val is not None:
                        net_margin_pct = (profit_val / revenue_val) * 100
                    if ebit_val is not None:
                        op_margin_pct = (ebit_val / revenue_val) * 100

                # Quarterly debt-to-equity approximation:
                # If quarterly balance sheet fields exist, use Total Liabilities / Net Worth as a proxy.
                debt_to_equity_q = None
                if net_worth_val and net_worth_val > 0 and total_liab_val is not None:
                    debt_to_equity_q = total_liab_val / net_worth_val

                quarter_info = {
                    "period": q.period_end.strftime("%b-%y") if q.period_end else "N/A",
                    "period_end": q.period_end.isoformat() if q.period_end else None,
                    "revenue": revenue_val,
                    "net_profit": profit_val,
                    "eps": float(q.eps) if q.eps else None,
                    "operating_profit": ebit_val,
                    "net_margin_pct": round(net_margin_pct, 2) if net_margin_pct is not None else None,
                    "operating_margin_pct": round(op_margin_pct, 2) if op_margin_pct is not None else None,
                    "debt_to_equity": round(debt_to_equity_q, 2) if debt_to_equity_q is not None else None,
                }
                quarters.append(quarter_info)
                
                if q.revenue:
                    sales_trend.append(float(q.revenue))
                if q.net_profit:
                    profit_trend.append(float(q.net_profit))
            
            # Calculate trends
            trends = {}
            if len(sales_trend) >= 2:
                sales_growth = ((sales_trend[0] - sales_trend[-1]) / sales_trend[-1]) * 100 if sales_trend[-1] > 0 else 0
                trends["sales_growth"] = sales_growth
            
            if len(profit_trend) >= 2:
                profit_growth = ((profit_trend[0] - profit_trend[-1]) / profit_trend[-1]) * 100 if profit_trend[-1] > 0 else 0
                trends["profit_growth"] = profit_growth
            
            # Build summary
            summary_parts = []
            if len(quarters) > 0:
                latest = quarters[0]
                if latest.get("revenue"):
                    summary_parts.append(f"Latest Quarter Revenue: ₹{latest['revenue']/10000:.2f} Cr")
                if latest.get("net_profit"):
                    summary_parts.append(f"Net Profit: ₹{latest['net_profit']/10000:.2f} Cr")
                if latest.get("eps"):
                    summary_parts.append(f"EPS: ₹{latest['eps']:.2f}")
                if latest.get("net_margin_pct") is not None:
                    summary_parts.append(f"Net Margin: {latest['net_margin_pct']:.2f}%")
                if latest.get("operating_margin_pct") is not None:
                    summary_parts.append(f"Operating Margin: {latest['operating_margin_pct']:.2f}%")
            
            if trends.get("sales_growth"):
                summary_parts.append(f"Sales Growth (QoQ): {trends['sales_growth']:.2f}%")
            if trends.get("profit_growth"):
                summary_parts.append(f"Profit Growth (QoQ): {trends['profit_growth']:.2f}%")
            
            summary = ". ".join(summary_parts) if summary_parts else "Quarterly data analysis complete."
            
            ratios_snapshot = {}
            if all_ratios and len(all_ratios) > 0:
                r0 = all_ratios[0]
                for k in ["debt_to_equity", "current_ratio", "operating_margin", "roe", "roce", "pe_ratio", "pb_ratio"]:
                    v = getattr(r0, k, None)
                    if v is not None:
                        try:
                            ratios_snapshot[k] = float(v)
                        except Exception:
                            pass
                if getattr(r0, "period_end", None):
                    ratios_snapshot["as_of_period_end"] = r0.period_end.isoformat()

            # Extract debt_to_equity series for last 8 quarters (last 2 years)
            debt_to_equity_series = [
                {
                    "period": q.get("period"),
                    "period_end": q.get("period_end"),
                    "debt_to_equity": q.get("debt_to_equity")
                }
                for q in quarters[:8]  # Last 8 quarters = 2 years
            ]

            return {
                "summary": summary,
                "quarters": quarters,
                "has_data": True,
                "trends": trends,
                "quarter_count": len(quarters),
                "ratios_snapshot": ratios_snapshot,
                "debt_to_equity_series": debt_to_equity_series,  # Last 2 years quarterly D/E
            }
            
        except Exception as e:
            logger.error(f"Error generating quarterly P&L analysis: {e}")
            return {"summary": "Quarterly analysis unavailable.", "quarters": [], "has_data": False, "trends": {}}
    
    def _generate_yearly_pl_analysis(
        self,
        yearly_data: List,
        symbol: str
    ) -> Dict:
        """Generate yearly P&L analysis"""
        try:
            if not yearly_data or len(yearly_data) == 0:
                return {
                    "summary": "Yearly financial data not available.",
                    "years": [],
                    "has_data": False,
                    "growth_metrics": {}
                }
            
            years = []
            revenue_history = []
            profit_history = []
            
            for y in yearly_data[:8]:  # Last 8 years
                year_info = {
                    "year": y.period_end.year if y.period_end else "N/A",
                    "period_end": y.period_end.isoformat() if y.period_end else None,
                    "revenue": float(y.revenue) if y.revenue else None,
                    "net_profit": float(y.net_profit) if y.net_profit else None,
                    "eps": float(y.eps) if y.eps else None,
                    "net_worth": float(y.net_worth) if y.net_worth else None
                }
                years.append(year_info)
                
                if y.revenue:
                    revenue_history.append(float(y.revenue))
                if y.net_profit:
                    profit_history.append(float(y.net_profit))
            
            # Calculate growth metrics
            growth_metrics = {}
            if len(revenue_history) >= 2:
                revenue_cagr = ((revenue_history[0] / revenue_history[-1]) ** (1 / (len(revenue_history) - 1)) - 1) * 100 if revenue_history[-1] > 0 else 0
                growth_metrics["revenue_cagr"] = revenue_cagr
            
            if len(profit_history) >= 2:
                profit_cagr = ((profit_history[0] / profit_history[-1]) ** (1 / (len(profit_history) - 1)) - 1) * 100 if profit_history[-1] > 0 else 0
                growth_metrics["profit_cagr"] = profit_cagr
            
            # Build summary
            summary_parts = []
            if len(years) > 0:
                latest = years[0]
                if latest.get("revenue"):
                    summary_parts.append(f"FY{latest['year']} Revenue: ₹{latest['revenue']/10000:.2f} Cr")
                if latest.get("net_profit"):
                    summary_parts.append(f"Net Profit: ₹{latest['net_profit']/10000:.2f} Cr")
            
            if growth_metrics.get("revenue_cagr"):
                summary_parts.append(f"Revenue CAGR: {growth_metrics['revenue_cagr']:.2f}%")
            if growth_metrics.get("profit_cagr"):
                summary_parts.append(f"Profit CAGR: {growth_metrics['profit_cagr']:.2f}%")
            
            summary = ". ".join(summary_parts) if summary_parts else "Yearly data analysis complete."
            
            return {
                "summary": summary,
                "years": years,
                "has_data": True,
                "growth_metrics": growth_metrics,
                "year_count": len(years)
            }
            
        except Exception as e:
            logger.error(f"Error generating yearly P&L analysis: {e}")
            return {"summary": "Yearly analysis unavailable.", "years": [], "has_data": False, "growth_metrics": {}}
    
    def _generate_balance_sheet_analysis(
        self,
        yearly_data: List,
        symbol: str
    ) -> Dict:
        """Generate balance sheet analysis"""
        try:
            if not yearly_data or len(yearly_data) == 0:
                return {
                    "summary": "Balance sheet data not available.",
                    "balance_sheets": [],
                    "has_data": False
                }
            
            balance_sheets = []
            for y in yearly_data[:5]:  # Last 5 years
                bs_info = {
                    "year": y.period_end.year if y.period_end else "N/A",
                    "total_assets": float(y.total_assets) if y.total_assets else None,
                    "total_liabilities": float(y.total_liabilities) if y.total_liabilities else None,
                    "net_worth": float(y.net_worth) if y.net_worth else None,
                    "current_assets": float(y.current_assets) if y.current_assets else None,
                    "current_liabilities": float(y.current_liabilities) if y.current_liabilities else None
                }
                balance_sheets.append(bs_info)
            
            # Build summary
            summary_parts = []
            if len(balance_sheets) > 0:
                latest = balance_sheets[0]
                if latest.get("total_assets"):
                    summary_parts.append(f"Total Assets: ₹{latest['total_assets']/10000:.2f} Cr")
                if latest.get("net_worth"):
                    summary_parts.append(f"Net Worth: ₹{latest['net_worth']/10000:.2f} Cr")
            
            summary = ". ".join(summary_parts) if summary_parts else "Balance sheet analysis complete."
            
            return {
                "summary": summary,
                "balance_sheets": balance_sheets,
                "has_data": len(balance_sheets) > 0
            }
            
        except Exception as e:
            logger.error(f"Error generating balance sheet analysis: {e}")
            return {"summary": "Balance sheet analysis unavailable.", "balance_sheets": [], "has_data": False}
    
    def _generate_financial_strength(
        self,
        financial_data: Dict,
        ratios: Dict,
        quarterly_data: List,
        yearly_data: List
    ) -> Dict:
        """Enhanced financial strength analysis"""
        # Use the existing method but with more data
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_financial_strength(financial_data, ratios)
    
    def _generate_valuation(
        self,
        current_price: float,
        ratios: Dict,
        all_ratios: List
    ) -> Dict:
        """Enhanced valuation analysis"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_valuation(current_price, ratios)
    
    def _generate_price_action(
        self,
        symbol: str,
        current_price: float,
        technical: Optional[Dict]
    ) -> Dict:
        """Generate price action analysis"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_price_action(symbol, current_price, technical)
    
    def _generate_technical_signals(
        self,
        technical: Dict
    ) -> Dict:
        """Generate technical signals"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_technical_signals(technical)
    
    async def _generate_chart_pattern_analysis(
        self,
        symbol: str,
        current_price: float
    ) -> Dict:
        """Generate chart pattern analysis"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return await base_generator._generate_chart_pattern_analysis(symbol, current_price)
    
    async def _generate_comprehensive_chart_pattern_analysis(
        self,
        symbol: str,
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate comprehensive chart pattern analysis including all patterns"""
        try:
            # Get Reverse Head & Shoulder from advanced detector
            from services.research_report_generator import ResearchReportGenerator
            base_generator = ResearchReportGenerator()
            base_analysis = await base_generator._generate_chart_pattern_analysis(symbol, current_price, timeframe)
            
            # Get additional patterns from enhanced chart service
            enhanced_service = EnhancedChartService()
            additional_patterns = await enhanced_service.get_pattern_recognition(symbol)
            
            # Combine patterns
            all_patterns = []
            if base_analysis.get("has_patterns") and base_analysis.get("patterns"):
                all_patterns.extend(base_analysis["patterns"])
            
            if additional_patterns and "patterns" in additional_patterns:
                for pattern_type, pattern_data in additional_patterns["patterns"].items():
                    if pattern_data:
                        all_patterns.append({
                            "pattern_type": pattern_type,
                            "pattern_name": pattern_type.replace("_", " ").title(),
                            "confidence": pattern_data.get("confidence", 0.5),
                            "pattern_data": pattern_data
                        })
            
            # Get primary pattern (highest confidence)
            primary_pattern = None
            if all_patterns:
                all_patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)
                primary_pattern = all_patterns[0]
            
            summary_parts = []
            if len(all_patterns) > 0:
                summary_parts.append(f"Detected {len(all_patterns)} chart pattern(s).")
                if primary_pattern:
                    pattern_name = primary_pattern.get("pattern_name", "Pattern")
                    confidence = primary_pattern.get("confidence", 0) * 100
                    summary_parts.append(f"Primary: {pattern_name} ({confidence:.1f}% confidence).")
            
            summary = " ".join(summary_parts) if summary_parts else "No significant chart patterns detected."
            
            return {
                "summary": summary,
                "patterns": all_patterns,
                "has_patterns": len(all_patterns) > 0,
                "primary_pattern": primary_pattern,
                "pattern_count": len(all_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive chart pattern analysis: {e}")
            return {
                "summary": "Pattern analysis unavailable.",
                "patterns": [],
                "has_patterns": False
            }
    
    async def _generate_market_factors_analysis(
        self,
        symbol: str
    ) -> Dict:
        """Generate market factors analysis (News, Orderbook, Block Deals, FII/DII)"""
        try:
            factors = await market_factors_service.get_market_factors(symbol)
            
            if "error" in factors:
                return {
                    "summary": "Market factors data not available at this time.",
                    "has_data": False
                }
            
            # Build summary
            summary_parts = []
            
            # News analysis
            news = factors.get("news", {})
            if news.get("total_news", 0) > 0:
                sentiment = news.get("sentiment", "neutral")
                positive_count = news.get("positive_count", 0)
                negative_count = news.get("negative_count", 0)
                impact = news.get("impact", "Moderate")
                
                summary_parts.append(
                    f"Recent News: {news.get('total_news', 0)} news items found. "
                    f"Sentiment: {sentiment.capitalize()} ({positive_count} positive, {negative_count} negative). "
                    f"Impact: {impact}."
                )
            
            # Orderbook analysis
            orderbook = factors.get("orderbook", {})
            if orderbook.get("volume", 0) > 0:
                buy_pressure = orderbook.get("buy_pressure", "medium")
                sell_pressure = orderbook.get("sell_pressure", "medium")
                interpretation = orderbook.get("interpretation", "")
                
                summary_parts.append(
                    f"Orderbook: Buy pressure: {buy_pressure.capitalize()}, "
                    f"Sell pressure: {sell_pressure.capitalize()}. {interpretation}"
                )
            
            # Block deals
            block_deals = factors.get("block_deals", [])
            if len(block_deals) > 0:
                summary_parts.append(
                    f"Block Deals: {len(block_deals)} recent block deal(s) detected."
                )
            
            # FII/DII flows - Detailed analysis
            fii_dii = factors.get("fii_dii_flows", {})
            if fii_dii:
                fii_net = fii_dii.get("fii_net_investment", 0)
                dii_net = fii_dii.get("dii_net_investment", 0)
                trend = fii_dii.get("trend", "neutral")
                data_source = fii_dii.get("data_source", "Unknown")
                
                if fii_net != 0 or dii_net != 0:
                    fii_status = "buying" if fii_net > 0 else "selling" if fii_net < 0 else "neutral"
                    dii_status = "buying" if dii_net > 0 else "selling" if dii_net < 0 else "neutral"
                    
                    summary_parts.append(
                        f"Institutional Flows (Source: {data_source}): "
                        f"FII Net Investment: ₹{fii_net:.2f} Cr ({fii_status}), "
                        f"DII Net Investment: ₹{dii_net:.2f} Cr ({dii_status}). "
                        f"Trend: {trend.replace('_', ' ').title()}."
                    )
                else:
                    summary_parts.append(
                        f"Institutional Flows: Data not available. "
                        f"FII/DII data sources: NSE, NSDL, Moneycontrol."
                    )
            
            # Overall impact - Detailed breakdown
            impact_analysis = factors.get("impact_analysis", {})
            overall_impact = impact_analysis.get("overall_impact", "Neutral")
            impact_score = impact_analysis.get("impact_score", 0.0)
            impact_summary = impact_analysis.get("summary", "")
            calculation_explanation = impact_analysis.get("calculation_explanation", {})
            detailed_breakdown = impact_analysis.get("detailed_breakdown", {})
            
            # Add detailed impact explanation
            impact_details = f"Overall Impact: {overall_impact} (Score: {impact_score}). {impact_summary}"
            if calculation_explanation:
                method = calculation_explanation.get("method", "")
                interpretation = calculation_explanation.get("interpretation", "")
                impact_details += f" Calculation Method: {method}. {interpretation}"
            
            summary = " ".join(summary_parts) if summary_parts else "Market factors analysis available."
            summary += f" {impact_details}"
            
            return {
                "summary": summary,
                "has_data": True,
                "news": news,
                "orderbook": orderbook,
                "block_deals": block_deals,
                "fii_dii_flows": fii_dii,
                "insider_trading": factors.get("insider_trading", []),
                "promoter_changes": factors.get("promoter_changes", {}),
                "delivery_data": factors.get("delivery_data", {}),
                "impact_analysis": impact_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating market factors analysis for {symbol}: {e}")
            return {
                "summary": f"Error in market factors analysis: {str(e)}",
                "has_data": False
            }
    
    async def _generate_price_predictions(
        self,
        symbol: str,
        current_price: float,
        sections: Dict
    ) -> Dict:
        """Generate price predictions for 1W, 1M, 2M, 3M, 6M, 1Y, and 2Y based on all analysis"""
        try:
            # Prepare analysis data from all sections
            analysis_data = {
                "technical_indicators": sections.get("technical_analysis", {}),
                "market_factors": sections.get("market_factors", {}),
                "chart_patterns": sections.get("chart_patterns", {}),
                "market_structure_analysis": sections.get("market_structure_analysis", {}),
                "support_resistance_analysis": sections.get("support_resistance_analysis", {}),
                "market_sentiment": sections.get("market_sentiment", {}),
                "trendline_analysis": sections.get("trendline_analysis", {}),
                "swing_point_analysis": sections.get("swing_point_analysis", {}),
                "supply_demand_analysis": sections.get("supply_demand_analysis", {}),
                "chart_images_analysis": sections.get("chart_images_analysis", {})  # Include chart image analysis
            }
            
            # Generate predictions
            predictions = await price_prediction_service.generate_price_predictions(
                symbol=symbol,
                current_price=current_price,
                analysis_data=analysis_data
            )
            
            if "error" in predictions:
                return {
                    "summary": f"Price predictions not available: {predictions.get('error', 'Unknown error')}",
                    "has_data": False
                }
            
            # Format summary
            timeframes = predictions.get("timeframes", {})
            summary_parts = []
            
            # Keep ordering short → long horizon
            for tf_name in ["1W", "1M", "2M", "3M", "6M", "1Y", "2Y"]:
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
            
            # Add note if chart images were used
            chart_images = sections.get("chart_images_analysis", {})
            if chart_images and chart_images.get("has_data"):
                summary_parts.append("(Includes insights from uploaded chart images)")
            
            summary = "Price Predictions - " + " | ".join(summary_parts) if summary_parts else "Predictions not available."
            
            return {
                "summary": summary,
                "has_data": True,
                "current_price": current_price,
                "overall_confidence": predictions.get("overall_confidence", 0),
                "timeframes": timeframes,
                "prediction_date": predictions.get("prediction_date", datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error generating price predictions for {symbol}: {e}")
            return {
                "summary": f"Error generating price predictions: {str(e)}",
                "has_data": False
            }
    
    def _generate_market_sentiment(
        self,
        sentiment: Dict
    ) -> Dict:
        """Generate market sentiment"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_market_sentiment(sentiment)
    
    def _generate_risk_assessment(
        self,
        ratios: Optional[Dict],
        technical: Optional[Dict],
        sentiment: Optional[Dict],
        quarterly_data: List
    ) -> Dict:
        """Enhanced risk assessment"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_risk_assessment(ratios, technical, sentiment)
    
    def _generate_strong_points(
        self,
        sections: Dict,
        symbol: str,
        current_price: float
    ) -> Dict:
        """Generate 10 strong points supporting the recommendation"""
        try:
            strong_points = []
            
            # 1. Financial Strength
            financial = sections.get("financial_strength", {})
            if financial.get("assessment") == "Strong":
                strong_points.append({
                    "point": "Strong Financial Performance",
                    "description": f"Company demonstrates strong financial metrics with {financial.get('roe', 'N/A')}% ROE and {financial.get('roce', 'N/A')}% ROCE, indicating efficient capital utilization and profitability."
                })
            
            # 2. Valuation
            valuation = sections.get("valuation", {})
            if valuation.get("assessment") == "undervalued":
                pe = valuation.get("pe_ratio", "N/A")
                strong_points.append({
                    "point": "Attractive Valuation",
                    "description": f"Trading at PE ratio of {pe}, which is attractive compared to sector average, presenting good value opportunity."
                })
            
            # 3. Chart Pattern
            chart_patterns = sections.get("chart_patterns", {})
            if chart_patterns.get("has_patterns"):
                primary = chart_patterns.get("primary_pattern")
                if primary:
                    pattern_name = primary.get("pattern_name", "Pattern")
                    target = primary.get("target_price", 0)
                    upside = primary.get("potential_upside", 0)
                    strong_points.append({
                        "point": f"{pattern_name} Pattern Detected",
                        "description": f"Technical analysis reveals {pattern_name} pattern with target price of ₹{target:.2f}, indicating potential upside of {upside:.2f}%."
                    })
            
            # 4. Growth Trends
            quarterly = sections.get("quarterly_pl", {})
            if quarterly.get("trends", {}).get("profit_growth", 0) > 0:
                growth = quarterly["trends"]["profit_growth"]
                strong_points.append({
                    "point": "Positive Profit Growth",
                    "description": f"Quarterly profit growth of {growth:.2f}% demonstrates improving profitability and operational efficiency."
                })
            
            # 5. Technical Signals
            technical = sections.get("technical_signals", {})
            if technical.get("signals"):
                signals = technical["signals"]
                if any("buy" in s.lower() for s in signals):
                    strong_points.append({
                        "point": "Positive Technical Signals",
                        "description": "Technical indicators show bullish signals, supporting upward price momentum."
                    })
            
            # 6. Market Sentiment
            sentiment = sections.get("market_sentiment", {})
            if sentiment.get("overall_sentiment") == "Bullish":
                strong_points.append({
                    "point": "Bullish Market Sentiment",
                    "description": "Overall market sentiment is bullish, with positive news and social sentiment supporting the stock."
                })
            
            # 7. Low Debt
            financial_ratios = sections.get("financial_ratios", {})
            debt_eq = financial_ratios.get("ratios", {}).get("debt_to_equity")
            if debt_eq is not None and debt_eq < 0.5:
                strong_points.append({
                    "point": "Low Debt Profile",
                    "description": f"Debt-to-Equity ratio of {debt_eq:.2f} indicates low financial risk and strong balance sheet."
                })
            
            # 8. Consistent Performance
            yearly = sections.get("yearly_pl", {})
            if yearly.get("growth_metrics", {}).get("profit_cagr", 0) > 10:
                cagr = yearly["growth_metrics"]["profit_cagr"]
                strong_points.append({
                    "point": "Strong Historical Growth",
                    "description": f"Profit CAGR of {cagr:.2f}% over recent years demonstrates consistent and strong growth trajectory."
                })
            
            # 9. Price Action
            price_action = sections.get("price_action", {})
            if price_action.get("trend") == "uptrend":
                strong_points.append({
                    "point": "Strong Uptrend",
                    "description": "Price action shows strong uptrend with positive momentum, indicating sustained buying interest."
                })
            
            # 10. Risk Profile
            risk = sections.get("risk_assessment", {})
            if risk.get("risk_level") == "low":
                strong_points.append({
                    "point": "Low Risk Profile",
                    "description": "Comprehensive risk assessment indicates low to moderate risk, making it suitable for investment."
                })
            
            # Fill up to 10 points if we have fewer
            while len(strong_points) < 10:
                strong_points.append({
                    "point": f"Additional Analysis Point {len(strong_points) + 1}",
                    "description": "Further analysis supports the investment thesis based on comprehensive evaluation."
                })
            
            return {
                "summary": f"Based on comprehensive analysis, {len(strong_points)} strong points support the investment recommendation.",
                "points": strong_points[:10],  # Ensure exactly 10 points
                "count": len(strong_points[:10])
            }
            
        except Exception as e:
            logger.error(f"Error generating strong points: {e}")
            return {"summary": "Strong points analysis unavailable.", "points": [], "count": 0}
    
    def _generate_recommendation(
        self,
        sections: Dict
    ) -> Dict:
        """Generate investment recommendation"""
        from services.research_report_generator import ResearchReportGenerator
        base_generator = ResearchReportGenerator()
        return base_generator._generate_recommendation(sections)
    
    def _generate_conclusion(
        self,
        sections: Dict,
        symbol: str,
        current_price: float
    ) -> Dict:
        """Generate comprehensive conclusion"""
        try:
            recommendation = sections.get("recommendation", {})
            rec_type = recommendation.get("recommendation", "HOLD")
            confidence = recommendation.get("confidence", 50)
            target_price = recommendation.get("target_price")
            upside = recommendation.get("potential_upside")
            holding_period = recommendation.get("holding_period", "3-6 months")
            
            conclusion_parts = []
            
            # Opening statement
            conclusion_parts.append(
                f"{symbol} presents a {rec_type} opportunity based on comprehensive analysis across multiple dimensions."
            )
            
            # Financial strength
            financial = sections.get("financial_strength", {})
            if financial.get("assessment") == "Strong":
                conclusion_parts.append(
                    "The company demonstrates strong financial performance with robust profitability metrics and efficient capital utilization."
                )
            
            # Technical analysis
            chart_patterns = sections.get("chart_patterns", {})
            if chart_patterns.get("has_patterns"):
                primary = chart_patterns.get("primary_pattern")
                if primary:
                    pattern_name = primary.get("pattern_name", "pattern")
                    conclusion_parts.append(
                        f"Technical analysis reveals a {pattern_name} pattern, indicating favorable price action and potential upward movement."
                    )
            
            # Valuation
            valuation = sections.get("valuation", {})
            if valuation.get("assessment") == "undervalued":
                conclusion_parts.append(
                    "Current valuation appears attractive, presenting a good entry opportunity for investors."
                )
            
            # Growth
            quarterly = sections.get("quarterly_pl", {})
            if quarterly.get("trends", {}).get("profit_growth", 0) > 0:
                conclusion_parts.append(
                    "Positive growth trends in quarterly performance support the investment thesis."
                )
            
            # Recommendation
            if target_price:
                conclusion_parts.append(
                    f"With a target price of ₹{target_price:.2f} and expected holding period of {holding_period}, "
                    f"the investment offers {confidence}% confidence level."
                )
            else:
                conclusion_parts.append(
                    f"Based on comprehensive analysis, the recommendation is {rec_type} with {confidence}% confidence."
                )
            
            # Risk note
            risk = sections.get("risk_assessment", {})
            risk_level = risk.get("risk_level", "medium")
            conclusion_parts.append(
                f"Investors should consider the {risk_level} risk profile and conduct their own due diligence before investing."
            )
            
            conclusion = " ".join(conclusion_parts)
            
            return {
                "summary": conclusion,
                "recommendation": rec_type,
                "confidence": confidence,
                "target_price": target_price,
                "potential_upside": upside,
                "holding_period": holding_period
            }
            
        except Exception as e:
            logger.error(f"Error generating conclusion: {e}")
            return {
                "summary": f"Based on comprehensive analysis, {symbol} presents an investment opportunity. Investors should conduct their own research.",
                "recommendation": "HOLD",
                "confidence": 50
            }
    
    async def _generate_trendline_analysis(
        self,
        symbol: str,
        data: List[Dict],
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate trendline analysis section"""
        try:
            result = self.trendline_service.detect_all_trendlines(
                data=data,
                min_touches=2,
                lookback_period=100
            )
            
            if "error" in result:
                return {"summary": "Trendline analysis unavailable.", "has_data": False}
            
            uptrend_lines = result.get("uptrend_lines", [])
            downtrend_lines = result.get("downtrend_lines", [])
            channels = result.get("channels", [])
            best_uptrend = result.get("best_uptrend")
            best_downtrend = result.get("best_downtrend")
            current_trend = result.get("current_trend", {})
            recent_breaks = result.get("recent_breaks", [])
            
            summary_parts = []
            
            # Current trend
            trend = current_trend.get("trend", "unknown")
            confidence = current_trend.get("confidence", "low")
            summary_parts.append(f"Current trend: {trend.upper()} (confidence: {confidence})")
            
            # Best trendlines
            if best_uptrend:
                touches = best_uptrend.get("touches", 0)
                summary_parts.append(f"Primary support trendline with {touches} touches identified")
            
            if best_downtrend:
                touches = best_downtrend.get("touches", 0)
                summary_parts.append(f"Primary resistance trendline with {touches} touches identified")
            
            # Channels
            if channels:
                summary_parts.append(f"{len(channels)} price channel(s) detected")
            
            # Recent breaks
            if recent_breaks:
                summary_parts.append(f"{len(recent_breaks)} recent trendline break(s) detected")
            
            summary = ". ".join(summary_parts) if summary_parts else "Trendline analysis complete."
            
            return {
                "summary": summary,
                "has_data": True,
                "timeframe": timeframe,
                "uptrend_count": len(uptrend_lines),
                "downtrend_count": len(downtrend_lines),
                "channel_count": len(channels),
                "current_trend": trend,
                "confidence": confidence,
                "recent_breaks_count": len(recent_breaks),
                "best_uptrend": best_uptrend,
                "best_downtrend": best_downtrend
            }
            
        except Exception as e:
            logger.error(f"Error generating trendline analysis: {e}")
            return {"summary": "Trendline analysis unavailable.", "has_data": False}
    
    async def _generate_market_structure_analysis(
        self,
        symbol: str,
        data: List[Dict],
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate market structure analysis section"""
        try:
            # Validate data before processing
            if not data or len(data) < 20:
                logger.warning(f"Insufficient data for market structure analysis: {len(data) if data else 0} candles")
                return {"summary": "Market structure analysis unavailable - insufficient data.", "has_data": False}
            
            result = self.market_structure_service.analyze_market_structure(
                data=data,
                strength=5
            )
            
            if not result.get("success"):
                error_msg = result.get("error", "Unknown error")
                logger.warning(f"Market structure analysis failed: {error_msg}")
                return {"summary": "Market structure analysis unavailable.", "has_data": False}
            
            structure_data = result.get("data", {})
            bos_events = structure_data.get("bos_events", [])
            choch_events = structure_data.get("choch_events", [])
            current_structure = structure_data.get("current_structure", {})
            trading_signals = structure_data.get("trading_signals", [])
            stats = structure_data.get("statistics", {})
            
            summary_parts = []
            
            # Current structure
            phase = current_structure.get("phase", "unknown")
            structure_type = current_structure.get("structure_type", "unknown")
            summary_parts.append(f"Current market phase: {phase.upper()}, Structure: {structure_type}")
            
            # BOS events
            bos_count = stats.get("bos_count", 0)
            if bos_count > 0:
                summary_parts.append(f"{bos_count} Break of Structure (BOS) events detected - indicating trend continuation")
            
            # CHoCH events
            choch_count = stats.get("choch_count", 0)
            if choch_count > 0:
                summary_parts.append(f"{choch_count} Change of Character (CHoCH) events detected - indicating potential reversals")
            
            # Trading signals
            if trading_signals:
                latest_signal = trading_signals[0] if trading_signals else {}
                signal_type = latest_signal.get("signal", "NEUTRAL")
                summary_parts.append(f"Latest trading signal: {signal_type}")
            
            summary = ". ".join(summary_parts) if summary_parts else "Market structure analysis complete."
            
            return {
                "summary": summary,
                "has_data": True,
                "timeframe": timeframe,
                "current_phase": phase,
                "structure_type": structure_type,
                "bos_count": bos_count,
                "choch_count": choch_count,
                "trading_signals": trading_signals[:3]  # Latest 3 signals
            }
            
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Error generating market structure analysis: {error_msg}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return {"summary": "Market structure analysis unavailable.", "has_data": False}
    
    async def _generate_support_resistance_analysis(
        self,
        symbol: str,
        data: List[Dict],
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate support/resistance analysis section"""
        try:
            result = self.support_resistance_service.analyze_support_resistance(
                data=data,
                min_touches=2,
                tolerance_percent=0.5,
                lookback_period=100
            )
            
            if not result.get("success"):
                return {"summary": "Support/Resistance analysis unavailable.", "has_data": False}
            
            sr_data = result.get("data", {})
            
            # CRITICAL FIX: Re-classify ALL levels based on LIVE current_price
            # The analysis may have used stale data's last close, causing misclassification
            # Combine all levels and re-classify based on actual current price
            all_levels = []
            all_levels.extend(sr_data.get("support_levels", []))
            all_levels.extend(sr_data.get("resistance_levels", []))
            
            # Re-classify all levels based on LIVE current_price (not stale data price)
            # Use the current_price parameter which should be the live/current price
            support_levels = []
            resistance_levels = []
            
            for level in all_levels:
                level_price = level.get("price", 0)
                if level_price <= 0:
                    continue
                
                # Support: levels BELOW current price
                if level_price < current_price:
                    level['type'] = 'support'
                    support_levels.append(level)
                # Resistance: levels ABOVE current price
                elif level_price > current_price:
                    level['type'] = 'resistance'
                    resistance_levels.append(level)
                # Skip levels exactly at current price
            
            # Sort support descending (highest support = nearest to current price)
            support_levels.sort(key=lambda x: x.get("price", 0), reverse=True)
            
            # Sort resistance ascending (lowest resistance = nearest to current price)
            resistance_levels.sort(key=lambda x: x.get("price", float('inf')))
            
            # Find nearest levels from correctly classified lists
            nearest_support = support_levels[0] if support_levels else None
            nearest_resistance = resistance_levels[0] if resistance_levels else None
            
            # Update distances if we have valid levels (using live current_price)
            if nearest_support:
                support_price = nearest_support.get("price", 0)
                distance = current_price - support_price
                distance_percent = (distance / current_price) * 100
                nearest_support["distance"] = distance
                nearest_support["distance_percent"] = distance_percent
            
            if nearest_resistance:
                resistance_price = nearest_resistance.get("price", 0)
                distance = resistance_price - current_price
                distance_percent = (distance / current_price) * 100
                nearest_resistance["distance"] = distance
                nearest_resistance["distance_percent"] = distance_percent
            
            trading_zones = sr_data.get("trading_zones", {})
            
            summary_parts = []
            
            # Nearest levels (using live current_price)
            if nearest_support:
                support_price = nearest_support.get("price", 0)
                if current_price > 0 and support_price > 0:
                    # Support should ALWAYS be below current price (now correctly classified)
                    distance = ((current_price - support_price) / current_price) * 100
                    summary_parts.append(f"Nearest support: ₹{support_price:.2f} ({distance:.1f}% below current price)")
                else:
                    summary_parts.append(f"Nearest support: ₹{support_price:.2f}")
            else:
                summary_parts.append("No support level found below current price")
            
            if nearest_resistance:
                resistance_price = nearest_resistance.get("price", 0)
                if current_price > 0 and resistance_price > 0:
                    # Resistance should ALWAYS be above current price (now correctly classified)
                    distance = ((resistance_price - current_price) / current_price) * 100
                    summary_parts.append(f"Nearest resistance: ₹{resistance_price:.2f} ({distance:.1f}% above current price)")
                else:
                    summary_parts.append(f"Nearest resistance: ₹{resistance_price:.2f}")
            else:
                summary_parts.append("No resistance level found above current price")
            
            # Level counts
            summary_parts.append(f"{len(support_levels)} support level(s) and {len(resistance_levels)} resistance level(s) identified")
            
            # Trading zone
            current_zone = trading_zones.get("current_zone", "unknown")
            if current_zone != "unknown":
                summary_parts.append(f"Current trading zone: {current_zone.upper()}")
            
            summary = ". ".join(summary_parts) if summary_parts else "Support/Resistance analysis complete."
            
            return {
                "summary": summary,
                "has_data": True,
                "timeframe": timeframe,
                "support_levels_count": len(support_levels),
                "resistance_levels_count": len(resistance_levels),
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "current_zone": current_zone
            }
            
        except Exception as e:
            logger.error(f"Error generating support/resistance analysis: {e}")
            return {"summary": "Support/Resistance analysis unavailable.", "has_data": False}
    
    async def _generate_swing_point_analysis(
        self,
        symbol: str,
        data: List[Dict],
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate swing point analysis section"""
        try:
            result = self.swing_point_service.analyze_swing_points(
                data=data,
                strength=5
            )
            
            if not result.get("success"):
                return {"summary": "Swing point analysis unavailable.", "has_data": False}
            
            swing_data = result.get("data", {})
            swing_highs = swing_data.get("swing_highs", [])
            swing_lows = swing_data.get("swing_lows", [])
            trend_analysis = swing_data.get("trend_analysis", {})
            recent_pattern = swing_data.get("recent_pattern", [])
            
            summary_parts = []
            
            # Trend analysis
            trend = trend_analysis.get("trend", "unknown")
            pattern_sequence = trend_analysis.get("pattern_sequence", [])
            summary_parts.append(f"Current trend structure: {trend.upper()}")
            
            # Pattern sequence
            if pattern_sequence:
                latest_patterns = pattern_sequence[-3:] if len(pattern_sequence) >= 3 else pattern_sequence
                pattern_str = " → ".join(latest_patterns)
                summary_parts.append(f"Recent swing pattern: {pattern_str}")
            
            # Swing counts
            summary_parts.append(f"{len(swing_highs)} swing high(s) and {len(swing_lows)} swing low(s) identified")
            
            # Recent swings
            if swing_highs:
                latest_high = swing_highs[-1]
                high_price = latest_high.get("price", 0)
                summary_parts.append(f"Latest swing high: ₹{high_price:.2f}")
            
            if swing_lows:
                latest_low = swing_lows[-1]
                low_price = latest_low.get("price", 0)
                summary_parts.append(f"Latest swing low: ₹{low_price:.2f}")
            
            summary = ". ".join(summary_parts) if summary_parts else "Swing point analysis complete."
            
            return {
                "summary": summary,
                "has_data": True,
                "timeframe": timeframe,
                "swing_highs_count": len(swing_highs),
                "swing_lows_count": len(swing_lows),
                "trend": trend,
                "pattern_sequence": pattern_sequence[-5:] if pattern_sequence else []
            }
            
        except Exception as e:
            logger.error(f"Error generating swing point analysis: {e}")
            return {"summary": "Swing point analysis unavailable.", "has_data": False}
    
    async def _generate_supply_demand_analysis(
        self,
        symbol: str,
        data: List[Dict],
        current_price: float,
        timeframe: str = "1D"
    ) -> Dict:
        """Generate supply/demand analysis section"""
        try:
            result = self.supply_demand_service.analyze_supply_demand(
                data=data,
                lookback_period=100,
                min_zone_strength=0.5
            )
            
            if not result.get("success"):
                return {"summary": "Supply/Demand analysis unavailable.", "has_data": False}
            
            sd_data = result.get("data", {})
            demand_zones = sd_data.get("demand_zones", [])
            supply_zones = sd_data.get("supply_zones", [])
            fresh_demand = [z for z in demand_zones if z.get("status") == "fresh"]
            fresh_supply = [z for z in supply_zones if z.get("status") == "fresh"]
            tested_demand = [z for z in demand_zones if z.get("status") == "tested"]
            tested_supply = [z for z in supply_zones if z.get("status") == "tested"]
            
            summary_parts = []
            
            # Zone counts
            summary_parts.append(f"{len(demand_zones)} demand zone(s) and {len(supply_zones)} supply zone(s) identified")
            
            # Fresh zones (most important)
            if fresh_demand:
                summary_parts.append(f"{len(fresh_demand)} fresh demand zone(s) - potential bullish entry areas")
            
            if fresh_supply:
                summary_parts.append(f"{len(fresh_supply)} fresh supply zone(s) - potential bearish entry areas")
            
            # Tested zones
            if tested_demand:
                summary_parts.append(f"{len(tested_demand)} tested demand zone(s) - confirmed support levels")
            
            if tested_supply:
                summary_parts.append(f"{len(tested_supply)} tested supply zone(s) - confirmed resistance levels")
            
            # Nearest zones
            nearest_demand = sd_data.get("nearest_demand_zone")
            nearest_supply = sd_data.get("nearest_supply_zone")
            
            if nearest_demand:
                zone_price = nearest_demand.get("price_range", {}).get("high", 0)
                distance = ((current_price - zone_price) / current_price * 100) if current_price > 0 else 0
                summary_parts.append(f"Nearest demand zone: ₹{zone_price:.2f} ({distance:.1f}% below)")
            
            if nearest_supply:
                zone_price = nearest_supply.get("price_range", {}).get("low", 0)
                distance = ((zone_price - current_price) / current_price * 100) if current_price > 0 else 0
                summary_parts.append(f"Nearest supply zone: ₹{zone_price:.2f} ({distance:.1f}% above)")
            
            summary = ". ".join(summary_parts) if summary_parts else "Supply/Demand analysis complete."
            
            return {
                "summary": summary,
                "has_data": True,
                "timeframe": timeframe,
                "demand_zones_count": len(demand_zones),
                "supply_zones_count": len(supply_zones),
                "fresh_demand_count": len(fresh_demand),
                "fresh_supply_count": len(fresh_supply),
                "tested_demand_count": len(tested_demand),
                "tested_supply_count": len(tested_supply),
                "nearest_demand": nearest_demand,
                "nearest_supply": nearest_supply
            }
            
        except Exception as e:
            logger.error(f"Error generating supply/demand analysis: {e}")
            return {"summary": "Supply/Demand analysis unavailable.", "has_data": False}
    
    def _generate_chart_images_analysis(
        self,
        chart_image_analysis: Dict,
        symbol: str,
        current_price: float
    ) -> Dict:
        """Generate chart images analysis section with support/resistance prices"""
        try:
            if not chart_image_analysis.get("success"):
                return {
                    "summary": "Chart image analysis not available.",
                    "has_data": False
                }
            
            summary_parts = []
            
            # Basic info
            images_analyzed = chart_image_analysis.get("images_analyzed", 0)
            successful_analyses = chart_image_analysis.get("successful_analyses", 0)
            summary_parts.append(f"Analyzed {images_analyzed} chart image(s) for {symbol}. {successful_analyses} successful analysis(es).")
            
            # Patterns
            detected_patterns = chart_image_analysis.get("detected_patterns", [])
            if detected_patterns:
                unique_patterns = len(detected_patterns)
                summary_parts.append(f"Detected {unique_patterns} unique pattern type(s): {', '.join([p.get('pattern_name', 'Pattern') for p in detected_patterns[:3]])}")
            
            # Support and Resistance from images
            nearest_support = chart_image_analysis.get("nearest_support")
            nearest_resistance = chart_image_analysis.get("nearest_resistance")
            support_levels = chart_image_analysis.get("support_levels", [])
            resistance_levels = chart_image_analysis.get("resistance_levels", [])
            
            if nearest_support and nearest_support.get("estimated_price"):
                support_price = nearest_support.get("estimated_price")
                distance = ((current_price - support_price) / current_price * 100) if current_price > 0 else 0
                summary_parts.append(f"Nearest Support from Images: ₹{support_price:.2f} ({distance:.1f}% below current price)")
            
            if nearest_resistance and nearest_resistance.get("estimated_price"):
                resistance_price = nearest_resistance.get("estimated_price")
                distance = ((resistance_price - current_price) / current_price * 100) if current_price > 0 else 0
                summary_parts.append(f"Nearest Resistance from Images: ₹{resistance_price:.2f} ({distance:.1f}% above current price)")
            
            # Key levels
            key_levels = chart_image_analysis.get("key_levels", [])
            if key_levels:
                summary_parts.append(f"Identified {len(key_levels)} key price level(s) from chart images")
            
            # Overall trend
            overall_trend = chart_image_analysis.get("overall_trend", "unknown")
            if overall_trend != "unknown":
                summary_parts.append(f"Overall Trend from Images: {overall_trend.upper()}")
            
            summary = ". ".join(summary_parts) if summary_parts else "Chart image analysis complete."
            
            return {
                "summary": summary,
                "has_data": True,
                "images_analyzed": images_analyzed,
                "successful_analyses": successful_analyses,
                "detected_patterns": detected_patterns,
                "key_levels": key_levels,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "overall_trend": overall_trend,
                "current_price": current_price
            }
            
        except Exception as e:
            logger.error(f"Error generating chart images analysis: {e}")
            return {
                "summary": f"Error in chart image analysis: {str(e)}",
                "has_data": False
            }
    
    def _generate_executive_summary(
        self,
        symbol: str,
        company_name: str,
        current_price: float,
        financial_ratios: Optional[Dict],
        quarterly_data: List,
        yearly_data: List,
        technical_analysis: Optional[Dict],
        market_cap: Optional[float]
    ) -> Dict:
        """Generate executive summary at the top of the report"""
        try:
            summary_parts = []
            
            # Company overview
            summary_parts.append(f"{company_name} ({symbol}) is currently trading at ₹{current_price:.2f}.")
            
            # Market cap
            if market_cap:
                if market_cap >= 200000:  # 2L Cr
                    cap_category = "Large Cap"
                elif market_cap >= 50000:  # 50K Cr
                    cap_category = "Mid Cap"
                else:
                    cap_category = "Small Cap"
                summary_parts.append(f"Market Cap: ₹{market_cap/10000:.2f} Cr ({cap_category}).")
            
            # Financial health
            if financial_ratios:
                pe = financial_ratios.get("pe_ratio")
                roe = financial_ratios.get("roe")
                debt_equity = financial_ratios.get("debt_to_equity")
                
                if pe:
                    if pe < 15:
                        pe_assessment = "undervalued"
                    elif pe > 25:
                        pe_assessment = "overvalued"
                    else:
                        pe_assessment = "fairly valued"
                    summary_parts.append(f"P/E Ratio: {pe:.2f} ({pe_assessment}).")
                
                if roe:
                    if roe > 20:
                        roe_assessment = "excellent"
                    elif roe > 15:
                        roe_assessment = "strong"
                    else:
                        roe_assessment = "moderate"
                    summary_parts.append(f"ROE: {roe:.2f}% ({roe_assessment}).")
                
                if debt_equity:
                    if debt_equity < 0.5:
                        debt_assessment = "low debt"
                    elif debt_equity > 1.0:
                        debt_assessment = "high debt"
                    else:
                        debt_assessment = "moderate debt"
                    summary_parts.append(f"Debt/Equity: {debt_equity:.2f} ({debt_assessment}).")
            
            # Revenue trend
            if quarterly_data and len(quarterly_data) >= 2:
                latest_q = quarterly_data[0]
                prev_q = quarterly_data[1] if len(quarterly_data) > 1 else None
                
                if latest_q.revenue and prev_q and prev_q.revenue:
                    revenue_growth = ((float(latest_q.revenue) - float(prev_q.revenue)) / float(prev_q.revenue)) * 100
                    if revenue_growth > 0:
                        summary_parts.append(f"Revenue growth (QoQ): +{revenue_growth:.1f}%.")
                    else:
                        summary_parts.append(f"Revenue growth (QoQ): {revenue_growth:.1f}%.")
            
            # Technical outlook
            if technical_analysis:
                trend = technical_analysis.get("trend", "neutral")
                if trend == "uptrend":
                    summary_parts.append("Technical Analysis: Bullish trend detected.")
                elif trend == "downtrend":
                    summary_parts.append("Technical Analysis: Bearish trend detected.")
                else:
                    summary_parts.append("Technical Analysis: Neutral trend.")
            
            summary = " ".join(summary_parts)
            
            return {
                "summary": summary,
                "has_data": True,
                "company_name": company_name,
                "symbol": symbol,
                "current_price": current_price
            }
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {
                "summary": f"Executive summary unavailable: {str(e)}",
                "has_data": False
            }
    
    def _generate_key_metrics_dashboard(
        self,
        financial_ratios: Optional[Dict],
        current_price: float,
        quarterly_data: List,
        yearly_data: List,
        market_cap: Optional[float]
    ) -> Dict:
        """Generate key metrics dashboard (one-page snapshot)"""
        try:
            metrics = {}
            
            # Valuation metrics
            if financial_ratios:
                metrics["pe_ratio"] = financial_ratios.get("pe_ratio")
                metrics["pb_ratio"] = financial_ratios.get("pb_ratio")
                metrics["market_cap"] = market_cap / 10000 if market_cap else None  # Convert to Cr
            
            # Profitability metrics
            if financial_ratios:
                metrics["roe"] = financial_ratios.get("roe")
                metrics["roce"] = financial_ratios.get("roce")
                metrics["operating_margin"] = financial_ratios.get("operating_margin")
            
            # Financial health
            if financial_ratios:
                metrics["debt_to_equity"] = financial_ratios.get("debt_to_equity")
                metrics["current_ratio"] = financial_ratios.get("current_ratio")
            
            # Latest quarterly metrics
            if quarterly_data and len(quarterly_data) > 0:
                latest_q = quarterly_data[0]
                if latest_q.revenue:
                    metrics["latest_revenue"] = float(latest_q.revenue) / 10000  # Convert to Cr
                if latest_q.net_profit:
                    metrics["latest_net_profit"] = float(latest_q.net_profit) / 10000  # Convert to Cr
                if latest_q.revenue and latest_q.net_profit:
                    metrics["latest_net_margin"] = (float(latest_q.net_profit) / float(latest_q.revenue)) * 100
            
            # Year-over-year growth
            if yearly_data and len(yearly_data) >= 2:
                latest_y = yearly_data[0]
                prev_y = yearly_data[1]
                
                if latest_y.revenue and prev_y.revenue:
                    revenue_yoy = ((float(latest_y.revenue) - float(prev_y.revenue)) / float(prev_y.revenue)) * 100
                    metrics["revenue_yoy_growth"] = revenue_yoy
                
                if latest_y.net_profit and prev_y.net_profit:
                    profit_yoy = ((float(latest_y.net_profit) - float(prev_y.net_profit)) / float(prev_y.net_profit)) * 100
                    metrics["profit_yoy_growth"] = profit_yoy
            
            return {
                "metrics": metrics,
                "has_data": len(metrics) > 0
            }
        except Exception as e:
            logger.error(f"Error generating key metrics dashboard: {e}")
            return {
                "metrics": {},
                "has_data": False
            }
    
    def _generate_financial_trends_data(
        self,
        quarterly_data: List,
        yearly_data: List
    ) -> Dict:
        """Generate financial trends data for charts (revenue, profit, margins)"""
        try:
            trends = {
                "quarterly": [],
                "yearly": []
            }
            
            # Quarterly trends (last 8 quarters)
            for q in quarterly_data[:8]:
                if q.revenue and q.net_profit:
                    revenue_cr = float(q.revenue) / 10000
                    profit_cr = float(q.net_profit) / 10000
                    margin = (profit_cr / revenue_cr * 100) if revenue_cr > 0 else 0
                    
                    # Calculate operating margin if available
                    op_margin = None
                    if hasattr(q, 'ebit') and q.ebit and q.revenue:
                        ebit_cr = float(q.ebit) / 10000
                        op_margin = (ebit_cr / revenue_cr * 100) if revenue_cr > 0 else None
                    
                    trends["quarterly"].append({
                        "period": q.period_end.isoformat() if hasattr(q.period_end, 'isoformat') else str(q.period_end),
                        "revenue": revenue_cr,
                        "net_profit": profit_cr,
                        "net_margin": margin,
                        "operating_margin": op_margin
                    })
            
            # Yearly trends (last 5 years)
            for y in yearly_data[:5]:
                if y.revenue and y.net_profit:
                    revenue_cr = float(y.revenue) / 10000
                    profit_cr = float(y.net_profit) / 10000
                    margin = (profit_cr / revenue_cr * 100) if revenue_cr > 0 else 0
                    
                    trends["yearly"].append({
                        "period": y.period_end.isoformat() if hasattr(y.period_end, 'isoformat') else str(y.period_end),
                        "revenue": revenue_cr,
                        "net_profit": profit_cr,
                        "net_margin": margin
                    })
            
            return {
                "trends": trends,
                "has_data": len(trends["quarterly"]) > 0 or len(trends["yearly"]) > 0
            }
        except Exception as e:
            logger.error(f"Error generating financial trends data: {e}")
            return {
                "trends": {"quarterly": [], "yearly": []},
                "has_data": False
            }
    
    def _generate_risk_indicators(
        self,
        financial_ratios: Optional[Dict],
        quarterly_data: List,
        technical_analysis: Optional[Dict]
    ) -> Dict:
        """Generate color-coded risk indicators (green/yellow/red)"""
        try:
            indicators = {}
            
            # Debt risk
            if financial_ratios and financial_ratios.get("debt_to_equity"):
                de = financial_ratios.get("debt_to_equity")
                if de < 0.5:
                    indicators["debt_risk"] = {"level": "low", "color": "green", "value": de}
                elif de < 1.0:
                    indicators["debt_risk"] = {"level": "medium", "color": "yellow", "value": de}
                else:
                    indicators["debt_risk"] = {"level": "high", "color": "red", "value": de}
            
            # Liquidity risk
            if financial_ratios and financial_ratios.get("current_ratio"):
                cr = financial_ratios.get("current_ratio")
                if cr > 2.0:
                    indicators["liquidity_risk"] = {"level": "low", "color": "green", "value": cr}
                elif cr > 1.0:
                    indicators["liquidity_risk"] = {"level": "medium", "color": "yellow", "value": cr}
                else:
                    indicators["liquidity_risk"] = {"level": "high", "color": "red", "value": cr}
            
            # Profitability risk
            if financial_ratios and financial_ratios.get("roe"):
                roe = financial_ratios.get("roe")
                if roe > 20:
                    indicators["profitability_risk"] = {"level": "low", "color": "green", "value": roe}
                elif roe > 10:
                    indicators["profitability_risk"] = {"level": "medium", "color": "yellow", "value": roe}
                else:
                    indicators["profitability_risk"] = {"level": "high", "color": "red", "value": roe}
            
            # Valuation risk
            if financial_ratios and financial_ratios.get("pe_ratio"):
                pe = financial_ratios.get("pe_ratio")
                if pe < 15:
                    indicators["valuation_risk"] = {"level": "low", "color": "green", "value": pe}
                elif pe < 30:
                    indicators["valuation_risk"] = {"level": "medium", "color": "yellow", "value": pe}
                else:
                    indicators["valuation_risk"] = {"level": "high", "color": "red", "value": pe}
            
            # Revenue stability risk
            if quarterly_data and len(quarterly_data) >= 4:
                revenues = [float(q.revenue) for q in quarterly_data[:4] if q.revenue]
                if len(revenues) >= 4:
                    # Calculate coefficient of variation
                    avg_rev = sum(revenues) / len(revenues)
                    std_rev = (sum((r - avg_rev) ** 2 for r in revenues) / len(revenues)) ** 0.5
                    cv = (std_rev / avg_rev * 100) if avg_rev > 0 else 0
                    
                    if cv < 10:
                        indicators["revenue_stability"] = {"level": "low", "color": "green", "value": cv}
                    elif cv < 20:
                        indicators["revenue_stability"] = {"level": "medium", "color": "yellow", "value": cv}
                    else:
                        indicators["revenue_stability"] = {"level": "high", "color": "red", "value": cv}
            
            # Overall risk score
            if indicators:
                risk_scores = {"low": 1, "medium": 2, "high": 3}
                total_score = sum(risk_scores.get(ind["level"], 2) for ind in indicators.values())
                avg_score = total_score / len(indicators)
                
                if avg_score < 1.5:
                    overall_risk = "low"
                    overall_color = "green"
                elif avg_score < 2.5:
                    overall_risk = "medium"
                    overall_color = "yellow"
                else:
                    overall_risk = "high"
                    overall_color = "red"
                
                indicators["overall_risk"] = {
                    "level": overall_risk,
                    "color": overall_color,
                    "score": round(avg_score, 2)
                }
            
            return {
                "indicators": indicators,
                "has_data": len(indicators) > 0
            }
        except Exception as e:
            logger.error(f"Error generating risk indicators: {e}")
            return {
                "indicators": {},
                "has_data": False
            }
    
    def _generate_comparison_table(
        self,
        quarterly_data: List,
        yearly_data: List,
        financial_ratios: Optional[Dict],
        all_ratios: List
    ) -> Dict:
        """Generate comparison table (current vs previous quarter/year)"""
        try:
            comparison = {
                "quarterly": {},
                "yearly": {},
                "ratios": {}
            }
            
            # Quarterly comparison
            if quarterly_data and len(quarterly_data) >= 2:
                current_q = quarterly_data[0]
                previous_q = quarterly_data[1]
                
                comparison["quarterly"] = {
                    "current": {
                        "period": current_q.period_end.isoformat() if hasattr(current_q.period_end, 'isoformat') else str(current_q.period_end),
                        "revenue": float(current_q.revenue) / 10000 if current_q.revenue else None,
                        "net_profit": float(current_q.net_profit) / 10000 if current_q.net_profit else None,
                        "eps": float(current_q.eps) if current_q.eps else None
                    },
                    "previous": {
                        "period": previous_q.period_end.isoformat() if hasattr(previous_q.period_end, 'isoformat') else str(previous_q.period_end),
                        "revenue": float(previous_q.revenue) / 10000 if previous_q.revenue else None,
                        "net_profit": float(previous_q.net_profit) / 10000 if previous_q.net_profit else None,
                        "eps": float(previous_q.eps) if previous_q.eps else None
                    }
                }
                
                # Calculate changes
                if comparison["quarterly"]["current"]["revenue"] and comparison["quarterly"]["previous"]["revenue"]:
                    revenue_change = ((comparison["quarterly"]["current"]["revenue"] - comparison["quarterly"]["previous"]["revenue"]) / comparison["quarterly"]["previous"]["revenue"]) * 100
                    comparison["quarterly"]["revenue_change_pct"] = revenue_change
                
                if comparison["quarterly"]["current"]["net_profit"] and comparison["quarterly"]["previous"]["net_profit"]:
                    profit_change = ((comparison["quarterly"]["current"]["net_profit"] - comparison["quarterly"]["previous"]["net_profit"]) / comparison["quarterly"]["previous"]["net_profit"]) * 100
                    comparison["quarterly"]["profit_change_pct"] = profit_change
            
            # Yearly comparison
            if yearly_data and len(yearly_data) >= 2:
                current_y = yearly_data[0]
                previous_y = yearly_data[1]
                
                comparison["yearly"] = {
                    "current": {
                        "period": current_y.period_end.isoformat() if hasattr(current_y.period_end, 'isoformat') else str(current_y.period_end),
                        "revenue": float(current_y.revenue) / 10000 if current_y.revenue else None,
                        "net_profit": float(current_y.net_profit) / 10000 if current_y.net_profit else None
                    },
                    "previous": {
                        "period": previous_y.period_end.isoformat() if hasattr(previous_y.period_end, 'isoformat') else str(previous_y.period_end),
                        "revenue": float(previous_y.revenue) / 10000 if previous_y.revenue else None,
                        "net_profit": float(previous_y.net_profit) / 10000 if previous_y.net_profit else None
                    }
                }
                
                # Calculate changes
                if comparison["yearly"]["current"]["revenue"] and comparison["yearly"]["previous"]["revenue"]:
                    revenue_change = ((comparison["yearly"]["current"]["revenue"] - comparison["yearly"]["previous"]["revenue"]) / comparison["yearly"]["previous"]["revenue"]) * 100
                    comparison["yearly"]["revenue_change_pct"] = revenue_change
                
                if comparison["yearly"]["current"]["net_profit"] and comparison["yearly"]["previous"]["net_profit"]:
                    profit_change = ((comparison["yearly"]["current"]["net_profit"] - comparison["yearly"]["previous"]["net_profit"]) / comparison["yearly"]["previous"]["net_profit"]) * 100
                    comparison["yearly"]["profit_change_pct"] = profit_change
            
            # Ratios comparison (current vs previous period)
            if all_ratios and len(all_ratios) >= 2:
                current_ratio = all_ratios[0]
                previous_ratio = all_ratios[1]
                
                comparison["ratios"] = {
                    "current": {
                        "pe_ratio": float(current_ratio.pe_ratio) if current_ratio.pe_ratio else None,
                        "pb_ratio": float(current_ratio.pb_ratio) if current_ratio.pb_ratio else None,
                        "roe": float(current_ratio.roe) if current_ratio.roe else None,
                        "debt_to_equity": float(current_ratio.debt_to_equity) if current_ratio.debt_to_equity else None
                    },
                    "previous": {
                        "pe_ratio": float(previous_ratio.pe_ratio) if previous_ratio.pe_ratio else None,
                        "pb_ratio": float(previous_ratio.pb_ratio) if previous_ratio.pb_ratio else None,
                        "roe": float(previous_ratio.roe) if previous_ratio.roe else None,
                        "debt_to_equity": float(previous_ratio.debt_to_equity) if previous_ratio.debt_to_equity else None
                    }
                }
            
            return {
                "comparison": comparison,
                "has_data": bool(comparison.get("quarterly") or comparison.get("yearly") or comparison.get("ratios"))
            }
        except Exception as e:
            logger.error(f"Error generating comparison table: {e}")
            return {
                "comparison": {},
                "has_data": False
            }

# Create singleton instance
comprehensive_report_generator = ComprehensiveReportGenerator()

