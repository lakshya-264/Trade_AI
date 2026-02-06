/**
 * Intelligent Trading Interface - Smart Trading Features Dashboard
 * Integrates all backend Intelligent Trading endpoints for comprehensive smart trading
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  LightBulbIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CpuChipIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  PlayIcon,
  PauseIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  ShareIcon,
  DocumentArrowDownIcon,
  SignalIcon,
  CurrencyDollarIcon,
  AdjustmentsHorizontalIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { toast } from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import ErrorDisplay from './ErrorDisplay';
import BuySellButton from './BuySellButton';
import StockSelector from './StockSelector';
import { indexData, IndexStock } from '../data/indexStocks';

// Import Intelligent Trading API service
import intelligentTradingApi, {
  StockRecommendationsRequest,
  StockRecommendationsResponse,
  OptimalTimingResponse,
  MarketIntelligenceResponse,
  PortfolioOptimizationRequest,
  PortfolioOptimizationResponse,
  TradingSignalsResponse
} from '../services/intelligentTradingApi';

// Import Unified AI API service for recommendations
import unifiedAiApi, {
  AIRecommendationsRequest,
  AIRecommendationsResponse
} from '../services/unifiedAiApi';

// Import API service for stock quotes and details
import api from '../services/api';

interface IntelligentTradingInterfaceProps {
  className?: string;
}

type TabType = 'recommendations' | 'timing' | 'intelligence' | 'optimization' | 'signals';

const IntelligentTradingInterface: React.FC<IntelligentTradingInterfaceProps> = ({
  className = ''
}) => {
  const navigate = useNavigate();
  
  // State management
  const [activeTab, setActiveTab] = useState<TabType>('recommendations');
  const [selectedSymbol, setSelectedSymbol] = useState('RELIANCE');
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states with safe defaults
  const [recommendations, setRecommendations] = useState<AIRecommendationsResponse | null>(null);
  const [stockDetails, setStockDetails] = useState<Record<string, {
    quote: any;
    analysis: any;
    companyInfo: any;
  }>>({});
  const [expandedResearch, setExpandedResearch] = useState<Record<string, boolean>>({});
  const [optimalTiming, setOptimalTiming] = useState<OptimalTimingResponse | null>(null);
  const [marketIntelligence, setMarketIntelligence] = useState<MarketIntelligenceResponse | null>(null);
  const [portfolioOptimization, setPortfolioOptimization] = useState<PortfolioOptimizationResponse | null>(null);
  const [tradingSignals, setTradingSignals] = useState<TradingSignalsResponse | null>(null);

  // User preferences for recommendations
  const [userPreferences, setUserPreferences] = useState({
    risk_tolerance: 'medium' as 'low' | 'medium' | 'high',
    investment_horizon: 'medium_term' as 'short_term' | 'medium_term' | 'long_term',
    preferred_sectors: [] as string[],
    market_cap_preference: 'large_cap' as 'small_cap' | 'mid_cap' | 'large_cap',
    volatility_tolerance: 'medium' as 'low' | 'medium' | 'high',
    max_positions: 10,
    min_confidence: 70
  });

  // Portfolio data for optimization
  const [currentPortfolio, setCurrentPortfolio] = useState([
    { symbol: 'RELIANCE', quantity: 100, current_price: 2500, target_allocation: 20 },
    { symbol: 'TCS', quantity: 50, current_price: 3500, target_allocation: 15 },
    { symbol: 'INFY', quantity: 75, current_price: 1500, target_allocation: 10 }
  ]);

  const refreshIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

  // Helper function to map market trend values
  const mapMarketTrend = (trend: string): 'bullish' | 'bearish' | 'sideways' => {
    switch (trend) {
      case 'up': return 'bullish';
      case 'down': return 'bearish';
      case 'sideways': return 'sideways';
      default: return 'sideways';
    }
  };

  // Fetch stock details (quote, analysis, company info) for a symbol
  const fetchStockDetails = useCallback(async (symbol: string) => {
    try {
      const [quoteResponse, analysisResponse, companyResponse] = await Promise.allSettled([
        api.getQuote(symbol),
        unifiedAiApi.analyzeStock({
          symbol,
          analysis_depth: 'QUICK'
        }),
        api.getStockDetails(symbol)
      ]);

      const quote = quoteResponse.status === 'fulfilled' ? quoteResponse.value : null;
      const analysis = analysisResponse.status === 'fulfilled' ? analysisResponse.value : null;
      const companyInfo = companyResponse.status === 'fulfilled' && companyResponse.value.success 
        ? companyResponse.value.data 
        : null;

      setStockDetails(prev => ({
        ...prev,
        [symbol]: { quote, analysis, companyInfo }
      }));
    } catch (err) {
      console.error(`Error fetching details for ${symbol}:`, err);
    }
  }, []);

  // Fetch data functions
  const fetchRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use Unified AI API for recommendations with user preferences
      const request: AIRecommendationsRequest = {
        limit: userPreferences.max_positions,
        min_confidence: userPreferences.min_confidence,
        sectors: userPreferences.preferred_sectors.length > 0 ? userPreferences.preferred_sectors : undefined,
        market_cap: userPreferences.market_cap_preference === 'small_cap' ? 'small' :
                   userPreferences.market_cap_preference === 'mid_cap' ? 'mid' : 'large',
        risk_tolerance: userPreferences.risk_tolerance
      };
      
      const result = await unifiedAiApi.getAIRecommendations(request);
      setRecommendations(result);
      
      // Fetch stock details (quote, analysis, company info) for each recommendation
      if (result.recommendations) {
        const symbols = result.recommendations.map(rec => rec.symbol);
        await Promise.all(symbols.map(symbol => fetchStockDetails(symbol)));
      }
      
      toast.success(`AI recommendations loaded for ${result.recommendations?.length || 0} stocks`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get stock recommendations';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [userPreferences, fetchStockDetails]);

  const fetchOptimalTiming = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await intelligentTradingApi.getOptimalTiming(selectedSymbol);
      setOptimalTiming(result);
      toast.success(`Optimal timing analysis completed for ${selectedSymbol}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get optimal timing';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol]);

  const fetchMarketIntelligence = useCallback(async () => {
    try {
      const result = await intelligentTradingApi.getMarketIntelligence();
      setMarketIntelligence(result);
    } catch (err) {
      console.error('Failed to fetch market intelligence:', err);
    }
  }, []);

  const fetchPortfolioOptimization = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: PortfolioOptimizationRequest = {
        current_portfolio: currentPortfolio,
        constraints: {
          max_positions: 20,
          max_sector_allocation: 30,
          max_single_stock_allocation: 15,
          min_liquidity_requirement: 1000000
        },
        objectives: {
          target_return: 12,
          max_risk_tolerance: 15,
          investment_horizon: userPreferences.investment_horizon,
          rebalancing_frequency: 'monthly'
        },
        market_conditions: marketIntelligence ? {
          expected_volatility: marketIntelligence?.market_overview?.volatility_level || 'medium',
          market_trend: mapMarketTrend(marketIntelligence?.market_overview?.market_trend || 'sideways'),
          sector_rotation: marketIntelligence?.ai_insights?.sector_rotation_signals || []
        } : {
          expected_volatility: 'medium',
          market_trend: 'sideways',
          sector_rotation: []
        }
      };
      
      const result = await intelligentTradingApi.optimizePortfolio(request);
      setPortfolioOptimization(result);
      toast.success('Portfolio optimization completed');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to optimize portfolio';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [currentPortfolio, userPreferences, marketIntelligence]);

  const fetchTradingSignals = useCallback(async () => {
    try {
      const result = await intelligentTradingApi.getTradingSignals();
      setTradingSignals(result);
      toast.success(`Trading signals loaded: ${result.signals.length} signals`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get trading signals';
      setError(errorMessage);
      toast.error(errorMessage);
    }
  }, []);

  // Auto-refresh for live data
  useEffect(() => {
    if (isLive) {
      refreshIntervalRef.current = setInterval(() => {
        fetchMarketIntelligence();
        fetchTradingSignals();
        if (activeTab === 'recommendations' && recommendations) {
          fetchRecommendations();
        }
      }, 120000); // Refresh every 2 minutes
    } else {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [isLive, activeTab, recommendations, fetchMarketIntelligence, fetchTradingSignals, fetchRecommendations]);

  // Initial data load
  useEffect(() => {
    fetchMarketIntelligence();
  }, [fetchMarketIntelligence]);

  // Auto-fetch data when tab changes
  useEffect(() => {
    if (activeTab === 'timing' && !optimalTiming) {
      fetchOptimalTiming();
    } else if (activeTab === 'signals' && !tradingSignals) {
      fetchTradingSignals();
    }
  }, [activeTab, optimalTiming, tradingSignals, fetchOptimalTiming, fetchTradingSignals]);

  // Tab configuration
  const tabs = [
    { id: 'recommendations', label: 'Recommendations', icon: LightBulbIcon },
    { id: 'timing', label: 'Optimal Timing', icon: ClockIcon },
    { id: 'intelligence', label: 'Market Intelligence', icon: ArrowTrendingUpIcon },
    { id: 'optimization', label: 'Portfolio Optimization', icon: AdjustmentsHorizontalIcon },
    { id: 'signals', label: 'Trading Signals', icon: SignalIcon }
  ] as const;

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <ErrorDisplay 
          message={error} 
          onRetry={() => {
            setError(null);
            if (activeTab === 'recommendations') fetchRecommendations();
            else if (activeTab === 'timing') fetchOptimalTiming();
            else if (activeTab === 'optimization') fetchPortfolioOptimization();
            else if (activeTab === 'signals') fetchTradingSignals();
          }}
          title="Intelligent Trading Error"
        />
      </div>
    );
  }

  return (
    <div className={cn("h-full flex flex-col bg-gray-50 dark:bg-gray-900", className)}>
      {/* Header */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Symbol and Controls */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
                  className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter symbol"
                />
              </div>
            </div>

            {/* Live Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsLive(!isLive)}
                className={cn(
                  "flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors",
                  isLive
                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                )}
              >
                {isLive ? <PlayIcon className="h-4 w-4" /> : <PauseIcon className="h-4 w-4" />}
                <span>{isLive ? 'Live' : 'Paused'}</span>
              </button>

              <button
                onClick={() => {
                  if (activeTab === 'recommendations') fetchRecommendations();
                  else if (activeTab === 'timing') fetchOptimalTiming();
                  else if (activeTab === 'intelligence') fetchMarketIntelligence();
                  else if (activeTab === 'optimization') fetchPortfolioOptimization();
                  else if (activeTab === 'signals') fetchTradingSignals();
                }}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-4">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors",
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600 dark:text-blue-400"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        {loading && (
          <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            {/* User Preferences */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Investment Preferences</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Risk Tolerance
                  </label>
                  <select
                    value={userPreferences.risk_tolerance}
                    onChange={(e) => setUserPreferences(prev => ({...prev, risk_tolerance: e.target.value as 'low' | 'medium' | 'high'}))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Investment Horizon
                  </label>
                  <select
                    value={userPreferences.investment_horizon}
                    onChange={(e) => setUserPreferences(prev => ({...prev, investment_horizon: e.target.value as 'short_term' | 'medium_term' | 'long_term'}))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="short_term">Short Term (1-6 months)</option>
                    <option value="medium_term">Medium Term (6-24 months)</option>
                    <option value="long_term">Long Term (2+ years)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Market Cap Preference
                  </label>
                  <select
                    value={userPreferences.market_cap_preference}
                    onChange={(e) => setUserPreferences(prev => ({...prev, market_cap_preference: e.target.value as 'small_cap' | 'mid_cap' | 'large_cap'}))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="small_cap">Small Cap</option>
                    <option value="mid_cap">Mid Cap</option>
                    <option value="large_cap">Large Cap</option>
                  </select>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={fetchRecommendations}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Get AI Recommendations
                </button>
              </div>
            </div>

            {/* Recommendations Results */}
            {recommendations ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI Stock Recommendations</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {(recommendations.recommendations || []).map((rec, index) => {
                      const details = stockDetails[rec.symbol];
                      const quote = details?.quote;
                      const analysis = details?.analysis;
                      const companyInfo = details?.companyInfo;
                      const isExpanded = expandedResearch[rec.symbol] || false;
                      
                      return (
                        <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:shadow-lg transition-shadow">
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <h4 className="font-semibold text-gray-900 dark:text-white">{rec.symbol}</h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{rec.name}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-500">{rec.sector}</p>
                            </div>
                            <span className={cn(
                              "px-2 py-1 rounded-full text-xs font-medium",
                              rec.recommendation === 'BUY' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                              rec.recommendation === 'SELL' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                              "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                            )}>
                              {rec.recommendation}
                            </span>
                          </div>
                          
                          {/* Stock Price & Technical Indicators */}
                          <div className="space-y-2 text-sm mb-3">
                            {/* Current Price */}
                            {quote && (
                              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                                <div className="flex justify-between items-center mb-1">
                                  <span className="text-gray-600 dark:text-gray-400">Current Price:</span>
                                  <span className="font-bold text-lg text-gray-900 dark:text-white">₹{quote.last_price?.toFixed(2) || rec.current_price}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span className={quote.change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
                                    {quote.change >= 0 ? '+' : ''}{quote.change?.toFixed(2)} ({quote.change_percent?.toFixed(2)}%)
                                  </span>
                                  <span className="text-gray-500 dark:text-gray-400">
                                    Vol: {quote.volume ? (quote.volume / 1000000).toFixed(2) + 'M' : 'N/A'}
                                  </span>
                                </div>
                              </div>
                            )}
                            
                            {/* RSI & Volume Details */}
                            <div className="grid grid-cols-2 gap-2">
                              <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2">
                                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">RSI</div>
                                <div className="font-semibold text-gray-900 dark:text-white">
                                  {analysis?.analysis_result?.technical_analysis?.rsi?.toFixed(2) || 'N/A'}
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  {analysis?.analysis_result?.technical_analysis?.rsi 
                                    ? (analysis.analysis_result.technical_analysis.rsi > 70 ? 'Overbought' :
                                       analysis.analysis_result.technical_analysis.rsi < 30 ? 'Oversold' : 'Neutral')
                                    : ''}
                                </div>
                              </div>
                              <div className="bg-purple-50 dark:bg-purple-900/20 rounded p-2">
                                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Volume</div>
                                <div className="font-semibold text-gray-900 dark:text-white">
                                  {quote?.volume ? (quote.volume / 1000000).toFixed(2) + 'M' : 'N/A'}
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  {analysis?.analysis_result?.volume_analysis?.volume_trend || 'N/A'}
                                </div>
                              </div>
                            </div>
                            
                            {/* Recommendation Details */}
                            <div className="space-y-1 pt-2 border-t border-gray-200 dark:border-gray-600">
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                                <span className="font-medium text-gray-900 dark:text-white">{rec?.confidence ?? 0}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Price Target:</span>
                                <span className="font-medium text-gray-900 dark:text-white">₹{rec.price_target?.toFixed(2)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Stop Loss:</span>
                                <span className="font-medium text-gray-900 dark:text-white">₹{rec.stop_loss?.toFixed(2)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Risk Level:</span>
                                <span className="font-medium text-gray-900 dark:text-white capitalize">{rec.risk_level?.toLowerCase() || 'medium'}</span>
                              </div>
                            </div>
                          </div>
                          
                            {/* Reasoning */}
                          <p className="mt-3 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                            {rec.reasoning}
                          </p>
                          
                          {/* Buy/Sell Actions */}
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600" onClick={(e) => e.stopPropagation()}>
                            <BuySellButton
                              symbol={rec.symbol}
                              currentPrice={quote?.last_price || rec.current_price || 0}
                              size="sm"
                            />
                          </div>
                          
                          {/* Company Research Details - Dropdown */}
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                            <button
                              onClick={() => setExpandedResearch(prev => ({
                                ...prev,
                                [rec.symbol]: !prev[rec.symbol]
                              }))}
                              className="w-full flex items-center justify-between text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                            >
                              <span>Company Research Details</span>
                              <span className={cn(
                                "transition-transform",
                                isExpanded ? "rotate-180" : ""
                              )}>
                                <ChevronDownIcon className="h-4 w-4" />
                              </span>
                            </button>
                            
                            {isExpanded && (
                              <div className="mt-3 space-y-3 text-sm">
                                {/* Company Information */}
                                {companyInfo && (
                                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                                    <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Company Information</h5>
                                    <div className="space-y-1 text-xs">
                                      {companyInfo.company_name && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Company:</span>
                                          <span className="text-gray-900 dark:text-white">{companyInfo.company_name}</span>
                                        </div>
                                      )}
                                      {companyInfo.industry && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Industry:</span>
                                          <span className="text-gray-900 dark:text-white">{companyInfo.industry}</span>
                                        </div>
                                      )}
                                      {companyInfo.market_cap && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Market Cap:</span>
                                          <span className="text-gray-900 dark:text-white">₹{(companyInfo.market_cap / 10000000).toFixed(2)} Cr</span>
                                        </div>
                                      )}
                                      {companyInfo.pe_ratio && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">P/E Ratio:</span>
                                          <span className="text-gray-900 dark:text-white">{companyInfo.pe_ratio}</span>
                                        </div>
                                      )}
                                      {companyInfo.book_value && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Book Value:</span>
                                          <span className="text-gray-900 dark:text-white">₹{companyInfo.book_value}</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Technical Analysis Details */}
                                {analysis?.analysis_result?.technical_analysis && (
                                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                                    <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Technical Indicators</h5>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                      {analysis.analysis_result.technical_analysis.sma_20 && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">SMA 20:</span>
                                          <span className="text-gray-900 dark:text-white">₹{analysis.analysis_result.technical_analysis.sma_20.toFixed(2)}</span>
                                        </div>
                                      )}
                                      {analysis.analysis_result.technical_analysis.sma_50 && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">SMA 50:</span>
                                          <span className="text-gray-900 dark:text-white">₹{analysis.analysis_result.technical_analysis.sma_50.toFixed(2)}</span>
                                        </div>
                                      )}
                                      {analysis.analysis_result.technical_analysis.macd && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">MACD:</span>
                                          <span className="text-gray-900 dark:text-white">{analysis.analysis_result.technical_analysis.macd}</span>
                                        </div>
                                      )}
                                      {analysis.analysis_result.technical_analysis.signal && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Signal:</span>
                                          <span className="text-gray-900 dark:text-white">{analysis.analysis_result.technical_analysis.signal}</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Volume Analysis */}
                                {analysis?.analysis_result?.volume_analysis && (
                                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                                    <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Volume Analysis</h5>
                                    <div className="space-y-1 text-xs">
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Trend:</span>
                                        <span className="text-gray-900 dark:text-white">{analysis.analysis_result.volume_analysis.volume_trend || 'N/A'}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Signal:</span>
                                        <span className="text-gray-900 dark:text-white">{analysis.analysis_result.volume_analysis.volume_signal || 'N/A'}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Strength:</span>
                                        <span className="text-gray-900 dark:text-white">{analysis.analysis_result.volume_analysis.volume_strength || 'N/A'}</span>
                                      </div>
                                      {analysis.analysis_result.volume_analysis.volume_ratio && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Volume Ratio:</span>
                                          <span className="text-gray-900 dark:text-white">{analysis.analysis_result.volume_analysis.volume_ratio.toFixed(2)}</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Sentiment Analysis */}
                                {analysis?.analysis_result?.sentiment_analysis && (
                                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                                    <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Sentiment Analysis</h5>
                                    <div className="space-y-1 text-xs">
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">News Sentiment:</span>
                                        <span className="text-gray-900 dark:text-white capitalize">{analysis.analysis_result.sentiment_analysis.news_sentiment || 'N/A'}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Overall Sentiment:</span>
                                        <span className="text-gray-900 dark:text-white capitalize">{analysis.analysis_result.sentiment_analysis.overall_sentiment || 'N/A'}</span>
                                      </div>
                                      {analysis.analysis_result.sentiment_analysis.sentiment_score && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Sentiment Score:</span>
                                          <span className="text-gray-900 dark:text-white">{(analysis.analysis_result.sentiment_analysis.sentiment_score * 100).toFixed(1)}%</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Timing Recommendation */}
                                {rec.timing_recommendation && (
                                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                                    <h5 className="font-semibold text-gray-900 dark:text-white mb-2">Timing Recommendation</h5>
                                    <div className="space-y-1 text-xs">
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Action:</span>
                                        <span className="text-gray-900 dark:text-white">{rec.timing_recommendation.action}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Reason:</span>
                                        <span className="text-gray-900 dark:text-white">{rec.timing_recommendation.reason}</span>
                                      </div>
                                      {rec.timing_recommendation.next_opportunity && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600 dark:text-gray-400">Next Opportunity:</span>
                                          <span className="text-gray-900 dark:text-white">{rec.timing_recommendation.next_opportunity}</span>
                                        </div>
                                      )}
                                      <div className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">Time Horizon:</span>
                                        <span className="text-gray-900 dark:text-white">{rec.time_horizon}</span>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Market Insights */}
                {recommendations.market_conditions && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Market Insights</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">Market Conditions</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Overall Sentiment:</span>
                            <span className="font-medium text-gray-900 dark:text-white capitalize">{recommendations.market_conditions?.overall_sentiment ?? 'neutral'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Market Trend:</span>
                            <span className="font-medium text-gray-900 dark:text-white capitalize">{recommendations.market_conditions?.market_trend ?? 'sideways'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Volatility:</span>
                            <span className="font-medium text-gray-900 dark:text-white capitalize">{recommendations.market_conditions?.volatility_level ?? 'medium'}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">Sector Rotation</h4>
                        <ul className="space-y-1">
                          {(recommendations.market_conditions?.sector_rotation ?? []).length > 0 ? (
                            (recommendations.market_conditions?.sector_rotation || []).map((sector, index) => (
                              <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {sector}</li>
                            ))
                          ) : (
                            <li className="text-sm text-gray-500 dark:text-gray-500">No sector rotation signals</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12">
                <LightBulbIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Recommendations Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Configure your preferences and get AI-powered stock recommendations</p>
                <button
                  onClick={fetchRecommendations}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Get Recommendations
                </button>
              </div>
            )}
          </div>
        )}

        {/* Optimal Timing Tab */}
        {activeTab === 'timing' && (
          <div className="space-y-6">
            {/* Symbol Selector and Action Buttons */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-4">
                <div className="flex-1 w-full sm:w-auto">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Select Stock Symbol
                  </label>
                  <div className="w-full sm:w-80">
                    <StockSelector
                      value={selectedSymbol}
                      onChange={(symbol) => setSelectedSymbol(symbol)}
                      showNavigateButton={false}
                      className="w-full"
                    />
                  </div>
                </div>
                <div className="flex gap-2 mt-6 sm:mt-0">
                  <button
                    onClick={fetchOptimalTiming}
                    disabled={loading || !selectedSymbol}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <ClockIcon className="h-4 w-4" />
                    {loading ? 'Analyzing...' : 'Analyze Timing'}
                  </button>
                </div>
              </div>
            </div>

            {optimalTiming ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Optimal Timing Analysis - {optimalTiming.symbol || selectedSymbol}
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Optimal Entry</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Price Range:</span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            ₹{optimalTiming?.optimal_entry?.price_range?.min ?? '-'} - ₹{optimalTiming?.optimal_entry?.price_range?.max ?? '-'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{optimalTiming?.optimal_entry?.confidence ?? 0}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Timeframe:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{optimalTiming?.optimal_entry?.timeframe ?? ''}</span>
                        </div>
                      </div>
                      <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">{optimalTiming?.optimal_entry?.reasoning ?? ''}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Optimal Exit</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Price Range:</span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            ₹{optimalTiming?.optimal_exit?.price_range?.min ?? '-'} - ₹{optimalTiming?.optimal_exit?.price_range?.max ?? '-'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{optimalTiming?.optimal_exit?.confidence ?? 0}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Timeframe:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{optimalTiming?.optimal_exit?.timeframe ?? ''}</span>
                        </div>
                      </div>
                      <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">{optimalTiming?.optimal_exit?.reasoning ?? ''}</p>
                    </div>
                  </div>
                </div>

                {/* Market Phase Analysis */}
                {optimalTiming?.market_timing && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Market Phase Analysis</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                        <div className="text-sm text-gray-600 dark:text-gray-400">Current Phase</div>
                        <div className="font-semibold text-gray-900 dark:text-white capitalize">
                          {optimalTiming.market_timing?.current_phase || 'N/A'}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                        <div className="text-sm text-gray-600 dark:text-gray-400">Next Phase Probability</div>
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {optimalTiming.market_timing?.next_phase_probability ?? 0}%
                        </div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                        <div className="text-sm text-gray-600 dark:text-gray-400">Phase Duration</div>
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {optimalTiming.market_timing?.phase_duration_estimate || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Technical Signals */}
                {optimalTiming?.technical_signals && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Technical Signals</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Entry Signals</h4>
                        <ul className="space-y-1">
                          {(optimalTiming.technical_signals?.entry_signals || []).length > 0 ? (
                            optimalTiming.technical_signals.entry_signals.map((signal: string, index: number) => (
                              <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {signal}</li>
                            ))
                          ) : (
                            <li className="text-sm text-gray-500 dark:text-gray-500">No entry signals</li>
                          )}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Exit Signals</h4>
                        <ul className="space-y-1">
                          {(optimalTiming.technical_signals?.exit_signals || []).length > 0 ? (
                            optimalTiming.technical_signals.exit_signals.map((signal: string, index: number) => (
                              <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {signal}</li>
                            ))
                          ) : (
                            <li className="text-sm text-gray-500 dark:text-gray-500">No exit signals</li>
                          )}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Risk Signals</h4>
                        <ul className="space-y-1">
                          {(optimalTiming.technical_signals?.risk_signals || []).length > 0 ? (
                            optimalTiming.technical_signals.risk_signals.map((signal: string, index: number) => (
                              <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {signal}</li>
                            ))
                          ) : (
                            <li className="text-sm text-gray-500 dark:text-gray-500">No risk signals</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12">
                <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Timing Analysis Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get optimal entry/exit timing for {selectedSymbol}</p>
                <button
                  onClick={fetchOptimalTiming}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Analyze Timing
                </button>
              </div>
            )}
          </div>
        )}

        {/* Market Intelligence Tab */}
        {activeTab === 'intelligence' && (
          <div className="space-y-6">
            {marketIntelligence ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Market Intelligence</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Market Status</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{marketIntelligence.market_overview?.current_status ?? 'unknown'}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Overall Sentiment</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{marketIntelligence.market_overview?.overall_sentiment ?? 'neutral'}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Market Trend</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{marketIntelligence.market_overview?.market_trend ?? 'sideways'}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Volatility</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{marketIntelligence.market_overview?.volatility_level ?? 'medium'}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">AI Market Outlook</h4>
                      <p className="text-gray-700 dark:text-gray-300 mb-4">{marketIntelligence.ai_insights?.market_outlook ?? ''}</p>
                      
                      <div>
                        <h5 className="font-medium text-gray-900 dark:text-white mb-2">Key Themes</h5>
                        <ul className="space-y-1">
                          {(marketIntelligence.ai_insights?.key_themes ?? []).map((theme, index) => (
                            <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {theme}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Trading Opportunities</h4>
                      <div className="space-y-2">
                        {(marketIntelligence.trading_opportunities || []).map((opp, index) => (
                          <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900 dark:text-white">{opp.symbol}</span>
                              <span className={cn(
                                "px-2 py-1 rounded-full text-xs font-medium",
                                opp.confidence > 80 ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                                opp.confidence > 60 ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                                "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                              )}>
                                {opp.confidence}%
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{opp.opportunity}</p>
                            <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                              {opp.type} • {opp.timeframe} • {opp.risk_level} risk
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <ArrowTrendingUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Market Intelligence Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get AI-powered market insights and opportunities</p>
                <button
                  onClick={fetchMarketIntelligence}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Get Market Intelligence
                </button>
              </div>
            )}
          </div>
        )}

        {/* Portfolio Optimization Tab */}
        {activeTab === 'optimization' && (
          <div className="space-y-6">
            {portfolioOptimization ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Portfolio Optimization Results</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Expected Return</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{portfolioOptimization.portfolio_metrics.expected_return}%</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Expected Volatility</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{portfolioOptimization.portfolio_metrics.expected_volatility}%</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{portfolioOptimization.portfolio_metrics.sharpe_ratio}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{portfolioOptimization.portfolio_metrics.max_drawdown}%</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Optimized Portfolio</h4>
                      <div className="space-y-2">
                        {(portfolioOptimization.optimized_portfolio || []).map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div>
                              <span className="font-medium text-gray-900 dark:text-white">{item.symbol}</span>
                              <span className={cn(
                                "ml-2 px-2 py-1 rounded-full text-xs font-medium",
                                item.action === 'BUY' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                                item.action === 'SELL' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                                "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                              )}>
                                {item.action}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {item.recommended_allocation}%
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Rebalancing Recommendations</h4>
                      <div className="space-y-2">
                        {(portfolioOptimization.rebalancing_recommendations?.priority_trades || []).map((trade, index) => (
                          <div key={index} className="p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-gray-900 dark:text-white">{trade.symbol}</span>
                              <span className={cn(
                                "px-2 py-1 rounded-full text-xs font-medium",
                                trade.priority === 'high' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                                trade.priority === 'medium' ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                                "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                              )}>
                                {trade.priority}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {trade.action} {trade.quantity} shares
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                              {trade.reasoning}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <AdjustmentsHorizontalIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Portfolio Optimization Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Optimize your portfolio allocation</p>
                <button
                  onClick={fetchPortfolioOptimization}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Optimize Portfolio
                </button>
              </div>
            )}
          </div>
        )}

        {/* Trading Signals Tab */}
        {activeTab === 'signals' && (
          <div className="space-y-6">
            {tradingSignals ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Trading Signals</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {(tradingSignals.signals || []).map((signal, index) => {
                      const techIndicators = signal.technical_indicators || {};
                      return (
                        <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:shadow-lg transition-shadow">
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <h4 className="font-semibold text-gray-900 dark:text-white">{signal.symbol}</h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{signal?.timeframe ?? '1D'}</p>
                            </div>
                            <span className={cn(
                              "px-2 py-1 rounded-full text-xs font-medium",
                              signal.signal_type === 'BUY' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                              signal.signal_type === 'SELL' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                              "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                            )}>
                              {signal.signal_type}
                            </span>
                          </div>
                          
                          {/* Real Price & Technical Indicators */}
                          <div className="space-y-2 text-sm mb-3">
                            {/* Current Price */}
                            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-gray-600 dark:text-gray-400">Current Price:</span>
                                <span className="font-bold text-lg text-gray-900 dark:text-white">₹{signal.price?.toFixed(2) || 'N/A'}</span>
                              </div>
                              {techIndicators.change_percent !== undefined && (
                                <div className="text-xs">
                                  <span className={techIndicators.change_percent >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
                                    {techIndicators.change_percent >= 0 ? '+' : ''}{techIndicators.change_percent?.toFixed(2)}%
                                  </span>
                                </div>
                              )}
                            </div>
                            
                            {/* RSI & Volume Details */}
                            <div className="grid grid-cols-2 gap-2">
                              <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2">
                                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">RSI</div>
                                <div className="font-semibold text-gray-900 dark:text-white">
                                  {techIndicators.rsi?.toFixed(2) || 'N/A'}
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  {techIndicators.rsi 
                                    ? (techIndicators.rsi > 70 ? 'Overbought' :
                                       techIndicators.rsi < 30 ? 'Oversold' : 'Neutral')
                                    : ''}
                                </div>
                              </div>
                              <div className="bg-purple-50 dark:bg-purple-900/20 rounded p-2">
                                <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Volume</div>
                                <div className="font-semibold text-gray-900 dark:text-white">
                                  {techIndicators.volume ? (techIndicators.volume / 1000000).toFixed(2) + 'M' : 'N/A'}
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  Ratio: {techIndicators.volume_ratio?.toFixed(2) || 'N/A'}
                                </div>
                              </div>
                            </div>
                            
                            {/* Signal Details */}
                            <div className="space-y-1 pt-2 border-t border-gray-200 dark:border-gray-600">
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                                <span className="font-medium text-gray-900 dark:text-white">{signal.confidence}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Strength:</span>
                                <span className="font-medium text-gray-900 dark:text-white capitalize">{signal.strength}</span>
                              </div>
                              {signal.target && (
                                <div className="flex justify-between">
                                  <span className="text-gray-600 dark:text-gray-400">Target:</span>
                                  <span className="font-medium text-gray-900 dark:text-white">₹{signal.target.toFixed(2)}</span>
                                </div>
                              )}
                              {signal.stop_loss && (
                                <div className="flex justify-between">
                                  <span className="text-gray-600 dark:text-gray-400">Stop Loss:</span>
                                  <span className="font-medium text-gray-900 dark:text-white">₹{signal.stop_loss.toFixed(2)}</span>
                                </div>
                              )}
                            </div>
                            
                            {/* Technical Indicators Summary */}
                            {techIndicators.sma20 && techIndicators.sma50 && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-600">
                                <div>SMA 20: ₹{techIndicators.sma20.toFixed(2)}</div>
                                <div>SMA 50: ₹{techIndicators.sma50.toFixed(2)}</div>
                                {techIndicators.macd !== undefined && (
                                  <div>MACD: {techIndicators.macd.toFixed(2)}</div>
                                )}
                              </div>
                            )}
                          </div>
                          
                          <p className="mt-3 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                            {signal.reasoning}
                          </p>
                          
                          {/* Redirect to Comprehensive Trading Pro */}
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                            <button
                              onClick={() => navigate(`/comprehensive-trading-pro?symbol=${signal.symbol}`)}
                              className="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                            >
                              <ChartBarIcon className="h-4 w-4" />
                              Analyze on Chart
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <SignalIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Trading Signals Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get AI-powered trading signals</p>
                <button
                  onClick={fetchTradingSignals}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Get Trading Signals
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligentTradingInterface;
