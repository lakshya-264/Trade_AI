/**
 * Swing Point Analysis Component
 * Displays swing points labeled as HH (Higher High), HL (Higher Low), LH (Lower High), LL (Lower Low)
 * Essential for market structure and trend analysis
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  BoltIcon,
  AdjustmentsHorizontalIcon,
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
  type: 'swing_high' | 'swing_low';
  label?: 'HH' | 'HL' | 'LH' | 'LL';
  pattern?: 'bullish' | 'bearish' | 'initial';
  price_change?: number;
  price_change_percent?: number;
}

interface TrendAnalysis {
  trend: 'uptrend' | 'downtrend' | 'sideways';
  confidence: 'high' | 'medium' | 'low';
  description: string;
  bullish_signals: number;
  bearish_signals: number;
  recent_pattern: {
    higher_highs: number;
    lower_highs: number;
    higher_lows: number;
    lower_lows: number;
  };
  current_price?: number;
}

interface SwingPointAnalysisProps {
  symbol: string;
  chartData: any[];
  onSwingPointsDetected?: (data: any) => void;
  onLoadingStateChange?: (isLoading: boolean) => void;
  className?: string;
}

const SwingPointAnalysis: React.FC<SwingPointAnalysisProps> = ({
  symbol,
  chartData,
  onSwingPointsDetected,
  onLoadingStateChange,
  className = ''
}) => {
  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [swingData, setSwingData] = useState<any>(null);
  const [loadingMessage, setLoadingMessage] = useState<string>('Analyzing swing points...');
  
  // Display settings
  const [showHighs, setShowHighs] = useState(true);
  const [showLows, setShowLows] = useState(true);
  const [strength, setStrength] = useState(5);
  const [showSettings, setShowSettings] = useState(false);
  const [autoDetect, setAutoDetect] = useState(false); // Manual refresh by default

  // Ref to prevent multiple simultaneous requests
  const isRequestInProgress = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-detect swing points
  const detectSwingPoints = useCallback(async () => {
    if (!chartData || chartData.length === 0) {
      setError('No chart data available');
      return;
    }

    // Prevent multiple simultaneous requests
    if (isRequestInProgress.current) {
      console.log('Swing point analysis already in progress, skipping...');
      return;
    }

    try {
      // Cancel any previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();
      isRequestInProgress.current = true;
      
      setLoading(true);
      setError(null);
      setLoadingMessage('Preparing data...');
      onLoadingStateChange?.(true);

      // Set timeout warning if loading takes too long
      loadingTimeoutRef.current = setTimeout(() => {
        if (isRequestInProgress.current) {
          setLoadingMessage('This is taking longer than usual... Please wait.');
        }
      }, 5000); // Show message after 5 seconds

      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      setLoadingMessage('Sending request to server...');
      
      const response = await fetch(`${backendUrl}/api/swing-points/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          data: formatChartDataForAnalysis(chartData),
          strength
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Failed to detect swing points: ${response.statusText}`);
      }

      setLoadingMessage('Processing results...');
      const result = await response.json();
      
      if (result.success && result.data) {
        setSwingData(result.data);
        onSwingPointsDetected?.(result.data);
        setLoadingMessage('Analysis complete!');
      } else {
        throw new Error(result.error || 'Analysis failed');
      }
    } catch (err: any) {
      // Don't show error if request was aborted
      if (err.name === 'AbortError') {
        console.log('Swing point analysis request aborted');
        return;
      }
      setError(err instanceof Error ? err.message : 'Failed to detect swing points');
      console.error('Swing point detection error:', err);
    } finally {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setLoading(false);
      isRequestInProgress.current = false;
      abortControllerRef.current = null;
      onLoadingStateChange?.(false);
    }
  }, [symbol, chartData, strength, onSwingPointsDetected]);

  // Auto-detect on data change (with debounce to prevent rapid requests)
  useEffect(() => {
    if (autoDetect && chartData && chartData.length > 0 && !isRequestInProgress.current) {
      // Debounce: wait a bit before auto-detecting to avoid rapid requests
      const timeoutId = setTimeout(() => {
        detectSwingPoints();
      }, 300); // 300ms debounce

      return () => clearTimeout(timeoutId);
    }
  }, [autoDetect, detectSwingPoints, chartData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, []);

  // Helper functions
  const getLabelColor = (label?: string) => {
    switch (label) {
      case 'HH': return 'text-green-600 bg-green-50 border-green-200';
      case 'HL': return 'text-green-500 bg-green-50 border-green-200';
      case 'LH': return 'text-red-500 bg-red-50 border-red-200';
      case 'LL': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-500 bg-gray-50 border-gray-200';
    }
  };

  const getLabelDescription = (label?: string) => {
    switch (label) {
      case 'HH': return 'Higher High - Bullish';
      case 'HL': return 'Higher Low - Bullish';
      case 'LH': return 'Lower High - Bearish';
      case 'LL': return 'Lower Low - Bearish';
      default: return 'Initial Point';
    }
  };

  const formatPrice = (price: number) => {
    return `₹${price.toFixed(2)}`;
  };

  // Render swing point card
  const renderSwingPoint = (point: SwingPoint, index: number) => {
    const isHigh = point.type === 'swing_high';
    const isBullish = point.pattern === 'bullish';
    
    return (
      <div
        key={`${point.type}-${point.index}-${index}`}
        className={cn(
          'p-3 rounded-lg border',
          isBullish ? 'bg-green-50/50 border-green-200' : 
          point.pattern === 'bearish' ? 'bg-red-50/50 border-red-200' : 
          'bg-gray-50 border-gray-200'
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {isHigh ? (
              <ArrowTrendingUpIcon className="w-5 h-5 text-blue-600" />
            ) : (
              <ArrowTrendingDownIcon className="w-5 h-5 text-purple-600" />
            )}
            <div>
              <div className="flex items-center gap-2">
                {point.label && (
                  <span className={cn(
                    'px-2 py-0.5 rounded text-xs font-bold border',
                    getLabelColor(point.label)
                  )}>
                    {point.label}
                  </span>
                )}
                <span className="text-sm font-medium text-gray-700">
                  {formatPrice(point.price)}
                </span>
              </div>
              {point.label && (
                <div className="text-xs text-gray-500 mt-1">
                  {getLabelDescription(point.label)}
                </div>
              )}
            </div>
          </div>
          {point.price_change_percent !== undefined && (
            <div className={cn(
              'text-xs font-medium',
              point.price_change && point.price_change > 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {point.price_change_percent > 0 ? '+' : ''}
              {point.price_change_percent.toFixed(2)}%
            </div>
          )}
        </div>
      </div>
    );
  };

  // Filter visible points
  const visibleHighs = swingData?.swing_highs?.filter(() => showHighs) || [];
  const visibleLows = swingData?.swing_lows?.filter(() => showLows) || [];

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 relative', className)}>
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm rounded-lg z-50 flex flex-col items-center justify-center">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-xl max-w-sm w-full mx-4">
            <div className="flex flex-col items-center gap-4">
              <LoadingSpinner size="lg" />
              <div className="text-center">
                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Analyzing Swing Points
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {loadingMessage}
                </p>
                <div className="mt-4 w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ChartBarIcon className={cn('w-6 h-6', loading ? 'text-blue-400 animate-pulse' : 'text-blue-600')} />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Swing Point Analysis
            {loading && (
              <span className="ml-2 text-sm font-normal text-blue-600 animate-pulse">
                (Loading...)
              </span>
            )}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            disabled={loading}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Settings"
          >
            <AdjustmentsHorizontalIcon className="w-5 h-5 text-gray-600" />
          </button>
          <button
            onClick={detectSwingPoints}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Analyzing...
              </>
            ) : (
              <>
                <BoltIcon className="w-4 h-4" />
                Auto-Detect
              </>
            )}
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Detection Settings
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                Strength
              </label>
              <input
                type="number"
                value={strength}
                onChange={(e) => setStrength(Math.max(3, Math.min(10, parseInt(e.target.value) || 5)))}
                min={3}
                max={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Bars on each side (3-10)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={autoDetect}
                onChange={(e) => setAutoDetect(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label className="text-sm text-gray-700 dark:text-gray-300">
                Auto-detect on data change
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Toggle Controls */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <button
          onClick={() => setShowHighs(!showHighs)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
            showHighs
              ? 'bg-green-100 text-green-700 border-2 border-green-300'
              : 'bg-gray-100 text-gray-500 border-2 border-gray-200'
          )}
        >
          {showHighs ? <EyeIcon className="w-4 h-4" /> : <EyeSlashIcon className="w-4 h-4" />}
          Swing Highs (HH/LH)
        </button>
        <button
          onClick={() => setShowLows(!showLows)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
            showLows
              ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
              : 'bg-gray-100 text-gray-500 border-2 border-gray-200'
          )}
        >
          {showLows ? <EyeIcon className="w-4 h-4" /> : <EyeSlashIcon className="w-4 h-4" />}
          Swing Lows (HL/LL)
        </button>
      </div>

      {/* Loading State - Fallback (overlay handles main loading) */}
      {loading && !swingData && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <LoadingSpinner />
            <p className="mt-4 text-gray-600 dark:text-gray-400">{loadingMessage}</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {!loading && swingData && (
        <div className="space-y-6">
          {/* Trend Analysis */}
          {swingData.trend_analysis && (
            <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Market Structure</h3>
              <div className="flex items-center gap-3">
                <div className={cn(
                  'px-3 py-1.5 rounded-full font-bold text-sm',
                  swingData.trend_analysis.trend === 'uptrend' ? 'bg-green-100 text-green-700' :
                  swingData.trend_analysis.trend === 'downtrend' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                )}>
                  {swingData.trend_analysis.trend.toUpperCase()}
                </div>
                <div className="text-sm text-gray-600">
                  {swingData.trend_analysis.description}
                </div>
                <div className="ml-auto text-xs text-gray-500">
                  {swingData.trend_analysis.confidence} confidence
                </div>
              </div>
              <div className="mt-3 flex gap-4 text-xs">
                <div className="text-green-600">
                  Bullish: {swingData.trend_analysis.bullish_signals}
                </div>
                <div className="text-red-600">
                  Bearish: {swingData.trend_analysis.bearish_signals}
                </div>
              </div>
            </div>
          )}

          {/* Statistics */}
          {swingData.statistics && (
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {swingData.statistics.total_swing_points}
                </div>
                <div className="text-xs text-gray-600">Total Points</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {swingData.statistics.higher_highs + swingData.statistics.higher_lows}
                </div>
                <div className="text-xs text-gray-600">Bullish (HH+HL)</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {swingData.statistics.lower_highs + swingData.statistics.lower_lows}
                </div>
                <div className="text-xs text-gray-600">Bearish (LH+LL)</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {swingData.statistics.bullish_structure_percent}%
                </div>
                <div className="text-xs text-gray-600">Bullish %</div>
              </div>
            </div>
          )}

          {/* Swing Points Lists */}
          <div className="grid grid-cols-2 gap-6">
            {/* Swing Highs */}
            {showHighs && visibleHighs.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <ArrowTrendingUpIcon className="w-4 h-4" />
                  Swing Highs ({visibleHighs.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {visibleHighs.slice(-10).reverse().map((point: SwingPoint, idx: number) => 
                    renderSwingPoint(point, idx)
                  )}
                </div>
              </div>
            )}

            {/* Swing Lows */}
            {showLows && visibleLows.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <ArrowTrendingDownIcon className="w-4 h-4" />
                  Swing Lows ({visibleLows.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {visibleLows.slice(-10).reverse().map((point: SwingPoint, idx: number) => 
                    renderSwingPoint(point, idx)
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Current Structure */}
          {swingData.current_structure && swingData.current_structure.status === 'active' && (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Current Structure</h3>
              <div className="text-sm text-gray-600">
                {swingData.current_structure.message}
              </div>
              {swingData.current_structure.recent_sequence && (
                <div className="mt-2 text-xs text-gray-500 font-mono">
                  Recent: {swingData.current_structure.recent_sequence}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* No Data */}
      {!loading && !swingData && !error && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <ChartBarIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No swing points detected yet</p>
          <p className="text-sm mt-1">Click "Auto-Detect" to analyze swing points</p>
        </div>
      )}
    </div>
  );
};

export default SwingPointAnalysis;

