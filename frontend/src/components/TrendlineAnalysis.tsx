/**
 * Trendline Analysis Component
 * Automatically detects and displays trendlines, channels, and swing points on charts
 * Provides interactive trendline drawing and analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  AdjustmentsHorizontalIcon,
  BoltIcon,
  CheckCircleIcon,
  XMarkIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { cn } from '../lib/utils';
import LoadingSpinner from './LoadingSpinner';
import { formatChartDataForAnalysis } from '../utils/dataFormatter';

interface SwingPoint {
  index: number;
  price: number;
  time: string | number;
}

interface Trendline {
  type: 'uptrend' | 'downtrend' | 'horizontal';
  start_index: number;
  start_price: number;
  end_index: number;
  end_price: number;
  slope: number;
  intercept: number;
  touches: number;
  touch_points: SwingPoint[];
  strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
  is_broken?: {
    is_broken: boolean;
    break_index?: number;
    break_price?: number;
    break_percentage?: number;
  };
  length_bars: number;
  volume_info?: {
    volume_quality: 'very_high' | 'high' | 'moderate' | 'low';
    avg_volume_ratio: number;
    volume_confirmed_touches: number;
    total_touches: number;
  };
}

interface Channel {
  type: 'ascending_channel' | 'descending_channel';
  support_line: any;
  resistance_line: any;
  width: number;
  width_percentage: number;
}

interface TrendlineAnalysisProps {
  symbol: string;
  chartData: any[] | { candles?: any[] };
  onTrendlinesDetected?: (data: any) => void;
  className?: string;
  chartApi?: any;
  candlestickSeries?: any;
}

const TrendlineAnalysis: React.FC<TrendlineAnalysisProps> = ({
  symbol,
  chartData,
  onTrendlinesDetected,
  className = '',
  chartApi,
  candlestickSeries
}) => {
  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trendlineData, setTrendlineData] = useState<any>(null);
  
  // Display settings
  const [showUptrends, setShowUptrends] = useState(true);
  const [showDowntrends, setShowDowntrends] = useState(true);
  const [showHorizontal, setShowHorizontal] = useState(true);
  const [showChannels, setShowChannels] = useState(true);
  const [showSwingPoints, setShowSwingPoints] = useState(false);
  const [showBrokenLines, setShowBrokenLines] = useState(false);
  
  // Settings
  const [minTouches, setMinTouches] = useState(2);
  const [lookbackPeriod, setLookbackPeriod] = useState(100);
  const [showSettings, setShowSettings] = useState(false);
  const [autoDetect, setAutoDetect] = useState(false); // Disabled by default for performance
  const [showProjections, setShowProjections] = useState(false);
  const [futureBars, setFutureBars] = useState(20);
  const [projections, setProjections] = useState<any>(null);
  const [manualDrawingMode, setManualDrawingMode] = useState(false);
  const [manualTrendlines, setManualTrendlines] = useState<any[]>([]);
  const [drawingStart, setDrawingStart] = useState<{time: number, price: number} | null>(null);

  // Helper function to normalize chartData to always return an array
  const getChartDataArray = useCallback((): any[] => {
    if (Array.isArray(chartData)) {
      return chartData;
    }
    if (chartData && typeof chartData === 'object' && 'candles' in chartData) {
      return Array.isArray((chartData as any).candles) ? (chartData as any).candles : [];
    }
    return [];
  }, [chartData]);

  // Load manual trendlines
  const loadManualTrendlines = useCallback(async () => {
    if (!symbol) return;
    
    try {
      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/trendlines/manual/${symbol}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.manual_trendlines) {
          setManualTrendlines(result.manual_trendlines);
        }
      }
    } catch (err) {
      console.error('Error loading manual trendlines:', err);
    }
  }, [symbol]);

  // Auto-detect trendlines (optimized with loading guard and memoization)
  const detectTrendlines = useCallback(async () => {
    const dataArray = getChartDataArray();
    if (!dataArray || dataArray.length === 0) {
      setError('No chart data available');
      return;
    }

    // Prevent multiple simultaneous calls
    if (loading) {
      console.log('Trendline detection already in progress, skipping...');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const formattedData = formatChartDataForAnalysis(dataArray);
      
      if (!formattedData || formattedData.length === 0) {
        setError('Invalid chart data format');
        setLoading(false);
        return;
      }

      const response = await fetch(`${backendUrl}/api/trendlines/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          data: formattedData,
          min_touches: minTouches,
          lookback_period: lookbackPeriod
        })
      });

      if (!response.ok) {
        throw new Error('Failed to detect trendlines');
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        setTrendlineData(result.data);
        
        // Prepare trendline data with chart data for time mapping
        const currentChartData = dataArray.map((candle: any) => ({
          time: candle.time || candle.timestamp,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close
        }));

        const trendlineDataWithChart = {
          ...result.data,
          chartData: currentChartData,
          projections: projections?.projections || null,
          manual_trendlines: manualTrendlines
        };
        
        onTrendlinesDetected?.(trendlineDataWithChart);
        
        // Load manual trendlines after detection completes (only once)
        if (symbol && manualTrendlines.length === 0) {
          loadManualTrendlines();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect trendlines');
      console.error('Trendline detection error:', err);
    } finally {
      setLoading(false);
    }
  }, [symbol, minTouches, lookbackPeriod, onTrendlinesDetected, projections, manualTrendlines.length, loading, loadManualTrendlines, getChartDataArray]);

  // Fetch projections
  const fetchProjections = useCallback(async () => {
    const dataArray = getChartDataArray();
    if (!dataArray || dataArray.length === 0 || !trendlineData) {
      return;
    }

    try {
      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/trendlines/project-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          data: formatChartDataForAnalysis(dataArray),
          min_touches: minTouches,
          lookback_period: lookbackPeriod,
          future_bars: futureBars
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch projections');
      }

      const result = await response.json();
      
      if (result.success && result.projections) {
        setProjections(result.projections);
        
        // Update trendline data with projections
        const trendlineDataWithChart = {
          ...trendlineData,
          chartData: dataArray.map((candle: any) => ({
            time: candle.time || candle.timestamp,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close
          })),
          projections: result.projections.projections
        };
        
        onTrendlinesDetected?.(trendlineDataWithChart);
      }
    } catch (err) {
      console.error('Projection fetch error:', err);
    }
  }, [symbol, getChartDataArray, trendlineData, minTouches, lookbackPeriod, futureBars, onTrendlinesDetected]);

  // Auto-fetch projections when enabled (with debouncing)
  useEffect(() => {
    if (!showProjections || !trendlineData) {
      return;
    }

    // Debounce to prevent excessive API calls
    const timeoutId = setTimeout(() => {
      fetchProjections();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [showProjections]); // Only depend on showProjections, not trendlineData or fetchProjections

  // Auto-detect on data change (with debouncing and loading guard)
  useEffect(() => {
    const dataArray = getChartDataArray();
    if (!autoDetect || !dataArray || dataArray.length === 0 || loading) {
      return;
    }

    // Debounce to prevent multiple rapid calls
    const timeoutId = setTimeout(() => {
      if (!loading) { // Double-check loading state
        detectTrendlines();
      }
    }, 800); // 800ms debounce for better performance

    return () => clearTimeout(timeoutId);
  }, [autoDetect, symbol, getChartDataArray, loading]); // Only depend on autoDetect and symbol to prevent excessive calls

  // Helper functions
  const getTrendlineColor = (type: string, strength: string): string => {
    const colors: Record<string, Record<string, string>> = {
      uptrend: {
        weak: 'border-green-300',
        moderate: 'border-green-400',
        strong: 'border-green-500',
        very_strong: 'border-green-600'
      },
      downtrend: {
        weak: 'border-red-300',
        moderate: 'border-red-400',
        strong: 'border-red-500',
        very_strong: 'border-red-600'
      },
      horizontal: {
        weak: 'border-blue-300',
        moderate: 'border-blue-400',
        strong: 'border-blue-500',
        very_strong: 'border-blue-600'
      }
    };
    return colors[type]?.[strength] || 'border-gray-400';
  };

  const getStrengthBadge = (strength: string): JSX.Element => {
    const badges: Record<string, { color: string; text: string }> = {
      weak: { color: 'bg-gray-100 text-gray-800', text: 'Weak' },
      moderate: { color: 'bg-yellow-100 text-yellow-800', text: 'Moderate' },
      strong: { color: 'bg-orange-100 text-orange-800', text: 'Strong' },
      very_strong: { color: 'bg-red-100 text-red-800', text: 'Very Strong' }
    };
    const badge = badges[strength] || badges.weak;
    return (
      <span className={cn('px-2 py-1 text-xs font-medium rounded', badge.color)}>
        {badge.text}
      </span>
    );
  };

  const formatPrice = (price: number): string => {
    return `₹${price.toFixed(2)}`;
  };

  const renderTrendline = (line: Trendline, index: number): JSX.Element => {
    const isBroken = line.is_broken?.is_broken || false;
    if (isBroken && !showBrokenLines) return <></>;

    return (
      <div
        key={`${line.type}-${index}`}
        className={cn(
          'p-3 rounded-lg border-l-4 transition-all hover:shadow-md',
          getTrendlineColor(line.type, line.strength),
          isBroken ? 'bg-gray-50 opacity-60' : 'bg-white'
        )}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {line.type === 'uptrend' && (
              <ArrowTrendingUpIcon className="w-4 h-4 text-green-600" />
            )}
            {line.type === 'downtrend' && (
              <ArrowTrendingDownIcon className="w-4 h-4 text-red-600" />
            )}
            {line.type === 'horizontal' && (
              <MinusIcon className="w-4 h-4 text-blue-600" />
            )}
            <span className="font-semibold text-sm text-gray-900">
              {line.type.charAt(0).toUpperCase() + line.type.slice(1).replace('_', ' ')}
            </span>
            {isBroken && (
              <span className="text-xs text-red-600 font-medium">(Broken)</span>
            )}
          </div>
          {getStrengthBadge(line.strength)}
        </div>

        <div className="space-y-1 text-sm text-gray-700">
          <div className="flex justify-between">
            <span className="text-gray-600">Start:</span>
            <span className="font-medium">{formatPrice(line.start_price)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Current:</span>
            <span className="font-medium">{formatPrice(line.end_price)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Touches:</span>
            <span className="font-medium">{line.touches}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Length:</span>
            <span className="font-medium">{line.length_bars} bars</span>
          </div>
          
          {/* Volume Confirmation Info */}
          {line.volume_info && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="flex items-center justify-between mb-1">
                <span className="text-gray-600 text-xs">Volume Quality:</span>
                <span className={cn(
                  'px-2 py-0.5 text-xs font-medium rounded',
                  line.volume_info.volume_quality === 'very_high' ? 'bg-green-100 text-green-800' :
                  line.volume_info.volume_quality === 'high' ? 'bg-blue-100 text-blue-800' :
                  line.volume_info.volume_quality === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                )}>
                  {line.volume_info.volume_quality === 'very_high' ? 'Very High' :
                   line.volume_info.volume_quality === 'high' ? 'High' :
                   line.volume_info.volume_quality === 'moderate' ? 'Moderate' : 'Low'}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600">Avg Volume Ratio:</span>
                <span className="font-medium">{line.volume_info.avg_volume_ratio?.toFixed(2) || '1.00'}x</span>
              </div>
              {line.volume_info.volume_confirmed_touches > 0 && (
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">Volume Confirmed:</span>
                  <span className="font-medium text-green-700">
                    {line.volume_info.volume_confirmed_touches}/{line.volume_info.total_touches} touches
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {isBroken && line.is_broken && line.is_broken.break_price !== undefined && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="text-xs text-red-600">
              Broken at {formatPrice(line.is_broken.break_price)} 
              ({line.is_broken.break_percentage?.toFixed(2)}%)
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ChartBarIcon className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Trendline Analysis
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
            title="Settings"
          >
            <AdjustmentsHorizontalIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">
            Detection Settings
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Minimum Touches: {minTouches}
              </label>
              <input
                type="range"
                min="2"
                max="5"
                value={minTouches}
                onChange={(e) => setMinTouches(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Lookback Period: {lookbackPeriod}
              </label>
              <input
                type="range"
                min="50"
                max="200"
                step="10"
                value={lookbackPeriod}
                onChange={(e) => setLookbackPeriod(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoDetect"
                checked={autoDetect}
                onChange={(e) => setAutoDetect(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="autoDetect" className="text-sm text-gray-700 dark:text-gray-300">
                Auto-detect on data change
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Display Toggles */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => setShowUptrends(!showUptrends)}
          className={cn(
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            showUptrends
              ? 'bg-green-100 text-green-800 border-2 border-green-400'
              : 'bg-gray-100 text-gray-600 border-2 border-transparent'
          )}
        >
          {showUptrends ? <EyeIcon className="w-4 h-4 inline mr-1" /> : <EyeSlashIcon className="w-4 h-4 inline mr-1" />}
          Uptrends
        </button>
        <button
          onClick={() => setShowDowntrends(!showDowntrends)}
          className={cn(
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            showDowntrends
              ? 'bg-red-100 text-red-800 border-2 border-red-400'
              : 'bg-gray-100 text-gray-600 border-2 border-transparent'
          )}
        >
          {showDowntrends ? <EyeIcon className="w-4 h-4 inline mr-1" /> : <EyeSlashIcon className="w-4 h-4 inline mr-1" />}
          Downtrends
        </button>
        <button
          onClick={() => setShowHorizontal(!showHorizontal)}
          className={cn(
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            showHorizontal
              ? 'bg-blue-100 text-blue-800 border-2 border-blue-400'
              : 'bg-gray-100 text-gray-600 border-2 border-transparent'
          )}
        >
          {showHorizontal ? <EyeIcon className="w-4 h-4 inline mr-1" /> : <EyeSlashIcon className="w-4 h-4 inline mr-1" />}
          Horizontal
        </button>
        <button
          onClick={() => setShowChannels(!showChannels)}
          className={cn(
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            showChannels
              ? 'bg-purple-100 text-purple-800 border-2 border-purple-400'
              : 'bg-gray-100 text-gray-600 border-2 border-transparent'
          )}
        >
          Channels
        </button>
        <button
          onClick={() => setShowSwingPoints(!showSwingPoints)}
          className={cn(
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            showSwingPoints
              ? 'bg-orange-100 text-orange-800 border-2 border-orange-400'
              : 'bg-gray-100 text-gray-600 border-2 border-transparent'
          )}
        >
          Swing Points
        </button>
        <button
          onClick={() => setShowBrokenLines(!showBrokenLines)}
          className={cn(
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
            showBrokenLines
              ? 'bg-gray-200 text-gray-800 border-2 border-gray-400'
              : 'bg-gray-100 text-gray-600 border-2 border-transparent'
          )}
        >
          Show Broken
        </button>
      </div>

      {/* Detect Button */}
      <button
        onClick={detectTrendlines}
        disabled={loading}
        className="w-full mb-6 py-2 px-4 bg-blue-600 text-white rounded-lg font-medium 
                 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <LoadingSpinner size="sm" />
            Detecting Trendlines...
          </>
        ) : (
          <>
            <BoltIcon className="w-5 h-5" />
            Auto-Detect Trendlines
          </>
        )}
      </button>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {/* Results */}
      {!loading && trendlineData && (
        <div className="space-y-6">
          {/* Current Trend Summary */}
          {trendlineData.current_trend && (
            <div className={cn(
              'p-4 rounded-lg border-2',
              trendlineData.current_trend.trend === 'uptrend' && 'bg-green-50 border-green-400',
              trendlineData.current_trend.trend === 'downtrend' && 'bg-red-50 border-red-400',
              trendlineData.current_trend.trend === 'sideways' && 'bg-gray-50 border-gray-400'
            )}>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-600">Current Trend:</span>
                  <span className="ml-2 text-lg font-bold text-gray-900 capitalize">
                    {trendlineData.current_trend.trend}
                  </span>
                </div>
                {getStrengthBadge(trendlineData.current_trend.confidence)}
              </div>
            </div>
          )}

          {/* Uptrend Lines */}
          {showUptrends && trendlineData.uptrend_lines && trendlineData.uptrend_lines.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white flex items-center gap-2">
                <ArrowTrendingUpIcon className="w-5 h-5 text-green-600" />
                Uptrend Lines ({trendlineData.uptrend_lines.length})
              </h3>
              <div className="space-y-2">
                {trendlineData.uptrend_lines.slice(0, 5).map((line: Trendline, index: number) => 
                  renderTrendline(line, index)
                )}
              </div>
            </div>
          )}

          {/* Downtrend Lines */}
          {showDowntrends && trendlineData.downtrend_lines && trendlineData.downtrend_lines.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white flex items-center gap-2">
                <ArrowTrendingDownIcon className="w-5 h-5 text-red-600" />
                Downtrend Lines ({trendlineData.downtrend_lines.length})
              </h3>
              <div className="space-y-2">
                {trendlineData.downtrend_lines.slice(0, 5).map((line: Trendline, index: number) => 
                  renderTrendline(line, index)
                )}
              </div>
            </div>
          )}

          {/* Horizontal Lines */}
          {showHorizontal && trendlineData.horizontal_lines && trendlineData.horizontal_lines.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white flex items-center gap-2">
                <MinusIcon className="w-5 h-5 text-blue-600" />
                Key Levels ({trendlineData.horizontal_lines.length})
              </h3>
              <div className="space-y-2">
                {trendlineData.horizontal_lines.map((line: any, index: number) => (
                  <div key={`horizontal-${index}`} className="p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-gray-900">
                        {formatPrice(line.price)}
                      </span>
                      <div className="flex items-center gap-2">
                        {getStrengthBadge(line.strength)}
                        <span className="text-xs text-gray-600">{line.touches} touches</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Channels */}
          {showChannels && trendlineData.channels && trendlineData.channels.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">
                Channels ({trendlineData.channels.length})
              </h3>
              <div className="space-y-2">
                {trendlineData.channels.map((channel: Channel, index: number) => (
                  <div key={`channel-${index}`} className="p-3 bg-purple-50 rounded-lg border-2 border-purple-400">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-gray-900 capitalize">
                        {channel.type.replace('_', ' ')}
                      </span>
                      <span className="text-sm text-purple-700 font-medium">
                        Width: {channel.width_percentage.toFixed(2)}%
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      Channel width: {formatPrice(channel.width)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Projections & Targets */}
          {showProjections && projections && (
            <div className="p-4 bg-indigo-50 border-2 border-indigo-400 rounded-lg mb-4">
              <h3 className="text-sm font-semibold mb-3 text-indigo-900 flex items-center gap-2">
                <ChartBarIcon className="w-5 h-5" />
                Price Targets & Projections
              </h3>
              {Object.entries(projections.projections || {}).map(([key, projData]: [string, any]) => {
                const targetZone = projData.target_zone;
                const keyTargets = projData.key_targets;
                
                return (
                  <div key={key} className="mb-4 p-3 bg-white rounded-lg border border-indigo-300">
                    <div className="font-semibold text-gray-900 mb-2 capitalize">
                      {projData.trendline?.type || 'Trendline'} Projection
                    </div>
                    
                    {/* Key Targets */}
                    {keyTargets && (
                      <div className="grid grid-cols-3 gap-2 mb-3">
                        <div className="bg-blue-50 p-2 rounded">
                          <div className="text-xs text-gray-600">Short Term</div>
                          <div className="font-bold text-blue-900">{formatPrice(keyTargets.short_term.price)}</div>
                          <div className="text-xs text-gray-500">{keyTargets.short_term.bars} bars</div>
                        </div>
                        <div className="bg-purple-50 p-2 rounded">
                          <div className="text-xs text-gray-600">Medium Term</div>
                          <div className="font-bold text-purple-900">{formatPrice(keyTargets.medium_term.price)}</div>
                          <div className="text-xs text-gray-500">{keyTargets.medium_term.bars} bars</div>
                        </div>
                        <div className="bg-pink-50 p-2 rounded">
                          <div className="text-xs text-gray-600">Long Term</div>
                          <div className="font-bold text-pink-900">{formatPrice(keyTargets.long_term.price)}</div>
                          <div className="text-xs text-gray-500">{keyTargets.long_term.bars} bars</div>
                        </div>
                      </div>
                    )}
                    
                    {/* Target Zone */}
                    {targetZone && (
                      <div className="border-t border-gray-200 pt-2">
                        <div className="text-xs font-semibold text-gray-700 mb-1">Target Zone</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-600">Upper:</span>
                            <span className="ml-1 font-medium text-green-700">{formatPrice(targetZone.upper)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Lower:</span>
                            <span className="ml-1 font-medium text-red-700">{formatPrice(targetZone.lower)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Center:</span>
                            <span className="ml-1 font-medium">{formatPrice(targetZone.center)}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Width:</span>
                            <span className="ml-1 font-medium">{targetZone.width_percentage.toFixed(2)}%</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Recent Breaks */}
          {trendlineData.recent_breaks && trendlineData.recent_breaks.length > 0 && (
            <div className="p-4 bg-yellow-50 border-2 border-yellow-400 rounded-lg">
              <h3 className="text-sm font-semibold mb-3 text-yellow-900 flex items-center gap-2">
                <BoltIcon className="w-5 h-5" />
                Recent Trendline Breaks ({trendlineData.recent_breaks.length})
              </h3>
              <div className="space-y-3">
                {trendlineData.recent_breaks.map((breakInfo: any, index: number) => {
                  const signalQuality = breakInfo.signal_quality || breakInfo.signal?.quality || 'LOW';
                  const volumeConfirmed = breakInfo.volume_confirmed || breakInfo.signal?.volume_confirmed || false;
                  const retested = breakInfo.retest?.retested || breakInfo.signal?.retested || false;
                  const breakType = breakInfo.break_type || 'close';
                  
                  return (
                    <div key={index} className="p-3 bg-white rounded-lg border border-yellow-300">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {breakInfo.trendline_type === 'uptrend' ? '🔻' : '🔺'}
                          <span className="font-semibold text-gray-900 capitalize">
                            {breakInfo.trendline_type} Broken
                          </span>
                          {breakType === 'close' && (
                            <span className="px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded">Close Break</span>
                          )}
                          {breakType === 'wick' && (
                            <span className="px-2 py-0.5 text-xs bg-orange-100 text-orange-800 rounded">Wick Break</span>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          signalQuality === 'HIGH' ? 'bg-green-100 text-green-800' :
                          signalQuality === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {signalQuality} Quality
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
                        <div>
                          <span className="text-gray-600">Break:</span>
                          <span className="ml-1 font-medium">{breakInfo.break_percentage?.toFixed(2)}%</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Price:</span>
                          <span className="ml-1 font-medium">{formatPrice(breakInfo.break_price)}</span>
                        </div>
                        {volumeConfirmed && (
                          <div className="flex items-center gap-1">
                            <CheckCircleIcon className="w-4 h-4 text-green-600" />
                            <span className="text-green-700">Volume Confirmed</span>
                          </div>
                        )}
                        {retested && (
                          <div className="flex items-center gap-1">
                            <CheckCircleIcon className="w-4 h-4 text-blue-600" />
                            <span className="text-blue-700">Retested as {breakInfo.retest?.retest_type || 'Level'}</span>
                          </div>
                        )}
                      </div>
                      
                      {breakInfo.signal && (
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <div className="text-xs">
                            <span className="font-semibold text-gray-900">{breakInfo.signal.type} Signal:</span>
                            <span className="ml-2 text-gray-700">{breakInfo.signal.reason}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Data */}
      {!loading && !trendlineData && !error && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <ChartBarIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No trendlines detected yet</p>
          <p className="text-sm mt-1">Click "Auto-Detect" to find trendlines</p>
        </div>
      )}
    </div>
  );
};

export default TrendlineAnalysis;

