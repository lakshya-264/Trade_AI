/**
 * Unified AI Analysis Panel - Comprehensive AI Dashboard
 * Integrates all backend Unified AI endpoints for comprehensive analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  CpuChipIcon,
  ChartBarIcon,
  LightBulbIcon,
  BellIcon,
  Cog6ToothIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  PlayIcon,
  PauseIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  ShareIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import { toast } from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import ErrorDisplay from './ErrorDisplay';
import UnifiedAIWatchlist from './UnifiedAIWatchlist';
import MultiTimeframeComparison from './MultiTimeframeComparison';
import StockSelector from './StockSelector';
import FeedbackButton from './FeedbackButton';
import MLSignalsCard from './MLSignalsCard';
import SelfLearningIndicators from './SelfLearningIndicators';
import { userLearningApi } from '../services/userLearningApi';
import { useAuth } from '../context/AuthContext';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, Time } from 'lightweight-charts';
import candleDataApi from '../services/candleDataApi';
import refreshService from '../services/RefreshService';
import { deduplicateAndSortCandlestickData } from '../utils/chartDataUtils';
import TechnicalIndicators from './TechnicalIndicators';
import MLSignalsOverlay from './MLSignalsOverlay';

// Import Unified AI API service
import unifiedAiApi, {
  UnifiedAnalysisRequest,
  UnifiedAnalysisResponse,
  BatchAnalysisRequest,
  BatchAnalysisResponse,
  AIStatusResponse,
  AIRecommendationsRequest,
  AIRecommendationsResponse,
  StockInsightsRequest,
  StockInsightsResponse,
  MarketOverviewResponse,
  ChatRequest,
  ChatResponse,
  NotificationPreferences
} from '../services/unifiedAiApi';

interface UnifiedAIAnalysisPanelProps {
  className?: string;
  initialSymbol?: string;
  onAnalysisUpdate?: (result: UnifiedAnalysisResponse | null) => void;
  activeTab?: TabType;
  onTabChange?: (tab: TabType) => void;
}

type TabType = 'analysis' | 'batch' | 'recommendations' | 'insights' | 'market' | 'chat' | 'notifications' | 'status';

const UnifiedAIAnalysisPanel: React.FC<UnifiedAIAnalysisPanelProps> = ({
  className = '',
  initialSymbol,
  activeTab: activeTabProp,
  onTabChange
}) => {
  // State management - use prop if provided, otherwise use internal state
  const [internalActiveTab, setInternalActiveTab] = useState<TabType>('analysis');
  const activeTab = activeTabProp ?? internalActiveTab;
  const setActiveTab = onTabChange ?? setInternalActiveTab;
  const [selectedSymbol, setSelectedSymbol] = useState(initialSymbol || 'RELIANCE');
  const [userQuery, setUserQuery] = useState('');
  const [analysisDepth, setAnalysisDepth] = useState<'QUICK' | 'STANDARD' | 'COMPREHENSIVE'>('COMPREHENSIVE');
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [analysisResult, setAnalysisResult] = useState<UnifiedAnalysisResponse | null>(null);
  const [batchAnalysisResult, setBatchAnalysisResult] = useState<BatchAnalysisResponse | null>(null);
  const [serviceStatus, setServiceStatus] = useState<AIStatusResponse | null>(null);
  const [recommendations, setRecommendations] = useState<AIRecommendationsResponse | null>(null);
  const [stockInsights, setStockInsights] = useState<StockInsightsResponse | null>(null);
  const [marketOverview, setMarketOverview] = useState<MarketOverviewResponse | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatResponse[]>([]);
  const [notificationPreferences, setNotificationPreferences] = useState<NotificationPreferences | null>(null);

  // UI states
  const [batchSymbols, setBatchSymbols] = useState<string[]>(['RELIANCE', 'TCS', 'INFY']);
  const [chatMessage, setChatMessage] = useState('');
  const [chatSessionId, setChatSessionId] = useState<string>('');
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const { user } = useAuth();

  // Advanced Chart State (similar to Comprehensive Trading Pro)
  const [chartTimeframe, setChartTimeframe] = useState('1D');
  const [chartPeriod, setChartPeriod] = useState('1y');
  const [chartData, setChartData] = useState<any>(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [showChartIndicators, setShowChartIndicators] = useState(true);
  const [showChartMLSignals, setShowChartMLSignals] = useState(true);
  
  // Chart refs
  const advancedChartContainerRef = React.useRef<HTMLDivElement>(null);
  const advancedChartRef = React.useRef<IChartApi | null>(null);
  const candlestickSeriesRef = React.useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ma5SeriesRef = React.useRef<ISeriesApi<'Line'> | null>(null);
  const ma10SeriesRef = React.useRef<ISeriesApi<'Line'> | null>(null);
  const ma30SeriesRef = React.useRef<ISeriesApi<'Line'> | null>(null);

  const refreshIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

  // Fetch data functions
  const fetchAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: UnifiedAnalysisRequest = {
        symbol: selectedSymbol,
        user_query: userQuery || undefined,
        analysis_depth: analysisDepth,
        include_charts: true,
        include_news: true
      };
      
      const result = await unifiedAiApi.analyzeStock(request);
      
      // Debug logging
      console.log('📊 Analysis Result:', result);
      console.log('📊 Analysis Result Keys:', Object.keys(result || {}));
      console.log('📊 Analysis Result Data:', result?.analysis_result);
      
      if (result) {
        setAnalysisResult(result);
        toast.success(`Analysis completed for ${selectedSymbol}`);
      } else {
        throw new Error('No data returned from analysis');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze stock';
      console.error('❌ Analysis Error:', err);
      setError(errorMessage);
      toast.error(errorMessage);
      setAnalysisResult(null);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, userQuery, analysisDepth]);

  const fetchBatchAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: BatchAnalysisRequest = {
        symbols: batchSymbols,
        analysis_depth: analysisDepth,
        user_query: userQuery || undefined
      };
      
      const result = await unifiedAiApi.batchAnalyzeStocks(request);
      setBatchAnalysisResult(result);
      toast.success(`Batch analysis completed for ${batchSymbols.length} symbols`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to batch analyze stocks';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [batchSymbols, analysisDepth, userQuery]);

  const fetchServiceStatus = useCallback(async () => {
    try {
      const result = await unifiedAiApi.getServiceStatus();
      setServiceStatus(result);
    } catch (err) {
      console.error('Failed to fetch service status:', err);
    }
  }, []);

  const fetchRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      const request: AIRecommendationsRequest = {
        limit: 10,
        min_confidence: 70,
        risk_tolerance: 'medium'
      };
      
      const result = await unifiedAiApi.getAIRecommendations(request);
      setRecommendations(result);
      toast.success('AI recommendations loaded');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch recommendations';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStockInsights = useCallback(async () => {
    try {
      setLoading(true);
      const request: StockInsightsRequest = {
        insight_type: 'comprehensive'
      };
      
      const result = await unifiedAiApi.getStockInsights(selectedSymbol, request);
      setStockInsights(result);
      toast.success(`Insights loaded for ${selectedSymbol}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch stock insights';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol]);

  const fetchMarketOverview = useCallback(async () => {
    try {
      const result = await unifiedAiApi.getMarketOverview();
      setMarketOverview(result);
    } catch (err) {
      console.error('Failed to fetch market overview:', err);
    }
  }, []);

  const fetchNotificationPreferences = useCallback(async () => {
    try {
      const result = await unifiedAiApi.getNotificationPreferences();
      setNotificationPreferences(result);
    } catch (err) {
      console.error('Failed to fetch notification preferences:', err);
    }
  }, []);

  // Chat functions
  const sendChatMessage = useCallback(async () => {
    if (!chatMessage.trim()) return;
    
    try {
      setLoading(true);
      // Extract stock symbol from message if mentioned, otherwise use selected symbol
      const symbolMatch = chatMessage.match(/\b([A-Z]{2,10})\b/);
      const contextSymbol = symbolMatch ? symbolMatch[1] : selectedSymbol;
      
      const request: ChatRequest = {
        message: chatMessage,
        session_id: chatSessionId || undefined,
        context_symbol: contextSymbol
      };
      
      const response = await unifiedAiApi.chatWithAI(request);
      
      if (!chatSessionId) {
        setChatSessionId(response.session_id);
      }
      
      setChatHistory(prev => [...prev, response]);
      setChatMessage('');
      toast.success('Message sent to AI');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [chatMessage, chatSessionId, selectedSymbol]);

  // Auto-refresh for live data with real-time updates (using centralized service)
  useEffect(() => {
    if (isLive) {
      // Immediate refresh on enable
      fetchServiceStatus();
      fetchMarketOverview();
      if (activeTab === 'analysis' && selectedSymbol) {
        fetchAnalysis();
      }
      
      // Register with centralized refresh service
      const refreshId = `unified-ai-panel-${activeTab}-${selectedSymbol}`;
      
      const refreshCallback = () => {
        fetchServiceStatus();
        fetchMarketOverview();
        if (activeTab === 'analysis' && selectedSymbol) {
          fetchAnalysis();
        }
        if (activeTab === 'recommendations') {
          fetchRecommendations();
        }
        if (activeTab === 'insights' && selectedSymbol) {
          fetchStockInsights();
        }
        if (activeTab === 'market') {
          fetchMarketOverview();
        }
      };
      
      refreshService.register(refreshId, refreshCallback, 30000, false);

    return () => {
        refreshService.clear(refreshId);
      };
    } else {
      // Clear refresh when disabled
      const refreshId = `unified-ai-panel-${activeTab}-${selectedSymbol}`;
      refreshService.clear(refreshId);
      }
  }, [isLive, activeTab, selectedSymbol, fetchServiceStatus, fetchMarketOverview, fetchAnalysis, fetchRecommendations, fetchStockInsights]);

  // Initial data load
  useEffect(() => {
    fetchServiceStatus();
    fetchMarketOverview();
    fetchNotificationPreferences();
    
    // Auto-fetch analysis when component mounts or symbol changes
    if (activeTab === 'analysis' && selectedSymbol) {
      fetchAnalysis();
    }
  }, [fetchServiceStatus, fetchMarketOverview, fetchNotificationPreferences, activeTab, selectedSymbol, fetchAnalysis]);

  const [showWatchlist, setShowWatchlist] = useState(false);

  // Update symbol when initialSymbol prop changes (from URL)
  useEffect(() => {
    if (initialSymbol && initialSymbol !== selectedSymbol) {
      setSelectedSymbol(initialSymbol);
      if (activeTab === 'analysis') {
        fetchAnalysis();
      }
    }
  }, [initialSymbol]);

  // Load advanced chart data
  const loadAdvancedChartData = useCallback(async () => {
    if (!selectedSymbol || !advancedChartContainerRef.current) return;
    
    setChartLoading(true);
    try {
      // Map timeframe to API format
      const timeframeMap: Record<string, string> = {
        '1h': '1h',
        '4h': '4h',
        '1D': '1d',
        '1W': '1wk',
        '1M': '1mo'
      };
      
      const interval = timeframeMap[chartTimeframe] || '1d';
      
      // Fetch candle data
      const response = await candleDataApi.getCandles(selectedSymbol, interval, chartPeriod);
      
      if (response.success && response.data && response.data.length > 0) {
        // Format candlestick data
        let candlestickData: CandlestickData[] = response.data.map((candle: any) => ({
          time: (candle.time as number) as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }));
        
        // Deduplicate and sort
        candlestickData = deduplicateAndSortCandlestickData(candlestickData, false);
        
        setChartData({ candles: candlestickData });
        
        // Initialize or update chart
        if (!advancedChartRef.current && advancedChartContainerRef.current) {
          advancedChartRef.current = createChart(advancedChartContainerRef.current, {
            width: advancedChartContainerRef.current.clientWidth,
            height: 600,
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
            },
            timeScale: {
              borderColor: '#2B2B43',
              timeVisible: true,
            },
          });
          
          // Add candlestick series
          candlestickSeriesRef.current = advancedChartRef.current.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
          });
          
          // Add moving averages
          ma5SeriesRef.current = advancedChartRef.current.addLineSeries({
            color: '#2962FF',
            lineWidth: 1,
            title: 'MA5',
          });
          
          ma10SeriesRef.current = advancedChartRef.current.addLineSeries({
            color: '#FF6D00',
            lineWidth: 1,
            title: 'MA10',
          });
          
          ma30SeriesRef.current = advancedChartRef.current.addLineSeries({
            color: '#9C27B0',
            lineWidth: 1,
            title: 'MA30',
          });
        }
        
        // Update chart data
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(candlestickData as any);
          
          // Calculate and add moving averages
          const calculateMA = (period: number): LineData[] => {
            const ma: LineData[] = [];
            for (let i = period - 1; i < candlestickData.length; i++) {
              const sum = candlestickData.slice(i - period + 1, i + 1).reduce((acc, c) => acc + c.close, 0);
              ma.push({
                time: candlestickData[i].time,
                value: sum / period,
              });
            }
            return ma;
          };
          
          if (ma5SeriesRef.current) ma5SeriesRef.current.setData(calculateMA(5) as any);
          if (ma10SeriesRef.current) ma10SeriesRef.current.setData(calculateMA(10) as any);
          if (ma30SeriesRef.current) ma30SeriesRef.current.setData(calculateMA(30) as any);
          
          // Fit content
          if (advancedChartRef.current) {
            advancedChartRef.current.timeScale().fitContent();
          }
        }
      }
    } catch (error) {
      console.error('Error loading advanced chart data:', error);
      toast.error('Failed to load chart data');
    } finally {
      setChartLoading(false);
    }
  }, [selectedSymbol, chartTimeframe, chartPeriod]);

  // Initialize advanced chart
  useEffect(() => {
    if (selectedSymbol) {
      loadAdvancedChartData();
    }
    
    // Handle resize
    const handleResize = () => {
      if (advancedChartContainerRef.current && advancedChartRef.current) {
        advancedChartRef.current.applyOptions({
          width: advancedChartContainerRef.current.clientWidth
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      // Cleanup chart
      if (advancedChartRef.current) {
        advancedChartRef.current.remove();
        advancedChartRef.current = null;
        candlestickSeriesRef.current = null;
        ma5SeriesRef.current = null;
        ma10SeriesRef.current = null;
        ma30SeriesRef.current = null;
      }
    };
  }, [selectedSymbol, chartTimeframe, chartPeriod, loadAdvancedChartData]);

  // Tab configuration
  const tabs = [
    { id: 'analysis', label: 'Analysis', icon: ChartBarIcon },
    { id: 'batch', label: 'Batch Analysis', icon: CpuChipIcon },
    { id: 'recommendations', label: 'Recommendations', icon: LightBulbIcon },
    { id: 'insights', label: 'Insights', icon: EyeIcon },
    { id: 'market', label: 'Market Overview', icon: ArrowTrendingUpIcon },
    { id: 'chat', label: 'AI Chat', icon: BellIcon },
    { id: 'notifications', label: 'Notifications', icon: Cog6ToothIcon },
    { id: 'status', label: 'Status', icon: CheckCircleIcon }
  ] as const;

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <ErrorDisplay 
          message={error} 
          onRetry={() => {
            setError(null);
            if (activeTab === 'analysis') fetchAnalysis();
            else if (activeTab === 'batch') fetchBatchAnalysis();
            else if (activeTab === 'recommendations') fetchRecommendations();
            else if (activeTab === 'insights') fetchStockInsights();
          }}
          title="Unified AI Analysis Error"
        />
      </div>
    );
  }

  return (
    <div className={cn("h-full flex flex-col bg-gray-50 dark:bg-gray-900", className)}>
      {/* Header */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            {/* Symbol and Controls */}
            <div className="flex items-center space-x-3">
              <div className="w-64">
                <StockSelector
                  value={selectedSymbol}
                  onChange={(symbol) => {
                    setSelectedSymbol(symbol);
                    if (activeTab === 'analysis') {
                      fetchAnalysis();
                    }
                  }}
                  showNavigateButton={false}
                />
              </div>
              
              <select
                value={analysisDepth}
                onChange={(e) => setAnalysisDepth(e.target.value as 'QUICK' | 'STANDARD' | 'COMPREHENSIVE')}
                className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="QUICK">Quick</option>
                <option value="STANDARD">Standard</option>
                <option value="COMPREHENSIVE">Comprehensive</option>
              </select>

              <button
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                className={cn(
                  "px-3 py-1.5 text-sm rounded-lg transition-colors",
                  showAdvancedOptions
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                )}
              >
                Options
              </button>
            </div>

            {/* Live Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsLive(!isLive)}
                className={cn(
                  "flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
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
                  if (activeTab === 'analysis') fetchAnalysis();
                  else if (activeTab === 'batch') fetchBatchAnalysis();
                  else if (activeTab === 'recommendations') fetchRecommendations();
                  else if (activeTab === 'insights') fetchStockInsights();
                }}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                title="Refresh"
              >
                <ArrowPathIcon className="h-5 w-5" />
              </button>

              <button
                onClick={() => setShowWatchlist(!showWatchlist)}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  showWatchlist
                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
                title="Watchlist"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Advanced Options */}
          {showAdvancedOptions && (
            <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    User Query
                  </label>
                  <input
                    type="text"
                    value={userQuery}
                    onChange={(e) => setUserQuery(e.target.value)}
                    className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Ask AI about this stock..."
                  />
                </div>
                
                {activeTab === 'batch' && (
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Batch Symbols (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={batchSymbols.join(', ')}
                      onChange={(e) => setBatchSymbols(e.target.value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean))}
                      className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="RELIANCE, TCS, INFY"
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Tabs - Only show if not controlled by parent */}
        {!onTabChange && (
          <div className="px-4 border-t border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-1 overflow-x-auto">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      "flex items-center space-x-2 py-2.5 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap",
                      activeTab === tab.id
                        ? "border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20"
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
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4 relative">
        {/* Watchlist Sidebar */}
        {showWatchlist && (
          <div className="absolute top-4 right-4 w-80 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700">
            <UnifiedAIWatchlist
              onSymbolSelect={(symbol) => {
                setSelectedSymbol(symbol);
                setShowWatchlist(false);
                if (activeTab === 'analysis') {
                  fetchAnalysis();
                }
              }}
              selectedSymbol={selectedSymbol}
            />
          </div>
        )}

        {loading && (
          <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Analysis Tab */}
        {activeTab === 'analysis' && (
          <div className="h-full overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center p-8">
                <LoadingSpinner size="lg" />
                <span className="ml-4 text-gray-600 dark:text-gray-400">Analyzing {selectedSymbol}...</span>
              </div>
            )}
            {!loading && analysisResult ? (
              <div className="space-y-4">
                {/* Top Row: ML Signals and Self-Learning */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* ML Signals Card */}
                  <MLSignalsCard 
                    mlSignals={analysisResult.analysis_result?.ml_signals || null}
                    loading={loading}
                  />
                  
                  {/* Self-Learning Indicators */}
                  <SelfLearningIndicators 
                    symbol={selectedSymbol}
                    userId={user?.id}
                  />
                </div>

                {/* Debug Info (Development Only) */}
                {process.env.NODE_ENV === 'development' && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
                    <details className="text-xs">
                      <summary className="cursor-pointer font-semibold text-yellow-800 dark:text-yellow-200">
                        🔍 Debug: Analysis Result Structure
                      </summary>
                      <pre className="mt-2 p-2 bg-white dark:bg-gray-800 rounded overflow-auto max-h-64 text-xs">
                        {JSON.stringify(analysisResult, null, 2)}
                      </pre>
                    </details>
                  </div>
                )}

                {/* Analysis Details Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Left Column - Analysis Details */}
                  <div className="space-y-4">
                    {/* Recommendation Badge */}
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Recommendation</h3>
                        <div className="flex items-center space-x-2">
                          <span className={cn(
                            "px-3 py-1 rounded-full text-xs font-bold",
                            (analysisResult.recommendation || 'HOLD') === 'BUY' ? "bg-green-500 text-white" :
                            (analysisResult.recommendation || 'HOLD') === 'SELL' ? "bg-red-500 text-white" :
                            "bg-yellow-500 text-white"
                          )}>
                            {analysisResult.recommendation || 'HOLD'}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {(analysisResult.confidence_score || 0).toFixed(1)}% confidence
                          </span>
                        </div>
                      </div>
                    </div>

                  {/* Quick Stats Card */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Quick Stats</h3>
                    <div className="space-y-2">
                      {!!((analysisResult as any).current_price ?? (analysisResult as any)?.analysis_result?.quote?.last_price) && (
                        <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Current Price</span>
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">
                            ₹{((analysisResult as any).current_price ?? (analysisResult as any)?.analysis_result?.quote?.last_price) as number}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                        <span className="text-xs text-gray-600 dark:text-gray-400">Risk Level</span>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{analysisResult.risk_level || 'MEDIUM'}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                        <span className="text-xs text-gray-600 dark:text-gray-400">Processing Time</span>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{analysisResult.processing_time_ms || 0}ms</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                        <span className="text-xs text-gray-600 dark:text-gray-400">Analysis Time</span>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">
                          {analysisResult.analysis_timestamp 
                            ? new Date(analysisResult.analysis_timestamp).toLocaleTimeString()
                            : new Date().toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Trade Plan */}
                  {!!(analysisResult.entry_price ?? analysisResult.exit_price ?? analysisResult.price_target ?? analysisResult.stop_loss ?? analysisResult.holding_period) && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Trade Plan</h3>
                      <div className="space-y-2">
                        {!!(analysisResult.entry_price ?? (analysisResult as any).current_price ?? (analysisResult as any)?.analysis_result?.quote?.last_price) && (
                          <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Entry Price</span>
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              ₹{(
                                (analysisResult.entry_price ??
                                  (analysisResult as any).current_price ??
                                  (analysisResult as any)?.analysis_result?.quote?.last_price) as number
                              )}
                            </span>
                          </div>
                        )}

                        {!!(analysisResult.exit_price ?? analysisResult.price_target) && (
                          <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Exit / Target</span>
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              ₹{((analysisResult.exit_price ?? analysisResult.price_target) as number)}
                            </span>
                          </div>
                        )}

                        {!!analysisResult.stop_loss && (
                          <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Stop Loss</span>
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">₹{analysisResult.stop_loss}</span>
                          </div>
                        )}

                        {!!analysisResult.holding_period && (
                          <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Holding Period</span>
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              {analysisResult.holding_period}
                              {!!(analysisResult.holding_days_min != null && analysisResult.holding_days_max != null) && (
                                <span className="text-xs text-gray-500 dark:text-gray-400"> ({analysisResult.holding_days_min}-{analysisResult.holding_days_max} days)</span>
                              )}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* AI Insights Card */}
                  {analysisResult.analysis_result?.ai_reasoning && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">AI Reasoning</h3>
                      <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                        {analysisResult.analysis_result.ai_reasoning || 'No reasoning available'}
                      </p>
                    </div>
                  )}

                  {/* Natural Language Explanation */}
                  {analysisResult.analysis_result?.natural_language_explanation && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Explanation</h3>
                      <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                        {analysisResult.analysis_result.natural_language_explanation || 'No explanation available'}
                      </p>
                    </div>
                  )}

                  {/* Technical Analysis */}
                  {analysisResult.analysis_result?.technical_analysis && 
                   Object.keys(analysisResult.analysis_result.technical_analysis).length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Technical Indicators</h3>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(analysisResult.analysis_result.technical_analysis)
                          .filter(([_, value]) => value !== null && value !== undefined && value !== '')
                          .slice(0, 6)
                          .map(([key, value]) => (
                            <div key={key} className="p-2 bg-gray-50 dark:bg-gray-700 rounded">
                              <div className="text-xs text-gray-600 dark:text-gray-400 capitalize truncate">{key.replace(/_/g, ' ')}</div>
                              <div className="text-xs font-semibold text-gray-900 dark:text-white truncate">{String(value)}</div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Sentiment Analysis */}
                  {analysisResult.analysis_result?.sentiment_analysis && 
                   Object.keys(analysisResult.analysis_result.sentiment_analysis).length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Sentiment</h3>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(analysisResult.analysis_result.sentiment_analysis)
                          .filter(([_, value]) => value !== null && value !== undefined && value !== '')
                          .map(([key, value]) => (
                            <div key={key} className="p-2 bg-gray-50 dark:bg-gray-700 rounded">
                              <div className="text-xs text-gray-600 dark:text-gray-400 capitalize truncate">{key.replace(/_/g, ' ')}</div>
                              <div className="text-xs font-semibold text-gray-900 dark:text-white truncate">{String(value)}</div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* ML Signals */}
                  {analysisResult.analysis_result.ml_signals && (
                    <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg shadow-lg border-2 border-blue-200 dark:border-blue-800 p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <CpuChipIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">ML Prediction</h3>
                        </div>
                        <FeedbackButton
                          entityType="prediction"
                          entityId={`prediction_${selectedSymbol}_${analysisResult.analysis_timestamp}`}
                          symbol={selectedSymbol}
                          showRating={true}
                        />
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Signal</span>
                          <span className={cn(
                            "px-3 py-1 rounded-full text-xs font-bold",
                            (analysisResult.analysis_result.ml_signals.prediction || analysisResult.recommendation) === 'BUY' 
                              ? "bg-green-500 text-white" 
                              : (analysisResult.analysis_result.ml_signals.prediction || analysisResult.recommendation) === 'SELL'
                              ? "bg-red-500 text-white"
                              : "bg-yellow-500 text-white"
                          )}>
                            {analysisResult.analysis_result.ml_signals.prediction || analysisResult.recommendation || 'HOLD'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                          <span className="text-xs text-gray-600 dark:text-gray-400">Confidence</span>
                          <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                            {analysisResult.analysis_result.ml_signals.confidence 
                              ? ((analysisResult.analysis_result.ml_signals.confidence * 100).toFixed(1))
                              : analysisResult.confidence_score.toFixed(1)}%
                          </span>
                        </div>
                        {analysisResult.price_target && (
                          <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Price Target</span>
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              ₹{analysisResult.price_target.toFixed(2)}
                            </span>
                          </div>
                        )}
                        {analysisResult.stop_loss && (
                          <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Stop Loss</span>
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              ₹{analysisResult.stop_loss.toFixed(2)}
                            </span>
                          </div>
                        )}
                        {analysisResult.analysis_result.ml_signals.model_performance && (
                          <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                            <span className="text-xs text-gray-600 dark:text-gray-400">Model Performance</span>
                            <span className="text-xs font-semibold text-gray-900 dark:text-white">
                              {analysisResult.analysis_result.ml_signals.model_performance}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Pattern Analysis */}
                  {analysisResult.analysis_result.pattern_analysis && 
                   analysisResult.analysis_result.pattern_analysis.candlestick_patterns && 
                   analysisResult.analysis_result.pattern_analysis.candlestick_patterns.length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Detected Patterns</h3>
                      <div className="space-y-1">
                        {analysisResult.analysis_result.pattern_analysis.candlestick_patterns.map((pattern, index) => (
                          <div key={index} className="flex items-center space-x-2 text-xs">
                            <CheckCircleIcon className="h-3 w-3 text-green-500 flex-shrink-0" />
                            <span className="text-gray-700 dark:text-gray-300 capitalize">{pattern}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Conversational Response */}
                  {analysisResult.analysis_result?.conversational_response && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">AI Summary</h3>
                      <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                        {analysisResult.analysis_result.conversational_response || 'No summary available'}
                      </p>
                    </div>
                  )}
                </div>

                {/* Right Column - Additional Analysis */}
                <div className="space-y-4">
                  {/* Multi-Timeframe Comparison */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Multi-Timeframe Analysis</h3>
                    <MultiTimeframeComparison
                      symbol={selectedSymbol}
                      onTimeframeSelect={(timeframe) => {
                        console.log('Selected timeframe:', timeframe);
                      }}
                    />
                  </div>
                </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center max-w-md">
                  <div className="mb-6">
                    <CpuChipIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Analysis Available</h3>
                  <p className="text-gray-500 dark:text-gray-400 mb-6">
                    Click "Analyze Stock" to get comprehensive AI analysis for {selectedSymbol}
                  </p>
                  <button
                    onClick={fetchAnalysis}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-lg"
                  >
                    Analyze Stock
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Batch Analysis Tab */}
        {activeTab === 'batch' && (
          <div className="space-y-6">
            {batchAnalysisResult ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Batch Analysis Results</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Total Symbols</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{batchAnalysisResult.total_symbols}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Successful</div>
                      <div className="font-semibold text-green-600">{batchAnalysisResult.successful_analyses}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Failed</div>
                      <div className="font-semibold text-red-600">{batchAnalysisResult.failed_analyses}</div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(batchAnalysisResult.batch_analysis).map(([symbol, analysis]) => (
                    <div key={symbol} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-gray-900 dark:text-white">{symbol}</h4>
                        <span className={cn(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          analysis.recommendation === 'BUY' ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                          analysis.recommendation === 'SELL' ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                          "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                        )}>
                          {analysis.recommendation}
                        </span>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{analysis.confidence_score}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Risk:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{analysis.risk_level}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Processing:</span>
                          <span className="font-medium text-gray-900 dark:text-white">{analysis.processing_time_ms}ms</span>
                        </div>
                      </div>
                      
                      <p className="mt-3 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                        {analysis.ai_reasoning}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <CpuChipIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Batch Analysis Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Analyze multiple symbols at once</p>
                <button
                  onClick={fetchBatchAnalysis}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Analyze Batch
                </button>
              </div>
            )}
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            {recommendations ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI Stock Recommendations</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {recommendations.recommendations.map((rec, index) => (
                      <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-gray-900 dark:text-white">{rec.symbol}</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{rec.name}</p>
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
                        
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Confidence:</span>
                            <span className="font-medium text-gray-900 dark:text-white">{rec.confidence}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Price Target:</span>
                            <span className="font-medium text-gray-900 dark:text-white">₹{rec.price_target}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Stop Loss:</span>
                            <span className="font-medium text-gray-900 dark:text-white">₹{rec.stop_loss}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600 dark:text-gray-400">Risk Level:</span>
                            <span className="font-medium text-gray-900 dark:text-white">{rec.risk_level}</span>
                          </div>
                        </div>
                        
                        <p className="mt-3 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                          {rec.reasoning}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <LightBulbIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Recommendations Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get AI-powered stock recommendations</p>
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

        {/* Insights Tab */}
        {activeTab === 'insights' && (
          <div className="space-y-6">
            {stockInsights ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Stock Insights - {stockInsights.symbol}
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-3">Key Insights</h4>
                    <ul className="space-y-2">
                      {stockInsights.key_insights.map((insight, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-3">Risk Assessment</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Risk Level:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">{stockInsights.risk_assessment.level}</span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">Risk Factors:</span>
                        <ul className="mt-1 space-y-1">
                          {stockInsights.risk_assessment.factors.map((factor, index) => (
                            <li key={index} className="text-xs text-gray-600 dark:text-gray-400">• {factor}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <EyeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Insights Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get deep insights for {selectedSymbol}</p>
                <button
                  onClick={fetchStockInsights}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Get Insights
                </button>
              </div>
            )}
          </div>
        )}

        {/* Market Overview Tab */}
        {activeTab === 'market' && (
          <div className="space-y-6">
            {marketOverview ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Market Overview</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Market Status</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{marketOverview.market_status}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Overall Sentiment</div>
                      <div className="font-semibold text-gray-900 dark:text-white capitalize">{marketOverview.overall_sentiment}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Fear & Greed Index</div>
                      <div className="font-semibold text-gray-900 dark:text-white">{marketOverview.market_sentiment.fear_greed_index}</div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-3">AI Market Outlook</h4>
                    <p className="text-gray-700 dark:text-gray-300 mb-4">{marketOverview.ai_insights.market_outlook}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-gray-900 dark:text-white mb-2">Key Themes</h5>
                        <ul className="space-y-1">
                          {marketOverview.ai_insights.key_themes.map((theme, index) => (
                            <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {theme}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-gray-900 dark:text-white mb-2">Opportunities</h5>
                        <ul className="space-y-1">
                          {marketOverview.ai_insights.opportunities.map((opportunity, index) => (
                            <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {opportunity}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <ArrowTrendingUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Market Data Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Get AI-powered market overview</p>
                <button
                  onClick={fetchMarketOverview}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Get Market Overview
                </button>
              </div>
            )}
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="h-full flex flex-col">
            <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">AI Chat Assistant</h3>
              
              {/* Chat Messages */}
              <div className="h-96 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-gray-500 dark:text-gray-400">
                    <BellIcon className="h-8 w-8 mx-auto mb-2" />
                    <p>Start a conversation with AI about any stock or trading topic</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chatHistory.map((message, index) => (
                      <div key={index} className="flex flex-col space-y-2">
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                          <p className="text-sm text-gray-700 dark:text-gray-300">{message.response}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Chat Input */}
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ask AI about any stock (e.g., 'What is the analysis for RELIANCE?' or 'Compare TCS and INFY')..."
                />
                <button
                  onClick={sendChatMessage}
                  disabled={!chatMessage.trim() || loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === 'notifications' && (
          <div className="space-y-6">
            {notificationPreferences ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notification Preferences</h3>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={notificationPreferences.email_alerts}
                        onChange={(e) => setNotificationPreferences(prev => prev ? {...prev, email_alerts: e.target.checked} : null)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Email Alerts</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={notificationPreferences.sms_alerts}
                        onChange={(e) => setNotificationPreferences(prev => prev ? {...prev, sms_alerts: e.target.checked} : null)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">SMS Alerts</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={notificationPreferences.push_notifications}
                        onChange={(e) => setNotificationPreferences(prev => prev ? {...prev, push_notifications: e.target.checked} : null)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Push Notifications</span>
                    </label>
                    
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={notificationPreferences.price_alerts}
                        onChange={(e) => setNotificationPreferences(prev => prev ? {...prev, price_alerts: e.target.checked} : null)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Price Alerts</span>
                    </label>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Alert Frequency
                    </label>
                    <select
                      value={notificationPreferences.alert_frequency}
                      onChange={(e) => setNotificationPreferences(prev => prev ? {...prev, alert_frequency: e.target.value as 'immediate' | 'hourly' | 'daily'} : null)}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="immediate">Immediate</option>
                      <option value="hourly">Hourly</option>
                      <option value="daily">Daily</option>
                    </select>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={async () => {
                        try {
                          await unifiedAiApi.updateNotificationPreferences(notificationPreferences!);
                          toast.success('Notification preferences updated');
                        } catch (err) {
                          toast.error('Failed to update preferences');
                        }
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Save Preferences
                    </button>
                    
                    <button
                      onClick={async () => {
                        try {
                          await unifiedAiApi.testNotification('Test notification from Unified AI Dashboard');
                          toast.success('Test notification sent');
                        } catch (err) {
                          toast.error('Failed to send test notification');
                        }
                      }}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Test Notification
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Cog6ToothIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Notification Settings Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Configure your notification preferences</p>
                <button
                  onClick={fetchNotificationPreferences}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Load Settings
                </button>
              </div>
            )}
          </div>
        )}

        {/* Status Tab */}
        {activeTab === 'status' && (
          <div className="space-y-6">
            {serviceStatus ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Service Status</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Traditional AI</h4>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          {serviceStatus.traditional_ai.status === 'active' ? (
                            <CheckCircleIcon className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircleIcon className="h-4 w-4 text-red-500" />
                          )}
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            Status: {serviceStatus.traditional_ai.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Accuracy: {serviceStatus.traditional_ai?.performance_metrics?.accuracy ?? 'N/A'}%
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Response Time: {serviceStatus.traditional_ai?.performance_metrics?.response_time_ms ?? 'N/A'}ms
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Uptime: {serviceStatus.traditional_ai?.performance_metrics?.uptime_percentage ?? 'N/A'}%
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Generative AI</h4>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          {serviceStatus.generative_ai.status === 'active' ? (
                            <CheckCircleIcon className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircleIcon className="h-4 w-4 text-red-500" />
                          )}
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            Status: {serviceStatus.generative_ai.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Model: {serviceStatus.generative_ai?.model ?? 'N/A'}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Response Time: {serviceStatus.generative_ai?.performance_metrics?.response_time_ms ?? 'N/A'}ms
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Uptime: {serviceStatus.generative_ai?.performance_metrics?.uptime_percentage ?? 'N/A'}%
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
                    <div className="flex items-center space-x-2">
                      {serviceStatus.database_status === 'connected' ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircleIcon className="h-4 w-4 text-red-500" />
                      )}
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Database: {serviceStatus.database_status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Last Updated: {new Date(serviceStatus.last_updated).toLocaleString()}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <CheckCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Status Available</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Check Unified AI service status</p>
                <button
                  onClick={fetchServiceStatus}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Check Status
                </button>
              </div>
            )}
          </div>
        )}

        {/* Advanced Chart Section - Always visible at the end (similar to Comprehensive Trading Pro) */}
        <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-xl">
            {/* Chart Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                    Advanced Price Chart with ML Signals
                  </h3>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {selectedSymbol} • {chartTimeframe} • {chartPeriod}
                  </span>
                </div>
                
                {/* Chart Controls */}
                <div className="flex items-center space-x-3 flex-wrap gap-2">
                  {/* Timeframe Selector */}
                  <select
                    value={chartTimeframe}
                    onChange={(e) => {
                      setChartTimeframe(e.target.value);
                    }}
                    className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="1D">1 Day</option>
                    <option value="1W">1 Week</option>
                    <option value="1M">1 Month</option>
                  </select>
                  
                  {/* Period Selector */}
                  <select
                    value={chartPeriod}
                    onChange={(e) => {
                      setChartPeriod(e.target.value);
                    }}
                    className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="5d">5 Days</option>
                    <option value="1mo">1 Month</option>
                    <option value="3mo">3 Months</option>
                    <option value="6mo">6 Months</option>
                    <option value="1y">1 Year</option>
                    <option value="2y">2 Years</option>
                  </select>
                  
                  {/* Toggle Indicators */}
                  <button
                    onClick={() => setShowChartIndicators(!showChartIndicators)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      showChartIndicators
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    Indicators
                  </button>
                  
                  {/* Toggle ML Signals */}
                  <button
                    onClick={() => setShowChartMLSignals(!showChartMLSignals)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      showChartMLSignals
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    ML Signals
                  </button>
                  
                  {/* Refresh Button */}
                  <button
                    onClick={loadAdvancedChartData}
                    disabled={chartLoading}
                    className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    title="Refresh Chart"
                  >
                    <ArrowPathIcon className={`h-5 w-5 ${chartLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              </div>
            </div>

            {/* Chart Container */}
            <div className="relative">
              <div 
                ref={advancedChartContainerRef} 
                className="w-full h-[600px] bg-[#131722]"
              />
              
              {chartLoading && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
                  <LoadingSpinner size="lg" />
                </div>
              )}
              
              {/* ML Signals Overlay */}
              {showChartMLSignals && analysisResult?.analysis_result?.ml_signals && candlestickSeriesRef.current && advancedChartRef.current && (
                <MLSignalsOverlay
                  symbol={selectedSymbol}
                  chartApi={advancedChartRef.current}
                  candlestickSeries={candlestickSeriesRef.current}
                  visible={showChartMLSignals}
                />
              )}
            </div>

            {/* Technical Indicators Panel */}
            {showChartIndicators && chartData && chartData.candles && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                <TechnicalIndicators
                  data={chartData.candles.map((candle: any) => ({
                    date: new Date((candle.time as number) * 1000).toISOString(),
                    close: candle.close,
                    high: candle.high,
                    low: candle.low,
                    open: candle.open,
                    volume: candle.volume || 0,
                  }))}
                  symbol={selectedSymbol}
                  height={300}
                  loading={chartLoading}
                  className="bg-transparent"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedAIAnalysisPanel;

