import React, { useEffect, useState, useRef, useMemo, useCallback, Suspense, lazy } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, HistogramData, Time, BusinessDay } from 'lightweight-charts';
import comprehensiveTradingApi, { ChartDataRequest } from '../services/comprehensiveTradingApi';
import candleDataApi from '../services/candleDataApi';
import StockSelector from '../components/StockSelector';
import BuySellButton from '../components/BuySellButton';
import { deduplicateAndSortCandlestickData, deduplicateAndSortHistogramData, deduplicateAndSortLineData } from '../utils/chartDataUtils';
import ChartTooltip, { TooltipData } from '../components/ChartTooltip';
import OverlayDetailModal, { OverlayDetail } from '../components/OverlayDetailModal';
import chartOverlayService, { OverlaySettings, OverlayMetadata, MarketStructureData, SupportResistanceData, SupplyDemandData } from '../services/chartOverlayService';
import { useChartSettings } from '../hooks/useChartSettings';
import { ChartSettings } from '../types/chartSettings';
import { autoAlertService, AnalysisEvent } from '../services/autoAlertService';
import { toast } from 'react-hot-toast';
import { alertApi } from '../services/alertApi';
import { watchlistService } from '../services/watchlistService';
import MobileTradingDrawer from '../components/MobileTradingDrawer';
import MobileBottomSheet from '../components/MobileBottomSheet';
import refreshService from '../services/RefreshService';
import api from '../services/api';
import { requestDeduplicator } from '../utils/requestDeduplication';
import { useThrottle } from '../hooks/useThrottle';
import { ComponentLoader } from '../components/LoadingSkeleton';

// Lazy load heavy components to reduce initial bundle size
const EnhancedOrderPlacement = lazy(() => import('../components/EnhancedOrderPlacement'));
const PortfolioPanel = lazy(() => import('../components/PortfolioPanel'));
const TabbedAnalysisPanel = lazy(() => import('../components/TabbedAnalysisPanel'));
const ChartOverlayControls = lazy(() => import('../components/ChartOverlayControls'));
const TechnicalIndicators = lazy(() => import('../components/TechnicalIndicators'));
const EnhancedIndicatorSelector = lazy(() => import('../components/EnhancedIndicatorSelector'));
const ChartExportButton = lazy(() => import('../components/ChartExportButton'));
const Watchlist = lazy(() => import('../components/Watchlist'));
const ChartDrawingTools = lazy(() => import('../components/ChartDrawingTools'));
const DrawingCanvasOverlay = lazy(() => import('../components/DrawingCanvasOverlay'));
const LightweightChartIndicators = lazy(() => import('../components/LightweightChartIndicators'));
const ThemeCustomization = lazy(() => import('../components/ThemeCustomization'));
const ChartSettingsPanel = lazy(() => import('../components/ChartSettingsPanel'));
const ChatWidget = lazy(() => import('../components/ChatWidget'));
const SentimentOverlay = lazy(() => import('../components/SentimentOverlay'));
const MLSignalsOverlay = lazy(() => import('../components/MLSignalsOverlay'));
const MarketOverviewPanel = lazy(() => import('../components/MarketOverviewPanel'));
const PatternVisualization = lazy(() => import('../components/PatternVisualization'));
const AdvancedChartAnalysis = lazy(() => import('../components/AdvancedChartAnalysis'));
const FibonacciOverlay = lazy(() => import('../components/FibonacciOverlay'));
const PatternDetectionOverlay = lazy(() => import('../components/PatternDetectionOverlay'));
const MultiTimeframePanel = lazy(() => import('../components/MultiTimeframePanel'));

