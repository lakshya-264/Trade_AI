/**
 * Research Report Page
 * Auto-generated comprehensive research reports
 */

import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  DocumentTextIcon, 
  ChartBarIcon, 
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowLeftIcon,
  ArrowDownTrayIcon,
  TableCellsIcon,
  ChartPieIcon,
  PhotoIcon,
  StarIcon,
  BellIcon
} from '@heroicons/react/24/outline';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import StockSelector from '../components/StockSelector';
import PatternVisualization from '../components/PatternVisualization';
import MarketFactorsPanel from '../components/MarketFactorsPanel';
import ChartImageUpload from '../components/ChartImageUpload';
import BuySellButton from '../components/BuySellButton';
import ClickableSymbol from '../components/ClickableSymbol';
import candleDataApi from '../services/candleDataApi';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';

interface ResearchReport {
  symbol: string;
  company_name: string;
  current_price: number;
  market_cap?: number;
  report_date: string;
  timeframe?: string;
  sections: {
    executive_summary?: {
      summary: string;
      has_data: boolean;
      company_name?: string;
      symbol?: string;
      current_price?: number;
    };
    key_metrics_dashboard?: {
      metrics: Record<string, number | null>;
      has_data: boolean;
    };
    financial_trends?: {
      trends: {
        quarterly: Array<{
          period: string;
          revenue: number;
          net_profit: number;
          net_margin: number;
          operating_margin?: number | null;
        }>;
        yearly: Array<{
          period: string;
          revenue: number;
          net_profit: number;
          net_margin: number;
        }>;
      };
      has_data: boolean;
    };
    risk_indicators?: {
      indicators: Record<string, {
        level: string;
        color: string;
        value?: number;
        score?: number;
      }>;
      has_data: boolean;
    };
    comparison_table?: {
      comparison: {
        quarterly?: {
          current: {
            period: string;
            revenue?: number;
            net_profit?: number;
            eps?: number;
          };
          previous: {
            period: string;
            revenue?: number;
            net_profit?: number;
            eps?: number;
          };
          revenue_change_pct?: number;
          profit_change_pct?: number;
        };
        yearly?: {
          current: {
            period: string;
            revenue?: number;
            net_profit?: number;
          };
          previous: {
            period: string;
            revenue?: number;
            net_profit?: number;
          };
          revenue_change_pct?: number;
          profit_change_pct?: number;
        };
        ratios?: {
          current: {
            pe_ratio?: number;
            pb_ratio?: number;
            roe?: number;
            debt_to_equity?: number;
          };
          previous: {
            pe_ratio?: number;
            pb_ratio?: number;
            roe?: number;
            debt_to_equity?: number;
          };
        };
      };
      has_data: boolean;
    };
    financial_ratios?: {
      summary: string;
      ratios: Record<string, number>;
      has_data: boolean;
    };
    detailed_company_research?: {
      has_data: boolean;
      summary: string;
      sections?: Array<{
        type: string;
        title: string;
        content?: string;
        achievements?: string[];
        segments?: Array<{
          name: string;
          title: string;
          revenue: string;
          revenue_growth: string;
          ebitda: string;
          contribution: string;
          details?: any;
        }>;
        initiatives?: any;
        analysis?: any;
        context?: any;
      }>;
      financial_ratios?: Record<string, any>;
      full_research?: any;
      screener_data?: {
        growth_metrics?: {
          sales_growth_10y?: number;
          sales_growth_5y?: number;
          sales_growth_3y?: number;
          sales_growth_ttm?: number;
          profit_growth_10y?: number;
          profit_growth_5y?: number;
          profit_growth_3y?: number;
          profit_growth_ttm?: number;
          price_cagr_10y?: number;
          price_cagr_5y?: number;
          price_cagr_3y?: number;
          price_cagr_1y?: number;
          roe_10y?: number;
          roe_5y?: number;
          roe_3y?: number;
          roe_last_year?: number;
        };
        balance_sheet?: Array<{
          period: string;
          equity_capital?: number;
          reserves?: number;
          borrowings?: number;
        }>;
        cash_flows?: Array<{
          period: string;
          operating_cash_flow?: number;
          investing_cash_flow?: number;
          financing_cash_flow?: number;
        }>;
        detailed_shareholding?: Array<{
          period: string;
          promoters?: number;
          fiis?: number;
          diis?: number;
          government?: number;
          public?: number;
          no_of_shareholders?: number;
        }>;
      };
    };
    quarterly_pl?: {
      summary: string;
      quarters: Array<{
        period: string;
        revenue?: number;
        net_profit?: number;
        eps?: number;
        net_margin_pct?: number;
        operating_margin_pct?: number;
        debt_to_equity?: number;
      }>;
      has_data: boolean;
      trends: Record<string, number>;
      debt_to_equity_series?: Array<{
        period: string;
        period_end?: string;
        debt_to_equity?: number;
      }>;
    };
    yearly_pl?: {
      summary: string;
      years: Array<{
        year: number | string;
        revenue?: number;
        net_profit?: number;
        eps?: number;
      }>;
      has_data: boolean;
      growth_metrics: Record<string, number>;
    };
    balance_sheet?: {
      summary: string;
      balance_sheets: Array<any>;
      has_data: boolean;
    };
    price_action?: {
      summary: string;
      trend: string;
      trend_strength: string;
      momentum: string;
      rsi?: number;
      sma_20?: number;
      sma_50?: number;
    };
    financial_strength?: {
      summary: string;
      assessment: string;
      strength_score: number;
      strengths: string[];
      weaknesses: string[];
      revenue?: number;
      net_profit?: number;
      roe?: number;
      roce?: number;
      debt_to_equity?: number;
    };
    valuation?: {
      summary: string;
      assessment: string;
      pe_ratio?: number;
      pb_ratio?: number;
    };
    technical_signals?: {
      summary: string;
      signals: string[];
      rsi?: number;
      macd?: string;
    };
    chart_patterns?: {
      summary: string;
      patterns: any[];
      has_patterns: boolean;
      primary_pattern?: {
        pattern_name: string;
        target_price: number;
        potential_upside: number;
        confidence: number;
      };
    };
    trendline_analysis?: {
      summary: string;
      has_data: boolean;
      uptrend_count?: number;
      downtrend_count?: number;
      channel_count?: number;
      current_trend?: string;
      confidence?: string;
      recent_breaks_count?: number;
    };
    market_structure_analysis?: {
      summary: string;
      has_data: boolean;
      current_phase?: string;
      structure_type?: string;
      bos_count?: number;
      choch_count?: number;
      trading_signals?: any[];
    };
    support_resistance_analysis?: {
      summary: string;
      has_data: boolean;
      support_levels_count?: number;
      resistance_levels_count?: number;
      nearest_support?: { price: number };
      nearest_resistance?: { price: number };
      current_zone?: string;
    };
    swing_point_analysis?: {
      summary: string;
      has_data: boolean;
      swing_highs_count?: number;
      swing_lows_count?: number;
      trend?: string;
      pattern_sequence?: string[];
    };
    supply_demand_analysis?: {
      summary: string;
      has_data: boolean;
      demand_zones_count?: number;
      supply_zones_count?: number;
      fresh_demand_count?: number;
      fresh_supply_count?: number;
      tested_demand_count?: number;
      tested_supply_count?: number;
      nearest_demand?: { price_range: { low: number; high: number } };
      nearest_supply?: { price_range: { low: number; high: number } };
    };
    chart_images_analysis?: {
      summary: string;
      has_data: boolean;
      images_analyzed?: number;
      successful_analyses?: number;
      detected_patterns?: Array<{
        pattern_name: string;
        frequency: number;
        average_confidence: number;
        description: string;
      }>;
      key_levels?: Array<{
        percentage_range?: string;
        frequency: number;
        description: string;
        estimated_price?: number;
        price_type?: string;
        distance_from_current?: number;
        distance_percent?: number;
        is_support?: boolean;
        is_resistance?: boolean;
      }>;
      support_levels?: Array<{
        estimated_price: number;
        frequency: number;
        price_type: string;
        distance_percent?: number;
      }>;
      resistance_levels?: Array<{
        estimated_price: number;
        frequency: number;
        price_type: string;
        distance_percent?: number;
      }>;
      nearest_support?: {
        estimated_price: number;
        frequency: number;
        price_type: string;
        distance_percent?: number;
        distance_from_current?: number;
      };
      nearest_resistance?: {
        estimated_price: number;
        frequency: number;
        price_type: string;
        distance_percent?: number;
        distance_from_current?: number;
      };
      overall_trend?: string;
      individual_analyses?: Array<any>;
      current_price?: number;
    };
    price_predictions?: {
      summary: string;
      has_data: boolean;
      current_price?: number;
      overall_confidence?: number;
      timeframes?: {
        '1W'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
        '1M'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
        '2M'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
        '3M'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
        '6M'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
        '1Y'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
        '2Y'?: {
          timeframe: string;
          days: number;
          predicted_price: number;
          current_price: number;
          expected_return: number;
          potential_change: number;
          potential_change_percent: number;
          confidence: number;
          price_range?: {
            low_68: number;
            high_68: number;
            low_95: number;
            high_95: number;
            volatility: number;
          };
          risk_level?: string;
        };
      };
      prediction_date?: string;
    };
    market_factors?: {
      summary: string;
      has_data: boolean;
      news?: any;
      orderbook?: any;
      block_deals?: any[];
      fii_dii_flows?: any;
      impact_analysis?: any;
    };
    market_sentiment?: {
      summary: string;
      overall_sentiment: string;
      news_sentiment?: string;
      social_sentiment?: string;
      sentiment_score?: number;
    };
    risk_assessment?: {
      risk_level: string;
      risk_factors: string[];
      summary: string;
    };
    strong_points?: {
      summary: string;
      points: Array<{
        point: string;
        description: string;
      }>;
      count: number;
    };
    recommendation?: {
      recommendation: 'BUY' | 'SELL' | 'HOLD';
      confidence: number;
      reasoning: string[];
      summary: string;
      target_price?: number;
      potential_upside?: number;
      holding_period?: string;
    };
    conclusion?: {
      summary: string;
      recommendation: string;
      confidence: number;
    };
  };
}

// Projections endpoint payload is separate from report payload.
type ProjectionsPayload = any;

