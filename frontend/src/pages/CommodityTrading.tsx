/**
 * Commodity Trading Page
 * Complete UI for commodity trading (Gold, Silver, Crude Oil, Natural Gas) with real-time signals
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Clock, TrendingUp, TrendingDown, Activity, 
  RefreshCw, Zap, Target, AlertCircle, 
  BarChart3, Gauge, ArrowUpDown, ExternalLink
} from 'lucide-react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import SavedStrategies from '../components/strategy/SavedStrategies';
import PaperTrading from '../components/strategy/PaperTrading';
import { Strategy } from '../components/strategy/StrategyBuilder';
import api from '../services/api';
import candleDataApi from '../services/candleDataApi';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';

// Reuse the same interfaces from IntradayTrading
interface IntradaySignal {
  signal: string;
  confidence: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  strategy: string;
  message: string;
  timestamp: string;
}

interface VWAPSignal {
  signal: string;
  vwap: number;
  upper_band?: number;
  lower_band?: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  ai_insight?: string;
  risk_reward?: number;
  market_context?: string;
}

interface MomentumSignal {
  signal: string;
  rsi?: number;
  roc?: number;
  message: string;
  ai_insight?: string;
  momentum_strength?: string;
  trend_direction?: string;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
}

interface BreakoutSignal {
  signal: string;
  resistance?: number;
  support?: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  message: string;
  ai_insight?: string;
  breakout_strength?: string;
  volume_confirmation?: boolean;
}

interface MeanReversionSignal {
  signal: string;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  message: string;
  ai_insight?: string;
  deviation_from_mean?: number;
  reversion_probability?: number;
}

interface ScalpingSignal {
  signal: string;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  message: string;
  ai_insight?: string;
  scalping_opportunity?: string;
  quick_profit_potential?: number;
}

interface GapTradingSignal {
  signal: string;
  gap_type?: string;
  gap_pct?: number;
  today_open?: number;
  previous_close?: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  message: string;
  ai_insight?: string;
}

interface ClosingRangeSignal {
  signal: string;
  closing_high?: number;
  closing_low?: number;
  closing_range?: number;
  closing_mid?: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  message: string;
  ai_insight?: string;
}

interface VolumeProfileSignal {
  signal: string;
  poc_price?: number;
  poc_volume?: number;
  value_area_high?: number;
  value_area_low?: number;
  price_vs_poc_pct?: number;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  message: string;
  ai_insight?: string;
}

interface NewsSignal {
  signal: string;
  sentiment_score?: number;
  news_count?: number;
  high_impact_count?: number;
  message: string;
  ai_insight?: string;
}

// Commodity symbols mapping
const COMMODITY_SYMBOLS = [
  { value: 'GOLD', label: 'Gold (GC=F)', yahooSymbol: 'GC=F' },
  { value: 'SILVER', label: 'Silver (SI=F)', yahooSymbol: 'SI=F' },
  { value: 'CRUDE_OIL', label: 'Crude Oil (CL=F)', yahooSymbol: 'CL=F' },
  { value: 'NATURAL_GAS', label: 'Natural Gas (NG=F)', yahooSymbol: 'NG=F' },
];

// Map commodity symbols to Yahoo Finance format
const getCommodityYahooSymbol = (symbol: string): string => {
  const commodity = COMMODITY_SYMBOLS.find(c => c.value === symbol.toUpperCase());
  return commodity?.yahooSymbol || symbol;
};

const CommodityTrading: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selectedSymbol, setSelectedSymbol] = useState(() => {
    const symbolFromParams = searchParams.get('symbol');
    return symbolFromParams || 'GOLD';
  });
  const [timeframe, setTimeframe] = useState('5m');
  const [duration, setDuration] = useState('1d');
  const [loading, setLoading] = useState(false);
  
  // Strategy and parameter states
  const [strategy, setStrategy] = useState('vwap_trading');
  const [momentumPeriod, setMomentumPeriod] = useState(14);
  const [momentumThreshold, setMomentumThreshold] = useState(0.5);
  const [breakoutLookback, setBreakoutLookback] = useState(20);
  const [breakoutVolumeThreshold, setBreakoutVolumeThreshold] = useState(1.5);
  const [meanReversionPeriod, setMeanReversionPeriod] = useState(20);
  const [meanReversionStdMultiplier, setMeanReversionStdMultiplier] = useState(2.0);
  const [scalpingTickSize, setScalpingTickSize] = useState(0.05);
  const [scalpingMinProfitTarget, setScalpingMinProfitTarget] = useState(0.3);
  
  // Signals
  const [vwapSignal, setVwapSignal] = useState<VWAPSignal | null>(null);
  const [momentumSignal, setMomentumSignal] = useState<MomentumSignal | null>(null);
  const [breakoutSignal, setBreakoutSignal] = useState<BreakoutSignal | null>(null);
  const [meanReversionSignal, setMeanReversionSignal] = useState<MeanReversionSignal | null>(null);
  const [scalpingSignal, setScalpingSignal] = useState<ScalpingSignal | null>(null);
  const [gapTradingSignal, setGapTradingSignal] = useState<GapTradingSignal | null>(null);
  const [closingRangeSignal, setClosingRangeSignal] = useState<ClosingRangeSignal | null>(null);
  const [volumeProfileSignal, setVolumeProfileSignal] = useState<VolumeProfileSignal | null>(null);
  const [newsSignal, setNewsSignal] = useState<NewsSignal | null>(null);
  const [comprehensiveSignal, setComprehensiveSignal] = useState<IntradaySignal | null>(null);
  const [tradingSession, setTradingSession] = useState<string>('');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [nextDayPerception, setNextDayPerception] = useState<any>(null);
  
  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30);
  
  // Strategy & Paper Trading
  const [activeTab, setActiveTab] = useState<'signals' | 'saved' | 'paper'>('signals');
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  // Chart state
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const volumeChartRef = useRef<IChartApi | null>(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartData, setChartData] = useState<any>(null);

  useEffect(() => {
    if (autoRefresh && selectedSymbol) {
      const interval = setInterval(() => {
        fetchCurrentPrice();
        fetchAllSignals(false); // Don't show toast for auto-refresh
      }, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, selectedSymbol, timeframe, duration]);

  // Load chart data
  const loadChartData = useCallback(async () => {
    if (!candlestickSeriesRef.current || !selectedSymbol) return;

    setChartLoading(true);
    try {
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      
      // Map timeframe to API format
      const timeframeMap: Record<string, string> = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '1h': '1h',
        '1d': '1d',
      };
      const apiTimeframe = timeframeMap[timeframe] || '5m';

      // Map duration to API range
      const rangeMap: Record<string, string> = {
        '1d': '1d',
        '5d': '5d',
        '1w': '5d',
        '1mo': '1mo',
        '3mo': '3mo',
        '6mo': '6mo',
        '1y': '1y',
      };
      const apiRange = rangeMap[duration] || '1d';

      // Fetch candle data
      const response = await candleDataApi.getCandles(yahooSymbol, apiTimeframe, apiRange);

      if (response.success && response.data && response.data.length > 0) {
        // Transform and sort data
        let candles: CandlestickData[] = response.data.map((candle: any) => ({
          time: (Number(candle.time) as Time),
          open: Number(candle.open),
          high: Number(candle.high),
          low: Number(candle.low),
          close: Number(candle.close),
        }));

        // Sort by time ascending (required by Lightweight Charts)
        candles.sort((a, b) => Number(a.time) - Number(b.time));

        // Deduplicate and sort
        const uniqueData = deduplicateAndSortCandlestickData(candles, false);

        // Update chart
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(uniqueData);
          
          // Fit content
          if (chartRef.current) {
            chartRef.current.timeScale().fitContent();
          }
        }

        // Store chart data for signals
        setChartData({
          candles: uniqueData,
          symbol: yahooSymbol,
          timeframe: apiTimeframe,
          range: apiRange,
        });

        // Update current price from latest candle
        if (uniqueData.length > 0) {
          const latestCandle = uniqueData[uniqueData.length - 1];
          setCurrentPrice(latestCandle.close);
        }
      }
    } catch (error: any) {
      console.error('Error loading chart data:', error);
      toast.error('Failed to load chart data');
    } finally {
      setChartLoading(false);
    }
  }, [selectedSymbol, timeframe, duration]);

  useEffect(() => {
    setCurrentPrice(null);
    fetchTradingSession();
    fetchCurrentPrice();
    fetchNextDayPerception();
    fetchAllSignals(false); // Don't show toast on initial load
    if (candlestickSeriesRef.current) {
      loadChartData(); // Load chart data when symbol/timeframe/duration changes
    }
  }, [selectedSymbol, timeframe, duration, loadChartData]);

  // Initialize chart on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      if (chartContainerRef.current && !chartRef.current) {
        initializeChart();
      }
    }, 100);
    
    return () => {
      clearTimeout(timer);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      if (volumeChartRef.current) {
        volumeChartRef.current.remove();
        volumeChartRef.current = null;
      }
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
      if (volumeChartRef.current && chartContainerRef.current) {
        volumeChartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Convert duration to days for API calls
  const getDurationInDays = (duration: string): number => {
    const durationMap: Record<string, number> = {
      '1d': 1,
      '5d': 5,
      '1w': 7,
      '1mo': 30,
      '3mo': 90,
      '6mo': 180,
      '1y': 365
    };
    return durationMap[duration] || 1;
  };

  // Initialize chart
  const initializeChart = useCallback(() => {
    if (!chartContainerRef.current) return;

    // Main chart
    chartRef.current = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2a2e39' },
        horzLines: { color: '#2a2e39' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        timeVisible: true,
        borderColor: '#2a2e39',
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
      },
    });

    // Add candlestick series
    candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Load initial chart data
    loadChartData();
  }, [loadChartData]);

  const fetchCurrentPrice = async (symbol?: string) => {
    const symbolToFetch = symbol || selectedSymbol;
    if (!symbolToFetch) return;
    
    try {
      // Get Yahoo Finance symbol for commodity
      const yahooSymbol = getCommodityYahooSymbol(symbolToFetch);
      
      // Try fetching with Yahoo Finance symbol
      let quote = await api.getQuote(yahooSymbol, 'COMMODITY');
      
      if (quote && quote.last_price && quote.last_price > 0) {
        setCurrentPrice(quote.last_price);
        return;
      }
      
      // Fallback: try with commodity endpoint
      try {
        const response = await httpClient.get(`/api/comprehensive-trading/commodity/quote/${symbolToFetch}`) as any;
        if (response?.data?.success && response.data.data?.price) {
          setCurrentPrice(response.data.data.price);
          return;
        }
      } catch (e) {
        console.warn('Commodity endpoint not available, using fallback');
      }
      
      console.warn(`Could not fetch price for ${symbolToFetch}`);
    } catch (error) {
      console.error(`Failed to fetch current price for ${symbolToFetch}:`, error);
    }
  };

  const fetchTradingSession = async () => {
    try {
      const response = await httpClient.get('/api/comprehensive-trading/intraday/trading-session') as any;
      if (response.data?.success) {
        setTradingSession(response.data.data?.session || 'Unknown');
      }
    } catch (error) {
      console.error('Failed to fetch trading session');
    }
  };

  const fetchNextDayPerception = async () => {
    if (!selectedSymbol) return;
    
    try {
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.get(`/api/comprehensive-trading/commodity/chart-analysis/${yahooSymbol}?timeframe=1D&enable_multi_timeframe=true`) as any;
      
      if (response.success && response.data) {
        const analysis = response.data;
        setNextDayPerception({
          trend: analysis.facts?.trend || 'NEUTRAL',
          rsi: analysis.facts?.rsi || null,
          patterns: analysis.facts?.patterns_detected || 0,
          pattern_names: Array.isArray(analysis.facts?.pattern_names) ? analysis.facts.pattern_names : [],
          suggestions: analysis.suggestions || [],
          current_price: analysis.facts?.current_price || currentPrice,
          support_levels: analysis.facts?.support_levels || [],
          resistance_levels: analysis.facts?.resistance_levels || [],
          multi_timeframe_trend: analysis.facts?.multi_timeframe_trend || 'NEUTRAL',
          multi_timeframe_confidence: analysis.facts?.multi_timeframe_confidence || 0,
          ml_prediction: analysis.facts?.ml_prediction || 'NEUTRAL',
          ml_confidence: analysis.facts?.ml_confidence || 0,
        });
      }
    } catch (error) {
      console.error('Failed to fetch next day perception:', error);
    }
  };

  const fetchVWAPSignal = async () => {
    try {
      if (!currentPrice) {
        await fetchCurrentPrice();
      }
      
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/vwap-signal?symbol=${yahooSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        const vwapValue = data.vwap || 0;
        
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setVwapSignal({
          signal: data.signal || 'HOLD',
          vwap: vwapValue,
          upper_band: data.upper_band,
          lower_band: data.lower_band,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target
        });
      } else {
        const errorMsg = response?.error || response?.detail || 'No data available';
        console.warn('VWAP signal warning:', errorMsg);
        setVwapSignal(null);
      }
    } catch (error: any) {
      console.error('VWAP signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch VWAP signal';
      console.error('VWAP Error Details:', errorMsg, error.response?.status);
      setVwapSignal(null);
    }
  };

  const fetchMomentumSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/momentum-signal?symbol=${yahooSymbol}&timeframe=${timeframe}&period=${momentumPeriod}&threshold=${momentumThreshold}&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setMomentumSignal({
          signal: data.signal || 'HOLD',
          rsi: data.rsi,
          roc: data.roc,
          message: data.reason || data.message || 'Momentum signal generated',
          momentum_strength: data.strength,
          entry_price: data.entry_price || data.entry || data.current_price,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target || data.exit_price
        });
      } else {
        console.warn('Momentum signal warning:', response?.error || response?.detail);
        setMomentumSignal(null);
      }
    } catch (error: any) {
      console.error('Momentum signal error:', error);
      console.error('Momentum Error Details:', error.response?.data, error.response?.status);
      setMomentumSignal(null);
    }
  };

  const fetchBreakoutSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/breakout-signal?symbol=${yahooSymbol}&timeframe=${timeframe}&lookback_period=${breakoutLookback}&volume_threshold=${breakoutVolumeThreshold}&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setBreakoutSignal({
          signal: data.signal || 'HOLD',
          resistance: data.resistance,
          support: data.support,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          message: data.reason || data.message || 'Breakout signal generated',
          volume_confirmation: data.volume_ratio > breakoutVolumeThreshold
        });
      } else {
        console.warn('Breakout signal warning:', response?.error || response?.detail);
        setBreakoutSignal(null);
      }
    } catch (error: any) {
      console.error('Breakout signal error:', error);
      console.error('Breakout Error Details:', error.response?.data, error.response?.status);
      setBreakoutSignal(null);
    }
  };

  const fetchMeanReversionSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/mean-reversion-signal?symbol=${yahooSymbol}&timeframe=${timeframe}&period=${meanReversionPeriod}&std_multiplier=${meanReversionStdMultiplier}&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setMeanReversionSignal({
          signal: data.signal || 'HOLD',
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          message: data.reason || data.message || 'Mean reversion signal generated',
          deviation_from_mean: data.distance_from_mean_pct
        });
      } else {
        console.warn('Mean reversion signal warning:', response?.error || response?.detail);
        setMeanReversionSignal(null);
      }
    } catch (error: any) {
      console.error('Mean reversion signal error:', error);
      console.error('Mean Reversion Error Details:', error.response?.data, error.response?.status);
      setMeanReversionSignal(null);
    }
  };

  const fetchScalpingSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/scalping-signal?symbol=${yahooSymbol}&timeframe=1m&tick_size=${scalpingTickSize}&min_profit_target=${scalpingMinProfitTarget}&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setScalpingSignal({
          signal: data.signal || 'HOLD',
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          message: data.reason || data.message || 'Scalping signal generated'
        });
      } else {
        console.warn('Scalping signal warning:', response?.error || response?.detail);
        setScalpingSignal(null);
      }
    } catch (error: any) {
      console.error('Scalping signal error:', error);
      console.error('Scalping Error Details:', error.response?.data, error.response?.status);
      setScalpingSignal(null);
    }
  };

  const fetchGapTradingSignal = async () => {
    try {
      const days = Math.max(2, getDurationInDays(duration));
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/gap-trading-signal?symbol=${yahooSymbol}&timeframe=1d&gap_threshold=0.5&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setGapTradingSignal({
          signal: data.signal || 'HOLD',
          gap_type: data.gap_type,
          gap_pct: data.gap_pct,
          today_open: data.today_open,
          previous_close: data.previous_close,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          message: data.reason || data.message || 'Gap trading signal generated'
        });
      } else {
        console.warn('Gap trading signal warning:', response?.error || response?.detail);
        setGapTradingSignal(null);
      }
    } catch (error: any) {
      console.error('Gap trading signal error:', error);
      console.error('Gap Trading Error Details:', error.response?.data, error.response?.status);
      setGapTradingSignal(null);
    }
  };

  const fetchClosingRangeSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/closing-range-signal?symbol=${yahooSymbol}&timeframe=5m&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setClosingRangeSignal({
          signal: data.signal || 'HOLD',
          closing_high: data.closing_high,
          closing_low: data.closing_low,
          closing_range: data.closing_range,
          closing_mid: data.closing_mid,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          message: data.reason || data.message || 'Closing range signal generated'
        });
      } else {
        console.warn('Closing range signal warning:', response?.error || response?.detail);
        setClosingRangeSignal(null);
      }
    } catch (error: any) {
      console.error('Closing range signal error:', error);
      console.error('Closing Range Error Details:', error.response?.data, error.response?.status);
      setClosingRangeSignal(null);
    }
  };

  const fetchVolumeProfileSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/volume-profile-signal?symbol=${yahooSymbol}&timeframe=${timeframe}&bins=20&days=${days}`) as any;
      
      // Handle response structure: {success: true, data: {...}} or direct data
      const responseData = response?.data?.data || response?.data || response;
      
      if (response?.success || responseData) {
        const data = responseData;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setVolumeProfileSignal({
          signal: data.signal || 'HOLD',
          poc_price: data.poc_price,
          poc_volume: data.poc_volume,
          value_area_high: data.value_area_high,
          value_area_low: data.value_area_low,
          price_vs_poc_pct: data.price_vs_poc_pct,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          message: data.reason || data.message || 'Volume profile signal generated'
        });
      } else {
        console.warn('Volume profile signal warning:', response?.error || response?.detail);
        setVolumeProfileSignal(null);
      }
    } catch (error: any) {
      console.error('Volume profile signal error:', error);
      console.error('Volume Profile Error Details:', error.response?.data, error.response?.status);
      setVolumeProfileSignal(null);
    }
  };

  const fetchNewsSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/news-signal?symbol=${yahooSymbol}&days=${days}`) as any;
      
      if (response?.success || response?.data) {
        const data = response.data || response;
        setNewsSignal({
          signal: data.signal || 'HOLD',
          sentiment_score: data.sentiment_score,
          news_count: data.news_count,
          high_impact_count: data.high_impact_count,
          message: data.reason || data.message || 'News signal generated'
        });
      } else {
        console.warn('News signal warning:', response?.error || response?.detail);
        setNewsSignal(null);
      }
    } catch (error: any) {
      console.error('News signal error:', error);
      console.error('News Error Details:', error.response?.data, error.response?.status);
      setNewsSignal(null);
    }
  };

  const fetchComprehensiveSignal = async () => {
    try {
      const days = getDurationInDays(duration);
      const yahooSymbol = getCommodityYahooSymbol(selectedSymbol);
      const response = await httpClient.post(`/api/comprehensive-trading/commodity/comprehensive-signal?symbol=${yahooSymbol}&timeframe=${timeframe}&strategy=${strategy}&days=${days}`) as any;
      
      if (response?.success || response?.data) {
        const data = response.data || response;
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        }
        
        setComprehensiveSignal({
          signal: data.signal || 'HOLD',
          confidence: data.confidence || 0.5,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target,
          strategy: data.strategy || strategy,
          message: data.recommendation || data.message || 'Comprehensive signal generated',
          timestamp: new Date().toISOString()
        });
      } else {
        console.warn('Comprehensive signal warning:', response?.error || response?.detail);
        setComprehensiveSignal(null);
      }
    } catch (error: any) {
      console.error('Comprehensive signal error:', error);
      console.error('Comprehensive Error Details:', error.response?.data, error.response?.status);
      setComprehensiveSignal(null);
    }
  };

  const fetchAllSignals = async (showToast: boolean = true) => {
    setLoading(true);
    try {
      // Fetch current price and trading session first - ensure we have them before fetching signals
      await Promise.all([
        fetchCurrentPrice(),
        fetchTradingSession()
      ]);
      
      // Small delay to ensure price is set
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Then fetch all signals in parallel
      const results = await Promise.allSettled([
        fetchVWAPSignal(),
        fetchMomentumSignal(),
        fetchBreakoutSignal(),
        fetchMeanReversionSignal(),
        fetchScalpingSignal(),
        fetchGapTradingSignal(),
        fetchClosingRangeSignal(),
        fetchVolumeProfileSignal(),
        fetchNewsSignal(),
        fetchComprehensiveSignal()
      ]);
      
      // Count successful and failed signals
      const successful = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;
      
      // Refresh next day perception
      await fetchNextDayPerception();
      
      if (showToast) {
        if (failed === 0) {
          toast.success(`All ${successful} signals loaded successfully`);
        } else {
          toast.success(`${successful} signals loaded, ${failed} failed. Check console for details.`);
        }
      }
    } catch (error) {
      console.error('Error fetching signals:', error);
      if (showToast) {
        toast.error('Some signals failed to load. Check console for details.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
    navigate(`/commodity-trading?symbol=${symbol}&timeframe=${timeframe}&period=${duration}`);
    
    // Reset all signals
    setVwapSignal(null);
    setMomentumSignal(null);
    setBreakoutSignal(null);
    setMeanReversionSignal(null);
    setScalpingSignal(null);
    setGapTradingSignal(null);
    setClosingRangeSignal(null);
    setVolumeProfileSignal(null);
    setNewsSignal(null);
    setComprehensiveSignal(null);
    setNextDayPerception(null);
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'BUY' || signal === 'STRONG_BUY') return 'text-green-400';
    if (signal === 'SELL' || signal === 'STRONG_SELL') return 'text-red-400';
    return 'text-yellow-400';
  };

  const getSignalBgColor = (signal: string) => {
    if (signal === 'BUY' || signal === 'STRONG_BUY') return 'bg-green-500/20 border-green-500/50';
    if (signal === 'SELL' || signal === 'STRONG_SELL') return 'bg-red-500/20 border-red-500/50';
    return 'bg-yellow-500/20 border-yellow-500/50';
  };

  const renderSignalCard = (
    title: string,
    signal: any,
    onRefresh: () => void,
    icon: React.ReactNode,
    children?: React.ReactNode
  ) => {
    if (!signal) {
      return (
        <div className="bg-gradient-to-br from-[#1a1d28] to-[#252936] rounded-xl p-5 border border-gray-700/50 hover:border-gray-600 transition-all">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-bold text-gray-200 flex items-center gap-2">
              <div className="p-2 bg-gray-700/50 rounded-lg">{icon}</div>
              {title}
            </h3>
            <button
              onClick={onRefresh}
              className="text-xs px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-all border border-blue-500/30"
            >
              <RefreshCw className="w-3 h-3 inline mr-1" />
              Refresh
            </button>
          </div>
          <p className="text-xs text-gray-500 bg-[#0f1117]/50 p-3 rounded-lg">Click Refresh to load signal</p>
        </div>
      );
    }

    return (
      <div className={`rounded-xl p-5 border-2 shadow-lg hover:shadow-xl transition-all ${getSignalBgColor(signal.signal)}`}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-bold text-gray-200 flex items-center gap-2">
            <div className={`p-2 rounded-lg ${
              signal.signal.includes('BUY') ? 'bg-green-500/20' :
              signal.signal.includes('SELL') ? 'bg-red-500/20' : 'bg-yellow-500/20'
            }`}>
              {icon}
            </div>
            {title}
          </h3>
          <button
            onClick={onRefresh}
            className="text-xs px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-all border border-blue-500/30"
          >
            <RefreshCw className="w-3 h-3 inline mr-1" />
            Refresh
          </button>
        </div>
        <div className={`text-2xl font-bold mb-3 ${getSignalColor(signal.signal)}`}>
          {signal.signal}
        </div>
        <div className="bg-[#0f1117]/50 rounded-lg p-3 border border-gray-700/50">
          {children}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d14] via-[#131722] to-[#0f1117] text-white">
      <div className="max-w-7xl mx-auto p-4 md:p-6">
        {/* Enhanced Header with Gradient */}
        <div className="mb-8">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-amber-900/30 via-yellow-900/20 to-orange-900/30 border border-amber-500/20 p-6 mb-6">
            <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-transparent"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-amber-500/20 to-yellow-500/20 rounded-xl border border-amber-400/30">
                    <BarChart3 className="w-8 h-8 text-amber-400" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold mb-1 bg-gradient-to-r from-amber-300 to-yellow-300 bg-clip-text text-transparent">
                      Commodity Trading
                    </h1>
                    <p className="text-gray-300 text-sm">Real-time trading signals for Gold, Silver, Crude Oil, and Natural Gas</p>
                  </div>
                </div>
                {currentPrice && (
                  <div className="text-right">
                    <div className="text-xs text-gray-400 mb-1">Current Price</div>
                    <div className="text-3xl font-bold text-amber-400">
                      ₹{currentPrice.toFixed(2)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enhanced Tabs */}
          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setActiveTab('signals')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-200 ${
                activeTab === 'signals'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                  : 'bg-[#1a1d28] text-gray-400 hover:text-white hover:bg-[#252936] border border-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Trading Signals
              </div>
            </button>
            <button
              onClick={() => setActiveTab('saved')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-200 ${
                activeTab === 'saved'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                  : 'bg-[#1a1d28] text-gray-400 hover:text-white hover:bg-[#252936] border border-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Saved Strategies
              </div>
            </button>
            <button
              onClick={() => setActiveTab('paper')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-200 ${
                activeTab === 'paper'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                  : 'bg-[#1a1d28] text-gray-400 hover:text-white hover:bg-[#252936] border border-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Paper Trading
              </div>
            </button>
          </div>
        </div>

        {activeTab === 'signals' && (
          <>
            {/* Enhanced Controls Panel */}
            <div className="bg-gradient-to-br from-[#1a1d28] to-[#252936] rounded-2xl p-6 mb-6 border border-gray-700/50 shadow-xl">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                {/* Commodity Selector */}
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-2 flex items-center gap-2">
                    <BarChart3 className="w-3 h-3" />
                    Commodity
                  </label>
                  <select
                    value={selectedSymbol}
                    onChange={(e) => handleSymbolChange(e.target.value)}
                    className="w-full bg-[#0f1117] border border-gray-600 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all"
                  >
                    {COMMODITY_SYMBOLS.map((commodity) => (
                      <option key={commodity.value} value={commodity.value}>
                        {commodity.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Timeframe */}
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-2 flex items-center gap-2">
                    <Clock className="w-3 h-3" />
                    Timeframe
                  </label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full bg-[#0f1117] border border-gray-600 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all"
                  >
                    <option value="1m">1 Minute</option>
                    <option value="5m">5 Minutes</option>
                    <option value="15m">15 Minutes</option>
                    <option value="1h">1 Hour</option>
                    <option value="1d">1 Day</option>
                  </select>
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-2 flex items-center gap-2">
                    <TrendingUp className="w-3 h-3" />
                    Duration
                  </label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full bg-[#0f1117] border border-gray-600 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all"
                  >
                    <option value="1d">1 Day</option>
                    <option value="5d">5 Days</option>
                    <option value="1w">1 Week</option>
                    <option value="1mo">1 Month</option>
                    <option value="3mo">3 Months</option>
                    <option value="6mo">6 Months</option>
                    <option value="1y">1 Year</option>
                  </select>
                </div>

                {/* Actions */}
                <div className="flex items-end gap-2">
                  <button
                    onClick={() => fetchAllSignals(true)}
                    disabled={loading}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-4 h-4" />
                        Refresh All
                      </>
                    )}
                  </button>
                  <label className="flex items-center gap-2 text-xs text-gray-300 bg-[#0f1117] px-3 py-2.5 rounded-lg border border-gray-600 cursor-pointer hover:border-amber-500/50 transition-all">
                    <input
                      type="checkbox"
                      checked={autoRefresh}
                      onChange={(e) => setAutoRefresh(e.target.checked)}
                      className="rounded accent-amber-500"
                    />
                    Auto
                  </label>
                </div>
              </div>

              {/* Trading Session Info */}
              {tradingSession && (
                <div className="mt-4 pt-4 border-t border-gray-700/50">
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-gray-400">Trading Session: </span>
                    <span className="font-semibold text-amber-400">{tradingSession}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Chart Section */}
            {activeTab === 'signals' && (
              <div className="bg-gradient-to-br from-[#1a1d28] to-[#252936] rounded-2xl p-4 mb-6 border border-gray-700/50 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-amber-400" />
                    Price Chart - {COMMODITY_SYMBOLS.find(c => c.value === selectedSymbol)?.label || selectedSymbol}
                  </h2>
                  <button
                    onClick={loadChartData}
                    disabled={chartLoading}
                    className="px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-all border border-blue-500/30 text-sm flex items-center gap-2"
                  >
                    <RefreshCw className={`w-4 h-4 ${chartLoading ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>
                <div className="relative">
                  {chartLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#131722]/50 z-10 rounded-lg">
                      <div className="animate-spin h-8 w-8 border-2 border-amber-500 border-t-transparent rounded-full" />
                    </div>
                  )}
                  <div 
                    ref={chartContainerRef} 
                    className="w-full rounded-lg overflow-hidden"
                    style={{ height: '400px' }}
                  />
                </div>
              </div>
            )}

            {/* Enhanced Next Day Perception */}
            {nextDayPerception ? (
              <div className="bg-gradient-to-br from-purple-900/30 via-blue-900/20 to-indigo-900/30 rounded-2xl p-6 mb-6 border-2 border-purple-500/30 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Target className="w-6 h-6 text-purple-400" />
                    Next Day Perception
                  </h2>
                  <button
                    onClick={fetchNextDayPerception}
                    className="p-2 bg-purple-500/20 hover:bg-purple-500/30 rounded-lg border border-purple-500/30 transition-all"
                  >
                    <RefreshCw className="w-4 h-4 text-purple-400" />
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-[#0f1117]/50 rounded-xl p-4 border border-purple-500/20">
                    <div className="text-xs text-gray-400 mb-1">Trend Direction</div>
                    <div className={`text-xl font-bold ${
                      nextDayPerception.trend === 'BULLISH' ? 'text-green-400' :
                      nextDayPerception.trend === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                      {nextDayPerception.trend}
                    </div>
                  </div>
                  {nextDayPerception.rsi && (
                    <div className="bg-[#0f1117]/50 rounded-xl p-4 border border-purple-500/20">
                      <div className="text-xs text-gray-400 mb-1">RSI Indicator</div>
                      <div className="text-xl font-bold text-purple-400">{nextDayPerception.rsi.toFixed(2)}</div>
                    </div>
                  )}
                  {nextDayPerception.patterns > 0 && (
                    <div className="bg-[#0f1117]/50 rounded-xl p-4 border border-purple-500/20">
                      <div className="text-xs text-gray-400 mb-1">Patterns Detected</div>
                      <div className="text-xl font-bold text-amber-400">{nextDayPerception.patterns}</div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-[#1a1d28]/50 rounded-2xl p-6 mb-6 border border-gray-700 text-center">
                <p className="text-gray-400 mb-3">Next Day Perception not available</p>
                <button
                  onClick={fetchNextDayPerception}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-semibold transition-all"
                >
                  Load Perception
                </button>
              </div>
            )}

            {/* Enhanced Comprehensive Signal */}
            {comprehensiveSignal && (
              <div className={`rounded-2xl p-6 mb-6 border-2 shadow-xl ${getSignalBgColor(comprehensiveSignal.signal)}`}>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Zap className="w-6 h-6" />
                    Comprehensive Signal
                  </h2>
                  <div className={`px-4 py-2 rounded-xl font-bold text-lg ${getSignalColor(comprehensiveSignal.signal)}`}>
                    {comprehensiveSignal.signal}
                  </div>
                </div>
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-gray-400">Confidence: </span>
                    <div className="flex-1 bg-gray-700 rounded-full h-2.5">
                      <div 
                        className={`h-2.5 rounded-full ${
                          comprehensiveSignal.signal.includes('BUY') ? 'bg-green-500' :
                          comprehensiveSignal.signal.includes('SELL') ? 'bg-red-500' : 'bg-yellow-500'
                        }`}
                        style={{ width: `${(comprehensiveSignal.confidence * 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold">{(comprehensiveSignal.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
                {comprehensiveSignal.message && (
                  <p className="text-sm text-gray-300 mb-4 bg-[#0f1117]/50 p-3 rounded-lg border border-gray-700">
                    {typeof comprehensiveSignal.message === 'string' 
                      ? comprehensiveSignal.message 
                      : (comprehensiveSignal.message as any)?.text || (comprehensiveSignal.message as any)?.message || 'Signal generated'}
                  </p>
                )}
                {comprehensiveSignal.entry_price && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-[#0f1117]/50 rounded-xl p-4 border border-gray-700">
                      <div className="text-xs text-gray-400 mb-1">Entry Price</div>
                      <div className="text-xl font-bold text-blue-400">₹{comprehensiveSignal.entry_price.toFixed(2)}</div>
                    </div>
                    {comprehensiveSignal.stop_loss && (
                      <div className="bg-[#0f1117]/50 rounded-xl p-4 border border-red-500/30">
                        <div className="text-xs text-gray-400 mb-1">Stop Loss</div>
                        <div className="text-xl font-bold text-red-400">₹{comprehensiveSignal.stop_loss.toFixed(2)}</div>
                      </div>
                    )}
                    {comprehensiveSignal.target_price && (
                      <div className="bg-[#0f1117]/50 rounded-xl p-4 border border-green-500/30">
                        <div className="text-xs text-gray-400 mb-1">Target Price</div>
                        <div className="text-xl font-bold text-green-400">₹{comprehensiveSignal.target_price.toFixed(2)}</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Enhanced Signal Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {renderSignalCard(
                'VWAP Trading',
                vwapSignal,
                fetchVWAPSignal,
                <Gauge className="w-4 h-4" />,
                vwapSignal && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">VWAP:</span>
                      <span className="font-semibold text-blue-400">₹{vwapSignal.vwap?.toFixed(2)}</span>
                    </div>
                    {vwapSignal.upper_band && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Upper Band:</span>
                        <span className="font-semibold text-green-400">₹{vwapSignal.upper_band.toFixed(2)}</span>
                      </div>
                    )}
                    {vwapSignal.lower_band && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Lower Band:</span>
                        <span className="font-semibold text-red-400">₹{vwapSignal.lower_band.toFixed(2)}</span>
                      </div>
                    )}
                    {vwapSignal.entry_price && (
                      <div className="mt-3 pt-3 border-t border-gray-600 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">Entry:</span>
                          <span className="font-bold text-blue-400">₹{vwapSignal.entry_price.toFixed(2)}</span>
                        </div>
                        {vwapSignal.stop_loss && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Stop Loss:</span>
                            <span className="font-semibold text-red-400">₹{vwapSignal.stop_loss.toFixed(2)}</span>
                          </div>
                        )}
                        {vwapSignal.target_price && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Target:</span>
                            <span className="font-semibold text-green-400">₹{vwapSignal.target_price.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Momentum',
                momentumSignal,
                fetchMomentumSignal,
                <TrendingUp className="w-4 h-4" />,
                momentumSignal && (
                  <div className="space-y-2 text-sm">
                    {momentumSignal.rsi && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">RSI:</span>
                        <span className="font-semibold text-purple-400">{momentumSignal.rsi.toFixed(2)}</span>
                      </div>
                    )}
                    {momentumSignal.roc && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">ROC:</span>
                        <span className="font-semibold text-cyan-400">{momentumSignal.roc.toFixed(2)}%</span>
                      </div>
                    )}
                    {momentumSignal.entry_price && (
                      <div className="mt-3 pt-3 border-t border-gray-600 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">Entry:</span>
                          <span className="font-bold text-blue-400">₹{momentumSignal.entry_price.toFixed(2)}</span>
                        </div>
                        {momentumSignal.stop_loss && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Stop Loss:</span>
                            <span className="font-semibold text-red-400">₹{momentumSignal.stop_loss.toFixed(2)}</span>
                          </div>
                        )}
                        {momentumSignal.target_price && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Target:</span>
                            <span className="font-semibold text-green-400">₹{momentumSignal.target_price.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    )}
                    {momentumSignal.message && (
                      <div className="mt-3 pt-3 border-t border-gray-600 text-gray-300 text-xs">
                        {typeof momentumSignal.message === 'string' ? momentumSignal.message : (momentumSignal.message as any)?.text || (momentumSignal.message as any)?.message || 'Momentum signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Breakout',
                breakoutSignal,
                fetchBreakoutSignal,
                <Zap className="w-4 h-4" />,
                breakoutSignal && (
                  <div className="space-y-2 text-sm">
                    {breakoutSignal.resistance && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Resistance:</span>
                        <span className="font-semibold text-red-400">₹{breakoutSignal.resistance.toFixed(2)}</span>
                      </div>
                    )}
                    {breakoutSignal.support && (
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Support:</span>
                        <span className="font-semibold text-green-400">₹{breakoutSignal.support.toFixed(2)}</span>
                      </div>
                    )}
                    {breakoutSignal.entry_price && (
                      <div className="mt-3 pt-3 border-t border-gray-600 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">Entry:</span>
                          <span className="font-bold text-blue-400">₹{breakoutSignal.entry_price.toFixed(2)}</span>
                        </div>
                        {breakoutSignal.stop_loss && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Stop Loss:</span>
                            <span className="font-semibold text-red-400">₹{breakoutSignal.stop_loss.toFixed(2)}</span>
                          </div>
                        )}
                        {breakoutSignal.target_price && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Target:</span>
                            <span className="font-semibold text-green-400">₹{breakoutSignal.target_price.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    )}
                    {breakoutSignal.message && (
                      <div className="mt-3 pt-3 border-t border-gray-600 text-gray-300 text-xs">
                        {typeof breakoutSignal.message === 'string' ? breakoutSignal.message : (breakoutSignal.message as any)?.text || (breakoutSignal.message as any)?.message || 'Breakout signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Mean Reversion',
                meanReversionSignal,
                fetchMeanReversionSignal,
                <ArrowUpDown className="w-4 h-4" />,
                meanReversionSignal && (
                  <div className="text-xs space-y-1">
                    {meanReversionSignal.deviation_from_mean && (
                      <div>Deviation: {meanReversionSignal.deviation_from_mean.toFixed(2)}%</div>
                    )}
                    {meanReversionSignal.entry_price && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div>Entry: ₹{meanReversionSignal.entry_price.toFixed(2)}</div>
                        {meanReversionSignal.stop_loss && <div>SL: ₹{meanReversionSignal.stop_loss.toFixed(2)}</div>}
                        {meanReversionSignal.target_price && <div>Target: ₹{meanReversionSignal.target_price.toFixed(2)}</div>}
                      </div>
                    )}
                    {meanReversionSignal.message && (
                      <div className="mt-2 pt-2 border-t border-gray-600 text-gray-400">
                        {typeof meanReversionSignal.message === 'string' ? meanReversionSignal.message : (meanReversionSignal.message as any)?.text || (meanReversionSignal.message as any)?.message || 'Mean reversion signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Scalping',
                scalpingSignal,
                fetchScalpingSignal,
                <Activity className="w-4 h-4" />,
                scalpingSignal && (
                  <div className="text-xs space-y-1">
                    {scalpingSignal.entry_price && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div>Entry: ₹{scalpingSignal.entry_price.toFixed(2)}</div>
                        {scalpingSignal.stop_loss && <div>SL: ₹{scalpingSignal.stop_loss.toFixed(2)}</div>}
                        {scalpingSignal.target_price && <div>Target: ₹{scalpingSignal.target_price.toFixed(2)}</div>}
                      </div>
                    )}
                    {scalpingSignal.message && (
                      <div className="mt-2 pt-2 border-t border-gray-600 text-gray-400">
                        {typeof scalpingSignal.message === 'string' ? scalpingSignal.message : (scalpingSignal.message as any)?.text || (scalpingSignal.message as any)?.message || 'Scalping signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Gap Trading',
                gapTradingSignal,
                fetchGapTradingSignal,
                <Target className="w-4 h-4" />,
                gapTradingSignal && (
                  <div className="text-xs space-y-1">
                    {gapTradingSignal.gap_pct && (
                      <div>Gap: {gapTradingSignal.gap_pct.toFixed(2)}%</div>
                    )}
                    {gapTradingSignal.gap_type && (
                      <div>Type: {gapTradingSignal.gap_type}</div>
                    )}
                    {gapTradingSignal.entry_price && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div>Entry: ₹{gapTradingSignal.entry_price.toFixed(2)}</div>
                        {gapTradingSignal.stop_loss && <div>SL: ₹{gapTradingSignal.stop_loss.toFixed(2)}</div>}
                        {gapTradingSignal.target_price && <div>Target: ₹{gapTradingSignal.target_price.toFixed(2)}</div>}
                      </div>
                    )}
                    {gapTradingSignal.message && (
                      <div className="mt-2 pt-2 border-t border-gray-600 text-gray-400">
                        {typeof gapTradingSignal.message === 'string' ? gapTradingSignal.message : (gapTradingSignal.message as any)?.text || (gapTradingSignal.message as any)?.message || 'Gap trading signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Closing Range',
                closingRangeSignal,
                fetchClosingRangeSignal,
                <Clock className="w-4 h-4" />,
                closingRangeSignal && (
                  <div className="text-xs space-y-1">
                    {closingRangeSignal.closing_high && (
                      <div>High: ₹{closingRangeSignal.closing_high.toFixed(2)}</div>
                    )}
                    {closingRangeSignal.closing_low && (
                      <div>Low: ₹{closingRangeSignal.closing_low.toFixed(2)}</div>
                    )}
                    {closingRangeSignal.entry_price && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div>Entry: ₹{closingRangeSignal.entry_price.toFixed(2)}</div>
                        {closingRangeSignal.stop_loss && <div>SL: ₹{closingRangeSignal.stop_loss.toFixed(2)}</div>}
                        {closingRangeSignal.target_price && <div>Target: ₹{closingRangeSignal.target_price.toFixed(2)}</div>}
                      </div>
                    )}
                    {closingRangeSignal.message && (
                      <div className="mt-2 pt-2 border-t border-gray-600 text-gray-400">
                        {typeof closingRangeSignal.message === 'string' ? closingRangeSignal.message : (closingRangeSignal.message as any)?.text || (closingRangeSignal.message as any)?.message || 'Closing range signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'Volume Profile',
                volumeProfileSignal,
                fetchVolumeProfileSignal,
                <BarChart3 className="w-4 h-4" />,
                volumeProfileSignal && (
                  <div className="text-xs space-y-1">
                    {volumeProfileSignal.poc_price && (
                      <div>POC: ₹{volumeProfileSignal.poc_price.toFixed(2)}</div>
                    )}
                    {volumeProfileSignal.value_area_high && (
                      <div>VA High: ₹{volumeProfileSignal.value_area_high.toFixed(2)}</div>
                    )}
                    {volumeProfileSignal.value_area_low && (
                      <div>VA Low: ₹{volumeProfileSignal.value_area_low.toFixed(2)}</div>
                    )}
                    {volumeProfileSignal.entry_price && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div>Entry: ₹{volumeProfileSignal.entry_price.toFixed(2)}</div>
                        {volumeProfileSignal.stop_loss && <div>SL: ₹{volumeProfileSignal.stop_loss.toFixed(2)}</div>}
                        {volumeProfileSignal.target_price && <div>Target: ₹{volumeProfileSignal.target_price.toFixed(2)}</div>}
                      </div>
                    )}
                    {volumeProfileSignal.message && (
                      <div className="mt-2 pt-2 border-t border-gray-600 text-gray-400">
                        {typeof volumeProfileSignal.message === 'string' ? volumeProfileSignal.message : (volumeProfileSignal.message as any)?.text || (volumeProfileSignal.message as any)?.message || 'Volume profile signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}

              {renderSignalCard(
                'News Trading',
                newsSignal,
                fetchNewsSignal,
                <AlertCircle className="w-4 h-4" />,
                newsSignal && (
                  <div className="text-xs space-y-1">
                    {newsSignal.sentiment_score !== undefined && (
                      <div>Sentiment: {newsSignal.sentiment_score.toFixed(2)}</div>
                    )}
                    {newsSignal.news_count !== undefined && (
                      <div>News Count: {newsSignal.news_count}</div>
                    )}
                    {newsSignal.message && (
                      <div className="mt-2 pt-2 border-t border-gray-600 text-gray-400">
                        {typeof newsSignal.message === 'string' ? newsSignal.message : (newsSignal.message as any)?.text || (newsSignal.message as any)?.message || 'News signal generated'}
                      </div>
                    )}
                  </div>
                )
              )}
            </div>
          </>
        )}

        {activeTab === 'saved' && (
          <SavedStrategies
            symbol={selectedSymbol}
            onStrategySelect={(strategy) => {
              setSelectedStrategy(strategy);
            }}
            onStrategyDelete={() => {
              setSelectedStrategy(null);
            }}
          />
        )}

        {activeTab === 'paper' && (
          <PaperTrading
            strategy={selectedStrategy!}
            symbol={selectedSymbol}
            currentPrice={currentPrice || 0}
          />
        )}
      </div>
    </div>
  );
};

export default CommodityTrading;