// Professional TradingView-Style Interface with Lightweight-Charts
const ComprehensiveTradingPro: React.FC = () => {
  // Get symbol and tab from URL query parameters
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const symbolFromUrl = searchParams.get('symbol') || 'RELIANCE';
  const tabFromUrl = searchParams.get('tab');
  const initialTabIndex = tabFromUrl ? parseInt(tabFromUrl, 10) : 0;
  const periodFromUrl = searchParams.get('period') || '1y';
  const timeframeFromUrl = searchParams.get('timeframe') || '1D';
  
  // State Management
  const [activeSymbol, setActiveSymbol] = useState(symbolFromUrl);
  const [timeframe, setTimeframe] = useState(timeframeFromUrl);
  const [period, setPeriod] = useState(periodFromUrl); // Period/range selector
  const [chartData, setChartData] = useState<any>(null);
  const [loading, setLoading] = useState(false); // Non-blocking loading state
  const [error, setError] = useState<string | null>(null);
  const [showIndicators, setShowIndicators] = useState(false);
  const [showEnhancedIndicatorSelector, setShowEnhancedIndicatorSelector] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showWatchlist, setShowWatchlist] = useState(false);
  const [showTechnicalIndicators, setShowTechnicalIndicators] = useState(true);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [chatMinimized, setChatMinimized] = useState(false);
  const [showSentimentOverlay, setShowSentimentOverlay] = useState(true);
  const [showMLSignalsOverlay, setShowMLSignalsOverlay] = useState(true);
  const [showMarketOverview, setShowMarketOverview] = useState(false);
  const [showPatternVisualization, setShowPatternVisualization] = useState(true);
  const [showFibonacci, setShowFibonacci] = useState(false);
  const [showPatternDetection, setShowPatternDetection] = useState(true);
  const [showMultiTimeframe, setShowMultiTimeframe] = useState(false);
  const [showPortfolio, setShowPortfolio] = useState(false);
  const [showMobileDrawer, setShowMobileDrawer] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [showChartSettings, setShowChartSettings] = useState(false);
  const [drawingOverlayProps, setDrawingOverlayProps] = useState<{
    drawings: any[];
    currentDrawing: any | null;
    isDrawing: boolean;
    activeTool: string | null;
    onMouseDown: (e: React.MouseEvent) => void;
    onMouseMove: (e: React.MouseEvent) => void;
    onMouseUp: (e: React.MouseEvent) => void;
  } | null>(null);
  
  // Indicators state
  const [indicators, setIndicators] = useState<Array<{
    name: string;
    type: 'SMA' | 'EMA' | 'RSI' | 'MACD' | 'BB' | 'ATR' | 'STOCH';
    period: number;
    color: string;
    visible: boolean;
  }>>([
    { name: 'SMA 20', type: 'SMA', period: 20, color: '#3B82F6', visible: false },
    { name: 'SMA 50', type: 'SMA', period: 50, color: '#10B981', visible: false },
    { name: 'EMA 12', type: 'EMA', period: 12, color: '#F59E0B', visible: false },
    { name: 'RSI', type: 'RSI', period: 14, color: '#8B5CF6', visible: false },
    { name: 'MACD', type: 'MACD', period: 14, color: '#EF4444', visible: false },
    { name: 'Bollinger Bands', type: 'BB', period: 20, color: '#06B6D4', visible: false },
  ]);
  
  // Right sidebar navigation state
  const [rightSidebarTab, setRightSidebarTab] = useState<'watchlist' | 'positions' | 'orders' | 'chain' | 'depth' | 'holdings' | 'balance' | 'layout'>('watchlist');
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  
  // Chart Settings Management
  const {
    settings: chartSettings,
    updateTheme,
    updateAppearance,
    updateCandlestick,
    updateScale,
    resetToDefaults,
    exportSettings,
    importSettings,
  } = useChartSettings();
  
  // Indices data
  const [indices, setIndices] = useState<Record<string, { price: number; change: number; changePercent: number }>>({});
  const [loadingIndices, setLoadingIndices] = useState(false);
  
  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Fetch indices data with timeout protection
  useEffect(() => {
    const fetchIndices = async () => {
      setLoadingIndices(true);
      const marketIndices = [
        { symbol: 'NIFTY_50', name: 'NIFTY' },
        { symbol: 'SENSEX', name: 'SENSEX' },
        { symbol: 'NIFTYBANK', name: 'BANKNIFTY' }
      ];

      // Add overall timeout for indices loading (5 seconds max)
      const indicesTimeout = setTimeout(() => {
        console.warn('[ComprehensiveTradingPro] Indices loading timeout');
        setLoadingIndices(false);
      }, 5000);

      try {
        for (const index of marketIndices) {
          try {
            // Add timeout per index (2 seconds max per index)
            const indexPromise = Promise.race([
              candleDataApi.getLatestCandle(index.symbol),
              new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Index fetch timeout')), 2000)
              )
            ]) as Promise<any>;
            
            const response = await indexPromise;
            if (response.success && response.data) {
              const candle = response.data;
              const change = candle.close - candle.open;
              const changePercent = (change / candle.open) * 100;
              setIndices(prev => ({
                ...prev,
                [index.symbol]: {
                  price: candle.close,
                  change: change,
                  changePercent: changePercent
                }
              }));
            }
          } catch (error) {
            console.log(`Could not fetch index ${index.symbol}:`, error);
            // Continue to next index even if one fails
          }
          // Small delay between requests to avoid rate limiting
          await new Promise(resolve => setTimeout(resolve, 100)); // Reduced from 200ms
        }
      } finally {
        clearTimeout(indicesTimeout);
        setLoadingIndices(false);
      }
    };

    fetchIndices();
    // Use centralized refresh service
    refreshService.register('comprehensive-trading-indices', fetchIndices, 30000, false);
    return () => {
      refreshService.clear('comprehensive-trading-indices');
    };
  }, []);
  
  // Real-time updates
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [dataSource, setDataSource] = useState<'YAHOO_FINANCE' | 'MOCK' | 'LOADING'>('LOADING');
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  const [lastAnalysisTime, setLastAnalysisTime] = useState<Date | null>(null);
  const [analysisRefreshTrigger, setAnalysisRefreshTrigger] = useState(0);
  const [activeTabIndex, setActiveTabIndex] = useState(initialTabIndex);
  
  // Real-time quote data for OHLC bar
  const [realTimeQuote, setRealTimeQuote] = useState<any>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  
  // Chart Overlay Settings
  const [overlaySettings, setOverlaySettings] = useState<OverlaySettings>({
    showBOS: true,
    showCHoCH: true,
    showSupport: true,
    showResistance: true,
    showDemandZones: true,
    showSupplyZones: true,
    showTrendlines: true,
    showSwingPoints: true,
    freshZonesOnly: false,
    strongZonesOnly: false,
    minStrength: 0.3,
  });
  const [overlaysInitialized, setOverlaysInitialized] = useState(false);
  
  // Apply chart settings to chart when they change
  useEffect(() => {
    if (!chartRef.current || !candlestickSeriesRef.current) return;
    
    const settings = chartSettings;
    
    // Apply layout settings
    chartRef.current.applyOptions({
      layout: {
        background: { color: settings.theme.colors.background },
        textColor: settings.theme.colors.text,
      },
      grid: {
        vertLines: {
          color: settings.appearance.gridVisible
            ? settings.appearance.gridColor
            : 'transparent',
          style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
        },
        horzLines: {
          color: settings.appearance.gridVisible
            ? settings.appearance.gridColor
            : 'transparent',
          style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
        },
      },
      crosshair: {
        mode: settings.appearance.crosshairVisible ? 1 : 0,
        vertLine: {
          color: settings.appearance.crosshairColor,
          style: settings.appearance.crosshairStyle === 'dashed' ? 1 : settings.appearance.crosshairStyle === 'dotted' ? 2 : 0,
        },
        horzLine: {
          color: settings.appearance.crosshairColor,
          style: settings.appearance.crosshairStyle === 'dashed' ? 1 : settings.appearance.crosshairStyle === 'dotted' ? 2 : 0,
        },
      },
      timeScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        timeVisible: settings.scale.timeVisible,
      },
      rightPriceScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        scaleMargins: settings.scale.scaleMargins,
      },
      leftPriceScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        scaleMargins: settings.scale.scaleMargins,
      },
    });
    
    // Apply candlestick settings
    if (settings.candlestick.style === 'candlestick') {
      candlestickSeriesRef.current.applyOptions({
        upColor: settings.candlestick.upColor,
        downColor: settings.candlestick.downColor,
        wickUpColor: settings.candlestick.wickUpColor,
        wickDownColor: settings.candlestick.wickDownColor,
        borderVisible: settings.candlestick.borderVisible,
      });
    }
    // Note: Other chart styles (line, area, bars) would require removing and re-adding the series
    
    // Update volume chart if it exists
    if (volumeChartRef.current) {
      volumeChartRef.current.applyOptions({
        layout: {
          background: { color: settings.theme.colors.background },
          textColor: settings.theme.colors.text,
        },
        grid: {
          vertLines: {
            color: settings.appearance.gridVisible
              ? settings.appearance.gridColor
              : 'transparent',
            style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
          },
          horzLines: {
            color: settings.appearance.gridVisible
              ? settings.appearance.gridColor
              : 'transparent',
            style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
          },
        },
        timeScale: {
          borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
          timeVisible: settings.scale.timeVisible,
        },
        rightPriceScale: {
          borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        },
      });
    }
    
    if (volumeSeriesRef.current) {
      volumeSeriesRef.current.applyOptions({
        color: settings.candlestick.upColor,
      });
    }
    
  }, [chartSettings]);
  
  // Interactive features state
  const [tooltipData, setTooltipData] = useState<TooltipData | null>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [modalDetail, setModalDetail] = useState<OverlayDetail | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  
  // Handler to merge partial overlay settings
  const handleOverlaySettingsChange = (partialSettings: Partial<OverlaySettings>) => {
    const newSettings = { ...overlaySettings, ...partialSettings };
    setOverlaySettings(newSettings);
    // Update service immediately when settings change
    if (overlaysInitialized && chartOverlayService) {
      chartOverlayService.updateSettings(partialSettings);
    }
  };
  
  // Interactive features handlers
  const convertMetadataToTooltip = (metadata: OverlayMetadata, x: number, y: number): TooltipData => {
    return {
      type: metadata.type,
      title: metadata.title,
      price: metadata.price,
      data: metadata.data,
      position: { x, y }
    };
  };

  const convertMetadataToModal = (metadata: OverlayMetadata): OverlayDetail => {
    const isInWatchlist = watchlistService.isInWatchlist(activeSymbol);
    
    return {
      type: metadata.type,
      title: metadata.title,
      subtitle: metadata.price ? `Price Level: ₹${metadata.price.toFixed(2)}` : undefined,
      price: metadata.price,
      priceRange: metadata.priceRange,
      data: metadata.data,
      actions: [
        {
          label: isInWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist',
          onClick: () => {
            if (isInWatchlist) {
              watchlistService.removeSymbol(activeSymbol);
              toast.success(`${activeSymbol} removed from watchlist`);
            } else {
              watchlistService.addSymbol(activeSymbol);
              toast.success(`${activeSymbol} added to watchlist`);
            }
            // Update modal to reflect change
            setModalDetail(prev => prev ? {
              ...prev,
              actions: prev.actions?.map(action => 
                action.label.includes('Watchlist')
                  ? { ...action, label: watchlistService.isInWatchlist(activeSymbol) ? 'Remove from Watchlist' : 'Add to Watchlist' }
                  : action
              )
            } : null);
          }
        },
        {
          label: 'Set Alert',
          onClick: () => {
            if (metadata.price) {
              // Navigate to alerts tab or create alert
              setActiveTabIndex(8); // Alerts tab index
              toast.success(`Opening alerts for ${activeSymbol} at ₹${metadata.price.toFixed(2)}`);
            }
          }
        }
      ]
    };
  };

  // Helper function to check if chart is valid
  const isChartValid = (): boolean => {
    return !!(
      chartRef.current &&
      chartContainerRef.current &&
      candlestickSeriesRef.current
    );
  };

  // Use useCallback to ensure handlers are stable across renders
  const handleChartClick = useCallback((event: MouseEvent) => {
    if (!isChartValid()) return;
    
    try {
      const chart = chartRef.current!;
      const series = candlestickSeriesRef.current;
      if (!series) return;
      
      const rect = (event.target as HTMLElement).getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      // Get price at click position
      const price = series.coordinateToPrice(y);
      if (price) {
        const overlay = chartOverlayService.getOverlayAtPrice(price as number);
        if (overlay) {
          setModalDetail(convertMetadataToModal(overlay));
          setModalVisible(true);
          setTooltipVisible(false);
        }
      }
    } catch (error) {
      console.error('Error handling chart click:', error);
    }
  }, []); // Empty deps - handlers use refs which are stable

  const handleChartMouseMove = useCallback((event: MouseEvent) => {
    if (!isChartValid()) return;
    
    try {
      const series = candlestickSeriesRef.current;
      if (!series) return;
      
      const rect = (event.target as HTMLElement).getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      // Get price at mouse position
      const price = series.coordinateToPrice(y);
      if (price) {
        const overlay = chartOverlayService.getOverlayAtPrice(price as number, 1.0);
        if (overlay) {
          setTooltipData(convertMetadataToTooltip(overlay, event.clientX, event.clientY));
          setTooltipVisible(true);
        } else {
          setTooltipVisible(false);
        }
      } else {
        setTooltipVisible(false);
      }
    } catch (error) {
      // Silently handle errors during mouse move
    }
  }, []); // Empty deps - handlers use refs which are stable

  const handleChartMouseLeave = useCallback(() => {
    setTooltipVisible(false);
  }, []);

  // Handle window resize - stable callback for chart resizing
  const handleChartResize = useCallback(() => {
    if (chartContainerRef.current && chartRef.current) {
      try {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      } catch (error) {
        console.debug('Chart resize error:', error);
      }
    }
  }, []); // Empty deps - uses refs which are stable

  // Auto-alert handler
  const handleAutoAlert = async (event: AnalysisEvent) => {
    try {
      const result = autoAlertService.processEvent(event);
      
      if (result.shouldCreate && result.alertData) {
        // Check if similar alert already exists
        const existingAlerts = await alertApi.listAlerts(activeSymbol);
        const similarAlert = existingAlerts.alerts?.find((a: any) => 
          a.alert_type === result.alertData.alert_type &&
          Math.abs((a.target_price || 0) - (result.alertData.target_price || 0)) < 0.01
        );

        if (!similarAlert) {
          const response = await alertApi.createAlert(result.alertData as any);
          if (response.success) {
            toast.success(`Auto-alert created: ${event.type.replace('_', ' ')}`, {
              icon: '🔔',
              duration: 3000
            });
          }
        }
      }
    } catch (error) {
      console.error('Error creating auto-alert:', error);
    }
  };
  
  // MA Settings
  const [maSettings, setMaSettings] = useState({
    ma5: { enabled: true, color: '#FFA500', period: 5 },
    ma10: { enabled: true, color: '#9370DB', period: 10 },
    ma30: { enabled: true, color: '#00BFFF', period: 30 },
    ma60: { enabled: true, color: '#FF1493', period: 60 },
  });

  // Chart refs
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartWrapperRef = useRef<HTMLDivElement>(null); // For export - contains both chart and volume
  const volumeContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const volumeChartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const maSeriesRefs = useRef<{
    ma5: ISeriesApi<'Line'> | null;
    ma10: ISeriesApi<'Line'> | null;
    ma30: ISeriesApi<'Line'> | null;
    ma60: ISeriesApi<'Line'> | null;
  }>({
    ma5: null,
    ma10: null,
    ma30: null,
    ma60: null,
  });

  // Timeframe options with descriptions (controls candle interval)
  const timeframes = [
    { value: '1m', label: '1 Minute', interval: '1m' },
    { value: '5m', label: '5 Minutes', interval: '5m' },
    { value: '15m', label: '15 Minutes', interval: '15m' },
    { value: '1H', label: '1 Hour', interval: '1h' },
    { value: '2H', label: '2 Hours', interval: '2h' },
    { value: '4H', label: '4 Hours', interval: '4h' },
    { value: '1D', label: '1 Day', interval: '1d' },
    { value: '1W', label: '1 Week', interval: '1wk' },
    { value: '1M', label: '1 Month', interval: '1mo' },
  ];

  // Period/Range options (controls how much historical data to show)
  const periods = [
    { value: '1d', label: '1 Day', range: '1d' },
    { value: '2d', label: '2 Days', range: '2d' },
    { value: '3d', label: '3 Days', range: '3d' },
    { value: '5d', label: '5 Days', range: '5d' },
    { value: '1w', label: '1 Week', range: '5d' },
    { value: '1mo', label: '1 Month', range: '1mo' },
    { value: '3mo', label: '3 Months', range: '3mo' },
    { value: '6mo', label: '6 Months', range: '6mo' },
    { value: '1y', label: '1 Year', range: '1y' },
    { value: '2y', label: '2 Years', range: '2y' },
    { value: '3y', label: '3 Years', range: '3y' },
    { value: '5y', label: '5 Years', range: '5y' },
  ];

  // Helper function to get period duration in seconds
  const getPeriodDurationInSeconds = (periodValue: string): number => {
    const periodMap: Record<string, number> = {
      '1d': 1 * 24 * 60 * 60,           // 1 day
      '2d': 2 * 24 * 60 * 60,           // 2 days
      '3d': 3 * 24 * 60 * 60,           // 3 days
      '5d': 5 * 24 * 60 * 60,           // 5 days
      '1w': 7 * 24 * 60 * 60,           // 1 week (7 days)
      '1mo': 30 * 24 * 60 * 60,         // 1 month (30 days)
      '3mo': 90 * 24 * 60 * 60,         // 3 months (90 days)
      '6mo': 180 * 24 * 60 * 60,        // 6 months (180 days)
      '1y': 365 * 24 * 60 * 60,         // 1 year (365 days)
      '2y': 2 * 365 * 24 * 60 * 60,     // 2 years
      '3y': 3 * 365 * 24 * 60 * 60,     // 3 years
      '5y': 5 * 365 * 24 * 60 * 60,     // 5 years
    };
    return periodMap[periodValue] || 365 * 24 * 60 * 60; // Default to 1 year
  };

  // Cache for processed chart data to avoid re-processing
  const processedDataCache = useRef<Map<string, any>>(new Map());
  
  // Debounce utility for chart updates
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Load chart data using new Candle Data API (optimized with caching and request deduplication)
  // Abort controller ref for cancelling requests
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const loadChartData = useCallback(async (customPeriod?: string, customTimeframe?: string, customSymbol?: string) => {
    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    
    // Use provided values or fall back to state
    const currentSymbol = customSymbol || activeSymbol;
    const currentPeriod = customPeriod || period;
    const currentTimeframe = customTimeframe || timeframe;
    
    // Create deduplication key
    const requestKey = `chart-${currentSymbol}-${currentTimeframe}-${currentPeriod}`;
    
    // Check if too many requests are pending
    if (requestDeduplicator.getPendingCount() > 5) {
      console.warn('[ComprehensiveTradingPro] Too many pending requests, skipping...');
      return;
    }
    
    try {
      // Set loading state asynchronously to not block UI
      requestAnimationFrame(() => {
        if (!abortController.signal.aborted) {
          setLoading(true);
        }
      });
      
      const timeframeConfig = timeframes.find(tf => tf.value === currentTimeframe);
      const periodConfig = periods.find(p => p.value === currentPeriod);
      const interval = timeframeConfig?.interval || '1d';
      
      // For intraday timeframes (5m, 15m, 1h, etc.), we need to request enough data
      // to cover the period accounting for weekends/holidays
      const isIntraday = ['5m', '15m', '1h', '2h', '4h'].includes(interval);
      let range = periodConfig?.range || currentPeriod || '1y';
      
      if (isIntraday) {
        // For intraday timeframes, ensure we request enough data
        // Calculate period in days
        const periodDays = getPeriodDurationInSeconds(currentPeriod) / (24 * 60 * 60);
        
        if (periodDays <= 1) {
          range = '2d'; // Request 2 days for 1 day period
        } else if (periodDays <= 5) {
          range = `${Math.ceil(periodDays * 1.5)}d`; // Add 50% buffer
        } else if (periodDays <= 30) {
          range = `${Math.ceil(periodDays * 1.2)}d`; // Add 20% buffer
        } else if (periodDays <= 90) {
          range = `${Math.ceil(periodDays * 1.1)}d`; // Add 10% buffer for 1-3 months
        } else {
          // For longer periods (3+ months), convert to months/weeks
          if (currentPeriod === '1w') {
            range = '5d'; // 1 week = 5 trading days
          } else if (currentPeriod === '1mo') {
            range = '1mo';
          } else if (currentPeriod === '3mo') {
            range = '3mo';
          } else if (currentPeriod === '6mo') {
            range = '6mo';
          } else {
            range = currentPeriod; // Use period as-is for years
          }
        }
      } else {
        // For daily/weekly/monthly timeframes, use period range directly
        range = periodConfig?.range || currentPeriod || '1y';
      }
      
      console.log(`📊 [ComprehensiveTradingPro] Timeframe: ${currentTimeframe}`);
      console.log(`📊 [ComprehensiveTradingPro] Period: ${currentPeriod}`);
      console.log(`📊 [ComprehensiveTradingPro] Interval: ${interval}, Range: ${range} (isIntraday: ${isIntraday})`);
      console.log(`📊 [ComprehensiveTradingPro] Fetching for symbol: ${currentSymbol}`);
      
      // Check cache first (optimization)
      const cacheKey = `${currentSymbol}-${interval}-${range}-${currentPeriod}`;
      const cachedData = processedDataCache.current.get(cacheKey);
      
      if (cachedData) {
        console.log(`📊 [ComprehensiveTradingPro] Using cached data for ${cacheKey}`);
        setChartData(cachedData);
        setDataSource('YAHOO_FINANCE');
        setLastUpdateTime(new Date());
        setError(null); // Clear any previous errors
        // Don't update URL here - let user actions handle URL updates to prevent loops
        setLoading(false);
        return;
      }
      
      // Fetch candle data from our new API with timeout, deduplication, and abort support
      console.log(`📡 [ComprehensiveTradingPro] Fetching from API: ${currentSymbol}, ${interval}, ${range}`);
      
      // Check if request was aborted before making API call
      if (abortController.signal.aborted) {
        console.log('[ComprehensiveTradingPro] Request aborted before API call');
        return;
      }
      
      const response = await requestDeduplicator.deduplicate(
        requestKey,
        async () => {
          // Create a promise that rejects on abort
          const abortPromise = new Promise((_, reject) => {
            abortController.signal.addEventListener('abort', () => {
              reject(new Error('Request cancelled'));
            });
          });
          
          return await Promise.race([
            candleDataApi.getCandles(currentSymbol, interval, range),
            abortPromise,
            new Promise((_, reject) => 
              setTimeout(() => reject(new Error('API request timeout after 10 seconds')), 10000)
            )
          ]) as any;
        },
        5000 // 5 second deduplication window
      );
      
      // Check if request was aborted after API call
      if (abortController.signal.aborted) {
        console.log('[ComprehensiveTradingPro] Request aborted after API call');
        return;
      }
      
      if (response.success && response.data.length > 0) {
        // Transform data to match expected format and sort by time (memoized processing)
        interface CandleData {
          time: number;
          open: number;
          high: number;
          low: number;
          close: number;
          volume: number;
        }
        
        let candles: CandleData[] = response.data.map((candle: any) => ({
          time: candle.time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
          volume: candle.volume
        }));
        
        // CRITICAL: Sort by time ascending (required by Lightweight Charts)
        // Ensure time is a number for proper comparison
        candles.sort((a: CandleData, b: CandleData) => {
          const timeA = Number(a.time);
          const timeB = Number(b.time);
          if (isNaN(timeA) || isNaN(timeB)) {
            console.warn('Invalid time value detected:', a.time, b.time);
            return 0;
          }
          return timeA - timeB;
        });
        
        // Validate sorting - check for any out-of-order data
        for (let i = 1; i < candles.length; i++) {
          const prevTime = Number(candles[i - 1].time);
          const currTime = Number(candles[i].time);
          if (currTime < prevTime) {
            console.error(`Data out of order detected at index ${i}: time=${currTime}, prev time=${prevTime}`);
            // Re-sort to fix
            candles.sort((a: CandleData, b: CandleData) => Number(a.time) - Number(b.time));
            break;
          }
        }
        
        // Filter candles to only show the selected period range
        // Use the last candle's time as reference (more reliable for historical data)
        if (candles.length > 0) {
          const lastCandleTime = candles[candles.length - 1].time;
          const periodDurationSeconds = getPeriodDurationInSeconds(currentPeriod);
          const cutoffTime = lastCandleTime - periodDurationSeconds;
          
          // Filter candles to only include those within the selected period
          const beforeFilter = candles.length;
          candles = candles.filter((candle: CandleData) => candle.time >= cutoffTime);
          
          console.log(`📊 [ComprehensiveTradingPro] Filtered ${beforeFilter} candles to ${candles.length} for period ${currentPeriod}`);
          console.log(`📊 [ComprehensiveTradingPro] Cutoff time: ${new Date(cutoffTime * 1000).toISOString()}`);
          console.log(`📊 [ComprehensiveTradingPro] Last candle time: ${new Date(lastCandleTime * 1000).toISOString()}`);
          console.log(`📊 [ComprehensiveTradingPro] Period duration: ${currentPeriod} = ${periodDurationSeconds} seconds (${periodDurationSeconds / (24 * 60 * 60)} days)`);
        }
        
        const transformedData = { candles };
        
        // Cache the processed data (limit cache size to prevent memory issues)
        if (processedDataCache.current.size > 10) {
          // Remove oldest entry (simple FIFO)
          const firstKey = processedDataCache.current.keys().next().value;
          if (firstKey) {
            processedDataCache.current.delete(firstKey);
          }
        }
        processedDataCache.current.set(cacheKey, transformedData);
        
        console.log('[ComprehensiveTradingPro] ✅ Setting chartData:', transformedData);
        console.log('[ComprehensiveTradingPro] Period:', currentPeriod, 'Duration (seconds):', getPeriodDurationInSeconds(currentPeriod));
        console.log('[ComprehensiveTradingPro] Filtered candles length:', transformedData.candles.length);
        if (transformedData.candles.length > 0) {
          console.log('[ComprehensiveTradingPro] First candle:', transformedData.candles[0]);
          console.log('[ComprehensiveTradingPro] Last candle:', transformedData.candles[transformedData.candles.length - 1]);
        }
        
        setChartData(transformedData);
        setDataSource('YAHOO_FINANCE');
        setLastUpdateTime(new Date());
        setError(null); // Clear any previous errors
      console.log(`✅ Loaded ${response.data.length} candles, filtered to ${candles.length} for period ${currentPeriod}`);
      
      // Don't update URL here - let user actions handle URL updates to prevent loops
      } else {
        console.warn('No candle data available, using mock data');
        setChartData(generateMockData());
        setDataSource('MOCK');
        setLastUpdateTime(new Date());
        setError(null); // Clear any previous errors when using mock data
      }
    } catch (error: any) {
      // Don't show error if request was cancelled
      if (error?.message === 'Request cancelled' || abortController.signal.aborted) {
        console.log('[ComprehensiveTradingPro] Request cancelled, ignoring error');
        return;
      }
      
      console.error('Failed to load chart data:', error);
      const errorMessage = error?.message || 'Failed to load chart data';
      
      // Only set error if it's not a timeout/cancellation
      if (!errorMessage.includes('timeout') && !errorMessage.includes('cancelled') && !errorMessage.includes('Request cancelled')) {
        setError(errorMessage);
        console.warn('Using mock data as fallback');
        // Use mock data as fallback
        setChartData(generateMockData());
        setDataSource('MOCK');
        setLastUpdateTime(new Date());
        // Show error toast only for real errors
        toast.error(`Failed to load chart data: ${errorMessage}. Using mock data.`);
      }
    } finally {
      // Clean up abort controller if this was the active request
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
      
      // Only set loading to false if request wasn't cancelled
      if (!abortController.signal.aborted) {
        setLoading(false);
      }
    }
  }, [activeSymbol, period, timeframe]); // Removed searchParams to avoid infinite loops

  // Track if we've done initial load
  const hasInitialLoadedRef = useRef(false);
  const skipNextReloadRef = useRef(false);
  
  // Initial load on mount - only runs once
  useEffect(() => {
    if (hasInitialLoadedRef.current) return;
    
    const initialSymbol = searchParams.get('symbol') || 'RELIANCE';
    const initialPeriod = searchParams.get('period') || '1y';
    const initialTimeframe = searchParams.get('timeframe') || '1D';
    
    console.log('🔄 [ComprehensiveTradingPro] Initial load:', { initialSymbol, initialPeriod, initialTimeframe });
    
    // Mark as loaded and skip reload BEFORE setting state to prevent double load
    hasInitialLoadedRef.current = true;
    skipNextReloadRef.current = true;
    
    // Update URL to ensure it's in sync (only if needed)
    const currentUrl = searchParams.toString();
    const expectedParams = new URLSearchParams();
    expectedParams.set('symbol', initialSymbol);
    expectedParams.set('timeframe', initialTimeframe);
    expectedParams.set('period', initialPeriod);
    if (currentUrl !== expectedParams.toString()) {
      setSearchParams(expectedParams, { replace: true });
      lastProcessedUrlRef.current = expectedParams.toString();
    } else {
      lastProcessedUrlRef.current = currentUrl;
    }
    
    // Set state (this will trigger reload effect, but skipNextReloadRef prevents it)
    setActiveSymbol(initialSymbol);
    setPeriod(initialPeriod);
    setTimeframe(initialTimeframe);
    
    // Load with URL params directly (bypass state)
    loadChartData(initialPeriod, initialTimeframe, initialSymbol);
  }, []); // Empty deps - only run on mount

  // Reload when state changes (but skip initial mount) - with debounce to prevent rapid reloads
  useEffect(() => {
    // Skip if we haven't done initial load yet
    if (!hasInitialLoadedRef.current) return;
    
    // Skip if we're syncing from URL (to avoid double load)
    if (skipNextReloadRef.current) {
      skipNextReloadRef.current = false;
      return;
    }
    
    // Debounce rapid state changes to prevent multiple API calls
    const timeoutId = setTimeout(() => {
      console.log('🔄 [ComprehensiveTradingPro] Reloading due to state change:', { activeSymbol, period, timeframe });
      loadChartData();
    }, 150); // 150ms debounce for state changes
    
    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSymbol, period, timeframe]); // loadChartData is stable due to useCallback

  // Sync URL params to state when URL changes (but only if URL actually changed externally)
  // Use a ref to track the last URL we processed to avoid loops
  const lastProcessedUrlRef = useRef<string>('');
  useEffect(() => {
    // Skip on initial mount
    if (!hasInitialLoadedRef.current) return;
    
    const currentUrl = searchParams.toString();
    // If URL hasn't changed, skip (prevents loop from setSearchParams)
    if (currentUrl === lastProcessedUrlRef.current) return;
    
    const urlSymbol = searchParams.get('symbol') || 'RELIANCE';
    const urlTimeframe = searchParams.get('timeframe') || '1D';
    const urlPeriod = searchParams.get('period') || '1y';
    
    // Check if URL params differ from state
    const needsUpdate = urlSymbol !== activeSymbol || urlTimeframe !== timeframe || urlPeriod !== period;
    
    if (needsUpdate) {
      console.log('🔄 [ComprehensiveTradingPro] URL params changed externally, syncing state:', { urlSymbol, urlPeriod, urlTimeframe });
      lastProcessedUrlRef.current = currentUrl; // Mark as processed BEFORE state update
      skipNextReloadRef.current = true; // Prevent double load
      setActiveSymbol(urlSymbol);
      setPeriod(urlPeriod);
      setTimeframe(urlTimeframe);
      // State change will trigger reload effect above
    } else {
      // URL matches state, just update the ref
      lastProcessedUrlRef.current = currentUrl;
    }
  }, [searchParams]); // Only depend on searchParams, not state (to avoid loops)

  // Debounced version of loadChartData to prevent rapid-fire updates
  const debouncedLoadChartData = useCallback((customPeriod?: string, customTimeframe?: string) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    
    debounceTimeoutRef.current = setTimeout(() => {
      loadChartData(customPeriod, customTimeframe);
    }, 300); // 300ms debounce
  }, [loadChartData]);

  // Auto-refresh effect (every 60 seconds for real-time data) - uses debounced version and request deduplication
  useEffect(() => {
    if (!autoRefresh) return;
    
    // Don't auto-refresh if already loading to prevent queue buildup
    if (loading) {
      console.log('⏸️ [ComprehensiveTradingPro] Skipping auto-refresh - already loading');
      return;
    }

    const intervalId = setInterval(() => {
      // Double-check loading state before refreshing
      if (loading) {
        console.log('⏸️ [ComprehensiveTradingPro] Skipping auto-refresh - already loading');
        return;
      }
      console.log('🔄 Auto-refreshing chart data...');
      // Use deduplicated load to prevent concurrent requests
      const requestKey = `chart-${activeSymbol}-${timeframe}-${period}`;
      requestDeduplicator.deduplicate(
        requestKey,
        async () => {
          debouncedLoadChartData();
          return Promise.resolve();
        },
        10000 // 10 second deduplication window
      );
      // Note: Analysis components require manual refresh - not auto-triggered
    }, 60000); // 60 seconds (increased from 30 to reduce server load)

    return () => clearInterval(intervalId);
  }, [autoRefresh, debouncedLoadChartData, activeSymbol, timeframe, period]);

  // Note: Analysis components (swing points, trendlines, etc.) now require manual refresh
  // Only chart data refreshes automatically when stock is selected
  // Users can click the refresh button in each analysis tab to update analysis

  // Generate mock data for demo
  const generateMockData = () => {
    const candles = [];
    let price = 2500;
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    
    for (let i = 0; i < 200; i++) {
      const change = (Math.random() - 0.5) * 20;
      const open = price;
      const close = price + change;
      const high = Math.max(open, close) + Math.random() * 10;
      const low = Math.min(open, close) - Math.random() * 10;
      const volume = Math.random() * 10000000 + 1000000;
      
      const date = new Date(now);
      date.setDate(date.getDate() - (200 - i));
      
      candles.push({
        time: Math.floor(date.getTime() / 1000),
        open,
        high,
        low,
        close,
        volume,
      });
      price = close;
    }
    return { candles };
  };

  // Calculate Moving Averages (optimized with sliding window - O(n) instead of O(n*period))
  const calculateMA = useCallback((data: any[], period: number): LineData[] => {
    if (data.length < period) return [];
    
    const ma: LineData[] = [];
    let sum = 0;
    
    // Initialize sum for first window
    for (let i = 0; i < period; i++) {
      sum += data[i].close;
    }
    
    // First MA value
    ma.push({
      time: data[period - 1].time,
      value: sum / period,
    });
    
    // Slide window: remove first, add next (O(n) instead of O(n*period))
    for (let i = period; i < data.length; i++) {
      sum = sum - data[i - period].close + data[i].close;
      ma.push({
        time: data[i].time,
        value: sum / period,
      });
    }
    
    return ma;
  }, []);

  // Helper function to convert Unix timestamp to BusinessDay format for daily+ timeframes
  const convertToBusinessDay = (timestamp: number): BusinessDay => {
    const date = new Date(timestamp * 1000);
    return {
      year: date.getUTCFullYear(),
      month: date.getUTCMonth() + 1, // getUTCMonth() returns 0-11
      day: date.getUTCDate(),
    };
  };

  // Helper to determine if timeframe requires BusinessDay format
  const requiresBusinessDayFormat = (tf: string): boolean => {
    // Daily, weekly, monthly timeframes use BusinessDay format
    return ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y', '5Y'].includes(tf);
  };

  // Memoize indicator data transformation to prevent recalculation on every render
  const indicatorDataMemo = useMemo(() => {
    if (!chartData?.candles || !Array.isArray(chartData.candles)) return [];
    return chartData.candles.map((c: any) => ({
      time: typeof c.time === 'string' ? new Date(c.time).getTime() / 1000 : c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.volume || 0
    }));
  }, [chartData?.candles]);

  // Get candles data (optimized with better memoization and caching)
  const candles = useMemo(() => {
    // Early return if no data
    if (!chartData?.candles || !Array.isArray(chartData.candles) || chartData.candles.length === 0) {
      return [];
    }
    
    const candlesArray = chartData.candles;
    
    // Check if we need BusinessDay format (memoize this check)
    const useBusinessDay = requiresBusinessDayFormat(timeframe);
    
    // Define the candle type
    type CandleData = {
      time: Time;
      open: number;
      high: number;
      low: number;
      close: number;
      volume: number;
    };
    
    // Convert to Lightweight-Charts format with validation (optimized processing)
    const converted = candlesArray.map((c: any): CandleData | null => {
      // Parse time value
      let timeValue: number;
      
      if (typeof c.time === 'number') {
        // If it's a timestamp in seconds, use as-is; if in milliseconds, convert
        timeValue = c.time > 10000000000 ? Math.floor(c.time / 1000) : c.time;
      } else if (typeof c.time === 'string') {
        // Parse date string
        const date = new Date(c.time);
        timeValue = Math.floor(date.getTime() / 1000);
      } else if (c.timestamp) {
        // Fallback to timestamp field
        timeValue = typeof c.timestamp === 'number' ? c.timestamp : Math.floor(new Date(c.timestamp).getTime() / 1000);
      } else {
        // Invalid time
        return null;
      }
      
      // Validate time is a valid number
      if (isNaN(timeValue) || !isFinite(timeValue) || timeValue <= 0) {
        console.warn('Invalid time value:', c);
        return null;
      }
      
      // Ensure time is an integer (Unix timestamp in seconds)
      const validatedTime = Math.floor(timeValue);
      
      // Convert to appropriate format based on timeframe
      let formattedTime: Time;
      if (useBusinessDay) {
        formattedTime = convertToBusinessDay(validatedTime) as Time;
      } else {
        formattedTime = validatedTime as Time;
      }
      
      // Validate OHLC values
      const open = Number(c.open ?? c.o ?? 0);
      const high = Number(c.high ?? c.h ?? 0);
      const low = Number(c.low ?? c.l ?? 0);
      const close = Number(c.close ?? c.c ?? 0);
      const volume = Number(c.volume ?? c.v ?? 0);
      
      // Additional validation: ensure OHLC are valid numbers
      if (isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close) || isNaN(volume)) {
        console.warn('Invalid OHLC values:', c);
        return null;
      }
      
      // Validate high >= low and high/low contain open/close
      if (high < low || high < Math.max(open, close) || low > Math.min(open, close)) {
        console.warn('Invalid OHLC relationship:', c);
        return null;
      }
      
      return {
        time: formattedTime,
        open,
        high,
        low,
        close,
        volume,
      };
    })
    .filter((c: CandleData | null): c is CandleData => c !== null) // Remove invalid entries
    .sort((a: CandleData, b: CandleData) => {
      // Sort by time - handle both BusinessDay and Unix timestamp formats
      if (useBusinessDay) {
        const aTime = a.time as BusinessDay;
        const bTime = b.time as BusinessDay;
        const aDate = new Date(aTime.year, aTime.month - 1, aTime.day).getTime();
        const bDate = new Date(bTime.year, bTime.month - 1, bTime.day).getTime();
        return aDate - bDate;
      } else {
        return (a.time as number) - (b.time as number);
      }
    });
    
    // Early return if all candles were invalid
    if (converted.length === 0 && candlesArray.length > 0) {
      console.error('All candles had invalid time values. Sample:', candlesArray[0]);
      return [];
    }
    
    // Return processed candles (already sorted and filtered)
    
    return converted;
  }, [chartData?.candles, timeframe]); // Optimized: only depend on candles array, not entire chartData object

  // Calculate all MAs
  const mas = useMemo(() => {
    if (candles.length === 0) return {};
    return {
      ma5: maSettings.ma5.enabled ? calculateMA(candles, 5) : [],
      ma10: maSettings.ma10.enabled ? calculateMA(candles, 10) : [],
      ma30: maSettings.ma30.enabled ? calculateMA(candles, 30) : [],
      ma60: maSettings.ma60.enabled ? calculateMA(candles, 60) : [],
    };
  }, [candles, maSettings]);

  // Fetch real-time quote data with request deduplication
  const fetchRealTimeQuote = useCallback(async () => {
    if (!activeSymbol) return;
    
    // Prevent duplicate concurrent requests
    const requestKey = `quote-${activeSymbol}`;
    
    try {
      const quote = await requestDeduplicator.deduplicate(
        requestKey,
        async () => {
          setQuoteLoading(true);
          try {
            const result = await api.getQuote(activeSymbol, 'NSE');
            return result;
          } finally {
            setQuoteLoading(false);
          }
        },
        5000 // 5 second deduplication window
      );
      
      if (quote && quote.last_price && quote.last_price > 0) {
        setRealTimeQuote(quote);
        console.log(`[ComprehensiveTradingPro] Real-time quote fetched:`, {
          symbol: activeSymbol,
          last_price: quote.last_price,
          open: quote.open,
          high: quote.high,
          low: quote.low,
          close: quote.close || quote.last_price
        });
      }
    } catch (error) {
      console.warn(`[ComprehensiveTradingPro] Failed to fetch real-time quote for ${activeSymbol}:`, error);
      // Don't show error toast, just use candle data as fallback
      setQuoteLoading(false);
    }
  }, [activeSymbol]);

  // Throttled version of fetchRealTimeQuote to prevent rapid calls
  const throttledFetchQuote = useThrottle(fetchRealTimeQuote, 3000); // Max once per 3 seconds

  // Fetch quote when symbol changes and set up auto-refresh (throttled)
  useEffect(() => {
    // Don't fetch quote if already loading chart data
    if (!loading) {
      throttledFetchQuote();
    }
    
    if (!autoRefresh) return;
    
    // Set up auto-refresh for quote (every 10 seconds - increased from 5 to reduce load)
    const quoteInterval = setInterval(() => {
      // Skip if chart is loading to prevent overload
      if (loading) {
        console.log('⏸️ [ComprehensiveTradingPro] Skipping quote refresh - chart loading');
        return;
      }
      throttledFetchQuote();
    }, 10000); // Refresh every 10 seconds (reduced frequency)
    
    return () => clearInterval(quoteInterval);
  }, [activeSymbol, autoRefresh, throttledFetchQuote, loading]);

  // Get current candle (last one) - prefer real-time quote data if available
  const currentCandle = useMemo(() => {
    // If we have real-time quote data, use it for OHLC (more accurate)
    if (realTimeQuote && realTimeQuote.last_price && realTimeQuote.last_price > 0) {
      const quoteCandle = {
        time: candles.length > 0 ? candles[candles.length - 1]?.time : Math.floor(Date.now() / 1000),
        open: realTimeQuote.open || realTimeQuote.last_price,
        high: realTimeQuote.high || realTimeQuote.last_price,
        low: realTimeQuote.low || realTimeQuote.last_price,
        close: realTimeQuote.close || realTimeQuote.last_price,
        volume: realTimeQuote.volume || 0
      };
      
      // Validate quote candle
      if (quoteCandle.open > 0 && quoteCandle.high > 0 && quoteCandle.low > 0 && quoteCandle.close > 0 &&
          quoteCandle.high >= quoteCandle.low &&
          quoteCandle.high >= Math.max(quoteCandle.open, quoteCandle.close) &&
          quoteCandle.low <= Math.min(quoteCandle.open, quoteCandle.close)) {
        console.log(`[ComprehensiveTradingPro] Using real-time quote for OHLC:`, quoteCandle);
        return quoteCandle;
      }
    }
    
    // Fallback to last candle from chart data
    if (candles.length === 0) return null;
    
    // Get the last candle
    const lastCandle = candles[candles.length - 1];
    
    // Validate the candle has valid OHLC values
    if (!lastCandle || 
        !lastCandle.open || !lastCandle.high || !lastCandle.low || !lastCandle.close ||
        isNaN(lastCandle.open) || isNaN(lastCandle.high) || isNaN(lastCandle.low) || isNaN(lastCandle.close) ||
        lastCandle.open <= 0 || lastCandle.high <= 0 || lastCandle.low <= 0 || lastCandle.close <= 0) {
      console.warn('Invalid currentCandle data:', lastCandle);
      // Try to find a valid candle from the end
      for (let i = candles.length - 1; i >= 0; i--) {
        const candle = candles[i];
        if (candle && candle.open > 0 && candle.high > 0 && candle.low > 0 && candle.close > 0 &&
            !isNaN(candle.open) && !isNaN(candle.high) && !isNaN(candle.low) && !isNaN(candle.close)) {
          console.log('Using valid candle at index', i, 'instead of last candle');
          return candle;
        }
      }
      return null;
    }
    
    // Additional validation: ensure OHLC relationships are correct
    if (lastCandle.high < lastCandle.low || 
        lastCandle.high < Math.max(lastCandle.open, lastCandle.close) || 
        lastCandle.low > Math.min(lastCandle.open, lastCandle.close)) {
      console.warn('Invalid OHLC relationships in currentCandle:', lastCandle);
      // Try to find a valid candle
      for (let i = candles.length - 2; i >= 0; i--) {
        const candle = candles[i];
        if (candle && candle.high >= candle.low && 
            candle.high >= Math.max(candle.open, candle.close) && 
            candle.low <= Math.min(candle.open, candle.close)) {
          console.log('Using valid candle at index', i, 'due to OHLC validation');
          return candle;
        }
      }
    }
    
    // Debug: Log current candle data to help identify price mismatches
    if (lastCandle) {
      console.log(`[ComprehensiveTradingPro] Using candle data for OHLC:`, {
        symbol: activeSymbol,
        open: lastCandle.open,
        high: lastCandle.high,
        low: lastCandle.low,
        close: lastCandle.close,
        time: lastCandle.time,
        totalCandles: candles.length
      });
    }
    
    return lastCandle;
  }, [candles, activeSymbol, realTimeQuote]);

  // Initialize main chart - defer to prevent blocking initial render
  useEffect(() => {
    if (!chartContainerRef.current) return;
    
    // Capture chartSettings at effect time to avoid stale closure
    const currentSettings = chartSettings;
    
    // Defer chart initialization to next frame to not block initial render
    const initTimer = requestAnimationFrame(() => {
    if (!chartContainerRef.current) return;

    // Create chart with settings (using captured value)
    const settings = currentSettings;
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { color: settings.theme.colors.background },
        textColor: settings.theme.colors.text,
      },
      grid: {
        vertLines: {
          color: settings.appearance.gridVisible ? settings.appearance.gridColor : 'transparent',
          style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
        },
        horzLines: {
          color: settings.appearance.gridVisible ? settings.appearance.gridColor : 'transparent',
          style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
        },
      },
      crosshair: {
        mode: settings.appearance.crosshairVisible ? 1 : 0,
        vertLine: {
          width: 1,
          color: settings.appearance.crosshairColor,
          style: settings.appearance.crosshairStyle === 'dashed' ? 1 : settings.appearance.crosshairStyle === 'dotted' ? 2 : 0,
          labelBackgroundColor: '#2962FF',
        },
        horzLine: {
          width: 1,
          color: settings.appearance.crosshairColor,
          style: settings.appearance.crosshairStyle === 'dashed' ? 1 : settings.appearance.crosshairStyle === 'dotted' ? 2 : 0,
          labelBackgroundColor: '#2962FF',
        },
      },
      localization: {
        timeFormatter: (businessDayOrTime: any) => {
          let timestamp: number;
          if (typeof businessDayOrTime === 'number') {
            timestamp = businessDayOrTime;
          } else {
            // BusinessDay format - create UTC date
            const date = new Date(Date.UTC(businessDayOrTime.year, businessDayOrTime.month - 1, businessDayOrTime.day));
            timestamp = Math.floor(date.getTime() / 1000);
          }
          // Convert UTC timestamp to IST (UTC+5:30)
          const utcDate = new Date(timestamp * 1000);
          const formatter = new Intl.DateTimeFormat('en-IN', {
            timeZone: 'Asia/Kolkata',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          });
          return formatter.format(utcDate);
        },
        // Format dates as DD/MM
        dateFormat: 'dd/MM',
      },
      timeScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        timeVisible: settings.scale.timeVisible,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        scaleMargins: settings.scale.scaleMargins,
      },
      leftPriceScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        scaleMargins: settings.scale.scaleMargins,
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

    // Add candlestick series with settings
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: settings.candlestick.upColor,
      downColor: settings.candlestick.downColor,
      borderVisible: settings.candlestick.borderVisible,
      wickUpColor: settings.candlestick.wickUpColor,
      wickDownColor: settings.candlestick.wickDownColor,
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Add MA series
    maSeriesRefs.current.ma5 = chart.addLineSeries({
      color: maSettings.ma5.color,
      lineWidth: 2,
      title: 'MA5',
      priceLineVisible: false,
      lastValueVisible: false,
    });

    maSeriesRefs.current.ma10 = chart.addLineSeries({
      color: maSettings.ma10.color,
      lineWidth: 2,
      title: 'MA10',
      priceLineVisible: false,
      lastValueVisible: false,
    });

    maSeriesRefs.current.ma30 = chart.addLineSeries({
      color: maSettings.ma30.color,
      lineWidth: 2,
      title: 'MA30',
      priceLineVisible: false,
      lastValueVisible: false,
    });

    maSeriesRefs.current.ma60 = chart.addLineSeries({
      color: maSettings.ma60.color,
      lineWidth: 2,
      title: 'MA60',
      priceLineVisible: false,
      lastValueVisible: false,
    });
    
    // Initialize chart overlay service
    chartOverlayService.initialize(chart, candlestickSeries);
    chartOverlayService.updateSettings(overlaySettings);
    
    // Add interactive event listeners to chart container (only once, no duplicates)
    // Handlers are stable via useCallback, so safe to add/remove
    if (chartContainerRef.current) {
      chartContainerRef.current.addEventListener('click', handleChartClick as any);
      chartContainerRef.current.addEventListener('mousemove', handleChartMouseMove as any);
      chartContainerRef.current.addEventListener('mouseleave', handleChartMouseLeave as any);
    }
    
    // Add resize listener after chart is initialized
    // handleChartResize is stable via useCallback, so safe to add/remove
    window.addEventListener('resize', handleChartResize);
    
    setOverlaysInitialized(true);
    });
    
    // Cleanup
    return () => {
      cancelAnimationFrame(initTimer);
      
      // Remove event listeners (handlers are stable via useCallback)
      if (chartContainerRef.current) {
        chartContainerRef.current.removeEventListener('click', handleChartClick as any);
        chartContainerRef.current.removeEventListener('mousemove', handleChartMouseMove as any);
        chartContainerRef.current.removeEventListener('mouseleave', handleChartMouseLeave as any);
      }
      
      window.removeEventListener('resize', handleChartResize);
      
      try {
        chartOverlayService.destroy();
      } catch (error) {
        console.debug('Chart overlay service destroy error:', error);
      }
      
      try {
        if (chartRef.current) {
          chartRef.current.remove();
        }
      } catch (error) {
        console.debug('Chart removal error:', error);
      }
      
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      maSeriesRefs.current = { ma5: null, ma10: null, ma30: null, ma60: null };
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount - chart settings changes handled via applyOptions

  // Initialize volume chart - defer to prevent blocking
  useEffect(() => {
    if (!volumeContainerRef.current) return;
    
    // Handle window resize - defined outside requestAnimationFrame to be accessible in cleanup
    const handleResize = () => {
      if (volumeContainerRef.current && volumeChartRef.current) {
        try {
          volumeChartRef.current.applyOptions({
            width: volumeContainerRef.current.clientWidth,
            height: volumeContainerRef.current.clientHeight,
          });
        } catch (error) {
          console.debug('Volume chart resize error:', error);
        }
      }
    };
    
    // Defer volume chart initialization
    const volumeInitTimer = requestAnimationFrame(() => {
      if (!volumeContainerRef.current) return;

      // Create volume chart with settings
      const settings = chartSettings;
      const volumeChart = createChart(volumeContainerRef.current, {
      width: volumeContainerRef.current.clientWidth,
      height: volumeContainerRef.current.clientHeight,
      layout: {
        background: { color: settings.theme.colors.background },
        textColor: settings.theme.colors.text,
      },
      grid: {
        vertLines: {
          color: settings.appearance.gridVisible ? settings.appearance.gridColor : 'transparent',
          style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
        },
        horzLines: {
          color: settings.appearance.gridVisible ? settings.appearance.gridColor : 'transparent',
          style: settings.appearance.gridStyle === 'dashed' ? 1 : settings.appearance.gridStyle === 'dotted' ? 2 : 0,
        },
      },
      localization: {
        timeFormatter: (businessDayOrTime: any) => {
          let timestamp: number;
          if (typeof businessDayOrTime === 'number') {
            timestamp = businessDayOrTime;
          } else {
            // BusinessDay format - create UTC date
            const date = new Date(Date.UTC(businessDayOrTime.year, businessDayOrTime.month - 1, businessDayOrTime.day));
            timestamp = Math.floor(date.getTime() / 1000);
          }
          // Convert UTC timestamp to IST (UTC+5:30)
          const utcDate = new Date(timestamp * 1000);
          const formatter = new Intl.DateTimeFormat('en-IN', {
            timeZone: 'Asia/Kolkata',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          });
          return formatter.format(utcDate);
        },
        // Format dates as DD/MM
        dateFormat: 'dd/MM',
      },
      timeScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
        timeVisible: settings.scale.timeVisible,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: settings.appearance.borderVisible ? settings.appearance.borderColor : 'transparent',
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    volumeChartRef.current = volumeChart;

    // Add volume histogram series with settings
    const volumeSeries = volumeChart.addHistogramSeries({
      color: settings.candlestick.upColor,
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    volumeSeriesRef.current = volumeSeries;

    // Sync time scales
    if (chartRef.current) {
      try {
      chartRef.current.timeScale().subscribeVisibleLogicalRangeChange((timeRange) => {
          try {
            if (volumeChartRef.current) {
              volumeChartRef.current.timeScale().setVisibleLogicalRange(timeRange as any);
            }
          } catch (error) {
            console.debug('Volume chart sync error:', error);
          }
      });
      } catch (error) {
        console.debug('Chart timeScale subscription error:', error);
      }

      try {
        if (volumeChartRef.current) {
          volumeChartRef.current.timeScale().subscribeVisibleLogicalRangeChange((timeRange) => {
            try {
              if (chartRef.current) {
                chartRef.current.timeScale().setVisibleLogicalRange(timeRange as any);
              }
            } catch (error) {
              console.debug('Main chart sync error:', error);
            }
          });
        }
      } catch (error) {
        console.debug('Volume chart timeScale subscription error:', error);
      }
    }

    // Add resize listener after chart is created
    window.addEventListener('resize', handleResize);
    });
    
    // Cleanup
    return () => {
      cancelAnimationFrame(volumeInitTimer);
      window.removeEventListener('resize', handleResize);
      try {
        if (volumeChartRef.current) {
          volumeChartRef.current.remove();
        }
      } catch (error) {
        console.debug('Volume chart removal error:', error);
      }
      volumeChartRef.current = null;
      volumeSeriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update chart data
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || candles.length === 0) return;
    
    // Check if charts are still valid
    if (!chartRef.current || !volumeChartRef.current) return;

    try {
      // Check if we need BusinessDay format
      const useBusinessDay = requiresBusinessDayFormat(timeframe);
      
      // Filter and validate candles - ensure all have valid time values
      const validCandles = candles.filter((c: any) => {
        // Validate time based on format
        let timeValid = false;
        if (useBusinessDay) {
          const time = c.time as BusinessDay;
          timeValid = (
            time !== undefined &&
            time !== null &&
            typeof time === 'object' &&
            typeof time.year === 'number' &&
            typeof time.month === 'number' &&
            typeof time.day === 'number'
          );
        } else {
          const time = c.time as number;
          timeValid = (
            time !== undefined &&
            time !== null &&
            !isNaN(time) &&
            isFinite(time) &&
            time > 0
          );
        }
        
        return (
          timeValid &&
          typeof c.open === 'number' &&
          typeof c.high === 'number' &&
          typeof c.low === 'number' &&
          typeof c.close === 'number'
        );
      });

      if (validCandles.length === 0) {
        console.error('No valid candles to display');
        return;
      }

      if (validCandles.length !== candles.length) {
        console.warn(`Filtered out ${candles.length - validCandles.length} invalid candles`);
      }

      // Set candlestick data - time format is already handled in candles useMemo
      const candlestickData: CandlestickData[] = validCandles.map((c: any) => ({
        time: c.time,
        open: Number(c.open),
        high: Number(c.high),
        low: Number(c.low),
        close: Number(c.close),
      }));

      // Deduplicate and sort candlestick data
      let uniqueCandlestickData = deduplicateAndSortCandlestickData(candlestickData, useBusinessDay);
      
      // Final validation: Ensure data is properly sorted before setting
      // This is a critical safety check for Lightweight Charts
      const getTimeValue = (item: any): number => {
        if (useBusinessDay) {
          const time = item.time as BusinessDay;
          return new Date(time.year, time.month - 1, time.day).getTime();
        } else {
          return Number(item.time);
        }
      };
      
      // Final sort to ensure ascending order
      uniqueCandlestickData = [...uniqueCandlestickData].sort((a, b) => {
        const timeA = getTimeValue(a);
        const timeB = getTimeValue(b);
        if (isNaN(timeA) || isNaN(timeB)) {
          console.warn('Invalid time in final sort:', a.time, b.time);
          return 0;
        }
        return timeA - timeB;
      });
      
      // Validate final data before setting
      for (let i = 1; i < uniqueCandlestickData.length; i++) {
        const prevTime = getTimeValue(uniqueCandlestickData[i - 1]);
        const currTime = getTimeValue(uniqueCandlestickData[i]);
        if (currTime < prevTime) {
          console.error(`Final validation failed: data out of order at index ${i}: time=${currTime}, prev time=${prevTime}`);
          // This should not happen, but if it does, we need to fix it
          uniqueCandlestickData = [...uniqueCandlestickData].sort((a, b) => getTimeValue(a) - getTimeValue(b));
          break;
        }
      }
      
      // Check if chart is still valid before setting data
      if (candlestickSeriesRef.current && chartRef.current) {
        try {
          // Final safety check: Validate data is sorted before setting
          if (uniqueCandlestickData.length > 1) {
            for (let i = 1; i < uniqueCandlestickData.length; i++) {
              const prevTime = getTimeValue(uniqueCandlestickData[i - 1]);
              const currTime = getTimeValue(uniqueCandlestickData[i]);
              if (currTime <= prevTime) {
                console.error(`CRITICAL: Data not sorted before setData! Index ${i}: time=${currTime}, prev time=${prevTime}`);
                // Emergency re-sort
                uniqueCandlestickData = [...uniqueCandlestickData].sort((a, b) => getTimeValue(a) - getTimeValue(b));
                console.log('Emergency re-sort completed');
                break;
              }
            }
          }
          
          candlestickSeriesRef.current.setData(uniqueCandlestickData);
          console.log(`✅ Successfully set ${uniqueCandlestickData.length} candles to chart`);
        } catch (error: any) {
          console.error('Error setting candlestick data:', error);
          if (error.message && error.message.includes('asc ordered')) {
            console.error('Data ordering error detected. Attempting to fix...');
            // Try one more time with a fresh sort
            const emergencySorted = [...uniqueCandlestickData].sort((a, b) => getTimeValue(a) - getTimeValue(b));
            try {
              candlestickSeriesRef.current.setData(emergencySorted);
              console.log('Emergency sort and retry succeeded');
            } catch (retryError) {
              console.error('Emergency retry also failed:', retryError);
            }
          }
          return;
        }
      }

      // Set volume data with matching time values (time format already handled)
      const volumeData: HistogramData[] = validCandles.map((c: any) => ({
        time: c.time,
        value: Number(c.volume || 0),
        color: c.close >= c.open ? '#26a69a80' : '#ef535080',
      }));

      // Deduplicate and sort volume data
      const uniqueVolumeData = deduplicateAndSortHistogramData(volumeData, requiresBusinessDayFormat(timeframe));
      
      // Check if volume chart is still valid before setting data
      if (volumeSeriesRef.current && volumeChartRef.current) {
        try {
          volumeSeriesRef.current.setData(uniqueVolumeData);
        } catch (error) {
          console.error('Error setting volume data:', error);
          return;
        }
      }

      // Set visible range to show only the filtered candles (selected period)
      try {
        if (chartRef.current && uniqueCandlestickData && uniqueCandlestickData.length > 0) {
          const lastCandleTime = uniqueCandlestickData[uniqueCandlestickData.length - 1].time;
          const firstCandleTime = uniqueCandlestickData[0].time;
          
          console.log(`📊 [ComprehensiveTradingPro] Setting visible range: ${new Date(Number(firstCandleTime) * 1000).toISOString()} to ${new Date(Number(lastCandleTime) * 1000).toISOString()}`);
          console.log(`📊 [ComprehensiveTradingPro] Total candles in chart: ${uniqueCandlestickData.length}`);
          
          // Set visible range to show all filtered candles
          chartRef.current.timeScale().setVisibleRange({
            from: firstCandleTime as Time,
            to: lastCandleTime as Time,
          });
        }
        
        if (volumeChartRef.current && uniqueVolumeData && uniqueVolumeData.length > 0) {
          const lastCandleTime = uniqueVolumeData[uniqueVolumeData.length - 1].time;
          const firstCandleTime = uniqueVolumeData[0].time;
          
          volumeChartRef.current.timeScale().setVisibleRange({
            from: firstCandleTime as Time,
            to: lastCandleTime as Time,
          });
        }
      } catch (error) {
        // Chart might be disposed, ignore
        console.debug('Chart setVisibleRange error:', error);
      }
    } catch (error) {
      console.error('Error setting chart data:', error);
      console.error('Sample candle:', candles[0]);
    }
  }, [candles]);

  // Update MA lines
  useEffect(() => {
    if (!maSeriesRefs.current.ma5 || candles.length === 0 || !chartRef.current) return;

    // Check if we need BusinessDay format
    const useBusinessDay = requiresBusinessDayFormat(timeframe);

    // Helper function to validate and format MA data
    const validateMAData = (maData: LineData[]): LineData[] => {
      if (!maData || maData.length === 0) return [];
      const filtered = maData
        .filter((point: any) => {
          // Validate time based on format
          if (useBusinessDay) {
            const time = point.time as BusinessDay;
            return (
              time !== undefined &&
              time !== null &&
              typeof time.year === 'number' &&
              typeof time.month === 'number' &&
              typeof time.day === 'number' &&
              typeof point.value === 'number' &&
              !isNaN(point.value) &&
              isFinite(point.value)
            );
          } else {
            const time = point.time as number;
            return (
              time !== undefined &&
              time !== null &&
              !isNaN(time) &&
              isFinite(time) &&
              time > 0 &&
              typeof point.value === 'number' &&
              !isNaN(point.value) &&
              isFinite(point.value)
            );
          }
        })
        .map((point: any) => ({
          time: point.time, // Already in correct format from candles
          value: Number(point.value),
        }));
      
      // Deduplicate and sort
      return deduplicateAndSortLineData(filtered, useBusinessDay);
    };

    // Update MA5
    if (maSettings.ma5.enabled && mas.ma5 && chartRef.current) {
      const validMA5 = validateMAData(mas.ma5);
      if (validMA5.length > 0 && maSeriesRefs.current.ma5) {
        try {
          maSeriesRefs.current.ma5.setData(validMA5);
          maSeriesRefs.current.ma5.applyOptions({
          color: maSettings.ma5.color,
          visible: true,
        });
        } catch (error) {
          console.debug('Error updating MA5:', error);
        }
      }
    } else if (maSeriesRefs.current.ma5) {
      try {
        maSeriesRefs.current.ma5.applyOptions({ visible: false });
      } catch (error) {
        console.debug('Error hiding MA5:', error);
      }
    }

    // Update MA10
    if (maSettings.ma10.enabled && mas.ma10 && chartRef.current) {
      const validMA10 = validateMAData(mas.ma10);
      if (validMA10.length > 0 && maSeriesRefs.current.ma10) {
        try {
          maSeriesRefs.current.ma10.setData(validMA10);
          maSeriesRefs.current.ma10.applyOptions({
          color: maSettings.ma10.color,
          visible: true,
        });
        } catch (error) {
          console.debug('Error updating MA10:', error);
        }
      }
    } else if (maSeriesRefs.current.ma10) {
      try {
        maSeriesRefs.current.ma10.applyOptions({ visible: false });
      } catch (error) {
        console.debug('Error hiding MA10:', error);
      }
    }

    // Update MA30
    if (maSettings.ma30.enabled && mas.ma30 && chartRef.current) {
      const validMA30 = validateMAData(mas.ma30);
      if (validMA30.length > 0 && maSeriesRefs.current.ma30) {
        try {
          maSeriesRefs.current.ma30.setData(validMA30);
          maSeriesRefs.current.ma30.applyOptions({
          color: maSettings.ma30.color,
          visible: true,
        });
        } catch (error) {
          console.debug('Error updating MA30:', error);
        }
      }
    } else if (maSeriesRefs.current.ma30) {
      try {
        maSeriesRefs.current.ma30.applyOptions({ visible: false });
      } catch (error) {
        console.debug('Error hiding MA30:', error);
      }
    }

    // Update MA60
    if (maSettings.ma60.enabled && mas.ma60 && chartRef.current) {
      const validMA60 = validateMAData(mas.ma60);
      if (validMA60.length > 0 && maSeriesRefs.current.ma60) {
        try {
          maSeriesRefs.current.ma60.setData(validMA60);
          maSeriesRefs.current.ma60.applyOptions({
          color: maSettings.ma60.color,
          visible: true,
        });
        } catch (error) {
          console.debug('Error updating MA60:', error);
        }
      }
    } else if (maSeriesRefs.current.ma60) {
      try {
        maSeriesRefs.current.ma60.applyOptions({ visible: false });
      } catch (error) {
        console.debug('Error hiding MA60:', error);
      }
    }
  }, [mas, maSettings]);

  // Format large numbers
  const formatVolume = (vol: number) => {
    if (vol >= 1000000) return (vol / 1000000).toFixed(2) + 'M';
    if (vol >= 1000) return (vol / 1000).toFixed(2) + 'K';
    return vol.toFixed(0);
  };

  // Get MA values for current candle
  const currentMAValues = useMemo(() => {
    if (!mas.ma5 || mas.ma5.length === 0) return {};
    return {
      ma5: mas.ma5[mas.ma5.length - 1]?.value,
      ma10: mas.ma10?.[mas.ma10.length - 1]?.value,
      ma30: mas.ma30?.[mas.ma30.length - 1]?.value,
      ma60: mas.ma60?.[mas.ma60.length - 1]?.value,
    };
  }, [mas]);

  // Show loading overlay (non-blocking) - page still renders
  // Don't block the entire page - show loading indicator but allow interaction

  return (
    <div className={`bg-[#131722] text-white ${isFullscreen ? 'fixed inset-0 z-50 flex flex-col h-screen' : 'min-h-screen'}`}>
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between px-2 sm:px-4 py-2 bg-[#1e222d] border-b border-[#2a2e39] sticky top-0 z-40">
        {/* Left Section - Symbol and Timeframes */}
        <div className="flex items-center gap-2 sm:gap-4 flex-1 min-w-0">
          {/* Mobile Menu Button */}
          <button 
            onClick={() => setShowMobileDrawer(true)}
            className="p-2 hover:bg-[#2a2e39] rounded min-w-[44px] min-h-[44px] flex items-center justify-center lg:hidden"
            aria-label="Open menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          {/* Desktop Menu Button */}
          <button className="hidden lg:block p-2 hover:bg-[#2a2e39] rounded">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Symbol Selector - Dropdown with Stocks and Indexes */}
          <div className="relative flex-1 min-w-0">
              <StockSelector 
                value={activeSymbol}
                onChange={(symbol) => {
                  setActiveSymbol(symbol);
                setSearchParams({ symbol, timeframe, period });
                // Load chart data for the new symbol
                loadChartData(period, timeframe);
                }}
                showNavigateButton={false}
              className="w-full sm:w-64"
              />
          </div>

          {/* Buy/Sell Buttons - Hidden on mobile */}
          {currentCandle && (
            <div className="hidden sm:flex items-center gap-2">
              <EnhancedOrderPlacement
                symbol={activeSymbol}
                currentPrice={currentCandle.close}
                onOrderPlaced={() => {
                  toast.success('Order placed successfully!');
                  if (showPortfolio) {
                    // Portfolio will auto-refresh
                  }
                }}
                size="sm"
              />
            </div>
          )}

          {/* Timeframe Dropdown */}
          <div className="hidden sm:flex items-center gap-2">
            <label className="text-sm text-gray-400 hidden md:inline">Timeframe:</label>
            <select
              value={timeframe}
              onChange={(e) => {
                const newTimeframe = e.target.value;
                setTimeframe(newTimeframe);
                loadChartData(period, newTimeframe);
              }}
              className="bg-[#2a2e39] text-white px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm font-medium border border-[#363a45] focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-[#363a45] transition-colors cursor-pointer min-h-[44px]"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label}
                </option>
              ))}
            </select>
          </div>

          {/* Period/Range Dropdown */}
          <div className="hidden sm:flex items-center gap-2">
            <label className="text-sm text-gray-400 hidden md:inline">Period:</label>
            <select
              value={period}
              onChange={(e) => {
                const newPeriod = e.target.value;
                setPeriod(newPeriod);
                loadChartData(newPeriod, timeframe);
              }}
              className="bg-[#2a2e39] text-white px-2 sm:px-3 py-1.5 sm:py-2 rounded text-xs sm:text-sm font-medium border border-[#363a45] focus:outline-none focus:ring-2 focus:ring-blue-500 hover:bg-[#363a45] transition-colors cursor-pointer min-h-[44px]"
            >
              {periods.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Right Section - Tools - Hidden on mobile, shown in drawer */}
        <div className="hidden lg:flex items-center gap-2">
          <button
            onClick={() => setShowWatchlist(!showWatchlist)}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm text-gray-300 hover:text-white transition-colors"
            title="Watchlist"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            Watchlist
          </button>

          <button
            onClick={() => {
              setShowChat(!showChat);
              if (!showChat) setChatMinimized(false);
            }}
            className={`flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm transition-colors ${
              showChat ? 'bg-green-500/20 text-green-400' : 'text-gray-300 hover:text-white'
            }`}
            title="AI Chat"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Chat
          </button>

          <button
            onClick={() => setShowMarketOverview(!showMarketOverview)}
            className={`flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm transition-colors ${
              showMarketOverview ? 'bg-purple-500/20 text-purple-400' : 'text-gray-300 hover:text-white'
            }`}
            title="Market Overview"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Market
          </button>

          <button
            onClick={() => navigate('/portfolio-allocation')}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm transition-colors text-gray-300 hover:text-white"
            title="Portfolio"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Portfolio
          </button>

          <button
            onClick={() => setShowMultiTimeframe(!showMultiTimeframe)}
            className={`flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm transition-colors ${
              showMultiTimeframe ? 'bg-blue-500/20 text-blue-400' : 'text-gray-300 hover:text-white'
            }`}
            title="Multi-Timeframe Analysis"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z" />
            </svg>
            Multi-TF
          </button>

          <button
            onClick={() => setShowEnhancedIndicatorSelector(true)}
            className={`flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm ${
              indicators.some(ind => ind.visible) ? 'bg-blue-500/20 text-blue-400' : 'text-gray-300 hover:text-white'
            }`}
            title="Technical Indicators"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
            Indicators ({indicators.filter(ind => ind.visible).length})
          </button>

          <button
            onClick={() => setShowFibonacci(!showFibonacci)}
            className={`flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm transition-colors ${
              showFibonacci ? 'bg-purple-500/20 text-purple-400' : 'text-gray-300 hover:text-white'
            }`}
            title="Fibonacci Retracements"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Fibonacci
          </button>

          <button className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Timezone
          </button>

          <button
            onClick={() => setShowChartSettings(!showChartSettings)}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm text-gray-300 hover:text-white transition-colors"
            title="Chart Settings"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Settings
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Setting
          </button>

          <Suspense fallback={<div className="w-8 h-8" />}>
            <ChartExportButton
              chartContainerRef={chartContainerRef}
              chartWrapperRef={chartWrapperRef}
              symbol={activeSymbol}
              timeframe={timeframe}
            />
          </Suspense>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            Full Screen
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={`flex ${isFullscreen ? 'flex-1 overflow-hidden' : ''}`}>
        {/* Left Sidebar - Drawing Tools (Hidden on mobile) */}
        <div className="hidden lg:block">
          <Suspense fallback={<div className="w-16" />}>
            <ChartDrawingTools
              chartContainerRef={chartContainerRef}
              symbol={activeSymbol}
              chartApi={chartRef.current}
              candlestickSeries={candlestickSeriesRef.current}
              onDrawingComplete={(drawing) => {
                console.log('Drawing completed:', drawing);
                // Update overlay props immediately with new drawing
                setDrawingOverlayProps(prev => {
                  if (!prev) return null;
                  return {
                    ...prev,
                    drawings: [...prev.drawings, drawing]
                  };
                });
              }}
              renderOverlay={(overlayProps) => {
                // Update state immediately when overlay props change
                setDrawingOverlayProps(overlayProps);
                return null; // Don't render here, render in chart container
              }}
            />
          </Suspense>
        </div>

        {/* Chart Area */}
        <div className={`flex-1 flex flex-col ${isFullscreen ? '' : 'h-[400px] sm:h-[500px] lg:h-[600px]'}`}>
          {/* Stock Info Bar (Groww Terminal Style) */}
          {currentCandle && (
            <div className="px-4 py-2 bg-white text-gray-900 border-b border-gray-200 flex items-center justify-between text-sm">
              <div className="flex items-center gap-6">
                <div>
                  <span className="font-semibold">{activeSymbol}</span>
                  <span className="text-gray-500 ml-2">• {timeframe} • NSE</span>
                </div>
                <div className="flex items-center gap-6">
                  <div>
                    <span className="text-gray-500">O:</span>
                    <span className="ml-1 font-medium">{currentCandle.open.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">H:</span>
                    <span className="ml-1 font-medium">{currentCandle.high.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">L:</span>
                    <span className="ml-1 font-medium">{currentCandle.low.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">C:</span>
                    <span className={`ml-1 font-medium ${currentCandle.close >= currentCandle.open ? 'text-green-600' : 'text-red-600'}`}>
                      {currentCandle.close.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className={`font-medium ${currentCandle.close >= currentCandle.open ? 'text-green-600' : 'text-red-600'}`}>
                      {currentCandle.close >= currentCandle.open ? '+' : ''}{(currentCandle.close - currentCandle.open).toFixed(2)} ({((currentCandle.close - currentCandle.open) / currentCandle.open * 100).toFixed(2)}%)
                    </span>
                  </div>
                  <div className="text-gray-500">
                    Volume SMA 9 {formatVolume(currentCandle.volume)}
                  </div>
                </div>
              </div>
              <button className="p-1 hover:bg-gray-100 rounded">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
          )}
          
          {/* OHLCV Data Display (Hidden - Original style kept for reference) */}
          {currentCandle && (
            <div className="px-2 sm:px-4 py-2 bg-[#1e222d] border-b border-[#2a2e39] flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-6 text-xs sm:text-sm overflow-x-auto hidden">
              <div className="flex flex-wrap gap-2 sm:gap-6">
                <span className="text-gray-400">
                  Time: <span className="text-white">{new Date((currentCandle.time as number) * 1000).toLocaleDateString()}</span>
                </span>
                <span className="text-gray-400">
                  Open: <span className="text-white">{currentCandle.open.toFixed(2)}</span>
                </span>
                <span className="text-gray-400">
                  High: <span className="text-white">{currentCandle.high.toFixed(2)}</span>
                </span>
                <span className="text-gray-400">
                  Low: <span className="text-white">{currentCandle.low.toFixed(2)}</span>
                </span>
                <span className="text-gray-400">
                  Close: <span className={currentCandle.close >= currentCandle.open ? 'text-green-500' : 'text-red-500'}>
                    {currentCandle.close.toFixed(2)}
                  </span>
                </span>
                <span className="text-gray-400">
                  Volume: <span className="text-white">{formatVolume(currentCandle.volume)}</span>
                </span>
              </div>

              {/* MA Values */}
              <div className="flex flex-wrap gap-2 sm:gap-4 ml-0 sm:ml-auto">
                {maSettings.ma5.enabled && currentMAValues.ma5 && (
                  <span style={{ color: maSettings.ma5.color }}>
                    MA5: {currentMAValues.ma5.toFixed(2)}
                  </span>
                )}
                {maSettings.ma10.enabled && currentMAValues.ma10 && (
                  <span style={{ color: maSettings.ma10.color }}>
                    MA10: {currentMAValues.ma10.toFixed(2)}
                  </span>
                )}
                {maSettings.ma30.enabled && currentMAValues.ma30 && (
                  <span style={{ color: maSettings.ma30.color }}>
                    MA30: {currentMAValues.ma30.toFixed(2)}
                  </span>
                )}
                {maSettings.ma60.enabled && currentMAValues.ma60 && (
                  <span style={{ color: maSettings.ma60.color }}>
                    MA60: {currentMAValues.ma60.toFixed(2)}
                  </span>
                )}
              </div>
              
              {/* Data Source Indicator & Auto-Refresh */}
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 ml-0 sm:ml-6 pl-0 sm:pl-6 border-0 sm:border-l border-[#2a2e39] w-full sm:w-auto mt-2 sm:mt-0">
                {/* Data Source Badge */}
                <div className={`px-2 py-1 rounded text-xs font-semibold ${
                  dataSource === 'YAHOO_FINANCE' 
                    ? 'bg-green-500/20 text-green-500 border border-green-500/30' 
                    : dataSource === 'MOCK'
                    ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'
                    : 'bg-gray-500/20 text-gray-500 border border-gray-500/30'
                }`}>
                  {dataSource === 'YAHOO_FINANCE' ? '🟢 LIVE' : dataSource === 'MOCK' ? '⚠️ MOCK' : '⏳ LOADING'}
                </div>
                
                {/* Last Update Time */}
                {lastUpdateTime && (
                  <span className="text-xs text-gray-500">
                    Data: {lastUpdateTime.toLocaleTimeString()}
                  </span>
                )}
                {/* Last Analysis Time */}
                {lastAnalysisTime && (
                  <span className="text-xs text-green-400 ml-2">
                    Analysis: {lastAnalysisTime.toLocaleTimeString()}
                  </span>
                )}
                
                {/* Auto-Refresh Toggle */}
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                    autoRefresh 
                      ? 'bg-blue-500/20 text-blue-500 border border-blue-500/30' 
                      : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                  }`}
                  title={autoRefresh ? 'Auto-refresh enabled (30s)' : 'Auto-refresh disabled'}
                >
                  <svg className={`w-3 h-3 ${autoRefresh ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {autoRefresh ? 'Auto' : 'Manual'}
                </button>
                
                {/* Manual Refresh Button */}
                <button
                  onClick={() => loadChartData()}
                  disabled={loading}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-gray-500/20 text-gray-400 border border-gray-500/30 hover:bg-gray-500/30 disabled:opacity-50"
                  title="Refresh now"
                >
                  <svg className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>
            </div>
          )}

          {/* Chart Wrapper for Export - Contains both main chart and volume */}
          <div ref={chartWrapperRef} className="flex-1 flex flex-col">
            <div className="flex-1 flex gap-4">
              {/* Main Chart Area */}
              <div className="flex-1 flex flex-col">
                {/* Main Chart - Lightweight-Charts */}
                <div className="flex-1 relative">
                  {loading && !chartData && (
                    <div className="absolute inset-0 flex items-center justify-center bg-[#131722] z-10">
                      <div className="flex flex-col items-center gap-3">
                        <div className="animate-spin h-10 w-10 border-3 border-blue-500 border-t-transparent rounded-full" />
                        <p className="text-sm text-gray-400">Loading chart data...</p>
                      </div>
                    </div>
                  )}
                  {loading && chartData && (
                    <div className="absolute top-2 right-2 z-20 flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                      <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
                      <span className="text-xs text-blue-400">Updating...</span>
                    </div>
                  )}
                  <div ref={chartContainerRef} className="w-full h-full relative">
                    {/* Drawing Canvas Overlay - Rendered here to overlay the chart */}
                    {drawingOverlayProps && (
                      <div 
                        className="absolute inset-0"
                        style={{ 
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          pointerEvents: drawingOverlayProps.activeTool ? 'auto' : 'none',
                          zIndex: 10
                        }}
                      >
                        <Suspense fallback={null}>
                          <DrawingCanvasOverlay
                            chartContainerRef={chartContainerRef}
                            {...drawingOverlayProps}
                          />
                        </Suspense>
                      </div>
                    )}
                    
                    {/* Indicators Overlay - Only render if indicators are visible */}
                    {chartRef.current && candlestickSeriesRef.current && chartData?.candles && indicators.some(ind => ind.visible) && (
                      <Suspense fallback={null}>
                        <LightweightChartIndicators
                          chart={chartRef.current}
                          candlestickSeries={candlestickSeriesRef.current}
                          data={indicatorDataMemo}
                          indicators={indicators}
                        />
                      </Suspense>
                    )}
                  </div>
                  
                  {/* Sentiment Overlay - Only render when chart has data */}
                  {showSentimentOverlay && chartRef.current && candlestickSeriesRef.current && chartData && (
                    <Suspense fallback={null}>
                      <SentimentOverlay
                        symbol={activeSymbol}
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        visible={showSentimentOverlay}
                      />
                    </Suspense>
                  )}
                  
                  {/* ML Signals Overlay - Only render when chart has data */}
                  {showMLSignalsOverlay && chartRef.current && candlestickSeriesRef.current && chartData && (
                    <Suspense fallback={null}>
                      <MLSignalsOverlay
                        symbol={activeSymbol}
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        visible={showMLSignalsOverlay}
                      />
                    </Suspense>
                  )}
                  
                  {/* Pattern Visualization Overlay - Only render when chart has data */}
                  {showPatternVisualization && chartRef.current && candlestickSeriesRef.current && chartData && (
                    <Suspense fallback={null}>
                      <PatternVisualization
                        symbol={activeSymbol}
                        timeframe={timeframe}
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        visible={showPatternVisualization}
                      />
                    </Suspense>
                  )}
                  
                  {/* Advanced Chart Analysis - Only render when chart has data */}
                  {chartRef.current && candlestickSeriesRef.current && candles.length > 0 && chartData && (
                    <Suspense fallback={null}>
                      <AdvancedChartAnalysis
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        candles={candles}
                        symbol={activeSymbol}
                        timeframe={timeframe}
                      />
                    </Suspense>
                  )}
                  
                  {/* Fibonacci Retracement Overlay */}
                  {showFibonacci && chartRef.current && candlestickSeriesRef.current && candles.length > 0 && (
                    <Suspense fallback={null}>
                      <FibonacciOverlay
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        candles={candles}
                        symbol={activeSymbol}
                        visible={showFibonacci}
                      />
                    </Suspense>
                  )}
                  
                  {/* Pattern Detection Overlay */}
                  {showPatternDetection && chartRef.current && candlestickSeriesRef.current && (
                    <Suspense fallback={null}>
                      <PatternDetectionOverlay
                        chartApi={chartRef.current}
                        candlestickSeries={candlestickSeriesRef.current}
                        symbol={activeSymbol}
                        timeframe={timeframe}
                        visible={showPatternDetection}
                      />
                    </Suspense>
                  )}
                </div>

                {/* Volume Chart - Lightweight-Charts */}
                <div className="h-32 border-t border-[#2a2e39] relative">
                  <div className="absolute top-2 left-4 text-xs text-gray-400 flex gap-4 z-10">
                    <span>VOLUME</span>
                    {currentCandle && (
                      <span className="text-red-500">{formatVolume(currentCandle.volume)}</span>
                    )}
                  </div>
                  <div ref={volumeContainerRef} className="w-full h-full" />
                </div>
              </div>

              {/* Market Overview Panel - Desktop Sidebar */}
              {showMarketOverview && (
                <div className="hidden lg:block w-80 border-l border-[#2a2e39]">
                  <Suspense fallback={<ComponentLoader message="Loading market overview..." />}>
                    <MarketOverviewPanel
                      symbol={activeSymbol}
                      onClose={() => setShowMarketOverview(false)}
                    />
                  </Suspense>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar - Navigation (Groww Terminal Style) */}
        {showRightSidebar && (
          <div className="hidden lg:flex flex-col w-12 bg-white border-l border-gray-200">
            {/* Action Buttons */}
            <div className="flex flex-col items-center py-2 border-b border-gray-200">
              <button className="w-8 h-8 mb-2 flex items-center justify-center hover:bg-gray-100 rounded">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
              <button className="w-8 h-8 mb-2 flex items-center justify-center hover:bg-gray-100 rounded text-green-600 font-bold">
                B
              </button>
              <button className="w-8 h-8 mb-2 flex items-center justify-center hover:bg-gray-100 rounded text-red-600 font-bold">
                S
              </button>
              <button 
                onClick={() => setShowSettings(!showSettings)}
                className="w-8 h-8 mb-2 flex items-center justify-center hover:bg-gray-100 rounded"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <button className="w-8 h-8 mb-2 flex items-center justify-center hover:bg-gray-100 rounded">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <button 
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="w-8 h-8 mb-2 flex items-center justify-center hover:bg-gray-100 rounded"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
      </div>

            {/* Navigation Menu */}
            <div className="flex-1 flex flex-col py-2">
              <button
                onClick={() => { setRightSidebarTab('watchlist'); setShowWatchlist(true); }}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'watchlist' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Watchlist"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
              <button
                onClick={() => { setRightSidebarTab('positions'); setShowPortfolio(true); }}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'positions' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Positions"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
              <button
                onClick={() => setRightSidebarTab('orders')}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'orders' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Orders"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </button>
              <button
                onClick={() => setRightSidebarTab('chain')}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'chain' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Chain"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
              <button
                onClick={() => setRightSidebarTab('depth')}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'depth' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Depth"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </button>
              <button
                onClick={() => setRightSidebarTab('holdings')}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'holdings' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Holdings"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </button>
              <button
                onClick={() => setRightSidebarTab('balance')}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'balance' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Balance"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </button>
              <button
                onClick={() => setRightSidebarTab('layout')}
                className={`w-10 h-10 mb-1 flex items-center justify-center rounded-l-lg ${rightSidebarTab === 'layout' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}`}
                title="Layout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Bottom Sheets */}
      {isMobile && (
        <>
          <MobileBottomSheet
            isOpen={showMarketOverview}
            onClose={() => setShowMarketOverview(false)}
            title="Market Overview"
          >
            <MarketOverviewPanel
              symbol={activeSymbol}
              onClose={() => setShowMarketOverview(false)}
            />
          </MobileBottomSheet>

          <MobileBottomSheet
            isOpen={showPortfolio}
            onClose={() => setShowPortfolio(false)}
            title="Portfolio"
          >
            <Suspense fallback={<ComponentLoader message="Loading portfolio..." />}>
              <PortfolioPanel
                visible={showPortfolio}
                onClose={() => setShowPortfolio(false)}
              />
            </Suspense>
          </MobileBottomSheet>
        </>
      )}

      {/* Desktop Panels (Alternative Position) */}
      {!isMobile && showMarketOverview && (
        <div className="absolute top-16 right-4 w-80 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50 max-h-[calc(100vh-5rem)]">
          <Suspense fallback={<ComponentLoader message="Loading market overview..." />}>
            <MarketOverviewPanel
              symbol={activeSymbol}
              onClose={() => setShowMarketOverview(false)}
            />
          </Suspense>
        </div>
      )}

      {!isMobile && showPortfolio && (
        <div className="absolute top-16 right-4 w-96 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50 max-h-[calc(100vh-5rem)] overflow-y-auto">
          <PortfolioPanel
            visible={showPortfolio}
            onClose={() => setShowPortfolio(false)}
          />
        </div>
      )}

      {/* Enhanced Indicator Settings Panel */}
      {showEnhancedIndicatorSelector && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Suspense fallback={<ComponentLoader message="Loading indicators..." />}>
            <EnhancedIndicatorSelector
            indicators={indicators}
            onIndicatorsChange={(updatedIndicators) => {
              // Filter to only supported indicator types and cast to match state type
              const supportedIndicators = updatedIndicators.filter(ind => 
                ['SMA', 'EMA', 'RSI', 'MACD', 'BB'].includes(ind.type)
              ) as Array<{
                name: string;
                type: 'SMA' | 'EMA' | 'RSI' | 'MACD' | 'BB' | 'ATR' | 'STOCH';
                period: number;
                color: string;
                visible: boolean;
              }>;
              setIndicators(supportedIndicators);
            }}
            onClose={() => setShowEnhancedIndicatorSelector(false)}
          />
          </Suspense>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-16 right-4 w-80 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50">
          <div className="p-4 border-b border-[#2a2e39] flex items-center justify-between">
            <h3 className="font-semibold">Settings</h3>
            <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-white">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm mb-2">Chart Type</label>
              <select className="w-full px-3 py-2 bg-[#131722] rounded text-sm">
                <option>Candlestick</option>
                <option>Line</option>
                <option>Bar</option>
                <option>Area</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-2">Theme</label>
              <select className="w-full px-3 py-2 bg-[#131722] rounded text-sm">
                <option>Dark</option>
                <option>Light</option>
                <option>Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-2">Period</label>
              <input
                type="number"
                value={200}
                className="w-full px-3 py-2 bg-[#131722] rounded text-sm"
                readOnly
              />
            </div>
          </div>
        </div>
      )}

      {/* Analysis Panels - Below Chart */}
      {!isFullscreen && chartData && (
        <div className="w-full bg-[#131722] p-6 space-y-6 border-t border-[#2a2e39]">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-3">
              <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Technical Analysis
            </h2>
            
            {/* Chart Overlay Controls */}
            {overlaysInitialized && (
              <div className="mb-6">
                <ChartOverlayControls
                  settings={overlaySettings}
                  onSettingsChange={handleOverlaySettingsChange}
                />
              </div>
            )}
            
            <div className="grid grid-cols-1 gap-6">
              {/* Technical Indicators Section */}
              {showTechnicalIndicators && chartData?.candles && (
                <div className="bg-[#1e222d] border border-[#2a2e39] rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Technical Indicators
                    </h3>
                    <button
                      onClick={() => setShowTechnicalIndicators(!showTechnicalIndicators)}
                      className="text-gray-400 hover:text-white transition-colors"
                      title="Toggle Technical Indicators"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <Suspense fallback={<ComponentLoader message="Loading technical indicators..." />}>
                    <TechnicalIndicators
                    data={chartData.candles.map((candle: any) => ({
                      date: new Date(candle.time * 1000).toISOString(),
                      close: candle.close,
                      high: candle.high,
                      low: candle.low,
                      open: candle.open,
                      volume: candle.volume,
                    }))}
                    symbol={activeSymbol}
                    height={400}
                    loading={loading}
                    className="bg-transparent"
                    onShowEnhancedSelector={setShowEnhancedIndicatorSelector}
                  />
                  </Suspense>
                </div>
              )}

              {/* Show Technical Indicators Toggle Button (when hidden) */}
              {!showTechnicalIndicators && (
                <button
                  onClick={() => setShowTechnicalIndicators(true)}
                  className="w-full py-3 px-4 bg-[#1e222d] border border-[#2a2e39] rounded-lg text-white hover:bg-[#252936] transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Show Technical Indicators
                </button>
              )}

              {/* Trendline Analysis */}
              <Suspense fallback={<ComponentLoader message="Loading analysis panel..." />}>
                <TabbedAnalysisPanel
                symbol={activeSymbol}
                chartData={chartData}
                currentPrice={chartData?.candles && chartData.candles.length > 0 ? chartData.candles[chartData.candles.length - 1]?.close : undefined}
                defaultTabIndex={initialTabIndex}
                refreshTrigger={analysisRefreshTrigger}
                activeTabIndex={activeTabIndex}
                onTabChange={setActiveTabIndex}
                lastAnalysisTime={lastAnalysisTime}
                onManualRefresh={() => {
                  setAnalysisRefreshTrigger(prev => prev + 1);
                  setLastAnalysisTime(new Date());
                }}
                onTrendlinesDetected={(data) => {
                  console.log('Trendlines detected:', data);
                  chartOverlayService.drawTrendlines(data);
                }}
                onSwingPointsDetected={(data) => {
                  console.log('Swing points detected:', data);
                  chartOverlayService.drawSwingPoints(data);
                }}
                onStructureDetected={(data) => {
                  console.log('Market structure detected:', data);
                  chartOverlayService.drawMarketStructure(data);
                  
                  // Auto-alert: Structure change
                  const currentPriceValue = chartData?.candles && chartData.candles.length > 0 ? chartData.candles[chartData.candles.length - 1]?.close : undefined;
                  if (data.bos_events && data.bos_events.length > 0 && currentPriceValue) {
                    const latestBOS = data.bos_events[data.bos_events.length - 1];
                    const event: AnalysisEvent = {
                      type: 'structure_change',
                      symbol: activeSymbol,
                      timestamp: new Date(),
                      data: {
                        eventType: 'BOS',
                        price: latestBOS.price || currentPriceValue,
                        currentPrice: currentPriceValue
                      },
                      confidence: 0.8
                    };
                    handleAutoAlert(event);
                  }
                  
                  if (data.choch_events && data.choch_events.length > 0 && currentPriceValue) {
                    const latestCHoCH = data.choch_events[data.choch_events.length - 1];
                    const event: AnalysisEvent = {
                      type: 'structure_change',
                      symbol: activeSymbol,
                      timestamp: new Date(),
                      data: {
                        eventType: 'CHoCH',
                        price: latestCHoCH.price || currentPriceValue,
                        currentPrice: currentPriceValue
                      },
                      confidence: 0.8
                    };
                    handleAutoAlert(event);
                  }
                }}
                onLevelsDetected={(data) => {
                  console.log('S&R levels detected:', data);
                  chartOverlayService.drawSupportResistance(data);
                  
                  // Auto-alert: Level touch
                  const currentPriceValue = chartData?.candles && chartData.candles.length > 0 ? chartData.candles[chartData.candles.length - 1]?.close : undefined;
                  if (data.levels && data.levels.length > 0 && currentPriceValue) {
                    data.levels.forEach((level: any) => {
                      const distance = Math.abs((currentPriceValue - (level.price || level.level)) / (level.price || level.level) * 100);
                      if (distance < 1.0) { // Within 1% of level
                        const event: AnalysisEvent = {
                          type: 'level_touch',
                          symbol: activeSymbol,
                          timestamp: new Date(),
                          data: {
                            level: level.price || level.level,
                            price: currentPriceValue,
                            levelType: level.type || 'support'
                          },
                          confidence: 0.9
                        };
                        handleAutoAlert(event);
                      }
                    });
                  }
                }}
                onZonesDetected={(data) => {
                  console.log('S&D zones detected:', data);
                  chartOverlayService.drawSupplyDemand(data);
                  
                  // Auto-alert: Zone break detection
                  const currentPriceValue = chartData?.candles && chartData.candles.length > 0 ? chartData.candles[chartData.candles.length - 1]?.close : undefined;
                  if (data.zones && data.zones.length > 0 && currentPriceValue) {
                    data.zones.forEach((zone: any) => {
                      const zoneBase = zone.base || zone.lower_bound;
                      const zoneTop = zone.top || zone.upper_bound;
                      if (zoneBase && zoneTop) {
                        const isInZone = currentPriceValue >= zoneBase && currentPriceValue <= zoneTop;
                        // Simple break detection - if price is near zone boundary
                        const nearBase = Math.abs(currentPriceValue - zoneBase) / zoneBase < 0.01;
                        const nearTop = Math.abs(currentPriceValue - zoneTop) / zoneTop < 0.01;
                        
                        if ((nearBase || nearTop) && zone.strength && zone.strength > 0.7) {
                          const event: AnalysisEvent = {
                            type: 'zone_break',
                            symbol: activeSymbol,
                            timestamp: new Date(),
                            data: {
                              zoneType: zone.type || 'supply',
                              price: currentPriceValue,
                              breakPrice: nearBase ? zoneBase : zoneTop,
                              base: zoneBase,
                              top: zoneTop
                            },
                            confidence: zone.strength || 0.7
                          };
                          handleAutoAlert(event);
                        }
                      }
                    });
                  }
                }}
              />
              </Suspense>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Period Bar (Groww Terminal Style) */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-t border-gray-200 sticky bottom-0 z-40">
        <div className="flex items-center gap-2 overflow-x-auto">
          {periods.map((p) => {
            const isActive = period === p.value;
            return (
              <button
                key={p.value}
                onClick={() => {
                  setPeriod(p.value);
                  loadChartData();
                }}
                className={`px-3 py-1 rounded text-sm font-medium whitespace-nowrap ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {p.label}
              </button>
            );
          })}
          <button className="px-3 py-1 text-gray-600 hover:bg-gray-100 rounded">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600">
            {new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false })} (UTC+5:30)
          </div>
          <div className="flex items-center gap-2">
            <button className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded">%</button>
            <button className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded">log</button>
            <button className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded">auto</button>
          </div>
        </div>
      </div>

      {/* Interactive Features */}
      <ChartTooltip data={tooltipData} visible={tooltipVisible} />
      <OverlayDetailModal 
        detail={modalDetail} 
        visible={modalVisible} 
        onClose={() => setModalVisible(false)} 
      />

      {/* Chat Widget */}
      {showChat && (
        <Suspense fallback={<ComponentLoader message="Loading chat..." />}>
          <ChatWidget
          symbol={activeSymbol}
          timeframe={timeframe}
          chartContext={{
            currentPrice: chartData?.candles && chartData.candles.length > 0 
              ? chartData.candles[chartData.candles.length - 1]?.close 
              : undefined,
            chartData: chartData
          }}
          minimized={chatMinimized}
          onMinimize={setChatMinimized}
          onClose={() => setShowChat(false)}
        />
        </Suspense>
      )}

      {/* Multi-Timeframe Panel */}
      {showMultiTimeframe && (
        <Suspense fallback={<ComponentLoader message="Loading multi-timeframe..." />}>
          <MultiTimeframePanel
          symbol={activeSymbol}
          mainTimeframe={timeframe}
          onClose={() => setShowMultiTimeframe(false)}
        />
        </Suspense>
      )}

      {/* Chart Settings Panel */}
      {showChartSettings && (
        <Suspense fallback={<ComponentLoader message="Loading chart settings..." />}>
          <ChartSettingsPanel
          settings={chartSettings}
          onSettingsChange={(partial) => {
            if (partial.theme) updateTheme(partial.theme);
            if (partial.appearance) updateAppearance(partial.appearance);
            if (partial.candlestick) updateCandlestick(partial.candlestick);
            if (partial.scale) updateScale(partial.scale);
          }}
          onThemeChange={updateTheme}
          onClose={() => setShowChartSettings(false)}
        />
        </Suspense>
      )}
    </div>
  );
};

export default ComprehensiveTradingPro;