const ResearchReport: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const symbolFromUrl = searchParams.get('symbol');
  
  const [symbol, setSymbol] = useState(symbolFromUrl || 'RELIANCE');
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [projections, setProjections] = useState<ProjectionsPayload | null>(null);
  const [loadingProjections, setLoadingProjections] = useState(false);
  const [projectionsError, setProjectionsError] = useState<string | null>(null);
  const [projectionAssumptions, setProjectionAssumptions] = useState({
    years: 5,
    base_discount_rate: 0.12,
    base_terminal_growth: 0.04,
    base_growth_override: '' as string, // decimal string; empty = auto
    base_profit_margin_override: '' as string, // decimal string; empty = auto
    bull_growth_delta: 0.03,
    bear_growth_delta: -0.03,
    bull_margin_delta: 0.01,
    bear_margin_delta: -0.01,
    eps_to_fcf_ratio: 0.85,
  });
  const [loading, setLoading] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);
  
  // Chart refs for pattern visualization
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [chartLoading, setChartLoading] = useState(false);
  
  // Chart refs for Financial Trends
  const revenueProfitChartRef = useRef<HTMLDivElement>(null);
  const marginsChartRef = useRef<HTMLDivElement>(null);
  const revenueProfitChartInstance = useRef<IChartApi | null>(null);
  const marginsChartInstance = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (symbol) {
      const currentSymbol = symbol.toUpperCase().trim();
      console.log('🔄 Symbol changed, fetching new report for:', currentSymbol);
      
      // Clear old report immediately when symbol changes to prevent showing wrong stock data
      setReport(null);
      setProjections(null);
      setProjectionsError(null);
      
      // Fetch new report for the selected symbol
      const fetchData = async () => {
        const requestedSymbol = currentSymbol;
        console.log('📡 Fetching report for symbol:', requestedSymbol, 'timeframe:', timeframe);
        setLoading(true);
        try {
          // Add timestamp to prevent caching
          const timestamp = Date.now();
          const response = await httpClient.get<any>(`/api/financial/research-report/${requestedSymbol}?timeframe=${timeframe}&_t=${timestamp}`);
          
          if (response.success && response.data) {
            // Verify the returned report has the correct symbol
            const receivedSymbol = (response.data.symbol || '').toUpperCase().trim();
            
            console.log('✅ Report fetch verification:', {
              requested: requestedSymbol,
              received: receivedSymbol,
              match: receivedSymbol === requestedSymbol,
              reportSymbol: response.data.symbol
            });
            
            if (receivedSymbol && receivedSymbol === requestedSymbol) {
              console.log('✅ Setting report with correct symbol:', receivedSymbol);
              setReport(response.data);
              toast.success(`Research report generated for ${receivedSymbol}`);
            } else {
              console.error('❌ Symbol mismatch detected:', { 
                requested: requestedSymbol, 
                received: receivedSymbol,
                reportData: response.data 
              });
              toast.error(`Report symbol mismatch - expected ${requestedSymbol}, got ${receivedSymbol}`);
              // Don't set the report if symbol doesn't match
              setReport(null);
            }
          } else {
            console.error('❌ Report fetch failed:', response.message);
            toast.error(response.message || 'Failed to generate research report');
          }
        } catch (error) {
          console.error('❌ Error fetching report:', error);
          toast.error('Failed to generate research report');
        } finally {
          setLoading(false);
        }
        
        // Fetch projections
        if (requestedSymbol) {
          setLoadingProjections(true);
          setProjectionsError(null);
          try {
            const params: Record<string, any> = {
              years: projectionAssumptions.years,
              base_discount_rate: projectionAssumptions.base_discount_rate,
              base_terminal_growth: projectionAssumptions.base_terminal_growth,
              bull_growth_delta: projectionAssumptions.bull_growth_delta,
              bear_growth_delta: projectionAssumptions.bear_growth_delta,
              bull_margin_delta: projectionAssumptions.bull_margin_delta,
              bear_margin_delta: projectionAssumptions.bear_margin_delta,
              eps_to_fcf: projectionAssumptions.eps_to_fcf_ratio,
            };

            if (projectionAssumptions.base_growth_override !== '') {
              params.base_growth_override = Number(projectionAssumptions.base_growth_override);
            }
            if (projectionAssumptions.base_profit_margin_override !== '') {
              params.base_profit_margin_override = Number(projectionAssumptions.base_profit_margin_override);
            }

            const projResponse = await httpClient.get<any>(`/api/financial/projections/${requestedSymbol}`, { params });
            if (projResponse.success && projResponse.data) {
              setProjections(projResponse.data);
            } else {
              setProjections(null);
              setProjectionsError(projResponse.message || 'Failed to generate projections');
            }
          } catch (error: any) {
            console.error('Error fetching projections:', error);
            setProjections(null);
            setProjectionsError(error?.message || 'Failed to generate projections');
          } finally {
            setLoadingProjections(false);
          }
        }
      };
      
      fetchData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, timeframe]); // Only refetch when symbol or timeframe changes, not projection assumptions

  // Initialize chart when pattern section is available
  useEffect(() => {
    if (report?.sections.chart_patterns?.has_patterns && chartContainerRef.current && !chartRef.current) {
      initializeChart();
      loadChartData();
    }

    return () => {
      if (chartRef.current) {
        try {
          if (chartContainerRef.current) {
            chartRef.current.remove();
          }
        } catch (error) {
          console.debug('Chart already disposed:', error);
        }
      }
      chartRef.current = null;
      candlestickSeriesRef.current = null;
    };
  }, [report?.sections.chart_patterns?.has_patterns, symbol]);

  // Reload chart data when timeframe changes
  useEffect(() => {
    if (report?.sections.chart_patterns?.has_patterns && candlestickSeriesRef.current) {
      loadChartData();
    }
  }, [timeframe]);

  // Initialize Financial Trends Charts
  useEffect(() => {
    if (!report?.sections.financial_trends?.has_data) return;

    const quarterly = report.sections.financial_trends.trends.quarterly || [];
    if (quarterly.length === 0) return;

    // Initialize Revenue & Profit Chart
    if (revenueProfitChartRef.current && !revenueProfitChartInstance.current) {
      const chart = createChart(revenueProfitChartRef.current, {
        width: revenueProfitChartRef.current.clientWidth,
        height: 250,
        layout: {
          background: { color: 'transparent' },
          textColor: '#374151',
        },
        grid: {
          vertLines: { color: '#E5E7EB' },
          horzLines: { color: '#E5E7EB' },
        },
        timeScale: {
          borderColor: '#D1D5DB',
          timeVisible: true,
        },
        rightPriceScale: {
          borderColor: '#D1D5DB',
        },
      });

      revenueProfitChartInstance.current = chart;

      // Add Revenue series (bar chart)
      const revenueSeries = chart.addHistogramSeries({
        color: '#3B82F6',
        priceFormat: {
          type: 'volume',
          precision: 0,
        },
        priceScaleId: 'revenue',
        title: 'Revenue',
      });

      // Add Profit series (line chart)
      const profitSeries = chart.addLineSeries({
        color: '#10B981',
        lineWidth: 2,
        priceScaleId: 'profit',
        title: 'Net Profit',
      });

      // Helper to convert period string to Time format
      const parsePeriod = (period: string): Time => {
        // First try ISO date format (YYYY-MM-DD) from backend
        if (period.match(/^\d{4}-\d{2}-\d{2}/)) {
          return period as Time;
        }
        
        // Try to parse formats like "Mar 2025", "Q1 FY26", "2025-03", etc.
        const months: { [key: string]: number } = {
          'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5,
          'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11
        };
        
        // Try "Mar 2025" format
        const parts = period.trim().split(/\s+/);
        if (parts.length >= 2) {
          const monthStr = parts[0].toLowerCase().substring(0, 3);
          const yearStr = parts[1];
          if (months[monthStr] !== undefined && yearStr) {
            const year = parseInt(yearStr);
            if (!isNaN(year)) {
              return `${year}-${String(months[monthStr] + 1).padStart(2, '0')}-01` as Time;
            }
          }
        }
        
        // Fallback: use as string if can't parse
        return period as Time;
      };

      // Helper to get comparable value for sorting (using same logic as parsePeriod)
      const getTimeValue = (period: string): string => {
        // First try ISO date format (YYYY-MM-DD) from backend
        if (period.match(/^\d{4}-\d{2}-\d{2}/)) {
          return period;
        }
        
        const months: { [key: string]: number } = {
          'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5,
          'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11
        };
        
        const parts = period.trim().split(/\s+/);
        if (parts.length >= 2) {
          const monthStr = parts[0].toLowerCase().substring(0, 3);
          const yearStr = parts[1];
          if (months[monthStr] !== undefined && yearStr) {
            const year = parseInt(yearStr);
            if (!isNaN(year)) {
              return `${year}-${String(months[monthStr] + 1).padStart(2, '0')}-01`;
            }
          }
        }
        return period;
      };

      // Sort quarterly data by time in ascending order (oldest first)
      // Use the same parsing logic that will be used for chart data
      const sortedQuarterly = [...quarterly].sort((a: any, b: any) => {
        const timeA = getTimeValue(a.period);
        const timeB = getTimeValue(b.period);
        return timeA.localeCompare(timeB);
      });

      // Prepare data (now sorted) - ensure data is in ascending order
      // Map and sort by the actual time value that will be used by the chart
      // Note: Backend already provides revenue and net_profit in crores, so use directly
      const revenueData = sortedQuarterly
        .filter((q: any) => q.revenue != null && q.revenue !== undefined && q.revenue !== 0)
        .map((q: any) => {
          const timeValue = parsePeriod(q.period);
          // Backend already converts to crores (divides by 10000), so use value directly
          // If value is very large (> 1 million), it might be in raw format, so divide by 10000
          // Otherwise, backend already provided it in crores
          const revenueValue = (q.revenue && q.revenue > 1000000) ? q.revenue / 10000 : (q.revenue || 0);
          return {
            time: timeValue,
            value: revenueValue,
            _sortKey: typeof timeValue === 'string' ? timeValue : String(timeValue)
          };
        })
        .sort((a, b) => a._sortKey.localeCompare(b._sortKey))
        .map(({ _sortKey, ...item }) => item); // Remove sort key

      const profitData = sortedQuarterly
        .filter((q: any) => q.net_profit != null && q.net_profit !== undefined)
        .map((q: any) => {
          const timeValue = parsePeriod(q.period);
          // Backend already converts to crores (divides by 10000), so use value directly
          // If value is very large (> 1 million), it might be in raw format, so divide by 10000
          // Otherwise, backend already provided it in crores
          const profitValue = (q.net_profit && q.net_profit > 1000000) ? q.net_profit / 10000 : (q.net_profit || 0);
          return {
            time: timeValue,
            value: profitValue,
            _sortKey: typeof timeValue === 'string' ? timeValue : String(timeValue)
          };
        })
        .sort((a, b) => a._sortKey.localeCompare(b._sortKey))
        .map(({ _sortKey, ...item }) => item); // Remove sort key

      // Final validation: ensure data is sorted (lightweight-charts requirement)
      const validateAndSort = (data: Array<{ time: Time; value: number }>) => {
        // Convert time to comparable value
        const getComparableTime = (time: Time): number => {
          if (typeof time === 'string') {
            // Parse "YYYY-MM-DD" format
            const date = new Date(time);
            return isNaN(date.getTime()) ? 0 : date.getTime();
          }
          return typeof time === 'number' ? time : 0;
        };
        
        return [...data].sort((a, b) => {
          const timeA = getComparableTime(a.time);
          const timeB = getComparableTime(b.time);
          return timeA - timeB;
        });
      };

      const sortedRevenueData = validateAndSort(revenueData);
      const sortedProfitData = validateAndSort(profitData);

      revenueSeries.setData(sortedRevenueData);
      profitSeries.setData(sortedProfitData);

      chart.timeScale().fitContent();

      // Handle resize
      const handleResize = () => {
        if (revenueProfitChartRef.current && revenueProfitChartInstance.current) {
          revenueProfitChartInstance.current.applyOptions({
            width: revenueProfitChartRef.current.clientWidth,
          });
        }
      };
      window.addEventListener('resize', handleResize);
    }

    // Initialize Margins Chart
    if (marginsChartRef.current && !marginsChartInstance.current) {
      const chart = createChart(marginsChartRef.current, {
        width: marginsChartRef.current.clientWidth,
        height: 250,
        layout: {
          background: { color: 'transparent' },
          textColor: '#374151',
        },
        grid: {
          vertLines: { color: '#E5E7EB' },
          horzLines: { color: '#E5E7EB' },
        },
        timeScale: {
          borderColor: '#D1D5DB',
          timeVisible: true,
        },
        rightPriceScale: {
          borderColor: '#D1D5DB',
        },
      });

      marginsChartInstance.current = chart;

      // Add Net Margin series
      const netMarginSeries = chart.addLineSeries({
        color: '#8B5CF6',
        lineWidth: 2,
        title: 'Net Margin',
      });

      // Add Operating Margin series (if available)
      const operatingMarginSeries = chart.addLineSeries({
        color: '#F59E0B',
        lineWidth: 2,
        title: 'Operating Margin',
      });

      // Helper to convert period string to Time format (reuse same function)
      const parsePeriod = (period: string): Time => {
        const months: { [key: string]: number } = {
          'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5,
          'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11
        };
        
        const parts = period.trim().split(/\s+/);
        if (parts.length >= 2) {
          const monthStr = parts[0].toLowerCase().substring(0, 3);
          const yearStr = parts[1];
          if (months[monthStr] !== undefined && yearStr) {
            const year = parseInt(yearStr);
            if (!isNaN(year)) {
              return `${year}-${String(months[monthStr] + 1).padStart(2, '0')}-01` as Time;
            }
          }
        }
        return period as Time;
      };

      // Helper to get comparable value for sorting (using same logic as parsePeriod)
      const getTimeValue = (period: string): string => {
        // First try ISO date format (YYYY-MM-DD) from backend
        if (period.match(/^\d{4}-\d{2}-\d{2}/)) {
          return period;
        }
        
        const months: { [key: string]: number } = {
          'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5,
          'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11
        };
        
        const parts = period.trim().split(/\s+/);
        if (parts.length >= 2) {
          const monthStr = parts[0].toLowerCase().substring(0, 3);
          const yearStr = parts[1];
          if (months[monthStr] !== undefined && yearStr) {
            const year = parseInt(yearStr);
            if (!isNaN(year)) {
              return `${year}-${String(months[monthStr] + 1).padStart(2, '0')}-01`;
            }
          }
        }
        return period;
      };

      // Sort quarterly data by time in ascending order (oldest first)
      // Use the same parsing logic that will be used for chart data
      const sortedQuarterly = [...quarterly].sort((a: any, b: any) => {
        const timeA = getTimeValue(a.period);
        const timeB = getTimeValue(b.period);
        return timeA.localeCompare(timeB);
      });

      // Prepare data (now sorted) - ensure data is in ascending order
      // Map and sort by the actual time value that will be used by the chart
      const netMarginData = sortedQuarterly
        .map((q: any) => {
          const timeValue = parsePeriod(q.period);
          return {
            time: timeValue,
            value: q.net_margin || 0,
            _sortKey: typeof timeValue === 'string' ? timeValue : String(timeValue)
          };
        })
        .sort((a, b) => a._sortKey.localeCompare(b._sortKey))
        .map(({ _sortKey, ...item }) => item); // Remove sort key

      const operatingMarginData = sortedQuarterly
        .filter((q: any) => q.operating_margin !== null && q.operating_margin !== undefined)
        .map((q: any) => {
          const timeValue = parsePeriod(q.period);
          return {
            time: timeValue,
            value: q.operating_margin || 0,
            _sortKey: typeof timeValue === 'string' ? timeValue : String(timeValue)
          };
        })
        .sort((a, b) => a._sortKey.localeCompare(b._sortKey))
        .map(({ _sortKey, ...item }) => item); // Remove sort key

      // Final validation: ensure data is sorted (lightweight-charts requirement)
      const validateAndSort = (data: Array<{ time: Time; value: number }>) => {
        // Convert time to comparable value
        const getComparableTime = (time: Time): number => {
          if (typeof time === 'string') {
            // Parse "YYYY-MM-DD" format
            const date = new Date(time);
            return isNaN(date.getTime()) ? 0 : date.getTime();
          }
          return typeof time === 'number' ? time : 0;
        };
        
        return [...data].sort((a, b) => {
          const timeA = getComparableTime(a.time);
          const timeB = getComparableTime(b.time);
          return timeA - timeB;
        });
      };

      const sortedNetMarginData = validateAndSort(netMarginData);
      const sortedOperatingMarginData = operatingMarginData.length > 0 
        ? validateAndSort(operatingMarginData) 
        : [];

      netMarginSeries.setData(sortedNetMarginData);
      if (sortedOperatingMarginData.length > 0) {
        operatingMarginSeries.setData(sortedOperatingMarginData);
      }

      chart.timeScale().fitContent();

      // Handle resize
      const handleResize = () => {
        if (marginsChartRef.current && marginsChartInstance.current) {
          marginsChartInstance.current.applyOptions({
            width: marginsChartRef.current.clientWidth,
          });
        }
      };
      window.addEventListener('resize', handleResize);
    }

    return () => {
      if (revenueProfitChartInstance.current) {
        revenueProfitChartInstance.current.remove();
        revenueProfitChartInstance.current = null;
      }
      if (marginsChartInstance.current) {
        marginsChartInstance.current.remove();
        marginsChartInstance.current = null;
      }
    };
  }, [report?.sections.financial_trends]);

  // Helper function to render nested details in a clean format (no JSON brackets)
  const renderNestedDetails = (details: any, level: number = 0): React.ReactNode => {
    if (!details || typeof details !== 'object') {
      return <span className="text-gray-900 dark:text-white">{String(details)}</span>;
    }
    
    if (Array.isArray(details)) {
      return (
        <ul className="list-disc list-inside space-y-1 ml-4">
          {details.map((item, idx) => (
            <li key={idx} className="text-gray-700 dark:text-gray-300">
              {typeof item === 'object' ? renderNestedDetails(item, level + 1) : String(item)}
            </li>
          ))}
        </ul>
      );
    }
    
    return (
      <div className={`space-y-3 ${level > 0 ? 'ml-4 border-l-2 border-gray-300 dark:border-gray-600 pl-4 mt-2' : ''}`}>
        {Object.entries(details).map(([key, value]) => {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          
          if (value === null || value === undefined || value === '') {
            return null;
          }
          
          if (typeof value === 'object' && !Array.isArray(value)) {
            return (
              <div key={key} className="space-y-2">
                <h6 className="font-semibold text-gray-900 dark:text-white text-sm">{formattedKey}:</h6>
                <div className="ml-2">
                  {renderNestedDetails(value, level + 1)}
                </div>
              </div>
            );
          }
          
          if (Array.isArray(value)) {
            return (
              <div key={key} className="space-y-2">
                <h6 className="font-semibold text-gray-900 dark:text-white text-sm">{formattedKey}:</h6>
                {renderNestedDetails(value, level + 1)}
              </div>
            );
          }
          
          // Format the value based on its content
          let displayValue = String(value);
          if (typeof value === 'number' && value != null && !isNaN(value)) {
            if (key.toLowerCase().includes('growth') || key.toLowerCase().includes('percent') || key.toLowerCase().includes('%')) {
              displayValue = `${value.toFixed(1)}%`;
            } else if (key.toLowerCase().includes('crore') || key.toLowerCase().includes('cr')) {
              displayValue = `₹${(value / 10000).toFixed(2)} Cr`;
            } else if (value > 1000) {
              displayValue = value.toLocaleString();
            } else {
              displayValue = value.toFixed(2);
            }
          } else if (value == null || (typeof value === 'number' && isNaN(value))) {
            displayValue = 'N/A';
          }
          
          return (
            <div key={key} className="flex items-start gap-2 py-1">
              <span className="font-medium text-gray-700 dark:text-gray-300 text-sm min-w-[140px]">{formattedKey}:</span>
              <span className="text-gray-900 dark:text-white flex-1">{displayValue}</span>
            </div>
          );
        })}
      </div>
    );
  };

  const fetchReport = async () => {
    if (!symbol) return;
    setLoading(true);
    // Clear report immediately to prevent showing stale data
    setReport(null);
    try {
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const response = await httpClient.get<any>(`/api/financial/research-report/${symbol}?timeframe=${timeframe}&_t=${timestamp}`);
      
      // httpClient.get returns APIResponse directly, so check response.success
      if (response.success && response.data) {
        // Verify the returned report has the correct symbol
        if (response.data.symbol && response.data.symbol.toUpperCase() === symbol.toUpperCase()) {
          setReport(response.data);
          toast.success(`Research report generated successfully for ${symbol}`);
        } else {
          console.error('Symbol mismatch:', { requested: symbol, received: response.data.symbol });
          toast.error('Report symbol mismatch - please try again');
        }
      } else {
        toast.error(response.message || 'Failed to generate research report');
      }
    } catch (error) {
      console.error('Error fetching report:', error);
      toast.error('Failed to generate research report');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjections = async () => {
    if (!symbol) return;
    setLoadingProjections(true);
    setProjectionsError(null);
    try {
      const params: Record<string, any> = {
        years: projectionAssumptions.years,
        base_discount_rate: projectionAssumptions.base_discount_rate,
        base_terminal_growth: projectionAssumptions.base_terminal_growth,
        bull_growth_delta: projectionAssumptions.bull_growth_delta,
        bear_growth_delta: projectionAssumptions.bear_growth_delta,
        bull_margin_delta: projectionAssumptions.bull_margin_delta,
        bear_margin_delta: projectionAssumptions.bear_margin_delta,
        eps_to_fcf: projectionAssumptions.eps_to_fcf_ratio, // Backend expects eps_to_fcf, not eps_to_fcf_ratio
      };

      if (projectionAssumptions.base_growth_override !== '') {
        params.base_growth_override = Number(projectionAssumptions.base_growth_override);
      }
      if (projectionAssumptions.base_profit_margin_override !== '') {
        params.base_profit_margin_override = Number(projectionAssumptions.base_profit_margin_override);
      }

      const response = await httpClient.get<any>(`/api/financial/projections/${symbol}`, { params });
      if (response.success && response.data) {
        setProjections(response.data);
      } else {
        setProjections(null);
        setProjectionsError(response.message || 'Failed to generate projections');
      }
    } catch (error: any) {
      console.error('Error fetching projections:', error);
      setProjections(null);
      setProjectionsError(error?.message || 'Failed to generate projections');
    } finally {
      setLoadingProjections(false);
    }
  };

  const renderSensitivityHeatmap = (
    grid: any,
    title: string,
    rowLabelKey: 'terminal_growth' | 'growth_rate'
  ) => {
    const discountRates: number[] = grid?.discount_rates || [];
    const rows: Array<{ [k: string]: any; values: number[] }> = grid?.rows || [];
    const allValues = rows.flatMap((r) => (Array.isArray(r.values) ? r.values : []));
    const minV = allValues.length ? Math.min(...allValues) : 0;
    const maxV = allValues.length ? Math.max(...allValues) : 1;
    const denom = Math.max(1e-9, maxV - minV);

    const pct = (x: number) => x != null && !isNaN(x) ? `${(x * 100).toFixed(1)}%` : 'N/A';
    const cellBg = (v: number) => {
      const t = (v - minV) / denom; // 0..1
      // green-ish scale (light -> stronger)
      const alpha = 0.10 + 0.35 * t;
      return `rgba(34, 197, 94, ${alpha})`;
    };

    return (
      <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">{title}</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-gray-600 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                <th className="py-2 pr-3">{rowLabelKey === 'terminal_growth' ? 'Terminal g' : 'Growth'}</th>
                {discountRates.map((r) => (
                  <th key={r} className="py-2 pr-3 whitespace-nowrap">
                    r={pct(r)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 pr-3 font-medium text-gray-900 dark:text-white whitespace-nowrap">
                    {pct(row[rowLabelKey])}
                  </td>
                  {(row.values || []).map((v: number, j: number) => (
                    <td
                      key={j}
                      className="py-2 pr-3 text-gray-900 dark:text-white whitespace-nowrap"
                      style={{ backgroundColor: cellBg(Number(v)) }}
                      title={`₹${v}`}
                    >
                      ₹{v != null && !isNaN(Number(v)) ? Number(v).toFixed(2) : 'N/A'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-2 text-[11px] text-gray-500 dark:text-gray-400">
          Cell values: intrinsic value per share (higher = greener).
        </div>
      </div>
    );
  };

  const formatPct = (v: number) => `${Math.round(v * 1000) / 10}%`;

  const HeatmapGrid: React.FC<{
    title: string;
    grid: { discount_rates: number[]; rows: Array<{ terminal_growth?: number; growth_rate?: number; values: number[] }> };
    rowLabel: 'terminal_growth' | 'growth_rate';
  }> = ({ title, grid, rowLabel }) => {
    const allVals: number[] = [];
    grid.rows.forEach(r => r.values.forEach(v => typeof v === 'number' && allVals.push(v)));
    const min = allVals.length ? Math.min(...allVals) : 0;
    const max = allVals.length ? Math.max(...allVals) : 0;

    const colorFor = (v: number) => {
      if (max === min) return 'rgba(59,130,246,0.20)'; // blue-ish
      const t = (v - min) / (max - min); // 0..1
      // interpolate red -> green
      const r = Math.round(239 + (34 - 239) * t);
      const g = Math.round(68 + (197 - 68) * t);
      const b = Math.round(68 + (94 - 68) * t);
      return `rgba(${r},${g},${b},0.18)`;
    };

    return (
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="text-sm font-semibold text-gray-900 dark:text-white mb-3">{title}</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-left text-gray-600 dark:text-gray-300">
                <th className="py-2 pr-2">{rowLabel === 'terminal_growth' ? 'Terminal g' : 'Growth'}</th>
                {grid.discount_rates.map((r) => (
                  <th key={r} className="py-2 px-2 whitespace-nowrap">{formatPct(r)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.rows.map((row, idx) => {
                const labelVal = (row as any)[rowLabel] as number;
                return (
                  <tr key={idx} className="border-t border-gray-200 dark:border-gray-600">
                    <td className="py-2 pr-2 font-medium text-gray-900 dark:text-white whitespace-nowrap">
                      {formatPct(labelVal)}
                    </td>
                    {row.values.map((v, j) => (
                      <td
                        key={j}
                        className="py-2 px-2 text-gray-900 dark:text-white text-center rounded"
                        style={{ backgroundColor: colorFor(v) }}
                        title={`₹${v}`}
                      >
                        ₹{v}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="mt-2 text-[11px] text-gray-500 dark:text-gray-300">
          Min ₹{min != null && !isNaN(min) ? min.toFixed(0) : 'N/A'} · Max ₹{max != null && !isNaN(max) ? max.toFixed(0) : 'N/A'}
        </div>
      </div>
    );
  };

  const initializeChart = () => {
    if (!chartContainerRef.current || chartRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1e222d' },
        horzLines: { color: '#1e222d' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          width: 1,
          color: '#758696',
          style: 3,
          labelBackgroundColor: '#2962FF',
        },
        horzLine: {
          width: 1,
          color: '#758696',
          style: 3,
          labelBackgroundColor: '#2962FF',
        },
      },
      timeScale: {
        borderColor: '#2a2e39',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    chartRef.current = chart;

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);
  };

  const loadChartData = async () => {
    if (!symbol || !candlestickSeriesRef.current) return;

    setChartLoading(true);
    try {
      // Map timeframe to API format (1D -> 1d, 1W -> 1wk, 1M -> 1mo, etc.)
      const timeframeMap: Record<string, string> = {
        '1m': '1m', '2m': '2m', '3m': '3m', '5m': '5m', '15m': '15m',
        '1h': '1h', '2h': '2h', '4h': '4h',
        '1D': '1d', '1W': '1wk', '1M': '1mo', '3M': '3mo', '6M': '6mo'
      };
      const apiTimeframe = timeframeMap[timeframe] || '1d';
      
      // Determine period based on timeframe
      const periodMap: Record<string, string> = {
        '1m': '5d', '2m': '5d', '3m': '5d', '5m': '5d', '15m': '5d',
        '1h': '1mo', '2h': '1mo', '4h': '1mo',
        '1D': '1y', '1W': '1y', '1M': '2y', '3M': '2y', '6M': '5y'
      };
      const period = periodMap[timeframe] || '1y';
      
      const data = await candleDataApi.getCandles(symbol, apiTimeframe, period);
      
      if (data && data.data && candlestickSeriesRef.current) {
        const formattedData: CandlestickData[] = data.data.map((candle: any) => ({
          time: (candle.time as number) as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }));

        // Deduplicate and sort data
        const uniqueData = deduplicateAndSortCandlestickData(formattedData, false);
        candlestickSeriesRef.current.setData(uniqueData);
        
        // Fit content
        if (chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
      }
    } catch (err: any) {
      console.error('Error loading chart data:', err);
    } finally {
      setChartLoading(false);
    }
  };

  const exportReport = async (format: 'txt' | 'pdf' = 'txt') => {
    if (!report || !report.symbol) {
      toast.error('No report available to export');
      return;
    }
    
    if (format === 'pdf') {
      try {
        // Export as PDF via API - use fetch directly for blob response
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'}/api/financial/research-report/${report.symbol}/export-pdf`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(report),
          }
        );
        
        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `research_report_${report.symbol}_${Date.now()}.pdf`;
          a.click();
          URL.revokeObjectURL(url);
          toast.success('PDF report exported successfully');
        } else {
          // Fallback to text export
          exportReport('txt');
        }
      } catch (error) {
        console.error('PDF export error:', error);
        toast.error('PDF export failed. Exporting as text instead.');
        exportReport('txt');
      }
    } else {
      // Text export
    const reportText = `
RESEARCH REPORT - ${report.symbol}
Generated: ${new Date(report.report_date).toLocaleDateString()}
Current Price: ₹${report.current_price != null ? report.current_price.toFixed(2) : 'N/A'}

${report.sections.financial_ratios?.summary || ''}

${report.sections.quarterly_pl?.summary || ''}

${report.sections.yearly_pl?.summary || ''}

${report.sections.chart_patterns?.summary || ''}

${report.sections.price_action?.summary || ''}

${report.sections.financial_strength?.summary || ''}

${report.sections.valuation?.summary || ''}

${report.sections.technical_signals?.summary || ''}

${report.sections.risk_assessment?.summary || ''}

${report.sections.strong_points?.summary || ''}

${report.sections.recommendation?.summary || ''}

${report.sections.conclusion?.summary || ''}
    `.trim();
    
    const blob = new Blob([reportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_report_${report.symbol}_${Date.now()}.txt`;
    a.click();
      URL.revokeObjectURL(url);
      toast.success('Report exported as text');
    }
  };

  const exportFullPagePdf = async () => {
    if (!reportRef.current) {
      toast.error('Nothing to export');
      return;
    }

    try {
      toast.loading('Generating full page PDF...', { id: 'pdf-export' });
      
      const element = reportRef.current;
      
      // Hide floating elements that shouldn't be in PDF
      const floatingElements = document.querySelectorAll('.fixed, .sticky');
      const originalDisplay: string[] = [];
      floatingElements.forEach((el) => {
        const htmlEl = el as HTMLElement;
        originalDisplay.push(htmlEl.style.display);
        htmlEl.style.display = 'none';
      });

      // Capture with high quality settings
      const canvas = await html2canvas(element, {
        scale: Math.min(window.devicePixelRatio || 2, 2),
        useCORS: true,
        allowTaint: false,
        backgroundColor: '#ffffff',
        logging: false,
        width: element.scrollWidth,
        height: element.scrollHeight,
        windowWidth: element.scrollWidth,
        windowHeight: element.scrollHeight,
        scrollX: 0,
        scrollY: 0,
      });

      // Restore floating elements
      floatingElements.forEach((el, idx) => {
        const htmlEl = el as HTMLElement;
        htmlEl.style.display = originalDisplay[idx];
      });

      const imgData = canvas.toDataURL('image/png', 0.95);
      const pdf = new jsPDF('p', 'pt', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const margin = 20; // Small margin
      const contentWidth = pdfWidth - (margin * 2);
      
      const imgProps = pdf.getImageProperties(imgData);
      const imgWidth = contentWidth;
      const imgHeight = (imgProps.height * contentWidth) / imgProps.width;

      let heightLeft = imgHeight;
      let position = margin;

      // Add first page
      pdf.addImage(imgData, 'PNG', margin, position, imgWidth, imgHeight);
      heightLeft -= (pdfHeight - margin * 2);

      // Add additional pages if needed
      while (heightLeft > 0) {
        position -= (pdfHeight - margin * 2);
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', margin, position, imgWidth, imgHeight);
        heightLeft -= (pdfHeight - margin * 2);
      }

      const filename = `research_report_full_${symbol}_${Date.now()}.pdf`;
      pdf.save(filename);
      
      toast.success('Full page PDF generated successfully', { id: 'pdf-export' });
    } catch (error) {
      console.error('Full page PDF error:', error);
      toast.error('Failed to generate full page PDF', { id: 'pdf-export' });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ArrowLeftIcon className="h-6 w-6" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                  <DocumentTextIcon className="h-8 w-8 text-blue-600" />
                  Research Report
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  Auto-generated comprehensive stock analysis
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <div className="w-64">
                <StockSelector
                  value={symbol}
                  onChange={setSymbol}
                  showNavigateButton={false}
                />
              </div>
              {report && (
                <BuySellButton
                  symbol={symbol}
                  currentPrice={report.current_price}
                  onOrderPlaced={() => {
                    toast.success('Portfolio updated! Check Portfolio Allocation section.');
                  }}
                />
              )}
              <div className="flex items-center gap-2">
                <label htmlFor="timeframe-select" className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                  Timeframe:
                </label>
                <select
                  id="timeframe-select"
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {/* Intraday timeframes */}
                  <option value="1m">1 min</option>
                  <option value="2m">2 min</option>
                  <option value="3m">3 min</option>
                  <option value="5m">5 min</option>
                  <option value="15m">15 min</option>
                  <option value="1h">1 hour</option>
                  <option value="2h">2 hours</option>
                  <option value="4h">4 hours</option>

                  {/* Higher timeframes */}
                  <option value="1D">Daily</option>
                  <option value="1W">Weekly</option>
                  <option value="1M">Monthly</option>
                  <option value="3M">3-Month</option>
                  <option value="6M">6-Month</option>
                </select>
              </div>
              {report && (
                <div className="flex items-center gap-2 flex-wrap">
                <button
                    onClick={() => exportReport('txt')}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    title="Export as Text"
                >
                  <ArrowDownTrayIcon className="h-5 w-5" />
                    Export TXT
                </button>
                  <button
                    onClick={() => exportReport('pdf')}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    title="Export Structured PDF"
                  >
                    <DocumentTextIcon className="h-5 w-5" />
                    Export PDF
                  </button>
                  <button
                    onClick={exportFullPagePdf}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    title="Download full page PDF"
                  >
                    <ChartBarIcon className="h-5 w-5" />
                    Full Page PDF
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 5Y Projections & DCF (Scenario + Sensitivity) */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-start justify-between gap-4 flex-col lg:flex-row">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
                <ChartPieIcon className="h-6 w-6 text-blue-600" />
                5Y Projections &amp; DCF (Scenario + Sensitivity)
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                This section is independent of the research report generation. Click Recalculate to run projections.
              </p>
            </div>
            <button
              onClick={fetchProjections}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-colors"
            >
              Recalculate
            </button>
          </div>

          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Assumptions</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Years (max 5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={projectionAssumptions.years}
                    onChange={(e) =>
                      setProjectionAssumptions((p) => ({ ...p, years: Math.max(1, Math.min(5, Number(e.target.value))) }))
                    }
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Base discount rate</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.base_discount_rate}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, base_discount_rate: Number(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Base terminal growth</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.base_terminal_growth}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, base_terminal_growth: Number(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">EPS → FCF ratio</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.eps_to_fcf_ratio}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, eps_to_fcf_ratio: Number(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Override base growth (optional)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.base_growth_override}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, base_growth_override: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                    placeholder="e.g. 0.10"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Override profit margin (optional)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.base_profit_margin_override}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, base_profit_margin_override: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                    placeholder="e.g. 0.18"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Bull growth delta</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.bull_growth_delta}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, bull_growth_delta: Number(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Bear growth delta</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.bear_growth_delta}
                    onChange={(e) => setProjectionAssumptions((p) => ({ ...p, bear_growth_delta: Number(e.target.value) }))}
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                </div>
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Output</div>
              {loadingProjections ? (
                <div className="text-sm text-gray-600 dark:text-gray-400">Loading projections…</div>
              ) : projectionsError ? (
                <div className="text-sm text-red-600 dark:text-red-400">{projectionsError}</div>
              ) : !projections ? (
                <div className="text-sm text-gray-600 dark:text-gray-400">Click Recalculate to generate projections.</div>
              ) : projections?.success === false ? (
                <div className="text-sm text-amber-700 dark:text-amber-300">{projections?.message || 'Projections unavailable'}</div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                      <div className="text-sm text-gray-600 dark:text-gray-400">DCF Band (per share)</div>
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                        Bear: <span className="font-bold">₹{projections.dcf_band?.bear ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Base: <span className="font-bold">₹{projections.dcf_band?.base ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Bull: <span className="font-bold">₹{projections.dcf_band?.bull ?? '—'}</span>
                      </div>
                    </div>
                    <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Base assumptions (auto)</div>
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                        Growth: <span className="font-semibold">{projections.scenarios?.base?.assumptions?.revenue_growth ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Discount: <span className="font-semibold">{projections.scenarios?.base?.assumptions?.discount_rate ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Terminal g: <span className="font-semibold">{projections.scenarios?.base?.assumptions?.terminal_growth ?? '—'}</span>
                      </div>
                    </div>
                    <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                      <div className="text-sm text-gray-600 dark:text-gray-400">History summary</div>
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                        Revenue CAGR: <span className="font-semibold">{projections.history_summary?.rev_cagr ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Profit CAGR: <span className="font-semibold">{projections.history_summary?.profit_cagr ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        EPS CAGR: <span className="font-semibold">{projections.history_summary?.eps_cagr ?? '—'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="overflow-x-auto mb-6">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-600 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                          <th className="py-2 pr-4">Year</th>
                          <th className="py-2 pr-4">Revenue</th>
                          <th className="py-2 pr-4">Net Profit</th>
                          <th className="py-2 pr-4">EPS</th>
                          <th className="py-2 pr-4">FCF/Share</th>
                          <th className="py-2 pr-4">Profit Margin</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(projections.scenarios?.base?.projection || []).map((row: any) => (
                          <tr key={row.year} className="border-b border-gray-100 dark:border-gray-700">
                            <td className="py-2 pr-4 font-medium text-gray-900 dark:text-white">{row.year}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">
                              {row.revenue?.toLocaleString?.('en-IN') ?? row.revenue}
                            </td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">
                              {row.net_profit?.toLocaleString?.('en-IN') ?? row.net_profit}
                            </td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.eps}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.fcf_per_share}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.profit_margin}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {projections?.sensitivity?.terminal_growth_vs_discount &&
                      renderSensitivityHeatmap(
                        projections.sensitivity.terminal_growth_vs_discount,
                        'Sensitivity: Terminal growth vs Discount rate',
                        'terminal_growth'
                      )}
                    {projections?.sensitivity?.growth_vs_discount &&
                      renderSensitivityHeatmap(
                        projections.sensitivity.growth_vs_discount,
                        'Sensitivity: Growth vs Discount rate',
                        'growth_rate'
                      )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Generating research report for {symbol}...</p>
          </div>
        ) : report && report.symbol ? (
          <div className="space-y-6" ref={reportRef}>
            {/* Recommendation Banner */}
            {report.sections?.recommendation && report.symbol && (
              <div className={`rounded-lg shadow-lg p-6 border-2 ${
                report.sections.recommendation.recommendation === 'BUY' ? 'bg-green-50 dark:bg-green-900/20 border-green-500' :
                report.sections.recommendation.recommendation === 'SELL' ? 'bg-red-50 dark:bg-red-900/20 border-red-500' :
                'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                      {report.sections.recommendation?.recommendation || 'HOLD'} - <ClickableSymbol symbol={report.symbol.toUpperCase()} variant="bold" className="text-2xl" />
                    </h2>
                    <p className="text-gray-700 dark:text-gray-300">
                      Current Price: ₹{report.current_price != null ? report.current_price.toFixed(2) : 'N/A'} | 
                      Confidence: {report.sections.recommendation?.confidence || 0}%
                      {report.sections.recommendation?.target_price != null && typeof report.sections.recommendation.target_price === 'number' && (
                        <> | Target: ₹{report.sections.recommendation.target_price.toFixed(2)}</>
                      )}
                      {report.sections.recommendation?.potential_upside != null && typeof report.sections.recommendation.potential_upside === 'number' && (
                        <> | Upside: {report.sections.recommendation.potential_upside.toFixed(2)}%</>
                      )}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                      {report.sections.recommendation?.summary || 'No summary available'}
                    </p>
                  </div>
                  <div className="text-6xl font-bold opacity-20">
                    {report.sections.recommendation?.recommendation || 'HOLD'}
                  </div>
                </div>
              </div>
            )}

            {/* Executive Summary */}
            {report.sections.executive_summary && report.sections.executive_summary.has_data && (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg shadow-lg p-6 mb-6 border-l-4 border-blue-600">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <DocumentTextIcon className="h-6 w-6 text-blue-600" />
                  Executive Summary
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {report.sections.executive_summary.summary}
                </p>
              </div>
            )}

            {/* Quick Actions */}
            {report && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={async () => {
                      try {
                        // First get or create default watchlist, then add symbol
                        const watchlistResponse = await httpClient.post(`/api/enhanced-charting/watchlists`, {
                          name: 'Default',
                          symbols: [report.symbol]
                        });
                        if (watchlistResponse.success) {
                          toast.success(`Added ${report.symbol} to watchlist`);
                        } else {
                          // Try adding to existing watchlist
                          const addResponse = await httpClient.post(`/api/enhanced-charting/watchlists/1/symbols`, {
                            symbols: [report.symbol]
                          });
                          if (addResponse.success) {
                            toast.success(`Added ${report.symbol} to watchlist`);
                          } else {
                            toast.error(addResponse.message || 'Failed to add to watchlist');
                          }
                        }
                      } catch (error: any) {
                        toast.error(error?.message || 'Failed to add to watchlist');
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <StarIcon className="h-5 w-5" />
                    Add to Watchlist
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const response = await httpClient.post(`/api/enhanced-charting/alerts/create`, {
                          symbol: report.symbol,
                          condition_type: 'price',
                          operator: 'above',
                          value: report.current_price * 1.05,
                          name: `${report.symbol} Price Alert`
                        });
                        if (response.success) {
                          toast.success(`Alert created for ${report.symbol}`);
                        } else {
                          toast.error(response.message || 'Failed to create alert');
                        }
                      } catch (error: any) {
                        toast.error(error?.message || 'Failed to create alert');
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <BellIcon className="h-5 w-5" />
                    Set Price Alert
                  </button>
                </div>
              </div>
            )}

            {/* Key Metrics Dashboard */}
            {report.sections.key_metrics_dashboard && report.sections.key_metrics_dashboard.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-purple-600" />
                  Key Metrics Dashboard
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {Object.entries(report.sections.key_metrics_dashboard.metrics).map(([key, value]) => (
                    value !== null && value !== undefined && (
                      <div key={key} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                        <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 capitalize">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white">
                          {typeof value === 'number' && value != null ? (
                            key.includes('cap') || key.includes('revenue') || key.includes('profit') ? 
                              `₹${value.toFixed(2)} Cr` :
                              key.includes('margin') || key.includes('growth') || key.includes('roe') || key.includes('roce') ?
                              `${value.toFixed(2)}%` :
                              value.toFixed(2)
                          ) : value != null ? value : 'N/A'}
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Risk Indicators */}
            {report.sections.risk_indicators && report.sections.risk_indicators.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ExclamationTriangleIcon className="h-6 w-6 text-orange-600" />
                  Risk Indicators
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {Object.entries(report.sections.risk_indicators.indicators).map(([key, indicator]: [string, any]) => (
                    <div key={key} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-2 capitalize">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          indicator.color === 'green' ? 'bg-green-500' :
                          indicator.color === 'yellow' ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`} />
                        <span className={`text-sm font-semibold ${
                          indicator.color === 'green' ? 'text-green-700 dark:text-green-400' :
                          indicator.color === 'yellow' ? 'text-yellow-700 dark:text-yellow-400' :
                          'text-red-700 dark:text-red-400'
                        }`}>
                          {indicator.level.toUpperCase()}
                        </span>
                      </div>
                      {indicator.value !== undefined && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Value: {typeof indicator.value === 'number' && indicator.value != null ? indicator.value.toFixed(2) : indicator.value}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Comparison Table */}
            {report.sections.comparison_table && report.sections.comparison_table.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TableCellsIcon className="h-6 w-6 text-indigo-600" />
                  Comparison: Current vs Previous
                </h3>
                {report.sections.comparison_table.comparison.quarterly && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quarterly Comparison</h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Metric</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Current Quarter</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Previous Quarter</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Change</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {report.sections.comparison_table.comparison.quarterly.current.revenue != null && (
                            <tr>
                              <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">Revenue</td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.current.revenue != null ? report.sections.comparison_table.comparison.quarterly.current.revenue.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.previous.revenue != null ? report.sections.comparison_table.comparison.quarterly.previous.revenue.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className={`px-4 py-3 text-sm font-semibold ${
                                (report.sections.comparison_table.comparison.quarterly.revenue_change_pct || 0) >= 0 
                                  ? 'text-green-600 dark:text-green-400' 
                                  : 'text-red-600 dark:text-red-400'
                              }`}>
                                {report.sections.comparison_table.comparison.quarterly.revenue_change_pct != null 
                                  ? `${report.sections.comparison_table.comparison.quarterly.revenue_change_pct >= 0 ? '+' : ''}${report.sections.comparison_table.comparison.quarterly.revenue_change_pct.toFixed(2)}%`
                                  : 'N/A'}
                              </td>
                            </tr>
                          )}
                          {report.sections.comparison_table.comparison.quarterly.current.net_profit != null && (
                            <tr>
                              <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">Net Profit</td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.current.net_profit != null ? report.sections.comparison_table.comparison.quarterly.current.net_profit.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.previous.net_profit != null ? report.sections.comparison_table.comparison.quarterly.previous.net_profit.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className={`px-4 py-3 text-sm font-semibold ${
                                (report.sections.comparison_table.comparison.quarterly.profit_change_pct || 0) >= 0 
                                  ? 'text-green-600 dark:text-green-400' 
                                  : 'text-red-600 dark:text-red-400'
                              }`}>
                                {report.sections.comparison_table.comparison.quarterly.profit_change_pct != null 
                                  ? `${report.sections.comparison_table.comparison.quarterly.profit_change_pct >= 0 ? '+' : ''}${report.sections.comparison_table.comparison.quarterly.profit_change_pct.toFixed(2)}%`
                                  : 'N/A'}
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Financial Trends Charts */}
            {report.sections.financial_trends && report.sections.financial_trends.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-teal-600" />
                  Financial Trends
                </h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {report.sections.financial_trends.trends.quarterly && report.sections.financial_trends.trends.quarterly.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quarterly Revenue & Profit</h4>
                      <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                        <div ref={revenueProfitChartRef} className="w-full h-full" />
                      </div>
                      <div className="mt-2 flex items-center justify-center gap-4 text-xs">
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-blue-500 rounded"></div>
                          <span className="text-gray-600 dark:text-gray-400">Revenue (₹ Cr)</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-green-500 rounded"></div>
                          <span className="text-gray-600 dark:text-gray-400">Net Profit (₹ Cr)</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {report.sections.financial_trends.trends.quarterly && report.sections.financial_trends.trends.quarterly.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quarterly Margins</h4>
                      <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                        <div ref={marginsChartRef} className="w-full h-full" />
                      </div>
                      <div className="mt-2 flex items-center justify-center gap-4 text-xs">
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-purple-500 rounded"></div>
                          <span className="text-gray-600 dark:text-gray-400">Net Margin (%)</span>
                        </div>
                        {report.sections.financial_trends.trends.quarterly.some((q: any) => q.operating_margin !== null && q.operating_margin !== undefined) && (
                          <div className="flex items-center gap-1">
                            <div className="w-3 h-3 bg-orange-500 rounded"></div>
                            <span className="text-gray-600 dark:text-gray-400">Operating Margin (%)</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Executive Summary */}
            {report.sections.executive_summary && report.sections.executive_summary.has_data && (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg shadow-lg p-6 mb-6 border-l-4 border-blue-600">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <DocumentTextIcon className="h-6 w-6 text-blue-600" />
                  Executive Summary
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {report.sections.executive_summary.summary}
                </p>
              </div>
            )}

            {/* Quick Actions */}
            {report && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={async () => {
                      try {
                        const watchlistResponse = await httpClient.post(`/api/enhanced-charting/watchlists`, {
                          name: 'Default',
                          symbols: [report.symbol]
                        });
                        if (watchlistResponse.success) {
                          toast.success(`Added ${report.symbol} to watchlist`);
                        } else {
                          const addResponse = await httpClient.post(`/api/enhanced-charting/watchlists/1/symbols`, {
                            symbols: [report.symbol]
                          });
                          if (addResponse.success) {
                            toast.success(`Added ${report.symbol} to watchlist`);
                          } else {
                            toast.error(addResponse.message || 'Failed to add to watchlist');
                          }
                        }
                      } catch (error: any) {
                        toast.error(error?.message || 'Failed to add to watchlist');
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <StarIcon className="h-5 w-5" />
                    Add to Watchlist
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const response = await httpClient.post(`/api/enhanced-charting/alerts/create`, {
                          symbol: report.symbol,
                          condition_type: 'price',
                          operator: 'above',
                          value: report.current_price * 1.05,
                          name: `${report.symbol} Price Alert`
                        });
                        if (response.success) {
                          toast.success(`Alert created for ${report.symbol}`);
                        } else {
                          toast.error(response.message || 'Failed to create alert');
                        }
                      } catch (error: any) {
                        toast.error(error?.message || 'Failed to create alert');
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <BellIcon className="h-5 w-5" />
                    Set Price Alert
                  </button>
                </div>
              </div>
            )}

            {/* Key Metrics Dashboard */}
            {report.sections.key_metrics_dashboard && report.sections.key_metrics_dashboard.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-purple-600" />
                  Key Metrics Dashboard
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {Object.entries(report.sections.key_metrics_dashboard.metrics).map(([key, value]) => (
                    value !== null && value !== undefined && (
                      <div key={key} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                        <div className="text-xs text-gray-600 dark:text-gray-400 mb-1 capitalize">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white">
                          {typeof value === 'number' && value != null ? (
                            key.includes('cap') || key.includes('revenue') || key.includes('profit') ? 
                              `₹${value.toFixed(2)} Cr` :
                              key.includes('margin') || key.includes('growth') || key.includes('roe') || key.includes('roce') ?
                              `${value.toFixed(2)}%` :
                              value.toFixed(2)
                          ) : value != null ? value : 'N/A'}
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Risk Indicators */}
            {report.sections.risk_indicators && report.sections.risk_indicators.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ExclamationTriangleIcon className="h-6 w-6 text-orange-600" />
                  Risk Indicators
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {Object.entries(report.sections.risk_indicators.indicators).map(([key, indicator]: [string, any]) => (
                    <div key={key} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-2 capitalize">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          indicator.color === 'green' ? 'bg-green-500' :
                          indicator.color === 'yellow' ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`} />
                        <span className={`text-sm font-semibold ${
                          indicator.color === 'green' ? 'text-green-700 dark:text-green-400' :
                          indicator.color === 'yellow' ? 'text-yellow-700 dark:text-yellow-400' :
                          'text-red-700 dark:text-red-400'
                        }`}>
                          {indicator.level.toUpperCase()}
                        </span>
                      </div>
                      {indicator.value !== undefined && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Value: {typeof indicator.value === 'number' && indicator.value != null ? indicator.value.toFixed(2) : indicator.value}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Comparison Table */}
            {report.sections.comparison_table && report.sections.comparison_table.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TableCellsIcon className="h-6 w-6 text-indigo-600" />
                  Comparison: Current vs Previous
                </h3>
                {report.sections.comparison_table.comparison.quarterly && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quarterly Comparison</h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Metric</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Current Quarter</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Previous Quarter</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Change</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {report.sections.comparison_table.comparison.quarterly.current.revenue != null && (
                            <tr>
                              <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">Revenue</td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.current.revenue != null ? report.sections.comparison_table.comparison.quarterly.current.revenue.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.previous.revenue != null ? report.sections.comparison_table.comparison.quarterly.previous.revenue.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className={`px-4 py-3 text-sm font-semibold ${
                                (report.sections.comparison_table.comparison.quarterly.revenue_change_pct || 0) >= 0 
                                  ? 'text-green-600 dark:text-green-400' 
                                  : 'text-red-600 dark:text-red-400'
                              }`}>
                                {report.sections.comparison_table.comparison.quarterly.revenue_change_pct != null 
                                  ? `${report.sections.comparison_table.comparison.quarterly.revenue_change_pct >= 0 ? '+' : ''}${report.sections.comparison_table.comparison.quarterly.revenue_change_pct.toFixed(2)}%`
                                  : 'N/A'}
                              </td>
                            </tr>
                          )}
                          {report.sections.comparison_table.comparison.quarterly.current.net_profit != null && (
                            <tr>
                              <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">Net Profit</td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.current.net_profit != null ? report.sections.comparison_table.comparison.quarterly.current.net_profit.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                ₹{report.sections.comparison_table.comparison.quarterly.previous.net_profit != null ? report.sections.comparison_table.comparison.quarterly.previous.net_profit.toFixed(2) : 'N/A'} Cr
                              </td>
                              <td className={`px-4 py-3 text-sm font-semibold ${
                                (report.sections.comparison_table.comparison.quarterly.profit_change_pct || 0) >= 0 
                                  ? 'text-green-600 dark:text-green-400' 
                                  : 'text-red-600 dark:text-red-400'
                              }`}>
                                {report.sections.comparison_table.comparison.quarterly.profit_change_pct != null 
                                  ? `${report.sections.comparison_table.comparison.quarterly.profit_change_pct >= 0 ? '+' : ''}${report.sections.comparison_table.comparison.quarterly.profit_change_pct.toFixed(2)}%`
                                  : 'N/A'}
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Financial Ratios Summary */}
            {report.sections.financial_ratios && report.sections.financial_ratios.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <CurrencyDollarIcon className="h-6 w-6 text-blue-600" />
                  Financial Ratios
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.financial_ratios.summary}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(report.sections.financial_ratios.ratios).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400 capitalize">{key.replace('_', ' ')}</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {typeof value === 'number' && value != null ? (
                          key.includes('cap') || key.includes('price') ? 
                            `₹${(value / 10000).toFixed(2)} Cr` : 
                            value.toFixed(2)
                        ) : value != null ? value : 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detailed Company Research */}
            {report.sections.detailed_company_research && report.sections.detailed_company_research.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <DocumentTextIcon className="h-6 w-6 text-purple-600" />
                  Detailed Company Research
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">{report.sections.detailed_company_research.summary}</p>
                
                {report.sections.detailed_company_research.sections?.map((section, idx) => (
                  <div key={idx} className="mb-8 last:mb-0">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 border-b border-gray-200 dark:border-gray-700 pb-2">
                      {section.title}
                    </h4>
                    
                    {/* Company Overview */}
                    {section.type === 'company_overview' && (
                      <div className="space-y-4">
                        {section.content && (
                          <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                            {section.content}
                          </p>
                        )}
                        {section.achievements && section.achievements.length > 0 && (
                          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                            <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Key Achievements:</h5>
                            <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                              {section.achievements.map((achievement, i) => (
                                <li key={i}>{achievement}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Business Segments */}
                    {section.type === 'business_segments' && section.segments && (
                      <div className="space-y-6">
                        {section.segments.map((segment, segIdx) => (
                          <div key={segIdx} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-5 border border-gray-200 dark:border-gray-600">
                            <h5 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">{segment.title}</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                              {segment.revenue && (
                                <div>
                                  <span className="text-sm text-gray-600 dark:text-gray-400">Revenue: </span>
                                  <span className="font-semibold text-gray-900 dark:text-white">{segment.revenue}</span>
                                  {segment.revenue_growth && (
                                    <span className="text-green-600 dark:text-green-400 ml-2">({segment.revenue_growth})</span>
                                  )}
                                </div>
                              )}
                              {segment.ebitda && (
                                <div>
                                  <span className="text-sm text-gray-600 dark:text-gray-400">EBITDA: </span>
                                  <span className="font-semibold text-gray-900 dark:text-white">{segment.ebitda}</span>
                                </div>
                              )}
                              {segment.contribution && (
                                <div>
                                  <span className="text-sm text-gray-600 dark:text-gray-400">Contribution: </span>
                                  <span className="font-semibold text-gray-900 dark:text-white">{segment.contribution}</span>
                                </div>
                              )}
                            </div>
                            {segment.details && typeof segment.details === 'object' && (
                              <div className="mt-4 bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
                                {renderNestedDetails(segment.details)}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Strategic Initiatives */}
                    {section.type === 'strategic_initiatives' && section.initiatives && (
                      <div className="space-y-4">
                        {Object.entries(section.initiatives).map(([key, initiative]: [string, any]) => (
                          <div key={key} className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                            <h5 className="font-semibold text-gray-900 dark:text-white mb-2">{initiative.title}</h5>
                            {initiative.highlights && Array.isArray(initiative.highlights) && (
                              <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                                {initiative.highlights.map((highlight: string, i: number) => (
                                  <li key={i}>{highlight}</li>
                                ))}
                              </ul>
                            )}
                            {initiative.valuation && (
                              <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                                <span className="font-medium">Valuation: </span>{initiative.valuation}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Competitive Analysis */}
                    {section.type === 'competitive_analysis' && section.analysis && (
                      <div className="space-y-4">
                        {Object.entries(section.analysis).map(([key, comp]: [string, any]) => (
                          <div key={key} className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                            <h5 className="font-semibold text-gray-900 dark:text-white mb-3">{comp.title}</h5>
                            {comp.jio && (
                              <div className="mb-3">
                                <h6 className="font-medium text-gray-900 dark:text-white mb-1">Jio:</h6>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300 ml-4">
                                  {Object.entries(comp.jio).map(([k, v]: [string, any]) => (
                                    <li key={k}><span className="capitalize">{k.replace(/_/g, ' ')}: </span>{String(v)}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {comp.airtel && (
                              <div>
                                <h6 className="font-medium text-gray-900 dark:text-white mb-1">Airtel:</h6>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300 ml-4">
                                  {Object.entries(comp.airtel).map(([k, v]: [string, any]) => (
                                    <li key={k}><span className="capitalize">{k.replace(/_/g, ' ')}: </span>{String(v)}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Macro Context */}
                    {section.type === 'macro_context' && section.context && (
                      <div className="space-y-4">
                        {Object.entries(section.context).map(([key, macro]: [string, any]) => (
                          <div key={key} className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4">
                            <h5 className="font-semibold text-gray-900 dark:text-white mb-2">{macro.title}</h5>
                            {macro.q1_fy26 && (
                              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                                <span className="font-medium">Q1 FY26: </span>{macro.q1_fy26}
                              </p>
                            )}
                            {macro.key_drivers && (
                              <div className="mb-2">
                                <h6 className="font-medium text-gray-900 dark:text-white mb-1">Key Drivers:</h6>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300 ml-4">
                                  {Object.entries(macro.key_drivers).map(([k, v]: [string, any]) => (
                                    <li key={k}><span className="capitalize">{k.replace(/_/g, ' ')}: </span>{String(v)}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {macro.risks && Array.isArray(macro.risks) && (
                              <div>
                                <h6 className="font-medium text-gray-900 dark:text-white mb-1">Risks:</h6>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300 ml-4">
                                  {macro.risks.map((risk: string, i: number) => (
                                    <li key={i}>{risk}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Screener Data Sections */}
                {report.sections.detailed_company_research.full_research?.screener_data && (
                  <div className="mt-8 space-y-6">
                    {/* Growth Metrics */}
                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics && (
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                          <ArrowTrendingUpIcon className="h-5 w-5 text-blue-600" />
                          Growth Metrics (Screener.in)
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                          {/* Compounded Sales Growth */}
                          <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Compounded Sales Growth</h5>
                            <div className="space-y-2">
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_10y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">10 Years:</span>
                                  <span className="text-sm font-bold text-gray-900 dark:text-white">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_10y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_5y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">5 Years:</span>
                                  <span className="text-sm font-bold text-gray-900 dark:text-white">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_5y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_3y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">3 Years:</span>
                                  <span className="text-sm font-bold text-gray-900 dark:text-white">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_3y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_ttm != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">TTM:</span>
                                  <span className="text-sm font-bold text-gray-900 dark:text-white">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.sales_growth_ttm.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Compounded Profit Growth */}
                          <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Compounded Profit Growth</h5>
                            <div className="space-y-2">
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_10y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">10 Years:</span>
                                  <span className="text-sm font-bold text-green-600 dark:text-green-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_10y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_5y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">5 Years:</span>
                                  <span className="text-sm font-bold text-green-600 dark:text-green-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_5y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_3y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">3 Years:</span>
                                  <span className="text-sm font-bold text-green-600 dark:text-green-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_3y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_ttm != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">TTM:</span>
                                  <span className="text-sm font-bold text-green-600 dark:text-green-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.profit_growth_ttm.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Stock Price CAGR */}
                          <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Stock Price CAGR</h5>
                            <div className="space-y-2">
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_10y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">10 Years:</span>
                                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_10y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_5y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">5 Years:</span>
                                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_5y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_3y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">3 Years:</span>
                                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_3y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_1y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">1 Year:</span>
                                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.price_cagr_1y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Return on Equity */}
                          <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                            <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Return on Equity (ROE)</h5>
                            <div className="space-y-2">
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_10y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">10 Years:</span>
                                  <span className="text-sm font-bold text-orange-600 dark:text-orange-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_10y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_5y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">5 Years:</span>
                                  <span className="text-sm font-bold text-orange-600 dark:text-orange-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_5y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_3y != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">3 Years:</span>
                                  <span className="text-sm font-bold text-orange-600 dark:text-orange-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_3y.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                              {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_last_year != null && (
                                <div className="flex justify-between">
                                  <span className="text-xs text-gray-600 dark:text-gray-400">Last Year:</span>
                                  <span className="text-sm font-bold text-orange-600 dark:text-orange-400">
                                    {report.sections.detailed_company_research.full_research.screener_data.growth_metrics.roe_last_year.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Balance Sheet */}
                    {report.sections.detailed_company_research.full_research.screener_data.balance_sheet && 
                     report.sections.detailed_company_research.full_research.screener_data.balance_sheet.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                          <TableCellsIcon className="h-5 w-5 text-green-600" />
                          Balance Sheet (Screener.in)
                        </h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-200 dark:border-gray-700">
                                <th className="text-left p-3 font-semibold text-gray-900 dark:text-white">Period</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Equity Capital (₹ Cr)</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Reserves (₹ Cr)</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Borrowings (₹ Cr)</th>
                              </tr>
                            </thead>
                            <tbody>
                              {report.sections.detailed_company_research.full_research.screener_data.balance_sheet.slice(0, 10).map((bs: any, idx: number) => (
                                <tr key={idx} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700">
                                  <td className="p-3 text-gray-900 dark:text-white font-medium">{bs.period}</td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {bs.equity_capital ? `₹${(bs.equity_capital / 10000).toFixed(2)}` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {bs.reserves ? `₹${(bs.reserves / 10000).toFixed(2)}` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {bs.borrowings ? `₹${(bs.borrowings / 10000).toFixed(2)}` : 'N/A'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    
                    {/* Cash Flows */}
                    {report.sections.detailed_company_research.full_research.screener_data.cash_flows && 
                     report.sections.detailed_company_research.full_research.screener_data.cash_flows.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                          <CurrencyDollarIcon className="h-5 w-5 text-blue-600" />
                          Cash Flows (Screener.in)
                        </h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-200 dark:border-gray-700">
                                <th className="text-left p-3 font-semibold text-gray-900 dark:text-white">Period</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Operating CF (₹ Cr)</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Investing CF (₹ Cr)</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Financing CF (₹ Cr)</th>
                              </tr>
                            </thead>
                            <tbody>
                              {report.sections.detailed_company_research.full_research.screener_data.cash_flows.slice(0, 10).map((cf: any, idx: number) => (
                                <tr key={idx} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700">
                                  <td className="p-3 text-gray-900 dark:text-white font-medium">{cf.period}</td>
                                  <td className={`p-3 text-right font-medium ${
                                    cf.operating_cash_flow && cf.operating_cash_flow >= 0 
                                      ? 'text-green-600 dark:text-green-400' 
                                      : 'text-red-600 dark:text-red-400'
                                  }`}>
                                    {cf.operating_cash_flow ? `₹${(cf.operating_cash_flow / 10000).toFixed(2)}` : 'N/A'}
                                  </td>
                                  <td className={`p-3 text-right font-medium ${
                                    cf.investing_cash_flow && cf.investing_cash_flow >= 0 
                                      ? 'text-green-600 dark:text-green-400' 
                                      : 'text-red-600 dark:text-red-400'
                                  }`}>
                                    {cf.investing_cash_flow ? `₹${(cf.investing_cash_flow / 10000).toFixed(2)}` : 'N/A'}
                                  </td>
                                  <td className={`p-3 text-right font-medium ${
                                    cf.financing_cash_flow && cf.financing_cash_flow >= 0 
                                      ? 'text-green-600 dark:text-green-400' 
                                      : 'text-red-600 dark:text-red-400'
                                  }`}>
                                    {cf.financing_cash_flow ? `₹${(cf.financing_cash_flow / 10000).toFixed(2)}` : 'N/A'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                    
                    {/* Shareholding Pattern */}
                    {report.sections.detailed_company_research.full_research.screener_data.detailed_shareholding && 
                     report.sections.detailed_company_research.full_research.screener_data.detailed_shareholding.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                          <ChartPieIcon className="h-5 w-5 text-purple-600" />
                          Shareholding Pattern (Screener.in)
                        </h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-200 dark:border-gray-700">
                                <th className="text-left p-3 font-semibold text-gray-900 dark:text-white">Period</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Promoters</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">FIIs</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">DIIs</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Government</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Public</th>
                                <th className="text-right p-3 font-semibold text-gray-900 dark:text-white">Shareholders</th>
                              </tr>
                            </thead>
                            <tbody>
                              {report.sections.detailed_company_research.full_research.screener_data.detailed_shareholding.slice(0, 12).map((sh: any, idx: number) => (
                                <tr key={idx} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700">
                                  <td className="p-3 text-gray-900 dark:text-white font-medium">{sh.period}</td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {sh.promoters ? `${sh.promoters.toFixed(2)}%` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {sh.fiis ? `${sh.fiis.toFixed(2)}%` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {sh.diis ? `${sh.diis.toFixed(2)}%` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {sh.government ? `${sh.government.toFixed(2)}%` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {sh.public ? `${sh.public.toFixed(2)}%` : 'N/A'}
                                  </td>
                                  <td className="p-3 text-right text-gray-700 dark:text-gray-300">
                                    {sh.no_of_shareholders ? sh.no_of_shareholders.toLocaleString() : 'N/A'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Quarterly P&L Analysis */}
            {report.sections.quarterly_pl && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <TableCellsIcon className="h-6 w-6 text-green-600" />
                  Quarterly P&L Analysis
                </h3>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                  Debug: has_data={String(!!report.sections.quarterly_pl.has_data)} • quarters=
                  {String(report.sections.quarterly_pl.quarters?.length ?? 0)}
                </div>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.quarterly_pl.summary}</p>

                {(report.sections.quarterly_pl as any).ratios_snapshot && Object.keys((report.sections.quarterly_pl as any).ratios_snapshot).length > 0 && (
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700 mb-4">
                    <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Debt ratios snapshot</div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      {(report.sections.quarterly_pl as any).ratios_snapshot.as_of_period_end && (
                        <div className="text-gray-700 dark:text-gray-200">
                          <span className="text-gray-500 dark:text-gray-400">As of:</span>{' '}
                          {new Date((report.sections.quarterly_pl as any).ratios_snapshot.as_of_period_end).toLocaleDateString()}
                        </div>
                      )}
                      {(report.sections.quarterly_pl as any).ratios_snapshot.debt_to_equity != null && (
                        <div className="text-gray-700 dark:text-gray-200">
                          <span className="text-gray-500 dark:text-gray-400">Debt/Equity:</span>{' '}
                          {!isNaN(Number((report.sections.quarterly_pl as any).ratios_snapshot.debt_to_equity)) ? Number((report.sections.quarterly_pl as any).ratios_snapshot.debt_to_equity).toFixed(2) : 'N/A'}
                        </div>
                      )}
                      {(report.sections.quarterly_pl as any).ratios_snapshot.current_ratio != null && (
                        <div className="text-gray-700 dark:text-gray-200">
                          <span className="text-gray-500 dark:text-gray-400">Current ratio:</span>{' '}
                          {!isNaN(Number((report.sections.quarterly_pl as any).ratios_snapshot.current_ratio)) ? Number((report.sections.quarterly_pl as any).ratios_snapshot.current_ratio).toFixed(2) : 'N/A'}
                        </div>
                      )}
                      {(report.sections.quarterly_pl as any).ratios_snapshot.operating_margin != null && (
                        <div className="text-gray-700 dark:text-gray-200">
                          <span className="text-gray-500 dark:text-gray-400">Op. margin:</span>{' '}
                          {!isNaN(Number((report.sections.quarterly_pl as any).ratios_snapshot.operating_margin)) ? Number((report.sections.quarterly_pl as any).ratios_snapshot.operating_margin).toFixed(2) : 'N/A'}%
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {report.sections.quarterly_pl.has_data ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left p-2">Period</th>
                          <th className="text-right p-2">Revenue</th>
                          <th className="text-right p-2">Net Profit</th>
                          <th className="text-right p-2">EPS</th>
                          <th className="text-right p-2">Net Margin</th>
                          <th className="text-right p-2">Op Margin</th>
                          <th className="text-right p-2">D/E</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.sections.quarterly_pl.quarters.slice(0, 8).map((q, idx) => (
                          <tr key={idx} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="p-2">{q.period}</td>
                            <td className="text-right p-2">{q.revenue ? `₹${(q.revenue / 10000).toFixed(2)} Cr` : 'N/A'}</td>
                            <td className="text-right p-2">{q.net_profit ? `₹${(q.net_profit / 10000).toFixed(2)} Cr` : 'N/A'}</td>
                            <td className="text-right p-2">{q.eps ? `₹${q.eps.toFixed(2)}` : 'N/A'}</td>
                            <td className="text-right p-2">{q.net_margin_pct != null ? `${Number(q.net_margin_pct).toFixed(2)}%` : 'N/A'}</td>
                            <td className="text-right p-2">{q.operating_margin_pct != null ? `${Number(q.operating_margin_pct).toFixed(2)}%` : 'N/A'}</td>
                            <td className="text-right p-2">{q.debt_to_equity != null ? Number(q.debt_to_equity).toFixed(2) : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                    <div className="flex items-start gap-3">
                      <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-2">
                          No quarterly financial rows found in DB for this symbol.
                        </p>
                        <p className="text-xs text-amber-700 dark:text-amber-300 mb-3">
                          Run quarterly financial sync/import first to view financial data.
                        </p>
                        <button
                          onClick={async () => {
                            try {
                              toast.loading(`Syncing financial data for ${symbol}...`, { id: 'sync-financial' });
                              const response = await httpClient.post(`/api/financial-data/sync/stock-financial-data/${symbol}`);
                              const responseData = response.data as any;
                              if (responseData?.success) {
                                toast.success(`Financial data sync completed for ${symbol}`, { id: 'sync-financial' });
                                // Reload the report after sync
                                setTimeout(() => {
                                  window.location.reload();
                                }, 2000);
                              } else {
                                toast.error(responseData?.message || 'Sync failed', { id: 'sync-financial' });
                              }
                            } catch (error: any) {
                              const errorMsg = error.response?.data?.detail || error.message || 'Failed to sync financial data';
                              toast.error(errorMsg, { id: 'sync-financial' });
                            }
                          }}
                          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-md transition-colors duration-200 flex items-center gap-2"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                          Sync Financial Data for {symbol}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Yearly P&L Analysis */}
            {report.sections.yearly_pl && report.sections.yearly_pl.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-purple-600" />
                  Yearly P&L Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.yearly_pl.summary}</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left p-2">Year</th>
                        <th className="text-right p-2">Revenue</th>
                        <th className="text-right p-2">Net Profit</th>
                        <th className="text-right p-2">EPS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.sections.yearly_pl.years.map((y, idx) => (
                        <tr key={idx} className="border-b border-gray-100 dark:border-gray-800">
                          <td className="p-2">{y.year}</td>
                          <td className="text-right p-2">{y.revenue ? `₹${(y.revenue / 10000).toFixed(2)} Cr` : 'N/A'}</td>
                          <td className="text-right p-2">{y.net_profit ? `₹${(y.net_profit / 10000).toFixed(2)} Cr` : 'N/A'}</td>
                          <td className="text-right p-2">{y.eps ? `₹${y.eps.toFixed(2)}` : 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Chart Pattern Analysis with Visual Chart */}
            {report.sections.chart_patterns && report.sections.chart_patterns.has_patterns && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartPieIcon className="h-6 w-6 text-orange-600" />
                  Chart Pattern Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.chart_patterns.summary}</p>
                
                {/* Pattern Details */}
                {report.sections.chart_patterns.primary_pattern && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-4">
                    <div className="font-semibold text-lg text-gray-900 dark:text-white">
                      {report.sections.chart_patterns.primary_pattern.pattern_name}
                    </div>
                    <div className="mt-2 space-y-1 text-sm text-gray-700 dark:text-gray-300">
                      <div>
                        Confidence:{' '}
                        {typeof report.sections.chart_patterns.primary_pattern.confidence === 'number'
                          ? `${(report.sections.chart_patterns.primary_pattern.confidence * 100).toFixed(1)}%`
                          : 'N/A'}
                      </div>
                      <div>
                        Target Price:{' '}
                        {typeof report.sections.chart_patterns.primary_pattern.target_price === 'number'
                          ? `₹${report.sections.chart_patterns.primary_pattern.target_price.toFixed(2)}`
                          : 'N/A'}
                      </div>
                      <div>
                        Potential Upside:{' '}
                        {typeof report.sections.chart_patterns.primary_pattern.potential_upside === 'number'
                          ? `${report.sections.chart_patterns.primary_pattern.potential_upside.toFixed(2)}%`
                          : 'N/A'}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Interactive Chart with Pattern Visualization */}
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Interactive Chart with Pattern Lines ({timeframe === '1D' ? 'Daily' : timeframe === '1W' ? 'Weekly' : timeframe === '1M' ? 'Monthly' : timeframe === '3M' ? '3-Month' : timeframe === '6M' ? '6-Month' : timeframe === '1h' ? '1 Hour' : timeframe === '4h' ? '4 Hour' : timeframe === '15m' ? '15 Minute' : timeframe === '5m' ? '5 Minute' : timeframe === '1m' ? '1 Minute' : timeframe === '2m' ? '2 Minute' : timeframe === '3m' ? '3 Minute' : timeframe === '2h' ? '2 Hour' : timeframe} View)
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      Zoom: Mouse Wheel | Pan: Click & Drag
                    </div>
                  </div>
                  <div className="relative h-[500px] rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-[#131722]">
                    {chartLoading && (
                      <div className="absolute inset-0 flex items-center justify-center bg-[#131722]/50 z-10">
                        <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
                      </div>
                    )}
                    <div ref={chartContainerRef} className="w-full h-full" />
                    
                    {/* Pattern Visualization Overlay */}
                    {chartRef.current && candlestickSeriesRef.current && (
                      <PatternVisualization
                        symbol={symbol}
                        timeframe={timeframe}
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        visible={true}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Trading Analysis Sections */}
            
            {/* Trendline Analysis */}
            {report.sections.trendline_analysis && report.sections.trendline_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-blue-600" />
                  Trendline Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.trendline_analysis.summary}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Current Trend</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.trendline_analysis.current_trend || 'N/A'}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Uptrend Lines</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.trendline_analysis.uptrend_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Downtrend Lines</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.trendline_analysis.downtrend_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Channels</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.trendline_analysis.channel_count || 0}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Market Structure Analysis */}
            {report.sections.market_structure_analysis && report.sections.market_structure_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-green-600" />
                  Market Structure Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.market_structure_analysis.summary}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Current Phase</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.market_structure_analysis.current_phase || 'N/A'}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">BOS Events</div>
                    <div className="text-lg font-bold text-green-600">
                      {report.sections.market_structure_analysis.bos_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">CHoCH Events</div>
                    <div className="text-lg font-bold text-orange-600">
                      {report.sections.market_structure_analysis.choch_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Structure Type</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.market_structure_analysis.structure_type || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Support/Resistance Analysis */}
            {report.sections.support_resistance_analysis && report.sections.support_resistance_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TableCellsIcon className="h-6 w-6 text-yellow-600" />
                  Support & Resistance Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.support_resistance_analysis.summary}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Support Levels</div>
                    <div className="text-lg font-bold text-green-600">
                      {report.sections.support_resistance_analysis.support_levels_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Resistance Levels</div>
                    <div className="text-lg font-bold text-red-600">
                      {report.sections.support_resistance_analysis.resistance_levels_count || 0}
                    </div>
                  </div>
                  {report.sections.support_resistance_analysis.nearest_support && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Nearest Support</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        ₹{typeof report.sections.support_resistance_analysis.nearest_support.price === 'number' 
                          ? report.sections.support_resistance_analysis.nearest_support.price.toFixed(2) 
                          : 'N/A'}
                      </div>
                    </div>
                  )}
                  {report.sections.support_resistance_analysis.nearest_resistance && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Nearest Resistance</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        ₹{typeof report.sections.support_resistance_analysis.nearest_resistance.price === 'number' 
                          ? report.sections.support_resistance_analysis.nearest_resistance.price.toFixed(2) 
                          : 'N/A'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Swing Point Analysis */}
            {report.sections.swing_point_analysis && report.sections.swing_point_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-purple-600" />
                  Swing Point Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.swing_point_analysis.summary}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Swing Highs</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.swing_point_analysis.swing_highs_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Swing Lows</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.swing_point_analysis.swing_lows_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Trend</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.swing_point_analysis.trend || 'N/A'}
                    </div>
                  </div>
                  {report.sections.swing_point_analysis.pattern_sequence && report.sections.swing_point_analysis.pattern_sequence.length > 0 && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 col-span-2">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Recent Pattern</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {report.sections.swing_point_analysis.pattern_sequence.slice(-3).join(' → ')}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Supply/Demand Analysis */}
            {report.sections.supply_demand_analysis && report.sections.supply_demand_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <CurrencyDollarIcon className="h-6 w-6 text-pink-600" />
                  Supply & Demand Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.supply_demand_analysis.summary}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Demand Zones</div>
                    <div className="text-lg font-bold text-green-600">
                      {report.sections.supply_demand_analysis.demand_zones_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Supply Zones</div>
                    <div className="text-lg font-bold text-red-600">
                      {report.sections.supply_demand_analysis.supply_zones_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Fresh Demand</div>
                    <div className="text-lg font-bold text-green-600">
                      {report.sections.supply_demand_analysis.fresh_demand_count || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Fresh Supply</div>
                    <div className="text-lg font-bold text-red-600">
                      {report.sections.supply_demand_analysis.fresh_supply_count || 0}
                    </div>
                  </div>
                  {report.sections.supply_demand_analysis.nearest_demand && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Nearest Demand Zone</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        ₹{typeof report.sections.supply_demand_analysis.nearest_demand.price_range?.low === 'number' 
                          ? report.sections.supply_demand_analysis.nearest_demand.price_range.low.toFixed(2) 
                          : 'N/A'} - ₹{typeof report.sections.supply_demand_analysis.nearest_demand.price_range?.high === 'number' 
                          ? report.sections.supply_demand_analysis.nearest_demand.price_range.high.toFixed(2) 
                          : 'N/A'}
                      </div>
                    </div>
                  )}
                  {report.sections.supply_demand_analysis.nearest_supply && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Nearest Supply Zone</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        ₹{typeof report.sections.supply_demand_analysis.nearest_supply.price_range?.low === 'number' 
                          ? report.sections.supply_demand_analysis.nearest_supply.price_range.low.toFixed(2) 
                          : 'N/A'} - ₹{typeof report.sections.supply_demand_analysis.nearest_supply.price_range?.high === 'number' 
                          ? report.sections.supply_demand_analysis.nearest_supply.price_range.high.toFixed(2) 
                          : 'N/A'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Chart Images Upload & Analysis */}
            <ChartImageUpload
              symbol={symbol}
              onAnalysisComplete={async (analysis) => {
                // Regenerate full report with chart image analysis to update price predictions
                try {
                  setLoading(true);
                  const response = await httpClient.post<any>(
                    `/api/financial/research-report/${symbol}/regenerate-with-chart-images?timeframe=${timeframe}`,
                    analysis
                  );
                  
                  if (response.success && response.data) {
                    setReport(response.data);
                    toast.success('Report regenerated with chart image analysis');
                  } else {
                    // Fallback: update local state if regeneration fails
                    if (report) {
                      setReport({
                        ...report,
                        sections: {
                          ...report.sections,
                          chart_images_analysis: {
                            summary: analysis.summary?.summary_text || 'Chart images analyzed',
                            has_data: true,
                            images_analyzed: analysis.images_analyzed || 0,
                            successful_analyses: analysis.successful_analyses || 0,
                            detected_patterns: analysis.detected_patterns || [],
                            key_levels: analysis.key_levels || [],
                            support_levels: analysis.support_levels || [],
                            resistance_levels: analysis.resistance_levels || [],
                            nearest_support: analysis.nearest_support,
                            nearest_resistance: analysis.nearest_resistance,
                            overall_trend: analysis.overall_trend || 'unknown',
                            individual_analyses: analysis.individual_analyses || [],
                            current_price: analysis.current_price
                          }
                        }
                      });
                    }
                    toast.error(response.message || 'Failed to regenerate report with chart analysis');
                  }
                } catch (error: any) {
                  console.error('Error regenerating report:', error);
                  // Fallback: update local state
                  if (report) {
                    setReport({
                      ...report,
                      sections: {
                        ...report.sections,
                        chart_images_analysis: {
                          summary: analysis.summary?.summary_text || 'Chart images analyzed',
                          has_data: true,
                          images_analyzed: analysis.images_analyzed || 0,
                          successful_analyses: analysis.successful_analyses || 0,
                          detected_patterns: analysis.detected_patterns || [],
                          key_levels: analysis.key_levels || [],
                          support_levels: analysis.support_levels || [],
                          resistance_levels: analysis.resistance_levels || [],
                          nearest_support: analysis.nearest_support,
                          nearest_resistance: analysis.nearest_resistance,
                          overall_trend: analysis.overall_trend || 'unknown',
                          individual_analyses: analysis.individual_analyses || [],
                          current_price: analysis.current_price
                        }
                      }
                    });
                  }
                  toast.error('Failed to regenerate report. Chart analysis added to current report.');
                } finally {
                  setLoading(false);
                }
              }}
            />
            
            {/* Enhanced Chart Images Analysis Display */}
            {report.sections.chart_images_analysis && report.sections.chart_images_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <PhotoIcon className="h-6 w-6 text-blue-600" />
                  Chart Images Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.chart_images_analysis.summary}
                </p>
                
                {/* Support & Resistance from Images */}
                {(report.sections.chart_images_analysis.nearest_support || report.sections.chart_images_analysis.nearest_resistance) && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Support & Resistance from Chart Images</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {report.sections.chart_images_analysis.nearest_support && report.sections.chart_images_analysis.nearest_support.estimated_price && (
                        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                          <div className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Nearest Support</div>
                          <div className="text-2xl font-bold text-green-700 dark:text-green-400">
                            ₹{report.sections.chart_images_analysis.nearest_support.estimated_price != null && !isNaN(report.sections.chart_images_analysis.nearest_support.estimated_price) ? report.sections.chart_images_analysis.nearest_support.estimated_price.toFixed(2) : 'N/A'}
                          </div>
                          {report.sections.chart_images_analysis.nearest_support.distance_percent != null && (
                            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              {!isNaN(report.sections.chart_images_analysis.nearest_support.distance_percent) ? report.sections.chart_images_analysis.nearest_support.distance_percent.toFixed(1) : 'N/A'}% below current price
                            </div>
                          )}
                          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            Detected in {report.sections.chart_images_analysis.nearest_support.frequency || 1} image(s)
                          </div>
                        </div>
                      )}
                      
                      {report.sections.chart_images_analysis.nearest_resistance && report.sections.chart_images_analysis.nearest_resistance.estimated_price && (
                        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
                          <div className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Nearest Resistance</div>
                          <div className="text-2xl font-bold text-red-700 dark:text-red-400">
                            ₹{report.sections.chart_images_analysis.nearest_resistance.estimated_price != null && !isNaN(report.sections.chart_images_analysis.nearest_resistance.estimated_price) ? report.sections.chart_images_analysis.nearest_resistance.estimated_price.toFixed(2) : 'N/A'}
                          </div>
                          {report.sections.chart_images_analysis.nearest_resistance.distance_percent != null && (
                            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              {!isNaN(report.sections.chart_images_analysis.nearest_resistance.distance_percent) ? report.sections.chart_images_analysis.nearest_resistance.distance_percent.toFixed(1) : 'N/A'}% above current price
                            </div>
                          )}
                          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            Detected in {report.sections.chart_images_analysis.nearest_resistance.frequency || 1} image(s)
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Images Analyzed</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.chart_images_analysis.images_analyzed || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Patterns Detected</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.chart_images_analysis.detected_patterns?.length || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Overall Trend</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.chart_images_analysis.overall_trend || 'Unknown'}
                    </div>
                  </div>
                </div>

                {report.sections.chart_images_analysis.detected_patterns && report.sections.chart_images_analysis.detected_patterns.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Detected Patterns:</h4>
                    <div className="space-y-2">
                      {report.sections.chart_images_analysis.detected_patterns.map((pattern: any, idx: number) => (
                        <div key={idx} className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-gray-900 dark:text-white">
                              {pattern.pattern_name}
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              Confidence: {typeof pattern.average_confidence === 'number' ? (pattern.average_confidence * 100).toFixed(0) : 'N/A'}% | Frequency: {pattern.frequency || 0}
                            </span>
                          </div>
                          {pattern.description && (
                            <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                              {pattern.description}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {report.sections.chart_images_analysis.key_levels && report.sections.chart_images_analysis.key_levels.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Key Price Levels Identified:</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {report.sections.chart_images_analysis.key_levels.map((level: any, idx: number) => (
                        <div key={idx} className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-2">
                          {level.estimated_price ? (
                            <>
                              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                                ₹{level.estimated_price != null && !isNaN(level.estimated_price) ? level.estimated_price.toFixed(2) : 'N/A'}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                                {level.price_type || 'Level'}
                              </div>
                              {level.distance_percent != null && (
                                <div className="text-xs text-gray-500 dark:text-gray-500">
                                  {!isNaN(level.distance_percent) ? level.distance_percent.toFixed(1) : 'N/A'}% away
                                </div>
                              )}
                            </>
                          ) : (
                            <>
                              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                                {level.percentage_range || 'N/A'}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Frequency: {level.frequency || 0}
                              </div>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Shared Chart Images Analysis */}
            {report.sections.chart_images_analysis && report.sections.chart_images_analysis.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <PhotoIcon className="h-6 w-6 text-indigo-600" />
                  Shared Chart Images Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.chart_images_analysis.summary}
                </p>
                
                {/* Support & Resistance from Images */}
                {(report.sections.chart_images_analysis.nearest_support || report.sections.chart_images_analysis.nearest_resistance) && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Support & Resistance from Chart Images</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {report.sections.chart_images_analysis.nearest_support && report.sections.chart_images_analysis.nearest_support.estimated_price && (
                        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                          <div className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Nearest Support</div>
                          <div className="text-2xl font-bold text-green-700 dark:text-green-400">
                            ₹{report.sections.chart_images_analysis.nearest_support.estimated_price != null && !isNaN(report.sections.chart_images_analysis.nearest_support.estimated_price) ? report.sections.chart_images_analysis.nearest_support.estimated_price.toFixed(2) : 'N/A'}
                          </div>
                          {report.sections.chart_images_analysis.nearest_support.distance_percent != null && (
                            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              {!isNaN(report.sections.chart_images_analysis.nearest_support.distance_percent) ? report.sections.chart_images_analysis.nearest_support.distance_percent.toFixed(1) : 'N/A'}% below current price
                            </div>
                          )}
                          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            Detected in {report.sections.chart_images_analysis.nearest_support.frequency || 1} image(s)
                          </div>
                        </div>
                      )}
                      
                      {report.sections.chart_images_analysis.nearest_resistance && report.sections.chart_images_analysis.nearest_resistance.estimated_price && (
                        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
                          <div className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Nearest Resistance</div>
                          <div className="text-2xl font-bold text-red-700 dark:text-red-400">
                            ₹{report.sections.chart_images_analysis.nearest_resistance.estimated_price != null && !isNaN(report.sections.chart_images_analysis.nearest_resistance.estimated_price) ? report.sections.chart_images_analysis.nearest_resistance.estimated_price.toFixed(2) : 'N/A'}
                          </div>
                          {report.sections.chart_images_analysis.nearest_resistance.distance_percent != null && (
                            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              {!isNaN(report.sections.chart_images_analysis.nearest_resistance.distance_percent) ? report.sections.chart_images_analysis.nearest_resistance.distance_percent.toFixed(1) : 'N/A'}% above current price
                            </div>
                          )}
                          <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            Detected in {report.sections.chart_images_analysis.nearest_resistance.frequency || 1} image(s)
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Images Analyzed</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.chart_images_analysis.images_analyzed || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Patterns Detected</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.chart_images_analysis.detected_patterns?.length || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Overall Trend</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.chart_images_analysis.overall_trend || 'Unknown'}
                    </div>
                  </div>
                </div>

                {report.sections.chart_images_analysis.detected_patterns && report.sections.chart_images_analysis.detected_patterns.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Detected Patterns:</h4>
                    <div className="space-y-2">
                      {report.sections.chart_images_analysis.detected_patterns.map((pattern: any, idx: number) => (
                        <div key={idx} className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-gray-900 dark:text-white">
                              {pattern.pattern_name}
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              Confidence: {typeof pattern.average_confidence === 'number' ? (pattern.average_confidence * 100).toFixed(0) : 'N/A'}% | Frequency: {pattern.frequency || 0}
                            </span>
                          </div>
                          {pattern.description && (
                            <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                              {pattern.description}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {report.sections.chart_images_analysis.key_levels && report.sections.chart_images_analysis.key_levels.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Key Price Levels Identified:</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {report.sections.chart_images_analysis.key_levels.map((level: any, idx: number) => (
                        <div key={idx} className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-2">
                          {level.estimated_price ? (
                            <>
                              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                                ₹{level.estimated_price != null && !isNaN(level.estimated_price) ? level.estimated_price.toFixed(2) : 'N/A'}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                                {level.price_type || 'Level'}
                              </div>
                              {level.distance_percent != null && (
                                <div className="text-xs text-gray-500 dark:text-gray-500">
                                  {!isNaN(level.distance_percent) ? level.distance_percent.toFixed(1) : 'N/A'}% away
                                </div>
                              )}
                            </>
                          ) : (
                            <>
                              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                                {level.percentage_range || 'N/A'}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Frequency: {level.frequency || 0}
                              </div>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Price Predictions */}
            {report.sections.price_predictions && report.sections.price_predictions.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-red-600" />
                  Price Predictions
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.price_predictions.summary}
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                  {['1W', '1M', '2M', '3M', '6M', '1Y', '2Y'].map((tf) => {
                    const tfData = report.sections.price_predictions?.timeframes?.[tf as '1W' | '1M' | '2M' | '3M' | '6M' | '1Y' | '2Y'];
                    if (!tfData) return null;
                    
                    const isPositive = tfData.potential_change_percent > 0;
                    const changeColor = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
                    
                    return (
                      <div key={tf} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-gray-600 dark:text-gray-400 text-sm font-medium">{tf}</span>
                          <span className={`text-lg font-bold ${changeColor}`}>
                            {isPositive ? '+' : ''}{tfData.potential_change_percent.toFixed(1)}%
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                          ₹{tfData.predicted_price != null && typeof tfData.predicted_price === 'number' ? tfData.predicted_price.toFixed(2) : 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                          Current: ₹{tfData.current_price != null && typeof tfData.current_price === 'number' ? tfData.current_price.toFixed(2) : 'N/A'}
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                          <span className="text-blue-600 dark:text-blue-400 font-medium">{tfData.confidence != null && typeof tfData.confidence === 'number' ? tfData.confidence.toFixed(0) : '0'}%</span>
                        </div>
                        {tfData.risk_level && (
                          <div className="flex items-center justify-between text-xs mt-1">
                            <span className="text-gray-600 dark:text-gray-400">Risk:</span>
                            <span className={`font-medium ${
                              tfData.risk_level === 'Low' ? 'text-green-600 dark:text-green-400' :
                              tfData.risk_level === 'Medium' ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
                            }`}>
                              {tfData.risk_level}
                            </span>
                          </div>
                        )}
                        {tfData.price_range && (
                          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Range (68%): ₹{tfData.price_range.low_68.toFixed(2)} - ₹{tfData.price_range.high_68.toFixed(2)}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {report.sections.price_predictions.overall_confidence && (
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Overall Confidence:</span>
                      <span className="text-blue-600 dark:text-blue-400 font-bold text-lg">
                        {report.sections.price_predictions.overall_confidence.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Market Factors Analysis */}
            {report.sections.market_factors && report.sections.market_factors.has_data && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-purple-600" />
                  Market Factors Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.market_factors.summary}
                </p>
                
                {/* Use MarketFactorsPanel component */}
                <div className="mt-4">
                  <MarketFactorsPanel 
                    symbol={symbol}
                    className="bg-transparent border-0 p-0"
                  />
                </div>
              </div>
            )}

            {/* 5Y Projections + DCF + Sensitivity (Pro UI) */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <div className="flex items-start justify-between gap-4 flex-col lg:flex-row">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
                    <ChartPieIcon className="h-6 w-6 text-blue-600" />
                    5Y Projections & DCF (Scenario + Sensitivity)
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Adjust assumptions and re-run projections. Values are per-share and scenario-based (Base/Bull/Bear).
                  </p>
                </div>

                <button
                  onClick={fetchProjections}
                  disabled={loadingProjections}
                  className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold disabled:opacity-60"
                >
                  {loadingProjections ? 'Recalculating…' : 'Recalculate'}
                </button>
              </div>

              {/* Controls */}
              <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Years (1–5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={projectionAssumptions.years}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, years: Number(e.target.value || 5) }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Discount rate (base)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.base_discount_rate}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, base_discount_rate: Number(e.target.value || 0.12) }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Terminal growth (base)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.base_terminal_growth}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, base_terminal_growth: Number(e.target.value || 0.04) }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">EPS → FCF/share</label>
                  <input
                    type="number"
                    step="0.05"
                    value={projectionAssumptions.eps_to_fcf_ratio}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, eps_to_fcf_ratio: Number(e.target.value || 0.85) }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Base growth override (optional, e.g. 0.10)</label>
                  <input
                    type="text"
                    value={projectionAssumptions.base_growth_override}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, base_growth_override: e.target.value }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                    placeholder="auto"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Base profit margin override (optional, e.g. 0.18)</label>
                  <input
                    type="text"
                    value={projectionAssumptions.base_profit_margin_override}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, base_profit_margin_override: e.target.value }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                    placeholder="auto"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Bull growth delta</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.bull_growth_delta}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, bull_growth_delta: Number(e.target.value || 0.03) }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Bear growth delta</label>
                  <input
                    type="number"
                    step="0.01"
                    value={projectionAssumptions.bear_growth_delta}
                    onChange={(e) => setProjectionAssumptions(s => ({ ...s, bear_growth_delta: Number(e.target.value || 0.03) }))}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              {/* Outputs */}
              <div className="mt-6">
                {!projections?.success ? (
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Projections unavailable (missing annual financial data). Import/sync ANNUAL financials first.
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div className="text-sm text-gray-600 dark:text-gray-400">DCF Band (per share)</div>
                        <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">Bear: <span className="font-bold">₹{projections.dcf_band?.bear ?? '—'}</span></div>
                        <div className="text-sm text-gray-700 dark:text-gray-200">Base: <span className="font-bold">₹{projections.dcf_band?.base ?? '—'}</span></div>
                        <div className="text-sm text-gray-700 dark:text-gray-200">Bull: <span className="font-bold">₹{projections.dcf_band?.bull ?? '—'}</span></div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div className="text-sm text-gray-600 dark:text-gray-400">Base assumptions</div>
                        <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                          Growth: <span className="font-semibold">{formatPct(projections.scenarios?.base?.assumptions?.revenue_growth || 0)}</span>
                        </div>
                        <div className="text-sm text-gray-700 dark:text-gray-200">
                          Discount: <span className="font-semibold">{formatPct(projections.scenarios?.base?.assumptions?.discount_rate || 0)}</span>
                        </div>
                        <div className="text-sm text-gray-700 dark:text-gray-200">
                          Terminal g: <span className="font-semibold">{formatPct(projections.scenarios?.base?.assumptions?.terminal_growth || 0)}</span>
                        </div>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div className="text-sm text-gray-600 dark:text-gray-400">History summary</div>
                        <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                          Revenue CAGR: <span className="font-semibold">{projections.history_summary?.rev_cagr != null ? formatPct(projections.history_summary.rev_cagr) : '—'}</span>
                        </div>
                        <div className="text-sm text-gray-700 dark:text-gray-200">
                          Profit CAGR: <span className="font-semibold">{projections.history_summary?.profit_cagr != null ? formatPct(projections.history_summary.profit_cagr) : '—'}</span>
                        </div>
                        <div className="text-sm text-gray-700 dark:text-gray-200">
                          EPS CAGR: <span className="font-semibold">{projections.history_summary?.eps_cagr != null ? formatPct(projections.history_summary.eps_cagr) : '—'}</span>
                        </div>
                      </div>
                    </div>

                    <div className="overflow-x-auto mb-6">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-600 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                            <th className="py-2 pr-4">Year</th>
                            <th className="py-2 pr-4">Revenue</th>
                            <th className="py-2 pr-4">Net Profit</th>
                            <th className="py-2 pr-4">EPS</th>
                            <th className="py-2 pr-4">FCF/Share</th>
                            <th className="py-2 pr-4">Profit Margin</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(projections.scenarios?.base?.projection || []).map((row: any) => (
                            <tr key={row.year} className="border-b border-gray-100 dark:border-gray-700">
                              <td className="py-2 pr-4 font-medium text-gray-900 dark:text-white">{row.year}</td>
                              <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.revenue?.toLocaleString?.('en-IN') ?? row.revenue}</td>
                              <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.net_profit?.toLocaleString?.('en-IN') ?? row.net_profit}</td>
                              <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.eps}</td>
                              <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.fcf_per_share}</td>
                              <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.profit_margin}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {projections.sensitivity?.terminal_growth_vs_discount && (
                        <HeatmapGrid
                          title="Sensitivity: Terminal growth vs Discount rate"
                          grid={projections.sensitivity.terminal_growth_vs_discount}
                          rowLabel="terminal_growth"
                        />
                      )}
                      {projections.sensitivity?.growth_vs_discount && (
                        <HeatmapGrid
                          title="Sensitivity: Growth rate vs Discount rate"
                          grid={projections.sensitivity.growth_vs_discount}
                          rowLabel="growth_rate"
                        />
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* 10 Strong Points */}
            {report.sections.strong_points && report.sections.strong_points.count > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  {report.sections.strong_points.count} Strong Points Supporting {report.sections.recommendation?.recommendation || 'Recommendation'}
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">{report.sections.strong_points.summary}</p>
                <div className="space-y-4">
                  {report.sections.strong_points.points.map((point, idx) => (
                    <div key={idx} className="border-l-4 border-green-500 pl-4 py-2">
                      <div className="font-semibold text-gray-900 dark:text-white">
                        {idx + 1}. {point.point}
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                        {point.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Price Action */}
            {report.sections.price_action && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-blue-600" />
                  Price Action Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.price_action.summary}
                </p>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Trend</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.price_action.trend}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Momentum</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.price_action.momentum}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">RSI</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">
                      {report.sections.price_action.rsi?.toFixed(1) || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Financial Strength */}
            {report.sections.financial_strength && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <CurrencyDollarIcon className="h-6 w-6 text-green-600" />
                  Financial Strength
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.financial_strength.summary}
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {report.sections.financial_strength.roe && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">ROE</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {report.sections.financial_strength.roe.toFixed(1)}%
                      </div>
                    </div>
                  )}
                  {report.sections.financial_strength.roce && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">ROCE</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {report.sections.financial_strength.roce.toFixed(1)}%
                      </div>
                    </div>
                  )}
                  {report.sections.financial_strength.debt_to_equity !== undefined && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Debt/Equity</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {report.sections.financial_strength.debt_to_equity.toFixed(2)}
                      </div>
                    </div>
                  )}
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Assessment</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                      {report.sections.financial_strength.assessment}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Valuation */}
            {report.sections.valuation && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-purple-600" />
                  Valuation
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.valuation.summary}
                </p>
                <div className="grid grid-cols-2 gap-4">
                  {report.sections.valuation.pe_ratio && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">PE Ratio</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {report.sections.valuation.pe_ratio.toFixed(2)}
                      </div>
                    </div>
                  )}
                  {report.sections.valuation.pb_ratio && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">PB Ratio</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">
                        {report.sections.valuation.pb_ratio.toFixed(2)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 5Y Projections + DCF (Scenario + Sensitivity) */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <ChartPieIcon className="h-6 w-6 text-blue-600" />
                5Y Projections & DCF (Pro)
              </h3>
              {loadingProjections ? (
                <div className="text-sm text-gray-600 dark:text-gray-400">Loading projections…</div>
              ) : projections?.success ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">DCF Band (per share)</div>
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                        Bear: <span className="font-bold">₹{projections.dcf_band?.bear ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Base: <span className="font-bold">₹{projections.dcf_band?.base ?? '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Bull: <span className="font-bold">₹{projections.dcf_band?.bull ?? '—'}</span>
                      </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Base Assumptions</div>
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                        Growth: <span className="font-semibold">{Math.round((projections.scenarios?.base?.assumptions?.revenue_growth || 0) * 100)}%</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Discount: <span className="font-semibold">{Math.round((projections.scenarios?.base?.assumptions?.discount_rate || 0) * 100)}%</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Terminal g: <span className="font-semibold">{Math.round((projections.scenarios?.base?.assumptions?.terminal_growth || 0) * 100)}%</span>
                      </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">History (CAGR)</div>
                      <div className="mt-2 text-sm text-gray-700 dark:text-gray-200">
                        Revenue CAGR: <span className="font-semibold">{projections.history_summary?.rev_cagr != null ? `${Math.round(projections.history_summary.rev_cagr * 100)}%` : '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        Profit CAGR: <span className="font-semibold">{projections.history_summary?.profit_cagr != null ? `${Math.round(projections.history_summary.profit_cagr * 100)}%` : '—'}</span>
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-200">
                        EPS CAGR: <span className="font-semibold">{projections.history_summary?.eps_cagr != null ? `${Math.round(projections.history_summary.eps_cagr * 100)}%` : '—'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="overflow-x-auto mb-6">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-600 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                          <th className="py-2 pr-4">Year</th>
                          <th className="py-2 pr-4">Revenue</th>
                          <th className="py-2 pr-4">Net Profit</th>
                          <th className="py-2 pr-4">EPS</th>
                          <th className="py-2 pr-4">FCF/Share</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(projections.scenarios?.base?.projection || []).map((row: any) => (
                          <tr key={row.year} className="border-b border-gray-100 dark:border-gray-700">
                            <td className="py-2 pr-4 font-medium text-gray-900 dark:text-white">{row.year}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.revenue?.toLocaleString?.('en-IN') ?? row.revenue}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.net_profit?.toLocaleString?.('en-IN') ?? row.net_profit}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.eps}</td>
                            <td className="py-2 pr-4 text-gray-700 dark:text-gray-200">{row.fcf_per_share}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Sensitivity tables are available in API response (growth vs discount, terminal g vs discount). Next step: render as heatmap.
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Projections unavailable (missing annual financial data). Import/sync annual financials first.
                </div>
              )}
            </div>

            {/* Technical Signals */}
            {report.sections.technical_signals && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ChartBarIcon className="h-6 w-6 text-orange-600" />
                  Technical Signals
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.technical_signals.summary}
                </p>
                {report.sections.technical_signals.signals.length > 0 && (
                  <ul className="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
                    {report.sections.technical_signals.signals.map((signal, idx) => (
                      <li key={idx}>{signal}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Market Sentiment & News Analysis */}
            {report.sections.market_sentiment && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ArrowTrendingUpIcon className={`h-6 w-6 ${
                    report.sections.market_sentiment.overall_sentiment === 'Bullish' ? 'text-green-600' :
                    report.sections.market_sentiment.overall_sentiment === 'Bearish' ? 'text-red-600' :
                    'text-yellow-600'
                  }`} />
                  Market Sentiment & News Analysis
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.market_sentiment.summary}
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Overall Sentiment</div>
                    <div className={`text-lg font-bold ${
                      report.sections.market_sentiment.overall_sentiment === 'Bullish' ? 'text-green-600' :
                      report.sections.market_sentiment.overall_sentiment === 'Bearish' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>
                      {report.sections.market_sentiment.overall_sentiment}
                    </div>
                  </div>
                  {report.sections.market_sentiment.news_sentiment && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">News Sentiment</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                        {report.sections.market_sentiment.news_sentiment}
                      </div>
                    </div>
                  )}
                  {report.sections.market_sentiment.social_sentiment && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Social Sentiment</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white capitalize">
                        {report.sections.market_sentiment.social_sentiment}
                      </div>
                    </div>
                  )}
                  {report.sections.market_sentiment.sentiment_score !== undefined && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Sentiment Score</div>
                      <div className={`text-lg font-bold ${
                        (report.sections.market_sentiment.sentiment_score || 0) > 0.3 ? 'text-green-600' :
                        (report.sections.market_sentiment.sentiment_score || 0) < -0.3 ? 'text-red-600' :
                        'text-yellow-600'
                      }`}>
                        {(report.sections.market_sentiment.sentiment_score || 0).toFixed(2)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Risk Assessment */}
            {report.sections.risk_assessment && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <ExclamationTriangleIcon className={`h-6 w-6 ${
                    report.sections.risk_assessment.risk_level === 'low' ? 'text-green-600' :
                    report.sections.risk_assessment.risk_level === 'high' ? 'text-red-600' :
                    'text-yellow-600'
                  }`} />
                  Risk Assessment
                </h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  {report.sections.risk_assessment.summary}
                </p>
                <div className="space-y-2">
                  {report.sections.risk_assessment.risk_factors.map((factor, idx) => {
                    const riskLevel = report.sections.risk_assessment?.risk_level || 'medium';
                    return (
                      <div key={idx} className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                        <div className={`w-2 h-2 rounded-full ${
                          riskLevel === 'low' ? 'bg-green-500' :
                          riskLevel === 'high' ? 'bg-red-500' :
                          'bg-yellow-500'
                        }`}></div>
                        {factor}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Comprehensive Conclusion */}
            {report.sections.conclusion && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <DocumentTextIcon className="h-6 w-6 text-indigo-600" />
                  Conclusion
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {report.sections.conclusion.summary}
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 text-center">
            <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              No Report Available
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Select a stock to generate a research report
            </p>
            <button
              onClick={fetchReport}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Generate Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResearchReport;

