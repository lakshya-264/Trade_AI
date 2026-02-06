/**
 * Intraday Trading Page
 * Complete UI for intraday trading with real-time signals
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Clock, TrendingUp, TrendingDown, Activity, 
  RefreshCw, Zap, Target, AlertCircle, 
  BarChart3, Gauge, ArrowUpDown, ExternalLink
} from 'lucide-react';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';
import StockSelector from '../components/StockSelector';
import SavedStrategies from '../components/strategy/SavedStrategies';
import PaperTrading from '../components/strategy/PaperTrading';
import { Strategy } from '../components/strategy/StrategyBuilder';
import api from '../services/api';

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
  rvol?: number;
  volume_quality?: string;
  fakeout_risk?: boolean;
  double_top_resistance?: number;
  near_double_top?: boolean;
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

interface SMASignal {
  signal: string;
  sma20?: number;
  sma50?: number;
  sma200?: number;
  price_vs_sma20?: number;
  price_vs_sma50?: number;
  price_vs_sma200?: number;
  golden_cross?: boolean;
  death_cross?: boolean;
  multi_ma_alignment?: string;
  alignment_type?: 'perfect_bullish' | 'perfect_bearish' | 'partial_bullish' | 'partial_bearish' | 'none';
  message: string;
  ai_insight?: string;
  strength?: string;
  confidence?: number;
}

interface OpeningRangeSignal {
  signal: string;
  opening_high?: number;
  opening_low?: number;
  opening_range?: number;
  current_price?: number;
  entry?: number;
  stop_loss?: number;
  target?: number;
  reason: string;
  strength?: string;
}

interface MACDSignal {
  signal: string;
  macd_line?: number;
  macd_signal?: number;
  macd_histogram?: number;
  bullish_crossover?: boolean;
  bearish_crossover?: boolean;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  reason: string;
  strength?: string;
  confidence?: number;
  ai_insight?: string;
}

interface BollingerBandsSignal {
  signal: string;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
  band_width?: number;
  percent_b?: number;
  is_squeeze?: boolean;
  is_expansion?: boolean;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  reason: string;
  strength?: string;
  confidence?: number;
  ai_insight?: string;
}

interface GapInfo {
  type: 'UPWARD' | 'DOWNWARD';
  start: number;
  end: number;
  size_pct: number;
  filled?: boolean;
}

const IntradayTrading: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selectedSymbol, setSelectedSymbol] = useState(() => {
    const symbolFromParams = searchParams.get('symbol');
    return symbolFromParams || 'NIFTY';
  });
  const [timeframe, setTimeframe] = useState('5m');
  const [duration, setDuration] = useState('1d'); // Duration filter: 1d, 2d, 3d, 4d, 5d, 1w, 1mo, 3mo, 6mo, 1y
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
  const [smaSignal, setSmaSignal] = useState<SMASignal | null>(null);
  const [openingRangeSignal, setOpeningRangeSignal] = useState<OpeningRangeSignal | null>(null);
  const [macdSignal, setMacdSignal] = useState<MACDSignal | null>(null);
  const [bollingerSignal, setBollingerSignal] = useState<BollingerBandsSignal | null>(null);
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

  useEffect(() => {
    if (autoRefresh && selectedSymbol) {
      const interval = setInterval(() => {
        // Fetch price first, then signals
        fetchCurrentPrice();
        fetchAllSignals();
      }, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, selectedSymbol, timeframe, duration]);

  useEffect(() => {
    // Reset current price when symbol changes
    setCurrentPrice(null);
    
    // Fetch data for the new symbol
    fetchTradingSession();
    fetchCurrentPrice();
    fetchNextDayPerception();
    // Auto-fetch signals on component mount or symbol/timeframe/duration change
    fetchAllSignals();
  }, [selectedSymbol, timeframe, duration]);

  // Convert duration to days for API calls
  const getDurationInDays = (duration: string): number => {
    const durationMap: Record<string, number> = {
      '1d': 1,
      '2d': 2,
      '3d': 3,
      '4d': 4,
      '5d': 5,
      '1w': 7,
      '1mo': 30,
      '3mo': 90,
      '6mo': 180,
      '1y': 365
    };
    return durationMap[duration] || 1;
  };

  const fetchCurrentPrice = async (symbol?: string) => {
    const symbolToFetch = symbol || selectedSymbol;
    if (!symbolToFetch) return;
    
    try {
      // Normalize symbol for API call
      let normalizedSymbol = symbolToFetch;
      // For indices, use as-is; for stocks, ensure .NS suffix if needed
      const isIndex = ['NIFTY', 'NIFTY50', 'NIFTY_50', 'BANKNIFTY', 'NIFTYBANK', 'SENSEX', 'NIFTY_IT', 'NIFTYIT', 'NIFTYMIDCAP50', 'NIFTYFIN', 'BANKEX'].includes(symbolToFetch.toUpperCase());
      
      if (!isIndex && !normalizedSymbol.includes('.')) {
        normalizedSymbol = `${normalizedSymbol}.NS`;
      }
      
      // Try fetching with normalized symbol first
      let quote = await api.getQuote(normalizedSymbol, 'NSE');
      
      if (quote && quote.last_price && quote.last_price > 0) {
        setCurrentPrice(quote.last_price);
        return;
      }
      
      // Fallback 1: try without .NS for stocks
      if (!isIndex && normalizedSymbol.endsWith('.NS')) {
        quote = await api.getQuote(symbolToFetch, 'NSE');
        if (quote && quote.last_price && quote.last_price > 0) {
          setCurrentPrice(quote.last_price);
          return;
        }
      }
      
      // Fallback 2: try with BSE exchange for BSE stocks
      if (symbolToFetch.includes('BSE') || symbolToFetch.toUpperCase().includes('BSE')) {
        quote = await api.getQuote(symbolToFetch.replace('.NS', '').replace('.BO', ''), 'BSE');
        if (quote && quote.last_price && quote.last_price > 0) {
          setCurrentPrice(quote.last_price);
          return;
        }
      }
      
      // If all attempts fail, log but don't throw
      console.warn(`Could not fetch price for ${symbolToFetch}, will try to get from signal data`);
    } catch (error) {
      console.error(`Failed to fetch current price for ${symbolToFetch}:`, error);
      // Don't set price to null, keep previous value if available
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
      // Fetch chart analysis for next day prediction with multi-timeframe enabled
      // Use intraday endpoint which properly normalizes symbols for all stock types
      const response = await httpClient.get(`/api/comprehensive-trading/intraday/chart-analysis/${selectedSymbol}?timeframe=${encodeURIComponent(timeframe)}&enable_multi_timeframe=true`) as any;
      
      if (response.success && response.data) {
        const analysis = response.data;
        // Extract relevant data for next day perception
        // Debug logging for all new features
        console.log('📊 Next Day Perception - Full API Response:', {
          patterns_detected: analysis.facts?.patterns_detected,
          pattern_names: analysis.facts?.pattern_names,
          multi_timeframe_analysis: analysis.facts?.multi_timeframe_analysis,
          multi_timeframe_trend: analysis.facts?.multi_timeframe_trend,
          multi_timeframe_confidence: analysis.facts?.multi_timeframe_confidence,
          ml_prediction: analysis.facts?.ml_prediction,
          ml_confidence: analysis.facts?.ml_confidence,
          pattern_success_rates: analysis.facts?.pattern_success_rates,
          options_flow_analysis: analysis.facts?.options_flow_analysis,
          options_sentiment: analysis.facts?.options_sentiment,
          has_bullish_divergence: analysis.facts?.has_bullish_divergence,
          has_bearish_divergence: analysis.facts?.has_bearish_divergence,
          // New indicators
          gift_nifty_data: analysis.facts?.gift_nifty_data,
          india_vix_data: analysis.facts?.india_vix_data,
          next_day_opening_analysis: analysis.facts?.next_day_opening_analysis
        });
        
        setNextDayPerception({
          trend: analysis.facts?.trend || 'NEUTRAL',
          rsi: analysis.facts?.rsi || null,
          patterns: analysis.facts?.patterns_detected || 0,
          pattern_names: Array.isArray(analysis.facts?.pattern_names) ? analysis.facts.pattern_names : [],
          high_confidence_patterns: Array.isArray(analysis.facts?.high_confidence_patterns) ? analysis.facts.high_confidence_patterns : [],
          pattern_confidence_scores: Array.isArray(analysis.facts?.pattern_confidence_scores) ? analysis.facts.pattern_confidence_scores : [],
          price_vs_sma20: analysis.facts?.price_vs_sma20 || null,
          price_vs_sma50: analysis.facts?.price_vs_sma50 || null,
          volume_trend: analysis.facts?.volume_trend || 'NEUTRAL',
          suggestions: analysis.suggestions || [],
          current_price: analysis.facts?.current_price || currentPrice,
          // Support/Resistance
          support_levels: analysis.facts?.support_levels || [],
          resistance_levels: analysis.facts?.resistance_levels || [],
          nearest_support: analysis.facts?.nearest_support || null,
          nearest_resistance: analysis.facts?.nearest_resistance || null,
          support_distance_pct: analysis.facts?.support_distance_pct || null,
          resistance_distance_pct: analysis.facts?.resistance_distance_pct || null,
          pivot_points: analysis.facts?.pivot_points || [],
          // Divergence
          divergences: analysis.facts?.divergences || [],
          has_bullish_divergence: analysis.facts?.has_bullish_divergence || false,
          has_bearish_divergence: analysis.facts?.has_bearish_divergence || false,
          bullish_divergence_count: analysis.facts?.bullish_divergence_count || 0,
          bearish_divergence_count: analysis.facts?.bearish_divergence_count || 0,
          // Volume Profile
          volume_profile_levels: analysis.facts?.volume_profile_levels || [],
          // Multi-Timeframe Analysis
          multi_timeframe_analysis: analysis.facts?.multi_timeframe_analysis || {},
          multi_timeframe_trend: analysis.facts?.multi_timeframe_trend || 'NEUTRAL',
          multi_timeframe_confidence: analysis.facts?.multi_timeframe_confidence || 0,
          // ML Prediction
          ml_prediction: analysis.facts?.ml_prediction || 'NEUTRAL',
          ml_confidence: analysis.facts?.ml_confidence || 0,
          // Pattern Success Rates
          pattern_success_rates: analysis.facts?.pattern_success_rates || {},
          // Options Flow
          options_flow_analysis: analysis.facts?.options_flow_analysis || null,
          options_sentiment: analysis.facts?.options_sentiment || 'NEUTRAL',
          // GIFT NIFTY Analysis (for NIFTY next day opening insights)
          gift_nifty_data: analysis.facts?.gift_nifty_data || null,
          gift_nifty_sentiment: analysis.facts?.gift_nifty_sentiment || null,
          // India VIX Analysis (volatility indicator)
          india_vix_data: analysis.facts?.india_vix_data || null,
          india_vix_level: analysis.facts?.india_vix_level || null,
          india_vix_sentiment: analysis.facts?.india_vix_sentiment || null,
          // Combined Next Day Opening Analysis
          next_day_opening_analysis: analysis.facts?.next_day_opening_analysis || null
        });
        
        // Debug logging for resistance levels
        console.log('🔍 Next Day Perception - Support/Resistance Data:', {
          support_levels: analysis.facts?.support_levels,
          resistance_levels: analysis.facts?.resistance_levels,
          pivot_points: analysis.facts?.pivot_points,
          current_price: analysis.facts?.current_price
        });
      }
    } catch (error) {
      console.error('Failed to fetch next day perception:', error);
    }
  };

  const fetchAIInsight = async (signalType: string, signalData: any) => {
    try {
      const response = await httpClient.post(
        `/api/comprehensive-trading/intraday/ai-insight?symbol=${selectedSymbol}&signal_type=${signalType}`,
        signalData
      ) as any;
      return response?.insight || null;
    } catch (error) {
      console.error(`AI insight error for ${signalType}:`, error);
      return null;
    }
  };

  const fetchVWAPSignal = async () => {
    setLoading(true);
    try {
      // Fetch current price if not available
      if (!currentPrice) {
        await fetchCurrentPrice();
      }
      
      const days = getDurationInDays(duration);
      console.log(`📊 Fetching VWAP signal: symbol=${selectedSymbol}, timeframe=${timeframe}, duration=${duration} (${days} days)`);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/vwap-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      console.log('VWAP Response:', response);
      
      // httpClient returns response directly, not wrapped in data
      if (response?.success) {
        const data = response.data || {};
        const vwapValue = response.vwap || data.vwap || 0;
        console.log('VWAP Data:', data, 'VWAP Value:', vwapValue);
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        // Map backend response to frontend interface
        setVwapSignal({
          signal: data.signal || 'HOLD',
          vwap: vwapValue,
          upper_band: data.upper_band,
          lower_band: data.lower_band,
          entry_price: data.entry_price || data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target_price || data.target
        });
        toast.success('VWAP signal updated');
      } else {
        console.error('VWAP signal response:', response);
        const errorMsg = response?.error || response?.detail || 'No data available';
        // Don't show toast for data unavailability - show in UI instead
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          setVwapSignal(null);
          // Show info message instead of error
          toast.error(`VWAP signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch VWAP signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('VWAP signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch VWAP signal';
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        setVwapSignal(null);
        toast.error(`VWAP signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchMomentumSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/momentum-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&period=${momentumPeriod}&threshold=${momentumThreshold}&days=${days}`) as any;
      console.log('Momentum Response:', response);
      
      // httpClient returns response directly, not wrapped in data
      if (response?.success) {
        const data = response.data || {};
        console.log('Momentum Data:', data);
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('momentum', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          rsi: data.rsi,
          roc: data.roc || data.roc_pct,
          ...data
        });
        
        // Map backend response to frontend interface
        setMomentumSignal({
          signal: data.signal || 'HOLD',
          rsi: data.rsi,
          roc: data.roc || data.roc_pct,
          message: data.reason || data.message || 'No reason provided',
          ai_insight: aiInsight,
          momentum_strength: data.rsi && data.rsi > 70 ? 'Strong Overbought' : 
                           data.rsi && data.rsi < 30 ? 'Strong Oversold' : 
                           data.rsi && data.rsi > 50 ? 'Bullish' : 'Bearish',
          trend_direction: data.roc && data.roc > 0 ? 'Upward' : 'Downward'
        });
        toast.success('Momentum signal updated');
      } else {
        console.error('Momentum signal response:', response);
        const errorMsg = response?.error || response?.detail || 'No data available';
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          setMomentumSignal(null);
          toast.error(`Momentum signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch Momentum signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('Momentum signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch momentum signal';
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        setMomentumSignal(null);
        toast.error(`Momentum signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchBreakoutSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/breakout-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&lookback_period=${breakoutLookback}&volume_threshold=${breakoutVolumeThreshold}&days=${days}`) as any;
      console.log('Breakout Full Response:', JSON.stringify(response, null, 2));
      
      // httpClient returns response directly, not wrapped in data
      if (response?.success) {
        const data = response.data || {};
        console.log('Breakout Signal Data:', data);
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('breakout', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          resistance: data.resistance || data.resistance_level,
          support: data.support || data.support_level,
          double_top_resistance: data.double_top_resistance,
          near_double_top: data.near_double_top,
          ...data
        });
        
        // Map backend response to frontend interface
        // Backend returns: entry, target (not entry_price, target_price)
        const breakoutSignal = {
          signal: data.signal || 'HOLD',
          resistance: data.resistance || data.resistance_level || null,
          support: data.support || data.support_level || null,
          entry_price: data.entry || data.entry_price || null,
          stop_loss: data.stop_loss || null,
          target_price: data.target || data.target_price || null,
          message: data.reason || data.message || 'No reason provided',
          ai_insight: aiInsight,
          breakout_strength: data.strength || (data.volume_confirmed ? 'Strong' : 'Moderate'),
          volume_confirmation: data.volume_confirmed || false,
          rvol: typeof data.rvol === 'number' ? data.rvol : (data.rvol ? Number(data.rvol) : null),
          volume_quality: data.volume_quality,
          fakeout_risk: !!data.fakeout_risk,
          double_top_resistance: data.double_top_resistance || null,
          near_double_top: data.near_double_top || false
        };
        
        console.log('Setting Breakout Signal:', breakoutSignal);
        setBreakoutSignal(breakoutSignal);
        toast.success('Breakout signal updated');
      } else {
        console.error('Breakout signal - No success flag:', response);
        const errorDetail = response?.error || response?.detail || 'No data available';
        if (errorDetail.includes('No data available') || errorDetail.includes('market is open')) {
          setBreakoutSignal(null);
          toast.error(`Breakout signal: ${errorDetail}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch Breakout signal: ' + errorDetail);
        }
      }
    } catch (error: any) {
      console.error('Breakout signal error:', error);
      console.error('Error response:', error.response);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch breakout signal';
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        setBreakoutSignal(null);
        toast.error(`Breakout signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchComprehensiveSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/comprehensive-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&strategy=${strategy}&days=${days}`) as any;
      // httpClient returns response directly, not wrapped in data
      if (response?.success) {
        setComprehensiveSignal(response.data);
        toast.success('Comprehensive signal updated');
      } else {
        console.error('Comprehensive signal response:', response);
        const errorMsg = response?.error || response?.detail || 'No data available';
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          setComprehensiveSignal(null);
          toast.error(`Comprehensive signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch Comprehensive signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('Comprehensive signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch comprehensive signal';
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        setComprehensiveSignal(null);
        toast.error(`Comprehensive signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchMeanReversionSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/mean-reversion-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&period=${meanReversionPeriod}&std_multiplier=${meanReversionStdMultiplier}&days=${days}`) as any;
      console.log('Mean Reversion Response:', response);
      
      // httpClient returns response directly, not wrapped in data
      if (response?.success) {
        const data = response.data || {};
        console.log('Mean Reversion Data:', data);
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('mean_reversion', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          mean: data.mean,
          deviation: data.deviation,
          ...data
        });
        
        // Map backend response to frontend interface
        setMeanReversionSignal({
          signal: data.signal || 'HOLD',
          entry_price: data.entry || data.entry_price || null,
          stop_loss: data.stop_loss || null,
          target_price: data.target || data.target_price || null,
          message: data.reason || data.message || 'No reason provided',
          ai_insight: aiInsight,
          deviation_from_mean: data.deviation_pct || data.deviation,
          reversion_probability: data.mean && data.current_price ? 
            Math.abs((data.current_price - data.mean) / data.mean) * 100 : undefined
        });
        toast.success('Mean Reversion signal updated');
      } else {
        console.error('Mean Reversion signal response:', response);
        const errorMsg = response?.error || response?.detail || 'No data available';
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          setMeanReversionSignal(null);
          toast.error(`Mean Reversion signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch Mean Reversion signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('Mean Reversion signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch mean reversion signal';
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        setMeanReversionSignal(null);
        toast.error(`Mean Reversion signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchScalpingSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/scalping-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&tick_size=${scalpingTickSize}&min_profit_target=${scalpingMinProfitTarget}&days=${days}`) as any;
      console.log('Scalping Response:', response);
      
      // httpClient returns response directly, not wrapped in data
      if (response?.success) {
        const data = response.data || {};
        console.log('Scalping Data:', data);
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('scalping', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          price_change_pct: data.price_change_pct,
          micro_trend: data.micro_trend,
          ...data
        });
        
        // Map backend response to frontend interface
        setScalpingSignal({
          signal: data.signal || 'HOLD',
          entry_price: data.entry || data.entry_price || null,
          stop_loss: data.stop_loss || null,
          target_price: data.target || data.target_price || null,
          message: data.reason || data.message || 'No reason provided',
          ai_insight: aiInsight,
          scalping_opportunity: data.micro_trend === 'UP' ? 'Quick Long' : 
                               data.micro_trend === 'DOWN' ? 'Quick Short' : 'Wait',
          quick_profit_potential: data.target && data.entry ? 
            ((data.target - data.entry) / data.entry * 100) : undefined
        });
        toast.success('Scalping signal updated');
      } else {
        console.error('Scalping signal response:', response);
        const errorMsg = response?.error || response?.detail || 'No data available';
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          setScalpingSignal(null);
          toast.error(`Scalping signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch Scalping signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('Scalping signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch scalping signal';
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        setScalpingSignal(null);
        toast.error(`Scalping signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchGapTradingSignal = async () => {
    setLoading(true);
    try {
      // Gap trading needs at least 2 days of data (today's open and yesterday's close)
      const days = Math.max(2, getDurationInDays(duration));
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/gap-trading-signal?symbol=${selectedSymbol}&timeframe=1d&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        setGapTradingSignal({
          signal: data.signal || 'HOLD',
          gap_type: data.gap_type,
          gap_pct: data.gap_pct,
          today_open: data.today_open,
          previous_close: data.previous_close,
          entry_price: data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target,
          message: data.reason || data.message || 'No reason provided'
        });
        toast.success('Gap Trading signal updated');
      } else {
        const errorMsg = response?.error || response?.detail || 'No data available';
        setGapTradingSignal(null);
        toast.error(`Gap Trading: ${errorMsg}`, { duration: 3000 });
      }
    } catch (error: any) {
      console.error('Gap Trading error:', error);
      setGapTradingSignal(null);
      toast.error('Failed to fetch gap trading signal');
    } finally {
      setLoading(false);
    }
  };

  const fetchClosingRangeSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/closing-range-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        setClosingRangeSignal({
          signal: data.signal || 'HOLD',
          closing_high: data.closing_high,
          closing_low: data.closing_low,
          closing_range: data.closing_range,
          closing_mid: data.closing_mid,
          entry_price: data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target,
          message: data.reason || data.message || 'No reason provided'
        });
        toast.success('Closing Range signal updated');
      } else {
        setClosingRangeSignal(null);
        toast.error('Failed to fetch closing range signal', { duration: 3000 });
      }
    } catch (error: any) {
      console.error('Closing Range error:', error);
      setClosingRangeSignal(null);
      toast.error('Failed to fetch closing range signal');
    } finally {
      setLoading(false);
    }
  };

  const fetchVolumeProfileSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/volume-profile-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        
        // Update current price from response if available (prefer response price as it's more accurate)
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        setVolumeProfileSignal({
          signal: data.signal || 'HOLD',
          poc_price: data.poc_price,
          poc_volume: data.poc_volume,
          value_area_high: data.value_area_high,
          value_area_low: data.value_area_low,
          price_vs_poc_pct: data.price_vs_poc_pct,
          entry_price: data.entry,
          stop_loss: data.stop_loss,
          target_price: data.target,
          message: data.reason || data.message || 'No reason provided'
        });
        toast.success('Volume Profile signal updated');
      } else {
        setVolumeProfileSignal(null);
        toast.error('Failed to fetch volume profile signal', { duration: 3000 });
      }
    } catch (error: any) {
      console.error('Volume Profile error:', error);
      setVolumeProfileSignal(null);
      toast.error('Failed to fetch volume profile signal');
    } finally {
      setLoading(false);
    }
  };

  const fetchNewsSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/news-signal?symbol=${selectedSymbol}&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        setNewsSignal({
          signal: data.signal || 'HOLD',
          sentiment_score: data.sentiment_score,
          news_count: data.news_count,
          high_impact_count: data.high_impact_count,
          message: data.reason || data.message || 'No reason provided'
        });
        toast.success('News signal updated');
      } else {
        setNewsSignal(null);
        toast.error('Failed to fetch news signal', { duration: 3000 });
      }
    } catch (error: any) {
      console.error('News signal error:', error);
      setNewsSignal(null);
      toast.error('Failed to fetch news signal');
    } finally {
      setLoading(false);
    }
  };

  const fetchSMASignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/sma-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      
      if (response?.success) {
        const data = response.data || {};
        
        // Update current price from response if available
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          // If still no price, try fetching again
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('sma', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          sma20: data.sma20,
          sma50: data.sma50,
          sma200: data.sma200,
          golden_cross: data.golden_cross,
          death_cross: data.death_cross,
          alignment_type: data.alignment_type,
          ...data
        });
        
        setSmaSignal({
          signal: data.signal || 'HOLD',
          sma20: data.sma20,
          sma50: data.sma50,
          sma200: data.sma200,
          price_vs_sma20: data.price_vs_sma20,
          price_vs_sma50: data.price_vs_sma50,
          price_vs_sma200: data.price_vs_sma200,
          golden_cross: data.golden_cross || false,
          death_cross: data.death_cross || false,
          multi_ma_alignment: data.multi_ma_alignment,
          alignment_type: data.alignment_type || 'none',
          message: data.reason || data.message || 'SMA signal generated',
          ai_insight: aiInsight,
          strength: data.strength || 'WEAK',
          confidence: data.confidence || 50
        });
        toast.success('SMA signal updated');
      } else {
        const errorMsg = response?.error || response?.detail || 'No data available';
        setSmaSignal(null);
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          toast.error(`SMA signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch SMA signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('SMA signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch SMA signal';
      setSmaSignal(null);
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        toast.error(`SMA signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchOpeningRangeSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/opening-range?symbol=${selectedSymbol}&timeframe=1m&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          await fetchCurrentPrice();
        }
        
        setOpeningRangeSignal({
          signal: data.signal || 'HOLD',
          opening_high: data.opening_high,
          opening_low: data.opening_low,
          opening_range: data.opening_range,
          current_price: data.current_price,
          entry: data.entry,
          stop_loss: data.stop_loss,
          target: data.target,
          reason: data.reason || data.message || 'Opening range signal generated',
          strength: data.strength || 'WEAK'
        });
        toast.success('Opening Range signal updated');
      } else {
        setOpeningRangeSignal(null);
        toast.error('Failed to fetch opening range signal', { duration: 3000 });
      }
    } catch (error: any) {
      console.error('Opening Range error:', error);
      setOpeningRangeSignal(null);
      toast.error('Failed to fetch opening range signal');
    } finally {
      setLoading(false);
    }
  };

  const fetchMACDSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/macd-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('macd', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          macd_line: data.macd_line,
          macd_signal: data.macd_signal,
          macd_histogram: data.macd_histogram,
          bullish_crossover: data.bullish_crossover,
          bearish_crossover: data.bearish_crossover,
          ...data
        });
        
        setMacdSignal({
          signal: data.signal || 'HOLD',
          macd_line: data.macd_line,
          macd_signal: data.macd_signal,
          macd_histogram: data.macd_histogram,
          bullish_crossover: data.bullish_crossover || false,
          bearish_crossover: data.bearish_crossover || false,
          entry_price: data.entry_price,
          stop_loss: data.stop_loss,
          target_price: data.target_price,
          reason: data.reason || data.message || 'MACD signal generated',
          strength: data.strength || 'WEAK',
          confidence: data.confidence || 50,
          ai_insight: aiInsight
        });
        toast.success('MACD signal updated');
      } else {
        const errorMsg = response?.error || response?.detail || 'No data available';
        setMacdSignal(null);
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          toast.error(`MACD signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch MACD signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('MACD signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch MACD signal';
      setMacdSignal(null);
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        toast.error(`MACD signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchBollingerBandsSignal = async () => {
    setLoading(true);
    try {
      const days = getDurationInDays(duration);
      const response = await httpClient.post(`/api/comprehensive-trading/intraday/bollinger-signal?symbol=${selectedSymbol}&timeframe=${timeframe}&days=${days}`) as any;
      if (response?.success) {
        const data = response.data || {};
        
        if (data.current_price && data.current_price > 0) {
          setCurrentPrice(data.current_price);
        } else if (!currentPrice) {
          await fetchCurrentPrice();
        }
        
        // Fetch AI insight
        const aiInsight = await fetchAIInsight('bollinger', {
          current_price: data.current_price || currentPrice,
          signal: data.signal || 'HOLD',
          bb_upper: data.bb_upper,
          bb_middle: data.bb_middle,
          bb_lower: data.bb_lower,
          band_width: data.band_width,
          percent_b: data.percent_b,
          is_squeeze: data.is_squeeze,
          is_expansion: data.is_expansion,
          ...data
        });
        
        setBollingerSignal({
          signal: data.signal || 'HOLD',
          bb_upper: data.bb_upper,
          bb_middle: data.bb_middle,
          bb_lower: data.bb_lower,
          band_width: data.band_width,
          percent_b: data.percent_b,
          is_squeeze: data.is_squeeze || false,
          is_expansion: data.is_expansion || false,
          entry_price: data.entry_price,
          stop_loss: data.stop_loss,
          target_price: data.target_price,
          reason: data.reason || data.message || 'Bollinger Bands signal generated',
          strength: data.strength || 'WEAK',
          confidence: data.confidence || 50,
          ai_insight: aiInsight
        });
        toast.success('Bollinger Bands signal updated');
      } else {
        const errorMsg = response?.error || response?.detail || 'No data available';
        setBollingerSignal(null);
        if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
          toast.error(`Bollinger Bands signal: ${errorMsg}`, { duration: 3000 });
        } else {
          toast.error('Failed to fetch Bollinger Bands signal: ' + errorMsg);
        }
      }
    } catch (error: any) {
      console.error('Bollinger Bands signal error:', error);
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to fetch Bollinger Bands signal';
      setBollingerSignal(null);
      if (errorMsg.includes('No data available') || errorMsg.includes('market is open')) {
        toast.error(`Bollinger Bands signal: ${errorMsg}`, { duration: 3000 });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchAllSignals = async () => {
    setLoading(true);
    try {
      // Fetch current price first - ensure we have it before fetching signals
      await fetchCurrentPrice();
      
      // Small delay to ensure price is set
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Then fetch all signals in parallel
      await Promise.all([
        fetchVWAPSignal(),
        fetchMomentumSignal(),
        fetchBreakoutSignal(),
        fetchMeanReversionSignal(),
        fetchScalpingSignal(),
        fetchGapTradingSignal(),
        fetchClosingRangeSignal(),
        fetchVolumeProfileSignal(),
        fetchNewsSignal(),
        fetchSMASignal(),
        fetchOpeningRangeSignal(),
        fetchMACDSignal(),
        fetchBollingerBandsSignal(),
        fetchComprehensiveSignal()
      ]);
      
      // Refresh next day perception
      await fetchNextDayPerception();
    } catch (error) {
      console.error('Error fetching signals:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    if (signal?.includes('BUY') || signal?.includes('BULLISH')) return 'text-green-400';
    if (signal?.includes('SELL') || signal?.includes('BEARISH')) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getSignalBg = (signal: string) => {
    if (signal?.includes('BUY') || signal?.includes('BULLISH')) return 'bg-green-500/20 border-green-500';
    if (signal?.includes('SELL') || signal?.includes('BEARISH')) return 'bg-red-500/20 border-red-500';
    return 'bg-yellow-500/20 border-yellow-500';
  };

  // Helper function to safely format numbers
  const safeToFixed = (value: number | null | undefined, decimals: number = 2): string => {
    if (value === null || value === undefined || isNaN(value)) {
      return 'N/A';
    }
    return value.toFixed(decimals);
  };

  return (
    <div className="min-h-screen bg-[#131722] text-white p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* All Controls - Moved to Top */}
        <div className="mb-6 bg-[#1a1d28] rounded-lg p-4 border border-gray-700">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[300px]">
              <label className="block text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Select Stock
              </label>
              <StockSelector
                value={selectedSymbol}
                  onChange={async (symbol) => {
                    console.log('StockSelector onChange called with:', symbol);
                    if (symbol && symbol !== selectedSymbol) {
                      setSelectedSymbol(symbol);
                      // Update URL params
                      const newParams = new URLSearchParams(searchParams);
                      newParams.set('symbol', symbol);
                      navigate(`?${newParams.toString()}`, { replace: true });
                      // Reset Next Day Perception when stock changes
                      setNextDayPerception(null);
                      // Reset current price
                      setCurrentPrice(null);
                      // Fetch new data for the selected stock
                      await fetchCurrentPrice();
                      await fetchNextDayPerception();
                    }
                  }}
                showNavigateButton={false}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="bg-[#2a2e39] border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="30m">30 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="1d">1 Day</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Duration
              </label>
                    <select
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      className="bg-[#2a2e39] border border-gray-600 rounded px-3 py-2 text-white"
                    >
                      <option value="1d">1 Day</option>
                      <option value="2d">2 Days</option>
                      <option value="3d">3 Days</option>
                      <option value="4d">4 Days</option>
                      <option value="5d">5 Days</option>
                      <option value="1w">1 Week</option>
                      <option value="1mo">1 Month</option>
                      <option value="3mo">3 Months</option>
                      <option value="6mo">6 Months</option>
                      <option value="1y">1 Year</option>
                    </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                <Gauge className="w-4 h-4" />
                Strategy
              </label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="bg-[#2a2e39] border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="vwap_trading">VWAP Trading</option>
                <option value="momentum">Momentum</option>
                <option value="breakout">Breakout</option>
                <option value="mean_reversion">Mean Reversion</option>
                <option value="scalping">Scalping</option>
                <option value="gap_trading">Gap Trading</option>
                <option value="closing_range">Closing Range</option>
                <option value="volume_profile">Volume Profile</option>
                <option value="news_trading">News Trading</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={fetchAllSignals}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh All
              </button>
              <button
                onClick={() => navigate(`/comprehensive-trading-pro?symbol=${selectedSymbol}&tab=patterns&period=1y`)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium text-sm"
                title="View detailed chart patterns"
              >
                <ExternalLink className="w-4 h-4" />
                View Chart
              </button>
            </div>
          </div>
          
          {/* Advanced Parameters - Collapsible */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-300 flex items-center gap-2">
              <span>⚙️ Advanced Parameters</span>
            </summary>
            <div className="mt-3 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 pt-3 border-t border-gray-700">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Momentum Period</label>
                <input
                  type="number"
                  value={momentumPeriod}
                  onChange={(e) => setMomentumPeriod(Number(e.target.value))}
                  min="5"
                  max="50"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Momentum Threshold</label>
                <input
                  type="number"
                  value={momentumThreshold}
                  onChange={(e) => setMomentumThreshold(Number(e.target.value))}
                  min="0.1"
                  max="2.0"
                  step="0.1"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Breakout Lookback</label>
                <input
                  type="number"
                  value={breakoutLookback}
                  onChange={(e) => setBreakoutLookback(Number(e.target.value))}
                  min="5"
                  max="100"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Breakout Volume Threshold</label>
                <input
                  type="number"
                  value={breakoutVolumeThreshold}
                  onChange={(e) => setBreakoutVolumeThreshold(Number(e.target.value))}
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Mean Reversion Period</label>
                <input
                  type="number"
                  value={meanReversionPeriod}
                  onChange={(e) => setMeanReversionPeriod(Number(e.target.value))}
                  min="5"
                  max="50"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Mean Reversion Std Multiplier</label>
                <input
                  type="number"
                  value={meanReversionStdMultiplier}
                  onChange={(e) => setMeanReversionStdMultiplier(Number(e.target.value))}
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Scalping Tick Size</label>
                <input
                  type="number"
                  value={scalpingTickSize}
                  onChange={(e) => setScalpingTickSize(Number(e.target.value))}
                  min="0.01"
                  max="1.0"
                  step="0.01"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Scalping Min Profit Target</label>
                <input
                  type="number"
                  value={scalpingMinProfitTarget}
                  onChange={(e) => setScalpingMinProfitTarget(Number(e.target.value))}
                  min="0.1"
                  max="5.0"
                  step="0.1"
                  className="w-full bg-[#2a2e39] border border-gray-600 rounded px-2 py-1 text-sm text-white"
                />
              </div>
            </div>
          </details>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('signals')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'signals'
                ? 'bg-blue-600 text-white'
                : 'bg-[#1a1d28] text-gray-400 hover:text-white'
            }`}
          >
            Trading Signals
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'saved'
                ? 'bg-blue-600 text-white'
                : 'bg-[#1a1d28] text-gray-400 hover:text-white'
            }`}
          >
            Saved Strategies
          </button>
          <button
            onClick={() => setActiveTab('paper')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'paper'
                ? 'bg-blue-600 text-white'
                : 'bg-[#1a1d28] text-gray-400 hover:text-white'
            }`}
          >
            Paper Trading
          </button>
        </div>

        {activeTab === 'saved' ? (
          <SavedStrategies
            symbol={selectedSymbol}
            onStrategySelect={(strategy) => {
              setSelectedStrategy(strategy);
              setActiveTab('paper');
            }}
            onStrategyDelete={() => setSelectedStrategy(null)}
          />
        ) : activeTab === 'paper' ? (
          selectedStrategy ? (
            <PaperTrading
              strategy={selectedStrategy}
              symbol={selectedSymbol}
              currentPrice={0}
            />
          ) : (
            <div className="bg-[#1a1d28] rounded-lg p-8 border border-gray-700 text-center">
              <p className="text-gray-400 mb-4">No strategy selected</p>
              <button
                onClick={() => setActiveTab('saved')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
              >
                Select a Strategy
              </button>
            </div>
          )
        ) : (
          <>
            {/* Next Day Perception Overview - Always visible - Moved to TOP */}
            <div className="mb-6 p-6 rounded-xl border-2 border-purple-500/30 bg-gradient-to-r from-purple-900/20 to-blue-900/20 shadow-lg" style={{ zIndex: 10 }}>
              <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Target className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold">Next Day Perception</h2>
                <span className="text-xs text-gray-400">(Based on Current Chart Analysis)</span>
              </div>
              <button
                onClick={fetchNextDayPerception}
                disabled={loading || !selectedSymbol}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 inline mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
            
            {!nextDayPerception ? (
              <div className="text-center py-8">
                <p className="text-gray-400 mb-4">
                  {!selectedSymbol 
                    ? 'Please select a stock to view Next Day Perception'
                    : 'Click "Refresh" to load Next Day Perception analysis'}
                </p>
                {selectedSymbol && (
                  <button
                    onClick={fetchNextDayPerception}
                    disabled={loading}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 inline mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Load Analysis
                  </button>
                )}
              </div>
            ) : (
              <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-[#1a1d28]/50 rounded-lg p-4 border border-gray-700">
                <span className="text-gray-400 text-sm">Trend</span>
                <div className={`text-xl font-bold mt-1 ${
                  nextDayPerception.trend === 'BULLISH' ? 'text-green-400' :
                  nextDayPerception.trend === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {nextDayPerception.trend || 'NEUTRAL'}
                </div>
              </div>
              {nextDayPerception.rsi && (
                <div className="bg-[#1a1d28]/50 rounded-lg p-4 border border-gray-700">
                  <span className="text-gray-400 text-sm">RSI</span>
                  <div className={`text-xl font-bold mt-1 ${
                    nextDayPerception.rsi > 70 ? 'text-red-400' :
                    nextDayPerception.rsi < 30 ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {nextDayPerception.rsi.toFixed(2)}
                  </div>
                </div>
              )}
              <div className="bg-[#1a1d28]/50 rounded-lg p-4 border border-gray-700">
                <span className="text-gray-400 text-sm">Patterns Detected</span>
                <div className="text-xl font-bold mt-1 text-white">
                  {nextDayPerception.patterns || (nextDayPerception.pattern_names?.length || 0)}
                </div>
                {nextDayPerception.pattern_names && Array.isArray(nextDayPerception.pattern_names) && nextDayPerception.pattern_names.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {nextDayPerception.pattern_names.slice(0, 4).map((patternName: string, idx: number) => (
                      <span 
                        key={idx}
                        className="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded border border-purple-500/30 font-medium"
                        title={`Pattern: ${patternName}`}
                      >
                        {patternName}
                      </span>
                    ))}
                    {nextDayPerception.pattern_names.length > 4 && (
                      <span className="text-xs px-2 py-0.5 text-gray-400">
                        +{nextDayPerception.pattern_names.length - 4} more
                      </span>
                    )}
                  </div>
                ) : nextDayPerception.patterns > 0 ? (
                  <div className="mt-2 text-xs text-yellow-400 flex items-center gap-1">
                    <span>⚠️</span>
                    <span>{nextDayPerception.patterns} patterns detected but names not available</span>
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-gray-500">
                    No patterns detected
                  </div>
                )}
              </div>
              <div className="bg-[#1a1d28]/50 rounded-lg p-4 border border-gray-700">
                <span className="text-gray-400 text-sm">Volume Trend</span>
                <div className={`text-xl font-bold mt-1 ${
                  nextDayPerception.volume_trend === 'INCREASING' ? 'text-green-400' :
                  nextDayPerception.volume_trend === 'DECREASING' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {nextDayPerception.volume_trend}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div className="bg-[#1a1d28]/50 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Price Action</h3>
                <p className="text-xs text-gray-500 mb-3">
                  Significance: Pivot + Support/Resistance help define intraday entry, stop-loss and targets. A breakout into resistance without volume is higher trap risk.
                </p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Pivot Point:</span>
                    <span className="font-semibold text-white">
                      {Array.isArray(nextDayPerception.pivot_points) && nextDayPerception.pivot_points.length > 0
                        ? `₹${Number(nextDayPerception.pivot_points[0]).toFixed(2)}`
                        : '—'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Support 1:</span>
                    <span className="font-semibold text-green-400">
                      {Array.isArray(nextDayPerception.support_levels) && nextDayPerception.support_levels.length > 0
                        ? `₹${Number(nextDayPerception.support_levels[0]).toFixed(2)}`
                        : '—'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Resistance 1:</span>
                    <span className="font-semibold text-red-400" title={nextDayPerception.resistance_levels?.length > 0 ? "Calculated resistance level" : "No resistance levels detected"}>
                      {Array.isArray(nextDayPerception.resistance_levels) && nextDayPerception.resistance_levels.length > 0
                        ? `₹${Number(nextDayPerception.resistance_levels[0]).toFixed(2)}`
                        : '—'}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-gray-700">
                    <div className="text-xs text-gray-400 font-semibold mb-1">Key Supports:</div>
                    <div className="text-xs text-gray-300">
                      {Array.isArray(nextDayPerception.support_levels) && nextDayPerception.support_levels.length > 0
                        ? nextDayPerception.support_levels.slice(0, 3).map((v: any) => `₹${Number(v).toFixed(2)}`).join(', ')
                        : '—'}
                    </div>
                    <div className="text-xs text-gray-400 font-semibold mt-2 mb-1">Key Resistances:</div>
                    <div className="text-xs text-gray-300">
                      {Array.isArray(nextDayPerception.resistance_levels) && nextDayPerception.resistance_levels.length > 0
                        ? nextDayPerception.resistance_levels.slice(0, 3).map((v: any) => `₹${Number(v).toFixed(2)}`).join(', ')
                        : '—'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-[#1a1d28]/50 rounded-lg p-4 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Gap Analysis</h3>
                <p className="text-xs text-gray-500 mb-3">
                  Significance: Active gaps act like magnets. In intraday, gaps often fill; avoid chasing breakouts into an unfilled gap without volume confirmation.
                </p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Gaps:</span>
                    <span className="font-semibold text-white">{nextDayPerception.gap_analysis?.total_gaps ?? '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Filled:</span>
                    <span className="font-semibold text-green-400">{nextDayPerception.gap_analysis?.filled ?? '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Active:</span>
                    <span className="font-semibold text-red-400">{nextDayPerception.gap_analysis?.active ?? '—'}</span>
                  </div>

                  {Array.isArray(nextDayPerception.gap_analysis?.active_gaps) && nextDayPerception.gap_analysis.active_gaps.length > 0 && (
                    <div className="pt-2 border-t border-gray-700">
                      <div className="text-xs text-gray-400 font-semibold mb-1">Active Gaps:</div>
                      <div className="space-y-1">
                        {nextDayPerception.gap_analysis.active_gaps.slice(0, 5).map((gap: GapInfo, idx: number) => (
                          <div key={idx} className="text-xs text-gray-300">
                            <span className={`font-semibold ${gap.type === 'UPWARD' ? 'text-green-400' : 'text-red-400'}`}>
                              {gap.type} Gap
                            </span>
                            {`: ₹${Number(gap.start).toFixed(2)} - ₹${Number(gap.end).toFixed(2)} (${Number(gap.size_pct).toFixed(2)}%)`}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* Detected Patterns - Detailed View */}
            {nextDayPerception.pattern_names && Array.isArray(nextDayPerception.pattern_names) && nextDayPerception.pattern_names.length > 0 ? (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                  <span>📊 Detected Chart Patterns:</span>
                  <span className="text-purple-400 font-bold">({nextDayPerception.pattern_names.length})</span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {nextDayPerception.pattern_names.map((patternName: string, idx: number) => {
                    const isHighConfidence = nextDayPerception.high_confidence_patterns?.includes(patternName);
                    const confidenceData = nextDayPerception.pattern_confidence_scores?.find(
                      (p: any) => p.name === patternName
                    );
                    const confidence = confidenceData?.confidence || null;
                    
                    return (
                      <span 
                        key={idx}
                        className={`text-xs px-3 py-1.5 rounded-md border font-medium hover:opacity-80 transition-colors ${
                          isHighConfidence 
                            ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-200 border-green-500/40' 
                            : 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-purple-200 border-purple-500/40'
                        }`}
                        title={`Pattern: ${patternName}${confidence ? ` (${confidence}% confidence)` : ''}`}
                      >
                        {patternName}
                        {confidence && (
                          <span className="ml-1 text-[10px] opacity-75">({confidence}%)</span>
                        )}
                      </span>
                    );
                  })}
                </div>
                {nextDayPerception.high_confidence_patterns && nextDayPerception.high_confidence_patterns.length > 0 && (
                  <p className="mt-3 text-xs text-green-400 flex items-center gap-1">
                    <span>✓</span>
                    <span>{nextDayPerception.high_confidence_patterns.length} high-confidence pattern(s) detected (≥70%)</span>
                  </p>
                )}
              </div>
            ) : nextDayPerception.patterns > 0 ? (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-yellow-500/30">
                <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                  <span>📊 Detected Chart Patterns:</span>
                  <span className="text-yellow-400 font-bold">({nextDayPerception.patterns} detected)</span>
                </h3>
                <div className="flex items-center gap-2 text-xs text-yellow-400">
                  <span>⚠️</span>
                  <span>{nextDayPerception.patterns} pattern(s) detected but pattern names are not available. Check backend logs for details.</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  This usually means patterns were detected but their names couldn't be extracted. Check the browser console for debugging info.
                </p>
              </div>
            ) : (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">📊 Detected Chart Patterns:</h3>
                <p className="text-xs text-gray-500">No patterns detected. Patterns will appear here when detected.</p>
              </div>
            )}
            
            {nextDayPerception.suggestions && nextDayPerception.suggestions.length > 0 && (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Trading Suggestions:</h3>
                <ul className="space-y-1">
                  {nextDayPerception.suggestions.slice(0, 3).map((suggestion: any, idx: number) => {
                    const suggestionText = typeof suggestion === 'string' 
                      ? suggestion 
                      : suggestion?.title || suggestion?.description || suggestion?.message || 'Trading suggestion';
                    return (
                      <li key={idx} className="text-sm text-gray-400 flex items-start gap-2">
                        <span className="text-purple-400 mt-1">•</span>
                        <span>{suggestionText}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Multi-Timeframe Analysis - Always show if perception exists */}
            {nextDayPerception && (
              <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                  <span className="text-blue-400">📊 Multi-Timeframe Analysis</span>
                  {nextDayPerception.multi_timeframe_trend && (
                    <span className={`text-sm px-2 py-1 rounded ${
                      nextDayPerception.multi_timeframe_trend === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                      nextDayPerception.multi_timeframe_trend === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {nextDayPerception.multi_timeframe_trend} ({((nextDayPerception.multi_timeframe_confidence || 0) * 100).toFixed(0)}%)
                    </span>
                  )}
                </h3>
                {nextDayPerception.multi_timeframe_analysis && Object.keys(nextDayPerception.multi_timeframe_analysis).length > 0 ? (
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    {Object.entries(nextDayPerception.multi_timeframe_analysis).map(([tf, data]: [string, any]) => (
                      <div key={tf} className="p-2 bg-[#2a2e39] rounded">
                        <div className="font-semibold text-gray-300">{tf}</div>
                        <div className={`text-xs ${
                          data.trend === 'BULLISH' ? 'text-green-400' :
                          data.trend === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                        }`}>
                          {data.trend}
                        </div>
                        {data.price && (
                          <div className="text-xs text-gray-500 mt-1">₹{data.price.toFixed(2)}</div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">Multi-timeframe data not available. Ensure market is open and data is accessible.</p>
                )}
              </div>
            )}

            {/* GIFT NIFTY Analysis - Show for NIFTY only */}
            {nextDayPerception?.gift_nifty_data && !nextDayPerception.gift_nifty_data.error && (
              <div className="mt-4 p-4 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="text-cyan-400">🌍 GIFT NIFTY Analysis</span>
                  <span className="text-xs text-gray-400">(Next Day Opening Indicator)</span>
                  {nextDayPerception.gift_nifty_sentiment && (
                    <span className={`text-sm px-2 py-1 rounded ${
                      nextDayPerception.gift_nifty_sentiment === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                      nextDayPerception.gift_nifty_sentiment === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {nextDayPerception.gift_nifty_sentiment}
                    </span>
                  )}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  {nextDayPerception.gift_nifty_data.price && (
                    <div>
                      <span className="text-gray-400">Price:</span>
                      <div className="font-bold text-white">₹{nextDayPerception.gift_nifty_data.price.toFixed(2)}</div>
                    </div>
                  )}
                  {nextDayPerception.gift_nifty_data.change_pct !== undefined && (
                    <div>
                      <span className="text-gray-400">Change:</span>
                      <div className={`font-bold ${
                        nextDayPerception.gift_nifty_data.change_pct > 0 ? 'text-green-400' :
                        nextDayPerception.gift_nifty_data.change_pct < 0 ? 'text-red-400' : 'text-gray-400'
                      }`}>
                        {nextDayPerception.gift_nifty_data.change_pct > 0 ? '+' : ''}{nextDayPerception.gift_nifty_data.change_pct.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {nextDayPerception.gift_nifty_data.premium_discount_pct !== undefined && (
                    <div>
                      <span className="text-gray-400">Premium/Discount:</span>
                      <div className={`font-bold ${
                        nextDayPerception.gift_nifty_data.premium_discount_pct > 0 ? 'text-green-400' :
                        nextDayPerception.gift_nifty_data.premium_discount_pct < 0 ? 'text-red-400' : 'text-gray-400'
                      }`}>
                        {nextDayPerception.gift_nifty_data.premium_discount_pct > 0 ? '+' : ''}{nextDayPerception.gift_nifty_data.premium_discount_pct.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {nextDayPerception.gift_nifty_data.sentiment && (
                    <div>
                      <span className="text-gray-400">Sentiment:</span>
                      <div className={`font-bold ${
                        nextDayPerception.gift_nifty_data.sentiment === 'BULLISH' ? 'text-green-400' :
                        nextDayPerception.gift_nifty_data.sentiment === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                        {nextDayPerception.gift_nifty_data.sentiment}
                      </div>
                    </div>
                  )}
                </div>
                {nextDayPerception.gift_nifty_data.note && (
                  <p className="mt-3 text-xs text-gray-400 italic">{nextDayPerception.gift_nifty_data.note}</p>
                )}
              </div>
            )}

            {/* India VIX Analysis - Show for all symbols (volatility indicator) */}
            {nextDayPerception?.india_vix_data && !nextDayPerception.india_vix_data.error && (
              <div className="mt-4 p-4 bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="text-orange-400">📊 India VIX</span>
                  <span className="text-xs text-gray-400">(Volatility Index)</span>
                  {nextDayPerception.india_vix_sentiment && (
                    <span className={`text-sm px-2 py-1 rounded ${
                      nextDayPerception.india_vix_sentiment === 'CALM' ? 'bg-green-500/20 text-green-400' :
                      nextDayPerception.india_vix_sentiment === 'FEARFUL' || nextDayPerception.india_vix_sentiment === 'PANIC' ? 'bg-red-500/20 text-red-400' :
                      nextDayPerception.india_vix_sentiment === 'CAUTIOUS' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {nextDayPerception.india_vix_sentiment}
                    </span>
                  )}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
                  {nextDayPerception.india_vix_data.level !== undefined && (
                    <div>
                      <span className="text-gray-400">VIX Level:</span>
                      <div className={`font-bold text-lg ${
                        nextDayPerception.india_vix_data.level < 15 ? 'text-green-400' :
                        nextDayPerception.india_vix_data.level < 20 ? 'text-yellow-400' :
                        nextDayPerception.india_vix_data.level < 25 ? 'text-orange-400' :
                        nextDayPerception.india_vix_data.level < 30 ? 'text-red-400' : 'text-red-600'
                      }`}>
                        {nextDayPerception.india_vix_data.level.toFixed(2)}
                      </div>
                    </div>
                  )}
                  {nextDayPerception.india_vix_data.change_pct !== undefined && (
                    <div>
                      <span className="text-gray-400">Change:</span>
                      <div className={`font-bold ${
                        nextDayPerception.india_vix_data.change_pct > 0 ? 'text-red-400' :
                        nextDayPerception.india_vix_data.change_pct < 0 ? 'text-green-400' : 'text-gray-400'
                      }`}>
                        {nextDayPerception.india_vix_data.change_pct > 0 ? '+' : ''}{nextDayPerception.india_vix_data.change_pct.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {nextDayPerception.india_vix_data.regime && (
                    <div>
                      <span className="text-gray-400">Regime:</span>
                      <div className={`font-bold ${
                        nextDayPerception.india_vix_data.regime === 'LOW' ? 'text-green-400' :
                        nextDayPerception.india_vix_data.regime === 'NORMAL' ? 'text-yellow-400' :
                        nextDayPerception.india_vix_data.regime === 'ELEVATED' ? 'text-orange-400' :
                        nextDayPerception.india_vix_data.regime === 'HIGH' ? 'text-red-400' : 'text-red-600'
                      }`}>
                        {nextDayPerception.india_vix_data.regime}
                      </div>
                    </div>
                  )}
                  {nextDayPerception.india_vix_data.confidence_adjustment !== undefined && (
                    <div>
                      <span className="text-gray-400">Confidence Impact:</span>
                      <div className={`font-bold ${
                        nextDayPerception.india_vix_data.confidence_adjustment > 0 ? 'text-green-400' :
                        nextDayPerception.india_vix_data.confidence_adjustment < 0 ? 'text-red-400' : 'text-gray-400'
                      }`}>
                        {nextDayPerception.india_vix_data.confidence_adjustment > 0 ? '+' : ''}{(nextDayPerception.india_vix_data.confidence_adjustment * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>
                {nextDayPerception.india_vix_data.interpretation && (
                  <div className="mt-3 p-3 bg-black/20 rounded-lg">
                    <p className="text-sm text-gray-300 mb-1">
                      <span className="font-semibold text-orange-400">Interpretation:</span> {nextDayPerception.india_vix_data.interpretation}
                    </p>
                    {nextDayPerception.india_vix_data.change_interpretation && (
                      <p className="text-xs text-gray-400 mt-1 italic">
                        {nextDayPerception.india_vix_data.change_interpretation}
                      </p>
                    )}
                  </div>
                )}
                {nextDayPerception.india_vix_data.note && (
                  <p className="mt-2 text-xs text-gray-400 italic">{nextDayPerception.india_vix_data.note}</p>
                )}
              </div>
            )}

            {/* Note: Tomorrow's NIFTY Opening Analysis has been moved to a dedicated page */}
            {/* Visit /tomorrow-nifty-opening for comprehensive analysis */}

            {/* ML Prediction - Always show if perception exists */}
            {nextDayPerception && (
              <div className="mt-4 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                  <span className="text-purple-400">🤖 ML Prediction</span>
                  {nextDayPerception.ml_prediction && (
                    <span className={`text-sm px-2 py-1 rounded ${
                      nextDayPerception.ml_prediction === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                      nextDayPerception.ml_prediction === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {nextDayPerception.ml_prediction} ({((nextDayPerception.ml_confidence || 0) * 100).toFixed(0)}% confidence)
                    </span>
                  )}
                </h3>
                <p className="text-sm text-gray-400">
                  Based on ensemble of technical indicators, patterns, and multi-timeframe analysis
                </p>
                {nextDayPerception.ml_prediction ? (
                  nextDayPerception.ml_confidence === 0 ? (
                    <p className="text-xs text-yellow-400 mt-2">
                      ⚠️ Low confidence - insufficient signal strength. Consider waiting for clearer patterns.
                    </p>
                  ) : null
                ) : (
                  <p className="text-sm text-gray-400 mt-2">ML prediction data not available yet.</p>
                )}
              </div>
            )}

            {/* Pattern Success Rates - Always show if perception exists */}
            {nextDayPerception && (
              <div className="mt-4 p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 text-indigo-400">📈 Historical Pattern Success Rates</h3>
                {nextDayPerception.pattern_success_rates && Object.keys(nextDayPerception.pattern_success_rates).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(nextDayPerception.pattern_success_rates).slice(0, 5).map(([patternName, data]: [string, any]) => (
                      <div key={patternName} className="flex items-center justify-between text-sm">
                        <span className="text-gray-300">{patternName}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-700 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                (data.success_rate || 0) >= 0.7 ? 'bg-green-500' :
                                (data.success_rate || 0) >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${(data.success_rate || 0) * 100}%` }}
                            />
                          </div>
                          <span className="text-gray-400 w-16 text-right">
                            {((data.success_rate || 0) * 100).toFixed(0)}%
                          </span>
                          {data.sample_size > 0 && (
                            <span className="text-xs text-gray-500">({data.sample_size})</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">No historical pattern data available yet. Patterns will be tracked over time.</p>
                )}
              </div>
            )}

            {/* Divergence Alerts */}
            {(nextDayPerception.has_bullish_divergence || nextDayPerception.has_bearish_divergence) && (
              <div className="mt-4 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 text-cyan-400">⚠️ Divergence Detected</h3>
                <div className="space-y-2">
                  {nextDayPerception.has_bullish_divergence && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-green-400 font-semibold">🔼 Bullish Divergence</span>
                      <span className="text-gray-400">
                        ({nextDayPerception.bullish_divergence_count || 0} signal{nextDayPerception.bullish_divergence_count !== 1 ? 's' : ''})
                      </span>
                    </div>
                  )}
                  {nextDayPerception.has_bearish_divergence && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-red-400 font-semibold">🔽 Bearish Divergence</span>
                      <span className="text-gray-400">
                        ({nextDayPerception.bearish_divergence_count || 0} signal{nextDayPerception.bearish_divergence_count !== 1 ? 's' : ''})
                      </span>
                    </div>
                  )}
                  <p className="text-xs text-gray-400 mt-2">
                    Divergence suggests potential trend reversal. Monitor price action closely.
                  </p>
                </div>
              </div>
            )}

            {/* Options Flow Analysis - Always show if perception exists */}
            {nextDayPerception && (
              <div className="mt-4 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                  <span className="text-orange-400">📊 Options Flow Analysis</span>
                  {nextDayPerception.options_sentiment && (
                    <span className={`text-sm px-2 py-1 rounded ${
                      nextDayPerception.options_sentiment === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                      nextDayPerception.options_sentiment === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {nextDayPerception.options_sentiment}
                    </span>
                  )}
                </h3>
                {nextDayPerception.options_flow_analysis ? (
                  <p className="text-sm text-gray-400">
                    {nextDayPerception.options_flow_analysis.is_fno_stock 
                      ? (nextDayPerception.options_flow_analysis.note || 'FNO stock detected - options flow analysis available')
                      : 'Stock not in FNO list - options flow analysis not applicable'}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400">Options flow analysis not available for this stock.</p>
                )}
              </div>
            )}

            {/* Support/Resistance Levels - Always show if data exists */}
            {(nextDayPerception.nearest_support || nextDayPerception.nearest_resistance || 
              (nextDayPerception.support_levels?.length > 0) || (nextDayPerception.resistance_levels?.length > 0)) && (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">
                  Key Levels for {selectedSymbol}:
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {nextDayPerception.nearest_resistance ? (
                    <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/30">
                      <span className="text-gray-400 text-xs">Nearest Resistance</span>
                      <div className="text-lg font-bold mt-1 text-red-400">
                        ₹{typeof nextDayPerception.nearest_resistance === 'number' ? nextDayPerception.nearest_resistance.toFixed(2) : 'N/A'}
                      </div>
                      {nextDayPerception.resistance_distance_pct && typeof nextDayPerception.resistance_distance_pct === 'number' && (
                        <div className="text-xs text-gray-500 mt-1">
                          {nextDayPerception.resistance_distance_pct.toFixed(2)}% above current price
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-gray-500/10 rounded-lg p-3 border border-gray-500/30">
                      <span className="text-gray-400 text-xs">Nearest Resistance</span>
                      <div className="text-lg font-bold mt-1 text-gray-400">N/A</div>
                    </div>
                  )}
                  {nextDayPerception.nearest_support ? (
                    <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/30">
                      <span className="text-gray-400 text-xs">Nearest Support</span>
                      <div className="text-lg font-bold mt-1 text-green-400">
                        ₹{typeof nextDayPerception.nearest_support === 'number' ? nextDayPerception.nearest_support.toFixed(2) : 'N/A'}
                      </div>
                      {nextDayPerception.support_distance_pct && typeof nextDayPerception.support_distance_pct === 'number' && (
                        <div className="text-xs text-gray-500 mt-1">
                          {nextDayPerception.support_distance_pct.toFixed(2)}% below current price
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-gray-500/10 rounded-lg p-3 border border-gray-500/30">
                      <span className="text-gray-400 text-xs">Nearest Support</span>
                      <div className="text-lg font-bold mt-1 text-gray-400">N/A</div>
                    </div>
                  )}
                </div>
                {(nextDayPerception.support_levels?.length > 0 || nextDayPerception.resistance_levels?.length > 0) && (
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    {nextDayPerception.resistance_levels?.length > 0 && (
                      <div>
                        <span className="text-gray-400">Resistance Levels:</span>
                        <div className="mt-1 space-y-1">
                          {nextDayPerception.resistance_levels.slice(0, 3).map((level: number, idx: number) => (
                            <div key={idx} className="text-red-300">₹{level.toFixed(2)}</div>
                          ))}
                        </div>
                      </div>
                    )}
                    {nextDayPerception.support_levels?.length > 0 && (
                      <div>
                        <span className="text-gray-400">Support Levels:</span>
                        <div className="mt-1 space-y-1">
                          {nextDayPerception.support_levels.slice(0, 3).map((level: number, idx: number) => (
                            <div key={idx} className="text-green-300">₹{level.toFixed(2)}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Divergence Signals */}
            {(nextDayPerception.has_bullish_divergence || nextDayPerception.has_bearish_divergence) && (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Divergence Detected:</h3>
                <div className="flex flex-wrap gap-2">
                  {nextDayPerception.has_bullish_divergence && (
                    <span className="px-3 py-1.5 bg-green-500/20 text-green-300 rounded-md border border-green-500/40 text-xs font-medium">
                      🟢 Bullish Divergence
                    </span>
                  )}
                  {nextDayPerception.has_bearish_divergence && (
                    <span className="px-3 py-1.5 bg-red-500/20 text-red-300 rounded-md border border-red-500/40 text-xs font-medium">
                      🔴 Bearish Divergence
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {nextDayPerception.has_bullish_divergence && "Price making lower lows while indicator making higher lows - potential reversal up"}
                  {nextDayPerception.has_bearish_divergence && "Price making higher highs while indicator making lower highs - potential reversal down"}
                </p>
              </div>
            )}

            {/* Pattern Confidence Scores */}
            {nextDayPerception.pattern_confidence_scores && nextDayPerception.pattern_confidence_scores.length > 0 && (
              <div className="mt-4 p-4 bg-[#1a1d28]/50 rounded-lg border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Pattern Confidence:</h3>
                <div className="space-y-1">
                  {nextDayPerception.pattern_confidence_scores.slice(0, 5).map((pattern: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between text-xs">
                      <span className="text-gray-400">{pattern.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-gray-700 rounded-full h-1.5">
                          <div 
                            className={`h-1.5 rounded-full ${
                              pattern.confidence >= 70 ? 'bg-green-500' : 
                              pattern.confidence >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${pattern.confidence}%` }}
                          />
                        </div>
                        <span className={`font-medium ${
                          pattern.confidence >= 70 ? 'text-green-400' : 
                          pattern.confidence >= 50 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {pattern.confidence}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {nextDayPerception.price_vs_sma20 !== null && nextDayPerception.price_vs_sma50 !== null && (
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-[#1a1d28]/50 rounded-lg p-3 border border-gray-700">
                  <span className="text-gray-400 text-xs">Price vs SMA 20</span>
                  <div className={`text-lg font-bold mt-1 ${
                    nextDayPerception.price_vs_sma20 > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {nextDayPerception.price_vs_sma20 > 0 ? '+' : ''}{nextDayPerception.price_vs_sma20.toFixed(2)}%
                  </div>
                </div>
                <div className="bg-[#1a1d28]/50 rounded-lg p-3 border border-gray-700">
                  <span className="text-gray-400 text-xs">Price vs SMA 50</span>
                  <div className={`text-lg font-bold mt-1 ${
                    nextDayPerception.price_vs_sma50 > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {nextDayPerception.price_vs_sma50 > 0 ? '+' : ''}{nextDayPerception.price_vs_sma50.toFixed(2)}%
                  </div>
                </div>
              </div>
            )}
              </>
            )}
            </div>

            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Clock className="w-8 h-8 text-green-400" />
                Intraday Trading Dashboard
              </h1>
              <p className="text-gray-400 mt-2">Real-time intraday signals and strategies</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-2 bg-[#1a1d28] rounded-lg border border-gray-700">
                <Activity className="w-4 h-4 text-blue-400" />
                <span className="text-sm">{tradingSession || 'Loading...'}</span>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Auto Refresh</span>
              </label>
              {autoRefresh && (
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className="bg-[#1a1d28] border border-gray-600 rounded px-3 py-1 text-sm"
                >
                  <option value={10}>10s</option>
                  <option value={30}>30s</option>
                  <option value={60}>60s</option>
                </select>
              )}
            </div>
          </div>

        {/* Info Banner for Data Availability */}
        {(!vwapSignal && !momentumSignal && !breakoutSignal && !meanReversionSignal && !scalpingSignal && !smaSignal && !openingRangeSignal && !macdSignal && !bollingerSignal && !comprehensiveSignal && !loading) && (
          <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-yellow-400 font-semibold mb-1">Intraday Data Not Available</h3>
                <p className="text-gray-300 text-sm">
                  Intraday data for {selectedSymbol} may not be available. This could be because:
                </p>
                <ul className="text-gray-400 text-xs mt-2 list-disc list-inside space-y-1">
                  <li>The market is currently closed</li>
                  <li>yfinance has limitations for Indian stock intraday data</li>
                  <li>Upstox API may need to be configured for real-time intraday data</li>
                </ul>
                <p className="text-gray-300 text-sm mt-2">
                  <strong>Tip:</strong> Try using daily timeframe or ensure Upstox API is configured for intraday data.
                </p>
              </div>
            </div>
          </div>
        )}
            </div>

        {/* Comprehensive Signal - Prominent */}
        {comprehensiveSignal && (
          <div className={`mb-6 p-6 rounded-xl border-2 ${getSignalBg(comprehensiveSignal.signal)}`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Zap className="w-6 h-6 text-yellow-400" />
                <h2 className="text-2xl font-bold">Comprehensive Signal</h2>
              </div>
              <span className={`text-lg font-bold ${getSignalColor(comprehensiveSignal.signal)}`}>
                {comprehensiveSignal.signal}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {currentPrice && (
                <div className="border-b md:border-b-0 md:border-r border-gray-600 pb-4 md:pb-0 md:pr-4">
                  <span className="text-gray-400 text-sm">Current Price</span>
                  <div className="text-2xl font-bold text-white">₹{currentPrice.toFixed(2)}</div>
                </div>
              )}
              {comprehensiveSignal.entry_price && (
                <div>
                  <span className="text-gray-400 text-sm">Entry Price</span>
                  <div className="text-xl font-bold">₹{comprehensiveSignal.entry_price.toFixed(2)}</div>
                </div>
              )}
              {comprehensiveSignal.stop_loss && (
                <div>
                  <span className="text-gray-400 text-sm">Stop Loss</span>
                  <div className="text-xl font-bold text-red-400">₹{comprehensiveSignal.stop_loss.toFixed(2)}</div>
                </div>
              )}
              {comprehensiveSignal.target_price && (
                <div>
                  <span className="text-gray-400 text-sm">Target Price</span>
                  <div className="text-xl font-bold text-green-400">₹{comprehensiveSignal.target_price.toFixed(2)}</div>
                </div>
              )}
              <div>
                <span className="text-gray-400 text-sm">Confidence</span>
                <div className="text-xl font-bold">{(comprehensiveSignal.confidence * 100).toFixed(0)}%</div>
              </div>
            </div>
            <p className="mt-4 text-gray-300">
              {typeof comprehensiveSignal.message === 'string' 
                ? comprehensiveSignal.message 
                : (comprehensiveSignal.message as any)?.text || (comprehensiveSignal.message as any)?.message || 'Signal generated'}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {/* VWAP Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                VWAP Trading
              </h2>
              <button
                onClick={fetchVWAPSignal}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {!vwapSignal && !loading && (
              <div className="p-4 rounded-lg border border-gray-600 bg-gray-800/50">
                <p className="text-gray-400 text-sm text-center">
                  Click "Refresh" to fetch VWAP signal
                </p>
                <p className="text-gray-500 text-xs text-center mt-2">
                  {selectedSymbol} - {timeframe}
                </p>
              </div>
            )}
            {vwapSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(vwapSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-bold text-lg">Signal: {vwapSignal.signal}</span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-400">VWAP:</span>
                    <span className="font-semibold">₹{vwapSignal.vwap.toFixed(2)}</span>
                  </div>
                  {vwapSignal.upper_band && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Upper Band:</span>
                      <span className="font-semibold text-green-400">₹{vwapSignal.upper_band.toFixed(2)}</span>
                    </div>
                  )}
                  {vwapSignal.lower_band && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Lower Band:</span>
                      <span className="font-semibold text-red-400">₹{vwapSignal.lower_band.toFixed(2)}</span>
                    </div>
                  )}
                  {vwapSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{vwapSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {vwapSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{vwapSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {vwapSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{vwapSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                  {vwapSignal.risk_reward && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Risk:Reward:</span>
                      <span className="font-semibold text-yellow-400">1:{vwapSignal.risk_reward}</span>
                    </div>
                  )}
                </div>
                {vwapSignal.ai_insight && (
                  <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-blue-300 font-semibold mb-1">AI Insight</p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {typeof vwapSignal.ai_insight === 'string' 
                            ? vwapSignal.ai_insight 
                            : (vwapSignal.ai_insight as any)?.text || (vwapSignal.ai_insight as any)?.message || (vwapSignal.ai_insight as any)?.insight || 'AI analysis available'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Momentum Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Gauge className="w-5 h-5 text-purple-400" />
                Momentum Trading
              </h2>
              <button
                onClick={fetchMomentumSignal}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !momentumSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading Momentum signal...
              </div>
            )}
            {!loading && !momentumSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch Momentum signal
              </div>
            )}
            {momentumSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(momentumSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(momentumSignal.signal)}`}>
                    Signal: {momentumSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {momentumSignal.rsi !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">RSI:</span>
                      <span className={`font-semibold ${
                        momentumSignal.rsi < 30 ? 'text-green-400' : 
                        momentumSignal.rsi > 70 ? 'text-red-400' : 
                        'text-yellow-400'
                      }`}>
                        {momentumSignal.rsi.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {momentumSignal.roc !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">ROC:</span>
                      <span className={`font-semibold ${momentumSignal.roc >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {momentumSignal.roc >= 0 ? '+' : ''}{momentumSignal.roc.toFixed(2)}%
                      </span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof momentumSignal.message === 'string' 
                    ? momentumSignal.message 
                    : (momentumSignal.message as any)?.text || (momentumSignal.message as any)?.message || 'Momentum signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* Breakout Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <ArrowUpDown className="w-5 h-5 text-orange-400" />
                Breakout Trading
              </h2>
              <button
                onClick={fetchBreakoutSignal}
                disabled={loading}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !breakoutSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading Breakout signal...
              </div>
            )}
            {!loading && !breakoutSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch Breakout signal
              </div>
            )}
            {breakoutSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(breakoutSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(breakoutSignal.signal)}`}>
                    Signal: {breakoutSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {breakoutSignal.resistance && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Resistance:</span>
                      <span className="font-semibold text-red-400">₹{breakoutSignal.resistance.toFixed(2)}</span>
                    </div>
                  )}
                  {breakoutSignal.double_top_resistance !== undefined && breakoutSignal.double_top_resistance !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 flex items-center gap-1">
                        <span>Double Top Resistance:</span>
                        {breakoutSignal.near_double_top && (
                          <span className="px-1.5 py-0.5 rounded text-xs bg-red-600 text-white font-bold">
                            NEAR
                          </span>
                        )}
                      </span>
                      <span className="font-semibold text-red-500 flex items-center gap-1">
                        ₹{breakoutSignal.double_top_resistance.toFixed(2)}
                        <span className="text-xs">🔴</span>
                      </span>
                    </div>
                  )}
                  {breakoutSignal.support && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Support:</span>
                      <span className="font-semibold text-green-400">₹{breakoutSignal.support.toFixed(2)}</span>
                    </div>
                  )}
                  {breakoutSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{breakoutSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {breakoutSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{breakoutSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {breakoutSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{breakoutSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                  {breakoutSignal.breakout_strength && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Breakout:</span>
                      <span className="font-semibold text-orange-400">{breakoutSignal.breakout_strength}</span>
                    </div>
                  )}
                  {breakoutSignal.volume_confirmation !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Volume:</span>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            breakoutSignal.volume_confirmation
                              ? 'bg-green-600 text-white'
                              : 'bg-yellow-600 text-black'
                          }`}
                        >
                          {breakoutSignal.volume_confirmation ? 'CONFIRMED' : 'FAKE-OUT RISK'}
                        </span>
                        {breakoutSignal.rvol !== undefined && breakoutSignal.rvol !== null && (
                          <span className="text-gray-300 text-xs">
                            RVOL: {Number(breakoutSignal.rvol).toFixed(2)}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  {breakoutSignal.fakeout_risk && (
                    <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                      <span className="text-xs text-yellow-200 font-semibold">
                        Action: Wait for retest / confirmation candle
                      </span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof breakoutSignal.message === 'string' 
                    ? breakoutSignal.message 
                    : (breakoutSignal.message as any)?.text || (breakoutSignal.message as any)?.message || 'Breakout signal generated'}
                </p>
                {breakoutSignal.double_top_resistance !== undefined && breakoutSignal.double_top_resistance !== null && (
                  <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-red-400">⚠️ DOUBLE TOP DETECTED</span>
                      <span className="text-xs text-gray-400">
                        Resistance at ₹{breakoutSignal.double_top_resistance.toFixed(2)}
                        {breakoutSignal.near_double_top && ' - Price is near this level'}
                      </span>
                    </div>
                  </div>
                )}
                {breakoutSignal.ai_insight && (
                  <div className="mt-3 p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-orange-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-orange-300 font-semibold mb-1">AI Insight</p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {typeof breakoutSignal.ai_insight === 'string' 
                            ? breakoutSignal.ai_insight 
                            : (breakoutSignal.ai_insight as any)?.text || (breakoutSignal.ai_insight as any)?.message || (breakoutSignal.ai_insight as any)?.insight || 'AI analysis available'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mean Reversion Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-cyan-400" />
                Mean Reversion
              </h2>
              <button
                onClick={fetchMeanReversionSignal}
                disabled={loading}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !meanReversionSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading Mean Reversion signal...
              </div>
            )}
            {!loading && !meanReversionSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch Mean Reversion signal
              </div>
            )}
            {meanReversionSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(meanReversionSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(meanReversionSignal.signal)}`}>
                    Signal: {meanReversionSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {meanReversionSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{meanReversionSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {meanReversionSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{meanReversionSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {meanReversionSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{meanReversionSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof meanReversionSignal.message === 'string' 
                    ? meanReversionSignal.message 
                    : (meanReversionSignal.message as any)?.text || (meanReversionSignal.message as any)?.message || 'Mean reversion signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* Scalping Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-400" />
                Scalping
              </h2>
              <button
                onClick={fetchScalpingSignal}
                disabled={loading}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !scalpingSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading Scalping signal...
              </div>
            )}
            {!loading && !scalpingSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch Scalping signal
              </div>
            )}
            {scalpingSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(scalpingSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(scalpingSignal.signal)}`}>
                    Signal: {scalpingSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {scalpingSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{scalpingSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {scalpingSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{scalpingSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {scalpingSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{scalpingSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                  {scalpingSignal.scalping_opportunity && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Opportunity:</span>
                      <span className="font-semibold text-yellow-400">{scalpingSignal.scalping_opportunity}</span>
                    </div>
                  )}
                  {scalpingSignal.quick_profit_potential !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Profit Potential:</span>
                      <span className="font-semibold text-yellow-400">{scalpingSignal.quick_profit_potential.toFixed(2)}%</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof scalpingSignal.message === 'string' 
                    ? scalpingSignal.message 
                    : (scalpingSignal.message as any)?.text || (scalpingSignal.message as any)?.message || 'Scalping signal generated'}
                </p>
                {scalpingSignal.ai_insight && (
                  <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-yellow-300 font-semibold mb-1">AI Insight</p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {typeof scalpingSignal.ai_insight === 'string' 
                            ? scalpingSignal.ai_insight 
                            : (scalpingSignal.ai_insight as any)?.text || (scalpingSignal.ai_insight as any)?.message || (scalpingSignal.ai_insight as any)?.insight || 'AI analysis available'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Gap Trading Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                Gap Trading
              </h2>
              <button
                onClick={fetchGapTradingSignal}
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {gapTradingSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(gapTradingSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(gapTradingSignal.signal)}`}>
                    Signal: {gapTradingSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {gapTradingSignal.gap_type && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gap Type:</span>
                      <span className="font-semibold">{gapTradingSignal.gap_type}</span>
                    </div>
                  )}
                  {gapTradingSignal.gap_pct !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Gap %:</span>
                      <span className={`font-semibold ${gapTradingSignal.gap_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {gapTradingSignal.gap_pct >= 0 ? '+' : ''}{gapTradingSignal.gap_pct.toFixed(2)}%
                      </span>
                    </div>
                  )}
                  {gapTradingSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{gapTradingSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {gapTradingSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{gapTradingSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {gapTradingSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{gapTradingSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof gapTradingSignal.message === 'string' 
                    ? gapTradingSignal.message 
                    : (gapTradingSignal.message as any)?.text || (gapTradingSignal.message as any)?.message || 'Gap trading signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* Closing Range Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Clock className="w-5 h-5 text-teal-400" />
                Closing Range
              </h2>
              <button
                onClick={fetchClosingRangeSignal}
                disabled={loading}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {closingRangeSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(closingRangeSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(closingRangeSignal.signal)}`}>
                    Signal: {closingRangeSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {closingRangeSignal.closing_high && closingRangeSignal.closing_low && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Range:</span>
                      <span className="font-semibold">₹{closingRangeSignal.closing_low.toFixed(2)} - ₹{closingRangeSignal.closing_high.toFixed(2)}</span>
                    </div>
                  )}
                  {closingRangeSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{closingRangeSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {closingRangeSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{closingRangeSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {closingRangeSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{closingRangeSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof closingRangeSignal.message === 'string' 
                    ? closingRangeSignal.message 
                    : (closingRangeSignal.message as any)?.text || (closingRangeSignal.message as any)?.message || 'Closing range signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* Volume Profile Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-cyan-400" />
                Volume Profile
              </h2>
              <button
                onClick={fetchVolumeProfileSignal}
                disabled={loading}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {volumeProfileSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(volumeProfileSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(volumeProfileSignal.signal)}`}>
                    Signal: {volumeProfileSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {volumeProfileSignal.poc_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">POC Price:</span>
                      <span className="font-semibold">₹{volumeProfileSignal.poc_price.toFixed(2)}</span>
                    </div>
                  )}
                  {volumeProfileSignal.value_area_high && volumeProfileSignal.value_area_low && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Value Area:</span>
                      <span className="font-semibold">₹{volumeProfileSignal.value_area_low.toFixed(2)} - ₹{volumeProfileSignal.value_area_high.toFixed(2)}</span>
                    </div>
                  )}
                  {volumeProfileSignal.entry_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{volumeProfileSignal.entry_price.toFixed(2)}</span>
                    </div>
                  )}
                  {volumeProfileSignal.stop_loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{volumeProfileSignal.stop_loss.toFixed(2)}</span>
                    </div>
                  )}
                  {volumeProfileSignal.target_price && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{volumeProfileSignal.target_price.toFixed(2)}</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof volumeProfileSignal.message === 'string' 
                    ? volumeProfileSignal.message 
                    : (volumeProfileSignal.message as any)?.text || (volumeProfileSignal.message as any)?.message || 'Volume profile signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* News Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Activity className="w-5 h-5 text-pink-400" />
                News Trading
              </h2>
              <button
                onClick={fetchNewsSignal}
                disabled={loading}
                className="px-4 py-2 bg-pink-600 hover:bg-pink-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {newsSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(newsSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(newsSignal.signal)}`}>
                    Signal: {newsSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {newsSignal.sentiment_score !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Sentiment:</span>
                      <span className={`font-semibold ${newsSignal.sentiment_score > 0 ? 'text-green-400' : newsSignal.sentiment_score < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                        {newsSignal.sentiment_score >= 0 ? '+' : ''}{newsSignal.sentiment_score.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {newsSignal.news_count !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">News Count:</span>
                      <span className="font-semibold">{newsSignal.news_count}</span>
                    </div>
                  )}
                  {newsSignal.high_impact_count !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">High Impact:</span>
                      <span className="font-semibold text-yellow-400">{newsSignal.high_impact_count}</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof newsSignal.message === 'string' 
                    ? newsSignal.message 
                    : (newsSignal.message as any)?.text || (newsSignal.message as any)?.message || 'News signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* SMA Trading Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-400" />
                SMA Trading
              </h2>
              <button
                onClick={fetchSMASignal}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !smaSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading SMA signal...
              </div>
            )}
            {!loading && !smaSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch SMA signal
              </div>
            )}
            {smaSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(smaSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(smaSignal.signal)}`}>
                    Signal: {smaSignal.signal}
                  </span>
                  {smaSignal.strength && (
                    <span className={`text-xs px-2 py-1 rounded ${
                      smaSignal.strength === 'STRONG' ? 'bg-green-500/20 text-green-400' :
                      smaSignal.strength === 'MODERATE' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {smaSignal.strength}
                    </span>
                  )}
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{currentPrice.toFixed(2)}</span>
                    </div>
                  )}
                  {smaSignal.sma20 !== undefined && smaSignal.sma20 !== null && !isNaN(smaSignal.sma20) && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">SMA20:</span>
                      <span className="font-semibold">₹{safeToFixed(smaSignal.sma20)}</span>
                    </div>
                  )}
                  {smaSignal.price_vs_sma20 !== undefined && smaSignal.price_vs_sma20 !== null && !isNaN(smaSignal.price_vs_sma20) && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Price vs SMA20:</span>
                      <span className={`font-semibold ${
                        smaSignal.price_vs_sma20 > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {smaSignal.price_vs_sma20 > 0 ? '+' : ''}{safeToFixed(smaSignal.price_vs_sma20)}%
                      </span>
                    </div>
                  )}
                  {smaSignal.sma50 !== undefined && smaSignal.sma50 !== null && !isNaN(smaSignal.sma50) && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">SMA50:</span>
                      <span className="font-semibold">₹{safeToFixed(smaSignal.sma50)}</span>
                    </div>
                  )}
                  {smaSignal.price_vs_sma50 !== undefined && smaSignal.price_vs_sma50 !== null && !isNaN(smaSignal.price_vs_sma50) && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Price vs SMA50:</span>
                      <span className={`font-semibold ${
                        smaSignal.price_vs_sma50 > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {smaSignal.price_vs_sma50 > 0 ? '+' : ''}{safeToFixed(smaSignal.price_vs_sma50)}%
                      </span>
                    </div>
                  )}
                  {smaSignal.sma200 !== undefined && smaSignal.sma200 !== null && !isNaN(smaSignal.sma200) && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">SMA200:</span>
                      <span className="font-semibold">₹{safeToFixed(smaSignal.sma200)}</span>
                    </div>
                  )}
                  {smaSignal.price_vs_sma200 !== undefined && smaSignal.price_vs_sma200 !== null && !isNaN(smaSignal.price_vs_sma200) && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Price vs SMA200:</span>
                      <span className={`font-semibold ${
                        smaSignal.price_vs_sma200 > 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {smaSignal.price_vs_sma200 > 0 ? '+' : ''}{safeToFixed(smaSignal.price_vs_sma200)}%
                      </span>
                    </div>
                  )}
                  {smaSignal.golden_cross && (
                    <div className="mt-2 p-2 bg-green-500/10 border border-green-500/30 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-green-400">🟢 GOLDEN CROSS</span>
                        <span className="text-xs text-gray-400">SMA50 crossed above SMA200</span>
                      </div>
                    </div>
                  )}
                  {smaSignal.death_cross && (
                    <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-red-400">🔴 DEATH CROSS</span>
                        <span className="text-xs text-gray-400">SMA50 crossed below SMA200</span>
                      </div>
                    </div>
                  )}
                  {smaSignal.multi_ma_alignment && (
                    <div className={`mt-2 p-2 rounded-lg border ${
                      smaSignal.alignment_type === 'perfect_bullish' ? 'bg-green-500/10 border-green-500/30' :
                      smaSignal.alignment_type === 'perfect_bearish' ? 'bg-red-500/10 border-red-500/30' :
                      smaSignal.alignment_type === 'partial_bullish' ? 'bg-blue-500/10 border-blue-500/30' :
                      smaSignal.alignment_type === 'partial_bearish' ? 'bg-orange-500/10 border-orange-500/30' :
                      'bg-gray-500/10 border-gray-500/30'
                    }`}>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold ${
                          smaSignal.alignment_type === 'perfect_bullish' ? 'text-green-400' :
                          smaSignal.alignment_type === 'perfect_bearish' ? 'text-red-400' :
                          smaSignal.alignment_type === 'partial_bullish' ? 'text-blue-400' :
                          smaSignal.alignment_type === 'partial_bearish' ? 'text-orange-400' :
                          'text-gray-400'
                        }`}>
                          {smaSignal.alignment_type === 'perfect_bullish' ? '🟢' :
                           smaSignal.alignment_type === 'perfect_bearish' ? '🔴' :
                           smaSignal.alignment_type === 'partial_bullish' ? '🔵' :
                           smaSignal.alignment_type === 'partial_bearish' ? '🟠' : ''} MULTI-MA ALIGNMENT
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">{smaSignal.multi_ma_alignment}</div>
                    </div>
                  )}
                  {smaSignal.confidence !== undefined && smaSignal.confidence !== null && (
                    <div className="flex justify-between mt-2 pt-2 border-t border-gray-600">
                      <span className="text-gray-400">Confidence:</span>
                      <span className="font-semibold text-yellow-400">{smaSignal.confidence}%</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {typeof smaSignal.message === 'string' 
                    ? smaSignal.message 
                    : (smaSignal.message as any)?.text || (smaSignal.message as any)?.message || 'SMA signal generated'}
                </p>
                {smaSignal.ai_insight && (
                  <div className="mt-3 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-purple-300 font-semibold mb-1">AI Insight</p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {typeof smaSignal.ai_insight === 'string' 
                            ? smaSignal.ai_insight 
                            : (smaSignal.ai_insight as any)?.text || (smaSignal.ai_insight as any)?.message || (smaSignal.ai_insight as any)?.insight || 'AI analysis available'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Opening Range Breakout Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Clock className="w-5 h-5 text-emerald-400" />
                Opening Range Breakout
              </h2>
              <button
                onClick={fetchOpeningRangeSignal}
                disabled={loading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !openingRangeSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading Opening Range signal...
              </div>
            )}
            {!loading && !openingRangeSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch Opening Range signal
              </div>
            )}
            {openingRangeSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(openingRangeSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(openingRangeSignal.signal)}`}>
                    Signal: {openingRangeSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{safeToFixed(currentPrice)}</span>
                    </div>
                  )}
                  {openingRangeSignal.opening_high !== undefined && openingRangeSignal.opening_high !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Opening High:</span>
                      <span className="font-semibold text-green-400">₹{safeToFixed(openingRangeSignal.opening_high)}</span>
                    </div>
                  )}
                  {openingRangeSignal.opening_low !== undefined && openingRangeSignal.opening_low !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Opening Low:</span>
                      <span className="font-semibold text-red-400">₹{safeToFixed(openingRangeSignal.opening_low)}</span>
                    </div>
                  )}
                  {openingRangeSignal.opening_range !== undefined && openingRangeSignal.opening_range !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Range:</span>
                      <span className="font-semibold">₹{safeToFixed(openingRangeSignal.opening_range)}</span>
                    </div>
                  )}
                  {openingRangeSignal.entry !== undefined && openingRangeSignal.entry !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{safeToFixed(openingRangeSignal.entry)}</span>
                    </div>
                  )}
                  {openingRangeSignal.stop_loss !== undefined && openingRangeSignal.stop_loss !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{safeToFixed(openingRangeSignal.stop_loss)}</span>
                    </div>
                  )}
                  {openingRangeSignal.target !== undefined && openingRangeSignal.target !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{safeToFixed(openingRangeSignal.target)}</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {openingRangeSignal.reason || 'Opening range breakout signal generated'}
                </p>
              </div>
            )}
          </div>

          {/* MACD Trading Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Activity className="w-5 h-5 text-violet-400" />
                MACD Trading
              </h2>
              <button
                onClick={fetchMACDSignal}
                disabled={loading}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !macdSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading MACD signal...
              </div>
            )}
            {!loading && !macdSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch MACD signal
              </div>
            )}
            {macdSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(macdSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(macdSignal.signal)}`}>
                    Signal: {macdSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{safeToFixed(currentPrice)}</span>
                    </div>
                  )}
                  {macdSignal.macd_line !== undefined && macdSignal.macd_line !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">MACD Line:</span>
                      <span className={`font-semibold ${macdSignal.macd_line >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {safeToFixed(macdSignal.macd_line, 4)}
                      </span>
                    </div>
                  )}
                  {macdSignal.macd_signal !== undefined && macdSignal.macd_signal !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Signal Line:</span>
                      <span className={`font-semibold ${macdSignal.macd_signal >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {safeToFixed(macdSignal.macd_signal, 4)}
                      </span>
                    </div>
                  )}
                  {macdSignal.macd_histogram !== undefined && macdSignal.macd_histogram !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Histogram:</span>
                      <span className={`font-semibold ${macdSignal.macd_histogram >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {macdSignal.macd_histogram >= 0 ? '+' : ''}{safeToFixed(macdSignal.macd_histogram, 4)}
                      </span>
                    </div>
                  )}
                  {macdSignal.bullish_crossover && (
                    <div className="mt-2 p-2 bg-green-500/10 border border-green-500/30 rounded-lg">
                      <span className="text-xs font-bold text-green-400">🟢 BULLISH CROSSOVER</span>
                    </div>
                  )}
                  {macdSignal.bearish_crossover && (
                    <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <span className="text-xs font-bold text-red-400">🔴 BEARISH CROSSOVER</span>
                    </div>
                  )}
                  {macdSignal.entry_price !== undefined && macdSignal.entry_price !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{safeToFixed(macdSignal.entry_price)}</span>
                    </div>
                  )}
                  {macdSignal.stop_loss !== undefined && macdSignal.stop_loss !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{safeToFixed(macdSignal.stop_loss)}</span>
                    </div>
                  )}
                  {macdSignal.target_price !== undefined && macdSignal.target_price !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{safeToFixed(macdSignal.target_price)}</span>
                    </div>
                  )}
                  {macdSignal.confidence !== undefined && macdSignal.confidence !== null && (
                    <div className="flex justify-between mt-2 pt-2 border-t border-gray-600">
                      <span className="text-gray-400">Confidence:</span>
                      <span className="font-semibold text-yellow-400">{macdSignal.confidence}%</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {macdSignal.reason || 'MACD signal generated'}
                </p>
                {macdSignal.ai_insight && (
                  <div className="mt-3 p-3 bg-violet-500/10 border border-violet-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-violet-300 font-semibold mb-1">AI Insight</p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {typeof macdSignal.ai_insight === 'string' 
                            ? macdSignal.ai_insight 
                            : (macdSignal.ai_insight as any)?.text || (macdSignal.ai_insight as any)?.message || (macdSignal.ai_insight as any)?.insight || 'AI analysis available'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Bollinger Bands Trading Signal */}
          <div className="bg-[#1a1d28] rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-amber-400" />
                Bollinger Bands
              </h2>
              <button
                onClick={fetchBollingerBandsSignal}
                disabled={loading}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                Refresh
              </button>
            </div>

            {loading && !bollingerSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Loading Bollinger Bands signal...
              </div>
            )}
            {!loading && !bollingerSignal && (
              <div className="p-4 rounded-lg border border-gray-700 text-center text-gray-400">
                Click "Refresh" to fetch Bollinger Bands signal
              </div>
            )}
            {bollingerSignal && (
              <div className={`p-4 rounded-lg border ${getSignalBg(bollingerSignal.signal)}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`font-bold text-lg ${getSignalColor(bollingerSignal.signal)}`}>
                    Signal: {bollingerSignal.signal}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  {currentPrice && (
                    <div className="flex justify-between border-b border-gray-600 pb-2 mb-2">
                      <span className="text-gray-400 font-semibold">Current Price:</span>
                      <span className="font-bold text-lg text-white">₹{safeToFixed(currentPrice)}</span>
                    </div>
                  )}
                  {bollingerSignal.bb_upper !== undefined && bollingerSignal.bb_upper !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Upper Band:</span>
                      <span className="font-semibold text-green-400">₹{safeToFixed(bollingerSignal.bb_upper)}</span>
                    </div>
                  )}
                  {bollingerSignal.bb_middle !== undefined && bollingerSignal.bb_middle !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Middle Band:</span>
                      <span className="font-semibold">₹{safeToFixed(bollingerSignal.bb_middle)}</span>
                    </div>
                  )}
                  {bollingerSignal.bb_lower !== undefined && bollingerSignal.bb_lower !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Lower Band:</span>
                      <span className="font-semibold text-red-400">₹{safeToFixed(bollingerSignal.bb_lower)}</span>
                    </div>
                  )}
                  {bollingerSignal.band_width !== undefined && bollingerSignal.band_width !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Band Width:</span>
                      <span className="font-semibold">{safeToFixed(bollingerSignal.band_width, 2)}%</span>
                    </div>
                  )}
                  {bollingerSignal.percent_b !== undefined && bollingerSignal.percent_b !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">%B:</span>
                      <span className={`font-semibold ${
                        bollingerSignal.percent_b > 80 ? 'text-red-400' : 
                        bollingerSignal.percent_b < 20 ? 'text-green-400' : 
                        'text-yellow-400'
                      }`}>
                        {safeToFixed(bollingerSignal.percent_b, 2)}%
                      </span>
                    </div>
                  )}
                  {bollingerSignal.is_squeeze && (
                    <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                      <span className="text-xs font-bold text-yellow-400">⚠️ BOLLINGER SQUEEZE DETECTED</span>
                      <div className="text-xs text-gray-400 mt-1">Low volatility - Watch for breakout</div>
                    </div>
                  )}
                  {bollingerSignal.is_expansion && (
                    <div className="mt-2 p-2 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                      <span className="text-xs font-bold text-orange-400">📈 HIGH VOLATILITY</span>
                      <div className="text-xs text-gray-400 mt-1">Band expansion detected</div>
                    </div>
                  )}
                  {bollingerSignal.entry_price !== undefined && bollingerSignal.entry_price !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry:</span>
                      <span className="font-semibold">₹{safeToFixed(bollingerSignal.entry_price)}</span>
                    </div>
                  )}
                  {bollingerSignal.stop_loss !== undefined && bollingerSignal.stop_loss !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="font-semibold text-red-400">₹{safeToFixed(bollingerSignal.stop_loss)}</span>
                    </div>
                  )}
                  {bollingerSignal.target_price !== undefined && bollingerSignal.target_price !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Target:</span>
                      <span className="font-semibold text-green-400">₹{safeToFixed(bollingerSignal.target_price)}</span>
                    </div>
                  )}
                  {bollingerSignal.confidence !== undefined && bollingerSignal.confidence !== null && (
                    <div className="flex justify-between mt-2 pt-2 border-t border-gray-600">
                      <span className="text-gray-400">Confidence:</span>
                      <span className="font-semibold text-yellow-400">{bollingerSignal.confidence}%</span>
                    </div>
                  )}
                </div>
                <p className="mt-3 text-sm text-gray-300">
                  {bollingerSignal.reason || 'Bollinger Bands signal generated'}
                </p>
                {bollingerSignal.ai_insight && (
                  <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Zap className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-amber-300 font-semibold mb-1">AI Insight</p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {typeof bollingerSignal.ai_insight === 'string' 
                            ? bollingerSignal.ai_insight 
                            : (bollingerSignal.ai_insight as any)?.text || (bollingerSignal.ai_insight as any)?.message || (bollingerSignal.ai_insight as any)?.insight || 'AI analysis available'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  );
};

export default IntradayTrading;

