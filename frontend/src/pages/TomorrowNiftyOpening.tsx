/**
 * Tomorrow's NIFTY Opening Analysis Page
 * Comprehensive analysis combining GIFT NIFTY, India VIX, Global markets, News, FII/DII flows, and Technical levels
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, Activity, 
  RefreshCw, AlertCircle, Globe, Newspaper,
  Users, BarChart3, Zap, Target, Clock
} from 'lucide-react';
import { httpClient } from '../config/api';
import { toast } from 'react-hot-toast';

interface GiftNiftyData {
  price: number;
  change_pct: number;
  premium_discount_pct: number;
  sentiment: string;
}

interface IndiaVixData {
  level: number;
  change_pct: number;
  regime: string;
  sentiment: string;
  interpretation: string;
}

interface NextDayOpeningAnalysis {
  applicable: boolean;
  current_nifty_price?: number | null;
  expected_opening_direction?: string;
  expected_opening_range?: {
    lower_bound: number;
    upper_bound: number;
    most_likely: number;
    range_width_pct: number;
  };
  confidence?: number;
  risk_assessment?: string;
  key_levels?: {
    support: number;
    resistance: number;
    current_price: number;
  };
  interpretation?: string;
  error?: string;
  note?: string;
  summary?: {
    gift_nifty_sentiment: string;
    vix_regime: string;
    expected_direction: string;
    volatility_level: string;
    opening_range_estimate: string;
    vix_change?: number;
    hours_until_open?: number;
    prediction_confidence?: number;
    all_factors_included?: boolean;
  };
  // Phase 1 enhancements
  time_analysis?: {
    hours_until_open: number;
    market_open_time: string;
    gift_nifty_weight: number;
    note: string;
  };
  prev_day_data?: {
    high: number;
    low: number;
    close: number;
    closing_position: number;
  };
  prev_day_close_strength?: string;
  vix_direction?: string;
  gift_nifty_volume_status?: string;
  gift_nifty_volume?: number;
  gift_nifty_volume_ratio?: number;
  gift_nifty_final_weight?: number;
  gap_fill_warning?: string;
  // Enhanced factors
  global_markets?: {
    us_markets: { status: string; change_pct: number; impact: string };
    asian_markets: { status: string; change_pct: number; impact: string };
    overall_sentiment: string;
  };
  news_events?: {
    overnight_news: Array<{ headline: string; impact: string; sentiment: string; sentiment_score?: number; description?: string; source?: string; published?: string }>;
    sector_news: Array<{ sector: string; headline: string; impact: string }>;
    overall_impact: string;
    news_count?: number;
    avg_sentiment?: number;
  };
  fii_dii_flows?: {
    fii_net: number;
    dii_net: number;
    interpretation: string;
    impact: string;
    data_source?: string;
    last_updated?: string;
    trend?: string;
  };
  currency_impact?: {
    usd_inr_rate: number;
    usd_inr_change_pct: number;
    sentiment: string;
    adjustment_pct: number;
    interpretation?: string;
  };
  options_oi?: {
    pcr: number;
    max_pain_level: number;
    max_pain_diff_pct?: number;
    sentiment: string;
    note?: string;
  };
  sector_rotation?: {
    banking_change_pct: number;
    it_change_pct: number;
    weighted_impact_pct: number;
    interpretation: string;
  };
  technical_levels?: {
    support_levels: number[];
    resistance_levels: number[];
    pivot_points: { r1: number; r2: number; r3: number; s1: number; s2: number; s3: number; pp: number };
    interpretation: string;
  };
  factor_contributions?: {
    gift_nifty: { impact_pct: number; weight: number; contribution: number };
    prev_day_close: { adjustment_pct: number; weight: number; contribution: number };
    global_markets: { adjustment_pct: number; weight: number; contribution: number };
    news: { adjustment_pct: number; weight: number; contribution: number };
    fii_dii: { adjustment_pct: number; weight: number; contribution: number };
    currency: { adjustment_pct: number; weight: number; contribution: number };
    options_oi: { adjustment_pct: number; weight: number; contribution: number };
    sector_rotation: { adjustment_pct: number; weight: number; contribution: number };
    vix_direction: { adjustment_pct: number; weight: number; contribution: number };
    total_adjustment_pct: number;
  };
  methodology?: {
    primary_indicator: string;
    secondary_indicators: string[];
    volatility_indicator: string;
    enhancements: string[];
  };
}

const TomorrowNiftyOpening: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [giftNiftyData, setGiftNiftyData] = useState<GiftNiftyData | null>(null);
  const [indiaVixData, setIndiaVixData] = useState<IndiaVixData | null>(null);
  const [openingAnalysis, setOpeningAnalysis] = useState<NextDayOpeningAnalysis | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const response = await httpClient.get('/api/comprehensive-trading/fno/chart-analysis/NIFTY', {
        timeframe: '1D',
        enable_multi_timeframe: true
      }) as any;

      console.log('📊 Full API Response:', response);
      
      if (response.success && response.data) {
        const facts = (response.data as any).facts || {};
        
        console.log('📋 Facts data:', facts);
        console.log('🎁 GIFT NIFTY Data:', facts.gift_nifty_data);
        console.log('⚡ India VIX Data:', facts.india_vix_data);
        console.log('📈 Next Day Opening Analysis:', facts.next_day_opening_analysis);
        
        // Set data with fallbacks
        setGiftNiftyData(facts.gift_nifty_data || null);
        setIndiaVixData(facts.india_vix_data || null);
        setOpeningAnalysis(facts.next_day_opening_analysis || null);
        setLastUpdated(new Date());
        
        // Check what's missing
        if (!facts.gift_nifty_data) {
          console.warn('⚠️ GIFT NIFTY data is missing');
        }
        if (!facts.india_vix_data) {
          console.warn('⚠️ India VIX data is missing');
        }
        if (!facts.next_day_opening_analysis) {
          console.warn('⚠️ Next Day Opening Analysis is missing');
        }
        
        toast.success('Analysis updated successfully');
      } else {
        console.error('❌ Response not successful:', response);
        toast.error('Failed to fetch analysis: Invalid response');
      }
    } catch (error: any) {
      console.error('❌ Failed to fetch analysis:', error);
      console.error('Error details:', error.response?.data || error.message);
      toast.error(error.message || 'Failed to fetch analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toUpperCase()) {
      case 'BULLISH':
        return 'text-green-400';
      case 'BEARISH':
        return 'text-red-400';
      case 'PANIC':
        return 'text-red-600';
      case 'EXTREME':
        return 'text-orange-500';
      default:
        return 'text-yellow-400';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'VERY HIGH':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'MODERATE':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-green-500/20 text-green-400 border-green-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0e27] via-[#1a1d28] to-[#0a0e27] text-white p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                <Clock className="w-8 h-8 text-indigo-400" />
                Tomorrow's NIFTY Opening Analysis
              </h1>
              <p className="text-gray-400">
                Comprehensive prediction combining GIFT NIFTY, India VIX, Global markets, News, FII/DII flows, and Technical levels
              </p>
            </div>
            <button
              onClick={fetchAnalysis}
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          {lastUpdated && (
            <p className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleString()}
            </p>
          )}
        </div>

        {loading && !openingAnalysis ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-400"></div>
          </div>
        ) : !openingAnalysis ? (
          <div className="text-center py-20">
            <AlertCircle className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">No analysis data available. Click Refresh to load.</p>
            {/* Debug Info */}
            <div className="mt-4 p-4 bg-black/30 rounded-lg max-w-2xl mx-auto text-left">
              <p className="text-sm font-semibold mb-2">Data Availability:</p>
              <ul className="text-xs text-gray-400 space-y-1">
                <li>GIFT NIFTY: {giftNiftyData ? '✅ Available' : '❌ Missing'}</li>
                <li>India VIX: {indiaVixData ? '✅ Available' : '❌ Missing'}</li>
                <li>Opening Analysis: {openingAnalysis ? '✅ Available' : '❌ Missing'}</li>
              </ul>
              <p className="text-xs text-gray-500 mt-4">Check browser console for detailed logs.</p>
            </div>
          </div>
        ) : openingAnalysis.error ? (
          <div className="space-y-6">
            {/* Error Display */}
            <div className="bg-red-500/10 border-2 border-red-500/40 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-red-400">
                <AlertCircle className="w-6 h-6" />
                Analysis Error
              </h2>
              <p className="text-red-300 mb-2">{openingAnalysis.error}</p>
              {openingAnalysis.note && (
                <p className="text-sm text-gray-400">{openingAnalysis.note}</p>
              )}
              {/* Show available data even if there's an error */}
              <div className="mt-4 p-4 bg-black/30 rounded-lg">
                <p className="text-sm font-semibold mb-2">Available Data:</p>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>Current Price: {openingAnalysis.current_nifty_price ? `₹${openingAnalysis.current_nifty_price}` : 'N/A'}</li>
                  <li>GIFT NIFTY: {giftNiftyData ? '✅ Available' : '❌ Missing'}</li>
                  <li>India VIX: {indiaVixData ? '✅ Available' : '❌ Missing'}</li>
                </ul>
              </div>
            </div>
            
            {/* Show GIFT NIFTY and VIX data even if analysis failed */}
            {giftNiftyData && (
              <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-400" />
                  GIFT NIFTY Data (Available)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">Price</span>
                    <div className="text-lg font-bold text-white mt-1">
                      ₹{giftNiftyData.price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Change</span>
                    <div className={`text-lg font-bold mt-1 ${giftNiftyData.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {giftNiftyData.change_pct >= 0 ? '+' : ''}{giftNiftyData.change_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Premium/Discount</span>
                    <div className={`text-lg font-bold mt-1 ${giftNiftyData.premium_discount_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {giftNiftyData.premium_discount_pct >= 0 ? '+' : ''}{giftNiftyData.premium_discount_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Sentiment</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(giftNiftyData.sentiment)}`}>
                      {giftNiftyData.sentiment || 'NEUTRAL'}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {indiaVixData && (
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-purple-400" />
                  India VIX Data (Available)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">VIX Level</span>
                    <div className="text-lg font-bold text-white mt-1">
                      {indiaVixData.level?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Change</span>
                    <div className={`text-lg font-bold mt-1 ${indiaVixData.change_pct >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {indiaVixData.change_pct >= 0 ? '+' : ''}{indiaVixData.change_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Regime</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(indiaVixData.regime)}`}>
                      {indiaVixData.regime || 'NORMAL'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Sentiment</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(indiaVixData.sentiment)}`}>
                      {indiaVixData.sentiment || 'NEUTRAL'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Current NIFTY Price */}
            <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border-2 border-indigo-500/40 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm mb-1">Current NIFTY Price</p>
                  <p className="text-4xl font-bold text-white">
                    ₹{openingAnalysis.current_nifty_price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                  </p>
                </div>
                <Activity className="w-12 h-12 text-indigo-400 opacity-50" />
              </div>
            </div>

            {/* Expected Opening Range - Main Card */}
            {openingAnalysis.expected_opening_range && (
              <div className="bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 border-2 border-indigo-500/40 rounded-lg p-6">
                <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Target className="w-6 h-6 text-indigo-400" />
                  Expected Opening Range
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="text-center p-4 bg-black/30 rounded-lg border border-indigo-500/30">
                    <span className="text-gray-400 text-sm">Lower Bound</span>
                    <div className="text-2xl font-bold text-red-400 mt-2">
                      ₹{openingAnalysis.expected_opening_range.lower_bound.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-black/30 rounded-lg border border-indigo-500/30">
                    <span className="text-gray-400 text-sm">Most Likely Opening</span>
                    <div className={`text-3xl font-bold mt-2 ${
                      openingAnalysis.expected_opening_direction === 'BULLISH' ? 'text-green-400' :
                      openingAnalysis.expected_opening_direction === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                      ₹{openingAnalysis.expected_opening_range.most_likely.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className={`text-sm mt-2 font-semibold ${
                      openingAnalysis.expected_opening_direction === 'BULLISH' ? 'text-green-400' :
                      openingAnalysis.expected_opening_direction === 'BEARISH' ? 'text-red-400' : 'text-gray-400'
                    }`}>
                      {openingAnalysis.expected_opening_direction}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-black/30 rounded-lg border border-indigo-500/30">
                    <span className="text-gray-400 text-sm">Upper Bound</span>
                    <div className="text-2xl font-bold text-green-400 mt-2">
                      ₹{openingAnalysis.expected_opening_range.upper_bound.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-black/20 rounded-lg">
                    <span className="text-gray-400 text-sm">Confidence</span>
                    <div className="text-2xl font-bold text-purple-400 mt-1">
                      {((openingAnalysis.confidence || 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className={`p-4 rounded-lg border ${getRiskColor(openingAnalysis.risk_assessment || 'MODERATE')}`}>
                    <span className="text-sm opacity-75">Risk Assessment</span>
                    <div className="text-xl font-bold mt-1">
                      {openingAnalysis.risk_assessment || 'MODERATE'}
                    </div>
                  </div>
                </div>

                <div className="mt-4 text-xs text-gray-400">
                  Range Width: ±{openingAnalysis.expected_opening_range.range_width_pct.toFixed(2)}%
                </div>
              </div>
            )}

            {/* Time Analysis & Prediction Confidence */}
            {openingAnalysis.time_analysis && (
              <div className="bg-gradient-to-r from-purple-500/10 to-indigo-500/10 border border-purple-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-purple-400" />
                  Prediction Timing & Confidence
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">Hours Until Market Open</span>
                    <div className="text-2xl font-bold text-purple-400 mt-1">
                      {openingAnalysis.time_analysis.hours_until_open.toFixed(1)}h
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{openingAnalysis.time_analysis.note}</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">GIFT NIFTY Weight</span>
                    <div className="text-2xl font-bold text-indigo-400 mt-1">
                      {(openingAnalysis.time_analysis.gift_nifty_weight * 100).toFixed(0)}%
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Dynamic weight based on timing</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Market Opens At</span>
                    <div className="text-lg font-bold text-white mt-1">
                      {new Date(openingAnalysis.time_analysis.market_open_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">IST (9:15 AM)</p>
                  </div>
                </div>
              </div>
            )}

            {/* Key Levels */}
            {openingAnalysis.key_levels && (
              <div className="bg-black/30 border border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-indigo-400" />
                  Key Trading Levels
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-black/20 rounded-lg">
                    <span className="text-gray-400 text-xs">Support</span>
                    <div className="text-xl font-bold text-green-400 mt-1">
                      ₹{openingAnalysis.key_levels.support?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-black/20 rounded-lg">
                    <span className="text-gray-400 text-xs">Current</span>
                    <div className="text-xl font-bold text-white mt-1">
                      ₹{openingAnalysis.key_levels.current_price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                    </div>
                  </div>
                  <div className="text-center p-4 bg-black/20 rounded-lg">
                    <span className="text-gray-400 text-xs">Resistance</span>
                    <div className="text-xl font-bold text-red-400 mt-1">
                      ₹{openingAnalysis.key_levels.resistance?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Previous Day Closing Behavior */}
            {openingAnalysis.prev_day_data && (
              <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-orange-400" />
                  Previous Day Closing Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">High</span>
                    <div className="text-lg font-bold text-green-400 mt-1">
                      ₹{openingAnalysis.prev_day_data.high.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Low</span>
                    <div className="text-lg font-bold text-red-400 mt-1">
                      ₹{openingAnalysis.prev_day_data.low.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Close</span>
                    <div className="text-lg font-bold text-white mt-1">
                      ₹{openingAnalysis.prev_day_data.close.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Closing Position</span>
                    <div className="text-lg font-bold text-purple-400 mt-1">
                      {(openingAnalysis.prev_day_data.closing_position * 100).toFixed(0)}%
                    </div>
                    <div className={`text-xs mt-1 font-semibold ${
                      openingAnalysis.prev_day_close_strength === 'STRONG' ? 'text-green-400' :
                      openingAnalysis.prev_day_close_strength === 'WEAK' ? 'text-red-400' : 'text-gray-400'
                    }`}>
                      {openingAnalysis.prev_day_close_strength || 'NEUTRAL'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* GIFT NIFTY Analysis - Enhanced */}
            {giftNiftyData && (
              <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-400" />
                  GIFT NIFTY Analysis (Primary Indicator)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <span className="text-gray-400 text-sm">Price</span>
                    <div className="text-lg font-bold text-white mt-1">
                      ₹{giftNiftyData.price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Change</span>
                    <div className={`text-lg font-bold mt-1 ${giftNiftyData.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {giftNiftyData.change_pct >= 0 ? '+' : ''}{giftNiftyData.change_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Premium/Discount</span>
                    <div className={`text-lg font-bold mt-1 ${giftNiftyData.premium_discount_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {giftNiftyData.premium_discount_pct >= 0 ? '+' : ''}{giftNiftyData.premium_discount_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Sentiment</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(giftNiftyData.sentiment)}`}>
                      {giftNiftyData.sentiment || 'NEUTRAL'}
                    </div>
                  </div>
                </div>
                
                {/* Phase 2: Volume Analysis */}
                {openingAnalysis.gift_nifty_volume_status && (
                  <div className="mt-4 p-3 bg-black/20 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Volume Status: </span>
                        <span className={`font-semibold ${
                          openingAnalysis.gift_nifty_volume_status === 'HIGH_VOLUME' ? 'text-green-400' :
                          openingAnalysis.gift_nifty_volume_status === 'LOW_VOLUME' ? 'text-yellow-400' : 'text-gray-400'
                        }`}>
                          {openingAnalysis.gift_nifty_volume_status.replace('_', ' ')}
                        </span>
                      </div>
                      {openingAnalysis.gift_nifty_volume_ratio && (
                        <div>
                          <span className="text-gray-400">Volume Ratio: </span>
                          <span className="font-semibold text-blue-400">
                            {openingAnalysis.gift_nifty_volume_ratio.toFixed(2)}x
                          </span>
                        </div>
                      )}
                      {openingAnalysis.gift_nifty_final_weight && (
                        <div>
                          <span className="text-gray-400">Final Weight: </span>
                          <span className="font-semibold text-purple-400">
                            {(openingAnalysis.gift_nifty_final_weight * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Gap Fill Warning */}
                {openingAnalysis.gap_fill_warning && (
                  <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-sm text-yellow-400">{openingAnalysis.gap_fill_warning}</p>
                  </div>
                )}
              </div>
            )}

            {/* India VIX Analysis - Enhanced with Direction */}
            {indiaVixData && (
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-purple-400" />
                  India VIX (Volatility Index)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
                  <div>
                    <span className="text-gray-400 text-sm">VIX Level</span>
                    <div className="text-lg font-bold text-white mt-1">
                      {indiaVixData.level?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Change</span>
                    <div className={`text-lg font-bold mt-1 ${indiaVixData.change_pct >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {indiaVixData.change_pct >= 0 ? '+' : ''}{indiaVixData.change_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Regime</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(indiaVixData.regime)}`}>
                      {indiaVixData.regime || 'NORMAL'}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Sentiment</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(indiaVixData.sentiment)}`}>
                      {indiaVixData.sentiment || 'NEUTRAL'}
                    </div>
                  </div>
                  {openingAnalysis.vix_direction && (
                    <div>
                      <span className="text-gray-400 text-sm">Direction</span>
                      <div className={`text-lg font-bold mt-1 ${
                        openingAnalysis.vix_direction === 'RISING_FEAR' ? 'text-red-500' :
                        openingAnalysis.vix_direction === 'FALLING_FEAR' ? 'text-green-400' : 'text-gray-400'
                      }`}>
                        {openingAnalysis.vix_direction.replace('_', ' ')}
                      </div>
                    </div>
                  )}
                </div>
                {indiaVixData.interpretation && (
                  <p className="text-sm text-gray-300 mt-2">{indiaVixData.interpretation}</p>
                )}
              </div>
            )}

            {/* Currency Impact */}
            {openingAnalysis.currency_impact && openingAnalysis.currency_impact.usd_inr_rate && (
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-green-400" />
                  Currency Impact (USD/INR)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">USD/INR Rate</span>
                    <div className="text-lg font-bold text-white mt-1">
                      ₹{openingAnalysis.currency_impact.usd_inr_rate.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Change</span>
                    <div className={`text-lg font-bold mt-1 ${
                      openingAnalysis.currency_impact.usd_inr_change_pct >= 0 ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {openingAnalysis.currency_impact.usd_inr_change_pct >= 0 ? '+' : ''}{openingAnalysis.currency_impact.usd_inr_change_pct.toFixed(2)}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Impact</span>
                    <div className={`text-lg font-bold mt-1 ${getSentimentColor(openingAnalysis.currency_impact.sentiment)}`}>
                      {openingAnalysis.currency_impact.sentiment}
                    </div>
                    {openingAnalysis.currency_impact.interpretation && (
                      <p className="text-xs text-gray-400 mt-1">{openingAnalysis.currency_impact.interpretation}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Options OI Data */}
            {openingAnalysis.options_oi && (
              <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-yellow-400" />
                  Options Open Interest Analysis
                </h3>
                {openingAnalysis.options_oi.pcr ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <span className="text-gray-400 text-sm">Put-Call Ratio (PCR)</span>
                      <div className="text-lg font-bold text-white mt-1">
                        {openingAnalysis.options_oi.pcr.toFixed(2)}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {openingAnalysis.options_oi.pcr > 1.2 ? 'Bearish (More Puts)' :
                         openingAnalysis.options_oi.pcr < 0.8 ? 'Bullish (More Calls)' : 'Neutral'}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">Max Pain Level</span>
                      <div className="text-lg font-bold text-purple-400 mt-1">
                        ₹{openingAnalysis.options_oi.max_pain_level.toFixed(2)}
                      </div>
                      {openingAnalysis.options_oi.max_pain_diff_pct !== undefined && (
                        <p className="text-xs text-gray-400 mt-1">
                          {openingAnalysis.options_oi.max_pain_diff_pct >= 0 ? '+' : ''}{openingAnalysis.options_oi.max_pain_diff_pct.toFixed(2)}% from current
                        </p>
                      )}
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">Sentiment</span>
                      <div className={`text-lg font-bold mt-1 ${getSentimentColor(openingAnalysis.options_oi.sentiment)}`}>
                        {openingAnalysis.options_oi.sentiment}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">{openingAnalysis.options_oi.note || 'Options OI data not available'}</p>
                )}
              </div>
            )}

            {/* Sector Rotation */}
            {openingAnalysis.sector_rotation && openingAnalysis.sector_rotation.banking_change_pct !== null && (
              <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-cyan-400" />
                  Sector Rotation Impact
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">Banking Sector</span>
                    <div className={`text-lg font-bold mt-1 ${openingAnalysis.sector_rotation.banking_change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {openingAnalysis.sector_rotation.banking_change_pct >= 0 ? '+' : ''}{openingAnalysis.sector_rotation.banking_change_pct.toFixed(2)}%
                    </div>
                    <p className="text-xs text-gray-400 mt-1">~30% weight in NIFTY</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">IT Sector</span>
                    <div className={`text-lg font-bold mt-1 ${openingAnalysis.sector_rotation.it_change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {openingAnalysis.sector_rotation.it_change_pct >= 0 ? '+' : ''}{openingAnalysis.sector_rotation.it_change_pct.toFixed(2)}%
                    </div>
                    <p className="text-xs text-gray-400 mt-1">~15% weight in NIFTY</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Weighted Impact</span>
                    <div className={`text-lg font-bold mt-1 ${openingAnalysis.sector_rotation.weighted_impact_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {openingAnalysis.sector_rotation.weighted_impact_pct >= 0 ? '+' : ''}{openingAnalysis.sector_rotation.weighted_impact_pct.toFixed(3)}%
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{openingAnalysis.sector_rotation.interpretation}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Enhanced Factors */}
            {openingAnalysis.global_markets && (
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-green-400" />
                  Global Markets Impact
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">US Markets</span>
                    <div className="text-lg font-bold text-white mt-1">
                      {openingAnalysis.global_markets.us_markets.status} ({openingAnalysis.global_markets.us_markets.change_pct >= 0 ? '+' : ''}{openingAnalysis.global_markets.us_markets.change_pct.toFixed(2)}%)
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{openingAnalysis.global_markets.us_markets.impact}</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Asian Markets</span>
                    <div className="text-lg font-bold text-white mt-1">
                      {openingAnalysis.global_markets.asian_markets.status} ({openingAnalysis.global_markets.asian_markets.change_pct >= 0 ? '+' : ''}{openingAnalysis.global_markets.asian_markets.change_pct.toFixed(2)}%)
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{openingAnalysis.global_markets.asian_markets.impact}</p>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-black/20 rounded-lg">
                  <span className="text-gray-400 text-sm">Overall Sentiment: </span>
                  <span className={`font-bold ${getSentimentColor(openingAnalysis.global_markets.overall_sentiment)}`}>
                    {openingAnalysis.global_markets.overall_sentiment}
                  </span>
                </div>
              </div>
            )}

            {openingAnalysis.news_events && (
              <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Newspaper className="w-5 h-5 text-yellow-400" />
                  News & Events Impact
                </h3>
                {openingAnalysis.news_events.overnight_news && openingAnalysis.news_events.overnight_news.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-semibold mb-2">Overnight News</h4>
                    <div className="space-y-2">
                      {openingAnalysis.news_events.overnight_news.map((news, idx) => (
                        <div key={idx} className="p-3 bg-black/20 rounded-lg">
                          <p className="text-sm font-medium">{news.headline}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            Impact: <span className={getSentimentColor(news.sentiment)}>{news.impact}</span>
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="p-3 bg-black/20 rounded-lg">
                  <span className="text-gray-400 text-sm">Overall Impact: </span>
                  <span className={`font-bold ${getSentimentColor(openingAnalysis.news_events.overall_impact)}`}>
                    {openingAnalysis.news_events.overall_impact}
                  </span>
                </div>
              </div>
            )}

            {openingAnalysis.fii_dii_flows && (
              <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-cyan-400" />
                  FII/DII Flows
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">FII Net Flow</span>
                    <div className={`text-lg font-bold mt-1 ${openingAnalysis.fii_dii_flows.fii_net >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {openingAnalysis.fii_dii_flows.fii_net >= 0 ? '+' : ''}₹{Math.abs(openingAnalysis.fii_dii_flows.fii_net).toLocaleString('en-IN')} Cr
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">DII Net Flow</span>
                    <div className={`text-lg font-bold mt-1 ${openingAnalysis.fii_dii_flows.dii_net >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {openingAnalysis.fii_dii_flows.dii_net >= 0 ? '+' : ''}₹{Math.abs(openingAnalysis.fii_dii_flows.dii_net).toLocaleString('en-IN')} Cr
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-300 mt-4">{openingAnalysis.fii_dii_flows.interpretation}</p>
                <div className="mt-2 p-2 bg-black/20 rounded">
                  <span className="text-gray-400 text-sm">Impact: </span>
                  <span className={`font-semibold ${getSentimentColor(openingAnalysis.fii_dii_flows.impact)}`}>
                    {openingAnalysis.fii_dii_flows.impact}
                  </span>
                </div>
              </div>
            )}

            {openingAnalysis.technical_levels && (
              <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-indigo-400" />
                  Technical Levels
                </h3>
                {openingAnalysis.technical_levels.pivot_points && (
                  <div className="mb-4">
                    <h4 className="font-semibold mb-2">Pivot Points</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">R3: </span>
                        <span className="font-bold text-red-400">₹{openingAnalysis.technical_levels.pivot_points.r3.toFixed(2)}</span>
                      </div>
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">R2: </span>
                        <span className="font-bold text-red-400">₹{openingAnalysis.technical_levels.pivot_points.r2.toFixed(2)}</span>
                      </div>
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">R1: </span>
                        <span className="font-bold text-red-400">₹{openingAnalysis.technical_levels.pivot_points.r1.toFixed(2)}</span>
                      </div>
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">PP: </span>
                        <span className="font-bold text-white">₹{openingAnalysis.technical_levels.pivot_points.pp.toFixed(2)}</span>
                      </div>
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">S1: </span>
                        <span className="font-bold text-green-400">₹{openingAnalysis.technical_levels.pivot_points.s1.toFixed(2)}</span>
                      </div>
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">S2: </span>
                        <span className="font-bold text-green-400">₹{openingAnalysis.technical_levels.pivot_points.s2.toFixed(2)}</span>
                      </div>
                      <div className="p-2 bg-black/20 rounded">
                        <span className="text-gray-400">S3: </span>
                        <span className="font-bold text-green-400">₹{openingAnalysis.technical_levels.pivot_points.s3.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                )}
                <p className="text-sm text-gray-300">{openingAnalysis.technical_levels.interpretation}</p>
              </div>
            )}

            {/* Combined Impact Analysis */}
            {openingAnalysis.interpretation && (
              <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  Combined Impact Analysis
                </h3>
                <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                  {openingAnalysis.interpretation}
                </p>
              </div>
            )}

            {/* Factor Contributions Breakdown */}
            {openingAnalysis.factor_contributions && (
              <div className="bg-black/30 border border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">Factor Contributions Breakdown</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">GIFT NIFTY (Primary):</span>
                    <span className="font-bold text-blue-400">
                      {openingAnalysis.factor_contributions.gift_nifty.impact_pct.toFixed(2)}% × {(openingAnalysis.factor_contributions.gift_nifty.weight * 100).toFixed(0)}% = {openingAnalysis.factor_contributions.gift_nifty.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">Previous Day Close:</span>
                    <span className="font-bold text-orange-400">
                      {openingAnalysis.factor_contributions.prev_day_close.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.prev_day_close.adjustment_pct.toFixed(3)}% × 5% = {openingAnalysis.factor_contributions.prev_day_close.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.prev_day_close.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">Global Markets:</span>
                    <span className="font-bold text-green-400">
                      {openingAnalysis.factor_contributions.global_markets.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.global_markets.adjustment_pct.toFixed(3)}% × 8% = {openingAnalysis.factor_contributions.global_markets.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.global_markets.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">News Sentiment:</span>
                    <span className="font-bold text-yellow-400">
                      {openingAnalysis.factor_contributions.news.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.news.adjustment_pct.toFixed(3)}% × 7% = {openingAnalysis.factor_contributions.news.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.news.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">FII/DII Flows:</span>
                    <span className="font-bold text-cyan-400">
                      {openingAnalysis.factor_contributions.fii_dii.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.fii_dii.adjustment_pct.toFixed(3)}% × 5% = {openingAnalysis.factor_contributions.fii_dii.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.fii_dii.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">Currency (USD/INR):</span>
                    <span className="font-bold text-emerald-400">
                      {openingAnalysis.factor_contributions.currency.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.currency.adjustment_pct.toFixed(3)}% × 2% = {openingAnalysis.factor_contributions.currency.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.currency.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">Options OI:</span>
                    <span className="font-bold text-yellow-400">
                      {openingAnalysis.factor_contributions.options_oi.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.options_oi.adjustment_pct.toFixed(3)}% × 3% = {openingAnalysis.factor_contributions.options_oi.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.options_oi.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">Sector Rotation:</span>
                    <span className="font-bold text-cyan-400">
                      {openingAnalysis.factor_contributions.sector_rotation.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.sector_rotation.adjustment_pct.toFixed(3)}% × 2% = {openingAnalysis.factor_contributions.sector_rotation.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.sector_rotation.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/20 rounded">
                    <span className="text-gray-400">VIX Direction:</span>
                    <span className="font-bold text-purple-400">
                      {openingAnalysis.factor_contributions.vix_direction.adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.vix_direction.adjustment_pct.toFixed(3)}% × 2% = {openingAnalysis.factor_contributions.vix_direction.contribution >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.vix_direction.contribution.toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-indigo-500/20 rounded-lg border border-indigo-500/30 mt-3">
                    <span className="text-lg font-bold">Total Adjustment:</span>
                    <span className={`text-lg font-bold ${
                      openingAnalysis.factor_contributions.total_adjustment_pct >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {openingAnalysis.factor_contributions.total_adjustment_pct >= 0 ? '+' : ''}{openingAnalysis.factor_contributions.total_adjustment_pct.toFixed(3)}%
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Methodology Info */}
            {openingAnalysis.methodology && (
              <div className="bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 border border-indigo-500/30 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">📚 Prediction Methodology</h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-semibold text-indigo-400">Primary Indicator: </span>
                    <span className="text-gray-300">{openingAnalysis.methodology.primary_indicator}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-purple-400">Secondary Indicators: </span>
                    <ul className="list-disc list-inside text-gray-300 mt-1 space-y-1">
                      {openingAnalysis.methodology.secondary_indicators.map((indicator, idx) => (
                        <li key={idx}>{indicator}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <span className="font-semibold text-pink-400">Enhancements Applied: </span>
                    <span className="text-gray-300">{openingAnalysis.methodology.enhancements.join(', ')}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Summary */}
            {openingAnalysis.summary && (
              <div className="bg-black/30 border border-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">Quick Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">GIFT NIFTY: </span>
                    <span className={`font-semibold ${getSentimentColor(openingAnalysis.summary.gift_nifty_sentiment)}`}>
                      {openingAnalysis.summary.gift_nifty_sentiment}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">VIX Regime: </span>
                    <span className={`font-semibold ${getSentimentColor(openingAnalysis.summary.vix_regime)}`}>
                      {openingAnalysis.summary.vix_regime}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Expected Direction: </span>
                    <span className={`font-semibold ${getSentimentColor(openingAnalysis.summary.expected_direction)}`}>
                      {openingAnalysis.summary.expected_direction}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Expected Range: </span>
                    <span className="font-semibold text-indigo-400">
                      {openingAnalysis.summary.opening_range_estimate}
                    </span>
                  </div>
                </div>
                {openingAnalysis.summary.hours_until_open && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <span className="text-gray-400 text-sm">Hours Until Open: </span>
                    <span className="font-semibold text-purple-400">{openingAnalysis.summary.hours_until_open.toFixed(1)}h</span>
                    {openingAnalysis.summary.all_factors_included && (
                      <span className="ml-4 text-xs text-green-400">✓ All factors included</span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TomorrowNiftyOpening;

